from django.db import models
from django.contrib.auth.models import User


class Brand(models.Model):
    """
    Parent organization for restaurant chains.
    E.g., "Starbucks India", "McDonald's Corp"
    Replaces: Manufacturer (from manufacturing version)
    """
    SUBSCRIPTION_TIERS = [
        ('BASIC', 'Basic'),
        ('PRO', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=255, help_text="Brand/Chain Name")
    logo_url = models.URLField(blank=True, null=True, help_text="Brand logo on Cloudinary")
    corporate_id = models.CharField(max_length=100, unique=True, help_text="Unique Corporate Identifier")
    contact_email = models.EmailField(help_text="Primary Contact Email")
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIERS, default='BASIC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
    
    def __str__(self):
        return f"{self.name} ({self.corporate_id})"


class Outlet(models.Model):
    """
    Specific restaurant location under a Brand.
    E.g., "Connaught Place Cafe", "Mall of India Branch"
    """
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='outlets')
    name = models.CharField(max_length=255, help_text="Outlet Name/Location")
    address = models.TextField(help_text="Full Address")
    city = models.CharField(max_length=100)
    seating_capacity = models.IntegerField(default=0, help_text="Total seating capacity")
    opening_time = models.TimeField(help_text="Daily opening time")
    closing_time = models.TimeField(help_text="Daily closing time")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['brand', 'name']
        verbose_name = 'Outlet'
        verbose_name_plural = 'Outlets'
        unique_together = ['brand', 'name']
    
    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class UserProfile(models.Model):
    """
    Links staff (managers, waiters, chefs) to specific Outlets with role-based access.
    """
    ROLE_CHOICES = [
        ('MANAGER', 'Manager'),
        ('WAITER', 'Waiter'),
        ('CHEF', 'Chef'),
        ('HOST', 'Host/Hostess'),
        ('CASHIER', 'Cashier'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='staff')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='WAITER')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_on_shift = models.BooleanField(default=False, help_text="Currently working")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['outlet', 'user__username']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} ({self.role}) - {self.outlet.name}"
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.manufacturer.name} ({self.role})"
