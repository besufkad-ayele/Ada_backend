"""
User Profile Models
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base


class User(Base):
    """User profile for booking system."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    
    # Personal Details
    location = Column(String, nullable=False)  # City/Country
    fayda_fan_number = Column(String, unique=True, nullable=True)  # Ethiopian loyalty program
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)  # Male/Female/Other
    
    # Account Info
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Booking Stats (updated by triggers/app logic)
    total_bookings = Column(Integer, default=0)
    total_spent_etb = Column(Integer, default=0)
    loyalty_points = Column(Integer, default=0)

    def __repr__(self):
        return f"<User {self.email}>"
