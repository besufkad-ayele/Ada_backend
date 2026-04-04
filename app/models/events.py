"""
Events, competitor rates, and pricing audit log.
These feed into demand forecasting and pricing decisions.
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean
from datetime import datetime

from app.database import Base


class Event(Base):
    """
    Ethiopian holidays, festivals, local events, conferences that impact demand.
    Used as features in the demand forecasting model.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    event_type = Column(String(50), nullable=False)  # holiday, festival, conference, sport, cultural
    date_start = Column(Date, nullable=False, index=True)
    date_end = Column(Date, nullable=False)
    impact_level = Column(Integer, default=3)  # 1-5, how much it affects demand
    impact_direction = Column(String(10), default="positive")  # positive, negative
    is_national = Column(Boolean, default=True)
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    expected_demand_multiplier = Column(Float, default=1.0)  # 1.0 = no impact, 1.5 = 50% more demand


class CompetitorRate(Base):
    """
    Competitor hotel rates for benchmarking.
    Scraped or manually entered.
    """
    __tablename__ = "competitor_rates"

    id = Column(Integer, primary_key=True, index=True)
    competitor_name = Column(String(200), nullable=False)
    room_category = Column(String(50), nullable=False)  # Maps to our room types
    date = Column(Date, nullable=False, index=True)
    rate_etb = Column(Float, nullable=False)
    rate_usd = Column(Float, nullable=True)
    source = Column(String(100), default="manual")  # manual, booking_com, tripadvisor
    collected_at = Column(DateTime, default=datetime.utcnow)


class PricingLog(Base):
    """
    Audit trail of every pricing decision made by the AI.
    Critical for explainability and debugging.
    """
    __tablename__ = "pricing_logs"

    id = Column(Integer, primary_key=True, index=True)
    room_type_code = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # What the engine decided
    previous_rate = Column(Float, nullable=True)
    new_rate = Column(Float, nullable=False)
    fare_class = Column(String(20), nullable=False)

    # Why it decided
    occupancy_at_decision = Column(Float, nullable=False)
    days_until_arrival = Column(Integer, nullable=False)
    forecasted_demand = Column(Float, nullable=True)
    competitor_rate = Column(Float, nullable=True)
    event_impact = Column(Float, default=1.0)

    # Decision reasoning
    reason = Column(Text, nullable=True)  # Human-readable explanation
    model_version = Column(String(50), default="v1.0")
    confidence = Column(Float, nullable=True)

    # Outcome (filled in after the fact)
    was_booked = Column(Boolean, nullable=True)
    actual_revenue = Column(Float, nullable=True)
