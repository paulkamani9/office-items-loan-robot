"""
Borrow screen for borrowing items
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    THEME_COLOR_PRIMARY,
    THEME_COLOR_SECONDARY,
    THEME_COLOR_ACCENT,
    THEME_COLOR_SUCCESS,
    THEME_COLOR_TEXT_LIGHT,
    THEME_COLOR_TEXT_DARK
)
from utils.logger import RobotLogger


class BorrowScreen:
    """
    Borrow interface
    """
    
    def __init__(self, parent, state_manager, robot_controller, back_callback, status_callback):
        """Initialize borrow interface"""
        self.logger = RobotLogger()
        self.parent = parent
        self.state = state_manager
        self.robot = robot_controller
        self.back_callback = back_callback
        self.status_callback = status_callback
        
        self.frame = tk.Frame(parent, bg=THEME_COLOR_PRIMARY)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.operation_in_progress = False
        self.is_active = True  # Flag to track if screen is still active
        
        self.create_ui()
        self.refresh_item_list()
    
    def create_ui(self):
        """Create borrow screen UI"""
        # Header with back button
        header = tk.Frame(self.frame, bg=THEME_COLOR_PRIMARY)
        header.pack(fill=tk.X, pady=(0, 20))
        
        back_btn = tk.Button(
            header,
            text="← Back",
            command=self.handle_back,
            font=('Arial', 12),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        back_btn.pack(side=tk.LEFT)
        
        title = tk.Label(
            header,
            text="BORROW MODE",
            font=('Arial', 24, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        title.pack(side=tk.LEFT, padx=20)
        
        # Available items label
        info_label = tk.Label(
            self.frame,
            text="Available Items:",
            font=('Arial', 16, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            anchor=tk.W
        )
        info_label.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        # Items grid container
        self.items_container = tk.Frame(self.frame, bg=THEME_COLOR_PRIMARY)
        self.items_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Progress bar (hidden initially)
        self.progress_frame = tk.Frame(self.frame, bg=THEME_COLOR_PRIMARY)
        self.progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=('Arial', 12),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=400
        )
        self.progress_bar.pack(pady=5)
    
    def refresh_item_list(self):
        """Update item display based on current availability"""
        # Clear existing items
        for widget in self.items_container.winfo_children():
            widget.destroy()
        
        # Get all items and their status
        all_status = self.state.get_all_status()
        available_items = self.state.get_available_items()
        
        # Create grid of item cards (3 columns)
        row = 0
        col = 0
        
        for item_name, status in all_status.items():
            # Create item card
            is_available = status == self.state.STATUS_AVAILABLE
            
            card = tk.Frame(
                self.items_container,
                bg=THEME_COLOR_ACCENT if is_available else THEME_COLOR_SECONDARY,
                relief='raised',
                bd=2
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            # Item name
            name_label = tk.Label(
                card,
                text=item_name,
                font=('Arial', 14, 'bold'),
                bg=THEME_COLOR_ACCENT if is_available else THEME_COLOR_SECONDARY,
                fg=THEME_COLOR_TEXT_LIGHT,
                wraplength=180
            )
            name_label.pack(pady=(20, 10))
            
            # Status indicator
            status_text = "Available" if is_available else "Loaned Out"
            status_label = tk.Label(
                card,
                text=status_text,
                font=('Arial', 10),
                bg=THEME_COLOR_ACCENT if is_available else THEME_COLOR_SECONDARY,
                fg=THEME_COLOR_TEXT_LIGHT if is_available else '#95A5A6'
            )
            status_label.pack(pady=(0, 10))
            
            # Borrow button
            btn_text = "BORROW" if is_available else "Not Available"
            borrow_btn = tk.Button(
                card,
                text=btn_text,
                command=lambda name=item_name: self.borrow_item(name),
                font=('Arial', 12, 'bold'),
                bg=THEME_COLOR_SUCCESS if is_available else '#7F8C8D',
                fg=THEME_COLOR_TEXT_LIGHT,
                relief='flat',
                padx=20,
                pady=10,
                cursor='hand2' if is_available else 'arrow',
                state=tk.NORMAL if is_available else tk.DISABLED
            )
            borrow_btn.pack(pady=(0, 20))
            
            # Update grid position
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            self.items_container.columnconfigure(i, weight=1)
    
    def borrow_item(self, item_name: str):
        """Execute borrow operation with status updates"""
        if self.operation_in_progress:
            messagebox.showwarning("Operation in Progress", "Please wait for current operation to complete.")
            return
        
        if not self.state.is_available(item_name):
            messagebox.showerror("Not Available", f"{item_name} is currently loaned out.")
            return
        
        # Confirm
        result = messagebox.askyesno(
            "Confirm Borrow",
            f"Borrow {item_name}?\n\nThe robot will retrieve it from storage and deliver it to the drop zone."
        )
        
        if not result:
            return
        
        # Disable UI and show progress
        self.operation_in_progress = True
        self.refresh_item_list()
        self.progress_label.config(text="Borrowing item... Please wait")
        self.progress_bar.start(10)
        
        # Run borrow operation in background thread
        thread = threading.Thread(
            target=self._borrow_thread,
            args=(item_name,),
            daemon=True
        )
        thread.start()
    
    def _borrow_thread(self, item_name: str):
        """Background thread for borrow operation"""
        def update_status(msg):
            if self.is_active:
                try:
                    self.progress_label.config(text=msg)
                except tk.TclError:
                    pass  # Widget may be destroyed
        
        try:
            # Check if still active before proceeding
            if not self.is_active:
                return
            
            # Execute borrow
            result = self.robot.borrow_item(item_name, status_callback=update_status)
            
            # Check if still active before updating UI
            if not self.is_active:
                return
            
            if result['success']:
                # Update state
                self.state.mark_loaned(item_name)
                
                # Show success
                self.parent.after(0, lambda: self._borrow_complete(item_name, True, "Success!"))
            else:
                # Show error
                self.parent.after(0, lambda: self._borrow_complete(
                    item_name, False, result.get('message', 'Unknown error')
                ))
        
        except Exception as e:
            self.logger.error(f"Borrow error: {e}")
            if self.is_active:
                self.parent.after(0, lambda: self._borrow_complete(item_name, False, str(e)))
    
    def _borrow_complete(self, item_name: str, success: bool, message: str):
        """Handle borrow completion (runs on main thread)"""
        if not self.is_active:
            return
        
        try:
            self.progress_bar.stop()
        except tk.TclError:
            pass
        
        self.operation_in_progress = False
        
        if success:
            messagebox.showinfo(
                "Borrow Complete",
                f"{item_name} has been delivered to the drop zone.\n\nPlease collect your item."
            )
            self.status_callback("Ready")
        else:
            messagebox.showerror(
                "Borrow Failed",
                f"Failed to borrow {item_name}:\n\n{message}"
            )
            self.status_callback("Error - see logs")
        
        # Refresh UI only if still active
        if self.is_active:
            try:
                self.refresh_item_list()
                self.progress_label.config(text="")
            except tk.TclError:
                pass
    
    def handle_back(self):
        """Handle back button - cleanup and return to main menu"""
        if self.operation_in_progress:
            result = messagebox.askyesno(
                "Operation in Progress",
                "An operation is in progress. Are you sure you want to go back?\n\nThe robot will continue its current movement."
            )
            if not result:
                return
        
        self.cleanup()
        self.back_callback()
    
    def cleanup(self):
        """Cleanup when leaving screen"""
        self.logger.info("Cleaning up borrow screen")
        self.is_active = False
        self.operation_in_progress = False
