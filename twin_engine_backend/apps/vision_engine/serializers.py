from rest_framework import serializers
from .models import VisionLog, DetectionZone


class VisionLogSerializer(serializers.ModelSerializer):
    """Serializer for VisionLog model."""
    machine_node_name = serializers.CharField(source='machine_node.name', read_only=True)
    
    class Meta:
        model = VisionLog
        fields = [
            'id', 'machine_node', 'machine_node_name',
            'object_type', 'confidence_score', 'current_total',
            'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class VisionLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vision logs (from AI inference)."""
    
    class Meta:
        model = VisionLog
        fields = ['machine_node', 'object_type', 'confidence_score', 'current_total']
    
    def validate_confidence_score(self, value):
        if not 0.0 <= value <= 1.0:
            raise serializers.ValidationError("Confidence score must be between 0.0 and 1.0")
        return value


class VisionLogBulkSerializer(serializers.Serializer):
    """Serializer for batch vision log creation."""
    detections = VisionLogCreateSerializer(many=True)
    
    def create(self, validated_data):
        detections_data = validated_data['detections']
        log_objects = [VisionLog(**data) for data in detections_data]
        return VisionLog.objects.bulk_create(log_objects)


class DetectionZoneSerializer(serializers.ModelSerializer):
    """Serializer for DetectionZone model."""
    machine_node_name = serializers.CharField(source='machine_node.name', read_only=True)
    
    class Meta:
        model = DetectionZone
        fields = [
            'id', 'machine_node', 'machine_node_name',
            'line_y_coordinate', 'active_status', 'loop_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DetectionZoneUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating detection zone count."""
    
    class Meta:
        model = DetectionZone
        fields = ['loop_count', 'active_status']


class VisionCountSummarySerializer(serializers.Serializer):
    """Serializer for vision count summary response."""
    machine_node_id = serializers.IntegerField()
    machine_node_name = serializers.CharField()
    object_type = serializers.CharField()
    total_count = serializers.IntegerField()
    last_detection = serializers.DateTimeField()
