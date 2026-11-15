"""
VIGIL Incident Manager
Handles incident creation, severity assignment, cooldown management,
snapshot capture, status updates, and context-aware event correlation.
"""
import os
import cv2
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from config.settings import (
    SNAPSHOT_DIR,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
    STATUS_PENDING,
    STATUS_VERIFIED,
    STATUS_RESOLVED,
    STATUS_FALSE_ALERT,
    CORRELATION_WINDOW_SECONDS
)
from backend.models import Incident, Camera
from backend.database import SessionLocal

class IncidentManager:
    def __init__(self):
        self.cooldown_tracker: Dict[str, float] = {}  # key -> last_trigger_timestamp
        self.recent_events_buffer: List[Dict[str, Any]] = []  # In-memory sliding window for correlation

    def _is_cooling_down(self, cooldown_key: str, cooldown_seconds: float) -> bool:
        """Checks if an alert for this key is within its cooldown period."""
        now = time.time()
        if cooldown_key in self.cooldown_tracker:
            elapsed = now - self.cooldown_tracker[cooldown_key]
            if elapsed < cooldown_seconds:
                return True
        return False

    def _update_cooldown(self, cooldown_key: str):
        self.cooldown_tracker[cooldown_key] = time.time()

    def save_snapshot(self, frame, incident_id: str) -> Optional[str]:
        """Saves a timestamped snapshot of the incident frame."""
        if frame is None:
            return None
        try:
            filename = f"{incident_id}.jpg"
            filepath = os.path.join(SNAPSHOT_DIR, filename)
            # Create a copy and annotate standard VIGIL watermark
            annotated = frame.copy()
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                annotated,
                f"VIGIL HEALTHCARE SAFETY - {incident_id} | {timestamp_str}",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )
            cv2.imwrite(filepath, annotated)
            return filepath
        except Exception as e:
            print(f"[IncidentManager] Error saving snapshot: {e}")
            return None

    def create_incident(
        self,
        camera_id: str,
        camera_name: str,
        event_type: str,
        severity: str,
        description: str,
        frame=None,
        cooldown_key: Optional[str] = None,
        cooldown_seconds: float = 20.0,
        trigger_correlation: bool = True
    ) -> Optional[Incident]:
        """
        Creates, logs, and persists an incident with cooldown checks,
        snapshot storage, and automatic context-aware correlation.
        """
        # 1. Cooldown check
        if cooldown_key and self._is_cooling_down(cooldown_key, cooldown_seconds):
            return None

        # 2. Generate unique incident ID
        now_dt = datetime.now()
        timestamp_slug = now_dt.strftime("%Y%m%d%H%M%S")
        import uuid
        incident_id = f"INC-{timestamp_slug}-{uuid.uuid4().hex[:6].upper()}"

        # 3. Save snapshot if frame provided
        snapshot_path = self.save_snapshot(frame, incident_id) if frame is not None else ""

        # 4. Save to Database
        session: Session = SessionLocal()
        created_incident = None
        try:
            incident = Incident(
                incident_id=incident_id,
                camera_id=camera_id,
                camera_name=camera_name,
                event_type=event_type,
                severity=severity,
                timestamp=now_dt,
                description=description,
                snapshot_path=snapshot_path or "",
                status=STATUS_PENDING,
                verification_notes=""
            )
            session.add(incident)
            session.commit()
            session.refresh(incident)
            created_incident = incident

            if cooldown_key:
                self._update_cooldown(cooldown_key)

            # 5. Add to correlation buffer
            event_record = {
                "incident_id": incident_id,
                "camera_id": camera_id,
                "camera_name": camera_name,
                "event_type": event_type,
                "severity": severity,
                "timestamp": now_dt,
                "unix_time": time.time(),
                "frame": frame
            }
            self.recent_events_buffer.append(event_record)
            self._prune_correlation_buffer()

            # 6. Check context-aware correlation if requested
            if trigger_correlation:
                self._check_correlations(event_record)

        except Exception as e:
            session.rollback()
            print(f"[IncidentManager] Failed to create incident: {e}")
        finally:
            session.close()

        return created_incident

    def _prune_correlation_buffer(self):
        """Discards events older than the correlation sliding window."""
        cutoff = time.time() - CORRELATION_WINDOW_SECONDS
        self.recent_events_buffer = [
            e for e in self.recent_events_buffer if e["unix_time"] >= cutoff
        ]

    def _check_correlations(self, trigger_event: Dict[str, Any]):
        """
        Module 6: Context-Aware Incident Correlation Engine
        Correlates temporally and spatially coupled events:
        Rule 1: Fall Detected + Crowd Surge in same camera within 30s -> CRITICAL Emergency
        Rule 2: Restricted Area Intrusion + Unattended Object within 30s -> HIGH Security Anomaly
        """
        cam_id = trigger_event["camera_id"]
        cam_name = trigger_event["camera_name"]
        t_type = trigger_event["event_type"]
        now_time = trigger_event["unix_time"]

        # Rule 1: Fall + Crowd Gathering
        if "Fall" in t_type:
            # Check if there is already a recent crowd event on this camera
            crowd_events = [
                e for e in self.recent_events_buffer
                if e["camera_id"] == cam_id and "Crowd" in e["event_type"]
                and abs(now_time - e["unix_time"]) <= CORRELATION_WINDOW_SECONDS
            ]
            if crowd_events:
                self._raise_correlated_incident(
                    cam_id=cam_id,
                    cam_name=cam_name,
                    event_type="Correlated: Emergency Fall & Crowd Gathering",
                    severity=SEVERITY_CRITICAL,
                    description=f"Correlated emergency detected in {cam_name}: Fall incident [{trigger_event['incident_id']}] followed by immediate crowd congregation. Immediate clinical dispatch recommended.",
                    frame=trigger_event["frame"],
                    cooldown_key=f"corr_fall_crowd_{cam_id}"
                )
        elif "Crowd" in t_type:
            # Check if there was a recent fall event on this camera
            fall_events = [
                e for e in self.recent_events_buffer
                if e["camera_id"] == cam_id and "Fall" in e["event_type"]
                and abs(now_time - e["unix_time"]) <= CORRELATION_WINDOW_SECONDS
            ]
            if fall_events:
                f_ev = fall_events[-1]
                self._raise_correlated_incident(
                    cam_id=cam_id,
                    cam_name=cam_name,
                    event_type="Correlated: Emergency Fall & Crowd Gathering",
                    severity=SEVERITY_CRITICAL,
                    description=f"Correlated emergency detected in {cam_name}: Active crowd surge around location of previous fall incident [{f_ev['incident_id']}]. High likelihood of patient distress.",
                    frame=trigger_event["frame"],
                    cooldown_key=f"corr_fall_crowd_{cam_id}"
                )

        # Rule 2: Restricted Area Intrusion + Unattended Object
        if ("Restricted" in t_type and any("Object" in e["event_type"] for e in self.recent_events_buffer if e["camera_id"] == cam_id)) or \
           ("Object" in t_type and any("Restricted" in e["event_type"] for e in self.recent_events_buffer if e["camera_id"] == cam_id)):
            self._raise_correlated_incident(
                cam_id=cam_id,
                cam_name=cam_name,
                event_type="Correlated: Unattended Object in Restricted Zone",
                severity=SEVERITY_HIGH,
                description=f"Correlated security alert in {cam_name}: Restricted zone access coincided with unattended item left in vicinity.",
                frame=trigger_event["frame"],
                cooldown_key=f"corr_restr_obj_{cam_id}"
            )

    def _raise_correlated_incident(
        self,
        cam_id: str,
        cam_name: str,
        event_type: str,
        severity: str,
        description: str,
        frame,
        cooldown_key: str
    ):
        """Raises a correlated incident without re-triggering correlation loops."""
        if self._is_cooling_down(cooldown_key, cooldown_seconds=CORRELATION_WINDOW_SECONDS):
            return
        self.create_incident(
            camera_id=cam_id,
            camera_name=cam_name,
            event_type=event_type,
            severity=severity,
            description=description,
            frame=frame,
            cooldown_key=cooldown_key,
            cooldown_seconds=CORRELATION_WINDOW_SECONDS,
            trigger_correlation=False
        )

    def get_incidents(
        self,
        camera_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieves incidents matching optional filters."""
        session: Session = SessionLocal()
        try:
            query = session.query(Incident).order_by(Incident.timestamp.desc())
            if camera_id and camera_id != "All":
                query = query.filter(Incident.camera_id == camera_id)
            if severity and severity != "All":
                query = query.filter(Incident.severity == severity)
            if status and status != "All":
                query = query.filter(Incident.status == status)
            results = query.limit(limit).all()
            return [i.to_dict() for i in results]
        finally:
            session.close()

    def update_incident_status(self, incident_id: str, new_status: str, notes: str = "") -> bool:
        """Updates the status and verification notes of an incident."""
        session: Session = SessionLocal()
        try:
            inc = session.query(Incident).filter(Incident.incident_id == incident_id).first()
            if inc:
                inc.status = new_status
                if notes:
                    inc.verification_notes = notes
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"[IncidentManager] Failed to update incident: {e}")
            return False
        finally:
            session.close()

    def get_incident_stats(self) -> Dict[str, Any]:
        """Computes statistical metrics for dashboard analytics."""
        session: Session = SessionLocal()
        try:
            total = session.query(Incident).count()
            critical = session.query(Incident).filter(Incident.severity == SEVERITY_CRITICAL).count()
            high = session.query(Incident).filter(Incident.severity == SEVERITY_HIGH).count()
            pending = session.query(Incident).filter(Incident.status == STATUS_PENDING).count()
            verified = session.query(Incident).filter(Incident.status == STATUS_VERIFIED).count()
            resolved = session.query(Incident).filter(Incident.status == STATUS_RESOLVED).count()

            # Breakdown by event type
            from sqlalchemy import func
            type_counts = session.query(Incident.event_type, func.count(Incident.id)).group_by(Incident.event_type).all()
            by_type = {t: c for t, c in type_counts}

            # Breakdown by camera
            cam_counts = session.query(Incident.camera_name, func.count(Incident.id)).group_by(Incident.camera_name).all()
            by_camera = {c: cnt for c, cnt in cam_counts}

            return {
                "total": total,
                "critical": critical,
                "high": high,
                "pending": pending,
                "verified": verified,
                "resolved": resolved,
                "by_type": by_type,
                "by_camera": by_camera
            }
        finally:
            session.close()

# Global singleton instance
incident_manager = IncidentManager()
