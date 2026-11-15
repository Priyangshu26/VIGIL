"""
VIGIL Vision Detector
Handles YOLO model loading, inference execution, and hardware acceleration fallback.
"""
import os
import torch
import numpy as np

# Ensure writable YOLO cache directory
os.environ["YOLO_CONFIG_DIR"] = "/tmp/Ultralytics"
from ultralytics import YOLO
from config.settings import YOLO_POSE_MODEL, YOLO_OBJ_MODEL, INFERENCE_IMAGE_SIZE, CONFIDENCE_THRESHOLD

class VisionDetector:
    def __init__(self):
        self.device = self._detect_device()
        print(f"[VisionDetector] Initializing models on target device: {self.device}")
        
        # Load YOLOv8n-pose for joint person detection, tracking and skeletal analysis
        try:
            self.pose_model = YOLO(YOLO_POSE_MODEL)
            self.pose_model.to(self.device)
            print("[VisionDetector] Loaded YOLO pose model successfully.")
        except Exception as e:
            print(f"[VisionDetector] Warning: Could not load pose model {YOLO_POSE_MODEL}: {e}")
            self.pose_model = None

        # Load YOLOv8n for COCO object detection (backpacks, handbags, suitcases)
        try:
            self.obj_model = YOLO(YOLO_OBJ_MODEL)
            self.obj_model.to(self.device)
            print("[VisionDetector] Loaded YOLO object model successfully.")
        except Exception as e:
            print(f"[VisionDetector] Warning: Could not load object model {YOLO_OBJ_MODEL}: {e}")
            self.obj_model = None

    def _detect_device(self) -> str:
        """Determines best available hardware target (MPS on Apple Silicon, else CPU)."""
        if torch.backends.mps.is_available():
            try:
                # Test MPS with small tensor
                _ = torch.zeros(1).to("mps")
                return "mps"
            except Exception:
                return "cpu"
        return "cpu"

    def detect_pose(self, frame, conf: float = CONFIDENCE_THRESHOLD, imgsz: int = INFERENCE_IMAGE_SIZE):
        """
        Runs YOLO pose estimation.
        Returns:
            list of dicts containing:
            - bbox: [x1, y1, x2, y2]
            - conf: float
            - keypoints: np.ndarray (17, 3) [x, y, conf]
        """
        if self.pose_model is None or frame is None:
            return []

        results = self.pose_model.predict(
            source=frame,
            conf=conf,
            imgsz=imgsz,
            device=self.device,
            verbose=False
        )

        detections = []
        if not results:
            return detections

        res = results[0]
        if res.boxes is None or len(res.boxes) == 0:
            return detections

        boxes = res.boxes.xyxy.cpu().numpy()
        scores = res.boxes.conf.cpu().numpy()
        kpts = res.keypoints.data.cpu().numpy() if res.keypoints is not None else None

        for i, box in enumerate(boxes):
            keypoint_data = kpts[i] if kpts is not None and i < len(kpts) else None
            detections.append({
                "bbox": [float(c) for c in box],
                "conf": float(scores[i]),
                "keypoints": keypoint_data
            })

        return detections

    def detect_objects(self, frame, target_classes=None, conf: float = CONFIDENCE_THRESHOLD, imgsz: int = INFERENCE_IMAGE_SIZE):
        """
        Runs YOLO object detection for unattended object detection (e.g. backpacks, bags).
        Target classes default to COCO [24, 26, 28].
        """
        if self.obj_model is None or frame is None:
            return []

        results = self.obj_model.predict(
            source=frame,
            conf=conf,
            imgsz=imgsz,
            classes=target_classes,
            device=self.device,
            verbose=False
        )

        objects = []
        if not results:
            return objects

        res = results[0]
        if res.boxes is None or len(res.boxes) == 0:
            return objects

        boxes = res.boxes.xyxy.cpu().numpy()
        scores = res.boxes.conf.cpu().numpy()
        classes = res.boxes.cls.cpu().numpy()

        for i, box in enumerate(boxes):
            cls_id = int(classes[i])
            cls_name = self.obj_model.names.get(cls_id, f"obj_{cls_id}")
            objects.append({
                "bbox": [float(c) for c in box],
                "conf": float(scores[i]),
                "class_id": cls_id,
                "class_name": cls_name
            })

        return objects
