# SmartHelmetGuard - Quick Reference Guide

## Dashboard Usage

### Live Monitoring Tab

**Controls:**
- **▶ Start Stream** - Begin capturing video feed
- **⏹ Stop Stream** - Stop the camera
- **Confidence Slider** - Adjust detection sensitivity (0.0-1.0)
  - Lower = more detections (higher false positives)
  - Higher = strict detections (may miss some)

**Displays:**
- **Live Feed** - Real-time video with bounding boxes
  - 🟢 Green box = Helmet detected (Legal)
  - 🔴 Red box = No helmet (Violation)
- **FPS Counter** - Processing speed
- **Violation Cards** - Real-time alerts
- **Active Tracks** - Number of people being tracked

**Evidence:**
- Click "Download Evidence" to save violation footage
- Face crops automatically extracted for no-helmet cases
- Stored in `evidence/YYYY-MM-DD/` folder

---

## Violation History Tab

**Filter Options:**

| Filter | Options |
|--------|---------|
| 📅 Period | Today / This Week / This Month / All Time |
| 🎯 Status | All / No Helmet / Helmet |
| 🔢 Confidence | Minimum confidence threshold (0-100%) |
| 📷 Camera | Select specific camera source |

**Table Columns:**
- **Track ID** - Unique identifier for tracked rider
- **Status** - "no_helmet" or "helmet"
- **Confidence** - Detection confidence %
- **Timestamp** - When violation occurred
- **Camera** - Which camera detected it
- **Actions** - View/Download/Delete

**Usage Tips:**
- Click column header to sort
- Select date range with calendar picker
- Use "Download Report" to export as PDF

---

## Analytics Tab

**Key Metrics:**

| Metric | Meaning |
|--------|---------|
| Total Violations Today | Count of violations in last 24 hours |
| This Week | Violations in last 7 days |
| Unique Riders | Number of different track IDs detected |
| Avg Confidence | Average detection confidence score |

**Charts:**

1. **Violations by Hour** - Bar chart showing distribution across 24 hours
2. **Confidence Distribution** - Histogram of confidence scores
3. **Compliance Rate** - Percentage with helmets vs without
4. **Top Violations** - Most frequent violators by location

**Export:**
- Click "🖨️ Generate Report" to create PDF with:
  - All metrics
  - Charts
  - Top violators
  - Evidence samples
  - Date range specified

---

## Settings Tab

### Camera Settings

**Source Selection:**
```
Webcam     → Default camera (index 0)
Webcam 2   → Second connected camera
Video File → Play video file
RTSP URL   → Network camera stream
```

**Configuration:**

| Setting | Values | Impact |
|---------|--------|--------|
| Resolution | 640x480 / 1280x720 / 1920x1080 | Speed vs quality |
| FPS | 15 / 24 / 30 / 60 | Frame rate |
| Brightness | 0-100 | Video brightness |
| Contrast | 0-100 | Video contrast |

### Detection Settings

```
Detection Confidence    0.0 ────●──── 1.0
                            (0.45 default)
                        ↓
                    Lower = More detections
                    Higher = Stricter
```

### Evidence Storage

| Setting | Default | Description |
|---------|---------|-------------|
| Auto Save | ✓ ON | Automatically save evidence |
| Save Full Frame | ✓ ON | Save complete scene image |
| Save Face Crop | ✓ ON | Save extracted face images |
| Blur Faces | OFF | Privacy protection |
| Retention Days | 30 | Auto-delete policy |

### Database Maintenance

**Cleanup Old Evidence**
- Removes files older than specified days
- Runs database optimization
- Frees disk space

**Export Database**
- Downloads violations.db SQLite file
- Includes all metadata
- Can be opened with DB browser tools

**Backup**
- Manual backup of all evidence
- Compressed ZIP file
- Timestamped automatically

---

## Keyboard Shortcuts (Manual Mode)

```
'q'     → Quit detection
'p'     → Pause/Resume
's'     → Save current frame
'r'     → Reset tracker
'c'     → Toggle confidence display
'f'     → Toggle FPS display
'h'     → Toggle help overlay
```

---

## Evidence Organization

### Folder Structure

```
evidence/
├── 2024-01-15/              (Date folder)
│   ├── 001-143022/           (Track ID - Timestamp)
│   │   ├── full_frame.jpg    (Complete video frame)
│   │   ├── face_0.jpg        (Detected face 1)
│   │   ├── face_1.jpg        (Detected face 2)
│   │   └── metadata.json     (Violation info)
│   │
│   └── 002-154530/
│       ├── full_frame.jpg
│       ├── face_0.jpg
│       └── metadata.json
│
└── 2024-01-16/
```

### Metadata JSON Example

```json
{
  "track_id": 1,
  "timestamp": "2024-01-15T14:30:22.123456",
  "status": "no_helmet",
  "violation_confidence": 0.92,
  "camera_source": "Camera-1",
  "frame_dimensions": {
    "width": 1280,
    "height": 720
  },
  "faces_detected": 2,
  "face_quality": [0.85, 0.92]
}
```

---

## Database Schema Quick Reference

### violations table
- `id` - Primary key
- `track_id` - Rider identifier
- `status` - "helmet" or "no_helmet"
- `confidence` - Detection confidence (0-1)
- `timestamp` - When detected
- `camera_source` - Which camera
- `location_description` - Location name (optional)

### evidence table
- `id` - Primary key
- `violation_id` - Links to violations
- `evidence_type` - "full_frame" or "face_crop"
- `file_path` - Location on disk
- `file_size_mb` - Storage size
- `quality_score` - Image quality 0-100

### face_evidence table
- `id` - Primary key
- `violation_id` - Links to violations
- `face_image_path` - Face image location
- `face_quality` - Quality score 0-100
- `face_size_pixels` - Pixel count

### statistics table
- `date` - Date of statistics
- `total_violations` - Count
- `unique_riders` - Count
- `avg_confidence` - Average %
- `helmet_detections` - Count
- `no_helmet_detections` - Count

---

## Querying Database (Advanced)

### Get recent violations
```sql
SELECT * FROM violations 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Count violations today
```sql
SELECT COUNT(*) as count 
FROM violations 
WHERE DATE(timestamp) = DATE('now') 
AND status = 'no_helmet';
```

### Find violations for specific track
```sql
SELECT * FROM violations 
WHERE track_id = 123 
ORDER BY timestamp DESC;
```

### Get evidence for violation
```sql
SELECT * FROM evidence 
WHERE violation_id = 45;
```

### Statistics by day
```sql
SELECT DATE(timestamp) as date, 
       COUNT(*) as violations,
       AVG(confidence) as avg_conf
FROM violations 
WHERE status = 'no_helmet'
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

---

## Configuration Profiles

### Production Profile
```python
profiles.apply_profile('production')
# High accuracy, full archiving
# Use: yolov8l, confidence 0.5, full evidence
```

### Performance Profile
```python
profiles.apply_profile('performance')
# High speed, minimal overhead
# Use: yolov8n, lower confidence, no face storage
```

### Privacy Profile
```python
profiles.apply_profile('privacy')
# Face data minimized, blur enabled
# Use: face crops disabled, face blur active
```

### Testing Profile
```python
profiles.apply_profile('testing')
# Loose detection, all evidence saved
# Use: confidence 0.35, minimal requirements
```

---

## Troubleshooting Quick Tips

| Problem | Solution |
|---------|----------|
| No camera | Check connection, try index 1-4 |
| Low FPS (<10) | Use yolov8n model, lower resolution |
| High GPU memory | Use yolov8s/n, reduce resolution |
| Models not loading | Run: `python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"` |
| Dashboard won't start | Check port 8501 free, run: `streamlit run dashboard.py --server.port 8502` |
| Database errors | Delete `data/violations.db`, it will rebuild |
| Evidence not saving | Check folder permissions: `evidence/` |

---

## Performance Benchmarks

### CPU Performance
| Model | Resolution | FPS | Latency |
|-------|-----------|-----|---------|
| yolov8n | 640x480 | 20-25 | 40-50ms |
| yolov8s | 1280x720 | 12-15 | 65-80ms |
| yolov8m | 1280x720 | 6-8 | 125-150ms |

### GPU Performance (RTX 3070)
| Model | Resolution | FPS | Latency |
|-------|-----------|-----|---------|
| yolov8n | 1920x1080 | 60+ | 16ms |
| yolov8m | 1920x1080 | 35-40 | 25ms |
| yolov8l | 1920x1080 | 20-25 | 40ms |

---

## API Endpoints (If Enabled)

```bash
# Get latest violations
curl http://localhost:5000/api/violations?limit=50&days=1

# Get violation details
curl http://localhost:5000/api/violations/123

# Get statistics
curl http://localhost:5000/api/statistics?date=2024-01-15

# Download evidence
curl http://localhost:5000/api/evidence/track_123/download -o evidence.zip
```

---

## Support Resources

**Documentation:**
- README.md - Feature overview
- SETUP_GUIDE.md - Installation guide
- This file - Quick reference

**Demos:**
```bash
python demo.py --mode health       # System check
python demo.py --mode demo         # Live detection
python demo.py --mode database     # DB operations
python demo.py --mode evidence     # Evidence management
```

**Logs:**
- `logs/system.log` - Error tracking
- Check for errors: `tail -f logs/system.log`

**Reset to Default:**
```bash
# Delete all database
rm data/violations.db

# Delete all evidence
rm -rf evidence/*

# Recreate fresh on next run
```

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Status**: Production Ready ✅
