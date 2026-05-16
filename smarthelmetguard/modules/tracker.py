# SmartHelmetGuard - Tracking Module
# Handles multi-object tracking using ByteTrack algorithm

import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta
from utils import setup_logger, BBoxUtils
from config import (
    TRACK_MAX_AGE, TRACK_MIN_HITS, TRACK_IOU_THRESHOLD,
    TRACKING_COOLDOWN, ENABLE_DUPLICATE_PREVENTION
)

logger = setup_logger(__name__)

class Track:
    """Represents a single tracked object"""
    
    next_id = 1
    
    def __init__(self, bbox, detection_data):
        """
        Initialize track
        
        Args:
            bbox: Initial bounding box [x1, y1, x2, y2]
            detection_data: Detection information (class, confidence, etc)
        """
        self.track_id = Track.next_id
        Track.next_id += 1
        
        self.bbox = bbox
        self.detection_data = detection_data
        
        self.hits = 1
        self.age = 0
        self.frames_since_update = 0
        
        self.detection_class = detection_data.get('class', 'unknown')
        self.confidence_scores = [detection_data.get('confidence', 0.5)]
        
        self.creation_time = datetime.now()
        self.last_update_time = datetime.now()
        
        self.violation_logged = False
        self.violation_log_time = None
    
    def update(self, bbox, detection_data):
        """Update track with new detection"""
        self.bbox = bbox
        self.detection_data = detection_data
        
        self.hits += 1
        self.frames_since_update = 0
        self.age += 1
        
        self.detection_class = detection_data.get('class', 'unknown')
        self.confidence_scores.append(detection_data.get('confidence', 0.5))
        
        # Keep only last 10 confidence scores
        if len(self.confidence_scores) > 10:
            self.confidence_scores.pop(0)
        
        self.last_update_time = datetime.now()
    
    def increment_age(self):
        """Increment age and frames without update"""
        self.age += 1
        self.frames_since_update += 1
    
    def get_state(self):
        """Get track state (confirmed, tentative, deleted)"""
        if self.hits >= TRACK_MIN_HITS:
            return "confirmed"
        elif self.frames_since_update < TRACK_MAX_AGE:
            return "tentative"
        else:
            return "deleted"
    
    def get_avg_confidence(self):
        """Get average confidence score"""
        if len(self.confidence_scores) == 0:
            return 0.0
        return np.mean(self.confidence_scores)
    
    def is_violation(self):
        """Check if this track represents a violation"""
        return self.detection_class == "no_helmet"
    
    def can_log_violation(self):
        """Check if violation can be logged (cooldown check)"""
        if not self.is_violation():
            return False
        
        if not self.violation_logged:
            return True
        
        # Check cooldown
        time_since_log = datetime.now() - self.violation_log_time
        return time_since_log > timedelta(seconds=TRACKING_COOLDOWN)
    
    def log_violation(self):
        """Mark violation as logged"""
        self.violation_logged = True
        self.violation_log_time = datetime.now()

class ByteTracker:
    """
    Multi-object tracker using ByteTrack algorithm
    
    Tracks riders across frames and associates detections
    """
    
    def __init__(self, max_age=TRACK_MAX_AGE, min_hits=TRACK_MIN_HITS, iou_threshold=TRACK_IOU_THRESHOLD):
        """
        Initialize tracker
        
        Args:
            max_age: Max frames to keep track without detection
            min_hits: Min detections to confirm track
            iou_threshold: IoU threshold for association
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        
        self.tracks = []
        self.frame_count = 0
    
    def update(self, detections):
        """
        Update tracker with new detections
        
        Args:
            detections: List of detections [
                {
                    'bbox': [x1, y1, x2, y2],
                    'class': str,
                    'confidence': float,
                    ...
                }, ...
            ]
            
        Returns:
            list: Active tracks with state 'confirmed'
        """
        self.frame_count += 1
        
        # First pass: match detections to existing tracks
        unmatched_detections = list(range(len(detections)))
        matched_tracks = set()
        
        # Try to match with confirmed tracks (high IoU threshold)
        for track in [t for t in self.tracks if t.get_state() == "confirmed"]:
            best_detection_idx = -1
            best_iou = self.iou_threshold
            
            for det_idx in unmatched_detections:
                iou = self._calculate_iou(track.bbox, detections[det_idx]['bbox'])
                
                if iou > best_iou:
                    best_iou = iou
                    best_detection_idx = det_idx
            
            if best_detection_idx >= 0:
                track.update(detections[best_detection_idx]['bbox'], detections[best_detection_idx])
                unmatched_detections.remove(best_detection_idx)
                matched_tracks.add(id(track))
        
        # Second pass: match with tentative tracks (lower IoU threshold)
        for track in [t for t in self.tracks if t.get_state() == "tentative"]:
            if id(track) in matched_tracks:
                continue
            
            best_detection_idx = -1
            best_iou = self.iou_threshold * 0.5
            
            for det_idx in unmatched_detections:
                iou = self._calculate_iou(track.bbox, detections[det_idx]['bbox'])
                
                if iou > best_iou:
                    best_iou = iou
                    best_detection_idx = det_idx
            
            if best_detection_idx >= 0:
                track.update(detections[best_detection_idx]['bbox'], detections[best_detection_idx])
                unmatched_detections.remove(best_detection_idx)
                matched_tracks.add(id(track))
        
        # Create new tracks for unmatched detections
        for det_idx in unmatched_detections:
            new_track = Track(detections[det_idx]['bbox'], detections[det_idx])
            self.tracks.append(new_track)
        
        # Update unmatched tracks (increment age)
        for track in self.tracks:
            if id(track) not in matched_tracks:
                track.increment_age()
        
        # Remove old tracks
        self.tracks = [t for t in self.tracks if t.get_state() != "deleted"]
        
        # Return active confirmed tracks
        active_tracks = [t for t in self.tracks if t.get_state() == "confirmed"]
        
        return active_tracks
    
    def _calculate_iou(self, bbox1, bbox2):
        """Calculate IoU between two bounding boxes"""
        return BBoxUtils.iou(bbox1, bbox2)
    
    def get_all_tracks(self):
        """Get all active tracks"""
        return [t for t in self.tracks if t.get_state() != "deleted"]
    
    def get_confirmed_tracks(self):
        """Get only confirmed tracks"""
        return [t for t in self.tracks if t.get_state() == "confirmed"]
    
    def get_violated_tracks(self):
        """Get confirmed tracks that are violations"""
        return [t for t in self.get_confirmed_tracks() if t.is_violation()]
    
    def get_track_by_id(self, track_id):
        """Get track by ID"""
        for track in self.tracks:
            if track.track_id == track_id:
                return track
        return None
    
    def get_violation_tracks(self, logged_only=False):
        """
        Get violation tracks
        
        Args:
            logged_only: If True, only return tracks with logged violations
            
        Returns:
            List of violation tracks
        """
        violations = []
        
        for track in self.get_confirmed_tracks():
            if track.is_violation():
                if logged_only:
                    if track.violation_logged:
                        violations.append(track)
                else:
                    violations.append(track)
        
        return violations
    
    def reset(self):
        """Reset tracker (use for new video or session)"""
        self.tracks = []
        self.frame_count = 0
        Track.next_id = 1
        logger.info("Tracker reset")

class TrackingStatistics:
    """Calculate statistics from tracking data"""
    
    def __init__(self):
        """Initialize statistics tracker"""
        self.tracked_objects = set()
        self.violation_count = 0
        self.max_concurrent_tracks = 0
    
    def update(self, tracks):
        """Update statistics with current tracks"""
        for track in tracks:
            self.tracked_objects.add(track.track_id)
        
        if len(tracks) > self.max_concurrent_tracks:
            self.max_concurrent_tracks = len(tracks)
    
    def get_statistics(self):
        """Get current statistics"""
        return {
            "unique_objects_tracked": len(self.tracked_objects),
            "violation_count": self.violation_count,
            "max_concurrent_tracks": self.max_concurrent_tracks
        }

logger.info("ByteTracker module initialized")
