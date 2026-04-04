from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./kuraz.db"
    GROQ_API_KEY: str = ""
    RESORT_NAME: str = "Kuriftu Resort and Spa"
    RESORT_TOTAL_ROOMS: int = 120

    # Room type configuration
    ROOM_TYPES: dict = {
        "standard": {
            "count": 60,
            "base_rate_etb": 4500,
            "base_rate_usd": 80,
            "max_occupancy": 2,
            "description": "Standard Room"
        },
        "deluxe": {
            "count": 40,
            "base_rate_etb": 7500,
            "base_rate_usd": 135,
            "max_occupancy": 2,
            "description": "Deluxe Lake View"
        },
        "suite": {
            "count": 15,
            "base_rate_etb": 12000,
            "base_rate_usd": 215,
            "max_occupancy": 3,
            "description": "Junior Suite"
        },
        "royal_suite": {
            "count": 5,
            "base_rate_etb": 22000,
            "base_rate_usd": 395,
            "max_occupancy": 4,
            "description": "Royal Suite"
        }
    }

    # Fare classes
    FARE_CLASSES: dict = {
        "saver": {
            "label": "Saver / Advance Purchase",
            "discount_pct": 0.30,
            "min_advance_days": 21,
            "inventory_pct": 0.40,
            "refundable": False,
            "changeable": False
        },
        "standard": {
            "label": "Standard / Flexible",
            "discount_pct": 0.10,
            "min_advance_days": 7,
            "inventory_pct": 0.40,
            "refundable": True,
            "changeable": True
        },
        "premium": {
            "label": "Premium / Last Minute",
            "discount_pct": -0.20,
            "min_advance_days": 0,
            "inventory_pct": 0.20,
            "refundable": True,
            "changeable": True
        }
    }

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()