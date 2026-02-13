from rest_framework import serializers
from .models import ShiftLog, ProductionReport


class ShiftLogSerializer(serializers.ModelSerializer):
    """Serializer for ShiftLog model."""
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    efficiency_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ShiftLog
        fields = [
            'id', 'manufacturer', 'manufacturer_name',
            'date', 'shift_start', 'shift_end',
            'total_units', 'total_downtime', 'anomaly_count',
            'efficiency_rate', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_efficiency_rate(self, obj):
        """Calculate efficiency as percentage (units per hour, accounting for downtime)."""
        from datetime import datetime, timedelta
        shift_duration = datetime.combine(datetime.min, obj.shift_end) - datetime.combine(datetime.min, obj.shift_start)
        total_minutes = shift_duration.total_seconds() / 60
        active_minutes = total_minutes - obj.total_downtime
        if active_minutes <= 0:
            return 0.0
        return round((obj.total_units / active_minutes) * 60, 2)  # Units per hour


class ShiftLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating shift logs."""
    
    class Meta:
        model = ShiftLog
        fields = [
            'manufacturer', 'date', 'shift_start', 'shift_end',
            'total_units', 'total_downtime', 'anomaly_count'
        ]


class ShiftLogSummarySerializer(serializers.Serializer):
    """Serializer for aggregated shift statistics."""
    date = serializers.DateField()
    total_shifts = serializers.IntegerField()
    total_units = serializers.IntegerField()
    total_downtime = serializers.FloatField()
    total_anomalies = serializers.IntegerField()
    avg_efficiency = serializers.FloatField()


class ProductionReportSerializer(serializers.ModelSerializer):
    """Serializer for ProductionReport model."""
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    
    class Meta:
        model = ProductionReport
        fields = [
            'id', 'manufacturer', 'manufacturer_name',
            'date', 'cloudinary_url', 'gpt_summary',
            'generation_type', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductionReportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reports."""
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    
    class Meta:
        model = ProductionReport
        fields = ['id', 'manufacturer_name', 'date', 'generation_type', 'cloudinary_url']


class ReportGenerateSerializer(serializers.Serializer):
    """Serializer for triggering report generation."""
    manufacturer_id = serializers.IntegerField()
    date = serializers.DateField()
    generation_type = serializers.ChoiceField(choices=['AUTO', 'MANUAL'], default='MANUAL')
    
    def validate_manufacturer_id(self, value):
        from apps.manufacturers.models import Manufacturer
        if not Manufacturer.objects.filter(id=value).exists():
            raise serializers.ValidationError("Manufacturer does not exist.")
        return value


class DailyReportResponseSerializer(serializers.Serializer):
    """Response serializer for /api/reports/daily/ endpoint (per API spec)."""
    report_text = serializers.CharField()
    generated_at = serializers.DateTimeField()
    cloudinary_url = serializers.URLField(allow_null=True)
