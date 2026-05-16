# SmartHelmetGuard - Utility Functions
# Helper functions for image processing, logging, and common operations

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import os
from config import LOG_FILE, LOG_LEVEL

# Setup Logger
def setup_logger(name, log_file=LOG_FILE, level=LOG_LEVEL):
    """Configure logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Create default logger
logger = setup_logger(__name__)

class ImageProcessor:
    """Handle image processing operations"""
    
    @staticmethod
    def read_image(image_path):
        """Safely read an image file"""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Failed to read image: {image_path}")
                return None
            return img
        except Exception as e:
            logger.error(f"Error reading image {image_path}: {e}")
            return None
    
    @staticmethod
    def save_image(image, output_path, create_dirs=True):
        """Safely save an image file"""
        try:
            output_path = Path(output_path)
            if create_dirs:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            
            success = cv2.imwrite(str(output_path), image)
            if success:
                logger.debug(f"Image saved: {output_path}")
                return str(output_path)
            else:
                logger.error(f"Failed to save image: {output_path}")
                return None
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return None
    
    @staticmethod
    def crop_region(image, bbox, margin=10):
        """
        Crop a region from the image with optional margin
        
        Args:
            image: Input image
            bbox: Bounding box (x1, y1, x2, y2)
            margin: Margin in pixels
            
        Returns:
            Cropped image or None
        """
        try:
            h, w = image.shape[:2]
            x1, y1, x2, y2 = bbox
            
            # Apply margin
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(w, x2 + margin)
            y2 = min(h, y2 + margin)
            
            cropped = image[y1:y2, x1:x2]
            
            if cropped.shape[0] > 0 and cropped.shape[1] > 0:
                return cropped
            else:
                logger.warning("Invalid crop dimensions")
                return None
                
        except Exception as e:
            logger.error(f"Error cropping image: {e}")
            return None
    
    @staticmethod
    def resize_image(image, width=None, height=None, maintain_aspect=True):
        """Resize image with optional aspect ratio maintenance"""
        try:
            h, w = image.shape[:2]
            
            if maintain_aspect:
                if width is not None:
                    ratio = width / w
                    height = int(h * ratio)
                elif height is not None:
                    ratio = height / h
                    width = int(w * ratio)
            
            if width and height:
                resized = cv2.resize(image, (width, height))
                return resized
            else:
                return image
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            return None
    
    @staticmethod
    def blur_region(image, bbox, blur_strength=51):
        """Blur a region of interest in the image"""
        try:
            img_copy = image.copy()
            x1, y1, x2, y2 = bbox
            
            # Ensure odd blur kernel size
            if blur_strength % 2 == 0:
                blur_strength += 1
            
            region = img_copy[y1:y2, x1:x2]
            blurred_region = cv2.GaussianBlur(region, (blur_strength, blur_strength), 0)
            img_copy[y1:y2, x1:x2] = blurred_region
            
            return img_copy
        except Exception as e:
            logger.error(f"Error blurring region: {e}")
            return image
    
    @staticmethod
    def draw_bbox(image, bbox, label, color, thickness=2, font_scale=0.6):
        """Draw bounding box with label on image"""
        try:
            img_copy = image.copy()
            x1, y1, x2, y2 = map(int, bbox)
            
            # Draw rectangle
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, thickness)
            
            # Put text
            if label:
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)[0]
                text_x = x1
                text_y = y1 - 5 if y1 > 25 else y2 + 20
                
                # Dark background for text
                bg_color = (50, 50, 50)
                cv2.rectangle(img_copy, 
                            (text_x, text_y - text_size[1] - 3),
                            (text_x + text_size[0] + 3, text_y + 3),
                            bg_color, -1)
                
                cv2.putText(img_copy, label, (text_x, text_y),
                          cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1)
            
            return img_copy
        except Exception as e:
            logger.error(f"Error drawing bbox: {e}")
            return image

class TimeUtils:
    """Handle time-related operations"""
    
    @staticmethod
    def get_timestamp():
        """Get current timestamp"""
        return datetime.now()
    
    @staticmethod
    def get_timestamp_str(format_str="%Y-%m-%d %H:%M:%S"):
        """Get current timestamp as formatted string"""
        return datetime.now().strftime(format_str)
    
    @staticmethod
    def get_date_str(date=None, format_str="%Y-%m-%d"):
        """Get date as formatted string"""
        if date is None:
            date = datetime.now()
        return date.strftime(format_str)
    
    @staticmethod
    def timestamp_to_str(timestamp, format_str="%Y-%m-%d %H:%M:%S"):
        """Convert timestamp to string"""
        if isinstance(timestamp, str):
            return timestamp
        return timestamp.strftime(format_str)

class FileUtils:
    """Handle file operations"""
    
    @staticmethod
    def ensure_dir_exists(dir_path):
        """Ensure directory exists, create if not"""
        dir_path = Path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def get_file_size(file_path):
        """Get file size in MB"""
        try:
            return os.path.getsize(file_path) / (1024 * 1024)
        except:
            return 0
    
    @staticmethod
    def delete_old_files(directory, days=30):
        """Delete files older than specified days"""
        import time
        try:
            now = time.time()
            cutoff = now - (days * 86400)
            
            for file in Path(directory).glob("*"):
                if file.is_file() and os.stat(file).st_mtime < cutoff:
                    file.unlink()
                    logger.info(f"Deleted old file: {file}")
        except Exception as e:
            logger.error(f"Error deleting old files: {e}")

class BBoxUtils:
    """Handle bounding box operations"""
    
    @staticmethod
    def xyxy_to_xywh(bbox):
        """Convert bbox from (x1, y1, x2, y2) to (x, y, w, h)"""
        x1, y1, x2, y2 = bbox
        return [x1, y1, x2 - x1, y2 - y1]
    
    @staticmethod
    def xywh_to_xyxy(bbox):
        """Convert bbox from (x, y, w, h) to (x1, y1, x2, y2)"""
        x, y, w, h = bbox
        return [x, y, x + w, y + h]
    
    @staticmethod
    def get_bbox_area(bbox):
        """Get area of bounding box"""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)
    
    @staticmethod
    def get_bbox_center(bbox):
        """Get center point of bounding box"""
        x1, y1, x2, y2 = bbox
        return [(x1 + x2) // 2, (y1 + y2) // 2]
    
    @staticmethod
    def iou(bbox1, bbox2):
        """Calculate IoU between two bboxes"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        inter_x1 = max(x1_1, x1_2)
        inter_y1 = max(y1_1, y1_2)
        inter_x2 = min(x2_1, x2_2)
        inter_y2 = min(y2_1, y2_2)
        
        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
        
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        
        union_area = area1 + area2 - inter_area
        
        if union_area == 0:
            return 0
        
        return inter_area / union_area

logger.info("Utils module initialized")
