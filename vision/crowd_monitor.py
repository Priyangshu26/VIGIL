"""
VIGIL Crowd & Congestion Monitoring Module
Monitors visible occupant counts against configurable thresholds and generates
congestion notifications with cooldown dampening.
"""
import time
from typing import Tuple, Optional
from config.settings import DEFAULT_CROWD_THRESHOLD, CROWD_COOLDOWN_SECONDS, SEVERITY_MEDIUM

class CrowdMonitor:
    def __init__(self, threshold: int = DEFAULT_CROWD_THRESHOLD, cooldown_sec: float = CROWD_COOLDOWN_SECONDS):
        self.threshold = threshold
        self.cooldown_sec = cooldown_sec
        self.last_alert_time = 0.0

    def update_threshold(self, new_threshold: int):
        self.threshold = max(1, new_threshold)

    def check_crowd(self, current_count: int, camera_name: str) -> Tuple[bool, Optional[str]]:
        """
        Evaluates current human count against configured limit.
        Returns:
            (is_alert, alert_description)
        """
        now = time.time()
        if current_count >= self.threshold:
            if (now - self.last_alert_time) >= self.cooldown_sec:
                self.last_alert_time = now
                desc = (
                    f"Crowd threshold exceeded in {camera_name}. "
                    f"Current occupancy: {current_count} persons (Configured limit: {self.threshold}). "
                    f"Possible hallway congestion or waiting area bottleneck."
                )
                return True, desc
        return False, None
