from django.contrib import admin
from .models import Brand, Outlet, UserProfile


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'corporate_id', 'contact_email', 'subscription_tier', 'created_at']
    list_filter = ['subscription_tier', 'created_at']
    search_fields = ['name', 'corporate_id', 'contact_email']
    ordering = ['name']


@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'city', 'seating_capacity', 'is_active', 'created_at']
    list_filter = ['brand', 'city', 'is_active']
    search_fields = ['name', 'brand__name', 'city']
    raw_id_fields = ['brand']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'outlet', 'role', 'is_on_shift', 'created_at']
    list_filter = ['role', 'outlet__brand', 'outlet', 'is_on_shift']
    search_fields = ['user__username', 'user__email', 'outlet__name']
    raw_id_fields = ['user', 'outlet']
