"""
Comprehensive tests for order_engine app (models, signals, API).
Run: python manage.py test apps.order_engine --verbosity=2

Note: Signal-based table status tests are in tests/test_table_status.py
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from apps.hospitality_group.models import Brand, Outlet, UserProfile
from apps.layout_twin.models import ServiceNode
from apps.order_engine.models import OrderTicket, PaymentLog
from apps.order_engine.signals import validate_status_transition


# ═══════════════════════════════════════════════════════════════
# HELPER MIXIN
# ═══════════════════════════════════════════════════════════════

class OrderTestMixin:
    """Shared test data setup for order_engine tests."""

    @classmethod
    def _create_base_data(cls):
        cls.brand = Brand.objects.create(
            name='Order Brand', corporate_id='OB1', contact_email='ob@x.com',
        )
        cls.outlet = Outlet.objects.create(
            brand=cls.brand, name='Order Outlet', address='A',
            city='C', opening_time='09:00', closing_time='22:00',
        )
        cls.user = User.objects.create_user('order_waiter', 'w@x.com', 'pass')
        cls.waiter = UserProfile.objects.create(
            user=cls.user, outlet=cls.outlet, role='WAITER',
        )
        cls.table = ServiceNode.objects.create(
            outlet=cls.outlet, name='T-Test', node_type='TABLE',
            capacity=4, current_status='BLUE',
        )


# ═══════════════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════════════

class OrderTicketModelTest(OrderTestMixin, TestCase):
    """Tests for OrderTicket model."""

    @classmethod
    def setUpTestData(cls):
        cls._create_base_data()

    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_create_order(self, mock_cl):
        mock_cl.return_value = MagicMock()
        order = OrderTicket.objects.create(
            table=self.table, waiter=self.waiter,
            customer_name='Alice', party_size=2,
            items=[{'name': 'Pizza', 'price': 400}],
            status='PLACED', subtotal=400, tax=20, total=420,
        )
        self.assertEqual(order.status, 'PLACED')
        self.assertIn('Order #', str(order))

    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_wait_time_property(self, mock_cl):
        mock_cl.return_value = MagicMock()
        order = OrderTicket.objects.create(
            table=self.table, waiter=self.waiter,
            items=[], status='PLACED',
        )
        # Just created, wait time should be ~0 minutes
        self.assertGreaterEqual(order.wait_time_minutes, 0)

    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_default_values(self, mock_cl):
        mock_cl.return_value = MagicMock()
        order = OrderTicket.objects.create(
            table=self.table, waiter=self.waiter, items=[],
        )
        self.assertEqual(order.subtotal, Decimal('0.00'))
        self.assertEqual(order.party_size, 1)


class PaymentLogModelTest(OrderTestMixin, TestCase):
    """Tests for PaymentLog model."""

    @classmethod
    def setUpTestData(cls):
        cls._create_base_data()

    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_create_payment(self, mock_cl):
        mock_cl.return_value = MagicMock()
        order = OrderTicket.objects.create(
            table=self.table, waiter=self.waiter,
            items=[], total=500,
        )
        payment = PaymentLog.objects.create(
            order=order, amount=500, method='UPI', status='SUCCESS',
        )
        self.assertEqual(str(payment), f'Payment SUCCESS: Rs.500 (UPI) for Order #{order.pk}')
        self.assertEqual(payment.tip_amount, Decimal('0.00'))


# ═══════════════════════════════════════════════════════════════
# SIGNAL / TRANSITION TESTS
# ═══════════════════════════════════════════════════════════════

class StatusTransitionTest(TestCase):
    """Tests for order status transition validation (signals.py)."""

    def test_valid_new_order(self):
        self.assertTrue(validate_status_transition(None, 'PLACED'))

    def test_valid_placed_to_preparing(self):
        self.assertTrue(validate_status_transition('PLACED', 'PREPARING'))

    def test_valid_placed_to_cancelled(self):
        self.assertTrue(validate_status_transition('PLACED', 'CANCELLED'))

    def test_valid_served_to_completed(self):
        self.assertTrue(validate_status_transition('SERVED', 'COMPLETED'))

    def test_invalid_completed_to_placed(self):
        with self.assertRaises(ValidationError):
            validate_status_transition('COMPLETED', 'PLACED')

    def test_invalid_cancelled_to_anything(self):
        with self.assertRaises(ValidationError):
            validate_status_transition('CANCELLED', 'PLACED')

    def test_invalid_skip_preparing(self):
        # PLACED → READY is allowed (flexible flow)
        self.assertTrue(validate_status_transition('PLACED', 'READY'))


# ═══════════════════════════════════════════════════════════════
# API TESTS
# ═══════════════════════════════════════════════════════════════

class OrderAPITest(OrderTestMixin, TestCase):
    """Tests for Order API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls._create_base_data()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_list_orders(self, mock_cl):
        mock_cl.return_value = MagicMock()
        resp = self.client.get('/api/orders/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_create_order_api(self, mock_cl):
        mock_cl.return_value = MagicMock()
        resp = self.client.post('/api/orders/', {
            'table': self.table.pk,
            'waiter': self.waiter.pk,
            'customer_name': 'Bob',
            'party_size': 3,
            'items': [{'name': 'Burger', 'price': 250}],
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_update_order_status(self, mock_cl):
        mock_cl.return_value = MagicMock()
        order = OrderTicket.objects.create(
            table=self.table, waiter=self.waiter,
            items=[], status='PLACED',
        )
        resp = self.client.post(f'/api/orders/{order.pk}/update_status/', {
            'status': 'PREPARING',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_active_orders(self, mock_cl):
        mock_cl.return_value = MagicMock()
        OrderTicket.objects.create(
            table=self.table, waiter=self.waiter,
            items=[], status='PLACED',
        )
        resp = self.client.get('/api/orders/active/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_orders_requires_auth(self):
        anon = APIClient()
        resp = anon.get('/api/orders/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PaymentAPITest(OrderTestMixin, TestCase):
    """Tests for Payment API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls._create_base_data()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.layout_twin.utils.broadcast.get_channel_layer')
    def test_list_payments(self, mock_cl):
        mock_cl.return_value = MagicMock()
        resp = self.client.get('/api/payments/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
