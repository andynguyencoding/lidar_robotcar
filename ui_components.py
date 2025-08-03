"""
UI components and menu management for the LiDAR Visualizer
"""

import tkinter as tk
from tkinter import ttk
from config import DEFAULT_CANVAS_SIZE


class UIManager:
    """Manages UI components and layout"""
    
    def __init__(self, root, callbacks):
        self.root = root
        self.callbacks = callbacks
        self.current_canvas_size = DEFAULT_CANVAS_SIZE
        
        # UI variables
        self.frame_var = None
        self.turn_var = None  
        self.prev_turn_var = None
        self.pred_turn_var = None
        self.linear_var = None
        self.status_var = None
        self.frame_info_var = None
        self.modified_info_var = None
        
        # Visualization toggle variables
        self.show_current_vel = None
        self.show_prev_vel = None
        self.show_pred_vel = None
        self.show_forward_dir = None
        
        # Dataset navigation variables
        self.selected_dataset = None
        self.dataset_radio_frame = None
        
        # UI components
        self.total_frames_label = None
        self.frame_entry = None
        self.turn_entry = None
        self.prev_turn_entry = None
        self.pred_turn_entry = None
        self.linear_entry = None
        
        # Buttons
        self.play_pause_button = None
        self.mode_button = None
        self.first_button = None
        self.prev_button = None
        self.next_button = None
        self.last_button = None
        self.replace_button = None
        
        # Modified frame buttons
        self.modified_button_frame = None
        self.first_modified_button = None
        self.prev_modified_button = None
        self.next_modified_button = None
        self.last_modified_button = None
        
        # Canvas components
        self.pygame_frame = None
        self.canvas = None
        
        # Menu components
        self.recent_menu = None
    
    def setup_ui(self):
        """Setup the main UI components"""
        # Initialize tkinter variables
        self.frame_var = tk.StringVar()
        self.turn_var = tk.StringVar()
        self.prev_turn_var = tk.StringVar()
        self.pred_turn_var = tk.StringVar()
        self.linear_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")  # Set initial status
        self.frame_info_var = tk.StringVar()
        self.modified_info_var = tk.StringVar()
        
        # Visualization toggle variables
        self.show_current_vel = tk.BooleanVar(value=True)
        self.show_prev_vel = tk.BooleanVar(value=True)
        self.show_pred_vel = tk.BooleanVar(value=True)
        self.show_forward_dir = tk.BooleanVar(value=True)
        
        # Dataset navigation variables
        self.selected_dataset = tk.StringVar(value="Original")  # Default to original dataset
        
        # Data splitting variables
        self.data_splits = {}  # Will store frame_id -> split_type mapping
        self.split_ratios = [70, 20, 10]  # Default train:validation:test ratios
        
        # Create menu bar
        self.create_menu_bar()
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Setup control panels - status panel must be packed first when using side='bottom'
        self.setup_controls_panel(main_frame)
        self.setup_status_panel(main_frame)  # Pack bottom elements first
        self.setup_content_panel(main_frame)  # Content expands in remaining space
        
        # Initialize display values
        self.frame_var.set("1")
        self.prev_turn_var.set("0.00")
        self.pred_turn_var.set("--")
        self.frame_info_var.set("Frame: -- [--]")
        self.modified_info_var.set("Modified: 0 frames")
        
        # Bind events
        self.bind_events()
    
    def setup_controls_panel(self, parent):
        """Setup the controls panel"""
        controls_container = ttk.Frame(parent)
        controls_container.pack(fill='x', pady=(0, 5))
        
        # Left controls panel - increased width to accommodate all controls including mode button
        left_controls = ttk.LabelFrame(controls_container, text="Navigation & Controls", padding=5)
        left_controls.pack(side='left', fill='y', padx=(0, 5))
        left_controls.configure(width=450)  # Increased width to show all controls including mode button
        left_controls.pack_propagate(False)  # Prevent shrinking
        
        # First row - main control buttons
        button_frame = ttk.Frame(left_controls)
        button_frame.pack(fill='x')
        
        self.play_pause_button = ttk.Button(button_frame, text="▶ Play", 
                                           command=self.callbacks.get('toggle_pause'), width=12)
        self.play_pause_button.pack(side='left', padx=(0, 5))
        
        # Navigation buttons (initially hidden)
        self.first_button = ttk.Button(button_frame, text="⏮ First", 
                                      command=self.callbacks.get('first_frame'), width=12)
        self.prev_button = ttk.Button(button_frame, text="◀ Prev", 
                                     command=self.callbacks.get('prev_frame'), width=12)
        self.next_button = ttk.Button(button_frame, text="Next ▶", 
                                     command=self.callbacks.get('next_frame'), width=12)
        self.last_button = ttk.Button(button_frame, text="Last ⏭", 
                                     command=self.callbacks.get('last_frame'), width=12)
        
        self.mode_button = ttk.Button(button_frame, text="Mode: Cont", 
                                     command=self.callbacks.get('toggle_inspect'), width=12)
        self.mode_button.pack(side='left', padx=(0, 5))
        
        # Frame input row
        frame_input_frame = ttk.Frame(left_controls)
        frame_input_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(frame_input_frame, text="Frame:", width=6).pack(side='left', padx=(0, 5))
        self.frame_entry = ttk.Entry(frame_input_frame, textvariable=self.frame_var, width=10)
        self.frame_entry.pack(side='left', padx=(0, 10))
        
        self.total_frames_label = ttk.Label(frame_input_frame, text="", font=('Arial', 9), foreground='gray')
        self.total_frames_label.pack(side='left', padx=(5, 0))
        
        # Modified frames navigation
        self.modified_button_frame = ttk.Frame(left_controls)
        self.modified_button_frame.pack(fill='x', pady=(5, 0))
        
        self.first_modified_button = ttk.Button(self.modified_button_frame, text="⏮ First Mod", 
                                              command=self.callbacks.get('first_modified_frame'), width=12)
        self.prev_modified_button = ttk.Button(self.modified_button_frame, text="◀ Prev Mod", 
                                             command=self.callbacks.get('prev_modified_frame'), width=12)
        self.next_modified_button = ttk.Button(self.modified_button_frame, text="Next Mod ▶", 
                                             command=self.callbacks.get('next_modified_frame'), width=12)
        self.last_modified_button = ttk.Button(self.modified_button_frame, text="Last Mod ⏭", 
                                             command=self.callbacks.get('last_modified_frame'), width=12)
        
        # Right controls panel - Data Management & Flipping - now expands to fill remaining space
        right_controls = ttk.LabelFrame(controls_container, text="Data Management", padding=5)
        right_controls.pack(side='right', fill='both', expand=True)
        
        # Flipping controls
        flip_frame = ttk.Frame(right_controls)
        flip_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Button(flip_frame, text="Flip H", 
                  command=self.callbacks.get('flip_horizontal'), width=8).pack(side='left', padx=(0, 2))
        ttk.Button(flip_frame, text="Flip V", 
                  command=self.callbacks.get('flip_vertical'), width=8).pack(side='left', padx=(0, 5))
        
        # Checkbox for "Apply to All Frames"
        self.flip_all_var = tk.BooleanVar()
        self.flip_all_checkbox = ttk.Checkbutton(flip_frame, text="All", 
                                               variable=self.flip_all_var, width=4)
        self.flip_all_checkbox.pack(side='left', padx=(0, 5))
        
        # Data splitting controls
        split_frame = ttk.Frame(right_controls)
        split_frame.pack(fill='x', pady=(5, 5))
        
        ttk.Button(split_frame, text="📊 Split Data", 
                  command=self.callbacks.get('split_data'), width=12).pack(side='left', padx=(0, 5))
        
        ttk.Button(split_frame, text="🔄 Move Set", 
                  command=self.callbacks.get('move_to_next_set'), width=12).pack(side='left')
        
        # Dataset selection radio buttons (visible below Split Data and Move Set buttons)
        self.dataset_radio_frame = ttk.LabelFrame(right_controls, text="Navigate Dataset", padding=3)
        self.dataset_radio_frame.pack(fill='x', pady=(5, 0))  # Pack immediately to make visible
        
        # Add trace for dataset selection changes
        self.selected_dataset.trace('w', lambda *args: self.callbacks.get('on_dataset_selection_changed', lambda: None)())
        
        # Radio buttons for dataset selection
        ttk.Radiobutton(self.dataset_radio_frame, text="Original", variable=self.selected_dataset, 
                       value="Original", width=9).pack(side='left', padx=(0, 2))
        ttk.Radiobutton(self.dataset_radio_frame, text="Train", variable=self.selected_dataset, 
                       value="Train", width=7).pack(side='left', padx=(0, 2))
        ttk.Radiobutton(self.dataset_radio_frame, text="Val", variable=self.selected_dataset, 
                       value="Validation", width=6).pack(side='left', padx=(0, 2))
        ttk.Radiobutton(self.dataset_radio_frame, text="Test", variable=self.selected_dataset, 
                       value="Test", width=6).pack(side='left')
    
    def setup_status_panel(self, parent):
        """Setup the status panel"""
        # Create a minimal status frame at the bottom
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', side='bottom', pady=(5, 0))
        
        # Create the status label - minimal styling
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                 font=('TkDefaultFont', 9), wraplength=800, anchor='e', justify='right')
        status_label.pack(fill='x')
    
    def show_dataset_radio_buttons(self):
        """Show the dataset selection radio buttons after data split"""
        if self.dataset_radio_frame:
            self.dataset_radio_frame.pack(fill='x', pady=(5, 0))
    
    def hide_dataset_radio_buttons(self):
        """Hide the dataset selection radio buttons"""
        if self.dataset_radio_frame:
            self.dataset_radio_frame.pack_forget()
    
    def setup_content_panel(self, parent):
        """Setup the main content panel"""
        content_frame = ttk.Frame(parent)
        # Don't expand vertically to leave room for status panel
        content_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        # Left sidebar - input controls
        left_sidebar = ttk.Frame(content_frame, width=150)
        left_sidebar.pack(side='left', fill='y', padx=(0, 5))
        left_sidebar.pack_propagate(False)
        
        self.setup_input_panel(left_sidebar)
        
        # Center panel - visualization
        center_panel = ttk.LabelFrame(content_frame, text="Lidar Visualization", padding=5)
        center_panel.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        self.setup_visualization_panel(center_panel)
    
    def setup_input_panel(self, parent):
        """Setup the input controls panel"""
        input_panel = ttk.LabelFrame(parent, text="🎮 Input Controls", padding=6)
        input_panel.pack(fill='both', expand=True)
        
        # Angular velocity
        ttk.Label(input_panel, text="Angular Vel:", 
                 font=('Arial', 9, 'bold'), foreground='darkblue').pack(anchor='w', pady=(0, 2))
        
        self.turn_entry = ttk.Entry(input_panel, textvariable=self.turn_var, 
                                   width=18, font=('Courier', 9))
        self.turn_entry.pack(pady=(0, 5), fill='x')
        
        # Previous Angular velocity
        ttk.Label(input_panel, text="Prev Angular Vel:", 
                 font=('Arial', 9, 'bold'), foreground='darkred').pack(anchor='w', pady=(0, 2))
        
        self.prev_turn_entry = ttk.Entry(input_panel, textvariable=self.prev_turn_var, 
                                        width=18, font=('Courier', 9), state='readonly')
        self.prev_turn_entry.pack(pady=(0, 3), fill='x')
        
        # Replace button
        self.replace_button = ttk.Button(input_panel, text="Replace (R)", 
                                        command=self.callbacks.get('replace_with_previous'), width=18)
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
                                     command=self.callbacks.get('duplicate_current_frame'), width=10)
        duplicate_button.pack(side='right')
        
        # Undo instruction
        ttk.Label(input_panel, text="💡 Press U for undo", 
                 font=('Arial', 7), foreground='darkgreen', 
                 wraplength=140).pack(anchor='w', pady=(0, 5), fill='x')
        
        # AI Prediction angular velocity
        ttk.Label(input_panel, text="Pred Angular Vel:", 
                 font=('Arial', 9, 'bold'), foreground='darkorange').pack(anchor='w', pady=(0, 2))
        
        self.pred_turn_entry = ttk.Entry(input_panel, textvariable=self.pred_turn_var, 
                                        width=18, font=('Courier', 9), state='readonly')
        self.pred_turn_entry.pack(pady=(0, 5), fill='x')
        
        # Frame info
        frame_info_label = ttk.Label(input_panel, textvariable=self.frame_info_var, 
                                    font=('Courier', 8), foreground='blue', wraplength=200)
        frame_info_label.pack(pady=(0, 2), fill='x')
        
        # Modified frames info
        modified_info_label = ttk.Label(input_panel, textvariable=self.modified_info_var, 
                                       font=('Courier', 8), foreground='purple', wraplength=200)
        modified_info_label.pack(pady=(0, 5), fill='x')
        
        # Instructions
        ttk.Label(input_panel, text="📝 Enter to update | R to replace | U to undo", 
                 font=('Arial', 7), foreground='darkgreen', 
                 wraplength=140).pack(anchor='w', pady=(0, 8), fill='x')
        
        # Augmentation Panel
        augment_panel = ttk.LabelFrame(parent, text="🔧 Augmentation", padding=6)
        augment_panel.pack(fill='x', pady=(5, 0))
        
        # Rotation controls only
        ttk.Label(augment_panel, text="Rotation:", 
                 font=('Arial', 9, 'bold'), foreground='darkgreen').pack(anchor='w', pady=(0, 2))
        
        rotation_frame = ttk.Frame(augment_panel)
        rotation_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Button(rotation_frame, text="↺ CCW", command=self.callbacks.get('rotate_ccw'), width=8).pack(side='left', padx=(0, 5))
        ttk.Button(rotation_frame, text="CW ↻", command=self.callbacks.get('rotate_cw'), width=8).pack(side='left')
        
        # Add Augmented Frames section
        ttk.Label(augment_panel, text="Add Frames:", 
                 font=('Arial', 9, 'bold'), foreground='darkblue').pack(anchor='w', pady=(8, 2))
        
        frames_input_frame = ttk.Frame(augment_panel)
        frames_input_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(frames_input_frame, text="Count:", font=('Arial', 8)).pack(side='left')
        self.frames_count_var = tk.StringVar(value="1")
        frames_count_entry = ttk.Entry(frames_input_frame, textvariable=self.frames_count_var, width=5, font=('Courier', 9))
        frames_count_entry.pack(side='left', padx=(5, 10))
        
        ttk.Button(frames_input_frame, text="Add", command=self.callbacks.get('add_augmented_frames'), width=6).pack(side='left')
        
        # Linear velocity
        ttk.Label(input_panel, text="Linear Vel:", 
                 font=('Arial', 9, 'bold'), foreground='darkblue').pack(anchor='w', pady=(8, 2))
        
        self.linear_entry = ttk.Entry(input_panel, textvariable=self.linear_var, 
                                     width=18, font=('Courier', 9))
        self.linear_entry.pack(pady=(0, 5), fill='x')
        
        ttk.Label(input_panel, text="⚠️ Not implemented", 
                 font=('Arial', 7), foreground='gray', 
                 wraplength=140).pack(anchor='w', pady=(0, 8), fill='x')
        
        # Resize instruction
        resize_label = ttk.Label(input_panel, 
                                text="🔧 Resize window to scale visualizer", 
                                font=('Arial', 7), foreground='purple', 
                                justify='center', wraplength=140)
        resize_label.pack(pady=(8, 0), fill='x')
    
    def setup_visualization_panel(self, parent):
        """Setup the visualization panel"""
        # Visualization toggles
        vis_toggles_frame = ttk.Frame(parent)
        vis_toggles_frame.pack(fill='x', pady=(0, 5))
        
        tk.Checkbutton(vis_toggles_frame, text="Cur Vel", variable=self.show_current_vel, 
                      command=self.callbacks.get('on_visualization_toggle'), width=8, fg='green').pack(side='left', padx=(0, 5))
        tk.Checkbutton(vis_toggles_frame, text="Prev Vel", variable=self.show_prev_vel,
                      command=self.callbacks.get('on_visualization_toggle'), width=8, fg='red').pack(side='left', padx=(0, 5))
        tk.Checkbutton(vis_toggles_frame, text="Pred Vel", variable=self.show_pred_vel,
                      command=self.callbacks.get('on_visualization_toggle'), width=8, fg='orange').pack(side='left', padx=(0, 5))
        tk.Checkbutton(vis_toggles_frame, text="Fwd Dir", variable=self.show_forward_dir,
                      command=self.callbacks.get('on_visualization_toggle'), width=8, fg='blue').pack(side='left', padx=(0, 5))
        
        # Add zoom control buttons on the right side
        zoom_frame = ttk.Frame(vis_toggles_frame)
        zoom_frame.pack(side='right', padx=(5, 0))
        
        ttk.Label(zoom_frame, text="Zoom:", font=('Arial', 8)).pack(side='left', padx=(0, 3))
        ttk.Button(zoom_frame, text="−", command=self.callbacks.get('zoom_out'), width=3).pack(side='left', padx=(0, 2))
        ttk.Button(zoom_frame, text="+", command=self.callbacks.get('zoom_in'), width=3).pack(side='left')
        
        # Pygame frame
        self.pygame_frame = tk.Frame(parent, width=self.current_canvas_size, 
                                    height=self.current_canvas_size, bg='lightgray')
        self.pygame_frame.pack(pady=5, expand=True, fill='both')
        self.pygame_frame.pack_propagate(False)
        
        # Canvas
        self.canvas = tk.Canvas(self.pygame_frame, width=self.current_canvas_size, 
                               height=self.current_canvas_size, bg='white')
        self.canvas.pack(expand=True)
    
    def create_menu_bar(self):
        """Create the main menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Browse Data...", command=self.callbacks.get('browse_data_file'), accelerator="Ctrl+O")
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent", menu=self.recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="Save Data", command=self.callbacks.get('save_data'), accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Preferences...", command=self.callbacks.get('show_preferences_dialog'))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.callbacks.get('quit_app'), accelerator="Ctrl+Q")
        
        # Data menu
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Show Statistics...", command=self.callbacks.get('show_data_statistics'), accelerator="Ctrl+I")
        
        # Visual menu
        visual_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visual", menu=visual_menu)
        visual_menu.add_command(label="Scale Factor...", command=self.callbacks.get('show_scale_factor_dialog'))
        visual_menu.add_command(label="Direction Ratio...", command=self.callbacks.get('show_direction_ratio_dialog'))
        
        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_command(label="Browse Model...", command=self.callbacks.get('browse_ai_model'))
        ai_menu.add_separator()
        ai_menu.add_command(label="Model Info...", command=self.callbacks.get('show_ai_model_info'))
        ai_menu.add_command(label="Clear Model", command=self.callbacks.get('clear_ai_model'))
        ai_menu.add_separator()
        
        # K-Best submenu
        kbest_menu = tk.Menu(ai_menu, tearoff=0)
        ai_menu.add_cascade(label="K-Best", menu=kbest_menu)
        kbest_menu.add_command(label="Load K-Best...", command=self.callbacks.get('show_kbest_analysis'))
        kbest_menu.add_command(label="View Current Positions...", command=self.callbacks.get('show_current_kbest_positions'))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Controls...", command=self.callbacks.get('show_controls_dialog'))
        help_menu.add_separator()
        help_menu.add_command(label="About...", command=self.callbacks.get('show_about_dialog'))
    
    def bind_events(self):
        """Bind keyboard and other events"""
        if self.callbacks.get('on_frame_input'):
            self.frame_entry.bind('<Return>', self.callbacks.get('on_frame_input'))
        if self.callbacks.get('on_angular_velocity_input'):
            self.turn_entry.bind('<Return>', self.callbacks.get('on_angular_velocity_input'))
        if self.callbacks.get('on_linear_velocity_input'):
            self.linear_entry.bind('<Return>', self.callbacks.get('on_linear_velocity_input'))
        if self.callbacks.get('on_key_press'):
            self.root.bind('<KeyPress>', self.callbacks.get('on_key_press'))
            self.root.focus_set()
        
        # Keyboard shortcuts
        if self.callbacks.get('browse_data_file'):
            self.root.bind_all("<Control-o>", lambda e: self.callbacks.get('browse_data_file')())
        if self.callbacks.get('save_data'):
            self.root.bind_all("<Control-s>", lambda e: self.callbacks.get('save_data')())
        if self.callbacks.get('show_data_statistics'):
            self.root.bind_all("<Control-i>", lambda e: self.callbacks.get('show_data_statistics')())
    
    def update_canvas_size(self, new_size):
        """Update the canvas size"""
        try:
            self.current_canvas_size = new_size
            self.pygame_frame.configure(width=new_size, height=new_size)
            self.canvas.configure(width=new_size, height=new_size)
        except Exception as e:
            print(f"Error updating canvas size: {e}")
    
    def update_recent_files_menu(self, recent_files, load_recent_callback):
        """Update the recent files submenu"""
        if hasattr(self, 'recent_menu'):
            # Clear existing menu items
            self.recent_menu.delete(0, 'end')
            
            if recent_files:
                for i, file_path in enumerate(recent_files):
                    import os
                    display_name = f"{i+1}. {os.path.basename(file_path)}"
                    self.recent_menu.add_command(
                        label=display_name,
                        command=lambda fp=file_path: load_recent_callback(fp)
                    )
            else:
                self.recent_menu.add_command(label="(No recent files)", state='disabled')
