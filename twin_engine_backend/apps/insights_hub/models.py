from django.db import models
from apps.hospitality_group.models import Outlet


class DailySummary(models.Model):
    """
    End-of-day aggregated metrics for each outlet.
    Feeds into dashboards and GPT-generated reports.
    
    Replaces: ShiftLog (from manufacturing version)
    """
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='daily_summaries')
    date = models.DateField()
    
    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_orders = models.IntegerField(default=0)
    avg_ticket_size = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_tips = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Operational metrics
    total_guests = models.IntegerField(default=0)
    avg_table_turnover_time = models.FloatField(default=0.0, help_text="Average minutes per table session")
    avg_wait_time = models.FloatField(default=0.0, help_text="Average wait time in minutes")
    
    # Performance metrics
    peak_hour = models.IntegerField(default=12, help_text="Hour with most orders (0-23)")
    peak_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Issues tracking
    delayed_orders = models.IntegerField(default=0, help_text="Orders with wait > 15min")
    cancelled_orders = models.IntegerField(default=0)
    
    # Category breakdown (JSON)
    sales_by_category = models.JSONField(default=dict, help_text="Revenue by category")
    top_selling_items = models.JSONField(default=list, help_text="Top 10 items sold")
    
    # Staff metrics
    staff_count = models.IntegerField(default=0)
    revenue_per_staff = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Daily Summary'
        verbose_name_plural = 'Daily Summaries'
        unique_together = ['outlet', 'date']
        indexes = [
            models.Index(fields=['outlet', '-date']),
        ]
    
    def __str__(self):
        return f"{self.outlet.name} - {self.date} (₹{self.total_revenue})"


class PDFReport(models.Model):
    """
    AI-generated PDF reports with insights and recommendations.
    Uses GPT-4 to analyze daily summaries and generate actionable insights.
    
    Replaces: ProductionReport (from manufacturing version)
    """
    REPORT_TYPE_CHOICES = [
        ('DAILY', 'Daily Operations Report'),
        ('WEEKLY', 'Weekly Summary'),
        ('MONTHLY', 'Monthly Analysis'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    GENERATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('GENERATING', 'Generating'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='pdf_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='DAILY')
    
    # Date range for the report
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Generated content
    cloudinary_url = models.URLField(blank=True, null=True, help_text="URL to the PDF on Cloudinary")
    gpt_summary = models.TextField(blank=True, null=True, help_text="AI-generated executive summary")
    insights = models.JSONField(default=list, help_text="List of AI-generated insights")
    recommendations = models.JSONField(default=list, help_text="Actionable recommendations")
    
    # Status
    status = models.CharField(max_length=20, choices=GENERATION_STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    
    # Metadata
    generated_by = models.CharField(max_length=50, default='GPT-4', help_text="AI model used")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'PDF Report'
        verbose_name_plural = 'PDF Reports'
        indexes = [
            models.Index(fields=['outlet', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.outlet.name} - {self.report_type} ({self.start_date} to {self.end_date})"
