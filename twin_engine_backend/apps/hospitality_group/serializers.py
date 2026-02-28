from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Brand, Outlet, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the built-in User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class BrandSerializer(serializers.ModelSerializer):
    """Serializer for Brand model (restaurant chain/group)."""
    outlet_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'corporate_id', 'contact_email', 
            'subscription_tier', 'outlet_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_outlet_count(self, obj):
        return obj.outlets.count()


class BrandListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing brands."""
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'corporate_id', 'subscription_tier']


class OutletSerializer(serializers.ModelSerializer):
    """Serializer for Outlet model (individual restaurant location)."""
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    staff_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Outlet
        fields = [
            'id', 'brand', 'brand_name', 'name', 'address', 'city', 
            'seating_capacity', 'opening_time', 'closing_time', 'is_active', 
            'staff_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_staff_count(self, obj):
        return obj.staff.count()


class OutletListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing outlets."""
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    class Meta:
        model = Outlet
        fields = ['id', 'name', 'brand_name', 'city', 'seating_capacity', 'is_active']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model (restaurant staff)."""
    user = UserSerializer(read_only=True)
    outlet_name = serializers.CharField(source='outlet.name', read_only=True)
    brand_name = serializers.CharField(source='outlet.brand.name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'outlet', 'outlet_name', 'brand_name',
            'role', 'phone', 'is_on_shift', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating UserProfile with nested User."""
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'outlet', 'role', 'phone'
        ]
    
    def create(self, validated_data):
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'first_name': validated_data.pop('first_name', ''),
            'last_name': validated_data.pop('last_name', ''),
        }
        user = User.objects.create_user(**user_data)
        profile = UserProfile.objects.create(user=user, **validated_data)
        return profile
