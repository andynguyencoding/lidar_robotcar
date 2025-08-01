"""
Test script for AI model integration
Tests loading and prediction functionality
"""

import sys
import os
import numpy as np

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_model import ai_model_manager, load_ai_model, get_ai_prediction, is_ai_model_loaded

def test_ai_model():
    """Test the AI model functionality"""
    print("Testing AI Model Integration")
    print("=" * 40)
    
    # Test 1: Check initial state
    print("1. Testing initial state...")
    print(f"   Model loaded: {is_ai_model_loaded()}")
    assert not is_ai_model_loaded(), "Model should not be loaded initially"
    print("   ✓ Initial state correct")
    
    # Test 2: Try to load the existing model
    model_path = "./notebooks/self_driving_model_0.2.pkl"
    if os.path.exists(model_path):
        print(f"2. Testing model loading from: {model_path}")
        success = load_ai_model(model_path)
        print(f"   Load success: {success}")
        print(f"   Model loaded: {is_ai_model_loaded()}")
        
        if success:
            print("   ✓ Model loaded successfully")
            
            # Test 3: Get model info
            print("3. Testing model info...")
            from ai_model import get_ai_model_info
            info = get_ai_model_info()
            print(f"   Model info: {info}")
            print("   ✓ Model info retrieved")
            
            # Test 4: Test prediction with dummy data
            print("4. Testing prediction...")
            # Create dummy LiDAR data (360 distance values)
            dummy_lidar = np.random.uniform(100, 500, 360).tolist()
            
            prediction = get_ai_prediction(dummy_lidar, frame_index=0)
            print(f"   Prediction: {prediction}")
            print(f"   Prediction type: {type(prediction)}")
            
            if prediction is not None:
                print("   ✓ Prediction successful")
                print(f"   Prediction value: {prediction:.4f}")
            else:
                print("   ⚠ Prediction returned None")
            
            # Test 5: Test prediction caching
            print("5. Testing prediction caching...")
            prediction2 = get_ai_prediction(dummy_lidar, frame_index=0)  # Same frame index
            print(f"   Cached prediction: {prediction2}")
            
            if prediction == prediction2:
                print("   ✓ Caching works correctly")
            else:
                print("   ⚠ Caching issue detected")
            
            # Test 6: Clear model
            print("6. Testing model clearing...")
            ai_model_manager.clear_model()
            print(f"   Model loaded after clear: {is_ai_model_loaded()}")
            assert not is_ai_model_loaded(), "Model should be cleared"
            print("   ✓ Model cleared successfully")
            
        else:
            print("   ✗ Failed to load model")
            return False
    else:
        print(f"2. Model file not found: {model_path}")
        print("   Creating a dummy model for testing...")
        
        # Create a simple dummy model for testing
        class DummyModel:
            def predict(self, X):
                # Return a simple prediction based on input
                return [np.mean(X[0]) / 1000.0]  # Normalize to reasonable range
        
        # Test with dummy model
        print("3. Testing with dummy model...")
        ai_model_manager.model = DummyModel()
        ai_model_manager.model_loaded = True
        ai_model_manager.model_path = "dummy_model"
        
        dummy_lidar = np.random.uniform(100, 500, 360).tolist()
        prediction = get_ai_prediction(dummy_lidar)
        print(f"   Dummy prediction: {prediction}")
        
        if prediction is not None:
            print("   ✓ Dummy model prediction successful")
        else:
            print("   ✗ Dummy model prediction failed")
    
    print("\n" + "=" * 40)
    print("AI Model Integration Test Complete!")
    return True

if __name__ == "__main__":
    try:
        test_ai_model()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
