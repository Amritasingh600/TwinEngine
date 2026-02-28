from rest_framework import serializers
from .models import SalesData, InventoryItem, StaffSchedule


class SalesDataSerializer(serializers.ModelSerializer):
    """Serializer for SalesData model (aggregated sales for predictions)."""
    outlet_name = serializers.CharField(source='outlet.name', read_only=True)
    
    class Meta:
        model = SalesData
        fields = [
            'id', 'outlet', 'outlet_name', 'date', 'hour',
            'total_orders', 'total_revenue', 'avg_ticket_size', 'avg_wait_time_minutes',
            'category_sales', 'top_items',
            'day_of_week', 'is_holiday', 'weather_condition',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SalesDataCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sales data records."""
    
    class Meta:
        model = SalesData
        fields = [
            'outlet', 'date', 'hour',
            'total_orders', 'total_revenue', 'avg_ticket_size', 'avg_wait_time_minutes',
            'category_sales', 'top_items',
            'day_of_week', 'is_holiday', 'weather_condition'
        ]


class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for InventoryItem model."""
    outlet_name = serializers.CharField(source='outlet.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'outlet', 'outlet_name', 'name', 'category', 'unit',
            'current_quantity', 'reorder_threshold', 'par_level', 'unit_cost',
            'expiry_date', 'last_restocked', 'is_low_stock', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class InventoryItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing inventory."""
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = ['id', 'name', 'category', 'current_quantity', 'unit', 'is_low_stock']


class InventoryUpdateSerializer(serializers.Serializer):
    """Serializer for updating inventory quantity."""
    quantity_change = serializers.FloatField(help_text="Positive for add, negative for subtract")
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        from django.utils import timezone
        instance.current_quantity += validated_data['quantity_change']
        if validated_data['quantity_change'] > 0:
            instance.last_restocked = timezone.now()
        instance.save()
        return instance


class StaffScheduleSerializer(serializers.ModelSerializer):
    """Serializer for StaffSchedule model."""
    staff_name = serializers.SerializerMethodField()
    staff_role = serializers.CharField(source='staff.role', read_only=True)
    
    class Meta:
        model = StaffSchedule
        fields = [
            'id', 'staff', 'staff_name', 'staff_role',
            'date', 'shift', 'start_time', 'end_time',
            'is_confirmed', 'checked_in', 'checked_out',
            'is_ai_suggested', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_staff_name(self, obj):
        if obj.staff and obj.staff.user:
            return obj.staff.user.get_full_name() or obj.staff.user.username
        return None


class StaffScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating staff schedules."""
    
    class Meta:
        model = StaffSchedule
        fields = [
            'staff', 'date', 'shift', 'start_time', 'end_time',
            'is_ai_suggested', 'notes'
        ]


class DemandPredictionSerializer(serializers.Serializer):
    """Serializer for demand prediction response."""
    date = serializers.DateField()
    hour = serializers.IntegerField()
    predicted_orders = serializers.IntegerField()
    predicted_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    recommended_staff = serializers.IntegerField()
    confidence = serializers.FloatField()
