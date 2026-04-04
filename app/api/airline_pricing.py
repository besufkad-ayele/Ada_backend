"""
Airline-Style Pricing API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.destinations import Destination, DestinationRoomType
from app.models.bookings import Booking
from app.engine.airline_pricing import AirlineStylePricingEngine, AIEnhancedPricingEngine

router = APIRouter(prefix="/api/pricing", tags=["Airline Pricing"])


class PriceRequest(BaseModel):
    destination_code: str
    room_type: str
    check_in: str  # YYYY-MM-DD
    adults: int = 2
    use_ai: bool = True  # Use AI-enhanced pricing or static table


class FareClassesRequest(BaseModel):
    destination_code: str
    room_type: str
    check_in: str


@router.post("/calculate")
def calculate_airline_price(request: PriceRequest, db: Session = Depends(get_db)):
    """
    Calculate price using airline-style revenue management
    
    Returns multiple fare classes with different restrictions
    """
    # Get room type
    room = db.query(DestinationRoomType).filter(
        DestinationRoomType.destination_code == request.destination_code,
        DestinationRoomType.room_type == request.room_type
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room type not found")
    
    # Parse check-in date
    check_in_date = datetime.strptime(request.check_in, "%Y-%m-%d")
    
    # Calculate current occupancy for this date
    current_occupancy = calculate_occupancy(
        request.destination_code,
        request.room_type,
        request.check_in,
        db
    )
    
    # Initialize pricing engine
    if request.use_ai:
        engine = AIEnhancedPricingEngine(
            base_rate=room.base_rate_etb,
            total_rooms=room.total_rooms
        )
        # Get AI-predicted demand
        predicted_demand = engine.predict_demand(check_in_date)
        pricing = engine.optimize_price(check_in_date, current_occupancy, predicted_demand)
    else:
        engine = AirlineStylePricingEngine(
            base_rate=room.base_rate_etb,
            total_rooms=room.total_rooms
        )
        # Check if weekend
        is_weekend = check_in_date.weekday() >= 4
        # Check if holiday (simplified)
        is_holiday = check_in_date.month in [9, 10]  # Meskel, Ethiopian New Year
        
        pricing = engine.calculate_price(
            check_in_date,
            current_occupancy,
            is_weekend=is_weekend,
            is_holiday=is_holiday
        )
    
    return {
        "destination": request.destination_code,
        "room_type": room.room_type_name,
        "check_in": request.check_in,
        "pricing": pricing,
        "room_details": {
            "total_rooms": room.total_rooms,
            "max_occupancy": room.max_occupancy,
            "size_sqm": room.size_sqm,
        }
    }


@router.post("/fare-classes")
def get_fare_classes(request: FareClassesRequest, db: Session = Depends(get_db)):
    """
    Get all available fare classes (like airline booking classes)
    
    Returns SAVER, STANDARD, FLEX, PREMIUM with different prices and restrictions
    """
    # Get room type
    room = db.query(DestinationRoomType).filter(
        DestinationRoomType.destination_code == request.destination_code,
        DestinationRoomType.room_type == request.room_type
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room type not found")
    
    # Parse check-in date
    check_in_date = datetime.strptime(request.check_in, "%Y-%m-%d")
    
    # Calculate current occupancy
    current_occupancy = calculate_occupancy(
        request.destination_code,
        request.room_type,
        request.check_in,
        db
    )
    
    # Calculate rooms remaining
    booked_rooms = count_booked_rooms(
        request.destination_code,
        request.room_type,
        request.check_in,
        db
    )
    rooms_remaining = room.total_rooms - booked_rooms
    
    # Initialize AI-enhanced engine
    engine = AIEnhancedPricingEngine(
        base_rate=room.base_rate_etb,
        total_rooms=room.total_rooms
    )
    
    # Get fare classes
    fare_classes = engine.get_available_fare_classes(
        check_in_date,
        current_occupancy,
        rooms_remaining
    )
    
    return {
        "destination": request.destination_code,
        "room_type": room.room_type_name,
        "check_in": request.check_in,
        "total_rooms": room.total_rooms,
        "booked_rooms": booked_rooms,
        "available_rooms": rooms_remaining,
        "current_occupancy_pct": round(current_occupancy, 1),
        "fare_classes": fare_classes,
    }


@router.get("/pricing-table")
def get_pricing_table():
    """
    Get the static pricing table (for admin dashboard visualization)
    """
    return {
        "table": AirlineStylePricingEngine.PRICING_TABLE,
        "description": "Static pricing rules based on time until arrival and inventory levels",
        "time_buckets": {
            ">30": "More than 1 month",
            "30-14": "1 month to 2 weeks",
            "14-7": "2 weeks to 1 week",
            "<7": "Less than 1 week"
        },
        "inventory_buckets": {
            "0-15": "0-15% occupancy",
            "15-30": "15-30% occupancy",
            "30-40": "30-40% occupancy",
            ">40": "Above 40% occupancy"
        }
    }


@router.get("/demand-forecast/{destination_code}")
def get_demand_forecast(
    destination_code: str,
    days_ahead: int = 90,
    db: Session = Depends(get_db)
):
    """
    Get AI demand forecast for next N days
    """
    destination = db.query(Destination).filter(
        Destination.code == destination_code
    ).first()
    
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    
    # Initialize AI engine (using a dummy base rate)
    engine = AIEnhancedPricingEngine(base_rate=10000, total_rooms=40)
    
    # Generate forecast
    forecast = []
    today = datetime.now()
    
    for day_offset in range(days_ahead):
        future_date = today + timedelta(days=day_offset)
        demand_multiplier = engine.predict_demand(future_date)
        
        forecast.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "day_of_week": future_date.strftime("%A"),
            "demand_multiplier": round(demand_multiplier, 2),
            "demand_level": get_demand_level(demand_multiplier),
            "recommended_strategy": get_pricing_strategy(demand_multiplier)
        })
    
    return {
        "destination": destination.name,
        "forecast_days": days_ahead,
        "forecast": forecast
    }


# Helper functions

def calculate_occupancy(
    destination_code: str,
    room_type: str,
    check_in: str,
    db: Session
) -> float:
    """Calculate current occupancy percentage for a specific date"""
    from app.models.rooms import RoomType
    
    # Get room type details
    room = db.query(DestinationRoomType).filter(
        DestinationRoomType.destination_code == destination_code,
        DestinationRoomType.room_type == room_type
    ).first()
    
    if not room:
        return 0.0
    
    # Count bookings for this date
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
    
    # Get room_type_id
    room_type_obj = db.query(RoomType).filter(RoomType.name == room_type).first()
    if not room_type_obj:
        return 0.0
    
    # Count confirmed bookings
    booked_count = db.query(Booking).filter(
        Booking.room_type_id == room_type_obj.id,
        Booking.check_in <= check_in_date,
        Booking.check_out > check_in_date,
        Booking.status.in_(["CONFIRMED", "CHECKED_IN"])
    ).count()
    
    occupancy_pct = (booked_count / room.total_rooms) * 100
    return min(100.0, occupancy_pct)


def count_booked_rooms(
    destination_code: str,
    room_type: str,
    check_in: str,
    db: Session
) -> int:
    """Count number of rooms already booked for a specific date"""
    from app.models.rooms import RoomType
    
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
    
    room_type_obj = db.query(RoomType).filter(RoomType.name == room_type).first()
    if not room_type_obj:
        return 0
    
    booked_count = db.query(Booking).filter(
        Booking.room_type_id == room_type_obj.id,
        Booking.check_in <= check_in_date,
        Booking.check_out > check_in_date,
        Booking.status.in_(["CONFIRMED", "CHECKED_IN"])
    ).count()
    
    return booked_count


def get_demand_level(multiplier: float) -> str:
    """Convert demand multiplier to human-readable level"""
    if multiplier >= 1.3:
        return "Very High"
    elif multiplier >= 1.1:
        return "High"
    elif multiplier >= 0.9:
        return "Normal"
    elif multiplier >= 0.7:
        return "Low"
    else:
        return "Very Low"


def get_pricing_strategy(multiplier: float) -> str:
    """Get recommended pricing strategy based on demand"""
    if multiplier >= 1.3:
        return "Increase prices, reduce discounts"
    elif multiplier >= 1.1:
        return "Maintain premium pricing"
    elif multiplier >= 0.9:
        return "Standard pricing strategy"
    elif multiplier >= 0.7:
        return "Offer moderate discounts"
    else:
        return "Aggressive discounting to stimulate demand"


from datetime import timedelta
