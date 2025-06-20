"""
Camera management for video capture
"""
import cv2
import time
import threading
from config import cap, camera_sources, camera_detection_lock, camera_detection_in_progress

def detect_cameras():
    """Detect and verify available cameras"""
    global camera_sources
    
    camera_detection_in_progress = True
    
    # Make a copy of the current sources for reference
    current_sources = camera_sources.copy()
    
    try:
        # First check for local cameras (index-based)
        local_cameras = {}
        for i in range(3):  # Try first 3 camera indices
            cap_test = cv2.VideoCapture(i)
            cap_test.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 1000)  # 1 second timeout
            
            ret = cap_test.grab()  # Just grab one frame to verify
            if ret:
                local_cameras[f"Computer Cam {i}"] = i
                print(f"Verified working camera at index {i}")
            cap_test.release()
        
        # Include ESP32-CAM if it was in the original sources
        if "ESP32-CAM" in current_sources:
            esp32_url = current_sources["ESP32-CAM"]
            # Don't attempt connection here, just add it back
            local_cameras["ESP32-CAM"] = esp32_url
            print(f"Added ESP32-CAM option (will validate when used): {esp32_url}")
        
        # Update the global camera sources
        camera_sources = local_cameras
        
        print(f"Background camera detection complete. Available: {list(camera_sources.keys())}")
        
    except Exception as e:
        print(f"Error detecting cameras: {e}")
    finally:
        camera_detection_in_progress = False
    
    return camera_sources

def initialize_cameras_background():
    """Start camera detection in background"""
    with camera_detection_lock:
        print("Starting background camera detection...")
        detect_cameras()

def is_camera_open():
    """Check if the camera is currently open"""
    return cap is not None and cap.isOpened()

def release_camera():
    """Release the camera resource"""
    global cap
    if cap is not None:
        try:
            cap.release()
            print("Camera released")
        except Exception as e:
            print(f"Error releasing camera: {e}")
        finally:
            cap = None

def read_frame():
    """Read a frame from the camera with error handling"""
    if cap is None or not cap.isOpened():
        return False, None
    
    try:
        return cap.read()
    except Exception as e:
        print(f"Error reading frame: {e}")
        return False, None

def open_camera(source, source_name):
    """Open a camera with the specified source"""
    global cap
    
    # Release any existing camera
    release_camera()
    
    # Limit to 2 attempts only
    max_attempts = 1  # Just 1 attempt to reduce messages
    
    try:
        # Handle different camera source types
        if source_name.startswith("Computer Cam "):
            # Local camera index
            try:
                # Extract the index number from the name
                index = int(source_name.split(" ")[-1])
                print(f"Extracted camera index {index} from {source_name}")
                
                for attempt in range(1, max_attempts + 1):
                    print(f"Opening computer camera at index {index} (attempt {attempt}/{max_attempts})")
                    cap = cv2.VideoCapture(index)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)
                    
                    if cap.isOpened():
                        # Verify by reading a frame
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            print(f"Camera {source_name} opened successfully")
                            return True
                
                # If we get here, the camera didn't open properly
                if cap is not None:
                    cap.release()
                    cap = None
                print(f"Failed to open camera {source_name}")
                return False
                
            except Exception as e:
                print(f"Error extracting camera index: {e}")
                return False
                
        elif source_name == "ESP32-CAM":
            # IP camera (ESP32-CAM)
            for attempt in range(1, max_attempts + 1):
                print(f"Opening ESP32-CAM stream (attempt {attempt}/{max_attempts})")
                cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
                
                if cap.isOpened():
                    print(f"ESP32-CAM stream opened successfully")
                    return True
            
            # If we get here, the camera didn't open properly
            if cap is not None:
                cap.release()
                cap = None
            print(f"Failed to open camera {source_name}")
            return False
            
        else:
            # Unknown camera type
            print(f"Unknown camera source type: {source_name}")
            return False
            
    except Exception as e:
        print(f"Error opening camera {source_name}: {e}")
        if cap is not None:
            cap.release()
            cap = None
        return False