# SmartHelmetGuard - Advanced Configuration Profiles
# Different configurations for different use cases

from config import *

class ProductionProfile:
    """Configuration for production deployment"""
    HELMET_MODEL_NAME = "yolov8l"  # Higher accuracy
    HELMET_CONFIDENCE_THRESHOLD = 0.5
    TRACK_MAX_AGE = 45
    TRACK_MIN_HITS = 5
    ENABLE_TRACKING = True
    ENABLE_DUPLICATE_PREVENTION = True
    TRACKING_COOLDOWN = 20
    SAVE_FULL_FRAME = True
    SAVE_FACE_CROP = True
    SAVE_EVIDENCE_AUTO = True
    EVIDENCE_RETENTION_DAYS = 90
    ENABLE_FACE_BLUR = False
    
    DESCRIPTION = "Production deployment: High accuracy, full evidence storage"

class HighPerformanceProfile:
    """Configuration for CPU-only or low-resource systems"""
    HELMET_MODEL_NAME = "yolov8n"  # Smallest, fastest
    HELMET_CONFIDENCE_THRESHOLD = 0.40
    TRACK_MAX_AGE = 20
    TRACK_MIN_HITS = 2
    ENABLE_TRACKING = True
    ENABLE_DUPLICATE_PREVENTION = True
    TRACKING_COOLDOWN = 10
    SAVE_FULL_FRAME = True
    SAVE_FACE_CROP = False  # Skip face to save processing
    SAVE_EVIDENCE_AUTO = True
    EVIDENCE_RETENTION_DAYS = 15
    ENABLE_FACE_BLUR = False
    
    DESCRIPTION = "High performance: Low latency, minimal storage"

class TestingProfile:
    """Configuration for development and testing"""
    HELMET_MODEL_NAME = "yolov8m"
    HELMET_CONFIDENCE_THRESHOLD = 0.35  # Lower to catch more
    TRACK_MAX_AGE = 30
    TRACK_MIN_HITS = 1  # Easier to create tracks
    ENABLE_TRACKING = True
    ENABLE_DUPLICATE_PREVENTION = False  # Save all
    SAVE_FULL_FRAME = True
    SAVE_FACE_CROP = True
    SAVE_EVIDENCE_AUTO = True
    EVIDENCE_RETENTION_DAYS = 7
    ENABLE_FACE_BLUR = False
    
    DESCRIPTION = "Testing: Loose detection for development"

class PrivacyProfile:
    """Configuration with privacy protection"""
    HELMET_MODEL_NAME = "yolov8m"
    HELMET_CONFIDENCE_THRESHOLD = 0.5
    TRACK_MAX_AGE = 30
    TRACK_MIN_HITS = 3
    ENABLE_TRACKING = True
    ENABLE_DUPLICATE_PREVENTION = True
    TRACKING_COOLDOWN = 30
    SAVE_FULL_FRAME = True
    SAVE_FACE_CROP = False  # Don't save faces
    SAVE_EVIDENCE_AUTO = True
    EVIDENCE_RETENTION_DAYS = 14
    ENABLE_FACE_BLUR = True  # Blur faces in full frames
    
    DESCRIPTION = "Privacy-focused: Minimal face data collection"

PROFILES = {
    'production': ProductionProfile,
    'performance': HighPerformanceProfile,
    'testing': TestingProfile,
    'privacy': PrivacyProfile
}

def get_profile(profile_name='production'):
    """Get configuration profile"""
    profile = PROFILES.get(profile_name.lower(), ProductionProfile)
    return profile

def list_profiles():
    """List available profiles"""
    for name, profile in PROFILES.items():
        print(f"  {name}: {profile.DESCRIPTION}")

def apply_profile(profile_name='production'):
    """Apply profile settings to current module"""
    profile = get_profile(profile_name)
    
    # Override settings
    globals().update({
        'HELMET_MODEL_NAME': profile.HELMET_MODEL_NAME,
        'HELMET_CONFIDENCE_THRESHOLD': profile.HELMET_CONFIDENCE_THRESHOLD,
        'TRACK_MAX_AGE': profile.TRACK_MAX_AGE,
        'TRACK_MIN_HITS': profile.TRACK_MIN_HITS,
        'ENABLE_TRACKING': profile.ENABLE_TRACKING,
        'ENABLE_DUPLICATE_PREVENTION': profile.ENABLE_DUPLICATE_PREVENTION,
        'TRACKING_COOLDOWN': profile.TRACKING_COOLDOWN,
        'SAVE_FULL_FRAME': profile.SAVE_FULL_FRAME,
        'SAVE_FACE_CROP': profile.SAVE_FACE_CROP,
        'SAVE_EVIDENCE_AUTO': profile.SAVE_EVIDENCE_AUTO,
        'EVIDENCE_RETENTION_DAYS': profile.EVIDENCE_RETENTION_DAYS,
        'ENABLE_FACE_BLUR': profile.ENABLE_FACE_BLUR
    })

if __name__ == "__main__":
    print("Available Profiles:")
    list_profiles()
