from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalesDataViewSet, InventoryItemViewSet, StaffScheduleViewSet,
    BusyHoursPredictionView, FootfallPredictionView,
    FoodDemandPredictionView, InventoryAlertView,
    StaffingPredictionView, RevenuePredictionView,
    PredictionDashboardView, TrainModelsView,
    SendInventoryAlertView,
)

router = DefaultRouter()
router.register(r'sales-data', SalesDataViewSet, basename='salesdata')
router.register(r'inventory', InventoryItemViewSet, basename='inventoryitem')
router.register(r'schedules', StaffScheduleViewSet, basename='staffschedule')

urlpatterns = [
    path('', include(router.urls)),

    # Prediction endpoints
    path('predictions/busy-hours/',       BusyHoursPredictionView.as_view(),  name='predict-busy-hours'),
    path('predictions/footfall/',         FootfallPredictionView.as_view(),   name='predict-footfall'),
    path('predictions/food-demand/',      FoodDemandPredictionView.as_view(), name='predict-food-demand'),
    path('predictions/inventory-alerts/', InventoryAlertView.as_view(),       name='predict-inventory'),
    path('predictions/staffing/',         StaffingPredictionView.as_view(),   name='predict-staffing'),
    path('predictions/revenue/',          RevenuePredictionView.as_view(),    name='predict-revenue'),
    path('predictions/dashboard/',        PredictionDashboardView.as_view(),  name='predict-dashboard'),
    path('predictions/train/',            TrainModelsView.as_view(),          name='predict-train'),
    path('predictions/send-inventory-alert/', SendInventoryAlertView.as_view(), name='send-inventory-alert'),
]
