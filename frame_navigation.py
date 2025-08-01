"""
Frame navigation and control logic for the LiDAR Visualizer
"""

from config import LIDAR_RESOLUTION


class FrameNavigator:
    """Handles frame navigation and control operations"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.prev_angular_velocity = 0.0
    
    def update_previous_angular_velocity(self, distances, augmented_mode):
        """Update the previous angular velocity from current frame data"""
        try:
            if distances and len(distances) == LIDAR_RESOLUTION + 1:
                current_angular = float(distances[360])
                if augmented_mode:
                    current_angular = -current_angular
                self.prev_angular_velocity = current_angular
                print(f"Updated previous angular velocity: {self.prev_angular_velocity}")
                return self.prev_angular_velocity
        except (ValueError, TypeError, IndexError):
            self.prev_angular_velocity = 0.0
        return self.prev_angular_velocity
    
    def move_to_frame(self, target_frame):
        """Move to a specific frame number (0-based index)"""
        try:
            max_frame = len(self.data_manager.lines) - 1
            
            # Validate frame number
            if target_frame < 0:
                target_frame = 0
            elif target_frame > max_frame:
                target_frame = max_frame
            
            # Jump to the target frame
            self.data_manager._pointer = target_frame
            # Reset read position to force re-reading of the dataframe
            self.data_manager._read_pos = target_frame - 1
            
            return target_frame
            
        except Exception as e:
            print(f"Error moving to frame: {e}")
            return None
    
    def prev_frame(self):
        """Move to previous frame"""
        if self.data_manager.has_prev():
            self.data_manager.prev()
            return True
        return False
    
    def next_frame(self):
        """Move to next frame"""
        if self.data_manager.has_next():
            self.data_manager.next()
            return True
        return False
    
    def first_frame(self):
        """Jump to first frame"""
        self.data_manager.first()
        return True
    
    def last_frame(self):
        """Jump to last frame"""
        self.data_manager.last()
        return True
    
    def first_modified_frame(self):
        """Jump to first modified frame"""
        if self.data_manager.modified_frames:
            self.data_manager.first_modified()
            return True
        return False
    
    def prev_modified_frame(self):
        """Navigate to previous modified frame"""
        if self.data_manager.has_prev_modified():
            self.data_manager.prev_modified()
            return True
        return False
    
    def next_modified_frame(self):
        """Navigate to next modified frame"""
        if self.data_manager.has_next_modified():
            self.data_manager.next_modified()
            return True
        return False
    
    def last_modified_frame(self):
        """Jump to last modified frame"""
        if self.data_manager.modified_frames:
            self.data_manager.last_modified()
            return True
        return False
    
    def get_current_frame_info(self):
        """Get information about the current frame"""
        try:
            current_frame = self.data_manager._pointer + 1
            total_frames = len(self.data_manager.lines)
            modified_count = len(self.data_manager.modified_frames) if hasattr(self.data_manager, 'modified_frames') else 0
            
            return {
                'current_frame': current_frame,
                'total_frames': total_frames,
                'modified_count': modified_count,
                'has_prev': self.data_manager.has_prev(),
                'has_next': self.data_manager.has_next(),
                'has_prev_modified': self.data_manager.has_prev_modified() if hasattr(self.data_manager, 'has_prev_modified') else False,
                'has_next_modified': self.data_manager.has_next_modified() if hasattr(self.data_manager, 'has_next_modified') else False
            }
        except Exception as e:
            print(f"Error getting frame info: {e}")
            return {
                'current_frame': 0,
                'total_frames': 0,
                'modified_count': 0,
                'has_prev': False,
                'has_next': False,
                'has_prev_modified': False,
                'has_next_modified': False
            }
