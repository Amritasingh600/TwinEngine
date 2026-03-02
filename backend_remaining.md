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

### 4. Table Status Auto-Update Logic - COMPLETED

**Completed On:** March 1, 2026

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

### 5. Admin Panel Customization - COMPLETED

**Completed On:** March 1, 2026

#### What Was Implemented:

**hospitality_group Admin:**
- `BrandAdmin`: Outlet inline forms, outlet count display, fieldsets organization
- `OutletAdmin`: Staff inline forms, staff count with on-shift indicator, editable is_active field
- `UserProfileAdmin`: Role/outlet filtering, editable is_on_shift status, raw_id fields for performance

**order_engine Admin:**
- `OrderTicketAdmin`: Payment inline forms, color-coded status badges (RED/ORANGE/YELLOW/GREEN/BLUE/GRAY)
- Wait time display with warning icons for delays >15 minutes
- Editable status field for quick updates, outlet name display

**layout_twin Admin:**
- `ServiceNodeAdmin`: Service flow inline forms, status badges matching floor colors
- Active orders count, editable current_status field
- 3D position fields in collapsible fieldset

**predictive_core Admin:**
- `SalesDataAdmin`: Revenue formatting with ₹ symbol, hourly data organization
- `InventoryItemAdmin`: Low stock warnings (red text), quantity display
- `StaffScheduleAdmin`: Shift badges (MORNING/AFTERNOON/EVENING/NIGHT colors), time range display

**insights_hub Admin:**
- `DailySummaryAdmin`: Revenue display, delayed orders warnings, date hierarchy
- `PDFReportAdmin`: Report type badges (DAILY/WEEKLY/MONTHLY/CUSTOM), status badges, date range display

#### Files Modified:
- `apps/hospitality_group/admin.py` - Enhanced Brand/Outlet/UserProfile admin
- `apps/order_engine/admin.py` - Enhanced OrderTicket admin with color badges
- `apps/layout_twin/admin.py` - Enhanced ServiceNode admin
- `apps/predictive_core/admin.py` - Enhanced SalesData/InventoryItem/StaffSchedule admin
- `apps/insights_hub/admin.py` - Enhanced DailySummary/PDFReport admin

#### Files Created:
- `apps/hospitality_group/management/commands/create_full_demo_data.py` - Comprehensive demo data generator
- `ADMIN_VERIFICATION_CHECKLIST.md` - Detailed testing guide (50+ test cases)

#### Demo Data Includes:
- 1 Brand, 1 Outlet, 5 Staff members (Manager, 2 Waiters, Chef, Host)
- 15 Tables with mixed statuses (BLUE/GREEN/YELLOW/RED)
- 15 Orders across all statuses (PLACED → COMPLETED)
- 8 Payments (CASH/CARD/UPI/WALLET methods)
- 8 Inventory items (3 with low stock warnings)
- 15 Staff schedules (3 days, all shifts)
- 35 Sales data records (7 days × 5 peak hours)
- 7 Daily summaries with metrics
- 3 PDF reports (DAILY/WEEKLY/MONTHLY)

#### Admin Features Verified:
- ✅ 20+ color-coded status badges
- ✅ Warning indicators (low stock, wait times, delayed orders)
- ✅ 4 inline form types for related data editing
- ✅ 5 quick-edit fields for operational efficiency
- ✅ Custom display methods (revenue, counts, time ranges)
- ✅ Advanced filtering and search functionality
- ✅ Organized fieldsets with collapsible sections

---

### 6. Environment & CORS Configuration - COMPLETED

**Completed On:** March 2, 2026

#### What Was Implemented:

**Phase 1 — Environment Foundation:**
- `.env` file with 16 env vars (Django, DB, CORS, CSRF, Redis, Azure, Cloudinary, Email, Sentry, Logging)
- `.env.example` template with all keys documented
- `settings.py` fully env-driven: SECRET_KEY, DEBUG, ALLOWED_HOSTS, TIME_ZONE, REDIS_URL
- Channel layer auto-switches: InMemoryChannelLayer (dev) ↔ RedisChannelLayer (prod)
- `dj-database-url` added to requirements (ready for future PostgreSQL switch)

**Phase 2 — CORS & Security:**
- Explicit `CORS_ALLOW_HEADERS` whitelist (authorization, content-type, x-csrftoken, etc.)
- Explicit `CORS_ALLOW_METHODS` whitelist (GET, POST, PUT, PATCH, DELETE, OPTIONS)
- `CSRF_TRUSTED_ORIGINS` env-driven
- Production security hardening gated behind `DEBUG=False`:
  - HTTPS/HSTS (1-year, preload)
  - Secure cookies (HttpOnly, SameSite=Lax)
  - X_FRAME_OPTIONS=DENY, XSS filter, content-type nosniff
  - SECURE_PROXY_SSL_HEADER for cloud load balancers

**Phase 3 — Data Migration Utilities:**
- `export_data` management command — dumps all app data to JSON (with `--include-auth`, `--apps`, `--indent`)
- `import_data` management command — loads fixtures (with `--flush`, `--dry-run`, `--ignore-errors`)
- PostgreSQL sequence reset on import
- `Makefile` with 22 targets (db-backup, db-restore, db-reset, test, run, etc.)

**Phase 4 — Static Files & Production:**
- WhiteNoise `CompressedManifestStaticFilesStorage` (gzip + cache-busting hashes)
- `STATIC_ROOT`, `STATICFILES_DIRS`, `MEDIA_URL`, `MEDIA_ROOT` configured
- Structured logging: console + rotating file handler (5 MB, 3 backups)
- Separate loggers for `django`, `django.request`, `apps.*`
- `Procfile` (Daphne ASGI for Render/Heroku)
- `build.sh` (Render build script: pip install, collectstatic, migrate)

**Phase 5 — Testing:**
- 52 tests covering all config: env vars, CORS, CSRF, security, channels, static files, logging, export/import commands, .env.example validation, deployment files
- All 63 tests passing (52 config + 11 signal tests)

#### Files Created:
- `.env.example` — Full env template with all keys
- `Makefile` — 22 development/deployment targets
- `Procfile` — Daphne ASGI deployment
- `build.sh` — Render build script
- `logs/.gitkeep` — Log directory
- `apps/hospitality_group/management/commands/export_data.py` — Data export command
- `apps/hospitality_group/management/commands/import_data.py` — Data import command
- `twinengine_core/tests/__init__.py` — 52 configuration tests

#### Files Modified:
- `twinengine_core/settings.py` — Full env-driven config, CORS, security, logging, WhiteNoise
- `.env` — Expanded from 6 to 16 keys
- `.gitignore` — Added logs, backups
- `requirements.txt` — Added `dj-database-url`

---

### 7. Cloudinary Media Integration - COMPLETED

**Completed On:** March 2, 2026

#### What Was Implemented:
- Dedicated `apps/cloudinary_service/` module with upload service, serializers, views, and URL routing
- `CloudinaryUploadService` class with `upload_file()`, `upload_bytes()`, `delete_file()` methods
- Root folder organization: all uploads stored under `twinengine/` on Cloudinary CDN
- 3 REST API endpoints (all require JWT authentication):

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload/` | POST | Single file upload (max 10 MB) |
| `/api/upload/multi/` | POST | Multi-file upload (max 10 files) |
| `/api/upload/delete/` | DELETE | Delete file by public_id |

- Serializer validation: file size (10 MB limit), file count (10 max), optional folder/tags
- Cloudinary config added to `settings.py` via environment variables

#### Files Created:
- `apps/cloudinary_service/__init__.py`
- `apps/cloudinary_service/upload.py` - CloudinaryUploadService class
- `apps/cloudinary_service/serializers.py` - File validation serializers
- `apps/cloudinary_service/views.py` - Upload/Delete API views
- `apps/cloudinary_service/urls.py` - URL routing

#### Files Modified:
- `twinengine_core/settings.py` - Cloudinary configuration
- `twinengine_core/urls.py` - Cloudinary URL routes

---

### 8. Azure GPT-4o Report Generation Pipeline - COMPLETED

**Completed On:** March 2, 2026

#### What Was Implemented:
- Complete 5-step AI report generation pipeline:
  1. **Collect raw data** from all models (orders, payments, inventory, staff, sales)
  2. **Send to Azure GPT-4o** for AI analysis (with automatic local fallback)
  3. **Build professional PDF** using ReportLab
  4. **Upload PDF to Cloudinary** storage
  5. **Return Cloudinary URL** to the client

- Data collection service (`data_collector.py`):
  - Aggregates order_summary, payment_summary, table_overview, inventory_summary, staff_summary
  - Uses Django ORM aggregations (Sum, Avg, Count)

- GPT-4o integration (`gpt_report.py`):
  - Azure OpenAI GPT-4o API call with structured prompt
  - Automatic fallback to local analysis if GPT-4o unavailable
  - Returns: executive_summary, insights[], recommendations[], model_used

- PDF generation (ReportLab):
  - Professional layout with header, key metrics table, order/payment breakdowns
  - Low stock alerts, executive summary, numbered insights & recommendations

- Report API endpoint:
  | Endpoint | Method | Purpose |
  |----------|--------|---------|
  | `/api/reports/generate/` | POST | Generate AI PDF report |
  - Request: `{"outlet_id": 4, "report_type": "DAILY", "start_date": "2026-03-02"}`
  - Response: `{cloudinary_url, gpt_summary, insights[], recommendations[], generated_by}`

#### Files Created:
- `apps/insights_hub/services/__init__.py`
- `apps/insights_hub/services/data_collector.py` - Raw data collection from all models
- `apps/insights_hub/services/gpt_report.py` - Azure GPT-4o integration + fallback

#### Files Modified:
- `apps/insights_hub/views.py` - Complete rewrite with 5-step pipeline
- `apps/insights_hub/serializers.py` - Added ReportGenerateSerializer
- `apps/insights_hub/urls.py` - Added generate endpoint
- `twinengine_core/settings.py` - Azure OpenAI configuration

---

### 9. Synthetic Data Generator - COMPLETED

**Completed On:** March 2, 2026

#### What Was Implemented:
- Comprehensive synthetic data generator covering every restaurant scenario
- Management command: `python manage.py generate_synthetic_data`
- Options: `--clear` flag to wipe and regenerate all data

#### Data Generated:
| Category | Count | Details |
|----------|-------|---------|
| Brand | 1 | "Spice Republic Hospitality Group" |
| Outlet | 1 | 72-seat restaurant in Koramangala |
| Staff | 9 | Manager, 3 Waiters, 2 Chefs, Host, Bartender, Dishwasher |
| Tables | 15 | 5 statuses: BLUE, GREEN, YELLOW, RED, GREY |
| Special Nodes | 5 | Kitchen, Bar, Entrance, Cash Counter, Restroom |
| Orders | 50 | Full lifecycle: COMPLETED(22), SERVED(8), PREPARING(5), READY(4), PLACED(5), CANCELLED(6) |
| Payments | 31 | CASH, CARD, UPI, WALLET, SPLIT + 1 FAILED |
| Inventory | 20 | 5 low stock + 5 near-expiry alerts |
| Staff Schedules | 29 | 4 days across MORNING/AFTERNOON/NIGHT shifts |
| Sales Data | 91 | 7 days of hourly sales records |
| Daily Summary | 1 | Revenue, orders, guests, tips, delayed count |

- Test user created: `synth_mgr_1` / `synth123` (Manager role)
- Uses `get_or_create` for Brand/Outlet (safe to re-run)

#### Files Created:
- `apps/insights_hub/management/commands/generate_synthetic_data.py`

---

## Remaining Tasks

## Task Summary

| Priority | Task | Status | Est. Time |
|----------|------|--------|-----------|
| 🔴 High | Admin Panel Customization | ✅ COMPLETED | - |
| 🔴 High | PostgreSQL/Neon Migration | ⏳ Pending | 2-3 hours |
| 🔴 High | Environment & CORS Configuration | ✅ COMPLETED | - |
| 🟠 Medium | Azure GPT-4o Report Generation | ✅ COMPLETED | - |
| 🟠 Medium | Cloudinary Media Integration | ✅ COMPLETED | - |
| 🟠 Medium | Demand Forecasting ML | ⏳ Pending | 6-8 hours |
| 🟠 Medium | API Documentation (Swagger) | ⏳ Pending | 3-4 hours |
| 🟠 Medium | Data Seeding & Fixtures | ✅ COMPLETED | - |
| 🟢 Low | Unit & Integration Tests | ⏳ Pending | 8-10 hours |
| 🟢 Low | Background Tasks (Celery) | ⏳ Pending | 4-5 hours |
| 🟢 Low | Email Notifications | ⏳ Pending | 2-3 hours |
| 🟢 Low | Rate Limiting & Throttling | ⏳ Pending | 2-3 hours |
| 🟢 Low | Logging & Error Monitoring | ⏳ Pending | 3-4 hours |
| 🟢 Low | Deployment Guide | ⏳ Pending | 2-3 hours |

**Total Remaining:** 8 tasks | **Est. Time:** 31-43 hours

---

## Table of Contents

### High Priority (Must Have)
1. [PostgreSQL/Neon Migration](#1-postgresqlneon-migration) - Deferred

### Medium Priority (Should Have)
2. [Demand Forecasting ML](#2-demand-forecasting-ml)
3. [API Documentation (Swagger)](#3-api-documentation-swagger)

### Lower Priority (Nice to Have)
4. [Unit & Integration Tests](#4-unit--integration-tests)
5. [Background Tasks with Celery](#5-background-tasks-with-celery)
6. [Email Notifications](#6-email-notifications)
7. [Rate Limiting & Throttling](#7-rate-limiting--throttling)
8. [Deployment Guide](#8-deployment-guide)

---

## HIGH PRIORITY TASKS (DEFERRED)

---

## 1. PostgreSQL/Neon Migration

**Priority:** 🔴 High — **DEFERRED to end of development**  
**Estimated Time:** 2-3 hours  
**Prerequisites:** `dj-database-url` already installed, `export_data`/`import_data` commands ready

### Purpose
Migrate from SQLite to production PostgreSQL (Neon serverless).
All tooling is already in place — just needs the Neon connection string.

### When Ready:
```bash
# 1. Export current data
python manage.py export_data --include-auth -o pre_migration_backup.json

# 2. Set DATABASE_URL in .env
DATABASE_URL=postgresql://user:pass@ep-xxx.region.aws.neon.tech/twinengine?sslmode=require

# 3. Update settings.py DATABASES block to use dj_database_url.config()

# 4. Migrate and import
python manage.py migrate
python manage.py import_data pre_migration_backup.json
```

---

## MEDIUM PRIORITY TASKS

---

## 2. Demand Forecasting ML

**Priority:** 🟡 Medium  
**Estimated Time:** 6-8 hours  
**Dependencies:** `scikit-learn`, `pandas`

### Purpose
ML predictions for:
- Expected covers by time slot
- Inventory depletion forecasts
- Optimal staffing levels

---

## 3. API Documentation (Swagger)

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

## LOWER PRIORITY TASKS

---

## 4. Unit & Integration Tests

**Priority:** 🟢 Lower  
**Estimated Time:** 4-6 hours

```bash
python manage.py test
coverage run manage.py test && coverage report
```

---

## 5. Background Tasks with Celery

**Priority:** 🟢 Lower  
**Estimated Time:** 4-5 hours

For async processing of reports and daily summaries.

```bash
pip install celery redis
celery -A twinengine_core worker -B -l info
```

---

## 6. Email Notifications

**Priority:** 🟢 Lower  
**Estimated Time:** 2-3 hours

Email alerts for daily reports, low inventory, and long wait times.

---

## 7. Rate Limiting & Throttling

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

## 8. Deployment Guide

**Priority:** 🟢 Lower  
**Estimated Time:** 2-3 hours

### Render (Backend)
- Start command: `daphne -b 0.0.0.0 -p $PORT twinengine_core.asgi:application`
- Build script: `build.sh` (already created)
- Procfile ready

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
| ✅ | Admin Panel Customization | High | Done | 2-3h |
| ✅ | Environment & CORS Config | High | Done | 1-2h |
| ✅ | Cloudinary Media Integration | Medium | Done | 2-3h |
| ✅ | Azure GPT-4o Report Pipeline | Medium | Done | 4-6h |
| ✅ | Synthetic Data Generator | Medium | Done | 2-3h |
| 1 | PostgreSQL/Neon Migration | 🔴 High | Deferred | 2-3h |
| 2 | Demand Forecasting ML | 🟡 Medium | Pending | 6-8h |
| 3 | API Documentation | 🟡 Medium | Pending | 2-3h |
| 4 | Unit & Integration Tests | 🟢 Lower | Pending | 4-6h |
| 5 | Celery Background Tasks | 🟢 Lower | Pending | 4-5h |
| 6 | Email Notifications | 🟢 Lower | Pending | 2-3h |
| 7 | Rate Limiting | 🟢 Lower | Pending | 1-2h |
| 8 | Deployment Guide | 🟢 Lower | Pending | 2-3h |

**Total Estimated Time:** ~25-33 hours remaining (9 completed, 8 pending)

---

## Quick Start Checklist

### To get MVP running:
- [x] JWT Authentication System ✅
- [x] Table Status Auto-Update Logic ✅
- [x] Admin Panel Customization ✅
- [x] Environment & CORS Configuration ✅
- [x] Cloudinary Media Integration ✅
- [x] Azure GPT-4o Report Pipeline ✅
- [x] Synthetic Data Generator ✅
- [ ] Task 1: PostgreSQL Migration (deferred)

### For production release add:
- [ ] Task 3: API Docs (Swagger)
- [ ] Task 8: Deployment Guide
