# SmartHelmetGuard - Demo Script
# Simple demonstration of the detection system

import argparse
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules import HelmetViolationDetector
from modules.database import DatabaseManager
from modules.evidence_manager import EvidenceManager
from utils import setup_logger

logger = setup_logger(__name__)

def demo_detection(camera_source=0, duration_seconds=30):
    """
    Run a quick detection demo
    
    Args:
        camera_source: Camera source (0 for webcam)
        duration_seconds: Run for this many seconds
    """
    print("\n" + "="*60)
    print("SmartHelmetGuard - Detection Demo")
    print("="*60)
    print(f"Camera: {camera_source}")
    print(f"Duration: {duration_seconds} seconds")
    print("\nInitializing system...")
    
    try:
        # Initialize detector
        detector = HelmetViolationDetector(camera_source=camera_source)
        detector.start()
        
        print("✓ System initialized")
        print("\nRunning detection... (Press Ctrl+C to stop)")
        print("-"*60)
        
        import time
        start_time = time.time()
        
        while True:
            # Get frame
            frame = detector.camera.get_frame(timeout=1)
            
            if frame is None:
                continue
            
            # Process
            result = detector.process_frame(frame)
            
            if result:
                # Print stats every 30 frames
                if detector.frame_count % 30 == 0:
                    stats = detector.get_statistics()
                    print(f"\n[Frame {detector.frame_count}] FPS: {stats['fps']:.1f} | "
                          f"Violations: {stats['violation_count']} | "
                          f"Active Tracks: {stats['active_tracks']}")
                
                # Check time limit
                if time.time() - start_time > duration_seconds:
                    break
        
        detector.stop()
        
        print("\n" + "-"*60)
        print("Demo Complete!")
        print("="*60)
        
        # Print summary
        stats = detector.get_statistics()
        print(f"\nSummary:")
        print(f"  Total Frames: {stats['frame_count']}")
        print(f"  Total Violations: {stats['violation_count']}")
        print(f"  Average FPS: {stats['fps']:.2f}")
        print(f"  Processing Time: {stats['avg_processing_time_ms']:.2f}ms")
        print(f"  Active Tracks: {stats['active_tracks']}")
        print(f"  Total in DB: {stats['total_violations_db']}")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        detector.stop()
    except Exception as e:
        print(f"\nError: {e}")
        logger.error(f"Demo error: {e}")
        sys.exit(1)

def demo_database():
    """Demonstrate database operations"""
    print("\n" + "="*60)
    print("SmartHelmetGuard - Database Demo")
    print("="*60)
    
    try:
        db = DatabaseManager()
        
        print("\nDatabase Operations:")
        print("-"*60)
        
        # Add sample violation
        print("1. Adding sample violation...")
        violation_id = db.add_violation(
            track_id=999,
            status='no_helmet',
            confidence=0.95,
            camera_source='Demo-Camera'
        )
        print(f"   ✓ Violation ID: {violation_id}")
        
        # Get violations
        print("\n2. Retrieving violations...")
        violations = db.get_violations(limit=5)
        print(f"   ✓ Found {len(violations)} violations")
        
        if violations:
            latest = violations[0]
            print(f"   Latest: Track {latest['track_id']} - {latest['status']} ({latest['confidence']*100:.1f}%)")
        
        # Get statistics
        print("\n3. Database statistics...")
        total = db.get_total_violations()
        print(f"   ✓ Total violations in database: {total}")
        
        daily_stats = db.get_daily_violations(days=1)
        print(f"   Today: {daily_stats['violation_count']} violations")
        print(f"   Unique riders: {daily_stats['unique_riders']}")
        print(f"   Avg confidence: {daily_stats['avg_confidence']*100:.1f}%")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def demo_evidence():
    """Demonstrate evidence management"""
    print("\n" + "="*60)
    print("SmartHelmetGuard - Evidence Manager Demo")
    print("="*60)
    
    try:
        em = EvidenceManager()
        
        print("\nEvidence Management:")
        print("-"*60)
        
        # Get statistics
        print("1. Evidence storage statistics...")
        stats = em.get_evidence_stats()
        print(f"   Total files: {stats.get('total_files', 0)}")
        print(f"   Total size: {stats.get('total_size_mb', 0):.2f} MB")
        print(f"   Location: {stats.get('evidence_directory', 'N/A')}")
        
        # List recent evidence
        print("\n2. Recent evidence...")
        evidence_list = em.get_all_evidence(limit=5)
        if evidence_list:
            for i, evidence in enumerate(evidence_list[:3], 1):
                metadata = evidence['metadata']
                print(f"   {i}. Track {metadata['track_id']} - {metadata['timestamp']}")
                print(f"      Confidence: {metadata['violation_confidence']*100:.1f}%")
                print(f"      Faces: {len(evidence['faces'])}")
        else:
            print("   No evidence found")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def demo_health_check():
    """System health check"""
    print("\n" + "="*60)
    print("SmartHelmetGuard - System Health Check")
    print("="*60)
    
    checks = [
        ("Python Version", check_python),
        ("PyTorch Installation", check_pytorch),
        ("OpenCV Installation", check_opencv),
        ("Camera/Webcam", check_camera),
        ("Database", check_database),
        ("Evidence Directory", check_evidence_dir),
        ("Model Download", check_models),
    ]
    
    print("\nRunning system checks...\n")
    passed = 0
    failed = 0
    
    for check_name, check_func in checks:
        try:
            result, message = check_func()
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {check_name}")
            if message:
                print(f"       {message}")
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ FAIL: {check_name}")
            print(f"       {str(e)}")
            failed += 1
    
    print("\n" + "-"*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0

def check_python():
    import sys
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return sys.version_info >= (3, 8), f"Python {version}"

def check_pytorch():
    try:
        import torch
        return torch.cuda.is_available(), f"PyTorch {torch.__version__} (GPU: {torch.cuda.is_available()})"
    except ImportError:
        return False, "PyTorch not installed"

def check_opencv():
    try:
        import cv2
        return True, f"OpenCV {cv2.__version__}"
    except ImportError:
        return False, "OpenCV not installed"

def check_camera():
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            return True, "Webcam (0) available"
        else:
            return False, "Webcam not accessible"
    except Exception as e:
        return False, str(e)

def check_database():
    try:
        from modules.database import DatabaseManager
        db = DatabaseManager()
        return True, f"Database ready ({db.db_path})"
    except Exception as e:
        return False, str(e)

def check_evidence_dir():
    try:
        from config import EVIDENCE_DIR
        from pathlib import Path
        Path(EVIDENCE_DIR).mkdir(parents=True, exist_ok=True)
        return True, f"Evidence dir ready ({EVIDENCE_DIR})"
    except Exception as e:
        return False, str(e)

def check_models():
    try:
        from ultralytics import YOLO
        # This will download if needed
        model = YOLO('yolov8n.pt')
        return True, "YOLOv8n model ready"
    except Exception as e:
        return False, str(e)

def main():
    """Main demo menu"""
    parser = argparse.ArgumentParser(
        description="SmartHelmetGuard - Demo & Testing Suite"
    )
    
    parser.add_argument(
        "--mode",
        choices=["demo", "database", "evidence", "health"],
        default="health",
        help="Demo mode to run"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Duration for detection demo in seconds"
    )
    
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera index (default: 0)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "demo":
        demo_detection(camera_source=args.camera, duration_seconds=args.duration)
    elif args.mode == "database":
        demo_database()
    elif args.mode == "evidence":
        demo_evidence()
    elif args.mode == "health":
        if not demo_health_check():
            sys.exit(1)

if __name__ == "__main__":
    main()
