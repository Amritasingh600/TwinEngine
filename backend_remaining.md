# TwinEngine Hospitality Backend - Remaining Tasks

This document outlines all remaining backend tasks with detailed implementation steps, code examples, and testing procedures.

---

## Completed Tasks ✅

### 1. WebSocket Consumers (Real-time Alerts) - COMPLETED

**Completed On:** February 28, 2026

#### What Was Implemented:
- `FloorConsumer` for real-time floor status updates
- `OrderConsumer` for order status notifications
- WebSocket routing for both consumers
- ASGI configuration with ProtocolTypeRouter
- Broadcast utility functions for pushing updates

#### WebSocket Endpoints:
| Endpoint | Purpose |
|----------|---------|
| `ws://host/ws/floor/<outlet_id>/` | Floor status real-time updates |
| `ws://host/ws/orders/` | Global orders stream |
| `ws://host/ws/orders/<outlet_id>/` | Outlet-specific order updates |

---

### 2. Hospitality Architecture Setup - COMPLETED

**Completed On:** February 28, 2026

#### What Was Implemented:
- Finalized all 12 models for hospitality domain
- Configured all 5 Django apps:
  - `hospitality_group` - Brand/Outlet/UserProfile management
  - `layout_twin` - ServiceNode/ServiceFlow (3D floor configuration)
  - `order_engine` - OrderTicket/PaymentLog (Order lifecycle)
  - `predictive_core` - SalesData/InventoryItem/StaffSchedule (AI predictions)
  - `insights_hub` - DailySummary/PDFReport (Reporting & analytics)
- Set up all cross-app imports
- Created all migrations and applied them

---

## Remaining Tasks

## Table of Contents

### High Priority (Must Have)
1. [Authentication System](#1-authentication-system)
2. [Table Status Auto-Update Logic](#2-table-status-auto-update-logic)
3. [Admin Panel Customization](#3-admin-panel-customization)
4. [PostgreSQL/Neon Migration](#4-postgresqlneon-migration)
5. [Environment & CORS Configuration](#5-environment--cors-configuration)

### Medium Priority (Should Have)
6. [Azure GPT-4o Report Generation](#6-azure-gpt-4o-report-generation)
7. [Cloudinary Media Integration](#7-cloudinary-media-integration)
8. [Demand Forecasting ML](#8-demand-forecasting-ml)
9. [API Documentation (Swagger)](#9-api-documentation-swagger)
10. [Data Seeding & Fixtures](#10-data-seeding--fixtures)

### Lower Priority (Nice to Have)
11. [Unit & Integration Tests](#11-unit--integration-tests)
12. [Background Tasks with Celery](#12-background-tasks-with-celery)
13. [Email Notifications](#13-email-notifications)
14. [Rate Limiting & Throttling](#14-rate-limiting--throttling)
15. [Logging & Error Monitoring](#15-logging--error-monitoring)
16. [Deployment Guide](#16-deployment-guide)

---

## HIGH PRIORITY TASKS

---

## 1. Authentication System

**Priority:** 🔴 High  
**Estimated Time:** 3-4 hours  
**Dependencies:** `djangorestframework-simplejwt`

### Purpose
Secure API endpoints with JWT authentication for:
- User login/logout
- Token refresh
- Role-based access (Manager/Staff/Viewer)

### Implementation Steps

#### Step 1: Install Dependencies
```bash
pip install djangorestframework-simplejwt
```

#### Step 2: Update Settings
```python
# twinengine_core/settings.py

INSTALLED_APPS = [
    # ... existing apps
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

#### Step 3: Create Auth URLs
Create `apps/hospitality_group/auth_urls.py`:

```python
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView, TokenVerifyView,
)
from .views import RegisterView, UserProfileView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserProfileView.as_view(), name='user-profile'),
]
```

#### Step 4: Add Custom Permissions
Create `apps/hospitality_group/permissions.py`:

```python
from rest_framework import permissions

class IsOutletUser(permissions.BasePermission):
    """Only allow users to access their own outlet's data."""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'outlet'):
            return obj.outlet == request.user.profile.outlet
        return True

class IsManagerOrReadOnly(permissions.BasePermission):
    """Managers can edit, others can only read."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.profile.role == 'MANAGER'
```

#### Step 5: Update Main URLs
```python
# twinengine_core/urls.py
path('api/auth/', include('apps.hospitality_group.auth_urls')),
```

### Testing
```bash
# Get JWT token
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Access protected endpoint
curl http://127.0.0.1:8000/api/outlets/ \
  -H "Authorization: Bearer <access_token>"
```

---

## 2. Table Status Auto-Update Logic

**Priority:** 🔴 High  
**Estimated Time:** 2-3 hours

### Purpose
Automatically update table (ServiceNode) status based on order lifecycle:
- Order Placed → Table turns YELLOW
- Order Served → Table turns GREEN
- Order Completed → Table turns BLUE (available)
- Wait time exceeded → Table turns RED

### Implementation

#### Step 1: Create Signal Handlers
Create `apps/order_engine/signals.py`:

```python
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import OrderTicket

@receiver(pre_save, sender=OrderTicket)
def capture_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = OrderTicket.objects.get(pk=instance.pk).status
        except OrderTicket.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=OrderTicket)
def update_table_status_on_order_change(sender, instance, created, **kwargs):
    """Update table status when order status changes."""
    from apps.layout_twin.models import ServiceNode
    from apps.layout_twin.utils import broadcast_node_status_change
    
    table = instance.table
    old_table_status = table.current_status
    new_status = None
    
    if created or instance.status == 'PLACED':
        new_status = 'YELLOW'  # Order in progress
    elif instance.status == 'SERVED':
        new_status = 'GREEN'   # Order delivered
    elif instance.status == 'COMPLETED':
        # Check if table has other active orders
        active_orders = OrderTicket.objects.filter(
            table=table,
            status__in=['PLACED', 'PREPARING', 'READY', 'SERVED']
        ).exclude(pk=instance.pk).exists()
        
        if not active_orders:
            new_status = 'BLUE'  # Table available
    elif instance.status == 'CANCELLED':
        active_orders = OrderTicket.objects.filter(
            table=table,
            status__in=['PLACED', 'PREPARING', 'READY', 'SERVED']
        ).exclude(pk=instance.pk).exists()
        
        if not active_orders:
            new_status = 'BLUE'
    
    if new_status and new_status != old_table_status:
        table.current_status = new_status
        table.save()
        
        # Broadcast via WebSocket
        broadcast_node_status_change(
            outlet_id=table.outlet_id,
            node_id=table.id,
            old_status=old_table_status,
            new_status=new_status
        )
```

#### Step 2: Register Signals
Update `apps/order_engine/apps.py`:

```python
from django.apps import AppConfig

class OrderEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.order_engine'
    
    def ready(self):
        import apps.order_engine.signals  # noqa
```

#### Step 3: Create Wait Time Alert Management Command
Create `apps/order_engine/management/commands/check_wait_times.py`:

```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Check for tables with exceeded wait times'
    
    def handle(self, *args, **options):
        from apps.order_engine.models import OrderTicket
        from apps.layout_twin.models import ServiceNode
        
        threshold = timezone.now() - timedelta(minutes=15)
        
        long_wait_orders = OrderTicket.objects.filter(
            status__in=['PLACED', 'PREPARING'],
            placed_at__lt=threshold
        ).select_related('table')
        
        for order in long_wait_orders:
            if order.table.current_status != 'RED':
                order.table.current_status = 'RED'
                order.table.save()
                self.stdout.write(f'Table {order.table.name} marked RED')
```

---

## 3. Admin Panel Customization

**Priority:** 🔴 High  
**Estimated Time:** 2-3 hours

### Purpose
Create intuitive admin interface for outlet managers with custom dashboards.

### Implementation

Update `apps/hospitality_group/admin.py`:
```python
from django.contrib import admin
from .models import Brand, Outlet, UserProfile

class OutletInline(admin.TabularInline):
    model = Outlet
    extra = 0
    fields = ['name', 'city', 'manager_name', 'seating_capacity', 'is_active']

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'corporate_id', 'subscription_tier', 'outlet_count', 'is_active']
    list_filter = ['subscription_tier', 'is_active']
    search_fields = ['name', 'corporate_id']
    inlines = [OutletInline]
    
    def outlet_count(self, obj):
        return obj.outlets.count()

@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'city', 'manager_name', 'seating_capacity', 'is_active']
    list_filter = ['brand', 'city', 'is_active']
    search_fields = ['name', 'address', 'manager_name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'outlet', 'role', 'is_active']
    list_filter = ['role', 'outlet', 'is_active']
```

Update `apps/order_engine/admin.py`:
```python
from django.contrib import admin
from .models import OrderTicket, PaymentLog

class PaymentInline(admin.TabularInline):
    model = PaymentLog
    extra = 0

@admin.register(OrderTicket)
class OrderTicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'status', 'guest_count', 'total', 'placed_at']
    list_filter = ['status', 'table__outlet', 'placed_at']
    search_fields = ['id', 'table__name']
    inlines = [PaymentInline]
```

---

## 4. PostgreSQL/Neon Migration

**Priority:** 🔴 High  
**Estimated Time:** 2-3 hours

### Purpose
Migrate from SQLite to production PostgreSQL (Neon serverless).

### Implementation

#### Step 1: Install Driver
```bash
pip install psycopg2-binary dj-database-url
```

#### Step 2: Update Settings
```python
# twinengine_core/settings.py
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

#### Step 3: Set Environment Variable
```bash
# .env
DATABASE_URL=postgresql://user:pass@ep-xxx.region.aws.neon.tech/twinengine?sslmode=require
```

#### Step 4: Migrate
```bash
python manage.py dumpdata > backup.json
python manage.py migrate
python manage.py loaddata backup.json
```

---

## 5. Environment & CORS Configuration

**Priority:** 🔴 High  
**Estimated Time:** 1-2 hours

### Create `.env.example`:
```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Redis (for Channels)
REDIS_URL=redis://localhost:6379/0

# Azure OpenAI
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Cloudinary
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

### Update `settings.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True
```

---

## MEDIUM PRIORITY TASKS

---

## 6. Azure GPT-4o Report Generation

**Priority:** 🟡 Medium  
**Estimated Time:** 4-6 hours  
**Dependencies:** `openai`

### Purpose
Generate AI-powered operational reports:
- Daily shift summaries
- Weekly performance analytics
- Custom date range reports

### Implementation
Create `apps/insights_hub/services/report_service.py` with Azure OpenAI integration.

---

## 7. Cloudinary Media Integration

**Priority:** 🟡 Medium  
**Estimated Time:** 2-3 hours  
**Dependencies:** `cloudinary`

### Purpose
Store and serve PDF reports and media via Cloudinary CDN.

---

## 8. Demand Forecasting ML

**Priority:** 🟡 Medium  
**Estimated Time:** 6-8 hours  
**Dependencies:** `scikit-learn`, `pandas`

### Purpose
ML predictions for:
- Expected covers by time slot
- Inventory depletion forecasts
- Optimal staffing levels

---

## 9. API Documentation (Swagger)

**Priority:** 🟡 Medium  
**Estimated Time:** 2-3 hours  
**Dependencies:** `drf-spectacular`

### Implementation
```bash
pip install drf-spectacular
```

```python
# urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

---

## 10. Data Seeding & Fixtures

**Priority:** 🟡 Medium  
**Estimated Time:** 2-3 hours

### Purpose
Create sample data for development and testing.

### Implementation
Create management command `apps/hospitality_group/management/commands/seed_data.py`:

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Seed database with sample hospitality data'
    
    def handle(self, *args, **options):
        from apps.hospitality_group.models import Brand, Outlet
        from apps.layout_twin.models import ServiceNode
        
        # Create sample brand
        brand, _ = Brand.objects.get_or_create(
            corporate_id='DEMO001',
            defaults={
                'name': 'Demo Restaurant Group',
                'contact_email': 'demo@example.com',
                'subscription_tier': 'GROWTH'
            }
        )
        
        # Create sample outlet with tables
        outlet, _ = Outlet.objects.get_or_create(
            brand=brand,
            name='Downtown Cafe',
            defaults={
                'address': '123 Main Street',
                'city': 'Mumbai',
                'manager_name': 'John Manager',
                'manager_phone': '9876543210',
                'seating_capacity': 50
            }
        )
        
        for i in range(1, 11):
            ServiceNode.objects.get_or_create(
                outlet=outlet,
                name=f'Table {i}',
                defaults={
                    'node_type': 'TABLE',
                    'pos_x': (i % 5) * 2.0,
                    'pos_z': (i // 5) * 2.0,
                    'capacity': 4,
                    'current_status': 'BLUE'
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Sample data created!'))
```

---

## LOWER PRIORITY TASKS

---

## 11. Unit & Integration Tests

**Priority:** 🟢 Lower  
**Estimated Time:** 4-6 hours

```bash
python manage.py test
coverage run manage.py test && coverage report
```

---

## 12. Background Tasks with Celery

**Priority:** 🟢 Lower  
**Estimated Time:** 4-5 hours

For async processing of reports and daily summaries.

```bash
pip install celery redis
celery -A twinengine_core worker -B -l info
```

---

## 13. Email Notifications

**Priority:** 🟢 Lower  
**Estimated Time:** 2-3 hours

Email alerts for daily reports, low inventory, and long wait times.

---

## 14. Rate Limiting & Throttling

**Priority:** 🟢 Lower  
**Estimated Time:** 1-2 hours

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

---

## 15. Logging & Error Monitoring

**Priority:** 🟢 Lower  
**Estimated Time:** 2-3 hours

Consider integrating Sentry for production error tracking.

---

## 16. Deployment Guide

**Priority:** 🟢 Lower  
**Estimated Time:** 3-4 hours

### Render (Backend)
- Start command: `daphne -b 0.0.0.0 -p $PORT twinengine_core.asgi:application`

### Vercel (Frontend)
- Configure environment variables for API URL

---

## Summary Table

| # | Task | Priority | Status | Est. Time |
|---|------|----------|--------|-----------|
| ✅ | WebSocket Consumers | High | Done | 4h |
| ✅ | Architecture Setup | High | Done | 4h |
| 1 | Authentication System | 🔴 High | Pending | 3-4h |
| 2 | Table Status Auto-Update | 🔴 High | Pending | 2-3h |
| 3 | Admin Panel Customization | 🔴 High | Pending | 2-3h |
| 4 | PostgreSQL/Neon Migration | 🔴 High | Pending | 2-3h |
| 5 | Environment & CORS Config | 🔴 High | Pending | 1-2h |
| 6 | Azure GPT-4o Reports | 🟡 Medium | Pending | 4-6h |
| 7 | Cloudinary Integration | 🟡 Medium | Pending | 2-3h |
| 8 | Demand Forecasting ML | 🟡 Medium | Pending | 6-8h |
| 9 | API Documentation | 🟡 Medium | Pending | 2-3h |
| 10 | Data Seeding & Fixtures | 🟡 Medium | Pending | 2-3h |
| 11 | Unit & Integration Tests | 🟢 Lower | Pending | 4-6h |
| 12 | Celery Background Tasks | 🟢 Lower | Pending | 4-5h |
| 13 | Email Notifications | 🟢 Lower | Pending | 2-3h |
| 14 | Rate Limiting | 🟢 Lower | Pending | 1-2h |
| 15 | Logging & Monitoring | 🟢 Lower | Pending | 2-3h |
| 16 | Deployment Guide | 🟢 Lower | Pending | 3-4h |

**Total Estimated Time:** ~50-65 hours

---

## Quick Start Checklist

### To get MVP running:
- [ ] Task 1: Authentication System
- [ ] Task 2: Table Status Auto-Update Logic
- [ ] Task 4: PostgreSQL Migration
- [ ] Task 5: Environment Configuration
- [ ] Task 10: Seed Sample Data

### For production release add:
- [ ] Task 3: Admin Panel
- [ ] Task 6: AI Reports
- [ ] Task 9: API Docs
- [ ] Task 16: Deployment
