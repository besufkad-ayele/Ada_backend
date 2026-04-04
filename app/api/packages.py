"""
API Routes — Package recommendation endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.engine.packages import PackageRecommender
from app.models.packages import Package, PackageComponent
from app.schemas.packages import (
    PackageOut, PackageComponentOut,
    PackageRecommendationRequest, PackageRecommendationResponse,
)
from pydantic import BaseModel
from app.engine.gemini import generate_package_with_gemini

class GeneratePackageRequest(BaseModel):
    target_audience: str

router = APIRouter(prefix="/api/packages", tags=["Package Recommendations"])


@router.get("/catalog")
def get_package_catalog(db: Session = Depends(get_db)):
    """Get all available packages with their components."""
    packages = db.query(Package).filter(Package.is_active == True).all()
    result = []
    for pkg in packages:
        components = db.query(PackageComponent).filter(
            PackageComponent.package_id == pkg.id
        ).all()
        result.append({
            "id": pkg.id,
            "code": pkg.code,
            "name": pkg.name,
            "description": pkg.description,
            "category": pkg.category,
            "base_price_etb": pkg.base_price_etb,
            "min_discount_pct": pkg.min_discount_pct,
            "max_discount_pct": pkg.max_discount_pct,
            "acceptance_rate": pkg.acceptance_rate,
            "avg_revenue_uplift_etb": pkg.avg_revenue_uplift_etb,
            "min_nights": pkg.min_nights,
            "components": [
                {
                    "service_name": c.service_name,
                    "service_category": c.service_category,
                    "description": c.description,
                    "retail_price_etb": c.retail_price_etb,
                    "quantity": c.quantity,
                }
                for c in components
            ],
        })
    return result


@router.post("/recommend")
def get_package_recommendation(
    request: PackageRecommendationRequest,
    db: Session = Depends(get_db),
):
    """
    Get AI-powered package recommendation for a booking.
    
    Takes guest details and returns the best package with dynamic pricing.
    Shows:
    - Which package to recommend
    - What discount to apply
    - Revenue uplift vs room-only booking
    - Full pricing breakdown
    """
    recommender = PackageRecommender(db)
    result = recommender.recommend(
        guest_nationality=request.guest_nationality,
        is_corporate=request.is_corporate,
        adults=request.adults,
        children=request.children,
        check_in=request.check_in,
        check_out=request.check_out,
        room_type_code=request.room_type_code,
        booking_channel=request.booking_channel,
        room_rate_etb=request.room_rate_etb,
    )
    return result


@router.get("/performance")
def get_package_performance(db: Session = Depends(get_db)):
    """Get performance metrics for all packages."""
    packages = db.query(Package).all()
    return [
        {
            "code": pkg.code,
            "name": pkg.name,
            "category": pkg.category,
            "times_offered": pkg.times_offered,
            "times_accepted": pkg.times_accepted,
            "acceptance_rate": pkg.acceptance_rate,
            "avg_revenue_uplift_etb": pkg.avg_revenue_uplift_etb,
        }
        for pkg in packages
    ]

@router.post("/generate")
def generate_ai_package(request: GeneratePackageRequest, db: Session = Depends(get_db)):
    """Use Gemini AI to dynamically create a new package based on a prompt."""
    try:
        data = generate_package_with_gemini(request.target_audience)
        
        # Save to DB
        new_pkg = Package(
            code=data["code"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            target_segments=data["target_segments"],
            base_price_etb=data["base_price_etb"],
            min_discount_pct=data["min_discount_pct"],
            max_discount_pct=data["max_discount_pct"],
            min_nights=data["min_nights"],
            margin_floor_pct=0.15,
            times_offered=0,
            times_accepted=0,
            acceptance_rate=0.0,
            avg_revenue_uplift_etb=data["base_price_etb"] * (1 - data.get("max_discount_pct", 0.10)),
            is_active=True,
        )
        db.add(new_pkg)
        db.flush()

        for comp in data.get("components", []):
            db.add(PackageComponent(
                package_id=new_pkg.id,
                service_name=comp["service_name"],
                service_category=comp["service_category"],
                description=comp["description"],
                cost_etb=comp["cost_etb"],
                retail_price_etb=comp["retail_price_etb"],
            ))
            
        db.commit()
        db.refresh(new_pkg)
        return {"status": "success", "package_code": new_pkg.code, "name": new_pkg.name}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
