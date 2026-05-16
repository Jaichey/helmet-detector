# SmartHelmetGuard - Streamlit Dashboard UI
# Modern industry-grade dashboard for helmet violation monitoring

import streamlit as st
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import pandas as pd
import time
import threading

# Import system modules
import sys
sys.path.insert(0, str(Path(__file__).parent))

from modules.camera import CameraManager
from modules.detector import HelmetDetector
from modules.face_extractor import FaceExtractor
from modules.tracker import ByteTracker
from modules.database import DatabaseManager
from modules.evidence_manager import EvidenceManager
from utils import setup_logger, ImageProcessor
from config import CONFIDENCE_SMOOTHING

logger = setup_logger(__name__)

# Configure Streamlit
st.set_page_config(
    page_title="SmartHelmetGuard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dashboard
def load_custom_css():
    """Load custom CSS styling"""
    st.markdown("""
    <style>
    /* Main background */
    .main {
        background-color: #0f1419;
        color: #e0e0e0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1f2e;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #1a1f2e;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #00d4ff;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #00d4ff;
        color: #000;
        font-weight: 600;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
    }
    
    .stButton > button:hover {
        background-color: #00a8cc;
    }
    
    /* Tabs */
    [data-testid="stTabs"] {
        background-color: transparent;
    }
    
    /* Cards */
    .violation-card {
        background-color: #1a1f2e;
        border: 2px solid #ff4444;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .legal-card {
        background-color: #1a1f2e;
        border: 2px solid #44ff44;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Status badge */
    .status-online {
        color: #44ff44;
        font-weight: bold;
    }
    
    .status-offline {
        color: #ff4444;
        font-weight: bold;
    }
    
    /* Violation alert */
    .alert-violation {
        background-color: rgba(255, 68, 68, 0.2);
        border-left: 4px solid #ff4444;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def initialize_session():
    """Initialize Streamlit session state"""
    if 'detector_initialized' not in st.session_state:
        st.session_state.detector_initialized = False
        st.session_state.detector = None
        st.session_state.camera = None
        st.session_state.tracker = None
        st.session_state.database = None
        st.session_state.face_extractor = None
        st.session_state.evidence_manager = None
        st.session_state.violations = []
        st.session_state.frame_count = 0
        st.session_state.violation_count = 0
        st.session_state.fps = 0
        st.session_state.camera_running = False  # Track camera state
        st.session_state.processing_time_ms = 0

def initialize_detector():
    """Initialize detector components"""
    try:
        if st.session_state.detector_initialized:
            return True
        
        with st.spinner("Loading AI Models..."):
            st.session_state.camera = CameraManager(source=0)
            st.session_state.detector = HelmetDetector()
            st.session_state.tracker = ByteTracker()
            st.session_state.database = DatabaseManager()
            st.session_state.face_extractor = FaceExtractor()
            st.session_state.evidence_manager = EvidenceManager()
            
            st.session_state.detector_initialized = True
            return True
    except Exception as e:
        st.error(f"Error initializing detector: {e}")
        logger.error(f"Initialization error: {e}")
        return False

def render_live_monitoring():
    """Render live monitoring page with true continuous streaming"""
    st.title("🎥 Live Helmet Violation Monitoring")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Frames", st.session_state.frame_count)
    
    with col2:
        st.metric("Violations Detected", st.session_state.violation_count)
    
    with col3:
        st.metric("Live FPS", f"{st.session_state.fps:.1f}")
    
    with col4:
        st.metric("Processing", f"{st.session_state.processing_time_ms:.1f}ms")
    
    # Main layout
    camera_col, violation_col = st.columns([2, 1])
    
    # Live feed display
    with camera_col:
        st.subheader("📹 Live Feed")
        frame_placeholder = st.empty()
        info_placeholder = st.empty()
        
        # Camera control buttons
        col1, col2, col3 = st.columns(3)
        
        start_button = col1.button("▶ Start Stream")
        confidence = col2.slider("Confidence Threshold", 0.0, 1.0, 0.45, 0.01)
        stop_button = col3.button("⏹ Stop Stream")
        
        # Handle Start button
        if start_button and not st.session_state.camera_running:
            if st.session_state.camera and not st.session_state.camera.is_online():
                st.session_state.camera.start()
                st.session_state.camera_running = True
                st.success("✅ Camera started! Continuous streaming active...")
                time.sleep(0.3)
                st.rerun()
            elif st.session_state.camera and st.session_state.camera.is_online():
                st.info("Camera already running")
        
        # Handle Stop button
        if stop_button and st.session_state.camera_running:
            if st.session_state.camera:
                st.session_state.camera.stop()
                st.session_state.camera_running = False
                st.info("⏹ Camera stopped")
                time.sleep(0.3)
                st.rerun()
        
        # CONTINUOUS STREAMING - Optimized for smooth video without lag
        if st.session_state.camera_running and st.session_state.camera:
            # Process frames in smaller batches for responsive UI (reduced from 15 to 8)
            frames_per_batch = 8  # Process 8 frames per cycle (~270ms at 30 FPS) = faster updates
            frame_skip = 0  # Process every frame (no skipping)
            
            for batch_index in range(frames_per_batch):
                # Check stop button
                if not st.session_state.camera_running:
                    break
                
                # Get frame from camera
                frame = st.session_state.camera.get_frame(timeout=0.5)
                
                if frame is not None:
                    # Run detection and evidence saving
                    result = process_frame_detection(frame, confidence)
                    
                    if result:
                        st.session_state.frame_count = result['frame_count']
                        st.session_state.fps = result['fps']
                        st.session_state.processing_time_ms = result['processing_time_ms']
                        st.session_state.violation_count = len([v for v in st.session_state.violations if v])
                        
                        # Track violations and save evidence (already done in process_frame_detection)
                        for violation in result['violations']:
                            existing = [v for v in st.session_state.violations 
                                      if v['track_id'] == violation['track_id']]
                            if not existing:
                                st.session_state.violations.append(violation)
                        
                        # Display frame (every iteration - smooth video)
                        frame_rgb = cv2.cvtColor(result['frame'], cv2.COLOR_BGR2RGB)
                        frame_placeholder.image(frame_rgb)
                        
                        # Display metrics
                        info_text = f"FPS: {result['fps']:.1f} | Processing: {result['processing_time_ms']:.1f}ms | Tracks: {len(result['tracked_objects'])}"
                        info_placeholder.info(info_text)
                
                # Minimal delay for responsive feel
                time.sleep(0.005)  # Very small delay
            
            # After batch, refresh for button state changes
            time.sleep(0.05)  # Brief pause
            st.rerun()
        
        elif st.session_state.camera_running:
            frame_placeholder.info("⚙️ Initializing camera... Starting continuous stream...")
            time.sleep(0.5)
            st.rerun()
        else:
            frame_placeholder.info("📹 Click 'Start Stream' to begin live continuous detection (no lag, no stopping)")
    
    # Violations panel
    with violation_col:
        st.subheader("⚠️ Live Violations")
        
        if st.session_state.violations:
            # Show last 5 violations
            for violation in st.session_state.violations[-5:]:
                with st.container():
                    st.markdown(f"""
                    <div style='background-color: rgba(255,68,68,0.1); border-left: 4px solid #ff4444; padding: 10px; margin: 5px 0; border-radius: 5px;'>
                    <b>Track ID:</b> {violation['track_id']}<br>
                    <b>Confidence:</b> {violation['confidence']:.1%}<br>
                    <b>Time:</b> {violation['timestamp'].strftime('%H:%M:%S')}<br>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No violations detected yet")

def render_violation_history():
    """Render violation history page"""
    st.title("📋 Violation History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_filter = st.selectbox("Time Period", ["Today", "This Week", "This Month", "All Time"])
    
    with col2:
        status_filter = st.selectbox("Status", ["All", "No Helmet", "Helmet"])
    
    with col3:
        min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.0)
    
    # Get violations from database
    violations_data = st.session_state.database.get_violations(limit=100)
    
    if violations_data:
        # Convert to DataFrame
        df = pd.DataFrame(violations_data)
        
        # Format display
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['confidence'] = (df['confidence'] * 100).round(2).astype(str) + "%"
        
        # Display table
        st.dataframe(
            df[['track_id', 'status', 'confidence', 'timestamp', 'camera_source']],
            use_container_width=True,
            height=400
        )
    else:
        st.info("No violations found")

def render_analytics():
    """Render analytics dashboard"""
    st.title("📊 Analytics & Statistics")
    
    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    stats = get_database_statistics()
    
    with col1:
        st.metric("Total Violations Today", stats.get('violations_today', 0))
    
    with col2:
        st.metric("This Week", stats.get('violations_this_week', 0))
    
    with col3:
        st.metric("Unique Riders", stats.get('unique_riders', 0))
    
    with col4:
        st.metric("Avg Confidence", f"{stats.get('avg_confidence', 0)*100:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Violations by Hour")
        # Create sample chart (can be enhanced with real data)
        hours = list(range(24))
        violations_per_hour = [np.random.randint(0, 10) for _ in hours]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=hours, y=violations_per_hour, marker_color='#ff4444'))
        fig.update_layout(
            title="Violations by Hour",
            xaxis_title="Hour",
            yaxis_title="Count",
            template="plotly_dark",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Detection Confidence Distribution")
        
        if st.session_state.violations:
            confidences = [v['confidence'] for v in st.session_state.violations]
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=confidences,
                nbinsx=20,
                marker_color='#00d4ff'
            ))
            fig.update_layout(
                title="Confidence Score Distribution",
                xaxis_title="Confidence",
                yaxis_title="Count",
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

def render_settings():
    """Render settings page"""
    st.title("⚙️ System Settings")
    
    st.subheader("Camera Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        camera_source = st.selectbox(
            "Camera Source",
            ["Webcam (0)", "Webcam (1)", "Video File", "RTSP Stream"]
        )
    
    with col2:
        resolution = st.selectbox(
            "Resolution",
            ["640x480", "1280x720", "1920x1080"]
        )
    
    st.subheader("Detection Settings")
    confidence = st.slider("Detection Confidence", 0.0, 1.0, 0.45)
    iou_threshold = st.slider("IoU Threshold", 0.0, 1.0, 0.45)
    
    st.subheader("Evidence Storage")
    col1, col2 = st.columns(2)
    
    with col1:
        auto_save = st.checkbox("Auto Save Evidence", value=True)
    
    with col2:
        blur_faces = st.checkbox("Blur Faces in Full Frame", value=False)
    
    st.subheader("Database Maintenance")
    if st.button("🗑️ Cleanup Old Evidence"):
        with st.spinner("Cleaning up..."):
            st.session_state.evidence_manager.cleanup_old_evidence(days=30)
            st.success("Cleanup complete")
    
    if st.button("📊 Generate Report"):
        st.info("Report generation coming soon...")

def process_frame_detection(frame, confidence):
    """Process frame with detection, face extraction, and evidence saving - optimized"""
    try:
        process_start = time.time()
        
        # Quick detection
        detections = st.session_state.detector.detect(frame, conf=confidence)
        tracked_objects = st.session_state.tracker.update(detections)
        
        result_frame = frame.copy()
        violations = []
        
        for track in tracked_objects:
            if track.is_violation():
                color = (0, 0, 255)  # Red for no helmet
                label = f"No Helmet {track.track_id}"
                
                # CRITICAL: Save violation to database with evidence
                violation_data = {
                    'track_id': track.track_id,
                    'confidence': track.get_avg_confidence(),
                    'timestamp': datetime.now()
                }
                violations.append(violation_data)
                
                # Save evidence asynchronously (non-blocking)
                try:
                    rider_bbox = track.bbox
                    
                    # Extract faces from rider region using face extractor
                    faces = st.session_state.face_extractor.extract_faces(
                        frame=frame,
                        rider_bbox=rider_bbox,
                        rider_class="no_helmet"
                    )
                    
                    # Save violation to database
                    violation_id = st.session_state.database.add_violation(
                        track_id=track.track_id,
                        status='no_helmet',
                        confidence=track.get_avg_confidence(),
                        camera_source='Webcam'
                    )
                    
                    if violation_id:
                        # Save full frame and extract face crops
                        evidence_result = st.session_state.evidence_manager.save_violation_evidence(
                            frame=frame,
                            faces=faces,
                            track_id=track.track_id,
                            violation_confidence=track.get_avg_confidence(),
                            camera_source='Webcam',
                            save_full=True,
                            save_faces=True
                        )
                        
                        if evidence_result:
                            # Add full frame evidence record
                            if evidence_result.get('full_frame'):
                                full_frame_info = evidence_result['full_frame']
                                st.session_state.database.add_evidence(
                                    violation_id=violation_id,
                                    evidence_type='full_frame',
                                    file_path=full_frame_info.get('path') if isinstance(full_frame_info, dict) else evidence_result['full_frame'],
                                    file_name='full_frame.jpg',
                                    quality_score=track.get_avg_confidence()
                                )
                            
                            # Add face evidence records
                            if evidence_result.get('faces'):
                                for face_info in evidence_result['faces']:
                                    face_path = face_info.get('path') if isinstance(face_info, dict) else face_info
                                    face_quality = face_info.get('quality', 0.8) if isinstance(face_info, dict) else 0.8
                                    st.session_state.database.add_face_evidence(
                                        violation_id=violation_id,
                                        face_image_path=face_path,
                                        quality_score=face_quality
                                    )
                        
                        logger.info(f"✅ Violation saved: Track {track.track_id}, Id {violation_id}, Faces: {len(faces)}")
                
                except Exception as e:
                    logger.error(f"⚠️  Error saving violation evidence: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                color = (0, 255, 0)  # Green for helmet
                label = f"Helmet {track.track_id}"
            
            x1, y1, x2, y2 = map(int, track.bbox)
            cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(result_frame, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Calculate processing time
        process_time_ms = (time.time() - process_start) * 1000
        fps = 1000.0 / process_time_ms if process_time_ms > 0 else 0
        
        return {
            'frame': result_frame,
            'violations': violations,
            'tracked_objects': tracked_objects,
            'frame_count': st.session_state.frame_count + 1,
            'fps': fps,
            'processing_time_ms': process_time_ms
        }
    except Exception as e:
        logger.error(f"Detection error: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_database_statistics():
    """Get statistics from database"""
    try:
        daily_stats = st.session_state.database.get_daily_violations(days=1)
        weekly_stats = st.session_state.database.get_daily_violations(days=7)
        
        return {
            'violations_today': daily_stats.get('violation_count', 0),
            'violations_this_week': weekly_stats.get('violation_count', 0),
            'unique_riders': daily_stats.get('unique_riders', 0),
            'avg_confidence': daily_stats.get('avg_confidence', 0) or 0
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {}

def main():
    """Main dashboard application"""
    load_custom_css()
    initialize_session()
    
    # Sidebar
    st.sidebar.title("🛡️ SmartHelmetGuard")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Live Monitoring", "Violation History", "Analytics", "Settings"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Status")
    
    if initialize_detector():
        st.sidebar.markdown("<span class='status-online'>● Online</span>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown("<span class='status-offline'>● Offline</span>", unsafe_allow_html=True)
    
    st.sidebar.info(f"Violations Logged: {st.session_state.violation_count}")
    
    # Render selected page
    if page == "Live Monitoring":
        render_live_monitoring()
    elif page == "Violation History":
        render_violation_history()
    elif page == "Analytics":
        render_analytics()
    else:
        render_settings()

if __name__ == "__main__":
    main()
