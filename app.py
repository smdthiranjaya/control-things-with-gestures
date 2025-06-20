"""
Main Flask application for gesture-controlled device system
"""
import threading
import signal
import sys
import time
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from config import cap
from camera_manager import initialize_cameras_background, release_camera
from api_routes import register_routes
from websocket_handlers import register_socketio_handlers, start_update_thread, stop_update_thread

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    print("\nShutting down server gracefully...")
    stop_update_thread()  # Stop the update thread
    cleanup_resources()
    sys.exit(0)

def cleanup_resources():
    """Clean up all resources before shutdown"""
    print("Cleaning up resources...")
    
    # Use the new force_camera_release function
    from camera_manager import force_camera_release
    force_camera_release()
    
    # Give the OS time to fully release ports and other resources
    time.sleep(0.5)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, static_folder='./frontend-vue', static_url_path='')
    CORS(app)
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Register routes and handlers
    register_routes(app, socketio)
    register_socketio_handlers(socketio)
    
    return app, socketio

def main():
    """Main application entry point"""
    try:
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create Flask app and SocketIO
        app, socketio = create_app()
        
        # Start update thread for real-time communication
        update_thread = start_update_thread(socketio)
        
        # Start camera detection in background (non-blocking)
        camera_thread = threading.Thread(target=initialize_cameras_background, daemon=True)
        camera_thread.start()
        
        # Start the server
        print("Starting Flask server on http://0.0.0.0:5000")
        print("Camera detection will happen in background...")
        
        try:
            socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        finally:
            stop_update_thread()
            cleanup_resources()
        
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        stop_update_thread()
        if cap is not None:
            cap.release()

if __name__ == '__main__':
    main()