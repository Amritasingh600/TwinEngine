from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import OrderTicket, PaymentLog
from .serializers import (
    OrderTicketSerializer, OrderTicketCreateSerializer, OrderTicketListSerializer,
    OrderStatusUpdateSerializer,
    PaymentLogSerializer, PaymentLogCreateSerializer,
    TableStatusTriggerSerializer
)


class OrderTicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Order Tickets.
    
    Endpoints:
    - GET /api/orders/ - List all orders
    - POST /api/orders/ - Create a new order
    - GET /api/orders/{id}/ - Retrieve order details
    - PUT/PATCH /api/orders/{id}/ - Update order
    - POST /api/orders/{id}/update-status/ - Update order status
    - GET /api/orders/active/ - Get all active orders
    """
    queryset = OrderTicket.objects.select_related('table', 'waiter__user').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['table', 'waiter', 'status', 'table__outlet']
    ordering_fields = ['placed_at', 'total', 'status']
    ordering = ['-placed_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderTicketCreateSerializer
        if self.action == 'list':
            return OrderTicketListSerializer
        return OrderTicketSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status and auto-update table color."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data)
        if serializer.is_valid():
            order = serializer.update(order, serializer.validated_data)
            return Response(OrderTicketSerializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active (not completed/cancelled) orders."""
        orders = self.queryset.exclude(status__in=['COMPLETED', 'CANCELLED'])
        outlet_id = request.query_params.get('outlet')
        if outlet_id:
            orders = orders.filter(table__outlet_id=outlet_id)
        serializer = OrderTicketListSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_table(self, request):
        """Get orders for a specific table."""
        table_id = request.query_params.get('table_id')
        if not table_id:
            return Response({'error': 'table_id parameter required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        orders = self.queryset.filter(table_id=table_id)
        active_only = request.query_params.get('active_only', 'false').lower() == 'true'
        if active_only:
            orders = orders.exclude(status__in=['COMPLETED', 'CANCELLED'])
        serializer = OrderTicketSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def kitchen_queue(self, request):
        """Get orders that need kitchen attention."""
        orders = self.queryset.filter(status__in=['PLACED', 'PREPARING'])
        outlet_id = request.query_params.get('outlet')
        if outlet_id:
            orders = orders.filter(table__outlet_id=outlet_id)
        serializer = OrderTicketListSerializer(orders.order_by('placed_at'), many=True)
        return Response(serializer.data)


class PaymentLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Payment Logs.
    
    Endpoints:
    - GET /api/payments/ - List all payments
    - POST /api/payments/ - Create a new payment
    - GET /api/payments/{id}/ - Retrieve payment details
    - GET /api/payments/summary/ - Get payment summary
    """
    queryset = PaymentLog.objects.select_related('order', 'order__table').all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'method', 'status']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentLogCreateSerializer
        return PaymentLogSerializer
    
    def perform_create(self, serializer):
        """After creating payment, mark order as completed if paid in full."""
        payment = serializer.save(status='SUCCESS')
        order = payment.order
        total_paid = sum(p.amount for p in order.payments.filter(status='SUCCESS'))
        if total_paid >= order.total:
            order.status = 'COMPLETED'
            order.completed_at = timezone.now()
            order.save()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get payment summary statistics."""
        from django.db.models import Sum, Count
        outlet_id = request.query_params.get('outlet')
        date_str = request.query_params.get('date')
        
        qs = self.queryset.filter(status='SUCCESS')
        if outlet_id:
            qs = qs.filter(order__table__outlet_id=outlet_id)
        if date_str:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            qs = qs.filter(created_at__date=target_date)
        
        stats = qs.aggregate(
            total_revenue=Sum('amount'),
            total_tips=Sum('tip_amount'),
            transaction_count=Count('id')
        )
        
        by_method = qs.values('method').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        return Response({
            **stats,
            'by_method': list(by_method)
        })


class TableStatusTriggerView(APIView):
    """
    API endpoint to manually update table status (color).
    
    POST /api/table/trigger/
    Request: { node_id: int, status: string }
    Response: { updated: true }
    """
    
    def post(self, request):
        serializer = TableStatusTriggerSerializer(data=request.data)
        if serializer.is_valid():
            from apps.layout_twin.models import ServiceNode
            
            node_id = serializer.validated_data['node_id']
            new_status = serializer.validated_data['status']
            
            node = ServiceNode.objects.get(id=node_id)
            old_status = node.current_status
            node.current_status = new_status
            node.save()
            
            return Response({
                'updated': True,
                'node_id': node_id,
                'old_status': old_status,
                'new_status': new_status
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
