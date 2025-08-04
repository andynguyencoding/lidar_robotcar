"""
File management operations for the LiDAR Visualizer
"""

import os
from tkinter import filedialog, messagebox
from .config import MAX_RECENT_FILES, RECENT_FILES_FILENAME


class FileManager:
    """Handles file operations and recent files management"""
    
    def __init__(self):
        self.recent_files = []
        self.max_recent_files = MAX_RECENT_FILES
        self.recent_files_path = RECENT_FILES_FILENAME
        self.load_recent_files()
    
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
            
        except Exception as e:
            print(f"Error adding recent file: {e}")
    
    def browse_data_file(self, initial_dir="./data"):
        """Browse for a data file and return the selected filename"""
        import os
        
        # Ensure the initial directory exists, fallback to current directory if not
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
        
        return filename
    
    def get_recent_files(self):
        """Get the list of recent files"""
        return self.recent_files.copy()
    
    def file_exists(self, file_path):
        """Check if a file exists"""
        return os.path.exists(file_path)
    
    def get_basename(self, file_path):
        """Get the basename of a file path"""
        return os.path.basename(file_path)
