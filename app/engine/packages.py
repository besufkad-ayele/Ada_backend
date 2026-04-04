"""
Package Recommendation Engine

AI-powered system that:
1. Takes a guest's booking context
2. Identifies their segment
3. Recommends the optimal package
4. Dynamically sets the discount percentage

The packages are pre-defined (10 bundles).
The AI picks WHICH package and WHAT discount.
"""
from typing import Optional, List, Dict
from datetime import date
from sqlalchemy.orm import Session

from app.models.packages import Package, PackageComponent
from app.models.rooms import DailyInventory, RoomType
from app.engine.segmentation import GuestSegmenter


class PackageRecommender:
    """
    Recommends the best package for each guest based on:
    - Guest segment
    - Current occupancy (high occupancy = lower discount needed)
    - Lead time
    - Room rate already charged
    - Package historical acceptance rate
    """

    def __init__(self, db: Session):
        self.db = db
        self.segmenter = GuestSegmenter()

    def recommend(
        self,
        guest_nationality: str = "Ethiopian",
        is_corporate: bool = False,
        adults: int = 1,
        children: int = 0,
        check_in: date = None,
        check_out: date = None,
        room_type_code: str = "standard",
        booking_channel: str = "direct",
        room_rate_etb: float = 0.0,
    ) -> Dict:
        """
        Get the top package recommendation with dynamic pricing.
        """
        # Step 1: Classify the guest
        segment_result = self.segmenter.classify(
            nationality=guest_nationality,
            is_corporate=is_corporate,
            adults=adults,
            children=children,
            check_in=check_in,
            check_out=check_out,
            room_type_code=room_type_code,
            booking_channel=booking_channel,
        )
        segment = segment_result["segment"]
        profile = self.segmenter.get_segment_profile(segment)

        # Step 2: Find matching packages
        all_packages = self.db.query(Package).filter(
            Package.is_active == True
        ).all()

        if not all_packages:
            return {
                "guest_segment": segment,
                "top_recommendation": None,
                "alternatives": [],
                "estimated_acceptance_rate": 0.0,
            }

        # Step 3: Score and rank packages
        scored = []
        nights = (check_out - check_in).days if check_in and check_out else 1

        for pkg in all_packages:
            score = self._score_package(pkg, segment, profile, nights)
            if score > 0:
                discount_pct = self._calculate_discount(
                    pkg, segment, profile, room_type_code, check_in
                )
                recommendation = self._build_recommendation(
                    pkg, discount_pct, room_rate_etb, nights
                )
                recommendation["_score"] = score
                scored.append(recommendation)

        # Sort by score descending
        scored.sort(key=lambda x: x["_score"], reverse=True)

        # Remove internal score
        for s in scored:
            del s["_score"]

        top = scored[0] if scored else None
        alternatives = scored[1:3] if len(scored) > 1 else []

        return {
            "guest_segment": segment,
            "segment_label": profile["label"],
            "segment_confidence": segment_result["confidence"],
            "segment_reason": segment_result["reason"],
            "top_recommendation": top,
            "alternatives": alternatives,
            "estimated_acceptance_rate": self._estimate_acceptance(
                segment, profile
            ),
        }

    def _score_package(
        self, package: Package, segment: str, profile: Dict, nights: int
    ) -> float:
        """
        Score a package for a given segment. Higher = better match.

        Factors:
        - Segment match (is this package designed for this segment?)
        - Historical acceptance rate
        - Night requirement match
        - Revenue uplift potential
        """
        score = 0.0

        # Segment match (biggest factor)
        target_segments = package.target_segments.split(",")
        if segment in target_segments:
            score += 50.0
        elif any(s.strip() in profile.get("preferred_packages", [])
                 for s in [package.code]):
            score += 30.0
        else:
            score += 5.0  # Still possible, just not ideal

        # Night requirement
        if package.min_nights <= nights <= package.max_nights:
            score += 15.0
        elif nights < package.min_nights:
            return 0  # Can't offer this package

        # Historical acceptance rate
        if package.acceptance_rate > 0:
            score += package.acceptance_rate * 20.0  # 0-20 points

        # Revenue uplift potential
        if package.avg_revenue_uplift_etb > 0:
            score += min(15.0, package.avg_revenue_uplift_etb / 500.0)

        return score

    def _calculate_discount(
        self,
        package: Package,
        segment: str,
        profile: Dict,
        room_type_code: str,
        check_in: Optional[date],
    ) -> float:
        """
        Dynamically calculate the discount percentage for this package.

        Rules:
        - Price-sensitive segments (domestic, group) → higher discount
        - Price-insensitive segments (business, honeymoon) → lower discount
        - High occupancy → lower discount (rooms will sell anyway)
        - Low occupancy → higher discount (incentivize ancillary spend)
        """
        # Start with mid-range
        discount = (package.min_discount_pct + package.max_discount_pct) / 2

        # Adjust by price sensitivity
        sensitivity = profile.get("price_sensitivity", "medium")
        if sensitivity == "very_low":
            discount = package.min_discount_pct  # Business: tiny discount
        elif sensitivity == "low":
            discount = package.min_discount_pct + (package.max_discount_pct - package.min_discount_pct) * 0.25
        elif sensitivity == "high":
            discount = package.min_discount_pct + (package.max_discount_pct - package.min_discount_pct) * 0.75
        elif sensitivity == "medium":
            discount = (package.min_discount_pct + package.max_discount_pct) / 2

        # Check occupancy if available
        if check_in:
            room_type = self.db.query(RoomType).filter(
                RoomType.code == room_type_code
            ).first()
            if room_type:
                inventory = self.db.query(DailyInventory).filter(
                    DailyInventory.room_type_id == room_type.id,
                    DailyInventory.date == check_in,
                ).first()
                if inventory and inventory.occupancy_rate > 0.75:
                    # High occupancy → reduce discount
                    discount *= 0.7
                elif inventory and inventory.occupancy_rate < 0.40:
                    # Low occupancy → increase discount to drive ancillary
                    discount = min(package.max_discount_pct, discount * 1.3)

        return round(max(package.min_discount_pct, min(package.max_discount_pct, discount)), 2)

    def _build_recommendation(
        self,
        package: Package,
        discount_pct: float,
        room_rate_etb: float,
        nights: int,
    ) -> Dict:
        """Build a complete recommendation with pricing breakdown."""
        components = self.db.query(PackageComponent).filter(
            PackageComponent.package_id == package.id
        ).all()

        individual_total = sum(c.retail_price_etb * c.quantity for c in components)
        package_price = individual_total * (1 - discount_pct)
        savings = individual_total - package_price
        room_total = room_rate_etb * nights
        revenue_uplift = package_price  # Additional revenue vs room-only

        return {
            "package_code": package.code,
            "package_name": package.name,
            "description": package.description or "",
            "components": [
                {
                    "service_name": c.service_name,
                    "service_category": c.service_category,
                    "description": c.description,
                    "retail_price_etb": c.retail_price_etb,
                    "quantity": c.quantity,
                }
                for c in components
            ],
            "individual_total_etb": round(individual_total, 2),
            "package_price_etb": round(package_price, 2),
            "discount_pct": discount_pct,
            "savings_etb": round(savings, 2),
            "revenue_uplift_etb": round(revenue_uplift, 2),
            "confidence": 0.75,
            "reason": f"Best match for guest segment. {discount_pct:.0%} discount applied based on price sensitivity and demand.",
            "room_total_etb": round(room_total, 2),
            "package_total_etb": round(package_price, 2),
            "combined_total_etb": round(room_total + package_price, 2),
        }

    def _estimate_acceptance(self, segment: str, profile: Dict) -> float:
        """Estimate the probability this guest accepts a package."""
        affinity = profile.get("package_affinity", "medium")
        rates = {
            "very_high": 0.80,
            "high": 0.65,
            "medium": 0.45,
            "low": 0.25,
        }
        return rates.get(affinity, 0.40)
