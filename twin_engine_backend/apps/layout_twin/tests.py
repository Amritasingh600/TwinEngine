"""
Comprehensive tests for layout_twin app (models, serializers, API).
Run: python manage.py test apps.layout_twin --verbosity=2
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.hospitality_group.models import Brand, Outlet
from apps.layout_twin.models import ServiceNode, ServiceFlow


# ═══════════════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════════════

class ServiceNodeModelTest(TestCase):
    """Tests for ServiceNode model."""

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(
            name='Layout Brand', corporate_id='LB1', contact_email='lb@x.com',
        )
        cls.outlet = Outlet.objects.create(
            brand=cls.brand, name='Layout Outlet', address='A',
            city='C', opening_time='09:00', closing_time='22:00',
        )

    def test_create_table_node(self):
        node = ServiceNode.objects.create(
            outlet=self.outlet, name='Table-1', node_type='TABLE',
            capacity=4, current_status='BLUE',
        )
        self.assertEqual(node.node_type, 'TABLE')
        self.assertEqual(node.current_status, 'BLUE')
        self.assertIn('Table-1', str(node))

    def test_create_kitchen_node(self):
        node = ServiceNode.objects.create(
            outlet=self.outlet, name='Kitchen-Main', node_type='KITCHEN',
        )
        self.assertEqual(node.node_type, 'KITCHEN')

    def test_default_position(self):
        node = ServiceNode.objects.create(
            outlet=self.outlet, name='Node-Default', node_type='TABLE',
        )
        self.assertEqual(node.pos_x, 0.0)
        self.assertEqual(node.pos_y, 0.0)
        self.assertEqual(node.pos_z, 0.0)

    def test_unique_together_outlet_name(self):
        ServiceNode.objects.create(
            outlet=self.outlet, name='DuplicateNode', node_type='TABLE',
        )
        with self.assertRaises(Exception):
            ServiceNode.objects.create(
                outlet=self.outlet, name='DuplicateNode', node_type='BAR',
            )

    def test_status_choices(self):
        for code, _ in ServiceNode.STATUS_CHOICES:
            node = ServiceNode.objects.create(
                outlet=self.outlet, name=f'Node-{code}',
                node_type='TABLE', current_status=code,
            )
            self.assertEqual(node.current_status, code)


class ServiceFlowModelTest(TestCase):
    """Tests for ServiceFlow model."""

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(
            name='Flow Brand', corporate_id='FB1', contact_email='fb@x.com',
        )
        cls.outlet = Outlet.objects.create(
            brand=cls.brand, name='Flow Outlet', address='A',
            city='C', opening_time='09:00', closing_time='22:00',
        )
        cls.kitchen = ServiceNode.objects.create(
            outlet=cls.outlet, name='Kitchen-Main', node_type='KITCHEN',
        )
        cls.table = ServiceNode.objects.create(
            outlet=cls.outlet, name='Table-1', node_type='TABLE',
        )

    def test_create_flow(self):
        flow = ServiceFlow.objects.create(
            source_node=self.kitchen, target_node=self.table,
            flow_type='FOOD_DELIVERY',
        )
        self.assertIn('→', str(flow))
        self.assertTrue(flow.is_active)

    def test_unique_together(self):
        ServiceFlow.objects.create(
            source_node=self.kitchen, target_node=self.table,
            flow_type='FOOD_DELIVERY',
        )
        with self.assertRaises(Exception):
            ServiceFlow.objects.create(
                source_node=self.kitchen, target_node=self.table,
                flow_type='FOOD_DELIVERY',
            )

    def test_different_flow_types_allowed(self):
        ServiceFlow.objects.create(
            source_node=self.kitchen, target_node=self.table,
            flow_type='FOOD_DELIVERY',
        )
        flow2 = ServiceFlow.objects.create(
            source_node=self.kitchen, target_node=self.table,
            flow_type='ORDER_PATH',
        )
        self.assertEqual(flow2.flow_type, 'ORDER_PATH')


# ═══════════════════════════════════════════════════════════════
# API TESTS
# ═══════════════════════════════════════════════════════════════

class ServiceNodeAPITest(TestCase):
    """Tests for ServiceNode API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(
            name='API Brand', corporate_id='AB1', contact_email='ab@x.com',
        )
        cls.outlet = Outlet.objects.create(
            brand=cls.brand, name='API Outlet', address='A',
            city='C', opening_time='09:00', closing_time='22:00',
        )

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('nodeuser', 'n@x.com', 'pass')
        self.client.force_authenticate(user=self.user)

    def test_list_nodes(self):
        ServiceNode.objects.create(
            outlet=self.outlet, name='N1', node_type='TABLE',
        )
        resp = self.client.get('/api/nodes/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_node(self):
        resp = self.client.post('/api/nodes/', {
            'outlet': self.outlet.pk,
            'name': 'NewTable',
            'node_type': 'TABLE',
            'capacity': 6,
            'pos_x': 1.5,
            'pos_y': 2.0,
            'pos_z': 0.0,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_node(self):
        node = ServiceNode.objects.create(
            outlet=self.outlet, name='GetNode', node_type='TABLE',
        )
        resp = self.client.get(f'/api/nodes/{node.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_status_action(self):
        node = ServiceNode.objects.create(
            outlet=self.outlet, name='StatusNode', node_type='TABLE',
            current_status='BLUE',
        )
        resp = self.client.post(f'/api/nodes/{node.pk}/update_status/', {
            'status': 'RED',
        }, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    def test_by_outlet_action(self):
        ServiceNode.objects.create(
            outlet=self.outlet, name='ByOutlet1', node_type='TABLE',
        )
        resp = self.client.get(f'/api/nodes/by_outlet/?outlet_id={self.outlet.pk}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ServiceFlowAPITest(TestCase):
    """Tests for ServiceFlow API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(
            name='FlowAPI Brand', corporate_id='FAB1', contact_email='fab@x.com',
        )
        cls.outlet = Outlet.objects.create(
            brand=cls.brand, name='FlowAPI Outlet', address='A',
            city='C', opening_time='09:00', closing_time='22:00',
        )
        cls.node_a = ServiceNode.objects.create(
            outlet=cls.outlet, name='NodeA', node_type='KITCHEN',
        )
        cls.node_b = ServiceNode.objects.create(
            outlet=cls.outlet, name='NodeB', node_type='TABLE',
        )

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('flowuser', 'f@x.com', 'pass')
        self.client.force_authenticate(user=self.user)

    def test_list_flows(self):
        resp = self.client.get('/api/flows/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_flow(self):
        resp = self.client.post('/api/flows/', {
            'source_node': self.node_a.pk,
            'target_node': self.node_b.pk,
            'flow_type': 'FOOD_DELIVERY',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_graph_action(self):
        ServiceFlow.objects.create(
            source_node=self.node_a, target_node=self.node_b,
            flow_type='FOOD_DELIVERY',
        )
        resp = self.client.get(f'/api/flows/graph/?outlet={self.outlet.pk}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)