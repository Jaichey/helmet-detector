# SmartHelmetGuard - Main Entry Point
# Run the complete system with all components

import argparse
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules import HelmetViolationDetector
from utils import setup_logger
import cv2

logger = setup_logger(__name__)

def run_manual_detection(detector, video_source=0, conf_threshold=0.45, output_video=None):
    """
    Run detection on video/camera feed
    
    Args:
        detector: HelmetViolationDetector instance
        video_source: Camera index or video file path
        conf_threshold: Detection confidence threshold
        output_video: Optional output video file path
    """
    try:
        logger.info("Starting manual detection mode...")
        
        # Initialize camera
        detector.camera = detector.camera or __import__('modules.camera', fromlist=['CameraManager']).CameraManager(video_source)
        detector.camera.start()
        
        # Video writer (if output specified)
        video_writer = None
        if output_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                output_video,
                fourcc,
                detector.camera.fps,
                (detector.camera.frame_width, detector.camera.frame_height)
            )
        
        frame_count = 0
        
        while True:
            # Get frame
            frame = detector.camera.get_frame(timeout=1)
            if frame is None:
                continue
            
            # Process frame
            result = detector.process_frame(frame, conf_threshold)
            
            if result is None:
                continue
            
            frame_count += 1
            
            # Display
            display_frame = result['frame']
            
            # Add info overlay
            info_text = [
                f"FPS: {result['fps']:.1f}",
                f"Violations: {detector.violation_count}",
                f"Active Tracks: {len(result['tracked_objects'])}",
                f"Processing: {result['processing_time_ms']:.1f}ms"
            ]
            
            y_offset = 30
            for text in info_text:
                cv2.putText(display_frame, text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 25
            
            # Show frame
            cv2.imshow("SmartHelmetGuard - Press 'q' to quit", display_frame)
            
            # Write to output video
            if video_writer:
                video_writer.write(display_frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("Quit requested by user")
                break
        
        logger.info(f"Detection completed: {frame_count} frames processed")
        
        # Cleanup
        if video_writer:
            video_writer.release()
        cv2.destroyAllWindows()
        detector.stop()
        
        # Print statistics
        stats = detector.get_statistics()
        print("\n" + "="*50)
        print("DETECTION STATISTICS")
        print("="*50)
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("="*50)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        detector.stop()
    except Exception as e:
        logger.error(f"Error during detection: {e}")
        detector.stop()
        raise

def run_dashboard():
    """Run Streamlit dashboard"""
    import subprocess
    
    dashboard_path = Path(__file__).parent / "dashboard.py"
    
    logger.info("Starting Streamlit dashboard...")
    try:
        subprocess.run(["streamlit", "run", str(dashboard_path)])
    except FileNotFoundError:
        logger.error("Streamlit not installed. Run: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SmartHelmetGuard - Real-Time Helmet Violation Detection System"
    )
    
    parser.add_argument(
        "--mode",
        choices=["dashboard", "manual", "api"],
        default="dashboard",
        help="Execution mode (default: dashboard)"
    )
    
    parser.add_argument(
        "--camera",
        type=str,
        default="0",
        help="Camera source: camera index (0, 1, ...), video file, or RTSP URL (default: 0)"
    )
    
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.45,
        help="Detection confidence threshold (default: 0.45)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output video file path (for manual mode)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without GUI display"
    )
    
    args = parser.parse_args()
    
    # Convert camera argument
    try:
        camera_source = int(args.camera)
    except ValueError:
        camera_source = args.camera  # File path or RTSP URL
    
    logger.info(f"SmartHelmetGuard v1.0.0 starting in {args.mode} mode...")
    
    if args.mode == "dashboard":
        run_dashboard()
    
    elif args.mode == "manual":
        detector = HelmetViolationDetector(
            camera_source=camera_source,
            confidence_threshold=args.confidence
        )
        detector.start()
        run_manual_detection(
            detector,
            video_source=camera_source,
            conf_threshold=args.confidence,
            output_video=args.output
        )
    
    elif args.mode == "api":
        logger.info("API mode not yet implemented")
        sys.exit(1)

if __name__ == "__main__":
    main()
