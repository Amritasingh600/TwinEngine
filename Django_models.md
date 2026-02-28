# TwinEngine Hospitality - Django Models Documentation

This document outlines all Django models across the five backend apps designed for the hospitality digital twin platform.

---

## 🏨 1. App: `hospitality_group`

**Role:** Manages the multi-tenant SaaS layer for brands and their outlets.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **Brand** | Stores corporate data for restaurant chains/groups | `name`, `corporate_id`, `contact_email`, `subscription_tier`, `is_active` |
| **Outlet** | Individual restaurant/cafe locations under a brand | `brand (FK)`, `name`, `address`, `city`, `manager_name`, `manager_phone`, `seating_capacity`, `operating_hours`, `is_active` |
| **UserProfile** | Extends User to link staff to specific outlets | `user (OneToOne)`, `outlet (FK)`, `role` (MANAGER/STAFF/VIEWER), `phone`, `is_active` |

### Model Details

```python
class Brand(models.Model):
    """Restaurant chain or hospitality group."""
    TIER_CHOICES = [
        ('STARTER', 'Starter - Up to 3 outlets'),
        ('GROWTH', 'Growth - Up to 10 outlets'),
        ('ENTERPRISE', 'Enterprise - Unlimited'),
    ]
    name = models.CharField(max_length=200)
    corporate_id = models.CharField(max_length=50, unique=True)
    contact_email = models.EmailField()
    subscription_tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Outlet(models.Model):
    """Individual restaurant or cafe location."""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='outlets')
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    manager_name = models.CharField(max_length=100)
    manager_phone = models.CharField(max_length=20)
    seating_capacity = models.PositiveIntegerField(default=50)
    operating_hours = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
    """Extended user profile for outlet staff."""
    ROLE_CHOICES = [
        ('MANAGER', 'Floor Manager'),
        ('STAFF', 'Service Staff'),
        ('VIEWER', 'View Only'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='staff')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
```

---

## 🗺️ 2. App: `layout_twin`

**Role:** The core "Digital Twin" configuration engine for 3D spatial layout.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **ServiceNode** | Tables, kitchen stations, or service areas in 3D space | `outlet (FK)`, `name`, `node_type` (TABLE/KITCHEN/WASH/BAR/ENTRANCE), `pos_x/y/z`, `capacity`, `current_status`, `is_active` |
| **ServiceFlow** | Defines operational flow paths between nodes | `outlet (FK)`, `source_node (FK)`, `target_node (FK)`, `flow_type` (ORDER/DELIVERY/CLEANUP), `avg_duration_minutes` |

### Model Details

```python
class ServiceNode(models.Model):
    """Represents tables, kitchen stations, or service areas in 3D space."""
    NODE_TYPE_CHOICES = [
        ('TABLE', 'Customer Table'),
        ('KITCHEN', 'Kitchen Station'),
        ('WASH', 'Dish Washing Area'),
        ('BAR', 'Bar Counter'),
        ('ENTRANCE', 'Entrance/Host Stand'),
    ]
    STATUS_CHOICES = [
        ('BLUE', 'Available'),      # Table free
        ('RED', 'Needs Attention'), # Wait time exceeded
        ('GREEN', 'Delivered'),     # Order delivered, happy
        ('YELLOW', 'Waiting'),      # Order in progress
        ('GREY', 'Reserved'),       # Reserved/inactive
    ]
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='service_nodes')
    name = models.CharField(max_length=100)
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES)
    pos_x = models.FloatField(default=0.0)
    pos_y = models.FloatField(default=0.0)
    pos_z = models.FloatField(default=0.0)
    capacity = models.PositiveIntegerField(default=4)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BLUE')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ServiceFlow(models.Model):
    """Defines operational flow between service nodes."""
    FLOW_TYPE_CHOICES = [
        ('ORDER', 'Order Flow'),
        ('DELIVERY', 'Food Delivery'),
        ('CLEANUP', 'Table Cleanup'),
    ]
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='service_flows')
    source_node = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='outgoing_flows')
    target_node = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='incoming_flows')
    flow_type = models.CharField(max_length=20, choices=FLOW_TYPE_CHOICES)
    avg_duration_minutes = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
```

---

## 🎫 3. App: `order_engine`

**Role:** Real-time order lifecycle tracking and payment processing.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **OrderTicket** | Tracks order from placement to completion | `table (FK)`, `waiter (FK)`, `status`, `guest_count`, `items (JSON)`, `subtotal`, `tax`, `total`, `special_requests`, `placed_at`, `served_at`, `completed_at` |
| **PaymentLog** | Records payment transactions | `order (FK)`, `amount`, `payment_method`, `status`, `transaction_id` |

### Model Details

```python
class OrderTicket(models.Model):
    """Real-time order lifecycle tracking - drives table color status."""
    STATUS_CHOICES = [
        ('PLACED', 'Order Placed'),
        ('PREPARING', 'In Kitchen'),
        ('READY', 'Ready for Pickup'),
        ('SERVED', 'Served to Table'),
        ('COMPLETED', 'Bill Paid'),
        ('CANCELLED', 'Cancelled'),
    ]
    table = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='orders')
    waiter = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='orders_handled')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLACED')
    guest_count = models.PositiveIntegerField(default=1)
    items = models.JSONField(default=list)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_requests = models.TextField(blank=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    served_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class PaymentLog(models.Model):
    """Payment transaction records."""
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI'),
        ('WALLET', 'Digital Wallet'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Successful'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    order = models.ForeignKey(OrderTicket, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 🔮 4. App: `predictive_core`

**Role:** AI/ML predictions for demand forecasting, inventory, and staffing.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **SalesData** | Aggregated sales data for AI predictions | `outlet (FK)`, `date`, `hour`, `total_orders`, `total_revenue`, `avg_order_value`, `peak_hour`, `covers_served` |
| **InventoryItem** | Track inventory levels with reorder predictions | `outlet (FK)`, `name`, `category`, `current_stock`, `unit`, `reorder_level`, `predicted_depletion_date`, `last_restocked` |
| **StaffSchedule** | AI-optimized staff scheduling | `outlet (FK)`, `staff_member (FK)`, `date`, `shift_start`, `shift_end`, `role_assigned`, `predicted_demand_level`, `is_confirmed` |

### Model Details

```python
class SalesData(models.Model):
    """Aggregated sales data for AI predictions."""
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='sales_data')
    date = models.DateField()
    hour = models.PositiveIntegerField(validators=[MaxValueValidator(23)])
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peak_hour = models.BooleanField(default=False)
    covers_served = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class InventoryItem(models.Model):
    """Inventory tracking with predictive reordering."""
    CATEGORY_CHOICES = [
        ('PRODUCE', 'Fresh Produce'),
        ('DAIRY', 'Dairy Products'),
        ('MEAT', 'Meat & Poultry'),
        ('BEVERAGE', 'Beverages'),
        ('DRY_GOODS', 'Dry Goods'),
        ('SUPPLIES', 'Supplies'),
    ]
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='inventory')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    predicted_depletion_date = models.DateField(null=True, blank=True)
    last_restocked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class StaffSchedule(models.Model):
    """AI-optimized staff scheduling."""
    DEMAND_LEVEL_CHOICES = [
        ('LOW', 'Low Demand'),
        ('MEDIUM', 'Medium Demand'),
        ('HIGH', 'High Demand'),
        ('PEAK', 'Peak Hours'),
    ]
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='schedules')
    staff_member = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    role_assigned = models.CharField(max_length=50)
    predicted_demand_level = models.CharField(max_length=20, choices=DEMAND_LEVEL_CHOICES, default='MEDIUM')
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 📊 5. App: `insights_hub`

**Role:** Reporting, analytics, and AI-generated summaries.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **DailySummary** | End-of-day aggregated metrics for dashboards | `outlet (FK)`, `date`, `total_orders`, `total_revenue`, `avg_table_turnover`, `peak_hour`, `peak_hour_revenue`, `total_covers`, `avg_wait_time_minutes`, `customer_satisfaction_score` |
| **PDFReport** | Stored AI-generated report documents | `outlet (FK)`, `report_type`, `date_range_start/end`, `cloudinary_url`, `gpt_summary`, `generated_at`, `generated_by` |

### Model Details

```python
class DailySummary(models.Model):
    """End-of-day aggregated metrics for each outlet."""
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='daily_summaries')
    date = models.DateField()
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_table_turnover = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    peak_hour = models.PositiveIntegerField(null=True, validators=[MaxValueValidator(23)])
    peak_hour_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_covers = models.PositiveIntegerField(default=0)
    avg_wait_time_minutes = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    customer_satisfaction_score = models.DecimalField(max_digits=3, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PDFReport(models.Model):
    """AI-generated PDF reports stored on Cloudinary."""
    REPORT_TYPE_CHOICES = [
        ('DAILY', 'Daily Operations Report'),
        ('WEEKLY', 'Weekly Summary'),
        ('MONTHLY', 'Monthly Analytics'),
        ('CUSTOM', 'Custom Date Range'),
    ]
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    date_range_start = models.DateField()
    date_range_end = models.DateField()
    cloudinary_url = models.URLField(blank=True)
    gpt_summary = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
```

---

## 🛠️ Implementation Summary

| App | Models | Purpose |
|-----|--------|---------|
| `hospitality_group` | 3 | Multi-tenant brand/outlet management |
| `layout_twin` | 2 | 3D floor layout and service flows |
| `order_engine` | 2 | Real-time order lifecycle tracking |
| `predictive_core` | 3 | AI predictions and forecasting |
| `insights_hub` | 2 | Reporting and analytics |
| **Total** | **12** | Complete hospitality operations |

---

## 🎨 Table Status Color Mapping

The `ServiceNode.current_status` field drives the 3D visualization colors:

| Status | Color | Trigger Condition |
|--------|-------|-------------------|
| `BLUE` | 🔵 Blue | Table available, no active orders |
| `YELLOW` | 🟡 Yellow | Order placed, waiting for food |
| `GREEN` | 🟢 Green | Order delivered successfully |
| `RED` | 🔴 Red | Wait time exceeded threshold |
| `GREY` | ⚫ Grey | Table reserved or inactive |

---

## 🔗 Entity Relationships

```
Brand (1) ──────────────── (N) Outlet
                               │
                               ├──── (N) ServiceNode ──── (N) OrderTicket
                               │           │                    │
                               │           └── ServiceFlow       └── PaymentLog
                               │
                               ├──── (N) UserProfile ──── StaffSchedule
                               │
                               ├──── (N) SalesData
                               ├──── (N) InventoryItem
                               ├──── (N) DailySummary
                               └──── (N) PDFReport
```
