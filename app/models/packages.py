"""
Package models.
Pre-defined service bundles that the AI recommends to guests based on segmentation.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Package(Base):
    """
    Pre-defined resort packages (e.g., Romance Escape, Family Getaway).
    These are NOT individually priced by AI — the AI picks WHICH package
    to recommend and sets the DISCOUNT dynamically.
    """
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # romance, family, business, wellness, adventure, conference

    # Target guest segments (comma-separated)
    target_segments = Column(String(500), nullable=False)

    # Pricing
    base_price_etb = Column(Float, nullable=False)  # Sum of component costs
    min_discount_pct = Column(Float, default=0.05)  # Minimum 5% discount
    max_discount_pct = Column(Float, default=0.25)  # Maximum 25% discount
    margin_floor_pct = Column(Float, default=0.15)  # Never go below 15% margin

    # Stats
    times_offered = Column(Integer, default=0)
    times_accepted = Column(Integer, default=0)
    acceptance_rate = Column(Float, default=0.0)
    avg_revenue_uplift_etb = Column(Float, default=0.0)

    is_active = Column(Boolean, default=True)
    min_nights = Column(Integer, default=1)
    max_nights = Column(Integer, default=14)

    # Relationships
    components = relationship("PackageComponent", back_populates="package")


class PackageComponent(Base):
    """Individual service items that make up a package."""
    __tablename__ = "package_components"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)
    service_name = Column(String(200), nullable=False)
    service_category = Column(String(50), nullable=False)  # spa, dining, activity, transfer, room_upgrade
    description = Column(String(500), nullable=True)
    cost_etb = Column(Float, nullable=False)  # Cost to resort
    retail_price_etb = Column(Float, nullable=False)  # Normal retail price
    quantity = Column(Integer, default=1)

    # Relationships
    package = relationship("Package", back_populates="components")
