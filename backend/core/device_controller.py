import requests
import time
from requests.adapters import HTTPAdapter
from backend.config import device_status, get_esp8266_ip, settings

# Create persistent HTTP session with keep-alive and aggressive retry
session = requests.Session()
session.headers.update({'Connection': 'keep-alive'})

# Configure adapter for faster connection handling
adapter = HTTPAdapter(
    pool_connections=1,
    pool_maxsize=1,
    max_retries=0,  # No retries - fail fast
    pool_block=False
)
session.mount('http://', adapter)

# Timeout tuple: (connect_timeout, read_timeout) in seconds
# Use longer timeout for initial connection, but session reuse keeps it fast
REQUEST_TIMEOUT = (3.0, 0.1)  # 3s to connect (first time), 100ms to read

# Connection warming - establish connection on module load
def warm_connection():
    """Pre-establish TCP connection to ESP8266"""
    try:
        esp_ip = get_esp8266_ip()
        session.get(f'http://{esp_ip}/status', timeout=(2.0, 2.0))  # Allow time for initial connection
        print(f"[CONNECTION] Warmed up connection to {esp_ip}")
    except Exception as e:
        print(f"[WARNING] Could not warm connection: {e}")

# Warm connection on import
try:
    warm_connection()
except:
    pass

# Debouncing
last_state_change = {}
debounce_delay = 1.0

# Keep-alive ping
last_keepalive = time.time()
keepalive_interval = 5.0  # Ping every 5 seconds to keep connection alive

def keepalive_ping():
    """Send periodic ping to keep TCP connection alive"""
    global last_keepalive
    current = time.time()
    if current - last_keepalive > keepalive_interval:
        try:
            esp_ip = get_esp8266_ip()
            session.get(f'http://{esp_ip}/status', timeout=REQUEST_TIMEOUT)
            last_keepalive = current
        except:
            pass  # Ignore errors in background ping

# State confirmation
state_buffer = {
    "all_leds": [],
    "led1": [],
    "led2": [],
    "motor": []
}
confirmation_frames = 5

last_total_fingers = 0

def control_device_direct(device, action):
    """Control device - motor controls both motor and buzzer together"""
    start_time = time.time()
    
    if device not in device_status:
        print(f"Unknown device: {device}")
        return False
    
    esp_ip = get_esp8266_ip()
    print(f"\n[DEBUG {time.strftime('%H:%M:%S.%f')[:-3]}] Control Request: {device} -> {action}")
        
    try:
        # If controlling motor, control both motor and buzzer together
        if device == "motor":
            req1_start = time.time()
            session.get(f'http://{esp_ip}/buzzer/{action}', timeout=REQUEST_TIMEOUT)
            req1_time = (time.time() - req1_start) * 1000
            print(f"  ├─ Buzzer request: {req1_time:.1f}ms")
            
            req2_start = time.time()
            session.get(f'http://{esp_ip}/motor/{action}', timeout=REQUEST_TIMEOUT)
            req2_time = (time.time() - req2_start) * 1000
            print(f"  ├─ Motor request: {req2_time:.1f}ms")
        else:
            # Regular on/off control for LEDs
            req_start = time.time()
            response = session.get(
                f'http://{esp_ip}/{device}/{action}', 
                timeout=REQUEST_TIMEOUT
            )
            req_time = (time.time() - req_start) * 1000
            print(f"  ├─ {device} request: {req_time:.1f}ms (status: {response.status_code})")
        
        device_status[device] = "ON" if action == "on" else "OFF"
        
        total_time = (time.time() - start_time) * 1000
        print(f"  └─ Total time: {total_time:.1f}ms\n")
            
        return True
            
    except requests.exceptions.Timeout:
        elapsed = (time.time() - start_time) * 1000
        print(f"  └─ ⚠ TIMEOUT after {elapsed:.1f}ms controlling {device}\n")
        return False
    except requests.exceptions.ConnectionError:
        elapsed = (time.time() - start_time) * 1000
        print(f"  └─ ⚠ CONNECTION ERROR after {elapsed:.1f}ms to {esp_ip}\n")
        return False
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"  └─ ⚠ ERROR after {elapsed:.1f}ms: {e}\n")
        return False

def control_devices_by_gesture(total_fingers):
    # Gesture Mapping: 0=All OFF | 1=Toggle Red | 2=Toggle Green | 3=Motor ON+LEDs OFF | 5=Both LEDs ON
    global last_total_fingers
    
    if not settings.get("detect_all_leds", True):
        return
    
    # Keep connection alive
    keepalive_ping()
    
    gesture_start = time.time()
    current_time = time.time()
    
    # Use unique keys for each gesture type
    gesture_keys = {
        0: "fist",
        1: "one_finger",
        2: "two_fingers",
        3: "three_fingers",
        5: "open_hand"
    }
    
    device_key = gesture_keys.get(total_fingers, f"gesture_{total_fingers}")
    
    if device_key not in state_buffer:
        state_buffer[device_key] = []
    
    state_buffer[device_key].append(total_fingers)
    
    # Keep only last N frames for this specific gesture
    if len(state_buffer[device_key]) > confirmation_frames:
        state_buffer[device_key].pop(0)
    
    # Only trigger if we have enough frames and they're all the same
    if len(state_buffer[device_key]) == confirmation_frames:
        if all(f == total_fingers for f in state_buffer[device_key]):
            # Check debounce and if gesture changed
            if total_fingers != last_total_fingers:
                last_change = last_state_change.get(device_key, 0)
                if current_time - last_change >= debounce_delay:
                    
                    # Execute gesture command
                    if total_fingers == 0:
                        # Closed fist - Turn OFF all components (Red LED, Green LED, Motor)
                        print("[GESTURE] Closed Fist - All Components OFF")
                        try:
                            esp_ip = get_esp8266_ip()
                            # Single batch request to turn off all devices
                            session.get(f'http://{esp_ip}/batch?led1=off&led2=off&motor=off&buzzer=off', timeout=REQUEST_TIMEOUT)
                            device_status["led1"] = "OFF"
                            device_status["led2"] = "OFF"
                            device_status["motor"] = "OFF"
                        except Exception as e:
                            print(f"[ERROR] Turn all off failed: {e}")
                            pass
                    
                    elif total_fingers == 5:
                        # Open hand - Turn ON Red and Green LEDs only (motor stays OFF)
                        print("[GESTURE] Open Hand - Red & Green LEDs ON")
                        try:
                            esp_ip = get_esp8266_ip()
                            # Single batch request to turn on both LEDs
                            session.get(f'http://{esp_ip}/batch?led1=on&led2=on', timeout=REQUEST_TIMEOUT)
                            device_status["led1"] = "ON"
                            device_status["led2"] = "ON"
                            device_status["motor"] = "OFF"
                        except Exception as e:
                            print(f"[ERROR] Turn LEDs on failed: {e}")
                            pass
                    
                    elif total_fingers == 1:
                        if settings.get("detect_led1", True):
                            current_state = device_status.get("led1", "OFF")
                            new_state = "OFF" if current_state == "ON" else "ON"
                            action = "on" if new_state == "ON" else "off"
                            print(f"[GESTURE] 1 Finger - Toggle Red LED: {new_state}")
                            try:
                                esp_ip = get_esp8266_ip()
                                session.get(f'http://{esp_ip}/led1/{action}', timeout=REQUEST_TIMEOUT)
                                device_status["led1"] = new_state
                            except Exception as e:
                                print(f"[ERROR] LED1 request failed: {e}")
                                pass
                    
                    elif total_fingers == 2:
                        if settings.get("detect_led2", True):
                            current_state = device_status.get("led2", "OFF")
                            new_state = "OFF" if current_state == "ON" else "ON"
                            action = "on" if new_state == "ON" else "off"
                            print(f"[GESTURE] 2 Fingers - Toggle Green LED: {new_state}")
                            try:
                                esp_ip = get_esp8266_ip()
                                session.get(f'http://{esp_ip}/led2/{action}', timeout=REQUEST_TIMEOUT)
                                device_status["led2"] = new_state
                            except Exception as e:
                                print(f"[ERROR] LED2 request failed: {e}")
                                pass
                    
                    elif total_fingers == 3:
                        # 3 fingers - Turn ON motor and buzzer together, turn OFF both LEDs
                        if settings.get("detect_motor", True):
                            print("[GESTURE] 3 Fingers - Motor & Buzzer ON, LEDs OFF")
                            try:
                                esp_ip = get_esp8266_ip()
                                # Single batch request: motor+buzzer ON, both LEDs OFF
                                session.get(f'http://{esp_ip}/batch?motor=on&buzzer=on&led1=off&led2=off', timeout=REQUEST_TIMEOUT)
                                device_status["motor"] = "ON"
                                device_status["led1"] = "OFF"
                                device_status["led2"] = "OFF"
                            except Exception as e:
                                print(f"[ERROR] 3-finger gesture failed: {e}")
                                pass
                    
                    else:
                        # Any other finger count - turn motor and buzzer OFF together if they were ON
                        if settings.get("detect_motor", True) and device_status.get("motor") == "ON":
                            print("[GESTURE] Motor & Buzzer OFF (gesture changed)")
                            try:
                                esp_ip = get_esp8266_ip()
                                # Single batch request to turn off motor and buzzer
                                session.get(f'http://{esp_ip}/batch?motor=off&buzzer=off', timeout=REQUEST_TIMEOUT)
                                device_status["motor"] = "OFF"
                            except Exception as e:
                                print(f"[ERROR] Motor & Buzzer off request failed: {e}")
                                pass
                    
                    last_state_change[device_key] = current_time
                    last_total_fingers = total_fingers
                    for key in state_buffer:
                        state_buffer[key].clear()
                    
                    gesture_time = (time.time() - gesture_start) * 1000
                    print(f"[TIMING] Gesture {total_fingers} execution: {gesture_time:.1f}ms")

def test_esp8266_connection(ip=None):
    test_ip = ip or get_esp8266_ip()
    try:
        response = requests.get(f'http://{test_ip}/status', timeout=2)
        return True, "Connected successfully"
    except requests.exceptions.Timeout:
        return False, "Connection timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection failed"
    except Exception as e:
        return False, str(e)