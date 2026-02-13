from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MachineTypeViewSet, MachineNodeViewSet, MachineEdgeViewSet

router = DefaultRouter()
router.register(r'machine-types', MachineTypeViewSet, basename='machinetype')
router.register(r'nodes', MachineNodeViewSet, basename='machinenode')
router.register(r'edges', MachineEdgeViewSet, basename='machineedge')

urlpatterns = [
    path('', include(router.urls)),
]
