"""
Calibration screen for position setup with live camera feed
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
    THEME_COLOR_WARNING,
    THEME_COLOR_TEXT_LIGHT,
    POSITION_NAMES,
    JOINT_MIN,
    JOINT_MAX
)
from utils.logger import RobotLogger


class CalibrationScreen:
    """
    Visual position calibration with sliders and live camera feed
    """
    
    def __init__(self, parent, robot_controller, position_manager, vision_system, back_callback, status_callback):
        """Initialize calibration interface"""
        self.logger = RobotLogger()
        self.parent = parent
        self.robot = robot_controller
        self.positions = position_manager
        self.vision = vision_system
        self.back_callback = back_callback
        self.status_callback = status_callback
        
        self.frame = tk.Frame(parent, bg=THEME_COLOR_PRIMARY)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.sliders = []
        self.gripper_sliders = {}
        self.selected_position = tk.StringVar(value='home')
        self.camera_active = False
        
        self.create_ui()
        self.load_position_to_sliders('home')
    
    def create_ui(self):
        """Create calibration screen UI with camera panel"""
        # Header
        header = tk.Frame(self.frame, bg=THEME_COLOR_PRIMARY)
        header.pack(fill=tk.X, pady=(0, 10))
        
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
            text="CALIBRATION MODE",
            font=('Arial', 24, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        title.pack(side=tk.LEFT, padx=20)
        
        # Main content area - split into left (controls) and right (camera)
        main_content = tk.Frame(self.frame, bg=THEME_COLOR_PRIMARY)
        main_content.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Left side - Controls
        left_frame = tk.Frame(main_content, bg=THEME_COLOR_PRIMARY)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Position selector
        selector_frame = tk.Frame(left_frame, bg=THEME_COLOR_PRIMARY)
        selector_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            selector_frame,
            text="Select Position:",
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        position_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.selected_position,
            values=POSITION_NAMES,
            state='readonly',
            font=('Arial', 11),
            width=20
        )
        position_dropdown.pack(side=tk.LEFT)
        position_dropdown.bind('<<ComboboxSelected>>', self.on_position_changed)
        
        test_btn = tk.Button(
            selector_frame,
            text="Test Position",
            command=self.test_position,
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_ACCENT,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2'
        )
        test_btn.pack(side=tk.RIGHT)
        
        # Sliders container
        sliders_frame = tk.Frame(left_frame, bg=THEME_COLOR_SECONDARY, relief='raised', bd=2)
        sliders_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Joint sliders
        joints_label = tk.Label(
            sliders_frame,
            text="Joint Angles",
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        joints_label.pack(pady=10)
        
        self.create_sliders(sliders_frame)
        
        # Gripper sliders
        gripper_frame = tk.Frame(sliders_frame, bg=THEME_COLOR_SECONDARY)
        gripper_frame.pack(fill=tk.X, padx=10, pady=5)
        
        gripper_label = tk.Label(
            gripper_frame,
            text="Gripper Positions",
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        gripper_label.pack(pady=5)
        
        self.create_gripper_sliders(gripper_frame)
        
        # Buttons
        button_frame = tk.Frame(left_frame, bg=THEME_COLOR_PRIMARY)
        button_frame.pack(fill=tk.X)
        
        update_btn = tk.Button(
            button_frame,
            text="Update Position",
            command=self.update_position,
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_SUCCESS,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        update_btn.pack(side=tk.LEFT, padx=3)
        
        save_btn = tk.Button(
            button_frame,
            text="Save All",
            command=self.save_all_positions,
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_ACCENT,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        save_btn.pack(side=tk.LEFT, padx=3)
        
        reset_btn = tk.Button(
            button_frame,
            text="Reset All",
            command=self.reset_to_defaults,
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_WARNING,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        reset_btn.pack(side=tk.LEFT, padx=3)
        
        # Right side - Camera
        right_frame = tk.Frame(main_content, bg=THEME_COLOR_SECONDARY, relief='raised', bd=2, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        camera_title = tk.Label(
            right_frame,
            text="Live Camera Feed",
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        camera_title.pack(pady=10)
        
        # Camera display container with fixed size
        camera_container = tk.Frame(right_frame, bg='black', width=320, height=240)
        camera_container.pack(padx=10, pady=5)
        camera_container.pack_propagate(False)  # Prevent resizing
        
        # Camera display label inside container
        self.camera_display = tk.Label(
            camera_container,
            bg='black'
        )
        self.camera_display.pack(fill=tk.BOTH, expand=True)
        
        # Store the target size for camera updates
        self.camera_width = 320
        self.camera_height = 240
        
        # Camera status
        self.camera_status = tk.Label(
            right_frame,
            text="Camera: Off",
            font=('Arial', 10),
            bg=THEME_COLOR_SECONDARY,
            fg='#95A5A6'
        )
        self.camera_status.pack(pady=5)
        
        # Camera toggle button
        self.camera_btn = tk.Button(
            right_frame,
            text="Start Camera",
            command=self.toggle_camera,
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_SUCCESS,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        self.camera_btn.pack(pady=10)
        
        # Helpful hint
        hint_label = tk.Label(
            right_frame,
            text="Use camera to help calibrate\nobservation_position for\naccurate item detection",
            font=('Arial', 9),
            bg=THEME_COLOR_SECONDARY,
            fg='#95A5A6',
            justify=tk.CENTER
        )
        hint_label.pack(pady=10)
    
    def create_sliders(self, parent):
        """Create 6 joint sliders"""
        for i in range(6):
            slider_frame = tk.Frame(parent, bg=THEME_COLOR_SECONDARY)
            slider_frame.pack(fill=tk.X, padx=20, pady=5)
            
            # Label
            label = tk.Label(
                slider_frame,
                text=f"Joint {i+1}:",
                font=('Arial', 11),
                bg=THEME_COLOR_SECONDARY,
                fg=THEME_COLOR_TEXT_LIGHT,
                width=10,
                anchor=tk.W
            )
            label.pack(side=tk.LEFT)
            
            # Slider
            slider_var = tk.IntVar(value=90)
            slider = tk.Scale(
                slider_frame,
                from_=JOINT_MIN,
                to=JOINT_MAX,
                orient=tk.HORIZONTAL,
                variable=slider_var,
                bg=THEME_COLOR_SECONDARY,
                fg=THEME_COLOR_TEXT_LIGHT,
                highlightthickness=0,
                length=400,
                troughcolor=THEME_COLOR_PRIMARY
            )
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            # Value label
            value_label = tk.Label(
                slider_frame,
                textvariable=slider_var,
                font=('Arial', 11, 'bold'),
                bg=THEME_COLOR_SECONDARY,
                fg=THEME_COLOR_TEXT_LIGHT,
                width=5
            )
            value_label.pack(side=tk.LEFT)
            
            self.sliders.append(slider_var)
    
    def create_gripper_sliders(self, parent):
        """Create gripper open/closed sliders"""
        for name, label in [('gripper_open', 'Open Position:'), ('gripper_closed', 'Closed Position:')]:
            slider_frame = tk.Frame(parent, bg=THEME_COLOR_SECONDARY)
            slider_frame.pack(fill=tk.X, padx=20, pady=5)
            
            # Label
            label_widget = tk.Label(
                slider_frame,
                text=label,
                font=('Arial', 11),
                bg=THEME_COLOR_SECONDARY,
                fg=THEME_COLOR_TEXT_LIGHT,
                width=15,
                anchor=tk.W
            )
            label_widget.pack(side=tk.LEFT)
            
            # Slider
            slider_var = tk.IntVar(value=90)
            slider = tk.Scale(
                slider_frame,
                from_=JOINT_MIN,
                to=JOINT_MAX,
                orient=tk.HORIZONTAL,
                variable=slider_var,
                bg=THEME_COLOR_SECONDARY,
                fg=THEME_COLOR_TEXT_LIGHT,
                highlightthickness=0,
                length=300,
                troughcolor=THEME_COLOR_PRIMARY
            )
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            # Value label
            value_label = tk.Label(
                slider_frame,
                textvariable=slider_var,
                font=('Arial', 11, 'bold'),
                bg=THEME_COLOR_SECONDARY,
                fg=THEME_COLOR_TEXT_LIGHT,
                width=5
            )
            value_label.pack(side=tk.LEFT)
            
            self.gripper_sliders[name] = slider_var
    
    def on_position_changed(self, event=None):
        """Handle position selection change"""
        position_name = self.selected_position.get()
        self.load_position_to_sliders(position_name)
    
    def load_position_to_sliders(self, position_name: str):
        """Load saved position values into sliders"""
        angles = self.positions.get_position(position_name)
        if angles is not None:
            for i, angle in enumerate(angles):
                self.sliders[i].set(angle)
            
            self.logger.debug(f"Loaded position: {position_name}")
        
        # Load gripper positions
        for name in ['gripper_open', 'gripper_closed']:
            value = self.positions.get_position(name)
            if value is not None:
                self.gripper_sliders[name].set(value)
    
    def test_position(self):
        """Move robot to current slider values"""
        if not self.robot.is_connected():
            messagebox.showerror("Error", "Robot not connected")
            return
        
        result = messagebox.askyesno(
            "Test Position",
            "Move robot to current slider positions?",
            icon='question'
        )
        
        if not result:
            return
        
        # Get current slider values
        angles = [slider.get() for slider in self.sliders]
        
        # Move robot in background
        def move():
            self.status_callback("Testing position...")
            if self.robot.move_to_joint_angles(angles):
                self.parent.after(0, lambda: messagebox.showinfo(
                    "Test Complete",
                    "Robot moved to test position"
                ))
                self.parent.after(0, lambda: self.status_callback("Ready"))
            else:
                self.parent.after(0, lambda: messagebox.showerror(
                    "Test Failed",
                    "Failed to move robot"
                ))
                self.parent.after(0, lambda: self.status_callback("Error"))
        
        thread = threading.Thread(target=move, daemon=True)
        thread.start()
    
    def update_position(self):
        """Save current slider values for selected position"""
        position_name = self.selected_position.get()
        angles = [slider.get() for slider in self.sliders]
        
        if self.positions.set_position(position_name, angles):
            messagebox.showinfo(
                "Position Updated",
                f"{position_name} has been updated.\n\nDon't forget to click 'Save All Positions' to persist changes!"
            )
            self.logger.info(f"Position updated: {position_name}")
        else:
            messagebox.showerror("Error", "Failed to update position")
    
    def save_all_positions(self):
        """Write all positions to positions.json"""
        # Update gripper positions
        for name, var in self.gripper_sliders.items():
            self.positions.set_position(name, var.get())
        
        if self.positions.save_positions():
            messagebox.showinfo(
                "Saved",
                "All positions have been saved to positions.json"
            )
            self.logger.info("All positions saved")
        else:
            messagebox.showerror("Error", "Failed to save positions")
    
    def reset_to_defaults(self):
        """Reset all positions to defaults"""
        result = messagebox.askyesno(
            "Reset Positions",
            "Reset all positions to default values?\n\nThis will overwrite all calibrated positions!",
            icon='warning'
        )
        
        if result:
            self.positions.reset_to_defaults()
            self.load_position_to_sliders(self.selected_position.get())
            messagebox.showinfo("Reset", "All positions reset to defaults")
    
    def handle_back(self):
        """Handle back button - cleanup and return to main menu"""
        self.cleanup()
        self.back_callback()
    
    def toggle_camera(self):
        """Toggle camera feed on/off"""
        if self.camera_active:
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        """Start live camera feed"""
        if self.vision is None:
            messagebox.showerror("Error", "Vision system not available")
            return
        
        self.camera_active = True
        self.camera_btn.config(text="Stop Camera", bg='#E74C3C')
        self.camera_status.config(text="Camera: Active", fg=THEME_COLOR_SUCCESS)
        self.update_camera_feed()
        self.logger.info("Camera feed started")
    
    def stop_camera(self):
        """Stop live camera feed"""
        self.camera_active = False
        self.camera_btn.config(text="Start Camera", bg=THEME_COLOR_SUCCESS)
        self.camera_status.config(text="Camera: Off", fg='#95A5A6')
        
        # Clear camera display
        self.camera_display.config(image='')
        self.logger.info("Camera feed stopped")
    
    def update_camera_feed(self):
        """Update camera display with current frame"""
        if not self.camera_active:
            return
        
        try:
            frame = self.vision.get_live_feed()
            if frame is not None:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)
                
                # Resize to exact display size (maintains aspect ratio within bounds)
                pil_image = pil_image.resize((self.camera_width, self.camera_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                
                # Update label
                self.camera_display.config(image=photo)
                self.camera_display.image = photo  # Keep reference
        
        except Exception as e:
            self.logger.debug(f"Camera feed update error: {e}")
        
        # Schedule next update (~30 FPS)
        if self.camera_active:
            self.parent.after(33, self.update_camera_feed)
    
    def cleanup(self):
        """Cleanup when leaving screen"""
        self.logger.info("Cleaning up calibration screen")
        self.stop_camera()
