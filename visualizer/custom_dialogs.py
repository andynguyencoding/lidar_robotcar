#!/usr/bin/env python3
"""
Custom dialog classes with keyboard shortcuts for Y/N responses
Fixed for aggressive event blocking to prevent double-press issues
"""

import tkinter as tk
from tkinter import ttk


class YesNoDialog:
    """Custom Yes/No dialog with Y/N keyboard shortcuts"""
    
    def __init__(self, parent, title, message, icon=None):
        self.result = None
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Calculate center position
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (200)
        y = (self.dialog.winfo_screenheight() // 2) - (100)
        self.dialog.geometry(f"400x200+{x}+{y}")
        
        self.setup_ui(message, icon)
        self.bind_keys()
        
    def setup_ui(self, message, icon):
        """Setup the dialog UI"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Icon and message frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        # Icon (if specified)
        if icon:
            if icon == 'warning':
                icon_text = "WARNING"
                icon_color = 'red'
            elif icon == 'question':
                icon_text = "?"
                icon_color = 'blue'
            elif icon == 'info':
                icon_text = "INFO"
                icon_color = 'darkgreen'
            else:
                icon_text = ""
                icon_color = 'black'
            
            if icon_text:
                icon_label = ttk.Label(content_frame, text=icon_text, 
                                     font=('Arial', 12, 'bold'), foreground=icon_color)
                icon_label.pack(side='left', padx=(0, 15), pady=10)
        
        # Message
        message_label = ttk.Label(content_frame, text=message, 
                                 font=('Arial', 11), wraplength=300, justify='left')
        message_label.pack(side='left', fill='both', expand=True, pady=10)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        # Buttons with keyboard shortcuts shown
        self.yes_button = ttk.Button(button_frame, text="Yes (Y)", 
                                    command=self.on_yes, width=12)
        self.yes_button.pack(side='left', padx=(0, 10))
        
        self.no_button = ttk.Button(button_frame, text="No (N)", 
                                   command=self.on_no, width=12)
        self.no_button.pack(side='right')
        
        # Default to Yes button
        self.dialog.after(50, lambda: self.yes_button.focus_set())
        
    def bind_keys(self):
        """Bind keyboard shortcuts with aggressive event blocking"""
        # Store reference to parent app for timing protection
        self._parent_app = None
        widget = self.parent
        while widget:
            if hasattr(widget, 'last_dialog_close_time'):
                self._parent_app = widget
                break
            widget = getattr(widget, 'master', None)
        
        # Aggressive event blocking approach
        def handle_key(action):
            def handler(event):
                # Immediately stop event propagation
                try:
                    event.widget.tk.call('break')
                except:
                    pass
                
                # Schedule action with delay to ensure clean execution
                self.dialog.after(100, lambda: self._safe_action(action))
                
                # Return break to prevent further propagation
                return "break"
            return handler
        
        # Bind all possible key variants
        for key in ['<Key-y>', '<Key-Y>', '<y>', '<Y>', '<KeyPress-y>', '<KeyPress-Y>']:
            try:
                self.dialog.bind(key, handle_key(self.on_yes))
            except:
                pass
                
        for key in ['<Key-n>', '<Key-N>', '<n>', '<N>', '<KeyPress-n>', '<KeyPress-N>']:
            try:
                self.dialog.bind(key, handle_key(self.on_no))
            except:
                pass
        
        self.dialog.bind('<Return>', handle_key(self.on_yes))
        self.dialog.bind('<Escape>', handle_key(self.on_no))
        
        # Catch ALL keys to prevent unwanted propagation
        self.dialog.bind('<Any-KeyPress>', self._block_all_keys)
        
        # Force modal behavior
        self.dialog.after(10, self._force_modal)
        
    def _force_modal(self):
        """Force modal behavior"""
        try:
            self.dialog.focus_force()
            self.dialog.grab_set_global()
            self.dialog.lift()
            self.dialog.attributes('-topmost', True)
            self.dialog.after(100, lambda: self.dialog.attributes('-topmost', False))
        except:
            pass
    
    def _block_all_keys(self, event):
        """Block all key events except our specific ones"""
        # Let our specific handlers deal with the keys we care about
        if event.keysym.lower() in ['y', 'n', 'return', 'escape']:
            return
        # Block everything else
        return "break"
    
    def _safe_action(self, action):
        """Execute action safely with error handling"""
        try:
            # Mark dialog close time for parent app timing protection
            if self._parent_app:
                import time
                self._parent_app.last_dialog_close_time = time.time() * 1000
            
            # Execute the action
            action()
        except Exception as e:
            print(f"Error in dialog action: {e}")
            try:
                self.dialog.destroy()
            except:
                pass
        
    def on_yes(self):
        """Handle Yes response"""
        self.result = True
        self._safe_destroy()
        
    def on_no(self):
        """Handle No response"""
        self.result = False
        self._safe_destroy()
        
    def on_cancel(self):
        """Handle window close"""
        self.result = False
        self._safe_destroy()
        
    def _safe_destroy(self):
        """Safely destroy dialog with proper cleanup"""
        try:
            # Release grab before destroying
            self.dialog.grab_release()
            # Give a small delay to ensure event processing is complete
            self.dialog.after(1, self.dialog.destroy)
        except:
            # Fallback - destroy immediately
            try:
                self.dialog.destroy()
            except:
                pass
        
    def show(self):
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result


class YesNoCancelDialog:
    """Custom Yes/No/Cancel dialog with Y/N/C keyboard shortcuts"""
    
    def __init__(self, parent, title, message, icon=None):
        self.result = None
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x220")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Calculate center position
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (225)
        y = (self.dialog.winfo_screenheight() // 2) - (110)
        self.dialog.geometry(f"450x220+{x}+{y}")
        
        self.setup_ui(message, icon)
        self.bind_keys()
        
    def setup_ui(self, message, icon):
        """Setup the dialog UI"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Icon and message frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        
        # Icon (if specified)
        if icon:
            if icon == 'warning':
                icon_text = "WARNING"
                icon_color = 'red'
            elif icon == 'question':
                icon_text = "?"
                icon_color = 'blue'
            elif icon == 'info':
                icon_text = "INFO"
                icon_color = 'darkgreen'
            else:
                icon_text = ""
                icon_color = 'black'
            
            if icon_text:
                icon_label = ttk.Label(content_frame, text=icon_text, 
                                     font=('Arial', 12, 'bold'), foreground=icon_color)
                icon_label.pack(side='left', padx=(0, 15), pady=10)
        
        # Message
        message_label = ttk.Label(content_frame, text=message, 
                                 font=('Arial', 11), wraplength=350, justify='left')
        message_label.pack(side='left', fill='both', expand=True, pady=10)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        # Buttons with keyboard shortcuts shown
        self.yes_button = ttk.Button(button_frame, text="Yes (Y)", 
                                    command=self.on_yes, width=12)
        self.yes_button.pack(side='left', padx=(0, 5))
        
        self.no_button = ttk.Button(button_frame, text="No (N)", 
                                   command=self.on_no, width=12)
        self.no_button.pack(side='left', padx=(0, 5))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel (C)", 
                                       command=self.on_cancel, width=12)
        self.cancel_button.pack(side='right')
        
        # Default to Yes button
        self.dialog.after(50, lambda: self.yes_button.focus_set())
        
    def bind_keys(self):
        """Bind keyboard shortcuts with aggressive event blocking"""
        # Store reference to parent app for timing protection
        self._parent_app = None
        widget = self.parent
        while widget:
            if hasattr(widget, 'last_dialog_close_time'):
                self._parent_app = widget
                break
            widget = getattr(widget, 'master', None)
        
        # Aggressive event blocking approach
        def handle_key(action):
            def handler(event):
                # Immediately stop event propagation
                try:
                    event.widget.tk.call('break')
                except:
                    pass
                
                # Schedule action with delay to ensure clean execution
                self.dialog.after(100, lambda: self._safe_action(action))
                
                # Return break to prevent further propagation
                return "break"
            return handler
        
        # Bind all possible key variants
        for key in ['<Key-y>', '<Key-Y>', '<y>', '<Y>', '<KeyPress-y>', '<KeyPress-Y>']:
            try:
                self.dialog.bind(key, handle_key(self.on_yes))
            except:
                pass
                
        for key in ['<Key-n>', '<Key-N>', '<n>', '<N>', '<KeyPress-n>', '<KeyPress-N>']:
            try:
                self.dialog.bind(key, handle_key(self.on_no))
            except:
                pass
                
        for key in ['<Key-c>', '<Key-C>', '<c>', '<C>', '<KeyPress-c>', '<KeyPress-C>']:
            try:
                self.dialog.bind(key, handle_key(self.on_cancel))
            except:
                pass
        
        self.dialog.bind('<Return>', handle_key(self.on_yes))
        self.dialog.bind('<Escape>', handle_key(self.on_cancel))
        
        # Catch ALL keys to prevent unwanted propagation
        self.dialog.bind('<Any-KeyPress>', self._block_all_keys)
        
        # Force modal behavior
        self.dialog.after(10, self._force_modal)
        
    def _force_modal(self):
        """Force modal behavior"""
        try:
            self.dialog.focus_force()
            self.dialog.grab_set_global()
            self.dialog.lift()
            self.dialog.attributes('-topmost', True)
            self.dialog.after(100, lambda: self.dialog.attributes('-topmost', False))
        except:
            pass
    
    def _block_all_keys(self, event):
        """Block all key events except our specific ones"""
        # Let our specific handlers deal with the keys we care about
        if event.keysym.lower() in ['y', 'n', 'c', 'return', 'escape']:
            return
        # Block everything else
        return "break"
    
    def _safe_action(self, action):
        """Execute action safely with error handling"""
        try:
            # Mark dialog close time for parent app timing protection
            if self._parent_app:
                import time
                self._parent_app.last_dialog_close_time = time.time() * 1000
            
            # Execute the action
            action()
        except Exception as e:
            print(f"Error in dialog action: {e}")
            try:
                self.dialog.destroy()
            except:
                pass
        
    def on_yes(self):
        """Handle Yes response"""
        self.result = True
        self._safe_destroy()
        
    def on_no(self):
        """Handle No response"""
        self.result = False
        self._safe_destroy()
        
    def on_cancel(self):
        """Handle Cancel response"""
        self.result = None
        self._safe_destroy()
        
    def _safe_destroy(self):
        """Safely destroy dialog with proper cleanup"""
        try:
            # Release grab before destroying
            self.dialog.grab_release()
            # Give a small delay to ensure event processing is complete
            self.dialog.after(1, self.dialog.destroy)
        except:
            # Fallback - destroy immediately
            try:
                self.dialog.destroy()
            except:
                pass
        
    def show(self):
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result


def ask_yes_no(parent, title, message, icon='question'):
    """Show a Yes/No dialog with Y/N keyboard shortcuts"""
    dialog = YesNoDialog(parent, title, message, icon)
    return dialog.show()


def ask_yes_no_cancel(parent, title, message, icon='question'):
    """Show a Yes/No/Cancel dialog with Y/N/C keyboard shortcuts"""
    dialog = YesNoCancelDialog(parent, title, message, icon)
    return dialog.show()
