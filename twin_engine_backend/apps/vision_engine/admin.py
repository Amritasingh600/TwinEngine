from django.contrib import admin
from .models import VisionLog, DetectionZone


@admin.register(VisionLog)
class VisionLogAdmin(admin.ModelAdmin):
    list_display = ['machine_node', 'object_type', 'timestamp', 'confidence_score', 'current_total']
    list_filter = ['object_type', 'timestamp', 'machine_node']
    search_fields = ['machine_node__name', 'object_type']
    raw_id_fields = ['machine_node']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(DetectionZone)
class DetectionZoneAdmin(admin.ModelAdmin):
    list_display = ['machine_node', 'line_y_coordinate', 'active_status', 'loop_count', 'updated_at']
    list_filter = ['active_status', 'machine_node']
    search_fields = ['machine_node__name']
    raw_id_fields = ['machine_node']
