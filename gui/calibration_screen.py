"""
Calibration screen for position setup
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
    THEME_COLOR_WARNING,
    THEME_COLOR_TEXT_LIGHT,
    POSITION_NAMES,
    JOINT_MIN,
    JOINT_MAX
)
from utils.logger import RobotLogger


class CalibrationScreen:
    """
    Visual position calibration with sliders
    """
    
    def __init__(self, parent, robot_controller, position_manager, back_callback, status_callback):
        """Initialize calibration interface"""
        self.logger = RobotLogger()
        self.parent = parent
        self.robot = robot_controller
        self.positions = position_manager
        self.back_callback = back_callback
        self.status_callback = status_callback
        
        self.frame = tk.Frame(parent, bg=THEME_COLOR_PRIMARY)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.sliders = []
        self.gripper_sliders = {}
        self.selected_position = tk.StringVar(value='home')
        
        self.create_ui()
        self.load_position_to_sliders('home')
    
    def create_ui(self):
        """Create calibration screen UI"""
        # Header
        header = tk.Frame(self.frame, bg=THEME_COLOR_PRIMARY)
        header.pack(fill=tk.X, pady=(0, 20))
        
        back_btn = tk.Button(
            header,
            text="← Back",
            command=self.back_callback,
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
        
        # Content area
        content = tk.Frame(self.frame, bg=THEME_COLOR_PRIMARY)
        content.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Position selector
        selector_frame = tk.Frame(content, bg=THEME_COLOR_PRIMARY)
        selector_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            selector_frame,
            text="Select Position:",
            font=('Arial', 14, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        position_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.selected_position,
            values=POSITION_NAMES,
            state='readonly',
            font=('Arial', 12),
            width=25
        )
        position_dropdown.pack(side=tk.LEFT)
        position_dropdown.bind('<<ComboboxSelected>>', self.on_position_changed)
        
        test_btn = tk.Button(
            selector_frame,
            text="Test Position",
            command=self.test_position,
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_ACCENT,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        test_btn.pack(side=tk.RIGHT)
        
        # Sliders container
        sliders_frame = tk.Frame(content, bg=THEME_COLOR_SECONDARY, relief='raised', bd=2)
        sliders_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Joint sliders
        joints_label = tk.Label(
            sliders_frame,
            text="Joint Angles",
            font=('Arial', 14, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        joints_label.pack(pady=15)
        
        self.create_sliders(sliders_frame)
        
        # Gripper sliders
        gripper_frame = tk.Frame(sliders_frame, bg=THEME_COLOR_SECONDARY)
        gripper_frame.pack(fill=tk.X, padx=20, pady=10)
        
        gripper_label = tk.Label(
            gripper_frame,
            text="Gripper Positions",
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        gripper_label.pack(pady=10)
        
        self.create_gripper_sliders(gripper_frame)
        
        # Buttons
        button_frame = tk.Frame(content, bg=THEME_COLOR_PRIMARY)
        button_frame.pack(fill=tk.X)
        
        update_btn = tk.Button(
            button_frame,
            text="Update Position",
            command=self.update_position,
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_SUCCESS,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        update_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = tk.Button(
            button_frame,
            text="Save All Positions",
            command=self.save_all_positions,
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_ACCENT,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(
            button_frame,
            text="Reset All",
            command=self.reset_to_defaults,
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_WARNING,
            fg=THEME_COLOR_TEXT_LIGHT,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        reset_btn.pack(side=tk.LEFT, padx=5)
    
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
    
    def cleanup(self):
        """Cleanup when leaving screen"""
        pass
