"""
Return screen with live camera feed and detection
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
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
    THEME_COLOR_DANGER,
    THEME_COLOR_WARNING,
    THEME_COLOR_TEXT_LIGHT,
    DETECTION_INTERVAL,
    INITIAL_WAIT_BEFORE_DETECTION,
    SAFETY_WAIT_AFTER_DETECTION,
    STABLE_DETECTION_COUNT,
    CONFIDENCE_THRESHOLD
)
from utils.logger import RobotLogger


class ReturnScreen:
    """
    Return interface with live camera feed
    """
    
    def __init__(self, parent, vision_system, robot_controller, state_manager, back_callback, status_callback):
        """Initialize return interface"""
        self.logger = RobotLogger()
        self.parent = parent
        self.vision = vision_system
        self.robot = robot_controller
        self.state = state_manager
        self.back_callback = back_callback
        self.status_callback = status_callback
        
        self.frame = tk.Frame(parent, bg=THEME_COLOR_PRIMARY)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.return_mode_active = False
        self.detection_thread = None
        self.operation_in_progress = False
        self.is_active = True  # Flag to track if screen is still active
        
        self.create_ui()
        
        # Start return mode automatically
        self.start_return_mode()
    
    def create_ui(self):
        """Create return screen UI"""
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
            text="RETURN MODE",
            font=('Arial', 24, 'bold'),
            bg=THEME_COLOR_PRIMARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        title.pack(side=tk.LEFT, padx=20)
        
        # Main content area (camera + detection status)
        content = tk.Frame(self.frame, bg=THEME_COLOR_PRIMARY)
        content.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Left side - Camera feed
        camera_frame = tk.Frame(content, bg=THEME_COLOR_SECONDARY, relief='raised', bd=2)
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        camera_label = tk.Label(
            camera_frame,
            text="Camera Feed",
            font=('Arial', 12, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        camera_label.pack(pady=10)
        
        self.camera_display = tk.Label(
            camera_frame,
            bg='black',
            width=50,
            height=30
        )
        self.camera_display.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)
        
        # Right side - Detection status
        status_frame = tk.Frame(content, bg=THEME_COLOR_SECONDARY, relief='raised', bd=2, width=300)
        status_frame.pack(side=tk.RIGHT, fill=tk.Y)
        status_frame.pack_propagate(False)
        
        status_title = tk.Label(
            status_frame,
            text="Detection Status",
            font=('Arial', 14, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        status_title.pack(pady=15)
        
        # Status message
        self.status_message = tk.Label(
            status_frame,
            text="Initializing...",
            font=('Arial', 12),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            wraplength=250,
            justify=tk.CENTER
        )
        self.status_message.pack(pady=20)
        
        # Detected item
        self.detected_label = tk.Label(
            status_frame,
            text="",
            font=('Arial', 14, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_SUCCESS,
            wraplength=250
        )
        self.detected_label.pack(pady=10)
        
        # Confidence
        self.confidence_label = tk.Label(
            status_frame,
            text="",
            font=('Arial', 11),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT
        )
        self.confidence_label.pack(pady=5)
        
        # Validation status
        self.validation_label = tk.Label(
            status_frame,
            text="",
            font=('Arial', 11, 'bold'),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_SUCCESS
        )
        self.validation_label.pack(pady=10)
        
        # Progress bar
        self.progress_frame = tk.Frame(status_frame, bg=THEME_COLOR_SECONDARY)
        self.progress_frame.pack(pady=20)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=('Arial', 10),
            bg=THEME_COLOR_SECONDARY,
            fg=THEME_COLOR_TEXT_LIGHT,
            wraplength=250
        )
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=250
        )
        self.progress_bar.pack(pady=5)
    
    def start_return_mode(self):
        """Initiate return mode"""
        self.logger.info("Starting return mode")
        self.status_callback("Return mode - waiting for item...")
        
        # Move robot to observation position
        def move_robot():
            if not self.is_active:
                return
            
            try:
                self.status_message.config(text="Moving to observation position...")
            except tk.TclError:
                return  # Widget destroyed
            
            if self.robot.move_to_observation_position(self.status_callback):
                # Wait initial period
                for i in range(int(INITIAL_WAIT_BEFORE_DETECTION)):
                    if not self.is_active:
                        return
                    remaining = int(INITIAL_WAIT_BEFORE_DETECTION) - i
                    try:
                        self.parent.after(0, lambda r=remaining: self.status_message.config(
                            text=f"Please place item in drop zone...\n\nStarting detection in {r}s"
                        ) if self.is_active else None)
                    except tk.TclError:
                        return
                    time.sleep(1)
                
                # Start detection only if still active
                if self.is_active:
                    self.return_mode_active = True
                    self.parent.after(0, self.start_detection_thread)
            else:
                if self.is_active:
                    self.parent.after(0, lambda: messagebox.showerror(
                        "Error",
                        "Failed to move robot to observation position"
                    ))
                    self.parent.after(0, self.handle_back)
        
        thread = threading.Thread(target=move_robot, daemon=True)
        thread.start()
    
    def start_detection_thread(self):
        """Start continuous detection thread"""
        self.return_mode_active = True
        self.detection_thread = threading.Thread(
            target=self.continuous_detection_loop,
            daemon=True
        )
        self.detection_thread.start()
        
        # Start camera feed update
        self.update_camera_feed()
    
    def continuous_detection_loop(self):
        """Background thread for continuous classification"""
        detection_count = 0
        last_detected_item = None
        
        while self.return_mode_active and self.is_active:
            try:
                if self.operation_in_progress:
                    time.sleep(1)
                    continue
                
                if not self.is_active:
                    break
                
                # Capture and classify
                result = self.vision.classify_item()
                
                # Update GUI only if still active
                if self.is_active:
                    try:
                        self.parent.after(0, lambda r=result: self.update_detection_status(r) if self.is_active else None)
                    except tk.TclError:
                        break
                
                # Check if valid detection
                if result.get('success', False):
                    detected_class = result['class_name']
                    confidence = result['confidence']
                    
                    # Same item detected consistently?
                    if detected_class == last_detected_item:
                        detection_count += 1
                    else:
                        detection_count = 1
                        last_detected_item = detected_class
                    
                    # Stable detection?
                    if detection_count >= STABLE_DETECTION_COUNT:
                        # Trigger return sequence
                        self.logger.info(f"Stable detection: {detected_class} ({confidence:.2%})")
                        self.parent.after(0, lambda: self.execute_return_sequence(detected_class))
                        
                        # Reset
                        detection_count = 0
                        last_detected_item = None
                        
                        # Wait for return to complete
                        while self.operation_in_progress and self.return_mode_active and self.is_active:
                            time.sleep(0.5)
                
                else:
                    # No valid detection
                    detection_count = 0
                    last_detected_item = None
                
                # Wait before next detection
                time.sleep(DETECTION_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Detection loop error: {e}")
                if not self.is_active:
                    break
                time.sleep(1)
    
    def update_camera_feed(self):
        """Update camera display"""
        if not self.return_mode_active or not self.is_active:
            return
        
        try:
            frame = self.vision.get_live_feed()
            if frame is not None:
                # Convert to PIL Image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Resize to fit display
                pil_image.thumbnail((400, 300), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(pil_image)
                
                # Update label
                self.camera_display.config(image=photo)
                self.camera_display.image = photo  # Keep reference
        
        except Exception as e:
            self.logger.debug(f"Camera feed update error: {e}")
        
        # Schedule next update (30 FPS) only if still active
        if self.return_mode_active and self.is_active:
            try:
                self.parent.after(33, self.update_camera_feed)
            except tk.TclError:
                pass  # Widget destroyed
    
    def update_detection_status(self, result: dict):
        """Update detection panel with classification results"""
        if not self.is_active:
            return
        
        try:
            if result.get('success', False):
                # Valid detection
                self.status_message.config(text="Item detected!", fg=THEME_COLOR_SUCCESS)
                self.detected_label.config(
                    text=f"Detected:\n{result['class_name']}",
                    fg=THEME_COLOR_SUCCESS
                )
                self.confidence_label.config(
                    text=f"Confidence: {result['confidence']:.1%}"
                )
                self.validation_label.config(
                    text="✓ Valid item",
                    fg=THEME_COLOR_SUCCESS
                )
            elif 'error' in result:
                # Error or invalid
                self.status_message.config(text="Waiting for item...", fg=THEME_COLOR_TEXT_LIGHT)
                
                if result.get('class_name'):
                    self.detected_label.config(
                        text=f"Detected:\n{result['class_name']}",
                        fg=THEME_COLOR_WARNING
                    )
                    self.confidence_label.config(
                        text=f"Confidence: {result.get('confidence', 0):.1%}"
                    )
                    self.validation_label.config(
                        text=f"✗ {result['error']}",
                        fg=THEME_COLOR_DANGER
                    )
                else:
                    self.detected_label.config(text="")
                    self.confidence_label.config(text="")
                    self.validation_label.config(text="Place item in view")
            else:
                # Waiting
                self.status_message.config(text="Waiting for item...", fg=THEME_COLOR_TEXT_LIGHT)
                self.detected_label.config(text="")
                self.confidence_label.config(text="")
                self.validation_label.config(text="")
        except tk.TclError:
            pass  # Widget destroyed
    
    def execute_return_sequence(self, item_name: str):
        """Execute return operation after valid detection"""
        if self.operation_in_progress or not self.is_active:
            return
        
        self.operation_in_progress = True
        
        # Show waiting message
        self.status_message.config(text=f"Processing...\n\nWaiting {SAFETY_WAIT_AFTER_DETECTION}s for safety")
        
        def return_thread():
            # Safety wait
            for _ in range(int(SAFETY_WAIT_AFTER_DETECTION * 10)):
                if not self.is_active:
                    return
                time.sleep(0.1)
            
            if not self.is_active:
                return
            
            # Show progress
            try:
                self.parent.after(0, lambda: self.progress_label.config(text="Returning item...") if self.is_active else None)
                self.parent.after(0, lambda: self.progress_bar.start() if self.is_active else None)
            except tk.TclError:
                return
            
            # Execute return
            result = self.robot.return_item(item_name, status_callback=self.status_callback)
            
            # Complete only if still active
            if self.is_active:
                self.parent.after(0, lambda: self._return_complete(item_name, result))
        
        thread = threading.Thread(target=return_thread, daemon=True)
        thread.start()
    
    def _return_complete(self, item_name: str, result: dict):
        """Handle return completion"""
        if not self.is_active:
            return
        
        try:
            self.progress_bar.stop()
            self.progress_label.config(text="")
        except tk.TclError:
            pass
        
        self.operation_in_progress = False
        
        if result.get('success', False):
            # Update state
            self.state.mark_available(item_name)
            
            # Show success
            try:
                self.status_message.config(
                    text=f"✓ {item_name} returned successfully!\n\nWaiting for next item...",
                    fg=THEME_COLOR_SUCCESS
                )
                self.detected_label.config(text="")
                self.confidence_label.config(text="")
                self.validation_label.config(text="")
            except tk.TclError:
                pass
            
            messagebox.showinfo(
                "Return Complete",
                f"{item_name} has been returned to storage."
            )
        else:
            # Show error
            error_msg = result.get('message', 'Unknown error')
            try:
                self.status_message.config(
                    text=f"Error returning item\n\n{error_msg}",
                    fg=THEME_COLOR_DANGER
                )
            except tk.TclError:
                pass
            
            messagebox.showerror(
                "Return Failed",
                f"Failed to return {item_name}:\n\n{error_msg}"
            )
    
    def stop_return_mode(self):
        """Exit return mode"""
        self.logger.info("Stopping return mode")
        self.is_active = False
        self.return_mode_active = False
        self.operation_in_progress = False
        
        # Wait for thread to stop (with timeout)
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1)
        
        # Move robot home in background
        def move_home():
            try:
                self.robot.move_home()
            except Exception as e:
                self.logger.debug(f"Error moving home: {e}")
        
        thread = threading.Thread(target=move_home, daemon=True)
        thread.start()
    
    def handle_back(self):
        """Handle back button"""
        if self.operation_in_progress:
            result = messagebox.askyesno(
                "Operation in Progress",
                "A return operation is in progress. Are you sure you want to go back?\n\nThe robot will stop and return home."
            )
            if not result:
                return
        
        self.cleanup()
        self.back_callback()
    
    def cleanup(self):
        """Cleanup when leaving screen"""
        self.logger.info("Cleaning up return screen")
        self.stop_return_mode()
