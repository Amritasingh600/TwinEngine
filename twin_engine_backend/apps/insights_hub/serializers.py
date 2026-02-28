from rest_framework import serializers
from .models import DailySummary, PDFReport


class DailySummarySerializer(serializers.ModelSerializer):
    """Serializer for DailySummary model."""
    outlet_name = serializers.CharField(source='outlet.name', read_only=True)
    
    class Meta:
        model = DailySummary
        fields = [
            'id', 'outlet', 'outlet_name', 'date',
            'total_revenue', 'total_orders', 'avg_ticket_size', 'total_tips',
            'total_guests', 'avg_table_turnover_time', 'avg_wait_time',
            'peak_hour', 'peak_revenue',
            'delayed_orders', 'cancelled_orders',
            'sales_by_category', 'top_selling_items',
            'staff_count', 'revenue_per_staff',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DailySummaryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing daily summaries."""
    outlet_name = serializers.CharField(source='outlet.name', read_only=True)
    
    class Meta:
        model = DailySummary
        fields = ['id', 'outlet_name', 'date', 'total_revenue', 'total_orders', 'total_guests']


class DailySummaryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating daily summaries."""
    
    class Meta:
        model = DailySummary
        fields = [
            'outlet', 'date',
            'total_revenue', 'total_orders', 'avg_ticket_size', 'total_tips',
            'total_guests', 'avg_table_turnover_time', 'avg_wait_time',
            'peak_hour', 'peak_revenue',
            'delayed_orders', 'cancelled_orders',
            'sales_by_category', 'top_selling_items',
            'staff_count', 'revenue_per_staff'
        ]


class PDFReportSerializer(serializers.ModelSerializer):
    """Serializer for PDFReport model."""
    outlet_name = serializers.CharField(source='outlet.name', read_only=True)
    
    class Meta:
        model = PDFReport
        fields = [
            'id', 'outlet', 'outlet_name', 'report_type',
            'start_date', 'end_date',
            'cloudinary_url', 'gpt_summary', 'insights', 'recommendations',
            'status', 'error_message', 'generated_by',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']


class PDFReportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reports."""
    outlet_name = serializers.CharField(source='outlet.name', read_only=True)
    
    class Meta:
        model = PDFReport
        fields = ['id', 'outlet_name', 'report_type', 'start_date', 'end_date', 'status', 'created_at']


class ReportGenerateSerializer(serializers.Serializer):
    """Serializer for triggering report generation."""
    outlet_id = serializers.IntegerField()
    report_type = serializers.ChoiceField(choices=['DAILY', 'WEEKLY', 'MONTHLY', 'CUSTOM'], default='DAILY')
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False)
    
    def validate_outlet_id(self, value):
        from apps.hospitality_group.models import Outlet
        if not Outlet.objects.filter(id=value).exists():
            raise serializers.ValidationError("Outlet does not exist.")
        return value
    
    def validate(self, data):
        if data.get('end_date') is None:
            data['end_date'] = data['start_date']
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError("end_date cannot be before start_date")
        return data


class DailyReportResponseSerializer(serializers.Serializer):
    """Response serializer for /api/reports/daily/ endpoint."""
    report_text = serializers.CharField()
    insights = serializers.ListField(child=serializers.CharField())
    recommendations = serializers.ListField(child=serializers.CharField())
    generated_at = serializers.DateTimeField()
    cloudinary_url = serializers.URLField(allow_null=True)
