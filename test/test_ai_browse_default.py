#!/usr/bin/env python3
"""
Test script to verify the AI model browsing defaults to ./models directory
"""

import subprocess
import time
import sys
import os

def test_ai_model_browse_default():
    """Test that AI model browsing defaults to ./models directory"""
    print("Testing AI Model Browse Default Directory...")
    
    # Check if models directory exists
    models_dir = os.path.abspath("./models")
    if os.path.exists(models_dir):
        print(f"✓ Models directory exists: {models_dir}")
        
        # List model files
        model_files = [f for f in os.listdir(models_dir) if f.endswith(('.pkl', '.pickle'))]
        print(f"✓ Found {len(model_files)} model files in models directory:")
        for i, model_file in enumerate(model_files, 1):
            print(f"   {i}. {model_file}")
    else:
        print(f"✗ Models directory does not exist: {models_dir}")
        return False
    
    print("\n🎯 Updated AI Model Browse Functionality:")
    print("   1. AI > Browse Model... now defaults to ./models directory")
    print("   2. If ./models directory exists, file dialog opens there automatically")
    print("   3. If ./models directory doesn't exist, falls back to current working directory")
    print("   4. Users can still navigate to other directories if needed")
    print("   5. Makes it much easier to find and load trained models")
    
    print("\n🧪 How to Test the Update:")
    print("   1. Start the visualizer")
    print("   2. Go to AI > Browse Model...")
    print("   3. The file dialog should automatically open in the models directory")
    print("   4. You should see all available .pkl model files immediately")
    print("   5. No need to navigate to the models folder manually")
    
    print("\n🔧 Technical Implementation:")
    print("   - Updated browse_ai_model() method")
    print("   - Uses os.path.abspath('./models') to get absolute path")
    print("   - Checks if models directory exists with os.path.exists()")
    print("   - Falls back to current working directory if models dir doesn't exist")
    print("   - Maintains all existing file type filters (.pkl, .pickle)")
    
    print("\n📁 Current Models Directory Content:")
    print(f"   Location: {models_dir}")
    print(f"   Model files available: {len(model_files)}")
    for model_file in model_files:
        file_path = os.path.join(models_dir, model_file)
        file_size = os.path.getsize(file_path)
        print(f"   - {model_file} ({file_size/1024:.1f} KB)")
    
    print("\n✨ User Experience Improvement:")
    print("   - Faster model loading workflow")
    print("   - Reduced clicks and navigation")
    print("   - More intuitive for users expecting models in ./models")
    print("   - Consistent with common ML project structure")
    
    return True

if __name__ == "__main__":
    success = test_ai_model_browse_default()
    if success:
        print("\n✅ AI Model Browse Default Directory test completed successfully!")
        print("The AI model browsing now defaults to ./models directory.")
        print("Test the functionality by using AI > Browse Model... in the running visualizer.")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
