"""Pydantic schemas for the pricing engine API."""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date


class PriceRequest(BaseModel):
    """Request to get the current optimal price for a room type on a date."""
    room_type_code: str
    date: date
    guest_nationality: Optional[str] = None
    booking_channel: Optional[str] = None
    lead_time_days: Optional[int] = None
    adults: int = 1
    children: int = 0


class FareClassInfo(BaseModel):
    fare_class: str
    label: str
    rate_etb: float
    rate_usd: float
    available: bool
    rooms_remaining: int
    discount_pct: float
    refundable: bool
    changeable: bool


class PriceResponse(BaseModel):
    """Engine response with optimal pricing across all fare classes."""
    room_type_code: str
    room_type_name: str
    date: date
    base_rate_etb: float
    fare_classes: List[FareClassInfo]
    recommended_fare_class: str
    recommended_rate_etb: float
    recommended_rate_usd: float
    occupancy_rate: float
    demand_forecast: Optional[float] = None
    competitor_avg_rate: Optional[float] = None
    ai_confidence: Optional[float] = None
    pricing_reason: str = ""


class BulkPriceRequest(BaseModel):
    """Get prices for multiple dates and room types."""
    room_type_codes: List[str]
    start_date: date
    end_date: date
    guest_nationality: Optional[str] = None


class PriceOverrideRequest(BaseModel):
    """Manual price override by revenue manager."""
    room_type_code: str
    date: date
    fare_class: str
    new_rate_etb: float
    reason: str


class WhatIfRequest(BaseModel):
    """What-if simulation request."""
    scenario_type: str  # "block_rooms", "event", "discount", "competitor_change"
    room_type_code: Optional[str] = None
    date_start: date
    date_end: date
    parameters: Dict = {}
    description: str = ""


class WhatIfResponse(BaseModel):
    """What-if simulation results."""
    scenario_description: str
    baseline_revenue_etb: float
    projected_revenue_etb: float
    revenue_delta_etb: float
    revenue_delta_pct: float
    occupancy_impact: float
    recommendations: List[str]
    daily_breakdown: List[Dict] = []
