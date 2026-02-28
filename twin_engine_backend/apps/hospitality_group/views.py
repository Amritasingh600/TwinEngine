from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from .models import Brand, Outlet, UserProfile
from .serializers import (
    BrandSerializer, BrandListSerializer,
    OutletSerializer, OutletListSerializer,
    UserProfileSerializer, UserProfileCreateSerializer
)
from .permissions import IsManager, IsManagerOrReadOnly, IsOutletUser


class BrandViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Brands (Restaurant Groups/Chains).
    
    Endpoints:
    - GET /api/brands/ - List all brands
    - POST /api/brands/ - Create a new brand
    - GET /api/brands/{id}/ - Retrieve brand details
    - PUT/PATCH /api/brands/{id}/ - Update brand
    - DELETE /api/brands/{id}/ - Delete brand
    - GET /api/brands/{id}/outlets/ - List outlets for brand
    - GET /api/brands/{id}/stats/ - Get brand statistics
    """
    queryset = Brand.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subscription_tier']
    search_fields = ['name', 'brand_code', 'contact_email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BrandListSerializer
        return BrandSerializer
    
    @action(detail=True, methods=['get'])
    def outlets(self, request, pk=None):
        """Get all outlets for this brand."""
        brand = self.get_object()
        outlets = brand.outlets.filter(is_active=True)
        serializer = OutletListSerializer(outlets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for this brand."""
        brand = self.get_object()
        outlets = brand.outlets.all()
        return Response({
            'total_outlets': outlets.count(),
            'active_outlets': outlets.filter(is_active=True).count(),
            'total_capacity': sum(o.seating_capacity for o in outlets),
            'total_staff': UserProfile.objects.filter(outlet__brand=brand).count()
        })


class OutletViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Outlets (Individual Restaurant Locations).
    
    Endpoints:
    - GET /api/outlets/ - List all outlets
    - POST /api/outlets/ - Create a new outlet
    - GET /api/outlets/{id}/ - Retrieve outlet details
    - PUT/PATCH /api/outlets/{id}/ - Update outlet
    - DELETE /api/outlets/{id}/ - Delete outlet
    - GET /api/outlets/{id}/staff/ - List staff for outlet
    - GET /api/outlets/{id}/tables/ - List tables for outlet
    """
    queryset = Outlet.objects.select_related('brand').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['brand', 'city', 'is_active']
    search_fields = ['name', 'city', 'brand__name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OutletListSerializer
        return OutletSerializer
    
    @action(detail=True, methods=['get'])
    def staff(self, request, pk=None):
        """Get all staff for this outlet."""
        outlet = self.get_object()
        staff = outlet.staff.all()
        serializer = UserProfileSerializer(staff, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """Get all tables (ServiceNodes) for this outlet."""
        from apps.layout_twin.serializers import ServiceNodeListSerializer
        outlet = self.get_object()
        tables = outlet.service_nodes.filter(node_type='TABLE', is_active=True)
        serializer = ServiceNodeListSerializer(tables, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def floor_status(self, request, pk=None):
        """Get current floor status summary."""
        outlet = self.get_object()
        nodes = outlet.service_nodes.filter(is_active=True)
        return Response({
            'outlet': outlet.name,
            'total_nodes': nodes.count(),
            'status_breakdown': {
                'ready': nodes.filter(current_status='BLUE').count(),
                'waiting': nodes.filter(current_status='RED').count(),
                'served': nodes.filter(current_status='GREEN').count(),
                'issue': nodes.filter(current_status='YELLOW').count(),
                'maintenance': nodes.filter(current_status='GREY').count(),
            }
        })


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing User Profiles (Restaurant Staff).
    
    Endpoints:
    - GET /api/staff/ - List all staff profiles
    - POST /api/staff/ - Create a new staff with profile
    - GET /api/staff/{id}/ - Retrieve staff profile
    - PUT/PATCH /api/staff/{id}/ - Update staff profile
    - DELETE /api/staff/{id}/ - Delete staff profile
    """
    queryset = UserProfile.objects.select_related('user', 'outlet', 'outlet__brand').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['outlet', 'outlet__brand', 'role', 'is_on_shift']
    search_fields = ['user__username', 'user__email', 'outlet__name']
    
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


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class RegisterView(generics.CreateAPIView):
    """
    Register a new user with profile.
    
    POST /api/auth/register/
    Body: {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secure_password",
        "outlet": 1,
        "role": "STAFF",
        "phone": "9876543210"
    }
    """
    permission_classes = [AllowAny]
    serializer_class = UserProfileCreateSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract user data
        username = serializer.validated_data['user']['username']
        email = serializer.validated_data['user']['email']
        password = serializer.validated_data['user']['password']
        
        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {'password': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create profile
        profile = UserProfile.objects.create(
            user=user,
            outlet=serializer.validated_data['outlet'],
            role=serializer.validated_data.get('role', 'STAFF'),
            phone=serializer.validated_data.get('phone', ''),
            is_active=serializer.validated_data.get('is_active', True)
        )
        
        return Response(
            UserProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED
        )


class UserProfileView(APIView):
    """
    Get or update the current authenticated user's profile.
    
    GET /api/auth/me/
    PUT /api/auth/me/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile."""
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request):
        """Update current user profile."""
        try:
            profile = request.user.profile
            
            # Only allow updating certain fields
            allowed_fields = ['phone', 'is_on_shift']
            update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
            
            for field, value in update_data.items():
                setattr(profile, field, value)
            
            profile.save()
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class ChangePasswordView(APIView):
    """
    Change password for the authenticated user.
    
    POST /api/auth/change-password/
    Body: {
        "old_password": "current_password",
        "new_password": "new_secure_password"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': 'Both old_password and new_password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check old password
        if not user.check_password(old_password):
            return Response(
                {'error': 'Old password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate new password
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )
