"""
Unit tests for VIGIL Incident Management & Context-Aware Correlation
"""
import unittest
import time
from backend.database import init_db
from backend.incident_manager import incident_manager
from config.settings import SEVERITY_CRITICAL, SEVERITY_MEDIUM

class TestIncidentManager(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_cooldown_prevention(self):
        cooldown_key = f"test_cooldown_{time.time()}"
        # First trigger should succeed
        inc1 = incident_manager.create_incident(
            camera_id="CAM-01",
            camera_name="Ward 4 Corridor",
            event_type="Test Cooldown Alert",
            severity=SEVERITY_MEDIUM,
            description="First trigger",
            cooldown_key=cooldown_key,
            cooldown_seconds=10.0,
            trigger_correlation=False
        )
        self.assertIsNotNone(inc1)

        # Immediate second trigger with same key should be blocked by cooldown
        inc2 = incident_manager.create_incident(
            camera_id="CAM-01",
            camera_name="Ward 4 Corridor",
            event_type="Test Cooldown Alert",
            severity=SEVERITY_MEDIUM,
            description="Second trigger",
            cooldown_key=cooldown_key,
            cooldown_seconds=10.0,
            trigger_correlation=False
        )
        self.assertIsNone(inc2, "Repeated trigger during cooldown must return None")

    def test_context_aware_correlation(self):
        cam_id = f"CAM-CORR-{int(time.time())}"
        
        # 1. Fall event arrives
        inc_fall = incident_manager.create_incident(
            camera_id=cam_id,
            camera_name="ICU Hallway",
            event_type="Possible Patient Fall",
            severity=SEVERITY_CRITICAL,
            description="Patient slipped and fell near bed 3",
            trigger_correlation=True
        )
        self.assertIsNotNone(inc_fall)

        # 2. Crowd surge arrives on same camera within correlation window
        inc_crowd = incident_manager.create_incident(
            camera_id=cam_id,
            camera_name="ICU Hallway",
            event_type="Crowd Limit Exceeded",
            severity=SEVERITY_MEDIUM,
            description="Occupancy increased to 6 persons",
            trigger_correlation=True
        )
        self.assertIsNotNone(inc_crowd)

        # 3. Check that the correlated event was automatically generated
        incidents = incident_manager.get_incidents(camera_id=cam_id)
        corr_events = [i for i in incidents if "Correlated:" in i["event_type"]]
        self.assertGreaterEqual(len(corr_events), 1, "Context-aware correlation engine must raise correlated alert")
        self.assertEqual(corr_events[0]["severity"], SEVERITY_CRITICAL)
        self.assertIn("Correlated emergency detected", corr_events[0]["description"])

if __name__ == "__main__":
    unittest.main()
