"""Pydantic schemas for package recommendation API."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class PackageComponentOut(BaseModel):
    service_name: str
    service_category: str
    description: Optional[str] = None
    retail_price_etb: float
    quantity: int

    class Config:
        from_attributes = True


class PackageOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: str
    base_price_etb: float
    acceptance_rate: float
    is_active: bool
    min_nights: int
    components: List[PackageComponentOut] = []

    class Config:
        from_attributes = True


class PackageRecommendationRequest(BaseModel):
    """Request a package recommendation for a booking."""
    guest_nationality: str = "Ethiopian"
    is_corporate: bool = False
    adults: int = 1
    children: int = 0
    check_in: date
    check_out: date
    room_type_code: str
    booking_channel: str = "direct"
    room_rate_etb: float  # The rate they're already getting


class PackageRecommendation(BaseModel):
    """AI-recommended package with dynamic pricing."""
    package_code: str
    package_name: str
    description: str
    components: List[PackageComponentOut]

    # Pricing
    individual_total_etb: float  # Sum of all items at retail
    package_price_etb: float  # Discounted bundle price
    discount_pct: float  # Applied discount
    savings_etb: float  # How much guest saves

    # Revenue impact
    revenue_uplift_etb: float  # Additional revenue vs room-only
    confidence: float  # AI confidence in this recommendation
    reason: str  # Why this package for this guest

    # Total booking value
    room_total_etb: float
    package_total_etb: float
    combined_total_etb: float


class PackageRecommendationResponse(BaseModel):
    """Top package recommendations for a booking."""
    guest_segment: str
    top_recommendation: PackageRecommendation
    alternatives: List[PackageRecommendation] = []
    estimated_acceptance_rate: float
