"""
API Routes — User profile and management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.bookings import Guest, Booking, BookingStatus

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/profile/{email}")
def get_user_profile(email: str, db: Session = Depends(get_db)):
    """Get user profile with loyalty information."""
    guest = db.query(Guest).filter(Guest.email == email).first()
    
    if not guest:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate loyalty points (1 point per 100 ETB spent)
    loyalty_points = int(guest.total_spend_etb / 100)
    
    # Determine next tier and progress
    tier_info = _get_tier_info(guest.loyalty_tier, guest.total_spend_etb)
    
    return {
        "id": guest.id,
        "first_name": guest.first_name,
        "last_name": guest.last_name,
        "email": guest.email,
        "phone": guest.phone,
        "nationality": guest.nationality,
        "is_corporate": guest.is_corporate,
        "company_name": guest.company_name,
        "loyalty_tier": guest.loyalty_tier,
        "loyalty_points": loyalty_points,
        "total_stays": guest.total_stays,
        "total_spend_etb": round(guest.total_spend_etb, 2),
        "segment": guest.segment,
        "member_since": guest.created_at.isoformat() if guest.created_at else None,
        "tier_info": tier_info,
    }


@router.get("/profile/{email}/bookings")
def get_user_bookings(
    email: str,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get user's booking history."""
    guest = db.query(Guest).filter(Guest.email == email).first()
    
    if not guest:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(Booking).filter(Booking.guest_id == guest.id)
    
    if status:
        query = query.filter(Booking.status == status)
    
    bookings = query.order_by(desc(Booking.booking_date)).limit(limit).all()
    
    result = []
    for b in bookings:
        from app.models.rooms import RoomType
        room_type = db.query(RoomType).get(b.room_type_id)
        
        result.append({
            "booking_ref": b.booking_ref,
            "room_type": room_type.name if room_type else "Unknown",
            "check_in": b.check_in.isoformat(),
            "check_out": b.check_out.isoformat(),
            "nights": b.nights,
            "adults": b.adults,
            "children": b.children,
            "status": b.status.value,
            "total_revenue_etb": round(b.total_revenue_etb, 2),
            "package_accepted": b.package_accepted,
            "booking_date": b.booking_date.isoformat(),
            "fare_class": b.fare_class,
        })
    
    return {
        "bookings": result,
        "total_bookings": len(result),
    }


@router.put("/profile/{email}")
def update_user_profile(
    email: str,
    profile_data: dict,
    db: Session = Depends(get_db)
):
    """Update user profile information."""
    guest = db.query(Guest).filter(Guest.email == email).first()
    
    if not guest:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update allowed fields
    if "first_name" in profile_data:
        guest.first_name = profile_data["first_name"]
    if "last_name" in profile_data:
        guest.last_name = profile_data["last_name"]
    if "phone" in profile_data:
        guest.phone = profile_data["phone"]
    if "nationality" in profile_data:
        guest.nationality = profile_data["nationality"]
    if "company_name" in profile_data:
        guest.company_name = profile_data["company_name"]
    
    db.commit()
    db.refresh(guest)
    
    return {"success": True, "message": "Profile updated successfully"}


@router.get("/admin/all")
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    tier: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all users for admin management (requires admin auth in production)."""
    query = db.query(Guest)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Guest.first_name.ilike(search_term)) |
            (Guest.last_name.ilike(search_term)) |
            (Guest.email.ilike(search_term))
        )
    
    if tier and tier != "all":
        query = query.filter(Guest.loyalty_tier == tier)
    
    total = query.count()
    guests = query.order_by(desc(Guest.total_spend_etb)).offset(skip).limit(limit).all()
    
    result = []
    for guest in guests:
        loyalty_points = int(guest.total_spend_etb / 100)
        result.append({
            "id": guest.id,
            "name": f"{guest.first_name} {guest.last_name}",
            "email": guest.email,
            "phone": guest.phone,
            "nationality": guest.nationality,
            "loyalty_tier": guest.loyalty_tier,
            "loyalty_points": loyalty_points,
            "total_stays": guest.total_stays,
            "total_spend_etb": round(guest.total_spend_etb, 2),
            "segment": guest.segment.value if guest.segment else None,
            "is_corporate": guest.is_corporate,
            "member_since": guest.created_at.isoformat() if guest.created_at else None,
        })
    
    return {
        "users": result,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
    }


@router.put("/admin/user/{user_id}/tier")
def update_user_tier(
    user_id: int,
    tier_data: dict,
    db: Session = Depends(get_db)
):
    """Update user loyalty tier (admin only)."""
    guest = db.query(Guest).get(user_id)
    
    if not guest:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_tier = tier_data.get("tier")
    if new_tier not in ["none", "silver", "gold", "platinum"]:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    guest.loyalty_tier = new_tier
    db.commit()
    
    return {"success": True, "message": f"User tier updated to {new_tier}"}


@router.get("/admin/stats")
def get_user_stats(db: Session = Depends(get_db)):
    """Get user statistics for admin dashboard."""
    total_users = db.query(Guest).count()
    
    tier_counts = {
        "none": db.query(Guest).filter(Guest.loyalty_tier == "none").count(),
        "silver": db.query(Guest).filter(Guest.loyalty_tier == "silver").count(),
        "gold": db.query(Guest).filter(Guest.loyalty_tier == "gold").count(),
        "platinum": db.query(Guest).filter(Guest.loyalty_tier == "platinum").count(),
    }
    
    # Top spenders
    top_spenders = db.query(Guest).order_by(desc(Guest.total_spend_etb)).limit(10).all()
    
    return {
        "total_users": total_users,
        "tier_distribution": tier_counts,
        "top_spenders": [
            {
                "name": f"{g.first_name} {g.last_name}",
                "email": g.email,
                "total_spend_etb": round(g.total_spend_etb, 2),
                "loyalty_tier": g.loyalty_tier,
            }
            for g in top_spenders
        ],
    }


def _get_tier_info(current_tier: str, total_spend: float):
    """Calculate tier progress and benefits."""
    tiers = {
        "none": {
            "name": "Member",
            "min_spend": 0,
            "benefits": ["Standard booking", "Email notifications"],
            "discount": 0,
        },
        "silver": {
            "name": "Silver",
            "min_spend": 10000,
            "benefits": ["5% discount", "Early check-in", "Late checkout (subject to availability)"],
            "discount": 0.05,
        },
        "gold": {
            "name": "Gold",
            "min_spend": 50000,
            "benefits": ["10% discount", "Room upgrade (subject to availability)", "Welcome amenity", "Priority support"],
            "discount": 0.10,
        },
        "platinum": {
            "name": "Platinum",
            "min_spend": 150000,
            "benefits": ["15% discount", "Guaranteed room upgrade", "Complimentary spa treatment", "VIP concierge", "Airport transfer"],
            "discount": 0.15,
        },
    }
    
    current = tiers[current_tier]
    
    # Find next tier
    next_tier = None
    spend_to_next = 0
    
    tier_order = ["none", "silver", "gold", "platinum"]
    current_index = tier_order.index(current_tier)
    
    if current_index < len(tier_order) - 1:
        next_tier_key = tier_order[current_index + 1]
        next_tier = tiers[next_tier_key]
        spend_to_next = next_tier["min_spend"] - total_spend
    
    progress = 0
    if next_tier:
        tier_range = next_tier["min_spend"] - current["min_spend"]
        current_progress = total_spend - current["min_spend"]
        progress = min(100, int((current_progress / tier_range) * 100))
    else:
        progress = 100  # Already at max tier
    
    return {
        "current_tier": current,
        "next_tier": next_tier,
        "spend_to_next_tier": max(0, spend_to_next),
        "progress_percent": progress,
    }



@router.get("/{user_id}")
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID for user dashboard."""
    from app.models.users import User
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "location": user.location,
        "age": user.age,
        "sex": user.sex,
        "role": "user",  # Default role
        "loyalty_points": user.loyalty_points or 0,
        "total_bookings": user.total_bookings or 0,
        "total_spent_etb": user.total_spent_etb or 0,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/list")
def get_all_users_list(db: Session = Depends(get_db)):
    """Get all users for admin user management page."""
    from app.models.users import User
    
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "location": user.location,
            "age": user.age,
            "sex": user.sex,
            "role": "user",  # Default role
            "is_active": user.is_active,
            "total_bookings": user.total_bookings or 0,
            "total_spent_etb": user.total_spent_etb or 0,
            "loyalty_points": user.loyalty_points or 0,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    
    return result
