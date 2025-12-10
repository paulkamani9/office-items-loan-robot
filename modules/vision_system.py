"""
Computer vision system for item classification
Handles camera interface and YOLO classification
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import Dict, Optional, Tuple
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    CAMERA_ID,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CROP_PERCENTAGE,
    CONFIDENCE_THRESHOLD,
    ITEM_CLASSES,
    CLASS_NAME_MAPPING
)
from utils.logger import RobotLogger


class VisionSystem:
    """
    Handle camera interface and YOLO classification
    """
    
    def __init__(self, model_path: str, camera_id: int = CAMERA_ID):
        """
        Initialize camera and load YOLO model
        
        IMPORTANT: Handle model input size dynamically to avoid mp.nra errors
        - Detect model's expected input size
        - Always resize frames to exact expected size
        """
        self.logger = RobotLogger()
        self.camera_id = camera_id
        self.camera = None
        self.model = None
        self.input_size = None
        
        # Load model
        try:
            self.logger.info(f"Loading model from {model_path}")
            self.model = YOLO(model_path)
            self.input_size = self.get_model_input_size()
            self.logger.info(f"✓ Model loaded - Expected input size: {self.input_size}x{self.input_size}")
        except Exception as e:
            self.logger.error(f"✗ Failed to load model: {e}")
            raise
        
        # Initialize camera
        self.initialize_camera()
    
    def get_model_input_size(self) -> int:
        """
        Detect and return model's expected input size
        This prevents type/size errors during inference
        """
        try:
            # Method 1: Check model overrides
            if hasattr(self.model, 'overrides'):
                imgsz = self.model.overrides.get('imgsz', None)
                if imgsz:
                    size = imgsz if isinstance(imgsz, int) else imgsz[0]
                    self.logger.debug(f"Model input size from overrides: {size}")
                    return size
            
            # Method 2: Check model args
            if hasattr(self.model, 'model') and hasattr(self.model.model, 'args'):
                imgsz = self.model.model.args.get('imgsz', None)
                if imgsz:
                    size = imgsz if isinstance(imgsz, int) else imgsz[0]
                    self.logger.debug(f"Model input size from args: {size}")
                    return size
            
            # Method 3: Try inference with test sizes and catch error
            test_sizes = [224, 416, 640]
            for size in test_sizes:
                try:
                    test_img = np.zeros((size, size, 3), dtype=np.uint8)
                    self.model(test_img, verbose=False)
                    self.logger.debug(f"Model input size detected via test: {size}")
                    return size
                except:
                    continue
            
            # Default fallback
            self.logger.warning("Could not detect model input size, using default: 416")
            return 416
            
        except Exception as e:
            self.logger.error(f"Error detecting model input size: {e}")
            return 416  # Safe default
    
    def normalize_class_name(self, raw_name: str) -> str:
        """
        Normalize model class name to match ITEM_CLASSES format
        
        Examples:
            'pen' -> 'Pen'
            'computer_keyboard' -> 'Computer Keyboard'
            'mobile_phone' -> 'Mobile Phone'
        
        Args:
            raw_name: Class name as returned by the model
        
        Returns:
            Normalized class name matching ITEM_CLASSES format
        """
        # First check if there's an explicit mapping
        if raw_name in CLASS_NAME_MAPPING:
            return CLASS_NAME_MAPPING[raw_name]
        
        # Fallback: Convert underscore format to title case with spaces
        # 'computer_keyboard' -> 'Computer Keyboard'
        normalized = raw_name.replace('_', ' ').title()
        
        self.logger.debug(f"Class name normalized: '{raw_name}' -> '{normalized}'")
        return normalized
    
    def initialize_camera(self) -> bool:
        """
        Setup camera with optimal settings for RPi4
        - Set resolution
        - Disable autofocus/auto-exposure
        - Configure for MJPEG compression
        - Warm-up capture (10 frames)
        """
        try:
            self.logger.info(f"Initializing camera {self.camera_id}")
            
            # Try with CAP_V4L2 backend first (more reliable on Linux)
            self.camera = cv2.VideoCapture(self.camera_id, cv2.CAP_V4L2)
            
            if not self.camera.isOpened():
                self.logger.warning("Failed with V4L2, trying default backend...")
                # Fallback to default backend
                self.camera = cv2.VideoCapture(self.camera_id)
                
            if not self.camera.isOpened():
                self.logger.error("Failed to open camera")
                return False
            
            # Set resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            
            # Try to set MJPEG for better performance (ignore if fails)
            try:
                self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            except:
                self.logger.debug("MJPEG format not supported, using default")
            
            # Try to disable auto settings (ignore if not supported)
            try:
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            except:
                pass
            
            try:
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            except:
                pass
            
            # Warm-up camera (capture and discard frames)
            self.logger.debug("Warming up camera...")
            for _ in range(10):
                ret, _ = self.camera.read()
                if not ret:
                    self.logger.warning(f"Warm-up frame failed, continuing...")
            
            # Verify camera is working by reading one frame
            ret, test_frame = self.camera.read()
            if not ret or test_frame is None:
                self.logger.error("Camera opened but cannot read frames")
                return False
            
            self.logger.info(f"✓ Camera initialized successfully - Frame size: {test_frame.shape}")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Camera initialization failed: {e}")
            return False
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture single frame from camera"""
        if self.camera is None or not self.camera.isOpened():
            self.logger.error("Camera not initialized")
            return None
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                self.logger.error("Failed to capture frame")
                return None
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def crop_center(self, frame: np.ndarray, crop_percent: float = CROP_PERCENTAGE) -> np.ndarray:
        """Crop center region of frame"""
        height, width = frame.shape[:2]
        
        crop_width = int(width * crop_percent)
        crop_height = int(height * crop_percent)
        
        start_x = (width - crop_width) // 2
        start_y = (height - crop_height) // 2
        
        cropped = frame[start_y:start_y+crop_height, start_x:start_x+crop_width]
        return cropped
    
    def classify_item(self, frame: Optional[np.ndarray] = None) -> Dict:
        """
        Classify item in frame
        
        Returns:
            {
                'success': bool,
                'class_name': str or None,
                'confidence': float,
                'all_predictions': dict  # All class probabilities for debugging
            }
        
        Process:
        1. Crop center region (70%)
        2. Resize to exact model input size
        3. Run classification
        4. Check confidence threshold (80%)
        5. Validate class is in ITEM_CLASSES
        """
        # Capture frame if not provided
        if frame is None:
            frame = self.capture_frame()
        
        if frame is None:
            return {
                'success': False,
                'class_name': None,
                'confidence': 0.0,
                'all_predictions': {},
                'error': 'Failed to capture frame'
            }
        
        try:
            # Crop center region
            cropped = self.crop_center(frame, CROP_PERCENTAGE)
            
            # CRITICAL: Resize to exact model input size
            resized = cv2.resize(cropped, (self.input_size, self.input_size))
            
            # Run classification
            results = self.model(resized, verbose=False)
            
            # Extract predictions
            if len(results) == 0:
                return {
                    'success': False,
                    'class_name': None,
                    'confidence': 0.0,
                    'all_predictions': {},
                    'error': 'No results from model'
                }
            
            result = results[0]
            
            # Get predicted class and confidence
            if hasattr(result, 'probs') and result.probs is not None:
                probs = result.probs
                top_class_idx = int(probs.top1)
                confidence = float(probs.top1conf)
                
                # Get class name from model
                class_names = result.names
                raw_class_name = class_names[top_class_idx]
                
                # Normalize class name to match ITEM_CLASSES format
                predicted_class = self.normalize_class_name(raw_class_name)
                
                # Get all predictions for debugging (with normalized names)
                all_preds = {}
                if hasattr(probs, 'data'):
                    for idx, prob in enumerate(probs.data):
                        normalized_name = self.normalize_class_name(class_names[idx])
                        all_preds[normalized_name] = float(prob)
                
                # Check confidence threshold
                if confidence < CONFIDENCE_THRESHOLD:
                    return {
                        'success': False,
                        'class_name': predicted_class,
                        'confidence': confidence,
                        'all_predictions': all_preds,
                        'error': f'Confidence too low: {confidence:.2%} < {CONFIDENCE_THRESHOLD:.2%}'
                    }
                
                # Validate class is in ITEM_CLASSES
                if predicted_class not in ITEM_CLASSES:
                    return {
                        'success': False,
                        'class_name': predicted_class,
                        'confidence': confidence,
                        'all_predictions': all_preds,
                        'error': f'Detected class not in system: {predicted_class} (raw: {raw_class_name})'
                    }
                
                # Success!
                self.logger.debug(f"Classification: {predicted_class} ({confidence:.2%})")
                return {
                    'success': True,
                    'class_name': predicted_class,
                    'confidence': confidence,
                    'all_predictions': all_preds
                }
            
            else:
                return {
                    'success': False,
                    'class_name': None,
                    'confidence': 0.0,
                    'all_predictions': {},
                    'error': 'Model did not return probabilities'
                }
                
        except Exception as e:
            self.logger.error(f"Classification error: {e}")
            return {
                'success': False,
                'class_name': None,
                'confidence': 0.0,
                'all_predictions': {},
                'error': str(e)
            }
    
    def get_live_feed(self) -> Optional[np.ndarray]:
        """
        Return current frame for GUI display
        Used in return mode to show camera feed
        """
        return self.capture_frame()
    
    def cleanup(self):
        """Release camera resources"""
        if self.camera is not None:
            self.camera.release()
            self.logger.info("Camera released")
        
        self.camera = None
    
    def __del__(self):
        """Ensure cleanup on deletion"""
        self.cleanup()
