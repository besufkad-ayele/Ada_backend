"""
API Routes — Dashboard analytics endpoints.
Provides KPIs, time series, segment breakdown, and AI insights.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, timedelta
from typing import Optional

from app.database import get_db
from app.models.rooms import RoomType, DailyInventory
from app.models.bookings import Booking, Guest, BookingStatus
from app.models.packages import Package
from app.config import get_settings
from app.data.ethiopian_calendar import get_ethiopian_holidays
from app.engine.gemini import generate_market_insights_with_gemini

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
settings = get_settings()

# In-memory activity log for demo (in production, use Redis or DB)
_ai_activity_log = []


@router.get("/kpis")
def get_kpis(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Get Key Performance Indicators for the dashboard header.
    RevPAR, ADR, Occupancy, TRevPAR, and more.
    """
    if period_end is None:
        period_end = date.today()
    if period_start is None:
        period_start = period_end - timedelta(days=30)

    # Comparison period (same length, immediately before)
    period_length = (period_end - period_start).days
    comp_start = period_start - timedelta(days=period_length)
    comp_end = period_start - timedelta(days=1)

    # Current period metrics
    current = _calculate_period_metrics(db, period_start, period_end)
    comparison = _calculate_period_metrics(db, comp_start, comp_end)

    # Calculate changes
    def pct_change(current_val, prev_val):
        if prev_val == 0:
            return 0.0
        return round((current_val - prev_val) / prev_val * 100, 2)

    total_rooms = settings.RESORT_TOTAL_ROOMS
    days = max(1, period_length)
    available_room_nights = total_rooms * days

    # RevPAR = Total Room Revenue / Available Room Nights
    revpar = current["total_room_revenue"] / max(1, available_room_nights)
    prev_revpar = comparison["total_room_revenue"] / max(1, available_room_nights)

    # ADR = Total Room Revenue / Rooms Sold
    adr = current["total_room_revenue"] / max(1, current["rooms_sold"])
    prev_adr = comparison["total_room_revenue"] / max(1, comparison["rooms_sold"])

    # TRevPAR = Total Revenue (rooms + packages) / Available Room Nights
    trevpar = current["total_revenue"] / max(1, available_room_nights)
    prev_trevpar = comparison["total_revenue"] / max(1, available_room_nights)

    # Occupancy
    occupancy = current["rooms_sold"] / max(1, available_room_nights)
    prev_occupancy = comparison["rooms_sold"] / max(1, available_room_nights)

    return {
        "revpar": round(revpar, 2),
        "revpar_change_pct": pct_change(revpar, prev_revpar),
        "adr": round(adr, 2),
        "adr_change_pct": pct_change(adr, prev_adr),
        "trevpar": round(trevpar, 2),
        "trevpar_change_pct": pct_change(trevpar, prev_trevpar),
        "occupancy_rate": round(occupancy, 4),
        "occupancy_change_pct": pct_change(occupancy, prev_occupancy),
        "total_room_revenue_etb": round(current["total_room_revenue"], 2),
        "total_package_revenue_etb": round(current["total_package_revenue"], 2),
        "total_revenue_etb": round(current["total_revenue"], 2),
        "total_revenue_change_pct": pct_change(current["total_revenue"], comparison["total_revenue"]),
        "total_bookings": current["total_bookings"],
        "package_attach_rate": round(current["package_attach_rate"], 4),
        "avg_lead_time_days": round(current["avg_lead_time"], 1),
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "comparison_period": f"vs {comp_start} to {comp_end}",
    }


@router.get("/revenue-timeseries")
def get_revenue_timeseries(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Get daily revenue time series for charts."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=90)

    total_rooms = settings.RESORT_TOTAL_ROOMS

    # Single query — fetch all bookings in range, then aggregate in Python
    bookings = db.query(Booking).filter(
        Booking.check_in >= start_date,
        Booking.check_in <= end_date,
        Booking.status != BookingStatus.CANCELLED,
    ).all()

    # Group by check_in date
    by_date: dict = {}
    current = start_date
    while current <= end_date:
        by_date[current.isoformat()] = {
            "date": current.isoformat(),
            "room_revenue": 0.0,
            "package_revenue": 0.0,
            "rooms_sold": 0,
        }
        current += timedelta(days=1)

    for b in bookings:
        key = b.check_in.isoformat()
        if key in by_date:
            by_date[key]["room_revenue"] += b.total_room_revenue_etb / max(1, b.nights)
            if b.package_accepted:
                by_date[key]["package_revenue"] += b.total_package_revenue_etb / max(1, b.nights)
            by_date[key]["rooms_sold"] += 1

    results = []
    for entry in by_date.values():
        room_rev = entry["room_revenue"]
        pkg_rev = entry["package_revenue"]
        rooms_sold = entry["rooms_sold"]
        adr = room_rev / max(1, rooms_sold)
        results.append({
            "date": entry["date"],
            "room_revenue": round(room_rev, 2),
            "package_revenue": round(pkg_rev, 2),
            "total_revenue": round(room_rev + pkg_rev, 2),
            "occupancy_rate": round(rooms_sold / max(1, total_rooms), 4),
            "adr": round(adr, 2),
            "revpar": round(room_rev / total_rooms, 2),
        })

    return results


@router.get("/segment-breakdown")
def get_segment_breakdown(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Get booking breakdown by guest segment."""
    if period_end is None:
        period_end = date.today()
    if period_start is None:
        period_start = period_end - timedelta(days=30)

    bookings = db.query(Booking).filter(
        Booking.check_in >= period_start,
        Booking.check_in <= period_end,
        Booking.status != BookingStatus.CANCELLED,
    ).all()

    if not bookings:
        return []

    # Group by segment
    segments = {}
    total_revenue = sum(b.total_revenue_etb for b in bookings)

    for b in bookings:
        seg = b.ai_segment or "unknown"
        if seg not in segments:
            segments[seg] = {
                "segment": seg,
                "booking_count": 0,
                "revenue_etb": 0.0,
                "total_rate": 0.0,
                "total_nights": 0,
                "packages_accepted": 0,
            }
        segments[seg]["booking_count"] += 1
        segments[seg]["revenue_etb"] += b.total_revenue_etb
        segments[seg]["total_rate"] += b.rate_etb
        segments[seg]["total_nights"] += b.nights
        if b.package_accepted:
            segments[seg]["packages_accepted"] += 1

    result = []
    segment_labels = {
        "international_leisure": "International Leisure",
        "domestic_weekend": "Domestic Weekend",
        "business": "Business",
        "honeymoon": "Honeymoon",
        "family": "Family",
        "group_tour": "Group Tour",
        "conference": "Conference",
        "long_stay": "Long Stay",
        "unknown": "Unknown",
    }

    for seg, data in segments.items():
        count = data["booking_count"]
        result.append({
            "segment": seg,
            "segment_label": segment_labels.get(seg, seg),
            "booking_count": count,
            "revenue_etb": round(data["revenue_etb"], 2),
            "revenue_pct": round(data["revenue_etb"] / max(1, total_revenue) * 100, 2),
            "avg_rate_etb": round(data["total_rate"] / max(1, count), 2),
            "avg_nights": round(data["total_nights"] / max(1, count), 2),
            "package_attach_rate": round(data["packages_accepted"] / max(1, count), 4),
        })

    result.sort(key=lambda x: x["revenue_etb"], reverse=True)
    return result


@router.get("/fare-class-performance")
def get_fare_class_performance(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Get performance metrics by fare class."""
    if period_end is None:
        period_end = date.today()
    if period_start is None:
        period_start = period_end - timedelta(days=30)

    bookings = db.query(Booking).filter(
        Booking.check_in >= period_start,
        Booking.check_in <= period_end,
        Booking.status != BookingStatus.CANCELLED,
    ).all()

    classes = {}
    for b in bookings:
        fc = b.fare_class
        if fc not in classes:
            classes[fc] = {
                "bookings": 0,
                "revenue_etb": 0.0,
                "total_rate": 0.0,
            }
        classes[fc]["bookings"] += 1
        classes[fc]["revenue_etb"] += b.total_room_revenue_etb
        classes[fc]["total_rate"] += b.rate_etb

    labels = {
        "saver": "Saver / Advance Purchase",
        "standard": "Standard / Flexible",
        "premium": "Premium / Last Minute",
    }
    total_bookings = sum(c["bookings"] for c in classes.values())

    return [
        {
            "fare_class": fc,
            "label": labels.get(fc, fc),
            "bookings": data["bookings"],
            "revenue_etb": round(data["revenue_etb"], 2),
            "avg_rate_etb": round(data["total_rate"] / max(1, data["bookings"]), 2),
            "fill_rate": round(data["bookings"] / max(1, total_bookings), 4),
        }
        for fc, data in classes.items()
    ]


@router.get("/pricing-heatmap")
def get_pricing_heatmap(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Get pricing heatmap data for the calendar view."""
    if end_date is None:
        end_date = date.today() + timedelta(days=30)
    if start_date is None:
        start_date = date.today()

    inventories = db.query(DailyInventory).filter(
        DailyInventory.date >= start_date,
        DailyInventory.date <= end_date,
    ).all()

    result = []
    for inv in inventories:
        rt = db.query(RoomType).get(inv.room_type_id)
        if not rt:
            continue

        # Determine demand level
        occ = inv.occupancy_rate or 0
        if occ >= 0.85:
            demand = "peak"
        elif occ >= 0.65:
            demand = "high"
        elif occ >= 0.45:
            demand = "medium"
        else:
            demand = "low"

        # Determine active fare class
        if inv.saver_open:
            active_fc = "saver"
        elif inv.standard_open:
            active_fc = "standard"
        else:
            active_fc = "premium"

        # Use the active fare class rate
        rate = getattr(inv, f"{active_fc}_rate", rt.base_rate_etb)

        result.append({
            "date": inv.date.isoformat(),
            "room_type_code": rt.code,
            "room_type_name": rt.name,
            "rate_etb": round(rate, 2),
            "occupancy_rate": round(occ, 4),
            "fare_class_active": active_fc,
            "demand_level": demand,
            "saver_open": inv.saver_open,
            "standard_open": inv.standard_open,
            "premium_open": inv.premium_open,
            "available_rooms": inv.available_rooms,
        })

    return result


@router.get("/analyze-pricing")
def analyze_pricing_data_with_ai(db: Session = Depends(get_db)):
    """Passes the upcoming 30 day heatmap matrix to Gemini and asks for strategic insights."""
    heatmap_data = get_pricing_heatmap(start_date=date.today(), end_date=date.today() + timedelta(days=14), db=db)
    
    try:
        insight_text = generate_market_insights_with_gemini(heatmap_data)
        return {"insight": insight_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-insights")
def get_ai_insights(db: Session = Depends(get_db)):
    """
    Generate AI-driven insights and recommendations.
    These appear in the dashboard as actionable alerts.
    """
    insights = []
    today = date.today()

    # Check upcoming high-demand periods
    from app.models.events import Event
    upcoming_events = db.query(Event).filter(
        Event.date_start >= today,
        Event.date_start <= today + timedelta(days=14),
    ).all()

    for event in upcoming_events:
        days_until = (event.date_start - today).days
        insights.append({
            "id": f"event_{event.id}",
            "category": "demand",
            "severity": "action" if days_until <= 5 else "warning",
            "title": f"{event.name} in {days_until} days",
            "message": (
                f"{event.name} is {days_until} days away. Expected demand increase of "
                f"{(event.expected_demand_multiplier - 1) * 100:.0f}%. "
                f"Consider closing Saver fare class for Deluxe and Suite rooms."
            ),
            "metric_impact": f"+{(event.expected_demand_multiplier - 1) * 100:.0f}% demand",
            "suggested_action": "Close Saver class, increase Standard rates by 15-25%",
            "confidence": 0.85,
        })

    # Check low occupancy dates
    low_occ = db.query(DailyInventory).filter(
        DailyInventory.date >= today,
        DailyInventory.date <= today + timedelta(days=14),
        DailyInventory.occupancy_rate < 0.35,
    ).all()

    if low_occ:
        dates = set(inv.date for inv in low_occ)
        insights.append({
            "id": "low_occ_alert",
            "category": "pricing",
            "severity": "warning",
            "title": f"Low occupancy on {len(dates)} upcoming dates",
            "message": (
                f"{len(dates)} dates in the next 2 weeks have occupancy below 35%. "
                f"Consider running a flash promotion or opening additional Saver inventory."
            ),
            "metric_impact": f"{len(dates)} dates below 35% occupancy",
            "suggested_action": "Launch 'Last Minute Escape' package with 20% discount",
            "confidence": 0.80,
        })

    # Package performance insight
    top_packages = db.query(Package).filter(
        Package.acceptance_rate > 0.50
    ).order_by(Package.acceptance_rate.desc()).limit(3).all()

    if top_packages:
        pkg_names = ", ".join(p.name for p in top_packages)
        insights.append({
            "id": "package_performance",
            "category": "package",
            "severity": "info",
            "title": "Top performing packages",
            "message": f"Highest acceptance rates: {pkg_names}. Consider featuring these in promotional campaigns.",
            "metric_impact": "Package attach rate optimization",
            "suggested_action": "Feature top packages on booking confirmation page",
            "confidence": 0.90,
        })

    # Revenue trend insight
    insights.append({
        "id": "revenue_trend",
        "category": "pricing",
        "severity": "info",
        "title": "Revenue optimization active",
        "message": (
            "Dynamic pricing engine is actively optimizing across all room types. "
            "Fare class fencing is automatically adjusting based on occupancy thresholds."
        ),
        "metric_impact": "Continuous optimization",
        "suggested_action": "Review pricing multiplier breakdown for fine-tuning",
        "confidence": 0.95,
    })

    return insights


@router.get("/ai-activity")
def get_ai_activity():
    """Get recent AI pricing decisions and actions."""
    # Return last 20 activities
    return _ai_activity_log[-20:] if _ai_activity_log else []


@router.post("/trigger-ai-update")
def trigger_ai_update(db: Session = Depends(get_db)):
    """
    Manually trigger the AI pricing engine to recalculate rates.
    This simulates the AI actively working and making decisions.
    """
    from app.engine.pricing import PricingEngine
    from datetime import datetime
    import uuid
    
    engine = PricingEngine(db)
    today = date.today()
    
    # Get all room types
    room_types = db.query(RoomType).all()
    
    activities = []
    for rt in room_types:
        # Calculate pricing for next 7 days
        for days_ahead in range(7):
            target_date = today + timedelta(days=days_ahead)
            
            try:
                # Get current inventory
                inventory = db.query(DailyInventory).filter(
                    DailyInventory.room_type_id == rt.id,
                    DailyInventory.date == target_date,
                ).first()
                
                old_rate = inventory.standard_rate if inventory else None
                
                # Run pricing engine
                pricing = engine.get_optimal_price(
                    room_type_code=rt.code,
                    target_date=target_date,
                )
                
                new_rate = pricing["recommended_rate_etb"]
                
                # Update inventory with new rates
                if inventory:
                    inventory.standard_rate = new_rate
                    inventory.saver_rate = new_rate * 0.85
                    inventory.premium_rate = new_rate * 1.15
                    db.commit()
                
                # Log activity
                if old_rate and abs(new_rate - old_rate) > 10:  # Only log significant changes
                    activity = {
                        "id": str(uuid.uuid4()),
                        "timestamp": datetime.now().isoformat(),
                        "action_type": "price_update",
                        "room_type": rt.name,
                        "old_rate": round(old_rate, 2),
                        "new_rate": round(new_rate, 2),
                        "reason": pricing["pricing_reason"][:150],
                        "confidence": pricing["ai_confidence"],
                    }
                    activities.append(activity)
                    _ai_activity_log.append(activity)
                    
            except Exception as e:
                print(f"Error updating pricing for {rt.code}: {e}")
                continue
    
    # Keep only last 100 activities in memory
    if len(_ai_activity_log) > 100:
        _ai_activity_log[:] = _ai_activity_log[-100:]
    
    return {
        "success": True,
        "updates_made": len(activities),
        "message": f"AI engine updated pricing for {len(activities)} room-date combinations",
        "activities": activities,
    }


def _calculate_period_metrics(db: Session, start: date, end: date) -> dict:
    """Calculate metrics for a date period."""
    bookings = db.query(Booking).filter(
        Booking.check_in >= start,
        Booking.check_in <= end,
        Booking.status != BookingStatus.CANCELLED,
    ).all()

    total_room_rev = sum(b.total_room_revenue_etb for b in bookings)
    total_pkg_rev = sum(b.total_package_revenue_etb for b in bookings)
    rooms_sold = sum(b.nights for b in bookings)
    packages = sum(1 for b in bookings if b.package_accepted)
    total = len(bookings)
    avg_lead = sum(b.lead_time_days for b in bookings) / max(1, total)

    return {
        "total_room_revenue": total_room_rev,
        "total_package_revenue": total_pkg_rev,
        "total_revenue": total_room_rev + total_pkg_rev,
        "rooms_sold": rooms_sold,
        "total_bookings": total,
        "package_attach_rate": packages / max(1, total),
        "avg_lead_time": avg_lead,
    }



@router.get("/ethiopian-events")
def get_ethiopian_events(db: Session = Depends(get_db)):
    """
    Get upcoming Ethiopian calendar events with AI pricing impact.
    Shows how the AI adjusts room rates based on Ethiopian holidays and festivals.
    """
    today = date.today()
    current_year = today.year
    
    # Get Ethiopian holidays for current and next year
    holidays = get_ethiopian_holidays(current_year)
    if today.month >= 10:  # Also get next year's events
        holidays.extend(get_ethiopian_holidays(current_year + 1))
    
    # Filter to upcoming events (next 90 days)
    upcoming = []
    for event in holidays:
        days_until = (event["date_start"] - today).days
        if 0 <= days_until <= 90:
            # Calculate pricing impact using a standard room type
            standard_room = db.query(RoomType).filter(RoomType.code == "standard").first()
            base_rate = standard_room.base_rate_etb if standard_room else 5000
            
            event_rate = base_rate * event["demand_multiplier"]
            increase_pct = (event["demand_multiplier"] - 1) * 100
            
            upcoming.append({
                "name": event["name"],
                "date_start": event["date_start"].isoformat(),
                "date_end": event["date_end"].isoformat(),
                "event_type": event["event_type"],
                "impact_level": event["impact_level"],
                "demand_multiplier": event["demand_multiplier"],
                "description": event["description"],
                "days_until": days_until,
                "pricing_impact": {
                    "base_rate": round(base_rate, 2),
                    "event_rate": round(event_rate, 2),
                    "increase_pct": round(increase_pct, 1),
                }
            })
    
    # Sort by date
    upcoming.sort(key=lambda x: x["date_start"])
    
    return {
        "events": upcoming,
        "total_events": len(upcoming),
        "highest_impact": max((e["impact_level"] for e in upcoming), default=0),
    }
