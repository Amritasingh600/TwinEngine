from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderTicketViewSet, PaymentLogViewSet, TableStatusTriggerView

router = DefaultRouter()
router.register(r'orders', OrderTicketViewSet, basename='orderticket')
router.register(r'payments', PaymentLogViewSet, basename='paymentlog')

urlpatterns = [
    path('', include(router.urls)),
    path('table/trigger/', TableStatusTriggerView.as_view(), name='table-trigger'),
]
