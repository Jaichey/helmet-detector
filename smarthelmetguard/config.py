# SmartHelmetGuard - Configuration Settings
# This file contains all configuration constants for the system

import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent
MODELS_DIR = PROJECT_ROOT / "models"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
ASSETS_DIR = PROJECT_ROOT / "assets"
DB_DIR = PROJECT_ROOT / "data"

# Create directories if they don't exist
EVIDENCE_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Database Configuration
DATABASE_PATH = DB_DIR / "violations.db"

# Model Configuration
HELMET_MODEL_NAME = "yolov8m"  # Can be yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
FACE_MODEL_TYPE = "opencv"  # opencv (default), yolov8 (requires custom face model)

# Detection Parameters
HELMET_CONFIDENCE_THRESHOLD = 0.45
FACE_CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45

# Tracking Parameters
TRACK_MAX_AGE = 30  # Frames to keep track alive without detection
TRACK_MIN_HITS = 3  # Minimum hits to create track
TRACK_IOU_THRESHOLD = 0.3

# Evidence Storage Parameters
MIN_FACE_SIZE = 20  # Minimum face size in pixels to save
EVIDENCE_RETENTION_DAYS = 30  # Days to keep evidence
SAVE_FULL_FRAME = True
SAVE_FACE_CROP = True
SAVE_EVIDENCE_AUTO = True

# Camera Configuration
CAMERA_FPS = 30
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CONFIDENCE_SMOOTHING = 5  # Moving average window for confidence scores

# UI Configuration
STREAMLIT_WIDE_MODE = True
DASHBOARD_REFRESH_INTERVAL = 1  # Seconds
VIOLATION_HISTORY_LIMIT = 100  # Show last N violations

# Feature Flags
ENABLE_FACE_BLUR = False  # Blur face in full frame save
ENABLE_NOTIFICATION_SOUND = True
ENABLE_TRACKING = True
ENABLE_DUPLICATE_PREVENTION = True  # Avoid saving same violator repeatedly
TRACKING_COOLDOWN = 15  # Seconds before counting same rider again

# API Configuration (Optional)
API_ENABLED = True
API_HOST = "127.0.0.1"
API_PORT = 5000

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "logs" / "system.log"
LOG_FILE.parent.mkdir(exist_ok=True)

# Classes for detection
DETECTION_CLASSES = {
    "helmet": 0,
    "no_helmet": 1,
    "person": 2,
    "motorcycle": 3
}

# Color Configuration (BGR format for OpenCV)
COLOR_HELMET = (0, 255, 0)  # Green
COLOR_NO_HELMET = (0, 0, 255)  # Red
COLOR_PERSON = (255, 165, 0)  # Orange
COLOR_TRACKING = (255, 255, 0)  # Cyan

# Evidence Categories
EVIDENCE_CATEGORIES = {
    "no_helmet": "No Helmet",
    "helmet": "Helmet Detected",
    "unknown": "Unknown"
}
