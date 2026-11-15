"""
VIGIL Database Manager and Session Initializer
"""
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from config.settings import DATABASE_URL, SNAPSHOT_DIR
from backend.models import Base, Camera, Incident, AppSetting

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    """Initializes tables and seeds default cameras and initial settings."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        # Seed Cameras if none exist
        if session.query(Camera).count() == 0:
            cams = [
                Camera(
                    camera_id="CAM-01",
                    name="Ward 4 Corridor",
                    location="Building B - Level 2",
                    source="webcam_0",
                    status="Active",
                    crowd_threshold=3,
                    restricted_zones_json=json.dumps([
                        {"name": "Medication Cart Zone", "x1": 0.02, "y1": 0.05, "x2": 0.38, "y2": 0.65}
                    ]),
                    enabled_modules_json=json.dumps(["human_tracking", "fall_detection", "object_detection", "crowd_monitoring", "restricted_zone"])
                ),
                Camera(
                    camera_id="CAM-02",
                    name="Emergency Room Entrance",
                    location="Ground Floor - Emergency Wing",
                    source="demo_video",
                    status="Active",
                    crowd_threshold=5,
                    restricted_zones_json=json.dumps([
                        {"name": "Ambulance Bay Access", "x1": 0.60, "y1": 0.10, "x2": 0.98, "y2": 0.90}
                    ]),
                    enabled_modules_json=json.dumps(["human_tracking", "fall_detection", "crowd_monitoring", "restricted_zone"])
                ),
                Camera(
                    camera_id="CAM-03",
                    name="ICU Waiting Hall",
                    location="Building A - Level 3",
                    source="demo_video",
                    status="Active",
                    crowd_threshold=4,
                    restricted_zones_json=json.dumps([]),
                    enabled_modules_json=json.dumps(["human_tracking", "fall_detection", "object_detection", "crowd_monitoring"])
                )
            ]
            session.add_all(cams)
            session.commit()

        # Seed initial AppSettings if empty
        if session.query(AppSetting).count() == 0:
            settings_defaults = [
                AppSetting(key="fall_confirmation_frames", value="8", description="Frames needed to verify prone fall posture"),
                AppSetting(key="unattended_object_seconds", value="5", description="Stationary seconds before flagging object"),
                AppSetting(key="crowd_cooldown_seconds", value="25", description="Seconds between crowd density alerts"),
                AppSetting(key="fall_cooldown_seconds", value="20", description="Seconds between repeated fall alerts for same track"),
                AppSetting(key="inference_resolution", value="640", description="Image resolution for YOLO inference"),
                AppSetting(key="hardware_acceleration", value="auto", description="MPS / CPU execution target")
            ]
            session.add_all(settings_defaults)
            session.commit()

        # Seed realistic benchmark demonstration incidents if table is empty
        if session.query(Incident).count() == 0:
            now = datetime.now()
            incidents_seed = [
                Incident(
                    incident_id=f"INC-{(now - timedelta(hours=3)).strftime('%Y%m%d%H%M%S')}-01",
                    camera_id="CAM-01",
                    camera_name="Ward 4 Corridor",
                    event_type="Possible Patient Fall",
                    severity="Critical",
                    timestamp=now - timedelta(hours=3),
                    description="Sudden transition from upright posture to horizontal ground-level posture detected (Torso angle: 78.4°, Duration: 2.1s).",
                    snapshot_path="",
                    status="Verified",
                    verification_notes="Nursing staff dispatched. Patient assisted without injury."
                ),
                Incident(
                    incident_id=f"INC-{(now - timedelta(hours=2)).strftime('%Y%m%d%H%M%S')}-02",
                    camera_id="CAM-01",
                    camera_name="Ward 4 Corridor",
                    event_type="Restricted Area Intrusion",
                    severity="High",
                    timestamp=now - timedelta(hours=2),
                    description="Tracked individual entered Medication Cart Zone [Zone 1] without authorization clearance.",
                    snapshot_path="",
                    status="Resolved",
                    verification_notes="Authorized technician carrying maintenance kit; verified credentials."
                ),
                Incident(
                    incident_id=f"INC-{(now - timedelta(hours=1, minutes=15)).strftime('%Y%m%d%H%M%S')}-03",
                    camera_id="CAM-03",
                    camera_name="ICU Waiting Hall",
                    event_type="Unattended Object Detected",
                    severity="Medium",
                    timestamp=now - timedelta(hours=1, minutes=15),
                    description="Black backpack stationary for >45 seconds with no detected human within 130px radius.",
                    snapshot_path="",
                    status="Resolved",
                    verification_notes="Retrieved by patient family member."
                ),
                Incident(
                    incident_id=f"INC-{(now - timedelta(minutes=30)).strftime('%Y%m%d%H%M%S')}-04",
                    camera_id="CAM-02",
                    camera_name="Emergency Room Entrance",
                    event_type="Crowd Limit Exceeded",
                    severity="Medium",
                    timestamp=now - timedelta(minutes=30),
                    description="Visible person count (7) exceeded configured threshold (5) in ER Entrance.",
                    snapshot_path="",
                    status="Pending",
                    verification_notes=""
                ),
                Incident(
                    incident_id=f"INC-{(now - timedelta(minutes=10)).strftime('%Y%m%d%H%M%S')}-05",
                    camera_id="CAM-01",
                    camera_name="Ward 4 Corridor",
                    event_type="Correlated: Emergency Fall & Crowd Gathering",
                    severity="Critical",
                    timestamp=now - timedelta(minutes=10),
                    description="High-priority correlation: Possible fall event at 21:56 followed by rapid crowd gathering (4 persons) in Ward 4 Corridor.",
                    snapshot_path="",
                    status="Pending",
                    verification_notes=""
                )
            ]
            session.add_all(incidents_seed)
            session.commit()

    finally:
        session.close()

def get_db():
    """Generator for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
