# TwinEngine - AI-Powered Digital Twin Platform

## 1. Overview

### 1.1 Title

**AI-Powered Digital Twin Platform for Enterprise Operations**

Enterprises operate complex systems involving supply chains, operations, workforce, and infrastructure. Decision-makers lack the ability to simulate outcomes before acting.

This project proposes an AI-powered digital twin platform that creates a virtual replica of enterprise operations, enabling simulation, forecasting, and optimisation through a cloud-based system.

### 1.2 Problem Statement

Organisations face:

- Limited visibility into system interactions
- No ability to simulate decisions
- Reactive operations management
- There is no accessible, AI-driven enterprise digital twin platform for operational decision-making.

### 1.3 Goal

**Develop a digital twin platform that:**

- Ingests real-time operational data
- Builds predictive models of system behaviour
- Simulates future scenarios
- Optimises decisions using AI
- Visualises outcomes through an interactive UI

### 1.4 Value Proposition

TwinEngine provides an accessible, modular AI-Powered Digital Twin platform that transforms static video feeds and raw sensor data into an interactive 3D command centre, enabling real-time bottleneck detection and automated operational reporting.

---

## 2. Scope & Control

### 2.1 In-Scope

- **3D Digital Twin Interface:** Development of an interactive 3D factory floor visualization using React and Three.js where machines are represented as clickable nodes.
- **Computer Vision Monitoring:** Implementation of object detection models to count units (e.g., apples, bottles) in real-time and detect process stoppages.
- **Anomaly Detection System:** Training and integration of ML models to identify irregularities in simulated sensor data, such as abnormal temperature or vibration levels.
- **Real-time Alerting:** A WebSocket-based system to change node colours (e.g., to red) and trigger UI notifications when an error or bottleneck is detected.
- **Automated Executive Reporting:** Integration of Azure GPT-4o to process operational logs into professional daily summary reports.
- **Interactive Control Panel:** Features like data tweaking sliders to simulate anomalies and video speed controls to test efficiency monitoring.

### 2.2 Out-of-Scope

- **Physical Hardware Integration:** Connecting to actual PLC (Programmable Logic Controller) hardware or industrial IoT sensors in the current version.
- **Mobile Application:** Development of native iOS or Android apps; the platform will remain a desktop-optimised web application.
- **Autonomous Machine Control:** The system is an advisory and monitoring platform; it will not send "stop" commands back to physical machinery.
- **AR/VR Integration:** Immersive virtual reality inspections are deferred for future enhancements.

#### Comparison Table

| Metric | Traditional Monitoring | TwinEngine |
|--------|------------------------|------------|
| Response Time | Manual inspection (minutes to hours) | Instant (real-time 3D alerts) |
| Reporting | Manual daily logs | Automated (LLM summaries) |
| Deployment | Rigged, hardware-heavy | Modular, software-defined |

### 2.3 Assumptions

- **Video Feed Availability:** It is assumed that high-quality video clips/feed of the manufacturing process are provided by industries for simulation.
- **Cloud Connectivity:** The system assumes constant internet access to reach Neon (database), Cloudinary, and AI inference APIs.
- **Simulated Data Accuracy:** The Kaggle-sourced machine data is assumed to be a reasonable proxy for real-world industrial sensor patterns.

### 2.4 Constraints

- **API Latency:** Real-time performance is subject to the response times of the Hugging Face and Azure GPT-4o APIs.
- **Processing Power:** The application will rely on cloud-based AI inference to stay within the limits of standard web hosting services.
- **Project Timeline:** All core features must be completed within the academic semester deadline.

### 2.5 Dependencies

- **Cloud Hosting:** Dependency on Render (backend) and Vercel (frontend) for deployment.
- **AI Models:** Reliance on pre-trained models from Hugging Face and proprietary APIs from Azure.
- **Database:** Continuous availability of the Neon serverless PostgreSQL instance.

---

## 3. Team Management & Planning

### 3.1 Team Roles and Responsibilities

| Member | Role | Responsibilities | Key Skills |
|--------|------|------------------|------------|
| Amrita Singh | Project Lead / ML Engineer | Model selection, training vision models for apple/bottle detection, and anomaly logic. | Python, ML (YOLO/Hugging Face), Azure AI |
| Akshat Gupta | System Architect / Full-Stack | 3D UI development (Three.js), Django backend, and Cloudinary/Neon integration. | React, Django, Three.js, PostgreSQL |

### 3.2 Week-wise Plan (8-Week Milestone Schedule)

| Week | Milestones | Primary Deliverable |
|------|------------|---------------------|
| Week 1 | Requirements & Synopsis | Finalized Project Synopsis and Scope. |
| Week 2 | Tech Stack & Environment | Neon DB setup, Cloudinary upload, and Django scaffolding. |
| Week 3 | 3D Foundation | Basic Three.js factory floor with static "Machine Nodes." |
| Week 4 | Vision Integration | Hugging Face API connection for apple/bottle counting. |
| Week 5 | Anomaly & Control | Logic for sensor sliders and "Red-Tile" error states. |
| Week 6 | Intelligence Layer | Integration of Azure GPT-4o for log-to-report generation. |
| Week 7 | System Hardening | Bug fixing, UI polishing, and performance testing. |
| Week 8 | Final Presentation | Deployment on Vercel/Render and project demo. |

---

## 4. Users & UX

### 4.1 Personas

- **Factory Operations Manager:** Needs a high-level view of the entire production line to monitor overall efficiency and identify bottlenecks quickly. They rely on automated reports for shift summaries.
- **Maintenance Engineer:** Technical user who monitors machine "health" data (vibration, temperature). They use the 3D twin to pinpoint exactly which machine node is trending toward a failure.

### 4.2 Top User Journeys

1. **Dashboard Login & Overview:** User logs in and views the real-time 3D factory floor. All nodes are green, indicating normal operations.
2. **Anomaly Investigation:** A machine node turns **Red** due to a detected stoppage. The user clicks the node to open a live video feed and diagnostic panel.
3. **Efficiency Testing:** The user uses the "Speed Slider" on a video feed to simulate a slowdown in production and observes how the system triggers a "Low Efficiency" warning.
4. **Report Generation:** At the end of a shift, the user requests an AI-generated summary of all logs and errors recorded by the system.

### 4.3 User Stories

- **As an Operations Manager,** I want to see a 3D visualization of my factory floor so that I can immediately identify which part of the production line is experiencing a delay.
- **As a Maintenance Engineer,** I want to receive real-time alerts for high machine vibrations so that I can perform proactive repairs before a total breakdown occurs.
- **As a Plant Supervisor,** I want an AI-generated daily report so that I can review production trends without manually sorting through hours of logs.

### 4.4 Accessibility & Localisation

- **Intuitive 3D Navigation:** Simple mouse-based controls for zooming and rotating the factory map, making it accessible to non-technical staff.
- **Colour-Coded Status Alerts:** Standardised green (normal), yellow (warning), and red (error) signals for clear communication.
- **Simplified Language:** GPT-4o reports will use professional but simple terminology to ensure clarity for all stakeholders.

---

## 5. Market and Competitors

### 5.1 Competitor Table

| Competitor | Product Type | Target Users | Key Features | Pricing | Strengths / Weaknesses | Our Differentiator |
|------------|--------------|--------------|--------------|---------|------------------------|-------------------|
| Siemens / GE Digital | Enterprise Legacy Systems | Multi-national corporations | Deep integration, heavy IoT sensors, custom hardware. | High (Enterprise licensing) | S: Robust & powerful. W: Rigid, extremely expensive, months to deploy. | Lightweight & Modular: Fast deployment using software-defined nodes. |
| Tableau / PowerBI | Data Dashboards | Analysts & Management | Static charts, historical data trends, visual graphs. | SaaS (Subscription) | S: Great for long-term trends. W: Lacks spatial context; no real-time vision. | Spatial 3D Context: Visualization of the physical factory floor in real-time. |
| Manual CCTV | Traditional Monitoring | Security & Supervisors | Raw video feeds, manual unit counting. | Low (CCTV hardware) | S: Simple to install. W: High human error; no automated logic or alerting. | AI Intelligence: Automated counting and anomaly detection on the same feed. |

### 5.2 Positioning

TwinEngine focuses on **Personalised Spatial Operations**. Unlike legacy systems that overwhelm users with data tables, TwinEngine prioritises an "Explainable Twin" approach where AI translates complex machine signals into simple 3D visual cues and GPT-generated reports.

**Measurable Delta:**

- **Problem Identification:** ≤10s vs 5–20 min (manual inspection).
- **Deployment Speed:** Days vs Months (standard industrial setups).
- **Reporting:** Instant AI summaries vs hours of manual log review.

---

## 6. Objectives and Success Metrics

- **O1: Real-Time Visualization Sync:** Ensure the 3D factory floor (Three.js) updates within **< 500ms** of a backend state change (KPI: Sync Latency).
- **O2: Vision Accuracy:** Achieve at least **90% accuracy** in unit counting (apples/bottles) across standard video conditions (KPI: Mean Average Precision).
- **O3: Anomaly Detection Speed:** Trigger a "Red Node" alert within **2 seconds** of detecting a stoppage or sensor anomaly (KPI: Detection Latency).
- **O4: Report Generation Quality:** Produce a coherent daily operational report using GPT-4o with zero "hallucinations" regarding the logged error data (KPI: Report Accuracy).
- **O5: System Accessibility:** Ensure the 3D interface is navigable with a standard mouse/trackpad, resulting in a **< 2-minute learning curve** for new users (KPI: Time to Task Completion).

---

## 7. Key Features

| Feature | Description | Priority | Dependencies | Acceptance Criteria |
|---------|-------------|----------|--------------|---------------------|
| Interactive 3D Twin | A React/Three.js dashboard showing the factory layout with clickable machine nodes. | Must | React, Three.js | GIVEN a user clicks a node WHEN the machine is active THEN a live diagnostic panel opens. |
| Vision Flow Monitor | AI module that counts items and detects stoppages via Cloudinary video streams. | Must | Hugging Face API | GIVEN a video loop WHEN counting stops during "on" hours THEN an error is triggered. |
| Sensor Simulator | Backend logic and UI sliders to tweak temperature and vibration data. | Must | Django | GIVEN a slider is moved to "Max" WHEN the value exceeds the threshold THEN the node turns Red. |
| AI Report Agent | GPT-4o integration to summarize logs into a professional text report. | Should | Azure OpenAI | GIVEN a shift ends WHEN the report is requested THEN a 3rd-party readable summary is produced. |

---

## 8. Technical Design

### 8.1 High-Level Architecture

TwinEngine follows a **Layered Cloud Architecture** designed to separate the heavy AI processing from the user interface, ensuring a smooth 3D experience.

- **Interaction Layer (Client):** A React-based Single Page Application (SPA) using **Three.js** to render the 3D factory floor. It communicates with the backend via REST for configuration and **WebSockets** for real-time error alerts.
- **Orchestration Layer (Backend):** A **Django** server that acts as the "Twin Brain." It manages the state of each machine node (e.g., "Normal", "Alert", "Offline") and coordinates data flow between the vision models and the database.
- **Intelligence Layer (AI Services):** Offloads computation to **Hugging Face** or **Azure AI Custom Vision**. These services process video frames from **Cloud Storage** and return object counts and anomaly scores.
- **Data Layer:** **Neon (PostgreSQL)** stores the factory configuration (Nodes and Edges), while **Cloud Storage/Live feeds** handles the streaming video assets.

### 8.2 API Specifications

The backend provides a set of endpoints to manage the modular factory nodes.

| Endpoint | Method | Purpose | Request Schema | Response |
|----------|--------|---------|----------------|----------|
| `/api/nodes/` | GET | Fetch all factory nodes for 3D rendering. | None | 200 `[{id, name, status, position}]` |
| `/api/nodes/{id}/` | GET | Get detailed live feed and sensor data for a node. | None | 200 `{camera_url, counts, vibration}` |
| `/api/anomaly/trigger/` | POST | Update node status based on ML/slider data. | `node_id, status` | 201 `{updated: true}` |
| `/api/reports/daily/` | GET | Retrieve GPT-4o generated operational summary. | `date` | 200 `{report_text}` |

### 8.2.1 WebSocket Endpoints (Real-time Communication)

The platform uses **Django Channels** with WebSockets to enable real-time, bidirectional communication between the backend and connected clients. This is critical for the Digital Twin's core value proposition: **instant visual feedback**.

#### Why WebSockets?

Traditional REST APIs follow a request-response pattern where the client must constantly poll the server for updates. For a real-time 3D visualization system, this approach creates:
- **Latency issues:** Polling delays mean status changes aren't reflected instantly
- **Server load:** Hundreds of clients polling every second wastes resources
- **Poor UX:** Users see stale data until the next poll cycle

WebSockets maintain a persistent, open connection, allowing the server to **push** updates to all connected clients the moment something changes. When a machine goes into error state, every connected dashboard sees the node turn red within milliseconds.

#### WebSocket Endpoints

| Endpoint | Purpose | Connection Example |
|----------|---------|-------------------|
| `ws://host/ws/factory/<manufacturer_id>/` | Factory floor real-time updates | `ws://localhost:8000/ws/factory/1/` |
| `ws://host/ws/alerts/` | Global alerts stream (all manufacturers) | `ws://localhost:8000/ws/alerts/` |
| `ws://host/ws/alerts/<manufacturer_id>/` | Manufacturer-specific alerts | `ws://localhost:8000/ws/alerts/1/` |

#### Event Types

**Factory Floor Consumer (`/ws/factory/<id>/`)**

| Event | Direction | Description | Payload |
|-------|-----------|-------------|---------|
| `initial_state` | Server → Client | Sent on connection with all nodes | `{type, manufacturer_id, nodes[]}` |
| `node_status_change` | Server → Client | Broadcast when a node's status changes | `{type, node_id, node_name, status, previous_status, timestamp}` |
| `sensor_update` | Server → Client | Broadcast when new sensor data arrives | `{type, node_id, node_name, data{}, timestamp}` |
| `alert_broadcast` | Server → Client | Broadcast when a new alert is created | `{type, alert{}}` |
| `request_status` | Client → Server | Request current state refresh | `{type: "request_status"}` |
| `ping` / `pong` | Bidirectional | Connection health check | `{type: "ping"}` → `{type: "pong"}` |

**Alert Consumer (`/ws/alerts/`)**

| Event | Direction | Description | Payload |
|-------|-----------|-------------|---------|
| `initial_alerts` | Server → Client | Sent on connection with unresolved alerts | `{type, count, alerts[]}` |
| `new_alert` | Server → Client | Broadcast when anomaly is detected | `{type, alert{}, timestamp}` |
| `alert_resolved` | Server → Client | Broadcast when alert is resolved | `{type, alert_id, resolved_by, timestamp}` |
| `alert_count` | Server → Client | Current count of active alerts | `{type, count}` |

#### How It Works

1. **Frontend connects** to `ws://host/ws/factory/1/` when loading the 3D dashboard
2. **Server sends** `initial_state` with all machine nodes and their current status
3. **Frontend renders** the 3D scene with appropriate colors (green=NORMAL, yellow=WARNING, red=ERROR)
4. **When status changes** (via API call, ML detection, or slider), server broadcasts `node_status_change`
5. **All connected clients** receive the update and instantly update their 3D visualization

#### Testing WebSocket Endpoints

**Prerequisites:**
```bash
# The server must run via Daphne (ASGI server) for WebSocket support
cd twin_engine_backend
source venv/bin/activate
pip install websockets  # For testing
daphne -b 0.0.0.0 -p 8000 twinengine_core.asgi:application
```

**Test 1: Basic Connection (Python)**
```python
import asyncio
import websockets
import json

async def test_connection():
    async with websockets.connect('ws://localhost:8000/ws/factory/1/') as ws:
        # Receive initial state
        response = await ws.recv()
        data = json.loads(response)
        print(f"Connected! Type: {data['type']}")
        print(f"Nodes: {len(data['nodes'])}")
        
        # Test ping/pong
        await ws.send(json.dumps({'type': 'ping'}))
        pong = await ws.recv()
        print(f"Ping response: {json.loads(pong)['type']}")

asyncio.run(test_connection())
```

**Test 2: Real-time Broadcast (Two terminals)**

Terminal 1 - WebSocket Listener:
```python
import asyncio
import websockets
import json

async def listen():
    async with websockets.connect('ws://localhost:8000/ws/factory/1/') as ws:
        print("Listening for broadcasts...")
        while True:
            msg = await ws.recv()
            print(f"Received: {json.loads(msg)}")

asyncio.run(listen())
```

Terminal 2 - Trigger Status Change:
```bash
curl -X POST http://localhost:8000/api/nodes/1/update_status/ \
  -H "Content-Type: application/json" \
  -d '{"status": "ERROR"}'
```

Expected output in Terminal 1:
```json
{
  "type": "node_status_change",
  "node_id": 1,
  "node_name": "Roller-01",
  "status": "ERROR",
  "previous_status": "NORMAL",
  "timestamp": "2026-02-21T18:00:00.000000+00:00"
}
```

**Test 3: JavaScript (Browser Console)**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/factory/1/');

ws.onopen = () => console.log('Connected!');
ws.onmessage = (event) => console.log('Received:', JSON.parse(event.data));
ws.onerror = (error) => console.error('Error:', error);

// Send ping
ws.send(JSON.stringify({type: 'ping'}));
```

**Test 4: Alerts Stream**
```python
import asyncio
import websockets
import json

async def test_alerts():
    async with websockets.connect('ws://localhost:8000/ws/alerts/') as ws:
        response = await ws.recv()
        data = json.loads(response)
        print(f"Active alerts: {data['count']}")
        print(f"Alerts: {data['alerts']}")

asyncio.run(test_alerts())
```

#### Integration with 3D Frontend

In React/Three.js, connect to WebSocket on component mount:

```javascript
import { useEffect, useState } from 'react';

function useFactoryWebSocket(manufacturerId) {
  const [nodes, setNodes] = useState([]);
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/factory/${manufacturerId}/`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'initial_state') {
        setNodes(data.nodes);
      } else if (data.type === 'node_status_change') {
        setNodes(prev => prev.map(node => 
          node.id === data.node_id 
            ? { ...node, status: data.status }
            : node
        ));
      }
    };
    
    return () => ws.close();
  }, [manufacturerId]);
  
  return nodes;
}
```

### 8.3 Data Design: Core Entities

To remain modular, the database uses a graph-like structure.

- **Node:** Stores the machine type, location on the 3D grid, Cloudinary video URL, and associated ML model ID.
- **Edge:** Defines the connection between nodes (e.g., "Washing" flows to "Grinding").
- **SensorLog:** Stores historical counts and simulated vibration/temperature data for each node.
- **Alert:** Records all "Red Tile" events, including the timestamp and the reasoning provided by the AI.

---

## 9. Quality: NFRs and Testing

### 9.1 Non-functional Requirements (NFRs)

These targets ensure the platform feels professional and reliable.

| Metric | Target (SLO) | Measurement |
|--------|--------------|-------------|
| Sync Latency | < 500 ms | Time from backend event to 3D UI update. |
| Uptime | ≥ 99% | Availability of the web services on Render/Vercel. |
| Vision Accuracy | ≥ 90% | Success rate of the YOLO model in counting units. |
| Usability | < 2 min | Time for a new user to learn the 3D navigation. |

### 9.2 Test Plan

We will use a combination of automated and manual testing to verify the "Twin" logic.

- **Anomaly Simulation:** Manually pausing video feeds or using backend sliders to verify if the 3D node turns Red correctly.
- **Integration Testing:** Ensuring the Hugging Face API results are correctly parsed and stored in the Neon database.
- **UI/UX Testing:** Conducting "hallway usability tests" with peers to ensure the Three.js controls are intuitive.

---

## 10. Risks and Mitigations

We have identified potential roadblocks and their solutions to ensure the project meets the academic deadline.

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API Rate Limits | High | Medium | Implement caching and limit the frequency of frames sent to the AI model. |
| 3D Rendering Lag | Medium | High | Optimize Three.js geometry and use low-poly models for machine nodes. |
| Model Inaccuracy | Low | Medium | Fine-tune the YOLO model using a more diverse dataset of industrial clips. |
| Schedule Slip | Medium | High | Maintain a strict 8-week milestone plan with weekly progress demos. |

---

## 11. Appendices

### Glossary

- **Digital Twin:** A virtual representation of a physical asset or process.
- **Node:** An individual machine or zone within the factory graph.
- **Inference:** The process of a trained AI model making predictions on new data.

---

## 12. References

### Digital Twin Research Papers

- https://www.sciencedirect.com/science/article/pii/S
- https://www.researchgate.net/publication/394889118_Robot_digital_twin_systems_in_manufacturing_Technologies_applications_trends_and_challenges

### Docs & Guides

- Three.js Documentation
- Azure multi-modals docs
- Django Framework Guides
- Hugging Face Inference API Docs