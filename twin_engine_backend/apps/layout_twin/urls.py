from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceNodeViewSet, ServiceFlowViewSet

router = DefaultRouter()
router.register(r'nodes', ServiceNodeViewSet, basename='servicenode')
router.register(r'flows', ServiceFlowViewSet, basename='serviceflow')

urlpatterns = [
    path('', include(router.urls)),
]
