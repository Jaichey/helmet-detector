# SmartHelmetGuard - Database Module
# Handles SQLite database for evidence storage and querying

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from utils import setup_logger, TimeUtils
from config import DATABASE_PATH

logger = setup_logger(__name__)

class DatabaseManager:
    """
    Manage SQLite database for violation records
    
    Tables:
    - violations: Main violation records
    - evidence: Evidence files and metadata
    - statistics: Daily/weekly statistics
    """
    
    def __init__(self, db_path=DATABASE_PATH):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Violations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS violations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        track_id INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        camera_source TEXT DEFAULT 'unknown',
                        location_description TEXT,
                        latitude REAL,
                        longitude REAL,
                        unique_rider INTEGER DEFAULT 1,
                        UNIQUE(track_id, timestamp)
                    )
                ''')
                
                # Evidence table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evidence (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        violation_id INTEGER NOT NULL,
                        evidence_type TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_size_mb REAL,
                        captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        quality_score REAL,
                        FOREIGN KEY (violation_id) REFERENCES violations(id)
                    )
                ''')
                
                # Face evidence (separate table for better querying)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS face_evidence (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        violation_id INTEGER NOT NULL,
                        face_image_path TEXT NOT NULL,
                        face_quality REAL,
                        face_size_pixels INTEGER,
                        captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (violation_id) REFERENCES violations(id)
                    )
                ''')
                
                # Statistics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        total_violations INTEGER DEFAULT 0,
                        unique_riders INTEGER DEFAULT 0,
                        avg_confidence REAL DEFAULT 0,
                        helmet_detections INTEGER DEFAULT 0,
                        no_helmet_detections INTEGER DEFAULT 0,
                        UNIQUE(date)
                    )
                ''')
                
                # Create indexes for better query performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON violations(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_status ON violations(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_track_id ON violations(track_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_evidence_violation_id ON evidence(violation_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_face_evidence_violation_id ON face_evidence(violation_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_statistics_date ON statistics(date)')
                
                conn.commit()
                logger.info(f"Database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def add_violation(self, track_id, status, confidence, camera_source="Unknown", location=None):
        """
        Add violation record to database
        
        Args:
            track_id: Tracking ID
            status: 'no_helmet' or 'helmet'
            confidence: Detection confidence (0-1)
            camera_source: Camera ID or name
            location: Dict with 'name', 'lat', 'lon'
            
        Returns:
            violation_id or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                loc_name = location.get('name') if location else None
                lat = location.get('lat') if location else None
                lon = location.get('lon') if location else None
                
                cursor.execute('''
                    INSERT INTO violations 
                    (track_id, status, confidence, camera_source, location_description, latitude, longitude)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (track_id, status, confidence, camera_source, loc_name, lat, lon))
                
                conn.commit()
                violation_id = cursor.lastrowid
                
                logger.info(f"Violation recorded: ID={violation_id}, Track={track_id}, Status={status}")
                return violation_id
                
        except Exception as e:
            logger.error(f"Error adding violation: {e}")
            return None
    
    def add_evidence(self, violation_id, evidence_type, file_path, file_name, file_size_mb=None, quality_score=None):
        """
        Add evidence file record
        
        Args:
            violation_id: Associated violation ID
            evidence_type: 'full_frame', 'face_crop', 'metadata'
            file_path: Full path to evidence file
            file_name: File name only
            file_size_mb: File size in MB
            quality_score: Quality metric (0-1)
            
        Returns:
            evidence_id or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO evidence 
                    (violation_id, evidence_type, file_path, file_name, file_size_mb, quality_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (violation_id, evidence_type, str(file_path), file_name, file_size_mb, quality_score))
                
                conn.commit()
                evidence_id = cursor.lastrowid
                
                logger.debug(f"Evidence recorded: ID={evidence_id}, Type={evidence_type}")
                return evidence_id
                
        except Exception as e:
            logger.error(f"Error adding evidence: {e}")
            return None
    
    def add_face_evidence(self, violation_id, face_image_path, quality_score=None, face_size=None):
        """
        Add face evidence record
        
        Args:
            violation_id: Associated violation ID
            face_image_path: Path to face image
            quality_score: Face quality (0-1)
            face_size: Face size in pixels
            
        Returns:
            face_evidence_id or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO face_evidence 
                    (violation_id, face_image_path, face_quality, face_size_pixels)
                    VALUES (?, ?, ?, ?)
                ''', (violation_id, str(face_image_path), quality_score, face_size))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error adding face evidence: {e}")
            return None
    
    def get_violations(self, limit=100, offset=0, status_filter=None, date_range=None):
        """
        Get violations from database
        
        Args:
            limit: Number of records to return
            offset: Offset for pagination
            status_filter: Filter by status ('helmet', 'no_helmet')
            date_range: Tuple (start_date, end_date)
            
        Returns:
            List of violation records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM violations WHERE 1=1"
                params = []
                
                if status_filter:
                    query += " AND status = ?"
                    params.append(status_filter)
                
                if date_range:
                    start_date, end_date = date_range
                    query += " AND timestamp >= ? AND timestamp <= ?"
                    params.extend([start_date, end_date])
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error fetching violations: {e}")
            return []
    
    def get_violation_detail(self, violation_id):
        """Get detailed information about a violation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get violation
                cursor.execute("SELECT * FROM violations WHERE id = ?", (violation_id,))
                violation = cursor.fetchone()
                
                if not violation:
                    return None
                
                violation_dict = dict(violation)
                
                # Get associated evidence
                cursor.execute("SELECT * FROM evidence WHERE violation_id = ?", (violation_id,))
                violation_dict['evidence'] = [dict(row) for row in cursor.fetchall()]
                
                # Get face evidence
                cursor.execute("SELECT * FROM face_evidence WHERE violation_id = ?", (violation_id,))
                violation_dict['face_evidence'] = [dict(row) for row in cursor.fetchall()]
                
                return violation_dict
                
        except Exception as e:
            logger.error(f"Error fetching violation detail: {e}")
            return None
    
    def get_statistics(self, date=None):
        """Get statistics for a specific date"""
        try:
            if date is None:
                date = TimeUtils.get_date_str()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM statistics WHERE date = ?", (date,))
                result = cursor.fetchone()
                
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")
            return None
    
    def get_daily_violations(self, days=1):
        """Get violation count for last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute('''
                    SELECT COUNT(*) as violation_count, 
                           COUNT(DISTINCT track_id) as unique_riders,
                           AVG(confidence) as avg_confidence
                    FROM violations
                    WHERE timestamp >= ? AND status = 'no_helmet'
                ''', (start_date,))
                
                result = cursor.fetchone()
                return dict(zip(['violation_count', 'unique_riders', 'avg_confidence'], result))
                
        except Exception as e:
            logger.error(f"Error getting daily violations: {e}")
            return {'violation_count': 0, 'unique_riders': 0, 'avg_confidence': 0}
    
    def update_statistics(self, date, stats_dict):
        """Update daily statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO statistics 
                    (date, total_violations, unique_riders, avg_confidence, helmet_detections, no_helmet_detections)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (date, stats_dict.get('total_violations', 0),
                      stats_dict.get('unique_riders', 0),
                      stats_dict.get('avg_confidence', 0),
                      stats_dict.get('helmet_detections', 0),
                      stats_dict.get('no_helmet_detections', 0)))
                
                conn.commit()
                logger.debug(f"Statistics updated for {date}")
                
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def cleanup_old_data(self, days=30):
        """Remove evidence older than specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute("DELETE FROM violations WHERE timestamp < ?", (cutoff_date,))
                
                conn.commit()
                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old violations (before {cutoff_date})")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_total_violations(self):
        """Get total violation count in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM violations WHERE status = 'no_helmet'")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting violations: {e}")
            return 0

logger.info("DatabaseManager module initialized")
