# 🤖 Gesture-Controlled IoT Device System

A real-time gesture recognition system that controls IoT devices through hand gestures using computer vision and ESP8266/ESP32 microcontrollers.

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-red.svg)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.8+-orange.svg)](https://mediapipe.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### 👋 Gesture Recognition
- **Real-time hand tracking** using MediaPipe
- **Finger detection** for individual LED control
- **Rotation gestures** for motor control
- **Multi-finger counting** for voltage control
- **Smooth gesture filtering** to prevent noise

### 🎮 Device Control
- **LED Control**: Toggle LEDs with individual finger gestures
- **Motor Control**: Variable speed control through hand rotation
- **Bulb Dimming**: Brightness control based on finger count
- **Real-time Feedback**: Live device status updates

### 📹 Video Processing
- **Multiple Camera Support**: ESP32-CAM, USB cameras, built-in webcams
- **Live Video Streaming**: Real-time video feed with gesture overlay
- **Visual Indicators**: On-screen rotation and voltage indicators
- **Error Recovery**: Automatic camera reconnection

### 🌐 Web Interface
- **Modern Vue.js Frontend**: Responsive web interface
- **Real-time Updates**: WebSocket communication for live status
- **Settings Panel**: Configure detection parameters
- **Device Dashboard**: Monitor and control all connected devices

## 🛠️ Hardware Requirements

### Required Components
- **ESP8266** (NodeMCU/Wemos D1 Mini) - Main device controller
- **ESP32-CAM** - Video streaming (optional, can use USB camera)
- **LEDs** (3x) - Visual feedback devices
- **DC Motors** (2x) - Rotation control devices
- **Dimmable Bulb/LED Strip** - Variable brightness control
- **Jumper Wires & Breadboard** - Connections

### Network Setup
- All devices must be on the same WiFi network
- ESP8266 should have a static IP address
- ESP32-CAM configured for video streaming

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/smdthiranjaya/control-things-with-gestures.git
cd control-things-with-gestures
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Hardware Setup
```bash
# Flash ESP8266 with device control firmware
# Flash ESP32-CAM with streaming firmware
# Connect LEDs, motors, and bulb to ESP8266 pins
```

### 4. Configuration
```bash
# Edit config.py to match your network setup
ESP8266_IP = "192.168.1.15"  # Your ESP8266 IP
ESP32_CAM_URL = "http://192.168.1.25:81/stream"  # Your ESP32-CAM stream
```

### 5. Run Application
```bash
python app.py
```

Visit `http://localhost:5000` to access the web interface.

## 📁 Project Structure

```
control-things-with-gestures/
├── app.py                  # Main application entry point
├── config.py               # Configuration and global state
├── camera_manager.py       # Camera detection and management
├── gesture_detector.py     # MediaPipe gesture detection
├── device_controller.py    # ESP8266 device control
├── video_processor.py      # Video streaming and processing
├── api_routes.py          # Flask API routes
├── websocket_handlers.py  # SocketIO event handlers
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── frontend-vue/          # Vue.js frontend
├── arduino-sketches/      # ESP8266/ESP32 firmware
├── docs/                  # Documentation
└── README.md             # This file
```

## 🎯 Usage

### Basic Gesture Controls

| Gesture | Action | Device |
|---------|--------|--------|
| 👆 Index Finger | Toggle LED 1 | LED 1 |
| ✌️ Two Fingers | Toggle LED 2 | LED 2 |
| 🤟 Three Fingers | Toggle LED 3 | LED 3 |
| ✋ Four Fingers | Toggle Motor | Main Motor |
| 🖐️ All Fingers | Max Brightness | Bulb |

### Advanced Controls

- **Finger Rotation**: Rotate thumb and index finger to control finger motor speed
- **Hand Rotation**: Rotate entire hand to control hand motor speed  
- **Variable Brightness**: Number of raised fingers controls bulb brightness (0-5 fingers = 0-100%)

### Web Interface

1. **Camera Selection**: Choose between ESP32-CAM or USB cameras
2. **Settings Panel**: Configure gesture detection parameters
3. **Device Dashboard**: Monitor real-time device status
4. **Visual Indicators**: See gesture feedback on video stream

## ⚙️ Configuration

### Camera Settings
```python
settings = {
    "camera_source": "ESP32-CAM",           # Camera source
    "gesture_detection_enabled": True,       # Enable/disable detection
    "show_landmarks": True,                  # Show hand landmarks
    "finger_rotation_enabled": False,        # Finger rotation control
    "hand_rotation_enabled": False,          # Hand rotation control
}
```

### Device Detection
```python
settings = {
    "detect_all_leds": True,        # Enable LED control
    "detect_motor": False,          # Enable motor control
    "detect_bulb": False,           # Enable bulb control
    "detect_finger_motor": False,   # Enable finger motor
    "detect_hand_motor": False,     # Enable hand motor
}
```

### Visual Indicators
```python
settings = {
    "show_finger_rotation_indicator": False,  # Show finger rotation
    "show_hand_rotation_indicator": False,    # Show hand rotation  
    "show_bulb_indicator": False,            # Show bulb voltage
}
```

## 🔧 API Endpoints

### Device Control
```bash
POST /api/device/<device>/<action>     # Control device on/off
POST /api/device/bulb/voltage/<int>    # Set bulb voltage (0-100)
POST /api/motor/<motor>/voltage/<int>  # Set motor voltage (0-100)
GET  /api/device/status               # Get all device status
```

### Camera Management
```bash
GET /api/cameras                      # Get available cameras
GET /api/debug/cameras               # Debug camera status
```

### Settings
```bash
GET  /api/settings                   # Get current settings
POST /api/settings                   # Update settings
```

### Connection Testing
```bash
POST /api/test/connection            # Test ESP8266/ESP32 connection
```

## 🔍 Troubleshooting

### Common Issues

**Camera not detected**
```bash
# Check camera connections
# Verify ESP32-CAM stream URL
# Try different USB camera index
```

**Gesture detection not working**
```bash
# Ensure good lighting conditions
# Check camera focus and positioning
# Verify MediaPipe installation
```

**Device control not responding**
```bash
# Check ESP8266 network connection
# Verify IP address configuration
# Test connection via /api/test/connection
```

**High CPU usage**
```bash
# Reduce camera resolution
# Disable visual indicators
# Lower gesture detection confidence
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run linting
flake8 .

# Format code
black .
```

## 📊 Performance

- **Gesture Detection**: 30+ FPS on modern hardware
- **Response Time**: <100ms gesture to device action
- **Memory Usage**: ~200MB typical operation
- **Network Traffic**: Minimal (WebSocket updates only)

## 🛡️ Security

- **Local Network Only**: No external internet access required
- **No Data Storage**: No gesture data is stored permanently
- **Encrypted Communication**: HTTPS/WSS support available
- **Network Isolation**: Devices operate on local network only

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [@smdthiranjaya](https://github.com/smdthiranjaya)

## 🙏 Acknowledgments

- **MediaPipe** team for excellent hand tracking
- **OpenCV** community for computer vision tools
- **Flask** developers for the web framework
- **Vue.js** team for the frontend framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/smdthiranjaya/control-things-with-gestures/issues)
- **Discussions**: [GitHub Discussions](https://github.com/smdthiranjaya/control-things-with-gestures/discussions)
- **Email**: s.m.d.thiranjaya@gmail.com

## 🗺️ Roadmap

- [ ] **Mobile App**: React Native mobile application
- [ ] **Voice Control**: Add voice commands alongside gestures
- [ ] **Machine Learning**: Custom gesture training
- [ ] **Cloud Integration**: Optional cloud device management
- [ ] **Multi-User**: Support for multiple users
- [ ] **Gesture Recording**: Save and replay gesture sequences

---

⭐ **Star this repository if you found it helpful!**

🐛 **Found a bug?** [Report it here](https://github.com/smdthiranjaya/control-things-with-gestures/issues)

💡 **Have an idea?** [Share it in discussions](https://github.com/smdthiranjaya/control-things-with-gestures/discussions)