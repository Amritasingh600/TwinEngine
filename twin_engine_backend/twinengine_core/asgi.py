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

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twinengine_core.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
django_asgi_app = get_asgi_application()

# Import WebSocket URL patterns after Django setup
from apps.factory_graph.routing import websocket_urlpatterns as factory_ws
from apps.sensors.routing import websocket_urlpatterns as sensors_ws

application = ProtocolTypeRouter({
    # HTTP requests handled by Django
    'http': django_asgi_app,
    
    # WebSocket connections
    'websocket': AuthMiddlewareStack(
        URLRouter(
            factory_ws + sensors_ws
        )
    ),
})
