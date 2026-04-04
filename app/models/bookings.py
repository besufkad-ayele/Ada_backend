"""
Guest and booking models.
Tracks guest profiles, booking history, and attached services.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class GuestSegment(str, enum.Enum):
    INTERNATIONAL_LEISURE = "international_leisure"
    DOMESTIC_WEEKEND = "domestic_weekend"
    BUSINESS = "business"
    HONEYMOON = "honeymoon"
    FAMILY = "family"
    GROUP_TOUR = "group_tour"
    CONFERENCE = "conference"
    LONG_STAY = "long_stay"


class BookingChannel(str, enum.Enum):
    DIRECT = "direct"  # Hotel website
    OTA_BOOKING = "ota_booking"  # Booking.com
    OTA_EXPEDIA = "ota_expedia"
    PHONE = "phone"
    WALK_IN = "walk_in"
    CORPORATE = "corporate"
    TRAVEL_AGENT = "travel_agent"


class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    nationality = Column(String(50), default="Ethiopian")
    is_international = Column(Boolean, default=False)
    is_corporate = Column(Boolean, default=False)
    company_name = Column(String(200), nullable=True)
    loyalty_tier = Column(String(20), default="none")  # none, silver, gold, platinum
    total_stays = Column(Integer, default=0)
    total_spend_etb = Column(Float, default=0.0)
    segment = Column(SQLEnum(GuestSegment), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bookings = relationship("Booking", back_populates="guest")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_ref = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to registered user
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    room_type_id = Column(Integer, ForeignKey("room_types.id"), nullable=False)

    # Dates
    check_in = Column(Date, nullable=False, index=True)
    check_out = Column(Date, nullable=False)
    nights = Column(Integer, nullable=False)
    booking_date = Column(DateTime, nullable=False, index=True)
    lead_time_days = Column(Integer, nullable=False)  # Days between booking and check-in

    # Guests
    adults = Column(Integer, default=1)
    children = Column(Integer, default=0)

    # Pricing
    fare_class = Column(String(20), nullable=False)  # saver, standard, premium
    rate_etb = Column(Float, nullable=False)  # Nightly rate in ETB
    rate_usd = Column(Float, nullable=True)
    total_room_revenue_etb = Column(Float, nullable=False)
    total_package_revenue_etb = Column(Float, default=0.0)
    total_revenue_etb = Column(Float, nullable=False)

    # Package
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=True)
    package_discount_pct = Column(Float, default=0.0)
    package_accepted = Column(Boolean, default=False)

    # Booking details
    channel = Column(SQLEnum(BookingChannel), default=BookingChannel.DIRECT)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.CONFIRMED)
    is_refundable = Column(Boolean, default=True)
    special_requests = Column(Text, nullable=True)

    # AI metadata
    ai_segment = Column(SQLEnum(GuestSegment), nullable=True)
    ai_recommended_package_id = Column(Integer, nullable=True)
    ai_recommended_rate = Column(Float, nullable=True)
    actual_vs_ai_delta = Column(Float, nullable=True)  # How much we deviated from AI

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guest = relationship("Guest", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    room_type = relationship("RoomType")
    package = relationship("Package")
    services = relationship("BookingService", back_populates="booking")


class BookingService(Base):
    """Individual services attached to a booking (spa, dinner, transfer, etc.)"""
    __tablename__ = "booking_services"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    service_name = Column(String(200), nullable=False)
    service_category = Column(String(50), nullable=False)  # spa, dining, activity, transfer
    quantity = Column(Integer, default=1)
    unit_price_etb = Column(Float, nullable=False)
    total_price_etb = Column(Float, nullable=False)
    is_package_item = Column(Boolean, default=False)  # True if part of a package

    # Relationships
    booking = relationship("Booking", back_populates="services")
