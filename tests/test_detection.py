"""
Unit tests for VIGIL Vision & Detection Modules
"""
import unittest
import numpy as np
from vision.tracker import MultiObjectTracker
from vision.fall_detection import FallDetector
from vision.object_detection import UnattendedObjectDetector
from vision.crowd_monitor import CrowdMonitor
from vision.restricted_zone import RestrictedZoneMonitor
from vision.event_correlation import EventCorrelator

class TestVisionModules(unittest.TestCase):
    def test_multi_object_tracker(self):
        tracker = MultiObjectTracker()
        # Frame 1: One person detected
        dets_f1 = [{"bbox": [100.0, 100.0, 180.0, 300.0], "conf": 0.85}]
        tracks1 = tracker.update(dets_f1)
        self.assertEqual(len(tracks1), 1)
        tid = tracks1[0].track_id

        # Frame 2: Person moves slightly
        dets_f2 = [{"bbox": [105.0, 102.0, 185.0, 302.0], "conf": 0.88}]
        tracks2 = tracker.update(dets_f2)
        self.assertEqual(len(tracks2), 1)
        self.assertEqual(tracks2[0].track_id, tid, "Track ID must persist across frames")

    def test_fall_detector_upright_vs_prone(self):
        fall_detector = FallDetector(confirmation_frames=3, floor_level_ratio=0.65)

        # 1. Upright person (height > width, torso angle low)
        upright_bbox = [100.0, 100.0, 160.0, 320.0]  # width=60, height=220 (ratio=0.27)
        res_upright = fall_detector.analyze_pose(upright_bbox, None, frame_h=480)
        self.assertEqual(res_upright["posture"], "Upright")
        self.assertFalse(res_upright["is_candidate"])

        # 2. Patient sleeping in an elevated bed (y2=220, frame_h=480 -> y_ratio=0.45 < 0.65 floor level)
        bed_sleeping_bbox = [100.0, 150.0, 340.0, 220.0]  # width=240, height=70
        res_bed = fall_detector.analyze_pose(bed_sleeping_bbox, None, frame_h=480)
        self.assertEqual(res_bed["posture"], "Lying in Bed (Resting)")
        self.assertFalse(res_bed["is_candidate"], "Patient resting on elevated bed must NOT be flagged as fall")

        # 3. Patient lying in a designated Bed Safe Zone
        bed_zone = [{"name": "Bed 1", "x1": 0.1, "y1": 0.2, "x2": 0.8, "y2": 0.9}]
        res_zone = fall_detector.analyze_pose(bed_sleeping_bbox, None, frame_h=480, frame_w=640, bed_zones=bed_zone)
        self.assertEqual(res_zone["posture"], "Lying in Bed (Resting)")
        self.assertFalse(res_zone["is_candidate"])

        # 4. True fall on the floor (y2=420, frame_h=480 -> y_ratio=0.875 >= 0.65 floor level)
        floor_fall_bbox = [100.0, 350.0, 340.0, 420.0]  # width=240, height=70
        res_floor = fall_detector.analyze_pose(floor_fall_bbox, None, frame_h=480)
        self.assertEqual(res_floor["posture"], "Horizontal / Floor Fall")
        self.assertTrue(res_floor["is_candidate"], "Horizontal posture on the floor MUST be flagged as fall candidate")

        # 5. Temporal confirmation check for floor fall
        tracker = MultiObjectTracker()
        tracks = tracker.update([{"bbox": floor_fall_bbox, "conf": 0.9}])
        target = tracks[0]

        # Process frames
        is_fall, _ = fall_detector.process_track(target, frame_h=480)
        self.assertFalse(is_fall)
        is_fall, _ = fall_detector.process_track(target, frame_h=480)
        self.assertFalse(is_fall)
        is_fall, desc = fall_detector.process_track(target, frame_h=480)
        self.assertTrue(is_fall, "Should trigger fall alert after temporal persistence frames on the floor")
        self.assertIn("Possible patient floor fall detected", desc)

    def test_unattended_object_detector(self):
        obj_detector = UnattendedObjectDetector(time_threshold_sec=0.1, proximity_radius_px=100.0)

        # Bag detected at (400, 400), person far away at (100, 100)
        detected_objects = [{"class_name": "backpack", "bbox": [390.0, 390.0, 420.0, 420.0]}]
        detected_persons = [{"bbox": [90.0, 90.0, 130.0, 220.0]}]

        import time
        # Initial frame
        alerts1 = obj_detector.update(detected_objects, detected_persons)
        self.assertEqual(len(alerts1), 0, "No alert on first frame before threshold")

        time.sleep(0.15)  # Exceed 0.1s threshold
        alerts2 = obj_detector.update(detected_objects, detected_persons)
        self.assertEqual(len(alerts2), 1, "Should trigger unattended object alert")
        self.assertIn("Unattended backpack", alerts2[0][1])

    def test_crowd_monitor(self):
        monitor = CrowdMonitor(threshold=3, cooldown_sec=1.0)
        # Below threshold
        is_alert, _ = monitor.check_crowd(2, "Ward 4")
        self.assertFalse(is_alert)

        # Exceeds threshold
        is_alert, desc = monitor.check_crowd(4, "Ward 4")
        self.assertTrue(is_alert)
        self.assertIn("Crowd threshold exceeded", desc)

    def test_restricted_zone_monitor(self):
        zone_monitor = RestrictedZoneMonitor(cooldown_sec=1.0)
        zone = {"name": "Medication Cart", "x1": 0.1, "y1": 0.1, "x2": 0.4, "y2": 0.5}

        tracker = MultiObjectTracker()
        # Person feet inside zone: x=200, y=250 in 1000x1000 frame (x: 0.2, y: 0.25)
        tracks = tracker.update([{"bbox": [180.0, 100.0, 220.0, 250.0], "conf": 0.9}])
        intrusions = zone_monitor.check_intrusions(tracks, [zone], frame_w=1000, frame_h=1000, camera_name="Ward 4")
        self.assertEqual(len(intrusions), 1)
        self.assertIn("Individual #1 entered designated zone 'Medication Cart'", intrusions[0][2])

    def test_event_correlator(self):
        correlator = EventCorrelator()
        recent_events = [
            {"camera_id": "CAM-01", "camera_name": "Ward 4", "event_type": "Possible Patient Fall"},
            {"camera_id": "CAM-01", "camera_name": "Ward 4", "event_type": "Crowd Limit Exceeded"}
        ]
        correlated = correlator.evaluate_rules(recent_events)
        self.assertEqual(len(correlated), 1)
        self.assertEqual(correlated[0]["rule"], "FALL_AND_CROWD_SURGE")
        self.assertEqual(correlated[0]["priority"], "Critical")

if __name__ == "__main__":
    unittest.main()
