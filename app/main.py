"""
Kuraz AI — Revenue Management System
Main FastAPI Application

An AI-powered dynamic pricing system for Ethiopian hospitality.
Optimizes room rates like airline seats and recommends service packages
to maximize total guest revenue.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app.api import (
    pricing_router,
    dashboard_router,
    packages_router,
    simulation_router,
    ml_router,
    bookings_router,
    auth_router,
    users_router,
    destinations_router,
)
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("\n" + "=" * 60)
    print("🚀 KURAZ AI — Revenue Management System")
    print(f"   Resort: {settings.RESORT_NAME}")
    print(f"   Rooms: {settings.RESORT_TOTAL_ROOMS}")
    print("=" * 60)

    init_db()
    print("✅ Database initialized")

    yield

    # Shutdown
    print("\n👋 Kuraz AI shutting down...")


app = FastAPI(
    title="Kuraz AI — Revenue Management System",
    description=(
        "AI-powered dynamic pricing and package recommendation engine "
        "for Ethiopian hospitality. Prices hotel rooms like airline seats "
        "and recommends service bundles to maximize total guest revenue."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(pricing_router)
app.include_router(dashboard_router)
app.include_router(packages_router)
app.include_router(simulation_router)
app.include_router(ml_router)
app.include_router(bookings_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(destinations_router)


@app.get("/", tags=["Health"])
def root():
    """API health check and welcome."""
    return {
        "name": "Kuraz AI — Revenue Management System",
        "version": "1.0.0",
        "resort": settings.RESORT_NAME,
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "pricing": "/api/pricing/optimal-price",
            "dashboard": "/api/dashboard/kpis",
            "packages": "/api/packages/catalog",
            "simulation": "/api/simulate/booking",
            "ml_training": "/api/ml/train/forecasting",
        },
        "description": (
            "AI-powered dynamic pricing for hotel rooms with "
            "intelligent package recommendations. "
            "Built for the Ethiopia Hospitality Hackathon 2026."
        ),
    }


@app.get("/api/room-types", tags=["Rooms"])
def get_room_types(db: Session = Depends(get_db)):
    """Get all available room types with their details."""
    from app.models.rooms import RoomType
    
    room_types = db.query(RoomType).all()
    
    return [
        {
            "id": rt.id,
            "code": rt.code,
            "name": rt.name,
            "description": rt.description,
            "base_rate_etb": rt.base_rate_etb,
            "floor_rate_etb": rt.floor_rate_etb,
            "ceiling_rate_etb": rt.ceiling_rate_etb,
            "max_occupancy": rt.max_occupancy,
            "total_count": rt.total_count,
            "amenities": rt.amenities.split(",") if rt.amenities else [],
        }
        for rt in room_types
    ]


@app.get("/api/health", tags=["Health"])
def health_check():
    """Detailed health check."""
    from app.database import SessionLocal
    from app.models.rooms import RoomType

    try:
        db = SessionLocal()
        room_count = db.query(RoomType).count()
        db.close()
        db_status = "connected"
    except Exception as e:
        room_count = 0
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status,
        "room_types_configured": room_count,
        "resort": settings.RESORT_NAME,
    }


@app.post("/api/seed", tags=["Setup"])
def seed_database():
    """
    Seed the database with synthetic data.
    Call this once to populate the demo with realistic data.
    """
    try:
        from app.data.seed import run_full_seed
        run_full_seed()
        return {
            "status": "success",
            "message": "Database seeded with synthetic data. Ready for demo!"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)},
        )
