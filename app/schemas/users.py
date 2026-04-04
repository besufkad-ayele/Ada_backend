"""
User authentication and profile schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=20)
    location: str = Field(..., min_length=2, max_length=100)
    fayda_fan_number: Optional[str] = Field(None, max_length=50)
    age: int = Field(..., ge=18, le=120)
    sex: str = Field(..., pattern="^(Male|Female|Other)$")
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user profile response"""
    id: int
    full_name: str
    email: str
    phone_number: str
    location: str
    fayda_fan_number: Optional[str]
    age: int
    sex: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    total_bookings: int
    total_spent_etb: int
    loyalty_points: int

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    fayda_fan_number: Optional[str] = Field(None, max_length=50)
    age: Optional[int] = Field(None, ge=18, le=120)
    sex: Optional[str] = Field(None, pattern="^(Male|Female|Other)$")


class AuthToken(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
