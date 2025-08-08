"""
Configuration constants and settings for the LiDAR Visualizer
"""

# Logging Configuration
LOG_LEVEL = "INFO"  # Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_FILE = True  # Whether to log to file in addition to console
LOG_TO_CONSOLE = True  # Whether to log to console

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

# Augmentation Configuration
AUGMENTATION_MOVEMENT_STEP = 0.1  # Default movement step in meters
AUGMENTATION_UNIT = "m"  # Default unit measurement: "m" or "mm"

# Direction ratio configuration (angular velocity to degree mapping)
DIRECTION_RATIO_MAX_DEGREE = 45.0  # Maximum degrees for visualization
DIRECTION_RATIO_MAX_ANGULAR = 1.0  # Angular velocity value that maps to max degree

# LiDAR point visualization configuration
NORMAL_POINT_RADIUS = 3  # Default radius for normal lidar points
NORMAL_POINT_CENTER_RADIUS = 1  # Default radius for normal point centers
DECISIVE_POINT_RADIUS = 5  # Default radius for decisive frame points
DECISIVE_POINT_CENTER_RADIUS = 2  # Default radius for decisive point centers

# Export Configuration
EXPORT_FILE_PREFIX = "lidar_dataset"  # Default prefix for exported files
EXPORT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"  # Default timestamp format for exported files


def load_preferences_into_config():
    """
    Load saved preferences and update configuration variables
    Call this at application startup
    """
    try:
        from .preferences import load_preferences
        
        prefs = load_preferences()
        
        # Update global configuration variables with saved preferences
        global SCALE_FACTOR, DIRECTION_RATIO_MAX_DEGREE, DIRECTION_RATIO_MAX_ANGULAR
        global AUGMENTATION_UNIT, EXPORT_FILE_PREFIX, EXPORT_TIMESTAMP_FORMAT
        global DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, DEFAULT_CANVAS_SIZE
        global LOG_LEVEL, LOG_TO_FILE, LOG_TO_CONSOLE
        global NORMAL_POINT_RADIUS, NORMAL_POINT_CENTER_RADIUS
        global DECISIVE_POINT_RADIUS, DECISIVE_POINT_CENTER_RADIUS
        
        # Visual preferences
        SCALE_FACTOR = prefs.get("visual", {}).get("scale_factor", SCALE_FACTOR)
        DIRECTION_RATIO_MAX_DEGREE = prefs.get("visual", {}).get("direction_ratio_max_degree", DIRECTION_RATIO_MAX_DEGREE)
        DIRECTION_RATIO_MAX_ANGULAR = prefs.get("visual", {}).get("direction_ratio_max_angular", DIRECTION_RATIO_MAX_ANGULAR)
        NORMAL_POINT_RADIUS = prefs.get("visual", {}).get("normal_point_radius", NORMAL_POINT_RADIUS)
        NORMAL_POINT_CENTER_RADIUS = prefs.get("visual", {}).get("normal_point_center_radius", NORMAL_POINT_CENTER_RADIUS)
        DECISIVE_POINT_RADIUS = prefs.get("visual", {}).get("decisive_point_radius", DECISIVE_POINT_RADIUS)
        DECISIVE_POINT_CENTER_RADIUS = prefs.get("visual", {}).get("decisive_point_center_radius", DECISIVE_POINT_CENTER_RADIUS)
        
        # Data preferences
        AUGMENTATION_UNIT = prefs.get("data", {}).get("augmentation_unit", AUGMENTATION_UNIT)
        
        # Export preferences
        EXPORT_FILE_PREFIX = prefs.get("export", {}).get("file_prefix", EXPORT_FILE_PREFIX)
        EXPORT_TIMESTAMP_FORMAT = prefs.get("export", {}).get("timestamp_format", EXPORT_TIMESTAMP_FORMAT)
        
        # UI preferences
        DEFAULT_WINDOW_WIDTH = prefs.get("ui", {}).get("window_width", DEFAULT_WINDOW_WIDTH)
        DEFAULT_WINDOW_HEIGHT = prefs.get("ui", {}).get("window_height", DEFAULT_WINDOW_HEIGHT)
        DEFAULT_CANVAS_SIZE = prefs.get("ui", {}).get("canvas_size", DEFAULT_CANVAS_SIZE)
        
        # Logging preferences
        LOG_LEVEL = prefs.get("logging", {}).get("log_level", LOG_LEVEL)
        LOG_TO_FILE = prefs.get("logging", {}).get("log_to_file", LOG_TO_FILE)
        LOG_TO_CONSOLE = prefs.get("logging", {}).get("log_to_console", LOG_TO_CONSOLE)
        
        print(f"✅ Preferences loaded: Scale={SCALE_FACTOR:.3f}, Unit={AUGMENTATION_UNIT}, Export prefix={EXPORT_FILE_PREFIX}")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not load preferences: {e}")


def save_current_config_to_preferences():
    """
    Save current configuration variables to preferences file
    Call this when settings are changed
    """
    try:
        from .preferences import update_preferences, save_preferences
        
        # Prepare preferences update
        updates = {
            "visual": {
                "scale_factor": SCALE_FACTOR,
                "direction_ratio_max_degree": DIRECTION_RATIO_MAX_DEGREE,
                "direction_ratio_max_angular": DIRECTION_RATIO_MAX_ANGULAR,
                "normal_point_radius": NORMAL_POINT_RADIUS,
                "normal_point_center_radius": NORMAL_POINT_CENTER_RADIUS,
                "decisive_point_radius": DECISIVE_POINT_RADIUS,
                "decisive_point_center_radius": DECISIVE_POINT_CENTER_RADIUS
            },
            "data": {
                "augmentation_unit": AUGMENTATION_UNIT
            },
            "export": {
                "file_prefix": EXPORT_FILE_PREFIX,
                "timestamp_format": EXPORT_TIMESTAMP_FORMAT
            },
            "ui": {
                "window_width": DEFAULT_WINDOW_WIDTH,
                "window_height": DEFAULT_WINDOW_HEIGHT,
                "canvas_size": DEFAULT_CANVAS_SIZE
            },
            "logging": {
                "log_level": LOG_LEVEL,
                "log_to_file": LOG_TO_FILE,
                "log_to_console": LOG_TO_CONSOLE
            }
        }
        
        # Update and save preferences
        update_preferences(updates)
        success = save_preferences()
        
        if success:
            print("✅ Preferences saved successfully")
        else:
            print("❌ Failed to save preferences")
            
        return success
        
    except Exception as e:
        print(f"❌ Error saving preferences: {e}")
        return False


def calculate_scale_factor(data_manager, sample_size=10):
    """
    Analyze sample data to determine optimal scale factor for visualization
    
    Args:
        data_manager: DataManager instance with loaded data
        sample_size: Number of frames to sample for analysis
        
    Returns:
        float: Calculated scale factor
    """
    import math
    
    # Sample the first few frames to understand data range
    valid_distances = []
    sample_count = 0
    original_pointer = data_manager.pointer
    
    print("Analyzing data to determine optimal scale factor...")
    
    # Reset to beginning to sample from start (respecting data start line for header detection)
    data_manager._pointer = data_manager._data_start_line
    data_manager._read_pos = -1
    
    while data_manager.has_next() and sample_count < sample_size:
        distances = data_manager.dataframe
        if len(distances) == LIDAR_RESOLUTION + 1:
            for i in range(LIDAR_RESOLUTION):
                try:
                    distance_value = float(distances[i])
                    if not (math.isinf(distance_value) or math.isnan(distance_value)) and distance_value > 0:
                        valid_distances.append(distance_value)
                except (ValueError, TypeError):
                    continue
        data_manager.next()
        sample_count += 1
    
    # Reset data manager to beginning (respecting data start line)
    data_manager._pointer = data_manager._data_start_line
    data_manager._read_pos = -1
    
    if valid_distances:
        # Calculate statistics
        min_dist = min(valid_distances)
        max_dist = max(valid_distances)
        avg_dist = sum(valid_distances) / len(valid_distances)
        
        # Use 90th percentile as effective max to ignore outliers
        valid_distances.sort()
        percentile_90 = valid_distances[int(0.9 * len(valid_distances))]
        
        # Calculate scale factor: target radius / effective max distance
        calculated_scale = TARGET_RADIUS / percentile_90
        
        # Update global scale factor
        global SCALE_FACTOR
        SCALE_FACTOR = calculated_scale
        
        print(f"Data analysis complete:")
        print(f"  Distance range: {min_dist:.1f} - {max_dist:.1f} mm")
        print(f"  Average distance: {avg_dist:.1f} mm")
        print(f"  90th percentile: {percentile_90:.1f} mm")
        print(f"  Calculated scale factor: {calculated_scale:.3f}")
        
        return calculated_scale
    else:
        print("No valid distance data found, using default scale factor")
        return SCALE_FACTOR
