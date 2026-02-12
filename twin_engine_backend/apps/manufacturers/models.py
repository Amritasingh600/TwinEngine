from django.db import models
from django.contrib.auth.models import User


class Manufacturer(models.Model):
    """
    Stores corporate data for registered factory owners.
    Manages the multi-tenant SaaS layer.
    """
    SUBSCRIPTION_TIERS = [
        ('BASIC', 'Basic'),
        ('PRO', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=255, help_text="Company/Factory Name")
    corporate_id = models.CharField(max_length=100, unique=True, help_text="Unique Corporate Identifier")
    contact_email = models.EmailField(help_text="Primary Contact Email")
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIERS, default='BASIC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Manufacturer'
        verbose_name_plural = 'Manufacturers'
    
    def __str__(self):
        return f"{self.name} ({self.corporate_id})"


class UserProfile(models.Model):
    """
    Extends the default User to link staff to a specific Manufacturer.
    """
    ROLE_CHOICES = [
        ('MANAGER', 'Manager'),
        ('OPERATOR', 'Operator'),
        ('ENGINEER', 'Maintenance Engineer'),
        ('SUPERVISOR', 'Plant Supervisor'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OPERATOR')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['user__username']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.manufacturer.name} ({self.role})"
