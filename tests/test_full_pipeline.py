"""
Test full vision pipeline on demonstration video footage
"""
import cv2
from vision.pipeline import VisionPipeline
from backend.database import init_db
from backend.incident_manager import incident_manager

def test_pipeline_on_video():
    init_db()
    video_path = "data/videos/demo_hospital_corridor.mp4"
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), f"Cannot open {video_path}"

    pipeline = VisionPipeline({
        "camera_id": "CAM-01",
        "name": "Ward 4 Corridor",
        "crowd_threshold": 3,
        "restricted_zones": [{"name": "Med Cart Zone", "x1": 0.05, "y1": 0.60, "x2": 0.35, "y2": 0.85}],
        "enabled_modules": ["human_tracking", "fall_detection", "object_detection", "crowd_monitoring", "restricted_zone"]
    })

    frame_count = 0
    total_alerts = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame_count >= 60:  # Test 60 frames
            break
        annotated_frame, metrics, alerts = pipeline.process_frame(frame)
        assert annotated_frame is not None
        assert "people_count" in metrics
        frame_count += 1
        total_alerts += len(alerts)

    cap.release()
    print(f"Successfully processed {frame_count} frames. Alerts triggered: {total_alerts}")

if __name__ == "__main__":
    test_pipeline_on_video()
