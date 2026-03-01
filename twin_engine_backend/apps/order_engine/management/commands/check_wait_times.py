"""
Management command to check for tables with exceeded wait times.

This command should be run periodically (every 1-2 minutes) via:
- Cron job: */2 * * * * cd /path/to/project && python manage.py check_wait_times
- Celery Beat (recommended for production)
- Manual execution for testing

Tables with orders waiting > 15 minutes will be marked RED (Needs Attention).

Usage:
    python manage.py check_wait_times              # Check all outlets
    python manage.py check_wait_times --outlet=1   # Check specific outlet
    python manage.py check_wait_times --threshold=10  # Custom threshold (minutes)
    python manage.py check_wait_times --dry-run    # Preview without changes
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for tables with orders exceeding wait time threshold and mark them RED'

    def add_arguments(self, parser):
        parser.add_argument(
            '--outlet',
            type=int,
            help='Check only specific outlet ID',
        )
        parser.add_argument(
            '--threshold',
            type=int,
            default=15,
            help='Wait time threshold in minutes (default: 15)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually updating',
        )

    def handle(self, *args, **options):
        from apps.order_engine.models import OrderTicket
        from apps.layout_twin.models import ServiceNode
        from apps.layout_twin.utils.broadcast import broadcast_node_status_change, broadcast_wait_time_alert
        
        outlet_id = options.get('outlet')
        threshold_minutes = options['threshold']
        dry_run = options['dry_run']
        
        threshold_time = timezone.now() - timedelta(minutes=threshold_minutes)
        
        self.stdout.write(
            self.style.SUCCESS(f'\n{"="*60}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Wait Time Check - Threshold: {threshold_minutes} minutes')
        )
        self.stdout.write(
            self.style.SUCCESS(f'{"="*60}\n')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))
        
        # Find orders that have been waiting too long
        long_wait_orders = OrderTicket.objects.filter(
            status__in=['PLACED', 'PREPARING'],
            placed_at__lt=threshold_time
        ).select_related('table', 'table__outlet')
        
        # Filter by outlet if specified
        if outlet_id:
            long_wait_orders = long_wait_orders.filter(table__outlet_id=outlet_id)
        
        if not long_wait_orders.exists():
            self.stdout.write(self.style.SUCCESS('✓ No tables with exceeded wait times'))
            return
        
        # Group by table (one table can have multiple long-waiting orders)
        tables_to_update = {}
        for order in long_wait_orders:
            table = order.table
            wait_time = int((timezone.now() - order.placed_at).total_seconds() / 60)
            
            if table.id not in tables_to_update:
                tables_to_update[table.id] = {
                    'table': table,
                    'orders': [],
                    'max_wait': 0
                }
            
            tables_to_update[table.id]['orders'].append(order)
            tables_to_update[table.id]['max_wait'] = max(
                tables_to_update[table.id]['max_wait'], 
                wait_time
            )
        
        self.stdout.write(f'Found {len(tables_to_update)} table(s) with long wait times:\n')
        
        updated_count = 0
        already_red_count = 0
        
        for table_data in tables_to_update.values():
            table = table_data['table']
            max_wait = table_data['max_wait']
            order_count = len(table_data['orders'])
            
            status_indicator = '🔴' if table.current_status == 'RED' else '⚠️'
            self.stdout.write(
                f'  {status_indicator} {table.name} ({table.outlet.name})'
            )
            self.stdout.write(
                f'     └─ {order_count} order(s) waiting {max_wait} minutes'
            )
            
            if table.current_status == 'RED':
                already_red_count += 1
                self.stdout.write(
                    self.style.WARNING('     └─ Already marked RED')
                )
            else:
                old_status = table.current_status
                
                if not dry_run:
                    table.current_status = 'RED'
                    table.save(update_fields=['current_status', 'updated_at'])
                    
                    # Broadcast the status change
                    try:
                        broadcast_node_status_change(
                            outlet_id=table.outlet_id,
                            node_id=table.id,
                            old_status=old_status,
                            new_status='RED',
                            node_name=table.name
                        )
                        # Also send specific wait time alert
                        broadcast_wait_time_alert(
                            outlet_id=table.outlet_id,
                            node_id=table.id,
                            node_name=table.name,
                            wait_minutes=max_wait,
                            order_count=order_count
                        )
                    except Exception as e:
                        logger.warning(f"WebSocket broadcast failed: {e}")
                
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'     └─ Marked RED ({old_status} → RED)')
                )
            
            self.stdout.write('')  # Empty line for readability
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  • Tables checked: {len(tables_to_update)}')
        self.stdout.write(f'  • Updated to RED: {updated_count}')
        self.stdout.write(f'  • Already RED: {already_red_count}')
        
        if dry_run and updated_count > 0:
            self.stdout.write(
                self.style.WARNING(f'\n  ⚠️  Run without --dry-run to apply changes')
            )
        
        self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
