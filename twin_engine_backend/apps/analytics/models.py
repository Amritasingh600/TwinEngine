from django.db import models
from apps.manufacturers.models import Manufacturer


class ShiftLog(models.Model):
    """
    Aggregated data for a specific working hour window.
    """
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='shift_logs')
    date = models.DateField(help_text="Date of the shift")
    shift_start = models.TimeField(help_text="Shift start time")
    shift_end = models.TimeField(help_text="Shift end time")
    total_units = models.IntegerField(default=0, help_text="Total units produced during shift")
    total_downtime = models.FloatField(default=0.0, help_text="Total downtime in minutes")
    anomaly_count = models.IntegerField(default=0, help_text="Number of anomalies detected")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-shift_start']
        verbose_name = 'Shift Log'
        verbose_name_plural = 'Shift Logs'
        unique_together = ['manufacturer', 'date', 'shift_start']
    
    def __str__(self):
        return f"{self.manufacturer.name} - {self.date} ({self.shift_start} - {self.shift_end})"


class ProductionReport(models.Model):
    """
    Stores links to the finalized GPT-4o PDFs on Cloudinary.
    """
    GENERATION_TYPE_CHOICES = [
        ('AUTO', 'Automatic'),
        ('MANUAL', 'Manual'),
    ]
    
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='production_reports')
    date = models.DateField(help_text="Report date")
    cloudinary_url = models.URLField(help_text="URL to the report PDF on Cloudinary")
    gpt_summary = models.TextField(help_text="GPT-4o generated summary text")
    generation_type = models.CharField(max_length=10, choices=GENERATION_TYPE_CHOICES, default='AUTO')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Production Report'
        verbose_name_plural = 'Production Reports'
        unique_together = ['manufacturer', 'date', 'generation_type']
    
    def __str__(self):
        return f"{self.manufacturer.name} - Report {self.date} ({self.generation_type})"
