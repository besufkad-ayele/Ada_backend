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
