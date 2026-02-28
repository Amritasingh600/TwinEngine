from django.urls import re_path
from .consumers import FloorConsumer

websocket_urlpatterns = [
    re_path(r'ws/floor/(?P<outlet_id>\w+)/$', FloorConsumer.as_asgi()),
]
