from django.contrib import admin
from .models import SensorData, AnomalyAlert


@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ['machine_node', 'temperature', 'vibration', 'torque', 'rpm', 'tool_wear', 'timestamp']
    list_filter = ['timestamp', 'machine_node']
    search_fields = ['machine_node__name']
    raw_id_fields = ['machine_node']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(AnomalyAlert)
class AnomalyAlertAdmin(admin.ModelAdmin):
    list_display = ['get_machine_name', 'ai_prediction', 'severity', 'resolved_status', 'created_at']
    list_filter = ['severity', 'resolved_status', 'ai_prediction', 'created_at']
    search_fields = ['sensor_data__machine_node__name', 'ai_prediction', 'notes']
    raw_id_fields = ['sensor_data']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def get_machine_name(self, obj):
        return obj.sensor_data.machine_node.name
    get_machine_name.short_description = 'Machine'
