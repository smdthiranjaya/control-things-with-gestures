"""
Flask API routes
"""
import time
import cv2
import requests
from flask import request, jsonify, send_from_directory, Response
from config import (
    settings, last_settings_change, device_status, motor_values, 
    camera_sources, cap, get_esp8266_ip
)
from camera_manager import detect_cameras
from device_controller import test_esp8266_connection, set_device_voltage
from video_processor import generate_frames

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
            
            if device in motor_values:
                motor_values[device] = 100 if action == "on" else 0
                
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
    
    # Motor voltage control routes
    @app.route('/api/device/bulb/voltage/<int:voltage>', methods=['POST'])
    def set_bulb_voltage(voltage):
        success, message = set_device_voltage("bulb", voltage)
        
        if success:
            socketio.emit('device_status', device_status)
            socketio.emit('motor_values', motor_values)
            return jsonify({
                "success": True,
                "voltage": voltage,
                "status": device_status["bulb"]
            })
        else:
            return jsonify({"success": False, "message": message})
    
    @app.route('/api/motor/<motor>/voltage/<int:voltage>', methods=['POST'])
    def set_motor_voltage(motor, voltage):
        if motor not in ["finger_motor", "hand_motor"]:
            return jsonify({"success": False, "message": "Invalid motor"})
        
        success, message = set_device_voltage(motor, voltage)
        
        if success:
            socketio.emit('device_status', device_status)
            socketio.emit('motor_values', motor_values)
            return jsonify({
                "success": True,
                "voltage": voltage,
                "status": device_status[motor]
            })
        else:
            return jsonify({"success": False, "message": message})
    
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