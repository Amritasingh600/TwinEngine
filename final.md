# Project Report — A Detailed Assessment of the Work That Has Been Completed

## TwinEngine Hospitality Edition: AI-Powered Digital Twin Platform

**Team Members:** Amrita Singh (Project Lead / ML Engineer), Akshat Gupta (System Architect / Full-Stack Developer)

**Mentor:** Mr. Shivanshu Upadhyay

---

## 1. Project Timeline

The development of TwinEngine Hospitality followed an 8-week milestone schedule as documented in the project's progress log. Below is a summary of the development timeline:

| Period | Phase | Key Deliverables |
|--------|-------|-----------------|
| 7–10 Feb 2026 | Ideation & Synopsis | Project concept finalized, synopsis discussed and approved with mentor |
| 11–14 Feb 2026 | Foundation Setup | Django REST Framework scaffolding, initial model definitions, ML model planning discussed with mentor |
| 21 Feb 2026 | WebSocket Integration | Real-time WebSocket consumers created for floor status and order notifications |
| 28 Feb 2026 | Architecture Transformation | All 12 Django models finalized for hospitality domain across 5 apps; database schema created |
| 1 Mar 2026 | Auth, Admin & Signals | JWT authentication system, admin panel customization with color-coded badges, table status auto-update via Django signals |
| 2 Mar 2026 | AI Pipeline & Cloudinary | Cloudinary media integration, Azure GPT-4o report generation pipeline, synthetic data generator, end-to-end pipeline testing |
| 3 Mar 2026 | ML Prediction Module | All 6 machine learning models implemented, trained, tested; 8 prediction API endpoints created |
| 4 Mar 2026 | Infrastructure Hardening | API documentation (Swagger/ReDoc), Celery background jobs, email notifications, rate limiting, security hardening, deployment configuration (Docker, Azure, Render), comprehensive test suite (198 tests) |
| 5 & 6 Mar 2026 | Frontend Build & Integration | Complete React frontend built from scratch (8 pages), 6 rounds of bug fixes and feature enhancements, WebSocket integration, role-based access control |

---

## 2. Problem Statement and Objective

Restaurants, cafes, and food service outlets operate complex systems involving table management, order flow, inventory, and staff coordination. Managers lack real-time visibility into operational bottlenecks and predictive insights for optimization. Traditional monitoring relies on manual floor checks, end-of-day logs, and historical guesswork for demand planning.

TwinEngine Hospitality addresses these challenges by creating an AI-powered digital twin platform that provides:

- Real-time order lifecycle tracking and table status visualization
- Predictive models for demand forecasting, inventory optimization, and staff scheduling
- AI-powered operational report generation
- An interactive floor interface for monitoring and managing restaurant operations
- Role-based dashboards tailored to each staff member's responsibilities

---

## 3. Backend — Architecture and Capabilities

### 3.1 Application Architecture

The backend follows a layered architecture built on Django and Django REST Framework, structured into five specialized Django applications:

| Application | Responsibility |
|-------------|---------------|
| **hospitality_group** | Multi-tenant SaaS layer managing brands, outlets, and user profiles with five role types (Manager, Waiter, Chef, Host, Cashier) |
| **layout_twin** | The core digital twin configuration engine — manages service nodes (tables, kitchen stations, bars, entry points) with 3D spatial coordinates and directional service flow paths between them |
| **order_engine** | Real-time order lifecycle tracking from placement through completion, with payment processing and automatic table status updates driven by Django signals |
| **predictive_core** | Houses all six machine learning models, sales data storage, inventory tracking, and staff scheduling — the intelligence layer of the platform |
| **insights_hub** | AI-powered reporting engine that collects operational data, sends it to Azure GPT-4o for analysis, generates professional PDF reports, and stores them on Cloudinary |

An additional utility module, **cloudinary_service**, handles all media file uploads and deletions via Cloudinary CDN.

### 3.2 Data Model Design

The platform uses 12 interconnected Django models organized across the five apps:

- **Brand and Outlet** establish a multi-tenant hierarchy where a corporate brand can manage multiple restaurant locations, each with its own configuration, seating capacity, and operating hours.
- **UserProfile** extends Django's built-in User model, linking each staff member to a specific outlet with a designated role and shift status.
- **ServiceNode** represents physical entities in the restaurant (tables, kitchen stations, bars, entry points) with 3D coordinates for spatial visualization and a color-coded status system (Blue for available, Red for occupied and waiting, Green for served, Yellow for delays exceeding 15 minutes, Grey for reserved or under maintenance).
- **ServiceFlow** defines directional paths between service nodes, modeling operational flows such as food delivery routes, dish return paths, order paths, and customer movement patterns.
- **OrderTicket** tracks the complete lifecycle of a customer order through six states (Placed, Preparing, Ready, Served, Completed, Cancelled) with timestamps, item details stored as JSON, financial totals, and computed wait time properties.
- **PaymentLog** records payment transactions linked to orders, supporting five payment methods (Cash, Card, UPI, Digital Wallet, Split Payment) with independent status tracking.
- **SalesData** stores aggregated hourly sales metrics including order counts, revenue, average ticket size, wait times, category-wise sales breakdowns, and contextual factors like day of week, holiday status, and weather conditions — serving as the primary training data source for all ML models.
- **InventoryItem** tracks ingredient and supply levels with reorder thresholds, par levels, unit costs, and expiry dates, enabling predictive restocking alerts.
- **StaffSchedule** manages staff shift assignments with check-in/check-out tracking and an AI suggestion flag indicating whether the schedule was recommended by the staffing optimization model.
- **DailySummary** aggregates daily operational metrics (revenue, orders, guests, tips, delayed order counts) used for trend analysis and report generation.
- **PDFReport** stores metadata and Cloudinary URLs for generated reports, tracking their generation status and the AI model used.

### 3.3 Authentication and Authorization

The platform implements JWT (JSON Web Token) authentication using djangorestframework-simplejwt with the following configuration:

- Access tokens expire after 1 hour, refresh tokens after 7 days
- Token rotation is enabled — each refresh generates a new refresh token for security
- Six authentication endpoints handle login, token refresh, token verification, user registration with automatic profile creation, profile retrieval and updates, and secure password changes
- Four custom permission classes enforce role-based access control: outlet-level data isolation, manager-only access for sensitive operations, manager-edit with staff-read-only access, and combined staff-manager access
- Brute-force protection via django-axes locks accounts after 5 failed login attempts for 30 minutes

### 3.4 Real-Time Communication (WebSockets)

Django Channels powers two WebSocket consumers that deliver real-time updates to connected clients:

- **FloorConsumer** broadcasts table status changes to all clients monitoring an outlet's floor layout. When a table's status changes (via order lifecycle signals or manual updates), connected clients receive immediate notifications without polling.
- **OrderConsumer** streams order lifecycle events — new orders, status updates, and completions — to all clients monitoring an outlet's orders. This enables the chef's kitchen display, the cashier's payment view, and the manager's oversight dashboard to stay synchronized in real time.

The WebSocket infrastructure uses Django Channels with an in-memory channel layer for local development and Redis-backed channel layers for production, ensuring the system scales across multiple server instances.

### 3.5 Table Status Auto-Update Logic

Django signals (pre_save and post_save on OrderTicket) automate table color changes based on the order lifecycle:

- When an order is placed, being prepared, or ready for pickup, the associated table turns Yellow (waiting)
- When an order is served, the table turns Green (delivered)
- When an order is completed or cancelled, the table turns Blue (available) — but only if no other active orders exist for that table
- A management command periodically checks for orders exceeding a 15-minute wait threshold and marks those tables Red (needs attention)

Status transition validation ensures orders follow the correct lifecycle path (Placed → Preparing → Ready → Served → Completed), while allowing cancellation from any state.

### 3.6 Machine Learning Prediction Module

Six machine learning models form the predictive intelligence layer of the platform. All models are implemented using scikit-learn and follow a consistent pattern: they train on outlet-specific historical data stored in the SalesData, InventoryItem, and StaffSchedule models, serialize trained models as joblib files, and provide predictions through a unified PredictionService facade.

#### Model 1: Busy Hours Predictor
- **Algorithm:** RandomForestClassifier
- **Purpose:** Predicts the expected order volume for each hour of the day on a given date
- **Training Data:** Historical SalesData records — hour of day, day of week, holiday status, with engineered features including previous week's same-hour orders and 7-day rolling averages
- **Usefulness:** Enables managers to anticipate peak hours and prepare kitchen capacity, staffing levels, and inventory accordingly
- **Evaluation:** Trained and tested with full cross-validation metrics; gracefully falls back to historical averages when training data is insufficient (fewer than 14 days)

#### Model 2: Footfall Forecaster
- **Algorithm:** GradientBoostingRegressor
- **Purpose:** Forecasts the expected number of guests per hour for a given date
- **Training Data:** SalesData and DailySummary records — total guests, average party size, hourly patterns, day-of-week seasonality
- **Usefulness:** Drives table allocation planning, waitlist management, and reservation capacity decisions. Directly informs the staffing optimizer
- **Evaluation:** Shares feature engineering infrastructure with the Busy Hours Predictor, targeting guest count instead of order volume

#### Model 3: Food Demand Predictor
- **Algorithm:** RandomForestRegressor
- **Purpose:** Predicts demand per food category (Main Course, Starters, Beverages, Desserts) and identifies top-selling items for a given date
- **Training Data:** Category-wise sales breakdowns from the SalesData JSON fields, combined with temporal features
- **Usefulness:** Supports kitchen preparation planning — which ingredients to prep and in what quantities. Helps prevent food waste and ingredient stockouts
- **Evaluation:** Trains separate sub-models per category to capture category-specific demand patterns

#### Model 4: Inventory Depletion Predictor
- **Algorithm:** Rule-based with linear projection
- **Purpose:** Calculates days until each inventory item runs out and generates restocking urgency alerts (Critical, High, Moderate, OK)
- **Input Data:** Current inventory quantities, reorder thresholds, par levels, and daily consumption rates derived from order item analysis
- **Usefulness:** Prevents mid-service stockouts by providing automated purchase order suggestions. Includes expiry date warnings for perishable items
- **Evaluation:** Purely arithmetic — reliable even with minimal historical data. Suggested reorder quantities factor in daily consumption rate and lead time

#### Model 5: Staffing Optimizer
- **Algorithm:** RandomForestRegressor enhanced with ratio-based rules
- **Purpose:** Recommends the optimal number of waiters and chefs per shift (Morning, Afternoon, Night) based on predicted demand
- **Input Data:** Outputs from the Busy Hours and Footfall models, historical staff counts, outlet seating capacity, and delayed order history
- **Usefulness:** Balances the cost of overstaffing (wasted payroll) against the customer experience impact of understaffing (long waits, poor reviews). Provides per-shift cost estimates
- **Evaluation:** Calibrated using ratio rules (1 waiter per 4–5 active tables, 1 chef per 12–15 orders/hour) and refined by historical performance data from days with low delay counts

#### Model 6: Revenue Forecaster
- **Algorithm:** GradientBoostingRegressor
- **Purpose:** Predicts next-day and next-week revenue for an outlet
- **Training Data:** Historical revenue data from DailySummary records, with features including day-of-week patterns, previous day and previous week same-day revenue, and 7-day and 30-day rolling averages
- **Usefulness:** Supports cash flow planning, daily target setting, and performance benchmarking across outlets
- **Evaluation:** Captures day-of-week seasonality and trends; falls back to a weighted average (70% same-day last week + 30% recent 7-day average) when training data is sparse

#### Training Infrastructure

- A management command (`train_models`) trains all six models for a specified outlet, loading historical data, engineering features, fitting scikit-learn pipelines, evaluating performance, and serializing trained models as joblib files
- Each outlet gets its own set of trained model files, recognizing that different restaurant types (fine dining versus casual cafe) exhibit different operational patterns
- The PredictionService facade provides a single entry point for all prediction views, keeping the API layer clean
- All models include graceful fallbacks — they return reasonable estimates based on historical averages when untrained or when data is insufficient

#### Prediction API Endpoints

Eight REST API endpoints expose the ML predictions: individual endpoints for busy hours, footfall, food demand, inventory alerts, staffing recommendations, and revenue forecasts; a combined dashboard endpoint that aggregates all predictions; and a training endpoint that triggers model retraining for an outlet.

### 3.7 AI Report Generation Pipeline

The report generation pipeline follows a five-step process:

1. **Data Collection:** A dedicated service queries all relevant models (OrderTicket, PaymentLog, ServiceNode, InventoryItem, StaffSchedule, SalesData) for the specified outlet and date range, aggregating metrics using Django ORM operations (Sum, Avg, Count)

2. **AI Analysis:** The collected data is sent to Azure GPT-4o with a structured prompt requesting an executive summary, data-driven insights, and actionable recommendations. If the Azure OpenAI service is unavailable, a local fallback analysis engine generates the report content using rule-based logic

3. **PDF Generation:** ReportLab builds a professional PDF document containing a header with outlet name and date range, a key metrics table (revenue, orders, average ticket size, guests, average wait time), order and payment breakdowns, low stock alerts with highlighting, the executive summary from GPT-4o, and numbered lists of insights and recommendations

4. **Cloud Storage:** The generated PDF is uploaded to Cloudinary via the CloudinaryUploadService, returning a permanent download URL

5. **Notification:** Upon completion, an email notification with the report download link is sent to the brand's contact email address

The pipeline supports both synchronous execution (for immediate results) and asynchronous processing via Celery (for background generation with task status polling).

### 3.8 Redis and Celery — Background Processing

Redis serves two critical roles in the platform:

- **Message Broker for Celery:** Redis acts as the task queue broker, receiving background job requests and distributing them to Celery workers for processing
- **Channel Layer for WebSockets:** In production, Redis backs Django Channels' channel layer, enabling WebSocket message distribution across multiple server instances

Six Celery background tasks handle time-intensive or scheduled operations:

| Task | Purpose | Schedule |
|------|---------|----------|
| Train models for a single outlet | Retrains all 6 ML models using the latest historical data | On-demand or nightly at 02:00 |
| Train all outlets | Iterates through all active outlets and triggers model retraining | Nightly cron at 02:00 |
| Send inventory alerts for an outlet | Emails a low-stock alert listing items below their reorder threshold | On-demand or morning at 07:00 |
| Send inventory alerts for all outlets | Sweeps all outlets for low-stock items and sends consolidated alerts | Morning cron at 07:00 |
| Generate report (async) | Runs the complete 5-step report pipeline in the background | On-demand |
| Email report link | Sends a notification email with the completed report's download URL | Triggered on report completion |

Task results are stored in PostgreSQL via django-celery-results, and periodic schedules are managed through Django Admin via django-celery-beat's DatabaseScheduler. A task status polling endpoint allows the frontend to track background job progress.

### 3.9 Email Notification System

The platform integrates with Mailtrap SMTP for email delivery, using two professionally designed HTML email templates:

- **Inventory Alert Email:** Displays a formatted table of inventory items that have fallen below their reorder thresholds, grouped by category with current quantity and reorder point for each item
- **Report Ready Email:** Notifies stakeholders when a PDF report has been generated, including a direct download link to the Cloudinary-hosted file

### 3.10 API Documentation and Schema

All API endpoints are documented using drf-spectacular, which generates an OpenAPI 3.0 schema. Every view across all six apps is decorated with schema annotations, resulting in 71 documented paths and 120 operations. Interactive documentation is available via Swagger UI and ReDoc, allowing developers to explore and test all endpoints directly from the browser.

### 3.11 Rate Limiting and Security

Seven throttling scopes protect the API from abuse:

| Scope | Rate | Protected Endpoints |
|-------|------|-------------------|
| Anonymous requests | 30 per minute | All unauthenticated endpoints |
| Authenticated requests | 120 per minute | All authenticated endpoints |
| Authentication operations | 10 per minute | Login, registration, password change |
| Prediction queries | 60 per minute | All ML prediction endpoints |
| Report generation | 10 per minute | Report pipeline |
| File uploads | 20 per minute | Cloudinary upload/delete operations |
| Model training | 5 per minute | ML model retraining |

Additional security measures include:

- Security headers on every response (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy)
- Audit logging middleware that records user, method, path, status code, response duration, and client IP to a rotating log file
- Password minimum length of 10 characters
- Session timeout of 2 hours with browser-close expiry
- Upload size limit of 10 MB
- Production hardening with HTTPS/HSTS enforcement, secure cookies, and proxy SSL header support

### 3.12 Testing

A comprehensive test suite of 198 tests covers all backend components:

- Model validation and computed properties across all 12 models
- API endpoint CRUD operations, filtering, and edge cases for all five apps
- Authentication flows including registration, login, token refresh, profile management, and password changes
- Permission classes verifying role-based access control
- Signal-based table status transitions (11 dedicated tests)
- Order status transition validation (valid and invalid paths)
- Cloudinary upload/delete operations (mocked)
- Configuration tests covering environment variables, CORS, CSRF, security settings, channel layers, static files, logging, export/import commands, and deployment file presence
- ML prediction endpoint responses and training triggers

---

## 4. Frontend — Architecture and Capabilities

### 4.1 Technology Stack

The frontend is a single-page application built with React 19 and Vite 7, using:

- **React Router** for client-side routing with protected and role-restricted routes
- **Axios** for HTTP communication with automatic JWT attachment, token auto-refresh on 401 responses, and redirect to login on authentication failure
- **recharts** for data visualization (bar charts, line charts, area charts, pie charts)
- **react-hot-toast** for non-blocking toast notifications replacing native browser alerts
- **WebSocket hooks** for real-time floor and order updates

### 4.2 Role-Based Access Control

After login, the authenticated user's role (fetched from the profile endpoint) determines which pages and capabilities they can access. The frontend enforces this through a RoleRoute component that wraps protected routes:

| Role | Accessible Pages | Key Capabilities |
|------|-----------------|-----------------|
| **Manager** | Floor, Orders, Predictions, Inventory, Reports, Schedule | Full access to all features — order lifecycle management, payment handling, ML predictions, report generation, staff scheduling |
| **Waiter** | Floor, Orders | View floor layout and orders in read-only mode |
| **Chef** | Orders, Inventory | Kitchen card view with order status advancement (Placed → Preparing, Preparing → Ready), inventory add/remove |
| **Host** | Floor | Table management with four status options, staff assignment and shift toggling |
| **Cashier** | Orders | Unrestricted order status transitions, order creation, payment toggle |

### 4.3 Page Components

**Login Page:** Username and password form with error handling for invalid credentials and locked accounts. On successful authentication, JWT tokens are stored and the user is redirected to their role-appropriate landing page.

**Dashboard Page:** Displays a welcome banner with the user's name and role, followed by outlet cards that link to the appropriate section based on the user's role. Each role has a configured default landing page.

**Outlet Layout:** The navigation shell that wraps all outlet-specific pages. Provides a top navigation bar with role-specific tabs, a profile dropdown showing role badge and logout option, and an outlet context provider that makes the current outlet ID available to all child pages.

**Floor Page:** Renders the restaurant floor as a color-coded grid of table nodes. Each table displays its name, capacity, current status color, and any active order count. Managers and Hosts can click tables to update their status. Staff members are listed with shift toggle buttons. A WebSocket connection provides real-time status updates, with a visual indicator showing whether the live connection is active. A 20-second polling fallback ensures data freshness if the WebSocket connection drops.

**Orders Page:** The most complex page, rendering four distinct interfaces based on the user's role:
- Manager view: Full order table with lifecycle status buttons, payment management, and order creation forms
- Chef view: Card-based kitchen display showing active orders with elapsed time indicators and urgency highlighting. Action buttons allow advancing orders from Placed to Preparing and from Preparing to Ready. Only today's orders are shown.
- Cashier view: Status dropdown allowing unrestricted transitions, order creation with available-table filtering, and independent payment status toggling
- Waiter view: Read-only order listing

The page connects to the Order WebSocket for real-time updates, with toast notifications for new orders, status changes, and completions.

**Predictions Page:** Fetches all six ML prediction endpoints in parallel and displays the results using four chart types:
- Bar charts for hourly order volume and food demand by category
- Line charts for revenue forecasts and footfall trends
- Area charts for combined demand visualization
- Pie charts for order distribution breakdowns

Summary cards display key metrics, and staffing recommendations are presented in a shift-based table with waiter and chef counts.

**Inventory Page:** Provides a complete CRUD interface for inventory items with inline quantity editing, an add-item form supporting six inventory categories and five unit types, visual highlighting for items below their reorder threshold, and delete confirmation dialogs.

**Reports Page:** Allows managers to generate AI-powered reports by selecting a report type (Daily, Weekly, Monthly) and date range. The generated report displays the GPT-4o executive summary, numbered insights and recommendations, and a link to download the PDF from Cloudinary. A report history table lists previously generated reports with expand/collapse functionality, delete capability, and direct PDF download links.

**Schedule Page:** A three-tab interface for staff schedule management:
- Today's Schedule tab showing current shifts with check-in and check-out buttons
- All Schedules tab displaying the complete schedule history
- Create Schedule tab for adding new shift assignments

### 4.4 Real-Time WebSocket Integration

Two custom React hooks manage WebSocket connections:

- **useFloorSocket:** Connects to the floor channel for the current outlet, receiving table status updates, floor state snapshots, and individual node status change events. Updates the floor grid in real time without page refreshes.

- **useOrderSocket:** Connects to the order channel for the current outlet, handling four event types — active orders list (initial state), order created, order updated, and order completed. Triggers toast notifications for each event type so staff are immediately aware of changes.

Both hooks implement reconnection logic compatible with React 19's Strict Mode, which double-invokes effects during development. An active flag pattern ensures that cleanup functions do not prematurely close connections that are still establishing.

### 4.5 Data Visualization

The Predictions page leverages recharts to transform raw ML prediction data into interactive charts:

- **Hourly Demand Bar Chart:** Visualizes predicted order volume across all hours of the day, making peak hours immediately identifiable
- **Revenue Forecast Line Chart:** Plots daily revenue predictions over the coming week, enabling financial planning
- **Footfall Area Chart:** Shows expected guest counts throughout the day, helping with capacity planning
- **Food Category Pie Chart:** Breaks down predicted demand by food category, supporting kitchen prep decisions

All charts are responsive and include tooltips for precise value inspection.

### 4.6 Notification System

Toast notifications (via react-hot-toast) replace all native browser alerts throughout the application, providing:

- Success confirmations for CRUD operations (order created, inventory updated, report generated)
- Error messages for API failures with descriptive text
- Real-time WebSocket event notifications (new order placed, order status changed, order completed)
- Non-blocking display that does not interrupt the user's workflow

### 4.7 Loading States and Error Handling

CSS-animated spinners provide visual feedback during API calls across all pages. Each page component manages loading state independently, showing a centered spinner during data fetches and an appropriate empty state message when no data is available. API errors are caught and displayed as toast notifications rather than allowing pages to break.

---

## 5. Cloud Deployment Compatibility

The platform is designed for cloud-native deployment with configurations prepared for three deployment targets:

### 5.1 Azure App Service (Primary Target)

- **Infrastructure as Code:** A Bicep template provisions the complete Azure infrastructure — App Service Plan with Linux container support, Web App with WebSocket enabled, PostgreSQL Flexible Server (Burstable B1ms tier with SSL), Azure Cache for Redis (Basic C0 with TLS 1.2), and Azure Container Registry
- **One-Command Deployment:** A deploy script automates the entire process: creating a resource group, deploying infrastructure via Bicep, building and pushing a Docker image to ACR, configuring the web app with environment variables, and restarting the service
- **CI/CD Pipeline:** A GitHub Actions workflow triggers on pushes to the main branch, running linting and tests, building the Docker image, pushing to ACR, deploying to App Service, and verifying the health check endpoint

### 5.2 Render (Free Tier Alternative)

- A Render Blueprint specification (render.yaml) defines three services: web (Daphne ASGI server), worker (Celery), and a PostgreSQL database
- A build script handles dependency installation, static file collection, and database migrations
- A Procfile defines the process types for Daphne, Celery worker, and Celery Beat

### 5.3 Docker (Local and Self-Hosted)

- A multi-stage Dockerfile (builder + runtime) uses Python 3.12-slim, creates a non-root user for security, and includes a health check
- A universal entrypoint script supports four modes: web server (Daphne ASGI), WSGI server (Gunicorn), Celery worker, and Celery Beat scheduler
- Docker Compose orchestrates the full local stack: PostgreSQL 16, Redis 7, Django web server, Celery worker, and Celery Beat — all with proper networking and health checks
- Makefile targets simplify Docker operations: build, up, down, logs, shell, and clean

### 5.4 Environment and Configuration Management

- All sensitive configuration is externalized through environment variables, with a documented template (.env.example) covering 16 configuration keys
- The settings module auto-detects the deployment environment: SQLite for development, PostgreSQL (via DATABASE_URL) for production
- Channel layers auto-switch between in-memory (development) and Redis-backed (production)
- Static files are served via WhiteNoise with compressed, cache-busted manifests suitable for CDN delivery
- Structured logging adapts to the environment — file-based rotation for VMs, stdout-only for containers (compatible with Azure Log Analytics and Docker log aggregation)
- A health check endpoint validates database connectivity and returns the application version, used by Docker, Azure App Service, and Render for automated health monitoring

---

## 6. Summary

TwinEngine Hospitality is a complete, production-ready digital twin platform for restaurant operations. The backend provides a robust API layer with 71 documented endpoints, real-time WebSocket communication, six machine learning models for predictive analytics, an AI-powered report generation pipeline leveraging Azure GPT-4o, and background task processing via Celery and Redis. The frontend delivers a role-based, real-time dashboard experience with interactive data visualizations, live WebSocket updates, and a professional notification system. The entire platform is containerized and deployment-ready for Azure App Service, Render, or any Docker-compatible hosting environment, with comprehensive test coverage of 198 backend tests ensuring reliability across all components.
