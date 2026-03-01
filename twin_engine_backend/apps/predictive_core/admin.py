from django.contrib import admin
from django.utils.html import format_html
from .models import SalesData, InventoryItem, StaffSchedule


@admin.register(SalesData)
class SalesDataAdmin(admin.ModelAdmin):
    list_display = [
        'outlet', 'date', 'day_of_week', 'hour', 
        'total_orders', 'revenue_display', 'avg_wait_time_minutes', 
        'is_holiday'
    ]
    list_filter = ['outlet', 'date', 'day_of_week', 'is_holiday']
    search_fields = ['outlet__name']
    raw_id_fields = ['outlet']
    date_hierarchy = 'date'
    ordering = ['-date', 'hour']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Time & Location', {
            'fields': ('outlet', 'date', 'hour', 'day_of_week', 'is_holiday')
        }),
        ('Sales Metrics', {
            'fields': ('total_orders', 'total_revenue', 'avg_wait_time_minutes')
        }),
        ('Demand Metrics', {
            'fields': ('total_covers', 'avg_party_size', 'peak_hour_indicator'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def revenue_display(self, obj):
        """Format revenue with currency symbol."""
        return format_html('<strong>₹{:,.2f}</strong>', obj.total_revenue)
    revenue_display.short_description = 'Revenue'
    revenue_display.admin_order_field = 'total_revenue'


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'outlet', 'category', 'quantity_display', 
        'unit', 'is_low_stock_display', 'updated_at'
    ]
    list_filter = ['category', 'outlet', 'updated_at']
    search_fields = ['name', 'outlet__name']
    raw_id_fields = ['outlet']
    ordering = ['outlet', 'category', 'name']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('Item Information', {
            'fields': ('name', 'outlet', 'category')
        }),
        ('Quantity Management', {
            'fields': ('current_quantity', 'min_quantity', 'max_quantity', 'unit')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def quantity_display(self, obj):
        """Display quantity with color coding for low stock."""
        if obj.is_low_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ {}</span>',
                obj.current_quantity
            )
        return obj.current_quantity
    quantity_display.short_description = 'Quantity'
    quantity_display.admin_order_field = 'current_quantity'
    
    def is_low_stock_display(self, obj):
        """Boolean indicator for low stock."""
        return obj.is_low_stock
    is_low_stock_display.short_description = 'Low Stock'
    is_low_stock_display.boolean = True


@admin.register(StaffSchedule)
class StaffScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'staff', 'outlet_name', 'date', 'shift_badge', 
        'time_range', 'is_confirmed', 'is_ai_suggested', 'created_at'
    ]
    list_filter = ['shift', 'is_confirmed', 'is_ai_suggested', 'date', 'staff__outlet']
    search_fields = [
        'staff__user__username', 'staff__user__first_name', 
        'staff__user__last_name', 'staff__outlet__name'
    ]
    raw_id_fields = ['staff']
    date_hierarchy = 'date'
    ordering = ['-date', 'start_time']
    list_editable = ['is_confirmed']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('staff', 'date', 'shift', 'start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('is_confirmed', 'is_ai_suggested')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def outlet_name(self, obj):
        """Display outlet name for context."""
        return obj.staff.outlet.name if obj.staff else '-'
    outlet_name.short_description = 'Outlet'
    outlet_name.admin_order_field = 'staff__outlet'
    
    def shift_badge(self, obj):
        """Color-coded shift badge."""
        colors = {
            'MORNING': '#f39c12',     # Orange
            'AFTERNOON': '#3498db',   # Blue
            'EVENING': '#9b59b6',     # Purple
            'NIGHT': '#34495e',       # Dark Gray
        }
        color = colors.get(obj.shift, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_shift_display()
        )
    shift_badge.short_description = 'Shift'
    shift_badge.admin_order_field = 'shift'
    
    def time_range(self, obj):
        """Display shift time range."""
        return f"{obj.start_time.strftime('%I:%M %p')} - {obj.end_time.strftime('%I:%M %p')}"
    time_range.short_description = 'Time Range'
