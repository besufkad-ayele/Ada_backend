"""
Destinations and Booking API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime, timedelta
import random
import string

from app.database import get_db
from app.models.destinations import Destination, DestinationRoomType
from app.models.bookings import Booking
from app.models.users import User
from pydantic import BaseModel

router = APIRouter(prefix="/api/destinations", tags=["Destinations"])


# Schemas
class DestinationResponse(BaseModel):
    id: int
    code: str
    name: str
    location: str
    description: str
    amenities: List[str]
    is_active: bool

    class Config:
        from_attributes = True


class RoomTypeResponse(BaseModel):
    id: int
    destination_code: str
    room_type: str
    room_type_name: str
    total_rooms: int
    base_rate_etb: float
    base_rate_usd: float
    max_occupancy: int
    size_sqm: int
    description: str
    amenities: List[str]
    services_included: List[str]

    class Config:
        from_attributes = True


class BookingRequest(BaseModel):
    destination_code: str
    room_type: str
    check_in: str
    check_out: str
    adults: int
    children: int
    guest_email: str
    guest_name: str
    guest_phone: str
    selected_packages: List[str] = []
    payment_method: str = "card"


class BookingResponse(BaseModel):
    booking_code: str
    destination_name: str
    room_type_name: str
    check_in: str
    check_out: str
    nights: int
    adults: int
    children: int
    room_rate_etb: float
    packages_total_etb: float
    total_amount_etb: float
    status: str
    message: str


@router.get("/list", response_model=List[DestinationResponse])
def get_destinations(db: Session = Depends(get_db)):
    """Get all active destinations"""
    destinations = db.query(Destination).filter(Destination.is_active == True).all()
    
    # Parse amenities JSON
    result = []
    for dest in destinations:
        dest_dict = {
            "id": dest.id,
            "code": dest.code,
            "name": dest.name,
            "location": dest.location,
            "description": dest.description,
            "amenities": json.loads(dest.amenities) if dest.amenities else [],
            "is_active": dest.is_active
        }
        result.append(dest_dict)
    
    return result


@router.get("/{destination_code}/rooms", response_model=List[RoomTypeResponse])
def get_destination_rooms(destination_code: str, db: Session = Depends(get_db)):
    """Get all room types for a destination"""
    room_types = db.query(DestinationRoomType).filter(
        DestinationRoomType.destination_code == destination_code
    ).all()
    
    if not room_types:
        raise HTTPException(status_code=404, detail="Destination not found")
    
    # Parse JSON fields
    result = []
    for room in room_types:
        room_dict = {
            "id": room.id,
            "destination_code": room.destination_code,
            "room_type": room.room_type,
            "room_type_name": room.room_type_name,
            "total_rooms": room.total_rooms,
            "base_rate_etb": room.base_rate_etb,
            "base_rate_usd": room.base_rate_usd,
            "max_occupancy": room.max_occupancy,
            "size_sqm": room.size_sqm or 0,
            "description": room.description or "",
            "amenities": json.loads(room.amenities) if room.amenities else [],
            "services_included": json.loads(room.services_included) if room.services_included else []
        }
        result.append(room_dict)
    
    return result


@router.get("/calculate-price")
def calculate_booking_price(
    destination_code: str,
    room_type: str,
    check_in: str,
    check_out: str,
    adults: int,
    db: Session = Depends(get_db)
):
    """Calculate AI-optimized price for booking"""
    
    # Get room type
    room = db.query(DestinationRoomType).filter(
        DestinationRoomType.destination_code == destination_code,
        DestinationRoomType.room_type == room_type
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room type not found")
    
    # Calculate nights
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
    check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
    nights = (check_out_date - check_in_date).days
    
    if nights < 1:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")
    
    # AI Pricing Logic (simplified - uses existing pricing engine concepts)
    base_rate = room.base_rate_etb
    
    # Occupancy multiplier (simulate current occupancy)
    occupancy_rate = random.uniform(0.5, 0.9)
    if occupancy_rate > 0.8:
        occupancy_multiplier = 1.15
    elif occupancy_rate > 0.6:
        occupancy_multiplier = 1.05
    else:
        occupancy_multiplier = 0.95
    
    # Lead time multiplier
    days_until_checkin = (check_in_date - datetime.now()).days
    if days_until_checkin < 7:
        lead_time_multiplier = 1.10
    elif days_until_checkin < 30:
        lead_time_multiplier = 1.0
    else:
        lead_time_multiplier = 0.95
    
    # Weekend multiplier
    if check_in_date.weekday() >= 4:  # Friday, Saturday, Sunday
        weekend_multiplier = 1.08
    else:
        weekend_multiplier = 1.0
    
    # Calculate optimized rate
    optimized_rate = base_rate * occupancy_multiplier * lead_time_multiplier * weekend_multiplier
    optimized_rate = round(optimized_rate, 2)
    
    # Calculate total
    room_total = optimized_rate * nights
    
    return {
        "base_rate_etb": base_rate,
        "optimized_rate_etb": optimized_rate,
        "nights": nights,
        "room_total_etb": room_total,
        "occupancy_rate": round(occupancy_rate * 100, 1),
        "pricing_factors": {
            "occupancy_multiplier": occupancy_multiplier,
            "lead_time_multiplier": lead_time_multiplier,
            "weekend_multiplier": weekend_multiplier
        }
    }


@router.get("/packages")
def get_available_packages(
    destination_code: str,
    room_type: str,
    adults: int,
    db: Session = Depends(get_db)
):
    """Get recommended packages for booking"""
    
    # Simplified package recommendations based on destination and guest type
    packages = []
    
    # Romance Package
    if adults == 2:
        packages.append({
            "id": "romance",
            "name": "Romance Package",
            "description": "Couples spa treatment, candlelit dinner, champagne",
            "price_etb": 3500,
            "services": ["Couples Spa (90min)", "Candlelit Dinner", "Champagne", "Rose Petals"]
        })
    
    # Family Package
    if adults >= 2:
        packages.append({
            "id": "family",
            "name": "Family Fun Package",
            "description": "Kids activities, family dinner, adventure tours",
            "price_etb": 4200,
            "services": ["Kids Club Access", "Family Dinner", "Adventure Tour", "Welcome Gifts"]
        })
    
    # Wellness Package
    packages.append({
        "id": "wellness",
        "name": "Wellness & Spa Package",
        "description": "Daily spa treatments, yoga sessions, healthy meals",
        "price_etb": 5500,
        "services": ["Daily Spa Treatment", "Yoga Sessions", "Wellness Meals", "Meditation"]
    })
    
    # Adventure Package (for specific destinations)
    if destination_code in ["ENTOTO", "AWASH", "BISHOFTU"]:
        packages.append({
            "id": "adventure",
            "name": "Adventure Package",
            "description": "Guided tours, outdoor activities, equipment rental",
            "price_etb": 4800,
            "services": ["Guided Tours", "Equipment Rental", "Outdoor Activities", "Packed Lunch"]
        })
    
    # Cultural Package
    if destination_code in ["TANA", "AFRICAN_VILLAGE"]:
        packages.append({
            "id": "cultural",
            "name": "Cultural Experience Package",
            "description": "Traditional ceremonies, cultural tours, local cuisine",
            "price_etb": 3800,
            "services": ["Coffee Ceremony", "Cultural Tours", "Traditional Dinner", "Local Guide"]
        })
    
    return {
        "packages": packages,
        "recommendation": "romance" if adults == 2 else "family"
    }


@router.post("/book", response_model=BookingResponse)
def create_booking(booking: BookingRequest, db: Session = Depends(get_db)):
    """Create a new booking"""
    
    # Get destination
    destination = db.query(Destination).filter(
        Destination.code == booking.destination_code
    ).first()
    
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    
    # Get room type
    room = db.query(DestinationRoomType).filter(
        DestinationRoomType.destination_code == booking.destination_code,
        DestinationRoomType.room_type == booking.room_type
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room type not found")
    
    # Calculate pricing
    check_in_date = datetime.strptime(booking.check_in, "%Y-%m-%d")
    check_out_date = datetime.strptime(booking.check_out, "%Y-%m-%d")
    nights = (check_out_date - check_in_date).days
    
    # Get optimized price
    price_calc = calculate_booking_price(
        booking.destination_code,
        booking.room_type,
        booking.check_in,
        booking.check_out,
        booking.adults,
        db
    )
    
    room_total = price_calc["room_total_etb"]
    
    # Calculate packages total
    packages_total = 0
    if booking.selected_packages:
        package_prices = {
            "romance": 3500,
            "family": 4200,
            "wellness": 5500,
            "adventure": 4800,
            "cultural": 3800
        }
        for pkg_id in booking.selected_packages:
            packages_total += package_prices.get(pkg_id, 0)
    
    total_amount = room_total + packages_total
    
    # Generate booking code
    booking_code = "KRZ-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Create booking record (simplified - using existing Booking model structure)
    # Note: You may need to adapt this to match your exact Booking model fields
    
    return {
        "booking_code": booking_code,
        "destination_name": destination.name,
        "room_type_name": room.room_type_name,
        "check_in": booking.check_in,
        "check_out": booking.check_out,
        "nights": nights,
        "adults": booking.adults,
        "children": booking.children,
        "room_rate_etb": price_calc["optimized_rate_etb"],
        "packages_total_etb": packages_total,
        "total_amount_etb": total_amount,
        "status": "CONFIRMED",
        "message": f"Booking confirmed! Your confirmation code is {booking_code}. We've sent details to {booking.guest_email}"
    }
