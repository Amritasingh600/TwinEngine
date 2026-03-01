"""
Django signals for automatic table status updates based on order lifecycle.

Signal Flow:
1. pre_save: Capture the old order status before saving + validate transition
2. post_save: Compare old vs new status, update table color, broadcast via WebSocket

Status Mapping:
- PLACED/PREPARING/READY → Table turns YELLOW (waiting for food)
- SERVED → Table turns GREEN (food delivered)
- COMPLETED/CANCELLED → Table turns BLUE (available) if no other active orders

Valid Order Status Transitions:
PLACED → PREPARING → READY → SERVED → COMPLETED
Any state → CANCELLED
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


# Order status → Table color mapping
ORDER_TO_TABLE_STATUS = {
    'PLACED': 'YELLOW',      # Order in progress
    'PREPARING': 'YELLOW',   # Kitchen working
    'READY': 'YELLOW',       # Ready but not served
    'SERVED': 'GREEN',       # Food delivered
    'COMPLETED': 'BLUE',     # Available (if no other orders)
    'CANCELLED': 'BLUE',     # Available (if no other orders)
}

# Valid status transitions (from → [allowed destinations])
VALID_TRANSITIONS = {
    None: ['PLACED'],                                    # New order
    'PLACED': ['PREPARING', 'READY', 'SERVED', 'CANCELLED'],
    'PREPARING': ['READY', 'SERVED', 'CANCELLED'],
    'READY': ['SERVED', 'CANCELLED'],
    'SERVED': ['COMPLETED', 'CANCELLED'],
    'COMPLETED': [],                                     # Terminal state
    'CANCELLED': [],                                     # Terminal state
}


def validate_status_transition(old_status, new_status):
    """
    Validate that the status transition is allowed.
    Returns True if valid, raises ValidationError if not.
    """
    allowed = VALID_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise ValidationError(
            f"Invalid status transition: {old_status or 'NEW'} → {new_status}. "
            f"Allowed transitions: {', '.join(allowed) if allowed else 'None (terminal state)'}"
        )
    return True


@receiver(pre_save, sender='order_engine.OrderTicket')
def capture_old_status(sender, instance, **kwargs):
    """
    Capture the old order status before saving.
    This is needed to detect status transitions in post_save.
    Also validates that the status transition is allowed.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._old_table_id = old_instance.table_id
            
            # Validate status transition (only if status changed)
            if old_instance.status != instance.status:
                validate_status_transition(old_instance.status, instance.status)
                
        except sender.DoesNotExist:
            instance._old_status = None
            instance._old_table_id = None
    else:
        instance._old_status = None
        instance._old_table_id = None
        # Validate new orders must start as PLACED
        if instance.status != 'PLACED':
            validate_status_transition(None, instance.status)


@receiver(post_save, sender='order_engine.OrderTicket')
def update_table_status_on_order_change(sender, instance, created, **kwargs):
    """
    Update table (ServiceNode) status when order status changes.
    Also broadcasts the change via WebSocket for real-time 3D updates.
    """
    from apps.layout_twin.models import ServiceNode
    from apps.layout_twin.utils.broadcast import broadcast_node_status_change
    from apps.order_engine.utils import (
        broadcast_order_created, 
        broadcast_order_updated, 
        broadcast_order_completed
    )
    
    table = instance.table
    old_table_status = table.current_status
    old_order_status = getattr(instance, '_old_status', None)
    new_status = None
    
    # Prepare order data for broadcasts
    order_data = {
        'id': instance.pk,
        'table_id': table.id,
        'table_name': table.name,
        'status': instance.status,
        'customer_name': instance.customer_name,
        'party_size': instance.party_size,
        'total': float(instance.total),
        'placed_at': instance.placed_at.isoformat() if instance.placed_at else None,
    }
    
    # Get the expected table status based on order status
    expected_status = ORDER_TO_TABLE_STATUS.get(instance.status)
    
    if created:
        # New order placed → table should turn YELLOW
        new_status = 'YELLOW'
        
    elif instance.status in ['SERVED']:
        # Order served → table turns GREEN
        new_status = 'GREEN'
        
    elif instance.status in ['COMPLETED', 'CANCELLED']:
        # Check if table has other active orders
        active_orders = sender.objects.filter(
            table=table,
            status__in=['PLACED', 'PREPARING', 'READY', 'SERVED']
        ).exclude(pk=instance.pk).exists()
        
        if not active_orders:
            new_status = 'BLUE'  # Table available
        else:
            # Determine status based on other orders
            other_orders = sender.objects.filter(
                table=table,
                status__in=['PLACED', 'PREPARING', 'READY', 'SERVED']
            ).exclude(pk=instance.pk)
            
            # Priority: SERVED (GREEN) > others (YELLOW)
            if other_orders.filter(status='SERVED').exists():
                new_status = 'GREEN'
            else:
                new_status = 'YELLOW'
                
    elif instance.status in ['PLACED', 'PREPARING', 'READY']:
        # Check if any order on this table is served
        served_orders = sender.objects.filter(
            table=table,
            status='SERVED'
        ).exclude(pk=instance.pk).exists()
        
        if served_orders:
            new_status = 'GREEN'
        else:
            new_status = 'YELLOW'
    
    # Update table status if changed
    if new_status and new_status != old_table_status:
        table.current_status = new_status
        table.save(update_fields=['current_status', 'updated_at'])
        
        # Auto-set served_at timestamp
        if instance.status == 'SERVED' and not instance.served_at:
            instance.served_at = timezone.now()
            instance.save(update_fields=['served_at'])
        
        # Auto-set completed_at timestamp
        if instance.status == 'COMPLETED' and not instance.completed_at:
            instance.completed_at = timezone.now()
            instance.save(update_fields=['completed_at'])
        
        # Broadcast via WebSocket for real-time 3D updates
        try:
            broadcast_node_status_change(
                outlet_id=table.outlet_id,
                node_id=table.id,
                old_status=old_table_status,
                new_status=new_status
            )
        except Exception as e:
            # Don't fail the save if WebSocket broadcast fails
            logger.warning(f"WebSocket broadcast failed: {e}")
    
    # Handle table change (order moved to different table)
    old_table_id = getattr(instance, '_old_table_id', None)
    if old_table_id and old_table_id != table.id:
        try:
            old_table = ServiceNode.objects.get(pk=old_table_id)
            # Check if old table has other active orders
            active_on_old = sender.objects.filter(
                table_id=old_table_id,
                status__in=['PLACED', 'PREPARING', 'READY', 'SERVED']
            ).exists()
            
            if not active_on_old and old_table.current_status != 'BLUE':
                old_table_previous_status = old_table.current_status
                old_table.current_status = 'BLUE'
                old_table.save(update_fields=['current_status', 'updated_at'])
                
                # Broadcast old table status change
                try:
                    broadcast_node_status_change(
                        outlet_id=old_table.outlet_id,
                        node_id=old_table.id,
                        old_status=old_table_previous_status,
                        new_status='BLUE'
                    )
                except Exception:
                    pass
        except ServiceNode.DoesNotExist:
            pass
    
    # =========================================================================
    # ORDER-SPECIFIC BROADCASTS
    # These give the frontend more context about what's happening
    # =========================================================================
    try:
        if created:
            # New order created
            broadcast_order_created(
                outlet_id=table.outlet_id,
                order_data=order_data
            )
            logger.info(f"Order #{instance.pk} created on {table.name}")
            
        elif old_order_status and old_order_status != instance.status:
            # Order status changed
            broadcast_order_updated(
                outlet_id=table.outlet_id,
                order_id=instance.pk,
                old_status=old_order_status,
                new_status=instance.status,
                table_id=table.id
            )
            logger.info(f"Order #{instance.pk} status: {old_order_status} → {instance.status}")
            
            # Special broadcast for completed orders
            if instance.status == 'COMPLETED':
                broadcast_order_completed(
                    outlet_id=table.outlet_id,
                    order_id=instance.pk,
                    table_id=table.id,
                    total=float(instance.total)
                )
                logger.info(f"Order #{instance.pk} completed - Total: ₹{instance.total}")
                
    except Exception as e:
        logger.warning(f"Order broadcast failed: {e}")
