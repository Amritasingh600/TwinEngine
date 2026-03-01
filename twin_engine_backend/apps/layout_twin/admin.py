from django.contrib import admin
from django.utils.html import format_html
from .models import ServiceNode, ServiceFlow


class ServiceFlowInline(admin.TabularInline):
    """Inline display of service flows from a node."""
    model = ServiceFlow
    fk_name = 'source_node'
    extra = 0
    fields = ['target_node', 'flow_type', 'is_active']
    show_change_link = True


@admin.register(ServiceNode)
class ServiceNodeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'outlet', 'node_type', 'current_status', 'status_badge', 
        'capacity', 'active_orders', 'is_active', 'updated_at'
    ]
    list_filter = ['current_status', 'node_type', 'outlet', 'is_active', 'updated_at']
    search_fields = ['name', 'outlet__name']
    raw_id_fields = ['outlet']
    list_editable = ['current_status']
    inlines = [ServiceFlowInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'outlet', 'node_type', 'capacity', 'is_active')
        }),
        ('Current Status', {
            'fields': ('current_status',),
            'description': 'Color status automatically updated based on order lifecycle'
        }),
        ('3D Position', {
            'fields': ('pos_x', 'pos_y', 'pos_z'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Color-coded status badge matching floor visualization."""
        colors = {
            'BLUE': '#3498db',        # Free/Available
            'GREEN': '#2ecc71',       # Eating (served)
            'YELLOW': '#f1c40f',      # Order placed/preparing
            'RED': '#e74c3c',         # Long wait (>15 min)
        }
        color = colors.get(obj.current_status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.current_status
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'current_status'
    
    def active_orders(self, obj):
        """Display count of active orders for this table."""
        if obj.node_type == 'TABLE':
            count = obj.orders.exclude(status__in=['COMPLETED', 'CANCELLED']).count()
            if count > 0:
                return format_html('<strong>{}</strong>', count)
            return '-'
        return '-'
    active_orders.short_description = 'Active Orders'


@admin.register(ServiceFlow)
class ServiceFlowAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'source_node', 'target_node', 'outlet_name', 
        'flow_type', 'is_active', 'created_at'
    ]
    list_filter = ['flow_type', 'is_active', 'created_at', 'source_node__outlet']
    search_fields = [
        'source_node__name', 'target_node__name', 
        'source_node__outlet__name'
    ]
    raw_id_fields = ['source_node', 'target_node']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Flow Information', {
            'fields': ('source_node', 'target_node', 'flow_type', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def outlet_name(self, obj):
        """Display outlet name for context."""
        return obj.source_node.outlet.name if obj.source_node else '-'
    outlet_name.short_description = 'Outlet'
    outlet_name.admin_order_field = 'source_node__outlet'
