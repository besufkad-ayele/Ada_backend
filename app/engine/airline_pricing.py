"""
Airline-Style Revenue Management Pricing Engine
Based on classic airline yield management principles
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple
import random


class AirlineStylePricingEngine:
    """
    Implements airline-style dynamic pricing with:
    - Time-based discount buckets
    - Inventory-based pricing tiers
    - Fencing rules (limited inventory per discount level)
    """
    
    # Static pricing table (Phase 1 - Rule-based)
    # Format: (time_bucket, inventory_bucket) -> (discount_pct, inventory_extent_pct)
    PRICING_TABLE = {
        # Time bucket: >1 month (>30 days)
        (">30", "0-15"): (10.0, 15.0),    # 10% discount, up to 15% of inventory
        (">30", "15-30"): (5.0, 15.0),    # 5% discount, from 15-30% inventory
        (">30", "30-40"): (0.0, 0.0),     # No discount
        (">30", ">40"): (0.0, 0.0),       # No discount
        
        # Time bucket: 1 month - 2 weeks (30-14 days)
        ("30-14", "0-15"): (10.0, 20.0),  # 10% discount, up to 20% of inventory
        ("30-14", "15-30"): (5.0, 15.0),  # 5% discount, from 15-30% inventory
        ("30-14", "30-40"): (2.5, 20.0),  # 2.5% discount, from 40-60% inventory
        ("30-14", ">40"): (0.0, 0.0),     # No discount
        
        # Time bucket: 2 weeks - 1 week (14-7 days)
        ("14-7", "0-15"): (10.0, 25.0),   # 10% discount, up to 25% of inventory
        ("14-7", "15-30"): (5.0, 20.0),   # 5% discount, from 20-40% inventory
        ("14-7", "30-40"): (2.5, 25.0),   # 2.5% discount, from 50-75% inventory
        ("14-7", ">40"): (0.0, 0.0),      # No discount
        
        # Time bucket: <1 week (<7 days)
        ("<7", "0-15"): (5.0, 50.0),      # 5% discount, up to 50% of inventory
        ("<7", "15-30"): (2.5, 25.0),     # 2.5% discount, from 50-75% inventory
        ("<7", "30-40"): (1.25, 5.0),     # 1.25% discount, from 75-80% inventory
        ("<7", ">40"): (0.0, 0.0),        # No discount
    }
    
    def __init__(self, base_rate: float, total_rooms: int):
        """
        Initialize pricing engine
        
        Args:
            base_rate: Base room rate (rack rate)
            total_rooms: Total number of rooms available
        """
        self.base_rate = base_rate
        self.total_rooms = total_rooms
    
    def get_time_bucket(self, days_until_arrival: int) -> str:
        """Classify booking into time bucket"""
        if days_until_arrival > 30:
            return ">30"
        elif days_until_arrival >= 14:
            return "30-14"
        elif days_until_arrival >= 7:
            return "14-7"
        else:
            return "<7"
    
    def get_inventory_bucket(self, occupancy_pct: float) -> str:
        """Classify current inventory into bucket"""
        if occupancy_pct < 15:
            return "0-15"
        elif occupancy_pct < 30:
            return "15-30"
        elif occupancy_pct < 40:
            return "30-40"
        else:
            return ">40"
    
    def calculate_price(
        self,
        check_in_date: datetime,
        current_occupancy_pct: float,
        is_weekend: bool = False,
        is_holiday: bool = False,
        demand_multiplier: float = 1.0
    ) -> Dict:
        """
        Calculate optimized price using airline-style logic
        
        Args:
            check_in_date: Date of check-in
            current_occupancy_pct: Current occupancy percentage (0-100)
            is_weekend: Whether check-in is on weekend
            is_holiday: Whether check-in is during holiday period
            demand_multiplier: AI-predicted demand multiplier (1.0 = normal)
        
        Returns:
            Dictionary with pricing details
        """
        # Calculate days until arrival
        days_until_arrival = (check_in_date - datetime.now()).days
        
        # Get buckets
        time_bucket = self.get_time_bucket(days_until_arrival)
        inventory_bucket = self.get_inventory_bucket(current_occupancy_pct)
        
        # Get discount from table
        discount_pct, inventory_extent = self.PRICING_TABLE.get(
            (time_bucket, inventory_bucket),
            (0.0, 0.0)
        )
        
        # Apply special conditions
        # Weekend premium (reduce discount or add premium)
        if is_weekend:
            discount_pct = max(0, discount_pct - 2.5)  # Reduce discount by 2.5%
            weekend_premium = 1.08
        else:
            weekend_premium = 1.0
        
        # Holiday premium (no discounts during holidays)
        if is_holiday:
            discount_pct = 0.0
            holiday_premium = 1.15
        else:
            holiday_premium = 1.0
        
        # AI demand adjustment (Phase 2+)
        # If AI predicts high demand, reduce discount
        if demand_multiplier > 1.2:
            discount_pct = max(0, discount_pct - 5.0)
        elif demand_multiplier < 0.8:
            discount_pct = min(15.0, discount_pct + 3.0)
        
        # Calculate final rate
        discount_multiplier = 1.0 - (discount_pct / 100)
        optimized_rate = (
            self.base_rate * 
            discount_multiplier * 
            weekend_premium * 
            holiday_premium * 
            demand_multiplier
        )
        
        # Round to 2 decimals
        optimized_rate = round(optimized_rate, 2)
        
        # Calculate savings
        savings = self.base_rate - optimized_rate
        savings_pct = (savings / self.base_rate) * 100 if savings > 0 else 0
        
        return {
            "base_rate": self.base_rate,
            "optimized_rate": optimized_rate,
            "discount_applied_pct": discount_pct,
            "savings_etb": round(savings, 2),
            "savings_pct": round(savings_pct, 2),
            "pricing_factors": {
                "time_bucket": time_bucket,
                "inventory_bucket": inventory_bucket,
                "days_until_arrival": days_until_arrival,
                "current_occupancy_pct": round(current_occupancy_pct, 1),
                "inventory_extent_pct": inventory_extent,
                "weekend_premium": weekend_premium,
                "holiday_premium": holiday_premium,
                "demand_multiplier": demand_multiplier,
            },
            "fare_class": self._get_fare_class(discount_pct),
            "restrictions": self._get_restrictions(discount_pct),
        }
    
    def _get_fare_class(self, discount_pct: float) -> str:
        """Determine fare class based on discount"""
        if discount_pct >= 10:
            return "SAVER"  # Deep discount, most restrictions
        elif discount_pct >= 5:
            return "STANDARD"  # Moderate discount, some restrictions
        elif discount_pct > 0:
            return "FLEX"  # Small discount, few restrictions
        else:
            return "PREMIUM"  # No discount, fully flexible
    
    def _get_restrictions(self, discount_pct: float) -> Dict:
        """Define booking restrictions based on discount level"""
        if discount_pct >= 10:
            return {
                "refundable": False,
                "changeable": False,
                "prepayment_required": True,
                "cancellation_fee_pct": 100,
                "change_fee_etb": 0,  # Not changeable
            }
        elif discount_pct >= 5:
            return {
                "refundable": False,
                "changeable": True,
                "prepayment_required": True,
                "cancellation_fee_pct": 50,
                "change_fee_etb": 500,
            }
        elif discount_pct > 0:
            return {
                "refundable": True,
                "changeable": True,
                "prepayment_required": False,
                "cancellation_fee_pct": 25,
                "change_fee_etb": 250,
            }
        else:
            return {
                "refundable": True,
                "changeable": True,
                "prepayment_required": False,
                "cancellation_fee_pct": 0,
                "change_fee_etb": 0,
            }
    
    def get_available_fare_classes(
        self,
        check_in_date: datetime,
        current_occupancy_pct: float,
        rooms_remaining: int
    ) -> list:
        """
        Get all available fare classes with inventory fencing
        (Like airline booking classes: Y, B, M, Q, etc.)
        
        Returns list of fare classes with prices and availability
        """
        base_pricing = self.calculate_price(check_in_date, current_occupancy_pct)
        
        fare_classes = []
        
        # SAVER class (if discount >= 10%)
        if base_pricing["discount_applied_pct"] >= 10:
            inventory_extent = base_pricing["pricing_factors"]["inventory_extent_pct"]
            available_rooms = int((inventory_extent / 100) * self.total_rooms)
            available_rooms = min(available_rooms, rooms_remaining)
            
            if available_rooms > 0:
                fare_classes.append({
                    "class": "SAVER",
                    "rate": base_pricing["optimized_rate"],
                    "discount_pct": base_pricing["discount_applied_pct"],
                    "available_rooms": available_rooms,
                    "restrictions": base_pricing["restrictions"],
                    "description": "Best Value - Non-refundable, Prepay Required"
                })
        
        # STANDARD class (if discount >= 5%)
        if base_pricing["discount_applied_pct"] >= 5:
            fare_classes.append({
                "class": "STANDARD",
                "rate": round(self.base_rate * 0.95, 2),
                "discount_pct": 5.0,
                "available_rooms": rooms_remaining,
                "restrictions": self._get_restrictions(5.0),
                "description": "Good Value - Limited Changes"
            })
        
        # FLEX class (small discount)
        fare_classes.append({
            "class": "FLEX",
            "rate": round(self.base_rate * 0.975, 2),
            "discount_pct": 2.5,
            "available_rooms": rooms_remaining,
            "restrictions": self._get_restrictions(2.5),
            "description": "Flexible - Free Cancellation"
        })
        
        # PREMIUM class (rack rate)
        fare_classes.append({
            "class": "PREMIUM",
            "rate": self.base_rate,
            "discount_pct": 0.0,
            "available_rooms": rooms_remaining,
            "restrictions": self._get_restrictions(0.0),
            "description": "Fully Flexible - No Restrictions"
        })
        
        return fare_classes


class AIEnhancedPricingEngine(AirlineStylePricingEngine):
    """
    Phase 2+: AI-enhanced version that learns and optimizes
    beyond the static table
    """
    
    def __init__(self, base_rate: float, total_rooms: int):
        super().__init__(base_rate, total_rooms)
        self.learning_enabled = True
        self.optimization_history = []
    
    def predict_demand(
        self,
        check_in_date: datetime,
        historical_data: list = None
    ) -> float:
        """
        Phase 2: ML-based demand prediction
        
        Returns demand multiplier (1.0 = normal, >1.0 = high, <1.0 = low)
        """
        # TODO: Implement ML model (Prophet, LSTM, XGBoost)
        # For now, use simple heuristics
        
        day_of_week = check_in_date.weekday()
        month = check_in_date.month
        
        # Weekend boost
        if day_of_week >= 4:  # Fri, Sat, Sun
            demand = 1.2
        else:
            demand = 1.0
        
        # Seasonal adjustment (Ethiopian context)
        if month in [9, 10]:  # Meskel, Ethiopian New Year
            demand *= 1.3
        elif month in [1, 7]:  # Timkat, Summer
            demand *= 1.15
        elif month in [3, 4, 5]:  # Rainy season
            demand *= 0.85
        
        return demand
    
    def optimize_price(
        self,
        check_in_date: datetime,
        current_occupancy_pct: float,
        predicted_demand: float = None
    ) -> Dict:
        """
        Phase 3: AI optimization that can override static table
        """
        if predicted_demand is None:
            predicted_demand = self.predict_demand(check_in_date)
        
        # Get base pricing from static table
        base_pricing = self.calculate_price(
            check_in_date,
            current_occupancy_pct,
            demand_multiplier=predicted_demand
        )
        
        # AI can override here based on learning
        # For now, just use the base pricing
        
        return base_pricing
    
    def record_outcome(
        self,
        booking_date: datetime,
        check_in_date: datetime,
        price_offered: float,
        was_booked: bool,
        final_occupancy: float = None
    ):
        """
        Phase 4: Learning - record outcomes for future optimization
        """
        self.optimization_history.append({
            "booking_date": booking_date,
            "check_in_date": check_in_date,
            "price_offered": price_offered,
            "was_booked": was_booked,
            "final_occupancy": final_occupancy,
        })
        
        # TODO: Implement reinforcement learning
        # Update pricing table weights based on outcomes
