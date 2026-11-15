"""
VIGIL Multi-Object & Human Tracker
Lightweight, robust spatial-temporal tracker linking detections across consecutive video frames.
Provides persistent track IDs, centroid history, and trajectory analysis without heavy external dependencies.
"""
import numpy as np
from typing import List, Dict, Any, Tuple

def compute_iou(box1: List[float], box2: List[float]) -> float:
    """Computes Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])

    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area

def get_centroid(box: List[float]) -> Tuple[float, float]:
    """Returns center point (cx, cy) of bounding box."""
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)

class TrackedTarget:
    def __init__(self, track_id: int, bbox: List[float], keypoints=None, conf: float = 0.5):
        self.track_id = track_id
        self.bbox = bbox
        self.centroid = get_centroid(bbox)
        self.keypoints = keypoints
        self.conf = conf
        self.age = 1
        self.invisible_count = 0
        self.history: List[Tuple[float, float]] = [self.centroid]
        
        # State tracking for behavioral analysis
        self.fall_candidate_frames = 0
        self.posture = "Upright"  # Upright, Sitting, Prone/Horizontal, Unknown
        self.is_fallen = False
        self.stationary_duration_sec = 0.0

    def update(self, bbox: List[float], keypoints=None, conf: float = 0.5):
        self.bbox = bbox
        self.centroid = get_centroid(bbox)
        self.keypoints = keypoints if keypoints is not None else self.keypoints
        self.conf = conf
        self.age += 1
        self.invisible_count = 0
        self.history.append(self.centroid)
        if len(self.history) > 40:
            self.history.pop(0)

    def mark_missed(self):
        self.invisible_count += 1

class MultiObjectTracker:
    def __init__(self, max_missed_frames: int = 15, iou_threshold: float = 0.25, max_distance_pixels: float = 90.0):
        self.next_id = 1
        self.tracks: Dict[int, TrackedTarget] = {}
        self.max_missed_frames = max_missed_frames
        self.iou_threshold = iou_threshold
        self.max_distance_pixels = max_distance_pixels

    def update(self, detections: List[Dict[str, Any]]) -> List[TrackedTarget]:
        """
        Associates incoming detections to existing tracks using IoU and Centroid Proximity.
        Returns active tracked targets for the current frame.
        """
        # If no tracks exist, initialize all
        if not self.tracks:
            for det in detections:
                t = TrackedTarget(self.next_id, det["bbox"], det.get("keypoints"), det.get("conf", 0.5))
                self.tracks[self.next_id] = t
                self.next_id += 1
            return list(self.tracks.values())

        track_ids = list(self.tracks.keys())
        matched_tracks = set()
        matched_detections = set()

        # Step 1: Match based on IoU
        for d_idx, det in enumerate(detections):
            best_iou = 0.0
            best_tid = None
            for tid in track_ids:
                if tid in matched_tracks:
                    continue
                iou = compute_iou(det["bbox"], self.tracks[tid].bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_tid = tid

            if best_tid is not None and best_iou >= self.iou_threshold:
                self.tracks[best_tid].update(det["bbox"], det.get("keypoints"), det.get("conf", 0.5))
                matched_tracks.add(best_tid)
                matched_detections.add(d_idx)

        # Step 2: Fallback to Centroid Distance for fast moving or morphing postures
        for d_idx, det in enumerate(detections):
            if d_idx in matched_detections:
                continue
            det_c = get_centroid(det["bbox"])
            best_dist = float("inf")
            best_tid = None

            for tid in track_ids:
                if tid in matched_tracks:
                    continue
                trk_c = self.tracks[tid].centroid
                dist = np.hypot(det_c[0] - trk_c[0], det_c[1] - trk_c[1])
                if dist < best_dist:
                    best_dist = dist
                    best_tid = tid

            if best_tid is not None and best_dist <= self.max_distance_pixels:
                self.tracks[best_tid].update(det["bbox"], det.get("keypoints"), det.get("conf", 0.5))
                matched_tracks.add(best_tid)
                matched_detections.add(d_idx)

        # Step 3: Register brand new tracks
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_detections:
                t = TrackedTarget(self.next_id, det["bbox"], det.get("keypoints"), det.get("conf", 0.5))
                self.tracks[self.next_id] = t
                self.next_id += 1

        # Step 4: Mark missed tracks and remove dead tracks
        dead_tracks = []
        for tid in track_ids:
            if tid not in matched_tracks:
                self.tracks[tid].mark_missed()
                if self.tracks[tid].invisible_count > self.max_missed_frames:
                    dead_tracks.append(tid)

        for tid in dead_tracks:
            del self.tracks[tid]

        # Return active tracks visible in current frame
        return [t for t in self.tracks.values() if t.invisible_count == 0]
