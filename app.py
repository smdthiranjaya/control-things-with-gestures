import threading
import webbrowser
import time
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from backend.config import cap
from backend.core.camera_manager import initialize_cameras_background
from backend.routes.api_routes import register_routes
from backend.handlers.websocket_handlers import register_socketio_handlers, start_update_thread

def create_app():
    app = Flask(__name__, static_folder='./frontend-vue')
    CORS(app)
    
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    register_routes(app, socketio)
    register_socketio_handlers(socketio)
    
    return app, socketio

def open_browser():
    time.sleep(1.5)
    url = 'http://127.0.0.1:5000'
    print(f"Opening browser at {url}")
    webbrowser.open(url, new=2)

def main():
    try:
        app, socketio = create_app()
        
        start_update_thread(socketio)
        
        camera_thread = threading.Thread(target=initialize_cameras_background, daemon=True)
        camera_thread.start()
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
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