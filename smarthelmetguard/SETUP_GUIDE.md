# SmartHelmetGuard - Complete Setup & Deployment Guide

## 📋 Table of Contents

1. [Quick Start (5 minutes)](#quick-start)
2. [Full Installation (Detailed)](#full-installation)
3. [Running the System](#running-the-system)
4. [Troubleshooting](#troubleshooting)
5. [System Architecture](#system-architecture)
6. [Performance Tuning](#performance-tuning)
7. [Deployment](#deployment)

---

## Quick Start

### Windows
```bash
# Navigate to project directory
cd d:\AI_Projects\Helmet-Detector\smarthelmetguard

# Run the launcher (handles everything)
run_dashboard.bat
```

### Linux/macOS
```bash
cd /path/to/smarthelmetguard
chmod +x run_dashboard.sh
./run_dashboard.sh
```

Then open: **http://localhost:8501**

---

## Full Installation

### 1. Prerequisites Check

**Windows:**
```powershell
# Check Python
python --version  # Should be 3.8+

# Check pip
pip --version
```

**Linux/macOS:**
```bash
python3 --version
pip3 --version
```

**Install Python if needed:**
- Windows: https://www.python.org/downloads
- macOS: `brew install python3.10`
- Ubuntu: `sudo apt-get install python3.10 python3.10-venv python3-pip`

### 2. Clone/Setup Project

```bash
# Navigate to projects directory
cd d:\AI_Projects

# Clone (or you already have it)
git clone <repo-url>
cd Helmet-Detector/smarthelmetguard

# OR if already exists:
cd smarthelmetguard
```

### 3. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in terminal prompt.

### 4. Install PyTorch (CPU or GPU)

**For NVIDIA GPU (CUDA 11.8):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**For CPU Only:**
```bash
pip install torch torchvision torchaudio
```

**For AMD GPU (ROCm):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7
```

### 5. Install All Dependencies

```bash
pip install -r requirements.txt
```

**If you encounter issues, try installing separately:**
```bash
pip install ultralytics==8.1.0
pip install opencv-python==4.8.1.78
pip install streamlit==1.28.1
pip install plotly pandas scikit-image
```

### 6. Verify Installation

```bash
# Check all imports work
python -c "from ultralytics import YOLO; print('YOLOv8: OK')"
python -c "import cv2; print('OpenCV: OK')"
python -c "import streamlit; print('Streamlit: OK')"
python -c "import torch; print(f'PyTorch: OK (GPU: {torch.cuda.is_available()})')"
```

All should print "OK" or device info.

### 7. Run System Health Check

```bash
python demo.py --mode health
```

This will verify:
- ✓ Python version
- ✓ PyTorch installation
- ✓ OpenCV working
- ✓ Camera accessible
- ✓ Database ready
- ✓ Models available

---

## Running the System

### Option 1: Streamlit Dashboard (Recommended)

```bash
# Activate venv first
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Start dashboard
streamlit run dashboard.py
```

Then open: http://localhost:8501

### Option 2: Manual Detection (OpenCV Display)

```bash
# Run with webcam
python main.py --mode manual --camera 0

# Run with video file
python main.py --mode manual --camera "path/to/video.mp4"

# Run with RTSP stream
python main.py --mode manual --camera "rtsp://camera-ip:554/stream"

# Save output video
python main.py --mode manual --camera 0 --output "output.mp4"
```

### Option 3: Demo/Testing

```bash
# Quick detection demo (30 seconds)
python demo.py --mode demo --duration 30

# Database operations demo
python demo.py --mode database

# Evidence management demo
python demo.py --mode evidence

# System health check
python demo.py --mode health
```

---

## Configuration

### Adjust Settings

Edit `config.py` to change:

```python
# Model accuracy vs speed
HELMET_MODEL_NAME = "yolov8n"   # Fast (nano)
HELMET_MODEL_NAME = "yolov8s"   # Balanced (small)
HELMET_MODEL_NAME = "yolov8m"   # Default (medium)
HELMET_MODEL_NAME = "yolov8l"   # Accurate (large)

# Detection confidence (0-1, higher = stricter)
HELMET_CONFIDENCE_THRESHOLD = 0.45

# Tracking
TRACK_MAX_AGE = 30  # Frames to keep track without detection
TRACKING_COOLDOWN = 15  # Seconds before same rider counts again

# Storage
EVIDENCE_RETENTION_DAYS = 30  # Auto-delete after X days

# Feature toggles
ENABLE_FACE_BLUR = False
ENABLE_DUPLICATE_PREVENTION = True
```

### Use Configuration Profiles

```python
from profiles import apply_profile

# High-performance (low-resource systems)
apply_profile('performance')

# Production (high accuracy)
apply_profile('production')

# Privacy-focused (no face storage)
apply_profile('privacy')
```

---

## Troubleshooting

### Issue: Camera Not Opening

**Windows Registry Fix:**
```powershell
# Run as Administrator
# Then:
wmic logicaldisk get name
```

**Linux Camera Check:**
```bash
ls /dev/video*
# Check permissions:
sudo usermod -a -G plugdev $USER
# Restart after
```

### Issue: Low FPS (< 10 FPS)

**Solutions (in order):**

1. Use smaller model:
```python
HELMET_MODEL_NAME = "yolov8n"  # Nano model
```

2. Lower resolution:
```python
CAMERA_WIDTH = 640   # Not 1280
CAMERA_HEIGHT = 480  # Not 720
```

3. Disable face detection:
```python
SAVE_FACE_CROP = False
```

4. Enable GPU:
```python
# In detector.py, ensure:
device = "cuda"  # Not "cpu"
```

### Issue: Out of Memory (OOM)

**GPU Memory:**
```python
# Use smaller model
HELMET_MODEL_NAME = "yolov8s"

# Or in code:
detector = HelmetDetector(device="cpu")  # Use CPU instead
```

**RAM Memory:**
```python
# Reduce frame queue size
camera = CameraManager(frame_queue_size=10)  # Not 30
```

### Issue: Models Not Downloading

```bash
# Manual model download
python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"
python -c "from ultralytics import YOLO; YOLO('yolov8n-face.pt')"
```

### Issue: Database Errors

```bash
# Reset database (deletes all records)
rm smarthelmetguard/data/violations.db

# Rebuild on next run (auto)
```

### Issue: Port 8501 Already in Use

```bash
# Use different port
streamlit run dashboard.py --server.port 8502
```

---

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Camera Input                          │
│  (Webcam / Video File / RTSP Stream)                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              HelmetDetector (YOLOv8)                     │
│  Detects: helmet / no_helmet / person / motorcycle      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            ByteTracker (Multi-Object)                   │
│  Assigns track IDs, prevents duplicates                 │
└────────────────────┬────────────────────────────────────┘
                     │
              ┌──────┴──────┐
              │             │
              ▼             ▼
        ┌──────────┐   ┌──────────────┐
        │Helmet OK │   │NO HELMET ⚠️   │
        └──────────┘   └──────┬───────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ FaceExtractor (YOLOv8) │
                    │ Extract face crops      │
                    └──────────┬────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
              ┌─────────────┐      ┌──────────────┐
              │Save Evidence│      │Update Database│
              │(Images JSON)│      │(Metadata)    │
              └─────────────┘      └──────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Streamlit Dashboard  │
                    │ (Visualization)      │
                    └─────────────────────┘
```

### Data Flow

```
Video Frame
    ↓
Detection (25-35ms)
    ↓
Tracking & Association (5-10ms)
    ↓
Violation Classification (5ms)
    ↓
Face Extraction (10-20ms)
    ↓
Evidence Saving (30-50ms disk I/O)
    ↓
Database Logging (5-10ms)
    ↓
Dashboard Update (real-time)
```

### File Structure

```
smarthelmetguard/
├── modules/
│   ├── __init__.py              # Main HelmetViolationDetector class
│   ├── detector.py              # YOLOv8 helmet detection
│   ├── face_extractor.py        # Face detection & cropping
│   ├── tracker.py               # ByteTrack implementation
│   ├── camera.py                # Camera/video input management
│   ├── database.py              # SQLite database operations
│   └── evidence_manager.py      # Evidence file organization
│
├── ui/                          # UI components (future)
│
├── config.py                    # Configuration constants
├── utils.py                     # Helper functions
├── profiles.py                  # Configuration profiles
├── dashboard.py                 # Streamlit web UI
├── dashboard_advanced.py        # Advanced dashboard
├── main.py                      # CLI entry point
├── demo.py                      # Testing & demos
│
├── evidence/                    # Generated: evidence storage
│ └── YYYY-MM-DD/               # Organized by date
│     └── {track_id}-HHmmss/    # Per violation
│         ├── full_frame.jpg
│         ├── face_0.jpg
│         └── metadata.json
│
├── data/                        # Generated: database
│   └── violations.db           # SQLite database
│
├── logs/                        # Generated: system logs
│   └── system.log
│
├── venv/                        # Virtual environment
│
├── requirements.txt            # Python dependencies
├── README.md                   # User documentation
├── SETUP_GUIDE.md             # This file
├── run_dashboard.bat          # Windows launcher
└── run_dashboard.sh           # Linux/macOS launcher
```

---

## Performance Tuning

### Optimizing for Speed

```python
# config.py

# 1. Use smallest model
HELMET_MODEL_NAME = "yolov8n"

# 2. Lower resolution
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# 3. Disable optional features
SAVE_FACE_CROP = False
ENABLE_FACE_BLUR = False

# Expected: 20-30 FPS on CPU
```

### Optimizing for Accuracy

```python
# config.py

# 1. Use largest model
HELMET_MODEL_NAME = "yolov8l"

# 2. Higher resolution
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080

# 3. Stricter confidence
HELMET_CONFIDENCE_THRESHOLD = 0.6

# 4. More tracking hits
TRACK_MIN_HITS = 5

# Expected: 8-12 FPS with RTX GPU, high accuracy
```

### GPU vs CPU

**GPU Benefits:**
- 3-5x faster processing
- Higher resolution support
- Real-time 4K possible

**CPU Fallback:**
- Lower resolution (640x480)
- Smaller model (yolov8n)
- Acceptable FPS (15-25)
- Lower latency for web dashboard

### Batch Processing (Future)

For post-processing videos:
```python
# Process video file offline
python main.py --mode manual --camera "archive_video.mp4" --headless
```

---

## Deployment

### Production Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] All dependencies installed
- [ ] Camera/stream configured and tested
- [ ] Models downloaded (check `/models/`)
- [ ] Database created (`data/violations.db`)
- [ ] Evidence directory writable (`evidence/`)
- [ ] Health check passed (python demo.py --mode health)
- [ ] Dashboard runs without errors
- [ ] Test detection with actual camera

### Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY smarthelmetguard/ .

CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build & Run:
```bash
docker build -t smarthelmetguard .
docker run -p 8501:8501 --device /dev/video0 smarthelmetguard
```

### Systemd Service (Linux)

Create `/etc/systemd/system/smarthelmetguard.service`:
```ini
[Unit]
Description=SmartHelmetGuard Helmet Detection System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smarthelmetguard
Environment="PATH=/home/pi/smarthelmetguard/venv/bin"
ExecStart=/home/pi/smarthelmetguard/venv/bin/python -m streamlit run dashboard.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable & Start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smarthelmetguard
sudo systemctl start smarthelmetguard
```

### Remote Access

**SSH Tunnel:**
```bash
# On server
streamlit run dashboard.py --server.address localhost

# On local machine
ssh -L 8501:localhost:8501 user@server
# Then open: http://localhost:8501
```

---

## API Usage (Optional)

```python
from modules import HelmetViolationDetector
import cv2

# Initialize
detector = HelmetViolationDetector(camera_source=0)
detector.start()

# Process frame
while True:
    frame = detector.camera.get_frame()
    if frame is None:
        continue
    
    result = detector.process_frame(frame)
    
    if result:
        print(f"FPS: {result['fps']:.1f}")
        print(f"Violations: {len(result['violations'])}")
        
        # Display
        cv2.imshow("Detection", result['frame'])
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

detector.stop()
cv2.destroyAllWindows()
```

---

## Support & Documentation

**Getting Help:**
1. Run health check: `python demo.py --mode health`
2. Check logs: `cat logs/system.log`
3. Review README.md for features
4. Adjust config.py for your hardware

**Common Commands:**

```bash
# Test  detection
python demo.py --mode demo

# Check database
python -c "from modules.database import DatabaseManager; db = DatabaseManager(); print(f'Violations: {db.get_total_violations()}')"

# List evidence
python -c "from modules.evidence_manager import EvidenceManager; em = EvidenceManager(); print(em.get_evidence_stats())"

# Clear old evidence
python -c "from modules.evidence_manager import EvidenceManager; em = EvidenceManager(); em.cleanup_old_evidence(days=30)"
```

---

## License & Attribution

Built with:
- YOLOv8 (Ultralytics)
- OpenCV
- Streamlit
- ByteTrack algorithm

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Status**: Production Ready ✅
