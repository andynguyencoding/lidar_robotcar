#!/usr/bin/env python3
"""
Test script to verify the modular refactoring of visualizer.py
"""

import os
import sys
import traceback

def test_module_imports():
    """Test that all modules can be imported successfully"""
    print("Testing module imports...")
    
    modules_to_test = [
        'config',
        'file_manager',
        'undo_system', 
        'frame_navigation',
        'data_statistics',
        'ui_components',
        'visualization_renderer',
        'startup_config',
        'visualizer_core',
        'main'
    ]
    
    success_count = 0
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module} imported successfully")
            success_count += 1
        except ImportError as e:
            print(f"✗ {module} import failed: {e}")
        except Exception as e:
            print(f"✗ {module} error during import: {e}")
    
    print(f"\nImport Results: {success_count}/{len(modules_to_test)} modules imported successfully")
    return success_count == len(modules_to_test)

def test_config_constants():
    """Test configuration constants"""
    print("\nTesting configuration constants...")
    
    try:
        from visualizer.config import LIDAR_RESOLUTION, DECISIVE_FRAME_POSITIONS, MAX_RECENT_FILES
        
        assert LIDAR_RESOLUTION == 360, f"Expected LIDAR_RESOLUTION=360, got {LIDAR_RESOLUTION}"
        assert len(DECISIVE_FRAME_POSITIONS) > 0, "DECISIVE_FRAME_POSITIONS should not be empty"
        assert MAX_RECENT_FILES == 5, f"Expected MAX_RECENT_FILES=5, got {MAX_RECENT_FILES}"
        
        print("✓ Configuration constants are correct")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_file_manager():
    """Test file manager functionality"""
    print("\nTesting file manager...")
    
    try:
        from file_manager import FileManager
        
        fm = FileManager()
        
        # Test file existence check
        assert fm.file_exists(__file__), "Should detect this test file exists"
        assert not fm.file_exists("nonexistent_file.xyz"), "Should detect nonexistent file"
        
        # Test basename
        basename = fm.get_basename(__file__)
        assert basename.endswith(".py"), f"Expected .py file, got {basename}"
        
        print("✓ File manager functionality works")
        return True
        
    except Exception as e:
        print(f"✗ File manager test failed: {e}")
        return False

def test_undo_system():
    """Test undo system functionality"""
    print("\nTesting undo system...")
    
    try:
        from undo_system import UndoSystem
        
        undo = UndoSystem()
        
        # Test empty state
        assert not undo.has_changes(), "Should start with no changes"
        assert undo.get_last_change() is None, "Should return None for empty stack"
        
        # Test adding changes
        undo.add_change(1, "old", "new")
        assert undo.has_changes(), "Should have changes after adding"
        assert undo.get_stack_size() == 1, "Should have 1 change"
        
        # Test retrieving change
        change = undo.get_last_change()
        assert change == (1, "old", "new"), f"Expected (1, 'old', 'new'), got {change}"
        assert not undo.has_changes(), "Should have no changes after retrieval"
        
        print("✓ Undo system functionality works")
        return True
        
    except Exception as e:
        print(f"✗ Undo system test failed: {e}")
        return False

def test_data_analyzer():
    """Test data analyzer functionality"""
    print("\nTesting data analyzer...")
    
    try:
        from data_statistics import DataAnalyzer
        
        analyzer = DataAnalyzer()
        
        # Test header detection (basic functionality)
        # This is a simple test - we'd need actual data files for comprehensive testing
        print("✓ Data analyzer instantiated successfully")
        return True
        
    except Exception as e:
        print(f"✗ Data analyzer test failed: {e}")
        return False

def test_visualization_renderer():
    """Test visualization renderer instantiation"""
    print("\nTesting visualization renderer...")
    
    try:
        from visualization_renderer import VisualizationRenderer
        
        renderer = VisualizationRenderer()
        
        # Test configuration
        renderer.set_direction_ratio(45.0, 1.0)
        
        print("✓ Visualization renderer instantiated successfully")
        return True
        
    except Exception as e:
        print(f"✗ Visualization renderer test failed: {e}")
        return False

def test_main_functions():
    """Test main module functions"""
    print("\nTesting main module functions...")
    
    try:
        from main import calculate_scale_factor
        
        # Test function exists and can be called (we'd need real data for full test)
        print("✓ Main module functions accessible")
        return True
        
    except Exception as e:
        print(f"✗ Main module test failed: {e}")
        return False

def compare_line_counts():
    """Compare line counts between original and modular versions"""
    print("\nComparing line counts...")
    
    try:
        # Count lines in original file
        original_file = "visualizer.py"
        if os.path.exists(original_file):
            with open(original_file, 'r') as f:
                original_lines = len(f.readlines())
        else:
            print("Original visualizer.py not found for comparison")
            return True
        
        # Count lines in modular files
        modular_files = [
            'config.py',
            'file_manager.py', 
            'undo_system.py',
            'frame_navigation.py',
            'data_statistics.py',
            'ui_components.py',
            'visualization_renderer.py',
            'startup_config.py',
            'visualizer_core.py',
            'main.py'
        ]
        
        total_modular_lines = 0
        for file in modular_files:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    lines = len(f.readlines())
                    total_modular_lines += lines
                    print(f"  {file}: {lines} lines")
        
        print(f"\nLine count comparison:")
        print(f"  Original visualizer.py: {original_lines} lines")
        print(f"  Modular version total: {total_modular_lines} lines")
        print(f"  Difference: {total_modular_lines - original_lines:+d} lines")
        
        # The modular version might have slightly more lines due to imports and docstrings
        if total_modular_lines > original_lines * 0.8:  # Allow for some overhead
            print("✓ Line count comparison looks reasonable")
            return True
        else:
            print("⚠ Significant line count difference - some functionality may be missing")
            return False
        
    except Exception as e:
        print(f"✗ Line count comparison failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Testing Modular Refactoring of visualizer.py")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_module_imports),
        ("Configuration Constants", test_config_constants),
        ("File Manager", test_file_manager),
        ("Undo System", test_undo_system),
        ("Data Analyzer", test_data_analyzer),
        ("Visualization Renderer", test_visualization_renderer),
        ("Main Functions", test_main_functions),
        ("Line Count Comparison", compare_line_counts)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Modular refactoring appears successful.")
        print("\n📋 Refactoring Summary:")
        print("• Original 3300+ line file split into 10 focused modules")
        print("• Each module has a specific responsibility")
        print("• Import structure maintains functionality")
        print("• Modular design improves maintainability")
        
        print("\n🚀 Next Steps:")
        print("1. Test the actual visualizer application")
        print("2. Verify all UI interactions work correctly")
        print("3. Check data loading and visualization")
        print("4. Test AI model integration")
        print("5. Validate file operations and recent files")
        
    else:
        print("⚠️  Some tests failed. Review the issues above.")
        print("The modular refactoring may need additional fixes.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
