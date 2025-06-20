"""
Device control and ESP8266 communication
"""
import requests
import time
from config import device_status, motor_values, get_esp8266_ip, settings

# Track last connection failure to avoid excessive retries
# Make these variables truly global for the module
_last_connection_failure = 0
_connection_failure_cooldown = 5 
_last_connection_error_message = ""

def control_device_direct(device, action):
    """Control device directly without going through the API route"""
    global _last_connection_failure, _last_connection_error_message
    
    if device not in device_status:
        print(f"Unknown device: {device}")
        return False
    
    # Check if we're in cooldown period after a connection failure
    current_time = time.time()
    if current_time - _last_connection_failure < _connection_failure_cooldown:
        # Update device status locally even if we can't reach the device
        # This prevents UI inconsistency and excessive retries
        device_status[device] = "ON" if action == "on" else "OFF"
        if device in motor_values and action == "off":
            motor_values[device] = 0
        return True
    
    esp_ip = get_esp8266_ip()
    
    try:
        # For motors with voltage control
        if device in ["finger_motor", "hand_motor"] and action == "on":
            voltage = motor_values.get(device, 0)
            response = requests.get(
                f'http://{esp_ip}/{device}/set/{voltage}', 
                timeout=0.3
            )
            print(f"Sent {device} voltage: {voltage}%")
        else:
            # Regular on/off control
            response = requests.get(
                f'http://{esp_ip}/{device}/{action}', 
                timeout=0.3
            )
        
        device_status[device] = "ON" if action == "on" else "OFF"
        
        if device in motor_values and action == "off":
            motor_values[device] = 0
            
        return True
            
    except requests.exceptions.Timeout:
        if current_time - _last_connection_failure > _connection_failure_cooldown:
            print(f"Timeout controlling {device} - ESP8266 may be offline")
            _last_connection_failure = current_time
            _last_connection_error_message = f"Timeout controlling {device}"
        
        # Update device status locally even if we can't reach the device
        device_status[device] = "ON" if action == "on" else "OFF"
        if device in motor_values and action == "off":
            motor_values[device] = 0
        return True
        
    except requests.exceptions.ConnectionError:
        if current_time - _last_connection_failure > _connection_failure_cooldown:
            print(f"Connection error to ESP8266 at {esp_ip} - device may be offline")
            _last_connection_failure = current_time
            _last_connection_error_message = f"Connection error to ESP8266"
        
        # Update device status locally even if we can't reach the device
        device_status[device] = "ON" if action == "on" else "OFF"
        if device in motor_values and action == "off":
            motor_values[device] = 0
        return True
        
    except Exception as e:
        if current_time - _last_connection_failure > _connection_failure_cooldown:
            print(f"Error controlling {device}: {e}")
            _last_connection_failure = current_time
            _last_connection_error_message = str(e)
            
        # Update device status locally even if we can't reach the device
        device_status[device] = "ON" if action == "on" else "OFF"
        if device in motor_values and action == "off":
            motor_values[device] = 0
        return True

def control_led_devices(fingers, prev_fingers):
    """Control LED devices based on finger gestures"""
    if not settings.get("detect_all_leds", True):
        return
    
    # Control individual LEDs (LED1-LED5)
    for i in range(5):  # Updated to handle all 5 LEDs
        if fingers[i] != prev_fingers[i]:
            # Maps finger index to device name
            device_map = ["led1", "led2", "led3", "led4", "led5"]
            device = device_map[i]
            
            if settings.get(f"detect_{device}", True):
                action = "on" if fingers[i] == 1 else "off"
                print(f"Gesture detected: Controlling {device} -> {action}")
                control_device_direct(device, action)
    
    # Control buzzer based on all 5 fingers
    if settings.get("detect_buzzer", True):
        # Buzzer ON when all 5 fingers are raised
        all_fingers_raised = all(fingers)
        # Buzzer OFF when all fingers are closed (fist)
        all_fingers_closed = not any(fingers)
        
        # Only send command if the state has changed
        if all_fingers_raised and device_status["buzzer"] != "ON":
            print("Gesture detected: All fingers raised -> Buzzer ON")
            control_device_direct("buzzer", "on")
        elif all_fingers_closed and device_status["buzzer"] != "OFF":
            print("Gesture detected: Fist made -> Buzzer OFF")
            control_device_direct("buzzer", "off")

def control_bulb_voltage(total_fingers):
    """Control bulb voltage based on total fingers raised"""
    global _last_connection_failure 
    
    if not settings.get("detect_bulb", True):
        return
    
    # Map 0-5 fingers to 0-100% voltage
    bulb_voltage = (total_fingers * 100) // 5
    
    if motor_values["bulb_voltage"] != bulb_voltage:
        motor_values["bulb_voltage"] = bulb_voltage
        
        # Control bulb through ESP8266
        esp_ip = get_esp8266_ip()
        if bulb_voltage > 0:
            device_status["bulb"] = "ON"
            
            # Check if we're in cooldown period after a connection failure
            current_time = time.time()
            if current_time - _last_connection_failure < _connection_failure_cooldown:
                return
                
            try:
                response = requests.get(
                    f'http://{esp_ip}/bulb/set/{bulb_voltage}', 
                    timeout=0.5
                )
            except Exception as e:
                _last_connection_failure = time.time()
                print(f"Error setting bulb voltage: {e}")
        else:
            device_status["bulb"] = "OFF"
            control_device_direct("bulb", "off")

def control_finger_motor(motor_value):
    """Control finger motor with voltage"""
    global _last_connection_failure 
    
    if not (settings.get("finger_rotation_enabled", True) and 
            settings.get("detect_finger_motor", True)):
        return
    
    if abs(motor_values["finger_motor"] - motor_value) > 1:
        motor_values["finger_motor"] = int(motor_value)
        # Send voltage to ESP8266
        if motor_value > 0:
            device_status["finger_motor"] = "ON"
            
            # Check if we're in cooldown period
            current_time = time.time()
            if current_time - _last_connection_failure < _connection_failure_cooldown:
                return
                
            try:
                esp_ip = get_esp8266_ip()
                response = requests.get(
                    f'http://{esp_ip}/finger_motor/set/{int(motor_value)}', 
                    timeout=0.3
                )
                print(f"Finger motor set to {int(motor_value)}%")
            except Exception as e:
                _last_connection_failure = time.time()
                print(f"Error setting finger motor voltage: {e}")
        else:
            device_status["finger_motor"] = "OFF"
            control_device_direct("finger_motor", "off")

def control_hand_motor(motor_value):
    """Control hand motor with voltage"""
    global _last_connection_failure 
    
    if not (settings.get("hand_rotation_enabled", True) and 
            settings.get("detect_hand_motor", True)):
        return
    
    if abs(motor_values["hand_motor"] - motor_value) > 1:
        motor_values["hand_motor"] = int(motor_value)
        # Send voltage to ESP8266
        if motor_value > 0:
            device_status["hand_motor"] = "ON"
            
            # Check if we're in cooldown period
            current_time = time.time()
            if current_time - _last_connection_failure < _connection_failure_cooldown:
                return
                
            try:
                esp_ip = get_esp8266_ip()
                response = requests.get(
                    f'http://{esp_ip}/hand_motor/set/{int(motor_value)}', 
                    timeout=0.3
                )
                print(f"Hand motor set to {int(motor_value)}%")
            except Exception as e:
                _last_connection_failure = time.time()
                print(f"Error setting hand motor voltage: {e}")
        else:
            device_status["hand_motor"] = "OFF"
            control_device_direct("hand_motor", "off")

def reset_bulb_when_no_hand():
    """Reset bulb voltage to 0 when no hand is detected"""
    if settings.get("detect_bulb", True):
        if motor_values["bulb_voltage"] != 0:
            motor_values["bulb_voltage"] = 0
            device_status["bulb"] = "OFF"
            try:
                control_device_direct("bulb", "off")
            except Exception as e:
                print(f"Error turning off bulb: {e}")

def test_esp8266_connection(ip=None):
    """Test connection to ESP8266"""
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

def set_device_voltage(device, voltage):
    """Set voltage for motor devices"""
    global _last_connection_failure 
    
    if device not in ["finger_motor", "hand_motor", "bulb"]:
        return False, "Invalid device"
    
    voltage = max(0, min(100, voltage)) 
    motor_values[device if device != "bulb" else "bulb_voltage"] = voltage
    
    current_time = time.time()
    if current_time - _last_connection_failure < _connection_failure_cooldown:
        device_status[device] = "ON" if voltage > 0 else "OFF"
        return True, f"Device status updated locally (ESP8266 in cooldown)"
    
    esp_ip = get_esp8266_ip()
    
    try:
        if voltage > 0:
            device_status[device] = "ON"
            response = requests.get(f'http://{esp_ip}/{device}/set/{voltage}', timeout=0.5)
            print(f"Set {device} to {voltage}%")
        else:
            device_status[device] = "OFF"
            response = requests.get(f'http://{esp_ip}/{device}/off', timeout=0.5)
            
        return True, f"Successfully set {device} to {voltage}%"
    except Exception as e:
        _last_connection_failure = time.time()
        print(f"Error setting {device} voltage: {e}")
        
        device_status[device] = "ON" if voltage > 0 else "OFF"
        return True, f"Updated locally (ESP8266 error: {str(e)})"