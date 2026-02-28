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
from rest_framework.response import Response
from rest_framework.decorators import api_view


@api_view(['GET'])
def api_root(request):
    """API root endpoint with available endpoints."""
    return Response({
        'message': 'Welcome to TwinEngine Hospitality API',
        'version': '2.0.0',
        'endpoints': {
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
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Root
    path('api/', api_root, name='api-root'),
    
    # App URLs
    path('api/', include('apps.hospitality_group.urls')),
    path('api/', include('apps.layout_twin.urls')),
    path('api/', include('apps.order_engine.urls')),
    path('api/', include('apps.predictive_core.urls')),
    path('api/', include('apps.insights_hub.urls')),
]
