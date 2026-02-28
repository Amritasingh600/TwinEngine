from django.contrib import admin
from .models import ServiceNode, ServiceFlow


@admin.register(ServiceNode)
class ServiceNodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'outlet', 'node_type', 'current_status', 'capacity', 'is_active', 'updated_at']
    list_filter = ['current_status', 'node_type', 'outlet', 'is_active']
    search_fields = ['name', 'outlet__name']
    raw_id_fields = ['outlet']
    list_editable = ['current_status']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'outlet', 'node_type', 'current_status', 'capacity', 'is_active')
        }),
        ('3D Position', {
            'fields': ('pos_x', 'pos_y', 'pos_z')
        }),
    )


@admin.register(ServiceFlow)
class ServiceFlowAdmin(admin.ModelAdmin):
    list_display = ['source_node', 'target_node', 'flow_type', 'is_active', 'created_at']
    list_filter = ['flow_type', 'is_active']
    search_fields = ['source_node__name', 'target_node__name']
    raw_id_fields = ['source_node', 'target_node']
