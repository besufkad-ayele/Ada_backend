"""
API Routes — Simulation and what-if analysis endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models.rooms import RoomType
from app.models.bookings import Booking, Guest, BookingStatus, BookingChannel
from app.models.packages import Package
from app.engine.pricing import PricingEngine
from app.engine.segmentation import GuestSegmenter
from app.engine.packages import PackageRecommender
from app.schemas.bookings import BookingCreate

router = APIRouter(prefix="/api/simulate", tags=["Simulation"])


@router.get("/scenarios")
def get_predefined_scenarios():
    """Get pre-configured demo scenarios for the simulator."""
    today = date.today()
    
    scenarios = [
        {
            "name": "International Couple (45 days out)",
            "description": "Honeymoon travelers booking well in advance",
            "request": {
                "guest_first_name": "James",
                "guest_last_name": "Anderson",
                "guest_email": "james@example.com",
                "guest_nationality": "American",
                "is_corporate": False,
                "room_type_code": "suite",
                "check_in": (today + timedelta(days=45)).isoformat(),
                "check_out": (today + timedelta(days=48)).isoformat(),
                "adults": 2,
                "children": 0,
                "channel": "direct",
                "accept_package": True,
            }
        },
        {
            "name": "Last-Minute Business Traveler",
            "description": "Corporate booking 2 days before arrival",
            "request": {
                "guest_first_name": "Sarah",
                "guest_last_name": "Chen",
                "guest_email": "sarah.chen@company.com",
                "guest_nationality": "Chinese",
                "is_corporate": True,
                "company_name": "Tech Corp",
                "room_type_code": "deluxe",
                "check_in": (today + timedelta(days=2)).isoformat(),
                "check_out": (today + timedelta(days=4)).isoformat(),
                "adults": 1,
                "children": 0,
                "channel": "corporate",
                "accept_package": False,
            }
        },
        {
            "name": "Ethiopian Family Weekend",
            "description": "Domestic family booking for weekend getaway",
            "request": {
                "guest_first_name": "Abebe",
                "guest_last_name": "Tadesse",
                "guest_email": "abebe@email.et",
                "guest_nationality": "Ethiopian",
                "is_corporate": False,
                "room_type_code": "deluxe",
                "check_in": (today + timedelta(days=14)).isoformat(),
                "check_out": (today + timedelta(days=16)).isoformat(),
                "adults": 2,
                "children": 2,
                "channel": "direct",
                "accept_package": True,
            }
        },
    ]
    
    return scenarios


@router.post("/booking")
def simulate_booking(request: BookingCreate, db: Session = Depends(get_db)):
    """Simulate a complete booking flow with AI pricing, segmentation, and package recommendation."""
    check_in = request.check_in
    check_out = request.check_out
    nights = (check_out - check_in).days
    lead_time = (check_in - date.today()).days

    room_type = db.query(RoomType).filter(RoomType.code == request.room_type_code).first()
    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    segmenter = GuestSegmenter()
    segment_result = segmenter.classify(
        nationality=request.guest_nationality,
        is_corporate=request.is_corporate,
        adults=request.adults,
        children=request.children,
        check_in=check_in,
        check_out=check_out,
        room_type_code=request.room_type_code,
        booking_channel=request.channel,
        company_name=request.company_name,
    )

    pricing_engine = PricingEngine(db)
    pricing = pricing_engine.get_optimal_price(
        room_type_code=request.room_type_code,
        target_date=check_in,
        guest_nationality=request.guest_nationality,
        booking_channel=request.channel,
        lead_time_days=lead_time,
    )

    rate_per_night = pricing["recommended_rate_etb"]
    total_room_revenue = rate_per_night * nights

    package_recommender = PackageRecommender(db)
    package_result = package_recommender.recommend(
        guest_nationality=request.guest_nationality,
        is_corporate=request.is_corporate,
        adults=request.adults,
        children=request.children,
        check_in=check_in,
        check_out=check_out,
        room_type_code=request.room_type_code,
        booking_channel=request.channel,
        room_rate_etb=rate_per_night,
    )

    total_package_revenue = 0.0
    package_accepted = request.accept_package and package_result["top_recommendation"] is not None
    package_id = None
    
    if package_accepted and package_result["top_recommendation"]:
        pkg_data = package_result["top_recommendation"]
        total_package_revenue = pkg_data["package_price_etb"]
        pkg_record = db.query(Package).filter(Package.code == pkg_data["package_code"]).first()
        if pkg_record:
            package_id = pkg_record.id

    guest = Guest(
        first_name=request.guest_first_name,
        last_name=request.guest_last_name,
        email=request.guest_email,
        nationality=request.guest_nationality,
        is_corporate=request.is_corporate,
        company_name=request.company_name,
    )
    db.add(guest)
    db.flush()

    # Convert channel string to enum
    channel_enum = BookingChannel.DIRECT
    if request.channel == "corporate":
        channel_enum = BookingChannel.CORPORATE
    elif request.channel == "phone":
        channel_enum = BookingChannel.PHONE
    elif request.channel == "walk_in":
        channel_enum = BookingChannel.WALK_IN
    
    # Generate a temporary booking ref to satisfy NOT NULL constraint
    import random
    temp_ref = f"TEMP{random.randint(100000, 999999)}"
    
    booking = Booking(
        booking_ref=temp_ref,
        guest_id=guest.id,
        room_type_id=room_type.id,
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        booking_date=datetime.utcnow(),
        adults=request.adults,
        children=request.children,
        rate_etb=rate_per_night,
        fare_class=pricing["recommended_fare_class"],
        total_room_revenue_etb=total_room_revenue,
        channel=channel_enum,
        lead_time_days=lead_time,
        ai_segment=segment_result["segment"],
        package_accepted=package_accepted,
        package_id=package_id,
        total_package_revenue_etb=total_package_revenue,
        total_revenue_etb=total_room_revenue + total_package_revenue,
        status=BookingStatus.CONFIRMED,
    )
    db.add(booking)
    db.flush()  # Flush to get the ID without committing
    
    # Now update with the proper booking ref
    booking.booking_ref = f"KRZ{booking.id:06d}"
    db.commit()
    db.refresh(booking)

    base_rate = room_type.base_rate_etb * nights
    uplift_etb = (total_room_revenue + total_package_revenue) - base_rate
    uplift_pct = round((uplift_etb / base_rate) * 100, 1) if base_rate > 0 else 0

    return {
        "booking": {
            "booking_ref": booking.booking_ref,
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "room_type": room_type.name,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "nights": nights,
            "rate_per_night_etb": round(rate_per_night, 2),
            "total_room_revenue_etb": round(total_room_revenue, 2),
            "total_package_revenue_etb": round(total_package_revenue, 2),
            "total_revenue_etb": round(total_room_revenue + total_package_revenue, 2),
            "status": "confirmed",
        },
        "ai_analysis": {
            "segmentation": segment_result,
            "pricing": pricing,
            "package_recommendation": package_result,
        },
        "revenue_impact": {
            "base_rate_etb": round(base_rate, 2),
            "optimized_rate_etb": round(total_room_revenue + total_package_revenue, 2),
            "uplift_etb": round(uplift_etb, 2),
            "uplift_pct": f"+{uplift_pct}%",
        }
    }
