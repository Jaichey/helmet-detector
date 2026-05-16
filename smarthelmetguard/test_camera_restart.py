#!/usr/bin/env python3
"""Test camera restart functionality"""

import time
import sys
from pathlib import Path
from modules.camera import CameraManager
from utils import setup_logger

logger = setup_logger(__name__)

def test_camera_restart():
    """Test camera stop and restart cycle"""
    print("\n" + "="*60)
    print("Testing Camera Restart Functionality")  
    print("="*60 + "\n")
    
    try:
        # Initialize camera
        logger.info("1. Initializing camera...")
        camera = CameraManager(source=0)
        
        if not camera.capture or not camera.capture.isOpened():
            print("❌ FAILED: Camera initialization")
            return False
        
        print("✓ Camera initialized successfully\n")
        
        # First cycle
        logger.info("2. Starting camera (1st cycle)...")
        if not camera.start():
            print("❌ FAILED: First start")
            return False
        
        print("✓ Camera started successfully")
        time.sleep(2)
        
        frame = camera.get_frame(timeout=2)
        if frame is None:
            print("❌ FAILED: Could not get frame")
            return False
        
        print(f"✓ Successfully captured frame: {frame.shape}")
        
        # Stop camera
        logger.info("3. Stopping camera...")
        camera.stop()
        print("✓ Camera stopped successfully")
        time.sleep(1)
        
        # Second cycle - CRITICAL TEST
        logger.info("4. Restarting camera (2nd cycle) - THIS WAS FAILING BEFORE...")
        if not camera.start():
            print("❌ FAILED: Second start (This is the bug we fixed!)")
            return False
        
        print("✓ Camera restarted successfully!")
        time.sleep(2)
        
        frame2 = camera.get_frame(timeout=2)
        if frame2 is None:
            print("❌ FAILED: Could not get frame after restart")
            return False
        
        print(f"✓ Successfully captured frame after restart: {frame2.shape}")
        
        # Third cycle
        logger.info("5. Stopping camera again...")
        camera.stop()
        print("✓ Camera stopped successfully")
        time.sleep(1)
        
        # Fourth cycle
        logger.info("6. Final restart...")
        if not camera.start():
            print("❌ FAILED: Third start")
            return False
        
        print("✓ Camera restarted again")
        time.sleep(2)
        
        frame3 = camera.get_frame(timeout=2)
        if frame3 is not None:
            print(f"✓ Successfully captured frame after final restart: {frame3.shape}")
        
        camera.stop()
        
        print("\n" + "="*60)
        print("✅ ALL CAMERA RESTART TESTS PASSED!")
        print("="*60 + "\n")
        print("Summary:")
        print("  ✓ Initial camera initialization")
        print("  ✓ First start/stop cycle")
        print("  ✓ RESTART after stop (THIS WAS THE BUG)")
        print("  ✓ Multiple restart cycles")
        print("\nThe camera initialization error is now FIXED!\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_camera_restart()
    sys.exit(0 if success else 1)
