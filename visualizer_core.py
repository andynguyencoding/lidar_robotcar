"""
Core VisualizerWindow class - main application controller
"""

import tkinter as tk
import os
import traceback
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk, messagebox
from config import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, LIDAR_RESOLUTION
from ui_components import UIManager
from frame_navigation import FrameNavigator
from file_manager import FileManager
from undo_system import UndoSystem
from data_statistics import DataAnalyzer
from visualization_renderer import VisualizationRenderer
from pginput import DataManager
from logger import get_logger, debug, info, warning, error, log_ui_event, log_navigation, log_dataset_operation, log_function
from ai_model import is_ai_model_loaded, load_ai_model, get_ai_prediction, get_ai_model_info
from tkinter import messagebox, filedialog


def calculate_scale_factor(data_manager, sample_size=10):
    """Calculate appropriate scale factor - imported from main utilities"""
    from main import calculate_scale_factor as calc_scale
    calc_scale(data_manager, sample_size)


class VisualizerWindow:
    """Main visualizer window and application controller"""
    
    def __init__(self, config):
        self.config = config
        self.running = True
        self.paused = True  # Start paused by default
        self.inspect_mode = True  # Start in inspection mode by default
        self.augmented_mode = config['augmented_mode']
        
        # Direction ratio configuration (angular velocity to degree mapping)
        self.direction_ratio_max_degree = 45.0
        self.direction_ratio_max_angular = 1.0
        
        # Track unsaved changes
        self.has_unsaved_changes = False
        self.original_title = f"Lidar Visualizer - {os.path.basename(config['data_file'])}"
        
        # Initialize subsystems
        self.file_manager = FileManager()
        
        # Dataset management - ID-based approach for splits
        self.main_dataset = None  # Original full dataset (single source of truth)
        self.train_ids = []       # List of frame IDs for train dataset
        self.val_ids = []         # List of frame IDs for validation dataset  
        self.test_ids = []        # List of frame IDs for test dataset
        self.current_dataset_type = 'main'  # 'main', 'train', 'validation', 'test'
        self.current_dataset_position = 0   # Position within current dataset
        
        # Separate pointers for each dataset to maintain navigation state
        self.main_pointer = 0       # Pointer for original dataset
        self.train_pointer = 0      # Pointer for train dataset (position within train_ids)
        self.val_pointer = 0        # Pointer for validation dataset (position within val_ids)
        self.test_pointer = 0       # Pointer for test dataset (position within test_ids)
        self.undo_system = UndoSystem()
        self.data_analyzer = DataAnalyzer()
        
        # Initialize data manager
        self.data_manager = DataManager(config['data_file'], 'data/run2/_out.txt', False)
        
        # Set up main dataset as the original full dataset
        self.main_dataset = self.data_manager
        calculate_scale_factor(self.data_manager)
        
        # Initialize frame navigator
        self.frame_navigator = FrameNavigator(self.data_manager)
        
        # Create main tkinter window
        self.root = tk.Tk()
        self.root.title(self.original_title)
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.root.resizable(True, True)
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (DEFAULT_WINDOW_WIDTH // 2)
        y = (self.root.winfo_screenheight() // 2) - (DEFAULT_WINDOW_HEIGHT // 2)
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}+{x}+{y}")
        
        # Initialize visualization renderer
        self.renderer = VisualizationRenderer()
        
        # Setup UI with callbacks
        callbacks = self._get_callbacks()
        self.ui_manager = UIManager(self.root, callbacks)
        self.ui_manager.setup_ui()
        
        # Bind resize event for dynamic scaling
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Initialize pygame after UI setup
        self.init_pygame()
        
        # Initialize variables and load initial data
        self.distances = []
        self.load_initial_frame()
        
        # Update button states after everything is set up
        self.update_button_states()
        
        # Add current file to recent files
        self.file_manager.add_recent_file(config['data_file'])
        self.ui_manager.update_recent_files_menu(self.file_manager.get_recent_files(), self.load_recent_file)
        
        # Update initial UI state
        self.update_status()
        self.update_inputs()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup animation timer
        self.animate()
    
    def load_initial_frame(self):
        """Load the initial frame data from the data manager"""
        try:
            # Ensure data manager starts at first data frame (skip header if present)
            if hasattr(self.data_manager, '_pointer'):
                # Start from the data start line (0 if no header, 1 if header present)
                start_line = getattr(self.data_manager, '_data_start_line', 0)
                self.data_manager._pointer = start_line
                self.data_manager._read_pos = -1  # Force reading of first frame
            
            # Get the first frame data
            self.distances = self.data_manager.dataframe
            
            if self.distances and len(self.distances) == 361:
                print(f"Initial frame loaded: {len(self.distances)} data points")
                self.render_frame()
                self.update_inputs()
            else:
                print(f"Warning: Initial frame has {len(self.distances) if self.distances else 0} data points, expected 361")
        except Exception as e:
            print(f"Error loading initial frame: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_callbacks(self):
        """Get callback functions for UI components"""
        return {
            # Frame navigation
            'first_frame': self.first_frame,
            'prev_frame': self.prev_frame,
            'next_frame': self.next_frame,
            'last_frame': self.last_frame,
            'first_modified_frame': self.first_modified_frame,
            'prev_modified_frame': self.prev_modified_frame,
            'next_modified_frame': self.next_modified_frame,
            'last_modified_frame': self.last_modified_frame,
            'on_frame_input': self.on_frame_input,
            
            # Control functions
            'toggle_pause': self.toggle_pause,
            'toggle_inspect': self.toggle_inspect,
            'toggle_augmented': self.toggle_augmented,  # Keep for backward compatibility
            'flip_horizontal': self.flip_horizontal,
            'flip_vertical': self.flip_vertical,
            'quit_visualizer': self.quit_visualizer,
            
            # Input handling
            'on_angular_velocity_input': self.on_angular_velocity_input,
            'on_linear_velocity_input': self.on_linear_velocity_input,
            'replace_with_previous': self.replace_with_previous,
            'on_key_press': self.on_key_press,
            'on_visualization_toggle': self.on_visualization_toggle,
            
            # File operations
            'browse_data_file': self.browse_data_file,
            'save_data': self.save_data,
            'show_data_statistics': self.show_data_statistics,
            
            # AI functions
            'browse_ai_model': self.browse_ai_model,
            'show_ai_model_info': self.show_ai_model_info,
            'clear_ai_model': self.clear_ai_model,
            'show_kbest_analysis': self.show_kbest_analysis,
            'show_current_kbest_positions': self.show_current_kbest_positions,
            
            # Help functions
            'show_about_dialog': self.show_about_dialog,
            'show_controls_dialog': self.show_controls_dialog,
            
            # Visual settings
            'show_scale_factor_dialog': self.show_scale_factor_dialog,
            'show_direction_ratio_dialog': self.show_direction_ratio_dialog,
            'zoom_in': self.zoom_in,
            'zoom_out': self.zoom_out,
            
            # Settings
            'show_logging_config': self.show_logging_config,
            'show_log_viewer': self.show_log_viewer,
            'show_preferences_dialog': self.show_preferences_dialog,
            
            # Application control
            'quit_app': self.quit_visualizer,
            
            # Augmentation controls - Rotation only
            'rotate_cw': self.rotate_cw,
            'rotate_ccw': self.rotate_ccw,
            'add_augmented_frames': self.add_augmented_frames,
            'duplicate_current_frame': self.duplicate_current_frame,
            
            # Data splitting controls
            'split_data': self.split_data,
            'move_to_next_set': self.move_to_next_set,
            'on_dataset_selection_changed': self.on_dataset_selection_changed
        }
    
    def on_window_resize(self, event):
        """Handle window resize events and scale canvas accordingly"""
        if event.widget == self.root:
            # Calculate available space for canvas
            available_width = self.root.winfo_width() - 170
            available_height = self.root.winfo_height() - 170
            
            # Calculate optimal canvas size
            max_canvas_size = min(available_width, available_height, 800)
            new_canvas_size = max(300, max_canvas_size)
            
            # Only update if size changed significantly
            if abs(new_canvas_size - self.ui_manager.current_canvas_size) > 10:
                self.ui_manager.update_canvas_size(new_canvas_size)
                self.renderer.update_canvas_size(new_canvas_size)
    
    def init_pygame(self):
        """Initialize pygame with proper embedding"""
        success = self.renderer.init_pygame(self.ui_manager.canvas)
        if not success:
            messagebox.showerror("Error", "Failed to initialize pygame visualization")
    
    def update_previous_angular_velocity(self):
        """Update the previous angular velocity from current frame data"""
        try:
            if self.distances and len(self.distances) == 361:  # LIDAR_RESOLUTION + 1
                current_angular = float(self.distances[360])
                if self.augmented_mode:
                    current_angular = -current_angular
                self.frame_navigator.prev_angular_velocity = current_angular
                
                # Update the previous angular velocity display
                self.ui_manager.prev_turn_var.set(f"{current_angular:.2f}")
                print(f"Updated previous angular velocity: {current_angular}")
        except (ValueError, TypeError, IndexError):
            self.frame_navigator.prev_angular_velocity = 0.0
            self.ui_manager.prev_turn_var.set("0.00")

    # Frame navigation methods
    def prev_frame(self):
        """Move to previous frame in inspect mode"""
        print(f"DEBUG: prev_frame() called")
        
        if not self.inspect_mode:
            print(f"DEBUG: Not in inspect mode, returning")
            return
        
        print(f"DEBUG: current_dataset_type = {self.current_dataset_type}")
        print(f"DEBUG: hasattr(self, 'train_ids') = {hasattr(self, 'train_ids')}")
        
        # Check if we're in a split dataset mode
        if self.current_dataset_type != 'main' and hasattr(self, 'train_ids'):
            print(f"DEBUG: Using dataset navigation for {self.current_dataset_type}")
            current_pointer = self._get_current_dataset_pointer()
            print(f"DEBUG: Current pointer before navigation: {current_pointer}")
            
            result = self._navigate_dataset_frame('prev')
            print(f"DEBUG: _navigate_dataset_frame returned: {result}")
        elif self.frame_navigator.prev_frame():
            print(f"DEBUG: Using frame navigator (main dataset)")
            # Original navigation logic for main dataset
            self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
            
            self.distances = self.data_manager.dataframe
            if len(self.distances) == 361:  # LIDAR_RESOLUTION + 1
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Moved to previous frame: {self.data_manager.read_pos + 1}/{len(self.data_manager.lines)}")
        else:
            print(f"DEBUG: No navigation occurred - frame_navigator.prev_frame() returned False")

    def next_frame(self):
        """Move to next frame in inspect mode"""
        print(f"DEBUG: next_frame() called")
        
        if not self.inspect_mode:
            print(f"DEBUG: Not in inspect mode, returning")
            return
        
        print(f"DEBUG: current_dataset_type = {self.current_dataset_type}")
        print(f"DEBUG: hasattr(self, 'train_ids') = {hasattr(self, 'train_ids')}")
            
        # Check if we're in a split dataset mode
        if self.current_dataset_type != 'main' and hasattr(self, 'train_ids'):
            print(f"DEBUG: Using dataset navigation for {self.current_dataset_type}")
            current_pointer = self._get_current_dataset_pointer()
            print(f"DEBUG: Current pointer before navigation: {current_pointer}")
            
            result = self._navigate_dataset_frame('next')
            print(f"DEBUG: _navigate_dataset_frame returned: {result}")
        elif self.frame_navigator.next_frame():
            print(f"DEBUG: Using frame navigator (main dataset)")
            # Original navigation logic for main dataset
            self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
            
            self.distances = self.data_manager.dataframe
            if len(self.distances) == 361:  # LIDAR_RESOLUTION + 1
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Moved to next frame: {self.data_manager.read_pos + 1}/{len(self.data_manager.lines)}")
        else:
            print(f"DEBUG: No navigation occurred - frame_navigator.next_frame() returned False")
    
    def _navigate_dataset_frame(self, direction):
        """Navigate within the current ID-based dataset"""
        dataset_ids = self._get_current_dataset_ids()
        
        # Get current pointer and update based on direction
        current_pointer = self._get_current_dataset_pointer()
        old_position = current_pointer
        
        print(f"DEBUG: _navigate_dataset_frame({direction}) - current_pointer={current_pointer}, dataset_size={len(dataset_ids)}")
        
        if direction == 'prev' and current_pointer > 0:
            new_position = current_pointer - 1
        elif direction == 'next' and current_pointer < len(dataset_ids) - 1:
            new_position = current_pointer + 1
        else:
            print(f"Navigation blocked: {direction} not possible from position {current_pointer} in {self.current_dataset_type} dataset")
            return False  # Return False when navigation is blocked
        
        # Set the new position using the dataset pointer system
        self._set_current_dataset_pointer(new_position)
        
        # Get updated position for display
        self.current_dataset_position = new_position  # Keep for backward compatibility
        new_pointer = self._get_current_dataset_pointer()
        
        # Navigate to the frame ID in the original dataset
        frame_id = self._get_current_frame_id()
        print(f"Navigation: {self.current_dataset_type.upper()} {old_position}→{new_pointer} (Frame ID: {frame_id})")
        self._navigate_to_frame_id(frame_id)
        
        # Update the display
        self.distances = self.data_manager.dataframe
        if len(self.distances) == 361:  # LIDAR_RESOLUTION + 1
            self.render_frame()
            self.update_inputs()
        
        self.update_button_states()
        print(f"Dataset navigation: {self.current_dataset_type.upper()} frame {new_pointer + 1}/{len(dataset_ids)} (ID: {frame_id})")
        return True  # Return True when navigation is successful
            
        # Check if data has been split into datasets
        if hasattr(self.ui_manager, 'data_splits') and self.ui_manager.data_splits:
            self.navigate_dataset_frame('next')
        elif self.frame_navigator.next_frame():
            # Original navigation logic
            self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
            
            self.distances = self.data_manager.dataframe
            if len(self.distances) == 361:  # LIDAR_RESOLUTION + 1
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Moved to next frame: {self.data_manager.read_pos + 1}/{len(self.data_manager.lines)}")
    
    def first_frame(self):
        """Jump to first frame in inspect mode"""
        if not self.inspect_mode:
            return
            
        # Check if data has been split into datasets
        if hasattr(self.ui_manager, 'data_splits') and self.ui_manager.data_splits:
            self.navigate_dataset_frame('first')
        elif self.frame_navigator.first_frame():
            # Original navigation logic
            self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
            
            self.distances = self.data_manager.dataframe
            if len(self.distances) == 361:
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Jumped to first frame: {self.data_manager.read_pos + 1}/{len(self.data_manager.lines)}")

    def last_frame(self):
        """Jump to last frame in inspect mode"""
        if not self.inspect_mode:
            return
            
        # Check if data has been split into datasets
        if hasattr(self.ui_manager, 'data_splits') and self.ui_manager.data_splits:
            self.navigate_dataset_frame('last')
        elif self.frame_navigator.last_frame():
            # Original navigation logic
            self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
            
            self.distances = self.data_manager.dataframe
            if len(self.distances) == 361:
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Jumped to last frame: {self.data_manager.read_pos + 1}/{len(self.data_manager.lines)}")
    
    # Modified frame navigation methods
    def first_modified_frame(self):
        """Jump to first modified frame"""
        if self.inspect_mode and self.frame_navigator.first_modified_frame():
            self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
            
            self.distances = self.data_manager.dataframe
            if len(self.distances) == 361:
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Jumped to first modified frame: {self.data_manager.get_modified_position_info()}")
    
    def prev_modified_frame(self):
        """Navigate to previous modified frame"""
        if self.inspect_mode and self.frame_navigator.prev_modified_frame():
            self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
            
            self.distances = self.data_manager.dataframe
            if len(self.distances) == 361:
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Previous modified frame: {self.data_manager.get_modified_position_info()}")
    
    def next_modified_frame(self):
        """Navigate to next modified frame"""
        if self.inspect_mode and self.frame_navigator.next_modified_frame():
            self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
            
            self.distances = self.data_manager.dataframe
            if len(self.distances) == 361:
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Next modified frame: {self.data_manager.get_modified_position_info()}")
    
    def last_modified_frame(self):
        """Jump to last modified frame"""
        if self.inspect_mode and self.frame_navigator.last_modified_frame():
            self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
            
            self.distances = self.data_manager.dataframe
            if len(self.distances) == 361:
                self.render_frame()
                self.update_inputs()
            
            self.update_button_states()
            print(f"Jumped to last modified frame: {self.data_manager.get_modified_position_info()}")
    
    def on_frame_input(self, event):
        """Handle frame number input - jump directly to specified frame"""
        try:
            frame_input = self.ui_manager.frame_var.get().strip()
            if not frame_input:
                return
                
            target_frame = int(frame_input) - 1  # Convert to 0-based index
            result = self.frame_navigator.move_to_frame(target_frame)
            
            if result is not None:
                # Update distances from the new frame
                self.distances = self.data_manager.dataframe
                
                # Update visualization
                self.render_frame()
                self.update_inputs()
                
                # Update button states
                if self.inspect_mode:
                    self.update_button_states()
                    
                # Update frame input to show actual frame number
                self.ui_manager.frame_var.set(str(result + 1))
                
                # Remove focus from text field
                self.root.focus_set()
                
                print(f"Jumped to frame {result + 1}")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid frame number")
            frame_info = self.frame_navigator.get_current_frame_info()
            self.ui_manager.frame_var.set(str(frame_info['current_frame']))
        except Exception as e:
            error_msg = f"Error jumping to frame: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error in on_frame_input: {e}")
    
    # Control methods
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        self.update_status()
        self.update_button_states()
        print(f'PAUSE STATUS: {self.paused}')
    
    def toggle_inspect(self):
        """Toggle inspection mode"""
        self.inspect_mode = not self.inspect_mode
        if self.inspect_mode:
            self.paused = True
        else:
            self.paused = False
        self.update_status()
        self.update_button_states()
        print(f'INSPECT MODE: {self.inspect_mode}')
    
    def toggle_augmented(self):
        """Toggle augmented mode - flips the current frame data horizontally"""
        if not hasattr(self, 'data_manager') or not self.data_manager:
            print("No data manager available")
            return
            
        try:
            # Get current frame data
            current_line = self.data_manager.lines[self.data_manager.pointer]
            
            # Parse the data (expecting 360 LiDAR readings + angular velocity)
            data_parts = current_line.strip().split(',')
            if len(data_parts) < 361:
                print(f"Invalid data format: expected 361 values, got {len(data_parts)}")
                return
            
            # Extract LiDAR readings (first 360 values) and angular velocity (last value)
            lidar_readings = [float(x) for x in data_parts[:360]]
            angular_velocity = float(data_parts[360])
            
            # Flip the LiDAR data horizontally by mapping angles
            # For horizontal flip: angle -> (180 - angle) % 360
            # This means: index i -> index (180 - i) % 360
            flipped_lidar = [0.0] * 360
            for i in range(360):
                # Calculate the flipped angle index
                flipped_index = (180 - i) % 360
                flipped_lidar[flipped_index] = lidar_readings[i]
            
            # Negate the angular velocity for horizontal flip
            flipped_angular_velocity = -angular_velocity
            
            # Reconstruct the data line in CSV format (360 distance values + angular velocity)
            # Ensure all values are properly formatted as strings
            flipped_data_strings = [str(float(x)) for x in flipped_lidar] + [str(float(flipped_angular_velocity))]
            flipped_line = ','.join(flipped_data_strings)
            
            # Ensure the line ends with a newline character (preserve original format)
            if not flipped_line.endswith('\n'):
                flipped_line += '\n'
            
            # Update the data in memory
            self.data_manager.lines[self.data_manager.pointer] = flipped_line
            
            # Invalidate the dataframe cache to force re-reading the modified data
            self.data_manager._read_pos = -1
            
            # Mark this frame as modified so it gets saved
            if self.data_manager.pointer not in self.data_manager._modified_frames:
                self.data_manager._modified_frames.append(self.data_manager.pointer)
                self.data_manager._modified_frames.sort()  # Keep the list sorted
            
            # Toggle the mode flag for display purposes (track if current frame is flipped)
            self.augmented_mode = not self.augmented_mode
            
            print(f'Frame {self.data_manager.pointer} flipped horizontally (angle mapping applied)')
            print(f"Angular velocity changed from {angular_velocity:.3f} to {flipped_angular_velocity:.3f}")
            print(f"Modified frames list: {self.data_manager._modified_frames}")
            print(f"First few values of flipped line: {flipped_lidar[:5]}")
            
            self.update_status()
            
            # Force refresh the current frame display to show the flipped data
            if hasattr(self, 'refresh_current_frame'):
                self.refresh_current_frame()
            else:
                # Trigger a redraw by rendering the frame
                self.render_frame()
            
        except Exception as e:
            print(f"Error flipping frame data: {e}")
            import traceback
            traceback.print_exc()
    
    def flip_horizontal(self):
        """Flip the current frame data horizontally (left-right mirror)"""
        if not hasattr(self, 'data_manager') or not self.data_manager:
            print("No data manager available")
            return
            
        try:
            # Check if "Apply to All Frames" is checked
            if hasattr(self, 'ui_manager') and hasattr(self.ui_manager, 'flip_all_var') and self.ui_manager.flip_all_var.get():
                self._flip_all_frames_horizontal()
            else:
                self._flip_single_frame_horizontal(self.data_manager.pointer)
                
                # For single frame operations, update UI immediately
                # Invalidate the dataframe cache to force re-reading the modified data
                self.data_manager._read_pos = -1
                
                # Mark data as changed (add asterisk to title)
                self.mark_data_changed()
                
                print(f'Frame {self.data_manager.pointer} flipped horizontally (left-right mirror)')
                
                self.update_status()
                
                # Force refresh the display
                if hasattr(self, 'refresh_current_frame'):
                    self.refresh_current_frame()
                else:
                    self.render_frame()
                
        except Exception as e:
            print(f"Error flipping frame horizontally: {e}")
            import traceback
            traceback.print_exc()
    
    def _flip_single_frame_horizontal(self, frame_index):
        """Apply horizontal flip to a single frame"""
        # Get frame data
        current_line = self.data_manager.lines[frame_index]
        
        # Parse the data (expecting 360 LiDAR readings + angular velocity)
        data_parts = current_line.strip().split(',')
        if len(data_parts) < 361:
            print(f"Invalid data format: expected 361 values, got {len(data_parts)}")
            return
        
        # Extract LiDAR readings (first 360 values) and angular velocity (last value)
        lidar_readings = [float(x) for x in data_parts[:360]]
        angular_velocity = float(data_parts[360])
        
        # Flip the LiDAR data horizontally using your algorithm: 0↔359, 1↔358, etc.
        flipped_lidar = [0.0] * 360
        for i in range(360):
            # Horizontal flip: swap left and right sides
            flipped_index = (359 - i) % 360
            flipped_lidar[flipped_index] = lidar_readings[i]
        
        # Negate the angular velocity for horizontal flip
        flipped_angular_velocity = -angular_velocity
        
        # Reconstruct the data line in CSV format
        flipped_data_strings = [str(float(x)) for x in flipped_lidar] + [str(float(flipped_angular_velocity))]
        flipped_line = ','.join(flipped_data_strings)
        
        # Ensure the line ends with a newline character
        if not flipped_line.endswith('\n'):
            flipped_line += '\n'
        
        # Update the data in memory
        self.data_manager.lines[frame_index] = flipped_line
        
        # Mark this frame as modified so it gets saved
        if frame_index not in self.data_manager._modified_frames:
            self.data_manager._modified_frames.append(frame_index)
            self.data_manager._modified_frames.sort()
    
    def _flip_all_frames_horizontal(self):
        """Apply horizontal flip to all frames"""
        total_frames = len(self.data_manager.lines)
        print(f"Applying horizontal flip to all {total_frames} frames...")
        
        for frame_index in range(total_frames):
            self._flip_single_frame_horizontal(frame_index)
        
        # Invalidate the dataframe cache to force re-reading the modified data
        self.data_manager._read_pos = -1
        
        # Mark data as changed (add asterisk to title)
        self.mark_data_changed()
        
        print(f'All {total_frames} frames flipped horizontally')
        print(f"Modified frames list: {len(self.data_manager._modified_frames)} frames")
        
        self.update_status()
        
        # Force refresh the display
        if hasattr(self, 'refresh_current_frame'):
            self.refresh_current_frame()
        else:
            self.render_frame()
    
    def flip_vertical(self):
        """Flip the current frame data vertically (forward-backward mirror)"""
        if not hasattr(self, 'data_manager') or not self.data_manager:
            print("No data manager available")
            return
            
        try:
            # Check if "Apply to All Frames" is checked
            if hasattr(self, 'ui_manager') and hasattr(self.ui_manager, 'flip_all_var') and self.ui_manager.flip_all_var.get():
                self._flip_all_frames_vertical()
            else:
                self._flip_single_frame_vertical(self.data_manager.pointer)
                
                # For single frame operations, update UI immediately
                # Invalidate the dataframe cache to force re-reading the modified data
                self.data_manager._read_pos = -1
                
                # Mark data as changed (add asterisk to title)
                self.mark_data_changed()
                
                print(f'Frame {self.data_manager.pointer} flipped vertically (forward-backward mirror)')
                
                self.update_status()
                
                # Force refresh the display
                if hasattr(self, 'refresh_current_frame'):
                    self.refresh_current_frame()
                else:
                    self.render_frame()
                    
        except Exception as e:
            print(f"Error flipping frame vertically: {e}")
            import traceback
            traceback.print_exc()
    
    def _flip_single_frame_vertical(self, frame_index):
        """Apply vertical flip to a single frame"""
        # Get frame data
        current_line = self.data_manager.lines[frame_index]
        
        # Parse the data (expecting 360 LiDAR readings + angular velocity)
        data_parts = current_line.strip().split(',')
        if len(data_parts) < 361:
            print(f"Invalid data format: expected 361 values, got {len(data_parts)}")
            return
        
        # Extract LiDAR readings (first 360 values) and angular velocity (last value)
        lidar_readings = [float(x) for x in data_parts[:360]]
        angular_velocity = float(data_parts[360])
        
        # Flip the LiDAR data vertically: forward↔backward
        flipped_lidar = [0.0] * 360
        for i in range(360):
            # Vertical flip: 0°↔180°, 90° stays 90°, 270° stays 270°
            flipped_index = (180 - i) % 360
            flipped_lidar[flipped_index] = lidar_readings[i]
        
        # Keep the angular velocity the same for vertical flip (no left-right change)
        flipped_angular_velocity = angular_velocity
        
        # Reconstruct the data line in CSV format
        flipped_data_strings = [str(float(x)) for x in flipped_lidar] + [str(float(flipped_angular_velocity))]
        flipped_line = ','.join(flipped_data_strings)
        
        # Ensure the line ends with a newline character
        if not flipped_line.endswith('\n'):
            flipped_line += '\n'
        
        # Update the data in memory
        self.data_manager.lines[frame_index] = flipped_line
        
        # Mark this frame as modified so it gets saved
        if frame_index not in self.data_manager._modified_frames:
            self.data_manager._modified_frames.append(frame_index)
            self.data_manager._modified_frames.sort()
    
    def _flip_all_frames_vertical(self):
        """Apply vertical flip to all frames"""
        total_frames = len(self.data_manager.lines)
        print(f"Applying vertical flip to all {total_frames} frames...")
        
        for frame_index in range(total_frames):
            self._flip_single_frame_vertical(frame_index)
        
        # Invalidate the dataframe cache to force re-reading the modified data
        self.data_manager._read_pos = -1
        
        # Mark data as changed (add asterisk to title)
        self.mark_data_changed()
        
        print(f'All {total_frames} frames flipped vertically')
        print(f"Modified frames list: {len(self.data_manager._modified_frames)} frames")
        
        self.update_status()
        
        # Force refresh the display
        if hasattr(self, 'refresh_current_frame'):
            self.refresh_current_frame()
        else:
            self.render_frame()
    
    def quit_visualizer(self):
        """Quit the visualizer"""
        self.on_closing()
    
    def mark_data_changed(self):
        """Mark that the data has unsaved changes and update window title"""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self.root.title(self.original_title + " *")
    
    def mark_data_saved(self):
        """Mark that the data has been saved and update window title"""
        if self.has_unsaved_changes:
            self.has_unsaved_changes = False
            self.root.title(self.original_title)
    
    def prompt_save_before_exit(self):
        """Prompt user to save changes before exiting"""
        if not self.has_unsaved_changes:
            return True  # No changes, safe to exit
        
        result = messagebox.askyesnocancel(
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save before exiting?",
            icon='warning'
        )
        
        if result is True:  # Yes - save and exit
            try:
                self.data_manager.save_to_original_file()
                self.mark_data_saved()
                return True
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save changes:\n{str(e)}")
                return False
        elif result is False:  # No - exit without saving
            return True
        else:  # Cancel - don't exit
            return False
    
    # Input handling
    def on_angular_velocity_input(self, event):
        """Handle angular velocity input"""
        try:
            new_value = self.ui_manager.turn_var.get()
            if new_value != "":
                # Store old value for undo
                old_value = str(self.distances[360]) if len(self.distances) > 360 else "0.0"
                current_frame = self.data_manager._pointer
                
                # Add to undo stack
                self.undo_system.add_change(current_frame, old_value, new_value)
                
                # Update the data
                if len(self.distances) == 361:
                    self.distances[360] = float(new_value)
                    
                    # Update the original line data in memory (same as DataManager.update method)
                    updated_line = ','.join(str(x) for x in self.distances)
                    self.data_manager.lines[self.data_manager._pointer] = updated_line + '\n'
                    
                    # Track this frame as modified (following DataManager pattern)
                    current_frame = self.data_manager._pointer
                    if current_frame not in self.data_manager._modified_frames:
                        self.data_manager._modified_frames.append(current_frame)
                        self.data_manager._modified_frames.sort()  # Keep the list sorted
                        # Update the modified pointer to point to the current frame
                        self.data_manager._modified_pointer = self.data_manager._modified_frames.index(current_frame)
                    
                    # Update display
                    self.render_frame()
                    self.update_inputs()
                    self.update_button_states()
                    
                    # Mark data as changed
                    self.mark_data_changed()
                    
                    print(f"Updated angular velocity to {new_value} at frame {current_frame}")
                
                # Remove focus from the input field to allow keyboard navigation
                self.ui_manager.turn_entry.selection_clear()
                self.root.focus_set()
        except (ValueError, TypeError) as e:
            messagebox.showerror("Invalid Input", "Please enter a valid numeric value")
            print(f"Error updating angular velocity: {e}")
    
    def on_linear_velocity_input(self, event):
        """Handle linear velocity input (not implemented)"""
        messagebox.showinfo("Not Implemented", "Linear velocity editing is not yet implemented")
    
    def replace_with_previous(self):
        """Replace current angular velocity with previous frame's angular velocity"""
        try:
            prev_value = self.frame_navigator.prev_angular_velocity
            if prev_value is not None:
                # Store old value for undo
                old_value = self.ui_manager.turn_var.get() if self.ui_manager.turn_var.get() else "0.0"
                current_frame = self.data_manager._pointer
                
                # Add to undo stack
                self.undo_system.add_change(current_frame, old_value, str(prev_value))
                
                # Set the new value
                self.ui_manager.turn_var.set(str(prev_value))
                
                # Trigger the update
                class MockEvent:
                    pass
                self.on_angular_velocity_input(MockEvent())
                
                print(f"Replaced current angular velocity with previous: {prev_value}")
            else:
                print("No previous angular velocity available")
        except Exception as e:
            error_msg = f"Error replacing angular velocity: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error in replace_with_previous: {e}")
    
    def on_key_press(self, event):
        """Handle keyboard events"""
        # Check if any text field is focused
        try:
            turn_focus = self.ui_manager.turn_entry.focus_get()
            frame_focus = self.ui_manager.frame_entry.focus_get()
            
            if (turn_focus == self.ui_manager.turn_entry or 
                frame_focus == self.ui_manager.frame_entry):
                if event.keysym.lower() in ['i', 'h', 'v', 'q']:
                    pass
                else:
                    return
        except:
            # If focus checking fails, assume no focus and continue
            pass
        
        if event.keysym == 'space':
            if self.inspect_mode:
                self.next_frame()
            else:
                self.toggle_pause()
        elif event.keysym.lower() == 'i':
            self.toggle_inspect()
        elif event.keysym.lower() == 'h':
            self.flip_horizontal()
        elif event.keysym.lower() == 'v':
            self.flip_vertical()
        elif event.keysym.lower() == 'q':
            self.quit_visualizer()
        elif event.keysym.lower() == 'r':
            self.replace_with_previous()
        elif event.keysym.lower() == 'u':
            self.undo_last_change()
        elif event.keysym == 'Left' and self.inspect_mode:
            self.prev_frame()
        elif event.keysym == 'Right' and self.inspect_mode:
            self.next_frame()
        elif event.keysym == 'Home' and self.inspect_mode:
            self.first_frame()
        elif event.keysym == 'End' and self.inspect_mode:
            self.last_frame()
        elif event.keysym == 'Up' and self.inspect_mode:
            self.prev_modified_frame()
        elif event.keysym == 'Down' and self.inspect_mode:
            self.next_modified_frame()
        elif event.keysym == 'Prior' and self.inspect_mode:
            self.first_modified_frame()
        elif event.keysym == 'Next' and self.inspect_mode:
            self.last_modified_frame()
    
    def on_visualization_toggle(self):
        """Callback for visualization toggle checkboxes"""
        try:
            if self.distances and len(self.distances) == 361:
                self.render_frame()
                print("Visualization toggles updated - canvas redrawn")
        except Exception as e:
            print(f"Error in visualization toggle callback: {e}")
    
    def zoom_in(self):
        """Increase the pygame scale factor by 10%"""
        try:
            import config
            new_scale = config.SCALE_FACTOR * 1.1
            config.SCALE_FACTOR = new_scale
            
            # Re-render the current frame with new scale factor
            if self.distances and len(self.distances) == 361:
                self.render_frame()
            
            print(f"Zoomed in - Scale factor: {config.SCALE_FACTOR:.4f}")
            
        except Exception as e:
            print(f"Error zooming in: {e}")
            messagebox.showerror("Zoom Error", f"Error zooming in:\n{str(e)}")
    
    def zoom_out(self):
        """Decrease the pygame scale factor by 10%"""
        try:
            import config
            new_scale = config.SCALE_FACTOR * 0.9
            
            # Prevent scale factor from becoming too small
            if new_scale < 0.01:
                new_scale = 0.01
                
            config.SCALE_FACTOR = new_scale
            
            # Re-render the current frame with new scale factor
            if self.distances and len(self.distances) == 361:
                self.render_frame()
            
            print(f"Zoomed out - Scale factor: {config.SCALE_FACTOR:.4f}")
            
        except Exception as e:
            print(f"Error zooming out: {e}")
            messagebox.showerror("Zoom Error", f"Error zooming out:\n{str(e)}")
    
    def undo_last_change(self):
        """Undo the last change made"""
        try:
            change = self.undo_system.get_last_change()
            if change is None:
                print("Nothing to undo")
                return
            
            frame_index, old_value, new_value = change
            
            # Navigate to the frame that was changed
            current_frame = self.data_manager._pointer
            if current_frame != frame_index:
                result = self.frame_navigator.move_to_frame(frame_index)
                if result is not None:
                    self.update_display()
            
            # Restore the old value
            self.ui_manager.turn_var.set(str(old_value))
            
            # Update the data
            if len(self.distances) == 361:
                self.distances[360] = old_value
                
                # Update the data manager
                if hasattr(self.data_manager, '_lidar_dataframe'):
                    self.data_manager._lidar_dataframe[360] = old_value
                    updated_line = ','.join(str(x) for x in self.data_manager._lidar_dataframe)
                    self.data_manager.lines[self.data_manager._pointer] = updated_line + '\n'
                
                print(f"Undone change: Frame {frame_index}, restored to {old_value} (was {new_value})")
                
                # Mark data as changed since we modified it
                self.mark_data_changed()
                
                # Update UI
                self.update_inputs()
                self.render_frame()
                
        except Exception as e:
            error_msg = f"Error during undo: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error in undo_last_change: {e}")
    
    # File operations
    def browse_data_file(self):
        """Browse for a new data file and load it"""
        filename = self.file_manager.browse_data_file()
        if filename:
            self.load_data_file(filename)
    
    def load_data_file(self, filename):
        """Load a data file and update the application state"""
        try:
            # Update status
            old_status = self.ui_manager.status_var.get()
            self.ui_manager.status_var.set("Loading data file...")
            self.root.update()
            
            # Create new data manager
            self.data_manager = DataManager(filename, 'data/run2/_out.txt', False)
            calculate_scale_factor(self.data_manager)
            
            # Update frame navigator
            self.frame_navigator = FrameNavigator(self.data_manager)
            
            # Update config
            self.config['data_file'] = filename
            
            # Update window title
            self.root.title(f"Lidar Visualizer - {os.path.basename(filename)}")
            
            # Reset state
            self.distances = []
            self.undo_system.clear()
            
            # Load initial frame with new data
            self.load_initial_frame()
            
            # Update button states to reflect new data
            self.update_button_states()
            
            # Update status
            self.update_status()
            
            # Add to recent files
            self.file_manager.add_recent_file(filename)
            self.ui_manager.update_recent_files_menu(self.file_manager.get_recent_files(), self.load_recent_file)
            
            print(f"Successfully loaded data file: {filename}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to load data file: {str(e)}"
            messagebox.showerror("Error", error_msg)
            if 'old_status' in locals():
                self.ui_manager.status_var.set(old_status)
            print(f"Error loading data file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_recent_file(self, file_path):
        """Load a file from the recent files list"""
        if self.file_manager.file_exists(file_path):
            self.load_data_file(file_path)
        else:
            # File no longer exists, remove from recent files
            self.file_manager.recent_files.remove(file_path)
            self.file_manager.save_recent_files()
            self.ui_manager.update_recent_files_menu(self.file_manager.get_recent_files(), self.load_recent_file)
            messagebox.showerror("File Not Found", f"File not found:\n{file_path}")
    
    def save_data(self):
        """Save the current data back to the original input file"""
        try:
            if not hasattr(self, 'data_manager') or not self.data_manager:
                messagebox.showerror("Error", "No data manager available for saving")
                return
            
            # Check if there are modifications to save
            if not hasattr(self.data_manager, 'has_changes_to_save') or not self.data_manager.has_changes_to_save():
                messagebox.showinfo("Info", "No modifications to save")
                return
            
            # Save modifications
            if hasattr(self.data_manager, 'save_to_original_file'):
                success = self.data_manager.save_to_original_file()
                if success:
                    self.mark_data_saved()  # Remove asterisk from title
                    messagebox.showinfo("Success", f"Data saved successfully to {os.path.basename(self.config['data_file'])}")
                else:
                    messagebox.showerror("Error", "Failed to save data")
            else:
                messagebox.showerror("Error", "Save functionality not available in current data manager")
                
        except Exception as e:
            error_msg = f"Failed to save data: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error saving data: {e}")
    
    def show_data_statistics(self):
        """Show data statistics popup"""
        try:
            if not hasattr(self, 'data_manager') or not self.data_manager:
                messagebox.showerror("Error", "No data loaded")
                return
            
            # Update status
            old_status = self.ui_manager.status_var.get()
            self.ui_manager.status_var.set("Analyzing data...")
            self.root.update()
            
            # Analyze the data
            stats = self.data_analyzer.analyze_data_file(self.config['data_file'])
            
            # Create statistics popup
            self.display_data_statistics(stats, self.config['data_file'])
            
            # Restore status
            self.ui_manager.status_var.set(old_status)
            
        except Exception as e:
            error_msg = f"Failed to analyze data: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error analyzing data: {e}")
    
    def display_data_statistics(self, stats, data_file):
        """Display comprehensive data statistics in a popup window with histogram and data processing capabilities"""
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"Data Statistics - {os.path.basename(data_file)}")
        popup.geometry("800x650")  # Increased height for new buttons
        popup.resizable(True, True)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (800 // 2)
        y = (popup.winfo_screenheight() // 2) - (650 // 2)
        popup.geometry(f"800x650+{x}+{y}")
        
        # Make popup modal
        popup.transient(self.root)
        popup.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Store references for updating
        self.stats_popup = popup
        self.stats_data_file = data_file
        self.stats_imputed = False
        self.original_stats = stats.copy()
        
        # Statistics text
        stats_frame = ttk.LabelFrame(main_frame, text="Data Quality", padding=10)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        # Store stats frame for updating
        self.stats_display_frame = stats_frame
        
        # Function to update stats display
        def update_stats_display(current_stats):
            # Clear existing content
            for widget in self.stats_display_frame.winfo_children():
                widget.destroy()
            
            stats_text = f"""File: {os.path.basename(data_file)}
Total Frames: {current_stats['total_frames']}
Frames with Invalid Data: {current_stats['frames_with_invalid']} ({current_stats['frames_with_invalid']/max(current_stats['total_frames'], 1)*100:.1f}%)
Total Invalid Data Points: {current_stats['total_invalid_count']}
Valid Angular Velocity Values: {len(current_stats['angular_velocities'])}
File has Headers: {'Yes' if current_stats.get('has_headers', False) else 'No'}"""
            
            # Show regular stats
            ttk.Label(self.stats_display_frame, text=stats_text, font=('Courier', 9), 
                     wraplength=400, justify='left').pack(anchor='w')
            
            if 'augmented_count' in current_stats and current_stats['augmented_count'] > 0:
                # Show augmented count in blue
                augmented_label = ttk.Label(self.stats_display_frame, 
                                        text=f"Augmented Data Frames: {current_stats['augmented_count']}", 
                                        font=('Courier', 9), foreground='blue',
                                        wraplength=400, justify='left')
                augmented_label.pack(anchor='w')
            
            if 'imputed_count' in current_stats and current_stats['imputed_count'] > 0:
                # Show imputed count in green
                imputed_label = ttk.Label(self.stats_display_frame, 
                                        text=f"Imputed Data Points: {current_stats['imputed_count']}", 
                                        font=('Courier', 9), foreground='green',
                                        wraplength=400, justify='left')
                imputed_label.pack(anchor='w')
        
        # Initial stats display
        update_stats_display(stats)
        
        # Button frame for Impute, Augment and Save buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(0, 10))
        
        # Impute button
        def impute_invalid_data():
            """Impute invalid data points using adjacent values"""
            try:
                # Check if we have previously modified data to work on
                if hasattr(self, 'imputed_data') and self.stats_imputed and self.imputed_data:
                    # Work on previously modified data
                    print("Working on previously modified data...")
                    processed_lines = [line[:] for line in self.imputed_data]  # Deep copy
                    has_headers = hasattr(self, 'imputed_has_headers') and self.imputed_has_headers
                    
                    # Skip header for processing
                    start_idx = 1 if has_headers else 0
                    data_lines_from_modified = processed_lines[start_idx:]
                else:
                    # Work on original file data
                    print("Working on original file data...")
                    # Check if file has headers
                    has_headers = self.has_header(data_file)
                    
                    # Read the original file to preserve headers
                    with open(data_file, 'r') as f:
                        all_lines = f.readlines()
                    
                    header_line = None
                    data_lines = []
                    
                    if has_headers and all_lines:
                        header_line = all_lines[0].strip()
                        data_lines = [line.strip() for line in all_lines[1:] if line.strip()]
                    else:
                        data_lines = [line.strip() for line in all_lines if line.strip()]
                    
                    processed_lines = []
                    
                    # Add header if it exists
                    if header_line:
                        processed_lines.append(header_line.split(','))
                    
                    # Convert string data to list format for consistency
                    data_lines_from_modified = []
                    for line in data_lines:
                        if line:
                            data_lines_from_modified.append(line.split(','))
                    
                    # Add original data to processed_lines
                    processed_lines.extend(data_lines_from_modified)
                
                imputed_count = 0
                
                # Process each data line for imputation
                for i, data in enumerate(data_lines_from_modified):
                    if len(data) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                        lidar_values = []
                        
                        # Convert to float and identify invalid positions
                        for j in range(LIDAR_RESOLUTION):
                            try:
                                value = float(data[j])
                                if math.isinf(value) or math.isnan(value) or value == 0:
                                    lidar_values.append(None)  # Mark as invalid (including 0 values)
                                else:
                                    lidar_values.append(value)
                            except (ValueError, TypeError):
                                lidar_values.append(None)  # Mark as invalid
                        
                        # Impute invalid values
                        for j in range(LIDAR_RESOLUTION):
                            if lidar_values[j] is None:  # Invalid value found
                                # Find left valid value
                                left_val = None
                                left_idx = j - 1
                                while left_idx >= 0 and left_val is None:
                                    if lidar_values[left_idx] is not None:
                                        left_val = lidar_values[left_idx]
                                        break
                                    left_idx -= 1
                                
                                # Find right valid value
                                right_val = None
                                right_idx = j + 1
                                while right_idx < LIDAR_RESOLUTION and right_val is None:
                                    if lidar_values[right_idx] is not None:
                                        right_val = lidar_values[right_idx]
                                        break
                                    right_idx += 1
                                
                                # Impute based on available adjacent values
                                if left_val is not None and right_val is not None:
                                    # Average of left and right
                                    lidar_values[j] = (left_val + right_val) / 2
                                elif left_val is not None:
                                    # Use left value
                                    lidar_values[j] = left_val
                                elif right_val is not None:
                                    # Use right value
                                    lidar_values[j] = right_val
                                else:
                                    # No valid adjacent values, use a default reasonable distance
                                    lidar_values[j] = 500.0  # Default distance in mm
                                
                                imputed_count += 1
                        
                        # Update the dataframe with imputed values
                        imputed_line = []
                        for j in range(LIDAR_RESOLUTION):
                            imputed_line.append(str(lidar_values[j]))
                        imputed_line.append(data[360])  # Keep original angular velocity
                        
                        # Update the processed data
                        start_idx = 1 if has_headers else 0
                        processed_lines[start_idx + i] = imputed_line
                
                # Store imputed data for saving
                self.imputed_data = processed_lines
                self.stats_imputed = True
                self.imputed_has_headers = has_headers
                
                # Re-analyze the imputed data
                new_stats = self.analyze_imputed_data_from_list(processed_lines, has_headers)
                new_stats['imputed_count'] = imputed_count
                
                # Update statistics display
                update_stats_display(new_stats)
                
                # Enable save button
                save_button.config(state='normal')
                
                # Update histogram if it exists
                if hasattr(self, 'stats_canvas') and new_stats['angular_velocities']:
                    self.update_histogram(new_stats)
                
                # Determine the source of data for success message
                data_source = "previously modified data" if (hasattr(self, 'imputed_data') and self.stats_imputed and self.imputed_data) else "original file data"
                
                messagebox.showinfo("Success", f"Successfully imputed {imputed_count} invalid data points!\n" +
                                  f"Worked on: {data_source}\n" +
                                  (f"File has headers: {'Yes' if has_headers else 'No'}"))
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to impute data: {str(e)}")
                print(f"Error imputing data: {e}")
                import traceback
                traceback.print_exc()
        
        impute_button = ttk.Button(button_frame, text="Impute Invalid Data", 
                                  command=impute_invalid_data, width=20)
        impute_button.pack(side='left', padx=(0, 10))
        
        # Augment Data button
        def augment_data():
            """Augment data by reversing lidar points and negating angular velocity"""
            try:
                # Prompt user for append or rewrite option
                choice = messagebox.askyesnocancel(
                    "Augment Data Options",
                    "How would you like to handle the augmented data?\n\n" +
                    "• Yes: Append augmented data to existing data\n" +
                    "• No: Replace existing data with augmented data only\n" +
                    "• Cancel: Cancel augmentation"
                )
                
                if choice is None:  # User clicked Cancel
                    return
                
                append_mode = choice  # True for append, False for replace
                
                # Check if we have previously modified data to work on
                if hasattr(self, 'imputed_data') and self.stats_imputed and self.imputed_data:
                    # Work on previously modified data
                    print("Augmenting previously modified data...")
                    source_data = [line[:] for line in self.imputed_data]  # Deep copy
                    has_headers = hasattr(self, 'imputed_has_headers') and self.imputed_has_headers
                    
                    # Extract data lines (skip header)
                    if has_headers and source_data:
                        header_line = source_data[0]
                        data_lines_from_source = source_data[1:]
                    else:
                        header_line = None
                        data_lines_from_source = source_data
                else:
                    # Work on original file data
                    print("Augmenting original file data...")
                    # Check if file has headers
                    has_headers = self.has_header(data_file)
                    
                    # Read the original file
                    with open(data_file, 'r') as f:
                        all_lines = f.readlines()
                    
                    if has_headers and all_lines:
                        header_line = all_lines[0].strip().split(',')
                        data_lines = [line.strip() for line in all_lines[1:] if line.strip()]
                    else:
                        header_line = None
                        data_lines = [line.strip() for line in all_lines if line.strip()]
                    
                    # Convert string data to list format for consistency
                    data_lines_from_source = []
                    for line in data_lines:
                        if line:
                            data_lines_from_source.append(line.split(','))
                
                # Create augmented data
                augmented_data = []
                augmented_count = 0
                
                for data in data_lines_from_source:
                    if len(data) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                        # Create augmented version
                        augmented_line = []
                        
                        # Reverse the lidar data (180-degree rotation effect)
                        lidar_data = data[:LIDAR_RESOLUTION]
                        reversed_lidar = lidar_data[LIDAR_RESOLUTION//2:] + lidar_data[:LIDAR_RESOLUTION//2]
                        augmented_line.extend(reversed_lidar)
                        
                        # Negate the angular velocity
                        try:
                            original_angular = float(data[LIDAR_RESOLUTION])
                            augmented_angular = -original_angular
                            augmented_line.append(str(augmented_angular))
                        except (ValueError, TypeError):
                            augmented_line.append(data[LIDAR_RESOLUTION])  # Keep original if can't convert
                        
                        augmented_data.append(augmented_line)
                        augmented_count += 1
                
                # Combine data based on user choice
                final_data = []
                
                # Add header if it exists
                if header_line:
                    final_data.append(header_line)
                
                if append_mode:
                    # Append mode: original + augmented
                    final_data.extend(data_lines_from_source)
                    final_data.extend(augmented_data)
                    final_count = len(data_lines_from_source) + augmented_count
                else:
                    # Replace mode: augmented only
                    final_data.extend(augmented_data)
                    final_count = augmented_count
                
                # Store augmented data for saving
                self.imputed_data = final_data
                self.stats_imputed = True
                self.imputed_has_headers = has_headers
                
                # Re-analyze the augmented data
                new_stats = self.analyze_imputed_data_from_list(final_data, has_headers)
                new_stats['augmented_count'] = augmented_count
                
                # Update statistics display
                update_stats_display(new_stats)
                
                # Enable save button
                save_button.config(state='normal')
                
                # Update histogram if it exists
                if hasattr(self, 'stats_canvas') and new_stats['angular_velocities']:
                    self.update_histogram(new_stats)
                
                mode_text = "appended to" if append_mode else "replaced"
                success_msg = f"Successfully augmented data!\n" + \
                             f"Created {augmented_count} augmented frames ({mode_text} original data)\n" + \
                             f"Total frames in result: {final_count}\n" + \
                             f"File has headers: {'Yes' if has_headers else 'No'}"
                messagebox.showinfo("Success", success_msg)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to augment data: {str(e)}")
                print(f"Error augmenting data: {e}")
                import traceback
                traceback.print_exc()
        
        augment_button = ttk.Button(button_frame, text="Augment Data", 
                                   command=augment_data, width=15)
        augment_button.pack(side='left', padx=(0, 10))
        
        # Save button (initially disabled)
        def save_data():
            """Save processed data to file"""
            try:
                if not hasattr(self, 'imputed_data') or not self.imputed_data:
                    messagebox.showerror("Error", "No processed data to save")
                    return
                
                # Ask user for save location
                from tkinter import filedialog
                save_file = filedialog.asksaveasfilename(
                    title="Save Processed Data",
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
                    initialname=f"processed_{os.path.basename(data_file)}"
                )
                
                if save_file:
                    # Write the data
                    with open(save_file, 'w') as f:
                        for line in self.imputed_data:
                            if isinstance(line, list):
                                f.write(','.join(line) + '\n')
                            else:
                                f.write(str(line) + '\n')
                    
                    messagebox.showinfo("Success", f"Data saved successfully to:\n{save_file}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {str(e)}")
                print(f"Error saving data: {e}")
        
        save_button = ttk.Button(button_frame, text="Save Data", 
                                command=save_data, width=12, state='disabled')
        save_button.pack(side='left', padx=(0, 10))
        
        # Angular velocity statistics and histogram
        if stats['angular_velocities']:
            # Statistics frame
            vel_frame = ttk.LabelFrame(main_frame, text="Angular Velocity Statistics", padding=10)
            vel_frame.pack(fill='x', pady=(0, 10))
            
            vel_stats = f"""Mean: {np.mean(stats['angular_velocities']):.3f}
Std Dev: {np.std(stats['angular_velocities']):.3f}
Min: {np.min(stats['angular_velocities']):.3f}
Max: {np.max(stats['angular_velocities']):.3f}"""
            
            ttk.Label(vel_frame, text=vel_stats, font=('Courier', 9), justify='left').pack(anchor='w')
            
            # Histogram frame
            self.stats_hist_frame = ttk.LabelFrame(main_frame, text="Angular Velocity Distribution", padding=5)
            self.stats_hist_frame.pack(fill='both', expand=True)
            
            # Create histogram
            self.create_histogram(stats)
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=popup.destroy)
        close_button.pack(pady=10)
    
    def has_header(self, data_file):
        """Check if the data file has a header line"""
        try:
            with open(data_file, 'r') as f:
                first_line = f.readline().strip()
                if not first_line:
                    return False
                
                # Split the line and check if first few elements are numeric
                elements = first_line.split(',')
                if len(elements) < 10:  # Should have at least 10 elements for lidar data
                    return False
                
                # Check if first few elements can be converted to float
                try:
                    for i in range(min(5, len(elements)-1)):  # Check first 5 elements
                        float(elements[i])
                    return False  # If all numeric, it's data, not header
                except (ValueError, TypeError):
                    return True  # If can't convert to float, likely a header
        except Exception:
            return False
    
    def create_histogram(self, stats):
        """Create histogram in the stats window"""
        try:
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create histogram with 20 bins
            n, bins, patches = ax.hist(stats['angular_velocities'], bins=20, 
                                     edgecolor='black', alpha=0.7, color='skyblue')
            
            ax.set_xlabel('Angular Velocity Value')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Angular Velocity Values (20 bins)')
            ax.grid(True, alpha=0.3)
            
            # Add statistics text on the plot
            ax.text(0.02, 0.98, f'Mean: {np.mean(stats["angular_velocities"]):.3f}\n'
                                f'Std: {np.std(stats["angular_velocities"]):.3f}\n'
                                f'Min: {np.min(stats["angular_velocities"]):.3f}\n'
                                f'Max: {np.max(stats["angular_velocities"]):.3f}',
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Embed plot in tkinter
            self.stats_canvas = FigureCanvasTkAgg(fig, self.stats_hist_frame)
            self.stats_canvas.draw()
            self.stats_canvas.get_tk_widget().pack(fill='both', expand=True)
            
        except Exception as e:
            print(f"Error creating histogram: {e}")
    
    def update_histogram(self, stats):
        """Update histogram with new stats"""
        try:
            if hasattr(self, 'stats_canvas') and hasattr(self, 'stats_hist_frame'):
                # Clear existing canvas
                self.stats_canvas.get_tk_widget().destroy()
                
                # Create new histogram
                self.create_histogram(stats)
        except Exception as e:
            print(f"Error updating histogram: {e}")
    
    def analyze_imputed_data_from_list(self, processed_lines, has_headers):
        """Analyze imputed data from list format and return statistics"""
        try:
            angular_velocities = []
            total_invalid_count = 0
            frames_with_invalid = 0
            total_frames = 0
            
            # Skip header if present
            start_idx = 1 if has_headers else 0
            data_lines = processed_lines[start_idx:]
            
            for line in data_lines:
                if isinstance(line, list) and len(line) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                    total_frames += 1
                    
                    # Check for invalid data in lidar readings
                    invalid_in_frame = 0
                    for i in range(LIDAR_RESOLUTION):
                        try:
                            value = float(line[i])
                            if math.isinf(value) or math.isnan(value):
                                invalid_in_frame += 1
                        except (ValueError, TypeError):
                            invalid_in_frame += 1
                    
                    if invalid_in_frame > 0:
                        frames_with_invalid += 1
                        total_invalid_count += invalid_in_frame
                    
                    # Extract angular velocity (last column)
                    try:
                        ang_vel = float(line[LIDAR_RESOLUTION])
                        if not (math.isinf(ang_vel) or math.isnan(ang_vel)):
                            angular_velocities.append(ang_vel)
                    except (ValueError, TypeError):
                        pass  # Skip non-numeric angular velocities
            
            return {
                'total_frames': total_frames,
                'frames_with_invalid': frames_with_invalid,
                'total_invalid_count': total_invalid_count,
                'angular_velocities': angular_velocities,
                'has_headers': has_headers
            }
            
        except Exception as e:
            print(f"Error analyzing imputed data: {e}")
            return {
                'total_frames': 0,
                'frames_with_invalid': 0,
                'total_invalid_count': 0,
                'angular_velocities': [],
                'has_headers': has_headers
            }
    
    # AI functions - stubs for now
    def browse_ai_model(self):
        """Browse for AI model"""
        import os
        
        # Default to ./models directory if it exists, otherwise current directory
        models_dir = "./models"
        if not os.path.exists(models_dir):
            models_dir = "."
            
        file_path = filedialog.askopenfilename(
            title="Select AI Model",
            filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")],
            initialdir=models_dir
        )
        if file_path:
            try:
                load_ai_model(file_path)
                messagebox.showinfo("Success", f"AI model loaded: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load AI model: {str(e)}")
    
    def show_ai_model_info(self):
        """Show AI model information"""
        if is_ai_model_loaded():
            info = get_ai_model_info()
            messagebox.showinfo("AI Model Info", f"Model loaded: {info}")
        else:
            messagebox.showinfo("AI Model Info", "No AI model loaded")
    
    def clear_ai_model(self):
        """Clear loaded AI model"""
        from ai_model import ai_model_manager
        ai_model_manager.clear_model()
        messagebox.showinfo("Success", "AI model cleared")
    
    def show_about_dialog(self):
        """Show the About dialog"""
        about_text = """LiDAR Visualizer

Version: 0.1
Date: 01/08/2025
Author: Hoang Giang Nguyen
Email: hoang.g.nguyen@student.uts.edu.au

A comprehensive LiDAR data visualization tool with AI integration capabilities."""
        
        messagebox.showinfo("About LiDAR Visualizer", about_text)
    
    def show_controls_dialog(self):
        """Show the Controls dialog with keyboard shortcuts and usage information"""
        import tkinter as tk
        from tkinter import ttk
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Controls & Keyboard Shortcuts")
        popup.geometry("700x500")
        popup.resizable(True, True)
        
        # Center the popup
        popup.transient(self.root)
        popup.grab_set()
        
        # Calculate center position
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (350)
        y = (popup.winfo_screenheight() // 2) - (250)
        popup.geometry(f"700x500+{x}+{y}")
        
        main_frame = ttk.Frame(popup, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎮 Controls & Keyboard Shortcuts", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create scrollable text widget
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Text widget
        text_widget = tk.Text(text_frame, wrap='word', yscrollcommand=scrollbar.set,
                             font=('Consolas', 10), padx=10, pady=10)
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Controls content
        controls_text = """KEYBOARD SHORTCUTS:

🎵 PLAYBACK CONTROLS:
  Space          Play/Pause or Next frame (in inspect mode)
  I              Toggle Inspect/Continuous mode

📍 NAVIGATION:
  ←→ Arrow Keys  Previous/Next frame
  Home           First frame
  End            Last frame
  
📝 MODIFIED FRAMES:
  ↑↓ Arrow Keys  Previous/Next modified frame
  Page Up        First modified frame
  Page Down      Last modified frame

🔄 DATA MANIPULATION:
  H              Flip Horizontal
  V              Flip Vertical
  R              Replace current frame with previous
  U              Undo last change

🤖 AI FEATURES:
  AI Menu        Load AI models for predictions
  
📊 DATA SPLITTING:
  Split Data     Randomly split data into train/validation/test sets
  Move Set       Rotate current frame between dataset splits
  
MOUSE CONTROLS:

🖱️ VISUALIZATION:
  - Click buttons in the interface for various functions
  - Use entry fields to navigate to specific frames
  - Toggle visualization options with checkboxes

📋 INTERFACE PANELS:

🎮 Left Panel - Navigation & Controls:
  - Play/Pause, mode toggle, frame navigation
  - Frame input field and modified frame navigation
  
📊 Right Panel - Data Management:
  - Flip controls with "All frames" option
  - Data splitting and set management tools
  
📈 Visualization Panel:
  - LiDAR point visualization
  - Direction indicators (forward, current, previous, AI prediction)
  - Toggle visibility options
  
📋 Input Controls:
  - Angular velocity, linear velocity inputs
  - Frame information and statistics
  
💡 TIPS:
  - Use inspection mode for frame-by-frame analysis
  - Apply "All" checkbox for batch flip operations
  - Check status bar for current frame's dataset assignment
  - Use modified frame navigation to review changes
  - Load AI models for intelligent predictions"""
        
        text_widget.insert('1.0', controls_text)
        text_widget.config(state='disabled')  # Make it read-only
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))
        
        def close_dialog():
            popup.destroy()
        
        ttk.Button(button_frame, text="Close", command=close_dialog, 
                  width=10).pack()
        
        # Bind Escape key
        popup.bind('<Escape>', lambda e: close_dialog())
    
    def show_kbest_analysis(self):
        """Show the K-Best feature analysis dialog"""
        try:
            from kbest_analysis import show_kbest_analysis_dialog
            
            def refresh_visualization():
                """Callback to refresh visualization after applying K-Best results"""
                # Force a re-render to show updated DECISIVE_FRAME_POSITIONS
                try:
                    self.renderer.render_frame()
                    print("Visualization refreshed with new K-Best positions")
                except Exception as e:
                    print(f"Error refreshing visualization: {e}")
            
            # Show the K-Best analysis dialog
            show_kbest_analysis_dialog(self.root, self.data_manager, refresh_visualization)
            
        except ImportError as e:
            messagebox.showerror("Import Error", f"Could not import K-Best analysis module:\n{str(e)}\n\nPlease ensure scikit-learn is installed.")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening K-Best analysis:\n{str(e)}")
            print(f"Error opening K-Best analysis: {e}")
    
    def show_current_kbest_positions(self):
        """Show the current K-Best data point positions"""
        try:
            from config import DECISIVE_FRAME_POSITIONS
            
            # Create a new dialog window
            dialog = tk.Toplevel(self.root)
            dialog.title("Current K-Best Positions")
            dialog.geometry("600x500")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center the dialog on the parent window
            dialog.update_idletasks()
            x = (self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2))
            y = (self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2))
            dialog.geometry(f"+{x}+{y}")
            
            # Create main frame
            main_frame = tk.Frame(dialog)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Title label
            title_label = tk.Label(main_frame, 
                                 text="Current K-Best Data Point Positions", 
                                 font=('Arial', 14, 'bold'))
            title_label.pack(pady=(0, 10))
            
            # Information text
            info_text = f"Total positions: {len(DECISIVE_FRAME_POSITIONS)}\n"
            info_text += "These positions are highlighted in the visualization with magenta lines and red circles.\n\n"
            info_text += "Positions (0-359 degrees):"
            
            info_label = tk.Label(main_frame, text=info_text, justify=tk.LEFT)
            info_label.pack(anchor=tk.W, pady=(0, 10))
            
            # Create scrollable text widget for positions
            text_frame = tk.Frame(main_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            # Text widget with scrollbar
            text_widget = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED, 
                                height=15, font=('Courier', 10))
            scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Format positions in a readable way (10 per line)
            text_widget.config(state=tk.NORMAL)
            positions_text = ""
            for i, pos in enumerate(DECISIVE_FRAME_POSITIONS):
                if i % 10 == 0 and i > 0:
                    positions_text += "\n"
                positions_text += f"{pos:3d}  "
            
            text_widget.insert(tk.END, positions_text)
            text_widget.config(state=tk.DISABLED)
            
            # Button frame
            button_frame = tk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            # Close button
            close_button = tk.Button(button_frame, text="Close", command=dialog.destroy)
            close_button.pack(side=tk.RIGHT)
            
            # Copy to clipboard button
            def copy_to_clipboard():
                positions_str = str(DECISIVE_FRAME_POSITIONS)
                dialog.clipboard_clear()
                dialog.clipboard_append(positions_str)
                messagebox.showinfo("Copied", "Positions copied to clipboard!")
            
            copy_button = tk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard)
            copy_button.pack(side=tk.RIGHT, padx=(0, 10))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error showing current K-Best positions:\n{str(e)}")
    
    # Visual settings - stubs for now
    def show_scale_factor_dialog(self):
        """Show scale factor configuration dialog"""
        import tkinter as tk
        from tkinter import ttk, messagebox
        from config import SCALE_FACTOR
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Scale Factor Configuration")
        popup.geometry("400x250")
        popup.resizable(False, False)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (250 // 2)
        popup.geometry(f"400x250+{x}+{y}")
        
        # Make popup modal
        popup.transient(self.root)
        popup.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Lidar Visualization Scale Factor", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Description
        desc_label = ttk.Label(main_frame, 
                              text="Adjust the scale factor to control the visualization size.\nHigher values make distant objects appear closer.",
                              font=('Arial', 9), justify='center')
        desc_label.pack(pady=(0, 15))
        
        # Scale factor input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=(0, 20))
        
        ttk.Label(input_frame, text="Scale Factor:", 
                 font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        # Scale factor variable and entry
        scale_var = tk.StringVar()
        scale_var.set(f"{SCALE_FACTOR:.4f}")
        
        scale_entry = ttk.Entry(input_frame, textvariable=scale_var, 
                               width=12, font=('Courier', 10))
        scale_entry.pack(side='left')
        scale_entry.focus_set()
        
        # Current value info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(pady=(0, 20))
        
        ttk.Label(info_frame, text=f"Current: {SCALE_FACTOR:.4f}", 
                 font=('Arial', 8), foreground='blue').pack()
        ttk.Label(info_frame, text="Range: 0.001 - 9999.0", 
                 font=('Arial', 8), foreground='gray').pack()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        def apply_scale_factor():
            """Apply the new scale factor"""
            try:
                new_scale = float(scale_var.get())
                
                # Validate range
                if new_scale <= 0 or new_scale >= 9999:
                    messagebox.showerror("Invalid Value", 
                                       "Scale factor must be greater than 0 and less than 9999")
                    return
                
                # Update config module scale factor
                import config
                config.SCALE_FACTOR = new_scale
                
                # Update status to show change
                self.update_status()
                popup.destroy()
                print(f"Scale factor updated to: {new_scale:.4f}")
                
            except ValueError:
                messagebox.showerror("Invalid Value", 
                                   "Please enter a valid numeric value for scale factor")
        
        def cancel_dialog():
            """Cancel the dialog"""
            popup.destroy()
        
        # OK and Cancel buttons
        ttk.Button(button_frame, text="OK", command=apply_scale_factor, 
                  width=10).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=cancel_dialog, 
                  width=10).pack(side='left')
        
        # Bind Enter key to apply changes
        scale_entry.bind('<Return>', lambda e: apply_scale_factor())
        popup.bind('<Escape>', lambda e: cancel_dialog())
    
    def show_direction_ratio_dialog(self):
        """Show direction ratio configuration dialog"""
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Direction Ratio Configuration")
        popup.geometry("400x250")
        popup.resizable(False, False)
        
        # Center the popup
        popup.transient(self.root)
        popup.grab_set()
        
        # Calculate center position
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (250 // 2)
        popup.geometry(f"400x250+{x}+{y}")
        
        main_frame = ttk.Frame(popup, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Direction Ratio Configuration", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Description
        desc_label = ttk.Label(main_frame, 
                              text="Configure how angular velocity values map to direction visualization degrees.",
                              font=('Arial', 9), wraplength=350, justify='center')
        desc_label.pack(pady=(0, 20))
        
        # Direction (degree) input
        degree_frame = ttk.Frame(main_frame)
        degree_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(degree_frame, text="Maximum Direction (degrees):", 
                 font=('Arial', 10)).pack(anchor='w')
        degree_var = tk.StringVar(value=str(self.renderer.direction_ratio_max_degree))
        degree_entry = ttk.Entry(degree_frame, textvariable=degree_var, 
                                font=('Courier', 10), width=15)
        degree_entry.pack(anchor='w', pady=(5, 0))
        degree_entry.focus_set()
        
        # Angular velocity max input
        angular_frame = ttk.Frame(main_frame)
        angular_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(angular_frame, text="Angular Velocity Max:", 
                 font=('Arial', 10)).pack(anchor='w')
        angular_var = tk.StringVar(value=str(self.renderer.direction_ratio_max_angular))
        angular_entry = ttk.Entry(angular_frame, textvariable=angular_var, 
                                 font=('Courier', 10), width=15)
        angular_entry.pack(anchor='w', pady=(5, 0))
        
        # Current mapping info
        info_text = f"Current: Angular velocity {self.renderer.direction_ratio_max_angular} → {self.renderer.direction_ratio_max_degree}°"
        info_label = ttk.Label(main_frame, text=info_text, 
                              font=('Arial', 8), foreground='blue')
        info_label.pack(pady=(0, 15))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        def apply_direction_ratio():
            """Apply the new direction ratio settings"""
            try:
                new_degree = float(degree_var.get())
                new_angular = float(angular_var.get())
                
                if new_degree <= 0 or new_degree > 180:
                    messagebox.showerror("Invalid Value", 
                                       "Direction must be between 0 and 180 degrees")
                    return
                
                if new_angular <= 0:
                    messagebox.showerror("Invalid Value", 
                                       "Angular velocity max must be greater than 0")
                    return
                
                # Update the renderer configuration
                self.renderer.set_direction_ratio(new_degree, new_angular)
                
                popup.destroy()
                print(f"Direction ratio updated: {new_angular} → {new_degree}°")
                
            except ValueError:
                messagebox.showerror("Invalid Value", 
                                   "Please enter valid numeric values")
        
        def cancel_dialog():
            """Cancel the dialog"""
            popup.destroy()
        
        # OK and Cancel buttons
        ttk.Button(button_frame, text="OK", command=apply_direction_ratio, 
                  width=10).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=cancel_dialog, 
                  width=10).pack(side='left')
        
        # Bind Enter and Escape keys
        popup.bind('<Return>', lambda e: apply_direction_ratio())
        popup.bind('<Escape>', lambda e: cancel_dialog())
    
    def show_preferences_dialog(self):
        """Show preferences dialog"""
        import tkinter as tk
        from tkinter import ttk, messagebox
        from config import AUGMENTATION_UNIT
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Preferences")
        popup.geometry("450x380")
        popup.resizable(False, False)
        
        # Center the popup
        popup.transient(self.root)
        popup.grab_set()
        
        # Calculate center position
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (450 // 2)
        y = (popup.winfo_screenheight() // 2) - (380 // 2)
        popup.geometry(f"450x380+{x}+{y}")
        
        main_frame = ttk.Frame(popup, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Preferences", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Unit measurement configuration
        unit_frame = ttk.Frame(main_frame)
        unit_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(unit_frame, text="Data Unit Measurement:", 
                 font=('Arial', 10)).pack(anchor='w')
        unit_var = tk.StringVar(value=AUGMENTATION_UNIT)
        unit_combo = ttk.Combobox(unit_frame, textvariable=unit_var, 
                                 values=["m", "mm"], width=10, state="readonly")
        unit_combo.pack(anchor='w', pady=(5, 0))
        unit_combo.focus_set()
        
        # Data split ratios configuration
        split_frame = ttk.Frame(main_frame)
        split_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(split_frame, text="Data Split Ratios (Train:Validation:Test):", 
                 font=('Arial', 10)).pack(anchor='w')
        
        ratios_frame = ttk.Frame(split_frame)
        ratios_frame.pack(anchor='w', pady=(5, 0))
        
        train_var = tk.StringVar(value=str(self.ui_manager.split_ratios[0]))
        val_var = tk.StringVar(value=str(self.ui_manager.split_ratios[1]))
        test_var = tk.StringVar(value=str(self.ui_manager.split_ratios[2]))
        
        ttk.Label(ratios_frame, text="Train:").pack(side='left')
        train_entry = ttk.Entry(ratios_frame, textvariable=train_var, width=5)
        train_entry.pack(side='left', padx=(5, 10))
        
        ttk.Label(ratios_frame, text="Val:").pack(side='left')
        val_entry = ttk.Entry(ratios_frame, textvariable=val_var, width=5)
        val_entry.pack(side='left', padx=(5, 10))
        
        ttk.Label(ratios_frame, text="Test:").pack(side='left')
        test_entry = ttk.Entry(ratios_frame, textvariable=test_var, width=5)
        test_entry.pack(side='left', padx=(5, 0))
        
        ttk.Label(ratios_frame, text="%").pack(side='left', padx=(5, 0))
        
        # Current values info
        info_text = f"Current Unit: {AUGMENTATION_UNIT}\nCurrent Split: {':'.join(map(str, self.ui_manager.split_ratios))}%"
        info_label = ttk.Label(main_frame, text=info_text, 
                              font=('Arial', 8), foreground='blue')
        info_label.pack(pady=(0, 15))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        def apply_preferences():
            """Apply the new preferences"""
            try:
                new_unit = unit_var.get()
                
                # Validate and update split ratios
                train_ratio = int(train_var.get())
                val_ratio = int(val_var.get())
                test_ratio = int(test_var.get())
                
                if train_ratio + val_ratio + test_ratio != 100:
                    messagebox.showerror("Error", "Split ratios must sum to 100%")
                    return
                
                if train_ratio <= 0 or val_ratio <= 0 or test_ratio <= 0:
                    messagebox.showerror("Error", "All split ratios must be greater than 0")
                    return
                
                # Update config module
                import config
                config.AUGMENTATION_UNIT = new_unit
                
                # Update split ratios
                self.ui_manager.split_ratios = [train_ratio, val_ratio, test_ratio]
                
                popup.destroy()
                print(f"Preferences updated - Unit: {new_unit}, Split ratios: {train_ratio}:{val_ratio}:{test_ratio}")
                
            except ValueError:
                messagebox.showerror("Error", "Split ratios must be valid integers")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update preferences: {str(e)}")
        
        def cancel_dialog():
            """Cancel the dialog"""
            popup.destroy()
        
        # OK and Cancel buttons
        ttk.Button(button_frame, text="OK", command=apply_preferences, 
                  width=10).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=cancel_dialog, 
                  width=10).pack(side='left')
        
        # Bind Enter and Escape keys
        unit_combo.bind('<Return>', lambda e: apply_preferences())
        popup.bind('<Escape>', lambda e: cancel_dialog())
    
    # Augmentation methods - Rotation only
    
    def _mark_frame_modified(self):
        """Mark the current frame as modified"""
        current_frame = self.data_manager._pointer
        if current_frame not in self.data_manager._modified_frames:
            self.data_manager._modified_frames.append(current_frame)
            self.data_manager._modified_frames.sort()  # Keep the list sorted
            # Update the modified pointer to point to the current frame
            self.data_manager._modified_pointer = self.data_manager._modified_frames.index(current_frame)
            print(f"Frame {current_frame} added to modified frames list")
        
        # Mark data as changed (add asterisk to title)
        self.mark_data_changed()
    
    def _apply_rotation_transformation(self, angle_degrees):
        """Apply rotation transformation by shifting LiDAR data array indices
        
        Since LiDAR data is stored as 360 sequential distance values (0-359°),
        rotation is simply shifting the array indices with wraparound.
        
        Args:
            angle_degrees: rotation angle in degrees (positive = counter-clockwise, negative = clockwise)
        """
        try:
            # Get current frame data (this is a list of distance values)
            current_data = self.data_manager.dataframe
            if not current_data:
                raise ValueError("No current frame data available")
            
            # Create backup for undo functionality
            self.data_manager.backup_current_frame()
            
            print(f"Rotating {angle_degrees} degrees by shifting array indices")
            
            # Convert string data to string for processing (keep as strings)
            str_data = [str(value) for value in current_data]
            
            # Simple array shifting for rotation
            if len(str_data) >= 361:  # Ensure we have LiDAR data + angular velocity
                lidar_data = str_data[:-1]  # First 360 elements (exclude angular velocity)
                angular_velocity = str_data[-1]  # Last element is angular velocity
                
                # Shift array by angle_degrees positions
                # Positive angle = counter-clockwise = shift left (indices decrease)  
                # Negative angle = clockwise = shift right (indices increase)
                shift_amount = int(round(angle_degrees)) % 360
                
                # Perform the shift with wraparound
                if shift_amount != 0:
                    rotated_data = lidar_data[-shift_amount:] + lidar_data[:-shift_amount]
                else:
                    rotated_data = lidar_data[:]
                
                # Reconstruct the complete data with angular velocity
                modified_data = rotated_data + [angular_velocity]
                
                # Update the current frame with rotated data
                self.data_manager.update_current_frame(modified_data)
                
                # Mark frame as modified and refresh display
                self._mark_frame_modified()
                self.update_display()
                
                print(f"Array shifted by {shift_amount} positions for {angle_degrees}° rotation")
            else:
                print(f"Warning: Insufficient data length ({len(str_data)}) for rotation")
                
        except Exception as e:
            print(f"Error applying rotation transformation: {e}")
            import traceback
            traceback.print_exc()
    
    def rotate_cw(self):
        """Rotate lidar data 1 degree clockwise"""
        try:
            if not hasattr(self, 'data_manager') or not self.data_manager:
                return
            
            print("Rotating 1 degree clockwise")
            self._apply_rotation_transformation(-1.0)  # Negative for clockwise
            self.mark_data_changed()  # Mark data as changed
            
        except Exception as e:
            print(f"Error rotating clockwise: {e}")
    
    def rotate_ccw(self):
        """Rotate lidar data 1 degree counter-clockwise"""
        try:
            if not hasattr(self, 'data_manager') or not self.data_manager:
                return
            
            print("Rotating 1 degree counter-clockwise")
            self._apply_rotation_transformation(1.0)  # Positive for counter-clockwise
            self.mark_data_changed()  # Mark data as changed
            
        except Exception as e:
            print(f"Error rotating counter-clockwise: {e}")
    
    def add_augmented_frames(self):
        """Add augmented frames based on current frame after the current position"""
        try:
            if not hasattr(self, 'data_manager') or not self.data_manager:
                print("No data manager available")
                return
                
            # Get the number of frames to add from UI
            try:
                frame_count = int(self.ui_manager.frames_count_var.get())
                if frame_count <= 0:
                    print("Frame count must be greater than 0")
                    return
            except (ValueError, AttributeError):
                print("Invalid frame count. Please enter a valid number.")
                return
            
            # Get current frame data
            current_line = self.data_manager.lines[self.data_manager.pointer]
            
            # Insert augmented frames after current position
            insert_position = self.data_manager.pointer + 1
            new_lines = []
            
            for i in range(frame_count):
                # Create a copy of the current frame for augmentation
                new_lines.append(current_line)
            
            # Insert the new frames into the data
            self.data_manager.lines[insert_position:insert_position] = new_lines
            
            # Preserve dataset split information for new frames
            if self.ui_manager.data_splits:
                current_frame = self.data_manager.pointer
                current_split = self.ui_manager.data_splits.get(current_frame, 'train')  # Default to train if unassigned
                
                # Assign the same split to all new augmented frames
                for i in range(total_added):
                    new_frame_idx = insert_position + i
                    self.ui_manager.data_splits[new_frame_idx] = current_split
                    
                # Update indices for existing frames that got shifted
                updated_splits = {}
                for frame_idx, split_type in self.ui_manager.data_splits.items():
                    if frame_idx >= insert_position and frame_idx not in range(insert_position, insert_position + total_added):
                        # This frame was shifted by the insertion
                        updated_splits[frame_idx + total_added] = split_type
                    elif frame_idx < insert_position or frame_idx in range(insert_position, insert_position + total_added):
                        # This frame wasn't shifted or is one of the new frames
                        updated_splits[frame_idx] = split_type
                
                self.ui_manager.data_splits = updated_splits
            
            # Mark that augmented frames were added
            self.data_manager.mark_augmented_frames_added()
            
            # Mark data as changed
            self.mark_data_changed()
            
            # Update total frames count
            total_added = len(new_lines)
            
            print(f"Added {total_added} augmented frame(s) after position {self.data_manager.pointer}")
            print(f"Total frames in dataset: {len(self.data_manager.lines)}")
            
            # Update the status display
            self.update_status()
            
        except Exception as e:
            print(f"Error adding augmented frames: {e}")
            import traceback
            traceback.print_exc()

    def duplicate_current_frame(self):
        """Duplicate the current frame by the specified count after the current position"""
        try:
            if not hasattr(self, 'data_manager') or not self.data_manager:
                print("No data manager available")
                return
                
            # Get the number of duplicates to create from UI
            try:
                duplicate_count = int(self.ui_manager.duplicate_count_var.get())
                if duplicate_count <= 0:
                    print("Duplicate count must be greater than 0")
                    return
            except (ValueError, AttributeError):
                print("Invalid duplicate count. Please enter a valid number.")
                return
            
            # Get current frame data (exact copy)
            current_line = self.data_manager.lines[self.data_manager.pointer]
            
            # Insert duplicate frames after current position
            insert_position = self.data_manager.pointer + 1
            new_lines = []
            
            for i in range(duplicate_count):
                # Create an exact copy of the current frame
                new_lines.append(current_line)
            
            # Insert the duplicate frames into the data
            self.data_manager.lines[insert_position:insert_position] = new_lines
            
            # Preserve dataset split information for duplicated frames
            if self.ui_manager.data_splits:
                current_frame = self.data_manager.pointer
                current_split = self.ui_manager.data_splits.get(current_frame, 'train')  # Default to train if unassigned
                
                # Assign the same split to all duplicated frames
                for i in range(total_added):
                    new_frame_idx = insert_position + i
                    self.ui_manager.data_splits[new_frame_idx] = current_split
                    
                # Update indices for existing frames that got shifted
                updated_splits = {}
                for frame_idx, split_type in self.ui_manager.data_splits.items():
                    if frame_idx >= insert_position and frame_idx not in range(insert_position, insert_position + total_added):
                        # This frame was shifted by the insertion
                        updated_splits[frame_idx + total_added] = split_type
                    elif frame_idx < insert_position or frame_idx in range(insert_position, insert_position + total_added):
                        # This frame wasn't shifted or is one of the new frames
                        updated_splits[frame_idx] = split_type
                
                self.ui_manager.data_splits = updated_splits
            
            # Mark that frames were added (reuse the augmented frames tracking)
            self.data_manager.mark_augmented_frames_added()
            
            # Mark data as changed
            self.mark_data_changed()
            
            # Update total frames count
            total_added = len(new_lines)
            
            print(f"Duplicated current frame {total_added} time(s) after position {self.data_manager.pointer}")
            print(f"Total frames in dataset: {len(self.data_manager.lines)}")
            
            # Update the status display
            self.update_status()
            
        except Exception as e:
            print(f"Error duplicating current frame: {e}")
            import traceback
            traceback.print_exc()
    
    def split_data(self):
        """Split the data into train, validation, and test sets"""
        try:
            import random
            from tkinter import messagebox
            import tkinter as tk
            import tkinter.ttk as ttk
            
            if not hasattr(self, 'data_manager') or not self.data_manager:
                messagebox.showerror("Error", "No data manager available")
                return
            
            if not self.data_manager.lines:
                messagebox.showwarning("Warning", "No data loaded to split.")
                return
            
            # Create popup window
            popup = tk.Toplevel(self.root)
            popup.title("Split Data")
            popup.geometry("400x350")
            popup.resizable(False, False)
            
            # Center the popup
            popup.transient(self.root)
            popup.grab_set()
            
            # Calculate center position
            popup.update_idletasks()
            x = (popup.winfo_screenwidth() // 2) - (400 // 2)
            y = (popup.winfo_screenheight() // 2) - (350 // 2)
            popup.geometry(f"400x350+{x}+{y}")
            
            main_frame = ttk.Frame(popup, padding=20)
            main_frame.pack(fill='both', expand=True)
            
            # Title
            title_label = ttk.Label(main_frame, text="Split Data into Sets", 
                                   font=('Arial', 12, 'bold'))
            title_label.pack(pady=(0, 15))
            
            # Info
            total_frames = len(self.data_manager.lines)
            info_label = ttk.Label(main_frame, text=f"Total frames: {total_frames}")
            info_label.pack(pady=(0, 10))
            
            # Split ratios display and controls
            split_frame = ttk.LabelFrame(main_frame, text="Split Ratios (%)", padding=10)
            split_frame.pack(fill='x', pady=(0, 15))
            
            ratio_vars = {}
            for i, label in enumerate(['Train', 'Validation', 'Test']):
                row_frame = ttk.Frame(split_frame)
                row_frame.pack(fill='x', pady=2)
                
                ttk.Label(row_frame, text=f"{label}:", width=10).pack(side='left')
                ratio_vars[label.lower()] = tk.DoubleVar(value=self.ui_manager.split_ratios[i])
                
                spinbox = ttk.Spinbox(row_frame, from_=0.0, to=100.0, increment=1.0,
                                    textvariable=ratio_vars[label.lower()], width=8)
                spinbox.pack(side='left', padx=(5, 0))
                ttk.Label(row_frame, text="%").pack(side='left', padx=(2, 0))
            
            # Preview
            preview_frame = ttk.Frame(main_frame)
            preview_frame.pack(fill='x', pady=(0, 15))
            
            preview_label = ttk.Label(preview_frame, text="Preview:", font=('Arial', 10, 'bold'))
            preview_label.pack(anchor='w')
            
            preview_text = tk.Text(preview_frame, height=4, width=45, state='disabled')
            preview_text.pack(pady=(5, 0))
            
            def update_preview(*args):
                try:
                    ratios = [ratio_vars['train'].get(), ratio_vars['validation'].get(), ratio_vars['test'].get()]
                    total = sum(ratios)
                    
                    preview_text.config(state='normal')
                    preview_text.delete(1.0, tk.END)
                    
                    if abs(total - 100.0) > 0.1:
                        preview_text.insert(tk.END, f"⚠️ Total must be 100% (currently {total:.1f}%)")
                    else:
                        train_count = int(total_frames * ratios[0] / 100)
                        val_count = int(total_frames * ratios[1] / 100)
                        test_count = total_frames - train_count - val_count
                        
                        preview_text.insert(tk.END, f"Train: {train_count} frames ({ratios[0]:.1f}%)\n")
                        preview_text.insert(tk.END, f"Validation: {val_count} frames ({ratios[1]:.1f}%)\n")
                        preview_text.insert(tk.END, f"Test: {test_count} frames ({ratios[2]:.1f}%)")
                    
                    preview_text.config(state='disabled')
                except:
                    pass
            
            for var in ratio_vars.values():
                var.trace('w', update_preview)
            
            def perform_split():
                """Perform the actual data split"""
                try:
                    ratios = [ratio_vars['train'].get(), ratio_vars['validation'].get(), ratio_vars['test'].get()]
                    total = sum(ratios)
                    
                    if abs(total - 100.0) > 0.1:
                        messagebox.showerror("Error", f"Split ratios must total 100%. Current total: {total:.1f}%")
                        return
                    
                    # Update split ratios
                    self.ui_manager.split_ratios = ratios
                    
                    # Create random assignment for all frames
                    frame_indices = list(range(len(self.main_dataset.lines)))
                    random.shuffle(frame_indices)
                    
                    # Calculate split points
                    train_count = int(len(frame_indices) * ratios[0] / 100)
                    val_count = int(len(frame_indices) * ratios[1] / 100)
                    
                    # Create separate datasets
                    self._create_dataset_splits(frame_indices, train_count, val_count)
                    
                    # Initialize dataset pointers to 0
                    self.train_pointer = 0
                    self.val_pointer = 0
                    self.test_pointer = 0
                    self.main_pointer = self.data_manager._pointer  # Keep main dataset position
                    
                    # Sync current_dataset_position if we're in a dataset
                    if self.current_dataset_type != 'main':
                        self.current_dataset_position = self._get_current_dataset_pointer()
                    
                    # Clear old split mapping (not needed with new approach)
                    self.ui_manager.data_splits.clear()
                    
                    # Mark that data has been split
                    self.ui_manager.data_splits = {'split': True}  # Flag to indicate split data exists
                    
                    # Show dataset radio buttons
                    self.ui_manager.show_dataset_radio_buttons()
                    
                    # Mark data as changed
                    self.mark_data_changed()
                    
                    # Update status display
                    self.update_status()
                    
                    popup.destroy()
                    messagebox.showinfo("Success", 
                        f"Data split completed!\n"
                        f"Train: {train_count} frames\n"
                        f"Validation: {val_count} frames\n"
                        f"Test: {len(frame_indices) - train_count - val_count} frames")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to split data: {str(e)}")
            
            def cancel_split():
                popup.destroy()
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=(15, 10))
            
            ttk.Button(button_frame, text="Split", command=perform_split, 
                      width=12).pack(side='left', padx=(0, 15))
            ttk.Button(button_frame, text="Cancel", command=cancel_split, 
                      width=12).pack(side='left')
            
            # Initial preview update
            update_preview()
            
            # Bind Escape key
            popup.bind('<Escape>', lambda e: cancel_split())
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create split dialog: {str(e)}")
            print(f"Error in split_data: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_dataset_splits(self, frame_indices, train_count, val_count):
        """Create ID-based dataset splits that reference the original data"""
        # Create lists of frame IDs for each dataset
        self.train_ids = frame_indices[:train_count]
        self.val_ids = frame_indices[train_count:train_count + val_count]
        self.test_ids = frame_indices[train_count + val_count:]
        
        print(f"\n=== DATASET SPLIT DEBUG ===")
        print(f"Total frames to split: {len(frame_indices)}")
        print(f"Train count: {train_count}, Val count: {val_count}, Test count: {len(self.test_ids)}")
        
        # Debug: Print first 10 IDs of each dataset
        print(f"\nTrain IDs (first 10): {self.train_ids[:10]}")
        print(f"Val IDs (first 10): {self.val_ids[:10]}")
        print(f"Test IDs (first 10): {self.test_ids[:10]}")
        
        # Validation tests
        self._validate_dataset_splits()
        
        print(f"✅ Created ID-based datasets - Train: {len(self.train_ids)} IDs, Val: {len(self.val_ids)} IDs, Test: {len(self.test_ids)} IDs")
        print("=== END DATASET SPLIT DEBUG ===\n")
    
    def _validate_dataset_splits(self):
        """Validate dataset splits for correctness"""
        print("\n--- VALIDATION TESTS ---")
        
        # Test 1: Check for duplicates within each dataset
        train_duplicates = len(self.train_ids) - len(set(self.train_ids))
        val_duplicates = len(self.val_ids) - len(set(self.val_ids))
        test_duplicates = len(self.test_ids) - len(set(self.test_ids))
        
        print(f"Test 1 - Duplicates within datasets:")
        print(f"  Train duplicates: {train_duplicates}")
        print(f"  Val duplicates: {val_duplicates}")
        print(f"  Test duplicates: {test_duplicates}")
        
        if train_duplicates == 0 and val_duplicates == 0 and test_duplicates == 0:
            print("  ✅ PASSED: No duplicates within individual datasets")
        else:
            print("  ❌ FAILED: Found duplicates within datasets!")
        
        # Test 2: Check for overlaps between datasets
        train_set = set(self.train_ids)
        val_set = set(self.val_ids)
        test_set = set(self.test_ids)
        
        train_val_overlap = train_set.intersection(val_set)
        train_test_overlap = train_set.intersection(test_set)
        val_test_overlap = val_set.intersection(test_set)
        
        print(f"\nTest 2 - Overlaps between datasets:")
        print(f"  Train-Val overlap: {len(train_val_overlap)} frames")
        print(f"  Train-Test overlap: {len(train_test_overlap)} frames")
        print(f"  Val-Test overlap: {len(val_test_overlap)} frames")
        
        if len(train_val_overlap) == 0 and len(train_test_overlap) == 0 and len(val_test_overlap) == 0:
            print("  ✅ PASSED: No overlaps between datasets")
        else:
            print("  ❌ FAILED: Found overlaps between datasets!")
            if train_val_overlap:
                print(f"    Train-Val overlap IDs: {list(train_val_overlap)[:10]}...")
            if train_test_overlap:
                print(f"    Train-Test overlap IDs: {list(train_test_overlap)[:10]}...")
            if val_test_overlap:
                print(f"    Val-Test overlap IDs: {list(val_test_overlap)[:10]}...")
        
        # Test 3: Check total count
        total_split = len(self.train_ids) + len(self.val_ids) + len(self.test_ids)
        original_total = len(self.main_dataset.lines)
        
        print(f"\nTest 3 - Total frame count:")
        print(f"  Original dataset: {original_total} frames")
        print(f"  Split total: {total_split} frames")
        print(f"  Difference: {abs(original_total - total_split)}")
        
        if total_split == original_total:
            print("  ✅ PASSED: Total frame count matches")
        else:
            print("  ❌ FAILED: Total frame count mismatch!")
        
        # Test 4: Check ID ranges
        all_ids = self.train_ids + self.val_ids + self.test_ids
        min_id = min(all_ids) if all_ids else 0
        max_id = max(all_ids) if all_ids else 0
        
        print(f"\nTest 4 - ID ranges:")
        print(f"  Min ID: {min_id}")
        print(f"  Max ID: {max_id}")
        print(f"  Expected range: 0 to {original_total - 1}")
        
        if min_id >= 0 and max_id < original_total:
            print("  ✅ PASSED: All IDs within valid range")
        else:
            print("  ❌ FAILED: Some IDs outside valid range!")
        
        print("--- END VALIDATION TESTS ---")
    
    def _get_current_dataset_pointer(self):
        """Get the pointer for the current dataset"""
        if self.current_dataset_type == 'train':
            return self.train_pointer
        elif self.current_dataset_type == 'validation':
            return self.val_pointer
        elif self.current_dataset_type == 'test':
            return self.test_pointer
        else:  # main
            return self.main_pointer
    
    def _set_current_dataset_pointer(self, position):
        """Set the pointer for the current dataset"""
        if self.current_dataset_type == 'train':
            self.train_pointer = max(0, min(position, len(self.train_ids) - 1))
        elif self.current_dataset_type == 'validation':
            self.val_pointer = max(0, min(position, len(self.val_ids) - 1))
        elif self.current_dataset_type == 'test':
            self.test_pointer = max(0, min(position, len(self.test_ids) - 1))
        else:  # main
            self.main_pointer = max(0, min(position, len(self.main_dataset.lines) - 1))
    
    def _get_current_global_frame_id(self):
        """Get the global frame ID in the original dataset based on current dataset and pointer"""
        if self.current_dataset_type == 'train':
            if self.train_pointer < len(self.train_ids):
                return self.train_ids[self.train_pointer]
        elif self.current_dataset_type == 'validation':
            if self.val_pointer < len(self.val_ids):
                return self.val_ids[self.val_pointer]
        elif self.current_dataset_type == 'test':
            if self.test_pointer < len(self.test_ids):
                return self.test_ids[self.test_pointer]
        else:  # main
            return self.main_pointer
        return 0
    
    def _sync_data_manager_to_current_frame(self):
        """Sync the data manager pointer to the current global frame ID"""
        global_frame_id = self._get_current_global_frame_id()
        print(f"DEBUG: _sync_data_manager_to_current_frame() - global_frame_id = {global_frame_id}")
        print(f"DEBUG: Before sync - data_manager._pointer = {self.data_manager._pointer}")
        
        self.data_manager._pointer = global_frame_id
        # Invalidate dataframe cache to force re-reading
        self.data_manager._read_pos = global_frame_id - 1
        
        print(f"DEBUG: After sync - data_manager._pointer = {self.data_manager._pointer}")
        print(f"DEBUG: data_manager.has_prev() = {self.data_manager.has_prev()}")
        print(f"DEBUG: Synced data_manager pointer to global frame {global_frame_id}")
    
    def _get_current_dataset_ids(self):
        """Get the current dataset's frame IDs"""
        if self.current_dataset_type == 'train':
            return self.train_ids
        elif self.current_dataset_type == 'validation':
            return self.val_ids
        elif self.current_dataset_type == 'test':
            return self.test_ids
        else:
            # Main dataset - return all frame indices
            return list(range(len(self.main_dataset.lines)))
    
    def _get_current_frame_id(self):
        """Get the actual frame ID in the original dataset"""
        # Use the dataset pointer system instead of current_dataset_position
        current_pointer = self._get_current_dataset_pointer()
        dataset_ids = self._get_current_dataset_ids()
        
        if current_pointer < len(dataset_ids):
            return dataset_ids[current_pointer]
        return 0
    
    def _navigate_to_frame_id(self, frame_id):
        """Navigate the main dataset to a specific frame ID"""
        if 0 <= frame_id < len(self.main_dataset.lines):
            self.main_dataset._pointer = frame_id
            self.data_manager._pointer = frame_id  # Keep data_manager in sync
            # Reset read position to force re-reading of the dataframe
            self.data_manager._read_pos = frame_id - 1

    def on_dataset_selection_changed(self):
        """Handle dataset selection change - switch to ID-based dataset with separate pointers"""
        if hasattr(self.ui_manager, 'selected_dataset'):
            selected = self.ui_manager.selected_dataset.get()
            old_dataset = self.current_dataset_type
            print(f"\n=== DATASET SELECTION CHANGE ===")
            print(f"Switching from: {old_dataset.upper()} → {selected.upper()}")
            
            # Save current position in old dataset's pointer
            if old_dataset == 'main':
                self.main_pointer = self.data_manager._pointer
                print(f"DEBUG: Saved main_pointer = {self.main_pointer}")
            elif old_dataset == 'train':
                # Current position within train dataset
                if self.data_manager._pointer in self.train_ids:
                    self.train_pointer = self.train_ids.index(self.data_manager._pointer)
                    print(f"DEBUG: Saved train_pointer = {self.train_pointer} (global frame {self.data_manager._pointer})")
            elif old_dataset == 'validation':
                if self.data_manager._pointer in self.val_ids:
                    self.val_pointer = self.val_ids.index(self.data_manager._pointer)
                    print(f"DEBUG: Saved val_pointer = {self.val_pointer} (global frame {self.data_manager._pointer})")
            elif old_dataset == 'test':
                if self.data_manager._pointer in self.test_ids:
                    self.test_pointer = self.test_ids.index(self.data_manager._pointer)
                    print(f"DEBUG: Saved test_pointer = {self.test_pointer} (global frame {self.data_manager._pointer})")
            
            print(f"Saved {old_dataset} pointer position")
            
            # Switch the current dataset type
            if selected.lower() == 'original':
                self.current_dataset_type = 'main'
            else:
                self.current_dataset_type = selected.lower()
            
            # Get info about the new dataset
            dataset_ids = self._get_current_dataset_ids()
            print(f"New dataset has {len(dataset_ids)} frames")
            
            # Restore position in new dataset using its saved pointer
            current_pointer = self._get_current_dataset_pointer()
            print(f"Restoring {self.current_dataset_type} dataset to pointer position: {current_pointer}")
            
            # Special handling for main dataset
            if self.current_dataset_type == 'main':
                print(f"DEBUG: For main dataset, main_pointer = {self.main_pointer}")
                print(f"DEBUG: data_manager._pointer before sync = {self.data_manager._pointer}")
                
                # Fix for main_pointer not being properly saved:
                # If main_pointer is 0 but data_manager._pointer is not, use data_manager value
                if self.main_pointer == 0 and self.data_manager._pointer > 0:
                    print(f"DEBUG: Correcting main_pointer from 0 to {self.data_manager._pointer}")
                    self.main_pointer = self.data_manager._pointer
                    current_pointer = self.main_pointer
            
            # Sync current_dataset_position with the dataset pointer for backward compatibility
            self.current_dataset_position = current_pointer
            
            # Sync data manager to the correct global frame
            self._sync_data_manager_to_current_frame()
            
            # Update display
            self.distances = self.data_manager.dataframe
            if len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                self.update_inputs()
            
            self.update_status()
            self.update_button_states()
            print(f"=== DATASET SELECTION COMPLETE ===\n")
    
    def get_dataset_frames(self, dataset_type=None):
        """Get all frame indices for the current dataset"""
        dataset_ids = self._get_current_dataset_ids()
        return list(range(len(dataset_ids)))
    
    def _update_previous_angular_velocity(self):
        """Update the previous angular velocity from current frame data"""
        try:
            if self.data_manager.dataframe and len(self.data_manager.dataframe) == LIDAR_RESOLUTION + 1:
                current_angular = float(self.data_manager.dataframe[360])
                if self.augmented_mode:
                    current_angular = -current_angular
                self.frame_navigator.prev_angular_velocity = current_angular
                
                # Update the previous angular velocity display
                self.ui_manager.prev_turn_var.set(f"{self.frame_navigator.prev_angular_velocity:.2f}")
                print(f"Updated previous angular velocity: {self.frame_navigator.prev_angular_velocity}")
        except (ValueError, TypeError, IndexError):
            self.frame_navigator.prev_angular_velocity = 0.0
            self.ui_manager.prev_turn_var.set("0.00")

    def navigate_dataset_frame(self, direction):
        """Navigate within the selected dataset using separate pointers"""
        print(f"\n=== DATASET NAVIGATION: {direction.upper()} ===")
        print(f"Current dataset: {self.current_dataset_type}")
        
        if not self.ui_manager.data_splits and self.current_dataset_type != 'main':
            # If no splits but not in main dataset, use normal navigation
            if direction == 'next':
                self.next_frame()
            elif direction == 'prev':
                self.prev_frame()
            elif direction == 'first':
                self.first_frame()
            elif direction == 'last':
                self.last_frame()
            return
        
        # Get current dataset info
        dataset_ids = self._get_current_dataset_ids()
        if not dataset_ids:
            print(f"No frames in {self.current_dataset_type} dataset")
            return
        
        current_pointer = self._get_current_dataset_pointer()
        print(f"Current pointer in {self.current_dataset_type}: {current_pointer}")
        
        # Calculate new position
        if direction == 'next':
            new_pointer = min(current_pointer + 1, len(dataset_ids) - 1)
        elif direction == 'prev':
            new_pointer = max(current_pointer - 1, 0)
        elif direction == 'first':
            new_pointer = 0
        elif direction == 'last':
            new_pointer = len(dataset_ids) - 1
        else:
            print(f"Unknown direction: {direction}")
            return
        
        print(f"Moving from pointer {current_pointer} to {new_pointer}")
        
        # Update the dataset pointer
        self._set_current_dataset_pointer(new_pointer)
        
        # Update previous angular velocity
        self._update_previous_angular_velocity()
        
        # Sync data manager to the correct global frame
        self._sync_data_manager_to_current_frame()
        
        # Update display
        self.distances = self.data_manager.dataframe
        if len(self.distances) == LIDAR_RESOLUTION + 1:
            self.render_frame()
            self.update_inputs()
            
            # Simple tkinter update after rendering
            if hasattr(self, 'ui_manager') and hasattr(self.ui_manager, 'root'):
                self.ui_manager.root.update()
        
        self.update_button_states()
        
        # Enhanced debug output
        global_frame_id = self._get_current_global_frame_id()
        print(f"Final state - Dataset: {self.current_dataset_type}, Pointer: {new_pointer}, Global Frame: {global_frame_id + 1}")
        print(f"=== NAVIGATION COMPLETE ===\n")
    
    def move_to_next_set(self):
        """Move current frame to the next dataset (train -> validation -> test -> train)"""
        try:
            from tkinter import messagebox
            
            if not hasattr(self, 'data_manager') or not self.data_manager:
                messagebox.showerror("Error", "No data manager available")
                return
                
            current_frame = self.data_manager.pointer
            
            # Check if data has been split
            if not self.ui_manager.data_splits:
                messagebox.showwarning("Warning", "Data has not been split yet. Please split data first.")
                return
            
            # Get current split type
            current_split = self.ui_manager.data_splits.get(current_frame, 'train')
            
            # Determine next split type
            if current_split == 'train':
                next_split = 'validation'
            elif current_split == 'validation':
                next_split = 'test'
            else:  # test
                next_split = 'train'
            
            # Update the split
            self.ui_manager.data_splits[current_frame] = next_split
            
            # Mark data as changed
            self.mark_data_changed()
            
            # Update status display
            self.update_status()
            
            print(f"Frame {current_frame} moved from {current_split} to {next_split} set")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move frame to next set: {str(e)}")
            print(f"Error moving frame to next set: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_rotation_transformation(self, angle_degrees):
        """Apply rotation transformation by shifting array indices"""
        try:
            # Get current data line
            current_line = self.data_manager.lines[self.data_manager.pointer]
            data_parts = current_line.strip().split(',')
            
            # Check if we have enough data points (expecting at least 361 elements)
            if len(data_parts) < 361:
                print(f"Warning: Insufficient data points for rotation ({len(data_parts)} < 361)")
                return
            
            # Backup current frame before modification
            self.data_manager.backup_current_frame()
            
            # Extract lidar data (first 360 elements) and angular velocity (last element)
            lidar_data = data_parts[:360]  # First 360 elements are LiDAR readings
            angular_velocity = data_parts[-1]  # Last element is angular velocity
            other_data = data_parts[360:-1] if len(data_parts) > 361 else []  # Any data between LiDAR and angular velocity
            
            # Calculate shift amount (1 degree = 1 index for 360-degree array)
            shift_amount = int(angle_degrees) % 360
            
            # Apply rotation by shifting array indices
            if shift_amount != 0:
                # Positive shift for counter-clockwise, negative for clockwise
                rotated_lidar = lidar_data[-shift_amount:] + lidar_data[:-shift_amount]
                
                # Reconstruct the data line with original angular velocity preserved
                new_data_parts = rotated_lidar + other_data + [angular_velocity]
                
                # Update the line in data manager
                new_line = ','.join(new_data_parts) + '\n'
                self.data_manager.lines[self.data_manager.pointer] = new_line
                self.data_manager.update_current_frame_from_string(new_line.strip())
                
                # Refresh display
                self.render_frame()
                
                print(f"Rotated LiDAR data by {angle_degrees}° (shifted by {shift_amount} indices), angular velocity preserved: {angular_velocity}")
            
        except Exception as e:
            print(f"Error applying rotation transformation: {e}")
            import traceback
            traceback.print_exc()
    
    # Update methods
    def update_button_states(self):
        """Update button states based on current mode"""
        print(f"DEBUG: update_button_states() called - current_dataset_type = {self.current_dataset_type}")
        
        if self.inspect_mode:
            # Show navigation buttons, hide play/pause
            self.ui_manager.play_pause_button.pack_forget()
            self.ui_manager.first_button.pack(side='left', padx=(0, 2), before=self.ui_manager.mode_button)
            self.ui_manager.prev_button.pack(side='left', padx=(0, 2), before=self.ui_manager.mode_button)
            self.ui_manager.next_button.pack(side='left', padx=(0, 2), before=self.ui_manager.mode_button)
            self.ui_manager.last_button.pack(side='left', padx=(0, 5), before=self.ui_manager.mode_button)
            
            # Show modified frame buttons
            self.ui_manager.modified_button_frame.pack(fill='x', pady=(5, 0))
            self.ui_manager.first_modified_button.pack(side='left', padx=(0, 2))
            self.ui_manager.prev_modified_button.pack(side='left', padx=(0, 2))
            self.ui_manager.next_modified_button.pack(side='left', padx=(0, 2))
            self.ui_manager.last_modified_button.pack(side='left', padx=(0, 5))
            
            # Check if we're in dataset navigation mode
            has_data_splits = hasattr(self.ui_manager, 'data_splits') and self.ui_manager.data_splits
            print(f"DEBUG: has_data_splits = {has_data_splits}")
            
            if has_data_splits:
                # Use dataset navigation logic
                print(f"DEBUG: Using dataset navigation logic")
                self._update_dataset_button_states()
            else:
                # Use regular navigation logic
                print(f"DEBUG: Using regular navigation logic")
                self._update_regular_button_states()
        else:
            # Hide navigation buttons, show play/pause
            self.ui_manager.first_button.pack_forget()
            self.ui_manager.prev_button.pack_forget()
            self.ui_manager.next_button.pack_forget()
            self.ui_manager.last_button.pack_forget()
            self.ui_manager.modified_button_frame.pack_forget()
            
            self.ui_manager.play_pause_button.pack(side='left', padx=(0, 5), before=self.ui_manager.mode_button)
            
            # Update play/pause button
            if self.paused:
                self.ui_manager.play_pause_button.config(text="Play")
            else:
                self.ui_manager.play_pause_button.config(text="Pause")
    
    def _update_dataset_button_states(self):
        """Update button states for dataset navigation mode using separate pointers"""
        dataset_ids = self._get_current_dataset_ids()
        if not dataset_ids:
            # No frames in current dataset - disable all
            self.ui_manager.prev_button.config(state='disabled')
            self.ui_manager.first_button.config(state='disabled')
            self.ui_manager.next_button.config(state='disabled')
            self.ui_manager.last_button.config(state='disabled')
            return
        
        # Use the separate dataset pointer instead of trying to find global frame in local indices
        current_pointer = self._get_current_dataset_pointer()
        total_frames = len(dataset_ids)
        
        print(f"DEBUG: Button state update - Dataset: {self.current_dataset_type}, Pointer: {current_pointer}, Total: {total_frames}")
        
        # Check if we can go backward
        if current_pointer > 0:
            self.ui_manager.prev_button.config(state='normal')
            self.ui_manager.first_button.config(state='normal')
        else:
            self.ui_manager.prev_button.config(state='disabled')
            self.ui_manager.first_button.config(state='disabled')
        
        # Check if we can go forward
        if current_pointer < total_frames - 1:
            self.ui_manager.next_button.config(state='normal')
            self.ui_manager.last_button.config(state='normal')
        else:
            self.ui_manager.next_button.config(state='disabled')
            self.ui_manager.last_button.config(state='disabled')
    
    def _update_regular_button_states(self):
        """Update button states for regular navigation mode"""
        # Update button states based on frame info
        frame_info = self.frame_navigator.get_current_frame_info()
        
        # Regular navigation buttons
        if not frame_info['has_prev']:
            self.ui_manager.prev_button.config(state='disabled')
            self.ui_manager.first_button.config(state='disabled')
        else:
            self.ui_manager.prev_button.config(state='normal')
            self.ui_manager.first_button.config(state='normal')
            
        if not frame_info['has_next']:
            self.ui_manager.next_button.config(state='disabled')
            self.ui_manager.last_button.config(state='disabled')
        else:
            self.ui_manager.next_button.config(state='normal')
            self.ui_manager.last_button.config(state='normal')
        
        # Modified frame buttons
        if frame_info['modified_count'] > 0:
            if not frame_info['has_prev_modified']:
                self.ui_manager.prev_modified_button.config(state='disabled')
                self.ui_manager.first_modified_button.config(state='disabled')
            else:
                self.ui_manager.prev_modified_button.config(state='normal')
                self.ui_manager.first_modified_button.config(state='normal')
                
            if not frame_info['has_next_modified']:
                self.ui_manager.next_modified_button.config(state='disabled')
                self.ui_manager.last_modified_button.config(state='disabled')
            else:
                self.ui_manager.next_modified_button.config(state='normal')
                self.ui_manager.last_modified_button.config(state='normal')
        else:
            self.ui_manager.first_modified_button.config(state='disabled')
            self.ui_manager.prev_modified_button.config(state='disabled')
            self.ui_manager.next_modified_button.config(state='disabled')
            self.ui_manager.last_modified_button.config(state='disabled')
        
        # Update mode button
        if self.inspect_mode:
            self.ui_manager.mode_button.config(text="Mode: Inspect")
        else:
            self.ui_manager.mode_button.config(text="Mode: Cont")
    
    def update_status(self):
        """Update status display"""
        mode_text = 'INSPECT' if self.inspect_mode else 'CONTINUOUS'
        if self.paused and not self.inspect_mode:
            mode_text = 'PAUSED'
        
        data_text = 'AUGMENTED' if self.augmented_mode else 'REAL'
        
        # Add dataset split information if data has been split
        split_text = ""
        if hasattr(self, 'train_ids') and self.train_ids:
            # We're in dataset mode - show current dataset info
            if self.current_dataset_type != 'main':
                dataset_ids = self._get_current_dataset_ids()
                current_pos = self._get_current_dataset_pointer() + 1  # Use dataset pointer instead
                total_in_set = len(dataset_ids)
                current_frame_id = self._get_current_frame_id() + 1  # +1 for display
                split_text = f" | Dataset: {self.current_dataset_type.upper()} ({current_pos}/{total_in_set}) | Frame ID: {current_frame_id}"
            else:
                # Main dataset mode
                current_pos = self.data_manager._pointer + 1
                total_frames = len(self.data_manager.lines)
                split_text = f" | Frame: {current_pos}/{total_frames}"
        else:
            # No splits created yet
            current_pos = self.data_manager._pointer + 1
            total_frames = len(self.data_manager.lines)
            split_text = f" | Frame: {current_pos}/{total_frames}"
        
        self.ui_manager.status_var.set(f"Data: {os.path.basename(self.config['data_file'])} | Mode: {mode_text} | Data: {data_text}{split_text}")
    
    def update_inputs(self):
        """Update input fields and info displays using separate dataset pointers"""
        try:
            # Check if we're navigating a split dataset
            if hasattr(self.ui_manager, 'data_splits') and self.ui_manager.data_splits and self.current_dataset_type != 'main':
                # Get current dataset info using separate pointers
                dataset_ids = self._get_current_dataset_ids()
                current_pointer = self._get_current_dataset_pointer()
                global_frame_id = self._get_current_global_frame_id()
                
                if dataset_ids and current_pointer < len(dataset_ids):
                    # Show: actual frame ID from original dataset (global frame + 1)
                    actual_frame_id = global_frame_id + 1
                    # Position within current dataset
                    dataset_position = current_pointer + 1
                    total_dataset_frames = len(dataset_ids)
                    
                    # Only update frame input field if not currently focused
                    try:
                        current_focus = self.ui_manager.frame_entry.focus_get()
                        frame_field_focused = (current_focus == self.ui_manager.frame_entry)
                    except:
                        frame_field_focused = False
                        
                    if not frame_field_focused:
                        self.ui_manager.frame_var.set(str(actual_frame_id))
                    
                    dataset_name = self.current_dataset_type.title()
                    self.ui_manager.total_frames_label.config(text=f"of {total_dataset_frames} ({dataset_name})")
                    
                    # Update frame information display
                    mode_text = "AUGMENTED" if self.augmented_mode else "REAL"
                    self.ui_manager.frame_info_var.set(f"Frame: {actual_frame_id} ({dataset_position}/{total_dataset_frames} in {dataset_name}) [{mode_text}]")
                else:
                    # Fallback to default frame info if current frame not in dataset
                    frame_info = self.frame_navigator.get_current_frame_info()
                    if not frame_field_focused:
                        self.ui_manager.frame_var.set(str(frame_info['current_frame']))
                    self.ui_manager.total_frames_label.config(text=f"of {frame_info['total_frames']}")
                    mode_text = "AUGMENTED" if self.augmented_mode else "REAL"
                    self.ui_manager.frame_info_var.set(f"Frame: {frame_info['current_frame']}/{frame_info['total_frames']} [{mode_text}]")
            else:
                # Original dataset or no splits - use default frame info
                frame_info = self.frame_navigator.get_current_frame_info()
                
                # Only update frame input field if not currently focused
                try:
                    current_focus = self.ui_manager.frame_entry.focus_get()
                    frame_field_focused = (current_focus == self.ui_manager.frame_entry)
                except:
                    frame_field_focused = False
                    
                if not frame_field_focused:
                    self.ui_manager.frame_var.set(str(frame_info['current_frame']))
                
                self.ui_manager.total_frames_label.config(text=f"of {frame_info['total_frames']}")
                
                # Update frame information display
                mode_text = "AUGMENTED" if self.augmented_mode else "REAL"
                self.ui_manager.frame_info_var.set(f"Frame: {frame_info['current_frame']}/{frame_info['total_frames']} [{mode_text}]")
            
            # Update modified frames information display (following original pattern)
            total_modified = len(self.data_manager.modified_frames)
            if total_modified > 0:
                # If current frame is in modified frames list, show position in that list
                current_frame_index = self.data_manager.pointer
                if current_frame_index in self.data_manager.modified_frames:
                    current_modified_pos = self.data_manager.modified_frames.index(current_frame_index) + 1
                    self.ui_manager.modified_info_var.set(f"Modified: {current_modified_pos}/{total_modified} [Frame #{current_frame_index + 1}]")
                else:
                    self.ui_manager.modified_info_var.set(f"Modified: {total_modified} frames total")
            else:
                self.ui_manager.modified_info_var.set("Modified: 0 frames")

            # Update angular velocity fields (only if not currently focused)
            if len(self.distances) == 361:
                current_angular = float(self.distances[360])
                # Use actual angular value (data is flipped if needed, no display modification)
                
                # Only update if the turn entry field is not focused
                try:
                    turn_focus = self.ui_manager.turn_entry.focus_get()
                    turn_field_focused = (turn_focus == self.ui_manager.turn_entry)
                except:
                    turn_field_focused = False
                    
                if not turn_field_focused:
                    self.ui_manager.turn_var.set(f"{current_angular:.2f}")
            
            # Update previous angular velocity (read-only field)
            prev_angular = self.frame_navigator.prev_angular_velocity
            self.ui_manager.prev_turn_var.set(f"{prev_angular:.2f}")
            
        except Exception as e:
            print(f"Error updating inputs: {e}")
    
    def render_frame(self):
        """Render the current frame using the visualization renderer"""
        if self.distances and len(self.distances) == 361:
            self.renderer.render_frame(
                distances=self.distances,
                augmented_mode=self.augmented_mode,
                prev_angular_velocity=self.frame_navigator.prev_angular_velocity,
                show_current_vel=self.ui_manager.show_current_vel.get(),
                show_prev_vel=self.ui_manager.show_prev_vel.get(),
                show_pred_vel=self.ui_manager.show_pred_vel.get(),
                show_forward_dir=self.ui_manager.show_forward_dir.get(),
                data_manager=self.data_manager,
                pred_turn_var=self.ui_manager.pred_turn_var
            )
        else:
            print(f"Cannot render frame - distances: {len(self.distances) if self.distances else 0} points (expected 361)")
    
    def update_display(self):
        """Update the complete display"""
        self.distances = self.data_manager.dataframe
        if len(self.distances) == 361:
            self.render_frame()
            self.update_inputs()
    
    def animate(self):
        """Animation loop using tkinter's after method"""
        if not self.running:
            return
            
        try:
            # Handle inspection mode
            if self.inspect_mode:
                self.paused = True
            
            # Process data if available
            if self.data_manager.has_next():
                # In inspect mode, always get current data; in continuous mode, only when read_pos < pointer
                need_to_read_data = (self.inspect_mode or 
                                   self.data_manager.read_pos < self.data_manager.pointer)
                
                if need_to_read_data:
                    try:
                        self.distances = self.data_manager.dataframe
                        
                        if self.distances and len(self.distances) == 361:
                            self.render_frame()
                            self.update_inputs()
                    except Exception as e:
                        print(f"Error processing data frame: {e}")
                
                # Auto-advance frame only if not paused (continuous mode)
                if not self.paused:
                    try:
                        # Store current angular velocity as previous before advancing
                        self.frame_navigator.update_previous_angular_velocity(self.distances, self.augmented_mode)
                        
                        # Advance to next frame
                        self.data_manager.next()
                    except Exception as e:
                        print(f"Error advancing frame: {e}")
            
            # Schedule next animation frame
            self.root.after(50, self.animate)  # 20 FPS
            
        except Exception as e:
            print(f"Error in animation loop: {e}")
            # Continue animation even if there's an error
            self.root.after(100, self.animate)
    
    def show_logging_config(self):
        """Show logging configuration dialog"""
        try:
            from ui_components import LoggingConfigDialog
            log_ui_event("Logging config dialog opened")
            dialog = LoggingConfigDialog(self.root)
        except Exception as e:
            error(f"Error opening logging config dialog: {e}", "UI")
            messagebox.showerror("Error", f"Could not open logging configuration: {str(e)}")
    
    def show_log_viewer(self):
        """Show log viewer dialog"""
        try:
            from ui_components import LogViewerDialog
            log_ui_event("Log viewer dialog opened")
            dialog = LogViewerDialog(self.root)
        except Exception as e:
            error(f"Error opening log viewer dialog: {e}", "UI")
            messagebox.showerror("Error", f"Could not open log viewer: {str(e)}")
    
    def on_closing(self):
        """Handle window close event"""
        try:
            # Check for unsaved changes before closing
            if not self.prompt_save_before_exit():
                return  # User cancelled the exit
            
            self.running = False
            self.renderer.cleanup()
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            # Force exit if needed
            import sys
            sys.exit(0)
