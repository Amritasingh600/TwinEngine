from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def broadcast_order_created(outlet_id: int, order_data: dict):
    """
    Broadcast new order creation to connected clients.
    
    Args:
        outlet_id: The outlet ID
        order_data: Order details dictionary
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("No channel layer configured - WebSocket broadcast skipped")
        return
    
    try:
        message = {
            'type': 'order_created',
            'order': order_data,
            'timestamp': datetime.now().isoformat(),
        }
        
        # Broadcast to outlet-specific room
        async_to_sync(channel_layer.group_send)(f'orders_{outlet_id}', message)
        
        # Also broadcast to global room
        async_to_sync(channel_layer.group_send)('orders_global', message)
        
    except Exception as e:
        logger.warning(f"Order created broadcast failed: {e}")


def broadcast_order_updated(outlet_id: int, order_id: int, old_status: str, new_status: str, table_id: int = None):
    """
    Broadcast order status update.
    
    Args:
        outlet_id: The outlet ID
        order_id: The order ID
        old_status: Previous status
        new_status: New status
        table_id: Optional table ID
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("No channel layer configured - WebSocket broadcast skipped")
        return
    
    try:
        message = {
            'type': 'order_updated',
            'order_id': order_id,
            'old_status': old_status,
            'new_status': new_status,
            'table_id': table_id,
            'timestamp': datetime.now().isoformat(),
        }
        
        async_to_sync(channel_layer.group_send)(f'orders_{outlet_id}', message)
        async_to_sync(channel_layer.group_send)('orders_global', message)
        
    except Exception as e:
        logger.warning(f"Order updated broadcast failed: {e}")


def broadcast_order_completed(outlet_id: int, order_id: int, table_id: int, total: float):
    """
    Broadcast order completion.
    
    Args:
        outlet_id: The outlet ID
        order_id: The order ID
        table_id: The table ID
        total: Order total amount
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("No channel layer configured - WebSocket broadcast skipped")
        return
    
    try:
        message = {
            'type': 'order_completed',
            'order_id': order_id,
            'table_id': table_id,
            'total': total,
            'timestamp': datetime.now().isoformat(),
        }
        
        async_to_sync(channel_layer.group_send)(f'orders_{outlet_id}', message)
        async_to_sync(channel_layer.group_send)('orders_global', message)
        
    except Exception as e:
        logger.warning(f"Order completed broadcast failed: {e}")
