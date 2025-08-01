"""
Startup configuration window for the LiDAR Visualizer
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from data_statistics import DataAnalyzer


class StartupConfigWindow:
    """Startup configuration window for setting up the visualizer"""
    
    def __init__(self, preset_data_file=None):
        self.root = tk.Tk()
        self.root.title("Lidar Visualizer Configuration")
        
        # Data analyzer for statistics
        self.data_analyzer = DataAnalyzer()
        
        # Handle preset data file from command line argument
        self.preset_data_file = preset_data_file
        if preset_data_file:
            self.data_file = tk.StringVar(value=preset_data_file)
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
        self.selected_file_type = tk.StringVar(value='local')
        self.browsed_file_path = tk.StringVar(value="")
        self.data_loaded = False
        
        self.config_selected = False
        
        self.setup_ui()
        
        # Handle window close button (X)
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Force window to appear
        self.root.focus_force()
    
    def setup_ui(self):
        """Setup the startup configuration UI"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🚗 LiDAR Robot Car Visualizer", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Data file selection
        data_frame = ttk.LabelFrame(main_frame, text="Data File Selection", padding="10")
        data_frame.pack(fill='x', pady=(0, 15))
        
        # If preset data file provided, show info about it
        if self.preset_data_file:
            preset_info_frame = ttk.Frame(data_frame)
            preset_info_frame.pack(fill='x', pady=(0, 10))
            
            ttk.Label(preset_info_frame, text="📁 Preset Data File:", 
                     font=('Arial', 9, 'bold')).pack(anchor='w')
            ttk.Label(preset_info_frame, text=self.preset_data_file, 
                     font=('Courier', 8), foreground='darkblue', 
                     wraplength=450).pack(anchor='w', padx=(10, 0))
            
            # Show preset data file info
            preset_info_button = ttk.Button(preset_info_frame, text="📊 Analyze Preset Data", 
                                          command=self.analyze_preset_data)
            preset_info_button.pack(anchor='w', pady=(5, 0))
        
        # File type selection
        ttk.Radiobutton(data_frame, text="Use local default file (data/run1/out1.txt)", 
                       variable=self.selected_file_type, value='local').pack(anchor='w', pady=2)
        
        ttk.Radiobutton(data_frame, text="Browse for data file...", 
                       variable=self.selected_file_type, value='browse').pack(anchor='w', pady=2)
        
        if self.preset_data_file:
            ttk.Radiobutton(data_frame, text=f"Use preset: {os.path.basename(self.preset_data_file)}", 
                           variable=self.selected_file_type, value='preset').pack(anchor='w', pady=2)
            # Set preset as default selection
            self.selected_file_type.set('preset')
        
        # Browse file display
        self.browse_frame = ttk.Frame(data_frame)
        self.browse_frame.pack(fill='x', pady=(5, 0))
        
        self.browse_button = ttk.Button(self.browse_frame, text="Browse Files...", 
                                       command=self.browse_file)
        self.browse_button.pack(side='left')
        
        self.browse_label = ttk.Label(self.browse_frame, text="No file selected", 
                                     font=('Courier', 8), foreground='gray')
        self.browse_label.pack(side='left', padx=(10, 0))
        
        # Configuration options
        config_frame = ttk.LabelFrame(main_frame, text="Visualization Options", padding="10")
        config_frame.pack(fill='x', pady=(0, 15))
        
        # Inspection mode (changed default to True)
        ttk.Checkbutton(config_frame, text="Start in Inspection Mode (recommended)", 
                       variable=self.inspection_mode).pack(anchor='w', pady=2)
        
        ttk.Checkbutton(config_frame, text="Enable Augmented Data Mode", 
                       variable=self.augmented_mode).pack(anchor='w', pady=2)
        
        # Data preprocessing option
        preprocess_frame = ttk.LabelFrame(main_frame, text="Data Preprocessing (Optional)", padding="10")
        preprocess_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Checkbutton(preprocess_frame, text="Concatenate with augmented data (experimental)", 
                       variable=self.concatenate_data).pack(anchor='w', pady=2)
        
        concatenate_info = ttk.Label(preprocess_frame, 
                                   text="⚠️ This will combine original data with augmented versions for training",
                                   font=('Arial', 8), foreground='orange', wraplength=450)
        concatenate_info.pack(anchor='w', pady=(0, 2))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="🚀 Start Visualizer", 
                  command=self.start_visualizer, 
                  style='Accent.TButton').pack(side='right', padx=(5, 0))
        
        ttk.Button(button_frame, text="❌ Cancel", 
                  command=self.cancel).pack(side='right')
        
        ttk.Button(button_frame, text="📊 Analyze Data Quality", 
                  command=self.analyze_current_data).pack(side='left')
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to configure visualizer")
        ttk.Label(status_frame, textvariable=self.status_var, 
                 font=('Arial', 8), foreground='blue').pack(anchor='w')
    
    def browse_file(self):
        """Browse for a data file"""
        file_types = [
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select LiDAR Data File",
            filetypes=file_types,
            initialdir="data"
        )
        
        if filename:
            self.browsed_file_path.set(filename)
            self.browse_label.config(text=os.path.basename(filename), foreground='darkgreen')
            self.selected_file_type.set('browse')
            self.status_var.set(f"Selected: {filename}")
    
    def get_selected_data_file(self):
        """Get the currently selected data file path"""
        file_type = self.selected_file_type.get()
        
        if file_type == 'local':
            return 'data/run1/out1.txt'
        elif file_type == 'browse':
            return self.browsed_file_path.get()
        elif file_type == 'preset' and self.preset_data_file:
            return self.preset_data_file
        else:
            return 'data/run1/out1.txt'
    
    def analyze_current_data(self):
        """Analyze the currently selected data file"""
        try:
            data_file = self.get_selected_data_file()
            
            if not data_file or not os.path.exists(data_file):
                messagebox.showerror("Error", f"Data file not found: {data_file}")
                return
            
            self.status_var.set("Analyzing data...")
            self.root.update()
            
            # Analyze the data file
            stats = self.data_analyzer.analyze_data_file(data_file)
            
            # Show statistics popup
            self.display_data_statistics(stats, data_file)
            
            self.status_var.set("Data analysis complete")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze data: {str(e)}")
            self.status_var.set("Error analyzing data")
    
    def analyze_preset_data(self):
        """Analyze the preset data file"""
        if self.preset_data_file:
            try:
                self.status_var.set("Analyzing preset data...")
                self.root.update()
                
                stats = self.data_analyzer.analyze_data_file(self.preset_data_file)
                self.display_data_statistics(stats, self.preset_data_file)
                
                self.status_var.set("Preset data analysis complete")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to analyze preset data: {str(e)}")
                self.status_var.set("Error analyzing preset data")
    
    def display_data_statistics(self, stats, data_file):
        """Display data statistics in a popup window"""
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"Data Statistics - {os.path.basename(data_file)}")
        popup.geometry("600x400")
        popup.resizable(True, True)
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (600 // 2)
        y = (popup.winfo_screenheight() // 2) - (400 // 2)
        popup.geometry(f"600x400+{x}+{y}")
        
        # Make popup modal
        popup.transient(self.root)
        popup.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Statistics text
        stats_frame = ttk.LabelFrame(main_frame, text="Data Quality", padding=10)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        stats_text = f"""File: {os.path.basename(data_file)}
Total Frames: {stats['total_frames']}
Frames with Invalid Data: {stats['frames_with_invalid']} ({stats['frames_with_invalid']/max(stats['total_frames'], 1)*100:.1f}%)
Total Invalid Data Points: {stats['total_invalid_count']}
Valid Angular Velocity Values: {len(stats['angular_velocities'])}
File has Headers: {'Yes' if stats['has_headers'] else 'No'}"""
        
        ttk.Label(stats_frame, text=stats_text, font=('Courier', 9), justify='left').pack(anchor='w')
        
        # Angular velocity statistics
        if stats['angular_velocities']:
            import numpy as np
            vel_stats = f"""
Angular Velocity Statistics:
  Mean: {np.mean(stats['angular_velocities']):.3f}
  Std Dev: {np.std(stats['angular_velocities']):.3f}
  Min: {np.min(stats['angular_velocities']):.3f}
  Max: {np.max(stats['angular_velocities']):.3f}"""
            
            vel_frame = ttk.LabelFrame(main_frame, text="Angular Velocity", padding=10)
            vel_frame.pack(fill='x', pady=(0, 10))
            
            ttk.Label(vel_frame, text=vel_stats, font=('Courier', 9), justify='left').pack(anchor='w')
        
        # Close button
        ttk.Button(main_frame, text="Close", command=popup.destroy).pack(pady=10)
    
    def start_visualizer(self):
        """Start the visualizer with selected configuration"""
        try:
            data_file = self.get_selected_data_file()
            
            # Validate file exists
            if not os.path.exists(data_file):
                messagebox.showerror("Error", f"Data file not found: {data_file}")
                return
            
            # Validate file type selection for browse mode
            if self.selected_file_type.get() == 'browse' and not self.browsed_file_path.get():
                messagebox.showerror("Error", "Please select a file to browse or choose a different option")
                return
            
            self.config_selected = True
            self.root.quit()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start visualizer: {str(e)}")
    
    def cancel(self):
        """Cancel the configuration"""
        self.config_selected = False
        self.root.quit()
    
    def run(self):
        """Run the startup configuration window"""
        try:
            self.root.mainloop()
            self.root.destroy()
            
            if self.config_selected:
                return {
                    'data_file': self.get_selected_data_file(),
                    'inspection_mode': self.inspection_mode.get(),
                    'augmented_mode': self.augmented_mode.get(),
                    'concatenate_data': self.concatenate_data.get()
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error in startup configuration: {e}")
            return None
