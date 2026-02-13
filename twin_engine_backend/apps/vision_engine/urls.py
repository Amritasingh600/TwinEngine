from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VisionLogViewSet, DetectionZoneViewSet

router = DefaultRouter()
router.register(r'vision-logs', VisionLogViewSet, basename='visionlog')
router.register(r'detection-zones', DetectionZoneViewSet, basename='detectionzone')

urlpatterns = [
    path('', include(router.urls)),
]
