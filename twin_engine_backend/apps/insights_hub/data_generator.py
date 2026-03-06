"""
API-driven synthetic data generator for restaurant simulation.

Generates realistic data across ALL database tables for a given outlet,
covering full restaurant working hours. Designed to be called from
the Manager portal's "Generate" button.

Key design:
  - Generates MULTI-DAY historical data (default 14 days) so ML models
    have enough training data for predictions & reports.
  - Fetches last existing data to avoid unique constraint collisions.
  - Uses the outlet's actual opening/closing times.
  - All data is interconnected: orders → payments, tables → orders, etc.
  - Inventory shows realistic depletion trends over the date range.
  - Day-to-day variation in orders, revenue, and foot traffic for
    realistic model training (weekday vs weekend, peak vs off-peak).

ML model minimums:
  BusyHours / Footfall / FoodDemand → 7+ days of SalesData (hourly)
  Revenue Forecaster → 7+ DailySummary records
  Inventory Predictor → InventoryItems + 7+ days of OrderTicket history
  Staffing Optimizer → depends on BusyHours output
"""

import random
import uuid
from datetime import datetime, timedelta, time, date
from decimal import Decimal

from django.utils import timezone
from django.db.models import Max

from apps.hospitality_group.models import Outlet, UserProfile
from apps.layout_twin.models import ServiceNode, ServiceFlow
from apps.order_engine.models import OrderTicket, PaymentLog
from apps.predictive_core.models import SalesData, InventoryItem, StaffSchedule
from apps.insights_hub.models import DailySummary


# ── Menu data ──
MENU = {
    'starters': [
        {'name': 'Paneer Tikka', 'price': 320},
        {'name': 'Chicken 65', 'price': 280},
        {'name': 'Veg Spring Rolls', 'price': 220},
        {'name': 'Mutton Seekh Kebab', 'price': 380},
        {'name': 'Crispy Corn', 'price': 200},
        {'name': 'Fish Amritsari', 'price': 350},
    ],
    'mains': [
        {'name': 'Butter Chicken', 'price': 450},
        {'name': 'Dal Makhani', 'price': 280},
        {'name': 'Palak Paneer', 'price': 320},
        {'name': 'Mutton Rogan Josh', 'price': 520},
        {'name': 'Hyderabadi Biryani', 'price': 420},
        {'name': 'Chole Bhature', 'price': 250},
        {'name': 'Prawn Masala', 'price': 480},
        {'name': 'Veg Kolhapuri', 'price': 300},
    ],
    'breads': [
        {'name': 'Butter Naan', 'price': 60},
        {'name': 'Garlic Naan', 'price': 70},
        {'name': 'Tandoori Roti', 'price': 40},
        {'name': 'Laccha Paratha', 'price': 80},
    ],
    'beverages': [
        {'name': 'Masala Chai', 'price': 60},
        {'name': 'Cold Coffee', 'price': 150},
        {'name': 'Fresh Lime Soda', 'price': 100},
        {'name': 'Mango Lassi', 'price': 130},
        {'name': 'Espresso', 'price': 120},
    ],
    'desserts': [
        {'name': 'Gulab Jamun', 'price': 120},
        {'name': 'Rasmalai', 'price': 150},
        {'name': 'Kulfi', 'price': 100},
        {'name': 'Brownie with Ice Cream', 'price': 220},
    ],
}

FLAT_MENU = [item for cat in MENU.values() for item in cat]

CUSTOMER_NAMES = [
    'Rahul Verma', 'Priya Singh', 'Arun Mehta', 'Sneha Reddy', 'Vikram Joshi',
    'Ananya Gupta', 'Karthik Iyer', 'Pooja Sharma', 'Rohit Das', 'Meera Nair',
    'Sanjay Kapoor', 'Divya Patel', 'Arjun Malhotra', 'Neha Bhatia', 'Rajesh Kumar',
    'Sakshi Agarwal', 'Deepak Choudhary', 'Ishita Jain', 'Manish Yadav', 'Ritu Saxena',
    None, None, None,
]

SPECIAL_REQUESTS = [
    'Less spicy please', 'Extra napkins',
    'Birthday celebration - need a candle on dessert',
    'Nut allergy - strictly no peanuts',
    'Jain food - no onion, no garlic',
    'Extra raita on the side', 'Kids portions for 2 items',
    'Quick service please - in a hurry', 'Vegan - no dairy or ghee',
    None, None, None, None, None, None, None,
]

CANCELLATION_REASONS = [
    'Customer walked out - long wait',
    'Wrong dish delivered, customer left',
    'Allergy concern - ingredient mismatch',
    'Customer changed mind',
    'Kitchen ran out of ingredients',
]

INVENTORY_ITEMS = [
    ('Paneer', 'DAIRY', 'KG', 350), ('Tomatoes', 'PRODUCE', 'KG', 45),
    ('Chicken', 'MEAT', 'KG', 280), ('Basmati Rice', 'DRY', 'KG', 120),
    ('Cooking Oil', 'DRY', 'L', 180), ('Flour (Maida)', 'DRY', 'KG', 55),
    ('Onions', 'PRODUCE', 'KG', 25), ('Milk', 'DAIRY', 'L', 65),
    ('Sugar', 'DRY', 'KG', 50), ('Coffee Beans', 'BEVERAGE', 'KG', 850),
    ('Mango Pulp', 'BEVERAGE', 'L', 200), ('Soda Water', 'BEVERAGE', 'L', 25),
    ('Paper Napkins', 'SUPPLIES', 'BOXES', 120), ('Cream', 'DAIRY', 'L', 250),
    ('Prawns (frozen)', 'MEAT', 'KG', 650), ('Curd / Yogurt', 'DAIRY', 'KG', 100),
    ('Salt', 'DRY', 'KG', 30), ('Cleaning Solution', 'SUPPLIES', 'L', 150),
]


def generate_outlet_data(outlet_id, target_date=None, order_count=40, days=14):
    """
    Generate multi-day realistic restaurant data for an outlet.

    Creates enough historical data for all ML models to train and
    for reports to have meaningful aggregations.

    Args:
        outlet_id: ID of the Outlet to generate data for
        target_date: last date in the range (defaults to today)
        order_count: base number of orders PER DAY (varies ±30%)
        days: number of days of history to generate (default 14)

    Returns:
        dict with counts of created records per model
    """
    outlet = Outlet.objects.get(pk=outlet_id)
    if target_date is None:
        target_date = timezone.now().date()

    now = timezone.now()
    results = {
        'tables': 0,
        'flows': 0,
        'staff_available': 0,
        'orders': 0,
        'payments': 0,
        'inventory_items': 0,
        'schedules': 0,
        'sales_data_hours': 0,
        'daily_summaries': 0,
        'tables_updated': 0,
        'days_generated': 0,
    }

    # ── 1. Ensure tables exist ──
    tables = _ensure_tables(outlet)
    results['tables'] = len(tables)

    # ── 2. Ensure service flows exist ──
    flow_count = _ensure_flows(outlet, tables)
    results['flows'] = flow_count

    # ── 3. Get staff (waiters/managers who can take orders) ──
    waiters = list(
        UserProfile.objects.filter(
            outlet=outlet, role__in=['WAITER', 'MANAGER']
        )
    )
    if not waiters:
        waiters = list(UserProfile.objects.filter(outlet=outlet)[:1])
    results['staff_available'] = len(waiters)

    # ── 4. Ensure inventory items exist (once) ──
    inv_count = _ensure_inventory(outlet, target_date)
    results['inventory_items'] = inv_count

    # ── 5. Generate data for each day in the range ──
    start_date = target_date - timedelta(days=days - 1)
    all_orders = []

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        day_of_week = current_date.weekday()
        is_weekend = day_of_week in (5, 6)

        # Vary order count day to day (±30%), more on weekends
        multiplier = random.uniform(1.1, 1.4) if is_weekend else random.uniform(0.7, 1.1)
        day_orders_count = max(5, int(order_count * multiplier))

        # ── Create orders for this day ──
        day_orders = _create_orders(
            outlet, tables, waiters, current_date, now, day_orders_count
        )
        all_orders.extend(day_orders)
        results['orders'] += len(day_orders)

        # ── Create payments for this day's orders ──
        results['payments'] += _create_payments(day_orders)

        # ── Create staff schedules for this day ──
        results['schedules'] += _create_schedules(outlet, current_date)

        # ── Create hourly sales data for this day ──
        results['sales_data_hours'] += _create_sales_data(
            outlet, current_date, day_orders
        )

        # ── Create daily summary from this day's orders ──
        if _create_daily_summary(outlet, day_orders, current_date):
            results['daily_summaries'] += 1

        # ── Simulate inventory consumption for this day ──
        _consume_inventory(outlet, day_orders, current_date)

        results['days_generated'] += 1

    # ── 6. Update table statuses to reflect current state ──
    today_orders = [o for o in all_orders
                    if o.placed_at.date() == target_date]
    _update_table_statuses(tables, today_orders or all_orders[-20:])
    results['tables_updated'] = len(tables)

    return results


def _ensure_tables(outlet):
    """Ensure the outlet has tables. Create if none exist."""
    tables = list(
        ServiceNode.objects.filter(outlet=outlet, node_type='TABLE', is_active=True)
    )
    if tables:
        return tables

    # Fetch the last table number across ALL outlets to avoid name clashes
    # within the same outlet (unique_together: outlet, name)
    existing_names = set(
        ServiceNode.objects.filter(outlet=outlet)
        .values_list('name', flat=True)
    )

    new_tables = []
    table_num = 1
    for i in range(10):
        name = f'Table-{table_num}'
        while name in existing_names:
            table_num += 1
            name = f'Table-{table_num}'
        cap = random.choice([2, 2, 4, 4, 4, 6, 6, 8])
        node = ServiceNode.objects.create(
            outlet=outlet, name=name, node_type='TABLE',
            pos_x=float((i % 5) * 2.5), pos_y=0.0,
            pos_z=float((i // 5) * 3.0),
            capacity=cap, current_status='BLUE', is_active=True,
        )
        new_tables.append(node)
        existing_names.add(name)
        table_num += 1

    # Also create kitchen/wash if they don't exist
    for name, ntype, x, z in [
        ('Kitchen-Main', 'KITCHEN', 12.0, 2.0),
        ('Wash-Area', 'WASH', 12.0, 6.0),
        ('Entrance', 'ENTRY', 0.0, 4.0),
    ]:
        if not ServiceNode.objects.filter(outlet=outlet, name=name).exists():
            ServiceNode.objects.create(
                outlet=outlet, name=name, node_type=ntype,
                pos_x=x, pos_y=0.0, pos_z=z,
                capacity=0, current_status='GREEN', is_active=True,
            )

    return new_tables


def _ensure_flows(outlet, tables):
    """Create service flows between tables and kitchen/wash nodes."""
    kitchen = ServiceNode.objects.filter(
        outlet=outlet, node_type='KITCHEN'
    ).first()
    wash = ServiceNode.objects.filter(
        outlet=outlet, node_type='WASH'
    ).first()

    count = 0
    for table in tables:
        if kitchen:
            _, c = ServiceFlow.objects.get_or_create(
                source_node=table, target_node=kitchen,
                flow_type='ORDER_PATH', defaults={'is_active': True})
            count += c
            _, c = ServiceFlow.objects.get_or_create(
                source_node=kitchen, target_node=table,
                flow_type='FOOD_DELIVERY', defaults={'is_active': True})
            count += c
        if wash:
            _, c = ServiceFlow.objects.get_or_create(
                source_node=table, target_node=wash,
                flow_type='DISH_RETURN', defaults={'is_active': True})
            count += c
    return count


def _create_orders(outlet, tables, waiters, target_date, now, count):
    """Create orders spread across working hours."""
    opening = outlet.opening_time
    closing = outlet.closing_time

    # Convert to hour range
    open_h = opening.hour
    close_h = closing.hour if closing.hour > opening.hour else 24

    # Build hour weights (peak at lunch 12-14 and dinner 19-22)
    hours = list(range(open_h, close_h))
    weights = []
    for h in hours:
        if 12 <= h <= 14:
            weights.append(10)
        elif 19 <= h <= 22:
            weights.append(12)
        elif 11 <= h <= 15:
            weights.append(6)
        elif 18 <= h <= 23:
            weights.append(8)
        else:
            weights.append(3)

    # Status distribution
    distribution = {
        'COMPLETED': int(count * 0.40),
        'SERVED': int(count * 0.15),
        'PREPARING': int(count * 0.10),
        'READY': int(count * 0.08),
        'PLACED': int(count * 0.12),
        'CANCELLED': int(count * 0.10),
    }
    remainder = count - sum(distribution.values())
    distribution['COMPLETED'] += remainder

    status_list = []
    for s, n in distribution.items():
        status_list.extend([s] * n)
    random.shuffle(status_list)

    orders = []
    for target_status in status_list:
        table = random.choice(tables)
        waiter = random.choice(waiters) if waiters else None

        # Build items (1-6 dishes)
        num_items = random.choices([1, 2, 3, 4, 5, 6], weights=[5, 20, 30, 25, 12, 8])[0]
        items = random.sample(FLAT_MENU, min(num_items, len(FLAT_MENU)))
        subtotal = sum(it['price'] for it in items)
        tax = round(subtotal * 0.05, 2)
        total = subtotal + tax

        party = min(
            random.choices([1, 2, 3, 4, 5, 6, 8],
                           weights=[5, 25, 20, 20, 10, 10, 10])[0],
            table.capacity
        )

        # Pick a random hour within working hours
        hour = random.choices(hours, weights=weights)[0]
        minute = random.randint(0, 59)
        placed_dt = timezone.make_aware(
            datetime.combine(target_date, time(hour % 24, minute)),
            timezone.get_current_timezone(),
        )
        if placed_dt > now:
            placed_dt = now - timedelta(minutes=random.randint(5, 120))

        order = OrderTicket(
            table=table, waiter=waiter,
            customer_name=random.choice(CUSTOMER_NAMES),
            party_size=party, items=items,
            special_requests=random.choice(SPECIAL_REQUESTS),
            status='PLACED',
            subtotal=Decimal(str(subtotal)),
            tax=Decimal(str(tax)),
            total=Decimal(str(total)),
        )
        order.save()

        # Override placed_at (auto_now_add)
        OrderTicket.objects.filter(pk=order.pk).update(placed_at=placed_dt)
        order.refresh_from_db()

        # Progress through status transitions
        transition_map = {
            'PLACED': [],
            'PREPARING': ['PREPARING'],
            'READY': ['PREPARING', 'READY'],
            'SERVED': ['PREPARING', 'READY', 'SERVED'],
            'COMPLETED': ['PREPARING', 'READY', 'SERVED', 'COMPLETED'],
            'CANCELLED': ['CANCELLED'],
        }

        elapsed = 0
        for step in transition_map[target_status]:
            if step == 'CANCELLED':
                elapsed += random.randint(3, 35)
                order.status = 'CANCELLED'
                order.special_requests = (
                    (order.special_requests + ' | ' if order.special_requests else '')
                    + 'CANCELLED: ' + random.choice(CANCELLATION_REASONS)
                )
            elif step == 'PREPARING':
                elapsed += random.randint(2, 8)
                order.status = 'PREPARING'
            elif step == 'READY':
                elapsed += random.randint(8, 20) if random.random() > 0.15 else random.randint(25, 45)
                order.status = 'READY'
            elif step == 'SERVED':
                elapsed += random.randint(2, 10)
                order.status = 'SERVED'
                order.served_at = placed_dt + timedelta(minutes=elapsed)
            elif step == 'COMPLETED':
                elapsed += random.randint(15, 55)
                order.status = 'COMPLETED'
                order.completed_at = placed_dt + timedelta(minutes=elapsed)
            order.save()

        orders.append(order)

    return orders


def _create_payments(orders):
    """Create payments for served/completed orders."""
    count = 0
    for order in orders:
        if order.status == 'CANCELLED':
            if random.random() < 0.2:
                PaymentLog.objects.create(
                    order=order, amount=order.total,
                    method=random.choice(['CARD', 'UPI']),
                    status=random.choice(['FAILED', 'REFUNDED']),
                    transaction_id=f'TXN-F-{uuid.uuid4().hex[:8].upper()}',
                    tip_amount=Decimal('0.00'),
                )
                count += 1
            continue

        if order.status in ('COMPLETED', 'SERVED'):
            method = random.choices(
                ['CASH', 'CARD', 'UPI', 'WALLET'],
                weights=[20, 30, 35, 15],
            )[0]
            tip = Decimal(str(random.choices(
                [0, 20, 50, 100, 150, 200],
                weights=[40, 20, 15, 12, 8, 5],
            )[0]))

            PaymentLog.objects.create(
                order=order, amount=order.total,
                method=method, status='SUCCESS',
                transaction_id=f'TXN-{uuid.uuid4().hex[:8].upper()}',
                tip_amount=tip,
            )
            count += 1

    return count


def _ensure_inventory(outlet, target_date):
    """Create inventory items for the outlet if they don't exist."""
    count = 0
    for name, category, unit, cost in INVENTORY_ITEMS:
        _, created = InventoryItem.objects.get_or_create(
            outlet=outlet, name=name,
            defaults={
                'category': category,
                'unit': unit,
                'current_quantity': random.uniform(40, 100),
                'reorder_threshold': random.uniform(5, 15),
                'par_level': random.uniform(50, 100),
                'unit_cost': Decimal(str(cost)),
                'expiry_date': target_date + timedelta(days=random.randint(5, 30)),
                'last_restocked': timezone.now() - timedelta(days=random.randint(0, 3)),
            },
        )
        if created:
            count += 1
    return count


def _consume_inventory(outlet, orders, current_date):
    """
    Simulate inventory consumption based on orders placed on this day.
    Reduces quantities realistically so inventory shows depletion trends.
    """
    completed_orders = [o for o in orders if o.status in ('COMPLETED', 'SERVED')]
    order_count = len(completed_orders)
    if order_count == 0:
        return

    # Map menu items to inventory ingredients they consume
    ingredient_usage = {
        'Paneer Tikka': [('Paneer', 0.15), ('Cooking Oil', 0.02)],
        'Chicken 65': [('Chicken', 0.15), ('Cooking Oil', 0.05)],
        'Veg Spring Rolls': [('Flour (Maida)', 0.05), ('Cooking Oil', 0.03)],
        'Mutton Seekh Kebab': [('Onions', 0.05), ('Cooking Oil', 0.03)],
        'Crispy Corn': [('Cooking Oil', 0.04)],
        'Fish Amritsari': [('Flour (Maida)', 0.05), ('Cooking Oil', 0.05)],
        'Butter Chicken': [('Chicken', 0.2), ('Tomatoes', 0.1), ('Cream', 0.05)],
        'Dal Makhani': [('Cream', 0.03), ('Cooking Oil', 0.02)],
        'Palak Paneer': [('Paneer', 0.15), ('Cream', 0.03)],
        'Mutton Rogan Josh': [('Tomatoes', 0.1), ('Onions', 0.1), ('Cooking Oil', 0.03)],
        'Hyderabadi Biryani': [('Basmati Rice', 0.2), ('Onions', 0.1), ('Cooking Oil', 0.03)],
        'Chole Bhature': [('Flour (Maida)', 0.1), ('Cooking Oil', 0.05), ('Onions', 0.05)],
        'Prawn Masala': [('Prawns (frozen)', 0.15), ('Tomatoes', 0.1)],
        'Veg Kolhapuri': [('Onions', 0.1), ('Tomatoes', 0.1), ('Cooking Oil', 0.02)],
        'Butter Naan': [('Flour (Maida)', 0.08), ('Milk', 0.02)],
        'Garlic Naan': [('Flour (Maida)', 0.08), ('Milk', 0.02)],
        'Tandoori Roti': [('Flour (Maida)', 0.06)],
        'Laccha Paratha': [('Flour (Maida)', 0.08), ('Cooking Oil', 0.02)],
        'Masala Chai': [('Milk', 0.15), ('Sugar', 0.01)],
        'Cold Coffee': [('Coffee Beans', 0.02), ('Milk', 0.15), ('Sugar', 0.01)],
        'Fresh Lime Soda': [('Soda Water', 0.2), ('Sugar', 0.01)],
        'Mango Lassi': [('Mango Pulp', 0.1), ('Curd / Yogurt', 0.1), ('Sugar', 0.01)],
        'Espresso': [('Coffee Beans', 0.02), ('Sugar', 0.01)],
        'Gulab Jamun': [('Milk', 0.05), ('Sugar', 0.03)],
        'Rasmalai': [('Milk', 0.1), ('Sugar', 0.03)],
        'Kulfi': [('Milk', 0.1), ('Sugar', 0.02)],
        'Brownie with Ice Cream': [('Flour (Maida)', 0.05), ('Sugar', 0.03), ('Milk', 0.05)],
    }

    # Calculate total consumption per ingredient
    consumption = {}
    for order in completed_orders:
        for item in (order.items or []):
            item_name = item.get('name', '')
            for ing_name, qty in ingredient_usage.get(item_name, []):
                consumption[ing_name] = consumption.get(ing_name, 0) + qty

    # Also consume paper napkins proportional to order count
    consumption['Paper Napkins'] = consumption.get('Paper Napkins', 0) + order_count * 0.1
    consumption['Cleaning Solution'] = consumption.get('Cleaning Solution', 0) + order_count * 0.02

    # Apply consumption to inventory
    for item in InventoryItem.objects.filter(outlet=outlet):
        used = consumption.get(item.name, 0)
        if used > 0:
            item.current_quantity = max(0, item.current_quantity - used)
            item.save(update_fields=['current_quantity'])


def _create_schedules(outlet, target_date):
    """Create staff schedules for the target date."""
    staff = list(UserProfile.objects.filter(outlet=outlet))
    if not staff:
        return 0

    shift_times = {
        'MORNING': (time(6, 0), time(14, 0)),
        'AFTERNOON': (time(14, 0), time(22, 0)),
        'NIGHT': (time(22, 0), time(6, 0)),
    }

    count = 0
    for profile in staff:
        # Each staff member gets 1-2 shifts on the target date
        shift = random.choices(
            ['MORNING', 'AFTERNOON', 'NIGHT'],
            weights=[30, 50, 20],
        )[0]
        start, end = shift_times[shift]

        _, created = StaffSchedule.objects.get_or_create(
            staff=profile, date=target_date, shift=shift,
            defaults={
                'start_time': start,
                'end_time': end,
                'is_confirmed': random.random() < 0.85,
                'is_ai_suggested': random.random() < 0.3,
            },
        )
        if created:
            count += 1

    return count


def _create_sales_data(outlet, target_date, day_orders=None):
    """
    Create hourly sales data for the target date.
    When day_orders is provided, compute metrics from actual order data
    for realistic ML training features.
    """
    opening = outlet.opening_time
    closing = outlet.closing_time

    open_h = opening.hour
    close_h = closing.hour if closing.hour > opening.hour else 24
    day_of_week = target_date.weekday()
    is_weekend = day_of_week in (5, 6)

    # Group orders by hour if available
    orders_by_hour = {}
    if day_orders:
        for o in day_orders:
            h = o.placed_at.hour
            orders_by_hour.setdefault(h, []).append(o)

    count = 0
    for hour in range(open_h, close_h):
        hour_orders = orders_by_hour.get(hour, [])
        non_cancelled = [o for o in hour_orders if o.status != 'CANCELLED']

        if non_cancelled:
            # Compute from actual orders
            total_orders = len(non_cancelled)
            revenue = sum(float(o.total) for o in non_cancelled)
            avg_ticket = revenue / total_orders
            avg_wait = sum(
                (o.wait_time_minutes if o.served_at else random.randint(8, 25))
                for o in non_cancelled
            ) / total_orders

            # Category breakdown from ordered items
            cat_rev = {}
            item_counter = {}
            for o in non_cancelled:
                for it in (o.items or []):
                    name = it.get('name', '')
                    price = it.get('price', 0)
                    cat = _item_category(name)
                    cat_rev[cat] = cat_rev.get(cat, 0) + price
                    item_counter[name] = item_counter.get(name, 0) + 1
            top_items = sorted(item_counter, key=item_counter.get, reverse=True)[:5]
        else:
            # Fallback for hours with no orders - use baseline traffic model
            base_orders = {
                6: 2, 7: 3, 8: 5, 9: 4, 10: 4,
                11: 6, 12: 14, 13: 16, 14: 10, 15: 5, 16: 4, 17: 5,
                18: 8, 19: 18, 20: 22, 21: 20, 22: 12, 23: 4,
            }.get(hour, 4)
            if is_weekend:
                base_orders = int(base_orders * 1.3)
            total_orders = max(1, base_orders + random.randint(-3, 3))
            revenue = float(total_orders * random.randint(350, 650))
            avg_ticket = revenue / total_orders
            avg_wait = random.uniform(8, 30)
            cat_rev = {
                'Starters': revenue * 0.15,
                'Mains': revenue * 0.45,
                'Breads': revenue * 0.10,
                'Beverages': revenue * 0.15,
                'Desserts': revenue * 0.15,
            }
            top_items = random.sample(
                [it['name'] for it in FLAT_MENU], min(5, len(FLAT_MENU))
            )

        _, created = SalesData.objects.get_or_create(
            outlet=outlet, date=target_date, hour=hour,
            defaults={
                'total_orders': total_orders,
                'total_revenue': Decimal(str(round(revenue, 2))),
                'avg_ticket_size': Decimal(str(round(avg_ticket, 2))),
                'avg_wait_time_minutes': round(avg_wait, 1),
                'category_sales': {k: round(v, 2) for k, v in cat_rev.items()},
                'top_items': top_items,
                'day_of_week': day_of_week,
                'is_holiday': is_weekend,
                'weather_condition': random.choice(
                    ['SUNNY', 'CLOUDY', 'RAINY', 'CLEAR']
                ),
            },
        )
        if created:
            count += 1

    return count


def _item_category(item_name):
    """Map a menu item name to its category."""
    for cat_name, items_list in MENU.items():
        for it in items_list:
            if it['name'] == item_name:
                return cat_name.capitalize()
    return 'Mains'


def _create_daily_summary(outlet, orders, target_date):
    """Create a daily summary from generated orders."""
    if DailySummary.objects.filter(outlet=outlet, date=target_date).exists():
        return False

    day_orders = [o for o in orders if o.status != 'CANCELLED']
    total_rev = sum(float(o.total) for o in day_orders)
    total_ord = len(day_orders)
    cancelled = len([o for o in orders if o.status == 'CANCELLED'])
    delayed = len([o for o in orders if o.is_long_wait])
    total_guests = sum(o.party_size for o in day_orders)
    staff_count = UserProfile.objects.filter(outlet=outlet, is_on_shift=True).count() or 1

    avg_ticket = total_rev / total_ord if total_ord else 0
    rev_per_staff = total_rev / staff_count

    # Tips from payments
    total_tips = sum(
        float(p.tip_amount)
        for o in day_orders
        for p in o.payments.filter(status='SUCCESS')
    )

    # Top items
    item_counter = {}
    for o in day_orders:
        for it in (o.items or []):
            item_counter[it['name']] = item_counter.get(it['name'], 0) + 1
    top_items = sorted(item_counter, key=item_counter.get, reverse=True)[:10]

    # Category revenue
    cat_lookup = {}
    for cat_name, items_list in MENU.items():
        for it in items_list:
            cat_lookup[it['name']] = cat_name.capitalize()
    cat_revenue = {}
    for o in day_orders:
        for it in (o.items or []):
            cat = cat_lookup.get(it['name'], 'Mains')
            cat_revenue[cat] = cat_revenue.get(cat, 0) + it.get('price', 0)

    # Peak hour
    hour_rev = {}
    for o in day_orders:
        h = o.placed_at.hour
        hour_rev[h] = hour_rev.get(h, 0) + float(o.total)
    peak_hour = max(hour_rev, key=hour_rev.get) if hour_rev else 12

    DailySummary.objects.create(
        outlet=outlet, date=target_date,
        total_revenue=Decimal(str(round(total_rev, 2))),
        total_orders=total_ord,
        avg_ticket_size=Decimal(str(round(avg_ticket, 2))),
        total_tips=Decimal(str(round(total_tips, 2))),
        total_guests=total_guests,
        avg_table_turnover_time=random.uniform(35, 65),
        avg_wait_time=random.uniform(10, 22),
        peak_hour=peak_hour,
        peak_revenue=Decimal(str(round(total_rev * 0.18, 2))),
        delayed_orders=delayed,
        cancelled_orders=cancelled,
        sales_by_category=cat_revenue,
        top_selling_items=top_items,
        staff_count=staff_count,
        revenue_per_staff=Decimal(str(round(rev_per_staff, 2))),
    )
    return True


def _update_table_statuses(tables, orders):
    """Update table statuses based on active orders."""
    statuses = ['BLUE', 'RED', 'GREEN', 'YELLOW']
    for table in tables:
        active_orders = [
            o for o in orders
            if o.table_id == table.id and o.status not in ('COMPLETED', 'CANCELLED')
        ]
        if not active_orders:
            table.current_status = 'BLUE'
        else:
            latest = max(active_orders, key=lambda o: o.placed_at)
            status_map = {
                'PLACED': 'RED',
                'PREPARING': 'RED',
                'READY': 'YELLOW',
                'SERVED': 'GREEN',
            }
            table.current_status = status_map.get(latest.status, 'BLUE')
        table.save()
