from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ShiftLog, ProductionReport
from .serializers import (
    ShiftLogSerializer, ShiftLogCreateSerializer, ShiftLogSummarySerializer,
    ProductionReportSerializer, ProductionReportListSerializer,
    ReportGenerateSerializer, DailyReportResponseSerializer
)


class ShiftLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Shift Logs.
    
    Endpoints:
    - GET /api/shift-logs/ - List all shift logs
    - POST /api/shift-logs/ - Create a new shift log
    - GET /api/shift-logs/{id}/ - Retrieve shift log
    - GET /api/shift-logs/summary/ - Get aggregated statistics
    - GET /api/shift-logs/daily/ - Get daily summary
    """
    queryset = ShiftLog.objects.select_related('manufacturer').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['manufacturer', 'date']
    ordering_fields = ['date', 'shift_start', 'total_units']
    ordering = ['-date', '-shift_start']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ShiftLogCreateSerializer
        return ShiftLogSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get aggregated shift statistics."""
        manufacturer_id = request.query_params.get('manufacturer')
        days = int(request.query_params.get('days', 7))
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        qs = self.queryset.filter(date__gte=start_date)
        if manufacturer_id:
            qs = qs.filter(manufacturer_id=manufacturer_id)
        
        # Aggregate by date
        daily_stats = qs.values('date').annotate(
            total_shifts=Count('id'),
            total_units=Sum('total_units'),
            total_downtime=Sum('total_downtime'),
            total_anomalies=Sum('anomaly_count'),
            avg_efficiency=Avg('total_units')  # Simplified
        ).order_by('-date')
        
        return Response(list(daily_stats))
    
    @action(detail=False, methods=['get'])
    def daily(self, request):
        """Get today's shift summary."""
        manufacturer_id = request.query_params.get('manufacturer')
        date_str = request.query_params.get('date')
        
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = timezone.now().date()
        
        qs = self.queryset.filter(date=target_date)
        if manufacturer_id:
            qs = qs.filter(manufacturer_id=manufacturer_id)
        
        serializer = ShiftLogSerializer(qs, many=True)
        
        # Calculate totals
        totals = qs.aggregate(
            total_units=Sum('total_units'),
            total_downtime=Sum('total_downtime'),
            total_anomalies=Sum('anomaly_count')
        )
        
        return Response({
            'date': target_date,
            'shifts': serializer.data,
            'totals': totals
        })


class ProductionReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Production Reports.
    
    Endpoints:
    - GET /api/reports/ - List all reports
    - POST /api/reports/ - Create a new report
    - GET /api/reports/{id}/ - Retrieve report details
    - POST /api/reports/generate/ - Generate a new report using GPT-4o
    """
    queryset = ProductionReport.objects.select_related('manufacturer').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['manufacturer', 'date', 'generation_type']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductionReportListSerializer
        return ProductionReportSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new production report using GPT-4o.
        This is a placeholder - actual implementation would call Azure OpenAI.
        """
        serializer = ReportGenerateSerializer(data=request.data)
        if serializer.is_valid():
            from apps.manufacturers.models import Manufacturer
            
            manufacturer_id = serializer.validated_data['manufacturer_id']
            report_date = serializer.validated_data['date']
            gen_type = serializer.validated_data['generation_type']
            
            manufacturer = Manufacturer.objects.get(id=manufacturer_id)
            
            # Get shift data for the report
            shifts = ShiftLog.objects.filter(
                manufacturer=manufacturer,
                date=report_date
            )
            
            # Placeholder for GPT-4o integration
            # In production, this would call Azure OpenAI API
            gpt_summary = self._generate_summary(manufacturer, report_date, shifts)
            
            # Create the report
            report = ProductionReport.objects.create(
                manufacturer=manufacturer,
                date=report_date,
                cloudinary_url='',  # Would be set after PDF upload
                gpt_summary=gpt_summary,
                generation_type=gen_type
            )
            
            return Response(ProductionReportSerializer(report).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _generate_summary(self, manufacturer, report_date, shifts):
        """
        Placeholder for GPT-4o summary generation.
        In production, this would call Azure OpenAI API.
        """
        total_units = sum(s.total_units for s in shifts)
        total_downtime = sum(s.total_downtime for s in shifts)
        total_anomalies = sum(s.anomaly_count for s in shifts)
        
        return f"""
## Daily Production Report - {manufacturer.name}
### Date: {report_date}

### Summary
- **Total Shifts:** {shifts.count()}
- **Total Units Produced:** {total_units}
- **Total Downtime:** {total_downtime:.1f} minutes
- **Anomalies Detected:** {total_anomalies}

### Analysis
Production {'met expectations' if total_anomalies < 5 else 'experienced some issues'} today.
{'Operations ran smoothly with minimal interruptions.' if total_downtime < 30 else 'Some downtime was recorded that may require investigation.'}

### Recommendations
1. {'Continue monitoring standard operations.' if total_anomalies < 3 else 'Review anomaly logs for patterns.'}
2. {'Maintain current efficiency levels.' if total_downtime < 60 else 'Investigate causes of extended downtime.'}

---
*Report generated automatically by TwinEngine AI*
        """


class DailyReportView(APIView):
    """
    API endpoint to retrieve GPT-4o generated operational summary.
    
    GET /api/reports/daily/
    Query params: date (YYYY-MM-DD), manufacturer (optional)
    Response: { report_text: string }
    """
    
    def get(self, request):
        date_str = request.query_params.get('date')
        manufacturer_id = request.query_params.get('manufacturer')
        
        if not date_str:
            date_str = timezone.now().date().isoformat()
        
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find existing report
        qs = ProductionReport.objects.filter(date=report_date)
        if manufacturer_id:
            qs = qs.filter(manufacturer_id=manufacturer_id)
        
        report = qs.first()
        
        if report:
            return Response({
                'report_text': report.gpt_summary,
                'generated_at': report.created_at,
                'cloudinary_url': report.cloudinary_url or None
            })
        else:
            return Response(
                {'error': f'No report found for date {report_date}'},
                status=status.HTTP_404_NOT_FOUND
            )
