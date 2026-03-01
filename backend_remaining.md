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

### 3. JWT Authentication System - COMPLETED

**Completed On:** March 1, 2026

#### What Was Implemented:
- JWT token-based authentication using `djangorestframework-simplejwt`
- 6 authentication endpoints:
  | Endpoint | Method | Purpose |
  |----------|--------|---------|
  | `/api/auth/token/` | POST | Login - obtain JWT tokens |
  | `/api/auth/token/refresh/` | POST | Refresh access token |
  | `/api/auth/token/verify/` | POST | Verify token validity |
  | `/api/auth/register/` | POST | User registration with profile |
  | `/api/auth/me/` | GET/PUT | Get/update user profile |
  | `/api/auth/change-password/` | POST | Secure password change |

- JWT Configuration:
  - Access token lifetime: 1 hour
  - Refresh token lifetime: 7 days
  - Token rotation enabled

- Custom permission classes:
  | Permission | Description |
  |------------|-------------|
  | `IsOutletUser` | Users can only access their outlet's data |
  | `IsManager` | Manager-only endpoints |
  | `IsManagerOrReadOnly` | Managers edit, others read-only |
  | `IsStaffOrManager` | Staff + Manager access |

- Management command `create_demo_users`:
  - Creates demo brand: "Demo Restaurant Group"
  - Creates demo outlet: "Downtown Cafe" (Mumbai)
  - Creates 3 test users: manager_demo, waiter_demo, chef_demo

#### Files Created/Modified:
- `apps/hospitality_group/auth_urls.py` - Authentication URL routes
- `apps/hospitality_group/permissions.py` - Custom permission classes
- `apps/hospitality_group/views.py` - Auth views (Register, Profile, ChangePassword)
- `apps/hospitality_group/management/commands/create_demo_users.py` - Demo data command
- `twinengine_core/settings.py` - JWT settings, env variables
- `twinengine_core/urls.py` - Auth route registration
- `twin_engine_backend/.gitignore` - Backend-specific ignores

---

### 3. Table Status Auto-Update Logic ✅

**Completed:** March 1, 2025

**Implementation Summary:**
- Django signals (pre_save/post_save) for automatic table status updates
- Status mapping: PLACED/PREPARING/READY → YELLOW, SERVED → GREEN, COMPLETED/CANCELLED → BLUE
- Validated status transitions (PLACED → PREPARING → READY → SERVED → COMPLETED)
- Wait time properties on OrderTicket model
- WebSocket broadcasts for all status changes
- Management command `check_wait_times` for RED alerts

#### Files Created:
- `apps/order_engine/signals.py` - Signal handlers (260 lines)
- `apps/order_engine/management/commands/check_wait_times.py` - Wait time checker
- `apps/order_engine/tests/test_table_status.py` - 11 comprehensive tests

#### Files Modified:
- `apps/order_engine/models.py` - Added `wait_time_minutes`, `is_long_wait` properties
- `apps/order_engine/apps.py` - Signal registration in `ready()`
- `apps/layout_twin/utils/broadcast.py` - Added `broadcast_wait_time_alert()`
- `apps/layout_twin/consumers/floor_consumer.py` - Added `wait_time_alert()` handler
- `apps/order_engine/utils/__init__.py` - Enhanced order broadcasts with error handling

---

## Remaining Tasks

## Table of Contents

### High Priority (Must Have)
1. [Admin Panel Customization](#1-admin-panel-customization)
2. [PostgreSQL/Neon Migration](#2-postgresqlneon-migration)
3. [Environment & CORS Configuration](#3-environment--cors-configuration)

### Medium Priority (Should Have)
4. [Azure GPT-4o Report Generation](#4-azure-gpt-4o-report-generation)
5. [Cloudinary Media Integration](#5-cloudinary-media-integration)
6. [Demand Forecasting ML](#6-demand-forecasting-ml)
7. [API Documentation (Swagger)](#7-api-documentation-swagger)
8. [Data Seeding & Fixtures](#8-data-seeding--fixtures)

### Lower Priority (Nice to Have)
9. [Unit & Integration Tests](#9-unit--integration-tests)
10. [Background Tasks with Celery](#10-background-tasks-with-celery)
11. [Email Notifications](#11-email-notifications)
12. [Rate Limiting & Throttling](#12-rate-limiting--throttling)
13. [Logging & Error Monitoring](#13-logging--error-monitoring)
14. [Deployment Guide](#14-deployment-guide)

---

## HIGH PRIORITY TASKS

---

## 1. Admin Panel Customization

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

## 2. PostgreSQL/Neon Migration

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

## 3. Environment & CORS Configuration

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

## 4. Azure GPT-4o Report Generation

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

## 5. Cloudinary Media Integration

**Priority:** 🟡 Medium  
**Estimated Time:** 2-3 hours  
**Dependencies:** `cloudinary`

### Purpose
Store and serve PDF reports and media via Cloudinary CDN.

---

## 6. Demand Forecasting ML

**Priority:** 🟡 Medium  
**Estimated Time:** 6-8 hours  
**Dependencies:** `scikit-learn`, `pandas`

### Purpose
ML predictions for:
- Expected covers by time slot
- Inventory depletion forecasts
- Optimal staffing levels

---

## 7. API Documentation (Swagger)

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

## 8. Data Seeding & Fixtures

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

## 9. Unit & Integration Tests

**Priority:** 🟢 Lower  
**Estimated Time:** 4-6 hours

```bash
python manage.py test
coverage run manage.py test && coverage report
```

---

## 10. Background Tasks with Celery

**Priority:** 🟢 Lower  
**Estimated Time:** 4-5 hours

For async processing of reports and daily summaries.

```bash
pip install celery redis
celery -A twinengine_core worker -B -l info
```

---

## 11. Email Notifications

**Priority:** 🟢 Lower  
**Estimated Time:** 2-3 hours

Email alerts for daily reports, low inventory, and long wait times.

---

## 12. Rate Limiting & Throttling

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

## 13. Logging & Error Monitoring

**Priority:** 🟢 Lower  
**Estimated Time:** 2-3 hours

Consider integrating Sentry for production error tracking.

---

## 14. Deployment Guide

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
| ✅ | JWT Authentication | High | Done | 3-4h |
| ✅ | Table Status Auto-Update | High | Done | 2-3h |
| 1 | Admin Panel Customization | 🔴 High | Pending | 2-3h |
| 2 | PostgreSQL/Neon Migration | 🔴 High | Pending | 2-3h |
| 3 | Environment & CORS Config | 🔴 High | Pending | 1-2h |
| 4 | Azure GPT-4o Reports | 🟡 Medium | Pending | 4-6h |
| 5 | Cloudinary Integration | 🟡 Medium | Pending | 2-3h |
| 6 | Demand Forecasting ML | 🟡 Medium | Pending | 6-8h |
| 7 | API Documentation | 🟡 Medium | Pending | 2-3h |
| 8 | Data Seeding & Fixtures | 🟡 Medium | Pending | 2-3h |
| 9 | Unit & Integration Tests | 🟢 Lower | Pending | 4-6h |
| 10 | Celery Background Tasks | 🟢 Lower | Pending | 4-5h |
| 11 | Email Notifications | 🟢 Lower | Pending | 2-3h |
| 12 | Rate Limiting | 🟢 Lower | Pending | 1-2h |
| 13 | Logging & Monitoring | 🟢 Lower | Pending | 2-3h |
| 14 | Deployment Guide | 🟢 Lower | Pending | 3-4h |

**Total Estimated Time:** ~44-59 hours remaining (4 completed, 14 pending)

---

## Quick Start Checklist

### To get MVP running:
- [x] JWT Authentication System ✅
- [x] Table Status Auto-Update Logic ✅
- [ ] Task 2: PostgreSQL Migration
- [ ] Task 3: Environment Configuration
- [ ] Task 8: Seed Sample Data

### For production release add:
- [ ] Task 1: Admin Panel
- [ ] Task 4: AI Reports
- [ ] Task 7: API Docs
- [ ] Task 14: Deployment
