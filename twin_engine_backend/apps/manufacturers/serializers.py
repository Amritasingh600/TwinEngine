from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Manufacturer, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the built-in User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ManufacturerSerializer(serializers.ModelSerializer):
    """Serializer for Manufacturer model."""
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Manufacturer
        fields = [
            'id', 'name', 'corporate_id', 'contact_email', 
            'subscription_tier', 'user_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):
        return obj.users.count()


class ManufacturerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing manufacturers."""
    
    class Meta:
        model = Manufacturer
        fields = ['id', 'name', 'corporate_id', 'subscription_tier']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    user = UserSerializer(read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'manufacturer', 'manufacturer_name', 
            'role', 'created_at'
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
            'manufacturer', 'role'
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
