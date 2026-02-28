from django.contrib import admin
from .models import SalesData, InventoryItem, StaffSchedule


@admin.register(SalesData)
class SalesDataAdmin(admin.ModelAdmin):
    list_display = ['outlet', 'date', 'hour', 'total_orders', 'total_revenue', 'avg_wait_time_minutes']
    list_filter = ['outlet', 'date', 'day_of_week', 'is_holiday']
    search_fields = ['outlet__name']
    raw_id_fields = ['outlet']
    date_hierarchy = 'date'
    ordering = ['-date', 'hour']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'outlet', 'category', 'current_quantity', 'unit', 'is_low_stock_display', 'updated_at']
    list_filter = ['category', 'outlet']
    search_fields = ['name', 'outlet__name']
    raw_id_fields = ['outlet']
    ordering = ['outlet', 'category', 'name']
    
    def is_low_stock_display(self, obj):
        return obj.is_low_stock
    is_low_stock_display.short_description = 'Low Stock'
    is_low_stock_display.boolean = True


@admin.register(StaffSchedule)
class StaffScheduleAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'shift', 'start_time', 'end_time', 'is_confirmed', 'is_ai_suggested']
    list_filter = ['shift', 'is_confirmed', 'is_ai_suggested', 'date']
    search_fields = ['staff__user__username', 'staff__user__first_name']
    raw_id_fields = ['staff']
    date_hierarchy = 'date'
    ordering = ['-date', 'start_time']
