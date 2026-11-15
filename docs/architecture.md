# VIGIL System Architecture Documentation

**Project Name:** VIGIL  
**Full Title:** AI-Powered Healthcare Safety and Monitoring System  
**Category:** Artificial Intelligence, Computer Vision, Healthcare Technology and Smart Surveillance  

---

## 1. Architectural Overview

VIGIL functions as a modular software intelligence layer designed to integrate with existing hospital Closed-Circuit Television (CCTV) infrastructure. Rather than replacing physical camera hardware, VIGIL ingests real-time video streams, executes on-device AI inference, performs spatial-temporal tracking and behavioral posture analysis, and surfaces actionable notifications to clinical staff via a desktop-first monitoring dashboard.

```
                           +-------------------------------------+
                           |      SURVEILLANCE VIDEO INGEST      |
                           | (Webcam, RTSP Streams, Demo Feeds)  |
                           +------------------+------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |     YOLO VISION INFERENCE ENGINE    |
                           |  - YOLOv8n-pose (17 Skeletal Joints)|
                           |  - YOLOv8n (COCO Bags / Items)      |
                           +------------------+------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |    MULTI-OBJECT TRACKER (CENTROID)  |
                           |   Persistent Track IDs & Trajectory |
                           +------------------+------------------+
                                              |
     +-------------------+--------------------+--------------------+-------------------+
     |                   |                    |                    |                   |
     v                   v                    v                    v                   v
+----------+       +-----------+        +------------+       +------------+      +------------+
| MODULE 1 |       | MODULE 2  |        |  MODULE 3  |       |  MODULE 4  |      |  MODULE 5  |
|  Human   |       | Patient   |        | Unattended |       |   Crowd    |      | Restricted |
| Tracking |       | Fall Post |        |   Object   |       | Congestion |      |    Zone    |
| & Motion |       | Analysis  |        | Detection  |       | Monitoring |      | Intrusion  |
+----+-----+       +-----+-----+        +-----+------+       +-----+------+      +-----+------+
     |                   |                    |                    |                   |
     +-------------------+--------------------+--------------------+-------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |              MODULE 6:              |
                           | CONTEXT-AWARE CORRELATION ENGINE    |
                           |  - Temporal Sliding Window (30s)    |
                           |  - Fall + Crowd Surge Escalation    |
                           |  - Intrusion + Object Association   |
                           +------------------+------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |         INCIDENT MANAGER & DB       |
                           |   - SQLite (vigil.db)               |
                           |   - Timestamped Snapshots           |
                           |   - Alert Cooldown Dampening        |
                           +------------------+------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |   STREAMLIT CLINICAL DASHBOARD      |
                           |  - Live Feed & Visual HUD           |
                           |  - Incident Audit & Verification    |
                           |  - Camera Topology & Zones          |
                           |  - Healthcare Analytics & CSV Export|
                           +-------------------------------------+
```

---

## 2. Core Detection Modules

### Module 1: Human Detection and Spatial-Temporal Tracking
- **Model:** YOLOv8n-pose
- **Tracking Algorithm:** Centroid distance and Bounding Box Intersection over Union (IoU) association.
- **Output:** Consistent Track IDs across consecutive frames, centroid history, and age metrics.

### Module 2: Patient Fall Detection
- **Biomechanical Metrics:**
  - Torso angle ($\theta$) computed between shoulder midpoint and hip midpoint relative to the vertical gravity axis.
  - Bounding box aspect ratio ($W / H$).
  - Ground level proximity of hip and knee joints.
- **Differential Classification:**
  - **Upright:** Torso angle $< 35^\circ$, $W/H < 0.65$.
  - **Sitting:** Upright torso, hips elevated, knee/ankle flexion, $0.65 < W/H < 1.05$.
  - **Bending:** Lean angle $> 45^\circ$, vertical leg alignment, temporary duration.
  - **Horizontal / Prone (Fall Candidate):** Torso angle $> 55^\circ$, $W/H > 1.15$, persistent for $\ge 8$ consecutive frames.
- **Alert:** Critical priority "Possible Patient Fall" with snapshot capture and database persistence.

### Module 3: Unattended Object Detection
- **Model:** Pretrained YOLOv8n (COCO classes: Backpack [24], Handbag [26], Suitcase [28]).
- **Behavioral Logic:**
  - Tracks candidate objects across frames.
  - Evaluates Euclidean distance to the nearest detected human.
  - If nearest human distance exceeds 130 pixels for $> 5$ continuous seconds, flags item as "Unattended Object".

### Module 4: Crowd & Congestion Monitoring
- **Logic:** Aggregates real-time occupancy count per camera against a configurable administrative limit (default: 4 persons).
- **Dampening:** Cooldown window (25s) prevents notification flooding.

### Module 5: Restricted-Area Monitoring
- **Geometry:** Configurable rectangular polygons $[x_1, y_1, x_2, y_2]$ mapped to sensitive areas (e.g., medication carts, nurse stations).
- **Intrusion Check:** Evaluates foot-level contact coordinates of tracked individuals against polygon perimeters.

### Module 6: Context-Aware Incident Correlation Engine
- **Concept:** Rather than isolating discrete events, VIGIL correlates temporal and spatial incidents within a 30-second sliding window.
- **Rule Matrix:**
  1. **Fall Event + Subsequent Crowd Surge:** Escalates incident to a single **Critical** notification: `Correlated: Emergency Fall & Crowd Gathering`.
  2. **Restricted Zone Entry + Unattended Object:** Escalates to **High** security anomaly: `Correlated: Unattended Object in Restricted Zone`.

---

## 3. Database Schema

The SQLite database (`data/vigil.db`) uses SQLAlchemy ORM:

1. **`cameras` Table:**
   - `id` (PK, Integer)
   - `camera_id` (Unique String, e.g., "CAM-01")
   - `name` (String, e.g., "Ward 4 Corridor")
   - `location` (String)
   - `source` (String: webcam, video path, rtsp)
   - `status` (Active / Inactive)
   - `crowd_threshold` (Integer)
   - `restricted_zones_json` (Text / JSON array)
   - `enabled_modules_json` (Text / JSON array)
   - `created_at` (DateTime)

2. **`incidents` Table:**
   - `id` (PK, Integer)
   - `incident_id` (Unique String, e.g., "INC-20261115221417-A1B2C3")
   - `camera_id` (String, Indexed)
   - `camera_name` (String)
   - `event_type` (String)
   - `severity` (Critical / High / Medium / Low)
   - `timestamp` (DateTime, Indexed)
   - `description` (Text)
   - `snapshot_path` (String)
   - `status` (Pending / Verified / Resolved / False Alert)
   - `verification_notes` (Text)

3. **`app_settings` Table:**
   - `key` (PK, String)
   - `value` (Text)
   - `description` (String)

---

## 4. Hardware Acceleration and Fallback

VIGIL auto-probes for Apple Silicon Metal Performance Shaders (`mps`). If unavailable or uncompiled in the active environment, the system cleanly defaults to CPU inference using lightweight nano-models (`yolov8n-pose.pt` ~6.5MB, `yolov8n.pt` ~6.2MB) at 640x640 resolution, maintaining 15-25 FPS throughput.
