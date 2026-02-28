"""
Custom permissions for TwinEngine Hospitality.
Controls access based on user roles and outlet assignments.
"""
from rest_framework import permissions


class IsOutletUser(permissions.BasePermission):
    """
    Only allow users to access their own outlet's data.
    Users can only view/edit data from their assigned outlet.
    """
    message = "You can only access data from your assigned outlet."
    
    def has_object_permission(self, request, view, obj):
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return False
        
        # If object has an outlet, check if it matches user's outlet
        if hasattr(obj, 'outlet'):
            return obj.outlet == request.user.profile.outlet
        
        # If object IS an outlet, check if it matches user's outlet
        if obj.__class__.__name__ == 'Outlet':
            return obj == request.user.profile.outlet
        
        return True


class IsManagerOrReadOnly(permissions.BasePermission):
    """
    Managers can create/edit/delete.
    Staff and Viewers can only read.
    """
    message = "Only managers can perform this action."
    
    def has_permission(self, request, view):
        # Allow read operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Superusers can do everything
        if request.user.is_superuser:
            return True
        
        # Check if user has manager role
        if hasattr(request.user, 'profile'):
            return request.user.profile.role == 'MANAGER'
        
        return False


class IsManager(permissions.BasePermission):
    """
    Only managers can access this endpoint.
    """
    message = "Only managers can access this resource."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            return request.user.profile.role == 'MANAGER'
        
        return False


class IsStaffOrManager(permissions.BasePermission):
    """
    Staff and Managers can access.
    Viewers cannot.
    """
    message = "Only staff members and managers can access this resource."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['STAFF', 'MANAGER']
        
        return False
