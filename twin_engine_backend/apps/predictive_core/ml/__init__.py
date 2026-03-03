"""
ML prediction models for TwinEngine Hospitality Edition.
6 models: BusyHours, Footfall, FoodDemand, Inventory, Staffing, Revenue.
"""
from .prediction_service import PredictionService

__all__ = ['PredictionService']
