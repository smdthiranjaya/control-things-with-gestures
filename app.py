"""
Main Flask application for gesture-controlled device system
"""
import threading
import webbrowser
import time
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from config import cap
from camera_manager import initialize_cameras_background
from api_routes import register_routes
from websocket_handlers import register_socketio_handlers, start_update_thread

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, static_folder='./frontend-vue')
    CORS(app)
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Register routes and handlers
    register_routes(app, socketio)
    register_socketio_handlers(socketio)
    
    return app, socketio

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)  # Wait for server to start
    url = 'http://127.0.0.1:5000'
    print(f"Opening browser at {url}")
    webbrowser.open(url, new=2)  # Open in a new window/tab

def main():
    """Main application entry point"""
    try:
        # Create Flask app and SocketIO
        app, socketio = create_app()
        
        # Start update thread for real-time communication
        start_update_thread(socketio)
        
        # Start camera detection in background (non-blocking)
        camera_thread = threading.Thread(target=initialize_cameras_background, daemon=True)
        camera_thread.start()
        
        # Start browser opening in background
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start the server
        print("Starting Flask server on http://0.0.0.0:5000")
        print("Camera detection will happen in background...")
        print("Browser will open automatically...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except Exception as e:
        print(f"Error starting server: {e}")
        if cap is not None:
            cap.release()

if __name__ == '__main__':
    main()