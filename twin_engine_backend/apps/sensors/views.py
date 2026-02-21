from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import SensorData, AnomalyAlert
from .serializers import (
    SensorDataSerializer, SensorDataCreateSerializer, SensorDataBulkSerializer,
    AnomalyAlertSerializer, AnomalyAlertCreateSerializer, AnomalyResolveSerializer,
    AnomalyTriggerSerializer
)


class SensorDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Sensor Data.
    
    Endpoints:
    - GET /api/sensor-data/ - List all sensor readings
    - POST /api/sensor-data/ - Create a new sensor reading
    - GET /api/sensor-data/{id}/ - Retrieve sensor reading
    - POST /api/sensor-data/bulk/ - Bulk create sensor readings
    - GET /api/sensor-data/latest/ - Get latest reading per node
    """
    queryset = SensorData.objects.select_related('machine_node').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['machine_node']
    ordering_fields = ['timestamp', 'temperature', 'vibration']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SensorDataCreateSerializer
        return SensorDataSerializer
    
    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """Bulk create sensor data from IoT devices."""
        serializer = SensorDataBulkSerializer(data=request.data)
        if serializer.is_valid():
            created = serializer.save()
            return Response(
                {'created': len(created), 'message': 'Sensor data ingested successfully'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the latest sensor reading for each machine node."""
        from apps.factory_graph.models import MachineNode
        from django.db.models import Max
        
        # Get latest timestamp for each node
        latest_timestamps = SensorData.objects.values('machine_node').annotate(
            latest=Max('timestamp')
        )
        
        results = []
        for item in latest_timestamps:
            sensor = SensorData.objects.filter(
                machine_node_id=item['machine_node'],
                timestamp=item['latest']
            ).select_related('machine_node').first()
            if sensor:
                results.append(SensorDataSerializer(sensor).data)
        
        return Response(results)


class AnomalyAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Anomaly Alerts.
    
    Endpoints:
    - GET /api/alerts/ - List all alerts
    - POST /api/alerts/ - Create a new alert
    - GET /api/alerts/{id}/ - Retrieve alert details
    - POST /api/alerts/{id}/resolve/ - Resolve an alert
    - GET /api/alerts/active/ - Get all unresolved alerts
    """
    queryset = AnomalyAlert.objects.select_related(
        'sensor_data', 'sensor_data__machine_node'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['severity', 'resolved_status', 'ai_prediction']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AnomalyAlertCreateSerializer
        return AnomalyAlertSerializer
    
    def perform_create(self, serializer):
        """Create alert and broadcast via WebSocket."""
        alert = serializer.save()
        
        # Get manufacturer_id from the related sensor_data -> machine_node
        manufacturer_id = alert.sensor_data.machine_node.manufacturer_id
        
        # Broadcast new alert via WebSocket
        from apps.factory_graph.utils.broadcast import broadcast_new_alert
        alert_data = AnomalyAlertSerializer(alert).data
        broadcast_new_alert(alert_data, manufacturer_id=manufacturer_id)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark an alert as resolved and broadcast via WebSocket."""
        alert = self.get_object()
        serializer = AnomalyResolveSerializer(alert, data=request.data)
        if serializer.is_valid():
            # Get manufacturer_id before updating
            manufacturer_id = alert.sensor_data.machine_node.manufacturer_id
            
            alert = serializer.update(alert, serializer.validated_data)
            
            # Broadcast alert resolution via WebSocket
            from apps.factory_graph.utils.broadcast import broadcast_alert_resolved
            broadcast_alert_resolved(
                alert_id=alert.id,
                resolved_by=request.user.username if request.user.is_authenticated else None,
                manufacturer_id=manufacturer_id
            )
            
            return Response(AnomalyAlertSerializer(alert).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all unresolved alerts."""
        alerts = self.queryset.filter(resolved_status=False)
        serializer = AnomalyAlertSerializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get alert summary statistics."""
        total = self.queryset.count()
        active = self.queryset.filter(resolved_status=False).count()
        by_severity = {
            'critical': self.queryset.filter(severity='CRITICAL', resolved_status=False).count(),
            'high': self.queryset.filter(severity='HIGH', resolved_status=False).count(),
            'medium': self.queryset.filter(severity='MEDIUM', resolved_status=False).count(),
            'low': self.queryset.filter(severity='LOW', resolved_status=False).count(),
        }
        return Response({
            'total_alerts': total,
            'active_alerts': active,
            'resolved_alerts': total - active,
            'by_severity': by_severity
        })


class AnomalyTriggerView(APIView):
    """
    API endpoint to update node status based on ML/slider data.
    
    POST /api/anomaly/trigger/
    Request: { node_id: int, status: string }
    Response: { updated: true }
    """
    
    def post(self, request):
        serializer = AnomalyTriggerSerializer(data=request.data)
        if serializer.is_valid():
            from apps.factory_graph.models import MachineNode
            
            node_id = serializer.validated_data['node_id']
            new_status = serializer.validated_data['status']
            
            node = MachineNode.objects.get(id=node_id)
            old_status = node.status
            node.status = new_status
            node.save()
            
            # Broadcast status change via WebSocket
            from apps.factory_graph.utils.broadcast import broadcast_node_status_change
            broadcast_node_status_change(
                manufacturer_id=node.manufacturer_id,
                node_id=node_id,
                node_name=node.name,
                new_status=new_status,
                previous_status=old_status
            )
            
            return Response({
                'updated': True,
                'node_id': node_id,
                'old_status': old_status,
                'new_status': new_status
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
