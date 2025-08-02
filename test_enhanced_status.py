#!/usr/bin/env python3
"""
Test script to verify status panel visibility with the new changes
"""

import tkinter as tk
from tkinter import ttk

def test_status_visibility():
    """Test the enhanced status panel visibility"""
    root = tk.Tk()
    root.title("Enhanced Status Panel Test")
    root.geometry("800x600")
    
    # Main container
    main_frame = ttk.Frame(root)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Controls panel (top)
    controls_frame = ttk.LabelFrame(main_frame, text="🎮 Controls", padding=5)
    controls_frame.pack(fill='x', pady=(0, 5))
    ttk.Label(controls_frame, text="Control buttons would be here...").pack()
    
    # Status panel (bottom) - packed before content to ensure visibility
    status_frame = ttk.LabelFrame(main_frame, text="📊 Status", padding=8)
    status_frame.pack(fill='x', side='bottom', pady=(10, 0))
    
    status_var = tk.StringVar()
    status_var.set("Data: test.txt | Mode: INSPECT | Data: REAL")
    status_label = ttk.Label(status_frame, textvariable=status_var, 
             font=('TkDefaultFont', 10), wraplength=800, anchor='e', justify='right',
             relief='solid', padding=5)
    status_label.pack(fill='x', pady=3, ipady=3)
    
    # Content panel (middle) - expands in remaining space
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill='both', expand=True, pady=(0, 5))
    
    # Simulate main content
    content_label = ttk.Label(content_frame, text="Main application content area\n\nThe status panel should be clearly visible at the bottom\nwith enhanced styling and proper spacing.", 
                             justify='center')
    content_label.pack(expand=True)
    
    print("Status panel test running...")
    print("The status panel should now be clearly visible at the bottom")
    print("- Enhanced padding and spacing")
    print("- Emoji icon in title (📊 Status)")
    print("- Solid border relief")
    print("- Larger font size")
    print("- Proper bottom positioning")
    
    root.mainloop()

if __name__ == "__main__":
    test_status_visibility()
