"""
Main application window and navigation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
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
    THEME_COLOR_TEXT_LIGHT
)
from utils.logger import RobotLogger
from modules.vision_system import VisionSystem
from modules.robot_controller import RobotController
from modules.state_manager import StateManager
from modules.position_manager import PositionManager


# Button styles
MAIN_BUTTON_STYLE = {
    'font': ('Arial', 18, 'bold'),
    'bg': THEME_COLOR_ACCENT,
    'fg': THEME_COLOR_TEXT_LIGHT,
    'activebackground': '#2980B9',
    'relief': 'flat',
    'bd': 0,
    'padx': 40,
    'pady': 25,
    'cursor': 'hand2',
    'width': 20
}

ESTOP_BUTTON_STYLE = {
    'font': ('Arial', 10, 'bold'),
    'bg': THEME_COLOR_DANGER,
    'fg': THEME_COLOR_TEXT_LIGHT,
    'activebackground': '#C0392B',
    'relief': 'flat',
    'bd': 0,
    'padx': 15,
    'pady': 8,
    'cursor': 'hand2'
}


class MainWindow:
    """
    Main application window and navigation
    """
    
    def __init__(self, root, vision_system, robot_controller, state_manager, position_manager):
        """
        Initialize main window
        - Setup Tkinter root
        - Initialize modules
        - Create main menu
        - Start joint angle update thread
        """
        self.logger = RobotLogger()
        self.root = root
        self.vision = vision_system
        self.robot = robot_controller
        self.state = state_manager
        self.positions = position_manager
        
        # Setup window
        self.root.title("Office Items Loan Robot")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=THEME_COLOR_PRIMARY)
        
        # Current screen
        self.current_screen = None
        self.current_screen_frame = None
        
        # Create main container
        self.container = tk.Frame(self.root, bg=THEME_COLOR_PRIMARY)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self.create_header()
        
        # Create content area
        self.content_frame = tk.Frame(self.container, bg=THEME_COLOR_PRIMARY)
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
    
    def create_header(self):
        """Create header with title and emergency stop"""
        header = tk.Frame(self.container, bg=THEME_COLOR_SECONDARY, height=60)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header,
            text="Office Items Loan Robot",
            font=('Arial', 20, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        title_label.pack(side=tk.LEFT, padx=20)
        
        # Emergency Stop button
        estop_btn = tk.Button(
            header,
            text="⚠ EMERGENCY STOP",
            command=self.emergency_stop,
            **ESTOP_BUTTON_STYLE
        )
        estop_btn.pack(side=tk.RIGHT, padx=20)
    
    def create_status_bar(self):
        """Create status bar at bottom"""
        status_bar = tk.Frame(self.container, bg=THEME_COLOR_SECONDARY, height=40)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        
        # Joint angles display
        self.joints_label = tk.Label(
            status_bar,
            text="Joints: [-- -- -- -- -- --]",
            font=('Courier', 10),
            bg=THEME_COLOR_SECONDARY,
            fg='#95A5A6',  # Grayed out
            anchor=tk.W
        )
        self.joints_label.pack(side=tk.LEFT, padx=20)
        
        # Status message
        self.status_label = tk.Label(
            status_bar,
            text="Status: Ready",
            font=('Arial', 10),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            anchor=tk.E
        )
        self.status_label.pack(side=tk.RIGHT, padx=20)
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.config(text=f"Status: {message}")
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
            
            threading.Event().wait(0.5)  # Update every 500ms
    
    def clear_content(self):
        """Clear current content frame and cleanup any running processes"""
        # First cleanup current screen (stop any running threads/processes)
        if self.current_screen is not None:
            if hasattr(self.current_screen, 'cleanup'):
                try:
                    self.current_screen.cleanup()
                except Exception as e:
                    self.logger.debug(f"Screen cleanup error: {e}")
            self.current_screen = None
        
        # Destroy the screen frame
        if self.current_screen_frame is not None:
            try:
                self.current_screen_frame.destroy()
            except Exception as e:
                self.logger.debug(f"Frame destroy error: {e}")
            self.current_screen_frame = None
        
        # Also destroy any remaining children in content_frame
        for widget in self.content_frame.winfo_children():
            try:
                widget.destroy()
            except Exception as e:
                self.logger.debug(f"Widget destroy error: {e}")
    
    def show_main_menu(self):
        """Create main menu with 4 buttons"""
        self.clear_content()
        self.update_status("Ready")
        
        # Create centered frame for buttons
        menu_frame = tk.Frame(self.content_frame, bg=THEME_COLOR_PRIMARY)
        menu_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.current_screen_frame = menu_frame
        
        # Borrow button
        borrow_btn = tk.Button(
            menu_frame,
            text="📦 BORROW",
            command=self.show_borrow_screen,
            **MAIN_BUTTON_STYLE
        )
        borrow_btn.pack(pady=15)
        
        # Return button
        return_btn = tk.Button(
            menu_frame,
            text="↩ RETURN",
            command=self.show_return_screen,
            **MAIN_BUTTON_STYLE
        )
        return_btn.pack(pady=15)
        
        # Settings button
        settings_btn = tk.Button(
            menu_frame,
            text="⚙ SETTINGS",
            command=self.show_settings_screen,
            **MAIN_BUTTON_STYLE
        )
        settings_btn.pack(pady=15)
        
        # Test button
        test_btn = tk.Button(
            menu_frame,
            text="🧪 TEST",
            command=self.show_test_screen,
            **MAIN_BUTTON_STYLE
        )
        test_btn.pack(pady=15)
    
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
        # Track the frame for proper cleanup
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
        # Track the frame for proper cleanup
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
        # Track the frame for proper cleanup
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
        # Track the frame for proper cleanup
        if hasattr(self.current_screen, 'frame'):
            self.current_screen_frame = self.current_screen.frame
    
    def emergency_stop(self):
        """Handle emergency stop button"""
        result = messagebox.askyesno(
            "Emergency Stop",
            "Stop all robot movements immediately?",
            icon='warning'
        )
        
        if result:
            self.robot.emergency_stop()
            self.update_status("EMERGENCY STOP ACTIVATED")
            messagebox.showinfo("Emergency Stop", "Robot stopped. System halted.")
    
    def cleanup(self):
        """Cleanup on application close"""
        self.logger.info("Shutting down application...")
        self.running = False
        
        # Cleanup current screen
        if self.current_screen and hasattr(self.current_screen, 'cleanup'):
            self.current_screen.cleanup()
        
        # Cleanup modules
        if self.vision:
            self.vision.cleanup()
        
        if self.robot:
            self.robot.cleanup()
        
        self.logger.info("Application shutdown complete")
