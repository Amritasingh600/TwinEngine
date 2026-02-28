from rest_framework import serializers
from .models import OrderTicket, PaymentLog


class OrderTicketSerializer(serializers.ModelSerializer):
    """Serializer for OrderTicket model."""
    table_name = serializers.CharField(source='table.name', read_only=True)
    waiter_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OrderTicket
        fields = [
            'id', 'table', 'table_name', 'waiter', 'waiter_name',
            'customer_name', 'party_size', 'items', 'special_requests',
            'status', 'status_display',
            'placed_at', 'served_at', 'completed_at',
            'subtotal', 'tax', 'total'
        ]
        read_only_fields = ['id', 'placed_at']
    
    def get_waiter_name(self, obj):
        if obj.waiter and obj.waiter.user:
            return obj.waiter.user.get_full_name() or obj.waiter.user.username
        return None


class OrderTicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating order tickets."""
    
    class Meta:
        model = OrderTicket
        fields = [
            'table', 'waiter', 'customer_name', 'party_size',
            'items', 'special_requests', 'subtotal', 'tax', 'total'
        ]


class OrderTicketListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing orders."""
    table_name = serializers.CharField(source='table.name', read_only=True)
    
    class Meta:
        model = OrderTicket
        fields = ['id', 'table_name', 'status', 'party_size', 'total', 'placed_at']


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status."""
    status = serializers.ChoiceField(choices=OrderTicket.STATUS_CHOICES)
    
    def update(self, instance, validated_data):
        from django.utils import timezone
        instance.status = validated_data['status']
        
        # Auto-update timestamps
        if instance.status == 'SERVED':
            instance.served_at = timezone.now()
        elif instance.status == 'COMPLETED':
            instance.completed_at = timezone.now()
        
        instance.save()
        return instance


class PaymentLogSerializer(serializers.ModelSerializer):
    """Serializer for PaymentLog model."""
    order_table = serializers.CharField(source='order.table.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentLog
        fields = [
            'id', 'order', 'order_table', 'amount', 'method',
            'status', 'status_display', 'transaction_id', 'tip_amount', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payment logs."""
    
    class Meta:
        model = PaymentLog
        fields = ['order', 'amount', 'method', 'transaction_id', 'tip_amount']


class TableStatusTriggerSerializer(serializers.Serializer):
    """Serializer for manual table status update."""
    node_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['BLUE', 'RED', 'GREEN', 'YELLOW', 'GREY'])
    
    def validate_node_id(self, value):
        from apps.layout_twin.models import ServiceNode
        if not ServiceNode.objects.filter(id=value).exists():
            raise serializers.ValidationError("Service node does not exist.")
        return value
