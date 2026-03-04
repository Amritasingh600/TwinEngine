"""
Inline request/response serializers for drf-spectacular schema generation.
Used by APIViews that don't have a model-backed serializer_class.
"""
from rest_framework import serializers


class UserProfileUpdateRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, help_text="Phone number")
    is_on_shift = serializers.BooleanField(required=False, help_text="Whether user is currently on shift")


class ChangePasswordRequestSerializer(serializers.Serializer):
    old_password = serializers.CharField(help_text="Current password")
    new_password = serializers.CharField(help_text="New password")


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
