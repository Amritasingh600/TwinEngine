from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BrandViewSet, OutletViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'outlets', OutletViewSet, basename='outlet')
router.register(r'staff', UserProfileViewSet, basename='userprofile')

urlpatterns = [
    path('', include(router.urls)),
]
