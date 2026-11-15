"""
VIGIL Unattended Object Detection Module
Tracks candidate items (backpacks, handbags, suitcases), calculates proximity to visible persons,
accumulates stationary duration, and raises alerts when items are left unattended.
"""
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from config.settings import (
    UNATTENDED_TIME_THRESH_SEC,
    PERSON_PROXIMITY_PIXELS,
    SEVERITY_MEDIUM
)

class TrackedObject:
    def __init__(self, obj_id: int, class_name: str, bbox: List[float]):
        self.obj_id = obj_id
        self.class_name = class_name
        self.bbox = bbox
        self.centroid = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.unattended_since: Optional[float] = None
        self.is_attended = True
        self.alert_raised = False
        self.invisible_count = 0

    def update(self, bbox: List[float]):
        self.bbox = bbox
        self.centroid = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
        self.last_seen = time.time()
        self.invisible_count = 0

class UnattendedObjectDetector:
    def __init__(
        self,
        time_threshold_sec: float = UNATTENDED_TIME_THRESH_SEC,
        proximity_radius_px: float = PERSON_PROXIMITY_PIXELS
    ):
        self.time_threshold_sec = time_threshold_sec
        self.proximity_radius_px = proximity_radius_px
        self.next_obj_id = 1
        self.tracked_objects: Dict[int, TrackedObject] = {}

    def update(
        self,
        detected_objects: List[Dict[str, Any]],
        detected_persons: List[Any]
    ) -> List[Tuple[TrackedObject, str]]:
        """
        Updates tracked objects and evaluates attended/unattended status.
        Returns:
            List of (TrackedObject, alert_description) for newly triggered alerts.
        """
        now = time.time()
        matched_obj_ids = set()

        # Step 1: Match detections to existing tracked objects
        for det in detected_objects:
            d_bbox = det["bbox"]
            d_c = ((d_bbox[0] + d_bbox[2]) / 2.0, (d_bbox[1] + d_bbox[3]) / 2.0)
            best_id = None
            best_dist = float("inf")

            for oid, tobj in self.tracked_objects.items():
                if oid in matched_obj_ids:
                    continue
                dist = np.hypot(d_c[0] - tobj.centroid[0], d_c[1] - tobj.centroid[1])
                if dist < best_dist and dist < 80.0:  # Distance threshold for stationary object
                    best_dist = dist
                    best_id = oid

            if best_id is not None:
                self.tracked_objects[best_id].update(d_bbox)
                matched_obj_ids.add(best_id)
            else:
                new_obj = TrackedObject(self.next_obj_id, det["class_name"], d_bbox)
                self.tracked_objects[self.next_obj_id] = new_obj
                matched_obj_ids.add(self.next_obj_id)
                self.next_obj_id += 1

        # Step 2: Handle missed objects
        dead_ids = []
        for oid, tobj in self.tracked_objects.items():
            if oid not in matched_obj_ids:
                tobj.invisible_count += 1
                if tobj.invisible_count > 30:
                    dead_ids.append(oid)
        for oid in dead_ids:
            del self.tracked_objects[oid]

        # Step 3: Check proximity to detected persons
        alerts = []
        for oid, tobj in self.tracked_objects.items():
            # Calculate distance to closest person
            min_dist_to_person = float("inf")
            for person in detected_persons:
                p_c = person.centroid if hasattr(person, "centroid") else ((person["bbox"][0] + person["bbox"][2]) / 2.0, (person["bbox"][1] + person["bbox"][3]) / 2.0)
                d = np.hypot(tobj.centroid[0] - p_c[0], tobj.centroid[1] - p_c[1])
                if d < min_dist_to_person:
                    min_dist_to_person = d

            is_near_person = (min_dist_to_person <= self.proximity_radius_px)
            tobj.is_attended = is_near_person

            if not is_near_person:
                if tobj.unattended_since is None:
                    tobj.unattended_since = now
                
                unattended_elapsed = now - tobj.unattended_since
                if unattended_elapsed >= self.time_threshold_sec and not tobj.alert_raised:
                    tobj.alert_raised = True
                    desc = (
                        f"Unattended {tobj.class_name} (Item #{tobj.obj_id}) detected. "
                        f"Stationary with no person within {int(self.proximity_radius_px)}px radius "
                        f"for {unattended_elapsed:.1f}s. Human verification advised."
                    )
                    alerts.append((tobj, desc))
            else:
                # Person returned or nearby; reset timer
                tobj.unattended_since = None
                tobj.alert_raised = False

        return alerts
