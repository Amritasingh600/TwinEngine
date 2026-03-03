"""
Model 3: Food Demand Predictor
Predicts demand per food category and top-selling items for a given date.
Algorithm: RandomForestRegressor (one model per category, scikit-learn)
"""
import logging
import joblib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .feature_engineering import build_food_demand_features

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / 'ml_models'
FEATURE_COLS = [
    'hour', 'day_of_week', 'is_holiday', 'is_weekend',
    'total_orders', 'rolling_avg_cat_7d',
]
TARGET_COL = 'category_sales'


class FoodDemandPredictor:
    """Predicts per-category food demand for a given outlet and date."""

    def train(self, outlet_id: int) -> dict:
        """Train one RandomForest model per food category."""
        category_dfs = build_food_demand_features(outlet_id)
        if category_dfs is None:
            return {"status": "skipped", "reason": "Insufficient data (need 7+ days)"}

        MODELS_DIR.mkdir(exist_ok=True)
        all_metrics = {}
        trained_count = 0

        for category, df in category_dfs.items():
            if len(df) < 20:
                all_metrics[category] = {"status": "skipped", "reason": "too few rows"}
                continue

            df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
            if len(df) < 20:
                all_metrics[category] = {"status": "skipped", "reason": "too few rows after dropna"}
                continue

            X = df[FEATURE_COLS].values
            y = df[TARGET_COL].values

            # Time-aware split
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]

            if len(X_test) == 0:
                X_test, y_test = X_train[-5:], y_train[-5:]

            model = RandomForestRegressor(
                n_estimators=50, max_depth=4, random_state=42,
            )
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            metrics = {
                "mae": round(float(mean_absolute_error(y_test, y_pred)), 2),
                "r2": round(float(r2_score(y_test, y_pred)), 3) if len(y_test) > 1 else 0.0,
                "samples": len(X_train),
            }

            # Save per-category model
            safe_cat = category.replace(' ', '_').lower()
            model_path = MODELS_DIR / f"outlet_{outlet_id}_food_{safe_cat}.joblib"
            joblib.dump(model, model_path)

            all_metrics[category] = {"status": "trained", "metrics": metrics}
            trained_count += 1

        logger.info("Food demand models trained for outlet %d: %d categories", outlet_id, trained_count)
        return {
            "status": "trained" if trained_count > 0 else "skipped",
            "categories_trained": trained_count,
            "details": all_metrics,
            "metrics": {"categories": trained_count},
        }

    def predict(self, outlet_id: int, target_date) -> dict:
        """Predict per-category demand for the given date."""
        from apps.predictive_core.models import SalesData

        hours = list(range(8, 24))
        day_of_week = target_date.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0

        # Discover categories from historical data
        recent = SalesData.objects.filter(outlet_id=outlet_id).order_by('-date')[:20]
        categories = set()
        for rec in recent:
            if rec.category_sales and isinstance(rec.category_sales, dict):
                categories.update(rec.category_sales.keys())

        if not categories:
            categories = {'Main Course', 'Starters', 'Beverages', 'Desserts'}

        category_forecast = {}

        for category in categories:
            safe_cat = category.replace(' ', '_').lower()
            model_path = MODELS_DIR / f"outlet_{outlet_id}_food_{safe_cat}.joblib"

            if model_path.exists():
                model = joblib.load(model_path)
                # Build prediction rows for each hour
                pred_rows = []
                for h in hours:
                    # Get rolling avg for this category
                    from datetime import timedelta
                    start = target_date - timedelta(days=7)
                    hist = SalesData.objects.filter(
                        outlet_id=outlet_id,
                        date__gte=start,
                        date__lt=target_date,
                        hour=h,
                    )
                    cat_vals = []
                    order_vals = []
                    for s in hist:
                        cs = s.category_sales or {}
                        cat_vals.append(float(cs.get(category, 0)))
                        order_vals.append(s.total_orders)

                    pred_rows.append({
                        'hour': h,
                        'day_of_week': day_of_week,
                        'is_holiday': 0,
                        'is_weekend': is_weekend,
                        'total_orders': np.mean(order_vals) if order_vals else 0,
                        'rolling_avg_cat_7d': np.mean(cat_vals) if cat_vals else 0,
                    })

                X = pd.DataFrame(pred_rows)[FEATURE_COLS].values
                preds = model.predict(X)
                total_cat_sales = max(0, float(np.sum(preds)))
            else:
                # Fallback: historical average
                hist = SalesData.objects.filter(
                    outlet_id=outlet_id,
                    day_of_week=day_of_week,
                )
                cat_vals = []
                for s in hist:
                    cs = s.category_sales or {}
                    cat_vals.append(float(cs.get(category, 0)))
                total_cat_sales = float(np.mean(cat_vals)) * len(hours) if cat_vals else 0

            category_forecast[category] = {
                "predicted_revenue": round(total_cat_sales, 2),
            }

        # Top items from historical data
        top_items_forecast = self._get_top_items(outlet_id, day_of_week)

        return {
            "date": str(target_date),
            "category_forecast": category_forecast,
            "top_items_forecast": top_items_forecast,
        }

    def _get_top_items(self, outlet_id, day_of_week):
        """Get top predicted items based on historical top_items data."""
        from apps.predictive_core.models import SalesData

        hist = SalesData.objects.filter(
            outlet_id=outlet_id,
            day_of_week=day_of_week,
        ).order_by('-date')[:20]

        item_counts = {}
        for rec in hist:
            top_items = rec.top_items or []
            if isinstance(top_items, list):
                for item in top_items:
                    if isinstance(item, dict):
                        name = item.get('name', item.get('item', ''))
                        qty = item.get('quantity', item.get('orders', 1))
                    else:
                        name = str(item)
                        qty = 1
                    if name:
                        item_counts[name] = item_counts.get(name, 0) + qty

        # Sort by count and return top 5
        sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [
            {"item": name, "predicted_orders": max(1, count // max(len(list(hist)), 1))}
            for name, count in sorted_items
        ]
