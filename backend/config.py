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

# Network configuration - Can be updated via web interface
# Using mDNS hostnames - no need to change IPs on different networks!
ESP8266_IP = "esp8266.local"
ESP32_CAM_URL = "http://esp32cam.local:81/stream"

# Initialize with ESP32-CAM URL from constant
camera_sources = {"ESP32-CAM": ESP32_CAM_URL}

# Gesture detection state
fingers = [0, 0, 0, 0, 0]

# Timing controls
last_settings_change = 0
settings_cooldown = 2.0 

# Device status
device_status = {
    "led1": "OFF",  # Red LED
    "led2": "OFF",  # Green LED
    "motor": "OFF", # Motor & Buzzer
}

# Application settings
settings = {
    "camera_source": "Computer Cam 0", 
    "gesture_detection_enabled": True,
    "show_landmarks": True,
    "processing_scale": 0.5,
    "skip_frames": 1,
    "gesture_debounce_delay": 0.5,
    "motor_update_interval": 0.3,
    "detect_all_leds": True,
    "detect_led1": True,
    "detect_led2": True,
    "detect_motor": True,
    "auto_detect_cameras": False,
    "esp32_cam_url": ESP32_CAM_URL,
    "esp8266_ip": ESP8266_IP,    
}

# Camera management
cap = None

def get_esp8266_ip():
    """Get ESP8266 hostname from settings (mDNS)"""
    return settings.get("esp8266_ip", "esp8266.local")