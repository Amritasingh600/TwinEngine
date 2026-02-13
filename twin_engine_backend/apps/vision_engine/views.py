from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Max
from .models import VisionLog, DetectionZone
from .serializers import (
    VisionLogSerializer, VisionLogCreateSerializer, VisionLogBulkSerializer,
    DetectionZoneSerializer, DetectionZoneUpdateSerializer,
    VisionCountSummarySerializer
)


class VisionLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Vision Logs (AI detections).
    
    Endpoints:
    - GET /api/vision-logs/ - List all vision logs
    - POST /api/vision-logs/ - Create a new vision log
    - GET /api/vision-logs/{id}/ - Retrieve vision log
    - POST /api/vision-logs/bulk/ - Bulk create vision logs
    - GET /api/vision-logs/summary/ - Get count summary per node
    """
    queryset = VisionLog.objects.select_related('machine_node').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['machine_node', 'object_type']
    ordering_fields = ['timestamp', 'confidence_score', 'current_total']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VisionLogCreateSerializer
        return VisionLogSerializer
    
    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """Bulk create vision logs from AI inference."""
        serializer = VisionLogBulkSerializer(data=request.data)
        if serializer.is_valid():
            created = serializer.save()
            return Response(
                {'created': len(created), 'message': 'Vision logs recorded successfully'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get vision count summary per machine node."""
        from apps.factory_graph.models import MachineNode
        
        # Get the latest count for each node/object_type combination
        summaries = VisionLog.objects.values(
            'machine_node', 'machine_node__name', 'object_type'
        ).annotate(
            total_count=Max('current_total'),
            last_detection=Max('timestamp')
        ).order_by('machine_node')
        
        results = []
        for s in summaries:
            results.append({
                'machine_node_id': s['machine_node'],
                'machine_node_name': s['machine_node__name'],
                'object_type': s['object_type'],
                'total_count': s['total_count'],
                'last_detection': s['last_detection']
            })
        
        return Response(results)
    
    @action(detail=False, methods=['get'])
    def by_node(self, request):
        """Get vision logs for a specific node."""
        node_id = request.query_params.get('node_id')
        if not node_id:
            return Response(
                {'error': 'node_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        limit = int(request.query_params.get('limit', 100))
        logs = self.queryset.filter(machine_node_id=node_id)[:limit]
        serializer = VisionLogSerializer(logs, many=True)
        return Response(serializer.data)


class DetectionZoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Detection Zones (counting lines).
    
    Endpoints:
    - GET /api/detection-zones/ - List all detection zones
    - POST /api/detection-zones/ - Create a new detection zone
    - GET /api/detection-zones/{id}/ - Retrieve detection zone
    - PATCH /api/detection-zones/{id}/ - Update detection zone
    - POST /api/detection-zones/{id}/increment/ - Increment loop count
    - POST /api/detection-zones/{id}/reset/ - Reset loop count
    """
    queryset = DetectionZone.objects.select_related('machine_node').all()
    serializer_class = DetectionZoneSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['machine_node', 'active_status']
    
    @action(detail=True, methods=['post'])
    def increment(self, request, pk=None):
        """Increment the loop count (object crossed the line)."""
        zone = self.get_object()
        increment_by = int(request.data.get('count', 1))
        zone.loop_count += increment_by
        zone.save()
        
        return Response({
            'id': zone.id,
            'machine_node': zone.machine_node.name,
            'loop_count': zone.loop_count,
            'incremented_by': increment_by
        })
    
    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        """Reset the loop count to zero."""
        zone = self.get_object()
        old_count = zone.loop_count
        zone.loop_count = 0
        zone.save()
        
        return Response({
            'id': zone.id,
            'machine_node': zone.machine_node.name,
            'previous_count': old_count,
            'loop_count': 0,
            'reset': True
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active detection zones."""
        zones = self.queryset.filter(active_status=True)
        serializer = DetectionZoneSerializer(zones, many=True)
        return Response(serializer.data)
