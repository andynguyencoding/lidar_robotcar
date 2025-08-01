"""
Configuration constants and settings for the LiDAR Visualizer
"""

# LiDAR constants
LIDAR_RESOLUTION = 360

# Display constants
SCREEN_WIDTH = 800
SCALE_FACTOR = 0.25  # Default fallback value
TARGET_RADIUS = 300  # Use ~300 pixels of the 400 pixel radius available

# Selected positions in a frame (result of the Sklearn SelectKBest function)
DECISIVE_FRAME_POSITIONS = [24, 29, 31, 35, 38, 39, 40, 41, 42, 43, 44, 45, 47, 50, 54, 55, 57, 302,
                            304, 312, 314, 315, 316, 318, 319, 321, 324, 326, 328, 330]

# UI Configuration
DEFAULT_WINDOW_WIDTH = 850
DEFAULT_WINDOW_HEIGHT = 750
MIN_WINDOW_WIDTH = 600
MIN_WINDOW_HEIGHT = 500
DEFAULT_CANVAS_SIZE = 680

# File Management
MAX_RECENT_FILES = 5
RECENT_FILES_FILENAME = "visualizer_recent_files.txt"

# Undo System
MAX_UNDO_STEPS = 20

# Direction ratio configuration (angular velocity to degree mapping)
DIRECTION_RATIO_MAX_DEGREE = 45.0  # Maximum degrees for visualization
DIRECTION_RATIO_MAX_ANGULAR = 1.0  # Angular velocity value that maps to max degree
