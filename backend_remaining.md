# TwinEngine Backend - Remaining Tasks

This document outlines all remaining backend tasks with detailed implementation steps, code examples, and testing procedures.

---

## Table of Contents

1. [WebSocket Consumers (Real-time Alerts)](#1-websocket-consumers-real-time-alerts)
2. [Authentication System](#2-authentication-system)
3. [Hugging Face Vision Integration](#3-hugging-face-vision-integration)
4. [Azure GPT-4o Report Generation](#4-azure-gpt-4o-report-generation)
5. [Cloudinary Media Integration](#5-cloudinary-media-integration)
6. [Unit Tests](#6-unit-tests)
7. [PostgreSQL/Neon Migration](#7-postgresqlneon-migration)
8. [Background Tasks with Celery](#8-background-tasks-with-celery)

---

## 1. WebSocket Consumers (Real-time Alerts)

**Priority:** High  
**Estimated Time:** 4-6 hours  
**Dependencies:** `channels`, `channels-redis` (already in requirements.txt)

### Purpose
Enable real-time communication between backend and frontend for:
- Instant node status changes (Normal → Error)
- Live sensor data streaming
- Alert notifications

### Implementation Steps

#### Step 1: Create Consumers Directory
```bash
mkdir -p apps/factory_graph/consumers
touch apps/factory_graph/consumers/__init__.py
```

#### Step 2: Create WebSocket Consumer
Create `apps/factory_graph/consumers/factory_consumer.py`:

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async


class FactoryFloorConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time factory floor updates.
    Handles node status changes and alert broadcasts.
    """
    
    async def connect(self):
        self.manufacturer_id = self.scope['url_route']['kwargs'].get('manufacturer_id', 'default')
        self.room_group_name = f'factory_{self.manufacturer_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send initial state
        await self.send_initial_state()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'request_status':
            await self.send_initial_state()
        elif message_type == 'update_node_status':
            await self.handle_node_update(data)
    
    async def send_initial_state(self):
        """Send current state of all nodes."""
        nodes = await self.get_all_nodes()
        await self.send(text_data=json.dumps({
            'type': 'initial_state',
            'nodes': nodes
        }))
    
    @database_sync_to_async
    def get_all_nodes(self):
        from apps.factory_graph.models import MachineNode
        from apps.factory_graph.serializers import MachineNodeListSerializer
        
        nodes = MachineNode.objects.filter(manufacturer_id=self.manufacturer_id)
        return MachineNodeListSerializer(nodes, many=True).data
    
    async def handle_node_update(self, data):
        """Process node status update and broadcast to group."""
        node_id = data.get('node_id')
        new_status = data.get('status')
        
        # Update in database
        updated = await self.update_node_status(node_id, new_status)
        
        if updated:
            # Broadcast to all clients in the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'node_status_change',
                    'node_id': node_id,
                    'status': new_status,
                    'timestamp': str(updated)
                }
            )
    
    @database_sync_to_async
    def update_node_status(self, node_id, status):
        from apps.factory_graph.models import MachineNode
        from django.utils import timezone
        
        try:
            node = MachineNode.objects.get(id=node_id)
            node.status = status
            node.save()
            return timezone.now()
        except MachineNode.DoesNotExist:
            return None
    
    # Event handlers for group messages
    async def node_status_change(self, event):
        """Send node status change to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'node_status_change',
            'node_id': event['node_id'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))
    
    async def alert_broadcast(self, event):
        """Send alert notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'alert_id': event['alert_id'],
            'node_id': event['node_id'],
            'severity': event['severity'],
            'message': event['message']
        }))
    
    async def sensor_update(self, event):
        """Send sensor data update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'sensor_update',
            'node_id': event['node_id'],
            'data': event['data']
        }))
```

#### Step 3: Create Alert Consumer
Create `apps/sensors/consumers/alert_consumer.py`:

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class AlertConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time alert notifications."""
    
    async def connect(self):
        self.alert_group = 'alerts_all'
        
        await self.channel_layer.group_add(
            self.alert_group,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.alert_group,
            self.channel_name
        )
    
    async def new_alert(self, event):
        """Broadcast new alert to all connected clients."""
        await self.send(text_data=json.dumps({
            'type': 'new_alert',
            'alert': event['alert']
        }))
    
    async def alert_resolved(self, event):
        """Broadcast alert resolution."""
        await self.send(text_data=json.dumps({
            'type': 'alert_resolved',
            'alert_id': event['alert_id']
        }))
```

#### Step 4: Create WebSocket Routing
Create `apps/factory_graph/routing.py`:

```python
from django.urls import re_path
from .consumers.factory_consumer import FactoryFloorConsumer

websocket_urlpatterns = [
    re_path(r'ws/factory/(?P<manufacturer_id>\d+)/$', FactoryFloorConsumer.as_asgi()),
]
```

Create `apps/sensors/routing.py`:

```python
from django.urls import re_path
from .consumers.alert_consumer import AlertConsumer

websocket_urlpatterns = [
    re_path(r'ws/alerts/$', AlertConsumer.as_asgi()),
]
```

#### Step 5: Update ASGI Configuration
Update `twinengine_core/asgi.py`:

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twinengine_core.settings')

django_asgi_app = get_asgi_application()

from apps.factory_graph.routing import websocket_urlpatterns as factory_ws
from apps.sensors.routing import websocket_urlpatterns as sensor_ws

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            factory_ws + sensor_ws
        )
    ),
})
```

#### Step 6: Add Broadcast Utility
Create `apps/factory_graph/utils/broadcast.py`:

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_node_status_change(manufacturer_id, node_id, status):
    """Broadcast node status change to all connected clients."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'factory_{manufacturer_id}',
        {
            'type': 'node_status_change',
            'node_id': node_id,
            'status': status,
            'timestamp': str(timezone.now())
        }
    )


def broadcast_new_alert(alert_data):
    """Broadcast new alert to all clients."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'alerts_all',
        {
            'type': 'new_alert',
            'alert': alert_data
        }
    )
```

#### Step 7: Update Views to Broadcast
Update `apps/sensors/views.py` `AnomalyTriggerView`:

```python
# Add after node.save()
from apps.factory_graph.utils.broadcast import broadcast_node_status_change
broadcast_node_status_change(node.manufacturer_id, node_id, new_status)
```

### Testing WebSockets

#### Manual Testing with websocat:
```bash
# Install websocat
brew install websocat

# Connect to WebSocket
websocat ws://127.0.0.1:8000/ws/factory/1/

# Send message
{"type": "request_status"}
```

#### Python Test Script:
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/factory/1/"
    async with websockets.connect(uri) as websocket:
        # Request initial state
        await websocket.send(json.dumps({"type": "request_status"}))
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
```

---

## 2. Authentication System

**Priority:** High  
**Estimated Time:** 3-4 hours  
**Dependencies:** `djangorestframework-simplejwt`

### Purpose
Secure API endpoints with JWT authentication for:
- User login/logout
- Token refresh
- Permission-based access control

### Implementation Steps

#### Step 1: Install Dependencies
```bash
pip install djangorestframework-simplejwt
```

Add to `requirements.txt`:
```
djangorestframework-simplejwt
```

#### Step 2: Update Settings
Add to `twinengine_core/settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # ... existing config
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

#### Step 3: Create Auth URLs
Create `apps/manufacturers/auth_urls.py`:

```python
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import RegisterView, UserProfileView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserProfileView.as_view(), name='user-profile'),
]
```

#### Step 4: Create Register View
Add to `apps/manufacturers/views.py`:

```python
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

class RegisterView(APIView):
    """User registration endpoint."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserProfileCreateSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response({
                'message': 'User created successfully',
                'user_id': profile.user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """Get current user's profile."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
```

#### Step 5: Add Custom Permissions
Create `apps/manufacturers/permissions.py`:

```python
from rest_framework import permissions


class IsManufacturerUser(permissions.BasePermission):
    """Only allow users to access their own manufacturer's data."""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'manufacturer'):
            return obj.manufacturer == request.user.profile.manufacturer
        return True


class IsManagerOrReadOnly(permissions.BasePermission):
    """Managers can edit, others can only read."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.profile.role == 'MANAGER'
```

#### Step 6: Update Main URLs
Add to `twinengine_core/urls.py`:

```python
urlpatterns = [
    # ... existing urls
    path('api/auth/', include('apps.manufacturers.auth_urls')),
]
```

### Testing Authentication

```bash
# Register a new user
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123","manufacturer":1,"role":"OPERATOR"}'

# Get JWT token
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Access protected endpoint
curl http://127.0.0.1:8000/api/nodes/ \
  -H "Authorization: Bearer <access_token>"

# Refresh token
curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}'
```

---

## 3. Hugging Face Vision Integration

**Priority:** Medium  
**Estimated Time:** 6-8 hours  
**Dependencies:** `huggingface_hub` (already in requirements.txt)

### Purpose
Connect to Hugging Face Inference API for:
- Object detection (apples, bottles counting)
- Production line stoppage detection

### Implementation Steps

#### Step 1: Create Vision Service
Create `apps/vision_engine/services/__init__.py` and `apps/vision_engine/services/huggingface_service.py`:

```python
import os
import requests
import base64
from typing import Optional, Dict, List
from django.conf import settings


class HuggingFaceVisionService:
    """Service for interacting with Hugging Face Inference API."""
    
    def __init__(self, endpoint: str = None, api_key: str = None):
        self.endpoint = endpoint or os.getenv('HF_INFERENCE_ENDPOINT')
        self.api_key = api_key or os.getenv('HF_API_KEY')
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def detect_objects(self, image_data: bytes) -> List[Dict]:
        """
        Detect objects in an image using object detection model.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            List of detected objects with labels, scores, and bounding boxes
        """
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                data=image_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'error': str(e)}
    
    def count_objects(self, image_data: bytes, target_label: str) -> Dict:
        """
        Count specific objects in an image.
        
        Args:
            image_data: Raw image bytes
            target_label: Label to count (e.g., 'apple', 'bottle')
            
        Returns:
            Dict with count and detections
        """
        detections = self.detect_objects(image_data)
        
        if 'error' in detections:
            return detections
        
        # Filter and count target objects
        target_objects = [
            d for d in detections 
            if d.get('label', '').lower() == target_label.lower()
            and d.get('score', 0) > 0.5  # Confidence threshold
        ]
        
        return {
            'target_label': target_label,
            'count': len(target_objects),
            'detections': target_objects,
            'total_objects': len(detections)
        }
    
    def detect_production_stoppage(self, frame1: bytes, frame2: bytes, threshold: float = 0.95) -> Dict:
        """
        Detect if production has stopped by comparing two frames.
        
        Args:
            frame1: First frame bytes
            frame2: Second frame bytes
            threshold: Similarity threshold (higher = more similar = stopped)
            
        Returns:
            Dict with stoppage status and similarity score
        """
        # For production stoppage, we compare object counts
        # If counts don't change over time, production may be stopped
        
        count1 = self.count_objects(frame1, 'all')
        count2 = self.count_objects(frame2, 'all')
        
        # Simple comparison - in production, use more sophisticated methods
        if count1.get('count') == count2.get('count'):
            return {
                'is_stopped': True,
                'reason': 'No change in object count between frames',
                'frame1_count': count1.get('count'),
                'frame2_count': count2.get('count')
            }
        
        return {
            'is_stopped': False,
            'frame1_count': count1.get('count'),
            'frame2_count': count2.get('count')
        }


class VisionProcessor:
    """High-level processor for vision tasks."""
    
    def __init__(self, machine_node):
        self.machine_node = machine_node
        self.service = HuggingFaceVisionService(
            endpoint=machine_node.hf_endpoint,
            api_key=machine_node.hf_key
        )
    
    def process_frame(self, frame_data: bytes, object_type: str = 'apple') -> Dict:
        """Process a single video frame."""
        from apps.vision_engine.models import VisionLog
        
        result = self.service.count_objects(frame_data, object_type)
        
        if 'error' not in result:
            # Get current total
            last_log = VisionLog.objects.filter(
                machine_node=self.machine_node,
                object_type=object_type
            ).first()
            
            current_total = (last_log.current_total if last_log else 0) + result['count']
            
            # Create vision log
            avg_confidence = sum(d['score'] for d in result['detections']) / len(result['detections']) if result['detections'] else 0
            
            VisionLog.objects.create(
                machine_node=self.machine_node,
                object_type=object_type,
                confidence_score=avg_confidence,
                current_total=current_total
            )
            
            result['current_total'] = current_total
        
        return result
```

#### Step 2: Create Vision API Endpoint
Add to `apps/vision_engine/views.py`:

```python
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from .services.huggingface_service import VisionProcessor


class ProcessFrameView(APIView):
    """Process a video frame for object detection."""
    parser_classes = [MultiPartParser]
    
    def post(self, request):
        node_id = request.data.get('node_id')
        object_type = request.data.get('object_type', 'apple')
        frame = request.FILES.get('frame')
        
        if not node_id or not frame:
            return Response(
                {'error': 'node_id and frame are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.factory_graph.models import MachineNode
            node = MachineNode.objects.get(id=node_id)
            
            processor = VisionProcessor(node)
            result = processor.process_frame(frame.read(), object_type)
            
            return Response(result)
        except MachineNode.DoesNotExist:
            return Response(
                {'error': 'Machine node not found'},
                status=status.HTTP_404_NOT_FOUND
            )
```

#### Step 3: Add URL
Add to `apps/vision_engine/urls.py`:

```python
from .views import ProcessFrameView

urlpatterns = [
    # ... existing urls
    path('process-frame/', ProcessFrameView.as_view(), name='process-frame'),
]
```

### Testing Vision Integration

```bash
# Test object detection
curl -X POST http://127.0.0.1:8000/api/process-frame/ \
  -F "node_id=1" \
  -F "object_type=apple" \
  -F "frame=@/path/to/test_image.jpg"
```

---

## 4. Azure GPT-4o Report Generation

**Priority:** Medium  
**Estimated Time:** 4-6 hours  
**Dependencies:** `openai` (already in requirements.txt)

### Purpose
Generate executive summary reports using Azure OpenAI GPT-4o for:
- Daily production summaries
- Anomaly analysis
- Recommendations

### Implementation Steps

#### Step 1: Create Report Service
Create `apps/analytics/services/__init__.py` and `apps/analytics/services/report_service.py`:

```python
import os
from openai import AzureOpenAI
from typing import Dict, List
from datetime import date


class AzureReportService:
    """Service for generating reports using Azure OpenAI GPT-4o."""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
        )
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o')
    
    def generate_daily_report(self, manufacturer_name: str, report_date: date, 
                              shift_data: List[Dict], anomaly_data: List[Dict]) -> str:
        """
        Generate a comprehensive daily production report.
        
        Args:
            manufacturer_name: Name of the manufacturer
            report_date: Date of the report
            shift_data: List of shift log dictionaries
            anomaly_data: List of anomaly alert dictionaries
            
        Returns:
            Generated report text in Markdown format
        """
        # Prepare context for GPT-4o
        context = self._prepare_context(manufacturer_name, report_date, shift_data, anomaly_data)
        
        prompt = f"""You are an industrial operations analyst. Generate a professional daily production report based on the following data.

{context}

Generate a comprehensive report in Markdown format that includes:
1. Executive Summary (2-3 sentences)
2. Production Metrics (total units, efficiency, comparison to targets)
3. Downtime Analysis (causes, duration, impact)
4. Anomaly Report (issues detected, severity, resolution status)
5. Recommendations (actionable items for improvement)
6. Risk Assessment (potential issues to monitor)

Use professional language suitable for plant managers and executives.
Include specific numbers and percentages where available.
Keep the report concise but informative (500-800 words).
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert industrial operations analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3  # Lower temperature for more consistent reports
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating report: {str(e)}"
    
    def _prepare_context(self, manufacturer_name: str, report_date: date,
                         shift_data: List[Dict], anomaly_data: List[Dict]) -> str:
        """Prepare context string for the GPT prompt."""
        
        # Calculate aggregates
        total_units = sum(s.get('total_units', 0) for s in shift_data)
        total_downtime = sum(s.get('total_downtime', 0) for s in shift_data)
        total_anomalies = len(anomaly_data)
        critical_anomalies = len([a for a in anomaly_data if a.get('severity') == 'CRITICAL'])
        resolved_anomalies = len([a for a in anomaly_data if a.get('resolved_status')])
        
        context = f"""
## Factory: {manufacturer_name}
## Date: {report_date}

### Shift Data Summary:
- Number of shifts: {len(shift_data)}
- Total units produced: {total_units}
- Total downtime: {total_downtime:.1f} minutes
- Average units per shift: {total_units / len(shift_data) if shift_data else 0:.1f}

### Shift Details:
"""
        for i, shift in enumerate(shift_data, 1):
            context += f"""
Shift {i}:
  - Time: {shift.get('shift_start')} - {shift.get('shift_end')}
  - Units: {shift.get('total_units', 0)}
  - Downtime: {shift.get('total_downtime', 0):.1f} min
  - Anomalies: {shift.get('anomaly_count', 0)}
"""
        
        context += f"""
### Anomaly Summary:
- Total anomalies: {total_anomalies}
- Critical: {critical_anomalies}
- Resolved: {resolved_anomalies}
- Pending: {total_anomalies - resolved_anomalies}

### Anomaly Details:
"""
        for anomaly in anomaly_data[:10]:  # Limit to 10 most recent
            context += f"""
- Machine: {anomaly.get('machine_node_name', 'Unknown')}
  Prediction: {anomaly.get('ai_prediction')}
  Severity: {anomaly.get('severity')}
  Status: {'Resolved' if anomaly.get('resolved_status') else 'Active'}
"""
        
        return context
    
    def analyze_anomaly(self, sensor_data: Dict, historical_data: List[Dict]) -> str:
        """Generate analysis for a specific anomaly."""
        
        prompt = f"""Analyze this industrial sensor anomaly and provide insights:

Current Sensor Reading:
- Temperature: {sensor_data.get('temperature')}°C
- Vibration: {sensor_data.get('vibration')}
- Torque: {sensor_data.get('torque')} Nm
- RPM: {sensor_data.get('rpm')}
- Tool Wear: {sensor_data.get('tool_wear')}

Historical Average (last 24h):
- Avg Temperature: {sum(d.get('temperature', 0) for d in historical_data) / len(historical_data) if historical_data else 0:.1f}°C
- Avg Vibration: {sum(d.get('vibration', 0) for d in historical_data) / len(historical_data) if historical_data else 0:.1f}

Provide:
1. Root cause analysis (most likely causes)
2. Urgency level (Low/Medium/High/Critical)
3. Recommended actions
4. Estimated time to failure if unaddressed

Keep response concise (150-200 words).
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert in predictive maintenance."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error analyzing anomaly: {str(e)}"
```

#### Step 2: Update Report Generation View
Update `apps/analytics/views.py`:

```python
from .services.report_service import AzureReportService

class ProductionReportViewSet(viewsets.ModelViewSet):
    # ... existing code
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new production report using GPT-4o."""
        serializer = ReportGenerateSerializer(data=request.data)
        if serializer.is_valid():
            manufacturer_id = serializer.validated_data['manufacturer_id']
            report_date = serializer.validated_data['date']
            gen_type = serializer.validated_data['generation_type']
            
            manufacturer = Manufacturer.objects.get(id=manufacturer_id)
            
            # Get shift data
            shifts = ShiftLog.objects.filter(
                manufacturer=manufacturer,
                date=report_date
            )
            shift_data = ShiftLogSerializer(shifts, many=True).data
            
            # Get anomaly data
            from apps.sensors.models import AnomalyAlert
            from apps.sensors.serializers import AnomalyAlertSerializer
            
            anomalies = AnomalyAlert.objects.filter(
                sensor_data__machine_node__manufacturer=manufacturer,
                created_at__date=report_date
            ).select_related('sensor_data__machine_node')
            anomaly_data = AnomalyAlertSerializer(anomalies, many=True).data
            
            # Generate report using GPT-4o
            service = AzureReportService()
            gpt_summary = service.generate_daily_report(
                manufacturer.name,
                report_date,
                shift_data,
                anomaly_data
            )
            
            # Create and save report
            report = ProductionReport.objects.create(
                manufacturer=manufacturer,
                date=report_date,
                cloudinary_url='',  # Will be set after PDF generation
                gpt_summary=gpt_summary,
                generation_type=gen_type
            )
            
            return Response(ProductionReportSerializer(report).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### Testing GPT-4o Integration

```bash
# Set environment variables
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"

# Generate a report
curl -X POST http://127.0.0.1:8000/api/reports/generate/ \
  -H "Content-Type: application/json" \
  -d '{"manufacturer_id":1,"date":"2026-02-13","generation_type":"MANUAL"}'
```

---

## 5. Cloudinary Media Integration

**Priority:** Medium  
**Estimated Time:** 3-4 hours  
**Dependencies:** `cloudinary` (already in requirements.txt)

### Purpose
Handle media uploads for:
- Video feed storage
- Generated PDF reports
- Machine images

### Implementation Steps

#### Step 1: Configure Cloudinary
Add to `twinengine_core/settings.py`:

```python
import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)
```

#### Step 2: Create Media Service
Create `apps/analytics/services/cloudinary_service.py`:

```python
import cloudinary.uploader
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
import io
import markdown
from datetime import date


class CloudinaryService:
    """Service for Cloudinary media operations."""
    
    @staticmethod
    def upload_file(file_data, folder: str = 'twinengine', 
                    resource_type: str = 'auto') -> dict:
        """
        Upload a file to Cloudinary.
        
        Args:
            file_data: File bytes or file path
            folder: Cloudinary folder to store in
            resource_type: 'auto', 'image', 'video', 'raw'
            
        Returns:
            Cloudinary upload response dict
        """
        try:
            result = cloudinary.uploader.upload(
                file_data,
                folder=folder,
                resource_type=resource_type
            )
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def upload_video(video_data, machine_node_name: str) -> dict:
        """Upload a video feed clip."""
        return CloudinaryService.upload_file(
            video_data,
            folder=f'twinengine/videos/{machine_node_name}',
            resource_type='video'
        )
    
    @staticmethod
    def delete_file(public_id: str) -> bool:
        """Delete a file from Cloudinary."""
        try:
            cloudinary.uploader.destroy(public_id)
            return True
        except:
            return False


class PDFReportGenerator:
    """Generate PDF reports for upload to Cloudinary."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_report_pdf(self, report_content: str, 
                           manufacturer_name: str, 
                           report_date: date) -> bytes:
        """
        Generate a PDF from report content.
        
        Args:
            report_content: Markdown content from GPT-4o
            manufacturer_name: Name of manufacturer
            report_date: Report date
            
        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        title_style = self.styles['Title']
        story.append(Paragraph(f"Production Report - {manufacturer_name}", title_style))
        story.append(Paragraph(f"Date: {report_date}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Convert Markdown to HTML then to Paragraphs
        html_content = markdown.markdown(report_content)
        
        # Simple parsing - in production use a proper HTML parser
        for line in report_content.split('\n'):
            if line.startswith('## '):
                story.append(Spacer(1, 12))
                story.append(Paragraph(line[3:], self.styles['Heading2']))
            elif line.startswith('### '):
                story.append(Spacer(1, 8))
                story.append(Paragraph(line[4:], self.styles['Heading3']))
            elif line.startswith('- '):
                story.append(Paragraph(f"• {line[2:]}", self.styles['Normal']))
            elif line.strip():
                story.append(Paragraph(line, self.styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def upload_report(self, report_content: str, 
                      manufacturer_name: str, 
                      report_date: date) -> dict:
        """Generate PDF and upload to Cloudinary."""
        pdf_bytes = self.generate_report_pdf(report_content, manufacturer_name, report_date)
        
        return CloudinaryService.upload_file(
            pdf_bytes,
            folder=f'twinengine/reports/{manufacturer_name}',
            resource_type='raw'
        )
```

#### Step 3: Update Report Generation
Update the report generation to include PDF upload:

```python
# In apps/analytics/views.py generate action

from .services.cloudinary_service import PDFReportGenerator

# After generating gpt_summary
pdf_generator = PDFReportGenerator()
upload_result = pdf_generator.upload_report(
    gpt_summary,
    manufacturer.name,
    report_date
)

cloudinary_url = upload_result.get('url', '') if upload_result.get('success') else ''

# Create report with URL
report = ProductionReport.objects.create(
    manufacturer=manufacturer,
    date=report_date,
    cloudinary_url=cloudinary_url,
    gpt_summary=gpt_summary,
    generation_type=gen_type
)
```

### Testing Cloudinary

```bash
# Set environment variables
export CLOUDINARY_CLOUD_NAME="your-cloud-name"
export CLOUDINARY_API_KEY="your-api-key"
export CLOUDINARY_API_SECRET="your-api-secret"

# Test upload via Python shell
python manage.py shell
>>> from apps.analytics.services.cloudinary_service import CloudinaryService
>>> result = CloudinaryService.upload_file(open('test.jpg', 'rb'), 'test')
>>> print(result)
```

---

## 6. Unit Tests

**Priority:** Low  
**Estimated Time:** 8-10 hours  
**Dependencies:** `pytest`, `pytest-django`

### Implementation Steps

#### Step 1: Install Testing Dependencies
```bash
pip install pytest pytest-django pytest-cov factory_boy
```

Add to `requirements.txt`:
```
pytest
pytest-django
pytest-cov
factory_boy
```

#### Step 2: Create pytest Configuration
Create `pytest.ini` in backend root:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = twinengine_core.settings
python_files = tests.py test_*.py *_tests.py
addopts = --reuse-db -v
```

#### Step 3: Create Test Factories
Create `apps/manufacturers/tests/factories.py`:

```python
import factory
from django.contrib.auth.models import User
from apps.manufacturers.models import Manufacturer, UserProfile


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class ManufacturerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Manufacturer
    
    name = factory.Sequence(lambda n: f'Factory {n}')
    corporate_id = factory.Sequence(lambda n: f'CORP{n:04d}')
    contact_email = factory.LazyAttribute(lambda o: f'contact@{o.name.lower().replace(" ", "")}.com')
    subscription_tier = 'BASIC'


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile
    
    user = factory.SubFactory(UserFactory)
    manufacturer = factory.SubFactory(ManufacturerFactory)
    role = 'OPERATOR'
```

#### Step 4: Create Model Tests
Create `apps/manufacturers/tests/test_models.py`:

```python
import pytest
from django.db import IntegrityError
from .factories import ManufacturerFactory, UserProfileFactory


@pytest.mark.django_db
class TestManufacturerModel:
    
    def test_create_manufacturer(self):
        manufacturer = ManufacturerFactory()
        assert manufacturer.id is not None
        assert manufacturer.name.startswith('Factory')
    
    def test_unique_corporate_id(self):
        ManufacturerFactory(corporate_id='TEST001')
        with pytest.raises(IntegrityError):
            ManufacturerFactory(corporate_id='TEST001')
    
    def test_str_representation(self):
        manufacturer = ManufacturerFactory(name='Acme Corp', corporate_id='ACME001')
        assert str(manufacturer) == 'Acme Corp (ACME001)'


@pytest.mark.django_db
class TestUserProfileModel:
    
    def test_create_user_profile(self):
        profile = UserProfileFactory()
        assert profile.user is not None
        assert profile.manufacturer is not None
    
    def test_user_profile_cascade_delete(self):
        profile = UserProfileFactory()
        user = profile.user
        user.delete()
        assert not UserProfile.objects.filter(id=profile.id).exists()
```

#### Step 5: Create API Tests
Create `apps/manufacturers/tests/test_views.py`:

```python
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from .factories import ManufacturerFactory, UserProfileFactory


@pytest.mark.django_db
class TestManufacturerAPI:
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    def test_list_manufacturers(self, api_client):
        ManufacturerFactory.create_batch(3)
        response = api_client.get('/api/manufacturers/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_create_manufacturer(self, api_client):
        data = {
            'name': 'New Factory',
            'corporate_id': 'NEW001',
            'contact_email': 'new@factory.com',
            'subscription_tier': 'PRO'
        }
        response = api_client.post('/api/manufacturers/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Factory'
    
    def test_retrieve_manufacturer(self, api_client):
        manufacturer = ManufacturerFactory()
        response = api_client.get(f'/api/manufacturers/{manufacturer.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == manufacturer.name
    
    def test_update_manufacturer(self, api_client):
        manufacturer = ManufacturerFactory()
        response = api_client.patch(
            f'/api/manufacturers/{manufacturer.id}/',
            {'name': 'Updated Name'}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'
    
    def test_delete_manufacturer(self, api_client):
        manufacturer = ManufacturerFactory()
        response = api_client.delete(f'/api/manufacturers/{manufacturer.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
```

#### Step 6: Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific app tests
pytest apps/manufacturers/

# Run with verbose output
pytest -v
```

---

## 7. PostgreSQL/Neon Migration

**Priority:** Low  
**Estimated Time:** 2-3 hours  
**Dependencies:** `psycopg2-binary` (already in requirements.txt)

### Implementation Steps

#### Step 1: Create Neon Database
1. Go to [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string

#### Step 2: Update Settings
Update `twinengine_core/settings.py`:

```python
import dj_database_url

# Database
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

#### Step 3: Add dj-database-url
```bash
pip install dj-database-url
```

Add to `requirements.txt`:
```
dj-database-url
```

#### Step 4: Set Environment Variable
Add to `.env`:
```
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require
```

#### Step 5: Run Migrations
```bash
python manage.py migrate
```

### Testing Database Connection

```bash
python manage.py dbshell
# Should connect to PostgreSQL

python manage.py showmigrations
# Should show all migrations applied
```

---

## 8. Background Tasks with Celery

**Priority:** Low  
**Estimated Time:** 4-6 hours  
**Dependencies:** `celery`, `redis`

### Purpose
Handle long-running tasks asynchronously:
- Report generation
- Bulk data processing
- Vision inference batches

### Implementation Steps

#### Step 1: Install Dependencies
```bash
pip install celery redis
```

Add to `requirements.txt`:
```
celery[redis]
```

#### Step 2: Create Celery Configuration
Create `twinengine_core/celery.py`:

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'twinengine_core.settings')

app = Celery('twinengine')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

#### Step 3: Update __init__.py
Update `twinengine_core/__init__.py`:

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

#### Step 4: Add Celery Settings
Add to `twinengine_core/settings.py`:

```python
# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

#### Step 5: Create Tasks
Create `apps/analytics/tasks.py`:

```python
from celery import shared_task
from .services.report_service import AzureReportService
from .services.cloudinary_service import PDFReportGenerator


@shared_task
def generate_report_async(manufacturer_id: int, report_date: str):
    """Generate production report asynchronously."""
    from .models import ProductionReport, ShiftLog
    from apps.manufacturers.models import Manufacturer
    from apps.sensors.models import AnomalyAlert
    from datetime import datetime
    
    manufacturer = Manufacturer.objects.get(id=manufacturer_id)
    date_obj = datetime.strptime(report_date, '%Y-%m-%d').date()
    
    # Get data
    shifts = ShiftLog.objects.filter(manufacturer=manufacturer, date=date_obj)
    anomalies = AnomalyAlert.objects.filter(
        sensor_data__machine_node__manufacturer=manufacturer,
        created_at__date=date_obj
    )
    
    # Generate report
    service = AzureReportService()
    from .serializers import ShiftLogSerializer, AnomalyAlertSerializer
    
    gpt_summary = service.generate_daily_report(
        manufacturer.name,
        date_obj,
        ShiftLogSerializer(shifts, many=True).data,
        AnomalyAlertSerializer(anomalies, many=True).data
    )
    
    # Generate and upload PDF
    pdf_generator = PDFReportGenerator()
    upload_result = pdf_generator.upload_report(gpt_summary, manufacturer.name, date_obj)
    
    # Save to database
    report = ProductionReport.objects.create(
        manufacturer=manufacturer,
        date=date_obj,
        cloudinary_url=upload_result.get('url', ''),
        gpt_summary=gpt_summary,
        generation_type='AUTO'
    )
    
    return {'report_id': report.id, 'success': True}


@shared_task
def process_sensor_batch(sensor_readings: list):
    """Process a batch of sensor readings."""
    from apps.sensors.models import SensorData
    
    objects = [SensorData(**reading) for reading in sensor_readings]
    created = SensorData.objects.bulk_create(objects)
    
    return {'created': len(created)}
```

#### Step 6: Run Celery Worker

```bash
# Start Redis (if not running)
redis-server

# Start Celery worker
celery -A twinengine_core worker -l info

# Start Celery beat (for scheduled tasks)
celery -A twinengine_core beat -l info
```

### Testing Celery

```python
# In Django shell
from apps.analytics.tasks import generate_report_async

# Queue task
result = generate_report_async.delay(1, '2026-02-13')

# Check result
result.status
result.get()  # Wait for result
```

---

## Summary Checklist

| # | Task | Priority | Time | Status |
|---|------|----------|------|--------|
| 1 | WebSocket Consumers | High | 4-6h | ⬜ |
| 2 | Authentication (JWT) | High | 3-4h | ⬜ |
| 3 | Hugging Face Integration | Medium | 6-8h | ⬜ |
| 4 | Azure GPT-4o Integration | Medium | 4-6h | ⬜ |
| 5 | Cloudinary Integration | Medium | 3-4h | ⬜ |
| 6 | Unit Tests | Low | 8-10h | ⬜ |
| 7 | PostgreSQL Migration | Low | 2-3h | ⬜ |
| 8 | Celery Background Tasks | Low | 4-6h | ⬜ |

**Total Estimated Time:** 34-47 hours

---

## Environment Variables Required

Add these to `.env` before implementing:

```bash
# Authentication
SECRET_KEY=your-production-secret-key

# Database (for Neon)
DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require

# Redis (for Celery & Channels)
REDIS_URL=redis://localhost:6379/0

# Hugging Face
HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxx
HF_INFERENCE_ENDPOINT=https://api-inference.huggingface.co/models/facebook/detr-resnet-50

# Azure OpenAI
AZURE_OPENAI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```
