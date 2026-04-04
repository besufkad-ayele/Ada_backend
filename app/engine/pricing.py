"""
Dynamic Pricing Engine — The Core Algorithm

Treats each hotel room night as a perishable asset (like an airline seat).
Continuously optimizes: given current occupancy and days until arrival,
what price maximizes total revenue for that night?

Three layers:
1. Base rate adjustment (occupancy + lead time)
2. Demand signal modifiers (events, seasonality, competitors)
3. Fare class inventory fencing
"""
import math
from datetime import date, timedelta
from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.rooms import DailyInventory, RoomType, FareClass
from app.models.events import Event, CompetitorRate, PricingLog


settings = get_settings()


class PricingEngine:
    """
    The airline-style dynamic pricing engine.
    
    Core formula:
        optimal_rate = base_rate × occupancy_factor × lead_time_factor 
                       × demand_factor × event_factor × competitor_factor
    
    Constrained by:
        - Floor rate (never go below cost)
        - Ceiling rate (never go above market max)
        - Fare class fencing (different price for different segments)
    """

    # Occupancy thresholds that trigger pricing changes
    OCCUPANCY_TIERS = [
        (0.0, 0.30, 0.85),   # 0-30% occupancy → 15% discount (stimulate demand)
        (0.30, 0.50, 0.92),  # 30-50% → 8% discount
        (0.50, 0.65, 0.98),  # 50-65% → 2% discount
        (0.65, 0.75, 1.00),  # 65-75% → base rate
        (0.75, 0.85, 1.08),  # 75-85% → 8% premium
        (0.85, 0.92, 1.15),  # 85-92% → 15% premium
        (0.92, 1.00, 1.25),  # 92-100% → 25% premium (capture last-minute value)
    ]

    # Lead time multipliers (days until check-in)
    LEAD_TIME_TIERS = [
        (60, 999, 0.90),    # 60+ days out → early bird discount
        (30, 59, 0.94),     # 30-59 days → slight discount
        (21, 29, 0.97),     # 21-29 days → small discount
        (14, 20, 1.00),     # 14-20 days → base rate
        (7, 13, 1.05),      # 7-13 days → slight premium
        (3, 6, 1.12),       # 3-6 days → urgency premium
        (1, 2, 1.18),       # 1-2 days → strong premium
        (0, 0, 1.25),       # Same day → maximum premium
    ]

    # Day of week factors (Ethiopian hospitality patterns)
    DOW_FACTORS = {
        0: 0.90,  # Monday (low)
        1: 0.90,  # Tuesday (low)
        2: 0.93,  # Wednesday
        3: 0.95,  # Thursday (business picks up)
        4: 1.10,  # Friday (weekend starts)
        5: 1.20,  # Saturday (peak)
        6: 1.05,  # Sunday (checkout day)
    }

    # Monthly seasonality for Ethiopian resort
    MONTH_FACTORS = {
        1: 1.08,   # January — Timkat season
        2: 1.02,   # February
        3: 1.00,   # March
        4: 1.05,   # April — Easter season (Ethiopian)
        5: 0.92,   # May — early rains
        6: 0.85,   # June — heavy rain season
        7: 0.82,   # July — heavy rain
        8: 0.85,   # August — rain
        9: 0.95,   # September — Meskel festival
        10: 1.05,  # October — dry season starts
        11: 1.08,  # November — peak dry season
        12: 1.12,  # December — holiday peak + Genna
    }

    def __init__(self, db: Session):
        self.db = db

    def get_optimal_price(
        self,
        room_type_code: str,
        target_date: date,
        guest_nationality: Optional[str] = None,
        booking_channel: Optional[str] = None,
        lead_time_days: Optional[int] = None,
    ) -> Dict:
        """
        Calculate the optimal price for a room type on a specific date.
        Returns pricing for all fare classes with recommendations.
        """
        # Get room type
        room_type = self.db.query(RoomType).filter(
            RoomType.code == room_type_code
        ).first()
        if not room_type:
            raise ValueError(f"Room type '{room_type_code}' not found")

        # Get or create daily inventory
        inventory = self._get_or_create_inventory(room_type, target_date)

        # Calculate days until arrival
        if lead_time_days is None:
            lead_time_days = max(0, (target_date - date.today()).days)

        # --- STEP 1: Calculate base multipliers ---
        occupancy_factor = self._get_occupancy_factor(inventory.occupancy_rate)
        lead_time_factor = self._get_lead_time_factor(lead_time_days)
        dow_factor = self.DOW_FACTORS.get(target_date.weekday(), 1.0)
        month_factor = self.MONTH_FACTORS.get(target_date.month, 1.0)

        # --- STEP 2: Event and demand signals ---
        event_factor = self._get_event_factor(target_date)
        competitor_factor, competitor_avg = self._get_competitor_factor(
            room_type_code, target_date
        )

        # --- STEP 3: Combine all factors ---
        combined_multiplier = (
            occupancy_factor
            * lead_time_factor
            * dow_factor
            * month_factor
            * event_factor
            * competitor_factor
        )

        # --- STEP 4: Calculate fare class rates ---
        base_rate = room_type.base_rate_etb
        fare_classes = self._calculate_fare_class_rates(
            base_rate, combined_multiplier, room_type, inventory
        )

        # --- STEP 5: Determine recommended fare class ---
        recommended = self._recommend_fare_class(
            fare_classes, inventory, lead_time_days, guest_nationality
        )

        # --- STEP 6: Constrain to floor/ceiling ---
        for fc in fare_classes:
            fc["rate_etb"] = max(room_type.floor_rate_etb, 
                               min(room_type.ceiling_rate_etb, fc["rate_etb"]))
            fc["rate_usd"] = round(fc["rate_etb"] / 55.0, 2)  # ETB to USD approx

        # Build pricing reason
        reason = self._build_pricing_reason(
            occupancy_factor, lead_time_factor, dow_factor,
            month_factor, event_factor, competitor_factor,
            inventory.occupancy_rate, lead_time_days
        )

        # --- STEP 7: Write audit log (non-blocking) ---
        try:
            log = PricingLog(
                room_type_code=room_type_code,
                date=target_date,
                new_rate=recommended["rate_etb"],
                fare_class=recommended["fare_class"],
                occupancy_at_decision=inventory.occupancy_rate,
                days_until_arrival=lead_time_days,
                forecasted_demand=inventory.forecasted_demand,
                competitor_rate=competitor_avg,
                event_impact=event_factor,
                reason=reason,
                confidence=self._calculate_confidence(inventory),
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            self.db.rollback()  # Never let logging break pricing

        return {
            "room_type_code": room_type_code,
            "room_type_name": room_type.name,
            "date": target_date,
            "base_rate_etb": base_rate,
            "fare_classes": fare_classes,
            "recommended_fare_class": recommended["fare_class"],
            "recommended_rate_etb": recommended["rate_etb"],
            "recommended_rate_usd": round(recommended["rate_etb"] / 55.0, 2),
            "occupancy_rate": inventory.occupancy_rate,
            "demand_forecast": inventory.forecasted_demand,
            "competitor_avg_rate": competitor_avg,
            "ai_confidence": self._calculate_confidence(inventory),
            "pricing_reason": reason,
            "multiplier_breakdown": {
                "occupancy": occupancy_factor,
                "lead_time": lead_time_factor,
                "day_of_week": dow_factor,
                "seasonality": month_factor,
                "event": event_factor,
                "competitor": competitor_factor,
                "combined": combined_multiplier,
            }
        }

    def get_bulk_prices(
        self,
        room_type_codes: List[str],
        start_date: date,
        end_date: date,
        guest_nationality: Optional[str] = None,
    ) -> List[Dict]:
        """Get prices for multiple dates and room types (for heatmap/calendar)."""
        results = []
        current = start_date
        while current <= end_date:
            for code in room_type_codes:
                try:
                    price = self.get_optimal_price(
                        code, current, guest_nationality=guest_nationality
                    )
                    results.append(price)
                except Exception:
                    pass
            current += timedelta(days=1)
        return results

    def run_what_if(
        self,
        scenario_type: str,
        room_type_code: Optional[str],
        date_start: date,
        date_end: date,
        parameters: Dict,
    ) -> Dict:
        """
        Run a what-if simulation without modifying actual data.
        Scenarios: block_rooms, event, discount, competitor_change
        """
        baseline_revenue = 0.0
        projected_revenue = 0.0
        daily_breakdown = []

        room_types = [room_type_code] if room_type_code else [
            rt.code for rt in self.db.query(RoomType).all()
        ]

        current = date_start
        while current <= date_end:
            for code in room_types:
                # Baseline (current pricing)
                baseline = self.get_optimal_price(code, current)
                baseline_rev = baseline["recommended_rate_etb"]

                # Modified scenario
                modified_rev = baseline_rev
                if scenario_type == "block_rooms":
                    blocked = parameters.get("rooms_to_block", 10)
                    discount = parameters.get("discount_pct", 0.15)
                    # Blocking rooms increases occupancy for remaining
                    rt = self.db.query(RoomType).filter(RoomType.code == code).first()
                    if rt:
                        remaining = rt.total_count - blocked
                        group_rev = blocked * baseline_rev * (1 - discount)
                        inv = self._get_or_create_inventory(rt, current)
                        new_occ = min(1.0, inv.booked_rooms / max(1, remaining))
                        new_factor = self._get_occupancy_factor(new_occ)
                        individual_rev = remaining * baseline_rev * new_factor
                        modified_rev = (group_rev + individual_rev) / rt.total_count

                elif scenario_type == "event":
                    impact = parameters.get("demand_multiplier", 1.3)
                    modified_rev = baseline_rev * impact * 0.95  # Conservative

                elif scenario_type == "discount":
                    discount_pct = parameters.get("discount_pct", 0.10)
                    volume_increase = parameters.get("volume_increase_pct", 0.20)
                    modified_rev = baseline_rev * (1 - discount_pct) * (1 + volume_increase)

                elif scenario_type == "competitor_change":
                    competitor_change = parameters.get("competitor_rate_change_pct", -0.10)
                    # If competitor drops price, we might need to follow partially
                    our_adjustment = competitor_change * 0.5  # Follow 50%
                    modified_rev = baseline_rev * (1 + our_adjustment)

                baseline_revenue += baseline_rev
                projected_revenue += modified_rev

                daily_breakdown.append({
                    "date": current.isoformat(),
                    "room_type": code,
                    "baseline_rate": baseline_rev,
                    "projected_rate": modified_rev,
                    "delta": modified_rev - baseline_rev,
                })

            current += timedelta(days=1)

        delta = projected_revenue - baseline_revenue
        return {
            "scenario_description": f"{scenario_type} simulation",
            "baseline_revenue_etb": round(baseline_revenue, 2),
            "projected_revenue_etb": round(projected_revenue, 2),
            "revenue_delta_etb": round(delta, 2),
            "revenue_delta_pct": round(delta / max(1, baseline_revenue) * 100, 2),
            "occupancy_impact": parameters.get("volume_increase_pct", 0),
            "recommendations": self._generate_scenario_recommendations(
                scenario_type, delta, parameters
            ),
            "daily_breakdown": daily_breakdown,
        }

    # ==================== PRIVATE METHODS ====================

    def _get_occupancy_factor(self, occupancy_rate: float) -> float:
        """Map occupancy rate to price multiplier with smooth interpolation between tiers."""
        for i, (low, high, factor) in enumerate(self.OCCUPANCY_TIERS):
            if low <= occupancy_rate < high:
                # Interpolate toward the next tier's factor
                next_factor = self.OCCUPANCY_TIERS[i + 1][2] if i + 1 < len(self.OCCUPANCY_TIERS) else 1.5
                position = (occupancy_rate - low) / max(0.01, high - low)
                return round(factor + position * (next_factor - factor), 4)
        return 1.5  # occupancy >= 100%

    def _get_lead_time_factor(self, days: int) -> float:
        """Map lead time (days until check-in) to price multiplier."""
        for low, high, factor in self.LEAD_TIME_TIERS:
            if low <= days <= high:
                return factor
        return 0.80  # Far future = early bird

    def _get_event_factor(self, target_date: date) -> float:
        """Check if any events affect demand on this date."""
        events = self.db.query(Event).filter(
            Event.date_start <= target_date,
            Event.date_end >= target_date,
        ).all()

        if not events:
            return 1.0

        # Use the highest impact event
        max_multiplier = max(e.expected_demand_multiplier for e in events)
        return max_multiplier

    def _get_competitor_factor(
        self, room_type_code: str, target_date: date
    ) -> Tuple[float, Optional[float]]:
        """
        Adjust pricing based on competitor rates.
        If we're cheaper, raise a bit. If we're more expensive, don't drop below floor.
        """
        rates = self.db.query(CompetitorRate).filter(
            CompetitorRate.date == target_date,
            CompetitorRate.room_category == room_type_code,
        ).all()

        if not rates:
            return 1.0, None

        avg_rate = sum(r.rate_etb for r in rates) / len(rates)
        room_type = self.db.query(RoomType).filter(
            RoomType.code == room_type_code
        ).first()

        if not room_type:
            return 1.0, avg_rate

        our_base = room_type.base_rate_etb
        ratio = avg_rate / max(1, our_base)

        # Don't swing too much based on competitors
        if ratio > 1.2:
            return 1.08, avg_rate  # Competitors much higher → raise slightly
        elif ratio > 1.05:
            return 1.03, avg_rate
        elif ratio < 0.8:
            return 0.95, avg_rate  # Competitors much lower → drop slightly
        elif ratio < 0.95:
            return 0.98, avg_rate
        else:
            return 1.0, avg_rate

    def _calculate_fare_class_rates(
        self,
        base_rate: float,
        combined_multiplier: float,
        room_type: RoomType,
        inventory: DailyInventory,
    ) -> List[Dict]:
        """Calculate rates for each fare class (Saver, Standard, Premium)."""
        fare_config = settings.FARE_CLASSES
        result = []

        for fc_code, fc in fare_config.items():
            # Apply the multiplier to get the market rate, then apply fare class discount
            market_rate = base_rate * combined_multiplier
            rate = market_rate * (1 - fc["discount_pct"])

            # Get availability
            is_open = getattr(inventory, f"{fc_code}_open", True)
            sold = getattr(inventory, f"{fc_code}_sold", 0)
            total = getattr(inventory, f"{fc_code}_total", 0)
            remaining = max(0, total - sold)

            result.append({
                "fare_class": fc_code,
                "label": fc["label"],
                "rate_etb": round(rate, 2),
                "rate_usd": round(rate / 55.0, 2),
                "available": is_open and remaining > 0,
                "rooms_remaining": remaining,
                "discount_pct": fc["discount_pct"],
                "refundable": fc["refundable"],
                "changeable": fc["changeable"],
            })

        return result

    def _recommend_fare_class(
        self,
        fare_classes: List[Dict],
        inventory: DailyInventory,
        lead_time_days: int,
        guest_nationality: Optional[str],
    ) -> Dict:
        """Decide which fare class to recommend based on context."""
        available = [fc for fc in fare_classes if fc["available"]]
        if not available:
            # All sold out — return premium rate as walk-in
            return fare_classes[-1]  # Premium is last

        # International tourists → recommend standard or premium
        if guest_nationality and guest_nationality.lower() not in [
            "ethiopian", "ethiopia", "et"
        ]:
            for fc in available:
                if fc["fare_class"] in ["standard", "premium"]:
                    return fc

        # Early bookers → recommend saver
        if lead_time_days >= 21:
            for fc in available:
                if fc["fare_class"] == "saver":
                    return fc

        # Medium lead time → standard
        if lead_time_days >= 7:
            for fc in available:
                if fc["fare_class"] == "standard":
                    return fc

        # Last minute → premium
        for fc in available:
            if fc["fare_class"] == "premium":
                return fc

        return available[0]

    def _get_or_create_inventory(
        self, room_type: RoomType, target_date: date
    ) -> DailyInventory:
        """Get existing inventory record or create a new one."""
        inventory = self.db.query(DailyInventory).filter(
            DailyInventory.room_type_id == room_type.id,
            DailyInventory.date == target_date,
        ).first()

        if not inventory:
            fare_config = settings.FARE_CLASSES
            total = room_type.total_count
            inventory = DailyInventory(
                room_type_id=room_type.id,
                date=target_date,
                total_rooms=total,
                booked_rooms=0,
                blocked_rooms=0,
                available_rooms=total,
                occupancy_rate=0.0,
                saver_total=int(total * fare_config["saver"]["inventory_pct"]),
                saver_sold=0,
                saver_open=True,
                standard_total=int(total * fare_config["standard"]["inventory_pct"]),
                standard_sold=0,
                standard_open=True,
                premium_total=total - int(total * fare_config["saver"]["inventory_pct"]) - int(total * fare_config["standard"]["inventory_pct"]),
                premium_sold=0,
                premium_open=True,
                saver_rate=room_type.base_rate_etb * (1 - fare_config["saver"]["discount_pct"]),
                standard_rate=room_type.base_rate_etb * (1 - fare_config["standard"]["discount_pct"]),
                premium_rate=room_type.base_rate_etb * (1 + abs(fare_config["premium"]["discount_pct"])),
            )
            self.db.add(inventory)
            self.db.commit()
            self.db.refresh(inventory)

        return inventory

    def _calculate_confidence(self, inventory: DailyInventory) -> float:
        """
        Calculate AI confidence in the pricing recommendation.
        Higher confidence when we have more data signals.
        """
        score = 0.5  # Base confidence

        if inventory.forecasted_demand is not None:
            score += 0.15
        if inventory.competitor_avg_rate is not None:
            score += 0.10
        if inventory.booked_rooms > 0:
            score += 0.10  # We have real booking data
        if inventory.occupancy_rate > 0.3:
            score += 0.05  # Enough data to make strong prediction

        return min(0.95, round(score, 2))

    def _build_pricing_reason(
        self,
        occ_factor: float, lt_factor: float, dow_factor: float,
        month_factor: float, event_factor: float, comp_factor: float,
        occupancy: float, lead_time: int,
    ) -> str:
        """Build a human-readable explanation of the pricing decision."""
        reasons = []

        if occupancy > 0.85:
            reasons.append(f"High occupancy ({occupancy:.0%}) driving premium pricing")
        elif occupancy < 0.30:
            reasons.append(f"Low occupancy ({occupancy:.0%}) — stimulating demand with lower rates")

        if lead_time <= 2:
            reasons.append("Last-minute booking premium applied")
        elif lead_time >= 30:
            reasons.append("Early booking discount available")

        if event_factor > 1.1:
            reasons.append(f"Local event increasing demand (×{event_factor:.2f})")

        if dow_factor >= 1.10:
            reasons.append("Weekend premium applied")
        elif dow_factor <= 0.90:
            reasons.append("Weekday rate discount")

        if month_factor >= 1.15:
            reasons.append("Peak season surcharge")
        elif month_factor <= 0.75:
            reasons.append("Rainy season discount")

        if comp_factor != 1.0:
            direction = "above" if comp_factor > 1.0 else "below"
            reasons.append(f"Competitor rates trending {direction} average")

        return ". ".join(reasons) if reasons else "Standard rate based on market conditions."

    def _generate_scenario_recommendations(
        self, scenario_type: str, delta: float, parameters: Dict
    ) -> List[str]:
        """Generate actionable recommendations for what-if scenarios."""
        recs = []
        if delta > 0:
            recs.append(f"This scenario projects +{delta:,.0f} ETB additional revenue")
            recs.append("Consider implementing this change")
        else:
            recs.append(f"This scenario projects {delta:,.0f} ETB revenue impact")
            recs.append("Consider adjusting parameters to minimize negative impact")

        if scenario_type == "block_rooms":
            recs.append("Ensure remaining inventory is repriced upward after blocking")
        elif scenario_type == "event":
            recs.append("Close Saver fare class and shift inventory to Standard/Premium")
        elif scenario_type == "discount":
            recs.append("Target discount to specific channels (OTA or direct) for best results")

        return recs
