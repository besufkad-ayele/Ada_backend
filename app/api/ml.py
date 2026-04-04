"""
API Routes — ML training, forecasting, and AI LLM natural language interface.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.ml.forecasting import DemandForecaster
from app.config import get_settings

router = APIRouter(prefix="/api/ml", tags=["ML / AI"])
settings = get_settings()


@router.post("/train/forecasting")
def train_forecasting_model(db: Session = Depends(get_db)):
    """
    Train the demand forecasting model on historical data.
    Call this after seeding data.
    """
    forecaster = DemandForecaster()
    metrics = forecaster.train(db)
    return {
        "model": "XGBoost Demand Forecaster",
        "metrics": metrics,
    }


@router.get("/forecast")
def get_demand_forecast(
    room_type_code: str = "standard",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Get demand forecast for a date range."""
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    forecaster = DemandForecaster()
    if forecaster.model is None:
        return {
            "status": "model_not_trained",
            "message": "Call POST /api/ml/train/forecasting first",
        }

    predictions = forecaster.predict_range(start_date, end_date, room_type_code, db)
    return {
        "room_type": room_type_code,
        "predictions": predictions,
    }


# ==================== AI LLM INTERFACE (Groq/Llama) ====================

class NLQueryRequest(BaseModel):
    query: str


@router.post("/ask")
def ask_revenue_ai(request: NLQueryRequest, db: Session = Depends(get_db)):
    """
    Natural language interface to the revenue management engine.
    Powered by Groq (Llama 3.1 70B). Ask questions like:
    - "What happens if I block 20 rooms for a tour group next weekend?"
    - "Should I run a promotion for next Friday?"
    - "Why did the AI increase prices for Saturday?"
    """
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        return {
            "answer": (
                "Groq API key not configured. Add GROQ_API_KEY to your .env file. "
                "Get a free key at https://console.groq.com/keys (Free tier: 30 requests/min)"
            ),
            "source": "system",
        }

    try:
        from groq import Groq
        from app.engine.pricing import PricingEngine
        from app.models.rooms import RoomType, DailyInventory
        from app.models.bookings import Booking, BookingStatus

        client = Groq(api_key=settings.GROQ_API_KEY)

        # Build context snapshot for AI
        today = date.today()
        room_types = db.query(RoomType).all()

        # Current occupancy snapshot
        occ_summary = []
        for rt in room_types:
            inv = db.query(DailyInventory).filter(
                DailyInventory.room_type_id == rt.id,
                DailyInventory.date == today,
            ).first()
            occ_rate = inv.occupancy_rate if inv else 0.0
            occ_summary.append(f"{rt.name}: {occ_rate:.0%} occupancy")

        # Recent revenue (last 7 days)
        week_ago = today - timedelta(days=7)
        recent_bookings = db.query(Booking).filter(
            Booking.check_in >= week_ago,
            Booking.status != BookingStatus.CANCELLED,
        ).all()
        weekly_revenue = sum(b.total_revenue_etb for b in recent_bookings)
        weekly_bookings = len(recent_bookings)

        context = f"""
You are the AI revenue manager for {settings.RESORT_NAME}, an Ethiopian luxury resort.
You have access to the Kuraz AI dynamic pricing system.

CURRENT RESORT STATUS (as of {today}):
- Total rooms: {settings.RESORT_TOTAL_ROOMS}
- Today's occupancy: {', '.join(occ_summary)}
- Last 7 days: {weekly_bookings} bookings, ETB {weekly_revenue:,.0f} total revenue
- Pricing engine: Active (airline-style yield management)
- Fare classes: Saver (30% off, 21+ days), Standard (10% off, 7+ days), Premium (+20%, last minute)

PRICING RULES:
- Saver class closes at 60% occupancy or within 14 days of arrival
- Standard class closes at 85% occupancy or within 3 days
- Premium is always available
- Prices adjust based on: occupancy, lead time, day of week, Ethiopian holidays, competitor rates

PACKAGES AVAILABLE: Romance Escape, Family Getaway, Business Express, Weekend Wellness,
Adventure Package, Conference Package, Honeymoon Bliss, Day Use Pass, Cultural Experience, Extended Stay

Answer the following question from the revenue manager. Be specific, use numbers, and give actionable advice.
Keep your answer under 150 words. Use ETB for currency.

QUESTION: {request.query}
"""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert revenue management AI assistant for Ethiopian hospitality. Provide specific, actionable advice with numbers."
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.7,
            max_tokens=500,
        )
        
        answer = chat_completion.choices[0].message.content.strip()

        return {
            "answer": answer,
            "source": "groq-llama-3.1-70b",
            "context_snapshot": {
                "date": today.isoformat(),
                "occupancy": occ_summary,
                "weekly_revenue_etb": round(weekly_revenue, 2),
                "weekly_bookings": weekly_bookings,
            },
        }

    except Exception as e:
        return {
            "answer": f"AI query failed: {str(e)}. Make sure GROQ_API_KEY is set correctly in .env",
            "source": "error",
        }
