# TwinEngine — Machine Learning Models Plan

> This document outlines every ML model we will implement in the `predictive_core` app,
> what data feeds each one, the algorithm choice, and a feasibility rating.

---

## Implementation Overview

### What We're Building

A **self-contained ML prediction engine** inside the existing `apps/predictive_core/` Django app. Six models that predict demand, footfall, food popularity, inventory needs, staff requirements, and revenue — all trained on the restaurant's own historical data stored in PostgreSQL.

### How It Works (End-to-End Flow)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        REQUEST FLOW                                 │
│                                                                     │
│  Frontend/Client                                                    │
│       │                                                             │
│       ▼                                                             │
│  GET /api/predictions/busy-hours/?outlet=4&date=2026-03-04          │
│       │                                                             │
│       ▼                                                             │
│  Django REST View (PredictionViewSet)                               │
│       │                                                             │
│       ├── Validates params (outlet_id, date)                        │
│       ├── Calls PredictionService.get_busy_hours(outlet, date)      │
│       │         │                                                   │
│       │         ├── Loads trained model from ml_models/*.joblib      │
│       │         ├── Runs feature_engineering.py on query date        │
│       │         ├── model.predict(features) → predictions           │
│       │         └── Returns structured dict                         │
│       │                                                             │
│       └── Serializes response → JSON → Client                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        TRAINING FLOW                                │
│                                                                     │
│  Manager triggers: POST /api/predictions/train/?outlet=4            │
│  OR cron: python manage.py train_models --outlet 4                  │
│       │                                                             │
│       ▼                                                             │
│  TrainModelsView / Management Command                               │
│       │                                                             │
│       ├── Query SalesData, DailySummary, OrderTicket for outlet     │
│       ├── feature_engineering.py → pandas DataFrame                 │
│       ├── Train each model (GBR, Ridge, RF)                        │
│       ├── Evaluate (MAE, RMSE, R²)                                 │
│       ├── joblib.dump(model) → ml_models/outlet_4_demand.joblib     │
│       └── Return training metrics                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Directory & File Structure

```
twin_engine_backend/
├── apps/
│   └── predictive_core/                    # ← EXISTING app (models, views, serializers already here)
│       │
│       ├── models.py                       # EXISTING — SalesData, InventoryItem, StaffSchedule
│       ├── serializers.py                  # MODIFY  — add prediction response serializers
│       ├── views.py                        # MODIFY  — add prediction API views
│       ├── urls.py                         # MODIFY  — add prediction URL routes
│       │
│       ├── ml/                             # NEW — entire ML module
│       │   ├── __init__.py                 # Exports PredictionService for easy imports
│       │   │
│       │   ├── feature_engineering.py      # SHARED — query DB → pandas DataFrame
│       │   │   ├── build_demand_features()         # SalesData → features for Models 1,2,6
│       │   │   ├── build_food_demand_features()    # SalesData.category_sales → per-category features
│       │   │   ├── build_inventory_features()      # InventoryItem + OrderTicket → consumption rates
│       │   │   └── build_staffing_features()       # StaffSchedule + demand predictions → features
│       │   │
│       │   ├── demand_model.py             # MODEL 1 — Busy Hours Predictor
│       │   │   └── class BusyHoursPredictor:
│       │   │       ├── train(outlet_id) → metrics dict
│       │   │       ├── predict(outlet_id, date) → hourly forecast
│       │   │       ├── _load_model(outlet_id) → sklearn model
│       │   │       └── _save_model(model, outlet_id)
│       │   │
│       │   ├── footfall_model.py           # MODEL 2 — Customer Footfall Forecaster
│       │   │   └── class FootfallForecaster:
│       │   │       ├── train(outlet_id) → metrics dict
│       │   │       └── predict(outlet_id, date) → hourly guest forecast
│       │   │
│       │   ├── food_demand_model.py        # MODEL 3 — Food Demand Predictor
│       │   │   └── class FoodDemandPredictor:
│       │   │       ├── train(outlet_id) → metrics dict
│       │   │       └── predict(outlet_id, date) → per-category forecast
│       │   │
│       │   ├── inventory_predictor.py      # MODEL 4 — Inventory Depletion Alert (rule-based)
│       │   │   └── class InventoryPredictor:
│       │   │       └── predict(outlet_id) → depletion alerts + restock suggestions
│       │   │       # No train() — purely calculation-based
│       │   │
│       │   ├── staffing_optimizer.py       # MODEL 5 — Staff Optimization Model
│       │   │   └── class StaffingOptimizer:
│       │   │       └── predict(outlet_id, date) → waiters/chefs per shift
│       │   │       # Uses output from Models 1 & 2
│       │   │
│       │   ├── revenue_model.py            # MODEL 6 — Revenue Forecaster
│       │   │   └── class RevenueForecaster:
│       │   │       ├── train(outlet_id) → metrics dict
│       │   │       └── predict(outlet_id, date, days=7) → daily revenue forecast
│       │   │
│       │   └── prediction_service.py       # FACADE — single entry point for views
│       │       └── class PredictionService:
│       │           ├── get_busy_hours(outlet_id, date)
│       │           ├── get_footfall(outlet_id, date)
│       │           ├── get_food_demand(outlet_id, date)
│       │           ├── get_inventory_alerts(outlet_id)
│       │           ├── get_staffing(outlet_id, date)
│       │           ├── get_revenue_forecast(outlet_id, date)
│       │           ├── get_dashboard(outlet_id, date)     # all combined
│       │           └── train_all(outlet_id)               # train all trainable models
│       │
│       ├── ml_models/                      # NEW — saved .joblib files (git-ignored)
│       │   ├── .gitkeep
│       │   ├── outlet_4_demand.joblib           # trained Model 1 for outlet 4
│       │   ├── outlet_4_footfall.joblib          # trained Model 2 for outlet 4
│       │   ├── outlet_4_food_demand.joblib       # trained Model 3 for outlet 4
│       │   ├── outlet_4_revenue.joblib           # trained Model 6 for outlet 4
│       │   └── training_metadata.json            # when trained, sample count, metrics
│       │
│       └── management/
│           └── commands/
│               └── train_models.py         # NEW — CLI: python manage.py train_models --outlet 4
│
├── requirements.txt                        # MODIFY — add scikit-learn, pandas, numpy, joblib
└── .gitignore                              # MODIFY — add *.joblib, ml_models/*.joblib
```

### Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| **Per-outlet models** | Each outlet gets its own trained model file | Different outlets have different patterns (fine dining vs cafe) |
| **joblib for persistence** | Save/load sklearn models as `.joblib` files | Fast, reliable, no DB overhead for model storage |
| **Facade pattern** | `PredictionService` wraps all 6 models | Views stay clean — one import, one method call |
| **Graceful fallback** | Every model returns historical averages if untrained | System never breaks — worst case is a simpler prediction |
| **No Celery dependency** | Training runs synchronously via management command or API | Keeps it simple — training takes seconds with this data volume |

---

## Data Available (What We Have to Work With)

| Source Model | Key Fields | Records (Synthetic) |
|---|---|---|
| `SalesData` | outlet, date, hour, total_orders, total_revenue, avg_ticket_size, avg_wait_time, category_sales (JSON), day_of_week, is_holiday | 91 |
| `OrderTicket` | table, waiter, party_size, items (JSON), status, placed_at, served_at, completed_at, total | 50 |
| `InventoryItem` | name, category, current_quantity, reorder_threshold, par_level, unit_cost, expiry_date, last_restocked | 20 |
| `StaffSchedule` | staff, date, shift, start_time, end_time, is_confirmed, checked_in, checked_out, is_ai_suggested | 29 |
| `DailySummary` | total_revenue, total_orders, total_guests, avg_wait_time, peak_hour, delayed_orders, cancelled_orders, staff_count | 7+ |
| `PaymentLog` | order, amount, method, tip_amount, status | 31 |

> **Note:** With synthetic data the record counts are small. Models are designed to work from
> ~30 days of data (the synthetic generator creates 7 days). For real production accuracy,
> 60-90 days of historical data is ideal. All models include graceful fallbacks when data is sparse.

---

## Models Overview

| # | Model Name | Input Data | Output | Algorithm | Feasibility |
|---|---|---|---|---|---|
| 1 | **Busy Hours Predictor** | SalesData (hour, day_of_week, is_holiday) | Predicted orders per hour | Gradient Boosting Regressor | ✅ Easy |
| 2 | **Customer Footfall Forecaster** | DailySummary + SalesData (total_guests, hour, day_of_week) | Predicted number of customers per hour | Linear Regression / Ridge | ✅ Easy |
| 3 | **Food Demand Predictor** | SalesData (category_sales, top_items, hour, day_of_week) | Predicted demand per food category / top items | Random Forest Regressor | ✅ Easy |
| 4 | **Inventory Depletion Alert** | InventoryItem + OrderTicket (items JSON) | Days until stockout, restock urgency flag | Rule-based + Linear Trend | ✅ Easy |
| 5 | **Staff Optimizer** | SalesData + StaffSchedule (predicted demand → staff mapping) | Required waiters & chefs per shift | Rule-based ratio + Regression | ✅ Easy |
| 6 | **Revenue Forecaster** | SalesData + DailySummary (total_revenue, date, day_of_week) | Next-day / next-week revenue forecast | Gradient Boosting Regressor | ✅ Easy |

---

## Detailed Model Specifications

---

### Model 1: Busy Hours Predictor

**Goal:** Predict the number of orders for each hour of the day, for a given date.

**Why it matters:** Lets managers know which hours will be peak so they can prepare kitchen, staff, and inventory in advance.

#### Input Features
| Feature | Source | Type |
|---|---|---|
| `hour` | SalesData.hour | int (0-23) |
| `day_of_week` | SalesData.day_of_week | int (0-6) |
| `is_holiday` | SalesData.is_holiday | bool |
| `is_weekend` | derived (day_of_week >= 5) | bool |
| `prev_week_same_hour_orders` | SalesData (lag 7 days) | float |
| `rolling_avg_orders_7d` | SalesData (7-day rolling mean) | float |

#### Output
```json
{
  "date": "2026-03-04",
  "hourly_forecast": [
    {"hour": 11, "predicted_orders": 8, "confidence": "high"},
    {"hour": 12, "predicted_orders": 14, "confidence": "high"},
    {"hour": 13, "predicted_orders": 12, "confidence": "medium"},
    ...
  ],
  "peak_hour": 12,
  "total_predicted_orders": 62
}
```

#### Algorithm
- **Primary:** `GradientBoostingRegressor` (scikit-learn) — handles nonlinear hour/day patterns well
- **Fallback:** If < 14 days of data → simple historical average per (hour, day_of_week)

#### Implementation Complexity: ✅ Easy
- Straightforward tabular regression
- Data already exists in `SalesData` at hourly granularity
- No feature engineering beyond basic lags and rolling averages

---

### Model 2: Customer Footfall Forecaster

**Goal:** Predict the number of customers (guests) expected per hour for a given date.

**Why it matters:** Directly drives table allocation, waitlist management, and reservation capacity.

#### Input Features
| Feature | Source | Type |
|---|---|---|
| `hour` | SalesData.hour | int |
| `day_of_week` | SalesData.day_of_week | int |
| `is_holiday` | SalesData.is_holiday | bool |
| `is_weekend` | derived | bool |
| `avg_party_size` | OrderTicket.party_size (historical avg) | float |
| `prev_week_guests` | DailySummary.total_guests (lag 7d) | float |

#### Output
```json
{
  "date": "2026-03-04",
  "hourly_guests": [
    {"hour": 12, "predicted_guests": 28},
    {"hour": 13, "predicted_guests": 22},
    ...
  ],
  "total_predicted_guests": 145,
  "avg_party_size": 2.4
}
```

#### Algorithm
- **Primary:** `Ridge` regression (simple, fast, works with limited data)
- **Fallback:** Historical average guests per hour for that day_of_week

#### Implementation Complexity: ✅ Easy
- Very similar pipeline to Model 1 but targets `total_guests` instead of `total_orders`
- Can share feature engineering code with Busy Hours Predictor

---

### Model 3: Food Demand Predictor

**Goal:** Predict demand per food category and top-selling items for a given date/hour.

**Why it matters:** Kitchen prep planning — which ingredients to prep, how much of each dish to expect. Prevents food waste and stockouts.

#### Input Features
| Feature | Source | Type |
|---|---|---|
| `hour` | SalesData.hour | int |
| `day_of_week` | SalesData.day_of_week | int |
| `is_holiday` | SalesData.is_holiday | bool |
| `category` | SalesData.category_sales (exploded per category) | str (one-hot) |
| `prev_week_category_sales` | SalesData.category_sales (7d lag) | float |
| `total_orders_predicted` | Output from Model 1 | float |

#### Output
```json
{
  "date": "2026-03-04",
  "category_forecast": {
    "Main Course": {"predicted_orders": 35, "predicted_revenue": 8750.00},
    "Starters": {"predicted_orders": 22, "predicted_revenue": 3300.00},
    "Beverages": {"predicted_orders": 40, "predicted_revenue": 4000.00},
    "Desserts": {"predicted_orders": 12, "predicted_revenue": 1800.00}
  },
  "top_items_forecast": [
    {"item": "Butter Chicken", "predicted_orders": 12},
    {"item": "Paneer Tikka", "predicted_orders": 9},
    {"item": "Masala Chai", "predicted_orders": 15}
  ]
}
```

#### Algorithm
- **Primary:** `RandomForestRegressor` (one model per category, trained on category_sales JSON values)
- **Fallback:** Historical average sales per category for that (day_of_week, hour)

#### Implementation Complexity: ✅ Easy
- Requires JSON parsing of `category_sales` and `top_items` fields
- One sub-model per category keeps each model simple
- scikit-learn handles this natively

---

### Model 4: Inventory Depletion Alert Model

**Goal:** Predict how many days until each inventory item runs out, and generate restock urgency alerts.

**Why it matters:** Prevents "sorry, we're out of X" mid-service. Automated purchase order suggestions.

#### Input Features
| Feature | Source | Type |
|---|---|---|
| `current_quantity` | InventoryItem.current_quantity | float |
| `reorder_threshold` | InventoryItem.reorder_threshold | float |
| `par_level` | InventoryItem.par_level | float |
| `daily_consumption_rate` | Derived from OrderTicket.items over last 7 days | float |
| `category` | InventoryItem.category | str |
| `days_since_restock` | now - InventoryItem.last_restocked | int |
| `expiry_date` | InventoryItem.expiry_date | date |

#### Output
```json
{
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
    },
    {
      "item": "Basmati Rice",
      "current_quantity": 22.0,
      "unit": "KG",
      "daily_consumption_rate": 3.5,
      "days_until_stockout": 6,
      "urgency": "MODERATE",
      "suggested_order_qty": 28.0,
      "expiry_warning": false
    }
  ],
  "expiring_soon": [
    {"item": "Fresh Cream", "expiry_date": "2026-03-05", "days_left": 2}
  ]
}
```

#### Algorithm
- **Primary:** Rule-based linear projection: `days_until_stockout = current_quantity / daily_consumption_rate`
- **Consumption rate calculation:** Sum item mentions in `OrderTicket.items` JSON over last N days → map to inventory items
- **Urgency levels:**
  - `CRITICAL` → ≤ 2 days or already below reorder threshold
  - `HIGH` → 3-4 days
  - `MODERATE` → 5-7 days
  - `OK` → > 7 days
- **Suggested order qty:** `par_level - current_quantity + (daily_consumption_rate × lead_time_days)`

#### Implementation Complexity: ✅ Easy
- Mostly arithmetic — no ML model training needed
- The hardest part is mapping OrderTicket `items` JSON to InventoryItem names (fuzzy matching or key mapping)
- Very reliable even with little data

---

### Model 5: Staff Optimization Model

**Goal:** Recommend the required number of **waiters** and **chefs** per shift based on predicted demand.

**Why it matters:** Understaffing = long waits and bad reviews. Overstaffing = wasted payroll. This balances both.

#### Input Features
| Feature | Source | Type |
|---|---|---|
| `predicted_orders_per_hour` | Output from Model 1 (Busy Hours) | float |
| `predicted_guests_per_hour` | Output from Model 2 (Footfall) | float |
| `avg_wait_time` | SalesData.avg_wait_time_minutes | float |
| `seating_capacity` | Outlet.seating_capacity | int |
| `shift` | StaffSchedule.shift (MORNING/AFTERNOON/NIGHT) | str |
| `day_of_week` | derived | int |
| `historical_staff_count` | StaffSchedule (count per shift historically) | int |
| `historical_delayed_orders` | DailySummary.delayed_orders | int |

#### Output
```json
{
  "date": "2026-03-04",
  "staffing_recommendation": {
    "MORNING": {
      "recommended_waiters": 2,
      "recommended_chefs": 2,
      "predicted_orders": 18,
      "predicted_guests": 35,
      "reason": "Low demand morning — 2 waiters can cover 15 tables"
    },
    "AFTERNOON": {
      "recommended_waiters": 4,
      "recommended_chefs": 3,
      "predicted_orders": 42,
      "predicted_guests": 85,
      "reason": "Peak lunch rush — 1 waiter per 4 active tables, 1 chef per 14 orders/hr"
    },
    "NIGHT": {
      "recommended_waiters": 3,
      "recommended_chefs": 2,
      "predicted_orders": 28,
      "predicted_guests": 55,
      "reason": "Moderate dinner service"
    }
  },
  "total_staff_needed": 16,
  "cost_estimate": "₹12,800"
}
```

#### Algorithm
- **Primary:** Ratio-based rules calibrated from historical data:
  - **Waiters:** 1 waiter per 4-5 active tables (adjusted by predicted orders)
  - **Chefs:** 1 chef per 12-15 orders/hour (adjusted by menu complexity)
  - If `delayed_orders` was high on similar past days → +1 staff buffer
- **Enhancement (if enough data):** `LinearRegression` trained on: `(predicted_orders, predicted_guests, day_of_week)` → `(actual_staff_needed)` where target is derived from days with low delayed_orders and good wait times.

#### Implementation Complexity: ✅ Easy
- Primarily ratio-based rules → always works, even day one
- ML refinement is a bonus layer, not a requirement
- Depends on Models 1 & 2 for demand inputs

---

### Model 6: Revenue Forecaster

**Goal:** Predict next-day and next-week total revenue for an outlet.

**Why it matters:** Cash flow planning, target setting, and performance benchmarking.

#### Input Features
| Feature | Source | Type |
|---|---|---|
| `day_of_week` | derived | int |
| `is_holiday` | SalesData.is_holiday | bool |
| `prev_day_revenue` | DailySummary.total_revenue (lag 1) | float |
| `prev_week_same_day_revenue` | DailySummary (lag 7) | float |
| `rolling_avg_revenue_7d` | DailySummary (7-day mean) | float |
| `rolling_avg_revenue_30d` | DailySummary (30-day mean) | float |
| `prev_day_orders` | DailySummary.total_orders (lag 1) | int |

#### Output
```json
{
  "outlet": "Spice Republic - Koramangala",
  "next_day": {
    "date": "2026-03-04",
    "predicted_revenue": 18500.00,
    "confidence_range": [16200, 20800]
  },
  "next_week": {
    "total_predicted_revenue": 125000.00,
    "daily_breakdown": [
      {"date": "2026-03-04", "predicted": 18500},
      {"date": "2026-03-05", "predicted": 16200},
      ...
    ]
  }
}
```

#### Algorithm
- **Primary:** `GradientBoostingRegressor` — captures day-of-week seasonality and trends
- **Fallback:** Weighted average (70% same-day last week + 30% recent 7-day avg)

#### Implementation Complexity: ✅ Easy
- Same pipeline as Models 1-2 but targeting revenue
- DailySummary already stores all needed aggregates

---

## Implementation Priority & Dependencies

```
                    ┌──────────────────────┐
                    │  Model 1: Busy Hours │
                    │  (orders per hour)   │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
   ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
   │ Model 2:        │ │ Model 3:     │ │ Model 5:         │
   │ Customer        │ │ Food Demand  │ │ Staff Optimizer  │
   │ Footfall        │ │ Predictor    │ │ (waiters/chefs)  │
   └─────────────────┘ └──────┬───────┘ └──────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Model 4: Inventory  │
                    │  Depletion Alert     │
                    └──────────────────────┘

   ┌──────────────────────┐
   │  Model 6: Revenue    │  (independent, can build anytime)
   │  Forecaster          │
   └──────────────────────┘
```

**Build order:**
1. **Model 1** first (Busy Hours) — foundation for Models 2, 3, 5
2. **Model 4** next (Inventory Alert) — independent of other models, purely rule-based
3. **Models 2 & 3** (Footfall + Food Demand) — use Model 1 output as a feature
4. **Model 5** (Staff Optimizer) — uses Models 1 & 2 outputs
5. **Model 6** (Revenue Forecaster) — independent, build whenever

---

## Tech Stack

| Package | Purpose | Version |
|---|---|---|
| `scikit-learn` | All regression models (GBR, RF, Ridge, LinearRegression) | >=1.6,<2.0 |
| `pandas` | DataFrame operations, feature engineering, time series | >=2.2,<3.0 |
| `numpy` | Numerical operations | >=2.2,<3.0 |
| `joblib` | Model serialization (save/load trained models) | >=1.4,<2.0 |

> All four packages are lightweight, well-maintained, and have no GPU/CUDA dependency.
> Total additional install size: ~50 MB.

---

## File Structure

```
apps/predictive_core/
├── ml/
│   ├── __init__.py
│   ├── feature_engineering.py    # Shared feature extraction utilities
│   ├── demand_model.py           # Model 1: Busy Hours Predictor
│   ├── footfall_model.py         # Model 2: Customer Footfall Forecaster
│   ├── food_demand_model.py      # Model 3: Food Demand Predictor
│   ├── inventory_predictor.py    # Model 4: Inventory Depletion Alert
│   ├── staffing_optimizer.py     # Model 5: Staff Optimization Model
│   ├── revenue_model.py          # Model 6: Revenue Forecaster
│   └── prediction_service.py     # Unified facade for all models
├── management/
│   └── commands/
│       └── train_models.py       # Management command to train all models
├── ml_models/                    # Saved trained model files (.joblib)
│   └── .gitkeep
├── serializers.py                # + new prediction response serializers
├── views.py                      # + new prediction API endpoints
└── urls.py                       # + new prediction routes
```

---

## API Endpoints (Final)

| Endpoint | Method | Model Used | Description |
|---|---|---|---|
| `/api/predictions/busy-hours/` | GET | Model 1 | Predicted orders per hour for a date |
| `/api/predictions/footfall/` | GET | Model 2 | Predicted customers per hour for a date |
| `/api/predictions/food-demand/` | GET | Model 3 | Predicted demand per category/item |
| `/api/predictions/inventory-alerts/` | GET | Model 4 | Inventory depletion forecasts |
| `/api/predictions/staffing/` | GET | Model 5 | Required waiters & chefs per shift |
| `/api/predictions/revenue/` | GET | Model 6 | Next-day & next-week revenue forecast |
| `/api/predictions/dashboard/` | GET | All | Combined summary for outlet dashboard |
| `/api/predictions/train/` | POST | All | Trigger model retraining (manager only) |

All endpoints require JWT authentication and accept `?outlet=<id>` and `?date=YYYY-MM-DD` query params.

---

## Feasibility Summary

| Model | Data Needed | Min Records | Algorithm Complexity | Overall Feasibility |
|---|---|---|---|---|
| Busy Hours | SalesData | 7 days (168 rows) | Low (tabular regression) | ✅ Very Easy |
| Customer Footfall | SalesData + DailySummary | 7 days | Low (linear regression) | ✅ Very Easy |
| Food Demand | SalesData (category_sales JSON) | 7 days | Low (per-category regression) | ✅ Easy |
| Inventory Alert | InventoryItem + OrderTicket | Any amount | None (rule-based math) | ✅ Easiest |
| Staff Optimizer | Models 1+2 output + StaffSchedule | Any amount | None (ratio rules) | ✅ Easy |
| Revenue Forecaster | DailySummary | 14 days | Low (tabular regression) | ✅ Easy |

> **All 6 models are feasible** with the existing data schema. No GPU, no deep learning,
> no external APIs needed. Pure scikit-learn + pandas running on the same server.

---

## Fallback Strategy

Every model has a **graceful fallback** when training data is insufficient:

| Data Available | Strategy |
|---|---|
| **0-6 days** | Return historical averages (simple mean by hour/day_of_week) |
| **7-29 days** | Use trained model but with wider confidence intervals |
| **30+ days** | Full model with lagged features and rolling averages |
| **90+ days** | Best accuracy — seasonal patterns become learnable |

The system will **never fail** — it will always return a prediction, just with varying confidence levels.

---

## Best Code Implementation

This section shows the actual code structure for every key file. This is the **reference implementation** — what will be built during the 5 phases.

---

### 1. `feature_engineering.py` — Shared Feature Extraction

The heart of the ML pipeline. Queries Django ORM → returns pandas DataFrames ready for sklearn.

```python
"""
Shared feature engineering utilities for all prediction models.
Queries Django ORM and returns clean pandas DataFrames.
"""
import pandas as pd
import numpy as np
from datetime import timedelta
from django.utils import timezone


def build_demand_features(outlet_id, min_days=7):
    """
    Build feature matrix from SalesData for demand/footfall/revenue models.
    
    Returns:
        pd.DataFrame with columns:
            hour, day_of_week, is_holiday, is_weekend,
            total_orders, total_revenue, total_guests (targets),
            prev_week_orders, rolling_avg_orders_7d, rolling_avg_revenue_7d
        
        None if insufficient data.
    """
    from apps.predictive_core.models import SalesData

    qs = SalesData.objects.filter(outlet_id=outlet_id).order_by('date', 'hour')
    if qs.count() < min_days * 8:  # at least 8 hours/day
        return None

    df = pd.DataFrame(list(qs.values(
        'date', 'hour', 'day_of_week', 'is_holiday',
        'total_orders', 'total_revenue', 'avg_ticket_size',
        'avg_wait_time_minutes'
    )))

    # Derived features
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    df['date'] = pd.to_datetime(df['date'])

    # Lag features (same hour, 7 days ago)
    df = df.sort_values(['date', 'hour']).reset_index(drop=True)
    df['prev_week_orders'] = df.groupby('hour')['total_orders'].shift(7)
    df['prev_week_revenue'] = df.groupby('hour')['total_revenue'].shift(7)

    # Rolling averages (7-day window per hour)
    df['rolling_avg_orders_7d'] = (
        df.groupby('hour')['total_orders']
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )
    df['rolling_avg_revenue_7d'] = (
        df.groupby('hour')['total_revenue']
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )

    # Fill NaN lags with rolling average
    df['prev_week_orders'] = df['prev_week_orders'].fillna(df['rolling_avg_orders_7d'])
    df['prev_week_revenue'] = df['prev_week_revenue'].fillna(df['rolling_avg_revenue_7d'])

    return df


def build_prediction_row(outlet_id, target_date, hour):
    """
    Build a single feature row for a future date+hour (for prediction time).
    Uses historical data to compute lag & rolling features.
    """
    from apps.predictive_core.models import SalesData

    day_of_week = target_date.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0

    # Get same hour from 7 days ago
    week_ago = target_date - timedelta(days=7)
    prev_week = SalesData.objects.filter(
        outlet_id=outlet_id, date=week_ago, hour=hour
    ).first()

    # Rolling 7-day average for this hour
    start = target_date - timedelta(days=7)
    rolling = SalesData.objects.filter(
        outlet_id=outlet_id, date__gte=start, date__lt=target_date, hour=hour
    ).values_list('total_orders', 'total_revenue')

    avg_orders = np.mean([r[0] for r in rolling]) if rolling else 0
    avg_revenue = np.mean([float(r[1]) for r in rolling]) if rolling else 0

    return {
        'hour': hour,
        'day_of_week': day_of_week,
        'is_holiday': 0,  # can be enhanced with a holiday calendar
        'is_weekend': is_weekend,
        'prev_week_orders': prev_week.total_orders if prev_week else avg_orders,
        'prev_week_revenue': float(prev_week.total_revenue) if prev_week else avg_revenue,
        'rolling_avg_orders_7d': avg_orders,
        'rolling_avg_revenue_7d': avg_revenue,
    }


def get_historical_averages(outlet_id, day_of_week):
    """
    Fallback: simple historical averages grouped by hour for a given day_of_week.
    Works even with minimal data.
    """
    from apps.predictive_core.models import SalesData

    qs = SalesData.objects.filter(
        outlet_id=outlet_id, day_of_week=day_of_week
    ).values('hour').annotate(
        avg_orders=models.Avg('total_orders'),
        avg_revenue=models.Avg('total_revenue'),
    ).order_by('hour')

    return {row['hour']: row for row in qs}
```

---

### 2. `demand_model.py` — Busy Hours Predictor (Model 1)

```python
"""
Model 1: Busy Hours Predictor
Predicts the number of orders per hour for a given date.
"""
import logging
import joblib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .feature_engineering import build_demand_features, build_prediction_row, get_historical_averages

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / 'ml_models'
FEATURE_COLS = [
    'hour', 'day_of_week', 'is_holiday', 'is_weekend',
    'prev_week_orders', 'rolling_avg_orders_7d',
]
TARGET_COL = 'total_orders'


class BusyHoursPredictor:
    """Predicts hourly order volume for a given outlet and date."""

    def train(self, outlet_id: int) -> dict:
        """Train and save a model for the given outlet."""
        df = build_demand_features(outlet_id)
        if df is None or len(df) < 50:
            return {"status": "skipped", "reason": "Insufficient data (need 50+ rows)"}

        df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values

        # Time-aware split (no data leakage)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        model = GradientBoostingRegressor(
            n_estimators=100, max_depth=4, learning_rate=0.1,
            min_samples_split=5, random_state=42,
        )
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        metrics = {
            "mae": round(mean_absolute_error(y_test, y_pred), 2),
            "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
            "r2": round(r2_score(y_test, y_pred), 3),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        # Save
        MODELS_DIR.mkdir(exist_ok=True)
        model_path = MODELS_DIR / f"outlet_{outlet_id}_demand.joblib"
        joblib.dump(model, model_path)

        logger.info("Busy Hours model trained for outlet %d: %s", outlet_id, metrics)
        return {"status": "trained", "metrics": metrics}

    def predict(self, outlet_id: int, target_date) -> dict:
        """Predict hourly orders for the given date."""
        model_path = MODELS_DIR / f"outlet_{outlet_id}_demand.joblib"

        # Build features for each hour (typical restaurant hours: 8-23)
        hours = list(range(8, 24))
        rows = [build_prediction_row(outlet_id, target_date, h) for h in hours]

        if model_path.exists():
            model = joblib.load(model_path)
            X = pd.DataFrame(rows)[FEATURE_COLS].values
            predictions = model.predict(X)
            predictions = np.maximum(predictions, 0).astype(int)  # no negative orders
            confidence = "high"
        else:
            # Fallback: historical averages
            avgs = get_historical_averages(outlet_id, target_date.weekday())
            predictions = [avgs.get(h, {}).get('avg_orders', 0) for h in hours]
            confidence = "low (using historical averages — model not yet trained)"

        hourly_forecast = [
            {"hour": h, "predicted_orders": int(p)}
            for h, p in zip(hours, predictions)
        ]

        peak = max(hourly_forecast, key=lambda x: x['predicted_orders'])

        return {
            "date": str(target_date),
            "hourly_forecast": hourly_forecast,
            "peak_hour": peak['hour'],
            "total_predicted_orders": sum(int(p) for p in predictions),
            "confidence": confidence,
        }
```

---

### 3. `inventory_predictor.py` — Inventory Depletion Alert (Model 4)

This is the simplest model — pure math, no training needed.

```python
"""
Model 4: Inventory Depletion Alert
Calculates days until stockout and generates restock urgency alerts.
No ML training required — rule-based linear projection.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count

logger = logging.getLogger(__name__)

# Urgency thresholds (days until stockout)
URGENCY_LEVELS = {
    'CRITICAL': 2,   # ≤ 2 days
    'HIGH': 4,       # 3-4 days
    'MODERATE': 7,   # 5-7 days
}
DEFAULT_LEAD_TIME_DAYS = 3  # assumed supplier delivery time


class InventoryPredictor:
    """Predicts inventory depletion and generates restock alerts."""

    def predict(self, outlet_id: int) -> dict:
        from apps.predictive_core.models import InventoryItem
        from apps.order_engine.models import OrderTicket

        items = InventoryItem.objects.filter(outlet_id=outlet_id)
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # Get recent orders to estimate consumption
        recent_orders = OrderTicket.objects.filter(
            table__outlet_id=outlet_id,
            placed_at__gte=week_ago,
            status__in=['COMPLETED', 'SERVED'],
        )

        # Count item mentions in orders (from items JSON field)
        item_consumption = self._estimate_consumption(recent_orders, days=7)

        alerts = []
        expiring_soon = []

        for item in items:
            daily_rate = item_consumption.get(item.name.lower(), 0)
            
            if daily_rate > 0:
                days_until_stockout = item.current_quantity / daily_rate
            elif item.is_low_stock:
                days_until_stockout = 1  # already low, assume critical
            else:
                days_until_stockout = 30  # no consumption data → assume OK

            # Determine urgency
            if days_until_stockout <= URGENCY_LEVELS['CRITICAL'] or item.is_low_stock:
                urgency = 'CRITICAL'
            elif days_until_stockout <= URGENCY_LEVELS['HIGH']:
                urgency = 'HIGH'
            elif days_until_stockout <= URGENCY_LEVELS['MODERATE']:
                urgency = 'MODERATE'
            else:
                urgency = 'OK'

            # Suggested reorder quantity
            suggested_qty = max(
                0,
                item.par_level - item.current_quantity + (daily_rate * DEFAULT_LEAD_TIME_DAYS)
            )

            if urgency != 'OK':
                alerts.append({
                    "item": item.name,
                    "category": item.category,
                    "current_quantity": item.current_quantity,
                    "unit": item.unit,
                    "daily_consumption_rate": round(daily_rate, 2),
                    "days_until_stockout": round(days_until_stockout, 1),
                    "urgency": urgency,
                    "suggested_order_qty": round(suggested_qty, 1),
                })

            # Expiry check
            if item.expiry_date and item.expiry_date <= (now.date() + timedelta(days=7)):
                days_left = (item.expiry_date - now.date()).days
                expiring_soon.append({
                    "item": item.name,
                    "expiry_date": str(item.expiry_date),
                    "days_left": max(days_left, 0),
                })

        # Sort alerts by urgency
        urgency_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2}
        alerts.sort(key=lambda x: urgency_order.get(x['urgency'], 3))

        return {
            "outlet_id": outlet_id,
            "inventory_alerts": alerts,
            "expiring_soon": expiring_soon,
            "total_critical": sum(1 for a in alerts if a['urgency'] == 'CRITICAL'),
            "total_alerts": len(alerts),
        }

    def _estimate_consumption(self, orders_qs, days: int) -> dict:
        """
        Parse OrderTicket.items JSON to estimate daily consumption per ingredient.
        Returns: {"item_name_lower": daily_consumption_rate}
        """
        item_counts = {}
        for order in orders_qs:
            items_list = order.items if isinstance(order.items, list) else []
            for entry in items_list:
                name = entry.get('name', '') if isinstance(entry, dict) else str(entry)
                name_lower = name.lower().strip()
                if name_lower:
                    qty = entry.get('quantity', 1) if isinstance(entry, dict) else 1
                    item_counts[name_lower] = item_counts.get(name_lower, 0) + qty

        # Convert to daily rate
        return {name: count / max(days, 1) for name, count in item_counts.items()}
```

---

### 4. `staffing_optimizer.py` — Staff Optimization (Model 5)

```python
"""
Model 5: Staff Optimization Model
Recommends waiters and chefs per shift based on predicted demand.
"""
import logging
import math

logger = logging.getLogger(__name__)

# Tunable ratios (can be adjusted per outlet later)
TABLES_PER_WAITER = 4       # 1 waiter handles 4 active tables
ORDERS_PER_CHEF_PER_HOUR = 14  # 1 chef can handle 14 orders/hour
MIN_WAITERS = 1
MIN_CHEFS = 1
HOURLY_WAGE = 200  # Rs. per hour (rough average)

# Shift hour ranges
SHIFT_HOURS = {
    'MORNING':   (6, 14),
    'AFTERNOON': (14, 22),
    'NIGHT':     (22, 6),  # wraps around midnight
}


class StaffingOptimizer:
    """Recommends staffing levels based on predicted demand."""

    def predict(self, outlet_id: int, target_date, demand_forecast: dict = None) -> dict:
        """
        Generate staffing recommendations per shift.
        
        Args:
            outlet_id: outlet to predict for
            target_date: date to predict
            demand_forecast: output from BusyHoursPredictor.predict()
                             if None, will call it internally
        """
        from apps.hospitality_group.models import Outlet

        outlet = Outlet.objects.get(id=outlet_id)
        total_tables = outlet.servicenode_set.filter(node_type='TABLE').count() or 15

        # Get demand forecast if not provided
        if demand_forecast is None:
            from .demand_model import BusyHoursPredictor
            demand_forecast = BusyHoursPredictor().predict(outlet_id, target_date)

        hourly = {h['hour']: h['predicted_orders'] for h in demand_forecast.get('hourly_forecast', [])}

        recommendations = {}
        total_staff = 0
        total_hours = 0

        for shift_name, (start_h, end_h) in SHIFT_HOURS.items():
            # Get hours in this shift
            if start_h < end_h:
                shift_hours_list = list(range(start_h, end_h))
            else:  # night shift wraps
                shift_hours_list = list(range(start_h, 24)) + list(range(0, end_h))

            # Peak demand in this shift
            shift_orders = [hourly.get(h, 0) for h in shift_hours_list]
            peak_orders = max(shift_orders) if shift_orders else 0
            total_shift_orders = sum(shift_orders)

            # Calculate active tables at peak (assume 70% of orders are concurrent)
            active_tables_at_peak = min(math.ceil(peak_orders * 0.7), total_tables)

            # Waiters needed
            waiters = max(MIN_WAITERS, math.ceil(active_tables_at_peak / TABLES_PER_WAITER))

            # Chefs needed (based on peak hourly orders)
            chefs = max(MIN_CHEFS, math.ceil(peak_orders / ORDERS_PER_CHEF_PER_HOUR))

            shift_staff = waiters + chefs
            shift_duration = len(shift_hours_list)
            total_staff += shift_staff
            total_hours += shift_staff * shift_duration

            recommendations[shift_name] = {
                "recommended_waiters": waiters,
                "recommended_chefs": chefs,
                "predicted_peak_orders_per_hour": peak_orders,
                "predicted_total_orders": total_shift_orders,
                "reason": self._build_reason(waiters, chefs, peak_orders, active_tables_at_peak),
            }

        return {
            "date": str(target_date),
            "outlet_id": outlet_id,
            "staffing_recommendation": recommendations,
            "total_staff_needed": total_staff,
            "estimated_cost": f"₹{total_hours * HOURLY_WAGE:,.0f}",
        }

    def _build_reason(self, waiters, chefs, peak_orders, active_tables):
        parts = []
        parts.append(f"{waiters} waiter(s) for ~{active_tables} active tables")
        parts.append(f"{chefs} chef(s) for ~{peak_orders} orders/hr at peak")
        return " | ".join(parts)
```

---

### 5. `prediction_service.py` — Unified Facade

One class that the views call. Handles model loading, fallbacks, and error wrapping.

```python
"""
PredictionService — single entry point for all ML predictions.
Views call this, never the individual model classes directly.
"""
import logging
from datetime import datetime

from .demand_model import BusyHoursPredictor
from .footfall_model import FootfallForecaster
from .food_demand_model import FoodDemandPredictor
from .inventory_predictor import InventoryPredictor
from .staffing_optimizer import StaffingOptimizer
from .revenue_model import RevenueForecaster

logger = logging.getLogger(__name__)


class PredictionService:
    """Facade that wraps all 6 prediction models."""

    def __init__(self):
        self.demand = BusyHoursPredictor()
        self.footfall = FootfallForecaster()
        self.food_demand = FoodDemandPredictor()
        self.inventory = InventoryPredictor()
        self.staffing = StaffingOptimizer()
        self.revenue = RevenueForecaster()

    def get_busy_hours(self, outlet_id: int, date) -> dict:
        return self._safe_call(self.demand.predict, outlet_id, date)

    def get_footfall(self, outlet_id: int, date) -> dict:
        return self._safe_call(self.footfall.predict, outlet_id, date)

    def get_food_demand(self, outlet_id: int, date) -> dict:
        return self._safe_call(self.food_demand.predict, outlet_id, date)

    def get_inventory_alerts(self, outlet_id: int) -> dict:
        return self._safe_call(self.inventory.predict, outlet_id)

    def get_staffing(self, outlet_id: int, date) -> dict:
        demand = self.get_busy_hours(outlet_id, date)
        return self._safe_call(self.staffing.predict, outlet_id, date, demand)

    def get_revenue_forecast(self, outlet_id: int, date, days: int = 7) -> dict:
        return self._safe_call(self.revenue.predict, outlet_id, date, days)

    def get_dashboard(self, outlet_id: int, date) -> dict:
        """Combined dashboard — calls all models and merges results."""
        return {
            "busy_hours": self.get_busy_hours(outlet_id, date),
            "footfall": self.get_footfall(outlet_id, date),
            "food_demand": self.get_food_demand(outlet_id, date),
            "inventory_alerts": self.get_inventory_alerts(outlet_id),
            "staffing": self.get_staffing(outlet_id, date),
            "revenue": self.get_revenue_forecast(outlet_id, date),
        }

    def train_all(self, outlet_id: int) -> dict:
        """Train all trainable models for the given outlet."""
        results = {}
        for name, model in [
            ("busy_hours", self.demand),
            ("footfall", self.footfall),
            ("food_demand", self.food_demand),
            ("revenue", self.revenue),
        ]:
            try:
                results[name] = model.train(outlet_id)
            except Exception as e:
                logger.error("Training %s failed: %s", name, e)
                results[name] = {"status": "error", "error": str(e)}

        # inventory & staffing don't need training
        results["inventory"] = {"status": "rule-based (no training needed)"}
        results["staffing"] = {"status": "rule-based (no training needed)"}
        return results

    def _safe_call(self, fn, *args, **kwargs) -> dict:
        """Wrap any model call with error handling."""
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error("Prediction failed: %s — %s", fn.__qualname__, e)
            return {"error": str(e), "fallback": True}
```

---

### 6. Views — Prediction API Endpoints

```python
# Added to apps/predictive_core/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import datetime

from .ml.prediction_service import PredictionService


class PredictionBaseView(APIView):
    """Base view with shared param parsing."""
    permission_classes = [IsAuthenticated]

    def _parse_params(self, request):
        outlet_id = request.query_params.get('outlet')
        date_str = request.query_params.get('date')

        if not outlet_id:
            return None, None, Response(
                {"error": "outlet query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            outlet_id = int(outlet_id)
        except ValueError:
            return None, None, Response(
                {"error": "outlet must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None, None, Response(
                    {"error": "date must be YYYY-MM-DD format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            from django.utils import timezone
            target_date = timezone.now().date()

        return outlet_id, target_date, None


class BusyHoursPredictionView(PredictionBaseView):
    """GET /api/predictions/busy-hours/?outlet=4&date=2026-03-04"""

    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_busy_hours(outlet_id, target_date)
        return Response(result)


class FootfallPredictionView(PredictionBaseView):
    """GET /api/predictions/footfall/?outlet=4&date=2026-03-04"""

    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_footfall(outlet_id, target_date)
        return Response(result)


class FoodDemandPredictionView(PredictionBaseView):
    """GET /api/predictions/food-demand/?outlet=4&date=2026-03-04"""

    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_food_demand(outlet_id, target_date)
        return Response(result)


class InventoryAlertView(PredictionBaseView):
    """GET /api/predictions/inventory-alerts/?outlet=4"""

    def get(self, request):
        outlet_id, _, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_inventory_alerts(outlet_id)
        return Response(result)


class StaffingPredictionView(PredictionBaseView):
    """GET /api/predictions/staffing/?outlet=4&date=2026-03-04"""

    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_staffing(outlet_id, target_date)
        return Response(result)


class RevenuePredictionView(PredictionBaseView):
    """GET /api/predictions/revenue/?outlet=4&date=2026-03-04"""

    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        days = int(request.query_params.get('days', 7))
        service = PredictionService()
        result = service.get_revenue_forecast(outlet_id, target_date, days)
        return Response(result)


class PredictionDashboardView(PredictionBaseView):
    """GET /api/predictions/dashboard/?outlet=4&date=2026-03-04"""

    def get(self, request):
        outlet_id, target_date, error = self._parse_params(request)
        if error:
            return error

        service = PredictionService()
        result = service.get_dashboard(outlet_id, target_date)
        return Response(result)


class TrainModelsView(APIView):
    """
    POST /api/predictions/train/?outlet=4
    Manager-only endpoint to trigger model retraining.
    """
    permission_classes = [IsAuthenticated]
    # Should also add IsManager permission in production

    def post(self, request):
        outlet_id = request.query_params.get('outlet')
        if not outlet_id:
            return Response(
                {"error": "outlet query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = PredictionService()
        results = service.train_all(int(outlet_id))
        return Response({"status": "training complete", "results": results})
```

---

### 7. URL Routing

```python
# Added to apps/predictive_core/urls.py

from django.urls import path
from .views import (
    BusyHoursPredictionView,
    FootfallPredictionView,
    FoodDemandPredictionView,
    InventoryAlertView,
    StaffingPredictionView,
    RevenuePredictionView,
    PredictionDashboardView,
    TrainModelsView,
)

# Add these to existing urlpatterns:
urlpatterns += [
    # Prediction endpoints
    path('predictions/busy-hours/',       BusyHoursPredictionView.as_view(),  name='predict-busy-hours'),
    path('predictions/footfall/',         FootfallPredictionView.as_view(),   name='predict-footfall'),
    path('predictions/food-demand/',      FoodDemandPredictionView.as_view(), name='predict-food-demand'),
    path('predictions/inventory-alerts/', InventoryAlertView.as_view(),       name='predict-inventory'),
    path('predictions/staffing/',         StaffingPredictionView.as_view(),   name='predict-staffing'),
    path('predictions/revenue/',          RevenuePredictionView.as_view(),    name='predict-revenue'),
    path('predictions/dashboard/',        PredictionDashboardView.as_view(),  name='predict-dashboard'),
    path('predictions/train/',            TrainModelsView.as_view(),          name='predict-train'),
]
```

---

### 8. Management Command — `train_models.py`

```python
"""
Management command to train all ML models for an outlet.
Usage:
    python manage.py train_models --outlet 4
    python manage.py train_models --all
"""
from django.core.management.base import BaseCommand
from apps.predictive_core.ml.prediction_service import PredictionService
from apps.hospitality_group.models import Outlet


class Command(BaseCommand):
    help = "Train all ML prediction models for one or all outlets"

    def add_arguments(self, parser):
        parser.add_argument('--outlet', type=int, help='Outlet ID to train for')
        parser.add_argument('--all', action='store_true', help='Train for all outlets')

    def handle(self, *args, **options):
        service = PredictionService()

        if options['all']:
            outlets = Outlet.objects.all()
        elif options['outlet']:
            outlets = Outlet.objects.filter(id=options['outlet'])
        else:
            self.stderr.write(self.style.ERROR("Provide --outlet <id> or --all"))
            return

        for outlet in outlets:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Training models for: {outlet.name} (ID: {outlet.pk})")
            self.stdout.write(f"{'='*60}")

            results = service.train_all(outlet.pk)

            for model_name, result in results.items():
                status_str = result.get('status', 'unknown')
                if status_str == 'trained':
                    metrics = result.get('metrics', {})
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✅ {model_name}: MAE={metrics.get('mae')}, "
                        f"R²={metrics.get('r2')}, "
                        f"samples={metrics.get('train_samples')}"
                    ))
                elif status_str == 'skipped':
                    self.stdout.write(self.style.WARNING(
                        f"  ⏭️  {model_name}: {result.get('reason')}"
                    ))
                elif 'rule-based' in status_str:
                    self.stdout.write(self.style.NOTICE(
                        f"  📐 {model_name}: {status_str}"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f"  ❌ {model_name}: {result.get('error', status_str)}"
                    ))

        self.stdout.write(self.style.SUCCESS("\nDone."))
```

---

## Complete API Reference

| Endpoint | Method | Auth | Query Params | Response Summary |
|---|---|---|---|---|
| `/api/predictions/busy-hours/` | GET | JWT | `outlet` (required), `date` (optional, default=today) | `{hourly_forecast[], peak_hour, total_predicted_orders}` |
| `/api/predictions/footfall/` | GET | JWT | `outlet`, `date` | `{hourly_guests[], total_predicted_guests, avg_party_size}` |
| `/api/predictions/food-demand/` | GET | JWT | `outlet`, `date` | `{category_forecast{}, top_items_forecast[]}` |
| `/api/predictions/inventory-alerts/` | GET | JWT | `outlet` | `{inventory_alerts[], expiring_soon[], total_critical}` |
| `/api/predictions/staffing/` | GET | JWT | `outlet`, `date` | `{staffing_recommendation{MORNING,AFTERNOON,NIGHT}, total_staff_needed, estimated_cost}` |
| `/api/predictions/revenue/` | GET | JWT | `outlet`, `date`, `days` (default=7) | `{next_day{predicted_revenue, confidence_range}, next_week{daily_breakdown[]}}` |
| `/api/predictions/dashboard/` | GET | JWT | `outlet`, `date` | All 6 predictions merged into one response |
| `/api/predictions/train/` | POST | JWT + Manager | `outlet` | `{status, results{model_name: metrics}}` |

### Example Request & Response

```bash
# Busy Hours prediction
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/predictions/busy-hours/?outlet=4&date=2026-03-04"
```

```json
{
  "date": "2026-03-04",
  "hourly_forecast": [
    {"hour": 8,  "predicted_orders": 2},
    {"hour": 9,  "predicted_orders": 4},
    {"hour": 10, "predicted_orders": 5},
    {"hour": 11, "predicted_orders": 8},
    {"hour": 12, "predicted_orders": 14},
    {"hour": 13, "predicted_orders": 12},
    {"hour": 14, "predicted_orders": 7},
    {"hour": 15, "predicted_orders": 4},
    {"hour": 16, "predicted_orders": 3},
    {"hour": 17, "predicted_orders": 5},
    {"hour": 18, "predicted_orders": 8},
    {"hour": 19, "predicted_orders": 13},
    {"hour": 20, "predicted_orders": 11},
    {"hour": 21, "predicted_orders": 9},
    {"hour": 22, "predicted_orders": 5},
    {"hour": 23, "predicted_orders": 2}
  ],
  "peak_hour": 12,
  "total_predicted_orders": 112,
  "confidence": "high"
}
```

```bash
# Train all models for an outlet
curl -X POST -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/predictions/train/?outlet=4"
```

```json
{
  "status": "training complete",
  "results": {
    "busy_hours": {"status": "trained", "metrics": {"mae": 1.8, "rmse": 2.3, "r2": 0.87}},
    "footfall":   {"status": "trained", "metrics": {"mae": 3.2, "rmse": 4.1, "r2": 0.81}},
    "food_demand":{"status": "trained", "metrics": {"mae": 2.1, "rmse": 2.9, "r2": 0.79}},
    "revenue":    {"status": "trained", "metrics": {"mae": 850, "rmse": 1100, "r2": 0.84}},
    "inventory":  {"status": "rule-based (no training needed)"},
    "staffing":   {"status": "rule-based (no training needed)"}
  }
}
```
