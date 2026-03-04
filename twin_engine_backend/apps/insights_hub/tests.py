"""
Tests for insights_hub app – DailySummary & PDFReport models, and CRUD API.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.hospitality_group.models import Brand, Outlet, UserProfile
from apps.insights_hub.models import DailySummary, PDFReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class InsightsTestMixin:
    """Shared setup for insights_hub tests."""

    def setUp(self):
        self.user = User.objects.create_user(username='ih_user', password='pass1234')
        self.brand = Brand.objects.create(
            name='IH Brand', corporate_id='IH001', contact_email='ih@test.com',
        )
        self.outlet = Outlet.objects.create(
            brand=self.brand,
            name='IH Outlet',
            city='Delhi',
            address='Test Ave',
            opening_time='09:00',
            closing_time='22:00',
        )
        UserProfile.objects.create(
            user=self.user,
            outlet=self.outlet,
            role='MANAGER',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


# ---------------------------------------------------------------------------
# Model tests – DailySummary
# ---------------------------------------------------------------------------
class DailySummaryModelTest(InsightsTestMixin, TestCase):

    def test_create(self):
        ds = DailySummary.objects.create(
            outlet=self.outlet,
            date=date.today(),
            total_revenue=Decimal('45000.00'),
            total_orders=120,
            avg_ticket_size=Decimal('375.00'),
            total_guests=200,
        )
        self.assertIn(self.outlet.name, str(ds))
        self.assertIn('45000', str(ds))

    def test_unique_together_outlet_date(self):
        DailySummary.objects.create(outlet=self.outlet, date=date.today())
        with self.assertRaises(Exception):
            DailySummary.objects.create(outlet=self.outlet, date=date.today())

    def test_json_defaults(self):
        ds = DailySummary.objects.create(outlet=self.outlet, date=date.today())
        self.assertEqual(ds.sales_by_category, {})
        self.assertEqual(ds.top_selling_items, [])

    def test_ordering(self):
        DailySummary.objects.create(outlet=self.outlet, date=date.today() - timedelta(days=1))
        DailySummary.objects.create(outlet=self.outlet, date=date.today())
        qs = DailySummary.objects.all()
        self.assertGreater(qs.first().date, qs.last().date)


# ---------------------------------------------------------------------------
# Model tests – PDFReport
# ---------------------------------------------------------------------------
class PDFReportModelTest(InsightsTestMixin, TestCase):

    def test_create(self):
        report = PDFReport.objects.create(
            outlet=self.outlet,
            report_type='DAILY',
            start_date=date.today(),
            end_date=date.today(),
        )
        self.assertEqual(report.status, 'PENDING')
        self.assertIn('DAILY', str(report))

    def test_status_choices(self):
        report = PDFReport.objects.create(
            outlet=self.outlet,
            report_type='WEEKLY',
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            status='COMPLETED',
            gpt_summary='Good week overall.',
        )
        self.assertEqual(report.status, 'COMPLETED')
        self.assertEqual(report.generated_by, 'GPT-4')

    def test_insights_and_recommendations_default(self):
        report = PDFReport.objects.create(
            outlet=self.outlet,
            report_type='MONTHLY',
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )
        self.assertEqual(report.insights, [])
        self.assertEqual(report.recommendations, [])


# ---------------------------------------------------------------------------
# API tests – DailySummary
# ---------------------------------------------------------------------------
class DailySummaryAPITest(InsightsTestMixin, TestCase):

    def test_list(self):
        resp = self.client.get('/api/summaries/')
        self.assertEqual(resp.status_code, 200)

    def test_create(self):
        resp = self.client.post('/api/summaries/', {
            'outlet': self.outlet.pk,
            'date': str(date.today()),
            'total_revenue': '30000.00',
            'total_orders': 80,
        })
        self.assertEqual(resp.status_code, 201)

    def test_retrieve(self):
        ds = DailySummary.objects.create(outlet=self.outlet, date=date.today())
        resp = self.client.get(f'/api/summaries/{ds.pk}/')
        self.assertEqual(resp.status_code, 200)

    def test_trends_action(self):
        DailySummary.objects.create(
            outlet=self.outlet, date=date.today(),
            total_revenue=Decimal('10000'), total_orders=50,
        )
        resp = self.client.get('/api/summaries/trends/', {'outlet': self.outlet.pk, 'days': 7})
        self.assertEqual(resp.status_code, 200)

    def test_unauthenticated(self):
        client = APIClient()
        resp = client.get('/api/summaries/')
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# API tests – PDFReport
# ---------------------------------------------------------------------------
class PDFReportAPITest(InsightsTestMixin, TestCase):

    def test_list(self):
        resp = self.client.get('/api/reports/')
        self.assertEqual(resp.status_code, 200)

    def test_retrieve(self):
        report = PDFReport.objects.create(
            outlet=self.outlet,
            report_type='DAILY',
            start_date=date.today(),
            end_date=date.today(),
        )
        resp = self.client.get(f'/api/reports/{report.pk}/')
        self.assertEqual(resp.status_code, 200)
