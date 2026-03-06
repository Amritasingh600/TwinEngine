# TwinEngine — Frontend Rebuild Plan

> **Date:** 5 March 2026
> **Status:** Planning
> **Backend Endpoints Available:** 79 (76 REST + 3 WebSocket)
> **Current Frontend Coverage:** ~20 endpoints (25%)
> **Target Coverage:** 76 endpoints (96%)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Role-Based Portal System](#2-role-based-portal-system)
3. [Portal 1: Login & Auth](#3-portal-1-login--auth)
4. [Portal 2: Admin / Data Simulator](#4-portal-2-admin--data-simulator)
5. [Portal 3: Host / Receptionist](#5-portal-3-host--receptionist)
6. [Portal 4: Waiter](#6-portal-4-waiter)
7. [Portal 5: Chef / Kitchen Display](#7-portal-5-chef--kitchen-display)
8. [Portal 6: Inventory & Payments Manager](#8-portal-6-inventory--payments-manager)
9. [Portal 7: General Manager](#9-portal-7-general-manager)
10. [WebSocket Integration](#10-websocket-integration)
11. [Endpoint Coverage Map](#11-endpoint-coverage-map)
12. [Tech Stack](#12-tech-stack)
13. [File Structure](#13-file-structure)
14. [Implementation Phases](#14-implementation-phases)

---

## 1. Architecture Overview

### Core Concept

TwinEngine frontend is a **role-based single-page application**. After login, the user's `role` field (from `GET /api/auth/me/`) determines which portal they see. Each portal is a self-contained dashboard tailored to that role's responsibilities.

### Data Flow

```
User logs in → JWT stored → Profile fetched → role extracted
                                                    │
                    ┌───────────────────────────────┤
                    ▼                               ▼
              MANAGER role?                    Other roles?
              ┌─────┴─────┐                        │
              │ is_superuser│                       ▼
              │  = true?    │              Route to role portal
              └─────┬─────┘              (HOST/WAITER/CHEF/CASHIER)
                yes │ no
                 ▼    ▼
             Admin  Manager
             Portal Portal
```

### Shared Infrastructure

- **AuthContext** — JWT management, auto-refresh, role detection
- **RoleRouter** — After login, redirects to correct portal based on `user.role`
- **WebSocket Manager** — Centralized hooks for Floor + Order real-time channels
- **API Service Layer** — All 76 endpoint functions in organized modules
- **Toast Notifications** — Real-time alerts from WebSocket events

---

## 2. Role-Based Portal System

| Role | Portal | Primary Responsibility | Color Theme |
|------|--------|----------------------|-------------|
| `MANAGER` (superuser) | Admin / Data Simulator | System config, synthetic data, CRUD management | Purple |
| `HOST` | Receptionist | Customer check-in/out, table assignment | Teal |
| `WAITER` | Waiter | Place orders, serve food, manage assigned tables | Blue |
| `CHEF` | Kitchen Display | Cook queue, mark orders ready | Orange |
| `CASHIER` | Inventory & Payments | Stock management, payment processing | Green |
| `MANAGER` | General Manager | Analytics, ML predictions, reports, oversight | Indigo |

### Role Detection Logic

```
After login:
  1. Fetch GET /api/auth/me/
  2. Read response.role and response.user.is_superuser
  3. Route:
     - role === 'MANAGER' && is_superuser → /admin
     - role === 'MANAGER' → /manager
     - role === 'HOST' → /host
     - role === 'WAITER' → /waiter
     - role === 'CHEF' → /chef
     - role === 'CASHIER' → /inventory
```

---

## 3. Portal 1: Login & Auth

### Pages

#### 4.1 Login Page (`/login`)
- Username + password form
- "Remember me" checkbox
- Error display for invalid credentials / locked accounts (django-axes)
- On success → redirect to role-specific portal

#### 4.2 Register Page (`/register`) — Admin only link
- Full staff registration form
- Fields: username, email, password, first_name, last_name, outlet (dropdown), role (dropdown), phone

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/token/` | POST | Login (get JWT pair) |
| `/api/auth/token/refresh/` | POST | Silent refresh (interceptor) |
| `/api/auth/token/verify/` | POST | Verify token validity |
| `/api/auth/me/` | GET | Fetch logged-in user profile |
| `/api/auth/register/` | POST | Register new staff |
| `/api/auth/change-password/` | POST | Change password |

### User Flow
```
1. User enters credentials
2. POST /api/auth/token/ → receive {access, refresh}
3. Store tokens in localStorage
4. GET /api/auth/me/ → receive {role, outlet, user{...}}
5. RoleRouter redirects based on role
```

---

## 4. Portal 2: Admin / Data Simulator

> **Access:** MANAGER with superuser flag
> **Route:** `/admin/*`
> **Purpose:** System administration, CRUD management for all entities, synthetic data injection for testing

### Pages

#### 5.1 Admin Dashboard (`/admin`)
- System overview cards: total brands, outlets, staff, nodes, orders today
- Quick links to each management section
- System health indicator (`GET /api/health/`)

#### 5.2 Brand Management (`/admin/brands`)
- Table listing all brands with outlet count
- Create / Edit / Delete brand modal
- Columns: Name, Corporate ID, Contact Email, Subscription Tier, Outlets Count

#### 5.3 Outlet Management (`/admin/outlets`)
- Table listing all outlets across brands
- Create / Edit / Delete outlet modal
- Fields: brand (dropdown), name, address, city, seating_capacity, opening_time, closing_time
- Toggle is_active status

#### 5.4 Staff Management (`/admin/staff`)
- Table listing all staff with role, outlet, on-shift status
- Register new staff (inline form or modal)
- Edit profile / Change password for any user
- Filter by outlet, role, on-shift status

#### 5.5 Floor Designer (`/admin/floor`)
- Outlet selector dropdown
- Grid/canvas showing all service nodes with positions
- Create new node: name, type (TABLE/KITCHEN/WASH/BAR/ENTRY), position (x,y,z), capacity
- Edit/delete existing nodes
- Create service flows: source → target, flow_type selector
- View flow graph visualization

#### 5.6 Data Simulator (`/admin/simulator`)
- **Purpose:** Bulk inject synthetic data for testing the entire system
- Outlet selector
- Sections:
  - **Sales Data Seeder:** date range, auto-generate hourly sales records
  - **Inventory Seeder:** auto-create inventory items with realistic quantities
  - **Schedule Seeder:** auto-create staff schedules for a date range
  - **Order Simulator:** create N orders with random items, party sizes, statuses
- Each section has its own "Generate" button + count input
- Activity log showing what was created

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health/` | GET | System health check |
| `/api/brands/` | GET | List all brands |
| `/api/brands/` | POST | Create brand |
| `/api/brands/{id}/` | GET | Get brand detail |
| `/api/brands/{id}/` | PUT/PATCH | Update brand |
| `/api/brands/{id}/` | DELETE | Delete brand |
| `/api/outlets/` | GET | List all outlets |
| `/api/outlets/` | POST | Create outlet |
| `/api/outlets/{id}/` | GET | Get outlet detail |
| `/api/outlets/{id}/` | PUT/PATCH | Update outlet |
| `/api/outlets/{id}/` | DELETE | Delete outlet |
| `/api/staff/` | GET | List all staff |
| `/api/staff/{id}/` | GET/PUT/PATCH/DELETE | Staff CRUD |
| `/api/auth/register/` | POST | Register new staff |
| `/api/auth/change-password/` | POST | Change any user's password |
| `/api/nodes/` | GET | List nodes |
| `/api/nodes/` | POST | Create node |
| `/api/nodes/{id}/` | GET/PUT/PATCH/DELETE | Node CRUD |
| `/api/flows/` | GET | List flows |
| `/api/flows/` | POST | Create flow |
| `/api/flows/{id}/` | GET/PUT/PATCH/DELETE | Flow CRUD |
| `/api/flows/graph/` | GET | Get flow graph (node-edge data) |
| `/api/sales-data/` | GET/POST | Sales data CRUD |
| `/api/inventory/` | POST | Create inventory items |
| `/api/schedules/` | POST | Create schedules |
| `/api/orders/` | POST | Create orders |
| `/api/upload/` | POST | Upload files |
| `/api/upload/multi/` | POST | Multi-file upload |
| `/api/upload/delete/` | POST | Delete file |

---

## 5. Portal 3: Host / Receptionist

> **Access:** HOST role
> **Route:** `/host/*`
> **Purpose:** Customer check-in, table assignment, seating map, customer exit

### Pages

#### 6.1 Reception Dashboard (`/host`)
- Live floor map (2D grid) showing all tables with color-coded status
  - 🔵 BLUE = Available | 🔴 RED = Occupied-Waiting | 🟢 GREEN = Served | 🟡 YELLOW = Delay | ⚫ GREY = Maintenance
- Table count summary bar: "12 Available | 5 Occupied | 2 Served | 1 Delay"
- Connected via WebSocket `/ws/floor/{outletId}/` for real-time updates

#### 6.2 Check-In Panel (sidebar or modal)
- Triggered by clicking an available (BLUE) table
- Form fields:
  - Customer name (text)
  - Party size (number, validated against table capacity)
  - Special requests (textarea, optional)
  - Assign waiter (dropdown of on-shift waiters)
- On submit:
  1. `POST /api/orders/` — create order with status PLACED
  2. Table auto-turns RED (backend signal handles this)
  3. Toast: "✅ Table-3 assigned to John (party of 4)"

#### 6.3 Active Seating List
- Table showing all currently occupied tables
- Columns: Table, Customer, Party Size, Waiter, Status, Time Seated, Wait Time
- Highlight rows where wait_time > 15 min (long wait)
- Action buttons:
  - "Flag Delay" → `POST /api/nodes/{id}/update_status/` → YELLOW
  - "Exit Customer" → `POST /api/orders/{id}/update_status/` → COMPLETED, then table → BLUE

#### 6.4 Table Status Override
- Quick toggle any table status manually
- Uses `POST /api/table/trigger/` with node_id and status
- Useful for maintenance (GREY), manual resets

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/nodes/` | GET | Fetch all tables for floor map |
| `/api/nodes/{id}/update_status/` | POST | Change table status color |
| `/api/orders/` | GET | List active orders (for seating list) |
| `/api/orders/` | POST | Create new order (check-in) |
| `/api/orders/{id}/update_status/` | POST | Complete order (check-out) |
| `/api/table/trigger/` | POST | Manual table status override |
| `/api/staff/` | GET | List on-shift waiters for assignment |
| `WS /ws/floor/{outletId}/` | — | Real-time floor updates |

### User Flow — Customer Lifecycle
```
1. Customer arrives → Host sees floor map
2. Host clicks available (BLUE) table → Check-in panel opens
3. Host fills customer name, party size, assigns waiter → Submit
4. POST /api/orders/ creates order → table turns RED automatically
5. [Waiter takes over from here]
6. When customer leaves → Host clicks "Exit Customer"
7. POST /api/orders/{id}/update_status/ → COMPLETED
8. Table turns BLUE (available again)
```

---

## 6. Portal 4: Waiter

> **Access:** WAITER role
> **Route:** `/waiter/*`
> **Purpose:** View assigned tables, take/modify orders, mark food served, manage table lifecycle

### Pages

#### 7.1 My Tables Dashboard (`/waiter`)
- Grid of assigned tables (only tables where waiter has active orders)
- Each table card shows:
  - Table name + status color badge
  - Customer name + party size
  - Order status (PLACED / PREPARING / READY / SERVED)
  - Time since order placed
  - Quick action buttons per status
- Real-time updates via WebSocket

#### 7.2 New Order Form (modal)
- Triggered from a table card or from "New Order" button
- Fields:
  - Table (dropdown of available tables or pre-selected)
  - Customer name
  - Party size
  - Items (JSON array builder):
    - Item name, quantity, price per item
    - "Add Item" button to add rows
    - Auto-calculate subtotal
  - Special requests (textarea)
  - Tax (auto-calculated or manual)
  - Total (auto-calculated)
- On submit: `POST /api/orders/`

#### 7.3 Order Detail View
- Full order info with timeline
- Status progression buttons:
  - PLACED → (wait for chef) → shown as "Waiting for Kitchen"
  - PREPARING → shown as "Kitchen is cooking"
  - READY → **"Mark Served"** button → `POST /api/orders/{id}/update_status/` → SERVED
  - SERVED → **"Complete & Bill"** button → COMPLETED
- Table status updates happen automatically via backend signals

#### 7.4 Notifications
- Real-time toasts from Order WebSocket:
  - "🍳 Order #15 is READY — Table-3" (chef marked it ready)
  - "⏰ Table-7 waiting 20 minutes!" (wait time alert from floor WS)

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/orders/` | GET | Fetch waiter's active orders |
| `/api/orders/` | POST | Create new order |
| `/api/orders/{id}/` | GET | Get single order detail |
| `/api/orders/{id}/update_status/` | POST | Progress order status |
| `/api/nodes/` | GET | Fetch tables to show floor state |
| `/api/nodes/{id}/update_status/` | POST | Update table color |
| `WS /ws/floor/{outletId}/` | — | Real-time table status |
| `WS /ws/orders/{outletId}/` | — | Real-time order updates |

### User Flow — Taking an Order
```
1. Waiter sees assigned tables on dashboard
2. Customer at Table-3 is ready to order
3. Waiter clicks Table-3 → "New Order" → fills items
4. POST /api/orders/ → order created with status PLACED
5. Order appears on Chef's Kitchen Display immediately (via WS)
6. Chef marks PREPARING → Waiter sees status change on their card
7. Chef marks READY → Waiter gets toast notification "Order READY!"
8. Waiter delivers food → clicks "Mark Served" → status = SERVED
9. Table turns GREEN (served)
10. Customer finishes → Waiter clicks "Complete" → status = COMPLETED
11. Table turns BLUE (available)
```

---

## 7. Portal 5: Chef / Kitchen Display

> **Access:** CHEF role
> **Route:** `/chef/*`
> **Purpose:** Real-time kitchen order queue, mark orders as preparing/ready

### Pages

#### 8.1 Kitchen Display System — KDS (`/chef`)
- **Full-screen, TV-optimized layout** (designed to run on a kitchen monitor)
- Split into columns:
  - **PLACED** (new orders, left column, highlighted red)
  - **PREPARING** (in progress, middle column, highlighted orange/yellow)
  - **READY** (done, right column, highlighted green, auto-clears after 60s)
- Each order card shows:
  - Table name (large font)
  - Items list with quantities
  - Special requests (highlighted)
  - Time since placed (with color escalation: green < 10min, yellow < 20min, red > 20min)
  - Action button: "Start Cooking" (PLACED→PREPARING) or "Ready!" (PREPARING→READY)
- Real-time via Order WebSocket — new orders slide in with animation
- Sound notification on new PLACED order (optional, configurable)

#### 8.2 Kitchen Stats Bar (top of KDS)
- Live metrics:
  - Orders in queue (PLACED count)
  - Currently cooking (PREPARING count)
  - Avg cook time today
  - Longest waiting order
- Fetched from `GET /api/orders/` with filters

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/orders/` | GET | Fetch PLACED + PREPARING orders |
| `/api/orders/{id}/update_status/` | POST | PLACED→PREPARING, PREPARING→READY |
| `WS /ws/orders/{outletId}/` | — | Real-time new orders + status changes |

### User Flow — Processing an Order
```
1. KDS is always open on kitchen monitor
2. New order appears in PLACED column (via WebSocket)
3. 🔔 Sound notification plays
4. Chef clicks "Start Cooking" → status = PREPARING → card moves to middle column
5. Chef finishes cooking → clicks "Ready!" → status = READY → card moves to right column
6. Waiter gets notified → picks up food → (Waiter marks SERVED)
7. READY card auto-fades after waiter picks up
```

---

## 8. Portal 6: Inventory & Payments Manager

> **Access:** CASHIER role
> **Route:** `/inventory/*`
> **Purpose:** Manage stock levels, process payments, track consumption

### Pages

#### 9.1 Inventory Dashboard (`/inventory`)
- Table of all inventory items for the outlet
- Columns: Item Name, Category, Quantity, Unit, Reorder Threshold, Par Level, Unit Cost, Expiry, Status
- Status badges: "OK" (green), "LOW" (yellow, qty ≤ threshold), "CRITICAL" (red, qty ≤ threshold/2)
- Inline edit: click quantity → edit → `PATCH /api/inventory/{id}/`
- Filter by category (PRODUCE, DAIRY, MEAT, DRY, BEVERAGE, SUPPLIES)
- Sort by quantity, name, category

#### 9.2 Restock Form (modal)
- Select item from dropdown
- Enter new quantity (adds to existing)
- Sets `last_restocked` timestamp
- `PATCH /api/inventory/{id}/` with updated quantity

#### 9.3 Add Inventory Item (`/inventory/add`)
- Form: name, category, unit, current_quantity, reorder_threshold, par_level, unit_cost, expiry_date
- `POST /api/inventory/`

#### 9.4 AI Alerts Panel (sidebar)
- Fetches `GET /api/predictions/inventory-alerts/?outlet=X`
- Shows urgency-sorted list:
  - CRITICAL: "Coffee Beans — 2 KG left, reorder 18 KG"
  - WARNING: "Cooking Oil — 5 L left, reorder 15 L"
- Each alert has a "Restock Now" button that pre-fills the restock form

#### 9.5 Payment Processing (`/inventory/payments`)
- List of recent payments with filters
- Columns: Order #, Table, Amount, Method, Status, Tip, Transaction ID, Date
- "New Payment" button → form:
  - Select order (dropdown of SERVED/COMPLETED orders)
  - Amount (pre-filled from order total)
  - Method: CASH / CARD / UPI / WALLET / SPLIT
  - Transaction ID (optional)
  - Tip amount
  - `POST /api/payments/`
- Payment status management: mark SUCCESS / FAILED / REFUNDED

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/inventory/` | GET | List all inventory items |
| `/api/inventory/` | POST | Add new item |
| `/api/inventory/{id}/` | GET | Item detail |
| `/api/inventory/{id}/` | PATCH | Update quantity / restock |
| `/api/inventory/{id}/` | DELETE | Remove item |
| `/api/predictions/inventory-alerts/` | GET | AI reorder alerts |
| `/api/payments/` | GET | List payments |
| `/api/payments/` | POST | Create payment |
| `/api/payments/{id}/` | GET/PATCH | Payment detail / update |
| `/api/orders/` | GET | Fetch orders for payment dropdown |

---

## 9. Portal 7: General Manager

> **Access:** MANAGER role (non-superuser)
> **Route:** `/manager/*`
> **Purpose:** Full oversight — analytics, ML predictions, AI reports, staff scheduling, live monitoring

### Pages

#### 10.1 Manager Dashboard (`/manager`)
- **KPI Cards Row:**
  - Today's Revenue | Orders Today | Avg Ticket Size | Active Tables | Staff On Shift
  - Data from `GET /api/summaries/` + `GET /api/orders/` + `GET /api/nodes/`
- **Live Floor Mini-Map:**
  - Compact version of floor map with table colors
  - Via WebSocket `/ws/floor/{outletId}/`
- **Active Orders Feed:**
  - Scrolling list of recent order events
  - Via WebSocket `/ws/orders/{outletId}/`
- **Quick Links:**
  - Predictions | Reports | Staff | Inventory Alerts

#### 10.2 ML Predictions Hub (`/manager/predictions`)
- Date picker (defaults to today)
- **6 Prediction Cards, each with chart:**

  **10.2.1 Busy Hours** — `GET /api/predictions/busy-hours/`
  - Bar chart: X = hour (8–23), Y = predicted orders
  - Highlight peak hour
  - Show total predicted orders

  **10.2.2 Footfall Forecast** — `GET /api/predictions/footfall/`
  - Area chart: hourly predicted guests
  - Peak guests indicator
  - Total guests for the day

  **10.2.3 Food Demand** — `GET /api/predictions/food-demand/`
  - Pie chart: revenue split by category (Mains, Starters, Beverages, etc.)
  - Table: top predicted items with order counts

  **10.2.4 Revenue Forecast** — `GET /api/predictions/revenue/`
  - Line chart: daily revenue for next 7 days
  - Confidence range ribbon (upper/lower bound)
  - Weekly total

  **10.2.5 Staffing Recommendations** — `GET /api/predictions/staffing/`
  - Table per shift (MORNING / AFTERNOON / NIGHT):
    - Recommended waiters, chefs
    - Predicted peak orders/hr
    - Reasoning text

  **10.2.6 Inventory Alerts** — `GET /api/predictions/inventory-alerts/`
  - Alert list with urgency colors
  - Suggested order quantities

- **Train Models Button:** `POST /api/predictions/train/?outlet=X`
  - Async dispatch → shows task progress via `GET /api/tasks/{task_id}/` polling
  - Shows training metrics on completion (MAE, RMSE, R²)

#### 10.3 Reports Center (`/manager/reports`)
- **Generate Report Section:**
  - Form: Report Type (DAILY/WEEKLY/MONTHLY), Start Date, End Date
  - "Generate" button → `POST /api/reports/generate/`
  - Async: shows progress spinner, polls `GET /api/tasks/{task_id}/` every 3 seconds
  - On completion: shows GPT executive summary, insights, recommendations
  - Download PDF button (Cloudinary URL)

- **Report History:**
  - Table of all generated reports
  - Columns: Type, Date Range, Status, Generated By, PDF Link, Created At
  - `GET /api/reports/`
  - Click to view full report detail: `GET /api/reports/{id}/`

- **Daily Report Lookup:**
  - Date picker → `GET /api/reports/daily/?outlet=X&date=YYYY-MM-DD`
  - Quick view of a specific day's report

#### 10.4 Daily Summaries / Analytics (`/manager/analytics`)
- **Summary Table:**
  - `GET /api/summaries/?outlet=X`
  - Columns: Date, Revenue, Orders, Avg Ticket, Guests, Peak Hour, Wait Time, Delayed, Cancelled
  - Sortable, filterable

- **Trends Charts:**
  - Line chart: Revenue over past 30 days
  - Bar chart: Orders per day
  - Data from `GET /api/sales-data/trends/?outlet=X&days=30`

- **Hourly Patterns:**
  - Heatmap or bar chart: average orders by hour of day
  - Data from `GET /api/sales-data/hourly_pattern/?outlet=X`

- **Create Summary:**
  - Manual creation form for a date
  - `POST /api/summaries/`

#### 10.5 Staff Schedule Manager (`/manager/staff`)
- **Today's Schedule:**
  - `GET /api/schedules/today/?outlet=X`
  - Cards per staff: name, role, shift, check-in/out times, status
  - "Check In" / "Check Out" buttons → `POST /api/schedules/{id}/check-in/` or `/check-out/`

- **Weekly Schedule View:**
  - Calendar grid: staff × days
  - `GET /api/schedules/?staff__outlet=X&date__gte=...&date__lte=...`

- **Create Schedule:**
  - Form: staff (dropdown), date, shift, start_time, end_time
  - `POST /api/schedules/`

- **Staff by Member:**
  - Select staff → `GET /api/schedules/by_staff/?staff_id=X`
  - View individual schedule history

- **AI Staffing Overlay:**
  - Show ML staffing recommendations alongside actual schedule
  - Highlight gaps: "AI suggests 4 waiters for AFTERNOON, you have 3 scheduled"

#### 10.6 Live Operations Monitor (`/manager/live`)
- **Full-size floor map** with real-time table colors (WebSocket)
- **Order ticker** — live feed of order events (WebSocket)
- **Wait time alerts** — popup when any table exceeds 15 min wait
- **Staff on-shift panel** — who's currently working
- Combined view for at-a-glance monitoring

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/predictions/dashboard/` | GET | All predictions combined |
| `/api/predictions/busy-hours/` | GET | Busy hours forecast |
| `/api/predictions/footfall/` | GET | Guest footfall forecast |
| `/api/predictions/food-demand/` | GET | Food category demand |
| `/api/predictions/revenue/` | GET | Revenue forecast |
| `/api/predictions/staffing/` | GET | Staffing recommendations |
| `/api/predictions/inventory-alerts/` | GET | Inventory reorder alerts |
| `/api/predictions/train/` | POST | Trigger ML model training |
| `/api/tasks/{task_id}/` | GET | Poll async task status |
| `/api/summaries/` | GET | List daily summaries |
| `/api/summaries/` | POST | Create daily summary |
| `/api/summaries/{id}/` | GET/PUT/PATCH/DELETE | Summary CRUD |
| `/api/reports/` | GET | List reports |
| `/api/reports/` | POST | (unused — use generate) |
| `/api/reports/{id}/` | GET | Report detail |
| `/api/reports/generate/` | POST | Generate AI report (async) |
| `/api/reports/daily/` | GET | Daily report lookup |
| `/api/sales-data/` | GET | Sales data list |
| `/api/sales-data/trends/` | GET | Sales trends |
| `/api/sales-data/hourly_pattern/` | GET | Hourly pattern data |
| `/api/schedules/` | GET | List schedules |
| `/api/schedules/` | POST | Create schedule |
| `/api/schedules/{id}/` | GET/PATCH | Schedule detail |
| `/api/schedules/{id}/check-in/` | POST | Record check-in |
| `/api/schedules/{id}/check-out/` | POST | Record check-out |
| `/api/schedules/today/` | GET | Today's schedules |
| `/api/schedules/by_staff/` | GET | Schedules for a staff member |
| `/api/orders/` | GET | Active orders for dashboard |
| `/api/nodes/` | GET | Floor map nodes |
| `/api/staff/` | GET | Staff list for scheduling |
| `WS /ws/floor/{outletId}/` | — | Live floor map |
| `WS /ws/orders/{outletId}/` | — | Live order feed |

---

## 10. WebSocket Integration

### Two WebSocket Channels

#### 11.1 Floor WebSocket — `/ws/floor/{outletId}/`

**Used by:** Host, Waiter, Manager portals

| Event | Direction | Payload | UI Action |
|-------|-----------|---------|-----------|
| `floor_state` | Server→Client | `{nodes: [...]}` | Initialize/replace floor map state |
| `floor_update` | Server→Client | `{node_id, status, node_name}` | Update single table color |
| `node_status_change` | Server→Client | `{node_id, old_status, new_status, timestamp}` | Update table + log event |
| `wait_time_alert` | Server→Client | `{node_id, node_name, wait_minutes, alert_level}` | Show toast warning |
| `request_update` | Client→Server | (empty) | Request full floor re-send |

#### 11.2 Order WebSocket — `/ws/orders/{outletId}/`

**Used by:** Waiter, Chef, Manager portals (currently NOT used by frontend — must implement)

| Event | Direction | Payload | UI Action |
|-------|-----------|---------|-----------|
| `active_orders` | Server→Client | `{orders: [...]}` | Initialize order list on connect |
| `order_created` | Server→Client | `{order: {...}}` | Add new order card (Chef: new queue item) |
| `order_updated` | Server→Client | `{order_id, old_status, new_status, table_id}` | Move card between columns |
| `order_completed` | Server→Client | `{order_id, table_id, total}` | Remove from active list |
| `request_orders` | Client→Server | (empty) | Request full order re-send |

### WebSocket Hooks to Build

```
useFloorSocket(outletId)     — already exists, needs minor updates
useOrderSocket(outletId)     — NEW: mirrors floor socket pattern for orders
```

---

## 11. Endpoint Coverage Map

### All 79 Endpoints → Portal Mapping

| # | Endpoint | Method | Portal(s) |
|---|----------|--------|-----------|
| **Auth (6)** | | | |
| 1 | `/api/auth/token/` | POST | Login |
| 2 | `/api/auth/token/refresh/` | POST | All (interceptor) |
| 3 | `/api/auth/token/verify/` | POST | All (on mount) |
| 4 | `/api/auth/register/` | POST | Admin |
| 5 | `/api/auth/me/` | GET | All (role detection) |
| 6 | `/api/auth/change-password/` | POST | Admin, Profile |
| **Brands (5)** | | | |
| 7 | `/api/brands/` | GET | Admin |
| 8 | `/api/brands/` | POST | Admin |
| 9 | `/api/brands/{id}/` | GET | Admin |
| 10 | `/api/brands/{id}/` | PUT/PATCH | Admin |
| 11 | `/api/brands/{id}/` | DELETE | Admin |
| **Outlets (5)** | | | |
| 12 | `/api/outlets/` | GET | Admin, Manager, Login redirect |
| 13 | `/api/outlets/` | POST | Admin |
| 14 | `/api/outlets/{id}/` | GET | Admin |
| 15 | `/api/outlets/{id}/` | PUT/PATCH | Admin |
| 16 | `/api/outlets/{id}/` | DELETE | Admin |
| **Staff (4)** | | | |
| 17 | `/api/staff/` | GET | Admin, Host, Manager |
| 18 | `/api/staff/{id}/` | GET | Admin |
| 19 | `/api/staff/{id}/` | PUT/PATCH | Admin |
| 20 | `/api/staff/{id}/` | DELETE | Admin |
| **Service Nodes (6)** | | | |
| 21 | `/api/nodes/` | GET | Host, Waiter, Admin, Manager |
| 22 | `/api/nodes/` | POST | Admin |
| 23 | `/api/nodes/{id}/` | GET | Admin |
| 24 | `/api/nodes/{id}/` | PUT/PATCH | Admin |
| 25 | `/api/nodes/{id}/` | DELETE | Admin |
| 26 | `/api/nodes/{id}/update_status/` | POST | Host, Waiter |
| **Service Flows (5)** | | | |
| 27 | `/api/flows/` | GET | Admin |
| 28 | `/api/flows/` | POST | Admin |
| 29 | `/api/flows/{id}/` | GET | Admin |
| 30 | `/api/flows/{id}/` | PUT/PATCH/DELETE | Admin |
| 31 | `/api/flows/graph/` | GET | Admin, Manager |
| **Orders (6)** | | | |
| 32 | `/api/orders/` | GET | Host, Waiter, Chef, Manager |
| 33 | `/api/orders/` | POST | Host, Waiter |
| 34 | `/api/orders/{id}/` | GET | Waiter, Manager |
| 35 | `/api/orders/{id}/` | PUT/PATCH | Waiter |
| 36 | `/api/orders/{id}/` | DELETE | Admin |
| 37 | `/api/orders/{id}/update_status/` | POST | Host, Waiter, Chef |
| **Payments (4)** | | | |
| 38 | `/api/payments/` | GET | Inventory, Manager |
| 39 | `/api/payments/` | POST | Inventory |
| 40 | `/api/payments/{id}/` | GET | Inventory |
| 41 | `/api/payments/{id}/` | PATCH | Inventory |
| **Table Trigger (1)** | | | |
| 42 | `/api/table/trigger/` | POST | Host |
| **Sales Data (4)** | | | |
| 43 | `/api/sales-data/` | GET | Manager, Admin |
| 44 | `/api/sales-data/` | POST | Admin (simulator) |
| 45 | `/api/sales-data/trends/` | GET | Manager |
| 46 | `/api/sales-data/hourly_pattern/` | GET | Manager |
| **Inventory (5)** | | | |
| 47 | `/api/inventory/` | GET | Inventory, Manager |
| 48 | `/api/inventory/` | POST | Inventory, Admin |
| 49 | `/api/inventory/{id}/` | GET | Inventory |
| 50 | `/api/inventory/{id}/` | PATCH | Inventory |
| 51 | `/api/inventory/{id}/` | DELETE | Inventory, Admin |
| **Schedules (7)** | | | |
| 52 | `/api/schedules/` | GET | Manager |
| 53 | `/api/schedules/` | POST | Manager, Admin |
| 54 | `/api/schedules/{id}/` | GET/PATCH | Manager |
| 55 | `/api/schedules/{id}/check-in/` | POST | Manager |
| 56 | `/api/schedules/{id}/check-out/` | POST | Manager |
| 57 | `/api/schedules/today/` | GET | Manager |
| 58 | `/api/schedules/by_staff/` | GET | Manager |
| **Predictions (8)** | | | |
| 59 | `/api/predictions/busy-hours/` | GET | Manager |
| 60 | `/api/predictions/footfall/` | GET | Manager |
| 61 | `/api/predictions/food-demand/` | GET | Manager |
| 62 | `/api/predictions/inventory-alerts/` | GET | Manager, Inventory |
| 63 | `/api/predictions/staffing/` | GET | Manager |
| 64 | `/api/predictions/revenue/` | GET | Manager |
| 65 | `/api/predictions/dashboard/` | GET | Manager |
| 66 | `/api/predictions/train/` | POST | Manager |
| **Summaries (5)** | | | |
| 67 | `/api/summaries/` | GET | Manager |
| 68 | `/api/summaries/` | POST | Manager |
| 69 | `/api/summaries/{id}/` | GET | Manager |
| 70 | `/api/summaries/{id}/` | PUT/PATCH | Manager |
| 71 | `/api/summaries/{id}/` | DELETE | Manager |
| **Reports (5)** | | | |
| 72 | `/api/reports/` | GET | Manager |
| 73 | `/api/reports/{id}/` | GET | Manager |
| 74 | `/api/reports/generate/` | POST | Manager |
| 75 | `/api/reports/daily/` | GET | Manager |
| 76 | `/api/reports/{id}/` | DELETE | Manager |
| **Cloudinary (3)** | | | |
| 77 | `/api/upload/` | POST | Admin |
| 78 | `/api/upload/multi/` | POST | Admin |
| 79 | `/api/upload/delete/` | POST | Admin |
| **System (3 — infrastructure only)** | | | |
| — | `/api/health/` | GET | Admin (health indicator) |
| — | `/api/` | GET | Not used in UI |
| — | `/api/tasks/{id}/` | GET | Manager (task polling) |
| **WebSocket (3)** | | | |
| — | `WS /ws/floor/{outletId}/` | — | Host, Waiter, Manager |
| — | `WS /ws/orders/{outletId}/` | — | Waiter, Chef, Manager |
| — | `WS /ws/orders/` | — | (global fallback) |

### Coverage Summary
- **Endpoints with UI:** 76/79 (96.2%)
- **Infrastructure only:** 3 (health, api root, schema) — no UI needed
- **WebSocket channels used:** 3/3 (100%)

---

## 12. Tech Stack

| Category | Choice | Reason |
|----------|--------|--------|
| Framework | React 18 + Vite | Already in place |
| Routing | React Router v6 | Already in place |
| HTTP | Axios | Already in place, interceptors working |
| State | React Context + useState | Simple, sufficient for this scale |
| Charts | Recharts | Lightweight, React-native, great for bar/line/pie/area |
| Notifications | React Hot Toast | Minimal, customizable, stacking |
| Icons | React Icons (Fi set) | Feather icons — clean, consistent |
| Styling | Tailwind CSS | Utility-first, rapid UI development |
| Date Handling | date-fns | Lightweight alternative to moment.js |
| WebSocket | Native WebSocket (custom hooks) | Already patterned in useFloorSocket |

---

## 13. File Structure

```
src/
├── main.jsx                          # Entry point
├── App.jsx                           # RoleRouter + route definitions
├── index.css                         # Tailwind imports
│
├── services/                         # API layer
│   ├── api.js                        # Axios instance + interceptors
│   ├── auth.api.js                   # Auth endpoints
│   ├── brands.api.js                 # Brand CRUD
│   ├── outlets.api.js                # Outlet CRUD
│   ├── staff.api.js                  # Staff CRUD
│   ├── nodes.api.js                  # Nodes + status updates
│   ├── flows.api.js                  # Flows + graph
│   ├── orders.api.js                 # Orders CRUD + status
│   ├── payments.api.js               # Payments CRUD
│   ├── inventory.api.js              # Inventory CRUD
│   ├── schedules.api.js              # Schedules + check-in/out
│   ├── predictions.api.js            # All 8 prediction endpoints
│   ├── reports.api.js                # Reports + generate + daily
│   ├── summaries.api.js              # Daily summaries CRUD
│   ├── upload.api.js                 # Cloudinary upload/delete
│   └── tasks.api.js                  # Task polling
│
├── hooks/                            # Custom React hooks
│   ├── useFloorSocket.js             # Floor WebSocket (existing, enhanced)
│   ├── useOrderSocket.js             # Order WebSocket (NEW)
│   ├── useTaskPoller.js              # Poll /api/tasks/{id}/ until done
│   └── useAutoRefresh.js             # Periodic data refresh
│
├── utils/
│   ├── AuthContext.jsx               # Auth state + role detection
│   ├── RoleRouter.jsx                # Post-login role-based redirect
│   └── helpers.js                    # Formatters, constants
│
├── components/                       # Shared components
│   ├── Layout/
│   │   ├── Sidebar.jsx               # Role-aware sidebar navigation
│   │   ├── TopBar.jsx                # User info, logout, outlet name
│   │   └── PortalLayout.jsx          # Sidebar + TopBar + content area
│   ├── FloorMap/
│   │   ├── FloorGrid.jsx             # 2D grid table map
│   │   └── TableCard.jsx             # Single table with color + info
│   ├── Orders/
│   │   ├── OrderCard.jsx             # Order display card
│   │   ├── OrderForm.jsx             # Create/edit order form
│   │   └── StatusBadge.jsx           # Color-coded status pill
│   ├── Charts/
│   │   ├── BusyHoursChart.jsx        # Bar chart
│   │   ├── FootfallChart.jsx         # Area chart
│   │   ├── RevenueChart.jsx          # Line chart with confidence
│   │   ├── FoodDemandPie.jsx         # Pie chart
│   │   └── TrendsChart.jsx           # Multi-line historical trends
│   └── common/
│       ├── DataTable.jsx             # Reusable sortable/filterable table
│       ├── Modal.jsx                 # Reusable modal
│       ├── LoadingSpinner.jsx        # Loading state
│       ├── EmptyState.jsx            # No data state
│       └── KPICard.jsx               # Metric card (number + label + icon)
│
├── portals/                          # Role-specific page groups
│   ├── admin/
│   │   ├── AdminDashboard.jsx
│   │   ├── BrandManager.jsx
│   │   ├── OutletManager.jsx
│   │   ├── StaffManager.jsx
│   │   ├── FloorDesigner.jsx
│   │   └── DataSimulator.jsx
│   ├── host/
│   │   ├── ReceptionDashboard.jsx
│   │   ├── CheckInPanel.jsx
│   │   └── ActiveSeatingList.jsx
│   ├── waiter/
│   │   ├── MyTables.jsx
│   │   ├── NewOrderForm.jsx
│   │   └── OrderDetail.jsx
│   ├── chef/
│   │   ├── KitchenDisplay.jsx
│   │   └── KitchenStats.jsx
│   ├── inventory/
│   │   ├── InventoryDashboard.jsx
│   │   ├── RestockForm.jsx
│   │   ├── AlertsPanel.jsx
│   │   └── PaymentManager.jsx
│   └── manager/
│       ├── ManagerDashboard.jsx
│       ├── PredictionsHub.jsx
│       ├── ReportsCenter.jsx
│       ├── AnalyticsPage.jsx
│       ├── StaffScheduler.jsx
│       └── LiveMonitor.jsx
│
└── assets/                           # Static assets
    └── logo.svg
```

---

## 14. Implementation Phases

### Phase 0 — Foundation (Days 1-2)
**Goal:** Shared infrastructure that all portals depend on

| Task | Details |
|------|---------|
| Restructure `src/` | Create folders: `services/`, `hooks/`, `components/`, `portals/`, `utils/` |
| Split `api.js` | Break monolith into domain-specific API modules (auth, brands, orders, etc.) |
| Build `RoleRouter` | Post-login redirect logic based on `user.role` |
| Build `PortalLayout` | Sidebar + TopBar + content area (role-aware nav items) |
| Install dependencies | `recharts`, `react-hot-toast`, `react-icons`, `date-fns` |
| Build `useOrderSocket` hook | New WebSocket hook for `/ws/orders/{outletId}/` |
| Build shared components | `DataTable`, `Modal`, `KPICard`, `StatusBadge`, `LoadingSpinner` |

### Phase 1 — Core Operations: Host + Waiter + Chef (Days 3-6)
**Goal:** The end-to-end customer lifecycle works

| Task | Details |
|------|---------|
| Host: ReceptionDashboard | Floor map + check-in panel + active seating list |
| Waiter: MyTables | Assigned tables grid with order status cards |
| Waiter: NewOrderForm | Item list builder + auto-calculation |
| Waiter: OrderDetail | Status progression + serve/complete buttons |
| Chef: KitchenDisplay | 3-column KDS with real-time order cards |
| WebSocket integration | Floor + Order WS working across all 3 portals |
| Cross-portal verification | Host creates order → appears on Chef KDS → Waiter notified |

### Phase 2 — Manager Portal (Days 7-10)
**Goal:** Analytics, predictions, and reports

| Task | Details |
|------|---------|
| Manager: Dashboard | KPI cards + live mini-map + order feed |
| Manager: PredictionsHub | 6 prediction sections with Recharts charts |
| Manager: ReportsCenter | Report generation form + async polling + history |
| Manager: AnalyticsPage | Daily summaries table + trends charts + hourly heatmap |
| Manager: StaffScheduler | Today view + weekly calendar + create/check-in/out |
| Manager: LiveMonitor | Full-screen floor + order ticker + alerts |
| Chart components | BusyHoursChart, FootfallChart, RevenueChart, FoodDemandPie, TrendsChart |

### Phase 3 — Admin Portal (Days 11-13)
**Goal:** Full CRUD management + data simulation

| Task | Details |
|------|---------|
| Admin: Dashboard | System overview cards + health check |
| Admin: BrandManager | CRUD table + modal |
| Admin: OutletManager | CRUD table + modal |
| Admin: StaffManager | Staff list + register form + password change |
| Admin: FloorDesigner | Node CRUD + flow CRUD + graph visualization |
| Admin: DataSimulator | Bulk seeders for sales, inventory, schedules, orders |
| Cloudinary integration | Upload/multi-upload/delete in admin panel |

### Phase 4 — Inventory & Payments (Days 14-15)
**Goal:** Stock management and payment processing

| Task | Details |
|------|---------|
| Inventory: Dashboard | Stock table with inline editing + category filters |
| Inventory: RestockForm | Quantity update modal |
| Inventory: AlertsPanel | AI alerts sidebar with restock shortcuts |
| Inventory: PaymentManager | Payment list + create form + status management |

### Phase 5 — Polish & Integration (Days 16-18)
**Goal:** Cross-portal consistency, edge cases, responsive design

| Task | Details |
|------|---------|
| Toast notifications | Real-time alerts from both WebSocket channels |
| Error handling | Network errors, 400/403/404/429 responses, empty states |
| Responsive design | Mobile-friendly layouts for Waiter and Chef portals |
| Loading states | Skeleton screens for all data-heavy pages |
| Dark mode support | Optional toggle in TopBar |
| End-to-end testing | Verify cross-portal data flow works correctly |
| Performance | Lazy-load portal bundles (React.lazy + Suspense) |

---

## Quick Reference — Portal ↔ Page ↔ Route Map

| Portal | Page | Route | Primary Endpoints |
|--------|------|-------|-------------------|
| **Login** | Login | `/login` | token, me |
| **Admin** | Dashboard | `/admin` | health, brands, outlets, staff |
| | Brand Manager | `/admin/brands` | brands CRUD |
| | Outlet Manager | `/admin/outlets` | outlets CRUD |
| | Staff Manager | `/admin/staff` | staff CRUD, register |
| | Floor Designer | `/admin/floor` | nodes CRUD, flows CRUD, graph |
| | Data Simulator | `/admin/simulator` | sales-data, inventory, schedules, orders POST |
| **Host** | Reception | `/host` | nodes, orders, table/trigger, WS floor |
| **Waiter** | My Tables | `/waiter` | orders, nodes, WS floor + orders |
| | Order Detail | `/waiter/order/:id` | orders/{id}, update_status |
| **Chef** | Kitchen Display | `/chef` | orders, update_status, WS orders |
| **Inventory** | Stock Dashboard | `/inventory` | inventory CRUD, predictions/inventory-alerts |
| | Payments | `/inventory/payments` | payments CRUD |
| **Manager** | Dashboard | `/manager` | summaries, orders, nodes, WS both |
| | Predictions | `/manager/predictions` | all 8 prediction endpoints, train |
| | Reports | `/manager/reports` | reports CRUD, generate, daily, tasks |
| | Analytics | `/manager/analytics` | summaries, sales-data/trends, hourly |
| | Staff Schedule | `/manager/staff` | schedules CRUD, check-in/out, today, by_staff |
| | Live Monitor | `/manager/live` | nodes, orders, WS both |

---

**Total Pages: 20**
**Total Portals: 6 + Login**
**Endpoints Covered: 76/79 (96.2%)**
**WebSocket Channels: 3/3 (100%)**
**Estimated Build Time: 15-18 days**
