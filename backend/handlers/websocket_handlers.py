"""
WebSocket event handlers
"""
import time
import threading
from flask_socketio import emit
from backend.config import device_status

def register_socketio_handlers(socketio):
    """Register all SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('device_status', device_status)

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

def send_updates(socketio):
    """Send periodic updates to connected clients"""
    while True:
        socketio.emit('device_status', device_status)
        time.sleep(0.5)

def start_update_thread(socketio):
    """Start the update thread for real-time communication"""
    update_thread = threading.Thread(target=send_updates, args=(socketio,), daemon=True)
    update_thread.start()
    return update_thread