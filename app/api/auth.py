"""
User Authentication API
Handles registration, login, and profile management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models.users import User
from app.schemas.users import UserCreate, UserLogin, UserResponse, UserUpdate, AuthToken

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "kuraz-ai-hackathon-2026-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/signup", response_model=AuthToken, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if Fayda Fan number already exists (if provided)
    if user_data.fayda_fan_number:
        existing_fayda = db.query(User).filter(
            User.fayda_fan_number == user_data.fayda_fan_number
        ).first()
        if existing_fayda:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fayda Fan number already registered"
            )
    
    # Create new user
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        location=user_data.location,
        fayda_fan_number=user_data.fayda_fan_number,
        age=user_data.age,
        sex=user_data.sex,
        password_hash=hash_password(user_data.password),
        is_active=True,
        is_verified=False,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    # Return response with properly formatted user data
    return AuthToken(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            full_name=new_user.full_name,
            email=new_user.email,
            phone_number=new_user.phone_number,
            location=new_user.location,
            fayda_fan_number=new_user.fayda_fan_number,
            age=new_user.age,
            sex=new_user.sex,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            created_at=new_user.created_at,
            total_bookings=new_user.total_bookings,
            total_spent_etb=new_user.total_spent_etb,
            loyalty_points=new_user.loyalty_points,
        )
    )


@router.post("/login", response_model=AuthToken)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Return response with properly formatted user data
    return AuthToken(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone_number=user.phone_number,
            location=user.location,
            fayda_fan_number=user.fayda_fan_number,
            age=user.age,
            sex=user.sex,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            total_bookings=user.total_bookings,
            total_spent_etb=user.total_spent_etb,
            loyalty_points=user.loyalty_points,
        )
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current user profile
    Note: In production, extract user_id from JWT token
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    user_id: int,
    updates: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user profile
    Note: In production, extract user_id from JWT token
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/check-email/{email}")
def check_email_exists(email: str, db: Session = Depends(get_db)):
    """
    Check if email is already registered
    """
    user = db.query(User).filter(User.email == email).first()
    return {"exists": user is not None}
