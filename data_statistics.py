"""
Data analysis and statistics functionality for the LiDAR Visualizer
"""

import os
import math
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from config import LIDAR_RESOLUTION


class DataAnalyzer:
    """Handles data analysis and statistics operations"""
    
    def __init__(self):
        pass
    
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
        """Analyze data file and return statistics"""
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
    
    def analyze_imputed_data(self, imputed_data):
        """Analyze imputed data and return statistics"""
        angular_velocities = []
        total_invalid_count = 0
        frames_with_invalid = 0
        total_frames = 0
        
        for line in imputed_data:
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
                print(f"Warning: Could not process line: {e}")
        
        return {
            'angular_velocities': angular_velocities,
            'total_invalid_count': total_invalid_count,
            'frames_with_invalid': frames_with_invalid,
            'total_frames': total_frames,
            'file_path': 'imputed_data',
            'has_headers': False
        }
    
    def analyze_imputed_data_from_list(self, imputed_data_list, has_headers=False):
        """Analyze imputed data from list and return statistics"""
        angular_velocities = []
        total_invalid_count = 0
        frames_with_invalid = 0
        total_frames = 0
        
        for line_num, line in enumerate(imputed_data_list):
            # Skip header if present
            if has_headers and line_num == 0:
                continue
                
            try:
                if len(line) == LIDAR_RESOLUTION + 1:  # 360 lidar + 1 turn value
                    total_frames += 1
                    
                    # Check for invalid data in lidar readings
                    invalid_in_frame = 0
                    for i in range(LIDAR_RESOLUTION):
                        try:
                            value = float(line[i])
                            if math.isinf(value) or math.isnan(value) or value == 0:
                                invalid_in_frame += 1
                        except (ValueError, TypeError):
                            invalid_in_frame += 1
                    
                    if invalid_in_frame > 0:
                        frames_with_invalid += 1
                        total_invalid_count += invalid_in_frame
                    
                    # Extract angular velocity (last column)
                    try:
                        ang_vel = float(line[360])
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
            'file_path': 'imputed_data_list',
            'has_headers': has_headers
        }
    
    def create_histogram(self, stats, parent_frame):
        """Create histogram for angular velocities"""
        try:
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(6, 4))
            
            if stats['angular_velocities']:
                ax.hist(stats['angular_velocities'], bins=50, alpha=0.7, color='blue', edgecolor='black')
                ax.set_xlabel('Angular Velocity')
                ax.set_ylabel('Frequency')
                ax.set_title('Angular Velocity Distribution')
                ax.grid(True, alpha=0.3)
                
                # Add statistics text
                mean_val = np.mean(stats['angular_velocities'])
                std_val = np.std(stats['angular_velocities'])
                min_val = np.min(stats['angular_velocities'])
                max_val = np.max(stats['angular_velocities'])
                
                stats_text = f'Mean: {mean_val:.3f}\nStd: {std_val:.3f}\nMin: {min_val:.3f}\nMax: {max_val:.3f}'
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            else:
                ax.text(0.5, 0.5, 'No valid angular velocity data', 
                       ha='center', va='center', transform=ax.transAxes)
            
            plt.tight_layout()
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
            return canvas
            
        except Exception as e:
            print(f"Error creating histogram: {e}")
            return None
    
    def update_histogram(self, canvas, stats):
        """Update existing histogram with new data"""
        try:
            if canvas and hasattr(canvas, 'figure'):
                # Clear and redraw
                canvas.figure.clear()
                ax = canvas.figure.add_subplot(111)
                
                if stats['angular_velocities']:
                    ax.hist(stats['angular_velocities'], bins=50, alpha=0.7, color='blue', edgecolor='black')
                    ax.set_xlabel('Angular Velocity')
                    ax.set_ylabel('Frequency')
                    ax.set_title('Angular Velocity Distribution')
                    ax.grid(True, alpha=0.3)
                    
                    # Add statistics text
                    mean_val = np.mean(stats['angular_velocities'])
                    std_val = np.std(stats['angular_velocities'])
                    min_val = np.min(stats['angular_velocities'])
                    max_val = np.max(stats['angular_velocities'])
                    
                    stats_text = f'Mean: {mean_val:.3f}\nStd: {std_val:.3f}\nMin: {min_val:.3f}\nMax: {max_val:.3f}'
                    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                else:
                    ax.text(0.5, 0.5, 'No valid angular velocity data', 
                           ha='center', va='center', transform=ax.transAxes)
                
                canvas.figure.tight_layout()
                canvas.draw()
                
            return True
            
        except Exception as e:
            print(f"Error updating histogram: {e}")
            return False
