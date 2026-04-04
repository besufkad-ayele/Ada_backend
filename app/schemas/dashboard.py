"""Pydantic schemas for the revenue management dashboard API."""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date


class KPIMetrics(BaseModel):
    """Key Performance Indicators for the dashboard header."""
    # Revenue metrics
    revpar: float  # Revenue Per Available Room
    revpar_change_pct: float
    adr: float  # Average Daily Rate
    adr_change_pct: float
    trevpar: float  # Total Revenue Per Available Room (includes packages)
    trevpar_change_pct: float

    # Occupancy
    occupancy_rate: float
    occupancy_change_pct: float

    # Revenue totals
    total_room_revenue_etb: float
    total_package_revenue_etb: float
    total_revenue_etb: float
    total_revenue_change_pct: float

    # Bookings
    total_bookings: int
    package_attach_rate: float  # % of bookings with a package
    avg_lead_time_days: float

    # Period
    period_start: date
    period_end: date
    comparison_period: str  # "vs last month", "vs same period last year"


class RevenueTimeSeriesPoint(BaseModel):
    date: date
    room_revenue: float
    package_revenue: float
    total_revenue: float
    occupancy_rate: float
    adr: float
    revpar: float


class SegmentBreakdown(BaseModel):
    segment: str
    segment_label: str
    booking_count: int
    revenue_etb: float
    revenue_pct: float
    avg_rate_etb: float
    avg_nights: float
    package_attach_rate: float


class FareClassPerformance(BaseModel):
    fare_class: str
    label: str
    bookings: int
    revenue_etb: float
    avg_rate_etb: float
    fill_rate: float  # % of allocated inventory sold


class PricingHeatmapCell(BaseModel):
    date: date
    room_type_code: str
    rate_etb: float
    occupancy_rate: float
    fare_class_active: str
    demand_level: str  # "low", "medium", "high", "peak"


class DashboardData(BaseModel):
    """Complete dashboard payload."""
    kpis: KPIMetrics
    revenue_timeseries: List[RevenueTimeSeriesPoint]
    segment_breakdown: List[SegmentBreakdown]
    fare_class_performance: List[FareClassPerformance]
    pricing_heatmap: List[PricingHeatmapCell]
    recent_ai_actions: List[Dict] = []
    top_packages: List[Dict] = []


class AIInsight(BaseModel):
    """AI-generated insight or recommendation for the dashboard."""
    id: str
    category: str  # "pricing", "demand", "package", "alert"
    severity: str  # "info", "warning", "action"
    title: str
    message: str
    metric_impact: Optional[str] = None
    suggested_action: Optional[str] = None
    confidence: float = 0.0
