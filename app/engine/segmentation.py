"""
Guest Segmentation Engine

Classifies guests into segments based on booking characteristics.
Used to:
1. Recommend the right package
2. Set the right discount level
3. Choose the right fare class
"""
from typing import Optional, Dict
from datetime import date


class GuestSegmenter:
    """
    Rule-based segmentation with ML override capability.
    
    Segments:
    - international_leisure: Foreign tourists, 2+ nights, leisure patterns
    - domestic_weekend: Ethiopian guests, Fri-Sun, family/couple
    - business: Corporate email/phone, weekday stays, short
    - honeymoon: Couple, suite/deluxe, weekend+ stay
    - family: 2+ adults, children present
    - group_tour: 5+ rooms, international
    - conference: Corporate, large group, weekday
    - long_stay: 5+ nights
    """

    def classify(
        self,
        nationality: str = "Ethiopian",
        is_corporate: bool = False,
        adults: int = 1,
        children: int = 0,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        room_type_code: str = "standard",
        booking_channel: str = "direct",
        company_name: Optional[str] = None,
        group_size: int = 1,
    ) -> Dict:
        """
        Classify a guest into a segment based on booking characteristics.
        Returns segment code, confidence, and reasoning.
        """
        is_international = nationality.lower() not in [
            "ethiopian", "ethiopia", "et", "eth"
        ]

        nights = 1
        if check_in and check_out:
            nights = (check_out - check_in).days

        is_weekend = False
        if check_in:
            is_weekend = check_in.weekday() >= 4  # Friday or later

        has_children = children > 0
        is_couple = adults == 2 and children == 0
        is_premium_room = room_type_code in ["suite", "royal_suite", "deluxe"]

        # --- Classification Logic (priority order) ---

        # Conference / Group
        if is_corporate and group_size >= 5:
            return {
                "segment": "conference",
                "confidence": 0.90,
                "reason": f"Corporate booking with {group_size} rooms, likely conference"
            }

        # Group tour
        if is_international and group_size >= 5:
            return {
                "segment": "group_tour",
                "confidence": 0.85,
                "reason": f"International group of {group_size}, likely tour group"
            }

        # Long stay
        if nights >= 5:
            return {
                "segment": "long_stay",
                "confidence": 0.80,
                "reason": f"{nights}-night stay qualifies as long stay"
            }

        # Honeymoon
        if is_couple and is_premium_room and nights >= 2:
            return {
                "segment": "honeymoon",
                "confidence": 0.75,
                "reason": "Couple in premium room, weekend+ stay suggests honeymoon/romantic"
            }

        # Business
        if is_corporate or (not is_weekend and nights <= 3 and not has_children):
            if is_corporate:
                return {
                    "segment": "business",
                    "confidence": 0.85,
                    "reason": f"Corporate booking ({company_name or 'company'})"
                }
            elif not is_weekend and adults == 1:
                return {
                    "segment": "business",
                    "confidence": 0.65,
                    "reason": "Solo weekday traveler, likely business"
                }

        # Family
        if has_children:
            return {
                "segment": "family",
                "confidence": 0.85,
                "reason": f"Family with {children} children"
            }

        # International leisure
        if is_international:
            return {
                "segment": "international_leisure",
                "confidence": 0.80,
                "reason": f"International guest from {nationality}"
            }

        # Domestic weekend
        if is_weekend:
            return {
                "segment": "domestic_weekend",
                "confidence": 0.75,
                "reason": "Domestic guest, weekend booking"
            }

        # Default: domestic leisure
        return {
            "segment": "domestic_weekend",
            "confidence": 0.50,
            "reason": "Default classification — domestic guest"
        }

    def get_segment_profile(self, segment: str) -> Dict:
        """Get the typical profile and behavior pattern for a segment."""
        profiles = {
            "international_leisure": {
                "label": "International Leisure",
                "avg_nights": 3.5,
                "avg_lead_time": 35,
                "price_sensitivity": "low",
                "package_affinity": "high",
                "preferred_packages": ["romance_escape", "cultural_experience", "adventure"],
                "preferred_channels": ["ota_booking", "ota_expedia", "direct"],
                "avg_daily_spend_etb": 8500,
                "typical_room": "deluxe",
            },
            "domestic_weekend": {
                "label": "Domestic Weekend",
                "avg_nights": 2.0,
                "avg_lead_time": 7,
                "price_sensitivity": "medium",
                "package_affinity": "medium",
                "preferred_packages": ["family_getaway", "weekend_wellness"],
                "preferred_channels": ["direct", "phone"],
                "avg_daily_spend_etb": 5500,
                "typical_room": "standard",
            },
            "business": {
                "label": "Business Traveler",
                "avg_nights": 2.0,
                "avg_lead_time": 5,
                "price_sensitivity": "very_low",
                "package_affinity": "low",
                "preferred_packages": ["business_express"],
                "preferred_channels": ["corporate", "direct"],
                "avg_daily_spend_etb": 7000,
                "typical_room": "standard",
            },
            "honeymoon": {
                "label": "Honeymoon / Romantic",
                "avg_nights": 3.0,
                "avg_lead_time": 25,
                "price_sensitivity": "low",
                "package_affinity": "very_high",
                "preferred_packages": ["honeymoon_bliss", "romance_escape"],
                "preferred_channels": ["direct", "travel_agent"],
                "avg_daily_spend_etb": 12000,
                "typical_room": "suite",
            },
            "family": {
                "label": "Family",
                "avg_nights": 2.5,
                "avg_lead_time": 14,
                "price_sensitivity": "medium",
                "package_affinity": "high",
                "preferred_packages": ["family_getaway", "adventure"],
                "preferred_channels": ["direct", "phone"],
                "avg_daily_spend_etb": 7500,
                "typical_room": "deluxe",
            },
            "group_tour": {
                "label": "Group Tour",
                "avg_nights": 2.0,
                "avg_lead_time": 45,
                "price_sensitivity": "high",
                "package_affinity": "very_high",
                "preferred_packages": ["cultural_experience"],
                "preferred_channels": ["travel_agent"],
                "avg_daily_spend_etb": 4500,
                "typical_room": "standard",
            },
            "conference": {
                "label": "Conference / Corporate Group",
                "avg_nights": 3.0,
                "avg_lead_time": 30,
                "price_sensitivity": "low",
                "package_affinity": "medium",
                "preferred_packages": ["conference_package"],
                "preferred_channels": ["corporate"],
                "avg_daily_spend_etb": 9000,
                "typical_room": "standard",
            },
            "long_stay": {
                "label": "Long Stay Guest",
                "avg_nights": 7.0,
                "avg_lead_time": 20,
                "price_sensitivity": "high",
                "package_affinity": "high",
                "preferred_packages": ["long_stay"],
                "preferred_channels": ["direct"],
                "avg_daily_spend_etb": 5000,
                "typical_room": "standard",
            },
        }
        return profiles.get(segment, profiles["domestic_weekend"])
