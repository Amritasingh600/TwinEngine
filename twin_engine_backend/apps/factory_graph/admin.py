from django.contrib import admin
from .models import MachineType, MachineNode, MachineEdge


@admin.register(MachineType)
class MachineTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(MachineNode)
class MachineNodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'manufacturer', 'machine_type', 'status', 'pos_x', 'pos_y', 'pos_z', 'updated_at']
    list_filter = ['status', 'manufacturer', 'machine_type']
    search_fields = ['name', 'manufacturer__name']
    raw_id_fields = ['manufacturer', 'machine_type']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'manufacturer', 'machine_type', 'status')
        }),
        ('3D Position', {
            'fields': ('pos_x', 'pos_y', 'pos_z')
        }),
        ('AI & Video', {
            'fields': ('video_feed_url', 'hf_endpoint', 'hf_key')
        }),
    )


@admin.register(MachineEdge)
class MachineEdgeAdmin(admin.ModelAdmin):
    list_display = ['source_node', 'target_node', 'flow_type', 'created_at']
    list_filter = ['flow_type']
    search_fields = ['source_node__name', 'target_node__name']
    raw_id_fields = ['source_node', 'target_node']
