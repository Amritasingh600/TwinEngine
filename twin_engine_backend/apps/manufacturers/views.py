from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Manufacturer, UserProfile
from .serializers import (
    ManufacturerSerializer, ManufacturerListSerializer,
    UserProfileSerializer, UserProfileCreateSerializer
)


class ManufacturerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Manufacturers.
    
    Endpoints:
    - GET /api/manufacturers/ - List all manufacturers
    - POST /api/manufacturers/ - Create a new manufacturer
    - GET /api/manufacturers/{id}/ - Retrieve manufacturer details
    - PUT/PATCH /api/manufacturers/{id}/ - Update manufacturer
    - DELETE /api/manufacturers/{id}/ - Delete manufacturer
    - GET /api/manufacturers/{id}/users/ - List users for manufacturer
    - GET /api/manufacturers/{id}/machines/ - List machines for manufacturer
    """
    queryset = Manufacturer.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subscription_tier']
    search_fields = ['name', 'corporate_id', 'contact_email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ManufacturerListSerializer
        return ManufacturerSerializer
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get all users associated with this manufacturer."""
        manufacturer = self.get_object()
        profiles = manufacturer.users.all()
        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def machines(self, request, pk=None):
        """Get all machines for this manufacturer."""
        from apps.factory_graph.serializers import MachineNodeListSerializer
        manufacturer = self.get_object()
        machines = manufacturer.machines.all()
        serializer = MachineNodeListSerializer(machines, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for this manufacturer."""
        manufacturer = self.get_object()
        return Response({
            'total_users': manufacturer.users.count(),
            'total_machines': manufacturer.machines.count(),
            'machines_by_status': {
                'normal': manufacturer.machines.filter(status='NORMAL').count(),
                'warning': manufacturer.machines.filter(status='WARNING').count(),
                'error': manufacturer.machines.filter(status='ERROR').count(),
                'offline': manufacturer.machines.filter(status='OFFLINE').count(),
            }
        })


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing User Profiles.
    
    Endpoints:
    - GET /api/users/ - List all user profiles
    - POST /api/users/ - Create a new user with profile
    - GET /api/users/{id}/ - Retrieve user profile
    - PUT/PATCH /api/users/{id}/ - Update user profile
    - DELETE /api/users/{id}/ - Delete user profile
    """
    queryset = UserProfile.objects.select_related('user', 'manufacturer').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['manufacturer', 'role']
    search_fields = ['user__username', 'user__email', 'manufacturer__name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserProfileCreateSerializer
        return UserProfileSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Delete user profile and associated User."""
        profile = self.get_object()
        user = profile.user
        profile.delete()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
