"""
Management command to create comprehensive demo data for testing the admin panel.
Creates brands, outlets, users, tables, orders, payments, inventory, schedules, and reports.

Usage:
    python manage.py create_full_demo_data
    python manage.py create_full_demo_data --clear  (to clear existing demo data first)
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, time
from decimal import Decimal
import random

from apps.hospitality_group.models import Brand, Outlet, UserProfile
from apps.layout_twin.models import ServiceNode, ServiceFlow
from apps.order_engine.models import OrderTicket, PaymentLog
from apps.predictive_core.models import SalesData, InventoryItem, StaffSchedule
from apps.insights_hub.models import DailySummary, PDFReport


class Command(BaseCommand):
    help = 'Creates comprehensive demo data for all models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_demo_data()
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Creating Comprehensive Demo Data'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Create data in order of dependencies
        brand = self.create_brand()
        outlet = self.create_outlet(brand)
        users = self.create_users(outlet)
        tables = self.create_tables(outlet)
        flows = self.create_service_flows(tables)
        orders = self.create_orders(tables, users)
        payments = self.create_payments(orders)
        sales_data = self.create_sales_data(outlet)
        inventory = self.create_inventory(outlet)
        schedules = self.create_schedules(users, outlet)
        summaries = self.create_daily_summaries(outlet)
        reports = self.create_reports(outlet, users)
        
        self.print_summary(brand, outlet, users, tables, orders, payments, 
                          inventory, schedules, summaries, reports)

    def clear_demo_data(self):
        self.stdout.write(self.style.WARNING('\nClearing existing demo data...'))
        
        # Delete in reverse order of dependencies
        PDFReport.objects.filter(outlet__brand__corporate_id='DEMO001').delete()
        DailySummary.objects.filter(outlet__brand__corporate_id='DEMO001').delete()
        StaffSchedule.objects.filter(staff__outlet__brand__corporate_id='DEMO001').delete()
        InventoryItem.objects.filter(outlet__brand__corporate_id='DEMO001').delete()
        SalesData.objects.filter(outlet__brand__corporate_id='DEMO001').delete()
        PaymentLog.objects.filter(order__table__outlet__brand__corporate_id='DEMO001').delete()
        OrderTicket.objects.filter(table__outlet__brand__corporate_id='DEMO001').delete()
        ServiceFlow.objects.filter(source_node__outlet__brand__corporate_id='DEMO001').delete()
        ServiceNode.objects.filter(outlet__brand__corporate_id='DEMO001').delete()
        UserProfile.objects.filter(outlet__brand__corporate_id='DEMO001').delete()
        User.objects.filter(username__endswith='_demo').delete()
        Outlet.objects.filter(brand__corporate_id='DEMO001').delete()
        Brand.objects.filter(corporate_id='DEMO001').delete()
        
        self.stdout.write(self.style.SUCCESS('✓ Cleared all demo data'))

    def create_brand(self):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('1. Creating Brand'))
        self.stdout.write('─' * 60)
        
        brand, created = Brand.objects.get_or_create(
            corporate_id='DEMO001',
            defaults={
                'name': 'TwinEngine Demo Restaurant Group',
                'contact_email': 'admin@twinengine.demo',
                'subscription_tier': 'PRO',
            }
        )
        status = '✓ Created' if created else '○ Already exists'
        self.stdout.write(self.style.SUCCESS(f'{status}: {brand.name}'))
        return brand

    def create_outlet(self, brand):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('2. Creating Outlet'))
        self.stdout.write('─' * 60)
        
        outlet, created = Outlet.objects.get_or_create(
            brand=brand,
            name='Downtown Cafe Mumbai',
            defaults={
                'address': '123 Marine Drive, Churchgate, Mumbai, Maharashtra 400020',
                'city': 'Mumbai',
                'seating_capacity': 50,
                'opening_time': time(9, 0),
                'closing_time': time(23, 0),
                'is_active': True
            }
        )
        status = '✓ Created' if created else '○ Already exists'
        self.stdout.write(self.style.SUCCESS(f'{status}: {outlet.name} ({outlet.seating_capacity} seats)'))
        return outlet

    def create_users(self, outlet):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('3. Creating Users & Profiles'))
        self.stdout.write('─' * 60)
        
        users_data = [
            {'username': 'manager_demo', 'email': 'manager@demo.com', 'password': 'manager123', 
             'role': 'MANAGER', 'phone': '+91-9876543211', 'first_name': 'Rajesh', 'last_name': 'Kumar'},
            {'username': 'waiter1_demo', 'email': 'waiter1@demo.com', 'password': 'waiter123', 
             'role': 'WAITER', 'phone': '+91-9876543212', 'first_name': 'Amit', 'last_name': 'Sharma'},
            {'username': 'waiter2_demo', 'email': 'waiter2@demo.com', 'password': 'waiter123', 
             'role': 'WAITER', 'phone': '+91-9876543213', 'first_name': 'Priya', 'last_name': 'Patel'},
            {'username': 'chef_demo', 'email': 'chef@demo.com', 'password': 'chef123', 
             'role': 'CHEF', 'phone': '+91-9876543214', 'first_name': 'Vikram', 'last_name': 'Singh'},
            {'username': 'host_demo', 'email': 'host@demo.com', 'password': 'host123', 
             'role': 'HOST', 'phone': '+91-9876543215', 'first_name': 'Sneha', 'last_name': 'Desai'},
        ]
        
        created_users = {}
        for user_data in users_data:
            user, user_created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )
            
            if user_created:
                user.set_password(user_data['password'])
                user.save()
            
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'outlet': outlet,
                    'role': user_data['role'],
                    'phone': user_data['phone'],
                    'is_on_shift': random.choice([True, False])
                }
            )
            
            created_users[user_data['role']] = profile
            status = '✓' if user_created else '○'
            shift_status = '🟢 ON SHIFT' if profile.is_on_shift else '⚪ OFF SHIFT'
            self.stdout.write(f'{status} {user.get_full_name()} - {user_data["role"]} - {shift_status}')
        
        return created_users

    def create_tables(self, outlet):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('4. Creating Tables (ServiceNodes)'))
        self.stdout.write('─' * 60)
        
        statuses = ['BLUE', 'GREEN', 'YELLOW', 'RED']
        tables = []
        
        # Create 15 tables
        for i in range(1, 16):
            table, created = ServiceNode.objects.get_or_create(
                outlet=outlet,
                name=f'Table {i}',
                defaults={
                    'node_type': 'TABLE',
                    'capacity': random.choice([2, 4, 6]),
                    'pos_x': float((i % 5) * 2.5),
                    'pos_y': 0.0,
                    'pos_z': float((i // 5) * 2.5),
                    'current_status': random.choice(statuses),
                    'is_active': True
                }
            )
            tables.append(table)
            status = '✓' if created else '○'
            status_color = {
                'BLUE': '🔵', 'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'
            }[table.current_status]
            self.stdout.write(f'{status} {table.name} - Capacity: {table.capacity} - {status_color} {table.current_status}')
        
        # Create kitchen and bar nodes
        kitchen, _ = ServiceNode.objects.get_or_create(
            outlet=outlet,
            name='Kitchen',
            defaults={'node_type': 'KITCHEN', 'capacity': 0, 'current_status': 'GREEN'}
        )
        bar, _ = ServiceNode.objects.get_or_create(
            outlet=outlet,
            name='Bar',
            defaults={'node_type': 'BAR', 'capacity': 0, 'current_status': 'GREEN'}
        )
        
        self.stdout.write(f'✓ Kitchen Node')
        self.stdout.write(f'✓ Bar Node')
        
        return tables + [kitchen, bar]

    def create_service_flows(self, nodes):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('5. Creating Service Flows'))
        self.stdout.write('─' * 60)
        
        tables = [n for n in nodes if n.node_type == 'TABLE']
        kitchen = next((n for n in nodes if n.node_type == 'KITCHEN'), None)
        bar = next((n for n in nodes if n.node_type == 'BAR'), None)
        
        flows = []
        count = 0
        
        # Create flows from tables to kitchen and bar
        for table in tables[:10]:  # First 10 tables to kitchen
            flow, created = ServiceFlow.objects.get_or_create(
                source_node=table,
                target_node=kitchen,
                defaults={'flow_type': 'ORDER', 'is_active': True}
            )
            if created:
                count += 1
        
        for table in tables[10:]:  # Remaining tables to bar
            flow, created = ServiceFlow.objects.get_or_create(
                source_node=table,
                target_node=bar,
                defaults={'flow_type': 'ORDER', 'is_active': True}
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {count} service flows (table → kitchen/bar)'))
        return flows

    def create_orders(self, tables, users):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('6. Creating Orders'))
        self.stdout.write('─' * 60)
        
        waiter1 = users.get('WAITER')
        waiter2_profile = UserProfile.objects.filter(role='WAITER').exclude(id=waiter1.id).first()
        
        # Status distribution: more completed orders for realistic demo
        statuses_to_create = ['PLACED'] * 2 + ['PREPARING'] * 3 + ['READY'] * 2 + ['SERVED'] * 4 + ['COMPLETED'] * 5 + ['CANCELLED'] * 1
        random.shuffle(statuses_to_create)
        
        menu_items = [
            {'name': 'Butter Chicken', 'price': 450},
            {'name': 'Paneer Tikka', 'price': 350},
            {'name': 'Dal Makhani', 'price': 280},
            {'name': 'Biryani', 'price': 380},
            {'name': 'Naan', 'price': 40},
            {'name': 'Masala Dosa', 'price': 150},
            {'name': 'Coffee', 'price': 80},
            {'name': 'Gulab Jamun', 'price': 120},
        ]
        
        orders = []
        now = timezone.now()
        table_index = 0
        
        for i, target_status in enumerate(statuses_to_create):
            # Find next table
            while table_index < len(tables) and tables[table_index].node_type != 'TABLE':
                table_index += 1
            
            if table_index >= len(tables):
                break
                
            table = tables[table_index]
            table_index += 1
            
            num_items = random.randint(2, 5)
            items = random.sample(menu_items, num_items)
            subtotal = sum(item['price'] for item in items)
            tax = round(subtotal * 0.05, 2)
            total = subtotal + tax
            
            # Vary order times
            hours_ago = random.randint(0, 5)
            placed_time = now - timedelta(hours=hours_ago, minutes=random.randint(0, 59))
            
            waiter = waiter1 if i % 2 == 0 else waiter2_profile
            
            # Create order with PLACED status first (required by validation)
            order = OrderTicket.objects.create(
                table=table,
                waiter=waiter,
                customer_name=random.choice(['Rahul', 'Priya', 'Amit', 'Sneha', 'Vikram', None]),
                party_size=random.randint(1, table.capacity),
                items=items,
                special_requests=random.choice(['Less spicy', 'Extra napkins', 'Birthday celebration', None, None]),
                status='PLACED',
                subtotal=Decimal(str(subtotal)),
                tax=Decimal(str(tax)),
                total=Decimal(str(total)),
                placed_at=placed_time,
            )
            
            # Progress order through status transitions to reach target status
            status_sequence = {
                'PLACED': ['PLACED'],
                'PREPARING': ['PLACED', 'PREPARING'],
                'READY': ['PLACED', 'PREPARING', 'READY'],
                'SERVED': ['PLACED', 'PREPARING', 'READY', 'SERVED'],
                'COMPLETED': ['PLACED', 'PREPARING', 'READY', 'SERVED', 'COMPLETED'],
                'CANCELLED': ['PLACED', 'CANCELLED'],
            }
            
            current_time = placed_time
            for status in status_sequence[target_status][1:]:  # Skip first PLACED since already set
                current_time = current_time + timedelta(minutes=random.randint(5, 15))
                order.status = status
                
                # Set timestamps for specific statuses
                if status == 'SERVED':
                    order.served_at = current_time
                elif status == 'COMPLETED':
                    order.completed_at = current_time
                
                order.save()
            
            orders.append(order)
            
            status_badge = {
                'PLACED': '🔴', 'PREPARING': '🟠', 'READY': '🟡',
                'SERVED': '🟢', 'COMPLETED': '🔵', 'CANCELLED': '⚪'
            }[target_status]
            self.stdout.write(f'✓ Order #{order.id} - {table.name} - ₹{total} - {status_badge} {target_status}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal orders created: {len(orders)}'))
        return orders

    def create_payments(self, orders):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('7. Creating Payments'))
        self.stdout.write('─' * 60)
        
        methods = ['CASH', 'CARD', 'UPI', 'WALLET']
        payments = []
        
        for order in orders:
            if order.status in ['COMPLETED', 'SERVED']:
                # Add tip randomly
                tip = random.choice([0, 20, 50, 100])
                
                payment, created = PaymentLog.objects.get_or_create(
                    order=order,
                    defaults={
                        'amount': order.total,
                        'method': random.choice(methods),
                        'status': 'COMPLETED' if order.status == 'COMPLETED' else 'PENDING',
                        'tip_amount': Decimal(str(tip)),
                        'transaction_id': f'TXN{order.id}{random.randint(1000, 9999)}',
                    }
                )
                payments.append(payment)
                
                if created:
                    method_emoji = {'CASH': '💵', 'CARD': '💳', 'UPI': '📱', 'WALLET': '👛'}[payment.method]
                    self.stdout.write(f'✓ Payment for Order #{order.id} - {method_emoji} {payment.method} - ₹{payment.amount + payment.tip_amount}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal payments created: {len(payments)}'))
        return payments

    def create_sales_data(self, outlet):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('8. Creating Sales Data'))
        self.stdout.write('─' * 60)
        
        sales_data = []
        today = timezone.now().date()
        
        # Create sales data for last 7 days
        for days_ago in range(7):
            date = today - timedelta(days=days_ago)
            day_of_week = date.weekday()
            
            # Create hourly data for peak hours
            for hour in [12, 13, 19, 20, 21]:
                data, created = SalesData.objects.get_or_create(
                    outlet=outlet,
                    date=date,
                    hour=hour,
                    defaults={
                        'day_of_week': day_of_week,
                        'is_holiday': date.weekday() in [5, 6],  # Weekend
                        'total_orders': random.randint(8, 20),
                        'total_revenue': Decimal(str(random.randint(5000, 15000))),
                        'avg_wait_time_minutes': random.randint(12, 25),
                    }
                )
                if created:
                    sales_data.append(data)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(sales_data)} sales data records (7 days × 5 peak hours)'))
        return sales_data

    def create_inventory(self, outlet):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('9. Creating Inventory Items'))
        self.stdout.write('─' * 60)
        
        items_data = [
            {'name': 'Basmati Rice', 'category': 'DRY', 'unit': 'KG', 'current': 45, 'min': 20, 'max': 100, 'cost': 120},
            {'name': 'Paneer', 'category': 'DAIRY', 'unit': 'KG', 'current': 8, 'min': 10, 'max': 25, 'cost': 350},  # Low stock
            {'name': 'Chicken', 'category': 'MEAT', 'unit': 'KG', 'current': 15, 'min': 10, 'max': 30, 'cost': 280},
            {'name': 'Tomatoes', 'category': 'PRODUCE', 'unit': 'KG', 'current': 12, 'min': 15, 'max': 40, 'cost': 45},  # Low stock
            {'name': 'Cooking Oil', 'category': 'DRY', 'unit': 'L', 'current': 25, 'min': 10, 'max': 50, 'cost': 180},
            {'name': 'Coffee Beans', 'category': 'BEVERAGE', 'unit': 'KG', 'current': 5, 'min': 8, 'max': 20, 'cost': 850},  # Low stock
            {'name': 'Paper Napkins', 'category': 'SUPPLIES', 'unit': 'BOXES', 'current': 30, 'min': 20, 'max': 50, 'cost': 120},
            {'name': 'Milk', 'category': 'DAIRY', 'unit': 'L', 'current': 40, 'min': 25, 'max': 80, 'cost': 65},
        ]
        
        inventory = []
        for item_data in items_data:
            item, created = InventoryItem.objects.get_or_create(
                outlet=outlet,
                name=item_data['name'],
                defaults={
                    'category': item_data['category'],
                    'unit': item_data['unit'],
                    'current_quantity': item_data['current'],
                    'reorder_threshold': item_data['min'],
                    'par_level': item_data['max'],
                    'unit_cost': Decimal(str(item_data['cost'])),
                }
            )
            inventory.append(item)
            
            if created:
                is_low = item.current_quantity < item.reorder_threshold
                status_emoji = '⚠️ LOW STOCK' if is_low else '✓ OK'
                self.stdout.write(f'{status_emoji} - {item.name} - {item.current_quantity}{item.unit}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal inventory items: {len(inventory)}'))
        return inventory

    def create_schedules(self, users, outlet):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('10. Creating Staff Schedules'))
        self.stdout.write('─' * 60)
        
        schedules = []
        today = timezone.now().date()
        
        shifts = [
            ('MORNING', time(9, 0), time(17, 0)),
            ('EVENING', time(17, 0), time(23, 0)),
            ('AFTERNOON', time(12, 0), time(20, 0)),
        ]
        
        # Create schedules for next 3 days
        for days_ahead in range(3):
            date = today + timedelta(days=days_ahead)
            
            for user_profile in UserProfile.objects.filter(outlet=outlet):
                shift_name, start_time, end_time = random.choice(shifts)
                
                schedule, created = StaffSchedule.objects.get_or_create(
                    staff=user_profile,
                    date=date,
                    defaults={
                        'shift': shift_name,
                        'start_time': start_time,
                        'end_time': end_time,
                        'is_confirmed': random.choice([True, False]),
                        'is_ai_suggested': random.choice([True, False]),
                    }
                )
                
                if created:
                    schedules.append(schedule)
                    confirmed = '✓ Confirmed' if schedule.is_confirmed else '○ Pending'
                    ai = '🤖 AI' if schedule.is_ai_suggested else '👤 Manual'
                    self.stdout.write(f'{confirmed} - {user_profile.user.get_full_name()} - {shift_name} - {ai}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal schedules created: {len(schedules)}'))
        return schedules

    def create_daily_summaries(self, outlet):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('11. Creating Daily Summaries'))
        self.stdout.write('─' * 60)
        
        summaries = []
        today = timezone.now().date()
        
        # Create summaries for last 7 days
        for days_ago in range(7):
            date = today - timedelta(days=days_ago)
            
            total_revenue = Decimal(str(random.randint(35000, 85000)))
            total_orders = random.randint(45, 120)
            delayed_orders = random.randint(0, 8)
            
            summary, created = DailySummary.objects.get_or_create(
                outlet=outlet,
                date=date,
                defaults={
                    'total_revenue': total_revenue,
                    'total_orders': total_orders,
                    'avg_ticket_size': total_revenue / total_orders if total_orders > 0 else 0,
                    'total_tips': Decimal(str(random.randint(1000, 5000))),
                    'total_guests': random.randint(80, 200),
                    'avg_table_turnover_time': random.randint(45, 90),
                    'avg_wait_time': random.randint(12, 25),
                    'peak_hour': random.randint(19, 21),
                    'peak_revenue': Decimal(str(random.randint(8000, 15000))),
                    'delayed_orders': delayed_orders,
                    'cancelled_orders': random.randint(0, 3),
                    'staff_count': 5,
                    'revenue_per_staff': total_revenue / 5,
                }
            )
            
            if created:
                summaries.append(summary)
                delayed_badge = f'⚠️ {delayed_orders} delayed' if delayed_orders > 0 else '✓ No delays'
                self.stdout.write(f'✓ {date} - ₹{total_revenue:,.2f} - {total_orders} orders - {delayed_badge}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal summaries created: {len(summaries)}'))
        return summaries

    def create_reports(self, outlet, users):
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(self.style.HTTP_INFO('12. Creating PDF Reports'))
        self.stdout.write('─' * 60)
        
        reports = []
        today = timezone.now().date()
        manager = users.get('MANAGER')
        
        report_types = [
            ('DAILY', today - timedelta(days=1), today - timedelta(days=1)),
            ('WEEKLY', today - timedelta(days=7), today),
            ('MONTHLY', today - timedelta(days=30), today),
        ]
        
        for report_type, start_date, end_date in report_types:
            report, created = PDFReport.objects.get_or_create(
                outlet=outlet,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                defaults={
                    'status': random.choice(['COMPLETED', 'PENDING', 'GENERATING']),
                    'gpt_summary': f'Summary for {report_type.lower()} report from {start_date} to {end_date}',
                    'insights': 'Revenue trending upward. Peak hours: 7-9 PM. Popular items: Biryani, Butter Chicken.',
                    'recommendations': 'Increase staff during peak hours. Consider promotions for afternoon slots.',
                    'generated_by': manager.user if manager else None,
                }
            )
            
            if created:
                reports.append(report)
                status_emoji = {'COMPLETED': '✅', 'PENDING': '⏳', 'GENERATING': '⚙️'}[report.status]
                self.stdout.write(f'{status_emoji} {report_type} Report - {start_date} to {end_date}')
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal reports created: {len(reports)}'))
        return reports

    def print_summary(self, brand, outlet, users, tables, orders, payments, 
                     inventory, schedules, summaries, reports):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Demo Data Creation Complete! 🎉'))
        self.stdout.write('=' * 60)
        
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'   • Brand: {brand.name}')
        self.stdout.write(f'   • Outlet: {outlet.name}')
        self.stdout.write(f'   • Users: {len(users)} staff members')
        self.stdout.write(f'   • Tables: {len([t for t in tables if t.node_type == "TABLE"])} tables')
        self.stdout.write(f'   • Orders: {len(orders)} orders')
        self.stdout.write(f'   • Payments: {len(payments)} payments')
        self.stdout.write(f'   • Inventory: {len(inventory)} items')
        self.stdout.write(f'   • Schedules: {len(schedules)} shifts')
        self.stdout.write(f'   • Daily Summaries: {len(summaries)} days')
        self.stdout.write(f'   • Reports: {len(reports)} reports')
        
        self.stdout.write(f'\n🔑 Test Credentials:')
        self.stdout.write(f'   • Manager: manager_demo / manager123')
        self.stdout.write(f'   • Waiter: waiter1_demo / waiter123')
        self.stdout.write(f'   • Chef: chef_demo / chef123')
        
        self.stdout.write(f'\n🌐 Next Steps:')
        self.stdout.write(f'   1. Start server: python manage.py runserver')
        self.stdout.write(f'   2. Visit admin: http://127.0.0.1:8000/admin/')
        self.stdout.write(f'   3. Login with any user above')
        self.stdout.write(f'   4. Explore all admin sections!')
        
        self.stdout.write('\n' + '=' * 60)
