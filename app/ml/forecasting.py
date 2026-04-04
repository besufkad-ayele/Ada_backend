"""
Demand Forecasting Module

Uses XGBoost to predict occupancy/demand for future dates.
Features: day of week, month, season, events, lag features, booking pace.

For hackathon: train on synthetic historical data, predict next 90 days.
The model learns seasonal patterns, holiday effects, and day-of-week trends.
"""
import os
import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import joblib

from app.models.rooms import DailyInventory, RoomType
from app.models.bookings import Booking
from app.models.events import Event
from app.data.ethiopian_calendar import get_season


MODEL_DIR = os.path.join(os.path.dirname(__file__), "trained_models")
os.makedirs(MODEL_DIR, exist_ok=True)


class DemandForecaster:
    """
    XGBoost-based demand forecasting.
    
    Predicts occupancy rate for a given room type and date.
    Features engineered from:
    - Calendar (DOW, month, season, holiday proximity)
    - Historical patterns (lag features, rolling averages)
    - Events (type, impact level)
    """

    def __init__(self):
        self.model = None
        self.feature_names = None
        self._load_model()

    def _load_model(self):
        """Load trained model if available."""
        model_path = os.path.join(MODEL_DIR, "demand_forecaster.joblib")
        if os.path.exists(model_path):
            saved = joblib.load(model_path)
            self.model = saved["model"]
            self.feature_names = saved["feature_names"]

    def train(self, db: Session) -> Dict:
        """
        Train the demand forecasting model on historical booking data.
        Returns training metrics.
        """
        from xgboost import XGBRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, r2_score

        print("  Training demand forecasting model...")

        # Build training dataset from daily inventory
        inventories = db.query(DailyInventory).filter(
            DailyInventory.date < date.today()
        ).all()

        if len(inventories) < 100:
            print("  Not enough data for training (need 100+ records)")
            return {"status": "insufficient_data", "records": len(inventories)}

        # Build features
        records = []
        for inv in inventories:
            room_type = db.query(RoomType).get(inv.room_type_id)
            features = self._extract_features(inv.date, room_type.code if room_type else "standard", db)
            features["occupancy_rate"] = inv.occupancy_rate
            records.append(features)

        df = pd.DataFrame(records)
        target = "occupancy_rate"

        feature_cols = [c for c in df.columns if c != target]
        X = df[feature_cols].values
        y = df[target].values

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train XGBoost
        model = XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Save
        self.model = model
        self.feature_names = feature_cols
        joblib.dump(
            {"model": model, "feature_names": feature_cols},
            os.path.join(MODEL_DIR, "demand_forecaster.joblib"),
        )

        # Feature importance
        importance = dict(zip(feature_cols, model.feature_importances_))
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]

        metrics = {
            "status": "trained",
            "records_used": len(records),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "mae": round(mae, 4),
            "r2_score": round(r2, 4),
            "top_features": {k: round(v, 4) for k, v in top_features},
        }
        print(f"  ✅ Model trained — MAE: {mae:.4f}, R²: {r2:.4f}")
        return metrics

    def predict(
        self, target_date: date, room_type_code: str, db: Session
    ) -> Optional[float]:
        """Predict occupancy rate for a date and room type."""
        if self.model is None:
            return None

        features = self._extract_features(target_date, room_type_code, db)
        X = np.array([[features.get(f, 0) for f in self.feature_names]])
        prediction = float(self.model.predict(X)[0])
        return max(0.0, min(1.0, prediction))

    def predict_range(
        self, start_date: date, end_date: date, room_type_code: str, db: Session
    ) -> List[Dict]:
        """Predict occupancy for a date range."""
        results = []
        current = start_date
        while current <= end_date:
            occ = self.predict(current, room_type_code, db)
            results.append({
                "date": current.isoformat(),
                "room_type": room_type_code,
                "predicted_occupancy": round(occ, 4) if occ else None,
                "demand_level": self._demand_level(occ) if occ else "unknown",
            })
            current += timedelta(days=1)
        return results

    def _extract_features(
        self, d: date, room_type_code: str, db: Session
    ) -> Dict:
        """Extract features for a single date."""
        season = get_season(d)

        # Check for events
        events = db.query(Event).filter(
            Event.date_start <= d, Event.date_end >= d
        ).all()
        has_event = len(events) > 0
        max_event_impact = max([e.expected_demand_multiplier for e in events], default=1.0)

        # Days to nearest event
        upcoming_events = db.query(Event).filter(
            Event.date_start >= d,
            Event.date_start <= d + timedelta(days=14)
        ).all()
        days_to_event = 999
        if upcoming_events:
            days_to_event = min((e.date_start - d).days for e in upcoming_events)

        # Room type encoding
        room_type_map = {"standard": 0, "deluxe": 1, "suite": 2, "royal_suite": 3}

        return {
            "day_of_week": d.weekday(),
            "month": d.month,
            "day_of_month": d.day,
            "is_weekend": 1 if d.weekday() >= 4 else 0,
            "is_friday": 1 if d.weekday() == 4 else 0,
            "is_saturday": 1 if d.weekday() == 5 else 0,
            "season_rainy": 1 if season == "rainy_low" else 0,
            "season_peak": 1 if season == "dry_peak" else 0,
            "season_shoulder": 1 if "shoulder" in season else 0,
            "has_event": 1 if has_event else 0,
            "event_impact": max_event_impact,
            "days_to_nearest_event": min(days_to_event, 30),
            "room_type_code": room_type_map.get(room_type_code, 0),
            "week_of_year": d.isocalendar()[1],
            "quarter": (d.month - 1) // 3 + 1,
        }

    def _demand_level(self, occupancy: float) -> str:
        """Classify demand level for display."""
        if occupancy >= 0.85:
            return "peak"
        elif occupancy >= 0.65:
            return "high"
        elif occupancy >= 0.45:
            return "medium"
        else:
            return "low"
