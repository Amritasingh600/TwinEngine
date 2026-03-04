"""
Custom DRF throttle classes for scoped rate limiting.

Each scope maps to a rate defined in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].
Attach to views via `throttle_classes = [AuthRateThrottle]`.
"""
from rest_framework.throttling import SimpleRateThrottle


class AuthRateThrottle(SimpleRateThrottle):
    """Strict limit on authentication endpoints (login, register, password change)."""
    scope = 'auth'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk,
            }
        return self.get_ident(request)


class PredictionRateThrottle(SimpleRateThrottle):
    """Rate limit for ML prediction endpoints."""
    scope = 'predictions'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk,
            }
        return self.get_ident(request)


class ReportRateThrottle(SimpleRateThrottle):
    """Strict limit on heavy report-generation endpoints."""
    scope = 'reports'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk,
            }
        return self.get_ident(request)


class UploadRateThrottle(SimpleRateThrottle):
    """Rate limit for file upload endpoints."""
    scope = 'uploads'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk,
            }
        return self.get_ident(request)


class TrainingRateThrottle(SimpleRateThrottle):
    """Very strict limit on model training (expensive operation)."""
    scope = 'training'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk,
            }
        return self.get_ident(request)
