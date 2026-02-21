"""
WebSocket consumer for real-time alert notifications.
Broadcasts anomaly alerts to all connected clients.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class AlertConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time alert notifications.
    
    Connection URL: ws://host/ws/alerts/
    Optional: ws://host/ws/alerts/<manufacturer_id>/ (filtered by manufacturer)
    
    Events:
        - initial_alerts: Sent on connect with recent unresolved alerts
        - new_alert: Broadcast when a new anomaly is detected
        - alert_resolved: Broadcast when an alert is resolved
        - alert_count: Current count of unresolved alerts
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Optional manufacturer filter
        self.manufacturer_id = self.scope['url_route']['kwargs'].get('manufacturer_id')
        
        # Group name - global or manufacturer-specific
        if self.manufacturer_id:
            self.alert_group = f'alerts_manufacturer_{self.manufacturer_id}'
        else:
            self.alert_group = 'alerts_all'
        
        # Join alert group
        await self.channel_layer.group_add(
            self.alert_group,
            self.channel_name
        )
        
        # Also join global group if manufacturer-specific
        if self.manufacturer_id:
            await self.channel_layer.group_add(
                'alerts_all',
                self.channel_name
            )
        
        await self.accept()
        
        # Send initial unresolved alerts on connection
        await self.send_initial_alerts()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.alert_group,
            self.channel_name
        )
        
        if self.manufacturer_id:
            await self.channel_layer.group_discard(
                'alerts_all',
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages from client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_alerts':
                await self.send_initial_alerts()
            elif message_type == 'request_count':
                await self.send_alert_count()
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
    
    async def send_initial_alerts(self):
        """Send recent unresolved alerts to the client."""
        alerts = await self.get_unresolved_alerts()
        await self.send(text_data=json.dumps({
            'type': 'initial_alerts',
            'count': len(alerts),
            'alerts': alerts
        }))
    
    async def send_alert_count(self):
        """Send count of unresolved alerts."""
        count = await self.get_alert_count()
        await self.send(text_data=json.dumps({
            'type': 'alert_count',
            'count': count
        }))
    
    @database_sync_to_async
    def get_unresolved_alerts(self):
        """Fetch recent unresolved alerts from database."""
        from apps.sensors.models import AnomalyAlert
        from apps.sensors.serializers import AnomalyAlertSerializer
        
        queryset = AnomalyAlert.objects.filter(
            resolved_status=False
        ).select_related('sensor_data__machine_node__manufacturer')
        
        # Filter by manufacturer if specified
        if self.manufacturer_id:
            queryset = queryset.filter(
                sensor_data__machine_node__manufacturer_id=self.manufacturer_id
            )
        
        # Limit to most recent 50 alerts
        alerts = queryset.order_by('-created_at')[:50]
        return AnomalyAlertSerializer(alerts, many=True).data
    
    @database_sync_to_async
    def get_alert_count(self):
        """Get count of unresolved alerts."""
        from apps.sensors.models import AnomalyAlert
        
        queryset = AnomalyAlert.objects.filter(resolved_status=False)
        
        if self.manufacturer_id:
            queryset = queryset.filter(
                sensor_data__machine_node__manufacturer_id=self.manufacturer_id
            )
        
        return queryset.count()
    
    # ==================== Event Handlers ====================
    # These methods handle events broadcast via channel_layer.group_send()
    
    async def new_alert(self, event):
        """
        Handle new alert broadcast.
        
        Called when channel_layer.group_send() is invoked with type='new_alert'
        """
        await self.send(text_data=json.dumps({
            'type': 'new_alert',
            'alert': event['alert'],
            'timestamp': event.get('timestamp', '')
        }))
    
    async def alert_resolved(self, event):
        """
        Handle alert resolution broadcast.
        
        Called when channel_layer.group_send() is invoked with type='alert_resolved'
        """
        await self.send(text_data=json.dumps({
            'type': 'alert_resolved',
            'alert_id': event['alert_id'],
            'resolved_by': event.get('resolved_by', ''),
            'timestamp': event.get('timestamp', '')
        }))
    
    async def alert_count_update(self, event):
        """
        Handle alert count update broadcast.
        
        Called when channel_layer.group_send() is invoked with type='alert_count_update'
        """
        await self.send(text_data=json.dumps({
            'type': 'alert_count',
            'count': event['count']
        }))
