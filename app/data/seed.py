"""
Synthetic Data Generator for Kuraz AI

Generates realistic hotel booking data that mimics a real Ethiopian resort.
Creates 2 years of historical data (~50,000 bookings) with:
- Seasonal patterns (rain vs dry season)
- Ethiopian holiday demand spikes
- Realistic guest mix (60% domestic, 40% international)
- Proper lead time distributions
- Fare class utilization patterns
"""
import random
import string
import math
from datetime import date, datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.models.rooms import RoomType, Room, DailyInventory
from app.models.bookings import Guest, Booking, BookingService, GuestSegment, BookingChannel, BookingStatus
from app.models.packages import Package, PackageComponent
from app.models.events import Event, CompetitorRate
from app.config import get_settings
from app.data.ethiopian_calendar import get_ethiopian_holidays, get_competitor_resorts, get_season

settings = get_settings()

# Ethiopian first/last names for realistic data
ETHIOPIAN_FIRST_NAMES = [
    "Abebe", "Almaz", "Bekele", "Biruk", "Dagmawi", "Eden", "Eyob", "Fasil",
    "Gelila", "Hana", "Henok", "Kidist", "Liya", "Meron", "Naod", "Ruth",
    "Sara", "Selamawit", "Solomon", "Tigist", "Yohannes", "Yordanos", "Zelalem",
    "Addis", "Bezawit", "Dawit", "Eleni", "Fitsum", "Genet", "Habtamu",
    "Kalkidan", "Lemma", "Mahlet", "Nebil", "Robel", "Selam", "Tadesse",
    "Wubet", "Yared", "Zewditu", "Aster", "Bereket", "Chaltu", "Desta",
]

ETHIOPIAN_LAST_NAMES = [
    "Tadesse", "Bekele", "Haile", "Desta", "Mekonnen", "Gebreselassie",
    "Alemayehu", "Tesfaye", "Mohammed", "Abebe", "Kebede", "Wolde",
    "Girma", "Negash", "Assefa", "Berhane", "Getachew", "Mulugeta",
    "Wondimu", "Yilma", "Zewde", "Asfaw", "Debebe", "Eshetu",
    "Fikre", "Gudeta", "Habte", "Kassa", "Legesse", "Mengistu",
]

INTERNATIONAL_FIRST_NAMES = [
    "James", "Emma", "Oliver", "Sophia", "William", "Isabella",
    "Hans", "Marie", "Pierre", "Elena", "Marco", "Yuki",
    "Ahmed", "Fatima", "Chen", "Mei", "John", "Sarah",
    "Michael", "Anna", "David", "Lisa", "Robert", "Maria",
]

INTERNATIONAL_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Mueller",
    "Schmidt", "Dubois", "Rossi", "Tanaka", "Wang", "Kim",
    "Anderson", "Thomas", "Martin", "Garcia", "Martinez", "Ali",
]

NATIONALITIES = [
    ("Ethiopian", 0.55),
    ("American", 0.08),
    ("British", 0.06),
    ("German", 0.05),
    ("French", 0.04),
    ("Italian", 0.03),
    ("Chinese", 0.04),
    ("Japanese", 0.02),
    ("Kenyan", 0.03),
    ("Nigerian", 0.02),
    ("Indian", 0.03),
    ("Saudi", 0.02),
    ("Other", 0.03),
]

COMPANIES = [
    "Ethiopian Airlines", "Ethio Telecom", "Commercial Bank of Ethiopia",
    "Dashen Bank", "UN ECA", "African Union", "WHO Ethiopia",
    "USAID Ethiopia", "GIZ Ethiopia", "World Bank Group",
    "Heineken Ethiopia", "BGI Ethiopia", "Unilever Ethiopia",
    "Total Energies Ethiopia", "Hilton Addis", "Embassy of USA",
    "Embassy of China", "EU Delegation", "UNDP Ethiopia",
]


def generate_booking_ref() -> str:
    """Generate a booking reference like KRZ-A1B2C3."""
    chars = string.ascii_uppercase + string.digits
    return f"KRZ-{''.join(random.choices(chars, k=6))}"


def pick_nationality() -> str:
    """Pick a nationality based on realistic distribution."""
    r = random.random()
    cum = 0.0
    for nat, prob in NATIONALITIES:
        cum += prob
        if r <= cum:
            return nat
    return "Ethiopian"


def seed_room_types(db: Session) -> List[RoomType]:
    """Create room types from config."""
    room_types = []
    for code, config in settings.ROOM_TYPES.items():
        rt = RoomType(
            code=code,
            name=config["description"],
            description=f"{config['description']} at {settings.RESORT_NAME}",
            total_count=config["count"],
            max_occupancy=config["max_occupancy"],
            base_rate_etb=config["base_rate_etb"],
            base_rate_usd=config["base_rate_usd"],
            floor_rate_etb=config["base_rate_etb"] * 0.50,  # Floor = 50% of base
            ceiling_rate_etb=config["base_rate_etb"] * 2.50,  # Ceiling = 250% of base
        )
        db.add(rt)
        room_types.append(rt)

    db.commit()
    for rt in room_types:
        db.refresh(rt)
    return room_types


def seed_rooms(db: Session, room_types: List[RoomType]) -> List[Room]:
    """Create individual room records."""
    rooms = []
    room_number = 100
    for rt in room_types:
        floor = 1
        for i in range(rt.total_count):
            if i > 0 and i % 15 == 0:
                floor += 1
            room = Room(
                room_number=str(room_number),
                room_type_id=rt.id,
                floor=floor,
                is_lake_view=(i % 3 == 0),  # Every 3rd room has lake view
            )
            db.add(room)
            rooms.append(room)
            room_number += 1
    db.commit()
    return rooms


def seed_packages(db: Session) -> List[Package]:
    """Create the 10 pre-defined resort packages."""
    packages_data = [
        {
            "code": "romance_escape",
            "name": "Romance Escape",
            "description": "Perfect for couples seeking a romantic lakeside retreat",
            "category": "romance",
            "target_segments": "honeymoon,international_leisure,domestic_weekend",
            "base_price_etb": 8500,
            "min_discount_pct": 0.10,
            "max_discount_pct": 0.20,
            "min_nights": 2,
            "components": [
                ("Couples Spa Treatment", "spa", "90-minute couples massage", 2500, 3500),
                ("Romantic Lakeside Dinner", "dining", "3-course dinner with wine", 2000, 3000),
                ("Late Checkout (2pm)", "room_upgrade", "Extended checkout", 500, 1000),
                ("Room Flower Decoration", "amenity", "Rose petals and champagne setup", 500, 1000),
            ]
        },
        {
            "code": "family_getaway",
            "name": "Family Getaway",
            "description": "Fun-filled family experience with activities for all ages",
            "category": "family",
            "target_segments": "family,domestic_weekend",
            "base_price_etb": 6000,
            "min_discount_pct": 0.10,
            "max_discount_pct": 0.25,
            "min_nights": 2,
            "components": [
                ("Breakfast for Family (all days)", "dining", "Full breakfast buffet for 4", 1500, 2400),
                ("Kids Pool & Activity Pass", "activity", "Supervised kids activities", 800, 1200),
                ("Boat Ride on Lake", "activity", "1-hour boat tour", 1000, 1500),
                ("BBQ Lunch", "dining", "Lakeside BBQ for family", 1200, 1800),
            ]
        },
        {
            "code": "business_express",
            "name": "Business Express",
            "description": "Everything a business traveler needs for a productive stay",
            "category": "business",
            "target_segments": "business,conference",
            "base_price_etb": 3500,
            "min_discount_pct": 0.05,
            "max_discount_pct": 0.10,
            "min_nights": 1,
            "components": [
                ("High-Speed WiFi Upgrade", "amenity", "Dedicated bandwidth", 300, 500),
                ("Breakfast Included", "dining", "Full breakfast buffet", 500, 800),
                ("Airport Transfer (both ways)", "transfer", "Private car to/from Bole", 1500, 2500),
                ("Express Checkout", "amenity", "Priority checkout service", 200, 300),
            ]
        },
        {
            "code": "weekend_wellness",
            "name": "Weekend Wellness",
            "description": "Rejuvenate with a complete spa and wellness experience",
            "category": "wellness",
            "target_segments": "domestic_weekend,international_leisure",
            "base_price_etb": 7500,
            "min_discount_pct": 0.10,
            "max_discount_pct": 0.20,
            "min_nights": 2,
            "components": [
                ("Full Spa Day (3 treatments)", "spa", "Massage, facial, body wrap", 3500, 5000),
                ("Yoga Session", "activity", "Morning lakeside yoga", 500, 800),
                ("Healthy Meals Package", "dining", "3 healthy meals per day", 2000, 3200),
                ("Meditation Session", "activity", "Guided meditation", 400, 600),
            ]
        },
        {
            "code": "adventure",
            "name": "Adventure Package",
            "description": "Explore the best of Ethiopian nature and culture",
            "category": "adventure",
            "target_segments": "international_leisure,family,domestic_weekend",
            "base_price_etb": 5500,
            "min_discount_pct": 0.10,
            "max_discount_pct": 0.20,
            "min_nights": 2,
            "components": [
                ("Boat Excursion", "activity", "Island monastery boat tour", 1500, 2200),
                ("Nature Hike", "activity", "Guided crater lake hike", 800, 1200),
                ("BBQ & Bonfire Night", "dining", "Outdoor BBQ with live music", 1200, 1800),
                ("Bird Watching Tour", "activity", "Early morning birding with guide", 600, 900),
            ]
        },
        {
            "code": "conference_package",
            "name": "Conference Package",
            "description": "All-inclusive conference and meetings package",
            "category": "conference",
            "target_segments": "conference,business",
            "base_price_etb": 5000,
            "min_discount_pct": 0.10,
            "max_discount_pct": 0.20,
            "min_nights": 1,
            "components": [
                ("Conference Hall (full day)", "venue", "Equipped meeting room for 50", 2000, 3500),
                ("Coffee Breaks (2)", "dining", "Morning and afternoon tea/coffee", 400, 600),
                ("Lunch Buffet", "dining", "Conference lunch for attendees", 800, 1200),
                ("AV Equipment", "amenity", "Projector, screen, sound system", 500, 800),
            ]
        },
        {
            "code": "honeymoon_bliss",
            "name": "Honeymoon Bliss",
            "description": "The ultimate honeymoon experience at the lakeside",
            "category": "romance",
            "target_segments": "honeymoon",
            "base_price_etb": 15000,
            "min_discount_pct": 0.05,
            "max_discount_pct": 0.15,
            "min_nights": 3,
            "components": [
                ("Suite Upgrade", "room_upgrade", "Upgrade to Royal Suite", 5000, 8000),
                ("Couples Spa (2 sessions)", "spa", "Daily spa treatments", 4000, 6000),
                ("Romantic Dinner (2 nights)", "dining", "Private lakeside dining", 3000, 4500),
                ("Honeymoon Decoration", "amenity", "Full room decoration with cake", 1500, 2500),
                ("Sunset Boat Cruise", "activity", "Private sunset cruise", 1200, 2000),
            ]
        },
        {
            "code": "day_use",
            "name": "Day Use Pass",
            "description": "Enjoy the resort for a day without staying overnight",
            "category": "leisure",
            "target_segments": "domestic_weekend",
            "base_price_etb": 3000,
            "min_discount_pct": 0.05,
            "max_discount_pct": 0.20,
            "min_nights": 0,
            "max_nights": 0,
            "components": [
                ("Pool Access (full day)", "activity", "Swimming pool and sun beds", 800, 1200),
                ("Lunch Buffet", "dining", "Full lunch buffet", 800, 1200),
                ("Spa Express (1 treatment)", "spa", "Choice of massage or facial", 1000, 1500),
            ]
        },
        {
            "code": "cultural_experience",
            "name": "Cultural Experience",
            "description": "Immerse yourself in Ethiopian culture and traditions",
            "category": "cultural",
            "target_segments": "international_leisure,group_tour",
            "base_price_etb": 4500,
            "min_discount_pct": 0.10,
            "max_discount_pct": 0.20,
            "min_nights": 2,
            "components": [
                ("Ethiopian Coffee Ceremony", "activity", "Traditional coffee ceremony", 500, 800),
                ("Cultural Dance Show", "activity", "Evening cultural performance", 800, 1200),
                ("Traditional Dinner", "dining", "Full Ethiopian traditional meal (injera)", 700, 1100),
                ("Local Market Tour", "activity", "Guided tour of local market", 600, 900),
            ]
        },
        {
            "code": "long_stay",
            "name": "Extended Stay",
            "description": "Special rates and perks for stays of 5 nights or more",
            "category": "extended",
            "target_segments": "long_stay,business,international_leisure",
            "base_price_etb": 8000,
            "min_discount_pct": 0.15,
            "max_discount_pct": 0.30,
            "min_nights": 5,
            "max_nights": 30,
            "components": [
                ("All Meals Included", "dining", "Breakfast, lunch, dinner daily", 4000, 6000),
                ("Laundry Service", "amenity", "Daily laundry and pressing", 1500, 2500),
                ("Weekly Spa Treatment", "spa", "One spa session per week", 1500, 2500),
                ("Airport Transfer", "transfer", "Round-trip airport transfer", 1500, 2500),
            ]
        },
    ]

    packages = []
    for pkg_data in packages_data:
        components_data = pkg_data.pop("components")
        max_nights = pkg_data.pop("max_nights", 14)

        # Pre-compute realistic acceptance rates and revenue uplift from segment probabilities
        segment_acceptance = {
            "honeymoon": 0.75, "international_leisure": 0.60,
            "family": 0.55, "domestic_weekend": 0.40,
            "business": 0.25, "conference": 0.35,
            "group_tour": 0.50, "long_stay": 0.45,
        }
        target_segs = pkg_data.get("target_segments", "").split(",")
        avg_acceptance = sum(
            segment_acceptance.get(s.strip(), 0.35) for s in target_segs
        ) / max(1, len(target_segs))

        # Simulate realistic times_offered / accepted
        times_offered = random.randint(80, 200)
        times_accepted = int(times_offered * avg_acceptance * random.uniform(0.85, 1.15))

        # Revenue uplift = package base price * mid discount
        mid_discount = (pkg_data["min_discount_pct"] + pkg_data["max_discount_pct"]) / 2
        avg_uplift = pkg_data["base_price_etb"] * (1 - mid_discount)

        pkg = Package(
            **pkg_data,
            max_nights=max_nights,
            margin_floor_pct=0.15,
            times_offered=times_offered,
            times_accepted=times_accepted,
            acceptance_rate=round(times_accepted / max(1, times_offered), 4),
            avg_revenue_uplift_etb=round(avg_uplift, 2),
        )
        db.add(pkg)
        db.flush()

        for comp in components_data:
            component = PackageComponent(
                package_id=pkg.id,
                service_name=comp[0],
                service_category=comp[1],
                description=comp[2],
                cost_etb=comp[3],
                retail_price_etb=comp[4],
            )
            db.add(component)

        packages.append(pkg)

    db.commit()
    for pkg in packages:
        db.refresh(pkg)
    return packages


def seed_events(db: Session) -> List[Event]:
    """Seed Ethiopian holidays and events for 2025-2026."""
    events = []
    for year in [2025, 2026]:
        holidays = get_ethiopian_holidays(year)
        for h in holidays:
            event = Event(
                name=h["name"],
                event_type=h["event_type"],
                date_start=h["date_start"],
                date_end=h["date_end"],
                impact_level=h["impact_level"],
                impact_direction="positive",
                is_national=h["is_national"],
                description=h["description"],
                expected_demand_multiplier=h["demand_multiplier"],
            )
            db.add(event)
            events.append(event)

    db.commit()
    return events


def seed_competitor_rates(db: Session, start_date: date, end_date: date):
    """Generate competitor rate data for benchmarking."""
    competitors = get_competitor_resorts()
    room_mapping = {
        "standard": "standard_rate_etb",
        "deluxe": "deluxe_rate_etb",
        "suite": "suite_rate_etb",
    }

    current = start_date
    while current <= end_date:
        # Only sample every 3rd day to reduce data volume
        if current.toordinal() % 3 == 0:
            for comp in competitors:
                for room_code, rate_key in room_mapping.items():
                    base = comp[rate_key]
                    # Add realistic variation
                    season = get_season(current)
                    seasonal_mult = {
                        "dry_peak": 1.15,
                        "post_rain_shoulder": 1.05,
                        "easter_shoulder": 1.10,
                        "pre_rain_shoulder": 0.95,
                        "rainy_low": 0.80,
                    }.get(season, 1.0)

                    dow_mult = 1.15 if current.weekday() >= 4 else 0.95
                    noise = random.uniform(0.93, 1.07)
                    rate = base * seasonal_mult * dow_mult * noise

                    cr = CompetitorRate(
                        competitor_name=comp["name"],
                        room_category=room_code,
                        date=current,
                        rate_etb=round(rate, 2),
                        rate_usd=round(rate / 55.0, 2),
                        source="synthetic",
                        collected_at=datetime.utcnow(),
                    )
                    db.add(cr)

        current += timedelta(days=1)

    db.commit()


def generate_bookings(
    db: Session,
    room_types: List[RoomType],
    packages: List[Package],
    start_date: date,
    end_date: date,
) -> int:
    """
    Generate realistic booking history.
    
    Models:
    - Seasonal demand curves
    - Day-of-week patterns
    - Lead time distributions by segment
    - Fare class utilization
    - Package acceptance rates
    """
    booking_count = 0
    fare_config = settings.FARE_CLASSES

    # Pre-create guests
    guests = []
    for i in range(3000):
        nationality = pick_nationality()
        is_intl = nationality != "Ethiopian"
        is_corp = random.random() < 0.15

        if is_intl:
            first = random.choice(INTERNATIONAL_FIRST_NAMES)
            last = random.choice(INTERNATIONAL_LAST_NAMES)
        else:
            first = random.choice(ETHIOPIAN_FIRST_NAMES)
            last = random.choice(ETHIOPIAN_LAST_NAMES)

        guest = Guest(
            first_name=first,
            last_name=last,
            email=f"{first.lower()}.{last.lower()}@{'gmail.com' if not is_corp else random.choice(COMPANIES).lower().replace(' ', '') + '.com'}",
            phone=f"+251-9{random.randint(10000000, 99999999)}" if not is_intl else f"+1-{random.randint(200, 999)}-{random.randint(1000000, 9999999)}",
            nationality=nationality,
            is_international=is_intl,
            is_corporate=is_corp,
            company_name=random.choice(COMPANIES) if is_corp else None,
            loyalty_tier=random.choices(
                ["none", "silver", "gold", "platinum"],
                weights=[0.65, 0.20, 0.10, 0.05]
            )[0],
        )
        db.add(guest)
        guests.append(guest)

    db.flush()

    # Generate bookings day by day
    current = start_date
    total_rooms = sum(rt.total_count for rt in room_types)

    while current <= end_date:
        # Determine demand for this day
        season = get_season(current)
        base_demand = {
            "dry_peak": 0.78,
            "post_rain_shoulder": 0.65,
            "easter_shoulder": 0.70,
            "pre_rain_shoulder": 0.55,
            "rainy_low": 0.40,
        }.get(season, 0.55)

        # Day of week adjustment
        dow_mult = {
            0: 0.70, 1: 0.68, 2: 0.72, 3: 0.78,
            4: 0.95, 5: 1.00, 6: 0.85,
        }.get(current.weekday(), 0.75)

        # Random noise
        noise = random.uniform(0.85, 1.15)
        target_occupancy = min(0.97, base_demand * dow_mult * noise)
        target_bookings = int(total_rooms * target_occupancy)

        # Distribute bookings across room types
        for rt in room_types:
            rt_bookings = int(target_bookings * (rt.total_count / total_rooms))
            rt_bookings = min(rt_bookings, rt.total_count)  # Can't exceed room count

            for _ in range(rt_bookings):
                guest = random.choice(guests)

                # Determine nights
                if guest.is_corporate:
                    nights = random.choices([1, 2, 3, 4, 5], weights=[0.25, 0.35, 0.25, 0.10, 0.05])[0]
                elif guest.is_international:
                    nights = random.choices([1, 2, 3, 4, 5, 7], weights=[0.05, 0.20, 0.30, 0.20, 0.15, 0.10])[0]
                else:
                    nights = random.choices([1, 2, 3], weights=[0.30, 0.50, 0.20])[0]

                check_in = current
                check_out = current + timedelta(days=nights)

                # Lead time (days between booking and check-in)
                if guest.is_corporate:
                    lead_time = random.choices(
                        [0, 1, 3, 5, 7, 14],
                        weights=[0.10, 0.15, 0.25, 0.25, 0.15, 0.10]
                    )[0]
                elif guest.is_international:
                    lead_time = random.choices(
                        [7, 14, 21, 30, 45, 60, 90],
                        weights=[0.05, 0.10, 0.20, 0.25, 0.20, 0.15, 0.05]
                    )[0]
                else:
                    lead_time = random.choices(
                        [0, 1, 3, 7, 14, 21, 30],
                        weights=[0.10, 0.15, 0.20, 0.25, 0.15, 0.10, 0.05]
                    )[0]

                booking_date = datetime.combine(
                    check_in - timedelta(days=lead_time),
                    datetime.min.time()
                )

                # Determine fare class based on lead time
                if lead_time >= 21:
                    fare_class = "saver"
                elif lead_time >= 7:
                    fare_class = "standard"
                else:
                    fare_class = "premium"

                # Calculate rate
                fc_config = fare_config[fare_class]
                rate = rt.base_rate_etb * (1 - fc_config["discount_pct"])

                # Apply seasonal and DOW adjustments
                season_mult = {
                    "dry_peak": 1.15, "post_rain_shoulder": 1.05,
                    "easter_shoulder": 1.10, "pre_rain_shoulder": 0.95,
                    "rainy_low": 0.80
                }.get(season, 1.0)
                rate *= season_mult * dow_mult
                rate *= random.uniform(0.95, 1.05)  # Small noise
                rate = round(rate, 2)

                total_room_revenue = rate * nights

                # Channel
                if guest.is_corporate:
                    channel = random.choice(["corporate", "direct"])
                elif guest.is_international:
                    channel = random.choices(
                        ["ota_booking", "ota_expedia", "direct", "travel_agent"],
                        weights=[0.35, 0.25, 0.25, 0.15]
                    )[0]
                else:
                    channel = random.choices(
                        ["direct", "phone", "ota_booking", "walk_in"],
                        weights=[0.35, 0.25, 0.25, 0.15]
                    )[0]

                # Guest composition
                adults = random.choices([1, 2, 3, 4], weights=[0.25, 0.50, 0.15, 0.10])[0]
                children = random.choices([0, 1, 2, 3], weights=[0.60, 0.25, 0.10, 0.05])[0]

                # Segment
                from app.engine.segmentation import GuestSegmenter
                segmenter = GuestSegmenter()
                seg_result = segmenter.classify(
                    nationality=guest.nationality,
                    is_corporate=guest.is_corporate,
                    adults=adults,
                    children=children,
                    check_in=check_in,
                    check_out=check_out,
                    room_type_code=rt.code,
                    booking_channel=channel,
                    company_name=guest.company_name,
                )
                segment = seg_result["segment"]

                # Package acceptance
                package_id = None
                package_discount = 0.0
                package_accepted = False
                total_package_revenue = 0.0

                acceptance_prob = {
                    "honeymoon": 0.75, "international_leisure": 0.60,
                    "family": 0.55, "domestic_weekend": 0.40,
                    "business": 0.25, "conference": 0.35,
                    "group_tour": 0.50, "long_stay": 0.45,
                }.get(segment, 0.30)

                if random.random() < acceptance_prob and packages:
                    # Find a matching package
                    matching = [p for p in packages if segment in p.target_segments]
                    if matching:
                        pkg = random.choice(matching)
                        package_id = pkg.id
                        package_accepted = True
                        package_discount = random.uniform(pkg.min_discount_pct, pkg.max_discount_pct)
                        total_package_revenue = pkg.base_price_etb * (1 - package_discount)

                total_revenue = total_room_revenue + total_package_revenue

                # Status
                status = random.choices(
                    ["checked_out", "cancelled", "no_show"],
                    weights=[0.88, 0.08, 0.04]
                )[0]

                booking = Booking(
                    booking_ref=generate_booking_ref(),
                    guest_id=guest.id,
                    room_type_id=rt.id,
                    check_in=check_in,
                    check_out=check_out,
                    nights=nights,
                    booking_date=booking_date,
                    lead_time_days=lead_time,
                    adults=adults,
                    children=children,
                    fare_class=fare_class,
                    rate_etb=rate,
                    rate_usd=round(rate / 55.0, 2),
                    total_room_revenue_etb=round(total_room_revenue, 2),
                    total_package_revenue_etb=round(total_package_revenue, 2),
                    total_revenue_etb=round(total_revenue, 2),
                    package_id=package_id,
                    package_discount_pct=round(package_discount, 2),
                    package_accepted=package_accepted,
                    channel=channel,
                    status=status,
                    ai_segment=segment,
                )
                db.add(booking)
                booking_count += 1

                # Update guest stats
                if status == "checked_out":
                    guest.total_stays += 1
                    guest.total_spend_etb += total_revenue
                    guest.segment = segment

        # Commit every 30 days to manage memory
        if (current - start_date).days % 30 == 0:
            db.commit()
            print(f"  Generated bookings through {current} ({booking_count:,} total)")

        current += timedelta(days=1)

    db.commit()
    return booking_count


def seed_daily_inventory(
    db: Session,
    room_types: List[RoomType],
    start_date: date,
    end_date: date,
):
    """Generate daily inventory records with realistic occupancy patterns."""
    fare_config = settings.FARE_CLASSES

    current = start_date
    while current <= end_date:
        season = get_season(current)
        base_occ = {
            "dry_peak": 0.78, "post_rain_shoulder": 0.65,
            "easter_shoulder": 0.70, "pre_rain_shoulder": 0.55,
            "rainy_low": 0.40,
        }.get(season, 0.55)

        dow_mult = {
            0: 0.70, 1: 0.68, 2: 0.72, 3: 0.78,
            4: 0.95, 5: 1.00, 6: 0.85,
        }.get(current.weekday(), 0.75)

        for rt in room_types:
            occupancy = min(0.98, base_occ * dow_mult * random.uniform(0.85, 1.15))
            booked = int(rt.total_count * occupancy)

            # Distribute across fare classes
            saver_total = int(rt.total_count * fare_config["saver"]["inventory_pct"])
            std_total = int(rt.total_count * fare_config["standard"]["inventory_pct"])
            prem_total = rt.total_count - saver_total - std_total

            saver_sold = min(saver_total, int(booked * 0.40))
            std_sold = min(std_total, int(booked * 0.40))
            prem_sold = min(prem_total, booked - saver_sold - std_sold)

            days_out = max(0, (current - date.today()).days)

            inv = DailyInventory(
                room_type_id=rt.id,
                date=current,
                total_rooms=rt.total_count,
                booked_rooms=booked,
                blocked_rooms=0,
                available_rooms=rt.total_count - booked,
                occupancy_rate=occupancy,
                saver_total=saver_total,
                saver_sold=saver_sold,
                saver_open=occupancy < 0.60 and days_out > 14,
                standard_total=std_total,
                standard_sold=std_sold,
                standard_open=occupancy < 0.85 and days_out > 3,
                premium_total=prem_total,
                premium_sold=prem_sold,
                premium_open=True,
                saver_rate=round(rt.base_rate_etb * 0.70, 2),
                standard_rate=round(rt.base_rate_etb * 0.90, 2),
                premium_rate=round(rt.base_rate_etb * 1.20, 2),
                forecasted_demand=occupancy * random.uniform(0.9, 1.1),
                forecasted_occupancy=occupancy * random.uniform(0.95, 1.05),
            )
            db.add(inv)

        if (current - start_date).days % 30 == 0:
            db.commit()
            print(f"  Generated inventory through {current}")

        current += timedelta(days=1)

    db.commit()


def run_full_seed():
    """
    Run the complete data seeding pipeline.
    Creates all tables and populates with realistic data.
    """
    # Reproducible randomness for seeding
    random.seed(42)
    from app.database import init_db

    print("=" * 60)
    print("KURAZ AI — Synthetic Data Generator")
    print("=" * 60)

    # Create tables
    print("\n[1/7] Creating database tables...")
    init_db()

    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(RoomType).count()
        if existing > 0:
            print("   Database already seeded. Skipping.")
            return

        # Seed room types
        print("\n[2/7] Creating room types...")
        room_types = seed_room_types(db)
        print(f"   Created {len(room_types)} room types")

        # Seed rooms
        print("\n[3/7] Creating individual rooms...")
        rooms = seed_rooms(db, room_types)
        print(f"   Created {len(rooms)} rooms")

        # Seed packages
        print("\n[4/7] Creating resort packages...")
        packages = seed_packages(db)
        print(f"   Created {len(packages)} packages with components")

        # Seed events
        print("\n[5/7] Seeding Ethiopian holidays and events...")
        events = seed_events(db)
        print(f"   Created {len(events)} events")

        # Date range: 2 years of history + 90 days forward
        hist_start = date(2024, 7, 1)
        hist_end = date.today()
        future_end = date.today() + timedelta(days=90)

        # Seed competitor rates
        print("\n[6/7] Generating competitor rate data...")
        seed_competitor_rates(db, hist_start, future_end)
        print("   Competitor rates generated")

        # Generate bookings
        print("\n[7/7] Generating booking history...")
        count = generate_bookings(db, room_types, packages, hist_start, hist_end)
        print(f"\n   ✅ Generated {count:,} bookings")

        # Generate inventory for future dates
        print("\n[BONUS] Generating historical and future inventory...")
        seed_daily_inventory(db, room_types, hist_start, future_end)
        print("   Future inventory generated")

        print("\n" + "=" * 60)
        print("✅ DATA SEEDING COMPLETE")
        print("=" * 60)
        print(f"   • Room types: {len(room_types)}")
        print(f"   • Rooms: {len(rooms)}")
        print(f"   • Packages: {len(packages)}")
        print(f"   • Events: {len(events)}")
        print(f"   • Bookings: {count:,}")
        print(f"   • Date range: {hist_start} to {future_end}")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    run_full_seed()
