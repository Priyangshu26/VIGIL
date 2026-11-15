"""
VIGIL Restricted-Area Monitoring Module
Detects unauthorized perimeter entries into configured restricted rectangular zones
using foot-level ground contact points of tracked individuals.
"""
import time
from typing import List, Dict, Any, Tuple, Optional
from config.settings import RESTRICTED_ZONE_COOLDOWN_SECONDS, SEVERITY_HIGH

class RestrictedZoneMonitor:
    def __init__(self, cooldown_sec: float = RESTRICTED_ZONE_COOLDOWN_SECONDS):
        self.cooldown_sec = cooldown_sec
        # track_id_zone_name -> last_alert_time
        self.alert_history: Dict[str, float] = {}

    def is_point_inside(self, px: float, py: float, zone: Dict[str, Any], frame_w: int, frame_h: int) -> bool:
        """
        Checks if pixel coordinate (px, py) lies inside the zone.
        Zone can be defined in normalized (0.0 - 1.0) or absolute pixel coordinates.
        """
        x1 = zone["x1"] * frame_w if zone["x1"] <= 1.0 else zone["x1"]
        y1 = zone["y1"] * frame_h if zone["y1"] <= 1.0 else zone["y1"]
        x2 = zone["x2"] * frame_w if zone["x2"] <= 1.0 else zone["x2"]
        y2 = zone["y2"] * frame_h if zone["y2"] <= 1.0 else zone["y2"]

        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        return min_x <= px <= max_x and min_y <= py <= max_y

    def check_intrusions(
        self,
        tracks: List[Any],
        zones: List[Dict[str, Any]],
        frame_w: int,
        frame_h: int,
        camera_name: str
    ) -> List[Tuple[Any, Dict[str, Any], str]]:
        """
        Checks all active tracks against configured restricted zones.
        Returns:
            List of (track, zone, alert_description)
        """
        if not zones or not tracks:
            return []

        now = time.time()
        intrusions = []

        for track in tracks:
            x1, y1, x2, y2 = track.bbox
            # Ground foot contact point is bottom-center of bounding box
            foot_x = (x1 + x2) / 2.0
            foot_y = y2

            for zone in zones:
                z_name = zone.get("name", "Restricted Zone")
                if self.is_point_inside(foot_x, foot_y, zone, frame_w, frame_h):
                    alert_key = f"{track.track_id}_{z_name}"
                    last_time = self.alert_history.get(alert_key, 0.0)

                    if (now - last_time) >= self.cooldown_sec:
                        self.alert_history[alert_key] = now
                        desc = (
                            f"Restricted area violation in {camera_name}. "
                            f"Individual #{track.track_id} entered designated zone '{z_name}'. "
                            f"Authorized personnel verification required."
                        )
                        intrusions.append((track, zone, desc))

        return intrusions
