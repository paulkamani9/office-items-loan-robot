"""
Test screen for testing operations
"""

import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import threading
import cv2
from PIL import Image, ImageTk
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    THEME_COLOR_PRIMARY,
    THEME_COLOR_SECONDARY,
    THEME_COLOR_ACCENT,
    THEME_COLOR_SUCCESS,
    THEME_COLOR_TEXT_LIGHT,
    ITEM_CLASSES
)
from utils.logger import RobotLogger


class TestScreen:
    """
    Test operations interface
    """
    
    def __init__(self, parent, robot_controller, vision_system, back_callback, status_callback):
        """Initialize test interface"""
        self.logger = RobotLogger()
        self.parent = parent
        self.robot = robot_controller
        self.vision = vision_system
        self.back_callback = back_callback
        self.status_callback = status_callback
        
        self.frame = tk.Frame(parent, bg=THEME_COLOR_PRIMARY)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.camera_window = None
        self.camera_active = False
        
        self.create_ui()
    
    def create_ui(self):
        """Create test screen UI"""
        # Header
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
            text="TEST MODE",
            font=('Arial', 24, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        title.pack(side=tk.LEFT, padx=20)
        
        # Scrollable content
        canvas = tk.Canvas(self.frame, bg=THEME_COLOR_PRIMARY, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=THEME_COLOR_PRIMARY)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Test Borrow Operations
        borrow_label = tk.Label(
            scrollable_frame,
            text="Test Borrow Operations",
            font=('Arial', 16, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            anchor=tk.W
        )
        borrow_label.pack(fill=tk.X, pady=(10, 10))
        
        borrow_grid = tk.Frame(scrollable_frame, bg=THEME_COLOR_PRIMARY)
        borrow_grid.pack(fill=tk.X, pady=(0, 20))
        
        self.create_item_buttons(borrow_grid, "borrow")
        
        # Test Return Operations
        return_label = tk.Label(
            scrollable_frame,
            text="Test Return Operations",
            font=('Arial', 16, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            anchor=tk.W
        )
        return_label.pack(fill=tk.X, pady=(20, 10))
        
        return_grid = tk.Frame(scrollable_frame, bg=THEME_COLOR_PRIMARY)
        return_grid.pack(fill=tk.X, pady=(0, 20))
        
        self.create_item_buttons(return_grid, "return")
        
        # Test Camera
        camera_label = tk.Label(
            scrollable_frame,
            text="Test Camera",
            font=('Arial', 16, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            anchor=tk.W
        )
        camera_label.pack(fill=tk.X, pady=(20, 10))
        
        camera_frame = tk.Frame(scrollable_frame, bg=THEME_COLOR_PRIMARY)
        camera_frame.pack(fill=tk.X, pady=(0, 20))
        
        test_camera_btn = tk.Button(
            camera_frame,
            text="Test Classification",
            command=self.test_camera,
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_ACCENT,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        test_camera_btn.pack(side=tk.LEFT, padx=5)
        
        # Test Servo Controls (for debugging)
        servo_label = tk.Label(
            scrollable_frame,
            text="Test Individual Servos",
            font=('Arial', 16, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            anchor=tk.W
        )
        servo_label.pack(fill=tk.X, pady=(20, 10))
        
        servo_frame = tk.Frame(scrollable_frame, bg=THEME_COLOR_PRIMARY)
        servo_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Test Gripper (Servo 6)
        gripper_open_btn = tk.Button(
            servo_frame,
            text="Open Gripper (S6)",
            command=self.test_gripper_open,
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_SUCCESS,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        gripper_open_btn.pack(side=tk.LEFT, padx=5)
        
        gripper_close_btn = tk.Button(
            servo_frame,
            text="Close Gripper (S6)",
            command=self.test_gripper_close,
            font=('Arial', 11, 'bold'),
            bg='#E74C3C',
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        gripper_close_btn.pack(side=tk.LEFT, padx=5)
        
        # Test Wrist (Servo 5)
        wrist_mid_btn = tk.Button(
            servo_frame,
            text="Wrist 90° (S5)",
            command=lambda: self.test_wrist(90),
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_ACCENT,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        wrist_mid_btn.pack(side=tk.LEFT, padx=5)
        
        wrist_left_btn = tk.Button(
            servo_frame,
            text="Wrist 0° (S5)",
            command=lambda: self.test_wrist(0),
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_ACCENT,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        wrist_left_btn.pack(side=tk.LEFT, padx=5)
        
        wrist_right_btn = tk.Button(
            servo_frame,
            text="Wrist 180° (S5)",
            command=lambda: self.test_wrist(180),
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_ACCENT,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        wrist_right_btn.pack(side=tk.LEFT, padx=5)
    
    def create_item_buttons(self, parent, operation):
        """Create grid of item test buttons"""
        row = 0
        col = 0
        
        for item_name in ITEM_CLASSES:
            card = tk.Frame(parent, bg=THEME_COLOR_SECONDARY, relief='raised', bd=2)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            
            # Item name
            name_label = tk.Label(
                card,
                text=item_name,
                font=('Arial', 11, 'bold'),
                bg=THEME_COLOR_SECONDARY,
                fg=THEME_COLOR_TEXT_LIGHT,
                wraplength=150
            )
            name_label.pack(pady=(10, 5))
            
            # Test button
            btn_text = f"Test {operation.capitalize()}"
            btn = tk.Button(
                card,
                text=btn_text,
                command=lambda item=item_name, op=operation: self.test_operation(item, op),
                font=('Arial', 10, 'bold'),
                bg=THEME_COLOR_ACCENT,
                fg=THEME_COLOR_TEXT_LIGHT,
                relief='flat',
                padx=15,
                pady=8,
                cursor='hand2'
            )
            btn.pack(pady=(0, 10))
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            parent.columnconfigure(i, weight=1)
    
    def test_operation(self, item_name: str, operation: str):
        """Test borrow or return operation"""
        if not self.robot.is_connected():
            messagebox.showerror("Error", "Robot not connected")
            return
        
        result = messagebox.askyesno(
            f"Test {operation.capitalize()}",
            f"Test {operation} operation for {item_name}?\n\nNote: This does NOT update state."
        )
        
        if not result:
            return
        
        # Create progress window
        progress_window = Toplevel(self.parent)
        progress_window.title(f"Testing {operation.capitalize()}")
        progress_window.geometry("400x150")
        progress_window.configure(bg=THEME_COLOR_PRIMARY)
        progress_window.transient(self.parent)
        progress_window.grab_set()
        
        status_label = tk.Label(
            progress_window,
            text=f"Testing {operation} for {item_name}...",
            font=('Arial', 12),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            wraplength=350
        )
        status_label.pack(pady=20)
        
        progress_bar = ttk.Progressbar(
            progress_window,
            mode='indeterminate',
            length=300
        )
        progress_bar.pack(pady=10)
        progress_bar.start(10)
        
        # Run test in background
        def test_thread():
            def update_status(msg):
                status_label.config(text=msg)
            
            try:
                if operation == "borrow":
                    result = self.robot.borrow_item(item_name, status_callback=update_status)
                else:  # return
                    result = self.robot.return_item(item_name, status_callback=update_status)
                
                # Close progress window
                progress_window.after(0, progress_window.destroy)
                
                # Show result
                if result.get('success', False):
                    self.parent.after(0, lambda: self.show_test_result(
                        True,
                        f"{operation.capitalize()} test completed successfully for {item_name}"
                    ))
                else:
                    self.parent.after(0, lambda: self.show_test_result(
                        False,
                        f"{operation.capitalize()} test failed:\n{result.get('message', 'Unknown error')}"
                    ))
            
            except Exception as e:
                progress_window.after(0, progress_window.destroy)
                self.parent.after(0, lambda: self.show_test_result(False, str(e)))
        
        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()
    
    def test_camera(self):
        """Open window showing live camera feed with classification"""
        if self.camera_active:
            messagebox.showwarning("Already Active", "Camera test is already running")
            return
        
        self.camera_active = True
        
        # Create camera window
        self.camera_window = Toplevel(self.parent)
        self.camera_window.title("Camera Test")
        self.camera_window.geometry("600x500")
        self.camera_window.configure(bg=THEME_COLOR_PRIMARY)
        self.camera_window.protocol("WM_DELETE_WINDOW", self.close_camera_window)
        
        # Camera display
        camera_label = tk.Label(
            self.camera_window,
            bg='black'
        )
        camera_label.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Results display
        results_frame = tk.Frame(self.camera_window, bg=THEME_COLOR_SECONDARY, relief='raised', bd=2)
        results_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        results_label = tk.Label(
            results_frame,
            text="Classification Results",
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        results_label.pack(pady=10)
        
        self.camera_results = tk.Label(
            results_frame,
            text="Waiting for classification...",
            font=('Arial', 11),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            wraplength=500,
            justify=tk.LEFT
        )
        self.camera_results.pack(pady=10, padx=20)
        
        # Start camera feed
        self.update_camera_test(camera_label)
    
    def update_camera_test(self, display_label):
        """Update camera test window"""
        if not self.camera_active or self.camera_window is None:
            return
        
        try:
            # Capture and classify
            frame = self.vision.capture_frame()
            if frame is not None:
                # Display frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                pil_image.thumbnail((560, 420), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(pil_image)
                display_label.config(image=photo)
                display_label.image = photo
                
                # Classify
                result = self.vision.classify_item(frame)
                
                # Update results
                if result.get('success', False):
                    text = f"✓ Detected: {result['class_name']}\n"
                    text += f"Confidence: {result['confidence']:.1%}\n\n"
                    text += "All predictions:\n"
                    for cls, conf in result.get('all_predictions', {}).items():
                        text += f"  {cls}: {conf:.1%}\n"
                    self.camera_results.config(text=text, fg=THEME_COLOR_SUCCESS)
                else:
                    error = result.get('error', 'No detection')
                    text = f"✗ {error}\n\n"
                    if result.get('class_name'):
                        text += f"Detected: {result['class_name']}\n"
                        text += f"Confidence: {result.get('confidence', 0):.1%}"
                    self.camera_results.config(text=text, fg='#F39C12')
        
        except Exception as e:
            self.logger.debug(f"Camera test update error: {e}")
        
        # Schedule next update
        if self.camera_active:
            self.camera_window.after(100, lambda: self.update_camera_test(display_label))
    
    def close_camera_window(self):
        """Close camera test window"""
        self.camera_active = False
        if self.camera_window:
            self.camera_window.destroy()
            self.camera_window = None
    
    def show_test_result(self, success: bool, message: str):
        """Display test result to user"""
        if success:
            messagebox.showinfo("Test Complete", message)
            self.status_callback("Test completed")
        else:
            messagebox.showerror("Test Failed", message)
            self.status_callback("Test failed")
    
    def test_gripper_open(self):
        """Test opening the gripper (servo 6)"""
        if not self.robot.is_connected():
            messagebox.showerror("Error", "Robot not connected")
            return
        
        self.status_callback("Testing gripper open...")
        try:
            result = self.robot.open_gripper()
            if result:
                messagebox.showinfo("Success", "Gripper opened successfully!")
            else:
                messagebox.showerror("Failed", "Failed to open gripper")
        except Exception as e:
            messagebox.showerror("Error", f"Gripper test error: {e}")
        self.status_callback("Ready")
    
    def test_gripper_close(self):
        """Test closing the gripper (servo 6)"""
        if not self.robot.is_connected():
            messagebox.showerror("Error", "Robot not connected")
            return
        
        self.status_callback("Testing gripper close...")
        try:
            result = self.robot.close_gripper()
            if result:
                messagebox.showinfo("Success", "Gripper closed successfully!")
            else:
                messagebox.showerror("Failed", "Failed to close gripper")
        except Exception as e:
            messagebox.showerror("Error", f"Gripper test error: {e}")
        self.status_callback("Ready")
    
    def test_wrist(self, angle: int):
        """Test moving the wrist (servo 5) to specific angle"""
        if not self.robot.is_connected():
            messagebox.showerror("Error", "Robot not connected")
            return
        
        self.status_callback(f"Testing wrist to {angle}°...")
        try:
            result = self.robot.move_wrist(angle, speed=500)
            if result:
                messagebox.showinfo("Success", f"Wrist moved to {angle}°!")
            else:
                messagebox.showerror("Failed", f"Failed to move wrist to {angle}°")
        except Exception as e:
            messagebox.showerror("Error", f"Wrist test error: {e}")
        self.status_callback("Ready")
    
    def handle_back(self):
        """Handle back button - cleanup and return to main menu"""
        self.cleanup()
        self.back_callback()
    
    def cleanup(self):
        """Cleanup when leaving screen"""
        self.logger.info("Cleaning up test screen")
        self.close_camera_window()
