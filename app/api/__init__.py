# API package init
from app.api.pricing import router as pricing_router
from app.api.dashboard import router as dashboard_router
from app.api.packages import router as packages_router
from app.api.simulation import router as simulation_router
from app.api.ml import router as ml_router
from app.api.bookings import router as bookings_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.destinations import router as destinations_router
