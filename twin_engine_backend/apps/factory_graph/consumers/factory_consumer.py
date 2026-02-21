"""
WebSocket consumer for real-time factory floor updates.
Handles node status changes, sensor updates, and alert broadcasts.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class FactoryFloorConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time factory floor updates.
    
    Connection URL: ws://host/ws/factory/<manufacturer_id>/
    
    Events:
        - initial_state: Sent on connect with all nodes
        - node_status_change: Broadcast when a node's status changes
        - sensor_update: Broadcast when new sensor data arrives
        - request_status: Client requests current state
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.manufacturer_id = self.scope['url_route']['kwargs'].get('manufacturer_id', 'default')
        self.room_group_name = f'factory_{self.manufacturer_id}'
        
        # Join room group for this manufacturer
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send initial state on connection
        await self.send_initial_state()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages from client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_status':
                await self.send_initial_state()
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def send_initial_state(self):
        """Send current state of all nodes to the client."""
        nodes = await self.get_all_nodes()
        await self.send(text_data=json.dumps({
            'type': 'initial_state',
            'manufacturer_id': self.manufacturer_id,
            'nodes': nodes
        }))
    
    @database_sync_to_async
    def get_all_nodes(self):
        """Fetch all nodes for this manufacturer from database."""
        from apps.factory_graph.models import MachineNode
        from apps.factory_graph.serializers import MachineNodeListSerializer
        
        nodes = MachineNode.objects.filter(
            manufacturer_id=self.manufacturer_id
        ).select_related('machine_type')
        
        return MachineNodeListSerializer(nodes, many=True).data
    
    # ==================== Event Handlers ====================
    # These methods handle events broadcast via channel_layer.group_send()
    
    async def node_status_change(self, event):
        """
        Handle node status change broadcast.
        
        Called when channel_layer.group_send() is invoked with type='node_status_change'
        """
        await self.send(text_data=json.dumps({
            'type': 'node_status_change',
            'node_id': event['node_id'],
            'node_name': event.get('node_name', ''),
            'status': event['status'],
            'previous_status': event.get('previous_status', ''),
            'timestamp': event['timestamp']
        }))
    
    async def sensor_update(self, event):
        """
        Handle sensor data update broadcast.
        
        Called when channel_layer.group_send() is invoked with type='sensor_update'
        """
        await self.send(text_data=json.dumps({
            'type': 'sensor_update',
            'node_id': event['node_id'],
            'node_name': event.get('node_name', ''),
            'data': event['data'],
            'timestamp': event['timestamp']
        }))
    
    async def alert_broadcast(self, event):
        """
        Handle new alert broadcast.
        
        Called when channel_layer.group_send() is invoked with type='alert_broadcast'
        """
        await self.send(text_data=json.dumps({
            'type': 'new_alert',
            'alert': event['alert']
        }))
