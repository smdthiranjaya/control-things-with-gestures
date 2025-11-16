# Gesture Control System

Control smart devices with hand gestures through computer vision.

## Project Structure

```
control-things-with-gestures/
│
├── app.py                      # Main Flask application entry point
├── start_app.bat              # Windows startup script
├── requirements.txt           # Python dependencies
│
├── backend/                   # Backend Python code
│   ├── __init__.py
│   ├── config.py             # Configuration and settings
│   │
│   ├── core/                 # Core functionality modules
│   │   ├── __init__.py
│   │   ├── camera_manager.py      # Camera detection and management
│   │   ├── device_controller.py   # ESP8266 device control
│   │   ├── gesture_detector.py    # MediaPipe gesture detection
│   │   ├── video_processor.py     # Video streaming and processing
│   │   └── utils.py               # Utility functions
│   │
│   ├── routes/               # API route handlers
│   │   ├── __init__.py
│   │   └── api_routes.py         # Flask REST API endpoints
│   │
│   └── handlers/             # Event handlers
│       ├── __init__.py
│       └── websocket_handlers.py # WebSocket event handlers
│
├── frontend-vue/             # Frontend web interface
│   └── index.html           # Vue.js single-page application
│
└── arduino/                  # Arduino firmware
    ├── CameraWebServer/     # ESP32-CAM firmware
    └── Esp8266/            # ESP8266 device control firmware

```

## Features

- **Hand Gesture Detection**: Uses MediaPipe for real-time hand tracking
- **Device Control**: Controls LEDs and motor via ESP8266
- **Multiple Camera Sources**: Supports ESP32-CAM and USB cameras
- **Modern UI**: Dark mode Vue.js interface
- **Real-time Updates**: WebSocket communication for instant feedback
- **Auto-restart**: Automatically restarts when network settings change

## Gesture Mappings

- **0 Fingers (Fist)**: Turn OFF all devices
- **1 Finger**: Toggle Red LED
- **2 Fingers**: Toggle Green LED
- **3 Fingers**: Turn ON Motor & Buzzer, Turn OFF both LEDs
- **5 Fingers (Open Hand)**: Turn ON both Red and Green LEDs

## Installation

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure network settings in `backend/config.py`:

   - Set ESP32-CAM URL
   - Set ESP8266 IP address

3. Upload Arduino firmware:

   - Upload `arduino/CameraWebServer/` to ESP32-CAM
   - Upload `arduino/Esp8266/` to ESP8266

4. Run the application:
   ```bash
   python app.py
   ```
   Or use `start_app.bat` for auto-restart capability.

## Usage

1. Open browser at `http://localhost:5000`
2. Select camera source from Settings
3. Enable device detection checkboxes
4. Perform hand gestures in front of camera
5. Devices respond to gestures in real-time

## Technical Details

- **Backend**: Flask 2.3.3, Flask-SocketIO 5.3.6
- **Computer Vision**: MediaPipe 0.10.21, OpenCV 4.8.1.78
- **Frontend**: Vue.js 3.2.36, Tailwind CSS 2.2.19
- **Hardware**: ESP32-CAM, ESP8266, 2 LEDs, 1 Motor/Buzzer

## Configuration

Edit `backend/config.py` to customize:

- ESP32-CAM URL and port
- ESP8266 IP address
- Gesture detection settings
- Camera enhancement parameters

## License

MIT License
