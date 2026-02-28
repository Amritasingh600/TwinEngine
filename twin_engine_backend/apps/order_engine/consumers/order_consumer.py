import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class OrderConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time order updates.
    Connects clients to outlet-specific or global order streams.
    """
    
    async def connect(self):
        self.outlet_id = self.scope['url_route']['kwargs'].get('outlet_id')
        
        if self.outlet_id:
            self.room_group_name = f'orders_{self.outlet_id}'
        else:
            self.room_group_name = 'orders_global'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial active orders
        if self.outlet_id:
            active_orders = await self.get_active_orders()
            await self.send(text_data=json.dumps({
                'type': 'active_orders',
                'orders': active_orders
            }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'request_orders':
            orders = await self.get_active_orders()
            await self.send(text_data=json.dumps({
                'type': 'active_orders',
                'orders': orders
            }))
    
    async def order_created(self, event):
        """Handle new order broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'order_created',
            'order': event['order'],
        }))
    
    async def order_updated(self, event):
        """Handle order status update broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'order_updated',
            'order_id': event['order_id'],
            'old_status': event.get('old_status'),
            'new_status': event['new_status'],
            'table_id': event.get('table_id'),
            'timestamp': event.get('timestamp'),
        }))
    
    async def order_completed(self, event):
        """Handle order completion broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'order_completed',
            'order_id': event['order_id'],
            'table_id': event.get('table_id'),
            'total': event.get('total'),
        }))
    
    @database_sync_to_async
    def get_active_orders(self):
        """Get active orders for the outlet."""
        from apps.order_engine.models import OrderTicket
        
        if not self.outlet_id:
            return []
        
        orders = OrderTicket.objects.filter(
            table__outlet_id=self.outlet_id,
            status__in=['PLACED', 'PREPARING', 'READY', 'SERVED']
        ).select_related('table', 'waiter').values(
            'id', 'status', 'guest_count', 'total',
            'placed_at', 'table__id', 'table__name',
            'waiter__user__username'
        )
        
        return list(orders)
