"""
Smoke test for ML predictions using Django's test infrastructure.
Run: python manage.py test apps.predictive_core.tests.test_ml_predictions --verbosity=2
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status


class PredictionEndpointTests(TestCase):
    """Test all 8 prediction API endpoints."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='test_ml_user', password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_busy_hours_endpoint(self):
        resp = self.client.get('/api/predictions/busy-hours/?outlet=4&date=2026-03-04')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('hourly_forecast', data)
        self.assertIn('peak_hour', data)
        print(f"  busy-hours: peak_hour={data.get('peak_hour')}, total={data.get('total_predicted_orders')}")

    def test_footfall_endpoint(self):
        resp = self.client.get('/api/predictions/footfall/?outlet=4&date=2026-03-04')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('hourly_guests', data)
        print(f"  footfall: total_guests={data.get('total_predicted_guests')}")

    def test_food_demand_endpoint(self):
        resp = self.client.get('/api/predictions/food-demand/?outlet=4&date=2026-03-04')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('category_forecast', data)
        print(f"  food-demand: categories={list(data.get('category_forecast', {}).keys())}")

    def test_inventory_alerts_endpoint(self):
        resp = self.client.get('/api/predictions/inventory-alerts/?outlet=4')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('inventory_alerts', data)
        print(f"  inventory: alerts={data.get('total_alerts')}, critical={data.get('total_critical')}")

    def test_staffing_endpoint(self):
        resp = self.client.get('/api/predictions/staffing/?outlet=4&date=2026-03-04')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        # May return fallback if outlet doesn't exist in test DB
        if 'error' in data:
            self.assertTrue(data.get('fallback'))
            print(f"  staffing: graceful fallback (no outlet in test DB)")
        else:
            self.assertIn('staffing_recommendation', data)
            print(f"  staffing: total_staff={data.get('total_staff_needed')}")

    def test_revenue_endpoint(self):
        resp = self.client.get('/api/predictions/revenue/?outlet=4&date=2026-03-04')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('next_day', data)
        print(f"  revenue: next_day={data.get('next_day', {}).get('predicted_revenue')}")

    def test_dashboard_endpoint(self):
        resp = self.client.get('/api/predictions/dashboard/?outlet=4&date=2026-03-04')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        expected_keys = ['busy_hours', 'footfall', 'food_demand', 'inventory_alerts', 'staffing', 'revenue']
        for key in expected_keys:
            self.assertIn(key, data, f"Missing key: {key}")
        print(f"  dashboard: all 6 predictions present")

    def test_train_endpoint(self):
        resp = self.client.post('/api/predictions/train/?outlet=4&sync=true')
        # sync=true runs training in-request; returns 200
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_202_ACCEPTED])
        data = resp.json()
        self.assertIn('results', data)
        print(f"  train: status={data.get('status')}")

    def test_missing_outlet_param(self):
        resp = self.client.get('/api/predictions/busy-hours/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_date_format(self):
        resp = self.client.get('/api/predictions/busy-hours/?outlet=4&date=invalid')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
