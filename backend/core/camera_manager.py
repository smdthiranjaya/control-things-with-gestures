import cv2
import time
import threading
from backend.config import (
    camera_sources, camera_detection_lock, camera_detection_in_progress,
    camera_detection_completed, settings, cap
)

def get_camera_sources():
    esp32_url = settings.get("esp32_cam_url", "http://10.168.182.148:81/stream")
    sources = {"ESP32-CAM": esp32_url}
    
    for index in [0, 1, 2]:
        try:
            sources[f"Computer Cam {index}"] = index
            print(f"Added camera at index {index}")
        except Exception as e:
            print(f"Error adding camera {index}: {e}")
    
    return sources

def detect_cameras():
    global camera_sources, camera_detection_completed, camera_detection_in_progress
    
    if not settings.get("auto_detect_cameras", True):
        return camera_sources
    
    if camera_detection_in_progress or camera_detection_completed:
        print("Returning cached camera sources")
        return camera_sources
    
    with camera_detection_lock:
        if not camera_detection_completed: 
            try:
                camera_detection_in_progress = True
                print("Camera detection requested")
                camera_sources = get_camera_sources()
                camera_detection_completed = True
                return camera_sources
            except Exception as e:
                print(f"Error in camera detection: {e}")
                import traceback
                traceback.print_exc()
                return camera_sources 
            finally:
                camera_detection_in_progress = False
        else:
            return camera_sources

def initialize_cameras_background():
    global camera_sources, camera_detection_completed
    
    if camera_detection_completed:
        return
        
    try:
        time.sleep(2)
        print("Starting background camera detection...")
        with camera_detection_lock:
            if not camera_detection_completed: 
                temp_sources = get_camera_sources()
                if temp_sources:
                    camera_sources = temp_sources
                camera_detection_completed = True
                print(f"Background camera detection complete. Available: {list(camera_sources.keys())}")
    except Exception as e:
        print(f"Error in background camera detection: {e}")
        import traceback
        traceback.print_exc()

def open_camera(source, current_source):
    global cap
    
    try:
        if current_source == "ESP32-CAM":
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
            cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
            cap.set(cv2.CAP_PROP_SATURATION, 0.55)
        else:
            cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(source)
            
            if isinstance(source, int) and cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        if cap is not None and cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print(f"Camera {current_source} opened successfully")
                return True
            else:
                print(f"Camera {current_source} opened but cannot read frames")
                cap.release()
                cap = None
                return False
        else:
            print(f"Failed to open camera {current_source} (may be in use by another app)")
            return False
            
    except Exception as e:
        print(f"Exception opening camera: {e}")
        cap = None
        return False

def release_camera():
    global cap
    
    if cap is not None:
        try:
            cap.release()
            print("Camera released")
        except Exception as e:
            print(f"Error releasing camera: {e}")
        cap = None

def is_camera_open():
    return cap is not None and cap.isOpened()

def read_frame():
    if cap is None:
        return False, None
    
    try:
        return cap.read()
    except Exception as e:
        print(f"Error reading frame: {e}")
        return False, None