from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import MachineType, MachineNode, MachineEdge
from .serializers import (
    MachineTypeSerializer, MachineTypeListSerializer,
    MachineNodeSerializer, MachineNodeListSerializer, MachineNodeDetailSerializer,
    MachineEdgeSerializer
)


class MachineTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Machine Types (3D templates).
    
    Endpoints:
    - GET /api/machine-types/ - List all machine types
    - POST /api/machine-types/ - Create a new machine type
    - GET /api/machine-types/{id}/ - Retrieve machine type details
    - PUT/PATCH /api/machine-types/{id}/ - Update machine type
    - DELETE /api/machine-types/{id}/ - Delete machine type
    """
    queryset = MachineType.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MachineTypeListSerializer
        return MachineTypeSerializer


class MachineNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Machine Nodes (3D factory floor).
    
    Endpoints (per API spec):
    - GET /api/nodes/ - Fetch all factory nodes for 3D rendering
    - POST /api/nodes/ - Create a new machine node
    - GET /api/nodes/{id}/ - Get detailed live feed and sensor data for a node
    - PUT/PATCH /api/nodes/{id}/ - Update machine node
    - DELETE /api/nodes/{id}/ - Delete machine node
    - POST /api/nodes/{id}/update-status/ - Update node status
    """
    queryset = MachineNode.objects.select_related('manufacturer', 'machine_type').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['manufacturer', 'machine_type', 'status']
    search_fields = ['name', 'manufacturer__name']
    ordering_fields = ['name', 'status', 'updated_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MachineNodeListSerializer
        if self.action == 'retrieve':
            return MachineNodeDetailSerializer
        return MachineNodeSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update the status of a machine node."""
        node = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['NORMAL', 'WARNING', 'ERROR', 'OFFLINE']:
            return Response(
                {'error': 'Invalid status. Must be NORMAL, WARNING, ERROR, or OFFLINE.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        node.status = new_status
        node.save()
        
        return Response({
            'id': node.id,
            'name': node.name,
            'status': node.status,
            'updated': True
        })
    
    @action(detail=True, methods=['get'])
    def sensor_history(self, request, pk=None):
        """Get sensor data history for this node."""
        from apps.sensors.serializers import SensorDataSerializer
        node = self.get_object()
        limit = int(request.query_params.get('limit', 50))
        sensor_data = node.sensor_data.all()[:limit]
        serializer = SensorDataSerializer(sensor_data, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def vision_history(self, request, pk=None):
        """Get vision log history for this node."""
        from apps.vision_engine.serializers import VisionLogSerializer
        node = self.get_object()
        limit = int(request.query_params.get('limit', 50))
        vision_logs = node.vision_logs.all()[:limit]
        serializer = VisionLogSerializer(vision_logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        """Get active alerts for this node."""
        from apps.sensors.models import AnomalyAlert
        from apps.sensors.serializers import AnomalyAlertSerializer
        node = self.get_object()
        alerts = AnomalyAlert.objects.filter(
            sensor_data__machine_node=node,
            resolved_status=False
        ).select_related('sensor_data')
        serializer = AnomalyAlertSerializer(alerts, many=True)
        return Response(serializer.data)


class MachineEdgeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Machine Edges (flow connections).
    
    Endpoints:
    - GET /api/edges/ - List all edges
    - POST /api/edges/ - Create a new edge
    - GET /api/edges/{id}/ - Retrieve edge details
    - PUT/PATCH /api/edges/{id}/ - Update edge
    - DELETE /api/edges/{id}/ - Delete edge
    """
    queryset = MachineEdge.objects.select_related('source_node', 'target_node').all()
    serializer_class = MachineEdgeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['source_node', 'target_node', 'flow_type']
    
    @action(detail=False, methods=['get'])
    def graph(self, request):
        """Get full factory graph (nodes + edges) for visualization."""
        manufacturer_id = request.query_params.get('manufacturer')
        
        # Get nodes
        nodes_qs = MachineNode.objects.all()
        if manufacturer_id:
            nodes_qs = nodes_qs.filter(manufacturer_id=manufacturer_id)
        
        nodes = MachineNodeListSerializer(nodes_qs, many=True).data
        
        # Get edges for those nodes
        node_ids = [n['id'] for n in nodes]
        edges_qs = MachineEdge.objects.filter(
            source_node_id__in=node_ids,
            target_node_id__in=node_ids
        )
        edges = MachineEdgeSerializer(edges_qs, many=True).data
        
        return Response({
            'nodes': nodes,
            'edges': edges
        })
