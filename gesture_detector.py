"""
Gesture detection and processing using MediaPipe
"""
import cv2
import numpy as np
import math
import mediapipe as mp
from config import settings

# MediaPipe setup
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)

def calculate_angle(a, b, c):
    """Calculate angle between three points."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    ab = b - a
    cb = b - c
    
    dot_product = np.dot(ab, cb)
    magnitude_product = np.linalg.norm(ab) * np.linalg.norm(cb)
    
    if magnitude_product < 1e-10:
        return 0
        
    angle_rad = np.arccos(np.clip(dot_product / magnitude_product, -1.0, 1.0))
    return np.degrees(angle_rad)

def calculate_wrist_rotation(landmarks):
    """Calculate wrist rotation angle."""
    wrist = landmarks[0]  # Landmark 0: wrist
    index_mcp = landmarks[5]  # Landmark 5: index finger MCP
    pinky_mcp = landmarks[17]  # Landmark 17: pinky MCP
    
    # Calculate the vector from wrist to the midpoint of index and pinky MCP
    mid_mcp_x = (index_mcp[0] + pinky_mcp[0]) / 2
    mid_mcp_y = (index_mcp[1] + pinky_mcp[1]) / 2
    vector_x = mid_mcp_x - wrist[0]
    vector_y = mid_mcp_y - wrist[1]
    
    # Calculate angle relative to horizontal
    angle = math.degrees(math.atan2(vector_y, vector_x))
    # Normalize angle to 0-180 degrees
    angle = (angle + 360) % 360
    if angle > 180:
        angle = 360 - angle
        
    return angle

def detect_fingers(landmarks, hand_label):
    """Detect which fingers are raised"""
    fingers = [0] * 5  # Reset fingers for current detection
    
    # Thumb detection
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]
    thumb_angle = calculate_angle(thumb_mcp, thumb_ip, thumb_tip)
    
    if hand_label == "Right":
        if thumb_tip[0] < thumb_ip[0] and thumb_angle > 30:
            fingers[0] = 1
    else:
        if thumb_tip[0] > thumb_ip[0] and thumb_angle > 30:
            fingers[0] = 1
    
    # Other fingers detection
    for i in range(1, 5):
        tip_idx = i * 4 + 4
        dip_idx = i * 4 + 3
        pip_idx = i * 4 + 2
        mcp_idx = i * 4 + 1
        
        if (landmarks[tip_idx][1] < landmarks[pip_idx][1] and
            landmarks[dip_idx][1] < landmarks[mcp_idx][1] and
            (landmarks[pip_idx][1] - landmarks[tip_idx][1]) > 15):
            fingers[i] = 1
    
    return fingers

def process_frame_for_gestures(frame):
    """Process frame and detect hand gestures"""
    if not settings.get("gesture_detection_enabled", True):
        return frame, None, None, None
    
    # Convert to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    hand_data = None
    
    if results.multi_hand_landmarks:
        hand_label = results.multi_handedness[0].classification[0].label
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # Convert landmarks to pixel coordinates
        h, w, _ = frame.shape
        landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]
        
        # Draw landmarks if enabled
        if settings.get("show_landmarks", True):
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        
        # Detect finger states
        fingers = detect_fingers(landmarks, hand_label)
        
        # Calculate rotation angles
        finger_angle = None
        hand_angle = None
        
        if settings.get("finger_rotation_enabled", True):
            index_tip = landmarks[8]
            thumb_tip = landmarks[4]
            wrist = landmarks[0]
            finger_angle = calculate_angle(index_tip, wrist, thumb_tip)
        
        if settings.get("hand_rotation_enabled", True):
            hand_angle = calculate_wrist_rotation(landmarks)
        
        hand_data = {
            'landmarks': landmarks,
            'fingers': fingers,
            'finger_angle': finger_angle,
            'hand_angle': hand_angle,
            'total_fingers': sum(fingers)
        }
    
    return frame, hand_data, results.multi_hand_landmarks, results.multi_handedness

def draw_rotation_indicators(frame, landmarks, finger_angle, hand_angle):
    """Draw rotation indicators on the frame."""
    h, w, _ = frame.shape
    
    # Finger rotation indicator
    if settings.get("show_finger_rotation_indicator", True):
        wrist = landmarks[0]
        index_tip = landmarks[8]
        thumb_tip = landmarks[4]
        center_x = int((thumb_tip[0] + index_tip[0]) / 2)
        center_y = int((thumb_tip[1] + index_tip[1]) / 2)
        
        radius = 50
        end_angle = (finger_angle * 3.6) % 360
        
        cv2.ellipse(frame, (center_x, center_y), (radius, radius), 0, 0, end_angle, (0, 255, 0), 5)
        cv2.putText(frame, f"Finger: {finger_angle}%", (center_x - 70, center_y - radius - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Hand rotation indicator
    if settings.get("show_hand_rotation_indicator", True):
        wrist = landmarks[0]
        
        # Draw circle at wrist
        cv2.circle(frame, (wrist[0], wrist[1]), 70, (0, 140, 255), 2)
        
        # Draw line following wrist rotation
        index_mcp = landmarks[5]
        pinky_mcp = landmarks[17]
        mid_mcp_x = (index_mcp[0] + pinky_mcp[0]) / 2
        mid_mcp_y = (index_mcp[1] + pinky_mcp[1]) / 2
        vector_x = mid_mcp_x - wrist[0]
        vector_y = mid_mcp_y - wrist[1]
        
        angle = math.degrees(math.atan2(vector_y, vector_x))
        angle = (angle + 360) % 360
        if angle > 180:
            angle = 360 - angle
            
        end_x = wrist[0] + int(60 * math.cos(math.radians(angle)))
        end_y = wrist[1] + int(60 * math.sin(math.radians(angle)))
        
        cv2.line(frame, (wrist[0], wrist[1]), (end_x, end_y), (0, 140, 255), 4)
        cv2.circle(frame, (end_x, end_y), 6, (0, 140, 255), -1)
        cv2.putText(frame, f"Hand: {hand_angle}%", (wrist[0] - 70, wrist[1] + 95),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 140, 255), 2)

def draw_bulb_indicator(frame, landmarks, voltage_percent):
    """Draw bulb voltage indicator on the frame."""
    h, w, _ = frame.shape
    
    # Draw at top center of frame
    center_x = w // 2
    y_pos = 80
    bar_width = 250
    bar_height = 30
    
    # Background bar
    cv2.rectangle(frame, (center_x - bar_width//2, y_pos), 
                  (center_x + bar_width//2, y_pos + bar_height), 
                  (50, 50, 50), -1)
    
    # Voltage level bar
    fill_width = int(bar_width * voltage_percent / 100)
    if fill_width > 0:
        # Color gradient from dark to bright yellow based on voltage
        color_intensity = int(100 + (155 * voltage_percent / 100))
        cv2.rectangle(frame, (center_x - bar_width//2, y_pos), 
                      (center_x - bar_width//2 + fill_width, y_pos + bar_height), 
                      (0, color_intensity, color_intensity), -1)
    
    # Draw 5 segment dividers
    for i in range(1, 5):
        x_pos = center_x - bar_width//2 + (bar_width * i // 5)
        cv2.line(frame, (x_pos, y_pos), (x_pos, y_pos + bar_height), (255, 255, 255), 2)
    
    # Border
    cv2.rectangle(frame, (center_x - bar_width//2, y_pos), 
                  (center_x + bar_width//2, y_pos + bar_height), 
                  (255, 255, 255), 2)
    
    # Text
    cv2.putText(frame, f"Bulb: {int(voltage_percent)}%", 
                (center_x - 50, y_pos - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Finger count indicators
    for i in range(5):
        x_pos = center_x - bar_width//2 + (bar_width * i // 5) + bar_width//10
        cv2.putText(frame, str(i+1), (x_pos - 5, y_pos + bar_height + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)