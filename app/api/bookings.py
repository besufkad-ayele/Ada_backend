"""
API Routes — Bookings endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from app.database import get_db
from app.models.bookings import Booking, Guest, BookingStatus
from app.models.rooms import RoomType
from app.models.packages import Package

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


@router.get("/recent")
def get_recent_bookings(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent bookings for dashboard display."""
    bookings = db.query(Booking).filter(
        Booking.status != BookingStatus.CANCELLED
    ).order_by(desc(Booking.booking_date)).limit(limit).all()
    
    result = []
    for b in bookings:
        guest = db.query(Guest).get(b.guest_id)
        room_type = db.query(RoomType).get(b.room_type_id)
        package = None
        if b.package_id:
            package = db.query(Package).filter(Package.code == b.package_id).first()
        
        result.append({
            "id": b.id,
            "booking_ref": b.booking_ref,
            "guest_name": f"{guest.first_name} {guest.last_name}" if guest else "Unknown",
            "room_type": room_type.name if room_type else "Unknown",
            "check_in": b.check_in.isoformat(),
            "check_out": b.check_out.isoformat(),
            "nights": b.nights,
            "total_revenue_etb": round(b.total_revenue_etb, 2),
            "ai_segment": b.ai_segment,
            "booking_date": b.booking_date.isoformat(),
            "package_name": package.name if package else None,
        })
    
    return result


@router.get("/all")
def get_all_bookings(db: Session = Depends(get_db)):
    """Get all bookings for admin dashboard."""
    from app.models.destinations import Destination, DestinationRoomType
    from app.models.users import User
    
    bookings = db.query(Booking).order_by(desc(Booking.booking_date)).all()
    
    result = []
    for b in bookings:
        guest = db.query(Guest).get(b.guest_id)
        room_type = db.query(RoomType).get(b.room_type_id)
        user = db.query(User).get(b.user_id) if b.user_id else None
        
        # Try to find destination name from room type
        destination_name = "Unknown"
        if room_type:
            dest_room = db.query(DestinationRoomType).filter(
                DestinationRoomType.room_type == room_type.name
            ).first()
            if dest_room:
                destination = db.query(Destination).filter(
                    Destination.code == dest_room.destination_code
                ).first()
                if destination:
                    destination_name = destination.name
        
        result.append({
            "id": b.id,
            "booking_code": b.booking_ref,
            "guest_name": f"{guest.first_name} {guest.last_name}" if guest else "Unknown",
            "guest_email": guest.email if guest else "",
            "destination_name": destination_name,
            "room_type_name": room_type.name if room_type else "Unknown",
            "check_in": b.check_in.isoformat(),
            "check_out": b.check_out.isoformat(),
            "adults": b.adults,
            "children": b.children,
            "total_amount_etb": round(b.total_revenue_etb, 2),
            "payment_method": "card",  # Default for now
            "status": b.status.value.upper(),
            "created_at": b.booking_date.isoformat()
        })
    
    return result


@router.get("/user/{user_id}")
def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    """Get all bookings for a specific user."""
    from app.models.destinations import Destination, DestinationRoomType
    
    bookings = db.query(Booking).filter(Booking.user_id == user_id).order_by(desc(Booking.booking_date)).all()
    
    result = []
    for b in bookings:
        guest = db.query(Guest).get(b.guest_id)
        room_type = db.query(RoomType).get(b.room_type_id)
        
        # Try to find destination name from room type
        destination_name = "Unknown"
        if room_type:
            dest_room = db.query(DestinationRoomType).filter(
                DestinationRoomType.room_type == room_type.name
            ).first()
            if dest_room:
                destination = db.query(Destination).filter(
                    Destination.code == dest_room.destination_code
                ).first()
                if destination:
                    destination_name = destination.name
        
        result.append({
            "id": b.id,
            "booking_code": b.booking_ref,
            "destination_name": destination_name,
            "room_type_name": room_type.name if room_type else "Unknown",
            "check_in": b.check_in.isoformat(),
            "check_out": b.check_out.isoformat(),
            "adults": b.adults,
            "children": b.children,
            "total_amount_etb": round(b.total_revenue_etb, 2),
            "status": b.status.value.upper(),
            "created_at": b.booking_date.isoformat()
        })
    
    return result
