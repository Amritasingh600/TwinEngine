from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ManufacturerViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r'manufacturers', ManufacturerViewSet, basename='manufacturer')
router.register(r'users', UserProfileViewSet, basename='userprofile')

urlpatterns = [
    path('', include(router.urls)),
]
