To implement the modular "TwinEngine" platform, you will create a series of models across your five Django apps. These models are designed to handle multi-tenancy, 3D spatial mapping, AI inference, and automated reporting.

---

## 🏗️ 1. App: `manufacturers`

**Role:** Manages the multi-tenant SaaS layer, ensuring data isolation between different clients.

| Model | Purpose | Key Fields (Approx. Count) |
| --- | --- | --- |
| **Manufacturer** | Stores corporate data for registered factory owners. | **4 Fields:** Name, Corporate ID, Contact Email, Subscription Tier. |
| **UserProfile** | Extends the default User to link staff to a specific Manufacturer. | **3 Fields:** User (OneToOne), Manufacturer (FK), Role (Manager/Operator). |

---

## 🔗 2. App: `factory_graph`

**Role:** The core "Digital Twin" configuration engine for 3D nodes and connections.

| Model | Purpose | Key Fields (Approx. Count) |
| --- | --- | --- |
| **MachineType** | Defines the generic machine template and its 3D assets. | **3 Fields:** Name (Char), Model_3D_EmbedCode (example : <div class="sketchfab-embed-wrapper"> <iframe title="Dekogon - Roller Machine" frameborder="0" allowfullscreen mozallowfullscreen="true" webkitallowfullscreen="true" allow="autoplay; fullscreen; xr-spatial-tracking" xr-spatial-tracking execution-while-out-of-viewport execution-while-not-rendered web-share src="https://sketchfab.com/models/9fa6d94f4e3342a0b8adfd922e8c1901/embed"> </iframe> <p style="font-size: 13px; font-weight: normal; margin: 5px; color: #4A4A4A;"> <a href="https://sketchfab.com/3d-models/dekogon-roller-machine-9fa6d94f4e3342a0b8adfd922e8c1901?utm_medium=embed&utm_campaign=share-popup&utm_content=9fa6d94f4e3342a0b8adfd922e8c1901" target="_blank" rel="nofollow" style="font-weight: bold; color: #1CAAD9;"> Dekogon - Roller Machine </a> by <a href="https://sketchfab.com/plord?utm_medium=embed&utm_campaign=share-popup&utm_content=9fa6d94f4e3342a0b8adfd922e8c1901" target="_blank" rel="nofollow" style="font-weight: bold; color: #1CAAD9;"> Bartek Nowak </a> on <a href="https://sketchfab.com?utm_medium=embed&utm_campaign=share-popup&utm_content=9fa6d94f4e3342a0b8adfd922e8c1901" target="_blank" rel="nofollow" style="font-weight: bold; color: #1CAAD9;">Sketchfab</a></p></div>), Description. |
| **MachineNode** | The specific instance of a machine in a 3D coordinate space. | **10 Fields:** Name, Manufacturer (FK), MachineType (FK), pos_x, pos_y, pos_z, Video_Feed_URL, HF_Endpoint, HF_Key, Status. |
| **MachineEdge** | Explicitly defines the directional material flow between nodes. | **3 Fields:** SourceNode (FK), TargetNode (FK), FlowType. |

---

## 👁️ 3. App: `vision_engine`

**Role:** Manages real-time object detection and production unit logic.

| Model | Purpose | Key Fields (Approx. Count) |
| --- | --- | --- |
| **VisionLog** | Records every item detected and counted by the AI. | **5 Fields:** MachineNode (FK), Object_Type, Timestamp, Confidence_Score, Current_Total. |
| **DetectionZone** | Stores the line coordinates for counting logic per machine. | **4 Fields:** MachineNode (FK), Line_Y_Coordinate, Active_Status, Loop_Count. |

---

## ⚡ 4. App: `sensors`

**Role:** Gateway for "IoT" vibration/temperature data and predictive maintenance.

| Model | Purpose | Key Fields (Approx. Count) |
| --- | --- | --- |
| **SensorData** | Stores telemetry from your Flask Mock App or real IoT devices. | **7 Fields:** MachineNode (FK), Temp, Vibration, Torque, RPM, Tool_Wear, Timestamp. |
| **AnomalyAlert** | Log of ambiguity detections (Good/Bad) from the ML model. | **4 Fields:** SensorData (FK), AI_Prediction, Severity, Resolved_Status. |

---

## 📊 5. App: `analytics`

**Role:** Handles end-of-shift processing and Cloudinary report management.

| Model | Purpose | Key Fields (Approx. Count) |
| --- | --- | --- |
| **ShiftLog** | Aggregated data for a specific working hour window. | **5 Fields:** Manufacturer (FK), Date, Total_Units, Total_Downtime, Anomaly_Count. |
| **ProductionReport** | Stores links to the finalized GPT-4o PDFs on Cloudinary. | **4 Fields:** Date, Cloudinary_URL, GPT_Summary (TextField), Generation_Type (Auto/Manual). |

---

### 🛠️ Implementation Summary

* **Total Models:** ~11 Core Models.
* **Fields:** Primarily `ForeignKey`, `FloatField` (for 3D and sensors), `URLField` (for Cloudinary), and `JSONField` (for bounding boxes).

