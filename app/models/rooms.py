"""
Room-related database models.
Handles room types, individual rooms, and daily inventory tracking.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class RoomStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"


class FareClass(str, enum.Enum):
    SAVER = "saver"
    STANDARD = "standard"
    PREMIUM = "premium"


class RoomType(Base):
    __tablename__ = "room_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g. "standard", "deluxe"
    name = Column(String(100), nullable=False)  # "Standard Room", "Deluxe Lake View"
    description = Column(String(500))
    total_count = Column(Integer, nullable=False)
    max_occupancy = Column(Integer, default=2)
    base_rate_etb = Column(Float, nullable=False)
    base_rate_usd = Column(Float, nullable=False)
    floor_rate_etb = Column(Float, nullable=False)  # Minimum allowed rate
    ceiling_rate_etb = Column(Float, nullable=False)  # Maximum allowed rate
    amenities = Column(String(1000), default="")  # JSON string of amenities

    # Relationships
    rooms = relationship("Room", back_populates="room_type")
    daily_inventory = relationship("DailyInventory", back_populates="room_type")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type_id = Column(Integer, ForeignKey("room_types.id"), nullable=False)
    floor = Column(Integer, default=1)
    status = Column(SQLEnum(RoomStatus), default=RoomStatus.AVAILABLE)
    is_lake_view = Column(Boolean, default=False)

    # Relationships
    room_type = relationship("RoomType", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room")


class DailyInventory(Base):
    """
    Tracks room availability, pricing, and fare class status for each room type per date.
    This is the central table the pricing engine reads/writes.
    """
    __tablename__ = "daily_inventory"

    id = Column(Integer, primary_key=True, index=True)
    room_type_id = Column(Integer, ForeignKey("room_types.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)

    # Inventory counts
    total_rooms = Column(Integer, nullable=False)
    booked_rooms = Column(Integer, default=0)
    blocked_rooms = Column(Integer, default=0)
    available_rooms = Column(Integer, nullable=False)

    # Occupancy
    occupancy_rate = Column(Float, default=0.0)

    # Fare class availability
    saver_total = Column(Integer, default=0)
    saver_sold = Column(Integer, default=0)
    saver_open = Column(Boolean, default=True)

    standard_total = Column(Integer, default=0)
    standard_sold = Column(Integer, default=0)
    standard_open = Column(Boolean, default=True)

    premium_total = Column(Integer, default=0)
    premium_sold = Column(Integer, default=0)
    premium_open = Column(Boolean, default=True)

    # Current pricing (ETB)
    saver_rate = Column(Float, default=0.0)
    standard_rate = Column(Float, default=0.0)
    premium_rate = Column(Float, default=0.0)

    # AI-recommended rate
    ai_recommended_rate = Column(Float, nullable=True)
    ai_confidence = Column(Float, nullable=True)

    # Demand forecast
    forecasted_demand = Column(Float, nullable=True)
    forecasted_occupancy = Column(Float, nullable=True)

    # Competitor reference
    competitor_avg_rate = Column(Float, nullable=True)

    # Relationships
    room_type = relationship("RoomType", back_populates="daily_inventory")
