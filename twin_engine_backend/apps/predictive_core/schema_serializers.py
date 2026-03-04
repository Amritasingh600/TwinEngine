"""
Response-only serializers for drf-spectacular OpenAPI schema generation.
These define the shape of JSON responses from prediction endpoints.
"""
from rest_framework import serializers


# ── Busy Hours ──────────────────────────────────────────────

class HourlyForecastItemSerializer(serializers.Serializer):
    hour = serializers.IntegerField(help_text="Hour of day (0-23)")
    predicted_orders = serializers.IntegerField()


class BusyHoursResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    hourly_forecast = HourlyForecastItemSerializer(many=True)
    peak_hours = serializers.ListField(child=serializers.IntegerField())
    total_predicted_orders = serializers.IntegerField()


# ── Footfall ────────────────────────────────────────────────

class HourlyGuestsItemSerializer(serializers.Serializer):
    hour = serializers.IntegerField(help_text="Hour of day (0-23)")
    predicted_guests = serializers.IntegerField()


class FootfallResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    hourly_guests = HourlyGuestsItemSerializer(many=True)
    total_predicted_guests = serializers.IntegerField()


# ── Food Demand ─────────────────────────────────────────────

class CategoryForecastValueSerializer(serializers.Serializer):
    predicted_revenue = serializers.FloatField()


class FoodDemandResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    category_forecast = serializers.DictField(
        child=CategoryForecastValueSerializer(),
        help_text="Keys are category names (e.g. Starters, Mains, Beverages)",
    )


# ── Inventory Alerts ────────────────────────────────────────

class InventoryAlertItemSerializer(serializers.Serializer):
    item = serializers.CharField()
    category = serializers.CharField()
    current_quantity = serializers.FloatField()
    unit = serializers.CharField()
    daily_consumption_rate = serializers.FloatField()
    days_until_stockout = serializers.FloatField()
    reorder_needed = serializers.BooleanField()
    suggested_reorder_quantity = serializers.FloatField()


class InventoryAlertsResponseSerializer(serializers.Serializer):
    outlet_id = serializers.IntegerField()
    inventory_alerts = InventoryAlertItemSerializer(many=True)


# ── Staffing ────────────────────────────────────────────────

class ShiftRecommendationSerializer(serializers.Serializer):
    recommended_waiters = serializers.IntegerField()
    recommended_chefs = serializers.IntegerField()
    predicted_peak_orders = serializers.IntegerField()


class StaffingResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    outlet_id = serializers.IntegerField()
    staffing_recommendation = serializers.DictField(
        child=ShiftRecommendationSerializer(),
        help_text="Keys are shift names: MORNING, AFTERNOON, EVENING",
    )


# ── Revenue ─────────────────────────────────────────────────

class RevenueDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    predicted_revenue = serializers.FloatField()
    confidence_range = serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2)
    confidence = serializers.CharField(help_text="e.g. 'high', 'low (using fallback)'")


class RevenueResponseSerializer(serializers.Serializer):
    outlet_id = serializers.IntegerField()
    next_day = RevenueDaySerializer()
    weekly = RevenueDaySerializer(many=True, required=False)


# ── Dashboard (composite) ──────────────────────────────────

class DashboardResponseSerializer(serializers.Serializer):
    busy_hours = BusyHoursResponseSerializer()
    footfall = FootfallResponseSerializer()
    food_demand = FoodDemandResponseSerializer()
    inventory_alerts = InventoryAlertsResponseSerializer()
    staffing = StaffingResponseSerializer()
    revenue = RevenueResponseSerializer()


# ── Train ───────────────────────────────────────────────────

class TrainResultSerializer(serializers.Serializer):
    status = serializers.CharField()
    results = serializers.DictField()


# ── Error ───────────────────────────────────────────────────

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
