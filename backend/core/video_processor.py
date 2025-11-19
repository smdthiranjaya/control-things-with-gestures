"""
Video processing and streaming functionality
"""
import cv2
import numpy as np
import time
from collections import deque
from backend.config import (
    camera_sources, settings, last_settings_change, settings_cooldown,
    device_status
)
from backend.core.camera_manager import open_camera, release_camera, is_camera_open, read_frame
from backend.core.gesture_detector import process_frame_for_gestures
from backend.core.device_controller import control_devices_by_gesture

def create_error_frame(message):
    """Create an error frame with a message"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(img, message, (50, 240), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return img

def generate_frames():
    """Video streaming generator with gesture detection"""
    
    # Ensure we have at least one camera source
    if not camera_sources:
        print("No camera sources available")
        while True:
            frame = create_error_frame("No cameras detected")
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.1)
    
    current_source = settings.get("camera_source", list(camera_sources.keys())[0] if camera_sources else "ESP32-CAM")
    source = camera_sources.get(current_source)
    
    # Track the current source
    current_cap_source = None
    
    # Time-based cooldown for camera reconnection
    if time.time() - last_settings_change < settings_cooldown:
        time.sleep(0.1)
    
    # Initialize camera
    camera_initialized = False
    initialization_attempts = 0
    max_init_attempts = 5
    
    while not camera_initialized:
        try:
            # Check if camera needs initialization or source changed
            if not is_camera_open() or current_cap_source != current_source:
                if initialization_attempts == 0:
                    print(f"Initializing camera source: {current_source}")
                initialization_attempts += 1
                
                # Give up after max attempts and show error frame
                if initialization_attempts > max_init_attempts:
                    print(f"⚠ Failed to connect to {current_source} - showing error screen")
                    print("  Try selecting a different camera from the web interface")
                    camera_initialized = True  # Stop trying
                    current_cap_source = None  # Mark as failed
                    break
                
                if is_camera_open():
                    release_camera()
                    time.sleep(0.5) 
                
                # Open new camera
                if open_camera(source, current_source):
                    current_cap_source = current_source
                    camera_initialized = True
                    initialization_attempts = 0
                else:
                    time.sleep(1)
            else:
                camera_initialized = True
        except Exception as e:
            print(f"Error initializing camera: {e}")
            time.sleep(1)
    
    # Frame error counter for reconnection logic
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    # Frame skipping for performance
    frame_count = 0
    last_hand_data = None
    
    # FPS counter
    fps_start_time = time.time()
    fps_frame_count = 0
    fps = 0
    
    while True:
        try:
            # Check if camera source has changed
            if current_source != settings.get("camera_source"):
                print(f"Camera source changed from {current_source} to {settings.get('camera_source')}")
                current_source = settings.get("camera_source")
                source = camera_sources.get(current_source)
                release_camera()
                current_cap_source = None
                initialization_attempts = 0  # Reset attempts counter
                camera_initialized = False  # Reinitialize with new source
                break  # Exit loop to reinitialize
            
            # If camera failed to initialize, show error frame
            if current_cap_source is None:
                frame = create_error_frame(f"Camera '{current_source}' unavailable")
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.1)
                continue
            
            # Try to read a frame
            success, frame = read_frame()
            
            if not success:
                consecutive_errors += 1
                
                if consecutive_errors >= max_consecutive_errors:
                    print(f"⚠ Camera disconnected, attempting to reconnect...")
                    release_camera()
                    current_cap_source = None
                    consecutive_errors = 0
                    time.sleep(1) 
                    continue
                    
                # Provide an error frame
                frame = create_error_frame("Camera connection error")
            else:
                # Reset error counter on successful frame
                consecutive_errors = 0
                frame_count += 1
                
                frame = cv2.flip(frame, 1)
                
                # Light enhancement for ESP32-CAM (minimal processing)
                if current_source == "ESP32-CAM":
                    # Only basic brightness/contrast adjustment
                    frame = cv2.convertScaleAbs(frame, alpha=1.05, beta=5)
                
                # Get performance settings
                skip_frames = settings.get("skip_frames", 1)
                processing_scale = settings.get("processing_scale", 0.5)
                
                # Only process gesture detection on certain frames for performance
                if settings.get("gesture_detection_enabled", True) and (frame_count % skip_frames == 0):
                    # Downscale frame for faster processing
                    height, width = frame.shape[:2]
                    small_frame = cv2.resize(frame, (int(width * processing_scale), int(height * processing_scale)))
                    
                    # Process the smaller frame
                    small_frame, hand_data, multi_hand_landmarks, multi_handedness = process_frame_for_gestures(small_frame)
                    
                    # Scale landmarks back to original size if detected
                    if hand_data:
                        scale_factor = 1.0 / processing_scale
                        hand_data['landmarks'] = [(int(x * scale_factor), int(y * scale_factor)) 
                                                  for x, y in hand_data['landmarks']]
                        last_hand_data = hand_data
                    
                    # Draw on full-size frame for display
                    if last_hand_data and settings.get("show_landmarks", True):
                        # Draw landmarks on full frame
                        for landmark in last_hand_data['landmarks']:
                            cv2.circle(frame, landmark, 5, (0, 255, 0), -1)
                else:
                    # Use last detected hand data for gesture control
                    hand_data = last_hand_data
                
                if hand_data:
                    total_fingers = hand_data['total_fingers']
                    
                    # New gesture-based control system
                    control_devices_by_gesture(total_fingers)
                    
                    # Draw finger count on frame
                    cv2.putText(frame, f"Fingers: {total_fingers}", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Calculate and display FPS
            fps_frame_count += 1
            if fps_frame_count >= 30:  # Update FPS every 30 frames
                fps_end_time = time.time()
                fps = fps_frame_count / (fps_end_time - fps_start_time)
                fps_start_time = fps_end_time
                fps_frame_count = 0
            
            # Draw FPS on frame
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Convert frame to JPEG with balanced quality
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)
            if not ret:
                print("Error encoding frame to JPEG")
                continue
                
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                  
        except Exception as e:
            print(f"Error in generate_frames: {e}")
            time.sleep(0.5) 
            
            # Provide an error frame
            error_frame = create_error_frame(f"Error: {str(e)}")
            
            try:
                ret, buffer = cv2.imencode('.jpg', error_frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as inner_e:
                print(f"Error creating error frame: {inner_e}")
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + b'\x00\x00\x00' + b'\r\n')