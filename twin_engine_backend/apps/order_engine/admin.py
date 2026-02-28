from django.contrib import admin
from .models import OrderTicket, PaymentLog


@admin.register(OrderTicket)
class OrderTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'waiter', 'status', 'party_size', 'total', 'placed_at']
    list_filter = ['status', 'table__outlet', 'waiter', 'placed_at']
    search_fields = ['table__name', 'customer_name', 'waiter__user__username']
    raw_id_fields = ['table', 'waiter']
    date_hierarchy = 'placed_at'
    ordering = ['-placed_at']
    list_editable = ['status']


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'method', 'status', 'tip_amount', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['order__table__name', 'transaction_id']
    raw_id_fields = ['order']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
