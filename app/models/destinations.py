"""
Kuriftu Destinations Model
"""
from sqlalchemy import Column, Integer, String, Float, Text, Boolean
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base


class Destination(Base):
    """Kuriftu Resort Destinations"""
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g., "ENTOTO", "AWASH"
    name = Column(String, nullable=False)  # e.g., "Kuriftu Entoto Adventure Park"
    location = Column(String, nullable=False)  # City/Region
    description = Column(Text, nullable=True)
    
    # Amenities
    amenities = Column(Text, nullable=True)  # JSON string of amenities
    
    # Status
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Destination {self.code}: {self.name}>"


class DestinationRoomType(Base):
    """Room types available at each destination"""
    __tablename__ = "destination_room_types"

    id = Column(Integer, primary_key=True, index=True)
    destination_code = Column(String, nullable=False, index=True)
    room_type = Column(String, nullable=False)  # "STANDARD", "DELUXE", "SUITE"
    room_type_name = Column(String, nullable=False)  # "Standard Room", "Deluxe Room", "Executive Suite"
    
    # Inventory
    total_rooms = Column(Integer, nullable=False)  # Total rooms of this type
    
    # Pricing
    base_rate_etb = Column(Float, nullable=False)
    base_rate_usd = Column(Float, nullable=False)
    
    # Room Details
    max_occupancy = Column(Integer, nullable=False)
    size_sqm = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    amenities = Column(Text, nullable=True)  # JSON string
    
    # Services included
    services_included = Column(Text, nullable=True)  # JSON string: ["WiFi", "Breakfast", "Pool Access"]
    
    def __repr__(self):
        return f"<DestinationRoomType {self.destination_code}-{self.room_type}>"
