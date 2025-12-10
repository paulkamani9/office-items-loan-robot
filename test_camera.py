#!/usr/bin/env python3
"""
Simple standalone camera test script
Tests live camera feed and classification independently

Usage:
    python test_camera.py
    python test_camera.py --camera 0  # Use camera ID 0
    python test_camera.py --no-classify  # Just show camera feed without classification
"""

import cv2
import argparse
import sys
import time

def test_camera_feed(camera_id=1, show_classification=True, model_path='models/fine-tunedmodel.pt'):
    """
    Test camera feed with optional classification
    
    Controls:
        q - Quit
        c - Capture single frame and classify
        s - Save current frame
        r - Toggle continuous classification
    """
    print(f"\n{'='*50}")
    print("CAMERA TEST")
    print(f"{'='*50}")
    print(f"Camera ID: {camera_id}")
    print(f"Classification: {'Enabled' if show_classification else 'Disabled'}")
    print(f"{'='*50}\n")
    
    # Initialize camera
    print("Initializing camera...")
    cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print(f"Failed to open camera {camera_id} with V4L2, trying default...")
        cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"ERROR: Could not open camera {camera_id}")
        return False
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Try MJPEG format
    try:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    except:
        pass
    
    # Warm up camera
    print("Warming up camera...")
    for _ in range(10):
        cap.read()
    
    # Test read
    ret, frame = cap.read()
    if not ret or frame is None:
        print("ERROR: Camera opened but cannot read frames")
        cap.release()
        return False
    
    print(f"✓ Camera initialized - Frame size: {frame.shape}")
    
    # Load model if classification enabled
    model = None
    if show_classification:
        try:
            from ultralytics import YOLO
            print(f"\nLoading model from {model_path}...")
            model = YOLO(model_path)
            print("✓ Model loaded successfully")
        except Exception as e:
            print(f"WARNING: Could not load model: {e}")
            print("Classification disabled")
            model = None
    
    # Display controls
    print("\n" + "="*50)
    print("CONTROLS:")
    print("  q - Quit")
    print("  c - Capture and classify single frame")
    print("  s - Save current frame to file")
    print("  r - Toggle continuous classification")
    print("  + - Increase brightness")
    print("  - - Decrease brightness")
    print("="*50 + "\n")
    
    continuous_classify = False
    frame_count = 0
    fps_start = time.time()
    fps = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                continue
            
            frame_count += 1
            
            # Calculate FPS every 30 frames
            if frame_count % 30 == 0:
                fps = 30 / (time.time() - fps_start)
                fps_start = time.time()
            
            # Create display frame
            display = frame.copy()
            
            # Add FPS overlay
            cv2.putText(display, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Continuous classification
            if continuous_classify and model is not None:
                result = classify_frame(model, frame)
                if result:
                    # Draw classification result
                    text = f"{result['class']}: {result['confidence']:.1%}"
                    color = (0, 255, 0) if result['confidence'] > 0.8 else (0, 165, 255)
                    cv2.putText(display, text, (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.putText(display, "[CONTINUOUS]", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            # Show frame
            cv2.imshow("Camera Test", display)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\nQuitting...")
                break
            
            elif key == ord('c') and model is not None:
                print("\n--- Single Classification ---")
                result = classify_frame(model, frame, verbose=True)
                if result:
                    print(f"Detected: {result['class']} ({result['confidence']:.1%})")
                print("----------------------------\n")
            
            elif key == ord('s'):
                filename = f"capture_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"✓ Frame saved to {filename}")
            
            elif key == ord('r'):
                continuous_classify = not continuous_classify
                status = "ON" if continuous_classify else "OFF"
                print(f"Continuous classification: {status}")
            
            elif key == ord('+') or key == ord('='):
                brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
                cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness + 10)
                print(f"Brightness: {cap.get(cv2.CAP_PROP_BRIGHTNESS)}")
            
            elif key == ord('-'):
                brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
                cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness - 10)
                print(f"Brightness: {cap.get(cv2.CAP_PROP_BRIGHTNESS)}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released")
    
    return True


def classify_frame(model, frame, verbose=False):
    """
    Classify a single frame
    
    Returns:
        dict with 'class', 'confidence', 'all_predictions'
        or None if failed
    """
    try:
        # Crop center 70%
        h, w = frame.shape[:2]
        crop_pct = 0.7
        crop_w, crop_h = int(w * crop_pct), int(h * crop_pct)
        start_x, start_y = (w - crop_w) // 2, (h - crop_h) // 2
        cropped = frame[start_y:start_y+crop_h, start_x:start_x+crop_w]
        
        # Resize for model
        resized = cv2.resize(cropped, (224, 224))
        
        # Run inference
        results = model(resized, verbose=False)
        
        if len(results) == 0:
            return None
        
        result = results[0]
        
        if hasattr(result, 'probs') and result.probs is not None:
            probs = result.probs
            top_idx = int(probs.top1)
            confidence = float(probs.top1conf)
            class_name = result.names[top_idx]
            
            # Get all predictions
            all_preds = {}
            if hasattr(probs, 'data'):
                for idx, prob in enumerate(probs.data):
                    all_preds[result.names[idx]] = float(prob)
            
            if verbose:
                print("\nAll predictions:")
                for name, conf in sorted(all_preds.items(), key=lambda x: x[1], reverse=True):
                    bar = "█" * int(conf * 20)
                    print(f"  {name:20s} {conf:6.1%} {bar}")
            
            return {
                'class': class_name,
                'confidence': confidence,
                'all_predictions': all_preds
            }
        
        return None
    
    except Exception as e:
        if verbose:
            print(f"Classification error: {e}")
        return None


def list_cameras():
    """List available cameras"""
    print("\nScanning for cameras...")
    available = []
    
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available.append(i)
                print(f"  Camera {i}: Available")
            cap.release()
    
    if not available:
        print("  No cameras found!")
    
    return available


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test camera feed and classification")
    parser.add_argument("--camera", "-c", type=int, default=1, 
                       help="Camera ID (default: 1)")
    parser.add_argument("--no-classify", action="store_true",
                       help="Disable classification, just show camera feed")
    parser.add_argument("--model", "-m", type=str, default="models/fine-tunedmodel.pt",
                       help="Path to YOLO model")
    parser.add_argument("--list", "-l", action="store_true",
                       help="List available cameras and exit")
    
    args = parser.parse_args()
    
    if args.list:
        list_cameras()
        sys.exit(0)
    
    success = test_camera_feed(
        camera_id=args.camera,
        show_classification=not args.no_classify,
        model_path=args.model
    )
    
    sys.exit(0 if success else 1)
