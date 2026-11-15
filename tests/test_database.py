"""
Unit test for VIGIL Database & Incident Persistence
"""
import unittest
from backend.database import init_db, SessionLocal
from backend.models import Camera, Incident, AppSetting
from backend.incident_manager import incident_manager

class TestDatabase(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_database_initialization(self):
        session = SessionLocal()
        cams = session.query(Camera).all()
        self.assertGreaterEqual(len(cams), 1, "At least one camera should be seeded.")
        
        incidents = session.query(Incident).all()
        self.assertGreaterEqual(len(incidents), 1, "Seed incidents should exist.")

        settings = session.query(AppSetting).all()
        self.assertGreaterEqual(len(settings), 1, "App settings should exist.")
        session.close()

    def test_incident_creation_and_retrieval(self):
        inc = incident_manager.create_incident(
            camera_id="CAM-01",
            camera_name="Ward 4 Corridor",
            event_type="Test Fall Incident",
            severity="High",
            description="Automated unit test incident verification.",
            trigger_correlation=False
        )
        self.assertIsNotNone(inc)
        self.assertTrue(inc.incident_id.startswith("INC-"))

        # Verify retrieval
        incidents = incident_manager.get_incidents(camera_id="CAM-01")
        found = any(i["incident_id"] == inc.incident_id for i in incidents)
        self.assertTrue(found, "Newly created incident should be found in query.")

    def test_incident_status_update(self):
        inc = incident_manager.create_incident(
            camera_id="CAM-01",
            camera_name="Ward 4 Corridor",
            event_type="Verification Test",
            severity="Medium",
            description="Status transition test.",
            trigger_correlation=False
        )
        ok = incident_manager.update_incident_status(inc.incident_id, "Verified", "Clinical staff confirmed")
        self.assertTrue(ok)
        
        updated = incident_manager.get_incidents(camera_id="CAM-01")
        target = next(i for i in updated if i["incident_id"] == inc.incident_id)
        self.assertEqual(target["status"], "Verified")
        self.assertEqual(target["verification_notes"], "Clinical staff confirmed")

if __name__ == "__main__":
    unittest.main()
