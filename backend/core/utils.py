"""
Utility functions shared across modules
"""
import numpy as np

def clamp(value, min_val, max_val):
    """Clamp a value between min and max"""
    return max(min_val, min(max_val, value))

def smooth_value(current_value, new_value, smoothing_factor):
    """Apply smoothing to a value"""
    return current_value * smoothing_factor + new_value * (1 - smoothing_factor)

def map_range(value, from_min, from_max, to_min, to_max):
    """Map a value from one range to another"""
    # Clamp input value to source range
    value = clamp(value, from_min, from_max)
    
    # Map to target range
    from_range = from_max - from_min
    to_range = to_max - to_min
    
    if from_range == 0:
        return to_min
    
    return to_min + (value - from_min) * to_range / from_range

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def format_device_name(device):
    """Format device name for display"""
    return device.replace('_', ' ').title()

def validate_voltage(voltage):
    """Validate and clamp voltage value"""
    try:
        voltage = int(voltage)
        return clamp(voltage, 0, 100)
    except (ValueError, TypeError):
        return 0

def create_response(success, message=None, data=None):
    """Create a standardized API response"""
    response = {"success": success}
    
    if message:
        response["message"] = message
    
    if data:
        response.update(data)
    
    return response