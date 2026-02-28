from django.contrib import admin
from .models import DailySummary, PDFReport


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ['outlet', 'date', 'total_revenue', 'total_orders', 'total_guests', 'avg_wait_time', 'delayed_orders']
    list_filter = ['date', 'outlet']
    search_fields = ['outlet__name']
    raw_id_fields = ['outlet']
    date_hierarchy = 'date'
    ordering = ['-date']


@admin.register(PDFReport)
class PDFReportAdmin(admin.ModelAdmin):
    list_display = ['outlet', 'report_type', 'start_date', 'end_date', 'status', 'created_at']
    list_filter = ['report_type', 'status', 'outlet']
    search_fields = ['outlet__name', 'gpt_summary']
    raw_id_fields = ['outlet']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Report Info', {
            'fields': ('outlet', 'report_type', 'start_date', 'end_date', 'status')
        }),
        ('Generated Content', {
            'fields': ('gpt_summary', 'insights', 'recommendations', 'cloudinary_url')
        }),
        ('Metadata', {
            'fields': ('generated_by', 'error_message')
        }),
    )
