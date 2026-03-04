"""
Custom middleware for TwinEngine.

- RequestAuditMiddleware: logs every API request with user, method, path, status, timing.
"""
import logging
import time

logger = logging.getLogger('twinengine.audit')


class RequestAuditMiddleware:
    """
    Logs each request with:
      user | method | path | status | response_time_ms | IP

    Skips static/media paths and the admin CSS/JS to keep the log clean.
    """

    SKIP_PREFIXES = ('/static/', '/media/', '/favicon.ico')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip non-API requests
        if request.path.startswith(self.SKIP_PREFIXES):
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        user = self._get_user(request)
        ip = self._get_client_ip(request)

        logger.info(
            '%s | %s %s | %d | %.1fms | %s',
            user, request.method, request.path,
            response.status_code, duration_ms, ip,
        )

        # Add security headers to every response
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), payment=()'
        )

        return response

    @staticmethod
    def _get_user(request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            return request.user.username
        return 'anon'

    @staticmethod
    def _get_client_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '?')
