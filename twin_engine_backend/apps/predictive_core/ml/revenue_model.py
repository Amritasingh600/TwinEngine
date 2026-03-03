"""
Model 6: Revenue Forecaster
Predicts next-day and next-week total revenue for an outlet.
Algorithm: GradientBoostingRegressor (scikit-learn)
"""
import logging
import joblib
from pathlib import Path
from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .feature_engineering import build_revenue_features

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / 'ml_models'
FEATURE_COLS = [
    'day_of_week', 'is_weekend',
    'prev_day_revenue', 'prev_week_revenue',
    'prev_day_orders', 'rolling_avg_revenue_7d',
    'rolling_avg_revenue_30d',
]
TARGET_COL = 'total_revenue'


class RevenueForecaster:
    """Predicts daily revenue for a given outlet."""

    def train(self, outlet_id: int) -> dict:
        """Train and save a GBR model for revenue prediction."""
        df = build_revenue_features(outlet_id)
        if df is None or len(df) < 7:
            return {"status": "skipped", "reason": "Insufficient data (need 7+ daily summaries)"}

        df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
        if len(df) < 7:
            return {"status": "skipped", "reason": "Insufficient data after dropna"}

        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values

        # Time-aware split
        split_idx = int(len(X) * 0.8)
        if split_idx == 0:
            split_idx = 1
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        if len(X_test) == 0:
            X_test, y_test = X_train[-2:], y_train[-2:]

        model = GradientBoostingRegressor(
            n_estimators=80, max_depth=3, learning_rate=0.1,
            min_samples_split=3, random_state=42,
        )
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        metrics = {
            "mae": round(float(mean_absolute_error(y_test, y_pred)), 2),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
            "r2": round(float(r2_score(y_test, y_pred)), 3) if len(y_test) > 1 else 0.0,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        MODELS_DIR.mkdir(exist_ok=True)
        model_path = MODELS_DIR / f"outlet_{outlet_id}_revenue.joblib"
        joblib.dump(model, model_path)

        logger.info("Revenue model trained for outlet %d: %s", outlet_id, metrics)
        return {"status": "trained", "metrics": metrics}

    def predict(self, outlet_id: int, target_date, days: int = 7) -> dict:
        """Predict revenue for the given date and optionally the next N days."""
        model_path = MODELS_DIR / f"outlet_{outlet_id}_revenue.joblib"

        daily_breakdown = []

        for day_offset in range(days):
            pred_date = target_date + timedelta(days=day_offset)
            features = self._build_features_for_date(outlet_id, pred_date)

            if model_path.exists():
                model = joblib.load(model_path)
                X = pd.DataFrame([features])[FEATURE_COLS].values
                pred_val = max(0, float(model.predict(X)[0]))
                confidence = "high"
            else:
                # Fallback: weighted average (70% same-day last week + 30% recent 7-day avg)
                pred_val = (
                    0.7 * features.get('prev_week_revenue', 0) +
                    0.3 * features.get('rolling_avg_revenue_7d', 0)
                )
                pred_val = max(0, pred_val)
                confidence = "low (using historical averages -- model not yet trained)"

            daily_breakdown.append({
                "date": str(pred_date),
                "predicted_revenue": round(pred_val, 2),
            })

        # First day details
        first_day = daily_breakdown[0] if daily_breakdown else {}
        first_pred = first_day.get('predicted_revenue', 0)

        # Confidence range (+-15%)
        conf_low = round(first_pred * 0.85, 2)
        conf_high = round(first_pred * 1.15, 2)

        total_week = sum(d['predicted_revenue'] for d in daily_breakdown)

        return {
            "outlet_id": outlet_id,
            "next_day": {
                "date": str(target_date),
                "predicted_revenue": first_pred,
                "confidence_range": [conf_low, conf_high],
                "confidence": confidence,
            },
            "next_week": {
                "total_predicted_revenue": round(total_week, 2),
                "daily_breakdown": daily_breakdown,
            },
        }

    def _build_features_for_date(self, outlet_id, target_date):
        """Build a single feature row for a target date using historical DailySummary."""
        from apps.insights_hub.models import DailySummary

        day_of_week = target_date.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0

        # Previous day
        prev_day = DailySummary.objects.filter(
            outlet_id=outlet_id, date=target_date - timedelta(days=1)
        ).first()

        # Same day last week
        prev_week = DailySummary.objects.filter(
            outlet_id=outlet_id, date=target_date - timedelta(days=7)
        ).first()

        # Rolling 7-day average
        start_7 = target_date - timedelta(days=7)
        recent_7 = DailySummary.objects.filter(
            outlet_id=outlet_id, date__gte=start_7, date__lt=target_date
        ).values_list('total_revenue', flat=True)
        avg_7 = float(np.mean([float(r) for r in recent_7])) if recent_7 else 0

        # Rolling 30-day average
        start_30 = target_date - timedelta(days=30)
        recent_30 = DailySummary.objects.filter(
            outlet_id=outlet_id, date__gte=start_30, date__lt=target_date
        ).values_list('total_revenue', flat=True)
        avg_30 = float(np.mean([float(r) for r in recent_30])) if recent_30 else avg_7

        return {
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'prev_day_revenue': float(prev_day.total_revenue) if prev_day else avg_7,
            'prev_week_revenue': float(prev_week.total_revenue) if prev_week else avg_7,
            'prev_day_orders': prev_day.total_orders if prev_day else 0,
            'rolling_avg_revenue_7d': avg_7,
            'rolling_avg_revenue_30d': avg_30,
        }
