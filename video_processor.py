"""
Video processing and streaming functionality
"""
import cv2
import numpy as np
import time
from collections import deque
from config import (
    camera_sources, settings, last_settings_change, settings_cooldown,
    prev_fingers, prev_finger_angle, prev_hand_angle, smoothing_factor,
    finger_angle_buffer, hand_angle_buffer, motor_values, device_status
)
from camera_manager import open_camera, release_camera, is_camera_open, read_frame
from gesture_detector import (
    process_frame_for_gestures, draw_rotation_indicators, draw_bulb_indicator
)
from device_controller import (
    control_led_devices, control_bulb_voltage, control_finger_motor,
    control_hand_motor, reset_bulb_when_no_hand
)

def create_error_frame(message):
    """Create an error frame with a message"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(img, message, (50, 240), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return img

def generate_frames():
    """Video streaming generator with gesture detection"""
    global prev_fingers, prev_finger_angle, prev_hand_angle
    
    # Initialize bulb_voltage if not present
    if "bulb_voltage" not in motor_values:
        motor_values["bulb_voltage"] = 0
    if "bulb" not in device_status:
        device_status["bulb"] = "OFF"
    
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
                
                frame = cv2.flip(frame, 1)
                
                # Process frame with gesture detection
                frame, hand_data, multi_hand_landmarks, multi_handedness = process_frame_for_gestures(frame)
                
                if hand_data:
                    landmarks = hand_data['landmarks']
                    fingers = hand_data['fingers']
                    finger_angle = hand_data['finger_angle']
                    hand_angle = hand_data['hand_angle']
                    total_fingers = hand_data['total_fingers']
                    
                    # Device control for LEDs and main motor
                    control_led_devices(fingers, prev_fingers)
                    prev_fingers = fingers.copy()
                    
                    # Bulb voltage control based on total fingers raised
                    control_bulb_voltage(total_fingers)
                    
                    # Finger rotation for finger motor
                    if finger_angle is not None:
                        finger_angle_buffer.append(finger_angle)
                        avg_finger_angle = sum(finger_angle_buffer) / len(finger_angle_buffer)
                        smooth_finger_angle = prev_finger_angle * smoothing_factor + avg_finger_angle * (1 - smoothing_factor)
                        prev_finger_angle = smooth_finger_angle
                        
                        motor_value = min(100, max(0, smooth_finger_angle * 100 / 120))
                        control_finger_motor(motor_value)
                    
                    # Wrist rotation for hand motor
                    if hand_angle is not None:
                        hand_angle_buffer.append(hand_angle)
                        avg_hand_angle = sum(hand_angle_buffer) / len(hand_angle_buffer)
                        smooth_hand_angle = prev_hand_angle * smoothing_factor + avg_hand_angle * (1 - smoothing_factor)
                        prev_hand_angle = smooth_hand_angle
                        
                        motor_value = min(100, max(0, smooth_hand_angle * 100 / 180))
                        control_hand_motor(motor_value)
                    
                    # Draw rotation indicators if enabled
                    if (settings.get("show_finger_rotation_indicator", True) or 
                        settings.get("show_hand_rotation_indicator", True)):
                        draw_rotation_indicators(frame, landmarks, 
                                                motor_values["finger_motor"],
                                                motor_values["hand_motor"])
                    
                    # Draw bulb indicator if enabled
                    if settings.get("show_bulb_indicator", True) and settings.get("detect_bulb", True):
                        draw_bulb_indicator(frame, landmarks, motor_values["bulb_voltage"])
                
                else:
                    # No hand detected - reset bulb voltage and fingers
                    reset_bulb_when_no_hand()
                    prev_fingers = [0, 0, 0, 0, 0]
            
            # Convert frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
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