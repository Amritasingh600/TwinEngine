from rest_framework import serializers
from .models import SensorData, AnomalyAlert


class SensorDataSerializer(serializers.ModelSerializer):
    """Serializer for SensorData model."""
    machine_node_name = serializers.CharField(source='machine_node.name', read_only=True)
    
    class Meta:
        model = SensorData
        fields = [
            'id', 'machine_node', 'machine_node_name',
            'temperature', 'vibration', 'torque', 'rpm', 'tool_wear',
            'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class SensorDataCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sensor data (from IoT/Mock devices)."""
    
    class Meta:
        model = SensorData
        fields = [
            'machine_node', 'temperature', 'vibration', 
            'torque', 'rpm', 'tool_wear'
        ]


class SensorDataBulkSerializer(serializers.Serializer):
    """Serializer for bulk sensor data ingestion."""
    readings = SensorDataCreateSerializer(many=True)
    
    def create(self, validated_data):
        readings_data = validated_data['readings']
        sensor_objects = [SensorData(**data) for data in readings_data]
        return SensorData.objects.bulk_create(sensor_objects)


class AnomalyAlertSerializer(serializers.ModelSerializer):
    """Serializer for AnomalyAlert model."""
    machine_node_name = serializers.SerializerMethodField()
    sensor_reading = serializers.SerializerMethodField()
    
    class Meta:
        model = AnomalyAlert
        fields = [
            'id', 'sensor_data', 'machine_node_name', 'sensor_reading',
            'ai_prediction', 'severity', 'resolved_status',
            'created_at', 'resolved_at', 'notes'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_machine_node_name(self, obj):
        return obj.sensor_data.machine_node.name
    
    def get_sensor_reading(self, obj):
        return {
            'temperature': obj.sensor_data.temperature,
            'vibration': obj.sensor_data.vibration,
            'torque': obj.sensor_data.torque,
            'rpm': obj.sensor_data.rpm
        }


class AnomalyAlertCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating anomaly alerts (from ML pipeline)."""
    
    class Meta:
        model = AnomalyAlert
        fields = ['sensor_data', 'ai_prediction', 'severity']


class AnomalyResolveSerializer(serializers.Serializer):
    """Serializer for resolving an anomaly alert."""
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        from django.utils import timezone
        instance.resolved_status = True
        instance.resolved_at = timezone.now()
        instance.notes = validated_data.get('notes', '')
        instance.save()
        return instance


class AnomalyTriggerSerializer(serializers.Serializer):
    """Serializer for /api/anomaly/trigger/ endpoint (per API spec)."""
    node_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['NORMAL', 'WARNING', 'ERROR', 'OFFLINE'])
    
    def validate_node_id(self, value):
        from apps.factory_graph.models import MachineNode
        if not MachineNode.objects.filter(id=value).exists():
            raise serializers.ValidationError("Machine node does not exist.")
        return value
