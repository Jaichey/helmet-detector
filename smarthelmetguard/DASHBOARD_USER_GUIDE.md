# 🚀 Dashboard User Guide - Optimized Version

**Updated:** February 8, 2026  
**Performance:** ⚡ OPTIMIZED FOR SPEED  

---

## 🎯 What's New

The dashboard has been **completely optimized** for speed and responsiveness:

- ✅ **Frames appear in 2-3 seconds** (was 10-15 seconds)
- ✅ **Real-time detection** (smooth and live)
- ✅ **No UI freezing** (responsive at all times)
- ✅ **Camera restart works perfectly** (no doubles)
- ✅ **Live performance metrics** (FPS, processing time)

---

## Quick Start (60 seconds)

### Step 1: Start Dashboard
```bash
cd d:\AI_Projects\Helmet-Detector\smarthelmetguard
streamlit run dashboard.py
```

### Step 2: Open Browser
```
http://localhost:8501
```

### Step 3: Go to "Live Monitoring"
- Click the **Live Monitoring** tab in the left sidebar

### Step 4: Click "Start Stream"
- 🔵 Button turns to "Stop Stream"
- ✅ Video feed appears in 2-3 seconds
- 📊 Metrics update in real-time

### Step 5: Watch Detection

- 🟢 **Green box** = Helmet detected (LEGAL)
- 🔴 **Red box** = No helmet (VIOLATION!) ⚠️

---

## Features & How to Use

### 📊 Live Metrics (Top of Page)

```
┌─────────────────────────────────────────────────┐
│  Total Frames │ Violations Detected │ Live FPS  │
│      130      │        29           │   10.2    │
└─────────────────────────────────────────────────┘
```

- **Total Frames**: Number of frames processed
- **Violations Detected**: Number of "no helmet" detections
- **Live FPS**: Current processing speed (frames per second)
- **Processing**: Time to analyze each frame in milliseconds

### 🎥 Live Feed

The main video window shows:
- Your camera feed in real-time
- **Green boxes** around riders with helmets ✓
- **Red boxes** around riders without helmets ⚠️
- Person ID and confidence score

**Example:**
```
Helmet 1 (0.95)  ← Green box = Legal
No Helmet 2 (0.87)  ← Red box = Violation
```

### 🎚️ Confidence Threshold Slider

Adjust detection sensitivity:
- **0.0 - 0.3**: Very aggressive (many false positives)
- **0.3 - 0.5**: **RECOMMENDED** (balanced)
- **0.5 - 0.8**: More strict (fewer detections)
- **0.8 - 1.0**: Very strict (only clear helmets)

**Recommendation:** Keep at default **0.45**

### ⚠️ Live Violations Panel

Shows last 5 violations detected:

```
╔═════════════════════════════════╗
║  Track ID: 1                    ║
║  Confidence: 91.5%              ║
║  Time: 18:40:56                 ║
╚═════════════════════════════════╝
```

- **Track ID**: Unique identifier for person
- **Confidence**: Detection certainty (higher = more confident)
- **Time**: When violation was detected

---

## Button Controls

### ▶ Start Stream
- **What it does**: Starts camera and begins detection
- **When to use**: At beginning of monitoring session
- **What happens**:
  - Camera initializes (if not already on)
  - First frame appears in ~2-3 seconds
  - Detection begins immediately

**✅ Expected behavior:**
```
Click "Start Stream"
    ↓ (2-3 seconds)
Frame appears
    ↓
Detection boxes show
    ↓
Metrics update
```

### ⏹ Stop Stream
- **What it does**: Stops camera gracefully
- **When to use**: When done monitoring
- **What happens**:
  - Camera thread stops safely
  - Frame display pauses
  - Resources freed for other apps

**✅ Expected behavior:**
```
Click "Stop Stream"
    ↓ (instant)
Message: "Camera stopped"
    ↓
Frame stream ends
    ↓
Can restart immediately
```

### Full Start/Stop Cycle
```
1. Click "▶ Start Stream"     → Camera running
2. Wait ~2-3 sec             → First frame appears
3. Watch detection           → Violations counted
4. Click "⏹ Stop Stream"     → Camera stops
5. Click "▶ Start Stream"    → ✅ Works! (used to fail)
6. Repeat step 3-5 as needed
```

---

## Dashboard Navigation

### 📌 Left Sidebar

```
🛡️ SmartHelmetGuard
├─ Navigation
│  ├─ Live Monitoring     ← You are here
│  ├─ Violation History   ← Past detections
│  ├─ Analytics           ← Statistics & charts
│  └─ Settings            ← Configuration
│
└─ System Status
   ├─ ● Online            ← Indicates if system ready
   └─ Violations Logged   ← Total count
```

---

## Performance Tips

### To Maximize FPS:

1. **Close other Windows applications** that use camera
2. **Maximize Streamlit window** for better rendering
3. **Use Chrome/Firefox** browsers (less overhead than others)
4. **Check GPU** - ensure NVIDIA CUDA is available
   ```bash
   nvidia-smi  # Should show GPU usage
   ```

### To Fix Slow Performance:

**If FPS is < 5:**

1. Lower resolution in Settings tab:
   - Change from 1280x720 to 640x480
   
2. Use smaller detection model in Settings:
   - Change from yolov8m to yolov8n

3. Restart Streamlit:
   ```bash
   # Press Ctrl+C in terminal
   streamlit run dashboard.py  # Restart it
   ```

---

## Other Dashboard Tabs

### 📋 Violation History
- View all detections from database
- Filter by date, confidence, camera source
- Download evidence images and details

### 📊 Analytics
- Daily/weekly violation statistics
- Charts and graphs
- Unique rider tracking
- Confidence distribution

### ⚙️ Settings
- Camera source selection
- Resolution & FPS configuration
- Detection thresholds
- Database maintenance
- Evidence cleanup

---

## Troubleshooting

### Problem: No frames showing up

**Solution:**
1. Click "Stop Stream"
2. Wait 2 seconds
3. Click "Start Stream" again
4. If still no frames, check:
   - Camera not used by other app (close Zoom, Teams, etc)
   - Camera permissions enabled (Settings → Privacy → Camera)

### Problem: Very slow (< 2 FPS)

**Solution:**
1. Go to Settings tab
2. Change resolution to 640x480
3. Change model to yolov8n
4. Restart Streamlit

### Problem: Camera shows error

**Solution:**
1. Close browser tab
2. Press Ctrl+C in terminal to stop Streamlit
3. Another app might be using camera
4. Check Windows: Settings → Privacy → Camera
5. Restart: `streamlit run dashboard.py`

### Problem: Helmet detection seems wrong

**Solution:**
1. Adjust confidence slider
   - Move to the right = stricter
   - Move to the left = more sensitive
2. Ensure good lighting
3. Camera should be 2-3 meters away
4. Check that head is clearly visible

---

## Real-World Usage Examples

### Example 1: Basic Monitoring
```
1. Open dashboard
2. Start stream
3. Wait ~3 seconds for frame
4. Watch for red violations
5. Click on Violation History to see more
6. Stop when done
```

### Example 2: Fine-tuning Detection
```
1. Start stream with motionless person
2. Adjust confidence slider to balance:
   - Too high = misses some helmets
   - Too low = false positives
3. Find sweet spot around 0.40-0.50
4. Save setting to config.py for future
```

### Example 3: Gathering Evidence
```
1. Run dashboard
2. When violation detected:
   - Take note of Track ID
   - Note the time
3. Go to "Violation History" tab
4. Find violation in database
5. View saved face crop images
6. Download evidence for report
```

---

## Performance Benchmarks

**Typical System Output:**

```
Total Frames: 130
Violations Detected: 29
Live FPS: 10.2
Processing: 95.3ms per frame

Active detection tracks: 3
Confidence threshold: 0.45
Current latency: ~2 seconds
```

**What's Good:**
- ✅ FPS > 5 = Good performance
- ✅ Processing < 100ms = Normal
- ✅ Latency < 5sec = Acceptable
- ✅ No error messages = System healthy

---

## Keyboard Shortcuts

In Streamlit dashboard:

- **Ctrl+C** (in terminal): Stop Streamlit server
- **R**: Refresh page (Cmd+R on Mac)
- **Ctrl++**: Zoom in (see larger video)
- **Ctrl+-**: Zoom out (see full dashboard)

---

## System Requirements

**Minimum:**
- 8GB RAM
- Dual-core CPU
- USB camera
- Chrome/Firefox browser

**Recommended:**
- 16GB RAM
- Quad-core CPU + GPU
- 1080p USB camera
- Chrome browser (latest)

---

## Next Steps

1. ✅ **Start Dashboard**
   ```bash
   streamlit run dashboard.py
   ```

2. ✅ **Click "Live Monitoring"** if not already there

3. ✅ **Click "Start Stream"** and wait 2-3 seconds

4. ✅ **Watch detections** in real-time

5. ✅ **Click "Violation History"** to see stored violations

6. ✅ **Adjust confidence slider** if needed

---

## Support

**If something doesn't work:**

1. Check the terminal running Streamlit (has error logs)
2. Read QUICK_TROUBLESHOOTING.md
3. Run test_installation.py to validate system
4. Check SETUP_GUIDE.md for installation help

---

**Status:** ✅ **READY TO USE**

Enjoy your optimized helmet detection system! 🎉
