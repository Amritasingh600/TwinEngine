from django.contrib import admin
from .models import Brand, Outlet, UserProfile


class OutletInline(admin.TabularInline):
    """Inline display of outlets under a brand."""
    model = Outlet
    extra = 0
    fields = ['name', 'city', 'seating_capacity', 'is_active']
    show_change_link = True


class UserProfileInline(admin.TabularInline):
    """Inline display of staff under an outlet."""
    model = UserProfile
    extra = 0
    fields = ['user', 'role', 'phone', 'is_on_shift']
    raw_id_fields = ['user']
    show_change_link = True


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'corporate_id', 'subscription_tier', 'outlet_count', 'created_at']
    list_filter = ['subscription_tier', 'created_at']
    search_fields = ['name', 'corporate_id', 'contact_email']
    ordering = ['name']
    inlines = [OutletInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Brand Information', {
            'fields': ('name', 'logo_url', 'corporate_id', 'contact_email')
        }),
        ('Subscription', {
            'fields': ('subscription_tier',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def outlet_count(self, obj):
        """Display count of outlets under this brand."""
        count = obj.outlets.count()
        return f"{count} outlet{'s' if count != 1 else ''}"
    outlet_count.short_description = 'Outlets'


@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'city', 'seating_capacity', 'staff_count', 'is_active', 'created_at']
    list_filter = ['brand', 'city', 'is_active', 'created_at']
    search_fields = ['name', 'brand__name', 'city', 'address']
    raw_id_fields = ['brand']
    inlines = [UserProfileInline]
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Outlet Information', {
            'fields': ('brand', 'name', 'address', 'city')
        }),
        ('Capacity & Hours', {
            'fields': ('seating_capacity', 'opening_time', 'closing_time')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def staff_count(self, obj):
        """Display count of staff members at this outlet."""
        count = obj.staff.count()
        active = obj.staff.filter(is_on_shift=True).count()
        return f"{count} total ({active} on shift)"
    staff_count.short_description = 'Staff'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'outlet', 'role', 'phone', 'is_on_shift', 'created_at']
    list_filter = ['role', 'outlet__brand', 'outlet', 'is_on_shift', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'outlet__name', 'phone']
    raw_id_fields = ['user', 'outlet']
    list_editable = ['is_on_shift']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'outlet', 'role', 'phone')
        }),
        ('Status', {
            'fields': ('is_on_shift',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
