from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Avg
from datetime import datetime
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes

from .models import SalesData, InventoryItem, StaffSchedule
from .serializers import (
    SalesDataSerializer, SalesDataCreateSerializer,
    InventoryItemSerializer, InventoryItemListSerializer, InventoryUpdateSerializer,
    StaffScheduleSerializer, StaffScheduleCreateSerializer
)
from .schema_serializers import (
    BusyHoursResponseSerializer, FootfallResponseSerializer,
    FoodDemandResponseSerializer, InventoryAlertsResponseSerializer,
    StaffingResponseSerializer, RevenueResponseSerializer,
    DashboardResponseSerializer, TrainResultSerializer,
    ErrorResponseSerializer,
)
from .ml.prediction_service import PredictionService
from twinengine_core.throttles import PredictionRateThrottle, TrainingRateThrottle


@extend_schema_view(
    list=extend_schema(tags=['Sales Data'], summary='List all sales data records'),
    create=extend_schema(tags=['Sales Data'], summary='Create a sales data record'),
    retrieve=extend_schema(tags=['Sales Data'], summary='Retrieve a sales data record'),
    update=extend_schema(tags=['Sales Data'], summary='Update a sales data record'),
    partial_update=extend_schema(tags=['Sales Data'], summary='Partial update a sales data record'),
    destroy=extend_schema(tags=['Sales Data'], summary='Delete a sales data record'),
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
    
    @extend_schema(tags=['Sales Data'], summary='Get sales trends over time', parameters=[
        OpenApiParameter('outlet', OpenApiTypes.INT, description='Filter by outlet ID'),
        OpenApiParameter('days', OpenApiTypes.INT, description='Number of days to look back (default 30)'),
    ])
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get sales trends over time."""
        outlet_id = request.query_params.get('outlet')
        try:
            days = int(request.query_params.get('days', 30))
        except (ValueError, TypeError):
            return Response({'error': 'days must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        
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
    
    @extend_schema(tags=['Sales Data'], summary='Get average hourly patterns', parameters=[
        OpenApiParameter('outlet', OpenApiTypes.INT, description='Filter by outlet ID'),
        OpenApiParameter('day_of_week', OpenApiTypes.INT, description='Day of week (0=Mon, 6=Sun)'),
    ])
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


@extend_schema_view(
    list=extend_schema(tags=['Inventory'], summary='List all inventory items'),
    create=extend_schema(tags=['Inventory'], summary='Create an inventory item'),
    retrieve=extend_schema(tags=['Inventory'], summary='Retrieve an inventory item'),
    update=extend_schema(tags=['Inventory'], summary='Update an inventory item'),
    partial_update=extend_schema(tags=['Inventory'], summary='Partial update an inventory item'),
    destroy=extend_schema(tags=['Inventory'], summary='Delete an inventory item'),
)
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
    
    @extend_schema(tags=['Inventory'], summary='Adjust inventory quantity', request=InventoryUpdateSerializer, responses={200: InventoryItemSerializer})
    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """Adjust inventory quantity (add or subtract)."""
        item = self.get_object()
        serializer = InventoryUpdateSerializer(data=request.data)
        if serializer.is_valid():
            item = serializer.update(item, serializer.validated_data)
            return Response(InventoryItemSerializer(item).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(tags=['Inventory'], summary='Get low-stock items', parameters=[
        OpenApiParameter('outlet', OpenApiTypes.INT, description='Filter by outlet ID'),
    ], responses={200: InventoryItemSerializer(many=True)})
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
    
    @extend_schema(tags=['Inventory'], summary='Get items expiring soon', parameters=[
        OpenApiParameter('days', OpenApiTypes.INT, description='Days until expiry (default 7)'),
        OpenApiParameter('outlet', OpenApiTypes.INT, description='Filter by outlet ID'),
    ], responses={200: InventoryItemSerializer(many=True)})
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get items expiring within X days."""
        from datetime import timedelta
        from django.utils import timezone
        
        try:
            days = int(request.query_params.get('days', 7))
        except (ValueError, TypeError):
            return Response({'error': 'days must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        outlet_id = request.query_params.get('outlet')
        
        threshold = timezone.now().date() + timedelta(days=days)
        qs = self.queryset.filter(expiry_date__lte=threshold, expiry_date__isnull=False)
        if outlet_id:
            qs = qs.filter(outlet_id=outlet_id)
        
        serializer = InventoryItemSerializer(qs, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Schedules'], summary='List all staff schedules'),
    create=extend_schema(tags=['Schedules'], summary='Create a staff schedule'),
    retrieve=extend_schema(tags=['Schedules'], summary='Retrieve a staff schedule'),
    update=extend_schema(tags=['Schedules'], summary='Update a staff schedule'),
    partial_update=extend_schema(tags=['Schedules'], summary='Partial update a staff schedule'),
    destroy=extend_schema(tags=['Schedules'], summary='Delete a staff schedule'),
)
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
    
    @extend_schema(tags=['Schedules'], summary='Record staff check-in', request=None, responses={200: StaffScheduleSerializer})
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """Record staff check-in."""
        from django.utils import timezone
        schedule = self.get_object()
        schedule.checked_in = timezone.now()
        schedule.save()
        return Response(StaffScheduleSerializer(schedule).data)
    
    @extend_schema(tags=['Schedules'], summary='Record staff check-out', request=None, responses={200: StaffScheduleSerializer})
    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        """Record staff check-out."""
        from django.utils import timezone
        schedule = self.get_object()
        schedule.checked_out = timezone.now()
        schedule.save()
        return Response(StaffScheduleSerializer(schedule).data)
    
    @extend_schema(tags=['Schedules'], summary="Get today's schedules", parameters=[
        OpenApiParameter('outlet', OpenApiTypes.INT, description='Filter by outlet ID'),
    ], responses={200: StaffScheduleSerializer(many=True)})
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
    
    @extend_schema(tags=['Schedules'], summary='Get schedules for a specific staff member', parameters=[
        OpenApiParameter('staff_id', OpenApiTypes.INT, description='Staff member ID', required=True),
    ], responses={200: StaffScheduleSerializer(many=True)})
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


# =====================================================================
# Prediction API Endpoints
# =====================================================================

_PREDICTION_PARAMS = [
    OpenApiParameter('outlet', OpenApiTypes.INT, description='Outlet ID', required=True),
    OpenApiParameter('date', OpenApiTypes.DATE, description='Target date (YYYY-MM-DD, default today)', required=False),
]


class PredictionBaseView(APIView):
    """Base view with shared parameter parsing."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [PredictionRateThrottle]

    def _parse_params(self, request):
        outlet_id = request.query_params.get('outlet')
        date_str = request.query_params.get('date')

        if not outlet_id:
            return None, None, Response(
                {"error": "outlet query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            outlet_id = int(outlet_id)
        except ValueError:
            return None, None, Response(
                {"error": "outlet must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None, None, Response(
                    {"error": "date must be YYYY-MM-DD format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            from django.utils import timezone
            target_date = timezone.now().date()

        return outlet_id, target_date, None


class BusyHoursPredictionView(PredictionBaseView):
    """Predict busy hours for an outlet on a given date."""

    @extend_schema(
        tags=['Predictions'],
        summary='Predict busy hours',
        parameters=_PREDICTION_PARAMS,
        responses={200: BusyHoursResponseSerializer, 400: ErrorResponseSerializer},
    )
    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_busy_hours(outlet_id, target_date)
        return Response(result)


class FootfallPredictionView(PredictionBaseView):
    """Predict hourly guest footfall for an outlet."""

    @extend_schema(
        tags=['Predictions'],
        summary='Predict footfall',
        parameters=_PREDICTION_PARAMS,
        responses={200: FootfallResponseSerializer, 400: ErrorResponseSerializer},
    )
    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_footfall(outlet_id, target_date)
        return Response(result)


class FoodDemandPredictionView(PredictionBaseView):
    """Predict per-category food demand revenue."""

    @extend_schema(
        tags=['Predictions'],
        summary='Predict food demand',
        parameters=_PREDICTION_PARAMS,
        responses={200: FoodDemandResponseSerializer, 400: ErrorResponseSerializer},
    )
    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_food_demand(outlet_id, target_date)
        return Response(result)


class InventoryAlertView(PredictionBaseView):
    """Get AI-based inventory reorder alerts."""

    @extend_schema(
        tags=['Predictions'],
        summary='Get inventory alerts',
        parameters=[_PREDICTION_PARAMS[0]],
        responses={200: InventoryAlertsResponseSerializer, 400: ErrorResponseSerializer},
    )
    def get(self, request):
        outlet_id, _, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_inventory_alerts(outlet_id)
        return Response(result)


class StaffingPredictionView(PredictionBaseView):
    """Get AI staffing recommendations by shift."""

    @extend_schema(
        tags=['Predictions'],
        summary='Predict staffing needs',
        parameters=_PREDICTION_PARAMS,
        responses={200: StaffingResponseSerializer, 400: ErrorResponseSerializer},
    )
    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_staffing(outlet_id, target_date)
        return Response(result)


class RevenuePredictionView(PredictionBaseView):
    """Forecast revenue for the next N days."""

    @extend_schema(
        tags=['Predictions'],
        summary='Forecast revenue',
        parameters=_PREDICTION_PARAMS + [
            OpenApiParameter('days', OpenApiTypes.INT, description='Number of forecast days (default 7)'),
        ],
        responses={200: RevenueResponseSerializer, 400: ErrorResponseSerializer},
    )
    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        try:
            days = int(request.query_params.get('days', 7))
        except (ValueError, TypeError):
            return Response({'error': 'days must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        service = PredictionService()
        result = service.get_revenue_forecast(outlet_id, target_date, days)
        return Response(result)


class PredictionDashboardView(PredictionBaseView):
    """Aggregated dashboard with all prediction types."""

    @extend_schema(
        tags=['Predictions'],
        summary='Get prediction dashboard (all models)',
        parameters=_PREDICTION_PARAMS,
        responses={200: DashboardResponseSerializer, 400: ErrorResponseSerializer},
    )
    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_dashboard(outlet_id, target_date)
        return Response(result)


class TrainModelsView(APIView):
    """
    Manager-only endpoint to trigger model retraining for an outlet.
    Training runs asynchronously via Celery; the response returns a task ID
    that can be polled at /api/tasks/{task_id}/.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [TrainingRateThrottle]

    @extend_schema(
        tags=['Predictions'],
        summary='Train ML models for an outlet (async)',
        parameters=[
            OpenApiParameter('outlet', OpenApiTypes.INT, description='Outlet ID', required=True),
            OpenApiParameter('sync', OpenApiTypes.BOOL, description='Run synchronously (default false)', required=False),
        ],
        request=None,
        responses={202: TrainResultSerializer, 200: TrainResultSerializer, 400: ErrorResponseSerializer},
    )
    def post(self, request):
        outlet_id = request.query_params.get('outlet')
        if not outlet_id:
            return Response(
                {"error": "outlet query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            outlet_id = int(outlet_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "outlet must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Allow ?sync=true for backward-compat / testing
        run_sync = request.query_params.get('sync', 'false').lower() == 'true'

        if run_sync:
            service = PredictionService()
            results = service.train_all(outlet_id)
            return Response({"status": "training complete", "results": results})

        # Dispatch to Celery
        from .tasks import train_models_for_outlet
        task = train_models_for_outlet.delay(outlet_id)
        return Response(
            {
                "status": "training dispatched",
                "task_id": task.id,
                "poll_url": f"/api/tasks/{task.id}/",
            },
            status=status.HTTP_202_ACCEPTED,
        )
