"""
WebSocket URL routing for factory_graph app.
"""
from django.urls import re_path
from .consumers.factory_consumer import FactoryFloorConsumer

websocket_urlpatterns = [
    # Factory floor real-time updates for a specific manufacturer
    # Example: ws://localhost:8000/ws/factory/1/
    re_path(r'ws/factory/(?P<manufacturer_id>\d+)/$', FactoryFloorConsumer.as_asgi()),
]
