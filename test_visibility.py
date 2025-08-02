#!/usr/bin/env python3
"""
Quick test to see if radio buttons are visible by running the actual programs
"""

import subprocess
import sys
import time

def test_radio_buttons_visibility():
    print("🧪 Testing Radio Buttons Visibility")
    print("=" * 40)
    
    print("\nInstructions:")
    print("1. The programs will start")
    print("2. Look for 'Navigate Dataset' section with Train/Val/Test radio buttons")
    print("3. They should be visible below the 'Split Data' and 'Move Set' buttons")
    print("4. Close each program window when you've verified the radio buttons are visible")
    
    print("\n📋 Expected Layout:")
    print("   [📊 Split Data] [🔄 Move Set]")
    print("   ┌─ Navigate Dataset ─────────────┐")
    print("   │ ◉ Train  ○ Val  ○ Test       │")
    print("   └────────────────────────────────┘")
    
    input("\nPress Enter to start testing...")
    
    # Test modular version
    print("\n🔧 Starting modular version (main.py)...")
    print("Look for the radio buttons below Split Data and Move Set buttons!")
    try:
        result = subprocess.run([sys.executable, "main.py"], 
                              capture_output=False, 
                              timeout=30)  # 30 second timeout
    except subprocess.TimeoutExpired:
        print("✓ Modular version ran (timed out - normal for GUI apps)")
    except KeyboardInterrupt:
        print("✓ Modular version closed by user")
    except Exception as e:
        print(f"⚠️  Modular version error: {e}")
    
    # Test monolithic version
    print("\n🔧 Starting monolithic version (visualizer.py)...")
    print("Look for the radio buttons below Split Data and Move Set buttons!")
    try:
        result = subprocess.run([sys.executable, "visualizer.py"], 
                              capture_output=False,
                              timeout=30)  # 30 second timeout
    except subprocess.TimeoutExpired:
        print("✓ Monolithic version ran (timed out - normal for GUI apps)")
    except KeyboardInterrupt:
        print("✓ Monolithic version closed by user")
    except Exception as e:
        print(f"⚠️  Monolithic version error: {e}")
    
    print("\n✅ Testing complete!")
    print("Both versions should now show the radio buttons immediately upon startup.")

if __name__ == "__main__":
    test_radio_buttons_visibility()
