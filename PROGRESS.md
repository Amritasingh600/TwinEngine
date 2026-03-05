# TwinEngine Hospitality - Development Progress

## February 2026

### Week 1: Project Initiation
- **7-9 Feb 2026** → Ideation and learning for project
- **10 Feb 2026** → Discussed and created the synopsis with mentor (Mr. Shivanshu Upadhayay)

### Week 2: Foundation Setup
- **11 Feb 2026** → Setup of the project structure and Django REST Framework
- **12 Feb 2026** → Completed models.py of each app (initial version)
- **13 Feb 2026** → Serialized the input and output at backend
- **14 Feb 2026** → Discussed with mentor (Mr. Shivanshu Sir) about ML models

### Week 3: WebSocket Integration
- **21 Feb 2026** → Creating WebSockets to project (Completed Task - 1)

### Week 4: Architecture Transformation
- **28 Feb 2026** → **Major Architecture Update: Hospitality Edition**
  - Finalized all Django models for hospitality domain
  - Created hospitality-focused data models:
    - `Brand`, `Outlet`, `UserProfile` (hospitality_group)
    - `ServiceNode`, `ServiceFlow` (layout_twin)
    - `OrderTicket`, `PaymentLog` (order_engine)
    - `SalesData`, `InventoryItem`, `StaffSchedule` (predictive_core)
    - `DailySummary`, `PDFReport` (insights_hub)
  - Configured all 5 Django apps with proper naming
  - Created all migrations for database schema
  - Updated all documentation files

## March 2026

### Week 5: Authentication & Admin Panel Implementation
- **1 Mar 2026** → **JWT Authentication System - COMPLETED ✅**
  - Implemented JWT token-based authentication using `djangorestframework-simplejwt`
  - Created 6 authentication endpoints:
    - `POST /api/auth/token/` - Login and obtain JWT tokens
    - `POST /api/auth/token/refresh/` - Refresh access token
    - `POST /api/auth/token/verify/` - Verify token validity
    - `POST /api/auth/register/` - User registration with profile
    - `GET/PUT /api/auth/me/` - Get/update authenticated user profile
    - `POST /api/auth/change-password/` - Secure password change
  - Configured JWT settings:
    - Access token lifetime: 1 hour
    - Refresh token lifetime: 7 days
    - Token rotation enabled for security
  - Created custom permission classes:
    - `IsOutletUser` - Restrict users to their outlet's data
    - `IsManager` - Manager-only access
    - `IsManagerOrReadOnly` - Managers can edit, others read-only
    - `IsStaffOrManager` - Staff and manager access
  - Created demo data management command:
    - Command: `python manage.py create_demo_users`
    - Creates demo brand, outlet, and 3 test users
    - Test users: manager_demo, waiter_demo, chef_demo (password: manager123, waiter123, chef123)
  - Comprehensive authentication testing completed
  - Documentation created: `AUTH_IMPLEMENTATION.md`

- **1 Mar 2026** → **Admin Panel Customization - COMPLETED ✅**
  - Enhanced all 5 Django app admin interfaces with advanced features:
  
  **hospitality_group Admin:**
  - Brand admin with outlet inline forms and outlet count display
  - Outlet admin with staff inline forms and staff count (with on-shift indicator)
  - UserProfile admin with role/outlet filtering and editable shift status
  - Organized fieldsets for better data entry
  
  **order_engine Admin:**
  - OrderTicket admin with payment inline forms
  - Color-coded status badges (RED/ORANGE/YELLOW/GREEN/BLUE/GRAY)
  - Wait time display with warning icons for delays >15 minutes
  - Quick-edit status field for operational efficiency
  - Outlet name display for multi-outlet brands
  
  **layout_twin Admin:**
  - ServiceNode admin with service flow inline forms
  - Status badges matching real-time floor visualization colors
  - Active orders count display
  - 3D position fields organized in collapsible fieldsets
  
  **predictive_core Admin:**
  - SalesData admin with formatted revenue display (₹ symbol)
  - InventoryItem admin with low stock warnings (red text alerts)
  - StaffSchedule admin with color-coded shift badges
  - Time range displays for better readability
  
  **insights_hub Admin:**
  - DailySummary admin with revenue formatting and delayed order warnings
  - PDFReport admin with report type badges (DAILY/WEEKLY/MONTHLY/CUSTOM)
  - Status badges for report generation tracking
  - Date range displays and has_pdf indicators
  
  - Fixed all Django system check errors (5 issues resolved)
  - All admin panels now production-ready with intuitive interfaces
  - Created comprehensive demo data command `create_full_demo_data`:
    - Generates 100+ realistic test records across all 12 models
    - Includes: 15 tables, 15 orders (all statuses), 8 payments, 8 inventory items
    - Adds: 15 staff schedules, 35 sales data records, 7 daily summaries, 3 PDF reports
    - Respects Django's status transition validation rules
    - Command: `python manage.py create_full_demo_data --clear`
  - Created detailed verification checklist (`ADMIN_VERIFICATION_CHECKLIST.md`):
    - 50+ individual test cases for all admin features
    - Step-by-step testing instructions for 5 apps
    - Visual guides for color badges, warnings, and displays
    - Troubleshooting section
  - Fixed UserProfile model bug (duplicate __str__ method with wrong field reference)
  - All admin features verified working:
    - ✅ 20+ color-coded badges across all statuses
    - ✅ Low stock warnings, wait time alerts, delayed order warnings
    - ✅ 4 types of inline forms (Outlets, UserProfiles, Payments, ServiceFlows)
    - ✅ 5 quick-edit fields for operational efficiency
    - ✅ Revenue formatting, time displays, counts, and custom methods
    - ✅ Advanced filtering and search across all models
    - `IsStaffOrManager` - Staff and manager access
  - Built authentication views:
    - `RegisterView` - User registration with automatic profile creation
    - `UserProfileView` - Profile management
    - `ChangePasswordView` - Secure password updates
  - Created management command `create_demo_users`:
    - Demo brand: "Demo Restaurant Group"
    - Demo outlet: "Downtown Cafe" (Mumbai)
    - 3 test users: Manager, Waiter, Chef
  - Added comprehensive test suite (`test_auth_complete.py`)
  - All authentication endpoints tested and verified working
  - Updated `requirements.txt` with JWT dependencies
  - Made API root publicly accessible while protecting other endpoints

- **1 Mar 2026** → **Table Status Auto-Update Logic - COMPLETED ✅**
  - Implemented Django signals for automatic table color updates based on order lifecycle
  - Status mapping logic:
    - Order PLACED/PREPARING/READY → Table turns YELLOW (waiting)
    - Order SERVED → Table turns GREEN (delivered)
    - Order COMPLETED/CANCELLED → Table turns BLUE (if no other active orders)
    - Wait time > 15 min → Table turns RED (needs attention)
  - Created status transition validation:
    - PLACED → PREPARING → READY → SERVED → COMPLETED
    - Any state → CANCELLED (allowed)
    - Invalid transitions raise ValidationError
  - Enhanced WebSocket broadcasts:
    - `broadcast_node_status_change()` - Real-time 3D floor updates
    - `broadcast_order_created()` - New order notifications
    - `broadcast_order_updated()` - Status change notifications
    - `broadcast_order_completed()` - Order completion alerts
    - `broadcast_wait_time_alert()` - Long wait time warnings
  - Created management command `check_wait_times`:
    - Marks tables RED when orders exceed threshold
    - Options: `--outlet`, `--threshold`, `--dry-run`
    - For cron: `*/2 * * * * python manage.py check_wait_times`
  - Added model properties to OrderTicket:
    - `wait_time_minutes` - Calculate current wait time
    - `is_long_wait` - Check if > 15 minute threshold
  - Created comprehensive test suite (11 tests passing):
    - Test order → YELLOW transition
    - Test served → GREEN transition
    - Test completed → BLUE transition
    - Test multiple orders on same table
    - Test status transition validation
    - Test wait time management command

- **2 Mar 2026** → **Cloudinary Media Integration - COMPLETED ✅**
  - Created dedicated `apps/cloudinary_service/` module
  - Implemented `CloudinaryUploadService` class:
    - `upload_file(file, folder)` - Upload Django UploadedFile objects
    - `upload_bytes(content, filename, folder)` - Upload raw bytes (PDFs, images)
    - `delete_file(public_id)` - Delete files from Cloudinary
    - Root folder: `twinengine/` (all uploads organized under this)
  - Created 3 REST API endpoints (all require JWT authentication):
    - `POST /api/upload/` - Single file upload (max 10 MB)
    - `POST /api/upload/multi/` - Multi-file upload (max 10 files)
    - `DELETE /api/upload/delete/` - Delete file by public_id
  - Created serializers with validation:
    - `FileUploadSerializer` - 10 MB file size limit, optional folder/tags
    - `MultiFileUploadSerializer` - Max 10 files per request
    - `FileDeleteSerializer` - Validates public_id
  - Configured Cloudinary in `settings.py`:
    - `cloud_name`, `api_key`, `api_secret` from environment variables
  - Files created:
    - `apps/cloudinary_service/__init__.py`
    - `apps/cloudinary_service/upload.py`
    - `apps/cloudinary_service/serializers.py`
    - `apps/cloudinary_service/views.py`
    - `apps/cloudinary_service/urls.py`
  - Files modified:
    - `twinengine_core/settings.py` - Added Cloudinary config
    - `twinengine_core/urls.py` - Added Cloudinary URL routes

- **2 Mar 2026** → **Azure GPT-4o Report Generation Pipeline - COMPLETED ✅**
  - Built complete 5-step AI report generation pipeline:
    1. **Collect raw data** from all models (orders, payments, inventory, staff, sales)
    2. **Send to Azure GPT-4o** for AI analysis (with local fallback)
    3. **Build professional PDF** using ReportLab
    4. **Upload PDF to Cloudinary** storage
    5. **Return Cloudinary URL** to the client
  - Created `apps/insights_hub/services/data_collector.py`:
    - `collect_raw_data(outlet, start_date, end_date)` function
    - Aggregates: order_summary, payment_summary, table_overview, inventory_summary, staff_summary, existing_daily_summaries
    - Uses Django ORM aggregations (Sum, Avg, Count)
  - Created `apps/insights_hub/services/gpt_report.py`:
    - `generate_report_with_gpt(raw_data)` - Azure OpenAI GPT-4o integration
    - `generate_report_fallback(raw_data)` - Local fallback when GPT-4o unavailable
    - Returns: executive_summary, insights[], recommendations[], model_used
  - Completely rewrote `apps/insights_hub/views.py`:
    - `PDFReportViewSet.generate()` - Main pipeline endpoint
    - `_build_pdf()` - Professional PDF with:
      - Header with outlet name and date range
      - Key Metrics table (revenue, orders, avg ticket, guests, avg wait time)
      - Order breakdown by status (pie-chart-style table)
      - Payment breakdown by method and status
      - Low stock alerts (highlighted items below reorder threshold)
      - Executive Summary section (from GPT-4o)
      - Numbered Insights and Recommendations
    - Automatic `DailySummary` creation from collected data
    - `PDFReport` record saved with Cloudinary URL
  - Updated `apps/insights_hub/serializers.py`:
    - `ReportGenerateSerializer` - Validates outlet_id, start_date, optional end_date, report_type
  - Azure OpenAI Configuration in `settings.py`:
    - `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`
  - Report API endpoint:
    - `POST /api/reports/generate/` - Generate and return PDF report
    - Request body: `{"outlet_id": 4, "report_type": "DAILY", "start_date": "2026-03-02"}`
    - Response includes: `cloudinary_url`, `gpt_summary`, `insights[]`, `recommendations[]`, `generated_by`

- **2 Mar 2026** → **Synthetic Data Generator - COMPLETED ✅**
  - Created `apps/insights_hub/management/commands/generate_synthetic_data.py`
  - Comprehensive data covering every restaurant scenario:
    - 1 Brand ("Spice Republic Hospitality Group") + 1 Outlet (72 seats)
    - 9 Staff (Manager, 3 Waiters, 2 Chefs, 1 Host, 1 Bartender, 1 Dishwasher)
    - 15 Tables with 5 different statuses (BLUE/GREEN/YELLOW/RED/GREY)
    - 5 Special nodes (Kitchen, Bar, Entrance, Cash Counter, Restroom)
    - 50 Orders with realistic distribution:
      - COMPLETED (22), SERVED (8), PREPARING (5), READY (4), PLACED (5), CANCELLED (6)
      - Full lifecycle simulation (PLACED → PREPARING → READY → SERVED → COMPLETED)
      - Cancellation reasons: "Customer left", "Long wait time", "Incorrect order", etc.
    - 31 Payment records (CASH/CARD/UPI/WALLET/SPLIT, including 1 FAILED)
    - 20 Inventory items (5 low stock, 5 near-expiry alerts)
    - 29 Staff schedules across 4 days (MORNING/AFTERNOON/NIGHT shifts)
    - 91 Hourly sales records (7 days of historical data)
    - 1 Daily summary (revenue, orders, guests, tips, delayed count)
  - Options: `--clear` flag to wipe and regenerate all data
  - Uses `get_or_create` for Brand/Outlet (safe to re-run)
  - Creates test user: `synth_mgr_1` / `synth123` (Manager role)
  - Command: `python manage.py generate_synthetic_data`

- **2 Mar 2026** → **End-to-End Pipeline Testing - VERIFIED ✅**
  - Full pipeline tested successfully:
    - Login → `POST /api/auth/token/` → 200 OK (JWT token)
    - Report Generation → `POST /api/reports/generate/` → 200 OK
    - GPT-4o analysis completed (model: `gpt-4o-2024-11-20`)
    - PDF uploaded to Cloudinary successfully
    - Response includes: Cloudinary URL, executive summary, 8 insights, 6 recommendations
  - Test results with synthetic data:
    - Revenue: Rs.47,575.50 across 50 orders
    - 153 guests served, avg ticket Rs.951.51
    - GPT-4o identified: peak hours (8-10 PM), 5 low-stock items, 6 cancellations
    - Actionable recommendations generated (staffing, inventory reorder, order tracking)

---

## Testing Guide: Report Generation & Cloudinary Pipeline

### Prerequisites
- Django dev server running: `python manage.py runserver`
- Synthetic data loaded: `python manage.py generate_synthetic_data`
- Virtual environment activated

### Step 1: Login & Obtain JWT Token

```bash
# Using curl
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "synth_mgr_1", "password": "synth123"}'

# Using PowerShell
$body = '{"username":"synth_mgr_1","password":"synth123"}'
$resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/token/" -Method POST -ContentType "application/json" -Body $body
$token = $resp.access
Write-Host "Token: $($token.Substring(0,50))..."
```

**Expected Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Step 2: Generate Report (Main Pipeline)

```bash
# Using curl
curl -X POST http://127.0.0.1:8000/api/reports/generate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"outlet_id": 4, "report_type": "DAILY", "start_date": "2026-03-02"}'

# Using PowerShell
$headers = @{Authorization = "Bearer $token"; "Content-Type" = "application/json"}
$body = '{"outlet_id": 4, "report_type": "DAILY", "start_date": "2026-03-02"}'
$report = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/reports/generate/" -Method POST -Headers $headers -Body $body
$report | ConvertTo-Json -Depth 5
```

**Expected Response (200 OK):**
```json
{
  "id": 1,
  "outlet": 4,
  "outlet_name": "Spice Republic Koramangala",
  "report_type": "DAILY",
  "start_date": "2026-03-02",
  "end_date": "2026-03-02",
  "cloudinary_url": "https://res.cloudinary.com/dfhl1aopy/raw/upload/.../report.pdf",
  "gpt_summary": "The operations at Spice Republic Koramangala...",
  "insights": ["Revenue was Rs.47,575.50...", "..."],
  "recommendations": ["Increase kitchen staff during peak hours...", "..."],
  "status": "COMPLETED",
  "error_message": null,
  "generated_by": "gpt-4o-2024-11-20",
  "created_at": "2026-03-02T...",
  "completed_at": "2026-03-02T..."
}
```

### Step 3: Download and Verify PDF

Open the `cloudinary_url` from the response in your browser. The PDF should contain:
- **Header**: Outlet name, report type, date range
- **Key Metrics Table**: Total Revenue, Total Orders, Avg Ticket Size, Total Guests, Avg Wait Time
- **Order Breakdown**: Count per status (COMPLETED, SERVED, PREPARING, etc.)
- **Payment Breakdown**: Count and total per method (CASH, CARD, UPI, WALLET, SPLIT)
- **Low Stock Alerts**: Items below reorder threshold (highlighted)
- **Executive Summary**: AI-generated analysis from GPT-4o
- **Insights**: Numbered list of data-driven observations
- **Recommendations**: Numbered list of actionable suggestions

### Step 4: Test Cloudinary File Upload (Standalone)

```bash
# Using PowerShell - upload a test file
$headers = @{Authorization = "Bearer $token"}
$form = @{file = Get-Item "C:\path\to\testfile.jpg"; folder = "test"}
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/upload/" -Method POST -Headers $headers -Form $form
```

**Expected Response (201 Created):**
```json
{
  "url": "https://res.cloudinary.com/dfhl1aopy/image/upload/.../testfile.jpg",
  "public_id": "twinengine/test/testfile",
  "resource_type": "image"
}
```

### Step 5: Test File Deletion from Cloudinary

```bash
# Using PowerShell
$headers = @{Authorization = "Bearer $token"; "Content-Type" = "application/json"}
$body = '{"public_id": "twinengine/test/testfile"}'
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/upload/delete/" -Method DELETE -Headers $headers -Body $body
```

**Expected Response (200 OK):**
```json
{
  "message": "File deleted successfully",
  "public_id": "twinengine/test/testfile"
}
```

### Quick Reference: All New API Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/reports/generate/` | Generate AI PDF report | JWT |
| GET | `/api/reports/` | List all reports | JWT |
| GET | `/api/reports/<id>/` | Get single report details | JWT |
| GET | `/api/reports/daily/` | Get today's daily report | JWT |
| POST | `/api/upload/` | Upload single file to Cloudinary | JWT |
| POST | `/api/upload/multi/` | Upload multiple files (max 10) | JWT |
| DELETE | `/api/upload/delete/` | Delete file from Cloudinary | JWT |

### Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired or missing | Re-login at `/api/auth/token/` |
| `400 Bad Request` on report | Invalid outlet_id or date | Check outlet exists: `python manage.py shell -c "from apps.hospitality_group.models import Outlet; print(Outlet.objects.values('id','name'))"` |
| Report shows all zeros | No data for that outlet/date | Run `python manage.py generate_synthetic_data` and use today's date |
| GPT-4o fallback used | Azure OpenAI key issue | Check `AZURE_OPENAI_KEY` in `.env`; report still generates with local analysis |
| `PDF not downloadable` | Cloudinary config issue | Check `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` in `.env` |

---

## March 3, 2026 -- ML Prediction Module (Complete Implementation)

### What Was Built
Implemented the full **Demand Forecasting ML Module** with 6 machine learning models, a unified prediction service, 8 REST API endpoints, a training management command, and a comprehensive test suite.

### 6 ML Models Implemented

| # | Model | Algorithm | Purpose |
|---|-------|-----------|---------|
| 1 | BusyHoursPredictor | RandomForestClassifier | Predicts busy vs. slow hours |
| 2 | FootfallForecaster | GradientBoostingRegressor | Forecasts expected guest count |
| 3 | FoodDemandPredictor | RandomForestRegressor | Predicts order volume per category |
| 4 | InventoryPredictor | GradientBoostingRegressor | Forecasts inventory depletion & reorder timing |
| 5 | StaffingOptimizer | RandomForestRegressor | Recommends optimal staff count per shift |
| 6 | RevenueForecaster | GradientBoostingRegressor | Predicts revenue by hour/day |

### Files Created

| File | Purpose |
|------|---------|
| `apps/predictive_core/ml/__init__.py` | ML package init |
| `apps/predictive_core/ml/feature_engineering.py` | Feature extraction from SalesData |
| `apps/predictive_core/ml/busy_hours.py` | BusyHoursPredictor model |
| `apps/predictive_core/ml/footfall.py` | FootfallForecaster model |
| `apps/predictive_core/ml/food_demand.py` | FoodDemandPredictor model |
| `apps/predictive_core/ml/inventory_predictor.py` | InventoryPredictor model |
| `apps/predictive_core/ml/staffing_optimizer.py` | StaffingOptimizer model |
| `apps/predictive_core/ml/revenue_forecaster.py` | RevenueForecaster model |
| `apps/predictive_core/ml/prediction_service.py` | PredictionService facade (unified API) |
| `apps/predictive_core/management/commands/train_models.py` | `python manage.py train_models` command |
| `apps/predictive_core/tests/test_ml_predictions.py` | 10 unit tests for all endpoints |
| `demo_predictions.py` | Demo script to test all endpoints via Django test client |

### Files Modified

| File | Change |
|------|--------|
| `apps/predictive_core/views.py` | Added 8 prediction API views |
| `apps/predictive_core/urls.py` | Added 8 prediction URL routes |
| `apps/predictive_core/serializers.py` | Added prediction request serializers |
| `apps/predictive_core/admin.py` | Fixed fieldsets (SalesData + InventoryItem field mismatches) |
| `requirements.txt` | Added scikit-learn, pandas, numpy, joblib |

### 8 Prediction API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/predictions/busy-hours/<outlet_id>/` | Predict busy/slow hours for a date |
| GET | `/api/predictions/footfall/<outlet_id>/` | Forecast expected guest count |
| GET | `/api/predictions/food-demand/<outlet_id>/` | Predict order volume by category |
| GET | `/api/predictions/inventory/<outlet_id>/` | Inventory depletion forecast & reorder alerts |
| GET | `/api/predictions/staffing/<outlet_id>/` | Optimal staff count per shift |
| GET | `/api/predictions/revenue/<outlet_id>/` | Revenue forecast by hour |
| GET | `/api/predictions/dashboard/<outlet_id>/` | Combined dashboard (all predictions) |
| POST | `/api/predictions/train/<outlet_id>/` | Trigger model training for an outlet |

### Training & Testing Results
- **Training**: `python manage.py train_models --outlet-id 4` -- All 6 models trained successfully
- **Unit Tests**: 10/10 passing (`python manage.py test apps.predictive_core.tests.test_ml_predictions`)
- **Live Demo**: `demo_predictions.py` -- All 7 endpoint groups returned real prediction data
- **Dependencies Added**: scikit-learn==1.8.0, pandas==3.0.1, numpy==2.4.2, joblib==1.5.3

### Bug Fixes Applied
- Fixed `StaffingOptimizer`: Changed `servicenode_set` to `service_nodes` (correct `related_name` from ServiceNode model)
- Fixed `SalesDataAdmin`: Removed non-existent fields (`total_covers`, `avg_party_size`, `peak_hour_indicator`) from fieldsets
- Fixed `InventoryItemAdmin`: Changed `min_quantity`/`max_quantity` to `reorder_threshold`/`par_level`, removed non-existent `created_at`

### Security Cleanup (GitHub-Ready)
- Removed all real secrets from `.env` (DB password, Azure key, Cloudinary credentials)
- Verified `.env` is in `.gitignore` (both root and backend)
- Added `*.joblib` and `**/ml_models/` to `.gitignore` (trained model artifacts)

---

### Phase 1: API Documentation (drf-spectacular) — COMPLETED ✅
- Installed and configured `drf-spectacular` for OpenAPI 3.0 schema generation
- Decorated all views across 6 apps with `@extend_schema` (70 paths, 119 operations)
- Added Swagger UI (`/api/docs/`) and ReDoc (`/api/redoc/`)
- Schema validation: **0 errors, 0 warnings**

### Phase 2: Celery Background Jobs & Email Notifications — COMPLETED ✅
- **4 Mar 2026** → Full Celery + Mailtrap email integration

#### Celery Configuration
- Installed `celery>=5.4.0`, `redis>=5.0.0`, `django-celery-beat>=2.6.0`, `django-celery-results>=2.5.1`
- Created `twinengine_core/celery.py` — Celery app with Redis broker and auto-discovery
- Updated `twinengine_core/__init__.py` — ensures Celery app loads on Django start
- Result backend: `django-db` (task results stored in PostgreSQL via django-celery-results)
- Beat scheduler: `DatabaseScheduler` (periodic tasks manageable via Django Admin)

#### Background Tasks (6 total)
| Task | Module | Description |
|------|--------|-------------|
| `train_models_for_outlet` | `predictive_core.tasks` | Retrain all 6 ML models for one outlet (async) |
| `train_all_outlets` | `predictive_core.tasks` | Nightly cron: iterate all active outlets |
| `send_inventory_alerts` | `predictive_core.tasks` | Email low-stock items for one outlet |
| `send_inventory_alerts_all` | `predictive_core.tasks` | Morning cron: inventory sweep all outlets |
| `generate_report_task` | `insights_hub.tasks` | Full report pipeline (data→GPT→PDF→Cloudinary→email) |
| `email_report_task` | `insights_hub.tasks` | Email completed report link to brand contact |

#### Celery Beat Schedule
| Job | Task | Schedule |
|-----|------|----------|
| `nightly-model-retraining` | `train_all_outlets` | Daily at 02:00 |
| `morning-inventory-alerts` | `send_inventory_alerts_all` | Daily at 07:00 |

#### Email Integration (Mailtrap Sandbox)
- Backend: `django.core.mail.backends.smtp.EmailBackend`
- Host: `sandbox.smtp.mailtrap.io:2525` (Mailtrap SMTP sandbox)
- Test email sent successfully to Mailtrap inbox
- Two HTML email templates created:
  - `templates/emails/inventory_alert.html` — low-stock alert table
  - `templates/emails/report_ready.html` — report completion notification with download link

#### View Updates (Async Dispatch)
- `TrainModelsView.post()` → dispatches `train_models_for_outlet.delay()`, returns 202 with `task_id`
  - Supports `?sync=true` for backward compatibility
- `PDFReportViewSet.generate()` → dispatches `generate_report_task.delay()`, returns 202 with `task_id`
  - Supports `?sync=true` for in-request execution

#### Task Status Polling Endpoint
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/tasks/<task_id>/` | Poll Celery task status (PENDING/STARTED/SUCCESS/FAILURE) |

#### Schema Update
- **71 paths, 120 operations** (was 70/119)
- New tag: **Tasks** — Celery background task status polling
- Schema validation: **0 errors, 0 warnings** (exit code 0)

#### How to Run Celery
```bash
# Worker (processes tasks)
celery -A twinengine_core worker --loglevel=info

# Beat (periodic task scheduler)
celery -A twinengine_core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
- `.env.example` already has clean placeholder values

### Phase 3: Rate Limiting, Throttling & Security — COMPLETED ✅
- **4 Mar 2026** → Full API throttling, brute-force protection, audit logging & security hardening

#### DRF Throttling (7 scopes)
| Scope | Rate | Applied To |
|-------|------|-----------|
| `anon` | 30/min | All unauthenticated requests (global default) |
| `user` | 120/min | All authenticated requests (global default) |
| `auth` | 10/min | Login, register, password change, token refresh |
| `predictions` | 60/min | All 8 prediction endpoints + training |
| `reports` | 10/min | PDF report generation |
| `uploads` | 20/min | Cloudinary file upload/delete |
| `training` | 5/min | ML model retraining |

- Created `twinengine_core/throttles.py` — 5 custom `SimpleRateThrottle` subclasses
- Applied throttle classes to views across 4 apps:
  - `hospitality_group`: RegisterView, ChangePasswordView, token obtain/refresh
  - `predictive_core`: All prediction views (via PredictionBaseView), TrainModelsView
  - `cloudinary_service`: FileUploadView, MultiFileUploadView, FileDeleteView
  - `insights_hub`: PDFReportViewSet

#### Brute-Force Protection (django-axes 8.3.1)
- Installed `django-axes>=8.0,<9.0`
- Configuration:
  - Lock after **5 failed login attempts**
  - Cooloff period: **30 minutes**
  - Lockout by **username + IP combination**
  - Reset counter on successful login
- All 10 axes migrations applied

#### Audit Logging Middleware
- Created `twinengine_core/middleware.py` — `RequestAuditMiddleware`
- Logs: `user | method path | status | duration_ms | IP` to `logs/audit.log`
- Skips static/media paths for performance
- Rotating file handler: 10 MB max, 5 backups

#### Security Headers (added to every response)
| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=()` |

#### Additional Security Hardening
- Password minimum length raised to **10 characters**
- Session timeout: **2 hours**, expires on browser close
- Upload size limit: **10 MB** (both memory and file)
- Django system check: **0 issues**
- Schema validation: **0 errors, 0 warnings** (71 paths, 120 operations — unchanged)

### Phase 4: Deployment Configuration (Azure + Render + Docker) — COMPLETED ✅
- **4 Mar 2026** → Full containerized deployment setup for Azure (primary) and Render (free tier)

#### Docker Configuration
- **Dockerfile** — Multi-stage build (builder + runtime), Python 3.12-slim, non-root user, health check
- **docker-entrypoint.sh** — Universal entrypoint supporting 4 modes: `server` (Daphne ASGI), `gunicorn` (WSGI), `worker` (Celery), `beat` (scheduler)
- **docker-compose.yml** — Full local stack: PostgreSQL 16, Redis 7, Django web, Celery worker, Celery beat
- **.dockerignore** — Excludes venv, .git, IDE files, docs, sqlite, media

#### Azure Deployment (Primary Target)
| File | Purpose |
|------|---------|
| `.azure/infra.bicep` | Infrastructure-as-Code: App Service Plan, Web App (container), PostgreSQL Flexible Server, Azure Cache for Redis, Container Registry |
| `.azure/infra.parameters.json` | Parameter template (Key Vault reference for DB password) |
| `.azure/deploy.sh` | One-command deploy script: creates RG → deploys Bicep → builds Docker → pushes to ACR → configures app → restarts |

- Azure App Service with Linux containers, WebSocket support, health check path
- PostgreSQL Flexible Server (Burstable B1ms, 32 GB, SSL required)
- Azure Cache for Redis (Basic C0, TLS 1.2)
- Azure Container Registry (Basic SKU, admin enabled)

#### Render Deployment (Free Tier)
| File | Purpose |
|------|---------|
| `render.yaml` | Blueprint spec: web service + worker + PostgreSQL database |
| `build.sh` | Build script: install deps → collectstatic → migrate |
| `Procfile` | Process types: web (Daphne), worker (Celery), beat (Celery Beat) |

#### GitHub Actions CI/CD
| Workflow | Trigger | Pipeline |
|----------|---------|----------|
| `.github/workflows/ci.yml` | Push to main/develop, PRs | Lint → Test (PostgreSQL + Redis) → Docker build |
| `.github/workflows/deploy-azure.yml` | Push to main, manual dispatch | Build → Push to ACR → Deploy to App Service → Health check |

#### Health Check Endpoint
- `GET /api/health/` — Returns `{"status": "healthy", "version": "2.0.0", "database": "connected"}`
- Returns 503 if database unreachable
- Used by Docker HEALTHCHECK, Azure App Service, and Render

#### Settings Hardening
- **Database**: Auto-detects SQLite (dev) vs PostgreSQL (prod) from `DATABASE_URL`
- **Persistent connections**: `CONN_MAX_AGE=600` in production, health checks enabled
- **Environment detection**: `DEPLOY_ENV` variable (`development` / `staging` / `production`)
- **Container logging**: `CONTAINER=true` switches to stdout-only (no file handlers) — optimal for Azure Log Analytics / Docker
- **Browsable API**: Disabled in production (`DEBUG=False`)
- **Deployment check**: `python manage.py check --deploy` passes (only dev SECRET_KEY warning)

#### Makefile Additions
- `make docker-build` / `docker-up` / `docker-down` / `docker-logs` / `docker-shell` / `docker-clean`
- `make azure-infra` / `check-deploy` / `celery-worker` / `celery-beat`

#### Documentation
- Created `DEPLOYMENT.md` — Complete deployment guide with Azure (3 options), Render, Docker, and CI/CD instructions

### Phase 5: Comprehensive Testing — COMPLETED ✅
- **4 Mar 2026** → Full test suite across all 6 apps + core

#### Test Coverage Summary
- **198 tests total**, all passing
- Run command: `DATABASE_URL='sqlite:///db.sqlite3' python manage.py test --verbosity=2`

#### Test Files Created / Updated

| App | File | Tests | Coverage |
|-----|------|-------|----------|
| `hospitality_group` | `tests.py` | 33 | Models (Brand, Outlet, UserProfile), Permissions (IsOutletUser, IsManagerOrReadOnly, IsManager), Auth API (register, login, refresh, profile, change-password), Brand CRUD, Outlet CRUD, Unauth access |
| `order_engine` | `tests/__init__.py` | 18 | Models (OrderTicket, PaymentLog), Status transitions (7 valid/invalid), Order API (CRUD + update_status + active), Payment API |
| `order_engine` | `tests/test_table_status.py` | 11 | Signal-based table status (pre-existing, preserved) |
| `layout_twin` | `tests.py` | 16 | Models (ServiceNode, ServiceFlow), Node API (CRUD + update_status + by_outlet), Flow API (CRUD + graph) |
| `predictive_core` | `tests/__init__.py` | 19 | Models (SalesData, InventoryItem, StaffSchedule), is_low_stock property, Sales API (CRUD + trends + hourly_pattern), Inventory API (CRUD + low_stock), Schedule API |
| `predictive_core` | `tests/test_ml_predictions.py` | 10 | ML prediction endpoints (busy-hours, footfall, food-demand, inventory, staffing, revenue, dashboard, train) — pre-existing, updated for async train |
| `insights_hub` | `tests.py` | 14 | Models (DailySummary, PDFReport), DailySummary API (CRUD + trends), PDFReport API (list + retrieve) |
| `cloudinary_service` | `tests.py` | 14 | Serializer validation (file size, max files, resource types), Upload API (success, failure, unauth), Multi-upload API, Delete API — all Cloudinary calls mocked |
| `twinengine_core` | `tests/__init__.py` | 63 | Settings (env vars, CORS, CSRF, security, channel layer, static files, logging), Health check (200/503), Throttle scopes (5 classes), Middleware (security headers, static skip), Commands (export/import), Deployment files |

#### Bug Fixes Discovered by Tests
- **RegisterView**: Fixed `validated_data['user']['username']` → `validated_data['username']` (serializer puts fields at top-level, not nested)
- **RegisterView**: Removed non-existent `is_active` field from `UserProfile.objects.create()`
- **RegisterView**: Added username uniqueness check before `User.objects.create_user()` to return 400 instead of IntegrityError
- **RegisterView**: Changed default role from `'STAFF'` to `'WAITER'` (valid ROLE_CHOICES value)
- **train endpoint test**: Updated to use `?sync=true` parameter for in-request execution (avoids Redis dependency in tests)

---

### Week 6: Frontend Build & Integration

- **5 Mar 2026** → **React Frontend — Complete Build & 6 Rounds of Bug Fixes / Feature Enhancements**

#### Full Frontend Built from Scratch (React 19 + Vite 7)
- 8 pages: Login, Dashboard, OutletLayout, Floor, Orders, Predictions, Inventory, Reports
- API service layer (`src/services/api.js`) with JWT auth, auto-refresh, Axios interceptors
- WebSocket hook for real-time floor updates
- Role-based access control via `AuthContext` with `ROLES` constant and `RoleRoute` component
- Vite proxy config: `/api` → Django backend, `/ws` → WebSocket

#### Role-Based Architecture
- **AuthContext** (`src/utils/AuthContext.jsx`): JWT login/logout, role getter, `hasRole()` helper
- **RoleRoute** component in `App.jsx`: restricts routes by role
- **OutletLayout**: role-specific navigation tabs per role
- 5 roles fully implemented: MANAGER, WAITER, CHEF, HOST, CASHIER

| Role | Pages | Capabilities |
|------|-------|-------------|
| MANAGER | Floor, Orders, Predictions, Inventory, Reports | Full access, lifecycle buttons, create orders, payment management |
| WAITER | Floor, Orders | Read-only on orders, view floor layout |
| CHEF | Orders, Inventory | Kitchen card view, inventory CRUD (add/remove items) |
| HOST | Floor | Table management, staff assignment, 4 table statuses |
| CASHIER | Orders | Free status transitions (any→any), create orders, payment toggle |

#### UI/UX — Professional CSS Overhaul
- ~1100+ lines of custom CSS (`index.css`)
- CSS custom properties for theming (colors, shadows, radius, spacing)
- Responsive grid layouts, data tables, card grids
- Color-coded status badges (orders, tables, payments)
- Professional profile dropdown with role badge + logout
- Empty states, loading states, error handling throughout

#### Round 1 Bug Fixes
- Cashier order action buttons (status dropdown with "Go" button)
- Host/Manager table status update flow
- Host staff visibility on floor page

#### Round 2 — UI Overhaul
- Optimistic table status updates (instant visual feedback)
- Professional CSS rewrite (full design system)
- Cashier dropdown for status changes
- Host staff editing capability

#### Round 3 — Feature Enhancement
- Host gets full 4-status options (BLUE/GREEN/YELLOW/RED)
- Expandable staff management section on floor page
- Fixed WebSocket connection badge ("Offline" → "Connecting...")
- Cashier gets ALL status options in dropdown
- Add new order functionality for Cashier/Manager
- Chef gets add/remove inventory items capability
- Professional profile dropdown + logout

#### Round 4 — Role Refinement
- Waiter made read-only on orders (no edit/create)
- Chef given access to Orders page (sees active orders, auto-refresh)
- Cashier create order form shows only available (BLUE) tables
- Backend switched to full `OrderTicketSerializer` for list view

#### Round 5 — Order Completion, Chef Cards, Payment System
- Table auto-marks available (BLUE) on order completion across all portals
- Chef portal: card-based kitchen display with status bars, elapsed time, urgency indicators
- Cashier status transitions relaxed: any status → any other status
- Payment system: separate Done/Pending toggle independent of order status
- FloorPage: 20s auto-refresh interval for table status sync

#### Round 6 — Critical Bug Fixes (Payment & Chef View)

**Bug Fix: Payment auto-completing orders**
- **Root cause**: `PaymentLogViewSet.perform_create()` was forcing `status='SUCCESS'` on every new payment AND auto-marking the order `COMPLETED` when total_paid ≥ order total
- **Fix**: Stripped auto-complete logic — `perform_create()` now just calls `serializer.save()`. Payments default to `PENDING`. Order status and payment status are now fully independent
- **File**: `apps/order_engine/views.py`

**Bug Fix: Chef portal showing empty screen**
- **Root cause**: Client-side filter `data.filter(o => ACTIVE_STATUSES.includes(o.status))` was removing ALL orders because every existing order had been auto-completed by the payment bug above
- **Fix**: Removed aggressive client-side filtering. Chef view now shows two sections:
  - 🔥 **Active Orders** (PLACED/PREPARING/READY/SERVED) — shown prominently at top
  - 📋 **Past Orders** (COMPLETED/CANCELLED) — shown below at 60% opacity
- Filter dropdown now includes all statuses (not just active)
- Chef default landing page changed from `inventory` → `orders`
- Added `console.error` logging to `fetchOrders`/`fetchPayments` (was silently swallowing errors)
- Removed invalid `order__table__outlet` filter param from `fetchPayments` (not in backend `filterset_fields`)
- **Files**: `src/pages/OrdersPage.jsx`, `src/pages/DashboardPage.jsx`

#### Frontend File Summary

| File | Purpose |
|------|---------|
| `src/App.jsx` | Routes with RoleRoute guards |
| `src/main.jsx` | React entry point |
| `src/index.css` | Full design system (~1100 lines) |
| `src/utils/AuthContext.jsx` | JWT auth + role management |
| `src/services/api.js` | Axios instance, all API calls, interceptors |
| `src/pages/LoginPage.jsx` | JWT login form |
| `src/pages/DashboardPage.jsx` | Outlet selector with role-based defaults |
| `src/pages/OutletLayout.jsx` | Top bar, role nav, profile dropdown, Outlet context |
| `src/pages/FloorPage.jsx` | 3D floor grid, table status, staff management, WebSocket |
| `src/pages/OrdersPage.jsx` | Orders table/cards, payment toggle, create form (~600 lines) |
| `src/pages/PredictionsPage.jsx` | ML prediction dashboard |
| `src/pages/InventoryPage.jsx` | Inventory CRUD, low stock alerts |
| `src/pages/ReportsPage.jsx` | AI report generation |