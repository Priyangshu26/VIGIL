# VIGIL &mdash; AI-Powered Healthcare Safety and Monitoring System

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Ultralytics YOLO](https://img.shields.io/badge/YOLO-v8n--pose%20%7C%20v8n-0052CC.svg)](https://github.com/ultralytics/ultralytics)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Database](https://img.shields.io/badge/Database-SQLite%20ORM-003B57.svg)](https://www.sqlite.org/)

**VIGIL** is an AI-powered computer vision analytics platform engineered to enhance patient safety, accelerate incident response, and reduce dependence on continuous manual surveillance in healthcare facilities (hospitals, nursing homes, and clinics).

Designed as an intelligent software layer for existing hospital CCTV systems, VIGIL processes video footage locally using deep learning models to identify high-risk incidents, including **patient falls**, **unattended objects**, **hallway congestion**, **restricted zone violations**, and **correlated clinical emergencies**.

---

## Key Features

1. **Human Detection and Tracking (Module 1):**
   - Real-time person detection powered by YOLO.
   - Spatial-temporal tracking with persistent IDs and trajectory history across frames.
   - Live occupancy counter.

2. **Patient Fall Detection (Module 2):**
   - Skeletal joint keypoint analysis (17 COCO keypoints: shoulders, hips, knees, ankles).
   - Biomechanical posture analysis: torso angle and width-to-height aspect ratio.
   - Distinguishes upright walking, normal sitting, and bending from horizontal/prone collapse.
   - Temporal confirmation window ($\ge 8$ frames) to minimize false positives.
   - Timestamped evidence snapshot capture with visual watermarking.

3. **Unattended Object Detection (Module 3):**
   - Tracks candidate items (backpacks, handbags, suitcases).
   - Monitors stationary duration and calculates distance to nearest visible person.
   - Generates alerts when items remain unattended beyond a configurable time threshold.

4. **Crowd and Congestion Monitoring (Module 4):**
   - Real-time occupancy tracking against per-camera capacity limits.
   - Cooldown period dampening to prevent alert flooding during busy visiting hours.

5. **Restricted-Area Monitoring (Module 5):**
   - Configurable rectangular perimeter zones (e.g., Medication Carts, ICU rooms).
   - Foot-level ground contact point detection for perimeter intrusion logging.

6. **Context-Aware Incident Correlation (Module 6):**
   - Correlates temporally and spatially coupled events within a 30-second sliding window.
   - Automatically escalates **Fall Incident + Subsequent Crowd Congregation** into a high-priority **Critical Emergency**.

7. **Clinical Incident Management & Dashboard:**
   - Centralized incident audit log with filters by camera, severity, and status.
   - Incident Forensic Inspector: full-resolution snapshot viewing.
   - Status update workflow: `Pending` &rarr; `Verified`, `Resolved`, or `False Alert` with clinical verification notes.
   - Interactive Plotly analytics and CSV compliance export.

---

## System Architecture

```
VIGIL_3.0/
├── app.py                      # Main application entry point (Streamlit Dashboard)
├── requirements.txt            # System dependencies
├── README.md                   # Complete system documentation
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
│
├── backend/
│   ├── database.py             # SQLite connection & table seeding
│   ├── models.py               # SQLAlchemy ORM models (Camera, Incident, AppSetting)
│   └── incident_manager.py     # Incident creation, cooldowns, snapshots & correlation
│
├── vision/
│   ├── detector.py             # YOLOv8n-pose & YOLOv8n inference with CPU/MPS fallback
│   ├── tracker.py              # Spatial-temporal Multi-Object Tracker (IoU + Centroid)
│   ├── fall_detection.py       # Skeletal pose & torso angle posture analyzer
│   ├── object_detection.py     # Unattended luggage & proximity detector
│   ├── crowd_monitor.py        # Occupancy limit & congestion monitor
│   ├── restricted_zone.py      # Perimeter intrusion checker
│   ├── event_correlation.py    # Cross-event correlation rules
│   └── pipeline.py             # Master vision orchestrator & HUD overlay renderer
│
├── dashboard/
│   ├── components/             # Reusable UI widgets (Header, KPI cards, Plotly charts)
│   ├── pages/                  # 7 core navigation views
│   │   ├── overview.py         # Executive summary & health KPIs
│   │   ├── live_monitoring.py  # Live video feed, HUD & telemetry
│   │   ├── incident_management.py # Incident table, snapshot viewer & verification
│   │   ├── camera_management.py   # Camera registration & zone editor
│   │   ├── analytics.py        # Trend charts & CSV export
│   │   ├── settings_page.py    # Threshold configuration & DB reset
│   │   └── about.py            # Project identity, architecture & ethics
│   └── styles/
│       └── custom.css          # Professional healthcare theme styling
│
├── data/
│   ├── snapshots/              # Watermarked evidence images
│   ├── videos/                 # Demonstration video feeds
│   └── vigil.db                # SQLite persistent database
│
├── scripts/
│   └── generate_demo_footage.py# Realistic hospital corridor benchmark video generator
│
├── tests/                      # Automated test suite (11 passing tests)
│   ├── test_database.py
│   ├── test_detection.py
│   ├── test_incidents.py
│   └── test_full_pipeline.py
│
└── docs/
    ├── architecture.md         # Detailed architectural documentation
    └── testing.md              # Test matrix, results & limitations
```

---

## Installation & Setup

### Prerequisites
- macOS (tested on Apple Silicon arm64) or Linux
- Python 3.9, 3.10, 3.11, or 3.12

### 1. Clone or Open Project
```bash
cd /Users/priyangshumondal07/Projects/VIGIL_3.0
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

Launch the desktop monitoring dashboard with one command:

```bash
streamlit run app.py
```

Open your browser to: **`http://localhost:8501`**

---

## Running Automated Tests

To run the complete test suite:

```bash
MPLCONFIGDIR=/tmp/matplotlib PYTHONPATH=. ./venv/bin/python -m unittest discover -s tests
```

---

## Demonstration Guide for Evaluators

When presenting VIGIL to college teachers and evaluators:

1. **Executive Overview (Landing Page):**
   - Highlights facility health: Connected Cameras, Total Incidents, Critical Alerts, and Pending Review count.
   - Shows live category distribution and severity breakdown.

2. **Live Monitoring:**
   - Select **"CAM-01 - Ward 4 Corridor"**.
   - Under Stream Source, choose **"Hospital Demo Feed"** (pre-generated realistic corridor simulation) or **"Built-in Webcam (Local)"**.
   - Click **`▶ START MONITORING`**.
   - **Observe Live AI Modules:**
     - **Module 1 (Tracking):** Individuals are tracked with blue bounding boxes, skeletal joints, and persistent ID headers (`ID #1 | UPRIGHT`).
     - **Module 2 (Fall Detection):** When the individual collapses, the system tracks the torso angle ($>55^\circ$), aspect ratio transition ($W/H > 1.15$), and highlights the box in **Critical Red** (`ID #1 | FALL DETECTED`).
     - **Module 3 (Unattended Object):** Shows bag detection and unattended timer.
     - **Module 4 (Crowd Alert):** When multiple people enter the frame, occupancy updates (`OCCUPANCY: 5/4`).
     - **Module 5 (Restricted Zone):** Visualizes the red semi-transparent "Medication Cart Zone" on the floor.
     - **Module 6 (Context-Aware Correlation):** Triggers `Correlated: Emergency Fall & Crowd Gathering`.

3. **Incident Management & Evidence Inspection:**
   - Navigate to **"Incident Management"**.
   - Filter by **Severity: Critical** or **Status: Pending**.
   - Select an incident from the inspector on the right.
   - Inspect the captured snapshot evidence with watermark.
   - Update the status from `Pending` &rarr; `Verified` with clinical notes (e.g. *"Nurse dispatched to Room 204"*).
   - Demonstrates that changes persist in SQLite.

4. **Analytics & Compliance Reporting:**
   - View incident trends and camera distribution.
   - Click **`📥 DOWNLOAD INCIDENT LOGS (CSV)`** to download the clinical audit file.

---

## Ethical & Privacy Principles

- **No Facial Biometrics:** VIGIL strictly tracks human figures using bounding boxes and skeletal joints. No facial recognition or demographic identification models are deployed.
- **Local On-Premises Processing:** All video frames are processed in-memory locally. No patient video feeds are streamed to external cloud servers.
- **Decision-Support Role:** VIGIL is an assistive decision-support layer to reduce surveillance fatigue; every notification is subject to clinical human verification.
