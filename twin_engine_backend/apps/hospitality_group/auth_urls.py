"""
Authentication URLs for JWT token management.
"""
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from twinengine_core.throttles import AuthRateThrottle
from .views import RegisterView, UserProfileView, ChangePasswordView


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Login view with auth-scoped rate limiting."""
    throttle_classes = [AuthRateThrottle]


class ThrottledTokenRefreshView(TokenRefreshView):
    """Token refresh with auth-scoped rate limiting."""
    throttle_classes = [AuthRateThrottle]


urlpatterns = [
    # JWT Token endpoints (rate-limited)
    path('token/', ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', ThrottledTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User management
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
