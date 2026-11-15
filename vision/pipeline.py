"""
VIGIL Master Vision Analytics Pipeline
Coordinates detection, tracking, fall posture analysis, unattended object monitoring,
restricted zone compliance, crowd counting, and HUD rendering.
"""
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from config.settings import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
    FALL_COOLDOWN_SECONDS,
    OBJECT_COOLDOWN_SECONDS
)
from vision.detector import VisionDetector
from vision.tracker import MultiObjectTracker
from vision.fall_detection import FallDetector
from vision.object_detection import UnattendedObjectDetector
from vision.crowd_monitor import CrowdMonitor
from vision.restricted_zone import RestrictedZoneMonitor
from backend.incident_manager import incident_manager

# COCO Pose Skeleton Connections (17 keypoints)
SKELETON_PAIRS = [
    (0, 1), (0, 2), (1, 3), (2, 4),           # Facial
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Upper body / Arms
    (5, 11), (6, 12), (11, 12),               # Torso
    (11, 13), (13, 15), (12, 14), (14, 16)    # Lower body / Legs
]

class VisionPipeline:
    def __init__(self, camera_config: Optional[Dict[str, Any]] = None):
        self.detector = VisionDetector()
        self.tracker = MultiObjectTracker()
        self.fall_detector = FallDetector()
        self.object_detector = UnattendedObjectDetector()
        self.crowd_monitor = CrowdMonitor()
        self.zone_monitor = RestrictedZoneMonitor()

        self.camera_id = "CAM-01"
        self.camera_name = "Ward 4 Corridor"
        self.crowd_threshold = 4
        self.restricted_zones = []
        self.bed_zones = []
        self.enabled_modules = [
            "human_tracking",
            "fall_detection",
            "object_detection",
            "crowd_monitoring",
            "restricted_zone"
        ]

        if camera_config:
            self.configure(camera_config)

    def configure(self, camera_config: Dict[str, Any]):
        """Dynamically applies camera configuration settings."""
        self.camera_id = camera_config.get("camera_id", self.camera_id)
        self.camera_name = camera_config.get("name", self.camera_name)
        self.crowd_threshold = camera_config.get("crowd_threshold", self.crowd_threshold)
        self.crowd_monitor.update_threshold(self.crowd_threshold)
        self.restricted_zones = camera_config.get("restricted_zones", [])
        self.bed_zones = camera_config.get("bed_zones", [])
        self.enabled_modules = camera_config.get("enabled_modules", self.enabled_modules)

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any], List[str]]:
        """
        Processes a single video frame through all active vision modules.
        Returns:
            annotated_frame: np.ndarray (BGR image with HUD)
            metrics: dict of current frame statistics
            active_alerts: list of alert messages triggered in this frame
        """
        if frame is None:
            return frame, {}, []

        h, w = frame.shape[:2]
        canvas = frame.copy()
        active_alerts: List[str] = []

        # 1. Human Detection & Pose Estimation (Module 1 & 2)
        person_detections = []
        if "human_tracking" in self.enabled_modules or "fall_detection" in self.enabled_modules:
            person_detections = self.detector.detect_pose(frame)

        # 2. Track people across frames (Module 1)
        active_tracks = self.tracker.update(person_detections)
        people_count = len(active_tracks)

        # 3. Crowd Monitoring (Module 4)
        if "crowd_monitoring" in self.enabled_modules:
            is_crowd_alert, crowd_desc = self.crowd_monitor.check_crowd(people_count, self.camera_name)
            if is_crowd_alert and crowd_desc:
                active_alerts.append(crowd_desc)
                incident_manager.create_incident(
                    camera_id=self.camera_id,
                    camera_name=self.camera_name,
                    event_type="Crowd Limit Exceeded",
                    severity=SEVERITY_MEDIUM,
                    description=crowd_desc,
                    frame=canvas,
                    cooldown_key=f"crowd_{self.camera_id}"
                )

        # 4. Fall Detection (Module 2) - With Bed Exclusion & Floor Level Ground Check
        if "fall_detection" in self.enabled_modules:
            for track in active_tracks:
                is_fall, fall_desc = self.fall_detector.process_track(
                    track, frame_h=h, frame_w=w, bed_zones=self.bed_zones
                )
                if is_fall and fall_desc:
                    active_alerts.append(fall_desc)
                    incident_manager.create_incident(
                        camera_id=self.camera_id,
                        camera_name=self.camera_name,
                        event_type="Possible Patient Fall",
                        severity=SEVERITY_CRITICAL,
                        description=fall_desc,
                        frame=canvas,
                        cooldown_key=f"fall_{self.camera_id}_{track.track_id}",
                        cooldown_seconds=FALL_COOLDOWN_SECONDS
                    )

        # 5. Restricted-Area Monitoring (Module 5)
        if "restricted_zone" in self.enabled_modules and self.restricted_zones:
            intrusions = self.zone_monitor.check_intrusions(
                active_tracks, self.restricted_zones, w, h, self.camera_name
            )
            for track, zone, intr_desc in intrusions:
                active_alerts.append(intr_desc)
                incident_manager.create_incident(
                    camera_id=self.camera_id,
                    camera_name=self.camera_name,
                    event_type="Restricted Area Intrusion",
                    severity=SEVERITY_HIGH,
                    description=intr_desc,
                    frame=canvas,
                    cooldown_key=f"zone_{self.camera_id}_{track.track_id}_{zone.get('name')}"
                )

        # 6. Unattended Object Detection (Module 3)
        detected_objects = []
        if "object_detection" in self.enabled_modules:
            detected_objects = self.detector.detect_objects(frame, target_classes=[24, 26, 28])
            obj_alerts = self.object_detector.update(detected_objects, active_tracks)
            for tobj, obj_desc in obj_alerts:
                active_alerts.append(obj_desc)
                incident_manager.create_incident(
                    camera_id=self.camera_id,
                    camera_name=self.camera_name,
                    event_type="Unattended Object Detected",
                    severity=SEVERITY_MEDIUM,
                    description=obj_desc,
                    frame=canvas,
                    cooldown_key=f"obj_{self.camera_id}_{tobj.obj_id}",
                    cooldown_seconds=OBJECT_COOLDOWN_SECONDS
                )

        # 7. Render Professional Healthcare HUD & Visual Annotations
        self._render_restricted_zones(canvas, w, h)
        self._render_tracked_people(canvas, active_tracks)
        self._render_tracked_objects(canvas)
        self._render_hud_banner(canvas, w, h, people_count, active_alerts)

        metrics = {
            "people_count": people_count,
            "crowd_threshold": self.crowd_threshold,
            "objects_tracked": len(self.object_detector.tracked_objects),
            "alerts_count": len(active_alerts),
            "camera_id": self.camera_id,
            "camera_name": self.camera_name
        }

        return canvas, metrics, active_alerts

    def _render_restricted_zones(self, frame: np.ndarray, w: int, h: int):
        """Draws clean restricted perimeter overlay zones."""
        for zone in self.restricted_zones:
            x1 = int(zone["x1"] * w if zone["x1"] <= 1.0 else zone["x1"])
            y1 = int(zone["y1"] * h if zone["y1"] <= 1.0 else zone["y1"])
            x2 = int(zone["x2"] * w if zone["x2"] <= 1.0 else zone["x2"])
            y2 = int(zone["y2"] * h if zone["y2"] <= 1.0 else zone["y2"])

            # Semi-transparent zone tint
            sub_rect = frame[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)]
            if sub_rect.size > 0:
                tint = np.full(sub_rect.shape, (40, 40, 200), dtype=np.uint8) # Dark Red tint
                cv2.addWeighted(sub_rect, 0.85, tint, 0.15, 0, sub_rect)

            # Border
            cv2.rectangle(frame, (x1, y1), (x2, y2), (79, 83, 217), 2)
            z_label = f"RESTRICTED: {zone.get('name', 'Zone')}"
            cv2.putText(frame, z_label, (x1 + 6, max(20, y1 + 18)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    def _render_tracked_people(self, frame: np.ndarray, tracks: List[Any]):
        """Renders bounding boxes, skeletal joints, track ID badges, and posture states."""
        for t in tracks:
            x1, y1, x2, y2 = [int(v) for v in t.bbox]
            is_fall = getattr(t, "is_fallen", False) or t.posture == "Horizontal / Floor Fall"

            # Colors (BGR)
            # Healthcare blue: (181, 120, 40), Critical Red: (79, 83, 217), Warning Amber: (60, 162, 230), Safe Green: (104, 133, 57)
            if is_fall:
                box_color = (79, 83, 217)  # Critical Red
                badge_text = f"ID #{t.track_id} | FALL DETECTED (FLOOR)"
            elif t.posture == "Lying in Bed (Resting)":
                box_color = (104, 133, 57)  # Safe Green / Resting
                badge_text = f"ID #{t.track_id} | IN BED (RESTING)"
            elif t.posture in ("Sitting", "Bending"):
                box_color = (60, 162, 230)  # Amber
                badge_text = f"ID #{t.track_id} | {t.posture.upper()}"
            else:
                box_color = (181, 120, 40)  # Professional Healthcare Blue
                badge_text = f"ID #{t.track_id} | UPRIGHT"

            # Draw sleek bounding box corners
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

            # Badge banner above head
            badge_h = 20
            cv2.rectangle(frame, (x1, max(0, y1 - badge_h)), (x1 + len(badge_text) * 9 + 10, y1), box_color, -1)
            cv2.putText(frame, badge_text, (x1 + 5, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

            # Draw Skeletal Keypoints if available
            if t.keypoints is not None and len(t.keypoints) >= 17:
                kpts = t.keypoints
                # Limbs
                for pair in SKELETON_PAIRS:
                    pt1, pt2 = kpts[pair[0]], kpts[pair[1]]
                    if pt1[2] > 0.4 and pt2[2] > 0.4:
                        p1 = (int(pt1[0]), int(pt1[1]))
                        p2 = (int(pt2[0]), int(pt2[1]))
                        cv2.line(frame, p1, p2, (255, 255, 255), 2, cv2.LINE_AA)
                # Joints
                for kp in kpts:
                    if kp[2] > 0.4:
                        cv2.circle(frame, (int(kp[0]), int(kp[1])), 3, box_color, -1, cv2.LINE_AA)

    def _render_tracked_objects(self, frame: np.ndarray):
        """Renders unattended object boxes and countdown timers."""
        for oid, tobj in self.object_detector.tracked_objects.items():
            x1, y1, x2, y2 = [int(v) for v in tobj.bbox]
            if tobj.alert_raised:
                color = (79, 83, 217)  # Red alert
                status_txt = f"{tobj.class_name.upper()} #{oid} | UNATTENDED ALERT"
            elif not tobj.is_attended:
                color = (60, 162, 230)  # Amber warning
                status_txt = f"{tobj.class_name.upper()} #{oid} | UNATTENDED"
            else:
                color = (104, 133, 57)  # Green attended
                status_txt = f"{tobj.class_name.upper()} #{oid} | ATTENDED"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, status_txt, (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)

    def _render_hud_banner(self, frame: np.ndarray, w: int, h: int, people_count: int, active_alerts: List[str]):
        """Renders top executive telemetry HUD header with camera status and occupancy count."""
        # Header background bar (Navy #15324B BGR: (75, 50, 21))
        cv2.rectangle(frame, (0, 0), (w, 36), (75, 50, 21), -1)

        # Camera Name & Status
        cv2.putText(
            frame,
            f"VIGIL LIVE | {self.camera_name} ({self.camera_id})",
            (12, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        # Occupancy Counter
        count_color = (60, 162, 230) if people_count >= self.crowd_threshold else (100, 220, 100)
        occ_text = f"OCCUPANCY: {people_count}/{self.crowd_threshold}"
        cv2.putText(frame, occ_text, (w - 320, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.52, count_color, 1, cv2.LINE_AA)

        # Timestamp
        time_str = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, time_str, (w - 85, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 200, 200), 1, cv2.LINE_AA)

        # Active Alert Bar if any
        if active_alerts:
            # Flashing banner
            cv2.rectangle(frame, (0, h - 30), (w, h), (79, 83, 217), -1)
            alert_summary = f"! ACTIVE ALERT: {active_alerts[0][:80]}"
            cv2.putText(frame, alert_summary, (12, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
