# TwinEngine Hospitality Edition - AI-Powered Digital Twin Platform

## 1. Overview

### 1.1 Title

**AI-Powered Digital Twin Platform for Hospitality Operations**

Restaurants, cafes, and food service outlets operate complex systems involving table management, order flow, inventory, and staff coordination. Managers lack real-time visibility into operational bottlenecks and predictive insights for optimization.

This project delivers an AI-powered digital twin platform that creates a virtual replica of hospitality floor operations, enabling real-time monitoring, demand forecasting, and intelligent reporting through a cloud-based system.

### 1.2 Problem Statement

Hospitality businesses face:

- Limited visibility into real-time floor status and service bottlenecks
- No ability to predict demand and optimize staffing/inventory
- Reactive order management leading to delays and poor customer experience
- No accessible, AI-driven platform for hospitality operational decision-making

### 1.3 Goal

**Develop a digital twin platform that:**

- Tracks real-time order lifecycle and table status
- Builds predictive models for demand forecasting
- Optimizes staff scheduling and inventory management
- Generates AI-powered operational reports
- Visualizes floor status through an interactive 3D interface

### 1.4 Value Proposition

TwinEngine Hospitality provides an accessible, modular AI-Powered Digital Twin platform that transforms raw operational data into an interactive 3D command centre, enabling real-time table monitoring, order tracking, and automated executive reporting.

---

## 2. Scope & Control

### 2.1 In-Scope

- **3D Digital Twin Interface:** Development of an interactive 3D floor visualization using React and Three.js where tables are represented as color-coded clickable nodes.
- **Order Lifecycle Tracking:** Implementation of real-time order status tracking from placement to payment completion.
- **Predictive Analytics:** ML models for demand forecasting, inventory optimization, and staff scheduling.
- **Real-time Alerting:** A WebSocket-based system to change node colours based on table status (BLUE: Available, RED: Needs Attention, GREEN: Order Delivered, YELLOW: Waiting, GREY: Reserved).
- **Automated Executive Reporting:** Integration of Azure GPT-4o to process operational data into professional daily summary reports.
- **Interactive Control Panel:** Dashboard for floor managers with real-time KPIs and outlet performance metrics.

### 2.2 Out-of-Scope

- **POS Hardware Integration:** Direct integration with existing Point-of-Sale hardware in the current version.
- **Mobile Application:** Development of native iOS or Android apps; the platform will remain a desktop-optimised web application.
- **Kitchen Display Systems:** Direct integration with kitchen display hardware is deferred.
- **AR/VR Integration:** Immersive virtual reality floor inspections are deferred for future enhancements.

#### Comparison Table

| Metric | Traditional Monitoring | TwinEngine Hospitality |
|--------|------------------------|------------------------|
| Response Time | Manual floor checks (minutes) | Instant (real-time 3D alerts) |
| Reporting | End-of-day manual logs | Automated (AI summaries) |
| Table Status | Wait staff communication | Visual 3D floor map |
| Demand Forecasting | Historical guesswork | AI-powered predictions |

### 2.3 Assumptions

- **Data Availability:** It is assumed that order and payment data can be captured and fed into the system.
- **Cloud Connectivity:** The system assumes constant internet access to reach database and AI inference APIs.
- **Outlet Configuration:** Each outlet's floor layout can be configured in the 3D twin interface.

### 2.4 Constraints

- **API Latency:** Real-time performance is subject to the response times of AI APIs.
- **Processing Power:** The application will rely on cloud-based AI inference for predictions.
- **Project Timeline:** All core features must be completed within the academic semester deadline.

### 2.5 Dependencies

- **Cloud Hosting:** Dependency on Render (backend) and Vercel (frontend) for deployment.
- **AI Models:** Reliance on Azure GPT-4o for report generation and custom ML models for predictions.
- **Database:** Continuous availability of the PostgreSQL/Neon instance.

---

## 3. Team Management & Planning

### 3.1 Team Roles and Responsibilities

| Member | Role | Responsibilities | Key Skills |
|--------|------|------------------|------------|
| Amrita Singh | Project Lead / ML Engineer | Predictive model development for demand forecasting and optimization. | Python, ML, Azure AI |
| Akshat Gupta | System Architect / Full-Stack | 3D UI development (Three.js), Django backend, and database integration. | React, Django, Three.js, PostgreSQL |

### 3.2 Week-wise Plan (8-Week Milestone Schedule)

| Week | Milestones | Primary Deliverable |
|------|------------|---------------------|
| Week 1 | Requirements & Synopsis | Finalized Project Synopsis and Scope. |
| Week 2 | Tech Stack & Environment | Database setup and Django scaffolding. |
| Week 3 | 3D Foundation | Basic Three.js floor plan with table nodes. |
| Week 4 | Order Engine | Real-time order tracking and table status. |
| Week 5 | Predictive Core | Demand forecasting and inventory predictions. |
| Week 6 | Intelligence Layer | Integration of Azure GPT-4o for report generation. |
| Week 7 | System Hardening | Bug fixing, UI polishing, and performance testing. |
| Week 8 | Final Presentation | Deployment on Vercel/Render and project demo. |

---

## 4. Users & UX

### 4.1 Personas

- **Floor Manager:** Needs a high-level view of the entire restaurant floor to monitor table availability, order status, and identify service bottlenecks quickly. They rely on automated reports for shift summaries.
- **Restaurant Owner:** Strategic user who monitors multi-outlet performance, reviews daily summaries, and uses predictive insights for staffing and inventory decisions.

### 4.2 Top User Journeys

1. **Dashboard Login & Overview:** User logs in and views the real-time 3D floor plan. Tables show color-coded status indicating availability and order state.
2. **Order Issue Investigation:** A table node turns **RED** due to a long wait time. The manager clicks the node to view order details and takes action.
3. **Shift Planning:** Manager uses predictive insights to optimize staff scheduling based on forecasted demand for upcoming shifts.
4. **Report Generation:** At the end of a shift, the manager requests an AI-generated summary of all operational metrics and performance data.

### 4.3 User Stories

- **As a Floor Manager,** I want to see a 3D visualization of my restaurant floor so that I can immediately identify which tables need attention.
- **As a Restaurant Owner,** I want to receive AI-generated daily reports so that I can review operational trends without manually sorting through data.
- **As an Operations Manager,** I want demand forecasts so that I can optimize staffing and reduce wait times during peak hours.

### 4.4 Accessibility & Localisation

- **Intuitive 3D Navigation:** Simple mouse-based controls for zooming and rotating the floor map, making it accessible to non-technical staff.
- **Colour-Coded Status Alerts:** Standardised colors for clear communication:
  - 🔵 BLUE: Available / Free
  - 🔴 RED: Needs Attention / Exceeded Wait
  - 🟢 GREEN: Order Delivered / Happy
  - 🟡 YELLOW: Waiting / In Progress
  - ⚫ GREY: Reserved / Inactive
- **Simplified Language:** GPT-4o reports will use professional but simple terminology to ensure clarity for all stakeholders.

---

## 5. Market and Competitors

### 5.1 Competitor Table

| Competitor | Product Type | Target Users | Key Features | Pricing | Strengths / Weaknesses | Our Differentiator |
|------------|--------------|--------------|--------------|---------|------------------------|-------------------|
| Toast / Square | POS Systems | Restaurants | Order processing, payments, basic reporting | SaaS (per terminal) | S: Integrated payments. W: No spatial visualization | 3D Spatial Twin: Visual floor management with real-time status |
| OpenTable | Reservation System | Front-of-house | Table booking, waitlist management | Commission-based | S: Customer-facing. W: No operational insights | Operational Intelligence: AI-powered demand forecasting |
| Restaurant365 | Back-office Software | Finance/Operations | Accounting, inventory tracking | Enterprise pricing | S: Comprehensive financials. W: Complex, expensive | Lightweight & Visual: Instant spatial insights |

### 5.2 Positioning

TwinEngine Hospitality focuses on **Real-Time Spatial Operations**. Unlike traditional POS systems that show transactional data, TwinEngine prioritizes a "Visual Twin" approach where operational status is translated into intuitive 3D visualizations and AI-generated reports.

**Measurable Delta:**

- **Table Status Visibility:** Instant vs walking the floor (minutes).
- **Report Generation:** Instant AI summaries vs hours of manual data review.
- **Demand Planning:** AI-powered predictions vs historical guesswork.

---

## 6. Objectives and Success Metrics

- **O1: Real-Time Visualization Sync:** Ensure the 3D floor plan (Three.js) updates within **< 500ms** of a status change (KPI: Sync Latency).
- **O2: Order Tracking Accuracy:** Track 100% of orders from placement to completion with accurate status updates.
- **O3: Alert Response Time:** Trigger visual alerts within **2 seconds** of status change thresholds (KPI: Detection Latency).
- **O4: Report Generation Quality:** Produce coherent daily operational reports using GPT-4o with accurate metrics (KPI: Report Accuracy).
- **O5: System Accessibility:** Ensure the 3D interface is navigable with a standard mouse/trackpad, resulting in a **< 2-minute learning curve** for new users.

---

## 7. Key Features

| Feature | Description | Priority | Dependencies | Acceptance Criteria |
|---------|-------------|----------|--------------|---------------------|
| Interactive 3D Twin | A React/Three.js dashboard showing the floor layout with clickable table nodes. | Must | React, Three.js | GIVEN a user clicks a table WHEN it has active orders THEN order details panel opens. |
| Order Lifecycle Engine | Real-time tracking of orders from placement through payment. | Must | Django, WebSockets | GIVEN an order is placed WHEN status changes THEN the 3D node color updates. |
| Predictive Analytics | ML-based demand forecasting and inventory optimization. | Must | Django | GIVEN historical data WHEN forecast is requested THEN accurate predictions are shown. |
| AI Report Agent | GPT-4o integration to summarize operational data into reports. | Should | Azure OpenAI | GIVEN a shift ends WHEN the report is requested THEN a professional summary is produced. |

---

## 8. Technical Design

### 8.1 High-Level Architecture

TwinEngine follows a **Layered Cloud Architecture** designed to separate AI processing from the user interface, ensuring a smooth 3D experience.

- **Interaction Layer (Client):** A React-based Single Page Application (SPA) using **Three.js** to render the 3D floor plan. It communicates with the backend via REST for configuration and **WebSockets** for real-time status updates.
- **Orchestration Layer (Backend):** A **Django** server that acts as the "Twin Brain." It manages the state of each service node (tables, stations) and coordinates data flow between the order engine and the database.
- **Intelligence Layer (AI Services):** Offloads computation to **Azure AI** for report generation and custom ML models for demand forecasting.
- **Data Layer:** **PostgreSQL/Neon** stores the outlet configuration, orders, and analytics data.

### 8.2 Backend App Architecture

| App | Purpose | Key Models |
|-----|---------|------------|
| `hospitality_group` | Multi-tenant SaaS layer | Brand, Outlet, UserProfile |
| `layout_twin` | 3D Digital Twin configuration | ServiceNode, ServiceFlow |
| `order_engine` | Real-time order tracking | OrderTicket, PaymentLog |
| `predictive_core` | AI predictions & forecasting | SalesData, InventoryItem, StaffSchedule |
| `insights_hub` | Reporting & analytics | DailySummary, PDFReport |

### 8.3 Authentication System

TwinEngine uses **JWT (JSON Web Token)** authentication via `djangorestframework-simplejwt`.

#### Authentication Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/auth/token/` | POST | Login - obtain access & refresh tokens | No |
| `/api/auth/token/refresh/` | POST | Refresh expired access token | No (refresh token) |
| `/api/auth/token/verify/` | POST | Verify token validity | No |
| `/api/auth/register/` | POST | Register new user with profile | No |
| `/api/auth/me/` | GET/PUT | Get or update authenticated user profile | Yes |
| `/api/auth/change-password/` | POST | Change password securely | Yes |

#### JWT Configuration

- **Access Token Lifetime:** 1 hour
- **Refresh Token Lifetime:** 7 days
- **Token Rotation:** Enabled (new refresh token on each refresh)
- **Header Format:** `Authorization: Bearer <access_token>`

#### Role-Based Permissions

| Permission Class | Description |
|-----------------|-------------|
| `IsOutletUser` | Users can only access their assigned outlet's data |
| `IsManager` | Manager-only access to sensitive endpoints |
| `IsManagerOrReadOnly` | Managers can edit, staff/viewers read-only |
| `IsStaffOrManager` | Staff and managers can access |

#### Demo Users (for testing)

Run `python manage.py create_demo_users` to create:

| Username | Password | Role |
|----------|----------|------|
| manager_demo | manager123 | MANAGER |
| waiter_demo | waiter123 | WAITER |
| chef_demo | chef123 | CHEF |

### 8.4 API Specifications

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/brands/` | GET/POST | Brand management | `[{id, name, brand_code, tier}]` |
| `/api/outlets/` | GET/POST | Fetch/create outlets | `[{id, name, address, status}]` |
| `/api/staff/` | GET/POST | Staff profile management | `[{id, user, outlet, role}]` |
| `/api/nodes/` | GET/POST | Fetch all service nodes for 3D rendering | `[{id, name, status, position}]` |
| `/api/orders/` | GET/POST | Order lifecycle management | `{id, table, status, items, total}` |
| `/api/reports/generate/` | POST | Generate AI operational report | `{report_url, summary}` |
| `/api/predictions/demand/` | GET | Get demand forecast | `{date, predicted_covers, confidence}` |

### 8.5 WebSocket Endpoints

| Endpoint | Purpose |
|----------|---------|
| `ws://host/ws/floor/<outlet_id>/` | Real-time floor status updates |
| `ws://host/ws/orders/<outlet_id>/` | Live order status stream |

### 8.6 Data Design: Core Entities

- **Outlet:** Restaurant/cafe location with address, manager, and configuration.
- **ServiceNode:** Tables, kitchen stations, or service areas with 3D position and status.
- **ServiceFlow:** Defines operational flows (e.g., Table → Kitchen → Table).
- **OrderTicket:** Tracks order lifecycle with status, items, and timing.
- **DailySummary:** Aggregated metrics for AI reporting and trend analysis.

---

## 9. Quality: NFRs and Testing

### 9.1 Non-functional Requirements (NFRs)

| Metric | Target (SLO) | Measurement |
|--------|--------------|-------------|
| Sync Latency | < 500 ms | Time from status change to 3D UI update |
| Uptime | ≥ 99% | Availability of web services |
| Order Accuracy | 100% | All orders tracked correctly |
| Usability | < 2 min | Time for new user to learn 3D navigation |

### 9.2 Test Plan

- **Order Flow Testing:** Verify order status changes are reflected in the 3D twin correctly.
- **Integration Testing:** Ensure API responses are correctly parsed and displayed.
- **UI/UX Testing:** Conduct usability tests to ensure Three.js controls are intuitive.

---

## 10. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API Rate Limits | High | Medium | Implement caching and request batching |
| 3D Rendering Lag | Medium | High | Optimize Three.js geometry and use efficient models |
| Prediction Accuracy | Medium | Medium | Continuous model training with real operational data |
| Schedule Slip | Medium | High | Maintain strict milestone plan with weekly progress demos |

---

## 11. Appendices

### Glossary

- **Digital Twin:** A virtual representation of a physical restaurant floor.
- **ServiceNode:** A table, station, or service area within the floor layout.
- **Order Ticket:** The complete lifecycle of a customer order from placement to payment.

### Table Status Colors

| Color | Status | Description |
|-------|--------|-------------|
| 🔵 BLUE | Available | Table is free and ready for seating |
| 🔴 RED | Needs Attention | Wait time exceeded or issue detected |
| 🟢 GREEN | Delivered | Order delivered, customer satisfied |
| 🟡 YELLOW | Waiting | Order in progress |
| ⚫ GREY | Reserved | Table reserved or inactive |

---

## 12. References

### Digital Twin Research

- Digital Twin Technology in Hospitality Operations
- Real-time Operational Monitoring Systems

### Documentation & Guides

- Three.js Documentation
- Azure OpenAI API Documentation
- Django REST Framework Guides
- WebSocket Implementation Patterns
