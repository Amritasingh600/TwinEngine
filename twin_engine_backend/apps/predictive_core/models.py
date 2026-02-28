from django.db import models
from apps.hospitality_group.models import Outlet, UserProfile


class SalesData(models.Model):
    """
    Aggregated sales data for AI predictions and demand forecasting.
    Used by predictive models to optimize staffing, inventory, and prep.
    
    Replaces: VisionLog (from manufacturing version)
    """
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='sales_data')
    date = models.DateField()
    hour = models.IntegerField(help_text="Hour of day (0-23) for hourly patterns")
    
    # Aggregated metrics
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    avg_ticket_size = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    avg_wait_time_minutes = models.FloatField(default=0.0, help_text="Average wait time for food")
    
    # Category breakdowns (JSON for flexibility)
    category_sales = models.JSONField(default=dict, help_text="Sales by category {category: amount}")
    top_items = models.JSONField(default=list, help_text="Top selling items for this period")
    
    # External factors for predictions
    day_of_week = models.IntegerField(help_text="0=Monday, 6=Sunday")
    is_holiday = models.BooleanField(default=False)
    weather_condition = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', 'hour']
        verbose_name = 'Sales Data'
        verbose_name_plural = 'Sales Data'
        unique_together = ['outlet', 'date', 'hour']
        indexes = [
            models.Index(fields=['outlet', '-date']),
            models.Index(fields=['day_of_week']),
        ]
    
    def __str__(self):
        return f"{self.outlet.name} - {self.date} {self.hour}:00 - ₹{self.total_revenue}"


class InventoryItem(models.Model):
    """
    Tracks ingredient/supply inventory with predictive reorder alerts.
    
    Replaces: DetectionZone (from manufacturing version)
    """
    CATEGORY_CHOICES = [
        ('PRODUCE', 'Fresh Produce'),
        ('DAIRY', 'Dairy Products'),
        ('MEAT', 'Meat & Poultry'),
        ('DRY', 'Dry Goods'),
        ('BEVERAGE', 'Beverages'),
        ('SUPPLIES', 'Kitchen Supplies'),
    ]
    
    UNIT_CHOICES = [
        ('KG', 'Kilograms'),
        ('L', 'Liters'),
        ('PCS', 'Pieces'),
        ('BAGS', 'Bags'),
        ('BOXES', 'Boxes'),
    ]
    
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='inventory_items')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='DRY')
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='KG')
    
    # Stock levels
    current_quantity = models.FloatField(default=0.0)
    reorder_threshold = models.FloatField(default=10.0, help_text="Alert when below this level")
    par_level = models.FloatField(default=50.0, help_text="Ideal stock level")
    
    # Costs
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # For perishables
    expiry_date = models.DateField(blank=True, null=True)
    
    # Tracking
    last_restocked = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['outlet', 'category', 'name']
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'
        unique_together = ['outlet', 'name']
        indexes = [
            models.Index(fields=['outlet', 'category']),
        ]
    
    @property
    def is_low_stock(self):
        return self.current_quantity <= self.reorder_threshold
    
    def __str__(self):
        status = "⚠️ LOW" if self.is_low_stock else "✓"
        return f"{self.name} ({self.current_quantity} {self.unit}) {status}"


class StaffSchedule(models.Model):
    """
    Staff scheduling optimized by AI predictions.
    """
    SHIFT_CHOICES = [
        ('MORNING', 'Morning (6AM-2PM)'),
        ('AFTERNOON', 'Afternoon (2PM-10PM)'),
        ('NIGHT', 'Night (10PM-6AM)'),
        ('SPLIT', 'Split Shift'),
    ]
    
    staff = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='MORNING')
    
    # Actual times (can differ from shift template)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Status tracking
    is_confirmed = models.BooleanField(default=False)
    checked_in = models.DateTimeField(blank=True, null=True)
    checked_out = models.DateTimeField(blank=True, null=True)
    
    # AI optimization flag
    is_ai_suggested = models.BooleanField(default=False, help_text="Shift suggested by AI based on predictions")
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', 'start_time']
        verbose_name = 'Staff Schedule'
        verbose_name_plural = 'Staff Schedules'
        unique_together = ['staff', 'date', 'shift']
        indexes = [
            models.Index(fields=['staff', '-date']),
            models.Index(fields=['date', 'shift']),
        ]
    
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.date} ({self.shift})"
