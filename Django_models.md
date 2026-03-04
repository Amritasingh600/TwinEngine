# TwinEngine Hospitality — Django Models Documentation

This document outlines all Django models across the five backend apps designed for the hospitality digital twin platform.

> **Last Updated:** 4 March 2026 — Reflects the actual implemented schema.

---

## 🏨 1. App: `hospitality_group`

**Role:** Manages the multi-tenant SaaS layer for brands and their outlets.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **Brand** | Stores corporate data for restaurant chains/groups | `name`, `logo_url`, `corporate_id`, `contact_email`, `subscription_tier`, `created_at`, `updated_at` |
| **Outlet** | Individual restaurant/cafe locations under a brand | `brand (FK)`, `name`, `address`, `city`, `seating_capacity`, `opening_time`, `closing_time`, `is_active` |
| **UserProfile** | Extends User to link staff to specific outlets | `user (OneToOne)`, `outlet (FK)`, `role` (MANAGER/WAITER/CHEF/HOST/CASHIER), `phone`, `is_on_shift` |

### Model Details

```python
class Brand(models.Model):
    """Parent organization for restaurant chains."""
    SUBSCRIPTION_TIERS = [
        ('BASIC', 'Basic'),
        ('PRO', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    name = models.CharField(max_length=255)
    logo_url = models.URLField(blank=True, null=True)
    corporate_id = models.CharField(max_length=100, unique=True)
    contact_email = models.EmailField()
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIERS, default='BASIC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

class Outlet(models.Model):
    """Specific restaurant location under a Brand."""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='outlets')
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    seating_capacity = models.IntegerField(default=0)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['brand', 'name']
        unique_together = ['brand', 'name']

class UserProfile(models.Model):
    """Links staff to specific Outlets with role-based access."""
    ROLE_CHOICES = [
        ('MANAGER', 'Manager'),
        ('WAITER', 'Waiter'),
        ('CHEF', 'Chef'),
        ('HOST', 'Host/Hostess'),
        ('CASHIER', 'Cashier'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='staff')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='WAITER')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_on_shift = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['outlet', 'user__username']
```

---

## 🗺️ 2. App: `layout_twin`

**Role:** The core "Digital Twin" configuration engine for 3D spatial layout.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **ServiceNode** | Tables, kitchen stations, or service areas in 3D space | `outlet (FK)`, `name`, `node_type` (TABLE/KITCHEN/WASH/BAR/ENTRY), `pos_x/y/z`, `capacity`, `current_status`, `is_active` |
| **ServiceFlow** | Defines operational flow paths between nodes | `source_node (FK)`, `target_node (FK)`, `flow_type` (FOOD_DELIVERY/DISH_RETURN/ORDER_PATH/CUSTOMER_FLOW), `is_active` |

### Model Details

```python
class ServiceNode(models.Model):
    """Represents tables, kitchen stations, or service areas in 3D space."""
    NODE_TYPE_CHOICES = [
        ('TABLE', 'Table'),
        ('KITCHEN', 'Kitchen Station'),
        ('WASH', 'Washing Station'),
        ('BAR', 'Bar Counter'),
        ('ENTRY', 'Entry/Reception'),
    ]
    STATUS_CHOICES = [
        ('BLUE', 'Empty / Ready'),           # 🔵 Table free, available
        ('RED', 'Occupied - Waiting'),       # 🔴 Food not served yet
        ('GREEN', 'Occupied - Served'),      # 🟢 Food served, eating
        ('YELLOW', 'Issue / Delay'),         # 🟡 Wait > 15 min or problem
        ('GREY', 'Maintenance / Reserved'),  # ⚫ Not available
    ]
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='service_nodes')
    name = models.CharField(max_length=100)
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES, default='TABLE')
    pos_x = models.FloatField(default=0.0)
    pos_y = models.FloatField(default=0.0)
    pos_z = models.FloatField(default=0.0)
    capacity = models.IntegerField(default=4)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BLUE')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['outlet', 'name']
        unique_together = ['outlet', 'name']

class ServiceFlow(models.Model):
    """Directional paths between nodes for operational flow visualization."""
    FLOW_TYPE_CHOICES = [
        ('FOOD_DELIVERY', 'Food Delivery'),      # Kitchen → Table
        ('DISH_RETURN', 'Dish Return'),          # Table → Washing
        ('ORDER_PATH', 'Order Path'),            # Table → Kitchen
        ('CUSTOMER_FLOW', 'Customer Flow'),      # Entry → Table → Exit
    ]
    source_node = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='outgoing_flows')
    target_node = models.ForeignKey(ServiceNode, on_delete=models.CASCADE, related_name='incoming_flows')
    flow_type = models.CharField(max_length=20, choices=FLOW_TYPE_CHOICES, default='FOOD_DELIVERY')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['source_node', 'target_node']
        unique_together = ['source_node', 'target_node', 'flow_type']
```

---

## 🎫 3. App: `order_engine`

**Role:** Real-time order lifecycle tracking and payment processing.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **OrderTicket** | Tracks order from placement to completion | `table (FK)`, `waiter (FK)`, `customer_name`, `party_size`, `status`, `items (JSON)`, `subtotal`, `tax`, `total`, `special_requests`, `placed_at`, `served_at`, `completed_at` |
| **PaymentLog** | Records payment transactions | `order (FK)`, `amount`, `method`, `status`, `transaction_id`, `tip_amount` |

### Model Details

```python
class OrderTicket(models.Model):
    """Real-time order lifecycle tracking - drives table color status."""
    STATUS_CHOICES = [
        ('PLACED', 'Order Placed'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready for Pickup'),
        ('SERVED', 'Served'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    table = models.ForeignKey(
        ServiceNode, on_delete=models.CASCADE, related_name='orders',
        limit_choices_to={'node_type': 'TABLE'}
    )
    waiter = models.ForeignKey(
        UserProfile, on_delete=models.SET_NULL, null=True,
        related_name='orders_served',
        limit_choices_to={'role__in': ['WAITER', 'MANAGER']}
    )
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    party_size = models.IntegerField(default=1)
    items = models.JSONField(default=list)
    special_requests = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLACED')
    placed_at = models.DateTimeField(auto_now_add=True)
    served_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-placed_at']
        indexes = [
            models.Index(fields=['table', '-placed_at']),
            models.Index(fields=['status']),
            models.Index(fields=['waiter', '-placed_at']),
        ]

    @property
    def wait_time_minutes(self):
        """Calculate wait time in minutes since order was placed."""
        ...

    @property
    def is_long_wait(self):
        """True if PLACED/PREPARING and wait > 15 minutes."""
        ...

class PaymentLog(models.Model):
    """Payment transactions linked to orders."""
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI Payment'),
        ('WALLET', 'Digital Wallet'),
        ('SPLIT', 'Split Payment'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    order = models.ForeignKey(OrderTicket, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', '-created_at']),
            models.Index(fields=['status']),
        ]
```

---

## 🔮 4. App: `predictive_core`

**Role:** AI/ML predictions for demand forecasting, inventory, and staffing.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **SalesData** | Aggregated hourly sales data for AI predictions | `outlet (FK)`, `date`, `hour`, `total_orders`, `total_revenue`, `avg_ticket_size`, `avg_wait_time_minutes`, `category_sales (JSON)`, `top_items (JSON)`, `day_of_week`, `is_holiday`, `weather_condition` |
| **InventoryItem** | Track inventory levels with reorder predictions | `outlet (FK)`, `name`, `category`, `unit`, `current_quantity`, `reorder_threshold`, `par_level`, `unit_cost`, `expiry_date`, `last_restocked` |
| **StaffSchedule** | AI-optimized staff scheduling | `staff (FK)`, `date`, `shift`, `start_time`, `end_time`, `is_confirmed`, `checked_in`, `checked_out`, `is_ai_suggested`, `notes` |

### Model Details

```python
class SalesData(models.Model):
    """Aggregated sales data for AI predictions and demand forecasting."""
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='sales_data')
    date = models.DateField()
    hour = models.IntegerField(help_text="Hour of day (0-23)")
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_ticket_size = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_wait_time_minutes = models.FloatField(default=0.0)
    category_sales = models.JSONField(default=dict)
    top_items = models.JSONField(default=list)
    day_of_week = models.IntegerField(help_text="0=Monday, 6=Sunday")
    is_holiday = models.BooleanField(default=False)
    weather_condition = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'hour']
        unique_together = ['outlet', 'date', 'hour']
        indexes = [
            models.Index(fields=['outlet', '-date']),
            models.Index(fields=['day_of_week']),
        ]

class InventoryItem(models.Model):
    """Tracks ingredient/supply inventory with predictive reorder alerts."""
    CATEGORY_CHOICES = [
        ('PRODUCE', 'Fresh Produce'),
        ('DAIRY', 'Dairy Products'),
        ('MEAT', 'Meat & Poultry'),
        ('DRY', 'Dry Goods'),
        ('BEVERAGE', 'Beverages'),
        ('SUPPLIES', 'Kitchen Supplies'),
    ]
    UNIT_CHOICES = [
        ('KG', 'Kilograms'),
        ('L', 'Liters'),
        ('PCS', 'Pieces'),
        ('BAGS', 'Bags'),
        ('BOXES', 'Boxes'),
    ]
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='inventory_items')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='DRY')
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='KG')
    current_quantity = models.FloatField(default=0.0)
    reorder_threshold = models.FloatField(default=10.0)
    par_level = models.FloatField(default=50.0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiry_date = models.DateField(blank=True, null=True)
    last_restocked = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['outlet', 'category', 'name']
        unique_together = ['outlet', 'name']
        indexes = [
            models.Index(fields=['outlet', 'category']),
        ]

    @property
    def is_low_stock(self):
        """True if current_quantity <= reorder_threshold."""
        return self.current_quantity <= self.reorder_threshold

class StaffSchedule(models.Model):
    """Staff scheduling optimized by AI predictions."""
    SHIFT_CHOICES = [
        ('MORNING', 'Morning (6AM-2PM)'),
        ('AFTERNOON', 'Afternoon (2PM-10PM)'),
        ('NIGHT', 'Night (10PM-6AM)'),
        ('SPLIT', 'Split Shift'),
    ]
    staff = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='MORNING')
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_confirmed = models.BooleanField(default=False)
    checked_in = models.DateTimeField(blank=True, null=True)
    checked_out = models.DateTimeField(blank=True, null=True)
    is_ai_suggested = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'start_time']
        unique_together = ['staff', 'date', 'shift']
        indexes = [
            models.Index(fields=['staff', '-date']),
            models.Index(fields=['date', 'shift']),
        ]
```

---

## 📊 5. App: `insights_hub`

**Role:** Reporting, analytics, and AI-generated summaries.

| Model | Purpose | Key Fields |
| --- | --- | --- |
| **DailySummary** | End-of-day aggregated metrics for dashboards | `outlet (FK)`, `date`, `total_revenue`, `total_orders`, `avg_ticket_size`, `total_tips`, `total_guests`, `avg_table_turnover_time`, `avg_wait_time`, `peak_hour`, `peak_revenue`, `delayed_orders`, `cancelled_orders`, `sales_by_category (JSON)`, `top_selling_items (JSON)`, `staff_count`, `revenue_per_staff` |
| **PDFReport** | Stored AI-generated report documents | `outlet (FK)`, `report_type`, `start_date`, `end_date`, `cloudinary_url`, `gpt_summary`, `insights (JSON)`, `recommendations (JSON)`, `status`, `error_message`, `generated_by`, `created_at`, `completed_at` |

### Model Details

```python
class DailySummary(models.Model):
    """End-of-day aggregated metrics for each outlet."""
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='daily_summaries')
    date = models.DateField()

    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    avg_ticket_size = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tips = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Operational metrics
    total_guests = models.IntegerField(default=0)
    avg_table_turnover_time = models.FloatField(default=0.0)
    avg_wait_time = models.FloatField(default=0.0)

    # Performance metrics
    peak_hour = models.IntegerField(default=12)
    peak_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Issues tracking
    delayed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)

    # Category breakdown (JSON)
    sales_by_category = models.JSONField(default=dict)
    top_selling_items = models.JSONField(default=list)

    # Staff metrics
    staff_count = models.IntegerField(default=0)
    revenue_per_staff = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['outlet', 'date']

class PDFReport(models.Model):
    """AI-generated PDF reports with insights and recommendations."""
    REPORT_TYPE_CHOICES = [
        ('DAILY', 'Daily Operations Report'),
        ('WEEKLY', 'Weekly Summary'),
        ('MONTHLY', 'Monthly Analysis'),
        ('CUSTOM', 'Custom Report'),
    ]
    GENERATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('GENERATING', 'Generating'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='pdf_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='DAILY')
    start_date = models.DateField()
    end_date = models.DateField()
    cloudinary_url = models.URLField(blank=True, null=True)
    gpt_summary = models.TextField(blank=True, null=True)
    insights = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=GENERATION_STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    generated_by = models.CharField(max_length=50, default='GPT-4')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
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

### Table Status Color System

| Color | Status | Meaning | Trigger |
|-------|--------|---------|---------|
| 🔵 BLUE | Empty / Ready | Table is free and available | Order COMPLETED or CANCELLED (no other active orders) |
| 🔴 RED | Occupied - Waiting | Food not yet served | Order PLACED or PREPARING |
| 🟢 GREEN | Occupied - Served | Food has been served | Order SERVED |
| 🟡 YELLOW | Issue / Delay | Wait time exceeded threshold | Wait > 15 minutes (via `check_wait_times` command) |
| ⚫ GREY | Maintenance / Reserved | Table not available | Manual status change |

### Order Status Transitions

```
PLACED → PREPARING → READY → SERVED → COMPLETED
  ↓         ↓          ↓       ↓
  └─────────┴──────────┴───────┴──→ CANCELLED
```
