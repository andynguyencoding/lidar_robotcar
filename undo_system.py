"""
Undo system for the LiDAR Visualizer
"""

from config import MAX_UNDO_STEPS


class UndoSystem:
    """Manages undo/redo functionality for data modifications"""
    
    def __init__(self):
        self.undo_stack = []  # Stack to track changes: [(frame_index, old_value, new_value), ...]
        self.max_undo_steps = MAX_UNDO_STEPS
    
    def add_change(self, frame_index, old_value, new_value):
        """Add a change to the undo stack"""
        try:
            # Only add if values are actually different
            if str(old_value) != str(new_value):
                self.undo_stack.append((frame_index, old_value, new_value))
                
                # Limit undo stack size
                if len(self.undo_stack) > self.max_undo_steps:
                    self.undo_stack.pop(0)  # Remove oldest entry
                    
                print(f"Added to undo stack: Frame {frame_index}, {old_value} -> {new_value}")
        except Exception as e:
            print(f"Error adding to undo stack: {e}")
    
    def get_last_change(self):
        """Get and remove the last change from the undo stack"""
        if not self.undo_stack:
            return None
        return self.undo_stack.pop()
    
    def has_changes(self):
        """Check if there are changes available to undo"""
        return len(self.undo_stack) > 0
    
    def clear(self):
        """Clear the undo stack"""
        self.undo_stack.clear()
    
    def get_stack_size(self):
        """Get the current size of the undo stack"""
        return len(self.undo_stack)
