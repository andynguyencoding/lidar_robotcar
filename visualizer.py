import pygame
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
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


class StartupConfigWindow:
    def __init__(self, preset_data_file=None):
        self.root = tk.Tk()
        self.root.title("Lidar Visualizer Configuration")
        
        # Handle preset data file from command line argument
        self.preset_data_file = preset_data_file
        if preset_data_file:
            self.data_file = tk.StringVar(value=preset_data_file)
            # Make window taller when showing preset data info
            window_height = 450
        else:
            self.data_file = tk.StringVar(value='data/run1/out1.txt')
            window_height = 400
        
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
            ttk.Radiobutton(file_frame, text="Local data (data/run1/out1.txt)", 
                           variable=self.selected_file_type, value='local').pack(anchor='w', pady=1)
            
            # Browse option with button
            browse_frame = ttk.Frame(file_frame)
            browse_frame.pack(fill='x', pady=1)
            
            ttk.Radiobutton(browse_frame, text="Browse for file:", 
                           variable=self.selected_file_type, value='browse').pack(side='left')
            
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
    # Default to local data file, but allow external file specification
    if data_file is None:
        data_file = 'data/run1/out1.txt'
    
    data_manager = DataManager(data_file, 'data/run2/_out.txt', False)
    
    # Auto-calculate optimal scale factor based on the data
    calculate_scale_factor(data_manager)
    pygame.init()
    clock = pygame.time.Clock()
    # Set up the drawing window
    screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_WIDTH])
    # Set up the font
    font = pygame.font.Font(None, 32)
    # FONT = pygame.font.Font(None, 32)

    input_box1 = InputBox(350, 650, 140, 32, font)
    input_box2 = InputBox(350, 700, 140, 32, font)
    input_boxes = [input_box1, input_box2]
    input_box1.add_observer(data_manager)

    running = True
    paused = False
    inspect_mode = inspection_mode  # Use the configuration from startup window
    augmented_mode = show_augmented  # Flag to show augmented (mirrored) data instead of real data
    distances = []

    while data_manager.has_next():
        if inspect_mode:
            paused = True
        # Did the user click the window close button?
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    # print('PAUSE STATUS: {}'.format(paused))
                elif event.key == pygame.K_i:
                    """
                    Press 'i' keyboard will turn on inspection mode,
                    which run frame by frame
                    """
                    inspect_mode = not inspect_mode
                    # print('INSPECT MODE: {}'.format(inspect_mode))
                elif event.key == pygame.K_a:
                    """
                    Press 'a' keyboard will toggle augmented data display,
                    which shows mirrored lidar data for data augmentation
                    """
                    augmented_mode = not augmented_mode
                    print(f'AUGMENTED MODE: {augmented_mode}')
                elif event.key == pygame.K_q:
                    running = False
            elif event.type == pygame.QUIT:
                # Press 'X' button on window will close the program
                running = False

            # handle input box event
            for box in input_boxes:
                box.handle_event(event)

        if not running:
            break
        if data_manager.read_pos < data_manager.pointer:
            distances = data_manager.dataframe
        if len(distances) == LIDAR_RESOLUTION + 1:  # One more column, the last column contain TURN value
            # Fill the background with white
            screen.fill((250, 250, 250))

            for x in range(LIDAR_RESOLUTION):
                # depend on the average distance, divide distance with a constant for better view
                # provide zoom in/out effect using scale_factor
                try:
                    distance_value = float(distances[x])
                    # Skip invalid data points (inf, nan)
                    if math.isinf(distance_value) or math.isnan(distance_value):
                        continue  # Skip this data point and move to the next one
                except (ValueError, TypeError):
                    # Skip non-numeric values (like 'lidar_0', headers, etc.)
                    continue
                a = distance_value * SCALE_FACTOR

                # Choose coordinates based on augmented mode
                if augmented_mode:
                    # Augmented data: mirror horizontally (flip Y coordinate for data augmentation)
                    x_coord = math.cos(x / 180 * math.pi) * a + SCREEN_WIDTH / 2
                    y_coord = math.sin(x / 180 * math.pi) * a + SCREEN_WIDTH / 2
                else:
                    # Real data: use correct coordinate system for Gazebo lidar data
                    x_coord = math.cos(x / 180 * math.pi) * a + SCREEN_WIDTH / 2
                    y_coord = -math.sin(x / 180 * math.pi) * a + SCREEN_WIDTH / 2

                if x in DECISIVE_FRAME_POSITIONS and highlight_frames:
                    # draw line to the point
                    pygame.draw.line(screen, (255, 0, 255), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2),
                                     (x_coord, y_coord), 2)

                    # Draw the important point with RED color
                    pygame.draw.circle(screen, (255, 0, 0), (x_coord, y_coord), 3)
                else:
                    # Draw the ordinary point with BLACK color
                    pygame.draw.circle(screen, (0, 0, 0), (x_coord, y_coord), 2)


            # draw input boxes on screen
            if not input_box1.active:
                input_box1.set_text(distances[360])
            for box in input_boxes:
                box.update()
            for box in input_boxes:
                box.draw(screen)

            # Render the text - handle non-numeric turn values
            try:
                turn_value = float(distances[360])
                # Show different turn value based on mode
                display_turn = -turn_value if augmented_mode else turn_value
                mode_text = "AUGMENTED" if augmented_mode else "REAL"
                text = font.render("line: {}, turn: {:.2f} [{}]".format(
                    data_manager.read_pos, display_turn, mode_text), True, (0, 255, 255))
            except (ValueError, TypeError):
                # Handle non-numeric turn values (like headers)
                mode_text = "AUGMENTED" if augmented_mode else "REAL"
                text = font.render("line: {}, turn: {} [{}]".format(
                    data_manager.read_pos, distances[360], mode_text), True, (0, 255, 255))
            # Blit the text to the screen
            screen.blit(text, (350, 600))

            # draw the car
            pygame.draw.circle(screen, (252, 132, 3), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2), 12)
            pygame.draw.line(screen, (0, 0, 255), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2),
                             (SCREEN_WIDTH / 2 + 40, SCREEN_WIDTH / 2), 3)
            # Use convention: Full LEFT/RIGHT TURN = 45 degree (Pi/4)
            try:
                turn_value = float(distances[360])
                # Flip turn value for augmented data (mirror steering)
                if augmented_mode:
                    turn_value = -turn_value
                x = math.cos(turn_value * math.pi / 4) * 40
                y = math.sin(turn_value * math.pi / 4) * 40
                pygame.draw.line(screen, (0, 255, 0), (SCREEN_WIDTH / 2, SCREEN_WIDTH / 2),
                                 (SCREEN_WIDTH / 2 + x, SCREEN_WIDTH / 2 + y), 3)
            except (ValueError, TypeError):
                # Skip drawing turn direction for non-numeric values
                pass
            # Flip the display - swaps back buffer to front buffer to make all drawings visible
            # This is standard pygame double buffering, not related to data orientation
            pygame.display.flip()
            clock.tick(10)

            if not paused:  # Moving to the next lidar scan cycle
                print('Not Paused')
                # write current line to file
                data_manager.write_line()
                # move to the next lidar data frame
                data_manager.next()
                # reset input value
                input_box1.value = ''

    pygame.quit()


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
    
    # Try GUI first if display is available
    if display_available:
        try:
            print("Initializing configuration window...")
            # Show startup configuration window (with preset data file if provided)
            config_window = StartupConfigWindow(preset_data_file)
            print("Configuration window created, waiting for user input...")
            
            # Check if window actually got created and is visible
            import time
            time.sleep(0.5)  # Give window time to appear
            
            config = config_window.get_config()
            
            if config is None:
                print("Configuration cancelled or window closed. Using console fallback...")
                raise Exception("GUI configuration failed")
            
            # Process concatenation if requested
            if config['concatenate_data']:
                success = concatenate_augmented_data(config['data_file'])
                if not success:
                    print("Failed to concatenate data. Exiting...")
                    sys.exit(1)
            
            # Start visualizer with selected configuration
            print(f"Starting visualizer with configuration:")
            print(f"  Data file: {config['data_file']}")
            print(f"  Inspection mode: {config['inspection_mode']}")
            print(f"  Augmented mode: {config['augmented_mode']}")
            print(f"  Data concatenated: {config['concatenate_data']}")
            
            run(
                data_file=config['data_file'],
                highlight_frames=True,
                show_augmented=config['augmented_mode'],
                inspection_mode=config['inspection_mode']
            )
        except Exception as e:
            print(f"Error with configuration window: {e}")
            display_available = False
    
    # Use console fallback if GUI failed or no display
    if not display_available:
        print("Using console configuration...")
        # Console-based fallback configuration with preset data file
        config = console_config(preset_data_file)
        if config:
            run(
                data_file=config['data_file'],
                highlight_frames=True,
                show_augmented=config['augmented_mode'],
                inspection_mode=config['inspection_mode']
            )
        else:
            # Use command line argument or default
            data_file = preset_data_file if preset_data_file else 'data/run1/out1.txt'
            print(f"Using default configuration with data file: {data_file}")
            run(data_file, True)
