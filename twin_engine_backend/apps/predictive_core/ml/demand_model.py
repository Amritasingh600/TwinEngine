"""
Model 1: Busy Hours Predictor
Predicts the number of orders per hour for a given date.
Algorithm: GradientBoostingRegressor (scikit-learn)
"""
import logging
import joblib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .feature_engineering import build_demand_features, build_prediction_row, get_historical_averages

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / 'ml_models'
FEATURE_COLS = [
    'hour', 'day_of_week', 'is_holiday', 'is_weekend',
    'prev_week_orders', 'rolling_avg_orders_7d',
]
TARGET_COL = 'total_orders'


class BusyHoursPredictor:
    """Predicts hourly order volume for a given outlet and date."""

    def train(self, outlet_id: int) -> dict:
        """Train and save a model for the given outlet."""
        df = build_demand_features(outlet_id)
        if df is None or len(df) < 50:
            return {"status": "skipped", "reason": "Insufficient data (need 50+ rows)"}

        df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values

        # Time-aware split (no data leakage)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        model = GradientBoostingRegressor(
            n_estimators=100, max_depth=4, learning_rate=0.1,
            min_samples_split=5, random_state=42,
        )
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        metrics = {
            "mae": round(mean_absolute_error(y_test, y_pred), 2),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
            "r2": round(float(r2_score(y_test, y_pred)), 3),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        # Save
        MODELS_DIR.mkdir(exist_ok=True)
        model_path = MODELS_DIR / f"outlet_{outlet_id}_demand.joblib"
        joblib.dump(model, model_path)

        logger.info("Busy Hours model trained for outlet %d: %s", outlet_id, metrics)
        return {"status": "trained", "metrics": metrics}

    def predict(self, outlet_id: int, target_date) -> dict:
        """Predict hourly orders for the given date."""
        model_path = MODELS_DIR / f"outlet_{outlet_id}_demand.joblib"

        # Build features for each hour (typical restaurant hours: 8-23)
        hours = list(range(8, 24))
        rows = [build_prediction_row(outlet_id, target_date, h) for h in hours]

        if model_path.exists():
            model = joblib.load(model_path)
            X = pd.DataFrame(rows)[FEATURE_COLS].values
            predictions = model.predict(X)
            predictions = np.maximum(predictions, 0).astype(int)  # no negative orders
            confidence = "high"
        else:
            # Fallback: historical averages
            avgs = get_historical_averages(outlet_id, target_date.weekday())
            predictions = [
                int(avgs.get(h, {}).get('avg_orders', 0) or 0)
                for h in hours
            ]
            confidence = "low (using historical averages -- model not yet trained)"

        hourly_forecast = [
            {"hour": h, "predicted_orders": int(p)}
            for h, p in zip(hours, predictions)
        ]

        peak = max(hourly_forecast, key=lambda x: x['predicted_orders'])

        return {
            "date": str(target_date),
            "hourly_forecast": hourly_forecast,
            "peak_hour": peak['hour'],
            "total_predicted_orders": sum(int(p) for p in predictions),
            "confidence": confidence,
        }
