"""
Tests for predictive_core app – models, properties, and CRUD viewset API.
ML prediction endpoint smoke tests live in tests/test_ml_predictions.py.
"""
from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.hospitality_group.models import Brand, Outlet, UserProfile
from apps.predictive_core.models import SalesData, InventoryItem, StaffSchedule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class PredictiveTestMixin:
    """Shared setup for predictive_core tests."""

    def setUp(self):
        self.user = User.objects.create_user(username='pc_user', password='pass1234')
        self.brand = Brand.objects.create(
            name='PC Brand', corporate_id='PC001', contact_email='pc@test.com',
        )
        self.outlet = Outlet.objects.create(
            brand=self.brand,
            name='PC Outlet',
            city='Mumbai',
            address='Test Rd',
            opening_time='09:00',
            closing_time='22:00',
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            outlet=self.outlet,
            role='MANAGER',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------
class SalesDataModelTest(PredictiveTestMixin, TestCase):

    def test_create_sales_data(self):
        sd = SalesData.objects.create(
            outlet=self.outlet,
            date=date.today(),
            hour=14,
            total_orders=50,
            total_revenue=Decimal('12500.00'),
            avg_ticket_size=Decimal('250.00'),
            day_of_week=date.today().weekday(),
        )
        self.assertEqual(str(sd), f"{self.outlet.name} - {date.today()} 14:00 - Rs.12500.00")

    def test_unique_together_outlet_date_hour(self):
        SalesData.objects.create(outlet=self.outlet, date=date.today(), hour=10, day_of_week=0)
        with self.assertRaises(Exception):
            SalesData.objects.create(outlet=self.outlet, date=date.today(), hour=10, day_of_week=0)

    def test_json_defaults(self):
        sd = SalesData.objects.create(outlet=self.outlet, date=date.today(), hour=0, day_of_week=0)
        self.assertEqual(sd.category_sales, {})
        self.assertEqual(sd.top_items, [])


class InventoryItemModelTest(PredictiveTestMixin, TestCase):

    def test_create_item(self):
        item = InventoryItem.objects.create(
            outlet=self.outlet,
            name='Tomatoes',
            category='PRODUCE',
            unit='KG',
            current_quantity=25.0,
            reorder_threshold=10.0,
            par_level=50.0,
            unit_cost=Decimal('60.00'),
        )
        self.assertIn('Tomatoes', str(item))
        self.assertIn('OK', str(item))

    def test_is_low_stock_true(self):
        item = InventoryItem.objects.create(
            outlet=self.outlet,
            name='Butter',
            category='DAIRY',
            current_quantity=5.0,
            reorder_threshold=10.0,
        )
        self.assertTrue(item.is_low_stock)
        self.assertIn('LOW', str(item))

    def test_is_low_stock_false(self):
        item = InventoryItem.objects.create(
            outlet=self.outlet,
            name='Rice',
            category='DRY',
            current_quantity=100.0,
            reorder_threshold=10.0,
        )
        self.assertFalse(item.is_low_stock)

    def test_unique_together_outlet_name(self):
        InventoryItem.objects.create(outlet=self.outlet, name='Salt')
        with self.assertRaises(Exception):
            InventoryItem.objects.create(outlet=self.outlet, name='Salt')


class StaffScheduleModelTest(PredictiveTestMixin, TestCase):

    def test_create_schedule(self):
        sched = StaffSchedule.objects.create(
            staff=self.profile,
            date=date.today(),
            shift='MORNING',
            start_time=time(6, 0),
            end_time=time(14, 0),
        )
        self.assertIn('MORNING', str(sched))

    def test_unique_together_staff_date_shift(self):
        StaffSchedule.objects.create(
            staff=self.profile, date=date.today(), shift='MORNING',
            start_time=time(6, 0), end_time=time(14, 0),
        )
        with self.assertRaises(Exception):
            StaffSchedule.objects.create(
                staff=self.profile, date=date.today(), shift='MORNING',
                start_time=time(6, 0), end_time=time(14, 0),
            )

    def test_ai_suggested_default_false(self):
        sched = StaffSchedule.objects.create(
            staff=self.profile, date=date.today(), shift='NIGHT',
            start_time=time(22, 0), end_time=time(6, 0),
        )
        self.assertFalse(sched.is_ai_suggested)


# ---------------------------------------------------------------------------
# API tests – SalesData
# ---------------------------------------------------------------------------
class SalesDataAPITest(PredictiveTestMixin, TestCase):

    def test_list_empty(self):
        resp = self.client.get('/api/sales-data/')
        self.assertEqual(resp.status_code, 200)

    def test_create(self):
        resp = self.client.post('/api/sales-data/', {
            'outlet': self.outlet.pk,
            'date': str(date.today()),
            'hour': 12,
            'total_orders': 30,
            'total_revenue': '8000.00',
            'avg_ticket_size': '266.67',
            'day_of_week': date.today().weekday(),
        })
        self.assertEqual(resp.status_code, 201)

    def test_trends_action(self):
        SalesData.objects.create(
            outlet=self.outlet, date=date.today(), hour=10,
            total_orders=10, total_revenue=Decimal('2000'), day_of_week=0,
        )
        resp = self.client.get('/api/sales-data/trends/', {'outlet': self.outlet.pk, 'days': 7})
        self.assertEqual(resp.status_code, 200)

    def test_hourly_pattern_action(self):
        resp = self.client.get('/api/sales-data/hourly_pattern/')
        self.assertEqual(resp.status_code, 200)

    def test_unauthenticated(self):
        client = APIClient()
        resp = client.get('/api/sales-data/')
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# API tests – Inventory
# ---------------------------------------------------------------------------
class InventoryAPITest(PredictiveTestMixin, TestCase):

    def test_list(self):
        resp = self.client.get('/api/inventory/')
        self.assertEqual(resp.status_code, 200)

    def test_create(self):
        resp = self.client.post('/api/inventory/', {
            'outlet': self.outlet.pk,
            'name': 'Flour',
            'category': 'DRY',
            'unit': 'KG',
            'current_quantity': 100,
            'reorder_threshold': 20,
            'par_level': 80,
            'unit_cost': '45.00',
        })
        self.assertEqual(resp.status_code, 201)

    def test_low_stock_action(self):
        InventoryItem.objects.create(
            outlet=self.outlet, name='Milk', category='DAIRY',
            current_quantity=2, reorder_threshold=10,
        )
        resp = self.client.get('/api/inventory/low_stock/')
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# API tests – Schedules
# ---------------------------------------------------------------------------
class ScheduleAPITest(PredictiveTestMixin, TestCase):

    def test_list(self):
        resp = self.client.get('/api/schedules/')
        self.assertEqual(resp.status_code, 200)

    def test_create(self):
        resp = self.client.post('/api/schedules/', {
            'staff': self.profile.pk,
            'date': str(date.today()),
            'shift': 'AFTERNOON',
            'start_time': '14:00',
            'end_time': '22:00',
        })
        self.assertEqual(resp.status_code, 201)
