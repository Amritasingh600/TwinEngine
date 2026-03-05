"""
ASGI config for twinengine_core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Auto-detect Azure App Service and use deployment settings
settings_module = 'twinengine_core.deployment' if 'WEBSITE_HOSTNAME' in os.environ else 'twinengine_core.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import WebSocket routing after Django setup
from apps.layout_twin.routing import websocket_urlpatterns as floor_ws
from apps.order_engine.routing import websocket_urlpatterns as order_ws

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            floor_ws + order_ws
        )
    ),
})
