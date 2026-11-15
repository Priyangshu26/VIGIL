"""
VIGIL Database Models
SQLAlchemy ORM models for Cameras, Incidents, and System Settings.
"""
from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(150), nullable=False)
    source = Column(String(255), default="webcam_0")  # webcam_0, file path, rtsp://
    status = Column(String(20), default="Active")     # Active, Inactive
    crowd_threshold = Column(Integer, default=4)
    restricted_zones_json = Column(Text, default="[]")  # JSON list of dicts: [{name, x1, y1, x2, y2}]
    enabled_modules_json = Column(Text, default='["human_tracking", "fall_detection", "object_detection", "crowd_monitoring", "restricted_zone"]')
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def restricted_zones(self):
        try:
            return json.loads(self.restricted_zones_json or "[]")
        except Exception:
            return []

    @restricted_zones.setter
    def restricted_zones(self, value):
        self.restricted_zones_json = json.dumps(value)

    @property
    def enabled_modules(self):
        try:
            return json.loads(self.enabled_modules_json or "[]")
        except Exception:
            return []

    @enabled_modules.setter
    def enabled_modules(self, value):
        self.enabled_modules_json = json.dumps(value)

    def to_dict(self):
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "name": self.name,
            "location": self.location,
            "source": self.source,
            "status": self.status,
            "crowd_threshold": self.crowd_threshold,
            "restricted_zones": self.restricted_zones,
            "enabled_modules": self.enabled_modules,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(60), unique=True, nullable=False, index=True)
    camera_id = Column(String(50), nullable=False, index=True)
    camera_name = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)  # Critical, High, Medium, Low
    timestamp = Column(DateTime, default=datetime.now, index=True)
    description = Column(Text, nullable=False)
    snapshot_path = Column(String(255), nullable=True)
    status = Column(String(30), default="Pending", index=True)  # Pending, Verified, Resolved, False Alert
    verification_notes = Column(Text, default="")

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "event_type": self.event_type,
            "severity": self.severity,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "",
            "description": self.description,
            "snapshot_path": self.snapshot_path,
            "status": self.status,
            "verification_notes": self.verification_notes or "",
        }


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
        }
