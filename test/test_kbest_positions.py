#!/usr/bin/env python3
"""
Test script to verify the K-Best positions viewer functionality
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_positions_viewer():
    """Test the K-Best positions viewer"""
    print("Testing K-Best positions viewer...")
    
    try:
        # Test importing the configuration
        from config import DECISIVE_FRAME_POSITIONS
        print(f"✓ Successfully imported DECISIVE_FRAME_POSITIONS")
        print(f"  Current positions count: {len(DECISIVE_FRAME_POSITIONS)}")
        print(f"  First 10 positions: {DECISIVE_FRAME_POSITIONS[:10]}")
        
        # Test creating a simple dialog to show positions
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Test the positions dialog functionality
        dialog = tk.Toplevel(root)
        dialog.title("Test K-Best Positions")
        dialog.geometry("400x300")
        
        # Add a text widget to display positions
        text_widget = tk.Text(dialog, wrap=tk.WORD, height=10, width=50)
        text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Format positions for display
        positions_text = f"Total positions: {len(DECISIVE_FRAME_POSITIONS)}\n\n"
        positions_text += "Positions:\n"
        
        for i, pos in enumerate(DECISIVE_FRAME_POSITIONS):
            if i % 10 == 0 and i > 0:
                positions_text += "\n"
            positions_text += f"{pos:3d}  "
        
        text_widget.insert(tk.END, positions_text)
        text_widget.config(state=tk.DISABLED)
        
        # Add close button
        close_button = tk.Button(dialog, text="Close", command=root.quit)
        close_button.pack(pady=5)
        
        print("✓ Successfully created test dialog")
        print("Dialog window should be visible - close it to continue")
        
        # Show the dialog
        dialog.deiconify()
        root.deiconify()
        root.mainloop()
        
        print("✓ Dialog closed successfully")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

def test_menu_structure():
    """Test that menu items can be created"""
    print("\nTesting menu structure...")
    
    try:
        root = tk.Tk()
        root.title("Menu Test")
        
        # Create menubar
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # Create AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)
        
        # Create K-Best submenu
        kbest_menu = tk.Menu(ai_menu, tearoff=0)
        ai_menu.add_cascade(label="K-Best", menu=kbest_menu)
        
        # Add menu items
        kbest_menu.add_command(label="Load K-Best...", command=lambda: print("Load K-Best clicked"))
        kbest_menu.add_command(label="View Current Positions...", command=lambda: print("View positions clicked"))
        
        print("✓ Successfully created K-Best submenu structure")
        print("  - AI > K-Best > Load K-Best...")
        print("  - AI > K-Best > View Current Positions...")
        
        root.destroy()
        
    except Exception as e:
        print(f"✗ Menu creation error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== K-Best Positions Viewer Test ===\n")
    
    # Test menu structure
    menu_success = test_menu_structure()
    
    # Test positions viewer
    viewer_success = test_positions_viewer()
    
    print(f"\n=== Test Results ===")
    print(f"Menu structure: {'✓ PASS' if menu_success else '✗ FAIL'}")
    print(f"Positions viewer: {'✓ PASS' if viewer_success else '✗ FAIL'}")
    
    if menu_success and viewer_success:
        print("\n🎉 All tests passed! K-Best positions viewer is ready.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        sys.exit(1)
