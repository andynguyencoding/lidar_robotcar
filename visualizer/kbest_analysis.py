#!/usr/bin/env python3
"""
K-Best Feature Selection for LiDAR Data Analysis

This module implements Scikit-learn's SelectKBest feature selection
to identify the most important LiDAR data points for machine learning models.
"""

import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.preprocessing import LabelEncoder
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
from .logger import info, debug, error, warning, log_function

def analyze_kbest_features(data_manager, k=30, score_func='f_classif'):
    """
    Analyze LiDAR data using SelectKBest to find most important features
    
    Args:
        data_manager: DataManager instance containing the data
        k: Number of best features to select
        score_func: Scoring function ('f_classif' or 'f_regression')
    
    Returns:
        dict: Analysis results containing best positions, scores, and statistics
    """
    info(f"Starting K-Best analysis with k={k}, score_func={score_func}", "KBest")
    try:
        # Collect all data points
        print(f"Starting K-Best analysis with k={k}, score_func={score_func}")
        
        X_data = []  # LiDAR features (360 values per frame)
        y_data = []  # Angular velocity labels
        
        # Reset data manager to beginning
        original_pointer = data_manager.pointer
        data_manager.first()
        
        frames_processed = 0
        max_frames = min(1000, len(data_manager.lines))  # Limit for performance
        
        while data_manager.has_next() and frames_processed < max_frames:
            try:
                distances = data_manager.dataframe
                if len(distances) == 361:  # 360 lidar + 1 angular velocity
                    # Extract LiDAR features (first 360 values)
                    lidar_features = distances[:360]
                    angular_velocity = distances[360]
                    
                    # Clean the data - replace invalid values
                    lidar_features = [
                        float(x) if str(x).replace('.', '').replace('-', '').isdigit() 
                        and str(x).lower() not in ['inf', 'nan', ''] 
                        and float(x) > 0 
                        else 1000.0  # Default safe distance
                        for x in lidar_features
                    ]
                    
                    # Validate angular velocity
                    if str(angular_velocity).replace('.', '').replace('-', '').isdigit():
                        X_data.append(lidar_features)
                        y_data.append(float(angular_velocity))
                        frames_processed += 1
                
                data_manager.next()
                
            except Exception as e:
                print(f"Error processing frame {frames_processed}: {e}")
                data_manager.next()
                continue
        
        # Restore original position
        data_manager._pointer = original_pointer
        data_manager._read_pos = original_pointer - 1
        
        if len(X_data) < 10:
            raise ValueError(f"Insufficient valid data for analysis. Only {len(X_data)} frames processed.")
        
        print(f"Processed {len(X_data)} frames for K-Best analysis")
        
        # Convert to numpy arrays
        X = np.array(X_data, dtype=np.float32)
        y = np.array(y_data, dtype=np.float32)
        
        print(f"Data shape: X={X.shape}, y={y.shape}")
        
        # Select scoring function
        if score_func == 'f_classif':
            # For classification, we need to discretize the continuous angular velocity
            # Create bins for angular velocity classes
            y_binned = np.digitize(y, bins=np.linspace(y.min(), y.max(), 10))
            scoring_func = f_classif
            target = y_binned
        else:
            scoring_func = f_regression
            target = y
        
        # Apply SelectKBest
        k_best = SelectKBest(score_func=scoring_func, k=k)
        X_selected = k_best.fit_transform(X, target)
        
        # Get selected feature indices (these are the LiDAR positions)
        selected_indices = k_best.get_support(indices=True)
        feature_scores = k_best.scores_
        
        print(f"Selected {len(selected_indices)} features")
        print(f"Best positions: {list(selected_indices)}")
        
        # Calculate statistics
        results = {
            'best_positions': list(selected_indices),
            'feature_scores': feature_scores,
            'selected_scores': feature_scores[selected_indices],
            'frames_analyzed': len(X_data),
            'k_value': k,
            'score_function': score_func,
            'angular_velocity_range': (float(y.min()), float(y.max())),
            'angular_velocity_std': float(y.std()),
            'score_range': (float(feature_scores.min()), float(feature_scores.max())),
            'selected_score_mean': float(feature_scores[selected_indices].mean()),
            'analysis_summary': {
                'total_features': len(feature_scores),
                'selected_features': len(selected_indices),
                'selection_ratio': len(selected_indices) / len(feature_scores),
                'top_score': float(feature_scores.max()),
                'selected_top_score': float(feature_scores[selected_indices].max())
            }
        }
        
        return results
        
    except Exception as e:
        print(f"Error in K-Best analysis: {e}")
        print(traceback.format_exc())
        raise


def update_decisive_frame_positions(best_positions):
    """
    Update the global DECISIVE_FRAME_POSITIONS with new K-Best results
    
    Args:
        best_positions: List of best feature positions from K-Best analysis
    """
    try:
        import config
        
        # Update the config module
        config.DECISIVE_FRAME_POSITIONS = list(best_positions)
        
        # Also update in other modules that might have imported it
        try:
            import visualization_renderer
            visualization_renderer.DECISIVE_FRAME_POSITIONS = list(best_positions)
        except:
            pass
            
        try:
            import visualizer
            visualizer.DECISIVE_FRAME_POSITIONS = list(best_positions)
        except:
            pass
            
        try:
            from . import ai_model
            # The ai_model module has hardcoded values, but they get overridden by config
        except:
            pass
        
        print(f"Updated DECISIVE_FRAME_POSITIONS with {len(best_positions)} positions")
        return True
        
    except Exception as e:
        print(f"Error updating DECISIVE_FRAME_POSITIONS: {e}")
        return False


class KBestAnalysisDialog:
    """Dialog for configuring and running K-Best analysis"""
    
    def __init__(self, parent, data_manager, callback=None):
        self.parent = parent
        self.data_manager = data_manager
        self.callback = callback
        self.results = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("K-Best Feature Analysis")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="K-Best Feature Selection Analysis", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Description
        desc_text = """This analysis uses Scikit-learn's SelectKBest to identify the most important 
LiDAR data points for machine learning models. The selected positions will be 
highlighted in the visualization and used for AI model training."""
        
        desc_label = ttk.Label(main_frame, text=desc_text, wraplength=550, justify='left')
        desc_label.pack(pady=(0, 15))
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Analysis Configuration", padding=10)
        config_frame.pack(fill='x', pady=(0, 15))
        
        # K value selection
        ttk.Label(config_frame, text="Number of features to select (k):").pack(anchor='w')
        self.k_var = tk.IntVar(value=30)
        k_frame = ttk.Frame(config_frame)
        k_frame.pack(fill='x', pady=(5, 10))
        
        self.k_scale = tk.Scale(k_frame, from_=10, to=100, orient='horizontal', 
                               variable=self.k_var, length=300)
        self.k_scale.pack(side='left')
        
        self.k_label = ttk.Label(k_frame, text="30 features")
        self.k_label.pack(side='left', padx=(10, 0))
        
        self.k_var.trace('w', self.update_k_label)
        
        # Score function selection
        ttk.Label(config_frame, text="Scoring function:").pack(anchor='w', pady=(10, 5))
        self.score_func_var = tk.StringVar(value='f_classif')
        
        score_frame = ttk.Frame(config_frame)
        score_frame.pack(fill='x')
        
        ttk.Radiobutton(score_frame, text="F-Classification (discrete classes)", 
                       variable=self.score_func_var, value='f_classif').pack(anchor='w')
        ttk.Radiobutton(score_frame, text="F-Regression (continuous values)", 
                       variable=self.score_func_var, value='f_regression').pack(anchor='w')
        
        # Results frame
        self.results_frame = ttk.LabelFrame(main_frame, text="Analysis Results", padding=10)
        self.results_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Results text widget with scrollbar
        text_frame = ttk.Frame(self.results_frame)
        text_frame.pack(fill='both', expand=True)
        
        self.results_text = tk.Text(text_frame, height=12, wrap='word', state='disabled')
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="Run Analysis", 
                  command=self.run_analysis).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Apply Results", 
                  command=self.apply_results).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Close", 
                  command=self.close_dialog).pack(side='right')
        
        # Initially disable Apply button
        self.apply_button = button_frame.winfo_children()[1]
        self.apply_button.configure(state='disabled')
        
    def update_k_label(self, *args):
        """Update the k value label"""
        k_value = self.k_var.get()
        self.k_label.configure(text=f"{k_value} features")
        
    def run_analysis(self):
        """Run the K-Best analysis"""
        try:
            # Update status
            self.results_text.configure(state='normal')
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Running K-Best analysis...\n\n")
            self.results_text.configure(state='disabled')
            self.dialog.update()
            
            # Run analysis
            k = self.k_var.get()
            score_func = self.score_func_var.get()
            
            self.results = analyze_kbest_features(self.data_manager, k, score_func)
            
            # Display results
            self.display_results()
            
            # Enable Apply button
            self.apply_button.configure(state='normal')
            
        except Exception as e:
            error_msg = f"Error during K-Best analysis: {str(e)}"
            messagebox.showerror("Analysis Error", error_msg)
            print(f"K-Best analysis error: {e}")
            print(traceback.format_exc())
            
    def display_results(self):
        """Display analysis results in the text widget"""
        if not self.results:
            return
            
        self.results_text.configure(state='normal')
        self.results_text.delete(1.0, tk.END)
        
        # Format results
        text = f"""K-Best Feature Selection Results
{'=' * 40}

Analysis Configuration:
• Number of features selected (k): {self.results['k_value']}
• Scoring function: {self.results['score_function']}
• Frames analyzed: {self.results['frames_analyzed']}

Data Statistics:
• Angular velocity range: {self.results['angular_velocity_range'][0]:.3f} to {self.results['angular_velocity_range'][1]:.3f}
• Angular velocity std dev: {self.results['angular_velocity_std']:.3f}
• Feature score range: {self.results['score_range'][0]:.3f} to {self.results['score_range'][1]:.3f}

Selection Results:
• Total LiDAR positions: {self.results['analysis_summary']['total_features']}
• Selected positions: {self.results['analysis_summary']['selected_features']}
• Selection ratio: {self.results['analysis_summary']['selection_ratio']:.1%}
• Average score of selected features: {self.results['selected_score_mean']:.3f}
• Top score overall: {self.results['analysis_summary']['top_score']:.3f}
• Top score in selection: {self.results['analysis_summary']['selected_top_score']:.3f}

Best LiDAR Positions:
{', '.join(map(str, sorted(self.results['best_positions'])))}

Top 10 Positions by Score:
"""
        
        # Add top 10 positions with scores
        positions_with_scores = list(zip(self.results['best_positions'], 
                                       self.results['selected_scores']))
        positions_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (pos, score) in enumerate(positions_with_scores[:10]):
            text += f"{i+1:2d}. Position {pos:3d}: Score {score:.3f}\n"
            
        text += f"\nNote: These positions will replace the current DECISIVE_FRAME_POSITIONS\nand be highlighted in the visualization with magenta lines and red circles."
        
        self.results_text.insert(tk.END, text)
        self.results_text.configure(state='disabled')
        
    def apply_results(self):
        """Apply the analysis results by updating DECISIVE_FRAME_POSITIONS"""
        if not self.results:
            messagebox.showwarning("No Results", "Please run the analysis first.")
            return
            
        try:
            # Update DECISIVE_FRAME_POSITIONS
            success = update_decisive_frame_positions(self.results['best_positions'])
            
            if success:
                messagebox.showinfo("Success", 
                    f"Successfully updated DECISIVE_FRAME_POSITIONS with {len(self.results['best_positions'])} positions.\n\n"
                    f"The visualization will now highlight these positions as the most important features for machine learning.")
                
                # Call callback if provided (to refresh visualization)
                if self.callback:
                    self.callback()
                    
                self.close_dialog()
            else:
                messagebox.showerror("Error", "Failed to update DECISIVE_FRAME_POSITIONS.")
                
        except Exception as e:
            error_msg = f"Error applying results: {str(e)}"
            messagebox.showerror("Error", error_msg)
            print(f"Error applying K-Best results: {e}")
            
    def close_dialog(self):
        """Close the dialog"""
        self.dialog.grab_release()
        self.dialog.destroy()


def show_kbest_analysis_dialog(parent, data_manager, callback=None):
    """
    Show the K-Best analysis dialog
    
    Args:
        parent: Parent tkinter window
        data_manager: DataManager instance
        callback: Optional callback function to call after applying results
    """
    try:
        dialog = KBestAnalysisDialog(parent, data_manager, callback)
        return dialog
    except Exception as e:
        error_msg = f"Error opening K-Best analysis dialog: {str(e)}"
        messagebox.showerror("Error", error_msg)
        print(f"Error opening K-Best dialog: {e}")
        return None
