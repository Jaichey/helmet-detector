# SmartHelmetGuard - Camera Input Module
# Handles camera, video file, and RTSP stream input

import cv2
import numpy as np
from pathlib import Path
from threading import Thread, Event
from queue import Queue, Empty
from utils import setup_logger, TimeUtils
from config import CAMERA_FPS, CAMERA_WIDTH, CAMERA_HEIGHT

logger = setup_logger(__name__)

class CameraManager:
    """
    Manage camera input from various sources:
    - Webcam (index 0, 1, 2, etc)
    - Video file
    - RTSP stream
    """
    
    def __init__(self, source=0, frame_queue_size=30):
        """
        Initialize camera manager
        
        Args:
            source: Camera source (int for webcam, str for video/RTSP)
            frame_queue_size: Size of frame queue for threading
        """
        self.source = source
        self.frame_queue = Queue(maxsize=frame_queue_size)
        self.capture = None
        self.is_running = False
        self.thread = None
        self.stop_event = Event()
        
        self.frame_count = 0
        self.fps = CAMERA_FPS
        self.frame_width = CAMERA_WIDTH
        self.frame_height = CAMERA_HEIGHT
        self.source_type = "unknown"
        
        self._setup_source()
    
    def _setup_source(self):
        """Initialize video capture source"""
        try:
            if isinstance(self.source, int):
                # Webcam
                logger.info(f"Opening webcam: {self.source}")
                self.capture = cv2.VideoCapture(self.source)
                # Set to use DSHOW backend instead of MSMF for better Windows compatibility
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for low latency
                self.source_type = "webcam"
                
            elif isinstance(self.source, str):
                # Video file or RTSP stream
                if self.source.startswith(('http://', 'https://', 'rtsp://')):
                    logger.info(f"Opening RTSP stream: {self.source}")
                    self.source_type = "rtsp_stream"
                else:
                    video_path = Path(self.source)
                    if not video_path.exists():
                        logger.error(f"Video file not found: {self.source}")
                        return False
                    logger.info(f"Opening video file: {self.source}")
                    self.source_type = "video_file"
                
                self.capture = cv2.VideoCapture(self.source)
            
            if not self.capture or not self.capture.isOpened():
                logger.error(f"Failed to open source: {self.source}")
                return False
            
            # Set camera properties for optimal performance
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Reduce latency on Windows
            if isinstance(self.source, int):
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Get actual properties
            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.capture.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps} FPS")
            logger.info(f"Source type: {self.source_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False
    
    def start(self):
        """Start reading frames in background thread"""
        # Reinitialize camera if it was released after stop
        if self.capture is None or not self.capture.isOpened():
            logger.info("Reinitializing camera after previous stop...")
            self._setup_source()
        
        if self.capture is None or not self.capture.isOpened():
            logger.error("Camera not initialized")
            return False
        
        if self.is_running:
            logger.warning("Camera already running")
            return True
        
        self.is_running = True
        self.stop_event.clear()
        self.thread = Thread(target=self._read_frames, daemon=True)
        self.thread.start()
        
        logger.info("Camera started")
        return True
    
    def stop(self):
        """Stop reading frames"""
        self.is_running = False
        self.stop_event.set()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.capture:
            self.capture.release()
            self.capture = None  # Set to None so it can be reinitialized
        
        logger.info("Camera stopped")
    
    def _read_frames(self):
        """Background thread for reading frames - optimized for speed"""
        while not self.stop_event.is_set():
            try:
                ret, frame = self.capture.read()
                
                if not ret:
                    logger.warning("Failed to read frame")
                    # For video files, loop or stop
                    if self.source_type == "video_file":
                        logger.info("End of video reached")
                        break
                    else:
                        continue
                
                self.frame_count += 1
                
                # Resize frame if needed
                frame = self._resize_frame(frame)
                
                # Clear old frames from queue if it's getting full
                # This ensures we always have the LATEST frame, not old ones
                if self.frame_queue.qsize() >= self.frame_queue.maxsize - 2:
                    try:
                        self.frame_queue.get_nowait()  # Discard oldest frame
                    except:
                        pass
                
                # Put latest frame
                try:
                    self.frame_queue.put(frame, block=False)
                except:
                    # Queue is full, that's ok - we'll get the next one
                    pass
                
            except Exception as e:
                logger.error(f"Error reading frame: {e}")
                continue
    
    def _resize_frame(self, frame):
        """Resize frame to target dimensions"""
        try:
            h, w = frame.shape[:2]
            
            if w != self.frame_width or h != self.frame_height:
                frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            
            return frame
            
        except Exception as e:
            logger.error(f"Error resizing frame: {e}")
            return frame
    
    def get_frame(self, timeout=1):
        """
        Get latest frame from queue with short timeout
        
        Args:
            timeout: Wait timeout in seconds (shorter = faster UI updates)
            
        Returns:
            Frame or None
        """
        try:
            # Use shorter timeout for responsive UI
            frame = self.frame_queue.get(timeout=timeout)
            return frame
        except Empty:
            return None
        except Exception as e:
            logger.debug(f"Error getting frame: {e}")
            return None
    
    def get_info(self):
        """Get camera information"""
        return {
            'source': str(self.source),
            'source_type': self.source_type,
            'frame_count': self.frame_count,
            'fps': self.fps,
            'width': self.frame_width,
            'height': self.frame_height,
            'is_running': self.is_running,
            'queue_size': self.frame_queue.qsize()
        }
    
    def set_resolution(self, width, height):
        """Set camera resolution"""
        if self.capture:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.frame_width = width
            self.frame_height = height
    
    def set_fps(self, fps):
        """Set camera FPS"""
        if self.capture:
            self.capture.set(cv2.CAP_PROP_FPS, fps)
            self.fps = fps
    
    def is_online(self):
        """Check if camera is online and running"""
        return self.is_running and self.capture and self.capture.isOpened()

class MultiCameraManager:
    """
    Manage multiple cameras simultaneously
    """
    
    def __init__(self):
        """Initialize multi-camera manager"""
        self.cameras = {}
    
    def add_camera(self, camera_id, source):
        """Add camera"""
        try:
            camera = CameraManager(source)
            if camera.capture and camera.capture.isOpened():
                self.cameras[camera_id] = camera
                logger.info(f"Camera added: {camera_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding camera {camera_id}: {e}")
            return False
    
    def start_all(self):
        """Start all cameras"""
        for camera_id, camera in self.cameras.items():
            camera.start()
            logger.info(f"Camera {camera_id} started")
    
    def stop_all(self):
        """Stop all cameras"""
        for camera_id, camera in self.cameras.items():
            camera.stop()
            logger.info(f"Camera {camera_id} stopped")
    
    def get_frame(self, camera_id, timeout=1):
        """Get frame from specific camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_frame(timeout=timeout)
        return None
    
    def get_all_frames(self):
        """Get frame from all cameras"""
        frames = {}
        for camera_id, camera in self.cameras.items():
            frame = camera.get_frame(timeout=0.1)
            if frame is not None:
                frames[camera_id] = frame
        return frames

logger.info("CameraManager module initialized")
