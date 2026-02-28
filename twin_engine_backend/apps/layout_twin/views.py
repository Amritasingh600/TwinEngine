from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import ServiceNode, ServiceFlow
from .serializers import (
    ServiceNodeSerializer, ServiceNodeListSerializer, ServiceNodeDetailSerializer,
    ServiceFlowSerializer
)


class ServiceNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Service Nodes (Tables, Kitchen Stations, etc.).
    
    Endpoints:
    - GET /api/nodes/ - Fetch all service nodes for 3D rendering
    - POST /api/nodes/ - Create a new service node
    - GET /api/nodes/{id}/ - Get detailed info for a node
    - PUT/PATCH /api/nodes/{id}/ - Update service node
    - DELETE /api/nodes/{id}/ - Delete service node
    - POST /api/nodes/{id}/update-status/ - Update node status (color)
    """
    queryset = ServiceNode.objects.select_related('outlet').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['outlet', 'node_type', 'current_status', 'is_active']
    search_fields = ['name', 'outlet__name']
    ordering_fields = ['name', 'current_status', 'updated_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceNodeListSerializer
        if self.action == 'retrieve':
            return ServiceNodeDetailSerializer
        return ServiceNodeSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update the status (color) of a service node."""
        node = self.get_object()
        new_status = request.data.get('status')
        
        valid_statuses = ['BLUE', 'RED', 'GREEN', 'YELLOW', 'GREY']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        node.current_status = new_status
        node.save()
        
        return Response({
            'id': node.id,
            'name': node.name,
            'status': node.current_status,
            'updated': True
        })
    
    @action(detail=True, methods=['get'])
    def order_history(self, request, pk=None):
        """Get order history for this table."""
        from apps.order_engine.serializers import OrderTicketSerializer
        node = self.get_object()
        if node.node_type != 'TABLE':
            return Response({'error': 'Order history only available for tables'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        limit = int(request.query_params.get('limit', 20))
        orders = node.orders.all()[:limit]
        serializer = OrderTicketSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_outlet(self, request):
        """Get all nodes for a specific outlet."""
        outlet_id = request.query_params.get('outlet_id')
        if not outlet_id:
            return Response({'error': 'outlet_id parameter required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        nodes = self.queryset.filter(outlet_id=outlet_id, is_active=True)
        serializer = ServiceNodeListSerializer(nodes, many=True)
        return Response(serializer.data)


class ServiceFlowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Service Flows (connections between nodes).
    
    Endpoints:
    - GET /api/flows/ - List all flows
    - POST /api/flows/ - Create a new flow
    - GET /api/flows/{id}/ - Retrieve flow details
    - PUT/PATCH /api/flows/{id}/ - Update flow
    - DELETE /api/flows/{id}/ - Delete flow
    - GET /api/flows/graph/ - Get full floor graph (nodes + flows)
    """
    queryset = ServiceFlow.objects.select_related('source_node', 'target_node').all()
    serializer_class = ServiceFlowSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['source_node', 'target_node', 'flow_type', 'is_active']
    
    @action(detail=False, methods=['get'])
    def graph(self, request):
        """Get full restaurant floor graph (nodes + flows) for visualization."""
        outlet_id = request.query_params.get('outlet')
        
        # Get nodes
        nodes_qs = ServiceNode.objects.filter(is_active=True)
        if outlet_id:
            nodes_qs = nodes_qs.filter(outlet_id=outlet_id)
        
        nodes = ServiceNodeListSerializer(nodes_qs, many=True).data
        
        # Get flows for those nodes
        node_ids = [n['id'] for n in nodes]
        flows_qs = ServiceFlow.objects.filter(
            source_node_id__in=node_ids,
            target_node_id__in=node_ids,
            is_active=True
        )
        flows = ServiceFlowSerializer(flows_qs, many=True).data
        
        return Response({
            'nodes': nodes,
            'flows': flows
        })
