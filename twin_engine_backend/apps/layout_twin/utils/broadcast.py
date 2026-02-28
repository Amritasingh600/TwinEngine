from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from datetime import datetime


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
    
    async_to_sync(channel_layer.group_send)(
        f'floor_{outlet_id}',
        {
            'type': 'floor_update',
            'node_id': node_id,
            'status': status,
            'node_name': node_name,
        }
    )


def broadcast_node_status_change(outlet_id: int, node_id: int, old_status: str, new_status: str):
    """
    Broadcast a node status change event.
    
    Args:
        outlet_id: The outlet ID
        node_id: The service node ID
        old_status: Previous status
        new_status: New status
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        f'floor_{outlet_id}',
        {
            'type': 'node_status_change',
            'node_id': node_id,
            'old_status': old_status,
            'new_status': new_status,
            'timestamp': datetime.now().isoformat(),
        }
    )
