"""
Flask API routes
"""
import time
import cv2
import requests
from flask import request, jsonify, send_from_directory, Response
from backend.config import (
    settings, last_settings_change, device_status,
    camera_sources, cap, get_esp8266_ip
)
from backend.core.camera_manager import detect_cameras
from backend.core.device_controller import test_esp8266_connection
from backend.core.video_processor import generate_frames

def register_routes(app, socketio):
    """Register all API routes with the Flask app"""
    
    # Serve the Vue app
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    # Camera routes
    @app.route('/api/cameras', methods=['GET'])
    def get_cameras():
        return jsonify(detect_cameras())
    
    @app.route('/api/debug/cameras', methods=['GET'])
    def debug_cameras():
        """Debug endpoint to check camera status"""
        return jsonify({
            "current_sources": camera_sources,
            "settings": settings,
            "cap_status": "open" if cap and cap.isOpened() else "closed"
        })
    
    # Settings routes
    @app.route('/api/settings', methods=['GET', 'POST'])
    def handle_settings():
        global settings, last_settings_change
        
        if request.method == 'POST':
            old_camera_source = settings.get("camera_source")
            
            settings.update(request.json)
            
            last_settings_change = time.time()
            
            print(f"Settings updated: {', '.join(request.json.keys())}")
            
            return jsonify({"status": "success", "settings": settings})
        return jsonify(settings)
    
    # Device control routes
    @app.route('/api/device/<device>/<action>', methods=['POST'])
    def control_device(device, action):
        if device not in device_status:
            return jsonify({"success": False, "message": f"Unknown device: {device}"})
            
        try:
            esp_ip = get_esp8266_ip()
            response = requests.get(f'http://{esp_ip}/{device}/{action}', timeout=0.5)
            
            device_status[device] = "ON" if action == "on" else "OFF"
                
            return jsonify({
                "success": True,
                "device": device,
                "status": device_status[device]
            })
                
        except Exception as e:
            print(f"Error controlling {device}: {e}")
            return jsonify({"success": False, "message": str(e)})
    
    @app.route('/api/device/status', methods=['GET'])
    def get_device_status():
        return jsonify(device_status)
    
    # Network settings update and restart
    @app.route('/api/network/settings', methods=['POST'])
    def update_network_settings():
        """Update network settings and trigger backend restart"""
        import os
        import sys
        import re
        
        data = request.json
        esp32_url = data.get('esp32_cam_url')
        esp8266_ip = data.get('esp8266_ip')
        
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.py')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Update ESP32-CAM URL in ALL locations
            if esp32_url:
                config_content = re.sub(
                    r'ESP32_CAM_URL\s*=\s*["\'].*?["\']',
                    f'ESP32_CAM_URL = "{esp32_url}"',
                    config_content
                )
                config_content = re.sub(
                    r'camera_sources\s*=\s*\{["\']ESP32-CAM["\']\s*:\s*["\'].*?["\']\}',
                    f'camera_sources = {{"ESP32-CAM": "{esp32_url}"}}',
                    config_content
                )
                config_content = re.sub(
                    r'["\']esp32_cam_url["\']\s*:\s*["\'].*?["\']',
                    f'"esp32_cam_url": "{esp32_url}"',
                    config_content
                )
                settings['esp32_cam_url'] = esp32_url
                camera_sources['ESP32-CAM'] = esp32_url
            
            # Update ESP8266 IP in ALL locations
            if esp8266_ip:
                config_content = re.sub(
                    r'ESP8266_IP\s*=\s*["\'].*?["\']',
                    f'ESP8266_IP = "{esp8266_ip}"',
                    config_content
                )
                config_content = re.sub(
                    r'["\']esp8266_ip["\']\s*:\s*["\'].*?["\']',
                    f'"esp8266_ip": "{esp8266_ip}"',
                    config_content
                )
                settings['esp8266_ip'] = esp8266_ip
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print(f"[CONFIG] Updated ALL network settings locations - ESP32: {esp32_url}, ESP8266: {esp8266_ip}")
            
            # Schedule backend restart
            def restart_backend():
                time.sleep(1)  
                print("[RESTART] Restarting backend with new network settings...")
                os._exit(42)
            
            import threading
            threading.Thread(target=restart_backend, daemon=True).start()
            
            return jsonify({
                "success": True,
                "message": "Network settings saved. Backend restarting...",
                "restarting": True
            })
            
        except Exception as e:
            print(f"[ERROR] Failed to update network settings: {e}")
            return jsonify({
                "success": False,
                "message": f"Failed to update settings: {str(e)}"
            })
    
    # Connection testing routes
    @app.route('/api/test/connection', methods=['POST'])
    def test_connection():
        data = request.json
        test_type = data.get('type')
        
        if test_type == 'esp8266':
            ip = data.get('ip', settings.get('esp8266_ip'))
            success, message = test_esp8266_connection(ip)
            return jsonify({"success": success, "message": message})
        
        elif test_type == 'esp32cam':
            url = data.get('url', settings.get('esp32_cam_url'))
            try:
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)
                if cap.isOpened():
                    cap.release()
                    return jsonify({"success": True, "message": "Camera accessible"})
                else:
                    return jsonify({"success": False, "message": "Cannot open camera"})
            except Exception as e:
                return jsonify({"success": False, "message": str(e)})
        
        return jsonify({"success": False, "message": "Invalid test type"})
    
    # Video streaming route
    @app.route('/video_feed')
    def video_feed():
        """Video streaming route."""
        return Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )