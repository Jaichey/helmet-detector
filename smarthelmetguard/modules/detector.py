# SmartHelmetGuard - Helmet Detection Module
# Handles real-time helmet detection using YOLOv8

import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import torch
from config import (
    HELMET_MODEL_NAME, HELMET_CONFIDENCE_THRESHOLD, 
    IOU_THRESHOLD, DETECTION_CLASSES, MODELS_DIR
)
from utils import setup_logger, BBoxUtils

logger = setup_logger(__name__)

# COCO Dataset Class IDs (for standard YOLOv8 COCO model)
COCO_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "airplane",
    5: "bus",
    6: "train",
    7: "truck",
    # ... 73 more classes in COCO
}

class HelmetDetector:
    """
    Helmet Detection System using YOLOv8 + Vision-based Analysis
    
    Strategy:
    1. Detect people and motorcycles using YOLOv8 COCO
    2. Analyze head region of person for helmet presence
    3. Check for helmet silhouette/shape above head
    """
    
    def __init__(self, model_name=HELMET_MODEL_NAME, device="auto"):
        """
        Initialize helmet detector
        
        Args:
            model_name: Model size (n, s, m, l, x) - COCO detection model
            device: Device to use (cuda, cpu, auto)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.confidence_threshold = HELMET_CONFIDENCE_THRESHOLD
        self.iou_threshold = IOU_THRESHOLD
        self.helmet_cascade = None
        
        self._initialize_model()
        self._initialize_helmet_detector()
    
    def _initialize_model(self):
        """Initialize YOLOv8 COCO model"""
        try:
            logger.info(f"Loading YOLOv8 {self.model_name} model (COCO)...")
            
            # Load standard COCO-trained YOLOv8 model
            model_path = f"{self.model_name}.pt"  # Will download from ultralytics
            self.model = YOLO(model_path)
            
            # Set device
            if self.device == "auto":
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self.model.to(self.device)
            logger.info(f"Model loaded successfully on {self.device}")
            logger.info(f"Using device: {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _initialize_helmet_detector(self):
        """Initialize helmet detection using Haar Cascade"""
        try:
            # Use OpenCV's cascades for head/helmet detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.helmet_cascade = cv2.CascadeClassifier(cascade_path)
            logger.info("Helmet detection cascade loaded")
        except Exception as e:
            logger.warning(f"Could not load helmet cascade: {e}")
    
    def detect(self, frame, conf=None, iou=None):
        """
        Detect people, motorcycles and helmets in frame
        
        Args:
            frame: Input frame (BGR image)
            conf: Confidence threshold override
            iou: IoU threshold override
            
        Returns:
            list: Detection results [{
                'bbox': [x1, y1, x2, y2],
                'class': 'helmet' or 'no_helmet',
                'confidence': float,
                'class_id': int,
                'area': float
            }, ...]
        """
        try:
            if self.model is None:
                logger.warning("Model not loaded")
                return []
            
            conf = conf or self.confidence_threshold
            iou = iou or self.iou_threshold
            
            # Run YOLOv8 detection on frame
            results = self.model(frame, conf=conf, iou=iou, verbose=False)
            
            detections = []
            
            if results and len(results) > 0:
                result = results[0]
                
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confs = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)
                    
                    for box, conf_score, class_id in zip(boxes, confs, class_ids):
                        x1, y1, x2, y2 = box
                        
                        # We're looking for "person" class (ID=0) from COCO
                        if class_id == 0:  # person
                            helmet_status = self._check_helmet_status(frame, [x1, y1, x2, y2])
                            
                            detection = {
                                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                'class': helmet_status,  # helmet or no_helmet
                                'confidence': float(conf_score),
                                'class_id': int(class_id),
                                'area': BBoxUtils.get_bbox_area([x1, y1, x2, y2]),
                                'original_class': 'person'
                            }
                            
                            detections.append(detection)
                        
                        # Also detect motorcycles/bikes for context
                        elif class_id == 3:  # motorcycle
                            detection = {
                                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                'class': 'unknown',
                                'confidence': float(conf_score),
                                'class_id': int(class_id),
                                'area': BBoxUtils.get_bbox_area([x1, y1, x2, y2]),
                                'original_class': 'motorcycle'
                            }
                            detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def _check_helmet_status(self, frame, bbox):
        """
        Analyze person's head region to determine helmet status
        
        Args:
            frame: Input frame
            bbox: Person bounding box [x1, y1, x2, y2]
            
        Returns:
            'helmet' or 'no_helmet'
        """
        try:
            x1, y1, x2, y2 = map(int, bbox)
            
            # Extract head region (top 40% of person bbox)
            head_height = int((y2 - y1) * 0.4)
            head_region = frame[y1:y1+head_height, x1:x2]
            
            if head_region.size == 0:
                return "no_helmet"  # Default to no helmet if can't analyze
            
            # Convert to HSV for better detection
            hsv = cv2.cvtColor(head_region, cv2.COLOR_BGR2HSV)
            
            # Look for darker regions (helmet typically darker than face)
            # Helmets are usually dark colors
            lower_dark = np.array([0, 0, 0])
            upper_dark = np.array([180, 255, 100])  # Dark colors
            
            mask = cv2.inRange(hsv, lower_dark, upper_dark)
            dark_ratio = np.count_nonzero(mask) / mask.size
            
            # If more than 40% of head region is dark, likely wearing helmet
            if dark_ratio > 0.4:
                return "helmet"
            else:
                return "no_helmet"
            
        except Exception as e:
            logger.debug(f"Error analyzing helmet: {e}")
            return "no_helmet"
    
    def filter_detections(self, detections, min_area=0, max_area=None):
        """
        Filter detections by area
        
        Args:
            detections: List of detections
            min_area: Minimum area in pixels
            max_area: Maximum area in pixels
            
        Returns:
            Filtered list of detections
        """
        filtered = []
        
        for det in detections:
            area = det['area']
            if area >= min_area:
                if max_area is None or area <= max_area:
                    filtered.append(det)
        
        return filtered
    
    def get_violation_status(self, detection):
        """
        Get violation status from detection
        
        Returns:
            'no_helmet': Violation detected
            'helmet': Legal
            'unknown': Uncertain
        """
        class_name = detection['class']
        confidence = detection['confidence']
        
        if class_name == "no_helmet":
            return "no_helmet"
        elif class_name == "helmet":
            return "helmet"
        else:
            return "unknown"
    
    def warmup(self):
        """Warmup model with dummy input for faster inference"""
        try:
            logger.info("Warming up model...")
            dummy_input = np.zeros((1, 640, 640, 3), dtype=np.uint8)
            self.model(dummy_input, verbose=False)
            logger.info("Model warmup complete")
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")

class DetectionAggregator:
    """Aggregate and process multiple detections"""
    
    def __init__(self, window_size=5):
        """
        Initialize aggregator
        
        Args:
            window_size: Window size for smoothing confidence
        """
        self.window_size = window_size
        self.confidence_history = {}
    
    def smooth_confidence(self, track_id, confidence):
        """
        Smooth confidence over time using moving average
        
        Args:
            track_id: Tracking ID
            confidence: Current confidence
            
        Returns:
            Smoothed confidence
        """
        if track_id not in self.confidence_history:
            self.confidence_history[track_id] = []
        
        history = self.confidence_history[track_id]
        history.append(confidence)
        
        # Keep only last N values
        if len(history) > self.window_size:
            history.pop(0)
        
        return np.mean(history)
    
    def clean_old_tracks(self, active_track_ids):
        """Remove confidence history for inactive tracks"""
        inactive_ids = set(self.confidence_history.keys()) - set(active_track_ids)
        for track_id in inactive_ids:
            del self.confidence_history[track_id]

logger.info("HelmetDetector module initialized")
