# SmartHelmetGuard - Evidence Manager Module
# Handles saving and organizing evidence files

import cv2
import os
from pathlib import Path
from datetime import datetime
from io import BytesIO
import json
from utils import setup_logger, ImageProcessor, TimeUtils, FileUtils
from config import EVIDENCE_DIR, SAVE_FULL_FRAME, SAVE_FACE_CROP

logger = setup_logger(__name__)

class EvidenceManager:
    """
    Manage evidence collection and storage
    
    Organizes evidence in directory structure:
    evidence/
    ├── YYYY-MM-DD/
    │   ├── {track_id}-{timestamp}/
    │   │   ├── full_frame.jpg
    │   │   ├── face_crop.jpg
    │   │   └── metadata.json
    """
    
    def __init__(self, base_dir=EVIDENCE_DIR):
        """
        Initialize evidence manager
        
        Args:
            base_dir: Base directory for evidence storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Evidence manager initialized: {self.base_dir}")
    
    def save_violation_evidence(self, frame, faces, track_id, violation_confidence, 
                               camera_source="Unknown", save_full=True, save_faces=True):
        """
        Save complete violation evidence
        
        Args:
            frame: Full frame image
            faces: List of face detections
            track_id: Tracking ID
            violation_confidence: Confidence score
            camera_source: Camera ID
            save_full: Save full frame
            save_faces: Save face crops
            
        Returns:
            dict: Saved evidence paths and metadata
        """
        try:
            timestamp = TimeUtils.get_timestamp()
            date_str = TimeUtils.get_date_str(timestamp)
            time_str = timestamp.strftime("%H%M%S")
            
            # Create evidence directory
            evidence_dir = self.base_dir / date_str / f"{track_id}-{time_str}"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            
            evidence_paths = {
                'track_id': track_id,
                'timestamp': timestamp.isoformat(),
                'camera_source': camera_source,
                'violation_confidence': violation_confidence,
                'full_frame': None,
                'faces': [],
                'metadata': None
            }
            
            # Save full frame
            if save_full and frame is not None:
                full_frame_path = evidence_dir / "full_frame.jpg"
                saved_path = ImageProcessor.save_image(frame, full_frame_path)
                if saved_path:
                    file_size = FileUtils.get_file_size(saved_path)
                    evidence_paths['full_frame'] = {
                        'path': str(full_frame_path),
                        'size_mb': file_size
                    }
            
            # Save face crops
            if save_faces and faces:
                for i, face_data in enumerate(faces):
                    try:
                        face_image = face_data.get('face_image')
                        if face_image is None:
                            continue
                        
                        face_path = evidence_dir / f"face_{i}.jpg"
                        saved_path = ImageProcessor.save_image(face_image, face_path)
                        
                        if saved_path:
                            file_size = FileUtils.get_file_size(saved_path)
                            
                            # Calculate face quality
                            quality = self._calculate_face_quality(face_image)
                            
                            evidence_paths['faces'].append({
                                'index': i,
                                'path': str(face_path),
                                'size_mb': file_size,
                                'quality': quality,
                                'bbox': face_data.get('bbox', []),
                                'type': face_data.get('type', 'unknown')
                            })
                    except Exception as e:
                        logger.warning(f"Error saving face {i}: {e}")
            
            # Save metadata
            metadata = self._create_metadata(track_id, timestamp, violation_confidence, 
                                            camera_source, faces, frame)
            metadata_path = evidence_dir / "metadata.json"
            self._save_metadata(metadata, metadata_path)
            evidence_paths['metadata'] = str(metadata_path)
            
            logger.info(f"Evidence saved for track {track_id}: {evidence_dir}")
            return evidence_paths
            
        except Exception as e:
            logger.error(f"Error saving violation evidence: {e}")
            return None
    
    def save_face_evidence(self, face_image, track_id, violation_id=None, quality=None):
        """
        Save individual face evidence
        
        Args:
            face_image: Face image
            track_id: Tracking ID
            violation_id: Database violation ID
            quality: Face quality score
            
        Returns:
            dict: Path and metadata
        """
        try:
            date_str = TimeUtils.get_date_str()
            timestamp_str = TimeUtils.get_timestamp_str("%H%M%S")
            
            face_dir = self.base_dir / date_str / f"faces"
            face_dir.mkdir(parents=True, exist_ok=True)
            
            file_name = f"{track_id}_{timestamp_str}.jpg"
            file_path = face_dir / file_name
            
            saved_path = ImageProcessor.save_image(face_image, file_path)
            
            if saved_path:
                file_size = FileUtils.get_file_size(saved_path)
                
                return {
                    'path': str(file_path),
                    'file_name': file_name,
                    'size_mb': file_size,
                    'quality': quality or self._calculate_face_quality(face_image),
                    'violation_id': violation_id
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error saving face evidence: {e}")
            return None
    
    def _calculate_face_quality(self, face_image):
        """
        Calculate quality score for face image
        
        Returns:
            Score 0-100
        """
        try:
            import numpy as np
            
            if face_image is None or face_image.shape[0] == 0:
                return 0
            
            # Convert to grayscale
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance (sharpness indicator)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-100
            quality = min(100, int(laplacian_var))
            
            return quality
            
        except Exception as e:
            logger.warning(f"Error calculating face quality: {e}")
            return 50
    
    def _create_metadata(self, track_id, timestamp, confidence, camera_source, faces, frame):
        """Create metadata dictionary for violation"""
        metadata = {
            'track_id': track_id,
            'timestamp': timestamp.isoformat(),
            'date': TimeUtils.get_date_str(timestamp),
            'time': timestamp.strftime("%H:%M:%S"),
            'violation_confidence': float(confidence),
            'camera_source': camera_source,
            'frame_dimensions': None,
            'faces_detected': len(faces) if faces else 0,
            'system': 'SmartHelmetGuard v1.0'
        }
        
        # Add frame dimensions
        if frame is not None:
            h, w = frame.shape[:2]
            metadata['frame_dimensions'] = {'width': w, 'height': h}
        
        return metadata
    
    def _save_metadata(self, metadata, output_path):
        """Save metadata to JSON file"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug(f"Metadata saved: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def get_evidence_path(self, track_id, date=None):
        """Get evidence directory path for a track"""
        if date is None:
            date = TimeUtils.get_date_str()
        
        return self.base_dir / date / track_id
    
    def get_evidence_stats(self):
        """Get storage statistics"""
        try:
            total_size = 0
            file_count = 0
            
            for file in self.base_dir.rglob('*'):
                if file.is_file():
                    file_count += 1
                    total_size += file.stat().st_size
            
            return {
                'total_files': file_count,
                'total_size_mb': total_size / (1024 * 1024),
                'evidence_directory': str(self.base_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting evidence stats: {e}")
            return {}
    
    def cleanup_old_evidence(self, days=30):
        """Delete evidence older than specified days"""
        FileUtils.delete_old_files(self.base_dir, days=days)
        logger.info(f"Old evidence cleaned (older than {days} days)")
    
    def get_all_evidence(self, limit=100):
        """Get list of all evidence files"""
        try:
            evidence_list = []
            
            # Get all JSON metadata files
            for metadata_file in sorted(self.base_dir.rglob('metadata.json'), reverse=True)[:limit]:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Get directory structure
                    evidence_dir = metadata_file.parent
                    
                    evidence_entry = {
                        'metadata': metadata,
                        'full_frame': None,
                        'faces': [],
                        'directory': str(evidence_dir)
                    }
                    
                    # Find full frame
                    full_frame_path = evidence_dir / 'full_frame.jpg'
                    if full_frame_path.exists():
                        evidence_entry['full_frame'] = str(full_frame_path)
                    
                    # Find faces
                    for face_file in sorted(evidence_dir.glob('face_*.jpg')):
                        evidence_entry['faces'].append(str(face_file))
                    
                    evidence_list.append(evidence_entry)
                    
                except Exception as e:
                    logger.warning(f"Error reading evidence: {e}")
            
            return evidence_list
            
        except Exception as e:
            logger.error(f"Error getting all evidence: {e}")
            return []

logger.info("EvidenceManager module initialized")
