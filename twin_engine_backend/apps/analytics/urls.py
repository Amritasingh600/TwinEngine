from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShiftLogViewSet, ProductionReportViewSet, DailyReportView

router = DefaultRouter()
router.register(r'shift-logs', ShiftLogViewSet, basename='shiftlog')
router.register(r'reports', ProductionReportViewSet, basename='productionreport')

urlpatterns = [
    # Custom endpoint BEFORE router to avoid conflict with reports/<pk>/
    path('reports/daily/', DailyReportView.as_view(), name='daily-report'),
    path('', include(router.urls)),
]
