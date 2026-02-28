from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import DailySummary, PDFReport
from .serializers import (
    DailySummarySerializer, DailySummaryListSerializer, DailySummaryCreateSerializer,
    PDFReportSerializer, PDFReportListSerializer,
    ReportGenerateSerializer, DailyReportResponseSerializer
)


class DailySummaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Daily Summaries.
    
    Endpoints:
    - GET /api/summaries/ - List all daily summaries
    - POST /api/summaries/ - Create a new summary
    - GET /api/summaries/{id}/ - Retrieve summary
    - GET /api/summaries/trends/ - Get trends over time
    - GET /api/summaries/compare/ - Compare outlets
    """
    queryset = DailySummary.objects.select_related('outlet').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['outlet', 'date', 'outlet__brand']
    ordering_fields = ['date', 'total_revenue', 'total_orders']
    ordering = ['-date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DailySummaryCreateSerializer
        if self.action == 'list':
            return DailySummaryListSerializer
        return DailySummarySerializer
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get performance trends over time."""
        outlet_id = request.query_params.get('outlet')
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        qs = self.queryset.filter(date__gte=start_date)
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        # Daily aggregates
        daily = qs.values('date').annotate(
            revenue=Sum('total_revenue'),
            orders=Sum('total_orders'),
            guests=Sum('total_guests'),
            avg_wait=Avg('avg_wait_time')
        ).order_by('date')
        
        return Response(list(daily))
    
    @action(detail=False, methods=['get'])
    def compare(self, request):
        """Compare performance across outlets."""
        brand_id = request.query_params.get('brand')
        days = int(request.query_params.get('days', 7))
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        qs = self.queryset.filter(date__gte=start_date)
        if brand_id:
            qs = qs.filter(outlet__brand_id=brand_id)
        
        # Aggregate by outlet
        by_outlet = qs.values('outlet', 'outlet__name').annotate(
            total_revenue=Sum('total_revenue'),
            total_orders=Sum('total_orders'),
            avg_ticket=Avg('avg_ticket_size'),
            avg_wait=Avg('avg_wait_time')
        ).order_by('-total_revenue')
        
        return Response(list(by_outlet))
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's summary (or generate one)."""
        outlet_id = request.query_params.get('outlet')
        today = timezone.now().date()
        
        qs = self.queryset.filter(date=today)
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        summaries = DailySummarySerializer(qs, many=True).data
        return Response(summaries)


class PDFReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing PDF Reports.
    
    Endpoints:
    - GET /api/reports/ - List all reports
    - POST /api/reports/ - Create a new report
    - GET /api/reports/{id}/ - Retrieve report details
    - POST /api/reports/generate/ - Generate a new report using GPT-4
    """
    queryset = PDFReport.objects.select_related('outlet').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['outlet', 'report_type', 'status', 'outlet__brand']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PDFReportListSerializer
        return PDFReportSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new PDF report using GPT-4.
        This is a placeholder - actual implementation would call Azure OpenAI.
        """
        serializer = ReportGenerateSerializer(data=request.data)
        if serializer.is_valid():
            from apps.hospitality_group.models import Outlet
            
            outlet_id = serializer.validated_data['outlet_id']
            report_type = serializer.validated_data['report_type']
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            
            outlet = Outlet.objects.get(id=outlet_id)
            
            # Get daily summaries for the report period
            summaries = DailySummary.objects.filter(
                outlet=outlet,
                date__gte=start_date,
                date__lte=end_date
            )
            
            # Generate report content (placeholder for GPT-4 integration)
            gpt_summary, insights, recommendations = self._generate_report_content(
                outlet, start_date, end_date, summaries
            )
            
            # Create the report
            report = PDFReport.objects.create(
                outlet=outlet,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                gpt_summary=gpt_summary,
                insights=insights,
                recommendations=recommendations,
                status='COMPLETED',
                completed_at=timezone.now()
            )
            
            return Response(PDFReportSerializer(report).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _generate_report_content(self, outlet, start_date, end_date, summaries):
        """
        Placeholder for GPT-4 report generation.
        In production, this would call Azure OpenAI API.
        """
        total_revenue = sum(s.total_revenue for s in summaries) if summaries else 0
        total_orders = sum(s.total_orders for s in summaries) if summaries else 0
        total_guests = sum(s.total_guests for s in summaries) if summaries else 0
        avg_wait = sum(s.avg_wait_time for s in summaries) / len(summaries) if summaries else 0
        
        gpt_summary = f"""
## Operations Report - {outlet.name}
### Period: {start_date} to {end_date}

### Key Metrics
- **Total Revenue:** ₹{total_revenue:,.2f}
- **Total Orders:** {total_orders:,}
- **Total Guests:** {total_guests:,}
- **Average Wait Time:** {avg_wait:.1f} minutes

### Performance Overview
The outlet {'performed well' if avg_wait < 15 else 'experienced some delays'} during this period.
{'Customer satisfaction likely remained high.' if avg_wait < 12 else 'Consider reviewing kitchen efficiency.'}

---
*Report generated by TwinEngine Hospitality AI*
        """
        
        insights = [
            f"Total revenue for the period: ₹{total_revenue:,.2f}",
            f"Average orders per day: {total_orders / max(1, (end_date - start_date).days + 1):.0f}",
            f"Average wait time: {avg_wait:.1f} minutes"
        ]
        
        recommendations = []
        if avg_wait > 15:
            recommendations.append("Consider adding staff during peak hours to reduce wait times")
        if total_orders > 0:
            recommendations.append("Maintain current inventory levels based on order volume")
        recommendations.append("Review top-selling items to optimize menu placement")
        
        return gpt_summary, insights, recommendations


class DailyReportView(APIView):
    """
    API endpoint to retrieve AI-generated operational summary.
    
    GET /api/reports/daily/
    Query params: date (YYYY-MM-DD), outlet (optional)
    Response: { report_text: string, insights: [], recommendations: [] }
    """
    
    def get(self, request):
        date_str = request.query_params.get('date')
        outlet_id = request.query_params.get('outlet')
        
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
        qs = PDFReport.objects.filter(
            start_date__lte=report_date,
            end_date__gte=report_date,
            status='COMPLETED'
        )
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        report = qs.first()
        
        if report:
            return Response({
                'report_text': report.gpt_summary,
                'insights': report.insights,
                'recommendations': report.recommendations,
                'generated_at': report.completed_at,
                'cloudinary_url': report.cloudinary_url or None
            })
        else:
            return Response(
                {'error': f'No report found for date {report_date}'},
                status=status.HTTP_404_NOT_FOUND
            )
