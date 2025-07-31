import pygame
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
import shutil
import threading
import traceback
import sys
from pginput import InputBox, DataManager

# constant based on lidar resolution
LIDAR_RESOLUTION = 360
# Constant screen width
SCREEN_WIDTH = 800
# Scale factor for distance visualization (will be auto-calculated based on data)
SCALE_FACTOR = 0.25  # Default fallback value
# Target visualization radius (pixels from center)
TARGET_RADIUS = 300  # Use ~300 pixels of the 400 pixel radius available
# Selected positions in a frame (result of the Sklearn SelectKBest function)
DECISIVE_FRAME_POSITIONS = [24, 29, 31, 35, 38, 39, 40, 41, 42, 43, 44, 45, 47, 50, 54, 55, 57, 302,
                            304, 312, 314, 315, 316, 318, 319, 321, 324, 326, 328, 330]


class VisualizerWindow:
    def __init__(self, config):
        self.config = config
        self.running = True
        self.paused = True  # Start paused by default
        self.inspect_mode = False  # Start in continuous mode by default (not inspection mode)
        self.augmented_mode = config['augmented_mode']
        
        # Initialize data manager
        self.data_manager = DataManager(config['data_file'], 'data/run2/_out.txt', False)
        calculate_scale_factor(self.data_manager)
        
        # Create main tkinter window
        self.root = tk.Tk()
        self.root.title(f"Lidar Visualizer - {os.path.basename(config['data_file'])}")
        self.root.geometry("850x750")  # Reduced size for better usability
        self.root.resizable(True, True)  # Make window resizable
        self.root.minsize(600, 500)  # Set minimum size
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (850 // 2)
        y = (self.root.winfo_screenheight() // 2) - (750 // 2)
        self.root.geometry(f"850x750+{x}+{y}")
        
        # Bind resize event for dynamic scaling
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Initialize canvas size before UI setup
        self.current_canvas_size = 680  # Increased canvas size further due to removed title
        
        # Setup UI first
        self.setup_ui()
        
        # Initialize pygame after UI setup
        self.init_pygame()
        
        # Initialize variables
        self.distances = []
        
        # Update button states after everything is set up
        self.update_button_states()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup animation timer
        self.animate()
    
    def on_window_resize(self, event):
        """Handle window resize events and scale canvas accordingly"""
        # Only handle resize events from the main window
        if event.widget == self.root:
            # Calculate available space for canvas (considering UI elements)
            # Account for smaller left sidebar (150px) and top controls (no title now)
            available_width = self.root.winfo_width() - 170  # Account for narrower left sidebar
            available_height = self.root.winfo_height() - 170  # Account for controls, status, and padding (reduced since no title)
            
            # Calculate optimal canvas size (square, limited by smaller dimension)
            max_canvas_size = min(available_width, available_height, 800)  # Cap at 800px
            new_canvas_size = max(300, max_canvas_size)  # Minimum 300px
            
            # Only update if size changed significantly
            if abs(new_canvas_size - self.current_canvas_size) > 10:
                self.current_canvas_size = new_canvas_size
                self.update_canvas_size()
    
    def update_canvas_size(self):
        """Update the pygame canvas size"""
        try:
            # Update pygame frame and canvas size
            self.pygame_frame.configure(width=self.current_canvas_size, height=self.current_canvas_size)
            self.canvas.configure(width=self.current_canvas_size, height=self.current_canvas_size)
            
            # Reinitialize pygame with new size
            if hasattr(self, 'screen'):
                self.screen = pygame.display.set_mode([self.current_canvas_size, self.current_canvas_size])
                
        except Exception as e:
            print(f"Error updating canvas size: {e}")
    
    def init_pygame(self):
        """Initialize pygame with proper embedding"""
        # Get the tkinter canvas window ID for embedding
        self.canvas.update()
        
        # Set environment variables for pygame embedding
        embed_info = self.canvas.winfo_id()
        os.environ['SDL_WINDOWID'] = str(embed_info)
        if os.name == 'posix':  # Linux/Unix
            os.environ['SDL_VIDEODRIVER'] = 'x11'
        
        # Initialize pygame
        pygame.init()
        
        # Create pygame surface with dynamic size
        self.screen = pygame.display.set_mode([self.current_canvas_size, self.current_canvas_size])
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
    
    def setup_ui(self):
        """Setup the tkinter UI components"""
        # Create menu bar
        self.create_menu_bar()
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Control buttons panel - moved to top, horizontal layout
        controls_panel = ttk.LabelFrame(main_frame, text="Controls", padding=5)
        controls_panel.pack(fill='x', pady=(0, 5))
        
        # Create horizontal button layout
        button_frame = ttk.Frame(controls_panel)
        button_frame.pack(fill='x')
        
        # Control buttons - horizontal layout
        self.play_pause_button = ttk.Button(button_frame, text="▶ Play", 
                                           command=self.toggle_pause, width=12)
        self.play_pause_button.pack(side='left', padx=(0, 5))
        
        # Prev/Next buttons for inspection mode (initially hidden)
        self.first_button = ttk.Button(button_frame, text="⏮ First", 
                                      command=self.first_frame, width=12)
        self.prev_button = ttk.Button(button_frame, text="◀ Prev", 
                                     command=self.prev_frame, width=12)
        self.next_button = ttk.Button(button_frame, text="Next ▶", 
                                     command=self.next_frame, width=12)
        self.last_button = ttk.Button(button_frame, text="Last ⏭", 
                                     command=self.last_frame, width=12)
        
        self.mode_button = ttk.Button(button_frame, text="Mode: Cont", 
                                     command=self.toggle_inspect, width=12)
        self.mode_button.pack(side='left', padx=(0, 5))
        
        ttk.Button(button_frame, text="Augmented", 
                  command=self.toggle_augmented, width=12).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Quit", 
                  command=self.quit_visualizer, width=12).pack(side='left', padx=(0, 5))
        
        # Keyboard shortcuts info - more compact, on the right side
        shortcuts_label = ttk.Label(button_frame, 
                                   text="💡 Shortcuts: Space=Play/Next | I=Mode | A=Augmented | Q=Quit | ←→=Prev/Next | Home/End=First/Last", 
                                   font=('Arial', 8), foreground='navy')
        shortcuts_label.pack(side='right', padx=(10, 0))
        
        # Status display - make it more compact
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=3)
        status_frame.pack(fill='x', pady=(0, 5))
        
        self.status_var = tk.StringVar()
        self.status_var.set(f"Data: {os.path.basename(self.config['data_file'])} | Mode: {'INSPECT' if self.inspect_mode else 'CONTINUOUS'} | Data: {'AUGMENTED' if self.augmented_mode else 'REAL'}")
        ttk.Label(status_frame, textvariable=self.status_var, 
                 font=('Courier', 9)).pack()
        
        # Create horizontal layout for main content
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        # Left sidebar - narrower, only input controls
        left_sidebar = ttk.Frame(content_frame, width=150)  # Reduced from default width
        left_sidebar.pack(side='left', fill='y', padx=(0, 5))
        left_sidebar.pack_propagate(False)  # Maintain fixed width
        
        # Input Controls panel (only panel in left sidebar now)
        input_panel = ttk.LabelFrame(left_sidebar, text="🎮 Input Controls", padding=6)
        input_panel.pack(fill='both', expand=True)
        
        # Angular velocity input
        ttk.Label(input_panel, text="Angular Velocity:", 
                 font=('Arial', 9, 'bold'), foreground='darkblue').pack(anchor='w', pady=(0, 2))
        
        self.turn_var = tk.StringVar()
        self.turn_entry = ttk.Entry(input_panel, textvariable=self.turn_var, 
                                   width=18, font=('Courier', 9))
        self.turn_entry.pack(pady=(0, 5), fill='x')
        
        # Status info below angular velocity input
        self.frame_info_var = tk.StringVar()
        self.frame_info_var.set("Frame: -- [--]")
        frame_info_label = ttk.Label(input_panel, textvariable=self.frame_info_var, 
                                    font=('Courier', 8), foreground='blue')
        frame_info_label.pack(pady=(0, 5), fill='x')
        
        # Instructions for angular velocity
        ttk.Label(input_panel, text="📝 Press Enter to update", 
                 font=('Arial', 7), foreground='darkgreen', 
                 wraplength=140).pack(anchor='w', pady=(0, 8), fill='x')
        
        # Linear velocity input
        ttk.Label(input_panel, text="Linear Velocity:", 
                 font=('Arial', 9, 'bold'), foreground='darkblue').pack(anchor='w', pady=(0, 2))
        
        self.linear_var = tk.StringVar()
        self.linear_entry = ttk.Entry(input_panel, textvariable=self.linear_var, 
                                     width=18, font=('Courier', 9))
        self.linear_entry.pack(pady=(0, 5), fill='x')
        
        # Instructions for linear velocity
        ttk.Label(input_panel, text="⚠️ Not implemented", 
                 font=('Arial', 7), foreground='gray', 
                 wraplength=140).pack(anchor='w', pady=(0, 8), fill='x')
        
        # Resize instruction in input panel
        resize_label = ttk.Label(input_panel, 
                                text="🔧 Resize window to scale visualizer", 
                                font=('Arial', 7), foreground='purple', 
                                justify='center', wraplength=140)
        resize_label.pack(pady=(8, 0), fill='x')
        
        # Center panel - Pygame canvas (now takes up much more space)
        center_panel = ttk.LabelFrame(content_frame, text="Lidar Visualization", padding=5)
        center_panel.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        # Create a frame for pygame embedding with dynamic size
        self.pygame_frame = tk.Frame(center_panel, width=self.current_canvas_size, height=self.current_canvas_size, bg='lightgray')
        self.pygame_frame.pack(pady=5, expand=True, fill='both')
        self.pygame_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Create a canvas widget for pygame to render into
        self.canvas = tk.Canvas(self.pygame_frame, width=self.current_canvas_size, height=self.current_canvas_size, bg='white')
        self.canvas.pack(expand=True)
        
        # Initialize the button states after setup
        self.update_button_states()
        
        # Bind Enter key to input fields for data update (matching original pygame behavior)
        self.turn_entry.bind('<Return>', self.on_angular_velocity_input)
        self.linear_entry.bind('<Return>', self.on_linear_velocity_input)
        
        # Bind keyboard events to root window
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.focus_set()  # Allow window to receive key events
    
    def create_menu_bar(self):
        """Create the main menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Browse Data...", command=self.browse_data_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save Data", command=self.save_data, accelerator="Ctrl+S")
        
        # Data menu
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Show Statistics...", command=self.show_data_statistics, accelerator="Ctrl+I")
        
        # Visual menu
        visual_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visual", menu=visual_menu)
        visual_menu.add_command(label="Scale Factor...", command=self.show_scale_factor_dialog)
        
        # Bind keyboard shortcuts
        self.root.bind_all("<Control-o>", lambda e: self.browse_data_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_data())
        self.root.bind_all("<Control-i>", lambda e: self.show_data_statistics())
    
    def on_key_press(self, event):
        """Handle keyboard events"""
        if event.keysym == 'space':
            if self.inspect_mode:
                # In inspect mode, space advances to next frame
                self.next_frame()
            else:
                # In continuous mode, space toggles play/pause
                self.toggle_pause()
        elif event.keysym.lower() == 'i':
            self.toggle_inspect()
        elif event.keysym.lower() == 'a':
            self.toggle_augmented()
        elif event.keysym.lower() == 'q':
            self.quit_visualizer()
        elif event.keysym == 'Left' and self.inspect_mode:
            # Left arrow key for previous frame in inspect mode
            self.prev_frame()
        elif event.keysym == 'Right' and self.inspect_mode:
            # Right arrow key for next frame in inspect mode
            self.next_frame()
        elif event.keysym == 'Home' and self.inspect_mode:
            # Home key for first frame in inspect mode
            self.first_frame()
        elif event.keysym == 'End' and self.inspect_mode:
            # End key for last frame in inspect mode
            self.last_frame()
    
    def prev_frame(self):
        """Move to previous frame in inspect mode"""
        if self.inspect_mode and self.data_manager.has_prev():
            # Move back one frame using DataManager's prev method
            self.data_manager.prev()
            
            # Update display
            self.distances = self.data_manager.dataframe
            if len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                self.update_inputs()
            
            # Update button states after moving
            self.update_button_states()
            
            print(f"Moved to previous frame: {self.data_manager.read_pos + 1}/{len(self.data_manager.lines)}")
    
    def next_frame(self):
        """Move to next frame in inspect mode"""
        if self.inspect_mode and self.data_manager.has_next():
            # Move forward one frame using DataManager's next method
            self.data_manager.next()
            
            # Update display
            self.distances = self.data_manager.dataframe
            if len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                self.update_inputs()
            
            # Update button states after moving
            self.update_button_states()
            
            print(f"Moved to next frame: {self.data_manager.read_pos + 1}/{len(self.data_manager.lines)}")

    def first_frame(self):
        """Jump to first frame in inspect mode"""
        if self.inspect_mode:
            # Jump to first frame using DataManager's first method
            self.data_manager.first()
            
            # Update display
            self.distances = self.data_manager.dataframe
            if len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                self.update_inputs()
            
            # Update button states after moving
            self.update_button_states()
            
            print(f"Jumped to first frame: {self.data_manager.read_pos + 1}/{len(self.data_manager.lines)}")

    def last_frame(self):
        """Jump to last frame in inspect mode"""
        if self.inspect_mode:
            # Jump to last frame using DataManager's last method
            self.data_manager.last()
            
            # Update display
            self.distances = self.data_manager.dataframe
            if len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                self.update_inputs()
            
            # Update button states after moving
            self.update_button_states()
            
            print(f"Jumped to last frame: {self.data_manager.read_pos + 1}/{len(self.data_manager.lines)}")
    
    def advance_frame(self):
        """Advance to next frame in inspect mode (legacy method - now uses next_frame)"""
        self.next_frame()
    
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
            # When exiting inspect mode, default to unpaused (playing) state
            self.paused = False
        self.update_status()
        self.update_button_states()
        print(f'INSPECT MODE: {self.inspect_mode}')
    
    def toggle_augmented(self):
        """Toggle augmented mode"""
        self.augmented_mode = not self.augmented_mode
        print(f'AUGMENTED MODE: {self.augmented_mode}')
        self.update_status()
    
    def update_button_states(self):
        """Update button text based on current state"""
        if self.inspect_mode:
            # In inspect mode: hide play/pause, show navigation buttons
            self.play_pause_button.pack_forget()
            self.first_button.pack(side='left', padx=(0, 2), before=self.mode_button)
            self.prev_button.pack(side='left', padx=(0, 2), before=self.mode_button)
            self.next_button.pack(side='left', padx=(0, 2), before=self.mode_button)
            self.last_button.pack(side='left', padx=(0, 5), before=self.mode_button)
            
            # Update navigation button states based on position
            if not self.data_manager.has_prev():
                self.prev_button.config(state='disabled')
                self.first_button.config(state='disabled')
            else:
                self.prev_button.config(state='normal')
                self.first_button.config(state='normal')
                
            if not self.data_manager.has_next():
                self.next_button.config(state='disabled')
                self.last_button.config(state='disabled')
            else:
                self.next_button.config(state='normal')
                self.last_button.config(state='normal')
        else:
            # In continuous mode: show play/pause, hide navigation buttons
            self.first_button.pack_forget()
            self.prev_button.pack_forget()
            self.next_button.pack_forget()
            self.last_button.pack_forget()
            self.play_pause_button.pack(side='left', padx=(0, 5), before=self.mode_button)
            
            # Update play/pause button
            if self.paused:
                self.play_pause_button.config(text="▶ Play")
            else:
                self.play_pause_button.config(text="⏸ Pause")
        
        # Update mode button
        if self.inspect_mode:
            self.mode_button.config(text="Mode: Inspect")
        else:
            self.mode_button.config(text="Mode: Cont")
    
    def update_status(self):
        """Update status display"""
        mode_text = 'INSPECT' if self.inspect_mode else 'CONTINUOUS'
        if self.paused and not self.inspect_mode:
            mode_text = 'PAUSED'
        
        data_text = 'AUGMENTED' if self.augmented_mode else 'REAL'
        
        self.status_var.set(f"Data: {os.path.basename(self.config['data_file'])} | Mode: {mode_text} | Data: {data_text}")
    
    def browse_data_file(self):
        """Browse for a new data file and load it"""
        file_types = [
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=file_types,
            initialdir="/home/andy"
        )
        
        if filename:
            try:
                # Update status to show loading
                old_status = self.status_var.get()
                self.status_var.set("Loading new data file...")
                self.root.update()
                
                # Create new data manager with the selected file
                self.data_manager = DataManager(filename, 'data/run2/_out.txt', False)
                calculate_scale_factor(self.data_manager)
                
                # Update config
                self.config['data_file'] = filename
                
                # Update window title
                self.root.title(f"Lidar Visualizer - {os.path.basename(filename)}")
                
                # Reset visualization state
                self.distances = []
                
                # Update status to show success
                self.status_var.set(f"Data loaded: {os.path.basename(filename)} | Mode: {'INSPECT' if self.inspect_mode else 'CONTINUOUS'} | Data: {'AUGMENTED' if self.augmented_mode else 'REAL'}")
                
                print(f"Successfully loaded data file: {filename}")
                
            except Exception as e:
                error_msg = f"Failed to load data file: {str(e)}"
                messagebox.showerror("Error", error_msg)
                self.status_var.set(old_status)  # Restore previous status
                print(f"Error loading data file: {e}")
    
    def save_data(self):
        """Save the current data using DataManager's write functionality"""
        try:
            # Check if we have data manager and it has an output file configured
            if not hasattr(self, 'data_manager') or not self.data_manager:
                messagebox.showerror("Error", "No data manager available for saving")
                return
            
            # In inspect mode, write the current frame before saving
            if self.inspect_mode and hasattr(self.data_manager, 'write_line'):
                self.data_manager.write_line()
            
            # Save all data (write remaining frames if in continuous mode)
            if hasattr(self.data_manager, 'write_line') and not self.inspect_mode:
                self.data_manager.write_line()
                
            # Show success message
            out_file = getattr(self.data_manager, 'out_file', 'output file')
            self.status_var.set(f"Data saved to {os.path.basename(out_file)} | Mode: {'INSPECT' if self.inspect_mode else 'CONTINUOUS'} | Data: {'AUGMENTED' if self.augmented_mode else 'REAL'}")
            messagebox.showinfo("Success", f"Data saved successfully to {os.path.basename(out_file)}")
            print(f"Data saved to: {out_file}")
            
        except Exception as e:
            error_msg = f"Failed to save data: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error saving data: {e}")
    
    def show_data_statistics(self):
        """Show data statistics popup for current data file"""
        try:
            if not hasattr(self, 'data_manager') or not self.data_manager:
                messagebox.showerror("Error", "No data loaded")
                return
            
            # Update status to show analysis in progress
            old_status = self.status_var.get()
            self.status_var.set("Analyzing data...")
            self.root.update()
            
            # Analyze the current data file
            stats = self.analyze_data_file(self.config['data_file'])
            
            # Show statistics popup (reuse the method from StartupConfigWindow)
            self.display_data_statistics(stats, self.config['data_file'])
            
            # Restore status
            self.status_var.set(old_status)
            
        except Exception as e:
            error_msg = f"Failed to analyze data: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.status_var.set(old_status if 'old_status' in locals() else "Error analyzing data")
            print(f"Error analyzing data: {e}")
    
    def has_header(self, data_file):
        """Detect if the file has a header row"""
        try:
            with open(data_file, 'r') as f:
                first_line = f.readline().strip()
                if not first_line:
                    return False
                
                # Split the first line
                data = first_line.split(',')
                
                # For our lidar data format, we expect exactly 361 columns (360 lidar + 1 angular velocity)
                if len(data) != LIDAR_RESOLUTION + 1:
                    return False  # Not the expected format
                
                # Check if first line contains mostly non-numeric data (likely headers)
                numeric_count = 0
                non_numeric_items = []
                for item in data:
                    try:
                        float(item)
                        numeric_count += 1
                    except (ValueError, TypeError):
                        non_numeric_items.append(item.strip().lower())
                
                # If less than 80% of values are numeric, likely a header
                numeric_percentage = (numeric_count / len(data)) * 100
                if numeric_percentage < 80:
                    return True
                
                # Additional check: if first line has typical header words AND multiple non-numeric fields
                # This prevents false positives from data files with mostly numeric data but one text field
                if len(non_numeric_items) > 1:  # More than one non-numeric field suggests headers
                    header_keywords = ['lidar', 'angle', 'distance', 'angular', 'velocity', 'x', 'y', 'theta']
                    for item in non_numeric_items:
                        for keyword in header_keywords:
                            if keyword in item:
                                return True
                
                return False
                
        except Exception as e:
            print(f"Error detecting header: {e}")
            return False
    
    def analyze_data_file(self, data_file):
        """Analyze data file and return statistics (moved from StartupConfigWindow)"""
        
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Data file not found: {data_file}")
        
        # Check if file has headers
        has_headers = self.has_header(data_file)
        
        angular_velocities = []
        total_invalid_count = 0
        frames_with_invalid = 0
        total_frames = 0
        
        with open(data_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Skip header line if present
                if has_headers and line_num == 1:
                    continue
                
                try:
                    data = line.split(',')
                    if len(data) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                        total_frames += 1
                        
                        # Check for invalid data in lidar readings
                        invalid_in_frame = 0
                        for i in range(LIDAR_RESOLUTION):
                            try:
                                value = float(data[i])
                                if math.isinf(value) or math.isnan(value) or value == 0:
                                    invalid_in_frame += 1
                            except (ValueError, TypeError):
                                invalid_in_frame += 1
                        
                        if invalid_in_frame > 0:
                            frames_with_invalid += 1
                            total_invalid_count += invalid_in_frame
                        
                        # Extract angular velocity (last column)
                        try:
                            ang_vel = float(data[360])
                            if not (math.isinf(ang_vel) or math.isnan(ang_vel)):
                                angular_velocities.append(ang_vel)
                        except (ValueError, TypeError):
                            pass  # Skip non-numeric angular velocities
                            
                except Exception as e:
                    print(f"Warning: Could not process line {line_num}: {e}")
        
        return {
            'angular_velocities': angular_velocities,
            'total_invalid_count': total_invalid_count,
            'frames_with_invalid': frames_with_invalid,
            'total_frames': total_frames,
            'file_path': data_file,
            'has_headers': has_headers
        }
    
    def display_data_statistics(self, stats, data_file):
        """Display data statistics in a popup window (moved from StartupConfigWindow)"""
        
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
            
            stats_text = f"""Total Frames: {current_stats['total_frames']}
Frames with Invalid Data: {current_stats['frames_with_invalid']} ({current_stats['frames_with_invalid']/max(current_stats['total_frames'], 1)*100:.1f}%)
Total Invalid Data Points: {current_stats['total_invalid_count']}
Valid Angular Velocity Values: {len(current_stats['angular_velocities'])}"""
            
            # Show regular stats
            ttk.Label(self.stats_display_frame, text=stats_text, font=('Courier', 10)).pack(anchor='w')
            
            if 'augmented_count' in current_stats and current_stats['augmented_count'] > 0:
                # Show augmented count in blue
                augmented_label = ttk.Label(self.stats_display_frame, 
                                        text=f"Augmented Data Frames: {current_stats['augmented_count']}", 
                                        font=('Courier', 10), foreground='blue')
                augmented_label.pack(anchor='w')
            
            if 'imputed_count' in current_stats and current_stats['imputed_count'] > 0:
                # Show imputed count in green
                imputed_label = ttk.Label(self.stats_display_frame, 
                                        text=f"Imputed Data Points: {current_stats['imputed_count']}", 
                                        font=('Courier', 10), foreground='green')
                imputed_label.pack(anchor='w')
        
        # Initial stats display
        update_stats_display(stats)
        
        # Button frame for Impute and Save buttons
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
                    
                    # Read the original file to preserve headers
                    with open(data_file, 'r') as f:
                        all_lines = f.readlines()
                    
                    header_line = None
                    data_lines = []
                    
                    if has_headers and all_lines:
                        header_line = all_lines[0].strip().split(',')
                        data_lines = [line.strip() for line in all_lines[1:] if line.strip()]
                    else:
                        data_lines = [line.strip() for line in all_lines if line.strip()]
                    
                    # Convert string data to list format for consistency
                    data_lines_from_source = []
                    for line in data_lines:
                        if line:
                            data_lines_from_source.append(line.split(','))
                
                augmented_count = 0
                processed_lines = []
                
                # Add header if it exists
                if header_line:
                    processed_lines.append(header_line)
                
                # If append mode, add original data first
                if append_mode:
                    # Add original/modified data lines first
                    for data in data_lines_from_source:
                        processed_lines.append(data)
                
                # Process each data line for augmentation
                for data in data_lines_from_source:
                    if len(data) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                        # Reverse the lidar data points (index 0 becomes 359, etc.)
                        reversed_lidar = []
                        for i in range(LIDAR_RESOLUTION):
                            reversed_lidar.append(data[359 - i])  # Reverse the order
                        
                        # Negate the angular velocity
                        try:
                            angular_velocity = float(data[360])
                            negated_angular = -angular_velocity
                        except (ValueError, TypeError):
                            negated_angular = 0.0  # Default if can't parse
                        
                        # Create augmented line
                        augmented_line = reversed_lidar + [str(negated_angular)]
                        processed_lines.append(augmented_line)
                        augmented_count += 1
                    else:
                        # In replace mode, keep line as is if format doesn't match
                        if not append_mode:
                            processed_lines.append(data)
                
                # Store augmented data for saving
                self.imputed_data = processed_lines
                self.stats_imputed = True
                self.imputed_has_headers = has_headers
                
                # Re-analyze the augmented data
                new_stats = self.analyze_imputed_data_from_list(processed_lines, has_headers)
                new_stats['augmented_count'] = augmented_count
                if append_mode:
                    new_stats['original_count'] = len(data_lines_from_source)
                    new_stats['append_mode'] = True
                else:
                    new_stats['append_mode'] = False
                
                # Update statistics display
                def update_stats_display_with_augmented(current_stats):
                    # Clear existing content
                    for widget in self.stats_display_frame.winfo_children():
                        widget.destroy()
                    
                    stats_text = f"""Total Frames: {current_stats['total_frames']}
Frames with Invalid Data: {current_stats['frames_with_invalid']} ({current_stats['frames_with_invalid']/max(current_stats['total_frames'], 1)*100:.1f}%)
Total Invalid Data Points: {current_stats['total_invalid_count']}
Valid Angular Velocity Values: {len(current_stats['angular_velocities'])}"""
                    
                    # Show regular stats
                    ttk.Label(self.stats_display_frame, text=stats_text, font=('Courier', 10)).pack(anchor='w')
                    
                    # Show mode-specific information
                    if 'append_mode' in current_stats:
                        if current_stats['append_mode']:
                            mode_text = f"Mode: Append (Original: {current_stats.get('original_count', 0)} + Augmented: {current_stats.get('augmented_count', 0)})"
                        else:
                            mode_text = f"Mode: Replace (Augmented only: {current_stats.get('augmented_count', 0)} frames)"
                        
                        mode_label = ttk.Label(self.stats_display_frame, 
                                            text=mode_text, 
                                            font=('Courier', 10), foreground='purple')
                        mode_label.pack(anchor='w')
                    
                    if 'augmented_count' in current_stats and current_stats['augmented_count'] > 0:
                        # Show augmented count in blue
                        augmented_label = ttk.Label(self.stats_display_frame, 
                                                text=f"Augmented Data Frames: {current_stats['augmented_count']}", 
                                                font=('Courier', 10), foreground='blue')
                        augmented_label.pack(anchor='w')
                    
                    if 'imputed_count' in current_stats and current_stats['imputed_count'] > 0:
                        # Show imputed count in green
                        imputed_label = ttk.Label(self.stats_display_frame, 
                                                text=f"Imputed Data Points: {current_stats['imputed_count']}", 
                                                font=('Courier', 10), foreground='green')
                        imputed_label.pack(anchor='w')
                
                update_stats_display_with_augmented(new_stats)
                
                # Enable save button
                save_button.config(state='normal')
                
                # Update histogram if it exists
                if hasattr(self, 'stats_canvas') and new_stats['angular_velocities']:
                    self.update_histogram(new_stats)
                
                # Determine the source of data for success message
                data_source = "previously modified data" if (hasattr(self, 'imputed_data') and self.stats_imputed and self.imputed_data) else "original file data"
                original_frame_count = len(data_lines_from_source)
                
                # Show success message based on mode
                if append_mode:
                    success_msg = f"Successfully augmented and appended {augmented_count} data frames!\n" + \
                                f"Total frames now: {original_frame_count + augmented_count}\n" + \
                                f"Worked on: {data_source}\n" + \
                                f"Lidar points reversed and angular velocities negated for augmented data.\n" + \
                                (f"File has headers: {'Yes' if has_headers else 'No'}")
                else:
                    success_msg = f"Successfully replaced data with {augmented_count} augmented frames!\n" + \
                                f"Data replaced with augmented versions.\n" + \
                                f"Worked on: {data_source}\n" + \
                                f"Lidar points reversed and angular velocities negated.\n" + \
                                (f"File has headers: {'Yes' if has_headers else 'No'}")
                
                messagebox.showinfo("Success", success_msg)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to augment data: {str(e)}")
                print(f"Error augmenting data: {e}")
                import traceback
                traceback.print_exc()
        
        augment_button = ttk.Button(button_frame, text="Augment Data", 
                                   command=augment_data, width=20)
        augment_button.pack(side='left', padx=(0, 10))
        
        # Save button (initially disabled) - updated text and functionality
        def save_modified_data():
            """Save the latest modified data (imputed or augmented)"""
            try:
                if not hasattr(self, 'imputed_data') or not self.stats_imputed:
                    messagebox.showerror("Error", "No modified data to save!")
                    return
                
                # Browse for save location
                save_file = filedialog.asksaveasfilename(
                    title="Save Modified Data",
                    defaultextension=".txt",
                    filetypes=[
                        ("Text files", "*.txt"),
                        ("CSV files", "*.csv"),
                        ("All files", "*.*")
                    ],
                    initialdir=os.path.dirname(data_file),
                    initialfile=os.path.basename(data_file).replace('.txt', '_modified.txt')
                )
                
                if not save_file:
                    return  # User cancelled
                
                # Get the preserve header setting from the checkbox
                preserve_headers = self.preserve_header_var.get()
                
                # Determine if original data had headers and if we should preserve them
                original_had_headers = hasattr(self, 'imputed_has_headers') and self.imputed_has_headers
                
                # Save the data with proper formatting
                with open(save_file, 'w') as f:
                    start_index = 0
                    
                    # Handle header preservation logic
                    if original_had_headers and preserve_headers:
                        # Skip the first line (header) when writing if we want to preserve it
                        # The header is already included in self.imputed_data
                        start_index = 0  # Include header (first line)
                    elif original_had_headers and not preserve_headers:
                        # Skip the header line when saving
                        start_index = 1  # Skip header (first line)
                    else:
                        # No original headers, save all data
                        start_index = 0
                    
                    # Write the data starting from the appropriate index
                    for i, line_data in enumerate(self.imputed_data):
                        if i >= start_index:
                            # Join the data and write to file
                            line_str = ','.join(line_data)
                            f.write(line_str + '\n')
                
                # Prepare success message
                header_status = "Yes" if (original_had_headers and preserve_headers) else "No"
                messagebox.showinfo("Success", 
                                  f"Modified data saved to:\n{os.path.basename(save_file)}\n" +
                                  f"Headers preserved: {header_status}")
                
                # Disable save button after successful save
                save_button.config(state='disabled')
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save modified data: {str(e)}")
                print(f"Error saving modified data: {e}")
                import traceback
                traceback.print_exc()
        
        save_button = ttk.Button(button_frame, text="Save", 
                                command=save_modified_data, width=20, state='disabled')
        save_button.pack(side='left', padx=(0, 10))
        
        # Preserve header checkbox
        preserve_header_frame = ttk.Frame(main_frame)
        preserve_header_frame.pack(fill='x', pady=(5, 10))
        
        self.preserve_header_var = tk.BooleanVar()
        # Default to True if the original file has headers, False otherwise
        has_headers = self.has_header(data_file)
        self.preserve_header_var.set(has_headers)
        
        preserve_header_checkbox = ttk.Checkbutton(
            preserve_header_frame, 
            text="Preserve header when saving", 
            variable=self.preserve_header_var
        )
        preserve_header_checkbox.pack(anchor='w')
        
        # Histogram
        if stats['angular_velocities']:
            hist_frame = ttk.LabelFrame(main_frame, text="Angular Velocity Distribution", padding=10)
            hist_frame.pack(fill='both', expand=True)
            
            # Store references for updating
            self.stats_hist_frame = hist_frame
            
            # Create initial histogram
            self.create_histogram(stats)
        else:
            ttk.Label(main_frame, text="No valid angular velocity data found!", 
                     foreground='red', font=('Arial', 12)).pack(pady=20)
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", 
                                 command=popup.destroy, width=15)
        close_button.pack(pady=10)
    
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
    
    def analyze_imputed_data(self, imputed_data):
        """Analyze imputed data and return statistics"""
        try:
            angular_velocities = []
            total_invalid_count = 0
            frames_with_invalid = 0
            total_frames = 0
            
            for line in imputed_data:
                line = line.strip()
                if not line:
                    continue
                
                data = line.split(',')
                if len(data) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                    total_frames += 1
                    
                    # Check for invalid data in lidar readings (should be minimal after imputation)
                    invalid_in_frame = 0
                    for i in range(LIDAR_RESOLUTION):
                        try:
                            value = float(data[i])
                            if math.isinf(value) or math.isnan(value):
                                invalid_in_frame += 1
                        except (ValueError, TypeError):
                            invalid_in_frame += 1
                    
                    if invalid_in_frame > 0:
                        frames_with_invalid += 1
                        total_invalid_count += invalid_in_frame
                    
                    # Extract angular velocity (last column)
                    try:
                        ang_vel = float(data[360])
                        if not (math.isinf(ang_vel) or math.isnan(ang_vel)):
                            angular_velocities.append(ang_vel)
                    except (ValueError, TypeError):
                        pass  # Skip non-numeric angular velocities
            
            return {
                'angular_velocities': angular_velocities,
                'total_invalid_count': total_invalid_count,
                'frames_with_invalid': frames_with_invalid,
                'total_frames': total_frames,
                'file_path': self.stats_data_file
            }
            
        except Exception as e:
            print(f"Error analyzing imputed data: {e}")
            return self.original_stats
    
    def analyze_imputed_data_from_list(self, imputed_data_list, has_headers=False):
        """Analyze imputed data from list format and return statistics"""
        try:
            angular_velocities = []
            total_invalid_count = 0
            frames_with_invalid = 0
            total_frames = 0
            
            start_index = 1 if has_headers else 0  # Skip header if present
            
            for i, data_frame in enumerate(imputed_data_list):
                # Skip header row
                if has_headers and i == 0:
                    continue
                    
                if len(data_frame) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                    total_frames += 1
                    
                    # Check for invalid data in lidar readings (should be minimal after imputation)
                    invalid_in_frame = 0
                    for j in range(LIDAR_RESOLUTION):
                        try:
                            value = float(data_frame[j])
                            if math.isinf(value) or math.isnan(value):
                                invalid_in_frame += 1
                        except (ValueError, TypeError):
                            invalid_in_frame += 1
                    
                    if invalid_in_frame > 0:
                        frames_with_invalid += 1
                        total_invalid_count += invalid_in_frame
                    
                    # Extract angular velocity (last column)
                    try:
                        ang_vel = float(data_frame[360])
                        if not (math.isinf(ang_vel) or math.isnan(ang_vel)):
                            angular_velocities.append(ang_vel)
                    except (ValueError, TypeError):
                        pass  # Skip non-numeric angular velocities
            
            return {
                'angular_velocities': angular_velocities,
                'total_invalid_count': total_invalid_count,
                'frames_with_invalid': frames_with_invalid,
                'total_frames': total_frames,
                'file_path': self.stats_data_file,
                'has_headers': has_headers
            }
            
        except Exception as e:
            print(f"Error analyzing imputed data from list: {e}")
            return self.original_stats
    
    def show_scale_factor_dialog(self):
        """Show scale factor configuration dialog"""
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Scale Factor Configuration")
        popup.geometry("400x250")  # Increased height from 200 to 250
        popup.resizable(False, False)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (250 // 2)  # Updated for new height
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
        scale_entry.focus_set()  # Focus on the entry field
        
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
                
                # Update global scale factor
                global SCALE_FACTOR
                SCALE_FACTOR = new_scale
                
                # Update status to show change
                self.status_var.set(f"Scale factor updated to {SCALE_FACTOR:.4f} | Mode: {'INSPECT' if self.inspect_mode else 'CONTINUOUS'} | Data: {'AUGMENTED' if self.augmented_mode else 'REAL'}")
                
                popup.destroy()
                print(f"Scale factor updated to: {SCALE_FACTOR:.4f}")
                
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
    
    def quit_visualizer(self):
        """Quit the visualizer"""
        print("Quitting visualizer...")
        self.running = False
        
        # Clean up data manager
        try:
            if hasattr(self, 'data_manager') and self.data_manager:
                if hasattr(self.data_manager, 'infile') and self.data_manager.infile:
                    self.data_manager.infile.close()
                if hasattr(self.data_manager, 'outfile') and self.data_manager.outfile:
                    self.data_manager.outfile.close()
        except Exception as e:
            print(f"Error closing data manager files: {e}")
        
        self.on_closing()
    
    def on_closing(self):
        """Handle window closing"""
        print("Closing visualizer...")
        self.running = False
        
        # Clean up pygame
        try:
            pygame.quit()
        except:
            pass
        
        # Close all popup windows first
        for child in list(self.root.winfo_children()):
            if isinstance(child, tk.Toplevel):
                try:
                    child.destroy()
                except:
                    pass
        
        try:
            # Exit the mainloop and destroy the window
            self.root.quit()     # Exit mainloop - important for program to terminate
            self.root.destroy()  # Destroy the window
        except:
            pass
        
        # Force exit if tkinter doesn't properly close
        print("Visualizer closed.")
        try:
            # Give a brief moment for cleanup
            import time
            time.sleep(0.1)
            sys.exit(0)
        except:
            pass
    
    def on_angular_velocity_input(self, event):
        """Handle angular velocity input - matches original pygame InputBox behavior"""
        try:
            new_turn = self.turn_var.get()
            print(f"Angular velocity input received: {new_turn}")
            
            # Update the current data frame with new angular velocity
            if self.distances and len(self.distances) == LIDAR_RESOLUTION + 1:
                self.distances[360] = new_turn
                
                # Update the data manager's current dataframe and ensure it's marked for saving
                if hasattr(self.data_manager, 'lines') and self.data_manager.read_pos >= 0:
                    # Get current line data
                    current_line_data = self.distances[:]  # Make a copy
                    
                    # Update the data manager's internal data
                    if hasattr(self.data_manager, '_lidar_dataframe'):
                        self.data_manager._lidar_dataframe = current_line_data
                    
                    # Mark this frame as modified for saving
                    line_str = ','.join(str(val) for val in current_line_data)
                    if self.data_manager.read_pos < len(self.data_manager.lines):
                        self.data_manager.lines[self.data_manager.read_pos] = line_str
                    
                    print(f"Data manager updated with new turn value: {new_turn} at frame {self.data_manager.read_pos + 1}")
                
                # Clear the input field after successful update (like original pygame behavior)
                self.turn_var.set('')
                print(f"Angular velocity updated to: {new_turn}")
                
                # Update button states in case we're at boundaries
                if self.inspect_mode:
                    self.update_button_states()
            else:
                print("No valid data frame to update")
                
        except Exception as e:
            print(f"Error updating angular velocity: {e}")
    
    def on_linear_velocity_input(self, event):
        """Handle linear velocity input - placeholder for future implementation"""
        linear_value = self.linear_var.get()
        print(f"Linear velocity input received (not yet implemented): {linear_value}")
        # Clear the input field
        self.linear_var.set('')
    
    def update_inputs(self):
        """Update tkinter input fields with current data"""
        if self.distances and len(self.distances) == LIDAR_RESOLUTION + 1:
            # Update angular velocity field with current value (if not actively being edited)
            if not self.turn_entry.focus_get() == self.turn_entry:  # Only update if not focused
                try:
                    turn_value = float(self.distances[360])
                    display_turn = -turn_value if self.augmented_mode else turn_value
                    self.turn_var.set(f"{display_turn:.2f}")
                except (ValueError, TypeError):
                    self.turn_var.set(str(self.distances[360]))
            
            # Update frame information display
            mode_text = "AUGMENTED" if self.augmented_mode else "REAL"
            current_frame = self.data_manager.pointer + 1  # Add 1 for 1-based indexing (pointer is 0-based)
            total_frames = len(self.data_manager.lines)
            self.frame_info_var.set(f"Frame: {current_frame}/{total_frames} [{mode_text}]")
            
            # Update linear velocity field (placeholder - keep empty for now)
            if not self.linear_entry.focus_get() == self.linear_entry:
                self.linear_var.set("")  # Keep empty as it's not implemented
    
    def render_frame(self):
        """Render the current lidar frame"""
        if not hasattr(self, 'screen'):
            return
            
        try:
            # Fill background
            self.screen.fill((250, 250, 250))
            
            # Calculate center and scale based on current canvas size
            center_x = self.current_canvas_size / 2
            center_y = self.current_canvas_size / 2
            
            # Dynamic scale factor based on canvas size
            dynamic_scale = SCALE_FACTOR * (self.current_canvas_size / 800)  # 800 is the original SCREEN_WIDTH
            
            # Render lidar points
            for x in range(LIDAR_RESOLUTION):
                try:
                    distance_value = float(self.distances[x])
                    if math.isinf(distance_value) or math.isnan(distance_value):
                        continue
                except (ValueError, TypeError):
                    continue
                    
                a = distance_value * dynamic_scale
                
                # Choose coordinates based on augmented mode
                if self.augmented_mode:
                    x_coord = math.cos(x / 180 * math.pi) * a + center_x
                    y_coord = math.sin(x / 180 * math.pi) * a + center_y
                else:
                    x_coord = math.cos(x / 180 * math.pi) * a + center_x
                    y_coord = -math.sin(x / 180 * math.pi) * a + center_y
                
                if x in DECISIVE_FRAME_POSITIONS:
                    # Draw line and important point
                    pygame.draw.line(self.screen, (255, 0, 255), (center_x, center_y),
                                   (x_coord, y_coord), 2)
                    pygame.draw.circle(self.screen, (255, 0, 0), (x_coord, y_coord), 3)
                else:
                    pygame.draw.circle(self.screen, (0, 0, 0), (x_coord, y_coord), 2)
            
            # Draw car (scaled)
            car_radius = max(6, int(12 * (self.current_canvas_size / 800)))
            car_line_length = max(20, int(40 * (self.current_canvas_size / 800)))
            
            pygame.draw.circle(self.screen, (252, 132, 3), (center_x, center_y), car_radius)
            pygame.draw.line(self.screen, (0, 0, 255), (center_x, center_y),
                            (center_x + car_line_length, center_y), 3)
            
            # Draw turn direction (scaled)
            try:
                turn_value = float(self.distances[360])
                if self.augmented_mode:
                    turn_value = -turn_value
                x = math.cos(turn_value * math.pi / 4) * car_line_length
                y = math.sin(turn_value * math.pi / 4) * car_line_length
                # Flip Y coordinate to match lidar coordinate system (pygame Y increases downward)
                pygame.draw.line(self.screen, (0, 255, 0), (center_x, center_y),
                               (center_x + x, center_y - y), 3)
            except (ValueError, TypeError):
                pass
            
            pygame.display.flip()
        except Exception as e:
            print(f"Error rendering frame: {e}")
    
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
                # Get current data
                if self.data_manager.read_pos < self.data_manager.pointer:
                    try:
                        self.distances = self.data_manager.dataframe
                        
                        # Validate the distances data
                        if self.distances and len(self.distances) == LIDAR_RESOLUTION + 1:
                            # Check for invalid tkinter references in distances
                            valid_distances = True
                            for i, val in enumerate(self.distances):
                                if isinstance(val, str) and (val.startswith('#!') or val.startswith('__tk_')):
                                    print(f"Warning: Invalid tkinter reference at position {i}: {val}")
                                    valid_distances = False
                                    break
                            
                            if valid_distances:
                                self.render_frame()
                                self.update_inputs()
                            else:
                                # Skip this frame
                                pass
                        
                    except Exception as data_error:
                        print(f"Error processing data frame: {data_error}")
                
                # Advance to next frame if not paused
                if not self.paused:
                    try:
                        self.data_manager.write_line()
                        self.data_manager.next()
                    except Exception as advance_error:
                        print(f"Error advancing frame: {advance_error}")
            else:
                # End of data
                print("End of data reached")
                self.running = False
                return
        
        except Exception as e:
            print(f"Error in animation: {e}")
            import traceback
            traceback.print_exc()
        
        # Schedule next frame
        if self.running:
            self.root.after(100, self.animate)  # ~10 FPS
    
    def run(self):
        """Start the visualizer"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error in visualizer: {e}")
        finally:
            self.running = False
            try:
                pygame.quit()
            except:
                pass


class StartupConfigWindow:
    def __init__(self, preset_data_file=None):
        self.root = tk.Tk()
        self.root.title("Lidar Visualizer Configuration")
        
        # Handle preset data file from command line argument
        self.preset_data_file = preset_data_file
        if preset_data_file:
            self.data_file = tk.StringVar(value=preset_data_file)
            # Make window taller when showing preset data info
            window_height = 500
        else:
            self.data_file = tk.StringVar(value='data/run1/out1.txt')
            window_height = 450
        
        self.root.geometry(f"520x{window_height}")
        self.root.resizable(False, False)
        
        # Center the window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (520 // 2)
        y = (self.root.winfo_screenheight() // 2) - (window_height // 2)
        self.root.geometry(f"520x{window_height}+{x}+{y}")
        
        # Make window stay on top initially
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        
        # Configuration variables
        self.inspection_mode = tk.BooleanVar(value=False)
        self.augmented_mode = tk.BooleanVar(value=False)
        self.concatenate_data = tk.BooleanVar(value=False)
        self.selected_file_type = tk.StringVar(value='local')  # 'local', 'browse', or 'preset'
        self.browsed_file_path = tk.StringVar(value="")
        self.data_loaded = False  # Track if data has been loaded
        
        self.config_selected = False
        
        self.setup_ui()
        
        # Handle window close button (X)
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Force window to appear
        self.root.focus_force()
        print("Configuration window should now be visible...")
        
    def setup_ui(self):
        # Title
        title_text = "Lidar Visualizer Configuration"
        if self.preset_data_file:
            # Truncate long file paths for better display
            display_file = self.preset_data_file
            if len(display_file) > 40:
                display_file = "..." + display_file[-37:]
            title_text += f"\n(Data file: {display_file})"
        
        title_label = ttk.Label(self.root, text=title_text, 
                               font=('Arial', 12, 'bold'), justify='center')
        title_label.pack(pady=(10, 5))
        
        # Data file selection
        file_frame = ttk.LabelFrame(self.root, text="Data Source", padding=8)
        file_frame.pack(fill='x', padx=15, pady=3)
        
        if self.preset_data_file:
            # Show grayed out options with preset file selected
            info_label = ttk.Label(file_frame, 
                                  text="Data source preset from command line:", 
                                  font=('Arial', 9), foreground='blue')
            info_label.pack(anchor='w', pady=(0, 3))
            
            # Show the actual file path in a separate label with word wrap
            file_path_label = ttk.Label(file_frame, 
                                       text=self.preset_data_file, 
                                       font=('Arial', 8), foreground='darkblue',
                                       wraplength=480)
            file_path_label.pack(anchor='w', pady=(0, 5))
            
            # Create disabled radio buttons
            radio1 = ttk.Radiobutton(file_frame, text="Local data (data/run1/out1.txt)", 
                                   variable=self.selected_file_type, value='local',
                                   state='disabled')
            radio1.pack(anchor='w', pady=1)
            
            radio2 = ttk.Radiobutton(file_frame, text="Custom file (command line argument)", 
                                   variable=self.selected_file_type, value='preset',
                                   state='disabled')
            radio2.pack(anchor='w', pady=1)
            
            # Select the preset option
            self.selected_file_type.set('preset')
        else:
            # Normal selectable options
            radio1 = ttk.Radiobutton(file_frame, text="Local data (data/run1/out1.txt)", 
                                   variable=self.selected_file_type, value='local',
                                   command=self.on_file_type_change)
            radio1.pack(anchor='w', pady=1)
            
            # Browse option with button
            browse_frame = ttk.Frame(file_frame)
            browse_frame.pack(fill='x', pady=1)
            
            radio2 = ttk.Radiobutton(browse_frame, text="Browse for file:", 
                                   variable=self.selected_file_type, value='browse',
                                   command=self.on_file_type_change)
            radio2.pack(side='left')
            
            browse_button = ttk.Button(browse_frame, text="Browse...", 
                                     command=self.browse_file, width=12)
            browse_button.pack(side='right', padx=(10, 0))
            
            # Show selected file path if any
            self.file_path_label = ttk.Label(file_frame, text="No file selected", 
                                           font=('Arial', 8), foreground='gray',
                                           wraplength=480)
            self.file_path_label.pack(anchor='w', pady=(2, 0))
        
        # Visualization mode
        viz_frame = ttk.LabelFrame(self.root, text="Visualization Mode", padding=8)
        viz_frame.pack(fill='x', padx=15, pady=3)
        
        ttk.Checkbutton(viz_frame, text="Inspection Mode (frame by frame)", 
                       variable=self.inspection_mode).pack(anchor='w', pady=1)
        ttk.Checkbutton(viz_frame, text="Show Augmented Data", 
                       variable=self.augmented_mode).pack(anchor='w', pady=1)
        
        # Data processing
        data_frame = ttk.LabelFrame(self.root, text="Data Processing", padding=8)
        data_frame.pack(fill='x', padx=15, pady=3)
        
        ttk.Checkbutton(data_frame, text="Concatenate augmented data to input file", 
                       variable=self.concatenate_data).pack(anchor='w', pady=1)
        
        # Info label
        info_label = ttk.Label(self.root, text="Note: Concatenation will double your dataset size", 
                              font=('Arial', 8), foreground='gray')
        info_label.pack(pady=3)
        
        # Load Data button
        load_frame = ttk.Frame(self.root)
        load_frame.pack(pady=10)
        
        self.load_button = ttk.Button(load_frame, text="📊 Load Data & Show Statistics", 
                                     command=self.load_and_analyze_data, width=30)
        self.load_button.pack()
        
        # Buttons - ensure they're always visible
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=15, side='bottom')
        
        # Make buttons more prominent
        start_button = ttk.Button(button_frame, text="✓ START VISUALIZER", 
                                 command=self.start_visualizer, width=20)
        start_button.pack(side='left', padx=10)
        
        cancel_button = ttk.Button(button_frame, text="✗ Cancel", 
                                  command=self.cancel, width=15)
        cancel_button.pack(side='left', padx=10)
        
        # Add instruction text
        instruction_label = ttk.Label(self.root, 
                                     text="Configure your options above, then click START VISUALIZER", 
                                     font=('Arial', 9, 'bold'), foreground='blue',
                                     wraplength=480)
        instruction_label.pack(pady=(5, 10), side='bottom')
    
    def browse_file(self):
        """Open file dialog to browse for data files"""
        file_types = [
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=file_types,
            initialdir="/home/andy"  # Start in user's home directory
        )
        
        if filename:
            self.browsed_file_path.set(filename)
            self.selected_file_type.set('browse')
            
            # Update the file path label to show selected file
            display_path = filename
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            
            self.file_path_label.config(text=f"Selected: {display_path}", 
                                      foreground='darkgreen')
            
            # Re-enable the Load Data button when a new file is selected
            self.reset_load_button()
        else:
            # User cancelled, reset if no file was previously selected
            if not self.browsed_file_path.get():
                self.file_path_label.config(text="No file selected", 
                                          foreground='gray')
    
    def get_selected_data_file(self):
        """Get the currently selected data file path"""
        file_type = self.selected_file_type.get()
        
        if file_type == 'local':
            return 'data/run1/out1.txt'
        elif file_type == 'browse':
            return self.browsed_file_path.get() if self.browsed_file_path.get() else 'data/run1/out1.txt'
        elif file_type == 'preset':
            return self.preset_data_file
        else:
            return 'data/run1/out1.txt'  # fallback
    
    def reset_load_button(self):
        """Reset the Load Data button to its initial state"""
        self.data_loaded = False
        if hasattr(self, 'load_button'):
            current_file = self.get_selected_data_file()
            if current_file and current_file != 'data/run1/out1.txt':
                # Show file name in button for non-default files
                import os
                filename = os.path.basename(current_file)
                if len(filename) > 20:
                    filename = filename[:17] + "..."
                self.load_button.config(state='normal', text=f"📊 Load {filename}")
            else:
                self.load_button.config(state='normal', text="📊 Load Data & Show Statistics")
    
    def on_file_type_change(self):
        """Called when file type selection changes"""
        self.reset_load_button()
    
    def load_and_analyze_data(self):
        """Load data file and show statistics popup"""
        # Get the selected data file
        data_file = self.get_selected_data_file()
        
        # Validate file selection
        if self.selected_file_type.get() == 'browse' and not self.browsed_file_path.get():
            messagebox.showerror("Error", "Please select a file first!")
            return
        
        # Gray out the load button
        self.load_button.config(state='disabled', text="📊 Loading Data...")
        self.root.update()
        
        try:
            # Analyze the data
            stats = self.analyze_data_file(data_file)
            
            # Show statistics popup
            self.show_data_statistics(stats, data_file)
            
            self.data_loaded = True
            # Show success message with file info
            import os
            filename = os.path.basename(data_file)
            if len(filename) > 15:
                filename = filename[:12] + "..."
            self.load_button.config(text=f"📊 {filename} Loaded ✓")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            # Reset button to initial state on error
            self.reset_load_button()
    
    def analyze_data_file(self, data_file):
        """Analyze data file and return statistics"""
        import os
        
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Data file not found: {data_file}")
        
        angular_velocities = []
        total_invalid_count = 0
        frames_with_invalid = 0
        total_frames = 0
        
        with open(data_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = line.split(',')
                    if len(data) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                        total_frames += 1
                        
                        # Check for invalid data in lidar readings
                        invalid_in_frame = 0
                        for i in range(LIDAR_RESOLUTION):
                            try:
                                value = float(data[i])
                                if math.isinf(value) or math.isnan(value):
                                    invalid_in_frame += 1
                            except (ValueError, TypeError):
                                invalid_in_frame += 1
                        
                        if invalid_in_frame > 0:
                            frames_with_invalid += 1
                            total_invalid_count += invalid_in_frame
                        
                        # Extract angular velocity (last column)
                        try:
                            ang_vel = float(data[360])
                            if not (math.isinf(ang_vel) or math.isnan(ang_vel)):
                                angular_velocities.append(ang_vel)
                        except (ValueError, TypeError):
                            pass  # Skip non-numeric angular velocities
                            
                except Exception as e:
                    print(f"Warning: Could not process line {line_num}: {e}")
        
        return {
            'angular_velocities': angular_velocities,
            'total_invalid_count': total_invalid_count,
            'frames_with_invalid': frames_with_invalid,
            'total_frames': total_frames,
            'file_path': data_file
        }
    
    def show_data_statistics(self, stats, data_file):
        """Show data statistics in a popup window"""
        import os
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"Data Statistics - {os.path.basename(data_file)}")
        popup.geometry("800x600")
        popup.resizable(True, True)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (800 // 2)
        y = (popup.winfo_screenheight() // 2) - (600 // 2)
        popup.geometry(f"800x600+{x}+{y}")
        
        # Make popup modal
        popup.transient(self.root)
        popup.grab_set()
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Data Analysis Results", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Statistics text
        stats_frame = ttk.LabelFrame(main_frame, text="Data Quality", padding=10)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats_text = f"""Total Frames: {stats['total_frames']}
Frames with Invalid Data: {stats['frames_with_invalid']} ({stats['frames_with_invalid']/max(stats['total_frames'], 1)*100:.1f}%)
Total Invalid Data Points: {stats['total_invalid_count']}
Valid Angular Velocity Values: {len(stats['angular_velocities'])}"""
        
        ttk.Label(stats_frame, text=stats_text, font=('Courier', 10)).pack(anchor='w')
        
        # Histogram
        if stats['angular_velocities']:
            hist_frame = ttk.LabelFrame(main_frame, text="Angular Velocity Distribution", padding=10)
            hist_frame.pack(fill='both', expand=True)
            
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
            canvas = FigureCanvasTkAgg(fig, hist_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
        else:
            ttk.Label(main_frame, text="No valid angular velocity data found!", 
                     foreground='red', font=('Arial', 12)).pack(pady=20)
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", 
                                 command=popup.destroy, width=15)
        close_button.pack(pady=10)
    
    def start_visualizer(self):
        # Validate file selection if browse option is selected
        if self.selected_file_type.get() == 'browse' and not self.browsed_file_path.get():
            messagebox.showerror("Error", "Please select a file or choose a different data source option.")
            return
        
        selected_file = self.get_selected_data_file()
        
        print("=" * 50)
        print("START VISUALIZER BUTTON CLICKED!")
        print(f"Data file: {selected_file}")
        print(f"File type: {self.selected_file_type.get()}")
        print(f"Inspection mode: {self.inspection_mode.get()}")
        print(f"Augmented mode: {self.augmented_mode.get()}")
        print(f"Concatenate data: {self.concatenate_data.get()}")
        print("=" * 50)
        self.config_selected = True
        self.root.quit()  # Exit mainloop
        # Don't destroy yet - let get_config handle it
    
    def cancel(self):
        print("CANCEL BUTTON CLICKED!")
        self.config_selected = False
        self.root.quit()  # Exit mainloop
        # Don't destroy yet - let get_config handle it
    
    def get_config(self):
        try:
            print("Starting tkinter mainloop...")
            self.root.mainloop()
            print(f"Mainloop ended. Config selected: {self.config_selected}")
            
            # Get config before destroying window
            result = None
            if self.config_selected:
                result = {
                    'data_file': self.get_selected_data_file(),
                    'inspection_mode': self.inspection_mode.get(),
                    'augmented_mode': self.augmented_mode.get(),
                    'concatenate_data': self.concatenate_data.get()
                }
                print(f"Configuration collected: {result}")
            
            # Now destroy the window
            try:
                self.root.destroy()
            except:
                pass  # Window might already be destroyed
                
            return result
        except Exception as e:
            print(f"Error in get_config: {e}")
            try:
                self.root.destroy()
            except:
                pass
            return None


def concatenate_augmented_data(input_file):
    """
    Read the input file and append augmented (mirrored) data to it
    """
    print(f"Reading data from {input_file}...")
    
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        augmented_lines = []
        processed_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Parse the line
                data = line.split(',')
                if len(data) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                    # Create augmented version
                    augmented_data = data.copy()
                    
                    # Flip the turn value (angular velocity)
                    try:
                        turn_value = float(data[360])
                        augmented_data[360] = str(-turn_value)
                    except (ValueError, TypeError):
                        # Keep non-numeric turn values as is
                        pass
                    
                    # Note: Lidar data mirroring is handled during visualization
                    # The raw distance values remain the same, only interpretation changes
                    augmented_lines.append(','.join(augmented_data))
                    processed_count += 1
                    
            except Exception as e:
                print(f"Warning: Could not process line: {line[:50]}... Error: {e}")
        
        # Append augmented data to original file
        print(f"Appending {processed_count} augmented data points to {input_file}...")
        with open(input_file, 'a') as f:
            for aug_line in augmented_lines:
                f.write('\n' + aug_line)
        
        print(f"Successfully concatenated {processed_count} augmented data points!")
        return True
        
    except Exception as e:
        print(f"Error processing file {input_file}: {e}")
        messagebox.showerror("Error", f"Failed to process data file: {e}")
        return False


def calculate_scale_factor(data_manager, sample_size=10):
    """
    Analyze sample data to determine optimal scale factor
    """
    global SCALE_FACTOR
    
    # Sample the first few frames to understand data range
    valid_distances = []
    sample_count = 0
    original_pointer = data_manager.pointer
    
    print("Analyzing data to determine optimal scale factor...")
    
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
    
    # Reset data manager to beginning
    data_manager._pointer = 0
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
        SCALE_FACTOR = TARGET_RADIUS / percentile_90
        
        print(f"Data analysis complete:")
        print(f"  Distance range: {min_dist:.1f} - {max_dist:.1f} mm")
        print(f"  Average distance: {avg_dist:.1f} mm")
        print(f"  90th percentile: {percentile_90:.1f} mm")
        print(f"  Calculated scale factor: {SCALE_FACTOR:.3f}")
    else:
        print("No valid distance data found, using default scale factor")
    
    return SCALE_FACTOR


def run(data_file=None, highlight_frames=True, show_augmented=False, inspection_mode=False):
    """Legacy run function - now uses the new VisualizerWindow"""
    # Create config from parameters
    config = {
        'data_file': data_file or 'data/run1/out1.txt',
        'inspection_mode': inspection_mode,
        'augmented_mode': show_augmented,
        'concatenate_data': False
    }
    
    # Create and run the new visualizer window
    visualizer = VisualizerWindow(config)
    visualizer.run()


def console_config(preset_data_file=None):
    """Fallback console-based configuration"""
    print("\n=== Lidar Visualizer Configuration ===")
    
    # Data file selection
    if preset_data_file:
        print(f"\nData Source: {preset_data_file} (preset from command line)")
        data_file = preset_data_file
    else:
        print("\nData Source Options:")
        print("1. Local data (data/run1/out1.txt)")
        print("2. Browse for file (enter full path)")
        
        while True:
            choice = input("Select data source (1/2) [1]: ").strip()
            if choice == '' or choice == '1':
                data_file = 'data/run1/out1.txt'
                break
            elif choice == '2':
                file_path = input("Enter full path to data file: ").strip()
                if file_path and file_path != '':
                    import os
                    if os.path.exists(file_path):
                        data_file = file_path
                        break
                    else:
                        print(f"File not found: {file_path}")
                        continue
                else:
                    print("No file path entered. Using default.")
                    data_file = 'data/run1/out1.txt'
                    break
            else:
                print("Invalid choice. Please enter 1 or 2.")
    
    # Inspection mode
    inspect = input("Enable inspection mode (frame by frame)? (y/n) [n]: ").strip().lower()
    inspection_mode = inspect in ['y', 'yes']
    
    # Augmented mode
    aug = input("Show augmented data? (y/n) [n]: ").strip().lower()
    augmented_mode = aug in ['y', 'yes']
    
    # Concatenate data
    concat = input("Concatenate augmented data to input file? (y/n) [n]: ").strip().lower()
    concatenate_data = concat in ['y', 'yes']
    
    config = {
        'data_file': data_file,
        'inspection_mode': inspection_mode,
        'augmented_mode': augmented_mode,
        'concatenate_data': concatenate_data
    }
    
    # Process concatenation if requested
    if config['concatenate_data']:
        success = concatenate_augmented_data(config['data_file'])
        if not success:
            print("Failed to concatenate data.")
            return None
    
    print(f"\nStarting visualizer with:")
    print(f"  Data file: {config['data_file']}")
    print(f"  Inspection mode: {config['inspection_mode']}")
    print(f"  Augmented mode: {config['augmented_mode']}")
    print(f"  Data concatenated: {config['concatenate_data']}")
    
    return config


if __name__ == '__main__':
    import sys
    
    # Check if running with command line arguments
    preset_data_file = None
    if len(sys.argv) > 1:
        preset_data_file = sys.argv[1]
        print(f"Command line data file provided: {preset_data_file}")
    
    # Check if we have a display available
    display_available = True
    try:
        import os
        if 'DISPLAY' not in os.environ and os.name != 'nt':
            display_available = False
            print("No display detected, using console configuration...")
    except:
        display_available = False
    
    # Create default configuration
    default_data_file = preset_data_file if preset_data_file else 'data/run1/out1.txt'
    config = {
        'data_file': default_data_file,
        'inspection_mode': False,
        'augmented_mode': False,
        'concatenate_data': False
    }
    
    print(f"Starting Lidar Visualizer with:")
    print(f"  Data file: {config['data_file']}")
    print(f"  Inspection mode: {config['inspection_mode']}")
    print(f"  Augmented mode: {config['augmented_mode']}")
    print(f"  Data concatenated: {config['concatenate_data']}")
    
    if display_available:
        try:
            # Create and run the visualizer window directly
            visualizer = VisualizerWindow(config)
            visualizer.run()
        except Exception as e:
            print(f"Error with visualizer window: {e}")
            display_available = False
    
    # Use console fallback if GUI failed or no display
    if not display_available:
        print("Using console configuration...")
        # Console-based fallback configuration with preset data file
        config = console_config(preset_data_file)
        if config:
            # Create and run the visualizer window
            visualizer = VisualizerWindow(config)
            visualizer.run()
        else:
            print(f"Using default configuration with data file: {default_data_file}")
            visualizer = VisualizerWindow(config)
            visualizer.run()
