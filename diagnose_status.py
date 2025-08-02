#!/usr/bin/env python3
"""
Diagnostic script to check status panel issues
"""

try:
    print("=== Status Panel Diagnostic ===")
    
    # Check if data file exists
    import os
    data_file = "data/run1/out1.txt"
    print(f"Data file exists: {os.path.exists(data_file)}")
    
    # Try to create basic UI manager
    print("\n1. Testing UI Manager import...")
    from ui_components import UIManager
    print("✓ UI Manager imported successfully")
    
    # Test basic tkinter setup
    print("\n2. Testing basic Tkinter...")
    import tkinter as tk
    from tkinter import ttk
    
    root = tk.Tk()
    root.withdraw()  # Hide the window
    print("✓ Tkinter root created")
    
    # Test UI Manager initialization 
    print("\n3. Testing UI Manager initialization...")
    callbacks = {}  # Empty callbacks for test
    ui = UIManager(root, callbacks)
    print("✓ UI Manager initialized")
    print(f"Status var before setup_ui: {ui.status_var}")
    
    # Test setup_ui (this creates all panels)
    print("\n4. Testing UI setup...")
    ui.setup_ui()
    print("✓ UI setup completed")
    print(f"Status var after setup_ui: {ui.status_var is not None}")
    print(f"Status var content: '{ui.status_var.get()}'")
    
    # Check if status panel exists
    print("\n5. Checking status panel...")
    # Look for children of root that might be the status panel
    main_frames = []
    for child in root.winfo_children():
        if isinstance(child, ttk.Frame):
            main_frames.append(child)
            print(f"Found main frame: {child}")
            
            # Look for status frame within main frame
            for subchild in child.winfo_children():
                if isinstance(subchild, ttk.LabelFrame):
                    if hasattr(subchild, 'cget') and 'Status' in str(subchild.cget('text')):
                        print(f"✓ Found Status LabelFrame: {subchild}")
                        
                        # Check for Label within status frame
                        for label in subchild.winfo_children():
                            if isinstance(label, ttk.Label):
                                print(f"✓ Found Status Label: {label}")
                                try:
                                    var = label.cget('textvariable')
                                    if var:
                                        print(f"✓ Status Label has textvariable: {var}")
                                        print(f"Status content: '{ui.status_var.get()}'")
                                except:
                                    print("Could not get textvariable info")
    
    root.destroy()
    print("\n✓ Test completed successfully")
    
except Exception as e:
    print(f"\n✗ Error during test: {e}")
    import traceback
    traceback.print_exc()
