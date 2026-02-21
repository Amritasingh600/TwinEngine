"""
WebSocket URL routing for sensors app.
"""
from django.urls import re_path
from .consumers.alert_consumer import AlertConsumer

websocket_urlpatterns = [
    # Global alerts stream (all manufacturers)
    # Example: ws://localhost:8000/ws/alerts/
    re_path(r'ws/alerts/$', AlertConsumer.as_asgi()),
    
    # Manufacturer-specific alerts stream
    # Example: ws://localhost:8000/ws/alerts/1/
    re_path(r'ws/alerts/(?P<manufacturer_id>\d+)/$', AlertConsumer.as_asgi()),
]
