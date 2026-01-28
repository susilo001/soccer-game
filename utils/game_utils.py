"""Game utilities and common functions."""

import math
from typing import Tuple


def calculate_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """Calculate distance between two points.
    
    Args:
        pos1: First position (x, y)
        pos2: Second position (x, y)
        
    Returns:
        Distance between the points
    """
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    return math.sqrt(dx ** 2 + dy ** 2)


def calculate_distance_squared(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """Calculate squared distance between two points (faster when exact distance not needed).
    
    Args:
        pos1: First position (x, y)
        pos2: Second position (x, y)
        
    Returns:
        Squared distance between the points
    """
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    return dx ** 2 + dy ** 2


def normalize_vector(x: float, y: float) -> Tuple[float, float]:
    """Normalize a 2D vector.
    
    Args:
        x: X component
        y: Y component
        
    Returns:
        Normalized vector (x, y)
    """
    magnitude = math.sqrt(x ** 2 + y ** 2)
    if magnitude == 0:
        return 0.0, 0.0
    return x / magnitude, y / magnitude


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two values.
    
    Args:
        a: Start value
        b: End value
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated value
    """
    return a + (b - a) * clamp(t, 0.0, 1.0)


# Game constants
FIELD_LENGTH = 105.0  # meters
FIELD_WIDTH = 68.0    # meters
GOAL_WIDTH = 7.32     # meters

# Common field positions
CENTER_POSITION = (0.0, 0.0)
HOME_GOAL_POSITION = (-FIELD_LENGTH / 2, 0.0)
AWAY_GOAL_POSITION = (FIELD_LENGTH / 2, 0.0)

# Performance constants
MIN_MOVEMENT_DISTANCE_SQUARED = 0.25  # 0.5^2 - minimum distance to trigger movement
BALL_INTERACTION_DISTANCE = 1.2      # Distance for ball interaction
POSSESSION_DISTANCE = 2.0             # Distance for ball possession