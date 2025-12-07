import time
import urllib3
import socket
from urllib.parse import urlencode
from backend.config import device_status, get_esp8266_ip, settings

# This keeps connections alive aggressively and reuses them
http_pool = None
_resolved_esp_ip = None

def resolve_hostname(hostname):
    """Resolve mDNS hostname to IP address once and cache it"""
    global _resolved_esp_ip
    if _resolved_esp_ip is None:
        try:
            print(f"[DNS] Resolving {hostname}...")
            resolved = socket.gethostbyname(hostname)
            _resolved_esp_ip = resolved
            print(f"[DNS] Resolved {hostname} → {resolved}")
        except socket.gaierror as e:
            print(f"[DNS ERROR] Failed to resolve {hostname}: {e}")
            _resolved_esp_ip = hostname
    return _resolved_esp_ip

def get_http_pool():
    """Get or create HTTP connection pool"""
    global http_pool
    if http_pool is None:
        hostname = get_esp8266_ip()
        esp_ip = resolve_hostname(hostname)
        
        http_pool = urllib3.HTTPConnectionPool(
            host=esp_ip,
            port=80,
            maxsize=1,
            block=False,
            timeout=urllib3.Timeout(connect=3.0, read=0.1),
            retries=False,
            headers={'Connection': 'keep-alive'}
        )
        print(f"[CONNECTION] Created connection pool to {esp_ip}")
    return http_pool

# Timeout for requests
REQUEST_TIMEOUT = urllib3.Timeout(connect=3.0, read=0.1)

# Connection warming - establish connection on module load
def warm_connection():
    """Pre-establish TCP connection to ESP8266"""
    try:
        pool = get_http_pool()
        pool.request('GET', '/status', timeout=urllib3.Timeout(connect=2.0, read=2.0))
        print(f"[CONNECTION] Warmed up connection to {pool.host}")
    except Exception as e:
        print(f"[WARNING] Could not warm connection: {e}")

try:
    warm_connection()
except:
    pass

# Debouncing
last_state_change = {}
debounce_delay = 1.0

# Keep-alive ping
last_keepalive = time.time()
keepalive_interval = 5.0  

def keepalive_ping():
    """Send periodic ping to keep TCP connection alive"""
    global last_keepalive
    current = time.time()
    if current - last_keepalive > keepalive_interval:
        try:
            pool = get_http_pool()
            pool.request('GET', '/status', timeout=REQUEST_TIMEOUT)
            last_keepalive = current
        except:
            pass 

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
    
    pool = get_http_pool()
    print(f"\n[DEBUG {time.strftime('%H:%M:%S.%f')[:-3]}] Control Request: {device} -> {action}")
        
    try:
        if device == "motor":
            req1_start = time.time()
            pool.request('GET', f'/buzzer/{action}', timeout=REQUEST_TIMEOUT)
            req1_time = (time.time() - req1_start) * 1000
            print(f"  ├─ Buzzer request: {req1_time:.1f}ms")
            
            req2_start = time.time()
            pool.request('GET', f'/motor/{action}', timeout=REQUEST_TIMEOUT)
            req2_time = (time.time() - req2_start) * 1000
            print(f"  ├─ Motor request: {req2_time:.1f}ms")
        else:
            req_start = time.time()
            response = pool.request('GET', f'/{device}/{action}', timeout=REQUEST_TIMEOUT)
            req_time = (time.time() - req_start) * 1000
            print(f"  ├─ {device} request: {req_time:.1f}ms (status: {response.status})")
        
        device_status[device] = "ON" if action == "on" else "OFF"
        
        total_time = (time.time() - start_time) * 1000
        print(f"  └─ Total time: {total_time:.1f}ms\n")
            
        return True
            
    except urllib3.exceptions.TimeoutError:
        elapsed = (time.time() - start_time) * 1000
        print(f"  └─ ⚠ TIMEOUT after {elapsed:.1f}ms controlling {device}\n")
        return False
    except urllib3.exceptions.HTTPError as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"  └─ ⚠ HTTP ERROR after {elapsed:.1f}ms: {e}\n")
        return False
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"  └─ ⚠ ERROR after {elapsed:.1f}ms: {e}\n")
        return False

def control_devices_by_gesture(total_fingers):
    global last_total_fingers
    
    if not settings.get("detect_all_leds", True):
        return
    
    keepalive_ping()
    
    gesture_start = time.time()
    current_time = time.time()
    
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
    
    if len(state_buffer[device_key]) > confirmation_frames:
        state_buffer[device_key].pop(0)
    
    # Only trigger if we have enough frames and they're all the same
    if len(state_buffer[device_key]) == confirmation_frames:
        if all(f == total_fingers for f in state_buffer[device_key]):
            if total_fingers != last_total_fingers:
                last_change = last_state_change.get(device_key, 0)
                if current_time - last_change >= debounce_delay:
                    
                    if total_fingers == 0:
                        print("[GESTURE] Closed Fist - All Components OFF")
                        try:
                            pool = get_http_pool()
                            pool.request('GET', '/batch?led1=off&led2=off&motor=off&buzzer=off', timeout=REQUEST_TIMEOUT)
                            device_status["led1"] = "OFF"
                            device_status["led2"] = "OFF"
                            device_status["motor"] = "OFF"
                        except Exception as e:
                            print(f"[ERROR] Turn all off failed: {e}")
                            pass
                    
                    elif total_fingers == 5:
                        print("[GESTURE] Open Hand - Red & Green LEDs ON")
                        try:
                            pool = get_http_pool()
                            pool.request('GET', '/batch?led1=on&led2=on', timeout=REQUEST_TIMEOUT)
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
                                pool = get_http_pool()
                                pool.request('GET', f'/led1/{action}', timeout=REQUEST_TIMEOUT)
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
                                pool = get_http_pool()
                                pool.request('GET', f'/led2/{action}', timeout=REQUEST_TIMEOUT)
                                device_status["led2"] = new_state
                            except Exception as e:
                                print(f"[ERROR] LED2 request failed: {e}")
                                pass
                    
                    elif total_fingers == 3:
                        if settings.get("detect_motor", True):
                            print("[GESTURE] 3 Fingers - Motor & Buzzer ON, LEDs OFF")
                            try:
                                pool = get_http_pool()
                                pool.request('GET', '/batch?motor=on&buzzer=on&led1=off&led2=off', timeout=REQUEST_TIMEOUT)
                                device_status["motor"] = "ON"
                                device_status["led1"] = "OFF"
                                device_status["led2"] = "OFF"
                            except Exception as e:
                                print(f"[ERROR] 3-finger gesture failed: {e}")
                                pass
                    
                    else:
                        if settings.get("detect_motor", True) and device_status.get("motor") == "ON":
                            print("[GESTURE] Motor & Buzzer OFF (gesture changed)")
                            try:
                                pool = get_http_pool()
                                pool.request('GET', '/batch?motor=off&buzzer=off', timeout=REQUEST_TIMEOUT)
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
    try:
        pool = get_http_pool()
        response = pool.request('GET', '/status', timeout=urllib3.Timeout(connect=2.0, read=2.0))
        return True, "Connected successfully"
    except urllib3.exceptions.TimeoutError:
        return False, "Connection timeout"
    except urllib3.exceptions.HTTPError:
        return False, "Connection failed"
    except Exception as e:
        return False, str(e)