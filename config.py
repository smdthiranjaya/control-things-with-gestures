"""
Configuration and global state management
"""
import threading
from collections import deque

# Disable camera auto-detection on startup
DISABLE_CAMERA_DETECTION = True

# Threading locks and flags
camera_detection_lock = threading.Lock()
camera_detection_in_progress = False
camera_detection_completed = False

# Initialize with just ESP32-CAM
camera_sources = {"ESP32-CAM": "http://192.168.1.25:81/stream"}

# Gesture detection state
fingers = [0, 0, 0, 0, 0] 
prev_fingers = [0, 0, 0, 0, 0]
prev_finger_angle = 0
prev_hand_angle = 0
smoothing_factor = 0.85
finger_angle_buffer = deque(maxlen=5)
hand_angle_buffer = deque(maxlen=5)

# Timing controls
last_settings_change = 0
settings_cooldown = 2.0 

# Network configuration
ESP8266_IP = "192.168.1.15"

# Device status
device_status = {
    "led1": "OFF",
    "led2": "OFF",
    "led3": "OFF",
    "led4": "OFF", 
    "led5": "OFF",  
    "buzzer": "OFF",
    "motor": "OFF",
    "finger_motor": "OFF",
    "hand_motor": "OFF",
    "bulb": "OFF",
}

# Motor values (0-100%)
motor_values = {
    "finger_motor": 0,
    "hand_motor": 0,
    "bulb_voltage": 0
}

# Application settings
settings = {
    "camera_source": "ESP32-CAM",
    "gesture_detection_enabled": True,
    "show_landmarks": True,
    "finger_rotation_enabled": False,
    "hand_rotation_enabled": False,   
    "show_finger_rotation_indicator": False, 
    "show_hand_rotation_indicator": False,  
    "detect_all_leds": True,
    "detect_led1": True,
    "detect_led2": True,
    "detect_led3": True,
    "detect_led4": True,  
    "detect_led5": True, 
    "detect_buzzer": False,
    "detect_motor": False, 
    "detect_bulb": False,
    "show_bulb_indicator": False,
    "detect_finger_motor": False, 
    "detect_hand_motor": False,
    "auto_detect_cameras": False,
    "esp32_cam_url": "http://192.168.1.25:81/stream",
    "esp8266_ip": "192.168.1.15",    
}

# Camera management
cap = None

def get_esp8266_ip():
    """Get ESP8266 IP from settings"""
    return settings.get("esp8266_ip", "192.168.1.15")