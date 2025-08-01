"""
AI Model Integration Module for LiDAR Visualizer
Handles loading and prediction with machine learning models
"""

import os
import pickle
import numpy as np
from tkinter import messagebox
import traceback


class AIModelManager:
    def __init__(self):
        self.model = None
        self.model_path = None
        self.model_loaded = False
        self.prediction_cache = {}  # Cache predictions to avoid recomputation
        
    def load_model(self, model_path):
        """Load a machine learning model from a pickle file"""
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Clear previous model and cache
            self.clear_model()
            
            # Load the model
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            self.model_path = model_path
            self.model_loaded = True
            
            print(f"Successfully loaded AI model from: {model_path}")
            
            # Try to get model info if available
            model_info = self.get_model_info()
            print(f"Model info: {model_info}")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to load AI model: {str(e)}"
            print(f"Error loading model: {e}")
            print(traceback.format_exc())
            messagebox.showerror("Model Loading Error", error_msg)
            return False
    
    def clear_model(self):
        """Clear the loaded model and cache"""
        self.model = None
        self.model_path = None
        self.model_loaded = False
        self.prediction_cache.clear()
        print("AI model cleared")
    
    def get_model_info(self):
        """Get information about the loaded model"""
        if not self.model_loaded:
            return "No model loaded"
        
        try:
            # Try to get common model attributes
            info_parts = []
            
            # Model type
            model_type = type(self.model).__name__
            info_parts.append(f"Type: {model_type}")
            
            # Try to get feature count if available
            if hasattr(self.model, 'n_features_in_'):
                info_parts.append(f"Features: {self.model.n_features_in_}")
            elif hasattr(self.model, 'feature_importances_'):
                info_parts.append(f"Features: {len(self.model.feature_importances_)}")
            
            # Try to get classes if available (for classification)
            if hasattr(self.model, 'classes_'):
                info_parts.append(f"Classes: {len(self.model.classes_)}")
            
            # File info
            if self.model_path:
                file_size = os.path.getsize(self.model_path) / 1024  # KB
                info_parts.append(f"Size: {file_size:.1f} KB")
            
            return " | ".join(info_parts) if info_parts else f"Type: {model_type}"
            
        except Exception as e:
            return f"Type: {type(self.model).__name__} (info unavailable)"
    
    def is_model_loaded(self):
        """Check if a model is currently loaded"""
        return self.model_loaded and self.model is not None
    
    def predict_direction(self, lidar_data, frame_index=None):
        """
        Predict direction from LiDAR data
        
        Args:
            lidar_data: List/array of LiDAR distances (expected: 360 values)
            frame_index: Optional frame index for caching
        
        Returns:
            float: Predicted angular velocity/direction (-1.0 to 1.0 range expected)
        """
        if not self.is_model_loaded():
            return None
        
        try:
            # Check cache first if frame_index provided
            if frame_index is not None and frame_index in self.prediction_cache:
                return self.prediction_cache[frame_index]
            
            # Prepare input data
            input_data = self.prepare_input_data(lidar_data)
            
            # Make prediction
            prediction = self.model.predict([input_data])[0]
            
            # Ensure prediction is a scalar
            if hasattr(prediction, 'item'):
                prediction = prediction.item()
            elif isinstance(prediction, (list, np.ndarray)) and len(prediction) == 1:
                prediction = prediction[0]
            
            # Cache the prediction if frame_index provided
            if frame_index is not None:
                self.prediction_cache[frame_index] = prediction
            
            return float(prediction)
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            print(traceback.format_exc())
            return None
    
    def prepare_input_data(self, lidar_data):
        """
        Prepare LiDAR data for model input
        
        Args:
            lidar_data: Raw LiDAR data (list/array)
        
        Returns:
            numpy array: Prepared input data
        """
        try:
            # Import DECISIVE_FRAME_POSITIONS from the main module
            # These are the selected positions that the model was trained on
            DECISIVE_FRAME_POSITIONS = [24, 29, 31, 35, 38, 39, 40, 41, 42, 43, 44, 45, 47, 50, 54, 55, 57, 302,
                                      304, 312, 314, 315, 316, 318, 319, 321, 324, 326, 328, 330]
            
            # Convert to numpy array
            full_lidar = np.array(lidar_data, dtype=np.float32)
            
            # Extract only the decisive frame positions
            if len(full_lidar) >= 360:
                # Use only the decisive positions from the LiDAR data
                input_array = np.zeros(len(DECISIVE_FRAME_POSITIONS), dtype=np.float32)
                for i, pos in enumerate(DECISIVE_FRAME_POSITIONS):
                    if pos < len(full_lidar):
                        input_array[i] = full_lidar[pos]
                    else:
                        input_array[i] = 0.0  # Default value for missing positions
            else:
                # If insufficient data, create array with zeros
                input_array = np.zeros(len(DECISIVE_FRAME_POSITIONS), dtype=np.float32)
                # Fill what we can
                for i, pos in enumerate(DECISIVE_FRAME_POSITIONS):
                    if pos < len(lidar_data):
                        input_array[i] = lidar_data[pos]
            
            # Handle any invalid values
            input_array = np.nan_to_num(input_array, nan=0.0, posinf=1000.0, neginf=0.0)
            
            return input_array
            
        except Exception as e:
            print(f"Error preparing input data: {e}")
            # Return zeros as fallback - use the expected number of features
            DECISIVE_FRAME_POSITIONS = [24, 29, 31, 35, 38, 39, 40, 41, 42, 43, 44, 45, 47, 50, 54, 55, 57, 302,
                                      304, 312, 314, 315, 316, 318, 319, 321, 324, 326, 328, 330]
            return np.zeros(len(DECISIVE_FRAME_POSITIONS), dtype=np.float32)
    
    def get_model_path(self):
        """Get the path of the currently loaded model"""
        return self.model_path if self.model_loaded else None
    
    def clear_prediction_cache(self):
        """Clear the prediction cache"""
        self.prediction_cache.clear()
        print("Prediction cache cleared")


# Global instance for the visualizer to use
ai_model_manager = AIModelManager()


def load_ai_model(model_path):
    """Convenience function to load a model"""
    return ai_model_manager.load_model(model_path)


def get_ai_prediction(lidar_data, frame_index=None):
    """Convenience function to get a prediction"""
    return ai_model_manager.predict_direction(lidar_data, frame_index)


def is_ai_model_loaded():
    """Convenience function to check if model is loaded"""
    return ai_model_manager.is_model_loaded()


def get_ai_model_info():
    """Convenience function to get model info"""
    return ai_model_manager.get_model_info()


def clear_ai_model():
    """Convenience function to clear the model"""
    return ai_model_manager.clear_model()
