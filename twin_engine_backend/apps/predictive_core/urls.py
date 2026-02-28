from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalesDataViewSet, InventoryItemViewSet, StaffScheduleViewSet

router = DefaultRouter()
router.register(r'sales-data', SalesDataViewSet, basename='salesdata')
router.register(r'inventory', InventoryItemViewSet, basename='inventoryitem')
router.register(r'schedules', StaffScheduleViewSet, basename='staffschedule')

urlpatterns = [
    path('', include(router.urls)),
]
