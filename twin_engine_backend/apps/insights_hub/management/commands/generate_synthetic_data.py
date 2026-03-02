"""
Synthetic Restaurant Data Generator - Covers EVERY possible restaurant scenario.

Creates highly realistic data for testing the GPT-4o report pipeline:
  Data -> GPT-4o -> PDF -> Cloudinary -> Link

Scenarios covered:
  - Normal operations (smooth orders, on-time service)
  - Delayed orders (wait > 15 min, kitchen bottleneck)
  - Cancelled orders (customer walked out, wrong dish, allergy)
  - Dishes never served (stuck at READY, kitchen forgot)
  - Large party bookings (8-12 guests, split bills)
  - VIP / celebration orders (birthday, anniversary, special requests)
  - Payment failures & refunds (card declined, refund processed)
  - Split payments (half card, half cash)
  - Excellent, average, and poor tipping
  - Peak hour rush (7-9 PM overload)
  - Low-stock inventory alerts (paneer, tomatoes running out)
  - Near-expiry ingredients (dairy about to expire)
  - Staff short-staffing (night shift gap)
  - All table statuses (BLUE available, GREEN served, YELLOW waiting, RED delayed, GREY inactive)
  - All payment methods (CASH, CARD, UPI, WALLET, SPLIT)
  - All order statuses (PLACED, PREPARING, READY, SERVED, COMPLETED, CANCELLED)
  - Daily sales data with hourly breakdown
  - DailySummary with realistic metrics

Usage:
    python manage.py generate_synthetic_data
    python manage.py generate_synthetic_data --clear     # Wipe previous synthetic data first
    python manage.py generate_synthetic_data --orders=60  # Custom order count
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import connection
from datetime import datetime, timedelta, time, date
from decimal import Decimal
import random
import uuid

from apps.hospitality_group.models import Brand, Outlet, UserProfile
from apps.layout_twin.models import ServiceNode, ServiceFlow
from apps.order_engine.models import OrderTicket, PaymentLog
from apps.predictive_core.models import SalesData, InventoryItem, StaffSchedule
from apps.insights_hub.models import DailySummary, PDFReport

BRAND_ID = 'SYNTH001'


# ===========================================================
# Menu - realistic Indian restaurant menu with categories
# ===========================================================
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
    None, None, None,  # Some walk-ins without names
]

SPECIAL_REQUESTS = [
    'Less spicy please',
    'Extra napkins',
    'Birthday celebration - need a candle on dessert',
    'Anniversary dinner - please ensure a quiet corner',
    'Nut allergy - strictly no peanuts',
    'Gluten-free options only',
    'Jain food - no onion, no garlic',
    'Extra raita on the side',
    'Kids portions for 2 items',
    'Wheelchair accessible seating',
    'Quick service please - in a hurry',
    'Vegan - no dairy or ghee',
    'No sugar in beverages',
    None, None, None, None, None, None, None,  # Most orders have no special request
]

CANCELLATION_REASONS = [
    'Customer walked out - long wait',
    'Wrong dish delivered, customer left',
    'Allergy concern - ingredient mismatch',
    'Customer changed mind',
    'Kitchen ran out of ingredients',
    'Duplicate order - merged with another table',
    'Party cancelled their reservation',
]


class Command(BaseCommand):
    help = 'Generate comprehensive synthetic restaurant data for report pipeline testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Delete all synthetic data before regenerating',
        )
        parser.add_argument(
            '--orders', type=int, default=50,
            help='Total number of orders to create (default: 50)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('  TwinEngine Synthetic Data Generator'))
        self.stdout.write(self.style.SUCCESS('  Covers EVERY restaurant scenario for GPT-4o report testing'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        if options['clear']:
            self._clear_data()

        brand = self._create_brand()
        outlet = self._create_outlet(brand)
        staff = self._create_staff(outlet)
        tables, special_nodes = self._create_floor_layout(outlet)
        self._create_service_flows(tables, special_nodes)
        orders = self._create_orders(tables, staff, count=options['orders'])
        self._create_payments(orders)
        self._create_inventory(outlet)
        self._create_staff_schedules(staff)
        self._create_sales_data(outlet)
        self._create_daily_summary(outlet, orders)

        self._print_summary(outlet)

    # ─────────────────────────────────────────────────────────
    # CLEANUP
    # ─────────────────────────────────────────────────────────
    def _clear_data(self):
        self.stdout.write(self.style.WARNING('\n[CLEAR] Clearing previous synthetic data...'))

        # First, delete by relationship chain (safe order)
        q = {'outlet__brand__corporate_id': BRAND_ID}
        tq = {'table__outlet__brand__corporate_id': BRAND_ID}

        try:
            PDFReport.objects.filter(**q).delete()
        except Exception:
            pass
        try:
            DailySummary.objects.filter(**q).delete()
        except Exception:
            pass
        try:
            StaffSchedule.objects.filter(staff__outlet__brand__corporate_id=BRAND_ID).delete()
        except Exception:
            pass
        try:
            InventoryItem.objects.filter(**q).delete()
        except Exception:
            pass
        try:
            SalesData.objects.filter(**q).delete()
        except Exception:
            pass
        try:
            PaymentLog.objects.filter(order__table__outlet__brand__corporate_id=BRAND_ID).delete()
        except Exception:
            pass
        try:
            OrderTicket.objects.filter(**tq).delete()
        except Exception:
            pass
        try:
            ServiceFlow.objects.filter(source_node__outlet__brand__corporate_id=BRAND_ID).delete()
        except Exception:
            pass
        try:
            ServiceNode.objects.filter(**q).delete()
        except Exception:
            pass
        try:
            UserProfile.objects.filter(outlet__brand__corporate_id=BRAND_ID).delete()
        except Exception:
            pass

        # Also clean up orphaned profiles / users by username prefix
        try:
            UserProfile.objects.filter(user__username__startswith='synth_').delete()
        except Exception:
            pass
        User.objects.filter(username__startswith='synth_').delete()
        Outlet.objects.filter(brand__corporate_id=BRAND_ID).delete()
        Brand.objects.filter(corporate_id=BRAND_ID).delete()

        self.stdout.write(self.style.SUCCESS('   [OK] All synthetic data cleared\n'))

    # ─────────────────────────────────────────────────────────
    # 1. BRAND & OUTLET
    # ─────────────────────────────────────────────────────────
    def _create_brand(self):
        self.stdout.write(self.style.HTTP_INFO('\n[1] Brand & Outlet'))
        brand, created = Brand.objects.get_or_create(
            corporate_id=BRAND_ID,
            defaults={
                'name': 'Spice Republic Hospitality Group',
                'contact_email': 'ops@spicerepublic.in',
                'subscription_tier': 'ENTERPRISE',
            },
        )
        self.stdout.write(f'   {"+ Created" if created else "= Exists"}: {brand.name}')
        return brand

    def _create_outlet(self, brand):
        outlet, created = Outlet.objects.get_or_create(
            brand=brand,
            name='Spice Republic Koramangala',
            defaults={
                'address': '147 80 Feet Road, Koramangala 4th Block, Bangalore 560034',
                'city': 'Bangalore',
                'seating_capacity': 72,
                'opening_time': time(11, 0),
                'closing_time': time(23, 30),
                'is_active': True,
            },
        )
        self.stdout.write(f'   {"+ Created" if created else "= Exists"}: {outlet.name}  ({outlet.seating_capacity} seats)')
        return outlet

    # ─────────────────────────────────────────────────────────
    # 2. STAFF (all roles, realistic shifts)
    # ─────────────────────────────────────────────────────────
    def _create_staff(self, outlet):
        self.stdout.write(self.style.HTTP_INFO('\n[2] Staff Profiles'))
        staff_data = [
            # Managers
            ('synth_mgr_1', 'Arjun', 'Menon', 'MANAGER', '+91-9900000001', True),
            # Waiters — 4 to spread across shifts
            ('synth_waiter_1', 'Amit', 'Sharma', 'WAITER', '+91-9900000002', True),
            ('synth_waiter_2', 'Priya', 'Patil', 'WAITER', '+91-9900000003', True),
            ('synth_waiter_3', 'Ravi', 'Kumar', 'WAITER', '+91-9900000004', True),
            ('synth_waiter_4', 'Neha', 'Deshmukh', 'WAITER', '+91-9900000005', False),  # off shift
            # Chefs — 2
            ('synth_chef_1', 'Vikram', 'Singh', 'CHEF', '+91-9900000006', True),
            ('synth_chef_2', 'Lakshmi', 'Nair', 'CHEF', '+91-9900000007', True),
            # Host — 1
            ('synth_host_1', 'Sneha', 'Reddy', 'HOST', '+91-9900000008', True),
            # Cashier — 1
            ('synth_cashier_1', 'Deepak', 'Joshi', 'CASHIER', '+91-9900000009', True),
        ]

        profiles = {}
        for username, first, last, role, phone, on_shift in staff_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@synth.local', 'first_name': first, 'last_name': last},
            )
            user.set_password('synth123')
            user.save()

            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={'outlet': outlet, 'role': role, 'phone': phone, 'is_on_shift': on_shift},
            )
            profiles.setdefault(role, []).append(profile)
            shift_status = '[ON]' if on_shift else '[OFF]'
            self.stdout.write(f'   {shift_status} {first} {last} - {role}')

        return profiles

    # ─────────────────────────────────────────────────────────
    # 3. FLOOR LAYOUT (tables + special nodes)
    # ─────────────────────────────────────────────────────────
    def _create_floor_layout(self, outlet):
        self.stdout.write(self.style.HTTP_INFO('\n[3] Floor Layout (Tables & Nodes)'))

        # Table configs: (name, capacity, status, x, z)
        # Mix of statuses: BLUE (free), GREEN (served), YELLOW (waiting), RED (delayed), GREY (reserved/inactive)
        table_configs = [
            # Dining section — mix of statuses
            ('Table 1',  2, 'BLUE',   1.0, 1.0),   # free
            ('Table 2',  2, 'GREEN',  3.0, 1.0),   # food served
            ('Table 3',  4, 'YELLOW', 5.0, 1.0),   # waiting for food
            ('Table 4',  4, 'RED',    7.0, 1.0),    # delayed > 15 min
            ('Table 5',  4, 'GREEN',  1.0, 3.5),   # food served
            ('Table 6',  6, 'YELLOW', 3.0, 3.5),   # waiting for food
            ('Table 7',  6, 'BLUE',   5.0, 3.5),   # free
            ('Table 8',  2, 'GREEN',  7.0, 3.5),   # food served
            # Family / large-party section
            ('Table 9',  8, 'YELLOW', 1.0, 6.0),   # large party waiting
            ('Table 10', 8, 'GREEN',  4.0, 6.0),   # large party served
            ('Table 11', 10, 'BLUE',  7.0, 6.0),   # VIP booth free
            # Outdoor / quick section
            ('Table 12', 2, 'GREY',   1.0, 8.5),   # maintenance / reserved
            ('Table 13', 2, 'BLUE',   3.0, 8.5),   # free
            ('Table 14', 4, 'RED',    5.0, 8.5),    # delayed
            ('Table 15', 4, 'GREEN',  7.0, 8.5),   # food served
        ]

        tables = []
        for name, cap, status, x, z in table_configs:
            node, created = ServiceNode.objects.get_or_create(
                outlet=outlet, name=name,
                defaults={
                    'node_type': 'TABLE', 'capacity': cap,
                    'pos_x': x, 'pos_y': 0.0, 'pos_z': z,
                    'current_status': status, 'is_active': status != 'GREY',
                },
            )
            tables.append(node)
            self.stdout.write(f'   [{status:6s}] {name}  cap={cap}')

        # Special nodes
        special = {}
        for name, ntype, x, z in [
            ('Main Kitchen', 'KITCHEN', 9.0, 3.0),
            ('Tandoor Station', 'KITCHEN', 9.0, 5.0),
            ('Bar Counter', 'BAR', 0.0, 0.0),
            ('Wash Area', 'WASH', 9.0, 7.0),
            ('Main Entrance', 'ENTRY', 0.0, 5.0),
        ]:
            node, _ = ServiceNode.objects.get_or_create(
                outlet=outlet, name=name,
                defaults={'node_type': ntype, 'capacity': 0, 'pos_x': x, 'pos_y': 0.0, 'pos_z': z,
                          'current_status': 'GREEN', 'is_active': True},
            )
            special[ntype] = node
            self.stdout.write(f'   [NODE] {name} ({ntype})')

        return tables, special

    def _create_service_flows(self, tables, special):
        self.stdout.write(self.style.HTTP_INFO('\n[4] Service Flows'))
        kitchen = special.get('KITCHEN')
        bar = special.get('BAR')
        wash = special.get('WASH')
        entry = special.get('ENTRY')
        count = 0

        for table in tables:
            # Order path: Table → Kitchen
            if kitchen:
                _, c = ServiceFlow.objects.get_or_create(
                    source_node=table, target_node=kitchen,
                    flow_type='ORDER_PATH', defaults={'is_active': True})
                count += c
            # Food delivery: Kitchen → Table
            if kitchen:
                _, c = ServiceFlow.objects.get_or_create(
                    source_node=kitchen, target_node=table,
                    flow_type='FOOD_DELIVERY', defaults={'is_active': True})
                count += c
            # Dish return: Table → Wash
            if wash:
                _, c = ServiceFlow.objects.get_or_create(
                    source_node=table, target_node=wash,
                    flow_type='DISH_RETURN', defaults={'is_active': True})
                count += c
            # Customer flow: Entry → Table
            if entry:
                _, c = ServiceFlow.objects.get_or_create(
                    source_node=entry, target_node=table,
                    flow_type='CUSTOMER_FLOW', defaults={'is_active': True})
                count += c

        self.stdout.write(self.style.SUCCESS(f'   [OK] {count} flows created'))

    # ─────────────────────────────────────────────────────────
    # 4. ORDERS — the heart of the simulation
    # ─────────────────────────────────────────────────────────
    def _create_orders(self, tables, staff, count):
        self.stdout.write(self.style.HTTP_INFO(f'\n[5] Orders ({count} total - covering every scenario)'))

        active_tables = [t for t in tables if t.node_type == 'TABLE' and t.is_active]
        waiters = staff.get('WAITER', []) + staff.get('MANAGER', [])
        today = timezone.now().date()
        now = timezone.now()

        # ── Status distribution — intentionally covers all cases ──
        distribution = {
            'COMPLETED': int(count * 0.36),   # 36 % — successful, fully paid
            'SERVED':    int(count * 0.16),   # 16 % — food on table, eating
            'PREPARING': int(count * 0.10),   # 10 % — in kitchen right now
            'READY':     int(count * 0.08),   # 8  % — waiting pickup (some "never served")
            'PLACED':    int(count * 0.10),   # 10 % — just placed
            'CANCELLED': int(count * 0.12),   # 12 % — various cancellation reasons
        }
        # Fill remainder into COMPLETED
        remainder = count - sum(distribution.values())
        distribution['COMPLETED'] += remainder

        # Build flat list, shuffle for realism
        status_list = []
        for s, n in distribution.items():
            status_list.extend([s] * n)
        random.shuffle(status_list)

        orders = []
        status_counts = {}

        for i, target_status in enumerate(status_list):
            table = random.choice(active_tables)
            waiter = random.choice(waiters)

            # ── Build order items (1-7 dishes) ──
            num_items = random.choices([1, 2, 3, 4, 5, 6, 7], weights=[5, 20, 30, 25, 12, 5, 3])[0]
            items = random.sample(FLAT_MENU, min(num_items, len(FLAT_MENU)))
            subtotal = sum(it['price'] for it in items)
            tax = round(subtotal * 0.05, 2)
            total = subtotal + tax

            # ── Determine party size ──
            party = min(random.choices([1, 2, 3, 4, 5, 6, 8, 10, 12],
                                       weights=[5, 25, 20, 20, 10, 8, 5, 4, 3])[0],
                        table.capacity)

            # ── Time spread across the day (11 AM – 11 PM) ──
            hour = random.choices(
                range(11, 24),
                # Peak at lunch (12-14) and dinner (19-22)
                weights=[3, 8, 8, 5, 3, 2, 2, 3, 10, 12, 12, 8, 4],
            )[0]
            minute = random.randint(0, 59)
            placed_dt = timezone.make_aware(
                datetime.combine(today, time(hour, minute)),
                timezone.get_current_timezone(),
            )
            # Ensure placed_at is not in the future
            if placed_dt > now:
                placed_dt = now - timedelta(minutes=random.randint(5, 60))

            # ── Special request ──
            special_req = random.choice(SPECIAL_REQUESTS)

            # ── Create the order (initially PLACED) ──
            # We bypass signals by using raw SQL for placed_at override, then progress status
            order = OrderTicket(
                table=table,
                waiter=waiter,
                customer_name=random.choice(CUSTOMER_NAMES),
                party_size=party,
                items=items,
                special_requests=special_req,
                status='PLACED',
                subtotal=Decimal(str(subtotal)),
                tax=Decimal(str(tax)),
                total=Decimal(str(total)),
            )
            order.save()

            # Override placed_at (auto_now_add field) via raw UPDATE
            OrderTicket.objects.filter(pk=order.pk).update(placed_at=placed_dt)
            order.refresh_from_db()

            # ── Progress through status transitions ──
            transition_map = {
                'PLACED':    [],
                'PREPARING': ['PREPARING'],
                'READY':     ['PREPARING', 'READY'],
                'SERVED':    ['PREPARING', 'READY', 'SERVED'],
                'COMPLETED': ['PREPARING', 'READY', 'SERVED', 'COMPLETED'],
                'CANCELLED': ['CANCELLED'],
            }

            elapsed = 0
            for step in transition_map[target_status]:
                if step == 'CANCELLED':
                    # Random cancel time — could be early (5 min) or late (30 min wait)
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
                    # Some orders take abnormally long (kitchen delays)
                    if random.random() < 0.15:
                        elapsed += random.randint(25, 45)  # long delay
                    else:
                        elapsed += random.randint(8, 18)
                    order.status = 'READY'
                elif step == 'SERVED':
                    elapsed += random.randint(2, 10)
                    order.status = 'SERVED'
                    order.served_at = placed_dt + timedelta(minutes=elapsed)
                elif step == 'COMPLETED':
                    elapsed += random.randint(15, 55)  # dining duration
                    order.status = 'COMPLETED'
                    order.completed_at = placed_dt + timedelta(minutes=elapsed)

                order.save()

            orders.append(order)
            status_counts[target_status] = status_counts.get(target_status, 0) + 1

        # Print breakdown
        for s in ['COMPLETED', 'SERVED', 'PREPARING', 'READY', 'PLACED', 'CANCELLED']:
            c = status_counts.get(s, 0)
            self.stdout.write(f'   [{s:12s}] x{c}')
        self.stdout.write(self.style.SUCCESS(f'   --- Total: {len(orders)} orders'))

        return orders

    # ─────────────────────────────────────────────────────────
    # 5. PAYMENTS — all methods, failures, refunds, tips
    # ─────────────────────────────────────────────────────────
    def _create_payments(self, orders):
        self.stdout.write(self.style.HTTP_INFO('\n[6] Payments (all methods, failures, refunds)'))

        payments = []
        stats = {'SUCCESS': 0, 'FAILED': 0, 'REFUNDED': 0, 'PENDING': 0}

        for order in orders:
            if order.status == 'CANCELLED':
                # 30 % of cancelled orders have a failed/refunded payment attempt
                if random.random() < 0.30:
                    p = PaymentLog.objects.create(
                        order=order,
                        amount=order.total,
                        method=random.choice(['CARD', 'UPI']),
                        status=random.choice(['FAILED', 'REFUNDED']),
                        transaction_id=f'TXN-F-{uuid.uuid4().hex[:8].upper()}',
                        tip_amount=Decimal('0.00'),
                    )
                    payments.append(p)
                    stats[p.status] += 1
                continue

            if order.status in ('COMPLETED', 'SERVED'):
                method = random.choices(
                    ['CASH', 'CARD', 'UPI', 'WALLET', 'SPLIT'],
                    weights=[20, 30, 30, 10, 10],
                )[0]

                # Tip distribution: 0 (40%), small (30%), medium (20%), generous (10%)
                tip = Decimal(str(random.choices(
                    [0, 20, 50, 100, 150, 200, 300],
                    weights=[40, 15, 15, 12, 8, 6, 4],
                )[0]))

                status = 'SUCCESS'
                # 5 % chance of a failed payment followed by a successful retry
                if random.random() < 0.05:
                    PaymentLog.objects.create(
                        order=order, amount=order.total,
                        method='CARD', status='FAILED',
                        transaction_id=f'TXN-F-{uuid.uuid4().hex[:8].upper()}',
                        tip_amount=Decimal('0.00'),
                    )
                    stats['FAILED'] += 1

                p = PaymentLog.objects.create(
                    order=order,
                    amount=order.total,
                    method=method,
                    status=status,
                    transaction_id=f'TXN-{uuid.uuid4().hex[:8].upper()}',
                    tip_amount=tip,
                )
                payments.append(p)
                stats[status] += 1

            elif order.status == 'PLACED':
                # Some newly placed orders might have a PENDING payment (advance for large parties)
                if order.party_size >= 6 and random.random() < 0.5:
                    p = PaymentLog.objects.create(
                        order=order,
                        amount=Decimal(str(float(order.total) * 0.3)),  # 30% advance
                        method='UPI', status='PENDING',
                        transaction_id=f'TXN-P-{uuid.uuid4().hex[:8].upper()}',
                        tip_amount=Decimal('0.00'),
                    )
                    payments.append(p)
                    stats['PENDING'] += 1

        for s, c in stats.items():
            self.stdout.write(f'   [{s}]: {c}')
        self.stdout.write(self.style.SUCCESS(f'   --- Total: {len(payments)} payment records'))

    # ─────────────────────────────────────────────────────────
    # 6. INVENTORY — includes low stock & near-expiry
    # ─────────────────────────────────────────────────────────
    def _create_inventory(self, outlet):
        self.stdout.write(self.style.HTTP_INFO('\n[7] Inventory (low stock + near-expiry alerts)'))
        today = timezone.now().date()

        items_data = [
            # (name, category, unit, current, reorder, par, cost, expiry_offset_days)
            # ─── LOW STOCK (current < reorder) ───
            ('Paneer',           'DAIRY',    'KG',   3,   10, 25,  350, 3),
            ('Tomatoes',         'PRODUCE',  'KG',   5,   15, 40,   45, 5),
            ('Coffee Beans',     'BEVERAGE', 'KG',   2,    8, 20,  850, 60),
            ('Chicken',          'MEAT',     'KG',   4,   12, 30,  280, 2),   # also near-expiry
            ('Curd / Yogurt',    'DAIRY',    'KG',   1,    5, 15,  100, 1),   # critical!
            # ─── ADEQUATE STOCK ───
            ('Basmati Rice',     'DRY',      'KG',  45,   20, 100, 120, 180),
            ('Cooking Oil',      'DRY',      'L',   28,   10,  50, 180, 120),
            ('Flour (Maida)',    'DRY',      'KG',  35,   15,  60,  55, 150),
            ('Onions',           'PRODUCE',  'KG',  25,   10,  50,  25, 14),
            ('Milk',             'DAIRY',    'L',   50,   25,  80,  65, 4),
            ('Sugar',            'DRY',      'KG',  20,    8,  40,  50, 365),
            ('Salt',             'DRY',      'KG',  15,    5,  30,  30, 365),
            # ─── BEVERAGES ───
            ('Mango Pulp',       'BEVERAGE', 'L',   10,    5,  20, 200, 30),
            ('Soda Water',       'BEVERAGE', 'L',   40,   15,  60,  25, 90),
            # ─── SUPPLIES ───
            ('Paper Napkins',    'SUPPLIES', 'BOXES', 35, 20, 50,  120, None),
            ('Disposable Gloves','SUPPLIES', 'BOXES', 18, 10, 30,   80, None),
            ('Cleaning Solution','SUPPLIES', 'L',    12,  5, 20,   150, None),
            ('Aluminium Foil',   'SUPPLIES', 'PCS',  22, 10, 40,    90, None),
            # ─── NEAR-EXPIRY but adequate stock ───
            ('Cream',            'DAIRY',    'L',    8,   5, 15,  250, 2),
            ('Prawns (frozen)',  'MEAT',     'KG',  10,   5, 20,  650, 3),
        ]

        created = 0
        low = 0
        expiring = 0
        for name, cat, unit, cur, reorder, par, cost, exp_days in items_data:
            expiry = (today + timedelta(days=exp_days)) if exp_days is not None else None
            item, c = InventoryItem.objects.get_or_create(
                outlet=outlet, name=name,
                defaults={
                    'category': cat, 'unit': unit,
                    'current_quantity': cur, 'reorder_threshold': reorder,
                    'par_level': par, 'unit_cost': Decimal(str(cost)),
                    'expiry_date': expiry, 'last_restocked': today - timedelta(days=random.randint(1, 7)),
                },
            )
            created += c
            is_low = cur < reorder
            is_expiring = exp_days is not None and exp_days <= 3
            low += is_low
            expiring += is_expiring

            if is_low:
                self.stdout.write(f'   [LOW]    {name}: {cur} {unit} (need {reorder})')
            elif is_expiring:
                self.stdout.write(f'   [EXPIRY] {name}: expires in {exp_days}d')
            else:
                self.stdout.write(f'   [OK]     {name}: {cur} {unit}')

        self.stdout.write(self.style.SUCCESS(f'   --- {created} items | {low} low stock | {expiring} near-expiry'))

    # ─────────────────────────────────────────────────────────
    # 7. STAFF SCHEDULES — includes short-staffing gaps
    # ─────────────────────────────────────────────────────────
    def _create_staff_schedules(self, staff):
        self.stdout.write(self.style.HTTP_INFO('\n[8] Staff Schedules (includes short-staffing)'))
        today = timezone.now().date()
        now = timezone.now()

        all_profiles = [p for profiles in staff.values() for p in profiles]
        created = 0

        shift_times = {
            'MORNING':   (time(6, 0),  time(14, 0)),
            'AFTERNOON': (time(14, 0), time(22, 0)),
            'NIGHT':     (time(22, 0), time(6, 0)),
        }

        for i, day_offset in enumerate(range(-1, 3)):  # yesterday, today, tomorrow, day after
            d = today + timedelta(days=day_offset)
            for profile in all_profiles:
                # Not everyone works every day — 75 % chance of being scheduled
                if random.random() > 0.75 and profile.role not in ('MANAGER',):
                    continue  # day off → short-staffing scenario

                shift = random.choices(
                    ['MORNING', 'AFTERNOON', 'NIGHT'],
                    weights=[30, 50, 20],
                )[0]
                start, end = shift_times[shift]

                sched, c = StaffSchedule.objects.get_or_create(
                    staff=profile, date=d, shift=shift,
                    defaults={
                        'start_time': start,
                        'end_time': end,
                        'is_confirmed': random.random() < 0.85,
                        'is_ai_suggested': random.random() < 0.3,
                        'checked_in': now - timedelta(hours=random.randint(1, 6)) if d == today and random.random() < 0.7 else None,
                        'checked_out': None,
                        'notes': random.choice([
                            None, None, None,
                            'Arrived 10 mins late',
                            'Covering for sick colleague',
                            'Training new waiter',
                            'Half-day approved',
                        ]),
                    },
                )
                created += c

        self.stdout.write(self.style.SUCCESS(f'   [OK] {created} schedule entries across 4 days'))

    # ─────────────────────────────────────────────────────────
    # 8. SALES DATA — hourly breakdown for past 7 days
    # ─────────────────────────────────────────────────────────
    def _create_sales_data(self, outlet):
        self.stdout.write(self.style.HTTP_INFO('\n[9] Historical Sales Data (7 days x hourly)'))
        today = timezone.now().date()
        created = 0

        for days_ago in range(7):
            d = today - timedelta(days=days_ago)
            day_of_week = d.weekday()
            is_weekend = day_of_week in (5, 6)

            for hour in range(11, 24):  # 11 AM to 11 PM
                # Hourly traffic model
                base_orders = {
                    11: 6, 12: 14, 13: 16, 14: 10, 15: 5, 16: 4, 17: 5,
                    18: 8, 19: 18, 20: 22, 21: 20, 22: 12, 23: 4,
                }[hour]
                # Weekend boost
                if is_weekend:
                    base_orders = int(base_orders * 1.3)
                orders = base_orders + random.randint(-3, 3)
                orders = max(1, orders)

                revenue = Decimal(str(orders * random.randint(350, 650)))
                avg_ticket = revenue / orders if orders else Decimal('0')

                category_sales = {
                    'Starters': float(revenue * Decimal('0.15')),
                    'Mains': float(revenue * Decimal('0.45')),
                    'Breads': float(revenue * Decimal('0.10')),
                    'Beverages': float(revenue * Decimal('0.15')),
                    'Desserts': float(revenue * Decimal('0.15')),
                }
                top_items = random.sample(
                    [it['name'] for it in FLAT_MENU], min(5, len(FLAT_MENU))
                )

                _, c = SalesData.objects.get_or_create(
                    outlet=outlet, date=d, hour=hour,
                    defaults={
                        'total_orders': orders,
                        'total_revenue': revenue,
                        'avg_ticket_size': avg_ticket,
                        'avg_wait_time_minutes': random.randint(8, 30),
                        'category_sales': category_sales,
                        'top_items': top_items,
                        'day_of_week': day_of_week,
                        'is_holiday': is_weekend,
                        'weather_condition': random.choice(['SUNNY', 'CLOUDY', 'RAINY', 'CLEAR']),
                    },
                )
                created += c

        self.stdout.write(self.style.SUCCESS(f'   [OK] {created} hourly sales records (7 days)'))

    # ─────────────────────────────────────────────────────────
    # 9. DAILY SUMMARY — realistic aggregated metrics
    # ─────────────────────────────────────────────────────────
    def _create_daily_summary(self, outlet, orders):
        self.stdout.write(self.style.HTTP_INFO('\n[10] Daily Summary'))
        today = timezone.now().date()

        # Compute from actual orders for today
        today_orders = [o for o in orders if o.placed_at and o.placed_at.date() == today]
        total_rev = sum(float(o.total) for o in today_orders if o.status not in ('CANCELLED',))
        total_ord = len([o for o in today_orders if o.status not in ('CANCELLED',)])
        cancelled = len([o for o in today_orders if o.status == 'CANCELLED'])
        delayed = len([o for o in today_orders if o.is_long_wait])
        total_guests = sum(o.party_size for o in today_orders if o.status not in ('CANCELLED',))
        total_tips_val = sum(
            float(p.tip_amount)
            for o in today_orders
            for p in o.payments.filter(status='SUCCESS')
        )
        staff_count = UserProfile.objects.filter(outlet=outlet, is_on_shift=True).count() or 1

        avg_ticket = total_rev / total_ord if total_ord else 0
        rev_per_staff = total_rev / staff_count

        # Top selling items from order data
        item_counter = {}
        for o in today_orders:
            if o.status == 'CANCELLED':
                continue
            for it in (o.items or []):
                item_counter[it['name']] = item_counter.get(it['name'], 0) + 1
        top_items = sorted(item_counter, key=item_counter.get, reverse=True)[:10]

        # Category sales from order data
        cat_revenue = {'Starters': 0, 'Mains': 0, 'Breads': 0, 'Beverages': 0, 'Desserts': 0}
        cat_lookup = {}
        for cat_name, items in MENU.items():
            for it in items:
                cat_lookup[it['name']] = cat_name.capitalize()
        for o in today_orders:
            if o.status == 'CANCELLED':
                continue
            for it in (o.items or []):
                cat = cat_lookup.get(it['name'], 'Mains')
                cat_revenue[cat] = cat_revenue.get(cat, 0) + it.get('price', 0)

        summary, created = DailySummary.objects.get_or_create(
            outlet=outlet, date=today,
            defaults={
                'total_revenue': Decimal(str(round(total_rev, 2))),
                'total_orders': total_ord,
                'avg_ticket_size': Decimal(str(round(avg_ticket, 2))),
                'total_tips': Decimal(str(round(total_tips_val, 2))),
                'total_guests': total_guests,
                'avg_table_turnover_time': random.uniform(35, 65),
                'avg_wait_time': random.uniform(10, 22),
                'peak_hour': 20,
                'peak_revenue': Decimal(str(round(total_rev * 0.18, 2))),
                'delayed_orders': delayed,
                'cancelled_orders': cancelled,
                'sales_by_category': cat_revenue,
                'top_selling_items': top_items,
                'staff_count': staff_count,
                'revenue_per_staff': Decimal(str(round(rev_per_staff, 2))),
            },
        )

        self.stdout.write(f'   Revenue: Rs.{total_rev:,.2f}')
        self.stdout.write(f'   Orders: {total_ord} active + {cancelled} cancelled')
        self.stdout.write(f'   Delayed: {delayed}')
        self.stdout.write(f'   Guests: {total_guests}')
        self.stdout.write(f'   Tips: Rs.{total_tips_val:,.2f}')
        self.stdout.write(f'   Staff on shift: {staff_count}')
        self.stdout.write(self.style.SUCCESS(f'   {"+ Created" if created else "= Exists"}'))

    # ─────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────
    def _print_summary(self, outlet):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('  Synthetic Data Generation Complete!'))
        self.stdout.write('=' * 70)

        self.stdout.write(f'\n  Outlet: {outlet.name}')
        self.stdout.write(f'  Outlet ID: {outlet.pk}')
        self.stdout.write(f'  Login: synth_mgr_1 / synth123')

        self.stdout.write(f'\n  Next Steps:')
        self.stdout.write(f'     1. Login -> POST /api/auth/login/  (synth_mgr_1 / synth123)')
        self.stdout.write(f'     2. Generate report -> POST /api/insights/reports/generate/')
        self.stdout.write(f'        Body: {{"outlet_id": {outlet.pk}, "report_type": "DAILY"}}')
        self.stdout.write(f'     3. The pipeline will:')
        self.stdout.write(f'        - Collect all today\'s data')
        self.stdout.write(f'        - Send to GPT-4o for analysis')
        self.stdout.write(f'        - Build a professional PDF')
        self.stdout.write(f'        - Upload to Cloudinary')
        self.stdout.write(f'        - Return the PDF link')
        self.stdout.write('\n' + '=' * 70 + '\n')
