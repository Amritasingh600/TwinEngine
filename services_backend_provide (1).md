# TwinEngine Hospitality — Backend Services & API Reference

> **Version:** 2.0.0  
> **Base URL:** `https://<host>/api/`  
> **Interactive Docs:** `/api/docs/` (Swagger UI) | `/api/redoc/` (ReDoc)  
> **OpenAPI Schema:** `/api/schema/`  
> **Last Updated:** 4 March 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication & Authorization](#2-authentication--authorization)
3. [Brand Management](#3-brand-management)
4. [Outlet Management](#4-outlet-management)
5. [Staff Management](#5-staff-management)
6. [Layout Twin — Service Nodes (3D Floor)](#6-layout-twin--service-nodes-3d-floor)
7. [Layout Twin — Service Flows](#7-layout-twin--service-flows)
8. [Order Engine — Orders](#8-order-engine--orders)
9. [Order Engine — Payments](#9-order-engine--payments)
10. [Order Engine — Table Status Trigger](#10-order-engine--table-status-trigger)
11. [Predictive Core — Sales Data](#11-predictive-core--sales-data)
12. [Predictive Core — Inventory](#12-predictive-core--inventory)
13. [Predictive Core — Staff Schedules](#13-predictive-core--staff-schedules)
14. [Predictive Core — ML Predictions](#14-predictive-core--ml-predictions)
15. [Insights Hub — Daily Summaries](#15-insights-hub--daily-summaries)
16. [Insights Hub — PDF Reports](#16-insights-hub--pdf-reports)
17. [Insights Hub — Daily Report Lookup](#17-insights-hub--daily-report-lookup)
18. [Cloudinary File Uploads](#18-cloudinary-file-uploads)
19. [Background Tasks (Celery)](#19-background-tasks-celery)
20. [System & Health](#20-system--health)
21. [WebSocket (Real-time) Endpoints](#21-websocket-real-time-endpoints)
22. [Rate Limiting & Throttling](#22-rate-limiting--throttling)
23. [Error Response Format](#23-error-response-format)

---

## 1. Overview

TwinEngine Hospitality backend is built with **Django REST Framework** and provides:

| Capability | Description |
|---|---|
| **Multi-tenant Management** | Brand → Outlet → Staff hierarchy with role-based access |
| **3D Digital Twin** | Service nodes (tables/stations) with 3D coordinates and color-coded status |
| **Order Lifecycle** | Full order tracking from PLACED → COMPLETED with auto table-color updates |
| **ML Predictions** | 6 machine learning models (demand, footfall, food, inventory, staffing, revenue) |
| **AI Reports** | Azure GPT-4o powered executive reports with PDF generation and Cloudinary storage |
| **File Storage** | Cloudinary CDN for file uploads (images, PDFs, CSVs) |
| **Real-time Updates** | WebSocket channels for live floor status and order notifications |
| **Background Jobs** | Celery workers for async report generation, model training, email alerts |

### Global Headers

| Header | Value | Required |
|---|---|---|
| `Content-Type` | `application/json` | Yes (for JSON bodies) |
| `Authorization` | `Bearer <access_token>` | Yes (except public endpoints) |

---

## 2. Authentication & Authorization

All auth endpoints are prefixed with `/api/auth/`.  
Token type: **JWT (JSON Web Token)** via `djangorestframework-simplejwt`.

| Setting | Value |
|---|---|
| Access Token Lifetime | 1 hour |
| Refresh Token Lifetime | 7 days |
| Token Rotation | Enabled |
| Brute-Force Protection | 5 failed attempts → 30 min lockout |

### 2.1 Login — Obtain JWT Tokens

```
POST /api/auth/token/
```

**Auth Required:** No  
**Rate Limit:** 10/min (auth scope)

**Request Body:**

```json
{
  "username": "manager_demo",
  "password": "manager123"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `username` | string | Yes | Account username |
| `password` | string | Yes | Account password |

**Response `200 OK`:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

| Field | Type | Description |
|---|---|---|
| `access` | string | JWT access token (1 hour) |
| `refresh` | string | JWT refresh token (7 days) |

---

### 2.2 Refresh Access Token

```
POST /api/auth/token/refresh/
```

**Auth Required:** No (uses refresh token)  
**Rate Limit:** 10/min

**Request Body:**

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `refresh` | string | Yes | Valid refresh token |

**Response `200 OK`:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

### 2.3 Verify Token

```
POST /api/auth/token/verify/
```

**Auth Required:** No

**Request Body:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response `200 OK`:** Empty body (token is valid)  
**Response `401 Unauthorized`:** Token is invalid or expired

---

### 2.4 Register New User

```
POST /api/auth/register/
```

**Auth Required:** No  
**Rate Limit:** 10/min

**Request Body:**

```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "outlet": 1,
  "role": "WAITER",
  "phone": "9876543210"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `username` | string | Yes | Unique username |
| `email` | string | Yes | Email address |
| `password` | string | Yes | Min 10 chars, validated against Django rules |
| `first_name` | string | No | First name |
| `last_name` | string | No | Last name |
| `outlet` | integer | Yes | Outlet ID to assign staff to |
| `role` | string | No | One of: `MANAGER`, `WAITER`, `CHEF`, `HOST`, `CASHIER` (default: `WAITER`) |
| `phone` | string | No | Phone number |

**Response `201 Created`:**

```json
{
  "id": 5,
  "user": {
    "id": 10,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "outlet": 1,
  "outlet_name": "Downtown Cafe",
  "brand_name": "Demo Restaurant Group",
  "role": "WAITER",
  "phone": "9876543210",
  "is_on_shift": false,
  "created_at": "2026-03-04T10:00:00Z"
}
```

---

### 2.5 Get / Update Current User Profile

```
GET  /api/auth/me/
PUT  /api/auth/me/
```

**Auth Required:** Yes

**GET Response `200 OK`:** Returns `UserProfile` object (same format as register response).

**PUT Request Body (only updatable fields):**

```json
{
  "phone": "9999999999",
  "is_on_shift": true
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone` | string | No | Updated phone number |
| `is_on_shift` | boolean | No | Shift status toggle |

**PUT Response `200 OK`:** Updated `UserProfile` object.

---

### 2.6 Change Password

```
POST /api/auth/change-password/
```

**Auth Required:** Yes  
**Rate Limit:** 10/min

**Request Body:**

```json
{
  "old_password": "current_password",
  "new_password": "NewSecure123!"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `old_password` | string | Yes | Current password |
| `new_password` | string | Yes | New password (min 10 chars) |

**Response `200 OK`:**

```json
{
  "message": "Password changed successfully."
}
```

---

### 2.7 Permission Classes

| Permission | Description |
|---|---|
| `IsOutletUser` | Users can only access data belonging to their assigned outlet |
| `IsManager` | Manager-only access |
| `IsManagerOrReadOnly` | Managers can write; other roles read-only |
| `IsStaffOrManager` | Staff and manager access |

---

## 3. Brand Management

```
GET    /api/brands/          — List all brands
POST   /api/brands/          — Create a brand
GET    /api/brands/{id}/     — Retrieve a brand
PUT    /api/brands/{id}/     — Full update
PATCH  /api/brands/{id}/     — Partial update
DELETE /api/brands/{id}/     — Delete a brand
GET    /api/brands/{id}/outlets/  — List outlets for a brand
GET    /api/brands/{id}/stats/    — Get brand statistics
```

**Auth Required:** Yes  
**Filters:** `subscription_tier`  
**Search:** `name`, `brand_code`, `contact_email`  
**Ordering:** `name`, `created_at`

### Create / Update Brand

**Request Body:**

```json
{
  "name": "Spice Republic Hospitality Group",
  "corporate_id": "SRHG-001",
  "contact_email": "admin@spicerepublic.com",
  "subscription_tier": "PRO"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Brand name |
| `corporate_id` | string | Yes | Unique corporate identifier |
| `contact_email` | string | Yes | Primary contact email |
| `subscription_tier` | string | No | `BASIC` / `PRO` / `ENTERPRISE` (default: `BASIC`) |

### List Response `200 OK`:

```json
[
  {
    "id": 1,
    "name": "Spice Republic Hospitality Group",
    "corporate_id": "SRHG-001",
    "subscription_tier": "PRO"
  }
]
```

### Detail Response `200 OK`:

```json
{
  "id": 1,
  "name": "Spice Republic Hospitality Group",
  "corporate_id": "SRHG-001",
  "contact_email": "admin@spicerepublic.com",
  "subscription_tier": "PRO",
  "outlet_count": 3,
  "created_at": "2026-02-28T10:00:00Z",
  "updated_at": "2026-03-01T12:00:00Z"
}
```

### Brand Stats `GET /api/brands/{id}/stats/`

**Response `200 OK`:**

```json
{
  "total_outlets": 3,
  "active_outlets": 2,
  "total_capacity": 200,
  "total_staff": 25
}
```

---

## 4. Outlet Management

```
GET    /api/outlets/               — List all outlets
POST   /api/outlets/               — Create an outlet
GET    /api/outlets/{id}/          — Retrieve an outlet
PUT    /api/outlets/{id}/          — Full update
PATCH  /api/outlets/{id}/          — Partial update
DELETE /api/outlets/{id}/          — Delete an outlet
GET    /api/outlets/{id}/staff/    — List staff for outlet
GET    /api/outlets/{id}/tables/   — List tables for outlet
GET    /api/outlets/{id}/floor_status/ — Get current floor status summary
```

**Auth Required:** Yes  
**Filters:** `brand`, `city`, `is_active`  
**Search:** `name`, `city`, `brand__name`  
**Ordering:** `name`, `created_at`

### Create / Update Outlet

**Request Body:**

```json
{
  "brand": 1,
  "name": "Koramangala Branch",
  "address": "80 Feet Road, Koramangala, Bangalore",
  "city": "Bangalore",
  "seating_capacity": 72,
  "opening_time": "10:00:00",
  "closing_time": "23:00:00",
  "is_active": true
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `brand` | integer | Yes | Brand FK |
| `name` | string | Yes | Outlet name |
| `address` | string | Yes | Full address |
| `city` | string | Yes | City name |
| `seating_capacity` | integer | No | Total seats (default: 0) |
| `opening_time` | time | Yes | Opening time (HH:MM:SS) |
| `closing_time` | time | Yes | Closing time (HH:MM:SS) |
| `is_active` | boolean | No | Active status (default: true) |

### Detail Response `200 OK`:

```json
{
  "id": 4,
  "brand": 1,
  "brand_name": "Spice Republic Hospitality Group",
  "name": "Koramangala Branch",
  "address": "80 Feet Road, Koramangala, Bangalore",
  "city": "Bangalore",
  "seating_capacity": 72,
  "opening_time": "10:00:00",
  "closing_time": "23:00:00",
  "is_active": true,
  "staff_count": 9,
  "created_at": "2026-02-28T10:00:00Z",
  "updated_at": "2026-03-01T12:00:00Z"
}
```

### Floor Status `GET /api/outlets/{id}/floor_status/`

**Response `200 OK`:**

```json
{
  "outlet": "Koramangala Branch",
  "total_nodes": 20,
  "status_breakdown": {
    "ready": 8,
    "waiting": 3,
    "served": 4,
    "issue": 2,
    "maintenance": 3
  }
}
```

---

## 5. Staff Management

```
GET    /api/staff/          — List all staff profiles
POST   /api/staff/          — Create a staff profile with user account
GET    /api/staff/{id}/     — Retrieve a staff profile
PUT    /api/staff/{id}/     — Full update
PATCH  /api/staff/{id}/     — Partial update
DELETE /api/staff/{id}/     — Delete staff profile and user account
```

**Auth Required:** Yes  
**Filters:** `outlet`, `outlet__brand`, `role`, `is_on_shift`  
**Search:** `user__username`, `user__email`, `outlet__name`

### Create Staff

**Request Body:**

```json
{
  "username": "waiter_1",
  "email": "waiter1@spicerepublic.com",
  "password": "SecurePass123!",
  "outlet": 4,
  "role": "WAITER",
  "phone": "9876543210"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `username` | string | Yes | Unique username |
| `email` | string | Yes | Email address |
| `password` | string | Yes | Password |
| `outlet` | integer | Yes | Outlet FK |
| `role` | string | No | `MANAGER` / `WAITER` / `CHEF` / `HOST` / `CASHIER` |
| `phone` | string | No | Phone number |

### Detail Response `200 OK`:

```json
{
  "id": 3,
  "user": {
    "id": 7,
    "username": "waiter_1",
    "email": "waiter1@spicerepublic.com",
    "first_name": "",
    "last_name": ""
  },
  "outlet": 4,
  "outlet_name": "Koramangala Branch",
  "brand_name": "Spice Republic Hospitality Group",
  "role": "WAITER",
  "phone": "9876543210",
  "is_on_shift": false,
  "created_at": "2026-03-01T10:00:00Z"
}
```

---

## 6. Layout Twin — Service Nodes (3D Floor)

```
GET    /api/nodes/                      — List all service nodes
POST   /api/nodes/                      — Create a service node
GET    /api/nodes/{id}/                 — Retrieve a node (with active order)
PUT    /api/nodes/{id}/                 — Full update
PATCH  /api/nodes/{id}/                 — Partial update
DELETE /api/nodes/{id}/                 — Delete a node
POST   /api/nodes/{id}/update-status/   — Update node status (color)
GET    /api/nodes/{id}/order-history/    — Get order history for a table
GET    /api/nodes/by_outlet/?outlet_id=X — Get nodes by outlet
```

**Auth Required:** Yes  
**Filters:** `outlet`, `node_type`, `current_status`, `is_active`  
**Search:** `name`, `outlet__name`  
**Ordering:** `name`, `current_status`, `updated_at`

### Create / Update Node

**Request Body:**

```json
{
  "outlet": 4,
  "name": "Table 1",
  "node_type": "TABLE",
  "pos_x": 2.5,
  "pos_y": 0.0,
  "pos_z": 3.0,
  "capacity": 4,
  "current_status": "BLUE",
  "is_active": true
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | Yes | Outlet FK |
| `name` | string | Yes | Display name |
| `node_type` | string | No | `TABLE` / `KITCHEN` / `WASH` / `BAR` / `ENTRY` (default: `TABLE`) |
| `pos_x` | float | No | 3D X coordinate (default: 0.0) |
| `pos_y` | float | No | 3D Y coordinate (default: 0.0) |
| `pos_z` | float | No | 3D Z coordinate (default: 0.0) |
| `capacity` | integer | No | Seating capacity (default: 4) |
| `current_status` | string | No | Color status (default: `BLUE`) |
| `is_active` | boolean | No | Active status (default: true) |

### Status Color Codes

| Status | Color | Meaning |
|---|---|---|
| `BLUE` | `#3B82F6` | Empty / Ready — table is free |
| `RED` | `#EF4444` | Occupied - Waiting — food not served |
| `GREEN` | `#22C55E` | Occupied - Served — customer eating |
| `YELLOW` | `#F59E0B` | Issue / Delay — wait > 15 min |
| `GREY` | `#6B7280` | Maintenance / Reserved |

### List Response `200 OK` (optimized for 3D rendering):

```json
[
  {
    "id": 1,
    "name": "Table 1",
    "node_type": "TABLE",
    "current_status": "BLUE",
    "capacity": 4,
    "position": { "x": 2.5, "y": 0.0, "z": 3.0 },
    "color": "#3B82F6"
  }
]
```

### Detail Response `200 OK` (includes active order):

```json
{
  "id": 1,
  "name": "Table 1",
  "outlet": 4,
  "outlet_name": "Koramangala Branch",
  "node_type": "TABLE",
  "pos_x": 2.5,
  "pos_y": 0.0,
  "pos_z": 3.0,
  "capacity": 4,
  "current_status": "BLUE",
  "is_active": true,
  "active_order": {
    "id": 12,
    "status": "PREPARING",
    "party_size": 3,
    "placed_at": "2026-03-04T12:30:00Z",
    "total": "1250.00"
  }
}
```

### Update Node Status `POST /api/nodes/{id}/update-status/`

**Request Body:**

```json
{
  "status": "RED"
}
```

**Response `200 OK`:**

```json
{
  "id": 1,
  "name": "Table 1",
  "status": "RED",
  "updated": true
}
```

### Order History `GET /api/nodes/{id}/order-history/?limit=20`

| Param | Type | Required | Description |
|---|---|---|---|
| `limit` | integer | No | Max results (default: 20) |

**Response `200 OK`:** Array of `OrderTicket` objects.

### Nodes by Outlet `GET /api/nodes/by_outlet/?outlet_id=4`

| Param | Type | Required | Description |
|---|---|---|---|
| `outlet_id` | integer | Yes | Outlet ID |

**Response `200 OK`:** Array of `ServiceNodeList` objects (3D-optimized).

---

## 7. Layout Twin — Service Flows

```
GET    /api/flows/          — List all flows
POST   /api/flows/          — Create a flow
GET    /api/flows/{id}/     — Retrieve a flow
PUT    /api/flows/{id}/     — Full update
PATCH  /api/flows/{id}/     — Partial update
DELETE /api/flows/{id}/     — Delete a flow
GET    /api/flows/graph/?outlet=X — Get full floor graph (nodes + flows)
```

**Auth Required:** Yes  
**Filters:** `source_node`, `target_node`, `flow_type`, `is_active`

### Create Flow

**Request Body:**

```json
{
  "source_node": 1,
  "target_node": 16,
  "flow_type": "ORDER_PATH",
  "is_active": true
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `source_node` | integer | Yes | Source ServiceNode FK |
| `target_node` | integer | Yes | Target ServiceNode FK (must differ from source) |
| `flow_type` | string | No | `FOOD_DELIVERY` / `DISH_RETURN` / `ORDER_PATH` / `CUSTOMER_FLOW` (default: `FOOD_DELIVERY`) |
| `is_active` | boolean | No | Active status (default: true) |

### Detail Response `200 OK`:

```json
{
  "id": 1,
  "source_node": 1,
  "source_node_name": "Table 1",
  "target_node": 16,
  "target_node_name": "Kitchen Station",
  "flow_type": "ORDER_PATH",
  "is_active": true,
  "created_at": "2026-03-01T10:00:00Z"
}
```

### Floor Graph `GET /api/flows/graph/?outlet=4`

| Param | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | No | Filter by outlet ID |

**Response `200 OK`:**

```json
{
  "nodes": [
    { "id": 1, "name": "Table 1", "node_type": "TABLE", "current_status": "BLUE", "capacity": 4, "position": {"x": 2.5, "y": 0, "z": 3}, "color": "#3B82F6" }
  ],
  "flows": [
    { "id": 1, "source_node": 1, "source_node_name": "Table 1", "target_node": 16, "target_node_name": "Kitchen Station", "flow_type": "ORDER_PATH", "is_active": true, "created_at": "..." }
  ]
}
```

---

## 8. Order Engine — Orders

```
GET    /api/orders/                       — List all orders
POST   /api/orders/                       — Create an order
GET    /api/orders/{id}/                  — Retrieve an order
PUT    /api/orders/{id}/                  — Full update
PATCH  /api/orders/{id}/                  — Partial update
DELETE /api/orders/{id}/                  — Delete an order
POST   /api/orders/{id}/update-status/    — Update order status
GET    /api/orders/active/?outlet=X       — Get all active orders
GET    /api/orders/by_table/?table_id=X   — Get orders for a table
GET    /api/orders/kitchen_queue/?outlet=X — Get kitchen queue
```

**Auth Required:** Yes  
**Filters:** `table`, `waiter`, `status`, `table__outlet`  
**Ordering:** `placed_at`, `total`, `status`

### Order Status Lifecycle

```
PLACED → PREPARING → READY → SERVED → COMPLETED
  ↓         ↓          ↓       ↓
  └─────────┴──────────┴───────┴──→ CANCELLED
```

> **Auto Table Color:** When an order status changes, the associated table's color (ServiceNode `current_status`) updates automatically via Django signals.

| Order Status | Table Color |
|---|---|
| `PLACED` / `PREPARING` / `READY` | `YELLOW` (waiting) |
| `SERVED` | `GREEN` (served) |
| `COMPLETED` / `CANCELLED` | `BLUE` (ready — if no other active orders) |
| Wait > 15 min | `RED` (needs attention) |

### Create Order

**Request Body:**

```json
{
  "table": 1,
  "waiter": 3,
  "customer_name": "Raj Sharma",
  "party_size": 4,
  "items": [
    { "name": "Butter Chicken", "qty": 2, "price": 350 },
    { "name": "Naan", "qty": 4, "price": 50 },
    { "name": "Masala Chai", "qty": 4, "price": 80 }
  ],
  "special_requests": "Less spicy, extra raita",
  "subtotal": 1220.00,
  "tax": 219.60,
  "total": 1439.60
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `table` | integer | Yes | ServiceNode FK (must be type TABLE) |
| `waiter` | integer | No | UserProfile FK (must be WAITER or MANAGER role) |
| `customer_name` | string | No | Customer name |
| `party_size` | integer | No | Number of guests (default: 1) |
| `items` | JSON array | No | List of ordered items |
| `special_requests` | string | No | Special instructions |
| `subtotal` | decimal | No | Subtotal amount |
| `tax` | decimal | No | Tax amount |
| `total` | decimal | No | Total amount |

### Detail Response `200 OK`:

```json
{
  "id": 12,
  "table": 1,
  "table_name": "Table 1",
  "waiter": 3,
  "waiter_name": "Ravi Kumar",
  "customer_name": "Raj Sharma",
  "party_size": 4,
  "items": [
    { "name": "Butter Chicken", "qty": 2, "price": 350 }
  ],
  "special_requests": "Less spicy, extra raita",
  "status": "PLACED",
  "status_display": "Order Placed",
  "placed_at": "2026-03-04T12:30:00Z",
  "served_at": null,
  "completed_at": null,
  "subtotal": "1220.00",
  "tax": "219.60",
  "total": "1439.60"
}
```

### Update Order Status `POST /api/orders/{id}/update-status/`

**Request Body:**

```json
{
  "status": "PREPARING"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `status` | string | Yes | `PLACED` / `PREPARING` / `READY` / `SERVED` / `COMPLETED` / `CANCELLED` |

> Invalid transitions (e.g., `SERVED` → `PLACED`) return `400 Bad Request`.

**Response `200 OK`:** Full `OrderTicket` object with updated status.

### Active Orders `GET /api/orders/active/?outlet=4`

Returns all orders not in `COMPLETED` or `CANCELLED` status.

| Param | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | No | Filter by outlet ID |

### Orders by Table `GET /api/orders/by_table/?table_id=1&active_only=true`

| Param | Type | Required | Description |
|---|---|---|---|
| `table_id` | integer | Yes | Table (ServiceNode) ID |
| `active_only` | boolean | No | Only active orders (default: false) |

### Kitchen Queue `GET /api/orders/kitchen_queue/?outlet=4`

Returns orders in `PLACED` or `PREPARING` status, ordered by `placed_at` (FIFO).

---

## 9. Order Engine — Payments

```
GET    /api/payments/             — List all payments
POST   /api/payments/             — Create a payment
GET    /api/payments/{id}/        — Retrieve a payment
PUT    /api/payments/{id}/        — Update a payment
PATCH  /api/payments/{id}/        — Partial update
DELETE /api/payments/{id}/        — Delete a payment
GET    /api/payments/summary/     — Get payment summary statistics
```

**Auth Required:** Yes  
**Filters:** `order`, `method`, `status`  
**Ordering:** `created_at`, `amount`

> **Auto Order Completion:** When total successful payments ≥ order total, the order automatically moves to `COMPLETED`.

### Create Payment

**Request Body:**

```json
{
  "order": 12,
  "amount": 1439.60,
  "method": "UPI",
  "transaction_id": "TXN-2026030412345",
  "tip_amount": 100.00
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `order` | integer | Yes | OrderTicket FK |
| `amount` | decimal | Yes | Payment amount |
| `method` | string | No | `CASH` / `CARD` / `UPI` / `WALLET` / `SPLIT` (default: `CASH`) |
| `transaction_id` | string | No | External transaction reference |
| `tip_amount` | decimal | No | Tip amount (default: 0) |

### Detail Response `200 OK`:

```json
{
  "id": 5,
  "order": 12,
  "order_table": "Table 1",
  "amount": "1439.60",
  "method": "UPI",
  "status": "SUCCESS",
  "status_display": "Success",
  "transaction_id": "TXN-2026030412345",
  "tip_amount": "100.00",
  "created_at": "2026-03-04T13:00:00Z"
}
```

### Payment Status Values

| Status | Description |
|---|---|
| `PENDING` | Payment initiated |
| `SUCCESS` | Payment completed |
| `FAILED` | Payment failed |
| `REFUNDED` | Payment refunded |

### Payment Summary `GET /api/payments/summary/?outlet=4&date=2026-03-04`

| Param | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | No | Filter by outlet ID |
| `date` | date | No | Filter by date (YYYY-MM-DD) |

**Response `200 OK`:**

```json
{
  "total_revenue": 47575.50,
  "total_tips": 3200.00,
  "transaction_count": 31,
  "by_method": [
    { "method": "CASH", "count": 8, "total": 12500.00 },
    { "method": "CARD", "count": 10, "total": 18000.00 },
    { "method": "UPI", "count": 9, "total": 13075.50 },
    { "method": "WALLET", "count": 4, "total": 4000.00 }
  ]
}
```

---

## 10. Order Engine — Table Status Trigger

```
POST /api/table/trigger/
```

**Auth Required:** Yes

Manually set a table's status color (bypasses order-based auto-updates).

**Request Body:**

```json
{
  "node_id": 1,
  "status": "GREY"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `node_id` | integer | Yes | ServiceNode ID (must exist) |
| `status` | string | Yes | `BLUE` / `RED` / `GREEN` / `YELLOW` / `GREY` |

**Response `201 Created`:**

```json
{
  "updated": true,
  "node_id": 1,
  "old_status": "BLUE",
  "new_status": "GREY"
}
```

---

## 11. Predictive Core — Sales Data

```
GET    /api/sales-data/                          — List all sales data
POST   /api/sales-data/                          — Create a sales data record
GET    /api/sales-data/{id}/                     — Retrieve a record
PUT    /api/sales-data/{id}/                     — Update a record
PATCH  /api/sales-data/{id}/                     — Partial update
DELETE /api/sales-data/{id}/                     — Delete a record
GET    /api/sales-data/trends/?outlet=X&days=30  — Sales trends over time
GET    /api/sales-data/hourly_pattern/?outlet=X  — Average hourly patterns
```

**Auth Required:** Yes  
**Filters:** `outlet`, `date`, `day_of_week`, `is_holiday`  
**Ordering:** `date`, `hour`, `total_revenue`

### Create Sales Data

**Request Body:**

```json
{
  "outlet": 4,
  "date": "2026-03-04",
  "hour": 12,
  "total_orders": 14,
  "total_revenue": 12500.00,
  "avg_ticket_size": 892.86,
  "avg_wait_time_minutes": 8.5,
  "category_sales": {
    "Main Course": 6500.00,
    "Starters": 2800.00,
    "Beverages": 2200.00,
    "Desserts": 1000.00
  },
  "top_items": ["Butter Chicken", "Paneer Tikka", "Masala Chai"],
  "day_of_week": 2,
  "is_holiday": false,
  "weather_condition": "Sunny"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | Yes | Outlet FK |
| `date` | date | Yes | Record date |
| `hour` | integer | Yes | Hour of day (0–23) |
| `total_orders` | integer | No | Total orders in this hour |
| `total_revenue` | decimal | No | Revenue in this hour |
| `avg_ticket_size` | decimal | No | Average ticket size |
| `avg_wait_time_minutes` | float | No | Average wait time (minutes) |
| `category_sales` | JSON object | No | Revenue per food category |
| `top_items` | JSON array | No | Top selling items |
| `day_of_week` | integer | Yes | 0=Monday, 6=Sunday |
| `is_holiday` | boolean | No | Holiday flag |
| `weather_condition` | string | No | Weather description |

### Sales Trends `GET /api/sales-data/trends/?outlet=4&days=30`

| Param | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | No | Filter by outlet |
| `days` | integer | No | Lookback period (default: 30) |

**Response `200 OK`:**

```json
[
  { "date": "2026-02-25", "orders": 48, "revenue": 42000.00, "avg_ticket": 875.00 },
  { "date": "2026-02-26", "orders": 55, "revenue": 51000.00, "avg_ticket": 927.27 }
]
```

### Hourly Pattern `GET /api/sales-data/hourly_pattern/?outlet=4&day_of_week=5`

| Param | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | No | Filter by outlet |
| `day_of_week` | integer | No | Day of week (0=Mon, 6=Sun) |

**Response `200 OK`:**

```json
[
  { "hour": 11, "avg_orders": 5.2, "avg_revenue": 4500.00, "avg_wait": 6.3 },
  { "hour": 12, "avg_orders": 12.8, "avg_revenue": 11200.00, "avg_wait": 9.1 }
]
```

---

## 12. Predictive Core — Inventory

```
GET    /api/inventory/                       — List all inventory items
POST   /api/inventory/                       — Create an item
GET    /api/inventory/{id}/                  — Retrieve an item
PUT    /api/inventory/{id}/                  — Full update
PATCH  /api/inventory/{id}/                  — Partial update
DELETE /api/inventory/{id}/                  — Delete an item
POST   /api/inventory/{id}/adjust/           — Adjust quantity (add/subtract)
GET    /api/inventory/low_stock/?outlet=X    — Get low-stock items
GET    /api/inventory/expiring_soon/?days=7  — Get items expiring soon
```

**Auth Required:** Yes  
**Filters:** `outlet`, `category`  
**Search:** `name`  
**Ordering:** `name`, `current_quantity`, `updated_at`

### Create Inventory Item

**Request Body:**

```json
{
  "outlet": 4,
  "name": "Chicken Breast",
  "category": "MEAT",
  "unit": "KG",
  "current_quantity": 15.0,
  "reorder_threshold": 5.0,
  "par_level": 25.0,
  "unit_cost": 320.00,
  "expiry_date": "2026-03-10",
  "last_restocked": "2026-03-02T08:00:00Z"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | Yes | Outlet FK |
| `name` | string | Yes | Item name |
| `category` | string | No | `PRODUCE` / `DAIRY` / `MEAT` / `DRY` / `BEVERAGE` / `SUPPLIES` |
| `unit` | string | No | `KG` / `L` / `PCS` / `BAGS` / `BOXES` |
| `current_quantity` | float | No | Current stock level |
| `reorder_threshold` | float | No | Alert threshold (default: 10.0) |
| `par_level` | float | No | Ideal stock level (default: 50.0) |
| `unit_cost` | decimal | No | Cost per unit |
| `expiry_date` | date | No | Expiry date |
| `last_restocked` | datetime | No | Last restock timestamp |

### Detail Response (includes computed `is_low_stock`):

```json
{
  "id": 1,
  "outlet": 4,
  "outlet_name": "Koramangala Branch",
  "name": "Chicken Breast",
  "category": "MEAT",
  "unit": "KG",
  "current_quantity": 15.0,
  "reorder_threshold": 5.0,
  "par_level": 25.0,
  "unit_cost": "320.00",
  "expiry_date": "2026-03-10",
  "last_restocked": "2026-03-02T08:00:00Z",
  "is_low_stock": false,
  "updated_at": "2026-03-04T10:00:00Z"
}
```

### Adjust Quantity `POST /api/inventory/{id}/adjust/`

**Request Body:**

```json
{
  "quantity_change": -3.5,
  "reason": "Used for dinner service"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `quantity_change` | float | Yes | Positive = add, Negative = subtract |
| `reason` | string | No | Reason for adjustment |

> If `quantity_change > 0`, `last_restocked` is auto-set to now.

**Response `200 OK`:** Updated `InventoryItem` object.

### Low Stock `GET /api/inventory/low_stock/?outlet=4`

Returns items where `current_quantity ≤ reorder_threshold`.

### Expiring Soon `GET /api/inventory/expiring_soon/?days=7&outlet=4`

| Param | Type | Required | Description |
|---|---|---|---|
| `days` | integer | No | Days until expiry (default: 7) |
| `outlet` | integer | No | Filter by outlet |

---

## 13. Predictive Core — Staff Schedules

```
GET    /api/schedules/                     — List all schedules
POST   /api/schedules/                     — Create a schedule
GET    /api/schedules/{id}/                — Retrieve a schedule
PUT    /api/schedules/{id}/                — Full update
PATCH  /api/schedules/{id}/                — Partial update
DELETE /api/schedules/{id}/                — Delete a schedule
POST   /api/schedules/{id}/check-in/       — Record staff check-in
POST   /api/schedules/{id}/check-out/      — Record staff check-out
GET    /api/schedules/today/?outlet=X      — Get today's schedules
GET    /api/schedules/by_staff/?staff_id=X — Get schedules for a staff member
```

**Auth Required:** Yes  
**Filters:** `staff`, `staff__outlet`, `date`, `shift`, `is_confirmed`  
**Ordering:** `date`, `start_time`

### Create Schedule

**Request Body:**

```json
{
  "staff": 3,
  "date": "2026-03-04",
  "shift": "MORNING",
  "start_time": "06:00:00",
  "end_time": "14:00:00",
  "is_ai_suggested": true,
  "notes": "AI recommended extra waiter for expected rush"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `staff` | integer | Yes | UserProfile FK |
| `date` | date | Yes | Schedule date |
| `shift` | string | No | `MORNING` / `AFTERNOON` / `NIGHT` / `SPLIT` (default: `MORNING`) |
| `start_time` | time | Yes | Shift start time |
| `end_time` | time | Yes | Shift end time |
| `is_ai_suggested` | boolean | No | Whether AI suggested this schedule |
| `notes` | string | No | Notes or comments |

### Detail Response `200 OK`:

```json
{
  "id": 5,
  "staff": 3,
  "staff_name": "Ravi Kumar",
  "staff_role": "WAITER",
  "date": "2026-03-04",
  "shift": "MORNING",
  "start_time": "06:00:00",
  "end_time": "14:00:00",
  "is_confirmed": false,
  "checked_in": null,
  "checked_out": null,
  "is_ai_suggested": true,
  "notes": "AI recommended extra waiter for expected rush",
  "created_at": "2026-03-03T18:00:00Z"
}
```

### Check-In / Check-Out `POST /api/schedules/{id}/check-in/` | `POST /api/schedules/{id}/check-out/`

**Request Body:** None (timestamps auto-set to `now()`)

**Response `200 OK`:** Updated schedule object with `checked_in` / `checked_out` timestamps.

---

## 14. Predictive Core — ML Predictions

All prediction endpoints require authentication and accept common query parameters.  
**Rate Limit:** 60/min (predictions scope)

### Common Query Parameters

| Param | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | Yes | Outlet ID |
| `date` | date | No | Target date in YYYY-MM-DD (default: today) |

---

### 14.1 Busy Hours Prediction

```
GET /api/predictions/busy-hours/?outlet=4&date=2026-03-04
```

Predicts the expected order volume per hour using a **RandomForestClassifier**.

**Response `200 OK`:**

```json
{
  "outlet_id": 4,
  "date": "2026-03-04",
  "hourly_forecast": [
    { "hour": 11, "predicted_orders": 8, "is_busy": false },
    { "hour": 12, "predicted_orders": 14, "is_busy": true },
    { "hour": 13, "predicted_orders": 12, "is_busy": true }
  ],
  "peak_hour": 12,
  "total_predicted_orders": 62,
  "model_type": "RandomForestClassifier"
}
```

---

### 14.2 Footfall Prediction

```
GET /api/predictions/footfall/?outlet=4&date=2026-03-04
```

Forecasts expected guest count per hour using a **GradientBoostingRegressor**.

**Response `200 OK`:**

```json
{
  "outlet_id": 4,
  "date": "2026-03-04",
  "hourly_guests": [
    { "hour": 12, "predicted_guests": 28 },
    { "hour": 13, "predicted_guests": 22 }
  ],
  "total_predicted_guests": 145,
  "model_type": "GradientBoostingRegressor"
}
```

---

### 14.3 Food Demand Prediction

```
GET /api/predictions/food-demand/?outlet=4&date=2026-03-04
```

Predicts per-category order volume and revenue using a **RandomForestRegressor**.

**Response `200 OK`:**

```json
{
  "outlet_id": 4,
  "date": "2026-03-04",
  "category_forecast": {
    "Main Course": { "predicted_orders": 35, "predicted_revenue": 8750.00 },
    "Starters": { "predicted_orders": 22, "predicted_revenue": 3300.00 },
    "Beverages": { "predicted_orders": 40, "predicted_revenue": 4000.00 },
    "Desserts": { "predicted_orders": 12, "predicted_revenue": 1800.00 }
  },
  "model_type": "RandomForestRegressor"
}
```

---

### 14.4 Inventory Alerts

```
GET /api/predictions/inventory-alerts/?outlet=4
```

AI-based inventory depletion forecast using **GradientBoostingRegressor** + rule-based urgency.

> **Note:** Does not require `date` parameter — analyzes current inventory state.

**Response `200 OK`:**

```json
{
  "outlet_id": 4,
  "inventory_alerts": [
    {
      "item": "Chicken Breast",
      "current_quantity": 5.0,
      "unit": "KG",
      "daily_consumption_rate": 2.3,
      "days_until_stockout": 2,
      "urgency": "CRITICAL",
      "suggested_order_qty": 15.0,
      "expiry_warning": false
    }
  ],
  "expiring_soon": [
    { "item": "Fresh Cream", "expiry_date": "2026-03-05", "days_left": 1 }
  ],
  "total_alerts": 5
}
```

| Urgency Level | Criteria |
|---|---|
| `CRITICAL` | ≤ 2 days until stockout OR below reorder threshold |
| `HIGH` | 3–4 days until stockout |
| `MODERATE` | 5–7 days until stockout |
| `OK` | > 7 days until stockout |

---

### 14.5 Staffing Prediction

```
GET /api/predictions/staffing/?outlet=4&date=2026-03-04
```

Recommends optimal staff count per shift using a **RandomForestRegressor** + demand-based ratios.

**Response `200 OK`:**

```json
{
  "outlet_id": 4,
  "date": "2026-03-04",
  "staffing_recommendation": {
    "MORNING": {
      "recommended_waiters": 2,
      "recommended_chefs": 2,
      "predicted_orders": 35,
      "predicted_guests": 50
    },
    "AFTERNOON": {
      "recommended_waiters": 3,
      "recommended_chefs": 3,
      "predicted_orders": 55,
      "predicted_guests": 80
    },
    "NIGHT": {
      "recommended_waiters": 1,
      "recommended_chefs": 1,
      "predicted_orders": 12,
      "predicted_guests": 15
    }
  },
  "model_type": "RandomForestRegressor"
}
```

---

### 14.6 Revenue Forecast

```
GET /api/predictions/revenue/?outlet=4&date=2026-03-04&days=7
```

Forecasts daily revenue using a **GradientBoostingRegressor**.

| Param | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | Yes | Outlet ID |
| `date` | date | No | Start date (default: today) |
| `days` | integer | No | Number of forecast days (default: 7) |

**Response `200 OK`:**

```json
{
  "outlet_id": 4,
  "start_date": "2026-03-04",
  "forecast_days": 7,
  "daily_revenue_forecast": [
    { "date": "2026-03-04", "predicted_revenue": 48000.00 },
    { "date": "2026-03-05", "predicted_revenue": 52000.00 },
    { "date": "2026-03-06", "predicted_revenue": 45000.00 }
  ],
  "total_predicted_revenue": 325000.00,
  "model_type": "GradientBoostingRegressor"
}
```

---

### 14.7 Prediction Dashboard (All Models Combined)

```
GET /api/predictions/dashboard/?outlet=4&date=2026-03-04
```

Returns aggregated results from all 6 prediction models in a single call.

**Response `200 OK`:**

```json
{
  "outlet_id": 4,
  "date": "2026-03-04",
  "busy_hours": { ... },
  "footfall": { ... },
  "food_demand": { ... },
  "inventory_alerts": { ... },
  "staffing": { ... },
  "revenue": { ... }
}
```

---

### 14.8 Train ML Models

```
POST /api/predictions/train/?outlet=4
```

**Auth Required:** Yes  
**Rate Limit:** 5/min (training scope)  
**Default Behavior:** Async (Celery task) — returns `202 Accepted` with `task_id`.  
**Sync Mode:** Add `?sync=true` to run in-request.

| Param | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | Yes | Outlet ID to train models for |
| `sync` | boolean | No | Run synchronously (default: false) |

**Async Response `202 Accepted`:**

```json
{
  "status": "training dispatched",
  "task_id": "a3b2c1d0-e5f6-7890-abcd-ef1234567890",
  "poll_url": "/api/tasks/a3b2c1d0-e5f6-7890-abcd-ef1234567890/"
}
```

**Sync Response `200 OK`:**

```json
{
  "status": "training complete",
  "results": {
    "busy_hours": { "status": "trained", "samples": 91, "accuracy": 0.85 },
    "footfall": { "status": "trained", "samples": 91, "r2_score": 0.78 },
    "food_demand": { "status": "trained", "samples": 91, "r2_score": 0.82 },
    "inventory": { "status": "trained", "samples": 20 },
    "staffing": { "status": "trained", "samples": 29 },
    "revenue": { "status": "trained", "samples": 91, "r2_score": 0.80 }
  }
}
```

> Trained model files are saved as `.joblib` in `ml_models/` — per outlet, per model type.

---

## 15. Insights Hub — Daily Summaries

```
GET    /api/summaries/                                   — List all daily summaries
POST   /api/summaries/                                   — Create a daily summary
GET    /api/summaries/{id}/                              — Retrieve a summary
PUT    /api/summaries/{id}/                              — Full update
PATCH  /api/summaries/{id}/                              — Partial update
DELETE /api/summaries/{id}/                              — Delete a summary
GET    /api/summaries/trends/?outlet=X&days=30           — Performance trends
GET    /api/summaries/compare/?brand=X&days=7            — Compare outlets
GET    /api/summaries/today/?outlet=X                    — Get today's summaries
```

**Auth Required:** Yes  
**Filters:** `outlet`, `date`, `outlet__brand`  
**Ordering:** `date`, `total_revenue`, `total_orders`

### Create Daily Summary

**Request Body:**

```json
{
  "outlet": 4,
  "date": "2026-03-04",
  "total_revenue": 47575.50,
  "total_orders": 50,
  "avg_ticket_size": 951.51,
  "total_tips": 3200.00,
  "total_guests": 153,
  "avg_table_turnover_time": 45.0,
  "avg_wait_time": 12.5,
  "peak_hour": 20,
  "peak_revenue": 8500.00,
  "delayed_orders": 3,
  "cancelled_orders": 6,
  "sales_by_category": {
    "Main Course": 22000.00,
    "Starters": 8500.00,
    "Beverages": 12000.00,
    "Desserts": 5075.50
  },
  "top_selling_items": ["Butter Chicken", "Paneer Tikka", "Masala Chai"],
  "staff_count": 9,
  "revenue_per_staff": 5286.17
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `outlet` | integer | Yes | Outlet FK |
| `date` | date | Yes | Summary date |
| `total_revenue` | decimal | No | Total revenue |
| `total_orders` | integer | No | Total orders count |
| `avg_ticket_size` | decimal | No | Average ticket size |
| `total_tips` | decimal | No | Total tips earned |
| `total_guests` | integer | No | Total guests served |
| `avg_table_turnover_time` | float | No | Avg turnover time (minutes) |
| `avg_wait_time` | float | No | Avg wait time (minutes) |
| `peak_hour` | integer | No | Peak revenue hour (0–23) |
| `peak_revenue` | decimal | No | Revenue during peak hour |
| `delayed_orders` | integer | No | Count of delayed orders |
| `cancelled_orders` | integer | No | Count of cancelled orders |
| `sales_by_category` | JSON | No | Revenue by food category |
| `top_selling_items` | JSON | No | Top selling items list |
| `staff_count` | integer | No | Staff on duty |
| `revenue_per_staff` | decimal | No | Revenue per staff member |

### Trends `GET /api/summaries/trends/?outlet=4&days=30`

**Response `200 OK`:**

```json
[
  {
    "date": "2026-02-25",
    "revenue": 42000.00,
    "orders": 48,
    "guests": 140,
    "avg_wait": 11.2
  }
]
```

### Compare Outlets `GET /api/summaries/compare/?brand=1&days=7`

**Response `200 OK`:**

```json
[
  {
    "outlet": 4,
    "outlet__name": "Koramangala Branch",
    "total_revenue": 285000.00,
    "total_orders": 310,
    "avg_ticket": 919.35,
    "avg_wait": 10.5
  }
]
```

---

## 16. Insights Hub — PDF Reports

```
GET    /api/reports/                — List all PDF reports
POST   /api/reports/                — Create a report record
GET    /api/reports/{id}/           — Retrieve a report
PUT    /api/reports/{id}/           — Update a report
PATCH  /api/reports/{id}/           — Partial update
DELETE /api/reports/{id}/           — Delete a report
POST   /api/reports/generate/       — Generate AI report (GPT-4o pipeline)
```

**Auth Required:** Yes  
**Rate Limit:** 10/min (reports scope)  
**Filters:** `outlet`, `report_type`, `status`, `outlet__brand`  
**Ordering:** `start_date`, `created_at`

### Generate AI Report `POST /api/reports/generate/`

This triggers the full 5-step pipeline:

1. **Collect** raw data from all models (orders, payments, inventory, staff, sales)
2. **Analyze** with Azure GPT-4o (or local fallback)
3. **Build** professional PDF using ReportLab
4. **Upload** PDF to Cloudinary
5. **Return** report with download URL

**Default:** Async via Celery → returns `202 Accepted` with `task_id`  
**Sync Mode:** Add `?sync=true` → returns `201 Created` with complete report

**Request Body:**

```json
{
  "outlet_id": 4,
  "report_type": "DAILY",
  "start_date": "2026-03-04",
  "end_date": "2026-03-04"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `outlet_id` | integer | Yes | Outlet ID (must exist) |
| `report_type` | string | No | `DAILY` / `WEEKLY` / `MONTHLY` / `CUSTOM` (default: `DAILY`) |
| `start_date` | date | Yes | Report start date |
| `end_date` | date | No | Report end date (default: same as start_date) |

**Async Response `202 Accepted`:**

```json
{
  "id": 5,
  "outlet": 4,
  "outlet_name": "Koramangala Branch",
  "report_type": "DAILY",
  "start_date": "2026-03-04",
  "end_date": "2026-03-04",
  "status": "GENERATING",
  "task_id": "a3b2c1d0-e5f6-7890-abcd-ef1234567890",
  "poll_url": "/api/tasks/a3b2c1d0-e5f6-7890-abcd-ef1234567890/"
}
```

**Sync Response `201 Created`:**

```json
{
  "id": 5,
  "outlet": 4,
  "outlet_name": "Koramangala Branch",
  "report_type": "DAILY",
  "start_date": "2026-03-04",
  "end_date": "2026-03-04",
  "cloudinary_url": "https://res.cloudinary.com/.../report.pdf",
  "gpt_summary": "The operations at Koramangala Branch showed strong performance...",
  "insights": [
    "Revenue was Rs.47,575.50 across 50 orders",
    "Peak hours were 8-10 PM with 65% of orders"
  ],
  "recommendations": [
    "Increase kitchen staff during peak hours (8-10 PM)",
    "Restock Chicken Breast and Paneer — critical stock levels"
  ],
  "status": "COMPLETED",
  "error_message": null,
  "generated_by": "gpt-4o-2024-11-20",
  "created_at": "2026-03-04T14:00:00Z",
  "completed_at": "2026-03-04T14:00:15Z"
}
```

### Report Status Values

| Status | Description |
|---|---|
| `PENDING` | Report queued |
| `GENERATING` | Pipeline running |
| `COMPLETED` | Report ready with PDF and insights |
| `FAILED` | Generation failed (see `error_message`) |

---

## 17. Insights Hub — Daily Report Lookup

```
GET /api/reports/daily/?date=2026-03-04&outlet=4
```

**Auth Required:** Yes

Retrieve the latest completed AI report for a given date. If no report exists, returns a `404` with instructions to generate one.

| Param | Type | Required | Description |
|---|---|---|---|
| `date` | date | No | Report date (default: today) |
| `outlet` | integer | No | Outlet ID |

**Response `200 OK` (when report exists):**

```json
{
  "report_id": 5,
  "report_text": "The operations at Koramangala Branch showed strong performance...",
  "insights": ["Revenue was Rs.47,575.50...", "..."],
  "recommendations": ["Increase kitchen staff...", "..."],
  "generated_at": "2026-03-04T14:00:15Z",
  "generated_by": "gpt-4o-2024-11-20",
  "cloudinary_url": "https://res.cloudinary.com/.../report.pdf"
}
```

**Response `404 Not Found` (when no report):**

```json
{
  "error": "No report found for date 2026-03-04. Use POST /api/reports/generate/ to create one.",
  "hint": {
    "url": "/api/reports/generate/",
    "method": "POST",
    "body": {
      "outlet_id": 4,
      "report_type": "DAILY",
      "start_date": "2026-03-04"
    }
  }
}
```

---

## 18. Cloudinary File Uploads

All upload endpoints use **multipart/form-data** and require JWT authentication.  
**Rate Limit:** 20/min (uploads scope)  
**Max file size:** 10 MB per file

---

### 18.1 Single File Upload

```
POST /api/upload/
```

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | Yes | File to upload (image, PDF, CSV, etc.) — max 10 MB |
| `folder` | string | No | Cloudinary sub-folder (default: `uploads`) |

**Response `201 Created`:**

```json
{
  "success": true,
  "url": "https://res.cloudinary.com/dfhl1aopy/raw/upload/.../report.pdf",
  "public_id": "twinengine/uploads/report",
  "resource_type": "raw",
  "original_filename": "report.pdf",
  "format": "pdf",
  "bytes": 12345
}
```

---

### 18.2 Multi-File Upload

```
POST /api/upload/multi/
```

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `files` | file[] | Yes | List of files (max 10 files, each max 10 MB) |
| `folder` | string | No | Cloudinary sub-folder (default: `uploads`) |

**Response `201 Created`:**

```json
{
  "uploaded": [
    {
      "success": true,
      "url": "https://res.cloudinary.com/...",
      "public_id": "twinengine/uploads/image1",
      "resource_type": "image"
    }
  ],
  "failed": [
    { "filename": "corrupt.jpg", "error": "Upload failed" }
  ]
}
```

---

### 18.3 Delete File

```
DELETE /api/upload/delete/
```

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "public_id": "twinengine/uploads/report",
  "resource_type": "raw"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `public_id` | string | Yes | Cloudinary public ID |
| `resource_type` | string | Yes | `image` / `raw` / `video` |

**Response `200 OK`:**

```json
{
  "success": true
}
```

---

## 19. Background Tasks (Celery)

### Task Status Polling

```
GET /api/tasks/{task_id}/
```

**Auth Required:** Yes

Poll the status of any Celery background task.

**Response `200 OK`:**

```json
{
  "task_id": "a3b2c1d0-e5f6-7890-abcd-ef1234567890",
  "status": "SUCCESS",
  "result": { ... },
  "error": null,
  "date_done": "2026-03-04T14:00:15Z"
}
```

| Field | Type | Description |
|---|---|---|
| `task_id` | string | Celery task UUID |
| `status` | string | `PENDING` / `STARTED` / `PROGRESS` / `SUCCESS` / `FAILURE` / `RETRY` / `REVOKED` |
| `result` | object | Task result (when SUCCESS) |
| `error` | string | Error message (when FAILURE) |
| `date_done` | datetime | Completion timestamp |

### Background Tasks Summary

| Task | Trigger | Description |
|---|---|---|
| `train_models_for_outlet` | `POST /api/predictions/train/` | Retrain all 6 ML models for one outlet |
| `train_all_outlets` | Celery Beat (daily 02:00) | Nightly retrain for all active outlets |
| `send_inventory_alerts` | Celery Beat (daily 07:00) | Email low-stock alerts per outlet |
| `send_inventory_alerts_all` | Celery Beat (daily 07:00) | Morning inventory sweep — all outlets |
| `generate_report_task` | `POST /api/reports/generate/` | Full GPT-4o report pipeline (async) |
| `email_report_task` | On report completion | Email report download link to brand contact |

### Celery Beat Schedule

| Job | Schedule | Task |
|---|---|---|
| `nightly-model-retraining` | Daily at 02:00 | `train_all_outlets` |
| `morning-inventory-alerts` | Daily at 07:00 | `send_inventory_alerts_all` |

---

## 20. System & Health

### Health Check

```
GET /api/health/
```

**Auth Required:** No

Used by Docker HEALTHCHECK, Azure App Service, and Render.

**Response `200 OK`:**

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected"
}
```

**Response `503 Service Unavailable`:**

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "unavailable"
}
```

### API Root

```
GET /api/
```

**Auth Required:** No

Returns a directory of all available endpoints.

### API Documentation

| Endpoint | Description |
|---|---|
| `GET /api/docs/` | Swagger UI — interactive API explorer |
| `GET /api/redoc/` | ReDoc — readable API documentation |
| `GET /api/schema/` | OpenAPI 3.0 JSON schema (71 paths, 120 operations) |

### Django Admin

```
GET /admin/
```

Full admin panel with color-coded badges, inline forms, and custom actions for all 12 models.

---

## 21. WebSocket (Real-time) Endpoints

WebSocket connections provide real-time updates without polling. Connect via `ws://` (dev) or `wss://` (prod).

### 21.1 Floor Status Updates

```
ws://<host>/ws/floor/<outlet_id>/
```

Receives real-time table/node status changes for 3D floor visualization.

**Incoming Messages (server → client):**

```json
{
  "type": "node_status_change",
  "node_id": 1,
  "name": "Table 1",
  "old_status": "BLUE",
  "new_status": "YELLOW",
  "timestamp": "2026-03-04T12:30:00Z"
}
```

```json
{
  "type": "wait_time_alert",
  "node_id": 1,
  "name": "Table 1",
  "wait_minutes": 18,
  "status": "RED"
}
```

---

### 21.2 Order Updates

```
ws://<host>/ws/orders/                — Global order stream
ws://<host>/ws/orders/<outlet_id>/    — Outlet-specific orders
```

Receives real-time order lifecycle events.

**Incoming Messages (server → client):**

```json
{
  "type": "order_created",
  "order_id": 12,
  "table": "Table 1",
  "status": "PLACED",
  "party_size": 4,
  "timestamp": "2026-03-04T12:30:00Z"
}
```

```json
{
  "type": "order_updated",
  "order_id": 12,
  "old_status": "PLACED",
  "new_status": "PREPARING",
  "timestamp": "2026-03-04T12:35:00Z"
}
```

```json
{
  "type": "order_completed",
  "order_id": 12,
  "table": "Table 1",
  "total": "1439.60",
  "timestamp": "2026-03-04T13:30:00Z"
}
```

---

## 22. Rate Limiting & Throttling

| Scope | Rate | Applied To |
|---|---|---|
| **Anonymous** | 30 requests/min | All unauthenticated requests |
| **Authenticated** | 120 requests/min | All authenticated requests |
| **Auth** | 10 requests/min | Login, register, password change, token refresh |
| **Predictions** | 60 requests/min | All 8 prediction endpoints |
| **Reports** | 10 requests/min | PDF report generation |
| **Uploads** | 20 requests/min | Cloudinary file operations |
| **Training** | 5 requests/min | ML model retraining |

### Brute-Force Protection

- **Engine:** `django-axes`
- **Lock After:** 5 failed login attempts
- **Cooloff Period:** 30 minutes
- **Lockout By:** Username + IP combination
- **Reset:** Counter resets on successful login

### Security Headers (on every response)

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=()` |

---

## 23. Error Response Format

All API errors follow a consistent format:

### Validation Error `400 Bad Request`

```json
{
  "field_name": ["Error message for this field."],
  "another_field": ["Required field."]
}
```

### Authentication Error `401 Unauthorized`

```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid"
}
```

### Permission Error `403 Forbidden`

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### Not Found `404 Not Found`

```json
{
  "detail": "Not found."
}
```

### Throttled `429 Too Many Requests`

```json
{
  "detail": "Request was throttled. Expected available in 45 seconds."
}
```

### Server Error `500 Internal Server Error`

```json
{
  "error": "Report generation failed: <error details>"
}
```

---

## Quick Reference — All Endpoints

| # | Method | Endpoint | Auth | Description |
|---|---|---|---|---|
| | | **Authentication** | | |
| 1 | `POST` | `/api/auth/token/` | No | Login — obtain JWT tokens |
| 2 | `POST` | `/api/auth/token/refresh/` | No | Refresh access token |
| 3 | `POST` | `/api/auth/token/verify/` | No | Verify token validity |
| 4 | `POST` | `/api/auth/register/` | No | Register new user |
| 5 | `GET/PUT` | `/api/auth/me/` | Yes | Get/update profile |
| 6 | `POST` | `/api/auth/change-password/` | Yes | Change password |
| | | **Brands** | | |
| 7 | `GET/POST` | `/api/brands/` | Yes | List/create brands |
| 8 | `GET/PUT/PATCH/DELETE` | `/api/brands/{id}/` | Yes | CRUD brand |
| 9 | `GET` | `/api/brands/{id}/outlets/` | Yes | List brand outlets |
| 10 | `GET` | `/api/brands/{id}/stats/` | Yes | Brand statistics |
| | | **Outlets** | | |
| 11 | `GET/POST` | `/api/outlets/` | Yes | List/create outlets |
| 12 | `GET/PUT/PATCH/DELETE` | `/api/outlets/{id}/` | Yes | CRUD outlet |
| 13 | `GET` | `/api/outlets/{id}/staff/` | Yes | Outlet staff list |
| 14 | `GET` | `/api/outlets/{id}/tables/` | Yes | Outlet tables |
| 15 | `GET` | `/api/outlets/{id}/floor_status/` | Yes | Floor status summary |
| | | **Staff** | | |
| 16 | `GET/POST` | `/api/staff/` | Yes | List/create staff |
| 17 | `GET/PUT/PATCH/DELETE` | `/api/staff/{id}/` | Yes | CRUD staff profile |
| | | **Layout — Nodes** | | |
| 18 | `GET/POST` | `/api/nodes/` | Yes | List/create nodes |
| 19 | `GET/PUT/PATCH/DELETE` | `/api/nodes/{id}/` | Yes | CRUD node |
| 20 | `POST` | `/api/nodes/{id}/update-status/` | Yes | Update node color |
| 21 | `GET` | `/api/nodes/{id}/order-history/` | Yes | Table order history |
| 22 | `GET` | `/api/nodes/by_outlet/` | Yes | Nodes by outlet |
| | | **Layout — Flows** | | |
| 23 | `GET/POST` | `/api/flows/` | Yes | List/create flows |
| 24 | `GET/PUT/PATCH/DELETE` | `/api/flows/{id}/` | Yes | CRUD flow |
| 25 | `GET` | `/api/flows/graph/` | Yes | Full floor graph |
| | | **Orders** | | |
| 26 | `GET/POST` | `/api/orders/` | Yes | List/create orders |
| 27 | `GET/PUT/PATCH/DELETE` | `/api/orders/{id}/` | Yes | CRUD order |
| 28 | `POST` | `/api/orders/{id}/update-status/` | Yes | Update order status |
| 29 | `GET` | `/api/orders/active/` | Yes | Active orders |
| 30 | `GET` | `/api/orders/by_table/` | Yes | Orders by table |
| 31 | `GET` | `/api/orders/kitchen_queue/` | Yes | Kitchen queue |
| | | **Payments** | | |
| 32 | `GET/POST` | `/api/payments/` | Yes | List/create payments |
| 33 | `GET/PUT/PATCH/DELETE` | `/api/payments/{id}/` | Yes | CRUD payment |
| 34 | `GET` | `/api/payments/summary/` | Yes | Payment statistics |
| | | **Table Trigger** | | |
| 35 | `POST` | `/api/table/trigger/` | Yes | Manual table status update |
| | | **Sales Data** | | |
| 36 | `GET/POST` | `/api/sales-data/` | Yes | List/create sales data |
| 37 | `GET/PUT/PATCH/DELETE` | `/api/sales-data/{id}/` | Yes | CRUD sales data |
| 38 | `GET` | `/api/sales-data/trends/` | Yes | Sales trends |
| 39 | `GET` | `/api/sales-data/hourly_pattern/` | Yes | Hourly patterns |
| | | **Inventory** | | |
| 40 | `GET/POST` | `/api/inventory/` | Yes | List/create inventory |
| 41 | `GET/PUT/PATCH/DELETE` | `/api/inventory/{id}/` | Yes | CRUD inventory item |
| 42 | `POST` | `/api/inventory/{id}/adjust/` | Yes | Adjust quantity |
| 43 | `GET` | `/api/inventory/low_stock/` | Yes | Low-stock items |
| 44 | `GET` | `/api/inventory/expiring_soon/` | Yes | Expiring items |
| | | **Staff Schedules** | | |
| 45 | `GET/POST` | `/api/schedules/` | Yes | List/create schedules |
| 46 | `GET/PUT/PATCH/DELETE` | `/api/schedules/{id}/` | Yes | CRUD schedule |
| 47 | `POST` | `/api/schedules/{id}/check-in/` | Yes | Record check-in |
| 48 | `POST` | `/api/schedules/{id}/check-out/` | Yes | Record check-out |
| 49 | `GET` | `/api/schedules/today/` | Yes | Today's schedules |
| 50 | `GET` | `/api/schedules/by_staff/` | Yes | Schedules by staff |
| | | **ML Predictions** | | |
| 51 | `GET` | `/api/predictions/busy-hours/` | Yes | Busy hours forecast |
| 52 | `GET` | `/api/predictions/footfall/` | Yes | Footfall forecast |
| 53 | `GET` | `/api/predictions/food-demand/` | Yes | Food demand forecast |
| 54 | `GET` | `/api/predictions/inventory-alerts/` | Yes | Inventory depletion alerts |
| 55 | `GET` | `/api/predictions/staffing/` | Yes | Staffing recommendations |
| 56 | `GET` | `/api/predictions/revenue/` | Yes | Revenue forecast |
| 57 | `GET` | `/api/predictions/dashboard/` | Yes | All predictions combined |
| 58 | `POST` | `/api/predictions/train/` | Yes | Train ML models |
| | | **Reports & Summaries** | | |
| 59 | `GET/POST` | `/api/summaries/` | Yes | List/create summaries |
| 60 | `GET/PUT/PATCH/DELETE` | `/api/summaries/{id}/` | Yes | CRUD summary |
| 61 | `GET` | `/api/summaries/trends/` | Yes | Performance trends |
| 62 | `GET` | `/api/summaries/compare/` | Yes | Compare outlets |
| 63 | `GET` | `/api/summaries/today/` | Yes | Today's summaries |
| 64 | `GET/POST` | `/api/reports/` | Yes | List/create reports |
| 65 | `GET/PUT/PATCH/DELETE` | `/api/reports/{id}/` | Yes | CRUD report |
| 66 | `POST` | `/api/reports/generate/` | Yes | Generate AI report |
| 67 | `GET` | `/api/reports/daily/` | Yes | Daily report lookup |
| | | **File Uploads** | | |
| 68 | `POST` | `/api/upload/` | Yes | Single file upload |
| 69 | `POST` | `/api/upload/multi/` | Yes | Multi-file upload |
| 70 | `DELETE` | `/api/upload/delete/` | Yes | Delete file |
| | | **Tasks & System** | | |
| 71 | `GET` | `/api/tasks/{task_id}/` | Yes | Poll task status |
| 72 | `GET` | `/api/health/` | No | Health check |
| 73 | `GET` | `/api/` | No | API root directory |
| 74 | `GET` | `/api/docs/` | No | Swagger UI |
| 75 | `GET` | `/api/redoc/` | No | ReDoc documentation |
| 76 | `GET` | `/api/schema/` | No | OpenAPI 3.0 schema |
| | | **WebSocket** | | |
| 77 | `WS` | `/ws/floor/<outlet_id>/` | — | Real-time floor updates |
| 78 | `WS` | `/ws/orders/` | — | Global order stream |
| 79 | `WS` | `/ws/orders/<outlet_id>/` | — | Outlet order stream |

---

> **Total: 79 endpoints** (76 REST + 3 WebSocket)  
> **OpenAPI Schema:** 71 paths, 120 operations  
> **Test Coverage:** 198 tests passing across all apps