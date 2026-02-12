from django.contrib import admin
from .models import Manufacturer, UserProfile


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['name', 'corporate_id', 'contact_email', 'subscription_tier', 'created_at']
    list_filter = ['subscription_tier', 'created_at']
    search_fields = ['name', 'corporate_id', 'contact_email']
    ordering = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'manufacturer', 'role', 'created_at']
    list_filter = ['role', 'manufacturer']
    search_fields = ['user__username', 'user__email', 'manufacturer__name']
    raw_id_fields = ['user', 'manufacturer']
