"""
Tests for Table Status Auto-Update Logic.

Tests the signal-based automatic table color changes based on order lifecycle:
- Order PLACED → Table YELLOW
- Order SERVED → Table GREEN  
- Order COMPLETED → Table BLUE (if no other active orders)
- Wait time exceeded → Table RED (via management command)

Run with: python manage.py test apps.order_engine.tests.test_table_status
"""
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import timedelta
from unittest.mock import patch, MagicMock

from apps.hospitality_group.models import Brand, Outlet, UserProfile
from apps.layout_twin.models import ServiceNode
from apps.order_engine.models import OrderTicket


class TableStatusSignalTestCase(TestCase):
    """Test automatic table status updates via Django signals."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests."""
        # Create brand
        cls.brand = Brand.objects.create(
            name='Test Restaurant Group',
            corporate_id='TEST001',
            contact_email='test@example.com',
            subscription_tier='PRO'
        )
        
        # Create outlet
        cls.outlet = Outlet.objects.create(
            brand=cls.brand,
            name='Test Cafe',
            address='123 Test Street',
            city='Test City',
            seating_capacity=50,
            opening_time='09:00:00',
            closing_time='22:00:00'
        )
        
        # Create user for waiter
        cls.user = User.objects.create_user(
            username='test_waiter',
            email='waiter@test.com',
            password='testpass123'
        )
        
        # Create waiter profile
        cls.waiter = UserProfile.objects.create(
            user=cls.user,
            outlet=cls.outlet,
            role='WAITER',
            phone='+91-9876543210'
        )
    
    def setUp(self):
        """Set up fresh table for each test."""
        self.table = ServiceNode.objects.create(
            outlet=self.outlet,
            name='Table-Test',
            node_type='TABLE',
            capacity=4,
            current_status='BLUE'  # Start as available
        )
    
    def tearDown(self):
        """Clean up after each test."""
        OrderTicket.objects.all().delete()
        ServiceNode.objects.filter(name='Table-Test').delete()
    
    # =========================================================================
    # TEST: Order Creation → Table turns YELLOW
    # =========================================================================
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_new_order_turns_table_yellow(self, mock_channel_layer):
        """When a new order is placed, table should turn YELLOW."""
        mock_channel_layer.return_value = MagicMock()
        
        # Verify table starts BLUE
        self.assertEqual(self.table.current_status, 'BLUE')
        
        # Create new order
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            customer_name='Test Customer',
            party_size=2,
            items=[{'name': 'Burger', 'price': 250}],
            status='PLACED'
        )
        
        # Refresh table from database
        self.table.refresh_from_db()
        
        # Table should now be YELLOW
        self.assertEqual(self.table.current_status, 'YELLOW')
    
    # =========================================================================
    # TEST: Order Served → Table turns GREEN
    # =========================================================================
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_served_order_turns_table_green(self, mock_channel_layer):
        """When order is served, table should turn GREEN."""
        mock_channel_layer.return_value = MagicMock()
        
        # Create order
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        
        # Update to SERVED
        order.status = 'SERVED'
        order.save()
        
        # Refresh table
        self.table.refresh_from_db()
        
        # Table should be GREEN
        self.assertEqual(self.table.current_status, 'GREEN')
    
    # =========================================================================
    # TEST: Order Completed → Table turns BLUE (if no other active orders)
    # =========================================================================
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_completed_order_turns_table_blue(self, mock_channel_layer):
        """When order is completed and no other orders, table should turn BLUE."""
        mock_channel_layer.return_value = MagicMock()
        
        # Create and serve order
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        order.status = 'SERVED'
        order.save()
        
        # Complete order
        order.status = 'COMPLETED'
        order.save()
        
        # Refresh table
        self.table.refresh_from_db()
        
        # Table should be BLUE (available)
        self.assertEqual(self.table.current_status, 'BLUE')
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_completed_order_with_other_active_orders(self, mock_channel_layer):
        """When one order completes but others are active, table stays colored."""
        mock_channel_layer.return_value = MagicMock()
        
        # Create two orders
        order1 = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        order2 = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        
        # Serve first order
        order1.status = 'SERVED'
        order1.save()
        
        # Complete first order
        order1.status = 'COMPLETED'
        order1.save()
        
        # Refresh table
        self.table.refresh_from_db()
        
        # Table should be YELLOW (still has active order2)
        self.assertEqual(self.table.current_status, 'YELLOW')
    
    # =========================================================================
    # TEST: Status Transition Validation
    # =========================================================================
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_invalid_status_transition_raises_error(self, mock_channel_layer):
        """Invalid status transitions should raise ValidationError."""
        mock_channel_layer.return_value = MagicMock()
        
        # Create order
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        
        # Try invalid transition: PLACED → COMPLETED (should go through SERVED)
        order.status = 'COMPLETED'
        
        with self.assertRaises(ValidationError):
            order.save()
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_valid_status_transitions(self, mock_channel_layer):
        """Valid status transitions should work without errors."""
        mock_channel_layer.return_value = MagicMock()
        
        # Create order
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        
        # Valid transitions
        order.status = 'PREPARING'
        order.save()
        
        order.status = 'READY'
        order.save()
        
        order.status = 'SERVED'
        order.save()
        
        order.status = 'COMPLETED'
        order.save()
        
        # Should complete without error
        self.assertEqual(order.status, 'COMPLETED')
    
    # =========================================================================
    # TEST: Cancelled Order
    # =========================================================================
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_cancelled_order_frees_table(self, mock_channel_layer):
        """Cancelled order should free the table if no other orders."""
        mock_channel_layer.return_value = MagicMock()
        
        # Create order
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        
        # Cancel order
        order.status = 'CANCELLED'
        order.save()
        
        # Refresh table
        self.table.refresh_from_db()
        
        # Table should be BLUE
        self.assertEqual(self.table.current_status, 'BLUE')
    
    # =========================================================================
    # TEST: Wait Time Properties
    # =========================================================================
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_wait_time_calculation(self, mock_channel_layer):
        """Test wait_time_minutes property calculation."""
        mock_channel_layer.return_value = MagicMock()
        
        # Create order
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        
        # Manually set placed_at to 10 minutes ago
        order.placed_at = timezone.now() - timedelta(minutes=10)
        order.save()
        
        # Check wait time (should be ~10 minutes)
        self.assertGreaterEqual(order.wait_time_minutes, 9)
        self.assertLessEqual(order.wait_time_minutes, 11)
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_is_long_wait_property(self, mock_channel_layer):
        """Test is_long_wait property for orders > 15 minutes."""
        mock_channel_layer.return_value = MagicMock()
        
        # Create order
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        
        # Short wait (should not be long wait)
        order.placed_at = timezone.now() - timedelta(minutes=5)
        order.save()
        self.assertFalse(order.is_long_wait)
        
        # Long wait (should be long wait)
        order.placed_at = timezone.now() - timedelta(minutes=20)
        order.save()
        self.assertTrue(order.is_long_wait)


class CheckWaitTimesCommandTestCase(TestCase):
    """Test the check_wait_times management command."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.brand = Brand.objects.create(
            name='Test Brand',
            corporate_id='TEST002',
            contact_email='test@brand.com'
        )
        cls.outlet = Outlet.objects.create(
            brand=cls.brand,
            name='Test Outlet',
            address='456 Test Ave',
            city='Test City',
            seating_capacity=30,
            opening_time='09:00:00',
            closing_time='22:00:00'
        )
        cls.user = User.objects.create_user(
            username='cmd_test_waiter',
            password='testpass'
        )
        cls.waiter = UserProfile.objects.create(
            user=cls.user,
            outlet=cls.outlet,
            role='WAITER'
        )
    
    def setUp(self):
        """Set up fresh table and order."""
        self.table = ServiceNode.objects.create(
            outlet=self.outlet,
            name='Table-CMD-Test',
            node_type='TABLE',
            current_status='YELLOW'
        )
    
    def tearDown(self):
        """Clean up."""
        OrderTicket.objects.all().delete()
        ServiceNode.objects.filter(name='Table-CMD-Test').delete()
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_check_wait_times_marks_table_red(self, mock_channel_layer):
        """Management command should mark long-waiting tables RED."""
        from django.core.management import call_command
        from io import StringIO
        
        mock_channel_layer.return_value = MagicMock()
        
        # Create order placed 20 minutes ago
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        order.placed_at = timezone.now() - timedelta(minutes=20)
        order.save()
        
        # Run command
        out = StringIO()
        call_command('check_wait_times', stdout=out)
        
        # Refresh table
        self.table.refresh_from_db()
        
        # Table should be RED
        self.assertEqual(self.table.current_status, 'RED')
    
    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_check_wait_times_dry_run(self, mock_channel_layer):
        """Dry run should not update tables."""
        from django.core.management import call_command
        from io import StringIO
        
        mock_channel_layer.return_value = MagicMock()
        
        # Create order placed 20 minutes ago
        order = OrderTicket.objects.create(
            table=self.table,
            waiter=self.waiter,
            status='PLACED'
        )
        order.placed_at = timezone.now() - timedelta(minutes=20)
        order.save()
        
        # Run command with dry-run
        out = StringIO()
        call_command('check_wait_times', '--dry-run', stdout=out)
        
        # Refresh table
        self.table.refresh_from_db()
        
        # Table should still be YELLOW (not updated)
        self.assertEqual(self.table.current_status, 'YELLOW')
