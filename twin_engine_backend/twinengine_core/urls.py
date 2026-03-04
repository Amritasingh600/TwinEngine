"""
URL configuration for twinengine_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.db import connection
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from drf_spectacular.utils import extend_schema

from apps.task_status import TaskStatusView


@extend_schema(exclude=True)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for load balancers and container orchestrators."""
    status = {'status': 'healthy', 'version': '2.0.0'}
    try:
        connection.ensure_connection()
        status['database'] = 'connected'
    except Exception:
        status['database'] = 'unavailable'
        return Response(status, status=503)
    return Response(status)


@extend_schema(exclude=True)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint with available endpoints."""
    return Response({
        'message': 'Welcome to TwinEngine Hospitality API',
        'version': '2.0.0',
        'endpoints': {
            # Authentication
            'auth': {
                'login': '/api/auth/token/',
                'refresh': '/api/auth/token/refresh/',
                'verify': '/api/auth/token/verify/',
                'register': '/api/auth/register/',
                'profile': '/api/auth/me/',
                'change-password': '/api/auth/change-password/',
            },
            # Resources
            'brands': '/api/brands/',
            'outlets': '/api/outlets/',
            'staff': '/api/staff/',
            'nodes': '/api/nodes/',
            'flows': '/api/flows/',
            'orders': '/api/orders/',
            'payments': '/api/payments/',
            'table-trigger': '/api/table/trigger/',
            'sales-data': '/api/sales-data/',
            'inventory': '/api/inventory/',
            'schedules': '/api/schedules/',
            'summaries': '/api/summaries/',
            'reports': '/api/reports/',
            'daily-report': '/api/reports/daily/',
            # File uploads (Cloudinary)
            'upload': '/api/upload/',
            'upload-multi': '/api/upload/multi/',
            'upload-delete': '/api/upload/delete/',
            # Background task polling
            'task-status': '/api/tasks/<task_id>/',
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check (for Azure App Service, Render, Docker)
    path('api/health/', health_check, name='health-check'),

    # API Root
    path('api/', api_root, name='api-root'),
    
    # Authentication endpoints
    path('api/auth/', include('apps.hospitality_group.auth_urls')),
    
    # App URLs
    path('api/', include('apps.hospitality_group.urls')),
    path('api/', include('apps.layout_twin.urls')),
    path('api/', include('apps.order_engine.urls')),
    path('api/', include('apps.predictive_core.urls')),
    path('api/', include('apps.insights_hub.urls')),
    path('api/', include('apps.cloudinary_service.urls')),

    # Task status polling
    path('api/tasks/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),

    # API Documentation (Swagger / ReDoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
