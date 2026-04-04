"""Pydantic schemas for booking-related endpoints."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class BookingCreate(BaseModel):
    guest_first_name: str
    guest_last_name: str
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_nationality: str = "Ethiopian"
    is_corporate: bool = False
    company_name: Optional[str] = None

    room_type_code: str
    check_in: date
    check_out: date
    adults: int = 1
    children: int = 0
    channel: str = "direct"

    # Package
    package_code: Optional[str] = None
    accept_package: bool = False

    special_requests: Optional[str] = None


class BookingServiceOut(BaseModel):
    service_name: str
    service_category: str
    quantity: int
    unit_price_etb: float
    total_price_etb: float
    is_package_item: bool

    class Config:
        from_attributes = True


class BookingOut(BaseModel):
    id: int
    booking_ref: str
    guest_name: str
    room_type: str
    check_in: date
    check_out: date
    nights: int
    adults: int
    children: int
    fare_class: str
    rate_etb: float
    total_room_revenue_etb: float
    total_package_revenue_etb: float
    total_revenue_etb: float
    channel: str
    status: str
    package_name: Optional[str] = None
    package_discount_pct: float = 0.0
    ai_segment: Optional[str] = None
    booking_date: datetime
    lead_time_days: int
    services: List[BookingServiceOut] = []

    class Config:
        from_attributes = True


class GuestOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    nationality: str
    is_international: bool
    is_corporate: bool
    loyalty_tier: str
    total_stays: int
    total_spend_etb: float
    segment: Optional[str] = None

    class Config:
        from_attributes = True
