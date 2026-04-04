"""Pydantic schemas for room-related API requests and responses."""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class RoomTypeOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    total_count: int
    max_occupancy: int
    base_rate_etb: float
    base_rate_usd: float
    floor_rate_etb: float
    ceiling_rate_etb: float

    class Config:
        from_attributes = True


class DailyInventoryOut(BaseModel):
    id: int
    room_type_code: Optional[str] = None
    room_type_name: Optional[str] = None
    date: date
    total_rooms: int
    booked_rooms: int
    available_rooms: int
    occupancy_rate: float

    saver_open: bool
    standard_open: bool
    premium_open: bool
    saver_rate: float
    standard_rate: float
    premium_rate: float

    ai_recommended_rate: Optional[float] = None
    ai_confidence: Optional[float] = None
    forecasted_demand: Optional[float] = None
    forecasted_occupancy: Optional[float] = None
    competitor_avg_rate: Optional[float] = None

    class Config:
        from_attributes = True


class InventoryDateRange(BaseModel):
    room_type_code: str
    start_date: date
    end_date: date


class RoomAvailabilityOut(BaseModel):
    room_type: str
    date: date
    available: int
    lowest_rate_etb: float
    fare_classes: dict
