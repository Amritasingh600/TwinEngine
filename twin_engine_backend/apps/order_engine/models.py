from django.db import models
from apps.layout_twin.models import ServiceNode
from apps.hospitality_group.models import UserProfile


class OrderTicket(models.Model):
    """
    Real-time order lifecycle tracking - drives table color status.
    This is the heart of the operational tracking system.
    
    Replaces: SensorData (from manufacturing version)
    """
    STATUS_CHOICES = [
        ('PLACED', 'Order Placed'),          # Just ordered → Table turns RED
        ('PREPARING', 'Preparing'),          # Kitchen working
        ('READY', 'Ready for Pickup'),       # Food ready to serve
        ('SERVED', 'Served'),                # Food delivered → Table turns GREEN
        ('COMPLETED', 'Completed'),          # Bill paid → Table turns BLUE
        ('CANCELLED', 'Cancelled'),          # Order voided
    ]
    
    # Link to table (ServiceNode)
    table = models.ForeignKey(
        ServiceNode, 
        on_delete=models.CASCADE, 
        related_name='orders',
        limit_choices_to={'node_type': 'TABLE'}
    )
    
    # Who is handling the order
    waiter = models.ForeignKey(
        UserProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='orders_served',
        limit_choices_to={'role__in': ['WAITER', 'MANAGER']}
    )
    
    # Customer info (optional for walk-ins)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    party_size = models.IntegerField(default=1, help_text="Number of guests")
    
    # Order details (JSON for flexibility)
    items = models.JSONField(default=list, help_text="List of menu items ordered")
    special_requests = models.TextField(blank=True, null=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLACED')
    
    # Timestamps for analytics
    placed_at = models.DateTimeField(auto_now_add=True)
    served_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['-placed_at']
        verbose_name = 'Order Ticket'
        verbose_name_plural = 'Order Tickets'
        indexes = [
            models.Index(fields=['table', '-placed_at']),
            models.Index(fields=['status']),
            models.Index(fields=['waiter', '-placed_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.pk} - {self.table.name} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Auto-update table status based on order status."""
        super().save(*args, **kwargs)
        # Update table color based on order status
        status_map = {
            'PLACED': 'RED',
            'PREPARING': 'RED',
            'READY': 'YELLOW',
            'SERVED': 'GREEN',
            'COMPLETED': 'BLUE',
            'CANCELLED': 'BLUE',
        }
        self.table.current_status = status_map.get(self.status, 'BLUE')
        self.table.save(update_fields=['current_status', 'updated_at'])


class PaymentLog(models.Model):
    """
    Payment transactions linked to orders.
    
    Replaces: AnomalyAlert (from manufacturing version)
    """
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI Payment'),
        ('WALLET', 'Digital Wallet'),
        ('SPLIT', 'Split Payment'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    order = models.ForeignKey(OrderTicket, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Optional transaction ID from payment gateway
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Tip tracking
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Log'
        verbose_name_plural = 'Payment Logs'
        indexes = [
            models.Index(fields=['order', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment {self.status}: ₹{self.amount} ({self.method}) for Order #{self.order.pk}"
