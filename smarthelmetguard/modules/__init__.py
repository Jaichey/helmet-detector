# SmartHelmetGuard - Main Application Module
# Orchestrates all components for helmet violation detection

import cv2
import numpy as np
from datetime import datetime, timedelta
import time
from pathlib import Path

from modules.camera import CameraManager
from modules.detector import HelmetDetector, DetectionAggregator
from modules.face_extractor import FaceExtractor, FaceManager
from modules.tracker import ByteTracker
from modules.database import DatabaseManager
from modules.evidence_manager import EvidenceManager

from utils import setup_logger, ImageProcessor, TimeUtils, BBoxUtils
from config import (
    COLOR_HELMET, COLOR_NO_HELMET, COLOR_TRACKING,
    ENABLE_TRACKING, ENABLE_DUPLICATE_PREVENTION, TRACKING_COOLDOWN
)

logger = setup_logger(__name__)

class HelmetViolationDetector:
    """
    Main helmet violation detection system
    
    Orchestrates:
    - Camera input
    - Helmet detection
    - Face extraction
    - Multi-object tracking
    - Evidence storage
    - Database logging
    """
    
    def __init__(self, camera_source=0, confidence_threshold=0.45):
        """
        Initialize violation detector
        
        Args:
            camera_source: Camera source (int, file path, or RTSP URL)
            confidence_threshold: Detection confidence threshold
        """
        logger.info("Initializing HelmetViolationDetector...")
        
        self.camera_source = camera_source
        self.confidence_threshold = confidence_threshold
        
        # Initialize components
        self.camera = None
        self.detector = None
        self.face_extractor = None
        self.tracker = None
        self.database = None
        self.evidence_manager = None
        self.detection_aggregator = None
        self.face_manager = None
        
        # Statistics
        self.frame_count = 0
        self.violation_count = 0
        self.fps = 0
        self.last_frame_time = None
        self.processing_times = []
        
        # Violation tracking
        self.logged_violations = set()
        self.violation_cooldown = {}
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            # Camera
            logger.info(f"Initializing camera: {self.camera_source}")
            self.camera = CameraManager(self.camera_source)
            if not self.camera.capture or not self.camera.capture.isOpened():
                raise Exception("Failed to initialize camera")
            
            # Detector
            logger.info("Initializing helmet detector...")
            self.detector = HelmetDetector()
            self.detector.warmup()
            
            # Face Extractor
            logger.info("Initializing face extractor...")
            self.face_extractor = FaceExtractor()
            
            # Tracker
            logger.info("Initializing tracker...")
            self.tracker = ByteTracker()
            
            # Database
            logger.info("Initializing database...")
            self.database = DatabaseManager()
            
            # Evidence Manager
            logger.info("Initializing evidence manager...")
            self.evidence_manager = EvidenceManager()
            
            # Aggregators
            self.detection_aggregator = DetectionAggregator()
            self.face_manager = FaceManager()
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise
    
    def start(self):
        """Start detection system"""
        try:
            logger.info("Starting detection system...")
            self.camera.start()
            logger.info("Detection system started")
            return True
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            return False
    
    def stop(self):
        """Stop detection system"""
        try:
            logger.info("Stopping detection system...")
            if self.camera:
                self.camera.stop()
            logger.info("Detection system stopped")
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    def process_frame(self, frame, conf_threshold=None):
        """
        Process single frame for violations
        
        Args:
            frame: Input frame (BGR image)
            conf_threshold: Override confidence threshold
            
        Returns:
            dict: Processing results with detections and violations
        """
        try:
            process_start = time.time()
            conf_threshold = conf_threshold or self.confidence_threshold
            
            self.frame_count += 1
            
            # Detect helmets
            detections = self.detector.detect(frame, conf=conf_threshold)
            
            # Filter detections (remove very small ones)
            detections = self.detector.filter_detections(detections, min_area=400)
            
            # Update tracker
            tracked_objects = self.tracker.update(detections)
            
            # Process violations
            violations = []
            result_frame = frame.copy()
            
            for track in tracked_objects:
                # Draw tracking box
                x1, y1, x2, y2 = map(int, track.bbox)
                
                if track.is_violation():
                    color = COLOR_NO_HELMET
                    label = f"No Helmet ID:{track.track_id} ({track.get_avg_confidence():.2f})"
                    
                    # Extract face for violation
                    faces = self.face_extractor.extract_faces(
                        frame, 
                        track.bbox,
                        rider_class=track.detection_class
                    )
                    
                    # Create violation record
                    violation_data = {
                        'track_id': track.track_id,
                        'status': 'no_helmet',
                        'confidence': track.get_avg_confidence(),
                        'timestamp': TimeUtils.get_timestamp(),
                        'bbox': track.bbox,
                        'faces': faces,
                        'frame': result_frame.copy()
                    }
                    
                    violations.append(violation_data)
                    
                    # Save evidence if violation logging is allowed
                    if ENABLE_DUPLICATE_PREVENTION:
                        if track.can_log_violation():
                            self._save_violation_evidence(violation_data)
                            track.log_violation()
                    else:
                        self._save_violation_evidence(violation_data)
                    
                else:
                    color = COLOR_HELMET
                    label = f"Helmet ID:{track.track_id} ({track.get_avg_confidence():.2f})"
                
                result_frame = ImageProcessor.draw_bbox(result_frame, track.bbox, label, color)
            
            # Calculate FPS
            current_time = time.time()
            if self.last_frame_time:
                self.fps = 1.0 / (current_time - self.last_frame_time)
            self.last_frame_time = current_time
            
            # Track processing time
            process_time = (time.time() - process_start) * 1000  # ms
            self.processing_times.append(process_time)
            if len(self.processing_times) > 30:
                self.processing_times.pop(0)
            
            return {
                'frame': result_frame,
                'detections': detections,
                'violations': violations,
                'tracked_objects': tracked_objects,
                'frame_count': self.frame_count,
                'fps': self.fps,
                'processing_time_ms': process_time,
                'avg_processing_time_ms': np.mean(self.processing_times) if self.processing_times else 0
            }
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None
    
    def _save_violation_evidence(self, violation_data):
        """Save violation evidence to disk and database"""
        try:
            track_id = violation_data['track_id']
            confidence = violation_data['confidence']
            frame = violation_data['frame']
            faces = violation_data['faces']
            
            # Save evidence files
            evidence = self.evidence_manager.save_violation_evidence(
                frame=frame,
                faces=faces,
                track_id=track_id,
                violation_confidence=confidence,
                camera_source="Camera-1"
            )
            
            if evidence:
                # Add to database
                violation_id = self.database.add_violation(
                    track_id=track_id,
                    status='no_helmet',
                    confidence=confidence,
                    camera_source="Camera-1"
                )
                
                if violation_id:
                    # Add evidence records
                    if evidence['full_frame']:
                        self.database.add_evidence(
                            violation_id=violation_id,
                            evidence_type='full_frame',
                            file_path=evidence['full_frame']['path'],
                            file_name='full_frame.jpg',
                            file_size_mb=evidence['full_frame']['size_mb']
                        )
                    
                    # Add face evidence
                    for face_data in evidence['faces']:
                        self.database.add_face_evidence(
                            violation_id=violation_id,
                            face_image_path=face_data['path'],
                            quality_score=face_data['quality'],
                            face_size=int(BBoxUtils.get_bbox_area(face_data['bbox']))
                        )
                
                self.violation_count += 1
                logger.info(f"Violation #{self.violation_count} saved: Track {track_id}")
                
                return violation_id
            
        except Exception as e:
            logger.error(f"Error saving violation evidence: {e}")
            return None
    
    def get_statistics(self):
        """Get system statistics"""
        return {
            'frame_count': self.frame_count,
            'violation_count': self.violation_count,
            'fps': round(self.fps, 2),
            'avg_processing_time_ms': round(np.mean(self.processing_times), 2) if self.processing_times else 0,
            'active_tracks': len(self.tracker.get_confirmed_tracks()),
            'total_violations_db': self.database.get_total_violations(),
            'camera_info': self.camera.get_info() if self.camera else {},
            'evidence_stats': self.evidence_manager.get_evidence_stats()
        }
    
    def get_current_violations(self):
        """Get current active violations"""
        violations = []
        
        for track in self.tracker.get_violated_tracks():
            violations.append({
                'track_id': track.track_id,
                'confidence': track.get_avg_confidence(),
                'age': track.age,
                'hits': track.hits,
                'bbox': track.bbox
            })
        
        return violations

logger.info("HelmetViolationDetector module initialized")
