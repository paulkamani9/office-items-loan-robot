"""
Return screen - elegant design with live camera feed and detection
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
    DETECTION_INTERVAL,
    INITIAL_WAIT_BEFORE_DETECTION,
    SAFETY_WAIT_AFTER_DETECTION,
    STABLE_DETECTION_COUNT,
    CONFIDENCE_THRESHOLD
)
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
    'card_bg': '#1e3a5f'
}


class ReturnScreen:
    """
    Elegant return interface with live camera feed
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
        
        self.frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.return_mode_active = False
        self.detection_thread = None
        self.operation_in_progress = False
        self.is_active = True
        
        self.create_ui()
        self.start_return_mode()
    
    def create_ui(self):
        """Create return screen UI"""
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
        title = tk.Label(
            header,
            text="↩️ RETURN AN ITEM",
            font=('Arial', 20, 'bold'),
            bg=COLORS['bg_dark'],
            fg=COLORS['accent_green']
        )
        title.pack(side=tk.LEFT, padx=20)
        
        # Subtitle
        subtitle = tk.Label(
            header,
            text="Place item in drop zone for automatic detection",
            font=('Arial', 11),
            bg=COLORS['bg_dark'],
            fg=COLORS['text_gray']
        )
        subtitle.pack(side=tk.RIGHT, padx=20)
        
        # Divider
        divider = tk.Frame(self.frame, bg=COLORS['bg_medium'], height=2)
        divider.pack(fill=tk.X, pady=(0, 15))
        
        # Main content - split view
        content = tk.Frame(self.frame, bg=COLORS['bg_dark'])
        content.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Left side - Camera feed (larger)
        camera_frame = tk.Frame(content, bg=COLORS['card_bg'], highlightbackground=COLORS['accent_blue'], highlightthickness=2)
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        camera_header = tk.Frame(camera_frame, bg=COLORS['bg_medium'])
        camera_header.pack(fill=tk.X)
        
        camera_title = tk.Label(
            camera_header,
            text="📷 Live Camera Feed",
            font=('Arial', 12, 'bold'),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_white']
        )
        camera_title.pack(pady=8)
        
        # Camera display container (fixed size)
        camera_container = tk.Frame(camera_frame, bg='black', width=480, height=360)
        camera_container.pack(padx=15, pady=15)
        camera_container.pack_propagate(False)
        
        self.camera_display = tk.Label(camera_container, bg='black')
        self.camera_display.pack(fill=tk.BOTH, expand=True)
        
        self.camera_width = 480
        self.camera_height = 360
        
        # Right side - Detection status panel
        status_panel = tk.Frame(content, bg=COLORS['card_bg'], width=280, highlightbackground=COLORS['accent_green'], highlightthickness=2)
        status_panel.pack(side=tk.RIGHT, fill=tk.Y)
        status_panel.pack_propagate(False)
        
        # Status panel header
        status_header = tk.Frame(status_panel, bg=COLORS['bg_medium'])
        status_header.pack(fill=tk.X)
        
        status_title = tk.Label(
            status_header,
            text="🔍 Detection Status",
            font=('Arial', 12, 'bold'),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_white']
        )
        status_title.pack(pady=8)
        
        # Status content
        status_content = tk.Frame(status_panel, bg=COLORS['card_bg'])
        status_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Main status message
        self.status_icon = tk.Label(
            status_content,
            text="🔄",
            font=('Arial', 36),
            bg=COLORS['card_bg']
        )
        self.status_icon.pack(pady=(20, 10))
        
        self.status_message = tk.Label(
            status_content,
            text="Initializing...",
            font=('Arial', 13, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text_white'],
            wraplength=240,
            justify=tk.CENTER
        )
        self.status_message.pack(pady=10)
        
        # Detected item display
        self.detected_frame = tk.Frame(status_content, bg=COLORS['bg_medium'])
        self.detected_frame.pack(fill=tk.X, pady=15)
        
        self.detected_label = tk.Label(
            self.detected_frame,
            text="",
            font=('Arial', 14, 'bold'),
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_green'],
            wraplength=240
        )
        self.detected_label.pack(pady=10)
        
        self.confidence_label = tk.Label(
            self.detected_frame,
            text="",
            font=('Arial', 11),
            bg=COLORS['bg_medium'],
            fg=COLORS['text_gray']
        )
        self.confidence_label.pack()
        
        # Validation status
        self.validation_label = tk.Label(
            status_content,
            text="",
            font=('Arial', 11, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['accent_green']
        )
        self.validation_label.pack(pady=10)
        
        # Progress section
        self.progress_frame = tk.Frame(status_content, bg=COLORS['card_bg'])
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=('Arial', 10),
            bg=COLORS['card_bg'],
            fg=COLORS['text_white'],
            wraplength=240
        )
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=220
        )
        self.progress_bar.pack(pady=5)
    
    def start_return_mode(self):
        """Initiate return mode"""
        self.logger.info("Starting return mode")
        self.status_callback("Return mode - initializing...")
        
        def move_robot():
            if not self.is_active:
                return
            
            try:
                self.status_message.config(text="Moving robot to\nobservation position...")
                self.status_icon.config(text="🤖")
            except tk.TclError:
                return
            
            if self.robot.move_to_observation_position(self.status_callback):
                # Countdown
                for i in range(int(INITIAL_WAIT_BEFORE_DETECTION)):
                    if not self.is_active:
                        return
                    remaining = int(INITIAL_WAIT_BEFORE_DETECTION) - i
                    try:
                        self.parent.after(0, lambda r=remaining: self._update_countdown(r) if self.is_active else None)
                    except tk.TclError:
                        return
                    time.sleep(1)
                
                if self.is_active:
                    self.return_mode_active = True
                    self.parent.after(0, self.start_detection_thread)
            else:
                if self.is_active:
                    self.parent.after(0, lambda: messagebox.showerror(
                        "Error", "Failed to move robot to observation position"
                    ))
                    self.parent.after(0, self.handle_back)
        
        thread = threading.Thread(target=move_robot, daemon=True)
        thread.start()
    
    def _update_countdown(self, remaining):
        """Update countdown display"""
        try:
            self.status_icon.config(text="⏳")
            self.status_message.config(
                text=f"Place item in drop zone\n\nStarting detection in {remaining}s"
            )
        except tk.TclError:
            pass
    
    def start_detection_thread(self):
        """Start continuous detection"""
        self.return_mode_active = True
        
        try:
            self.status_icon.config(text="👁️")
            self.status_message.config(text="Watching for items...")
        except tk.TclError:
            pass
        
        self.detection_thread = threading.Thread(
            target=self.continuous_detection_loop,
            daemon=True
        )
        self.detection_thread.start()
        
        self.update_camera_feed()
    
    def continuous_detection_loop(self):
        """Background detection loop"""
        detection_count = 0
        last_detected_item = None
        
        while self.return_mode_active and self.is_active:
            try:
                if self.operation_in_progress:
                    time.sleep(1)
                    continue
                
                if not self.is_active:
                    break
                
                result = self.vision.classify_item()
                
                if self.is_active:
                    try:
                        self.parent.after(0, lambda r=result: self.update_detection_status(r) if self.is_active else None)
                    except tk.TclError:
                        break
                
                if result.get('success', False):
                    detected_class = result['class_name']
                    
                    if detected_class == last_detected_item:
                        detection_count += 1
                    else:
                        detection_count = 1
                        last_detected_item = detected_class
                    
                    if detection_count >= STABLE_DETECTION_COUNT:
                        self.logger.info(f"Stable detection: {detected_class}")
                        self.parent.after(0, lambda: self.execute_return_sequence(detected_class))
                        
                        detection_count = 0
                        last_detected_item = None
                        
                        while self.operation_in_progress and self.return_mode_active and self.is_active:
                            time.sleep(0.5)
                else:
                    detection_count = 0
                    last_detected_item = None
                
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
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                pil_image = pil_image.resize((self.camera_width, self.camera_height), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(pil_image)
                self.camera_display.config(image=photo)
                self.camera_display.image = photo
        except Exception as e:
            self.logger.debug(f"Camera feed error: {e}")
        
        if self.return_mode_active and self.is_active:
            try:
                self.parent.after(33, self.update_camera_feed)
            except tk.TclError:
                pass
    
    def update_detection_status(self, result: dict):
        """Update detection panel"""
        if not self.is_active:
            return
        
        try:
            if result.get('success', False):
                self.status_icon.config(text="✅")
                self.status_message.config(text="Item detected!", fg=COLORS['accent_green'])
                self.detected_label.config(
                    text=f"📦 {result['class_name']}",
                    fg=COLORS['accent_green']
                )
                self.confidence_label.config(
                    text=f"Confidence: {result['confidence']:.1%}"
                )
                self.validation_label.config(
                    text="✓ Valid item - Processing...",
                    fg=COLORS['accent_green']
                )
            elif 'error' in result:
                self.status_icon.config(text="👁️")
                self.status_message.config(text="Watching for items...", fg=COLORS['text_white'])
                
                if result.get('class_name'):
                    self.detected_label.config(
                        text=f"📦 {result['class_name']}",
                        fg=COLORS['accent_orange']
                    )
                    self.confidence_label.config(
                        text=f"Confidence: {result.get('confidence', 0):.1%}"
                    )
                    self.validation_label.config(
                        text=f"⚠ {result['error']}",
                        fg=COLORS['accent_orange']
                    )
                else:
                    self.detected_label.config(text="")
                    self.confidence_label.config(text="")
                    self.validation_label.config(text="Place item in camera view")
            else:
                self.status_icon.config(text="👁️")
                self.status_message.config(text="Watching for items...", fg=COLORS['text_white'])
                self.detected_label.config(text="")
                self.confidence_label.config(text="")
                self.validation_label.config(text="")
        except tk.TclError:
            pass
    
    def execute_return_sequence(self, item_name: str):
        """Execute return operation"""
        if self.operation_in_progress or not self.is_active:
            return
        
        self.operation_in_progress = True
        
        try:
            self.status_icon.config(text="⏳")
            self.status_message.config(text=f"Processing...\n\nSafety wait: {SAFETY_WAIT_AFTER_DETECTION}s")
        except tk.TclError:
            pass
        
        def return_thread():
            for _ in range(int(SAFETY_WAIT_AFTER_DETECTION * 10)):
                if not self.is_active:
                    return
                time.sleep(0.1)
            
            if not self.is_active:
                return
            
            try:
                self.parent.after(0, lambda: self.progress_label.config(text=f"Returning {item_name}...") if self.is_active else None)
                self.parent.after(0, lambda: self.progress_bar.start() if self.is_active else None)
                self.parent.after(0, lambda: self.status_icon.config(text="🤖") if self.is_active else None)
            except tk.TclError:
                return
            
            result = self.robot.return_item(item_name, status_callback=self.status_callback)
            
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
            self.state.mark_available(item_name)
            
            try:
                self.status_icon.config(text="✅")
                self.status_message.config(
                    text=f"✓ {item_name}\nreturned successfully!",
                    fg=COLORS['accent_green']
                )
                self.detected_label.config(text="")
                self.confidence_label.config(text="")
                self.validation_label.config(text="Waiting for next item...")
            except tk.TclError:
                pass
            
            messagebox.showinfo(
                "✓ Return Complete",
                f"{item_name} has been returned to storage."
            )
            
            # Reset status after a moment
            try:
                self.parent.after(2000, self._reset_status)
            except tk.TclError:
                pass
        else:
            error_msg = result.get('message', 'Unknown error')
            try:
                self.status_icon.config(text="❌")
                self.status_message.config(
                    text=f"Return failed\n\n{error_msg}",
                    fg=COLORS['accent_red']
                )
            except tk.TclError:
                pass
            
            messagebox.showerror(
                "Return Failed",
                f"Could not return {item_name}:\n\n{error_msg}"
            )
    
    def _reset_status(self):
        """Reset status display for next item"""
        if not self.is_active:
            return
        try:
            self.status_icon.config(text="👁️")
            self.status_message.config(text="Watching for items...", fg=COLORS['text_white'])
        except tk.TclError:
            pass
    
    def stop_return_mode(self):
        """Stop return mode"""
        self.logger.info("Stopping return mode")
        self.is_active = False
        self.return_mode_active = False
        self.operation_in_progress = False
        
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1)
        
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
                "A return operation is in progress. Go back anyway?\n\nThe robot will stop and return home."
            )
            if not result:
                return
        
        self.cleanup()
        self.back_callback()
    
    def cleanup(self):
        """Cleanup when leaving"""
        self.logger.info("Cleaning up return screen")
        self.stop_return_mode()
