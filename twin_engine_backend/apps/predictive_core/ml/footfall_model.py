"""
Model 2: Customer Footfall Forecaster
Predicts the number of customers (guests) per hour for a given date.
Algorithm: Ridge Regression (scikit-learn)
"""
import logging
import joblib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .feature_engineering import build_footfall_features, get_historical_averages, build_prediction_row

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / 'ml_models'
FEATURE_COLS = [
    'hour', 'day_of_week', 'is_holiday', 'is_weekend',
    'total_orders', 'prev_week_guests', 'rolling_avg_guests_7d',
]
TARGET_COL = 'estimated_guests'


class FootfallForecaster:
    """Predicts hourly guest counts for a given outlet and date."""

    def train(self, outlet_id: int) -> dict:
        """Train and save a Ridge model for the given outlet."""
        result = build_footfall_features(outlet_id)
        if result is None:
            return {"status": "skipped", "reason": "Insufficient data (need 7+ days)"}

        df, avg_party = result

        if len(df) < 50:
            return {"status": "skipped", "reason": "Insufficient data (need 50+ rows)"}

        df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values

        # Time-aware split
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        metrics = {
            "mae": round(float(mean_absolute_error(y_test, y_pred)), 2),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
            "r2": round(float(r2_score(y_test, y_pred)), 3),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        # Save model + avg_party_size
        MODELS_DIR.mkdir(exist_ok=True)
        model_path = MODELS_DIR / f"outlet_{outlet_id}_footfall.joblib"
        joblib.dump({"model": model, "avg_party_size": avg_party}, model_path)

        logger.info("Footfall model trained for outlet %d: %s", outlet_id, metrics)
        return {"status": "trained", "metrics": metrics}

    def predict(self, outlet_id: int, target_date) -> dict:
        """Predict hourly guest counts for the given date."""
        model_path = MODELS_DIR / f"outlet_{outlet_id}_footfall.joblib"

        hours = list(range(8, 24))
        rows = [build_prediction_row(outlet_id, target_date, h) for h in hours]

        # Default avg party size
        avg_party = 2.0

        if model_path.exists():
            data = joblib.load(model_path)
            model = data["model"]
            avg_party = data.get("avg_party_size", 2.0)

            # Build feature matrix -- need total_orders estimate
            # Use demand predictor for orders, or use rolling avg as proxy
            feature_rows = []
            for row in rows:
                feature_rows.append({
                    'hour': row['hour'],
                    'day_of_week': row['day_of_week'],
                    'is_holiday': row['is_holiday'],
                    'is_weekend': row['is_weekend'],
                    'total_orders': row.get('rolling_avg_orders_7d', 0),
                    'prev_week_guests': row.get('prev_week_orders', 0) * avg_party,
                    'rolling_avg_guests_7d': row.get('rolling_avg_orders_7d', 0) * avg_party,
                })

            X = pd.DataFrame(feature_rows)[FEATURE_COLS].values
            predictions = model.predict(X)
            predictions = np.maximum(predictions, 0).astype(int)
            confidence = "high"
        else:
            # Fallback: historical averages * avg_party_size
            avgs = get_historical_averages(outlet_id, target_date.weekday())
            predictions = [
                int((avgs.get(h, {}).get('avg_orders', 0) or 0) * avg_party)
                for h in hours
            ]
            confidence = "low (using historical averages -- model not yet trained)"

        hourly_guests = [
            {"hour": h, "predicted_guests": int(p)}
            for h, p in zip(hours, predictions)
        ]

        return {
            "date": str(target_date),
            "hourly_guests": hourly_guests,
            "total_predicted_guests": sum(int(p) for p in predictions),
            "avg_party_size": round(avg_party, 1),
            "confidence": confidence,
        }
