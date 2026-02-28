from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DailySummaryViewSet, PDFReportViewSet, DailyReportView

router = DefaultRouter()
router.register(r'summaries', DailySummaryViewSet, basename='dailysummary')
router.register(r'reports', PDFReportViewSet, basename='pdfreport')

urlpatterns = [
    # Custom endpoint BEFORE router to avoid conflict with reports/<pk>/
    path('reports/daily/', DailyReportView.as_view(), name='daily-report'),
    path('', include(router.urls)),
]
