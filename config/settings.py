"""
VIGIL Configuration and System Settings
AI-Powered Healthcare Safety and Monitoring System
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
VIDEO_DIR = DATA_DIR / "videos"
DB_PATH = DATA_DIR / "vigil.db"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# Database Configuration
DATABASE_URL = f"sqlite:///{DB_PATH}"

# AI / Computer Vision Model Settings
# We use YOLOv8n-pose for joint person detection, tracking, and pose analysis (fall detection)
# and YOLOv8n for general COCO object detection (backpack, handbag, suitcase, etc.)
YOLO_POSE_MODEL = "yolov8n-pose.pt"
YOLO_OBJ_MODEL = "yolov8n.pt"
INFERENCE_IMAGE_SIZE = 640  # Standard resolution for robust inference
CONFIDENCE_THRESHOLD = 0.40

# Hardware Acceleration
# Auto-detect Apple Silicon MPS (Metal Performance Shaders) or fallback to CPU
DEVICE = "cpu"  # Checked at runtime in vision/detector.py

# Fall Detection Parameters
FALL_CONFIRMATION_FRAMES = 8       # Number of consecutive frames needed to confirm fall
FALL_ASPECT_RATIO_THRESH = 1.15    # Width / Height ratio indicating prone orientation
FALL_TORSO_ANGLE_THRESH = 55.0     # Angle (degrees) from vertical; >55° is horizontal
FALL_COOLDOWN_SECONDS = 20.0       # Alert cooldown per tracked person

# Unattended Object Detection Parameters
UNATTENDED_OBJECT_CLASSES = [24, 26, 28]  # COCO class IDs: 24: backpack, 26: handbag, 28: suitcase
UNATTENDED_TIME_THRESH_SEC = 5.0          # Seconds stationary before alert (demo default)
PERSON_PROXIMITY_PIXELS = 130             # Radius within which an object is considered attended
OBJECT_COOLDOWN_SECONDS = 30.0

# Crowd Monitoring Parameters
DEFAULT_CROWD_THRESHOLD = 4               # Default person limit per camera
CROWD_COOLDOWN_SECONDS = 25.0

# Restricted Zone Monitoring
RESTRICTED_ZONE_COOLDOWN_SECONDS = 20.0

# Event Correlation Window
CORRELATION_WINDOW_SECONDS = 30.0         # Time window to associate related events

# Severity Levels
SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"
SEVERITY_MEDIUM = "Medium"
SEVERITY_LOW = "Low"

# Incident Statuses
STATUS_PENDING = "Pending"
STATUS_VERIFIED = "Verified"
STATUS_RESOLVED = "Resolved"
STATUS_FALSE_ALERT = "False Alert"

# UI Theme Palette (Healthcare Professional)
THEME = {
    "navy": "#15324B",
    "blue": "#2878B5",
    "light_bg": "#F4F7FA",
    "white": "#FFFFFF",
    "text": "#263746",
    "muted": "#6C7A89",
    "amber": "#E6A23C",
    "red": "#D9534F",
    "green": "#398568",
    "border": "#DCE2E6",
}
