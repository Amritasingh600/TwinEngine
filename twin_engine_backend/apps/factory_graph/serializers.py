from rest_framework import serializers
from .models import MachineType, MachineNode, MachineEdge


class MachineTypeSerializer(serializers.ModelSerializer):
    """Serializer for MachineType model."""
    instance_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MachineType
        fields = [
            'id', 'name', 'model_3d_embed_code', 'description', 
            'instance_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_instance_count(self, obj):
        return obj.instances.count()


class MachineTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing machine types."""
    
    class Meta:
        model = MachineType
        fields = ['id', 'name', 'description']


class MachineNodeSerializer(serializers.ModelSerializer):
    """Serializer for MachineNode model."""
    machine_type_name = serializers.CharField(source='machine_type.name', read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    
    class Meta:
        model = MachineNode
        fields = [
            'id', 'name', 'manufacturer', 'manufacturer_name',
            'machine_type', 'machine_type_name',
            'pos_x', 'pos_y', 'pos_z',
            'video_feed_url', 'hf_endpoint', 'hf_key',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'hf_key': {'write_only': True}  # Don't expose API keys in responses
        }


class MachineNodeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for 3D rendering - matches API spec."""
    machine_type_name = serializers.CharField(source='machine_type.name', read_only=True)
    position = serializers.SerializerMethodField()
    
    class Meta:
        model = MachineNode
        fields = ['id', 'name', 'machine_type_name', 'status', 'position']
    
    def get_position(self, obj):
        return {'x': obj.pos_x, 'y': obj.pos_y, 'z': obj.pos_z}


class MachineNodeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for node diagnostics panel."""
    machine_type = MachineTypeListSerializer(read_only=True)
    latest_sensor_data = serializers.SerializerMethodField()
    latest_vision_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MachineNode
        fields = [
            'id', 'name', 'machine_type', 'status',
            'video_feed_url', 'pos_x', 'pos_y', 'pos_z',
            'latest_sensor_data', 'latest_vision_count'
        ]
    
    def get_latest_sensor_data(self, obj):
        latest = obj.sensor_data.first()
        if latest:
            return {
                'temperature': latest.temperature,
                'vibration': latest.vibration,
                'torque': latest.torque,
                'rpm': latest.rpm,
                'tool_wear': latest.tool_wear,
                'timestamp': latest.timestamp
            }
        return None
    
    def get_latest_vision_count(self, obj):
        latest = obj.vision_logs.first()
        if latest:
            return {
                'object_type': latest.object_type,
                'current_total': latest.current_total,
                'timestamp': latest.timestamp
            }
        return None


class MachineEdgeSerializer(serializers.ModelSerializer):
    """Serializer for MachineEdge model."""
    source_node_name = serializers.CharField(source='source_node.name', read_only=True)
    target_node_name = serializers.CharField(source='target_node.name', read_only=True)
    
    class Meta:
        model = MachineEdge
        fields = [
            'id', 'source_node', 'source_node_name',
            'target_node', 'target_node_name',
            'flow_type', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        if data['source_node'] == data['target_node']:
            raise serializers.ValidationError("Source and target nodes cannot be the same.")
        return data
