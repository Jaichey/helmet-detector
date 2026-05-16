# SmartHelmetGuard - Project File Directory

## Complete Project Structure & File Descriptions

```
smarthelmetguard/
├── 📄 Core Configuration
│   ├── config.py                    # Main configuration constants
│   ├── profiles.py                  # Pre-configured deployment profiles
│   └── .gitignore                   # Git ignore patterns
│
├── 📦 Core Modules (smarthelmetguard/modules/)
│   ├── __init__.py                  # Main HelmetViolationDetector orchestrator class
│   ├── detector.py                  # YOLOv8 helmet detection wrapper
│   ├── face_extractor.py            # Face detection and cropping engine
│   ├── tracker.py                   # ByteTrack multi-object tracking
│   ├── camera.py                    # Camera/video/RTSP input management
│   ├── database.py                  # SQLite database operations
│   └── evidence_manager.py          # Evidence file organization and storage
│
├── 🎨 User Interface
│   ├── dashboard.py                 # Main Streamlit web dashboard
│   ├── dashboard_advanced.py        # Advanced dashboard with more features
│   └── assets/                      # UI images and icons (folder)
│
├── 🚀 Entry Points
│   ├── main.py                      # CLI and orchestration entry point
│   ├── demo.py                      # Testing, demos, and health checks
│   ├── run_dashboard.bat            # Windows launcher script
│   └── run_dashboard.sh             # Linux/macOS launcher script
│
├── 🛠️ Utilities
│   └── utils.py                     # Helper functions (logging, image processing, etc)
│
├── 📚 Documentation
│   ├── README.md                    # Complete feature documentation
│   ├── SETUP_GUIDE.md              # Detailed installation & deployment guide
│   ├── QUICK_REFERENCE.md          # Dashboard usage & quick tips
│   └── PROJECT_FILE_DIRECTORY.md   # This file
│
├── ⚙️ Dependencies & Environment
│   ├── requirements.txt             # Python package dependencies
│   └── venv/                        # Virtual environment (auto-created)
│
├── 📊 Generated Folders (auto-created on first run)
│   ├── evidence/                    # Stored evidence files
│   │   └── YYYY-MM-DD/             # Organized by date
│   │       └── {track_id}-HHmmss/  # Per-violation folder
│   │           ├── full_frame.jpg
│   │           ├── face_0.jpg
│   │           └── metadata.json
│   ├── data/                        # Database folder
│   │   └── violations.db           # SQLite database file
│   ├── logs/                        # System logs
│   │   └── system.log              # Main application log
│   └── models/                      # Downloaded AI models (auto-managed)
│       ├── yolov8m.pt
│       └── yolov8n-face.pt
│
└── 📁 Additional Folders (optional)
    ├── tests/                       # Unit tests (future)
    ├── ui/                          # Advanced UI components (future)
    └── api/                         # Flask API support (future)
```

---

## File Descriptions & Key Functions

### Core Files

#### `config.py` (400+ lines)
**Purpose**: Centralized configuration constants

**Key Variables**:
- Model names and confidence thresholds
- Tracking parameters (max age, min hits)
- Evidence storage settings
- Feature flags and toggles
- Database paths

**Usage**:
```python
from config import HELMET_MODEL_NAME, CONFIDENCE_THRESHOLD
```

#### `utils.py` (500+ lines)
**Purpose**: Shared utility functions and helper classes

**Classes**:
- `ImageProcessor` - Image manipulation, bounding box drawing
- `TimeUtils` - Timestamp and date operations
- `FileUtils` - File and directory operations
- `BBoxUtils` - Bounding box calculations (IoU, area, center)

**Usage**:
```python
from utils import ImageProcessor, logger
frame = ImageProcessor.save_image(img, path)
```

#### `profiles.py` (150+ lines)
**Purpose**: Pre-configured deployment profiles

**Profiles**:
- `ProductionProfile` - High accuracy deployment
- `PerformanceProfile` - CPU-optimized
- `TestingProfile` - Loose detection
- `PrivacyProfile` - Minimal face data

**Usage**:
```python
from profiles import apply_profile
apply_profile('production')
```

---

### Module Files

#### `modules/detector.py` (350+ lines)
**Purpose**: Helmet detection using YOLOv8

**Classes**:
- `HelmetDetector` - Main detection wrapper
  - `detect()` - Run inference on frame
  - `filter_detections()` - Filter by area
  - `get_violation_status()` - Classify helmet/no-helmet
  - `warmup()` - Prepare model

- `DetectionAggregator` - Smooth confidence scores
  - `smooth_confidence()` - Moving average filtering

**Returns**:
```python
[{
    'bbox': [x1, y1, x2, y2],
    'class': 'helmet' or 'no_helmet',
    'confidence': 0.92,
    'class_id': 0,
    'area': pixels
}, ...]
```

#### `modules/face_extractor.py` (350+ lines)
**Purpose**: Face detection and extraction for violations

**Classes**:
- `FaceExtractor` - Face detection engine
  - `extract_faces()` - Find faces in rider region
  - `get_face_quality_score()` - Assess quality

- `FaceManager` - Track face history
  - `add_face()` - Store face detection
  - `get_best_face()` - Get highest quality

**Key Features**:
- Only extracts faces from "no_helmet" riders
- Fallback to rider region if face detection fails
- Quality scoring for better evidence

#### `modules/tracker.py` (400+ lines)
**Purpose**: Multi-object tracking with ByteTrack algorithm

**Classes**:
- `Track` - Individual tracked object
  - State: confirmed/tentative/deleted
  - Age, hits, confidence smoothing
  - Violation tracking and cooldown

- `ByteTracker` - Main tracking engine
  - `update()` - Process detections and update tracks
  - Duplicate detection prevention
  - Track lifecycle management

- `TrackingStatistics` - Track metrics
  - `get_statistics()` - Summary stats

**Key Features**:
- Prevents saving same violation twice
- Cooldown timer for repeat violations
- Track ID assignment

#### `modules/camera.py` (350+ lines)
**Purpose**: Camera and video input management

**Classes**:
- `CameraManager` - Single camera input
  - Sources: webcam, video file, RTSP
  - Threading for smooth capture
  - Frame queue management

- `MultiCameraManager` - Multiple cameras
  - Manage multiple sources simultaneously
  - Get frames from all cameras

**Features**:
- Non-blocking frame reading
- Auto-resize to target resolution
- Queue-based frame delivery

#### `modules/database.py` (400+ lines)
**Purpose**: SQLite database for violation records

**Database Tables**:
- `violations` - Main violation records
- `evidence` - Evidence files metadata
- `face_evidence` - Face-specific data
- `statistics` - Daily statistics

**Classes**:
- `DatabaseManager` - Main DB interface
  - `add_violation()` - Log violation
  - `add_evidence()` - Store evidence path
  - `get_violations()` - Query with filters
  - `cleanup_old_data()` - Auto-delete old records

**Indexes**: On timestamp, status, track_id for fast queries

#### `modules/evidence_manager.py` (350+ lines)
**Purpose**: Evidence file organization and storage

**Classes**:
- `EvidenceManager` - Evidence handling
  - `save_violation_evidence()` - Save all evidence
  - `save_face_evidence()` - Save individual face
  - `get_evidence_stats()` - Storage statistics
  - `cleanup_old_evidence()` - Delete old files

**Storage Structure**:
```
evidence/YYYY-MM-DD/{track_id}-HHmmss/
├── full_frame.jpg        (Marked with bounding boxes)
├── face_0.jpg            (Cropped face 1)
├── face_1.jpg            (Cropped face 2)
└── metadata.json         (All violation info)
```

---

### Entry Points

#### `modules/__init__.py` (320+ lines)
**Purpose**: Main system orchestrator

**Main Class**:
- `HelmetViolationDetector` - Complete system
  - `__init__()` - Initialize all components
  - `start()` - Begin detection
  - `stop()` - Shutdown gracefully
  - `process_frame()` - Core detection pipeline
  - `get_statistics()` - System stats
  - `_save_violation_evidence()` - Evidence handler

**Orchestration**:
- Combines all modules
- Manages detection pipeline
- Logs violations to database
- Saves evidence files

#### `main.py` (300+ lines)
**Purpose**: CLI entry point and argument handling

**Modes**:
- `dashboard` - Launch Streamlit UI
- `manual` - OpenCV window detection
- `api` - Flask REST API (future)

**Arguments**:
- `--mode` - Execution mode
- `--camera` - Camera source
- `--confidence` - Detection threshold
- `--output` - Output video file
- `--headless` - No GUI mode

#### `demo.py` (450+ lines)
**Purpose**: Testing and demonstration

**Demo Modes**:
- `health` - System health check
- `demo` - Live detection demo
- `database` - DB operations demo
- `evidence` - Evidence management demo

**Health Checks**:
- Python version
- PyTorch installation
- OpenCV availability
- Camera accessibility
- Database creation
- Model download

---

### User Interface

#### `dashboard.py` (500+ lines)
**Purpose**: Streamlit web dashboard

**Pages**:
1. **Live Monitoring** - Real-time feed and alerts
2. **Violation History** - Searchable record database
3. **Analytics** - Charts and statistics
4. **Settings** - Configuration options
5. **About** - System information

**Components**:
- Live video display
- Metric cards
- Violation cards
- Plotly charts
- Sliders and filters
- Data tables

#### `dashboard_advanced.py` (400+ lines)
**Purpose**: Advanced dashboard with enhanced UI

**Features**:
- Modern card-based layout
- Gradient backgrounds
- Custom CSS styling
- Animation support
- Better mobile responsiveness

---

### Launchers

#### `run_dashboard.bat` (50+ lines)
**Purpose**: Windows launcher script

**Steps**:
1. Create virtual environment
2. Activate venv
3. Install dependencies
4. Launch Streamlit

#### `run_dashboard.sh` (50+ lines)
**Purpose**: Linux/macOS launcher script

**Steps**:
1. Create virtual environment
2. Activate venv
3. Install dependencies
4. Launch Streamlit

---

### Documentation

#### `README.md` (500+ lines)
**Content**:
- Feature overview
- System requirements
- Installation steps
- Usage instructions
- Architecture overview
- Troubleshooting
- Performance metrics
- Privacy considerations

#### `SETUP_GUIDE.md` (600+ lines)
**Content**:
- Quick start (5 minutes)
- Full installation (step-by-step)
- Configuration profiles
- Performance tuning
- Deployment methods
- Docker setup
- Systemd service

#### `QUICK_REFERENCE.md` (600+ lines)
**Content**:
- Dashboard guide
- Tab-by-tab explanations
- Keyboard shortcuts
- Database schema reference
- SQL query examples
- Troubleshooting matrix
- Performance benchmarks

---

## File Dependencies

```
dashboard.py
├── modules/camera.py
├── modules/detector.py
├── modules/face_extractor.py
├── modules/tracker.py
├── modules/database.py
├── modules/evidence_manager.py
├── config.py
└── utils.py

modules/__init__.py (HelmetViolationDetector)
├── modules/camera.py
├── modules/detector.py
├── modules/face_extractor.py
├── modules/tracker.py
├── modules/database.py
├── modules/evidence_manager.py
├── config.py
└── utils.py

main.py
├── modules/__init__.py (HelmetViolationDetector)
└── All module dependencies

demo.py
├── modules/camera.py
├── modules/detector.py
├── modules/face_extractor.py
├── modules/tracker.py
├── modules/database.py
├── modules/evidence_manager.py
├── config.py
└── utils.py
```

---

## Database Files

### violations.db (SQLite)
**Tables**:
- violations (Primary records)
- evidence (File references)
- face_evidence (Face data)
- statistics (Daily stats)

**Size**: 
- Typical: 50-100MB per 10,000 violations
- Depends on image storage settings

**Retention**: 30 days (configurable)

---

## Evidence Directory

### Organization
```
evidence/
└── YYYY-MM-DD/           (One per day)
    └── {track_id}-HHmmss/ (One per violation)
        ├── full_frame.jpg
        ├── face_0.jpg
        ├── face_1.jpg (if multiple)
        └── metadata.json
```

### Typical Sizes
- Full frame: 200-500 KB
- Face crop: 20-100 KB
- Metadata: 1-2 KB

**Daily Storage**: 
- 100 violations/day = 50-100 MB
- 1000 violations/day = 500MB - 1GB

---

## Code Statistics

| File | Lines | Classes | Functions |
|------|-------|---------|-----------|
| config.py | 100 | 0 | 0 |
| utils.py | 500+ | 5 | 30+ |
| modules/detector.py | 350+ | 2 | 15+ |
| modules/face_extractor.py | 350+ | 2 | 15+ |
| modules/tracker.py | 400+ | 3 | 20+ |
| modules/camera.py | 350+ | 2 | 25+ |
| modules/database.py | 450+ | 1 | 20+ |
| modules/evidence_manager.py | 350+ | 1 | 15+ |
| modules/__init__.py | 320+ | 1 | 15+ |
| dashboard.py | 500+ | 0 | 15+ |
| dashboard_advanced.py | 400+ | 0 | 10+ |
| main.py | 250+ | 0 | 10+ |
| demo.py | 450+ | 0 | 20+ |
| profiles.py | 100+ | 4 | 3 |

**Total**: 5000+ lines of production code

---

## External Dependencies

**Core AI/ML**:
- ultralytics (YOLOv8)
- torch/torchvision
- opencv-python

**Web Interface**:
- streamlit
- plotly
- pandas

**Utilities**:
- numpy
- scipy
- scikit-image
- Pillow

**System**:
- sqlite3 (built-in)
- threading (built-in)
- logging (built-in)
- pathlib (built-in)

---

## Version History

**v1.0.0 (Current)**
- Complete detection system
- Streamlit dashboard
- SQLite database
- Evidence management
- Multi-object tracking
- Face extraction
- Production ready

---

**Last Updated**: January 2024  
**Total Project Size**: ~50MB (code + models ~2GB including PyTorch)
