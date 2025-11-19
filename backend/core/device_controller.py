import requests
import time
from backend.config import device_status, get_esp8266_ip, settings

# Debouncing
last_state_change = {}
debounce_delay = 1.0

# Request delay to prevent WiFi overload
request_delay = 0.05

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
    if device not in device_status:
        print(f"Unknown device: {device}")
        return False
    
    esp_ip = get_esp8266_ip()
        
    try:
        # If controlling motor, control both motor and buzzer together
        if device == "motor":
            requests.get(f'http://{esp_ip}/buzzer/{action}', timeout=0.3)
            time.sleep(0.05)
            requests.get(f'http://{esp_ip}/motor/{action}', timeout=0.3)
        else:
            # Regular on/off control for LEDs
            response = requests.get(
                f'http://{esp_ip}/{device}/{action}', 
                timeout=0.3
            )
        
        device_status[device] = "ON" if action == "on" else "OFF"
            
        return True
            
    except requests.exceptions.Timeout:
        print(f"Timeout controlling {device} - ESP8266 may be offline")
        return False
    except requests.exceptions.ConnectionError:
        print(f"Connection error to ESP8266 at {esp_ip} - device may be offline")
        return False
    except Exception as e:
        print(f"Error controlling {device}: {e}")
        return False

def control_devices_by_gesture(total_fingers):
    # Gesture Mapping: 0=All OFF | 1=Toggle Red | 2=Toggle Green | 3=Motor ON+LEDs OFF | 5=Both LEDs ON
    global last_total_fingers
    
    if not settings.get("detect_all_leds", True):
        return
    
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
                            if settings.get("detect_led1", True):
                                requests.get(f'http://{esp_ip}/led1/off', timeout=1.0)
                                time.sleep(request_delay)
                                device_status["led1"] = "OFF"
                            if settings.get("detect_led2", True):
                                requests.get(f'http://{esp_ip}/led2/off', timeout=1.0)
                                time.sleep(request_delay)
                                device_status["led2"] = "OFF"
                            if settings.get("detect_motor", True):
                                requests.get(f'http://{esp_ip}/motor/off', timeout=1.0)
                                time.sleep(request_delay)
                                device_status["motor"] = "OFF"
                        except Exception as e:
                            print(f"[ERROR] Turn all off failed: {e}")
                            pass
                    
                    elif total_fingers == 5:
                        # Open hand - Turn ON Red and Green LEDs only (motor stays OFF)
                        print("[GESTURE] Open Hand - Red & Green LEDs ON")
                        try:
                            esp_ip = get_esp8266_ip()
                            if settings.get("detect_led1", True):
                                requests.get(f'http://{esp_ip}/led1/on', timeout=1.0)
                                time.sleep(request_delay)
                                device_status["led1"] = "ON"
                            if settings.get("detect_led2", True):
                                requests.get(f'http://{esp_ip}/led2/on', timeout=1.0)
                                time.sleep(request_delay)
                                device_status["led2"] = "ON"
                            # Make sure motor is OFF
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
                                requests.get(f'http://{esp_ip}/led1/{action}', timeout=1.0)
                                time.sleep(request_delay)
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
                                requests.get(f'http://{esp_ip}/led2/{action}', timeout=1.0)
                                time.sleep(request_delay)
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
                                # Turn ON both buzzer and motor together
                                requests.get(f'http://{esp_ip}/buzzer/on', timeout=1.0)
                                time.sleep(request_delay)
                                requests.get(f'http://{esp_ip}/motor/on', timeout=1.0)
                                time.sleep(request_delay)
                                device_status["motor"] = "ON"
                                # Turn OFF both LEDs
                                if settings.get("detect_led1", True):
                                    requests.get(f'http://{esp_ip}/led1/off', timeout=1.0)
                                    time.sleep(request_delay)
                                    device_status["led1"] = "OFF"
                                if settings.get("detect_led2", True):
                                    requests.get(f'http://{esp_ip}/led2/off', timeout=1.0)
                                    time.sleep(request_delay)
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
                                requests.get(f'http://{esp_ip}/buzzer/off', timeout=1.0)
                                time.sleep(request_delay)
                                requests.get(f'http://{esp_ip}/motor/off', timeout=1.0)
                                time.sleep(request_delay)
                                device_status["motor"] = "OFF"
                            except Exception as e:
                                print(f"[ERROR] Motor & Buzzer off request failed: {e}")
                                pass
                    
                    last_state_change[device_key] = current_time
                    last_total_fingers = total_fingers
                    for key in state_buffer:
                        state_buffer[key].clear()

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