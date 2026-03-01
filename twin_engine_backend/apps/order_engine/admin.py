from django.contrib import admin
from django.utils.html import format_html
from .models import OrderTicket, PaymentLog


class PaymentInline(admin.TabularInline):
    """Inline display of payments for an order."""
    model = PaymentLog
    extra = 0
    fields = ['amount', 'method', 'status', 'tip_amount', 'transaction_id', 'created_at']
    readonly_fields = ['created_at']
    show_change_link = True


@admin.register(OrderTicket)
class OrderTicketAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'table', 'outlet_name', 'waiter', 'status', 'status_badge', 
        'party_size', 'total', 'wait_time_display', 'placed_at'
    ]
    list_filter = ['status', 'table__outlet', 'waiter', 'placed_at']
    search_fields = ['id', 'table__name', 'customer_name', 'waiter__user__username']
    raw_id_fields = ['table', 'waiter']
    date_hierarchy = 'placed_at'
    ordering = ['-placed_at']
    list_editable = ['status']
    inlines = [PaymentInline]
    readonly_fields = ['placed_at', 'served_at', 'completed_at', 'wait_time_display', 'is_long_wait']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('table', 'waiter', 'customer_name', 'party_size')
        }),
        ('Order Details', {
            'fields': ('items', 'special_requests', 'status')
        }),
        ('Financials', {
            'fields': ('subtotal', 'tax', 'total')
        }),
        ('Timing & Performance', {
            'fields': ('placed_at', 'served_at', 'completed_at', 'wait_time_display', 'is_long_wait'),
            'classes': ('collapse',)
        }),
    )
    
    def outlet_name(self, obj):
        """Display outlet name for better context."""
        return obj.table.outlet.name if obj.table else '-'
    outlet_name.short_description = 'Outlet'
    outlet_name.admin_order_field = 'table__outlet'
    
    def status_badge(self, obj):
        """Color-coded status badge for visual clarity."""
        colors = {
            'PLACED': '#e74c3c',      # Red
            'PREPARING': '#f39c12',   # Orange
            'READY': '#f1c40f',       # Yellow
            'SERVED': '#2ecc71',      # Green
            'COMPLETED': '#3498db',   # Blue
            'CANCELLED': '#95a5a6',   # Gray
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def wait_time_display(self, obj):
        """Display wait time with warning for long waits."""
        minutes = obj.wait_time_minutes
        if obj.is_long_wait:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ {} min</span>',
                minutes
            )
        return f"{minutes} min"
    wait_time_display.short_description = 'Wait Time'


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'order', 'outlet_name', 'amount', 'method_badge', 
        'status_badge', 'tip_amount', 'created_at'
    ]
    list_filter = ['status', 'method', 'created_at', 'order__table__outlet']
    search_fields = ['order__id', 'order__table__name', 'transaction_id', 'order__customer_name']
    raw_id_fields = ['order']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'amount', 'tip_amount', 'method', 'status')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'created_at')
        }),
    )
    
    def outlet_name(self, obj):
        """Display outlet name for context."""
        return obj.order.table.outlet.name if obj.order and obj.order.table else '-'
    outlet_name.short_description = 'Outlet'
    
    def method_badge(self, obj):
        """Color-coded payment method badge."""
        colors = {
            'CASH': '#95a5a6',        # Gray
            'CARD': '#3498db',        # Blue
            'UPI': '#9b59b6',         # Purple
            'WALLET': '#e67e22',      # Orange
            'SPLIT': '#1abc9c',       # Teal
        }
        color = colors.get(obj.method, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_method_display()
        )
    method_badge.short_description = 'Method'
    method_badge.admin_order_field = 'method'
    
    def status_badge(self, obj):
        """Color-coded payment status badge."""
        colors = {
            'PENDING': '#f39c12',     # Orange
            'COMPLETED': '#2ecc71',   # Green
            'FAILED': '#e74c3c',      # Red
            'REFUNDED': '#95a5a6',    # Gray
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
