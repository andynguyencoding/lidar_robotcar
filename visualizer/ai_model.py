"""
AI Model Integration Module for LiDAR Visualizer
Handles loading, training, and prediction with machine learning models
"""

import os
import pickle
import numpy as np
from tkinter import messagebox
import traceback


class RegressionModelTrainer:
    """Handles training of regression models from dataset splits"""
    
    def __init__(self):
        self.progress_callback = None
        
    def set_progress_callback(self, callback):
        """Set callback function for progress updates"""
        self.progress_callback = callback
        
    def log_progress(self, message):
        """Log progress message"""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        try:
            import pandas as pd
            import numpy as np
            from sklearn.feature_selection import SelectKBest, f_regression
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.metrics import mean_squared_error, r2_score
            import pickle
            return True, None
        except ImportError as e:
            missing_package = str(e).split("'")[1] if "'" in str(e) else "required package"
            error_msg = (f"Missing required package: {missing_package}\n\n"
                        f"Please install the required packages:\n"
                        f"pip install pandas scikit-learn numpy")
            return False, error_msg
    
    def train_regression_model(self, train_data, val_data, models_dir="models"):
        """
        Train a Random Forest regression model using the exact logic from notebooks/randomforest_regression.ipynb
        
        Args:
            train_data: List of training data lines (list of strings)
            val_data: List of validation data lines (list of strings) 
            models_dir: Directory to save the trained model
            
        Returns:
            dict: Training results with model path, metrics, etc.
        """
        try:
            # Check dependencies
            deps_ok, error_msg = self.check_dependencies()
            if not deps_ok:
                return {"success": False, "error": error_msg}
            
            # Import required packages
            import pandas as pd
            import numpy as np
            from sklearn.feature_selection import SelectKBest, f_regression
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.metrics import mean_squared_error, r2_score
            import pickle
            from datetime import datetime
            
            self.log_progress("🚀 Starting model training process...")
            self.log_progress(f"📊 Dataset sizes: Train={len(train_data)}, Val={len(val_data)}")
            
            # Step 1: Prepare training data
            self.log_progress("📋 Step 1/6: Preparing training data...")
            train_df = self._prepare_dataframe(train_data, "training")
            if train_df is None or train_df.empty:
                return {"success": False, "error": "No valid training data found"}
            
            # Step 2: Prepare validation data  
            self.log_progress("📋 Step 2/6: Preparing validation data...")
            val_df = self._prepare_dataframe(val_data, "validation")
            if val_df is None or val_df.empty:
                return {"success": False, "error": "No valid validation data found"}
                
            self.log_progress(f"✅ Data prepared: {len(train_df)} training, {len(val_df)} validation samples")
            
            # Step 3: Data preprocessing (cleanup zero distances)
            self.log_progress("🔧 Step 3/6: Data preprocessing - cleaning zero distances...")
            self._cleanup_zero_distances(train_df)
            self._cleanup_zero_distances(val_df)
            self.log_progress("✅ Zero distance cleanup completed")
            
            # Step 4: Data augmentation
            self.log_progress("🔄 Step 4/6: Creating augmented data...")
            train_augmented = self._get_augmented_data(train_df)
            val_augmented = self._get_augmented_data(val_df)
            
            # Combine original and augmented data
            combined_train = pd.concat([train_df, train_augmented], ignore_index=True)
            combined_val = pd.concat([val_df, val_augmented], ignore_index=True)
            
            # Rename last column to 'Turn'
            combined_train.rename(columns={combined_train.columns[-1]: 'Turn'}, inplace=True)
            combined_val.rename(columns={combined_val.columns[-1]: 'Turn'}, inplace=True)
            
            self.log_progress(f"✅ Data augmentation completed: {len(combined_train)} training samples, {len(combined_val)} validation samples")
            
            # Prepare features and target
            X_train = combined_train.iloc[:, :-1]  # All columns except last
            y_train = combined_train.iloc[:, -1]   # Last column (Turn)
            X_val = combined_val.iloc[:, :-1]
            y_val = combined_val.iloc[:, -1]
            
            self.log_progress(f"📊 Feature matrix shapes: X_train={X_train.shape}, X_val={X_val.shape}")
            self.log_progress(f"📊 Target vector shapes: y_train={len(y_train)}, y_val={len(y_val)}")
            
            # Step 5: Feature selection and model training
            self.log_progress("🎯 Step 5/6: Feature selection and model training...")
            
            # Feature selection with K-best (k=30 as in notebook)
            k = 30
            k_best = SelectKBest(score_func=f_regression, k=k)
            k_best.fit(X_train, y_train)
            
            selected_feature_indices = k_best.get_support(indices=True)
            self.log_progress(f"✅ Selected {k} best features: {selected_feature_indices[:10]}..." + 
                           f" (showing first 10)")
            
            # Create and train Random Forest Regressor
            rf = RandomForestRegressor(n_estimators=200, random_state=42)
            rf.fit(X_train.iloc[:, selected_feature_indices], y_train)
            self.log_progress("✅ Random Forest model training completed")
            
            # Step 6: Model evaluation
            self.log_progress("📈 Step 6/6: Model evaluation...")
            
            # Make predictions on validation data
            y_val_pred = rf.predict(X_val.iloc[:, selected_feature_indices])
            
            # Calculate metrics
            mse = mean_squared_error(y_val, y_val_pred)
            r2 = r2_score(y_val, y_val_pred)
            
            self.log_progress(f"📊 Model Performance Metrics:")
            self.log_progress(f"   • Mean Squared Error: {mse:.6f}")
            self.log_progress(f"   • R-squared Score: {r2:.6f}")
            
            # Save the model
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_filename = f'lidar_regression_model_{timestamp}.pkl'
            model_path = os.path.join(models_dir, model_filename)
            
            # Save both the model and feature indices
            model_data = {
                'model': rf,
                'feature_indices': selected_feature_indices,
                'k_best_selector': k_best,
                'training_metrics': {
                    'mse': mse,
                    'r2_score': r2,
                    'n_estimators': 200,
                    'k_features': k
                }
            }
            
            with open(model_path, 'wb') as file:
                pickle.dump(model_data, file)
            
            self.log_progress(f"💾 Model saved successfully:")
            self.log_progress(f"   📁 Path: {model_path}")
            self.log_progress(f"   📊 Features: {k} selected from 360 LiDAR points")
            self.log_progress(f"   🌳 Trees: 200 Random Forest estimators")
            self.log_progress("")
            self.log_progress("🎉 Model training completed successfully!")
            self.log_progress("   You can now use this model for angular velocity prediction.")
            
            return {
                "success": True,
                "model_path": model_path,
                "metrics": {
                    "mse": mse,
                    "r2_score": r2
                },
                "model_data": model_data
            }
            
        except Exception as e:
            error_msg = f"Error during training: {str(e)}"
            self.log_progress(f"❌ {error_msg}")
            import traceback
            error_details = traceback.format_exc()
            self.log_progress(f"📋 Error details:\n{error_details}")
            return {"success": False, "error": error_msg, "details": error_details}
    
    def _prepare_dataframe(self, data_lines, dataset_name):
        """Convert data lines to pandas DataFrame"""
        try:
            import pandas as pd
            
            processed_data = []
            for line in data_lines:
                if isinstance(line, str):
                    line = line.strip()
                    data_parts = line.split(',')
                else:
                    data_parts = line
                
                if len(data_parts) >= 361:  # 360 lidar + 1 angular
                    processed_data.append([float(x) for x in data_parts[:361]])
            
            if not processed_data:
                self.log_progress(f"❌ No valid data found in {dataset_name} set")
                return None
                
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            self.log_progress(f"❌ Error preparing {dataset_name} dataframe: {str(e)}")
            return None
    
    def _cleanup_zero_distances(self, data):
        """Clean up zero distances using interpolation (from notebook)"""
        for i in range(data.shape[0]):
            for j in range(data.shape[1] - 1):  # skip the last column (Turn value)
                if data.iloc[i, j] == 0:
                    # get right side value
                    k = j
                    left_val = right_val = 0
                    while k < data.shape[1] - 1:
                        if data.iloc[i, k] > 0:
                            right_val = data.iloc[i, k]
                            break
                        k = k + 1
                    # get the left side value
                    left_val = right_val
                    k = j
                    while k >= 0:
                        if data.iloc[i, k] > 0:
                            left_val = data.iloc[i, k]
                            break
                        k = k - 1
                    data.iat[i, j] = (left_val + right_val) / 2
    
    def _get_augmented_data(self, data):
        """Create augmented data by flipping LiDAR readings (from notebook)"""
        import pandas as pd
        
        augmented_data = np.zeros(data.shape)
        for i in range(augmented_data.shape[0]):
            for j in range(augmented_data.shape[1]):
                if j < 360:  # LiDAR data
                    augmented_data[i, j] = data.iloc[i, 359 - j]
                else:  # Angular velocity (last column)
                    augmented_data[i, j] = round(0 - float(data.iloc[i, j]), 2)
        return pd.DataFrame(augmented_data)


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

# Global trainer instance
regression_trainer = RegressionModelTrainer()


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


def train_regression_model(train_data, val_data, models_dir="models", progress_callback=None):
    """
    Convenience function to train a regression model
    
    Args:
        train_data: List of training data lines
        val_data: List of validation data lines
        models_dir: Directory to save the model
        progress_callback: Callback function for progress updates
        
    Returns:
        dict: Training results
    """
    if progress_callback:
        regression_trainer.set_progress_callback(progress_callback)
    
    return regression_trainer.train_regression_model(train_data, val_data, models_dir)
