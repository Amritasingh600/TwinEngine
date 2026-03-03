"""
PredictionService -- single entry point for all ML predictions.
Views call this, never the individual model classes directly.
"""
import logging
from datetime import datetime

from .demand_model import BusyHoursPredictor
from .footfall_model import FootfallForecaster
from .food_demand_model import FoodDemandPredictor
from .inventory_predictor import InventoryPredictor
from .staffing_optimizer import StaffingOptimizer
from .revenue_model import RevenueForecaster

logger = logging.getLogger(__name__)


class PredictionService:
    """Facade that wraps all 6 prediction models."""

    def __init__(self):
        self.demand = BusyHoursPredictor()
        self.footfall = FootfallForecaster()
        self.food_demand = FoodDemandPredictor()
        self.inventory = InventoryPredictor()
        self.staffing = StaffingOptimizer()
        self.revenue = RevenueForecaster()

    def get_busy_hours(self, outlet_id: int, date) -> dict:
        return self._safe_call(self.demand.predict, outlet_id, date)

    def get_footfall(self, outlet_id: int, date) -> dict:
        return self._safe_call(self.footfall.predict, outlet_id, date)

    def get_food_demand(self, outlet_id: int, date) -> dict:
        return self._safe_call(self.food_demand.predict, outlet_id, date)

    def get_inventory_alerts(self, outlet_id: int) -> dict:
        return self._safe_call(self.inventory.predict, outlet_id)

    def get_staffing(self, outlet_id: int, date) -> dict:
        demand = self.get_busy_hours(outlet_id, date)
        return self._safe_call(self.staffing.predict, outlet_id, date, demand)

    def get_revenue_forecast(self, outlet_id: int, date, days: int = 7) -> dict:
        return self._safe_call(self.revenue.predict, outlet_id, date, days)

    def get_dashboard(self, outlet_id: int, date) -> dict:
        """Combined dashboard -- calls all models and merges results."""
        return {
            "busy_hours": self.get_busy_hours(outlet_id, date),
            "footfall": self.get_footfall(outlet_id, date),
            "food_demand": self.get_food_demand(outlet_id, date),
            "inventory_alerts": self.get_inventory_alerts(outlet_id),
            "staffing": self.get_staffing(outlet_id, date),
            "revenue": self.get_revenue_forecast(outlet_id, date),
        }

    def train_all(self, outlet_id: int) -> dict:
        """Train all trainable models for the given outlet."""
        results = {}
        for name, model in [
            ("busy_hours", self.demand),
            ("footfall", self.footfall),
            ("food_demand", self.food_demand),
            ("revenue", self.revenue),
        ]:
            try:
                results[name] = model.train(outlet_id)
            except Exception as e:
                logger.error("Training %s failed: %s", name, e)
                results[name] = {"status": "error", "error": str(e)}

        # inventory & staffing don't need training
        results["inventory"] = {"status": "rule-based (no training needed)"}
        results["staffing"] = {"status": "rule-based (no training needed)"}
        return results

    def _safe_call(self, fn, *args, **kwargs) -> dict:
        """Wrap any model call with error handling."""
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error("Prediction failed: %s -- %s", fn.__qualname__, e)
            return {"error": str(e), "fallback": True}
