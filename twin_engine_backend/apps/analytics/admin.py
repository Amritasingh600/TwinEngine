from django.contrib import admin
from .models import ShiftLog, ProductionReport


@admin.register(ShiftLog)
class ShiftLogAdmin(admin.ModelAdmin):
    list_display = ['manufacturer', 'date', 'shift_start', 'shift_end', 'total_units', 'total_downtime', 'anomaly_count']
    list_filter = ['date', 'manufacturer']
    search_fields = ['manufacturer__name']
    raw_id_fields = ['manufacturer']
    date_hierarchy = 'date'
    ordering = ['-date', '-shift_start']


@admin.register(ProductionReport)
class ProductionReportAdmin(admin.ModelAdmin):
    list_display = ['manufacturer', 'date', 'generation_type', 'created_at']
    list_filter = ['generation_type', 'date', 'manufacturer']
    search_fields = ['manufacturer__name', 'gpt_summary']
    raw_id_fields = ['manufacturer']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Report Info', {
            'fields': ('manufacturer', 'date', 'generation_type')
        }),
        ('Content', {
            'fields': ('gpt_summary', 'cloudinary_url')
        }),
    )
