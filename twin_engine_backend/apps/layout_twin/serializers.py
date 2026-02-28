from rest_framework import serializers
from .models import ServiceNode, ServiceFlow


class ServiceNodeSerializer(serializers.ModelSerializer):
    """Serializer for ServiceNode model (tables, kitchen stations, etc.)."""
    outlet_name = serializers.CharField(source='outlet.name', read_only=True)
    status_display = serializers.CharField(source='get_current_status_display', read_only=True)
    
    class Meta:
        model = ServiceNode
        fields = [
            'id', 'outlet', 'outlet_name', 'name', 'node_type',
            'pos_x', 'pos_y', 'pos_z', 'capacity',
            'current_status', 'status_display', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceNodeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for 3D rendering - for floor visualization."""
    position = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceNode
        fields = ['id', 'name', 'node_type', 'current_status', 'capacity', 'position', 'color']
    
    def get_position(self, obj):
        return {'x': obj.pos_x, 'y': obj.pos_y, 'z': obj.pos_z}
    
    def get_color(self, obj):
        """Return hex color code for 3D rendering based on status."""
        color_map = {
            'BLUE': '#3B82F6',    # Ready/Empty - Blue
            'RED': '#EF4444',     # Waiting - Red
            'GREEN': '#22C55E',   # Served - Green
            'YELLOW': '#F59E0B',  # Issue - Yellow
            'GREY': '#6B7280',    # Maintenance - Grey
        }
        return color_map.get(obj.current_status, '#6B7280')


class ServiceNodeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for node details panel."""
    outlet_name = serializers.CharField(source='outlet.name', read_only=True)
    active_order = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceNode
        fields = [
            'id', 'name', 'outlet', 'outlet_name', 'node_type',
            'pos_x', 'pos_y', 'pos_z', 'capacity',
            'current_status', 'is_active', 'active_order'
        ]
    
    def get_active_order(self, obj):
        """Get current active order for this table."""
        if obj.node_type != 'TABLE':
            return None
        active = obj.orders.exclude(
            status__in=['COMPLETED', 'CANCELLED']
        ).order_by('-placed_at').first()
        if active:
            return {
                'id': active.id,
                'status': active.status,
                'party_size': active.party_size,
                'placed_at': active.placed_at,
                'total': str(active.total)
            }
        return None


class ServiceFlowSerializer(serializers.ModelSerializer):
    """Serializer for ServiceFlow model (paths between nodes)."""
    source_node_name = serializers.CharField(source='source_node.name', read_only=True)
    target_node_name = serializers.CharField(source='target_node.name', read_only=True)
    
    class Meta:
        model = ServiceFlow
        fields = [
            'id', 'source_node', 'source_node_name',
            'target_node', 'target_node_name',
            'flow_type', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        if data['source_node'] == data['target_node']:
            raise serializers.ValidationError("Source and target nodes cannot be the same.")
        return data
