"""
Ethiopian Calendar & Events Module

Provides:
- Major Ethiopian holidays and festivals
- Ethiopian calendar awareness (Ge'ez calendar is ~7-8 years behind Gregorian)
- Seasonal patterns specific to Ethiopian hospitality
"""
from datetime import date, timedelta
from typing import List, Dict


def get_ethiopian_holidays(year: int) -> List[Dict]:
    """
    Get major Ethiopian holidays for a given Gregorian year.
    These holidays significantly impact resort demand.
    
    Note: Ethiopian holidays follow the Ge'ez calendar.
    Some dates shift by a day or two depending on the year.
    These are approximate Gregorian equivalents.
    """
    holidays = [
        # Fixed Gregorian-approximate dates
        {
            "name": "Genna (Ethiopian Christmas)",
            "date_start": date(year, 1, 7),
            "date_end": date(year, 1, 8),
            "event_type": "holiday",
            "impact_level": 5,
            "demand_multiplier": 1.25,
            "is_national": True,
            "description": "Ethiopian Christmas. Major family celebration. Resorts fully booked."
        },
        {
            "name": "Timkat (Epiphany)",
            "date_start": date(year, 1, 19),
            "date_end": date(year, 1, 20),
            "event_type": "festival",
            "impact_level": 5,
            "demand_multiplier": 1.30,
            "is_national": True,
            "description": "Biggest Ethiopian festival. UNESCO heritage. Massive tourism influx."
        },
        {
            "name": "Adwa Victory Day",
            "date_start": date(year, 3, 2),
            "date_end": date(year, 3, 2),
            "event_type": "holiday",
            "impact_level": 3,
            "demand_multiplier": 1.15,
            "is_national": True,
            "description": "National holiday celebrating the Battle of Adwa."
        },
        {
            "name": "Ethiopian Good Friday (Siqlet)",
            "date_start": date(year, 4, 18),
            "date_end": date(year, 4, 18),
            "event_type": "holiday",
            "impact_level": 4,
            "demand_multiplier": 1.10,
            "is_national": True,
            "description": "Ethiopian Orthodox Good Friday."
        },
        {
            "name": "Ethiopian Easter (Fasika)",
            "date_start": date(year, 4, 20),
            "date_end": date(year, 4, 21),
            "event_type": "holiday",
            "impact_level": 5,
            "demand_multiplier": 1.22,
            "is_national": True,
            "description": "Easter celebration. Major family gatherings and travel."
        },
        {
            "name": "International Labor Day",
            "date_start": date(year, 5, 1),
            "date_end": date(year, 5, 1),
            "event_type": "holiday",
            "impact_level": 2,
            "demand_multiplier": 1.10,
            "is_national": True,
            "description": "Workers day. Long weekend travel."
        },
        {
            "name": "Patriots Victory Day",
            "date_start": date(year, 5, 5),
            "date_end": date(year, 5, 5),
            "event_type": "holiday",
            "impact_level": 3,
            "demand_multiplier": 1.10,
            "is_national": True,
            "description": "Commemorates liberation from Italian occupation."
        },
        {
            "name": "Downfall of the Derg",
            "date_start": date(year, 5, 28),
            "date_end": date(year, 5, 28),
            "event_type": "holiday",
            "impact_level": 2,
            "demand_multiplier": 1.05,
            "is_national": True,
            "description": "End of Derg regime commemoration."
        },
        {
            "name": "Enkutatash (Ethiopian New Year)",
            "date_start": date(year, 9, 11),
            "date_end": date(year, 9, 12),
            "event_type": "festival",
            "impact_level": 5,
            "demand_multiplier": 1.25,
            "is_national": True,
            "description": "Ethiopian New Year. Spring flowers, celebrations, family travel."
        },
        {
            "name": "Meskel (Finding of the True Cross)",
            "date_start": date(year, 9, 27),
            "date_end": date(year, 9, 28),
            "event_type": "festival",
            "impact_level": 5,
            "demand_multiplier": 1.20,
            "is_national": True,
            "description": "Meskel festival with bonfires. UNESCO heritage event."
        },
        {
            "name": "Eid al-Fitr (approximate)",
            "date_start": date(year, 4, 10),
            "date_end": date(year, 4, 11),
            "event_type": "holiday",
            "impact_level": 4,
            "demand_multiplier": 1.18,
            "is_national": True,
            "description": "End of Ramadan. Major celebration for Ethiopian Muslims."
        },
        {
            "name": "Eid al-Adha (approximate)",
            "date_start": date(year, 6, 17),
            "date_end": date(year, 6, 18),
            "event_type": "holiday",
            "impact_level": 4,
            "demand_multiplier": 1.15,
            "is_national": True,
            "description": "Feast of Sacrifice. Family celebrations."
        },
        {
            "name": "Mawlid (Prophet's Birthday, approximate)",
            "date_start": date(year, 9, 15),
            "date_end": date(year, 9, 15),
            "event_type": "holiday",
            "impact_level": 3,
            "demand_multiplier": 1.15,
            "is_national": True,
            "description": "Prophet Muhammad's birthday."
        },
    ]

    # Add seasonal events
    holidays.extend([
        {
            "name": "Holiday Season (Christmas-New Year)",
            "date_start": date(year, 12, 20),
            "date_end": date(year, 12, 31),
            "event_type": "cultural",
            "impact_level": 4,
            "demand_multiplier": 1.20,
            "is_national": True,
            "description": "International holiday season. International tourist peak."
        },
        {
            "name": "Great Ethiopian Run",
            "date_start": date(year, 11, 24),
            "date_end": date(year, 11, 24),
            "event_type": "sport",
            "impact_level": 3,
            "demand_multiplier": 1.25,
            "is_national": True,
            "description": "Largest road race in Africa. International participants."
        },
    ])

    return holidays


def get_competitor_resorts() -> List[Dict]:
    """Ethiopian resort competitors for rate benchmarking."""
    return [
        {
            "name": "Kuriftu Resort & Spa",
            "location": "Bishoftu",
            "standard_rate_etb": 5500,
            "deluxe_rate_etb": 8500,
            "suite_rate_etb": 14000,
            "tier": "luxury"
        },
        {
            "name": "Haile Resort",
            "location": "Multiple",
            "standard_rate_etb": 4000,
            "deluxe_rate_etb": 6500,
            "suite_rate_etb": 10000,
            "tier": "upper_midscale"
        },
        {
            "name": "Lewi Resort",
            "location": "Hawassa",
            "standard_rate_etb": 3800,
            "deluxe_rate_etb": 6000,
            "suite_rate_etb": 9500,
            "tier": "upper_midscale"
        },
        {
            "name": "Sabana Beach Resort",
            "location": "Hawassa",
            "standard_rate_etb": 3500,
            "deluxe_rate_etb": 5800,
            "suite_rate_etb": 9000,
            "tier": "midscale"
        },
        {
            "name": "Paradise Lodge",
            "location": "Arba Minch",
            "standard_rate_etb": 4200,
            "deluxe_rate_etb": 7000,
            "suite_rate_etb": 11000,
            "tier": "upper_midscale"
        },
    ]


def get_season(d: date) -> str:
    """Get the Ethiopian tourism season for a date."""
    month = d.month
    if month in [6, 7, 8]:
        return "rainy_low"  # Kiremt (heavy rains)
    elif month in [9, 10]:
        return "post_rain_shoulder"  # End of rains, Meskel
    elif month in [11, 12, 1, 2]:
        return "dry_peak"  # Best weather, holidays
    elif month in [3, 4]:
        return "easter_shoulder"  # Easter season
    else:
        return "pre_rain_shoulder"  # May, transition
