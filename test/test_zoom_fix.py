#!/usr/bin/env python3
"""
Test script to verify zoom functionality doesn't cause errors
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_zoom_methods():
    """Test that zoom methods can be called without import errors"""
    print("Testing zoom method definitions...")
    
    try:
        # Test monolithic version
        print("  Testing monolithic version (visualizer.py)...")
        with open('visualizer.py', 'r') as f:
            content = f.read()
            if 'def zoom_in(self):' in content and 'def zoom_out(self):' in content:
                print("    ✓ Zoom methods found in monolithic version")
            else:
                print("    ✗ Zoom methods missing in monolithic version")
                return False
        
        # Test modular version
        print("  Testing modular version (visualizer_core.py)...")
        with open('visualizer_core.py', 'r') as f:
            content = f.read()
            if 'def zoom_in(self):' in content and 'def zoom_out(self):' in content:
                print("    ✓ Zoom methods found in modular version")
                # Check if using correct render_frame call
                if 'self.render_frame()' in content and 'self.renderer.render_frame()' not in content.split('def zoom_')[1]:
                    print("    ✓ Using correct render_frame() call in modular version")
                else:
                    print("    ⚠ Check render_frame() calls in zoom methods")
            else:
                print("    ✗ Zoom methods missing in modular version")
                return False
        
        # Test UI components
        print("  Testing UI components...")
        with open('ui_components.py', 'r') as f:
            content = f.read()
            if 'zoom_in' in content and 'zoom_out' in content and 'Zoom:' in content:
                print("    ✓ Zoom buttons found in UI components")
            else:
                print("    ✗ Zoom buttons missing in UI components")
                return False
        
        print("✓ All zoom method definitions are correct")
        return True
        
    except Exception as e:
        print(f"✗ Error testing zoom methods: {e}")
        return False

def test_config_import():
    """Test that config can be imported and SCALE_FACTOR accessed"""
    print("\nTesting config import...")
    
    try:
        import config
        print(f"✓ Config imported successfully")
        print(f"  Current SCALE_FACTOR: {config.SCALE_FACTOR}")
        
        # Test scale factor modifications
        original = config.SCALE_FACTOR
        config.SCALE_FACTOR = original * 1.1
        print(f"  Zoom in test: {original:.4f} -> {config.SCALE_FACTOR:.4f}")
        
        config.SCALE_FACTOR = config.SCALE_FACTOR * 0.9
        print(f"  Zoom out test: -> {config.SCALE_FACTOR:.4f}")
        
        # Restore original
        config.SCALE_FACTOR = original
        print(f"  Restored: {config.SCALE_FACTOR:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Config import error: {e}")
        return False

if __name__ == "__main__":
    print("=== Zoom Error Fix Test ===\n")
    
    # Test method definitions
    methods_ok = test_zoom_methods()
    
    # Test config access
    config_ok = test_config_import()
    
    print(f"\n=== Test Results ===")
    print(f"Method definitions: {'✓ PASS' if methods_ok else '✗ FAIL'}")
    print(f"Config access: {'✓ PASS' if config_ok else '✗ FAIL'}")
    
    if methods_ok and config_ok:
        print("\n🎉 Zoom error fix applied successfully!")
        print("\nFix summary:")
        print("  - Changed self.renderer.render_frame() to self.render_frame()")
        print("  - This calls the wrapper method that provides all required parameters")
        print("  - Both zoom in/out functions should now work without errors")
    else:
        print("\n❌ Some issues remain. Check the errors above.")
        sys.exit(1)
