from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SensorDataViewSet, AnomalyAlertViewSet, AnomalyTriggerView

router = DefaultRouter()
router.register(r'sensor-data', SensorDataViewSet, basename='sensordata')
router.register(r'alerts', AnomalyAlertViewSet, basename='anomalyalert')

urlpatterns = [
    path('', include(router.urls)),
    path('anomaly/trigger/', AnomalyTriggerView.as_view(), name='anomaly-trigger'),
]
