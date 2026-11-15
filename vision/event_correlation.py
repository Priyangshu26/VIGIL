"""
VIGIL Event Correlation Module
Transparent, rule-based cross-event correlation evaluating spatial and temporal proximity.
"""
from typing import List, Dict, Any, Optional

class EventCorrelator:
    """
    Evaluates multi-event scenarios within a temporal sliding window.
    Maintains deterministic transparent rules.
    """
    def __init__(self, window_seconds: float = 30.0):
        self.window_seconds = window_seconds

    def evaluate_rules(self, recent_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        correlated = []
        if len(recent_events) < 2:
            return correlated

        # Group by camera
        by_cam = {}
        for ev in recent_events:
            cid = ev.get("camera_id")
            by_cam.setdefault(cid, []).append(ev)

        for cid, evs in by_cam.items():
            has_fall = any("Fall" in e["event_type"] for e in evs)
            has_crowd = any("Crowd" in e["event_type"] for e in evs)
            has_restricted = any("Restricted" in e["event_type"] for e in evs)
            has_object = any("Object" in e["event_type"] for e in evs)

            if has_fall and has_crowd:
                correlated.append({
                    "rule": "FALL_AND_CROWD_SURGE",
                    "camera_id": cid,
                    "camera_name": evs[0].get("camera_name", ""),
                    "priority": "Critical",
                    "title": "Correlated: Emergency Fall & Crowd Gathering"
                })

            if has_restricted and has_object:
                correlated.append({
                    "rule": "RESTRICTED_AND_UNATTENDED_OBJECT",
                    "camera_id": cid,
                    "camera_name": evs[0].get("camera_name", ""),
                    "priority": "High",
                    "title": "Correlated: Unattended Object in Restricted Zone"
                })

        return correlated
