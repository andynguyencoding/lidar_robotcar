#!/usr/bin/env python3
"""
Simple test to verify status panel visibility
"""

import tkinter as tk
from tkinter import ttk

def test_modular_status():
    """Test the modular status panel layout"""
    root = tk.Tk()
    root.title("Status Panel Test - Modular Style")
    root.geometry("800x600")
    
    # Main container
    main_frame = ttk.Frame(root)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Controls panel (top)
    controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding=3)
    controls_frame.pack(fill='x', pady=(0, 5))
    ttk.Label(controls_frame, text="Some controls here...").pack()
    
    # Content panel (middle)
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill='both', expand=True, pady=(0, 5))
    ttk.Label(content_frame, text="Main content area").pack(fill='both', expand=True)
    
    # Status panel (bottom)
    status_frame = ttk.LabelFrame(main_frame, text="Status", padding=3)
    status_frame.pack(fill='x', pady=(5, 0))
    
    status_var = tk.StringVar()
    status_var.set("Data: test.txt | Mode: INSPECT | Data: REAL")
    ttk.Label(status_frame, textvariable=status_var, 
             font=('Courier', 9), wraplength=800, anchor='e', justify='right').pack(fill='x')
    
    print("Status panel should be visible at the bottom with right-aligned text")
    print("Status text:", status_var.get())
    
    root.mainloop()

def test_monolithic_status():
    """Test the monolithic status panel layout"""
    root = tk.Tk()
    root.title("Status Panel Test - Monolithic Style")
    root.geometry("800x600")
    
    # Main container
    main_frame = ttk.Frame(root)  
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Some content area
    content_area = ttk.Frame(main_frame)
    content_area.pack(fill='both', expand=True, pady=(0, 5))
    ttk.Label(content_area, text="Main application area").pack(fill='both', expand=True)
    
    # Status display at the bottom - make it more compact with right-aligned text
    status_frame = ttk.LabelFrame(main_frame, text="Status", padding=3)
    status_frame.pack(fill='x', pady=(5, 0))
    
    status_var = tk.StringVar()
    status_var.set("Data: test.txt | Mode: INSPECT | Data: REAL")
    ttk.Label(status_frame, textvariable=status_var, 
             font=('Courier', 9), wraplength=800, anchor='e', justify='right').pack(fill='x')
    
    print("Status panel should be visible at the bottom with right-aligned text")
    print("Status text:", status_var.get())
    
    root.mainloop()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "monolithic":
        test_monolithic_status()
    else:
        test_modular_status()
