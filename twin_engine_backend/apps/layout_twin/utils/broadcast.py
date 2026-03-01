from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def broadcast_floor_update(outlet_id: int, node_id: int, status: str, node_name: str = ''):
    """
    Broadcast a floor update to all connected clients for an outlet.
    
    Args:
        outlet_id: The outlet ID
        node_id: The service node ID that changed
        status: The new status (BLUE, RED, GREEN, YELLOW, GREY)
        node_name: Optional node name for display
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("No channel layer configured - WebSocket broadcast skipped")
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            f'floor_{outlet_id}',
            {
                'type': 'floor_update',
                'node_id': node_id,
                'status': status,
                'node_name': node_name,
                'timestamp': datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.warning(f"Floor broadcast failed for outlet {outlet_id}: {e}")


def broadcast_node_status_change(outlet_id: int, node_id: int, old_status: str, new_status: str, node_name: str = ''):
    """
    Broadcast a node status change event.
    
    Args:
        outlet_id: The outlet ID
        node_id: The service node ID
        old_status: Previous status
        new_status: New status
        node_name: Optional node name for display
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("No channel layer configured - WebSocket broadcast skipped")
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            f'floor_{outlet_id}',
            {
                'type': 'node_status_change',
                'node_id': node_id,
                'node_name': node_name,
                'old_status': old_status,
                'new_status': new_status,
                'timestamp': datetime.now().isoformat(),
            }
        )
        logger.debug(f"Broadcast: Node {node_id} changed {old_status} → {new_status}")
    except Exception as e:
        logger.warning(f"Node status broadcast failed: {e}")


def broadcast_wait_time_alert(outlet_id: int, node_id: int, node_name: str, wait_minutes: int, order_count: int = 1):
    """
    Broadcast a wait time alert for a table that has exceeded threshold.
    
    Args:
        outlet_id: The outlet ID
        node_id: The table/service node ID
        node_name: Name of the table
        wait_minutes: How many minutes the longest order has been waiting
        order_count: Number of orders waiting on this table
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("No channel layer configured - WebSocket broadcast skipped")
        return
    
    try:
        async_to_sync(channel_layer.group_send)(
            f'floor_{outlet_id}',
            {
                'type': 'wait_time_alert',
                'node_id': node_id,
                'node_name': node_name,
                'wait_minutes': wait_minutes,
                'order_count': order_count,
                'alert_level': 'critical' if wait_minutes > 20 else 'warning',
                'timestamp': datetime.now().isoformat(),
            }
        )
        logger.info(f"Wait time alert: {node_name} waiting {wait_minutes}min ({order_count} orders)")
    except Exception as e:
        logger.warning(f"Wait time alert broadcast failed: {e}")
