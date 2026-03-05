"""
Azure App Service deployment settings for TwinEngine Hospitality.

This file is automatically used when WEBSITE_HOSTNAME is set (Azure App Service).
It imports everything from settings.py, then overrides production-specific values.

Usage:
    - manage.py, wsgi.py, and asgi.py auto-detect Azure via WEBSITE_HOSTNAME env var.
    - Set all required env vars in Azure Portal → App Service → Configuration.
"""

from .settings import *                     # noqa: F401, F403
from .settings import BASE_DIR, MIDDLEWARE  # explicit for linters
import os

# ───────────────────────────────────────────────────────────────
# Core Django settings
# ───────────────────────────────────────────────────────────────
DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY', os.environ.get(
    'DJANGO_SECRET_KEY', 'change-me-in-azure-portal'
))

WEBSITE_HOSTNAME = os.environ.get('WEBSITE_HOSTNAME', '')

ALLOWED_HOSTS = [WEBSITE_HOSTNAME] if WEBSITE_HOSTNAME else ['*']

CSRF_TRUSTED_ORIGINS = [
    f'https://{WEBSITE_HOSTNAME}',
]

# Add your frontend URL if deployed separately (e.g., Vercel)
_FRONTEND_URL = os.environ.get('FRONTEND_URL', '')
if _FRONTEND_URL:
    CSRF_TRUSTED_ORIGINS.append(_FRONTEND_URL)

# ───────────────────────────────────────────────────────────────
# CORS — allow frontend to call the API
# ───────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    f'https://{WEBSITE_HOSTNAME}',
]
if _FRONTEND_URL:
    CORS_ALLOWED_ORIGINS.append(_FRONTEND_URL)

CORS_ALLOW_CREDENTIALS = True

# ───────────────────────────────────────────────────────────────
# Middleware — same as settings.py (re-declared for clarity)
# ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
    'twinengine_core.middleware.RequestAuditMiddleware',
]

# ───────────────────────────────────────────────────────────────
# Database — Azure Database for PostgreSQL
# ───────────────────────────────────────────────────────────────
# Azure provides AZURE_POSTGRESQL_CONNECTIONSTRING as space-separated key=value pairs:
#   "dbname=... host=... port=5432 user=... password=... sslmode=require"
# Alternatively, you can set DATABASE_URL as a standard postgres:// URI.

_AZURE_CONN = os.environ.get('AZURE_POSTGRESQL_CONNECTIONSTRING', '')
_DATABASE_URL = os.environ.get('DATABASE_URL', '')

if _AZURE_CONN:
    # Parse Azure's space-separated connection string safely
    _conn_parts = {}
    for pair in _AZURE_CONN.split(' '):
        if '=' in pair:
            key, value = pair.split('=', 1)  # split on first = only (passwords may contain =)
            _conn_parts[key] = value

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _conn_parts.get('dbname', 'twinengine'),
            'HOST': _conn_parts.get('host', ''),
            'PORT': _conn_parts.get('port', '5432'),
            'USER': _conn_parts.get('user', ''),
            'PASSWORD': _conn_parts.get('password', ''),
            'OPTIONS': {
                'sslmode': _conn_parts.get('sslmode', 'require'),
            },
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
    }
elif _DATABASE_URL:
    # Standard DATABASE_URL format (postgres://user:pass@host:port/dbname)
    from urllib.parse import urlparse
    _parsed = urlparse(_DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _parsed.path.lstrip('/'),
            'HOST': _parsed.hostname,
            'PORT': _parsed.port or 5432,
            'USER': _parsed.username,
            'PASSWORD': _parsed.password,
            'OPTIONS': {
                'sslmode': 'require',
            },
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
    }
# else: falls back to settings.py DATABASES (SQLite for dev — should not happen on Azure)

# ───────────────────────────────────────────────────────────────
# Static files — WhiteNoise (serves static directly from Django)
# ───────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# ───────────────────────────────────────────────────────────────
# Security hardening (Azure runs behind a reverse proxy)
# ───────────────────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000              # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# ───────────────────────────────────────────────────────────────
# Redis & Channels (Azure Cache for Redis)
# ───────────────────────────────────────────────────────────────
_REDIS_URL = os.environ.get('REDIS_URL', os.environ.get('AZURE_REDIS_CONNECTIONSTRING', ''))

if _REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [_REDIS_URL],
            },
        },
    }
    CELERY_BROKER_URL = _REDIS_URL
else:
    # Fallback: in-memory (WebSockets won't scale across workers)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
    CELERY_BROKER_URL = 'redis://localhost:6379/0'

# ───────────────────────────────────────────────────────────────
# Logging — stdout only (Azure Log Stream / App Insights picks it up)
# ───────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'azure': {
            'format': '{asctime} [{levelname}] {name} — {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'azure',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Disable browsable API in production
REST_FRAMEWORK = {
    **globals().get('REST_FRAMEWORK', {}),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}