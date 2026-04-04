"""
API Routes — Pricing endpoints.
Core pricing engine, inventory management, and what-if simulation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional

from app.database import get_db
from app.engine.pricing import PricingEngine
from app.engine.inventory import InventoryManager
from app.schemas.pricing import (
    PriceRequest, PriceResponse, FareClassInfo,
    BulkPriceRequest, PriceOverrideRequest,
    WhatIfRequest, WhatIfResponse,
)

router = APIRouter(prefix="/api/pricing", tags=["Pricing Engine"])


@router.post("/optimal-price", response_model=PriceResponse)
def get_optimal_price(request: PriceRequest, db: Session = Depends(get_db)):
    """
    Get the AI-recommended optimal price for a room type on a date.
    Returns pricing for all fare classes (Saver, Standard, Premium).
    """
    engine = PricingEngine(db)
    try:
        result = engine.get_optimal_price(
            room_type_code=request.room_type_code,
            target_date=request.date,
            guest_nationality=request.guest_nationality,
            booking_channel=request.booking_channel,
            lead_time_days=request.lead_time_days,
        )
        return PriceResponse(
            room_type_code=result["room_type_code"],
            room_type_name=result["room_type_name"],
            date=result["date"],
            base_rate_etb=result["base_rate_etb"],
            fare_classes=[FareClassInfo(**fc) for fc in result["fare_classes"]],
            recommended_fare_class=result["recommended_fare_class"],
            recommended_rate_etb=result["recommended_rate_etb"],
            recommended_rate_usd=result["recommended_rate_usd"],
            occupancy_rate=result["occupancy_rate"],
            demand_forecast=result.get("demand_forecast"),
            competitor_avg_rate=result.get("competitor_avg_rate"),
            ai_confidence=result.get("ai_confidence"),
            pricing_reason=result["pricing_reason"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bulk-prices")
def get_bulk_prices(request: BulkPriceRequest, db: Session = Depends(get_db)):
    """
    Get prices for multiple dates and room types.
    Used for the pricing heatmap and calendar view.
    """
    engine = PricingEngine(db)
    results = engine.get_bulk_prices(
        room_type_codes=request.room_type_codes,
        start_date=request.start_date,
        end_date=request.end_date,
        guest_nationality=request.guest_nationality,
    )
    return {"prices": results}


@router.get("/inventory")
def get_inventory(
    start_date: date,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Get inventory summary for a date range."""
    if end_date is None:
        end_date = start_date + timedelta(days=30)
    manager = InventoryManager(db)
    return manager.get_inventory_summary(start_date, end_date)


@router.post("/update-fencing")
def update_fare_class_fencing(
    start_date: date,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Manually trigger fare class fencing update.
    Checks occupancy and lead time to open/close fare classes.
    """
    if end_date is None:
        end_date = start_date + timedelta(days=7)
    manager = InventoryManager(db)
    results = manager.update_all_inventory(start_date, end_date)
    return {
        "updated_dates": len(results),
        "changes": results,
    }


@router.post("/what-if", response_model=WhatIfResponse)
def run_what_if_simulation(request: WhatIfRequest, db: Session = Depends(get_db)):
    """
    Run a what-if revenue simulation.
    
    Scenarios:
    - block_rooms: Block N rooms for a group at X% discount
    - event: Simulate an event driving demand by X multiplier
    - discount: Run a promotion with X% discount
    - competitor_change: Simulate competitor price change
    """
    engine = PricingEngine(db)
    result = engine.run_what_if(
        scenario_type=request.scenario_type,
        room_type_code=request.room_type_code,
        date_start=request.date_start,
        date_end=request.date_end,
        parameters=request.parameters,
    )
    return WhatIfResponse(**result)


@router.get("/multipliers/{room_type_code}/{target_date}")
def get_price_multipliers(
    room_type_code: str,
    target_date: date,
    db: Session = Depends(get_db),
):
    """
    Get the breakdown of all price multipliers for explainability.
    Shows exactly WHY the AI set a specific price.
    """
    engine = PricingEngine(db)
    try:
        result = engine.get_optimal_price(room_type_code, target_date)
        return {
            "room_type": room_type_code,
            "date": target_date.isoformat(),
            "base_rate_etb": result["base_rate_etb"],
            "recommended_rate_etb": result["recommended_rate_etb"],
            "multipliers": result["multiplier_breakdown"],
            "reason": result["pricing_reason"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.get("/room-types")
def get_room_types(db: Session = Depends(get_db)):
    """Get all available room types with their details."""
    from app.models.rooms import RoomType
    
    room_types = db.query(RoomType).all()
    
    return [
        {
            "id": rt.id,
            "code": rt.code,
            "name": rt.name,
            "description": rt.description,
            "base_rate_etb": rt.base_rate_etb,
            "floor_rate_etb": rt.floor_rate_etb,
            "ceiling_rate_etb": rt.ceiling_rate_etb,
            "max_occupancy": rt.max_occupancy,
            "total_count": rt.total_count,
            "amenities": rt.amenities.split(",") if rt.amenities else [],
        }
        for rt in room_types
    ]
