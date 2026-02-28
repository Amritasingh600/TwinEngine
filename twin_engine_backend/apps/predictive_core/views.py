from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Avg
from .models import SalesData, InventoryItem, StaffSchedule
from .serializers import (
    SalesDataSerializer, SalesDataCreateSerializer,
    InventoryItemSerializer, InventoryItemListSerializer, InventoryUpdateSerializer,
    StaffScheduleSerializer, StaffScheduleCreateSerializer
)


class SalesDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Sales Data (for AI predictions).
    
    Endpoints:
    - GET /api/sales-data/ - List all sales data
    - POST /api/sales-data/ - Create new sales data
    - GET /api/sales-data/{id}/ - Retrieve sales data
    - GET /api/sales-data/trends/ - Get sales trends
    - GET /api/sales-data/hourly/ - Get hourly patterns
    """
    queryset = SalesData.objects.select_related('outlet').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['outlet', 'date', 'day_of_week', 'is_holiday']
    ordering_fields = ['date', 'hour', 'total_revenue']
    ordering = ['-date', 'hour']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SalesDataCreateSerializer
        return SalesDataSerializer
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get sales trends over time."""
        outlet_id = request.query_params.get('outlet')
        days = int(request.query_params.get('days', 30))
        
        from datetime import timedelta
        from django.utils import timezone
        start_date = timezone.now().date() - timedelta(days=days)
        
        qs = self.queryset.filter(date__gte=start_date)
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        daily = qs.values('date').annotate(
            orders=Sum('total_orders'),
            revenue=Sum('total_revenue'),
            avg_ticket=Avg('avg_ticket_size')
        ).order_by('date')
        
        return Response(list(daily))
    
    @action(detail=False, methods=['get'])
    def hourly_pattern(self, request):
        """Get average hourly patterns for predictions."""
        outlet_id = request.query_params.get('outlet')
        day_of_week = request.query_params.get('day_of_week')
        
        qs = self.queryset
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        if day_of_week is not None:
            qs = qs.filter(day_of_week=int(day_of_week))
        
        hourly = qs.values('hour').annotate(
            avg_orders=Avg('total_orders'),
            avg_revenue=Avg('total_revenue'),
            avg_wait=Avg('avg_wait_time_minutes')
        ).order_by('hour')
        
        return Response(list(hourly))


class InventoryItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Inventory Items.
    
    Endpoints:
    - GET /api/inventory/ - List all inventory items
    - POST /api/inventory/ - Create inventory item
    - GET /api/inventory/{id}/ - Retrieve inventory item
    - POST /api/inventory/{id}/adjust/ - Adjust quantity
    - GET /api/inventory/low-stock/ - Get low stock items
    """
    queryset = InventoryItem.objects.select_related('outlet').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['outlet', 'category']
    search_fields = ['name']
    ordering_fields = ['name', 'current_quantity', 'updated_at']
    ordering = ['outlet', 'category', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InventoryItemListSerializer
        return InventoryItemSerializer
    
    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """Adjust inventory quantity (add or subtract)."""
        item = self.get_object()
        serializer = InventoryUpdateSerializer(data=request.data)
        if serializer.is_valid():
            item = serializer.update(item, serializer.validated_data)
            return Response(InventoryItemSerializer(item).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all items below reorder threshold."""
        outlet_id = request.query_params.get('outlet')
        qs = self.queryset
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        # Filter for low stock items
        low_items = [item for item in qs if item.is_low_stock]
        serializer = InventoryItemSerializer(low_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get items expiring within X days."""
        from datetime import timedelta
        from django.utils import timezone
        
        days = int(request.query_params.get('days', 7))
        outlet_id = request.query_params.get('outlet')
        
        threshold = timezone.now().date() + timedelta(days=days)
        qs = self.queryset.filter(expiry_date__lte=threshold, expiry_date__isnull=False)
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        serializer = InventoryItemSerializer(qs, many=True)
        return Response(serializer.data)


class StaffScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Staff Schedules.
    
    Endpoints:
    - GET /api/schedules/ - List all schedules
    - POST /api/schedules/ - Create a schedule
    - GET /api/schedules/{id}/ - Retrieve schedule
    - POST /api/schedules/{id}/check-in/ - Record check-in
    - POST /api/schedules/{id}/check-out/ - Record check-out
    - GET /api/schedules/today/ - Get today's schedules
    """
    queryset = StaffSchedule.objects.select_related('staff', 'staff__user', 'staff__outlet').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['staff', 'staff__outlet', 'date', 'shift', 'is_confirmed']
    ordering_fields = ['date', 'start_time']
    ordering = ['-date', 'start_time']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StaffScheduleCreateSerializer
        return StaffScheduleSerializer
    
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """Record staff check-in."""
        from django.utils import timezone
        schedule = self.get_object()
        schedule.checked_in = timezone.now()
        schedule.save()
        return Response(StaffScheduleSerializer(schedule).data)
    
    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        """Record staff check-out."""
        from django.utils import timezone
        schedule = self.get_object()
        schedule.checked_out = timezone.now()
        schedule.save()
        return Response(StaffScheduleSerializer(schedule).data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's schedules."""
        from django.utils import timezone
        outlet_id = request.query_params.get('outlet')
        
        today = timezone.now().date()
        qs = self.queryset.filter(date=today)
        if outlet_id:
            qs = qs.filter(staff__outlet_id=outlet_id)
        
        serializer = StaffScheduleSerializer(qs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_staff(self, request):
        """Get schedules for a specific staff member."""
        staff_id = request.query_params.get('staff_id')
        if not staff_id:
            return Response({'error': 'staff_id parameter required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        qs = self.queryset.filter(staff_id=staff_id)
        serializer = StaffScheduleSerializer(qs, many=True)
        return Response(serializer.data)
