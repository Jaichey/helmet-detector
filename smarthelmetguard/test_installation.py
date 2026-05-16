#!/usr/bin/env python3
"""
SmartHelmetGuard - Installation Test Script
Tests all major components to ensure the system is installed correctly
"""

import sys

def test_imports():
    """Test that all required packages can be imported"""
    print("=" * 60)
    print("Testing package imports...")
    print("=" * 60)
    
    tests = []
    
    # Test PyTorch
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        cuda_status = f"CUDA {torch.version.cuda}" if cuda_available else "CPU only"
        print(f"✓ PyTorch {torch.__version__} ({cuda_status})")
        tests.append(True)
    except Exception as e:
        print(f"✗ PyTorch: {e}")
        tests.append(False)
    
    # Test Ultralytics
    try:
        from ultralytics import YOLO
        import ultralytics
        print(f"✓ Ultralytics {ultralytics.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"✗ Ultralytics: {e}")
        tests.append(False)
    
    # Test OpenCV
    try:
        import cv2
        print(f"✓ OpenCV {cv2.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"✗ OpenCV: {e}")
        tests.append(False)
    
    # Test NumPy
    try:
        import numpy as np
        print(f"✓ NumPy {np.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"✗ NumPy: {e}")
        tests.append(False)
    
    # Test Streamlit
    try:
        import streamlit as st
        print(f"✓ Streamlit {st.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"✗ Streamlit: {e}")
        tests.append(False)
    
    # Test Pandas
    try:
        import pandas as pd
        print(f"✓ Pandas {pd.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"✗ Pandas: {e}")
        tests.append(False)
    
    # Test Plotly
    try:
        import plotly
        print(f"✓ Plotly {plotly.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"✗ Plotly: {e}")
        tests.append(False)
    
    print()
    return all(tests)


def test_modules():
    """Test that project modules can be imported"""
    print("=" * 60)
    print("Testing project modules...")
    print("=" * 60)
    
    tests = []
    
    try:
        import config
        print("✓ config.py")
        tests.append(True)
    except Exception as e:
        print(f"✗ config.py: {e}")
        tests.append(False)
    
    try:
        import utils
        print("✓ utils.py")
        tests.append(True)
    except Exception as e:
        print(f"✗ utils.py: {e}")
        tests.append(False)
    
    try:
        from modules import detector
        print("✓ modules/detector.py")
        tests.append(True)
    except Exception as e:
        print(f"✗ modules/detector.py: {e}")
        tests.append(False)
    
    try:
        from modules import face_extractor
        print("✓ modules/face_extractor.py")
        tests.append(True)
    except Exception as e:
        print(f"✗ modules/face_extractor.py: {e}")
        tests.append(False)
    
    try:
        from modules import tracker
        print("✓ modules/tracker.py")
        tests.append(True)
    except Exception as e:
        print(f"✗ modules/tracker.py: {e}")
        tests.append(False)
    
    try:
        from modules import camera
        print("✓ modules/camera.py")
        tests.append(True)
    except Exception as e:
        print(f"✗ modules/camera.py: {e}")
        tests.append(False)
    
    try:
        from modules import database
        print("✓ modules/database.py")
        tests.append(True)
    except Exception as e:
        print(f"✗ modules/database.py: {e}")
        tests.append(False)
    
    try:
        from modules import evidence_manager
        print("✓ modules/evidence_manager.py")
        tests.append(True)
    except Exception as e:
        print(f"✗ modules/evidence_manager.py: {e}")
        tests.append(False)
    
    print()
    return all(tests)


def test_helmet_model():
    """Test helmet detection model download and loading"""
    print("=" * 60)
    print("Testing helmet detection model...")
    print("=" * 60)
    
    try:
        from ultralytics import YOLO
        print("Downloading/loading YOLOv8m model (this may take a moment)...")
        model = YOLO('yolov8m.pt')
        print("✓ YOLOv8m model loaded successfully")
        print(f"  Model device: {model.device}")
        return True
    except Exception as e:
        print(f"✗ Failed to load helmet model: {e}")
        return False


def test_face_detection():
    """Test face detection setup"""
    print("=" * 60)
    print("Testing face detection...")
    print("=" * 60)
    
    try:
        import cv2
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if face_cascade.empty():
            print("✗ Failed to load Haar Cascade classifier")
            return False
        
        print("✓ OpenCV Haar Cascade face detector loaded")
        print("  (Default face detection method)")
        return True
    except Exception as e:
        print(f"✗ Failed to load face detector: {e}")
        return False


def test_camera():
    """Test camera access"""
    print("=" * 60)
    print("Testing camera access...")
    print("=" * 60)
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("⚠ Camera 0 not available (this is OK if no camera is connected)")
            print("  You can use video files instead")
            return True
        
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            print(f"✓ Camera 0 working - Resolution: {frame.shape[1]}x{frame.shape[0]}")
            return True
        else:
            print("⚠ Camera opened but couldn't read frame")
            return True
            
    except Exception as e:
        print(f"⚠ Camera test error: {e}")
        print("  You can still use video files")
        return True


def test_database():
    """Test database creation"""
    print("=" * 60)
    print("Testing database...")
    print("=" * 60)
    
    try:
        from modules.database import DatabaseManager
        db = DatabaseManager()
        print("✓ Database initialized successfully")
        print(f"  Database path: {db.db_path}")
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print(" SmartHelmetGuard - Installation Test")
    print("="*60 + "\n")
    
    results = []
    
    # Run all tests
    results.append(("Package Imports", test_imports()))
    results.append(("Project Modules", test_modules()))
    results.append(("Helmet Model", test_helmet_model()))
    results.append(("Face Detection", test_face_detection()))
    results.append(("Camera Access", test_camera()))
    results.append(("Database", test_database()))
    
    # Print summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    print("=" * 60)
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Run the dashboard: streamlit run dashboard.py")
        print("  2. Or run demo mode: python demo.py --mode demo")
        print("  3. Or run main CLI: python main.py --mode manual --camera 0")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("  - Make sure all dependencies are installed: pip install -r requirements.txt")
        print("  - Check the README.md for installation instructions")
        print("  - See SETUP_GUIDE.md for detailed troubleshooting")
        return 1


if __name__ == "__main__":
    sys.exit(main())
