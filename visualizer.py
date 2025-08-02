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
from ai_model import ai_model_manager, load_ai_model, get_ai_prediction, is_ai_model_loaded, get_ai_model_info
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
        self.inspect_mode = True  # Start in inspection mode by default
        self.augmented_mode = config['augmented_mode']
        
        # Direction ratio configuration (angular velocity to degree mapping)
        self.direction_ratio_max_degree = 45.0  # Maximum degrees for visualization
        self.direction_ratio_max_angular = 1.0  # Angular velocity value that maps to max degree
        
        # Previous frame angular velocity for comparison
        self.prev_angular_velocity = 0.0
        
        # Undo functionality
        self.undo_stack = []  # Stack to track changes for undo: [(frame_index, old_value, new_value), ...]
        self.max_undo_steps = 20  # Maximum number of undo steps to keep
        
        # Recent files management
        self.recent_files = []
        self.max_recent_files = 5
        self.recent_files_path = "visualizer_recent_files.txt"
        
        # Track unsaved changes
        self.has_unsaved_changes = False
        
        # Initialize data manager
        self.data_manager = DataManager(config['data_file'], 'data/run2/_out.txt', False)
        calculate_scale_factor(self.data_manager)
        
        # Store original title before adding asterisk
        self.original_title = f"Lidar Visualizer - {os.path.basename(config['data_file'])}"
        
        # Create main tkinter window
        self.root = tk.Tk()
        self.root.title(self.original_title)
        
        # Visualization toggle variables (must be created after root window)
        self.show_current_vel = tk.BooleanVar(value=True)   # Current velocity (green line)
        self.show_prev_vel = tk.BooleanVar(value=True)      # Previous velocity (red line)
        self.show_pred_vel = tk.BooleanVar(value=True)      # AI prediction (orange line)
        self.show_forward_dir = tk.BooleanVar(value=True)   # Forward direction (blue line)
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
        
        # Load recent files
        self.load_recent_files()
        
        # Initialize pygame after UI setup
        self.init_pygame()
        
        # Initialize variables
        self.distances = []
        
        # Update button states after everything is set up
        self.update_button_states()
        
        # Add current file to recent files
        self.add_recent_file(config['data_file'])
        
        # Update recent files menu
        self.update_recent_files_menu()
        
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
        
        # Create horizontal button layout - First row
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
        
        ttk.Button(button_frame, text="Flip H", 
                  command=self.flip_horizontal, width=8).pack(side='left', padx=(0, 2))
        ttk.Button(button_frame, text="Flip V", 
                  command=self.flip_vertical, width=8).pack(side='left', padx=(0, 5))
        
        # Checkbox for "Apply to All Frames"
        self.flip_all_var = tk.BooleanVar()
        self.flip_all_checkbox = ttk.Checkbutton(button_frame, text="All", 
                                               variable=self.flip_all_var, width=4)
        self.flip_all_checkbox.pack(side='left', padx=(0, 5))
        
        # Frame number input row - between first and second button sets
        frame_input_frame = ttk.Frame(controls_panel)
        frame_input_frame.pack(fill='x', pady=(5, 0))
        
        # Frame label and input field
        ttk.Label(frame_input_frame, text="Frame:", width=6).pack(side='left', padx=(0, 5))
        self.frame_var = tk.StringVar()
        self.frame_entry = ttk.Entry(frame_input_frame, textvariable=self.frame_var, width=10)
        self.frame_entry.pack(side='left', padx=(0, 10))
        self.frame_entry.bind('<Return>', self.on_frame_input)
        
        # Add total frames info
        self.total_frames_label = ttk.Label(frame_input_frame, text="", font=('Arial', 9), foreground='gray')
        self.total_frames_label.pack(side='left', padx=(5, 0))
        
        # Create second button frame for modified frames navigation - Second row
        self.modified_button_frame = ttk.Frame(controls_panel)
        self.modified_button_frame.pack(fill='x', pady=(5, 0))
        
        # Modified frames navigation buttons (initially hidden)
        self.first_modified_button = ttk.Button(self.modified_button_frame, text="⏮ First Mod", 
                                              command=self.first_modified_frame, width=12)
        self.prev_modified_button = ttk.Button(self.modified_button_frame, text="◀ Prev Mod", 
                                             command=self.prev_modified_frame, width=12)
        self.next_modified_button = ttk.Button(self.modified_button_frame, text="Next Mod ▶", 
                                             command=self.next_modified_frame, width=12)
        self.last_modified_button = ttk.Button(self.modified_button_frame, text="Last Mod ⏭", 
                                             command=self.last_modified_frame, width=12)
        
        # Keyboard shortcuts info - separate frame with wrapping
        shortcuts_frame = ttk.Frame(controls_panel)
        shortcuts_frame.pack(fill='x', pady=(5, 0))
        
        shortcuts_label = ttk.Label(shortcuts_frame, 
                                   text="💡 Shortcuts: Space=Play/Next | I=Mode | H=Flip H | V=Flip V | R=Replace | U=Undo | ←→=Prev/Next | Home/End=First/Last | ↑↓=Prev/Next Modified | PgUp/PgDn=First/Last Modified | 🤖 AI Menu: Load models for predictions", 
                                   font=('Arial', 8), foreground='navy', justify='left', 
                                   wraplength=800)  # Allow text to wrap at 800 pixels
        shortcuts_label.pack(anchor='w')
        
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
        ttk.Label(input_panel, text="Angular Vel:", 
                 font=('Arial', 9, 'bold'), foreground='darkblue').pack(anchor='w', pady=(0, 2))
        
        self.turn_var = tk.StringVar()
        self.turn_entry = ttk.Entry(input_panel, textvariable=self.turn_var, 
                                   width=18, font=('Courier', 9))
        self.turn_entry.pack(pady=(0, 5), fill='x')
        
        # Previous Angular velocity input
        ttk.Label(input_panel, text="Prev Angular Vel:", 
                 font=('Arial', 9, 'bold'), foreground='darkred').pack(anchor='w', pady=(0, 2))
        
        self.prev_turn_var = tk.StringVar()
        self.prev_turn_entry = ttk.Entry(input_panel, textvariable=self.prev_turn_var, 
                                        width=18, font=('Courier', 9), state='readonly')
        self.prev_turn_entry.pack(pady=(0, 3), fill='x')
        
        # Replace button
        self.replace_button = ttk.Button(input_panel, text="Replace (R)", 
                                        command=self.replace_with_previous, width=18)
        self.replace_button.pack(pady=(0, 3), fill='x')
        
        # Duplicate frame section
        duplicate_frame = ttk.Frame(input_panel)
        duplicate_frame.pack(pady=(5, 3), fill='x')
        
        ttk.Label(duplicate_frame, text="Duplicate Frame:", 
                 font=('Arial', 9, 'bold'), foreground='purple').pack(anchor='w')
        
        duplicate_controls = ttk.Frame(duplicate_frame)
        duplicate_controls.pack(fill='x', pady=(2, 0))
        
        # Frame count input for duplication
        ttk.Label(duplicate_controls, text="Count:", font=('Arial', 8)).pack(side='left')
        self.duplicate_count_var = tk.StringVar(value="1")
        duplicate_count_entry = ttk.Entry(duplicate_controls, textvariable=self.duplicate_count_var, 
                                         width=5, font=('Courier', 9))
        duplicate_count_entry.pack(side='left', padx=(5, 5))
        
        # Duplicate button
        duplicate_button = ttk.Button(duplicate_controls, text="Dup.", 
                                     command=self.duplicate_current_frame, width=10)
        duplicate_button.pack(side='right')
        
        # Undo instruction for replace
        ttk.Label(input_panel, text="💡 Press U for undo", 
                 font=('Arial', 7), foreground='darkgreen', 
                 wraplength=140).pack(anchor='w', pady=(0, 5), fill='x')
        
        # AI Prediction angular velocity input
        ttk.Label(input_panel, text="Pred Angular Vel:", 
                 font=('Arial', 9, 'bold'), foreground='darkorange').pack(anchor='w', pady=(0, 2))
        
        self.pred_turn_var = tk.StringVar()
        self.pred_turn_entry = ttk.Entry(input_panel, textvariable=self.pred_turn_var, 
                                        width=18, font=('Courier', 9), state='readonly')
        self.pred_turn_entry.pack(pady=(0, 5), fill='x')
        
        # Status info below angular velocity input
        self.frame_info_var = tk.StringVar()
        self.frame_info_var.set("Frame: -- [--]")
        frame_info_label = ttk.Label(input_panel, textvariable=self.frame_info_var, 
                                    font=('Courier', 8), foreground='blue', wraplength=200)
        frame_info_label.pack(pady=(0, 2), fill='x')
        
        # Modified frames info below main frame info
        self.modified_info_var = tk.StringVar()
        self.modified_info_var.set("Modified: 0 frames")
        modified_info_label = ttk.Label(input_panel, textvariable=self.modified_info_var, 
                                       font=('Courier', 8), foreground='purple', wraplength=200)
        modified_info_label.pack(pady=(0, 5), fill='x')
        
        # Instructions for angular velocity
        ttk.Label(input_panel, text="📝 Enter to update | R to replace | U to undo", 
                 font=('Arial', 7), foreground='darkgreen', 
                 wraplength=140).pack(anchor='w', pady=(0, 8), fill='x')
        
        # Linear velocity input
        ttk.Label(input_panel, text="Linear Vel:", 
                 font=('Arial', 9, 'bold'), foreground='darkblue').pack(anchor='w', pady=(0, 2))
        
        self.linear_var = tk.StringVar()
        self.linear_entry = ttk.Entry(input_panel, textvariable=self.linear_var, 
                                     width=18, font=('Courier', 9))
        self.linear_entry.pack(pady=(0, 5), fill='x')
        
        # Instructions for linear velocity
        ttk.Label(input_panel, text="⚠️ Not implemented", 
                 font=('Arial', 7), foreground='gray', 
                 wraplength=140).pack(anchor='w', pady=(0, 8), fill='x')
        
        # Augmentation Panel
        augment_panel = ttk.LabelFrame(left_sidebar, text="🔧 Augmentation", padding=6)
        augment_panel.pack(fill='x', pady=(5, 0))
        
        # Rotation controls only
        ttk.Label(augment_panel, text="Rotation:", 
                 font=('Arial', 9, 'bold'), foreground='darkgreen').pack(anchor='w', pady=(0, 2))
        
        rotation_frame = ttk.Frame(augment_panel)
        rotation_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Button(rotation_frame, text="↺ CCW", command=self.rotate_ccw, width=8).pack(side='left', padx=(0, 5))
        ttk.Button(rotation_frame, text="CW ↻", command=self.rotate_cw, width=8).pack(side='left')
        
        # Add Augmented Frames section
        ttk.Label(augment_panel, text="Add Frames:", 
                 font=('Arial', 9, 'bold'), foreground='darkblue').pack(anchor='w', pady=(8, 2))
        
        frames_input_frame = ttk.Frame(augment_panel)
        frames_input_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(frames_input_frame, text="Count:", font=('Arial', 8)).pack(side='left')
        self.frames_count_var = tk.StringVar(value="1")
        frames_count_entry = ttk.Entry(frames_input_frame, textvariable=self.frames_count_var, width=5, font=('Courier', 9))
        frames_count_entry.pack(side='left', padx=(5, 10))
        
        ttk.Button(frames_input_frame, text="Add", command=self.add_augmented_frames, width=6).pack(side='left')
        
        # Resize instruction in input panel
        resize_label = ttk.Label(input_panel, 
                                text="🔧 Resize window to scale visualizer", 
                                font=('Arial', 7), foreground='purple', 
                                justify='center', wraplength=140)
        resize_label.pack(pady=(8, 0), fill='x')
        
        # Center panel - Pygame canvas (now takes up much more space)
        center_panel = ttk.LabelFrame(content_frame, text="Lidar Visualization", padding=5)
        center_panel.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        # Visualization toggles panel - compact checkboxes above pygame
        vis_toggles_frame = ttk.Frame(center_panel)
        vis_toggles_frame.pack(fill='x', pady=(0, 5))
        
        # Create checkboxes for visualization toggles in a single row with matching colors
        tk.Checkbutton(vis_toggles_frame, text="Cur Vel", variable=self.show_current_vel, 
                      command=self.on_visualization_toggle, width=8, fg='green').pack(side='left', padx=(0, 5))
        tk.Checkbutton(vis_toggles_frame, text="Prev Vel", variable=self.show_prev_vel,
                      command=self.on_visualization_toggle, width=8, fg='red').pack(side='left', padx=(0, 5))
        tk.Checkbutton(vis_toggles_frame, text="Pred Vel", variable=self.show_pred_vel,
                      command=self.on_visualization_toggle, width=8, fg='orange').pack(side='left', padx=(0, 5))
        tk.Checkbutton(vis_toggles_frame, text="Fwd Dir", variable=self.show_forward_dir,
                      command=self.on_visualization_toggle, width=8, fg='blue').pack(side='left', padx=(0, 5))
        
        # Add zoom control buttons on the right side
        zoom_frame = ttk.Frame(vis_toggles_frame)
        zoom_frame.pack(side='right', padx=(5, 0))
        
        ttk.Label(zoom_frame, text="Zoom:", font=('Arial', 8)).pack(side='left', padx=(0, 3))
        ttk.Button(zoom_frame, text="−", command=self.zoom_out, width=3).pack(side='left', padx=(0, 2))
        ttk.Button(zoom_frame, text="+", command=self.zoom_in, width=3).pack(side='left')
        
        # Create a frame for pygame embedding with dynamic size
        self.pygame_frame = tk.Frame(center_panel, width=self.current_canvas_size, height=self.current_canvas_size, bg='lightgray')
        self.pygame_frame.pack(pady=5, expand=True, fill='both')
        self.pygame_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Create a canvas widget for pygame to render into
        self.canvas = tk.Canvas(self.pygame_frame, width=self.current_canvas_size, height=self.current_canvas_size, bg='white')
        self.canvas.pack(expand=True)
        
        # Status display at the bottom - minimal and compact
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill='x', side='bottom', pady=(5, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set(f"Data: {os.path.basename(self.config['data_file'])} | Mode: {'INSPECT' if self.inspect_mode else 'CONTINUOUS'} | Data: {'AUGMENTED' if self.augmented_mode else 'REAL'}")
        ttk.Label(status_frame, textvariable=self.status_var, 
                 font=('TkDefaultFont', 9), wraplength=800, anchor='e', justify='right').pack(fill='x')
        
        # Initialize the button states after setup
        self.update_button_states()
        
        # Initialize frame input field with current frame
        self.frame_var.set(str(self.data_manager.pointer + 1))
        
        # Initialize previous angular velocity display
        self.prev_turn_var.set("0.00")
        
        # Initialize AI prediction angular velocity display
        self.pred_turn_var.set("--")
        
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
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent", menu=self.recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="Save Data", command=self.save_data, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Preferences...", command=self.show_preferences_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_visualizer, accelerator="Ctrl+Q")
        
        # Data menu
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Show Statistics...", command=self.show_data_statistics, accelerator="Ctrl+I")
        
        # Visual menu
        visual_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visual", menu=visual_menu)
        visual_menu.add_command(label="Scale Factor...", command=self.show_scale_factor_dialog)
        visual_menu.add_command(label="Direction Ratio...", command=self.show_direction_ratio_dialog)
        
        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_command(label="Browse Model...", command=self.browse_ai_model)
        ai_menu.add_separator()
        ai_menu.add_command(label="Model Info...", command=self.show_ai_model_info)
        ai_menu.add_command(label="Clear Model", command=self.clear_ai_model)
        ai_menu.add_separator()
        
        # K-Best submenu
        kbest_menu = tk.Menu(ai_menu, tearoff=0)
        ai_menu.add_cascade(label="K-Best", menu=kbest_menu)
        kbest_menu.add_command(label="Load K-Best...", command=self.show_kbest_analysis)
        kbest_menu.add_command(label="View Current Positions...", command=self.show_current_kbest_positions)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About...", command=self.show_about_dialog)
        
        # Bind keyboard shortcuts
        self.root.bind_all("<Control-o>", lambda e: self.browse_data_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_data())
        self.root.bind_all("<Control-i>", lambda e: self.show_data_statistics())
    
    def on_key_press(self, event):
        """Handle keyboard events"""
        # Check if any text field is focused - if so, ignore navigation keys
        if (self.turn_entry.focus_get() == self.turn_entry or 
            self.frame_entry.focus_get() == self.frame_entry or
            self.prev_turn_entry.focus_get() == self.prev_turn_entry):
            # Text field is focused, only allow non-navigation keys
            if event.keysym.lower() in ['i', 'h', 'v', 'q']:
                # Allow mode toggles and quit even when text field is focused
                pass
            else:
                # Ignore all other keys including arrow keys when text field is focused  
                return
        
        if event.keysym == 'space':
            if self.inspect_mode:
                # In inspect mode, space advances to next frame
                self.next_frame()
            else:
                # In continuous mode, space toggles play/pause
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
            # R key for replace current angular velocity with previous
            self.replace_with_previous()
        elif event.keysym.lower() == 'u':
            # U key for undo last change
            self.undo_last_change()
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
        # Modified frame navigation shortcuts (with Shift modifier)
        elif event.keysym == 'Up' and self.inspect_mode:
            # Shift+Up arrow for previous modified frame
            self.prev_modified_frame()
        elif event.keysym == 'Down' and self.inspect_mode:
            # Shift+Down arrow for next modified frame
            self.next_modified_frame()
        elif event.keysym == 'Prior' and self.inspect_mode:  # Page Up
            # Page Up for first modified frame
            self.first_modified_frame()
        elif event.keysym == 'Next' and self.inspect_mode:   # Page Down
            # Page Down for last modified frame
            self.last_modified_frame()
    
    def on_visualization_toggle(self):
        """Callback for visualization toggle checkboxes - triggers canvas redraw"""
        try:
            # Only redraw if we have valid distance data
            if self.distances and len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                print("Visualization toggles updated - canvas redrawn")
        except Exception as e:
            print(f"Error in visualization toggle callback: {e}")
    
    def zoom_in(self):
        """Increase the pygame scale factor by 10%"""
        try:
            global SCALE_FACTOR
            new_scale = SCALE_FACTOR * 1.1
            SCALE_FACTOR = new_scale
            
            # Update status bar to show new scale factor
            self.status_var.set(f"Scale factor: {SCALE_FACTOR:.4f} (Zoom In) | Mode: {'INSPECT' if self.inspect_mode else 'CONTINUOUS'} | Data: {'AUGMENTED' if self.augmented_mode else 'REAL'}")
            
            # Re-render the current frame with new scale factor
            if self.distances and len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
            
            print(f"Zoomed in - Scale factor: {SCALE_FACTOR:.4f}")
            
        except Exception as e:
            print(f"Error zooming in: {e}")
            messagebox.showerror("Zoom Error", f"Error zooming in:\n{str(e)}")
    
    def zoom_out(self):
        """Decrease the pygame scale factor by 10%"""
        try:
            global SCALE_FACTOR
            new_scale = SCALE_FACTOR * 0.9
            
            # Prevent scale factor from becoming too small
            if new_scale < 0.01:
                new_scale = 0.01
                
            SCALE_FACTOR = new_scale
            
            # Update status bar to show new scale factor
            self.status_var.set(f"Scale factor: {SCALE_FACTOR:.4f} (Zoom Out) | Mode: {'INSPECT' if self.inspect_mode else 'CONTINUOUS'} | Data: {'AUGMENTED' if self.augmented_mode else 'REAL'}")
            
            # Re-render the current frame with new scale factor
            if self.distances and len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
            
            print(f"Zoomed out - Scale factor: {SCALE_FACTOR:.4f}")
            
        except Exception as e:
            print(f"Error zooming out: {e}")
            messagebox.showerror("Zoom Error", f"Error zooming out:\n{str(e)}")
    
    def update_previous_angular_velocity(self):
        """Update the previous angular velocity from current frame data"""
        try:
            if self.distances and len(self.distances) == LIDAR_RESOLUTION + 1:
                current_angular = float(self.distances[360])
                if self.augmented_mode:
                    current_angular = -current_angular
                self.prev_angular_velocity = current_angular
                
                # Update the previous angular velocity display
                self.prev_turn_var.set(f"{self.prev_angular_velocity:.2f}")
                print(f"Updated previous angular velocity: {self.prev_angular_velocity}")
        except (ValueError, TypeError, IndexError):
            self.prev_angular_velocity = 0.0
            self.prev_turn_var.set("0.00")
    
    def prev_frame(self):
        """Move to previous frame in inspect mode"""
        if self.inspect_mode and self.data_manager.has_prev():
            # Store current angular velocity as previous before moving
            self.update_previous_angular_velocity()
            
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
            # Store current angular velocity as previous before moving
            self.update_previous_angular_velocity()
            
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
            # Store current angular velocity as previous before moving
            self.update_previous_angular_velocity()
            
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
            # Store current angular velocity as previous before moving
            self.update_previous_angular_velocity()
            
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
    
    # Modified frames navigation methods
    def first_modified_frame(self):
        """Jump to first modified frame"""
        if self.inspect_mode and self.data_manager.modified_frames:
            # Store current angular velocity as previous before moving
            self.update_previous_angular_velocity()
            
            self.data_manager.first_modified()
            
            # Update display
            self.distances = self.data_manager.dataframe
            if len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                self.update_inputs()
            
            # Update button states after moving
            self.update_button_states()
            
            print(f"Jumped to first modified frame: {self.data_manager.get_modified_position_info()}")
    
    def prev_modified_frame(self):
        """Navigate to previous modified frame"""
        if self.inspect_mode and self.data_manager.has_prev_modified():
            # Store current angular velocity as previous before moving
            self.update_previous_angular_velocity()
            
            self.data_manager.prev_modified()
            
            # Update display
            self.distances = self.data_manager.dataframe
            if len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                self.update_inputs()
            
            # Update button states after moving
            self.update_button_states()
            
            print(f"Previous modified frame: {self.data_manager.get_modified_position_info()}")
    
    def next_modified_frame(self):
        """Navigate to next modified frame"""
        if self.inspect_mode and self.data_manager.has_next_modified():
            # Store current angular velocity as previous before moving
            self.update_previous_angular_velocity()
            
            self.data_manager.next_modified()
            
            # Update display
            self.distances = self.data_manager.dataframe
            if len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                self.update_inputs()
            
            # Update button states after moving
            self.update_button_states()
            
            print(f"Next modified frame: {self.data_manager.get_modified_position_info()}")
    
    def last_modified_frame(self):
        """Jump to last modified frame"""
        if self.inspect_mode and self.data_manager.modified_frames:
            # Store current angular velocity as previous before moving
            self.update_previous_angular_velocity()
            
            self.data_manager.last_modified()
            
            # Update display
            self.distances = self.data_manager.dataframe
            if len(self.distances) == LIDAR_RESOLUTION + 1:
                self.render_frame()
                self.update_inputs()
            
            # Update button states after moving
            self.update_button_states()
            
            print(f"Jumped to last modified frame: {self.data_manager.get_modified_position_info()}")
    
    def on_frame_input(self, event):
        """Handle frame number input - jump directly to specified frame"""
        try:
            frame_input = self.frame_var.get().strip()
            if not frame_input:
                return
                
            target_frame = int(frame_input) - 1  # Convert to 0-based index
            max_frame = len(self.data_manager.lines) - 1
            
            # Validate frame number
            if target_frame < 0:
                target_frame = 0
                messagebox.showwarning("Invalid Frame", f"Frame number must be >= 1. Jumping to frame 1.")
            elif target_frame > max_frame:
                target_frame = max_frame
                messagebox.showwarning("Invalid Frame", f"Frame number must be <= {max_frame + 1}. Jumping to frame {max_frame + 1}.")
            
            # Jump to the target frame
            self.data_manager._pointer = target_frame
            # Reset read position to force re-reading of the dataframe
            self.data_manager._read_pos = target_frame - 1
            
            # Update visualization
            self.render_frame()
            self.update_inputs()
            
            # Update button states
            if self.inspect_mode:
                self.update_button_states()
                
            # Update frame input to show actual frame number
            self.frame_var.set(str(target_frame + 1))
            
            # Remove focus from text field so keyboard navigation works immediately
            self.root.focus_set()
            
            print(f"Jumped to frame {target_frame + 1}")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid frame number")
            self.frame_var.set(str(self.data_manager.pointer + 1))  # Reset to current frame
        except Exception as e:
            error_msg = f"Error jumping to frame: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error in on_frame_input: {e}")
    
    def replace_with_previous(self):
        """Replace current angular velocity with previous frame's angular velocity"""
        try:
            if hasattr(self, 'prev_angular_velocity'):
                # Store old value for undo before making changes
                old_turn = self.turn_var.get() if self.turn_var.get() else "0.0"
                current_frame = self.data_manager._pointer
                
                # Add to undo stack before making changes
                self.add_to_undo_stack(current_frame, old_turn, str(self.prev_angular_velocity))
                
                # Set the current angular velocity to the previous one
                self.turn_var.set(str(self.prev_angular_velocity))
                
                # Trigger the update (simulate pressing Enter) - but don't double-track in undo
                # Create a mock event for the on_angular_velocity_input method
                class MockEvent:
                    pass
                mock_event = MockEvent()
                
                # Temporarily disable undo tracking for this update
                temp_undo_stack = self.undo_stack[:]  # Save current stack
                self.on_angular_velocity_input(mock_event)
                self.undo_stack = temp_undo_stack  # Restore stack (remove double entry)
                
                print(f"Replaced current angular velocity with previous: {self.prev_angular_velocity}")
            else:
                print("No previous angular velocity available")
                
        except Exception as e:
            error_msg = f"Error replacing angular velocity: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error in replace_with_previous: {e}")
    
    def add_to_undo_stack(self, frame_index, old_value, new_value):
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
    
    def undo_last_change(self):
        """Undo the last change made"""
        try:
            if not self.undo_stack:
                print("Nothing to undo")
                return
            
            # Get the last change
            frame_index, old_value, new_value = self.undo_stack.pop()
            
            # Navigate to the frame that was changed
            current_frame = self.data_manager._pointer
            if current_frame != frame_index:
                # Jump to the frame that needs to be undone
                self.data_manager._pointer = frame_index
                self.data_manager._read_pos = frame_index - 1  # Force re-reading
                self.update_display()
            
            # Restore the old value
            self.turn_var.set(str(old_value))
            
            # Update the data without adding to undo stack (to avoid infinite loop)
            if self.distances and len(self.distances) == LIDAR_RESOLUTION + 1:
                self.distances[360] = old_value
                
                # Update the data manager's current dataframe
                if hasattr(self.data_manager, '_lidar_dataframe') and len(self.data_manager._lidar_dataframe) > 360:
                    self.data_manager._lidar_dataframe[360] = old_value
                    
                    # Update the original line data in memory
                    updated_line = ','.join(str(x) for x in self.data_manager._lidar_dataframe)
                    self.data_manager.lines[self.data_manager._pointer] = updated_line + '\n'
                    
                    # If old value is the same as original, remove from modified frames
                    # (This is a simplified approach - in practice you'd want to track original values)
                    if str(old_value) == "0.0" or old_value == 0.0:  # Assuming 0.0 is default
                        if frame_index in self.data_manager._modified_frames:
                            self.data_manager._modified_frames.remove(frame_index)
                            # Update modified pointer
                            if self.data_manager._modified_frames:
                                try:
                                    self.data_manager._modified_pointer = self.data_manager._modified_frames.index(frame_index)
                                except ValueError:
                                    self.data_manager._modified_pointer = max(0, min(len(self.data_manager._modified_frames) - 1, self.data_manager._modified_pointer))
                            else:
                                self.data_manager._modified_pointer = -1
                    
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
    
    def load_recent_files(self):
        """Load recent files from disk"""
        try:
            if os.path.exists(self.recent_files_path):
                with open(self.recent_files_path, 'r') as f:
                    self.recent_files = [line.strip() for line in f.readlines() if line.strip()]
                    # Keep only files that still exist
                    self.recent_files = [f for f in self.recent_files if os.path.exists(f)]
                    # Limit to max_recent_files
                    self.recent_files = self.recent_files[:self.max_recent_files]
                print(f"Loaded {len(self.recent_files)} recent files")
        except Exception as e:
            print(f"Error loading recent files: {e}")
            self.recent_files = []
    
    def save_recent_files(self):
        """Save recent files to disk"""
        try:
            with open(self.recent_files_path, 'w') as f:
                for file_path in self.recent_files:
                    f.write(file_path + '\n')
            print(f"Saved {len(self.recent_files)} recent files")
        except Exception as e:
            print(f"Error saving recent files: {e}")
    
    def add_recent_file(self, file_path):
        """Add a file to the recent files list"""
        try:
            # Convert to absolute path
            abs_path = os.path.abspath(file_path)
            
            # Remove if already exists (to move it to top)
            if abs_path in self.recent_files:
                self.recent_files.remove(abs_path)
            
            # Add to beginning of list
            self.recent_files.insert(0, abs_path)
            
            # Keep only max_recent_files
            self.recent_files = self.recent_files[:self.max_recent_files]
            
            # Save to disk
            self.save_recent_files()
            
            # Update menu
            self.update_recent_files_menu()
            
        except Exception as e:
            print(f"Error adding recent file: {e}")
    
    def load_recent_file(self, file_path):
        """Load a file from the recent files list"""
        if os.path.exists(file_path):
            self.load_data_file(file_path)
        else:
            # File no longer exists, remove from recent files
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
                self.save_recent_files()
                self.update_recent_files_menu()
            messagebox.showerror("File Not Found", f"File not found:\n{file_path}")
    
    def update_recent_files_menu(self):
        """Update the recent files submenu"""
        if hasattr(self, 'recent_menu'):
            # Clear existing menu items
            self.recent_menu.delete(0, 'end')
            
            if self.recent_files:
                for i, file_path in enumerate(self.recent_files):
                    # Show just the filename for display
                    display_name = f"{i+1}. {os.path.basename(file_path)}"
                    self.recent_menu.add_command(
                        label=display_name,
                        command=lambda fp=file_path: self.load_recent_file(fp)
                    )
            else:
                self.recent_menu.add_command(label="(No recent files)", state='disabled')
    
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
            if hasattr(self, 'flip_all_var') and self.flip_all_var.get():
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
        self.render_frame()
    
    def flip_vertical(self):
        """Flip the current frame data vertically (forward-backward mirror)"""
        if not hasattr(self, 'data_manager') or not self.data_manager:
            print("No data manager available")
            return
            
        try:
            # Check if "Apply to All Frames" is checked
            if hasattr(self, 'flip_all_var') and self.flip_all_var.get():
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
        self.render_frame()
    
    def update_button_states(self):
        """Update button text based on current state"""
        if self.inspect_mode:
            # In inspect mode: hide play/pause, show navigation buttons
            self.play_pause_button.pack_forget()
            self.first_button.pack(side='left', padx=(0, 2), before=self.mode_button)
            self.prev_button.pack(side='left', padx=(0, 2), before=self.mode_button)
            self.next_button.pack(side='left', padx=(0, 2), before=self.mode_button)
            self.last_button.pack(side='left', padx=(0, 5), before=self.mode_button)
            
            # Always show modified frame navigation buttons in inspection mode
            self.modified_button_frame.pack(fill='x', pady=(5, 0))
            self.first_modified_button.pack(side='left', padx=(0, 2))
            self.prev_modified_button.pack(side='left', padx=(0, 2))
            self.next_modified_button.pack(side='left', padx=(0, 2))
            self.last_modified_button.pack(side='left', padx=(0, 5))
            
            # Update modified navigation button states based on whether modified frames exist
            if self.data_manager.modified_frames:
                # Enable buttons and update states based on navigation position
                if not self.data_manager.has_prev_modified():
                    self.prev_modified_button.config(state='disabled')
                    self.first_modified_button.config(state='disabled')
                else:
                    self.prev_modified_button.config(state='normal')
                    self.first_modified_button.config(state='normal')
                    
                if not self.data_manager.has_next_modified():
                    self.next_modified_button.config(state='disabled')
                    self.last_modified_button.config(state='disabled')
                else:
                    self.next_modified_button.config(state='normal')
                    self.last_modified_button.config(state='normal')
            else:
                # Disable all modified frame buttons if no modified frames exist
                self.first_modified_button.config(state='disabled')
                self.prev_modified_button.config(state='disabled')
                self.next_modified_button.config(state='disabled')
                self.last_modified_button.config(state='disabled')
            
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
            
            # Hide modified frame buttons in continuous mode
            self.modified_button_frame.pack_forget()
            
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
    
    def load_data_file(self, filename):
        """Load a data file and update the application state"""
        try:
            # Update status to show loading
            old_status = self.status_var.get()
            self.status_var.set("Loading data file...")
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
            
            # Add to recent files and update menu
            self.add_recent_file(filename)
            self.update_recent_files_menu()
            
            print(f"Successfully loaded data file: {filename}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to load data file: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.status_var.set(old_status)  # Restore previous status
            print(f"Error loading data file: {e}")
            return False

    def browse_data_file(self):
        """Browse for a new data file and load it"""
        import os
        
        # Set initial directory to ./data, fallback to current directory if not exists
        initial_dir = "./data"
        if not os.path.exists(initial_dir):
            initial_dir = "."
            
        file_types = [
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=file_types,
            initialdir=initial_dir
        )
        
        if filename:
            self.load_data_file(filename)
    
    def save_data(self):
        """Save the current data back to the original input file"""
        try:
            # Check if we have data manager
            if not hasattr(self, 'data_manager') or not self.data_manager:
                messagebox.showerror("Error", "No data manager available for saving")
                return
            
            # Check if there are any modifications to save
            if not self.data_manager.has_changes_to_save():
                messagebox.showinfo("Info", "No modifications to save")
                return
            
            # Save modifications back to the original input file
            if hasattr(self.data_manager, 'save_to_original_file'):
                success = self.data_manager.save_to_original_file()
                if success:
                    modified_count = len(self.data_manager.modified_frames)
                    self.status_var.set(f"Saved {modified_count} modified frames to original file | Mode: {'INSPECT' if self.inspect_mode else 'CONTINUOUS'} | Data: {'AUGMENTED' if self.augmented_mode else 'REAL'}")
                    messagebox.showinfo("Success", f"Successfully saved {modified_count} modified frames back to the original input file")
                    print(f"Data saved to original file: {self.data_manager.in_file}")
                    self.mark_data_saved()  # Mark data as saved (remove asterisk)
                else:
                    raise Exception("Failed to save to original file")
            else:
                # Fallback to legacy save method if new method not available
                if hasattr(self.data_manager, 'write_line'):
                    self.data_manager.write_line()
                out_file = getattr(self.data_manager, 'out_file', 'output file')
                self.status_var.set(f"Data saved to {os.path.basename(out_file)} | Mode: {'INSPECT' if self.inspect_mode else 'CONTINUOUS'} | Data: {'AUGMENTED' if self.augmented_mode else 'REAL'}")
                messagebox.showinfo("Success", f"Data saved successfully to {os.path.basename(out_file)}")
                print(f"Data saved to: {out_file}")
                self.mark_data_saved()  # Mark data as saved (remove asterisk)
                
        except Exception as e:
            error_msg = f"Failed to save data: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error saving data: {e}")
            print(traceback.format_exc())
    
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
            ttk.Label(self.stats_display_frame, text=stats_text, font=('Courier', 10), 
                     wraplength=400, justify='left').pack(anchor='w')
            
            if 'augmented_count' in current_stats and current_stats['augmented_count'] > 0:
                # Show augmented count in blue
                augmented_label = ttk.Label(self.stats_display_frame, 
                                        text=f"Augmented Data Frames: {current_stats['augmented_count']}", 
                                        font=('Courier', 10), foreground='blue',
                                        wraplength=400, justify='left')
                augmented_label.pack(anchor='w')
            
            if 'imputed_count' in current_stats and current_stats['imputed_count'] > 0:
                # Show imputed count in green
                imputed_label = ttk.Label(self.stats_display_frame, 
                                        text=f"Imputed Data Points: {current_stats['imputed_count']}", 
                                        font=('Courier', 10), foreground='green',
                                        wraplength=400, justify='left')
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
                    ttk.Label(self.stats_display_frame, text=stats_text, font=('Courier', 10),
                             wraplength=400, justify='left').pack(anchor='w')
                    
                    # Show mode-specific information
                    if 'append_mode' in current_stats:
                        if current_stats['append_mode']:
                            mode_text = f"Mode: Append (Original: {current_stats.get('original_count', 0)} + Augmented: {current_stats.get('augmented_count', 0)})"
                        else:
                            mode_text = f"Mode: Replace (Augmented only: {current_stats.get('augmented_count', 0)} frames)"
                        
                        mode_label = ttk.Label(self.stats_display_frame, 
                                            text=mode_text, 
                                            font=('Courier', 10), foreground='purple',
                                            wraplength=400, justify='left')
                        mode_label.pack(anchor='w')
                    
                    if 'augmented_count' in current_stats and current_stats['augmented_count'] > 0:
                        # Show augmented count in blue
                        augmented_label = ttk.Label(self.stats_display_frame, 
                                                text=f"Augmented Data Frames: {current_stats['augmented_count']}", 
                                                font=('Courier', 10), foreground='blue',
                                                wraplength=400, justify='left')
                        augmented_label.pack(anchor='w')
                    
                    if 'imputed_count' in current_stats and current_stats['imputed_count'] > 0:
                        # Show imputed count in green
                        imputed_label = ttk.Label(self.stats_display_frame, 
                                                text=f"Imputed Data Points: {current_stats['imputed_count']}", 
                                                font=('Courier', 10), foreground='green',
                                                wraplength=400, justify='left')
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
    
    def show_direction_ratio_dialog(self):
        """Show dialog to configure direction ratio (angular velocity to degree mapping)"""
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
        degree_var = tk.StringVar(value=str(self.direction_ratio_max_degree))
        degree_entry = ttk.Entry(degree_frame, textvariable=degree_var, 
                                font=('Courier', 10), width=15)
        degree_entry.pack(anchor='w', pady=(5, 0))
        degree_entry.focus_set()
        
        # Angular velocity max input
        angular_frame = ttk.Frame(main_frame)
        angular_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(angular_frame, text="Angular Velocity Max:", 
                 font=('Arial', 10)).pack(anchor='w')
        angular_var = tk.StringVar(value=str(self.direction_ratio_max_angular))
        angular_entry = ttk.Entry(angular_frame, textvariable=angular_var, 
                                 font=('Courier', 10), width=15)
        angular_entry.pack(anchor='w', pady=(5, 0))
        
        # Current mapping info
        info_text = f"Current: Angular velocity {self.direction_ratio_max_angular} → {self.direction_ratio_max_degree}°"
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
                
                # Update the configuration
                self.direction_ratio_max_degree = new_degree
                self.direction_ratio_max_angular = new_angular
                
                print(f"Direction ratio updated: {new_angular} → {new_degree}°")
                popup.destroy()
                
            except ValueError:
                messagebox.showerror("Invalid Value", 
                                   "Please enter valid numeric values for both fields")
        
        def cancel_dialog():
            """Cancel the dialog"""
            popup.destroy()
        
        # OK and Cancel buttons
        ttk.Button(button_frame, text="OK", command=apply_direction_ratio, 
                  width=10).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=cancel_dialog, 
                  width=10).pack(side='left')
        
        # Bind Enter key to apply changes
        degree_entry.bind('<Return>', lambda e: apply_direction_ratio())
        angular_entry.bind('<Return>', lambda e: apply_direction_ratio())
        popup.bind('<Escape>', lambda e: cancel_dialog())

    def browse_ai_model(self):
        """Browse for an AI model file and load it"""
        file_types = [
            ("Pickle files", "*.pkl"),
            ("Pickle files", "*.pickle"),
            ("All files", "*.*")
        ]
        
        # Default to ./models directory if it exists, otherwise current directory
        models_dir = os.path.abspath("./models")
        if os.path.exists(models_dir):
            initial_dir = models_dir
        else:
            initial_dir = os.getcwd()
        
        filename = filedialog.askopenfilename(
            title="Select AI Model File",
            filetypes=file_types,
            initialdir=initial_dir
        )
        
        if filename:
            try:
                # Update status to show loading
                old_status = self.status_var.get()
                self.status_var.set("Loading AI model...")
                self.root.update()
                
                # Load the model using the AI model manager
                success = load_ai_model(filename)
                
                if success:
                    model_info = get_ai_model_info()
                    self.status_var.set(f"{old_status} | AI Model: {os.path.basename(filename)}")
                    messagebox.showinfo("Model Loaded", 
                                      f"AI model loaded successfully!\n\nModel: {os.path.basename(filename)}\n{model_info}")
                    print(f"AI model loaded: {filename}")
                else:
                    self.status_var.set(old_status)
                    
            except Exception as e:
                error_msg = f"Unexpected error loading AI model: {str(e)}"
                messagebox.showerror("Error", error_msg)
                self.status_var.set(old_status)
                print(f"Error loading AI model: {e}")
    
    def show_ai_model_info(self):
        """Show information about the currently loaded AI model"""
        if not is_ai_model_loaded():
            messagebox.showinfo("No Model", "No AI model is currently loaded.\n\nUse 'AI > Browse Model...' to load a model.")
            return
        
        try:
            model_info = get_ai_model_info()
            model_path = ai_model_manager.get_model_path()
            
            info_text = f"""AI Model Information

File: {os.path.basename(model_path) if model_path else 'Unknown'}
Path: {model_path if model_path else 'Unknown'}

{model_info}

The model predicts car direction and is visualized with an orange line in the LiDAR display."""
            
            messagebox.showinfo("AI Model Info", info_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error getting model information: {str(e)}")
    
    def clear_ai_model(self):
        """Clear the currently loaded AI model"""
        if not is_ai_model_loaded():
            messagebox.showinfo("No Model", "No AI model is currently loaded.")
            return
        
        try:
            # Ask for confirmation
            result = messagebox.askyesno("Clear Model", 
                                       "Are you sure you want to clear the current AI model?\n\nThis will stop AI predictions.")
            
            if result:
                ai_model_manager.clear_model()
                
                # Update status
                old_status = self.status_var.get()
                # Remove AI model info from status
                if " | AI Model:" in old_status:
                    self.status_var.set(old_status.split(" | AI Model:")[0])
                
                messagebox.showinfo("Model Cleared", "AI model has been cleared successfully.")
                print("AI model cleared")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error clearing AI model: {str(e)}")
    
    def show_about_dialog(self):
        """Show the About dialog"""
        about_text = """LiDAR Visualizer

Version: 0.1
Date: 01/08/2025
Author: Hoang Giang Nguyen
Email: hoang.g.nguyen@student.uts.edu.au

A comprehensive LiDAR data visualization tool with AI integration capabilities."""
        
        messagebox.showinfo("About LiDAR Visualizer", about_text)
    
    def show_preferences_dialog(self):
        """Show preferences dialog"""
        from config import AUGMENTATION_UNIT
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Preferences")
        popup.geometry("450x280")
        popup.resizable(False, False)
        
        # Center the popup
        popup.transient(self.root)
        popup.grab_set()
        
        # Calculate center position
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (450 // 2)
        y = (popup.winfo_screenheight() // 2) - (280 // 2)
        popup.geometry(f"450x280+{x}+{y}")
        
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
        
        # Current values info
        info_text = f"Current Unit: {AUGMENTATION_UNIT}"
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
                
                # Update config module
                import config
                config.AUGMENTATION_UNIT = new_unit
                
                popup.destroy()
                print(f"Preferences updated - Unit: {new_unit}")
                
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
                # Extract lidar data (first 360 elements) and angular velocity (last element)
                lidar_data = str_data[:360]  # First 360 elements are LiDAR readings
                angular_velocity = str_data[-1]  # Last element is angular velocity
                other_data = str_data[360:-1] if len(str_data) > 361 else []  # Any data between LiDAR and angular velocity
                
                # Shift array by angle_degrees positions
                # Positive angle = counter-clockwise = shift left (indices decrease)  
                # Negative angle = clockwise = shift right (indices increase)
                shift_amount = int(round(angle_degrees)) % 360
                
                # Perform the shift with wraparound
                if shift_amount != 0:
                    rotated_lidar = lidar_data[-shift_amount:] + lidar_data[:-shift_amount]
                else:
                    rotated_lidar = lidar_data[:]
                
                # Reconstruct the complete data with original angular velocity preserved
                modified_data = rotated_lidar + other_data + [angular_velocity]
                
                # Update the current frame with rotated data
                self.data_manager.update_current_frame(modified_data)
                
                # Mark frame as modified and refresh display
                self._mark_frame_modified()
                self.render_frame()
                
                print(f"Rotated LiDAR data by {angle_degrees}° (shifted by {shift_amount} indices), angular velocity preserved: {angular_velocity}")
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
                frame_count = int(self.frames_count_var.get())
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
            # Get the number of duplicates to create from UI
            try:
                duplicate_count = int(self.duplicate_count_var.get())
                if duplicate_count <= 0:
                    print("Duplicate count must be greater than 0")
                    return
            except ValueError:
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
    
    def show_kbest_analysis(self):
        """Show the K-Best feature analysis dialog"""
        try:
            from kbest_analysis import show_kbest_analysis_dialog
            
            def refresh_visualization():
                """Callback to refresh visualization after applying K-Best results"""
                # Force a re-render to show updated DECISIVE_FRAME_POSITIONS
                if hasattr(self, 'distances') and self.distances:
                    self.render_frame()
                    print("Visualization refreshed with new K-Best positions")
            
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
    
    def on_closing(self):
        """Handle window closing"""
        # Check for unsaved changes before closing
        if not self.prompt_save_before_exit():
            return  # User cancelled the exit
        
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
        """Handle angular velocity input - updates data manager properly"""
        try:
            new_turn = self.turn_var.get()
            print(f"Angular velocity input received: {new_turn}")
            
            # Update the current data frame with new angular velocity
            if self.distances and len(self.distances) == LIDAR_RESOLUTION + 1:
                # Store old value for undo before making changes
                old_turn = self.distances[360] if len(self.distances) > 360 else "0.0"
                current_frame = self.data_manager._pointer
                
                # Add to undo stack before making changes
                self.add_to_undo_stack(current_frame, old_turn, new_turn)
                
                self.distances[360] = new_turn
                
                # Update the data manager's current dataframe
                if hasattr(self.data_manager, '_lidar_dataframe') and len(self.data_manager._lidar_dataframe) > 360:
                    self.data_manager._lidar_dataframe[360] = new_turn
                    
                    # Update the original line data in memory (same as DataManager.update method)
                    updated_line = ','.join(str(x) for x in self.data_manager._lidar_dataframe)
                    self.data_manager.lines[self.data_manager._pointer] = updated_line + '\n'
                    
                    # Track this frame as modified
                    current_frame = self.data_manager._pointer
                    if current_frame not in self.data_manager._modified_frames:
                        self.data_manager._modified_frames.append(current_frame)
                        self.data_manager._modified_frames.sort()  # Keep the list sorted
                        # Update the modified pointer to point to the current frame
                        self.data_manager._modified_pointer = self.data_manager._modified_frames.index(current_frame)
                        print(f"Frame {current_frame} added to modified frames list")
                    
                    print(f"Data manager updated with new turn value: {new_turn} at frame {self.data_manager._pointer}")
                
                # Mark data as changed
                self.mark_data_changed()
                
                # Don't clear the input field - keep the value for user reference
                print(f"Angular velocity updated to: {new_turn}")
                
                # Immediately update the visualization
                self.render_frame()
                self.update_inputs()  # Update other UI elements
                
                # Update button states in case we're at boundaries or modified frames list changed
                if self.inspect_mode:
                    self.update_button_states()
                
                # Remove focus from text field so keyboard navigation works immediately
                self.root.focus_set()  # Transfer focus to the main window
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
            # Update frame input field with current frame number (if not actively being edited)
            if not self.frame_entry.focus_get() == self.frame_entry:  # Only update if not focused
                current_frame = self.data_manager.pointer + 1  # Convert to 1-based indexing
                self.frame_var.set(str(current_frame))
            
            # Update total frames info
            total_frames = len(self.data_manager.lines)
            self.total_frames_label.config(text=f"of {total_frames}")
            
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
            
            # Update modified frames information display
            total_modified = len(self.data_manager.modified_frames)
            if total_modified > 0:
                # If current frame is in modified frames list, show position in that list
                if self.data_manager.pointer in self.data_manager.modified_frames:
                    current_modified_pos = self.data_manager.modified_frames.index(self.data_manager.pointer) + 1
                    self.modified_info_var.set(f"Modified: {current_modified_pos}/{total_modified} [Frame #{self.data_manager.pointer + 1}]")
                else:
                    self.modified_info_var.set(f"Modified: {total_modified} frames total")
            else:
                self.modified_info_var.set("Modified: 0 frames")
            
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
                
                # Use standard coordinates - the data itself has been flipped if needed
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
            
            # Draw forward direction (blue line) - only if checkbox is checked
            if self.show_forward_dir.get():
                pygame.draw.line(self.screen, (0, 0, 255), (center_x, center_y),
                                (center_x + car_line_length, center_y), 3)
            
            # Draw turn direction (scaled with configurable direction ratio) - current velocity (green line)
            if self.show_current_vel.get():
                try:
                    turn_value = float(self.distances[360])
                    # Use the actual turn value from the data (already flipped if frame was flipped)
                    
                    # Apply configurable direction ratio mapping
                    # Convert angular velocity to degrees using the configured mapping
                    angle_degrees = (turn_value / self.direction_ratio_max_angular) * self.direction_ratio_max_degree
                    # Convert degrees to radians for math functions
                    angle_radians = angle_degrees * math.pi / 180
                    
                    x = math.cos(angle_radians) * car_line_length
                    y = math.sin(angle_radians) * car_line_length
                    # Flip Y coordinate to match lidar coordinate system (pygame Y increases downward)
                    pygame.draw.line(self.screen, (0, 255, 0), (center_x, center_y),
                                   (center_x + x, center_y - y), 3)
                except (ValueError, TypeError):
                    pass
            
            # Draw previous frame direction (in red) - only if checkbox is checked
            if self.show_prev_vel.get():
                try:
                    prev_turn_value = self.prev_angular_velocity
                    if self.augmented_mode:
                        prev_turn_value = -prev_turn_value
                        
                    # Apply configurable direction ratio mapping for previous frame
                    prev_angle_degrees = (prev_turn_value / self.direction_ratio_max_angular) * self.direction_ratio_max_degree
                    # Convert degrees to radians for math functions
                    prev_angle_radians = prev_angle_degrees * math.pi / 180
                    
                    prev_x = math.cos(prev_angle_radians) * car_line_length
                    prev_y = math.sin(prev_angle_radians) * car_line_length
                    # Flip Y coordinate to match lidar coordinate system (pygame Y increases downward)
                    pygame.draw.line(self.screen, (255, 0, 0), (center_x, center_y),
                                   (center_x + prev_x, center_y - prev_y), 2)  # Slightly thinner line
                except (ValueError, TypeError):
                    pass
            
            # Draw AI prediction direction (in orange) - only if checkbox is checked
            if self.show_pred_vel.get():
                try:
                    if is_ai_model_loaded():
                        # Get AI prediction for current frame
                        current_frame = self.data_manager.pointer
                        ai_prediction = get_ai_prediction(self.distances[:360], current_frame)
                        
                        if ai_prediction is not None:
                            ai_turn_value = float(ai_prediction)
                            if self.augmented_mode:
                                ai_turn_value = -ai_turn_value
                            
                            # Update AI prediction display
                            self.pred_turn_var.set(f"{ai_turn_value:.2f}")
                            
                            # Apply configurable direction ratio mapping for AI prediction
                            ai_angle_degrees = (ai_turn_value / self.direction_ratio_max_angular) * self.direction_ratio_max_degree
                            # Convert degrees to radians for math functions
                            ai_angle_radians = ai_angle_degrees * math.pi / 180
                            
                            ai_x = math.cos(ai_angle_radians) * car_line_length
                            ai_y = math.sin(ai_angle_radians) * car_line_length
                            # Flip Y coordinate to match lidar coordinate system (pygame Y increases downward)
                            pygame.draw.line(self.screen, (255, 165, 0), (center_x, center_y),
                                           (center_x + ai_x, center_y - ai_y), 3)  # Orange color (255, 165, 0)
                        else:
                            # No prediction available
                            self.pred_turn_var.set("--")
                    else:
                        # No AI model loaded
                        self.pred_turn_var.set("--")
                except (ValueError, TypeError, Exception) as e:
                    # Silently ignore AI prediction errors to avoid disrupting visualization
                    pass
            else:
                # When prediction visualization is disabled, still update the text field if model is loaded
                try:
                    if is_ai_model_loaded():
                        current_frame = self.data_manager.pointer
                        ai_prediction = get_ai_prediction(self.distances[:360], current_frame)
                        if ai_prediction is not None:
                            ai_turn_value = float(ai_prediction)
                            if self.augmented_mode:
                                ai_turn_value = -ai_turn_value
                            self.pred_turn_var.set(f"{ai_turn_value:.2f}")
                        else:
                            self.pred_turn_var.set("--")
                    else:
                        self.pred_turn_var.set("--")
                except:
                    self.pred_turn_var.set("--")
            
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
                        # Store current angular velocity as previous before advancing
                        self.update_previous_angular_velocity()
                        
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
        
        ttk.Label(stats_frame, text=stats_text, font=('Courier', 10),
                 wraplength=600, justify='left').pack(anchor='w')
        
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
    
    # Reset to beginning to sample from start (respecting data start line for header detection)  
    data_manager._pointer = getattr(data_manager, '_data_start_line', 0)
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
    
    # Reset data manager to beginning (respecting data start line for header detection)
    data_manager._pointer = getattr(data_manager, '_data_start_line', 0)
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
