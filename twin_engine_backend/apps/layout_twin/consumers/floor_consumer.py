import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class FloorConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time floor status updates.
    Connects clients to outlet-specific floor status streams.
    """
    
    async def connect(self):
        self.outlet_id = self.scope['url_route']['kwargs']['outlet_id']
        self.room_group_name = f'floor_{self.outlet_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial floor state
        initial_state = await self.get_floor_state()
        await self.send(text_data=json.dumps({
            'type': 'floor_state',
            'nodes': initial_state
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'request_update':
            # Client requesting latest state
            state = await self.get_floor_state()
            await self.send(text_data=json.dumps({
                'type': 'floor_state',
                'nodes': state
            }))
    
    async def floor_update(self, event):
        """Handle floor update broadcast from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'floor_update',
            'node_id': event['node_id'],
            'status': event['status'],
            'node_name': event.get('node_name', ''),
        }))
    
    async def node_status_change(self, event):
        """Handle individual node status change."""
        await self.send(text_data=json.dumps({
            'type': 'node_status_change',
            'node_id': event['node_id'],
            'old_status': event.get('old_status'),
            'new_status': event['new_status'],
            'timestamp': event.get('timestamp'),
        }))
    
    async def wait_time_alert(self, event):
        """Handle wait time alert for tables exceeding threshold."""
        await self.send(text_data=json.dumps({
            'type': 'wait_time_alert',
            'node_id': event['node_id'],
            'node_name': event.get('node_name', ''),
            'wait_minutes': event['wait_minutes'],
            'order_count': event.get('order_count', 1),
            'alert_level': event.get('alert_level', 'warning'),
            'timestamp': event.get('timestamp'),
        }))
    
    @database_sync_to_async
    def get_floor_state(self):
        """Get current floor state for the outlet."""
        from apps.layout_twin.models import ServiceNode
        
        nodes = ServiceNode.objects.filter(
            outlet_id=self.outlet_id,
            is_active=True
        ).values(
            'id', 'name', 'node_type', 'current_status',
            'pos_x', 'pos_y', 'pos_z', 'capacity'
        )
        
        return list(nodes)
