"""
Main application window and navigation
Elegant, user-friendly design with Borrow/Return as main focus
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    THEME_COLOR_PRIMARY,
    THEME_COLOR_SECONDARY,
    THEME_COLOR_ACCENT,
    THEME_COLOR_DANGER,
    THEME_COLOR_SUCCESS,
    THEME_COLOR_TEXT_LIGHT
)
from utils.logger import RobotLogger


# Modern color scheme
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
    'card_bg': '#1e3a5f'
}


class MainWindow:
    """
    Main application window with elegant, user-friendly design
    """
    
    def __init__(self, root, vision_system, robot_controller, state_manager, position_manager):
        """Initialize main window"""
        self.logger = RobotLogger()
        self.root = root
        self.vision = vision_system
        self.robot = robot_controller
        self.state = state_manager
        self.positions = position_manager
        
        # Setup window
        self.root.title("Office Items Loan Robot")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Current screen tracking
        self.current_screen = None
        self.current_screen_frame = None
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main container
        self.container = tk.Frame(self.root, bg=COLORS['bg_dark'])
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self.create_header()
        
        # Create content area
        self.content_frame = tk.Frame(self.container, bg=COLORS['bg_dark'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create status bar
        self.create_status_bar()
        
        # Show main menu
        self.show_main_menu()
        
        # Start joint angle update thread
        self.running = True
        self.update_thread = threading.Thread(target=self.update_joint_display_loop, daemon=True)
        self.update_thread.start()
        
        self.logger.info("Main window initialized")
    
    def create_menu_bar(self):
        """Create top menu bar for Settings and Test"""
        menubar = tk.Menu(self.root, bg=COLORS['bg_medium'], fg=COLORS['text_white'],
                         activebackground=COLORS['accent_blue'], activeforeground='white',
                         relief='flat', bd=0)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['bg_medium'], 
                            fg=COLORS['text_white'],
                            activebackground=COLORS['accent_blue'])
        tools_menu.add_command(label="⚙  Calibration / Settings", command=self.show_settings_screen)
        tools_menu.add_command(label="🧪  Test Robot", command=self.show_test_screen)
        tools_menu.add_separator()
        tools_menu.add_command(label="🏠  Home Position", command=self.go_home)
        
        menubar.add_cascade(label="  Tools  ", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['bg_medium'],
                           fg=COLORS['text_white'],
                           activebackground=COLORS['accent_blue'])
        help_menu.add_command(label="About", command=self.show_about)
        
        menubar.add_cascade(label="  Help  ", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_header(self):
        """Create elegant header with title and emergency stop"""
        header = tk.Frame(self.container, bg=COLORS['bg_medium'], height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Left side - Logo/Title
        title_frame = tk.Frame(header, bg=COLORS['bg_medium'])
        title_frame.pack(side=tk.LEFT, padx=25, pady=10)
        
        # Robot icon
        icon_label = tk.Label(
            title_frame,
            text="🤖",
            font=('Arial', 28),
            bg=COLORS['bg_medium']
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Title text
        title_text = tk.Frame(title_frame, bg=COLORS['bg_medium'])
        title_text.pack(side=tk.LEFT)
        
        title_label = tk.Label(
            title_text,
            text="Office Items Loan Robot",
            font=('Arial', 18, 'bold'),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_white']
        )
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(
            title_text,
            text="Automated Item Management System",
            font=('Arial', 9),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_gray']
        )
        subtitle_label.pack(anchor='w')
        
        # Right side - Emergency Stop
        estop_btn = tk.Button(
            header,
            text="⚠ EMERGENCY STOP",
            command=self.emergency_stop,
            font=('Arial', 11, 'bold'),
            bg=COLORS['accent_red'],
            fg='white',
            activebackground='#c0392b',
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        estop_btn.pack(side=tk.RIGHT, padx=25)
        
        # Connection status indicator
        self.connection_indicator = tk.Label(
            header,
            text="● Connected" if self.robot.is_connected() else "○ Disconnected",
            font=('Arial', 10),
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_green'] if self.robot.is_connected() else COLORS['accent_red']
        )
        self.connection_indicator.pack(side=tk.RIGHT, padx=10)
    
    def create_status_bar(self):
        """Create status bar at bottom"""
        status_bar = tk.Frame(self.container, bg=COLORS['bg_medium'], height=35)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        
        # Joint angles display
        self.joints_label = tk.Label(
            status_bar,
            text="Joints: [-- -- -- -- -- --]",
            font=('Courier', 9),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_gray']
        )
        self.joints_label.pack(side=tk.LEFT, padx=20, pady=8)
        
        # Status message
        self.status_label = tk.Label(
            status_bar,
            text="Ready",
            font=('Arial', 10),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_white']
        )
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=8)
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def update_joint_display_loop(self):
        """Background thread for updating joint angles"""
        while self.running:
            try:
                if self.robot.is_connected():
                    angles = self.robot.get_current_angles()
                    angles_str = ' '.join([f"{a:3d}°" for a in angles])
                    self.joints_label.config(text=f"Joints: [{angles_str}]")
            except Exception as e:
                self.logger.debug(f"Joint display update error: {e}")
            
            threading.Event().wait(0.5)
    
    def clear_content(self):
        """Clear current content frame and cleanup any running processes"""
        if self.current_screen is not None:
            if hasattr(self.current_screen, 'cleanup'):
                try:
                    self.current_screen.cleanup()
                except Exception as e:
                    self.logger.debug(f"Screen cleanup error: {e}")
            self.current_screen = None
        
        if self.current_screen_frame is not None:
            try:
                self.current_screen_frame.destroy()
            except Exception as e:
                self.logger.debug(f"Frame destroy error: {e}")
            self.current_screen_frame = None
        
        for widget in self.content_frame.winfo_children():
            try:
                widget.destroy()
            except Exception as e:
                self.logger.debug(f"Widget destroy error: {e}")
    
    def show_main_menu(self):
        """Create elegant main menu focused on Borrow and Return"""
        self.clear_content()
        self.update_status("Ready")
        
        # Main container
        menu_frame = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        menu_frame.pack(fill=tk.BOTH, expand=True)
        self.current_screen_frame = menu_frame
        
        # Welcome message
        welcome_frame = tk.Frame(menu_frame, bg=COLORS['bg_dark'])
        welcome_frame.pack(pady=(40, 30))
        
        welcome_label = tk.Label(
            welcome_frame,
            text="What would you like to do?",
            font=('Arial', 24, 'bold'),
            bg=COLORS['bg_dark'],
            fg=COLORS['text_white']
        )
        welcome_label.pack()
        
        subtitle = tk.Label(
            welcome_frame,
            text="Select an option below to get started",
            font=('Arial', 12),
            bg=COLORS['bg_dark'],
            fg=COLORS['text_gray']
        )
        subtitle.pack(pady=(5, 0))
        
        # Cards container
        cards_frame = tk.Frame(menu_frame, bg=COLORS['bg_dark'])
        cards_frame.pack(expand=True)
        
        # Borrow Card
        borrow_card = self.create_action_card(
            cards_frame,
            icon="📦",
            title="BORROW",
            description="Get an item from storage\ndelivered to the drop zone",
            color=COLORS['accent_blue'],
            command=self.show_borrow_screen
        )
        borrow_card.pack(side=tk.LEFT, padx=30, pady=20)
        
        # Return Card
        return_card = self.create_action_card(
            cards_frame,
            icon="↩️",
            title="RETURN",
            description="Return an item to storage\nusing camera detection",
            color=COLORS['accent_green'],
            command=self.show_return_screen
        )
        return_card.pack(side=tk.LEFT, padx=30, pady=20)
        
        # Quick stats
        self.create_stats_panel(menu_frame)
    
    def create_action_card(self, parent, icon, title, description, color, command):
        """Create a clickable action card"""
        card = tk.Frame(parent, bg=COLORS['card_bg'], cursor='hand2')
        card.configure(highlightbackground=color, highlightthickness=2)
        
        # Make entire card clickable
        def on_enter(e):
            card.configure(highlightthickness=4)
        
        def on_leave(e):
            card.configure(highlightthickness=2)
        
        def on_click(e):
            command()
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        card.bind('<Button-1>', on_click)
        
        # Card content
        content = tk.Frame(card, bg=COLORS['card_bg'])
        content.pack(padx=40, pady=35)
        
        # Bind children too
        for child in [content]:
            child.bind('<Button-1>', on_click)
        
        # Icon
        icon_label = tk.Label(
            content,
            text=icon,
            font=('Arial', 48),
            bg=COLORS['card_bg']
        )
        icon_label.pack()
        icon_label.bind('<Button-1>', on_click)
        
        # Title
        title_label = tk.Label(
            content,
            text=title,
            font=('Arial', 22, 'bold'),
            bg=COLORS['card_bg'],
            fg=color
        )
        title_label.pack(pady=(15, 10))
        title_label.bind('<Button-1>', on_click)
        
        # Description
        desc_label = tk.Label(
            content,
            text=description,
            font=('Arial', 11),
            bg=COLORS['card_bg'],
            fg=COLORS['text_gray'],
            justify=tk.CENTER
        )
        desc_label.pack()
        desc_label.bind('<Button-1>', on_click)
        
        # Button
        btn = tk.Button(
            content,
            text=f"Start {title.capitalize()}",
            font=('Arial', 12, 'bold'),
            bg=color,
            fg='white',
            activebackground=color,
            relief='flat',
            padx=30,
            pady=10,
            cursor='hand2',
            command=command
        )
        btn.pack(pady=(25, 0))
        
        return card
    
    def create_stats_panel(self, parent):
        """Create quick stats panel showing item availability"""
        stats_frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        stats_frame.pack(fill=tk.X, padx=50, pady=(30, 20))
        
        # Title
        stats_title = tk.Label(
            stats_frame,
            text="📊 Quick Status",
            font=('Arial', 12, 'bold'),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_white']
        )
        stats_title.pack(side=tk.LEFT, padx=20, pady=12)
        
        # Get stats
        all_status = self.state.get_all_status()
        available = sum(1 for s in all_status.values() if s == self.state.STATUS_AVAILABLE)
        loaned = sum(1 for s in all_status.values() if s == self.state.STATUS_LOANED_OUT)
        total = len(all_status)
        
        # Stats labels
        available_label = tk.Label(
            stats_frame,
            text=f"✓ {available} Available",
            font=('Arial', 11),
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_green']
        )
        available_label.pack(side=tk.LEFT, padx=20, pady=12)
        
        loaned_label = tk.Label(
            stats_frame,
            text=f"◐ {loaned} On Loan",
            font=('Arial', 11),
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_orange']
        )
        loaned_label.pack(side=tk.LEFT, padx=20, pady=12)
        
        total_label = tk.Label(
            stats_frame,
            text=f"Total: {total} items",
            font=('Arial', 11),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_gray']
        )
        total_label.pack(side=tk.RIGHT, padx=20, pady=12)
    
    def show_borrow_screen(self):
        """Switch to borrow interface"""
        from gui.borrow_screen import BorrowScreen
        self.clear_content()
        self.current_screen = BorrowScreen(
            self.content_frame,
            self.state,
            self.robot,
            self.show_main_menu,
            self.update_status
        )
        if hasattr(self.current_screen, 'frame'):
            self.current_screen_frame = self.current_screen.frame
    
    def show_return_screen(self):
        """Switch to return interface"""
        from gui.return_screen import ReturnScreen
        self.clear_content()
        self.current_screen = ReturnScreen(
            self.content_frame,
            self.vision,
            self.robot,
            self.state,
            self.show_main_menu,
            self.update_status
        )
        if hasattr(self.current_screen, 'frame'):
            self.current_screen_frame = self.current_screen.frame
    
    def show_settings_screen(self):
        """Switch to calibration/settings interface"""
        from gui.calibration_screen import CalibrationScreen
        self.clear_content()
        self.current_screen = CalibrationScreen(
            self.content_frame,
            self.robot,
            self.positions,
            self.vision,
            self.show_main_menu,
            self.update_status
        )
        if hasattr(self.current_screen, 'frame'):
            self.current_screen_frame = self.current_screen.frame
    
    def show_test_screen(self):
        """Switch to test operations interface"""
        from gui.test_screen import TestScreen
        self.clear_content()
        self.current_screen = TestScreen(
            self.content_frame,
            self.robot,
            self.vision,
            self.show_main_menu,
            self.update_status
        )
        if hasattr(self.current_screen, 'frame'):
            self.current_screen_frame = self.current_screen.frame
    
    def go_home(self):
        """Move robot to home position"""
        if messagebox.askyesno("Go Home", "Move robot to home position?"):
            self.update_status("Moving to home...")
            threading.Thread(target=self._go_home_thread, daemon=True).start()
    
    def _go_home_thread(self):
        """Background thread for going home"""
        try:
            self.robot.move_home()
            self.root.after(0, lambda: self.update_status("Ready"))
        except Exception as e:
            self.logger.error(f"Go home error: {e}")
            self.root.after(0, lambda: self.update_status("Error"))
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "Office Items Loan Robot\n\n"
            "Version 1.0\n\n"
            "Automated item management system using\n"
            "Yahboom Dofbot robot arm and YOLO vision.\n\n"
            "Settings and Test functions available\n"
            "in the Tools menu."
        )
    
    def emergency_stop(self):
        """Handle emergency stop button"""
        result = messagebox.askyesno(
            "Emergency Stop",
            "Stop all robot movements immediately?",
            icon='warning'
        )
        
        if result:
            self.robot.emergency_stop()
            self.update_status("⚠ EMERGENCY STOP")
            messagebox.showinfo("Emergency Stop", "Robot stopped.")
    
    def cleanup(self):
        """Cleanup on application close"""
        self.logger.info("Shutting down application...")
        self.running = False
        
        if self.current_screen and hasattr(self.current_screen, 'cleanup'):
            self.current_screen.cleanup()
        
        if self.vision:
            self.vision.cleanup()
        
        if self.robot:
            self.robot.cleanup()
        
        self.logger.info("Application shutdown complete")
