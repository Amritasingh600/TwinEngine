"""
Broadcast utilities for pushing real-time updates via WebSocket.

These functions are called from views/signals when data changes,
and they broadcast updates to all connected WebSocket clients.
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone


def broadcast_node_status_change(manufacturer_id, node_id, node_name, new_status, previous_status=None):
    """
    Broadcast a node status change to all clients watching this manufacturer's factory.
    
    Args:
        manufacturer_id: ID of the manufacturer
        node_id: ID of the machine node
        node_name: Name of the machine node
        new_status: New status value (NORMAL, WARNING, ERROR, OFFLINE)
        previous_status: Previous status value (optional)
    
    Usage:
        from apps.factory_graph.utils.broadcast import broadcast_node_status_change
        broadcast_node_status_change(node.manufacturer_id, node.id, node.name, 'ERROR', 'NORMAL')
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        f'factory_{manufacturer_id}',
        {
            'type': 'node_status_change',
            'node_id': node_id,
            'node_name': node_name,
            'status': new_status,
            'previous_status': previous_status or '',
            'timestamp': timezone.now().isoformat()
        }
    )


def broadcast_sensor_update(manufacturer_id, node_id, node_name, sensor_data):
    """
    Broadcast new sensor data to all clients watching this manufacturer's factory.
    
    Args:
        manufacturer_id: ID of the manufacturer
        node_id: ID of the machine node
        node_name: Name of the machine node
        sensor_data: Dict containing sensor readings
    
    Usage:
        from apps.factory_graph.utils.broadcast import broadcast_sensor_update
        broadcast_sensor_update(node.manufacturer_id, node.id, node.name, {
            'temperature': 85.5,
            'vibration': 0.3,
            'torque': 45.2,
            'rpm': 1200,
            'tool_wear': 0.15
        })
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        f'factory_{manufacturer_id}',
        {
            'type': 'sensor_update',
            'node_id': node_id,
            'node_name': node_name,
            'data': sensor_data,
            'timestamp': timezone.now().isoformat()
        }
    )


def broadcast_new_alert(alert_data, manufacturer_id=None):
    """
    Broadcast a new anomaly alert to all clients.
    
    Args:
        alert_data: Serialized alert data (dict)
        manufacturer_id: Optional - if provided, also broadcasts to manufacturer-specific group
    
    Usage:
        from apps.factory_graph.utils.broadcast import broadcast_new_alert
        broadcast_new_alert(AnomalyAlertSerializer(alert).data, manufacturer_id=1)
    """
    channel_layer = get_channel_layer()
    timestamp = timezone.now().isoformat()
    
    # Broadcast to global alerts group
    async_to_sync(channel_layer.group_send)(
        'alerts_all',
        {
            'type': 'new_alert',
            'alert': alert_data,
            'timestamp': timestamp
        }
    )
    
    # Also broadcast to manufacturer-specific group if provided
    if manufacturer_id:
        async_to_sync(channel_layer.group_send)(
            f'alerts_manufacturer_{manufacturer_id}',
            {
                'type': 'new_alert',
                'alert': alert_data,
                'timestamp': timestamp
            }
        )
        
        # Also broadcast to factory floor for that manufacturer
        async_to_sync(channel_layer.group_send)(
            f'factory_{manufacturer_id}',
            {
                'type': 'alert_broadcast',
                'alert': alert_data
            }
        )


def broadcast_alert_resolved(alert_id, resolved_by=None, manufacturer_id=None):
    """
    Broadcast that an alert has been resolved.
    
    Args:
        alert_id: ID of the resolved alert
        resolved_by: Username of who resolved it (optional)
        manufacturer_id: Optional - if provided, also broadcasts to manufacturer-specific group
    
    Usage:
        from apps.factory_graph.utils.broadcast import broadcast_alert_resolved
        broadcast_alert_resolved(alert.id, resolved_by='engineer1', manufacturer_id=1)
    """
    channel_layer = get_channel_layer()
    timestamp = timezone.now().isoformat()
    
    # Broadcast to global alerts group
    async_to_sync(channel_layer.group_send)(
        'alerts_all',
        {
            'type': 'alert_resolved',
            'alert_id': alert_id,
            'resolved_by': resolved_by or '',
            'timestamp': timestamp
        }
    )
    
    # Also broadcast to manufacturer-specific group if provided
    if manufacturer_id:
        async_to_sync(channel_layer.group_send)(
            f'alerts_manufacturer_{manufacturer_id}',
            {
                'type': 'alert_resolved',
                'alert_id': alert_id,
                'resolved_by': resolved_by or '',
                'timestamp': timestamp
            }
        )
