"""
Comprehensive tests for hospitality_group app.
Run: python manage.py test apps.hospitality_group --verbosity=2
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.hospitality_group.models import Brand, Outlet, UserProfile
from apps.hospitality_group.permissions import (
    IsOutletUser, IsManagerOrReadOnly, IsManager, IsStaffOrManager,
)


# ════════════════════════════════════════════════════════════════
# MODEL TESTS
# ════════════════════════════════════════════════════════════════

class BrandModelTest(TestCase):
    """Tests for Brand model."""

    def test_create_brand(self):
        brand = Brand.objects.create(
            name='Test Brand', corporate_id='TB001',
            contact_email='test@brand.com', subscription_tier='PRO',
        )
        self.assertEqual(str(brand), 'Test Brand (TB001)')
        self.assertEqual(brand.subscription_tier, 'PRO')

    def test_corporate_id_unique(self):
        Brand.objects.create(
            name='Brand A', corporate_id='UNIQUE1', contact_email='a@x.com',
        )
        with self.assertRaises(Exception):
            Brand.objects.create(
                name='Brand B', corporate_id='UNIQUE1', contact_email='b@x.com',
            )

    def test_default_subscription_tier(self):
        brand = Brand.objects.create(
            name='Default Brand', corporate_id='DEF1', contact_email='d@x.com',
        )
        self.assertEqual(brand.subscription_tier, 'BASIC')

    def test_ordering(self):
        Brand.objects.create(name='Zebra', corporate_id='Z1', contact_email='z@x.com')
        Brand.objects.create(name='Alpha', corporate_id='A1', contact_email='a@x.com')
        brands = list(Brand.objects.values_list('name', flat=True))
        self.assertEqual(brands, ['Alpha', 'Zebra'])


class OutletModelTest(TestCase):
    """Tests for Outlet model."""

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(
            name='Test Brand', corporate_id='TB001', contact_email='t@x.com',
        )

    def test_create_outlet(self):
        outlet = Outlet.objects.create(
            brand=self.brand, name='Downtown', address='123 Main St',
            city='Mumbai', seating_capacity=50,
            opening_time='09:00', closing_time='22:00',
        )
        self.assertIn('Downtown', str(outlet))
        self.assertTrue(outlet.is_active)

    def test_unique_together_brand_name(self):
        Outlet.objects.create(
            brand=self.brand, name='Same Name', address='Addr1',
            city='City', opening_time='09:00', closing_time='22:00',
        )
        with self.assertRaises(Exception):
            Outlet.objects.create(
                brand=self.brand, name='Same Name', address='Addr2',
                city='City', opening_time='09:00', closing_time='22:00',
            )


class UserProfileModelTest(TestCase):
    """Tests for UserProfile model."""

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(
            name='Brand', corporate_id='B1', contact_email='b@x.com',
        )
        cls.outlet = Outlet.objects.create(
            brand=cls.brand, name='Outlet', address='Addr',
            city='City', opening_time='09:00', closing_time='22:00',
        )
        cls.user = User.objects.create_user('testuser', 'u@x.com', 'pass1234')

    def test_create_profile(self):
        profile = UserProfile.objects.create(
            user=self.user, outlet=self.outlet, role='WAITER',
        )
        self.assertEqual(profile.role, 'WAITER')
        self.assertFalse(profile.is_on_shift)

    def test_one_to_one_constraint(self):
        UserProfile.objects.create(user=self.user, outlet=self.outlet)
        user2 = User.objects.create_user('u2', 'u2@x.com', 'pass')
        # Should work for different user
        UserProfile.objects.create(user=user2, outlet=self.outlet)
        # Same user again should fail
        with self.assertRaises(Exception):
            UserProfile.objects.create(
                user=self.user, outlet=self.outlet, role='CHEF',
            )


# ════════════════════════════════════════════════════════════════
# PERMISSION TESTS
# ════════════════════════════════════════════════════════════════

class PermissionTestCase(TestCase):
    """Tests for custom permission classes."""

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(
            name='Perm Brand', corporate_id='PB1', contact_email='p@x.com',
        )
        cls.outlet1 = Outlet.objects.create(
            brand=cls.brand, name='Outlet1', address='A1',
            city='C1', opening_time='09:00', closing_time='22:00',
        )
        cls.outlet2 = Outlet.objects.create(
            brand=cls.brand, name='Outlet2', address='A2',
            city='C2', opening_time='09:00', closing_time='22:00',
        )
        cls.manager_user = User.objects.create_user('mgr', 'mgr@x.com', 'pass')
        cls.waiter_user = User.objects.create_user('wtr', 'wtr@x.com', 'pass')
        cls.superuser = User.objects.create_superuser('admin', 'a@x.com', 'pass')

        UserProfile.objects.create(
            user=cls.manager_user, outlet=cls.outlet1, role='MANAGER',
        )
        UserProfile.objects.create(
            user=cls.waiter_user, outlet=cls.outlet1, role='WAITER',
        )

    def test_is_outlet_user_same_outlet(self):
        perm = IsOutletUser()
        request = type('Req', (), {'user': self.manager_user, 'method': 'GET'})()
        self.assertTrue(perm.has_object_permission(request, None, self.outlet1))

    def test_is_outlet_user_different_outlet(self):
        perm = IsOutletUser()
        request = type('Req', (), {'user': self.manager_user, 'method': 'GET'})()
        self.assertFalse(perm.has_object_permission(request, None, self.outlet2))

    def test_is_outlet_user_superuser_bypass(self):
        perm = IsOutletUser()
        request = type('Req', (), {'user': self.superuser, 'method': 'GET'})()
        self.assertTrue(perm.has_object_permission(request, None, self.outlet2))

    def test_is_manager_or_readonly_allows_read(self):
        perm = IsManagerOrReadOnly()
        request = type('Req', (), {
            'user': self.waiter_user, 'method': 'GET',
        })()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_manager_or_readonly_blocks_write(self):
        perm = IsManagerOrReadOnly()
        request = type('Req', (), {
            'user': self.waiter_user, 'method': 'POST',
        })()
        self.assertFalse(perm.has_permission(request, None))

    def test_is_manager_allows_manager_write(self):
        perm = IsManager()
        request = type('Req', (), {
            'user': self.manager_user, 'method': 'POST',
        })()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_manager_blocks_waiter(self):
        perm = IsManager()
        request = type('Req', (), {
            'user': self.waiter_user, 'method': 'POST',
        })()
        self.assertFalse(perm.has_permission(request, None))


# ════════════════════════════════════════════════════════════════
# API / VIEW TESTS
# ════════════════════════════════════════════════════════════════

class AuthAPITest(TestCase):
    """Tests for authentication endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        brand = Brand.objects.create(
            name='Reg Brand', corporate_id='RG1', contact_email='rg@test.com',
        )
        outlet = Outlet.objects.create(
            brand=brand, name='Reg Outlet', address='A', city='C',
            opening_time='09:00', closing_time='22:00',
        )
        resp = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'password': 'StrongPass123!',
            'email': 'new@test.com',
            'outlet': outlet.pk,
            'role': 'WAITER',
        }, format='json')
        self.assertIn(resp.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

    def test_register_duplicate_username(self):
        User.objects.create_user('existing', 'e@x.com', 'pass')
        brand = Brand.objects.create(
            name='Dup Brand', corporate_id='DUP1', contact_email='dup@test.com',
        )
        outlet = Outlet.objects.create(
            brand=brand, name='Dup Outlet', address='A', city='C',
            opening_time='09:00', closing_time='22:00',
        )
        resp = self.client.post('/api/auth/register/', {
            'username': 'existing',
            'password': 'StrongPass123!',
            'email': 'dup@test.com',
            'outlet': outlet.pk,
            'role': 'WAITER',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_obtain_token(self):
        User.objects.create_user('loginuser', 'l@x.com', 'TestPass123!')
        resp = self.client.post('/api/auth/token/', {
            'username': 'loginuser', 'password': 'TestPass123!',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_login_wrong_password(self):
        User.objects.create_user('loginuser', 'l@x.com', 'TestPass123!')
        resp = self.client.post('/api/auth/token/', {
            'username': 'loginuser', 'password': 'WrongPass',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        User.objects.create_user('refreshuser', 'r@x.com', 'TestPass123!')
        login = self.client.post('/api/auth/token/', {
            'username': 'refreshuser', 'password': 'TestPass123!',
        }, format='json')
        resp = self.client.post('/api/auth/token/refresh/', {
            'refresh': login.data['refresh'],
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

    def test_profile_requires_auth(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_authenticated(self):
        user = User.objects.create_user('profuser', 'p@x.com', 'TestPass123!')
        brand = Brand.objects.create(
            name='B', corporate_id='B1', contact_email='b@x.com',
        )
        outlet = Outlet.objects.create(
            brand=brand, name='O', address='A', city='C',
            opening_time='09:00', closing_time='22:00',
        )
        UserProfile.objects.create(user=user, outlet=outlet, role='WAITER')
        self.client.force_authenticate(user=user)
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_change_password(self):
        user = User.objects.create_user('chguser', 'c@x.com', 'OldPass123!')
        brand = Brand.objects.create(
            name='B2', corporate_id='B2', contact_email='b2@x.com',
        )
        outlet = Outlet.objects.create(
            brand=brand, name='O2', address='A', city='C',
            opening_time='09:00', closing_time='22:00',
        )
        UserProfile.objects.create(user=user, outlet=outlet)
        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/auth/change-password/', {
            'old_password': 'OldPass123!',
            'new_password': 'NewSecure456!',
        }, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])


class BrandViewSetTest(TestCase):
    """Tests for Brand CRUD endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('branduser', 'b@x.com', 'pass')
        self.client.force_authenticate(user=self.user)

    def test_list_brands(self):
        Brand.objects.create(
            name='List Brand', corporate_id='LB1', contact_email='l@x.com',
        )
        resp = self.client.get('/api/brands/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_brand(self):
        resp = self.client.post('/api/brands/', {
            'name': 'New Brand',
            'corporate_id': 'NB1',
            'contact_email': 'nb@x.com',
            'subscription_tier': 'PRO',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_brand(self):
        brand = Brand.objects.create(
            name='Ret Brand', corporate_id='RB1', contact_email='r@x.com',
        )
        resp = self.client.get(f'/api/brands/{brand.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], 'Ret Brand')

    def test_update_brand(self):
        brand = Brand.objects.create(
            name='Upd Brand', corporate_id='UB1', contact_email='u@x.com',
        )
        resp = self.client.patch(f'/api/brands/{brand.pk}/', {
            'subscription_tier': 'ENTERPRISE',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        brand.refresh_from_db()
        self.assertEqual(brand.subscription_tier, 'ENTERPRISE')

    def test_delete_brand(self):
        brand = Brand.objects.create(
            name='Del Brand', corporate_id='DB1', contact_email='d@x.com',
        )
        resp = self.client.delete(f'/api/brands/{brand.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Brand.objects.filter(pk=brand.pk).exists())


class OutletViewSetTest(TestCase):
    """Tests for Outlet CRUD endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('outletuser', 'o@x.com', 'pass')
        self.client.force_authenticate(user=self.user)
        self.brand = Brand.objects.create(
            name='Outlet Brand', corporate_id='OB1', contact_email='ob@x.com',
        )

    def test_list_outlets(self):
        resp = self.client.get('/api/outlets/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_outlet(self):
        resp = self.client.post('/api/outlets/', {
            'brand': self.brand.pk,
            'name': 'New Outlet',
            'address': 'Address',
            'city': 'City',
            'seating_capacity': 40,
            'opening_time': '09:00:00',
            'closing_time': '22:00:00',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_outlet(self):
        outlet = Outlet.objects.create(
            brand=self.brand, name='Get Outlet', address='A',
            city='C', opening_time='09:00', closing_time='22:00',
        )
        resp = self.client.get(f'/api/outlets/{outlet.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class UnauthenticatedAccessTest(TestCase):
    """Tests that unauthenticated access is blocked on protected endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_brands_requires_auth(self):
        resp = self.client.get('/api/brands/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_outlets_requires_auth(self):
        resp = self.client.get('/api/outlets/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_requires_auth(self):
        resp = self.client.get('/api/staff/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)