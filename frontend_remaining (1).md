# TwinEngine Frontend — Task Tracker

This document tracks all frontend tasks for the TwinEngine Hospitality platform.
Mirrors the style of `backend_remaining.md`. References `frontend_plan.md` as the target architecture.

> **Last Updated:** 5 March 2026 — Initial audit. All tasks pending.

---

## Current State — What Exists Today

### Codebase Metrics

| Metric | Value |
|--------|-------|
| Total source files | 17 |
| Total lines of code | ~2,962 |
| Page components | 8 (Login, Dashboard, OutletLayout, Floor, Orders, Predictions, Inventory, Reports) |
| Reusable shared components | 0 |
| API functions defined | 22 (in 1 monolith file) |
| Backend endpoints covered | ~28 of 79 (35%) |
| WebSocket channels used | 1 of 3 (33%) — Floor only |
| External dependencies | 4 (react, react-dom, react-router-dom, axios) |
| Charts / data visualizations | 0 |

### Currently Working Features

| Feature | File | Lines | What It Does |
|---------|------|-------|-------------|
| JWT Auth + Auto-Refresh | `services/api.js` | 42 | Axios interceptors attach Bearer token, auto-refresh on 401, redirect to `/login` on failure |
| Auth Context | `utils/AuthContext.jsx` | 59 | React Context with `login()`, `logout()`, `role`, `hasRole()`, 5 role constants |
| Login Page | `pages/LoginPage.jsx` | 82 | Username + password form, role selector dropdown, role mismatch validation |
| Dashboard / Outlet Picker | `pages/DashboardPage.jsx` | 107 | Welcome banner with user name/role, outlet cards linking to role's default page |
| Outlet Layout (Nav Shell) | `pages/OutletLayout.jsx` | 135 | Top nav bar with role-based tabs, profile dropdown, switch-outlet link, `<Outlet>` for children |
| Route Guards | `App.jsx` | 119 | `ProtectedRoute` (auth check), `RoleRoute` (role whitelist per route) |
| Floor Map (Live) | `pages/FloorPage.jsx` | 218 | Color-coded table grid, click-to-change-status (Manager/Host), staff shift toggles, WebSocket live updates + 20s polling fallback |
| Floor WebSocket Hook | `utils/useFloorSocket.js` | 40 | Connects to `ws/floor/{outletId}/`, handles `floor_state`, `floor_update`, `node_status_change` |
| Orders Page (4 Role Views) | `pages/OrdersPage.jsx` | 619 | Chef: card-based KDS with 15s auto-refresh + urgent highlighting. Cashier: full status dropdown + payments + create form. Manager: lifecycle buttons + payments + create. Waiter: read-only table. |
| Predictions Page | `pages/PredictionsPage.jsx` | 172 | Date picker, parallel API fetch (`Promise.all`), summary cards, hourly data tables, staffing shifts, inventory alerts |
| Inventory Page | `pages/InventoryPage.jsx` | 228 | CRUD table with inline quantity editing, add item form (6 categories, 5 units), low stock highlighting, delete confirmation |
| Reports Page | `pages/ReportsPage.jsx` | 96 | Report type selector (Daily/Weekly/Monthly), date picker, GPT summary + insights display, PDF download link |
| Helpers | `utils/helpers.js` | 24 | `STATUS_COLORS`, `STATUS_LABELS`, `fmtDate()`, `fmtCurrency()` |
| Stylesheet | `index.css` | 1,164 | Full design system: CSS custom properties, responsive breakpoints, cards, tables, forms, animations |

### API Functions Currently Defined (22)

```
Auth:        login, getProfile
Outlets:     getOutlets
Nodes:       getNodes, getFlowGraph, updateNodeStatus
Orders:      getOrders, getOrder, createOrder, updateOrderStatus
Predictions: getPredictionDashboard, getBusyHours, getFootfall, getRevenue,
             getFoodDemand, getInventoryAlerts, getStaffing
Inventory:   getInventory, createInventoryItem, updateInventoryItem, deleteInventoryItem
Payments:    getPayments, createPayment, updatePayment
Staff:       getStaff, getAllStaff, updateStaffMember
Reports:     generateReport, getDailySummaries
```

### API Functions Defined But Never Called in Any Page

| Function | Defined In | Used By |
|----------|-----------|---------|
| `getFlowGraph` | api.js | None |
| `getOrder` | api.js | None |
| `getFootfall` | api.js | None |
| `getFoodDemand` | api.js | None |
| `getInventoryAlerts` | api.js | None |
| `getDailySummaries` | api.js | None |

---

## Remaining Tasks

### 1. Foundation — Project Restructure 🔴 High Priority

**Status:** ❌ Not Started

#### What Needs to Be Done:

**1.1 Install New Dependencies**

Current `package.json` has 4 runtime dependencies. Plan requires 8:

| Package | Purpose | Currently Installed? |
|---------|---------|---------------------|
| `react` | UI framework | ✅ Yes (^19.2.0) |
| `react-dom` | DOM renderer | ✅ Yes |
| `react-router-dom` | Client routing | ✅ Yes (^7.13.1) |
| `axios` | HTTP client | ✅ Yes (^1.13.5) |
| `recharts` | Charts (bar, line, pie, area) | ❌ No |
| `react-hot-toast` | Toast notifications | ❌ No |
| `react-icons` | Icon library (Feather set) | ❌ No |
| `date-fns` | Date formatting/manipulation | ❌ No |
| `tailwindcss` | Utility-first CSS framework | ❌ No |

```bash
npm install recharts react-hot-toast react-icons date-fns
npm install -D tailwindcss @tailwindcss/vite
```

**1.2 Restructure `src/` Directory**

Current flat structure → planned nested structure:

```
CURRENT:                          PLANNED:
src/                              src/
├── pages/ (8 files)              ├── portals/ (6 folders, 20+ pages)
├── services/api.js (1 file)      ├── services/ (16 API modules)
├── utils/ (3 files)              ├── hooks/ (4 hooks)
└── (no components/)              ├── components/ (5 folders, 15+ shared)
                                  └── utils/ (4 files)
```

**1.3 Split Monolith `api.js` Into Domain Modules**

Current: 1 file with 22 functions (113 lines)
Planned: 16 focused modules + shared Axios instance

| New Module | Endpoints | Functions |
|-----------|-----------|-----------|
| `api.js` | — | Axios instance + interceptors only (shared) |
| `auth.api.js` | `/api/auth/*` | login, refreshToken, verifyToken, register, getProfile, changePassword |
| `brands.api.js` | `/api/brands/*` | getBrands, createBrand, getBrand, updateBrand, deleteBrand |
| `outlets.api.js` | `/api/outlets/*` | getOutlets, createOutlet, getOutlet, updateOutlet, deleteOutlet |
| `staff.api.js` | `/api/staff/*` | getStaff, getAllStaff, getStaffMember, updateStaffMember, deleteStaffMember |
| `nodes.api.js` | `/api/nodes/*` | getNodes, createNode, getNode, updateNode, deleteNode, updateNodeStatus |
| `flows.api.js` | `/api/flows/*` | getFlows, createFlow, getFlow, updateFlow, deleteFlow, getFlowGraph |
| `orders.api.js` | `/api/orders/*` | getOrders, createOrder, getOrder, updateOrder, deleteOrder, updateOrderStatus |
| `payments.api.js` | `/api/payments/*` | getPayments, createPayment, getPayment, updatePayment |
| `inventory.api.js` | `/api/inventory/*` | getInventory, createInventoryItem, getInventoryItem, updateInventoryItem, deleteInventoryItem |
| `schedules.api.js` | `/api/schedules/*` | getSchedules, createSchedule, getSchedule, updateSchedule, checkIn, checkOut, getToday, getByStaff |
| `predictions.api.js` | `/api/predictions/*` | getDashboard, getBusyHours, getFootfall, getFoodDemand, getRevenue, getStaffing, getInventoryAlerts, trainModels |
| `reports.api.js` | `/api/reports/*` | getReports, getReport, generateReport, getDailyReport, deleteReport |
| `summaries.api.js` | `/api/summaries/*` | getSummaries, createSummary, getSummary, updateSummary, deleteSummary |
| `salesdata.api.js` | `/api/sales-data/*` | getSalesData, createSalesData, getTrends, getHourlyPattern |
| `upload.api.js` | `/api/upload/*` | uploadFile, uploadMultiple, deleteFile |
| `tasks.api.js` | `/api/tasks/*` | getTaskStatus |

**1.4 Build RoleRouter**

Current: All roles land on `/` (DashboardPage), then pick an outlet → `/outlet/:id/` shared layout.
Planned: After login, auto-redirect to role-specific portal.

| Role | Redirect To | Current Behavior |
|------|------------|-----------------|
| MANAGER (superuser) | `/admin` | Goes to `/` → picks outlet → shares same `/outlet/:id/` as everyone |
| MANAGER | `/manager` | Same as above |
| HOST | `/host` | Same — no host-specific pages exist |
| WAITER | `/waiter` | Same — waiter sees read-only views |
| CHEF | `/chef` | Same — chef sees card view in OrdersPage |
| CASHIER | `/inventory` | Same — cashier sees table view in OrdersPage |

The `RoleRoute` guard component exists but only restricts access within the shared outlet layout. It needs to be replaced with a full `RoleRouter` that maps each role to a dedicated route tree.

**1.5 Build PortalLayout (Role-Aware Shell)**

Current `OutletLayout` (135 lines) provides a single top nav bar with role-based tab filtering.
Planned: `PortalLayout` with a sidebar navigation, top bar (user info + logout + outlet name), and content area. Each portal has its own nav items.

| Portal | Sidebar Items |
|--------|--------------|
| Admin | Dashboard, Brands, Outlets, Staff, Floor Designer, Data Simulator |
| Host | Reception (Floor Map), Active Seating |
| Waiter | My Tables, New Order |
| Chef | Kitchen Display |
| Inventory | Stock, Payments, AI Alerts |
| Manager | Dashboard, Predictions, Reports, Analytics, Staff Schedule, Live Monitor |

#### Files to Create:
- `src/services/*.api.js` — 16 API modules
- `src/utils/RoleRouter.jsx` — Post-login role redirect
- `src/components/Layout/PortalLayout.jsx` — Sidebar + TopBar + content area
- `src/components/Layout/Sidebar.jsx` — Role-aware sidebar navigation
- `src/components/Layout/TopBar.jsx` — User info, logout, outlet name
- `tailwind.config.js` — Tailwind configuration
- `postcss.config.js` — PostCSS configuration

#### Files to Modify:
- `package.json` — Add 5 new dependencies
- `vite.config.js` — Tailwind plugin
- `src/App.jsx` — Replace route tree with portal-based routes
- `src/index.css` — Replace raw CSS with Tailwind imports (or keep alongside)
- `src/services/api.js` — Strip to Axios instance only, move endpoints to modules

---

### 2. Shared Reusable Components 🔴 High Priority

**Status:** ❌ Not Started

#### What Needs to Be Done:

Current frontend has **zero** reusable components. Every page renders its own tables, modals, cards, and loading states inline. The plan calls for ~15 shared components.

| Component | Purpose | Currently Exists? |
|-----------|---------|------------------|
| `DataTable` | Sortable, filterable table with column definitions | ❌ — each page renders its own `<table>` |
| `Modal` | Reusable modal dialog (create/edit/confirm) | ❌ — forms are inline sections, not modals |
| `KPICard` | Metric card (number + label + icon + trend) | ❌ — PredictionsPage has inline `SummaryCard` helper |
| `StatusBadge` | Color-coded status pill (order/node/payment) | ❌ — inline `<span>` with hardcoded styles everywhere |
| `LoadingSpinner` | Centered loading state | ❌ — each page has its own `{loading && <p>Loading...</p>}` |
| `EmptyState` | No data message with icon | ❌ — inline "No data" text |
| `FloorGrid` | 2D table map with color-coded cards | ❌ — FloorPage renders this inline (could be extracted) |
| `TableCard` | Single table card with status + info | ❌ — part of FloorPage |
| `OrderCard` | Order display card | ❌ — OrdersPage chef view renders these inline |
| `OrderForm` | Create/edit order form | ❌ — OrdersPage has inline form (~100 lines per role) |

#### Files to Create:
- `src/components/common/DataTable.jsx`
- `src/components/common/Modal.jsx`
- `src/components/common/KPICard.jsx`
- `src/components/common/StatusBadge.jsx`
- `src/components/common/LoadingSpinner.jsx`
- `src/components/common/EmptyState.jsx`
- `src/components/FloorMap/FloorGrid.jsx`
- `src/components/FloorMap/TableCard.jsx`
- `src/components/Orders/OrderCard.jsx`
- `src/components/Orders/OrderForm.jsx`
- `src/components/Orders/StatusBadge.jsx`

---

### 3. Chart Components (Recharts) 🔴 High Priority

**Status:** ❌ Not Started

#### What Needs to Be Done:

Current `PredictionsPage` displays all ML data as raw HTML tables with numbers. No charts, no visualizations, no trend indicators.

The plan requires 5 chart components using Recharts:

| Chart Component | Chart Type | Data Source | Currently Shown As |
|----------------|-----------|-------------|-------------------|
| `BusyHoursChart` | Bar chart (X=hour, Y=orders) | `GET /api/predictions/busy-hours/` | Flat HTML table of numbers |
| `FootfallChart` | Area chart (hourly guests) | `GET /api/predictions/footfall/` | **Not displayed** (API function defined but never called) |
| `RevenueChart` | Line chart + confidence ribbon | `GET /api/predictions/revenue/` | Single number in a card |
| `FoodDemandPie` | Pie chart (category split) | `GET /api/predictions/food-demand/` | **Not displayed** (API function defined but never called) |
| `TrendsChart` | Multi-line historical chart | `GET /api/sales-data/trends/` | **No API function defined** |

#### Additional Chart Needs (Manager Analytics Page):
- Revenue trend over 30 days (line chart)
- Orders per day (bar chart)
- Hourly pattern heatmap (heatmap or colored bar chart)

#### Files to Create:
- `src/components/Charts/BusyHoursChart.jsx`
- `src/components/Charts/FootfallChart.jsx`
- `src/components/Charts/RevenueChart.jsx`
- `src/components/Charts/FoodDemandPie.jsx`
- `src/components/Charts/TrendsChart.jsx`

---

### 4. Order WebSocket Hook 🔴 High Priority

**Status:** ❌ Not Started

#### What Needs to Be Done:

The backend has two WebSocket consumers. The frontend only uses one:

| WebSocket | Backend Consumer | Frontend Hook | Status |
|-----------|-----------------|---------------|--------|
| `ws/floor/{outletId}/` | `FloorConsumer` | `useFloorSocket` ✅ | Working |
| `ws/orders/{outletId}/` | `OrderConsumer` | — | ❌ **Not implemented** |
| `ws/orders/` | `OrderConsumer` (global) | — | ❌ **Not implemented** |

The `OrderConsumer` broadcasts these events that the frontend currently ignores:

| Event | Payload | Who Needs It |
|-------|---------|-------------|
| `active_orders` | `{orders: [...]}` | Chef KDS, Waiter, Manager |
| `order_created` | `{order: {...}}` | Chef (new order slides in), Manager (live feed) |
| `order_updated` | `{order_id, old_status, new_status, table_id}` | Chef (card moves between columns), Waiter (toast notification) |
| `order_completed` | `{order_id, table_id, total}` | Manager (live feed), Waiter (toast) |
| `request_orders` | — (client→server) | All (request full re-send) |

**Impact of Missing WebSocket:**
- Chef's KDS uses 15-second polling instead of instant real-time updates
- Waiters have no notification when their order is Ready
- Manager has no live order feed
- No toast notifications for order events

#### Files to Create:
- `src/hooks/useOrderSocket.js` — mirrors `useFloorSocket` pattern

#### Files to Modify:
- `src/portals/chef/KitchenDisplay.jsx` — Replace polling with WebSocket
- `src/portals/waiter/MyTables.jsx` — Add order status notifications
- `src/portals/manager/LiveMonitor.jsx` — Add live order ticker

---

### 5. Admin Portal 🟠 Medium Priority

**Status:** ❌ Not Started — **No admin pages exist.**

#### What Needs to Be Done:

The Admin portal is for superuser managers. It provides CRUD management for all entities and a data simulation tool. Currently, none of these pages exist — all entity management is done via Django Admin only.

**6 Pages to Build:**

| Page | Route | Key Features | Backend Endpoints |
|------|-------|-------------|-------------------|
| Admin Dashboard | `/admin` | KPI cards (brands, outlets, staff, nodes, orders count), health indicator | `GET /api/health/`, `GET /api/brands/`, `GET /api/outlets/`, `GET /api/staff/`, `GET /api/orders/` |
| Brand Manager | `/admin/brands` | CRUD table + create/edit modal | `GET/POST /api/brands/`, `GET/PUT/PATCH/DELETE /api/brands/{id}/` |
| Outlet Manager | `/admin/outlets` | CRUD table + create/edit modal, brand selector, active toggle | `GET/POST /api/outlets/`, `GET/PUT/PATCH/DELETE /api/outlets/{id}/` |
| Staff Manager | `/admin/staff` | Staff table + register form + password change, filter by role/outlet | `GET /api/staff/`, `POST /api/auth/register/`, `POST /api/auth/change-password/`, `GET/PATCH/DELETE /api/staff/{id}/` |
| Floor Designer | `/admin/floor` | Node CRUD (drag grid), flow CRUD (source→target), flow graph visualization | `GET/POST /api/nodes/`, `GET/PUT/PATCH/DELETE /api/nodes/{id}/`, `GET/POST /api/flows/`, `GET/PUT/PATCH/DELETE /api/flows/{id}/`, `GET /api/flows/graph/` |
| Data Simulator | `/admin/simulator` | Bulk seeders: sales data, inventory, schedules, orders. Count inputs + generate buttons. | `POST /api/sales-data/`, `POST /api/inventory/`, `POST /api/schedules/`, `POST /api/orders/` |

**Endpoints used (count): 27**
Currently wired: 0 of 27

#### Files to Create:
- `src/portals/admin/AdminDashboard.jsx`
- `src/portals/admin/BrandManager.jsx`
- `src/portals/admin/OutletManager.jsx`
- `src/portals/admin/StaffManager.jsx`
- `src/portals/admin/FloorDesigner.jsx`
- `src/portals/admin/DataSimulator.jsx`

---

### 6. Host / Receptionist Portal 🟠 Medium Priority

**Status:** ❌ Not Started — **No host-specific pages exist.**

#### What Needs to Be Done:

The Host role currently sees the same FloorPage + shared OrdersPage as everyone else. The plan calls for a dedicated reception dashboard with customer lifecycle management.

**3 Pages to Build:**

| Page | Route | Key Features | Backend Endpoints |
|------|-------|-------------|-------------------|
| Reception Dashboard | `/host` | Live floor map (color-coded tables), table count summary bar ("12 Available, 5 Occupied"), real-time via Floor WS | `GET /api/nodes/`, `WS /ws/floor/{outletId}/` |
| Check-In Panel | `/host` (sidebar/modal) | Customer name, party size, waiter assignment dropdown, submit creates order + table turns RED | `POST /api/orders/`, `POST /api/nodes/{id}/update_status/`, `GET /api/staff/` |
| Active Seating List | `/host` (tab/panel) | Currently occupied tables: customer, party size, waiter, wait time, "Flag Delay" + "Exit Customer" buttons | `GET /api/orders/`, `POST /api/nodes/{id}/update_status/`, `POST /api/orders/{id}/update_status/`, `POST /api/table/trigger/` |

**Endpoints used (count): 8**
Currently wired (in api.js but no Host UI): 5 of 8

#### What Exists That Can Be Reused:
- `useFloorSocket` hook — works, minor enhancements needed
- `getNodes`, `updateNodeStatus` — already in api.js
- `getOrders`, `createOrder`, `updateOrderStatus` — already in api.js
- `getStaff` — already in api.js
- `STATUS_COLORS`, `STATUS_LABELS` — in helpers.js
- Floor grid rendering from `FloorPage` — can be extracted into `FloorGrid` component

#### Files to Create:
- `src/portals/host/ReceptionDashboard.jsx`
- `src/portals/host/CheckInPanel.jsx`
- `src/portals/host/ActiveSeatingList.jsx`

---

### 7. Waiter Portal 🟠 Medium Priority

**Status:** ❌ Not Started — **No waiter-specific pages exist.**

#### What Needs to Be Done:

The Waiter role currently sees a read-only table in `OrdersPage` with no ability to create orders, view details, or receive notifications. The plan calls for a dedicated portal.

**3 Pages to Build:**

| Page | Route | Key Features | Backend Endpoints |
|------|-------|-------------|-------------------|
| My Tables | `/waiter` | Grid of assigned tables with order status cards, real-time updates, quick action buttons | `GET /api/orders/`, `GET /api/nodes/`, `WS /ws/floor/`, `WS /ws/orders/` |
| New Order Form | `/waiter` (modal) | Table selector, customer name, party size, item list builder (name, qty, price, add row), auto-calc total | `POST /api/orders/`, `GET /api/nodes/` |
| Order Detail | `/waiter/order/:id` | Full order info, status timeline, "Mark Served" / "Complete & Bill" buttons | `GET /api/orders/{id}/`, `POST /api/orders/{id}/update_status/` |

**Endpoints used (count): 8**
Currently wired (in api.js but waiter view is read-only): 6 of 8

#### Gap Analysis:
- `createOrder` is defined in api.js but **no UI form exists** for Waiter role
- `getOrder` is defined in api.js but **never called** — no order detail page exists
- Order WebSocket (`useOrderSocket`) doesn't exist — waiter can't receive "Order READY" notifications
- No toast notifications of any kind

#### Files to Create:
- `src/portals/waiter/MyTables.jsx`
- `src/portals/waiter/NewOrderForm.jsx`
- `src/portals/waiter/OrderDetail.jsx`

---

### 8. Chef / Kitchen Display Portal 🟠 Medium Priority

**Status:** 🔶 Partially exists — OrdersPage has a chef card view, but it's not a dedicated portal.

#### What Exists:

`OrdersPage.jsx` (619 lines) renders a Chef-specific view:
- Card-based layout with color-coded status headers
- 15-second auto-refresh via `setInterval` polling
- Urgent order highlighting (>15 min, red pulsing border)
- Buttons: "Start Cooking" (PLACED→PREPARING), "Ready" (PREPARING→READY)
- Separate "Active Orders" and "Past Orders" sections

#### What's Missing to Match the Plan:

| Feature | Current | Planned |
|---------|---------|---------|
| Layout | Cards in the shared outlet layout | **Full-screen, TV-optimized 3-column KDS** (PLACED / PREPARING / READY columns) |
| Updates | 15s polling (`setInterval` + `getOrders()`) | **Real-time via Order WebSocket** (instant, no polling) |
| Sound | None | **Audio notification** on new PLACED order |
| Stats | None | **Kitchen stats bar** — queue count, cooking count, avg cook time, longest wait |
| Animations | None (except CSS pulse on urgent) | **Slide-in animation** for new orders, **column transition** when status changes |
| Portal | Nested inside `/outlet/:id/orders` | **Dedicated `/chef` route** with full-screen layout |

#### Files to Create:
- `src/portals/chef/KitchenDisplay.jsx` — 3-column full-screen KDS
- `src/portals/chef/KitchenStats.jsx` — Live metrics bar

#### Files to Retire:
- Chef-specific rendering in `pages/OrdersPage.jsx` (lines ~1–200 of the chef card view) → migrated to `KitchenDisplay.jsx`

---

### 9. Inventory & Payments Portal 🟠 Medium Priority

**Status:** 🔶 Partially exists — InventoryPage has basic CRUD, but no payments UI, no AI alerts, no dedicated portal.

#### What Exists:

`InventoryPage.jsx` (228 lines):
- Full CRUD table with inline quantity editing
- Add item form (category/unit dropdowns)
- Low stock highlighting (quantity ≤ reorder threshold)
- Summary cards (total items, low stock count)
- Delete confirmation dialog

`OrdersPage.jsx` — Cashier view has payment toggle (Pending ↔ Done) inline in the orders table.

#### What's Missing to Match the Plan:

| Feature | Current | Planned |
|---------|---------|---------|
| AI Alerts | Not displayed (API function `getInventoryAlerts` defined but never called) | **Sidebar panel** with ML alerts sorted by urgency, "Restock Now" shortcut buttons |
| Restock Form | Inline quantity edit (click number → type new value) | **Dedicated restock modal** with quantity-add (adds to existing), sets `last_restocked` |
| Payment Page | Inline toggle in OrdersPage cashier view | **Full payment management page** — list, create, filters, status management (SUCCESS/FAILED/REFUNDED) |
| Payment Create Form | Cashier can toggle "Done" on an order | **Full form** — order selector, amount (pre-filled), method (CASH/CARD/UPI/WALLET/SPLIT), transaction ID, tip |
| Portal | Inside shared `/outlet/:id/inventory` | **Dedicated `/inventory` route** with sidebar nav (Stock, Payments, Alerts) |

#### Files to Create:
- `src/portals/inventory/InventoryDashboard.jsx` — Enhanced stock table
- `src/portals/inventory/RestockForm.jsx` — Restock modal
- `src/portals/inventory/AlertsPanel.jsx` — ML inventory alerts sidebar
- `src/portals/inventory/PaymentManager.jsx` — Full payment CRUD page

#### Files to Retire:
- `pages/InventoryPage.jsx` → migrated and enhanced in `portals/inventory/InventoryDashboard.jsx`
- Cashier payment toggle in `pages/OrdersPage.jsx` → replaced by `PaymentManager.jsx`

---

### 10. General Manager Portal 🟠 Medium Priority

**Status:** 🔶 Partially exists — PredictionsPage + ReportsPage exist, but minimal. No analytics, no staff scheduling, no live monitoring.

#### What Exists:

| Page | Lines | What It Does | What's Missing |
|------|-------|-------------|----------------|
| `PredictionsPage` | 172 | Fetches 4 of 8 prediction endpoints, shows data in HTML tables | Charts (Recharts), 4 missing endpoints (footfall, food-demand not displayed), no train button |
| `ReportsPage` | 96 | Generate reports, show GPT summary | No report history list, no report detail view, no daily report lookup, no task polling UI |

#### 6 Pages to Build:

| Page | Route | Key Features | Backend Endpoints |
|------|-------|-------------|-------------------|
| Manager Dashboard | `/manager` | KPI row (revenue, orders, avg ticket, active tables, staff on shift), live floor mini-map, active orders feed, quick links | `GET /api/summaries/`, `GET /api/orders/`, `GET /api/nodes/`, `WS floor + orders` |
| Predictions Hub | `/manager/predictions` | **6 chart sections** (BusyHours bar, Footfall area, FoodDemand pie, Revenue line+confidence, Staffing table, Inventory alerts), model training trigger with async polling | All 8 prediction endpoints + `POST /api/predictions/train/` + `GET /api/tasks/{id}/` |
| Reports Center | `/manager/reports` | Generate form (type, dates) → async polling → GPT summary + PDF link. **Report history table** + detail view. Daily report lookup by date. | `POST /api/reports/generate/`, `GET /api/reports/`, `GET /api/reports/{id}/`, `GET /api/reports/daily/`, `GET /api/tasks/{id}/` |
| Analytics Page | `/manager/analytics` | Daily summaries table (sortable), revenue trends line chart (30 days), orders bar chart, hourly pattern heatmap, create summary form | `GET /api/summaries/`, `POST /api/summaries/`, `GET /api/sales-data/trends/`, `GET /api/sales-data/hourly_pattern/` |
| Staff Scheduler | `/manager/staff` | Today's schedule cards + check-in/out buttons, weekly calendar grid, create schedule form, per-staff schedule view, AI staffing overlay | `GET/POST /api/schedules/`, `POST /api/schedules/{id}/check-in/`, `POST /api/schedules/{id}/check-out/`, `GET /api/schedules/today/`, `GET /api/schedules/by_staff/`, `GET /api/predictions/staffing/` |
| Live Monitor | `/manager/live` | Full-screen floor map + order ticker + wait time alerts + staff on-shift panel | `GET /api/nodes/`, `GET /api/orders/`, `GET /api/staff/`, `WS floor + orders` |

**Endpoints used (count): 32**
Currently wired: 10 of 32

#### Gap: Endpoints With No API Function Defined

These endpoints are used by the Manager portal but have **no API function in the frontend at all**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/predictions/train/` | POST | Trigger ML model retraining |
| `/api/tasks/{id}/` | GET | Poll async task status |
| `/api/reports/` | GET | List all reports |
| `/api/reports/{id}/` | GET | Report detail |
| `/api/reports/daily/` | GET | Daily report lookup |
| `/api/reports/{id}/` | DELETE | Delete report |
| `/api/sales-data/trends/` | GET | Sales trends |
| `/api/sales-data/hourly_pattern/` | GET | Hourly sales pattern |
| `/api/schedules/` | GET/POST | List/create schedules |
| `/api/schedules/{id}/` | GET/PATCH | Schedule detail |
| `/api/schedules/{id}/check-in/` | POST | Record check-in |
| `/api/schedules/{id}/check-out/` | POST | Record check-out |
| `/api/schedules/today/` | GET | Today's schedules |
| `/api/schedules/by_staff/` | GET | Per-staff schedule |
| `/api/summaries/` | POST | Create summary |
| `/api/summaries/{id}/` | GET/PUT/PATCH/DELETE | Summary CRUD |

#### Files to Create:
- `src/portals/manager/ManagerDashboard.jsx`
- `src/portals/manager/PredictionsHub.jsx` (replaces `pages/PredictionsPage.jsx`)
- `src/portals/manager/ReportsCenter.jsx` (replaces `pages/ReportsPage.jsx`)
- `src/portals/manager/AnalyticsPage.jsx`
- `src/portals/manager/StaffScheduler.jsx`
- `src/portals/manager/LiveMonitor.jsx`

#### Files to Retire:
- `pages/PredictionsPage.jsx` → migrated to `portals/manager/PredictionsHub.jsx`
- `pages/ReportsPage.jsx` → migrated to `portals/manager/ReportsCenter.jsx`

---

### 11. Additional Hooks 🟢 Low Priority

**Status:** ❌ Not Started

| Hook | Purpose | Currently Exists? |
|------|---------|------------------|
| `useFloorSocket` | Floor WebSocket | ✅ Yes — working, minor enhancements needed |
| `useOrderSocket` | Order WebSocket | ❌ No — see Task 4 |
| `useTaskPoller` | Poll `GET /api/tasks/{id}/` every 3s until complete | ❌ No — ReportsPage does inline polling but not reusable |
| `useAutoRefresh` | Periodic data refresh (configurable interval) | ❌ No — OrdersPage chef view does inline `setInterval` |

#### Files to Create:
- `src/hooks/useOrderSocket.js`
- `src/hooks/useTaskPoller.js`
- `src/hooks/useAutoRefresh.js`

#### Files to Modify:
- `src/utils/useFloorSocket.js` → move to `src/hooks/useFloorSocket.js`

---

### 12. Toast Notifications 🟢 Low Priority

**Status:** ❌ Not Started

#### What Needs to Be Done:

Current frontend has **zero** user notifications. Errors are shown via inline text or `console.error`. Success is shown by re-fetching data.

Planned: `react-hot-toast` for all user-facing notifications.

**Notification Sources:**

| Source | Notification | Currently |
|--------|-------------|-----------|
| WebSocket (Floor) | "⏰ Table-7 waiting 20 minutes!" | Ignored — `wait_time_alert` event received but not displayed |
| WebSocket (Orders) | "🍳 Order #15 is READY — Table-3" | WebSocket not connected |
| API success | "✅ Order created", "✅ Report generated" | No feedback — data silently re-fetches |
| API error | "❌ Failed to update status: 403" | Inline `<p>` text or `console.error` |

#### Files to Create/Modify:
- Install `react-hot-toast`
- Add `<Toaster />` to `App.jsx`
- Update all API calls across all portals to show success/error toasts

---

### 13. Polish & UX 🟢 Low Priority

**Status:** ❌ Not Started

| Feature | Current | Planned |
|---------|---------|---------|
| Responsive design | Single CSS breakpoint at 768px in `index.css` | Mobile-friendly layouts for Waiter + Chef portals (used on tablets in restaurant) |
| Loading states | `{loading && <p>Loading...</p>}` | Skeleton screens / shimmer effects |
| Dark mode | Not supported | Optional toggle in TopBar |
| Error boundaries | Not implemented | React Error Boundaries per portal |
| Lazy loading | All pages loaded eagerly | `React.lazy` + `Suspense` per portal bundle |
| Accessibility | Not addressed | ARIA labels, keyboard navigation, screen reader support |

---

## Endpoint Coverage Gap — Full Comparison

### Endpoints Currently Wired (28 of 79)

```
✅ POST   /api/auth/token/              (login)
✅ POST   /api/auth/token/refresh/      (interceptor)
✅ GET    /api/auth/me/                  (getProfile)
✅ GET    /api/outlets/                  (getOutlets)
✅ GET    /api/nodes/                    (getNodes)
✅ GET    /api/flows/graph/             (getFlowGraph — defined but never called)
✅ POST   /api/nodes/{id}/update_status/ (updateNodeStatus)
✅ GET    /api/orders/                   (getOrders)
✅ GET    /api/orders/{id}/              (getOrder — defined but never called)
✅ POST   /api/orders/                   (createOrder)
✅ POST   /api/orders/{id}/update_status/ (updateOrderStatus)
✅ GET    /api/predictions/dashboard/    (getPredictionDashboard)
✅ GET    /api/predictions/busy-hours/   (getBusyHours)
✅ GET    /api/predictions/footfall/     (getFootfall — defined but never called)
✅ GET    /api/predictions/revenue/      (getRevenue)
✅ GET    /api/predictions/food-demand/  (getFoodDemand — defined but never called)
✅ GET    /api/predictions/inventory-alerts/ (getInventoryAlerts — defined but never called)
✅ GET    /api/predictions/staffing/     (getStaffing)
✅ GET    /api/inventory/                (getInventory)
✅ POST   /api/inventory/                (createInventoryItem)
✅ PATCH  /api/inventory/{id}/           (updateInventoryItem)
✅ DELETE /api/inventory/{id}/           (deleteInventoryItem)
✅ GET    /api/payments/                 (getPayments)
✅ POST   /api/payments/                 (createPayment)
✅ PATCH  /api/payments/{id}/            (updatePayment)
✅ GET    /api/staff/                    (getStaff, getAllStaff)
✅ PATCH  /api/staff/{id}/              (updateStaffMember)
✅ POST   /api/reports/generate/         (generateReport)
✅ GET    /api/summaries/                (getDailySummaries)
```

### Endpoints NOT Wired (51 of 79)

```
❌ POST   /api/auth/token/verify/
❌ POST   /api/auth/register/
❌ POST   /api/auth/change-password/
❌ GET    /api/brands/
❌ POST   /api/brands/
❌ GET    /api/brands/{id}/
❌ PUT    /api/brands/{id}/
❌ PATCH  /api/brands/{id}/
❌ DELETE /api/brands/{id}/
❌ POST   /api/outlets/
❌ GET    /api/outlets/{id}/
❌ PUT    /api/outlets/{id}/
❌ PATCH  /api/outlets/{id}/
❌ DELETE /api/outlets/{id}/
❌ GET    /api/staff/{id}/
❌ DELETE /api/staff/{id}/
❌ POST   /api/nodes/
❌ GET    /api/nodes/{id}/
❌ PUT    /api/nodes/{id}/
❌ PATCH  /api/nodes/{id}/
❌ DELETE /api/nodes/{id}/
❌ GET    /api/flows/
❌ POST   /api/flows/
❌ GET    /api/flows/{id}/
❌ PUT    /api/flows/{id}/
❌ PATCH  /api/flows/{id}/
❌ DELETE /api/flows/{id}/
❌ PUT    /api/orders/{id}/
❌ PATCH  /api/orders/{id}/
❌ DELETE /api/orders/{id}/
❌ GET    /api/payments/{id}/
❌ POST   /api/table/trigger/
❌ GET    /api/sales-data/
❌ POST   /api/sales-data/
❌ GET    /api/sales-data/trends/
❌ GET    /api/sales-data/hourly_pattern/
❌ GET    /api/schedules/
❌ POST   /api/schedules/
❌ GET    /api/schedules/{id}/
❌ PATCH  /api/schedules/{id}/
❌ POST   /api/schedules/{id}/check-in/
❌ POST   /api/schedules/{id}/check-out/
❌ GET    /api/schedules/today/
❌ GET    /api/schedules/by_staff/
❌ POST   /api/predictions/train/
❌ GET    /api/reports/
❌ GET    /api/reports/{id}/
❌ GET    /api/reports/daily/
❌ DELETE /api/reports/{id}/
❌ POST   /api/upload/
❌ POST   /api/upload/multi/
❌ POST   /api/upload/delete/
❌ GET    /api/tasks/{id}/
❌ GET    /api/health/
❌ POST/GET/PATCH/DELETE /api/summaries/{id}/
```

---

## Summary Table

| # | Task | Priority | Status | Files to Create | Endpoints Added |
|---|------|----------|--------|----------------|----------------|
| 1 | Foundation — Restructure & Dependencies | 🔴 High | ❌ Not Started | ~20 | 0 (infra) |
| 2 | Shared Reusable Components | 🔴 High | ❌ Not Started | 11 | 0 (UI) |
| 3 | Chart Components (Recharts) | 🔴 High | ❌ Not Started | 5 | 0 (UI) |
| 4 | Order WebSocket Hook | 🔴 High | ❌ Not Started | 1 | +1 WS |
| 5 | Admin Portal (6 pages) | 🟠 Medium | ❌ Not Started | 6 | +27 |
| 6 | Host / Receptionist Portal (3 pages) | 🟠 Medium | ❌ Not Started | 3 | +3 |
| 7 | Waiter Portal (3 pages) | 🟠 Medium | ❌ Not Started | 3 | +2 |
| 8 | Chef / Kitchen Display Portal (2 pages) | 🟠 Medium | 🔶 Partial | 2 | +1 WS |
| 9 | Inventory & Payments Portal (4 pages) | 🟠 Medium | 🔶 Partial | 4 | +1 |
| 10 | General Manager Portal (6 pages) | 🟠 Medium | 🔶 Partial | 6 | +18 |
| 11 | Additional Hooks | 🟢 Low | ❌ Not Started | 3 | 0 |
| 12 | Toast Notifications | 🟢 Low | ❌ Not Started | 0 | 0 |
| 13 | Polish & UX | 🟢 Low | ❌ Not Started | 0 | 0 |

### Overall Progress

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Pages | 8 | 20 | 12 to build |
| Components (shared) | 0 | 15 | 15 to build |
| API modules | 1 | 16 | 15 to build |
| Endpoint coverage | 28/79 (35%) | 76/79 (96%) | 48 to wire |
| WebSocket channels | 1/3 (33%) | 3/3 (100%) | 2 to connect |
| Charts | 0 | 5 | 5 to build |
| Dependencies | 4 | 9 | 5 to install |
| Total source files | 17 | ~65 | ~48 to create |
| Total lines (est.) | ~2,962 | ~12,000 | ~9,000 to write |

---

## Pages to Retire After Migration

Once portals are built, these legacy pages move to portals and the old files are deleted:

| Old File | Migrated To | Reason |
|----------|------------|--------|
| `pages/DashboardPage.jsx` | Absorbed by `RoleRouter` + individual portal dashboards | Outlet picker becomes implicit (profile has outlet) |
| `pages/OutletLayout.jsx` | `components/Layout/PortalLayout.jsx` | New layout with sidebar per role |
| `pages/FloorPage.jsx` | `portals/host/ReceptionDashboard.jsx` + `components/FloorMap/FloorGrid.jsx` | Extracted into reusable component |
| `pages/OrdersPage.jsx` | `portals/waiter/MyTables.jsx` + `portals/chef/KitchenDisplay.jsx` + `portals/inventory/PaymentManager.jsx` | 619-line monolith split into 3 role-specific pages |
| `pages/PredictionsPage.jsx` | `portals/manager/PredictionsHub.jsx` | Enhanced with charts |
| `pages/InventoryPage.jsx` | `portals/inventory/InventoryDashboard.jsx` | Enhanced with alerts + restock modal |
| `pages/ReportsPage.jsx` | `portals/manager/ReportsCenter.jsx` | Enhanced with history, detail, daily lookup |
| `pages/LoginPage.jsx` | Stays (or minor updates) | Still needed for auth |

---

## Quick Reference — What Works Right Now

```bash
# Start all services
cd twin_engine_backend && make dev

# Frontend runs at http://localhost:5173
# Backend runs at http://localhost:8000

# Test accounts (from synthetic data):
# Manager:  synth_mgr_1 / synth123
# Waiter:   synth_waiter_1 / synth123
# Chef:     synth_chef_1 / synth123
# Host:     synth_host_1 / synth123
# Cashier:  synth_cashier_1 / synth123
```