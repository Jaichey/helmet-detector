# SmartHelmetGuard - Face Extraction Module
# Handles face detection and extraction from rider regions

import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import torch
from config import FACE_MODEL_TYPE, FACE_CONFIDENCE_THRESHOLD, MIN_FACE_SIZE
from utils import setup_logger, ImageProcessor, BBoxUtils

logger = setup_logger(__name__)

class FaceExtractor:
    """
    Extract faces from detected riders using OpenCV Haar Cascade (default) or YOLOv8-face (optional)
    
    Only extracts faces for riders detected as "no_helmet"
    """
    
    def __init__(self, model_type=FACE_MODEL_TYPE, device="auto"):
        """
        Initialize face detector
        
        Args:
            model_type: 'opencv' (default), 'yolov8' (requires custom model), or 'haar'
            device: Device to use (cuda, cpu, auto) - only for YOLO models
        """
        self.model_type = model_type
        self.device = device
        self.model = None
        self.confidence_threshold = FACE_CONFIDENCE_THRESHOLD
        self.min_face_size = MIN_FACE_SIZE
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize face detection model"""
        try:
            logger.info(f"Loading face detection model ({self.model_type})...")
            
            if self.model_type == "yolov8":
                # Try to load YOLOv8-face model (optional - must be manually placed in models/)
                model_path = Path("models/yolov8n-face.pt")
                if model_path.exists():
                    self.model = YOLO(str(model_path))
                    
                    # Set device
                    if self.device == "auto":
                        self.device = "cuda" if torch.cuda.is_available() else "cpu"
                    
                    self.model.to(self.device)
                    logger.info(f"YOLOv8-face detector loaded on {self.device}")
                else:
                    logger.info("YOLOv8-face model not found. Using OpenCV Haar Cascade face detector instead.")
                    self._initialize_opencv_face_detector()
            
            elif self.model_type == "opencv" or self.model_type == "haar":
                self._initialize_opencv_face_detector()
            
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
            
        except Exception as e:
            logger.warning(f"Failed to load face model: {e}")
            logger.info("Face detection will use fallback method - rider upper region as face")
            self.model = None
    
    def _initialize_opencv_face_detector(self):
        """Initialize OpenCV Haar Cascade face detector"""
        try:
            # Load pre-trained Haar Cascade model (included with OpenCV)
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.model = cv2.CascadeClassifier(cascade_path)
            
            if self.model.empty():
                raise Exception("Failed to load Haar Cascade classifier")
            
            self.model_type = "opencv"
            logger.info("OpenCV Haar Cascade face detector loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load OpenCV face detector: {e}")
            self.model = None
    
    def extract_faces(self, frame, rider_bbox, rider_class="no_helmet"):
        """
        Extract faces from rider region
        
        Args:
            frame: Full frame image
            rider_bbox: Rider bounding box [x1, y1, x2, y2]
            rider_class: Detection class ('helmet', 'no_helmet', etc)
            
        Returns:
            list: Face detections [
                {
                    'face_image': cropped face image,
                    'bbox': [x1, y1, x2, y2],
                    'confidence': float,
                    'type': 'detected_face' or 'rider_region'
                }, ...
            ]
        """
        try:
            # Only extract faces if rider is without helmet
            if rider_class != "no_helmet":
                return []
            
            faces = []
            
            # If model is not available, use rider region as face
            if self.model is None:
                face_bbox = rider_bbox
                face_crop = ImageProcessor.crop_region(frame, face_bbox, margin=5)
                
                if face_crop is not None and self._is_valid_face(face_crop):
                    faces.append({
                        'face_image': face_crop,
                        'bbox': face_bbox,
                        'confidence': 0.8,  # Default confidence
                        'type': 'rider_region'
                    })
                
                return faces
            
            # Extract rider region
            x1, y1, x2, y2 = map(int, rider_bbox)
            rider_crop = frame[y1:y2, x1:x2].copy()
            
            if rider_crop.shape[0] <= 0 or rider_crop.shape[1] <= 0:
                return []
            
            # Detect faces based on model type
            if self.model_type == "opencv":
                # Use OpenCV Haar Cascade
                gray = cv2.cvtColor(rider_crop, cv2.COLOR_BGR2GRAY)
                detected_faces = self.model.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(self.min_face_size, self.min_face_size)
                )
                
                for (face_x, face_y, face_w, face_h) in detected_faces:
                    face_x1, face_y1 = face_x, face_y
                    face_x2, face_y2 = face_x + face_w, face_y + face_h
                    
                    # Convert to full frame coordinates
                    full_x1 = x1 + face_x1
                    full_y1 = y1 + face_y1
                    full_x2 = x1 + face_x2
                    full_y2 = y1 + face_y2
                    
                    # Crop face from full frame
                    face_crop = ImageProcessor.crop_region(
                        frame, 
                        [full_x1, full_y1, full_x2, full_y2],
                        margin=3
                    )
                    
                    if face_crop is not None:
                        faces.append({
                            'face_image': face_crop,
                            'bbox': [full_x1, full_y1, full_x2, full_y2],
                            'confidence': 0.85,  # OpenCV doesn't provide confidence
                            'type': 'detected_face'
                        })
                        
            elif self.model_type == "yolov8":
                # Use YOLO model
                results = self.model(rider_crop, conf=self.confidence_threshold, verbose=False)
                
                if results and len(results) > 0:
                    result = results[0]
                    
                    if result.boxes is not None:
                        boxes = result.boxes.xyxy.cpu().numpy()
                        confs = result.boxes.conf.cpu().numpy()
                        
                        for box, conf in zip(boxes, confs):
                            face_x1, face_y1, face_x2, face_y2 = map(int, box)
                            
                            # Convert to full frame coordinates
                            full_x1 = x1 + face_x1
                            full_y1 = y1 + face_y1
                            full_x2 = x1 + face_x2
                            full_y2 = y1 + face_y2
                            
                            # Validate face size
                            face_width = full_x2 - full_x1
                            face_height = full_y2 - full_y1
                            
                            if face_width >= self.min_face_size and face_height >= self.min_face_size:
                                # Crop face from full frame
                                face_crop = ImageProcessor.crop_region(
                                    frame, 
                                    [full_x1, full_y1, full_x2, full_y2],
                                    margin=3
                                )
                                
                                if face_crop is not None:
                                    faces.append({
                                        'face_image': face_crop,
                                        'bbox': [full_x1, full_y1, full_x2, full_y2],
                                        'confidence': float(conf),
                                        'type': 'detected_face'
                                    })
            
            # If no faces detected, use upper portion of rider as fallback
            if len(faces) == 0:
                rider_height = y2 - y1
                rider_width = x2 - x1
                
                # Use upper 40% of rider as face region
                fallback_y2 = y1 + int(rider_height * 0.4)
                fallback_bbox = [x1, y1, x2, fallback_y2]
                
                face_crop = ImageProcessor.crop_region(frame, fallback_bbox, margin=5)
                
                if face_crop is not None and self._is_valid_face(face_crop):
                    faces.append({
                        'face_image': face_crop,
                        'bbox': fallback_bbox,
                        'confidence': 0.7,
                        'type': 'rider_region'
                    })
            
            return faces
            
        except Exception as e:
            logger.error(f"Error extracting faces: {e}")
            return []
    
    def _is_valid_face(self, face_image):
        """Check if face image is valid (not too small, not mostly black)"""
        try:
            h, w = face_image.shape[:2]
            
            # Check minimum size
            if h < self.min_face_size or w < self.min_face_size:
                return False
            
            # Check if image is mostly black
            avg_brightness = np.mean(cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY))
            if avg_brightness < 20:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Face validation error: {e}")
            return False
    
    def get_face_quality_score(self, face_image):
        """
        Calculate quality score for face image
        
        Args:
            face_image: Face crop image
            
        Returns:
            Quality score 0-1
        """
        try:
            if face_image is None or face_image.shape[0] == 0:
                return 0.0
            
            # Convert to grayscale
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance (sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-1 (empirical threshold: 100 is good quality)
            quality = min(1.0, laplacian_var / 100.0)
            
            return quality
            
        except Exception as e:
            logger.warning(f"Quality score error: {e}")
            return 0.5

class FaceManager:
    """Manage face detections and avoid duplicates"""
    
    def __init__(self, duplicate_threshold=0.85):
        """
        Initialize face manager
        
        Args:
            duplicate_threshold: Face similarity threshold for duplicate detection
        """
        self.duplicate_threshold = duplicate_threshold
        self.face_history = {}  # track_id -> list of face data
    
    def add_face(self, track_id, face_data):
        """
        Add face detection to history
        
        Args:
            track_id: Tracking ID
            face_data: Face detection data
        """
        if track_id not in self.face_history:
            self.face_history[track_id] = []
        
        self.face_history[track_id].append(face_data)
    
    def get_best_face(self, track_id):
        """
        Get best face for a track based on quality
        
        Args:
            track_id: Tracking ID
            
        Returns:
            Best face data or None
        """
        if track_id not in self.face_history or len(self.face_history[track_id]) == 0:
            return None
        
        # Return most recent face (could be extended to use quality score)
        return self.face_history[track_id][-1]
    
    def clean_old_tracks(self, active_track_ids):
        """Remove history for inactive tracks"""
        inactive_ids = set(self.face_history.keys()) - set(active_track_ids)
        for track_id in inactive_ids:
            del self.face_history[track_id]

logger.info("FaceExtractor module initialized")
