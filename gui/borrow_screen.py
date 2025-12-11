"""
Borrow screen - elegant design for borrowing items
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import RobotLogger


# Modern color scheme (matching main_window)
COLORS = {
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e', 
    'bg_light': '#0f3460',
    'accent_blue': '#3498db',
    'accent_green': '#27ae60',
    'accent_orange': '#e67e22',
    'accent_red': '#e74c3c',
    'text_white': '#ffffff',
    'text_gray': '#bdc3c7',
    'card_bg': '#1e3a5f',
    'card_available': '#1e4d2b',
    'card_unavailable': '#2d2d44'
}


class BorrowScreen:
    """
    Elegant borrow interface with item cards
    """
    
    def __init__(self, parent, state_manager, robot_controller, back_callback, status_callback):
        """Initialize borrow interface"""
        self.logger = RobotLogger()
        self.parent = parent
        self.state = state_manager
        self.robot = robot_controller
        self.back_callback = back_callback
        self.status_callback = status_callback
        
        self.frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.operation_in_progress = False
        self.is_active = True
        
        self.create_ui()
        self.refresh_item_list()
    
    def create_ui(self):
        """Create borrow screen UI"""
        # Header
        header = tk.Frame(self.frame, bg=COLORS['bg_dark'])
        header.pack(fill=tk.X, pady=(0, 10))
        
        # Back button
        back_btn = tk.Button(
            header,
            text="← Back to Home",
            command=self.handle_back,
            font=('Arial', 11),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_white'],
            activebackground=COLORS['bg_light'],
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        back_btn.pack(side=tk.LEFT)
        
        # Title
        title_frame = tk.Frame(header, bg=COLORS['bg_dark'])
        title_frame.pack(side=tk.LEFT, padx=20)
        
        title = tk.Label(
            title_frame,
            text="📦 BORROW AN ITEM",
            font=('Arial', 20, 'bold'),
            bg=COLORS['bg_dark'],
            fg=COLORS['accent_blue']
        )
        title.pack(side=tk.LEFT)
        
        # Subtitle
        subtitle = tk.Label(
            header,
            text="Select an available item to borrow",
            font=('Arial', 11),
            bg=COLORS['bg_dark'],
            fg=COLORS['text_gray']
        )
        subtitle.pack(side=tk.RIGHT, padx=20)
        
        # Divider
        divider = tk.Frame(self.frame, bg=COLORS['bg_medium'], height=2)
        divider.pack(fill=tk.X, pady=(0, 15))
        
        # Items grid container with scrollable area
        self.items_container = tk.Frame(self.frame, bg=COLORS['bg_dark'])
        self.items_container.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Progress section (hidden initially)
        self.progress_frame = tk.Frame(self.frame, bg=COLORS['bg_medium'])
        self.progress_frame.pack(fill=tk.X, padx=20, pady=10)
        self.progress_frame.pack_forget()  # Hide initially
        
        progress_inner = tk.Frame(self.progress_frame, bg=COLORS['bg_medium'])
        progress_inner.pack(pady=15, padx=20)
        
        self.progress_icon = tk.Label(
            progress_inner,
            text="🔄",
            font=('Arial', 24),
            bg=COLORS['bg_medium']
        )
        self.progress_icon.pack()
        
        self.progress_label = tk.Label(
            progress_inner,
            text="",
            font=('Arial', 12),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_white']
        )
        self.progress_label.pack(pady=(10, 5))
        
        self.progress_bar = ttk.Progressbar(
            progress_inner,
            mode='indeterminate',
            length=400
        )
        self.progress_bar.pack()
    
    def refresh_item_list(self):
        """Update item display based on current availability"""
        # Clear existing items
        for widget in self.items_container.winfo_children():
            widget.destroy()
        
        # Get all items and their status
        all_status = self.state.get_all_status()
        
        # Create grid of item cards (3 columns)
        row = 0
        col = 0
        
        for item_name, status in all_status.items():
            is_available = status == self.state.STATUS_AVAILABLE
            
            # Create item card
            card = self.create_item_card(item_name, is_available)
            card.grid(row=row, column=col, padx=8, pady=8, sticky='nsew')
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            self.items_container.columnconfigure(i, weight=1)
    
    def create_item_card(self, item_name: str, is_available: bool):
        """Create a styled item card"""
        bg_color = COLORS['card_available'] if is_available else COLORS['card_unavailable']
        border_color = COLORS['accent_green'] if is_available else COLORS['text_gray']
        
        card = tk.Frame(
            self.items_container,
            bg=bg_color,
            highlightbackground=border_color,
            highlightthickness=2
        )
        
        # Card content
        content = tk.Frame(card, bg=bg_color)
        content.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        # Item icon (based on item name)
        icon = self.get_item_icon(item_name)
        icon_label = tk.Label(
            content,
            text=icon,
            font=('Arial', 28),
            bg=bg_color
        )
        icon_label.pack()
        
        # Item name
        name_label = tk.Label(
            content,
            text=item_name,
            font=('Arial', 13, 'bold'),
            bg=bg_color,
            fg=COLORS['text_white'],
            wraplength=160
        )
        name_label.pack(pady=(8, 5))
        
        # Status badge
        status_text = "✓ Available" if is_available else "✗ On Loan"
        status_color = COLORS['accent_green'] if is_available else COLORS['accent_orange']
        
        status_label = tk.Label(
            content,
            text=status_text,
            font=('Arial', 10),
            bg=bg_color,
            fg=status_color
        )
        status_label.pack(pady=(0, 10))
        
        # Borrow button
        if is_available:
            btn = tk.Button(
                content,
                text="BORROW",
                command=lambda name=item_name: self.borrow_item(name),
                font=('Arial', 11, 'bold'),
                bg=COLORS['accent_blue'],
                fg='white',
                activebackground='#2980b9',
                relief='flat',
                padx=25,
                pady=8,
                cursor='hand2'
            )
        else:
            btn = tk.Button(
                content,
                text="Unavailable",
                font=('Arial', 11),
                bg=COLORS['text_gray'],
                fg=COLORS['bg_dark'],
                relief='flat',
                padx=25,
                pady=8,
                state=tk.DISABLED
            )
        btn.pack()
        
        return card
    
    def get_item_icon(self, item_name: str) -> str:
        """Get appropriate icon for item"""
        icons = {
            'Chair': '🪑',
            'Computer Keyboard': '⌨️',
            'Computer Mouse': '🖱️',
            'Headphones': '🎧',
            'Mobile Phone': '📱',
            'Pen': '🖊️'
        }
        return icons.get(item_name, '📦')
    
    def borrow_item(self, item_name: str):
        """Execute borrow operation with status updates"""
        if self.operation_in_progress:
            messagebox.showwarning("Please Wait", "An operation is already in progress.")
            return
        
        if not self.state.is_available(item_name):
            messagebox.showerror("Not Available", f"{item_name} is currently on loan.")
            return
        
        # Confirm
        result = messagebox.askyesno(
            "Confirm Borrow",
            f"Borrow {item_name}?\n\nThe robot will retrieve it from storage\nand deliver it to the drop zone.",
            icon='question'
        )
        
        if not result:
            return
        
        # Show progress
        self.operation_in_progress = True
        self.progress_frame.pack(fill=tk.X, padx=20, pady=10)
        self.progress_label.config(text=f"Borrowing {item_name}...")
        self.progress_bar.start(10)
        self.refresh_item_list()
        
        # Run in background
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
                    pass
        
        try:
            if not self.is_active:
                return
            
            result = self.robot.borrow_item(item_name, status_callback=update_status)
            
            if not self.is_active:
                return
            
            if result['success']:
                self.state.mark_loaned(item_name)
                self.parent.after(0, lambda: self._borrow_complete(item_name, True, "Success!"))
            else:
                self.parent.after(0, lambda: self._borrow_complete(
                    item_name, False, result.get('message', 'Unknown error')
                ))
        
        except Exception as e:
            self.logger.error(f"Borrow error: {e}")
            if self.is_active:
                self.parent.after(0, lambda: self._borrow_complete(item_name, False, str(e)))
    
    def _borrow_complete(self, item_name: str, success: bool, message: str):
        """Handle borrow completion"""
        if not self.is_active:
            return
        
        try:
            self.progress_bar.stop()
            self.progress_frame.pack_forget()
        except tk.TclError:
            pass
        
        self.operation_in_progress = False
        
        if success:
            messagebox.showinfo(
                "✓ Borrow Complete",
                f"{item_name} has been delivered to the drop zone.\n\nPlease collect your item."
            )
            self.status_callback("Ready")
        else:
            messagebox.showerror(
                "Borrow Failed",
                f"Could not borrow {item_name}:\n\n{message}"
            )
            self.status_callback("Error")
        
        if self.is_active:
            try:
                self.refresh_item_list()
            except tk.TclError:
                pass
    
    def handle_back(self):
        """Handle back button"""
        if self.operation_in_progress:
            result = messagebox.askyesno(
                "Operation in Progress",
                "An operation is in progress. Go back anyway?\n\nThe robot will continue its movement."
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
