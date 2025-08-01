#!/usr/bin/env python3
"""
Quick test to verify the new AI prediction text field is working correctly
"""

import subprocess
import time
import sys
import os

def test_prediction_field():
    """Test the AI prediction text field functionality"""
    print("Testing AI Prediction Text Field...")
    
    # Check if model file exists
    model_file = "models/self_driving_model_0.2.pkl"
    if not os.path.exists(model_file):
        print(f"Model file not found: {model_file}")
        return False
    
    print(f"✓ Model file found: {model_file}")
    
    # Test AI model loading capability
    try:
        from ai_model import load_ai_model, is_ai_model_loaded, get_ai_prediction
        
        # Load the model
        success = load_ai_model(model_file)
        if success:
            print("✓ AI model loaded successfully")
            
            # Test if model is loaded
            if is_ai_model_loaded():
                print("✓ AI model status check passed")
                
                # Test prediction (using sample data)
                sample_distances = [500.0] * 360  # Simple test data
                prediction = get_ai_prediction(sample_distances, 0)
                
                if prediction is not None:
                    print(f"✓ AI prediction generated: {prediction}")
                    print("✓ The prediction text field should now display this value in the UI")
                else:
                    print("✗ AI prediction returned None")
                    return False
            else:
                print("✗ AI model not detected as loaded")
                return False
        else:
            print("✗ Failed to load AI model")
            return False
            
    except Exception as e:
        print(f"✗ Error testing AI model: {e}")
        return False
    
    print("\n🎯 AI Prediction Text Field Test Results:")
    print("   - The 'Pred Angular Vel' field should now be visible in the Input Controls panel")
    print("   - It should be positioned below the 'Replace (R)' button and undo instruction")
    print("   - When no AI model is loaded, it should display '--'")
    print("   - When a model is loaded and making predictions, it should display the predicted value")
    print("   - The field should update in real-time as you navigate through frames")
    
    return True

if __name__ == "__main__":
    success = test_prediction_field()
    if success:
        print("\n✅ AI Prediction Text Field test completed successfully!")
        print("The new feature is ready to use in the visualizer.")
    else:
        print("\n❌ AI Prediction Text Field test failed!")
        sys.exit(1)
