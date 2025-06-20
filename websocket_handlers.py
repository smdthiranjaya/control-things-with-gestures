"""
WebSocket event handlers
"""
import time
import threading
import traceback
from flask_socketio import emit

from config import device_status, motor_values

# Thread control flag
update_thread_running = True
# Track connected clients
connected_clients = 0

def register_socketio_handlers(socketio):
    """Register all SocketIO event handlers"""
    global connected_clients
    
    @socketio.on('connect')
    def handle_connect():
        global connected_clients
        connected_clients += 1
        print(f'Client connected (total: {connected_clients})')
        emit('device_status', device_status)
        emit('motor_values', motor_values)

    @socketio.on('disconnect')
    def handle_disconnect():
        global connected_clients
        connected_clients = max(0, connected_clients - 1)
        print(f'Client disconnected (remaining: {connected_clients})')

def send_updates(socketio):
    """Send periodic updates to connected clients"""
    global update_thread_running
    print("Update thread started")
    
    try:
        while update_thread_running:
            try:
                # Simply emit the updates - harmless if no clients connected
                socketio.emit('device_status', device_status)
                socketio.emit('motor_values', motor_values)
                
                # Sleep to prevent high CPU usage
                time.sleep(0.5)
            except Exception as e:
                # Log error but keep thread running
                print(f"Error in update thread: {e}")
                traceback.print_exc()
                time.sleep(1)  # Sleep longer on error
    except Exception as e:
        print(f"Fatal error in update thread: {e}")
        traceback.print_exc()
    finally:
        print("Update thread finishing")

def start_update_thread(socketio):
    """Start the update thread for real-time communication"""
    global update_thread_running
    update_thread_running = True
    update_thread = threading.Thread(target=send_updates, args=(socketio,), daemon=True)
    update_thread.start()
    return update_thread

def stop_update_thread():
    """Stop the update thread safely"""
    global update_thread_running
    update_thread_running = False
    print("Update thread stop requested")