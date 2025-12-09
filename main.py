"""
Office Items Loan Robot - Main Entry Point

This application manages lending and returning of office items using
a Yahboom Dofbot robot arm with computer vision.
"""

import tkinter as tk
from tkinter import messagebox
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from utils.logger import RobotLogger
from modules.vision_system import VisionSystem
from modules.robot_controller import RobotController
from modules.state_manager import StateManager
from modules.position_manager import PositionManager
from gui.main_window import MainWindow
from config.settings import LOG_FILE


def check_dependencies():
    """Check that all required dependencies are available"""
    logger = RobotLogger(LOG_FILE)
    logger.info("=" * 60)
    logger.info("Office Items Loan Robot - Starting Up")
    logger.info("=" * 60)
    
    errors = []
    
    # Check Arm_Lib
    try:
        from Arm_Lib import Arm_Device
        logger.info("✓ Arm_Lib loaded successfully")
    except ImportError as e:
        error_msg = f"✗ Arm_Lib not found: {e}"
        logger.error(error_msg)
        logger.error("Make sure Arm_Lib is copied to project root")
        logger.error("See SETUP.md for instructions")
        errors.append("Arm_Lib not available - robot control will not work")
    
    # Check model file
    model_path = project_root / 'models' / 'fine-tunedmodel.pt'
    if not model_path.exists():
        error_msg = f"✗ Model file not found: {model_path}"
        logger.error(error_msg)
        errors.append("Model file missing: models/fine-tunedmodel.pt")
    else:
        logger.info(f"✓ Model file found: {model_path}")
    
    # Check Python packages
    packages = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'PIL': 'Pillow',
        'ultralytics': 'ultralytics'
    }
    
    for module, package in packages.items():
        try:
            __import__(module)
            logger.info(f"✓ {package} available")
        except ImportError:
            error_msg = f"✗ {package} not installed"
            logger.error(error_msg)
            errors.append(f"Python package missing: {package}")
    
    return errors, logger


def initialize_systems(logger):
    """Initialize all system components"""
    logger.info("\nInitializing systems...")
    
    # Initialize position manager
    logger.info("Loading position configurations...")
    position_manager = PositionManager()
    
    # Initialize state manager
    logger.info("Initializing state manager...")
    state_manager = StateManager()
    
    # Initialize robot controller
    logger.info("Initializing robot controller...")
    robot_controller = RobotController(position_manager)
    
    # Initialize vision system
    logger.info("Initializing vision system...")
    model_path = project_root / 'models' / 'fine-tunedmodel.pt'
    
    try:
        vision_system = VisionSystem(str(model_path))
    except Exception as e:
        logger.error(f"Failed to initialize vision system: {e}")
        vision_system = None
    
    logger.info("\nSystem initialization complete!")
    logger.info("=" * 60)
    
    return vision_system, robot_controller, state_manager, position_manager


def on_closing(app, root, logger):
    """Handle application closure"""
    result = messagebox.askokcancel(
        "Quit",
        "Are you sure you want to quit?\n\nThe robot will return to home position."
    )
    
    if result:
        logger.info("User initiated shutdown")
        app.cleanup()
        root.destroy()


def main():
    """Application entry point"""
    # Check dependencies
    errors, logger = check_dependencies()
    
    # Show critical errors
    if errors:
        error_msg = "Critical errors detected:\n\n" + "\n".join(f"• {e}" for e in errors)
        error_msg += "\n\nSee terminal/log for details."
        
        root = tk.Tk()
        root.withdraw()
        
        result = messagebox.askyesno(
            "Startup Errors",
            error_msg + "\n\nContinue anyway? (Some features may not work)",
            icon='warning'
        )
        
        root.destroy()
        
        if not result:
            logger.info("User cancelled startup due to errors")
            return
    
    # Initialize systems
    try:
        vision, robot, state, positions = initialize_systems(logger)
        
        if vision is None:
            messagebox.showerror(
                "Initialization Error",
                "Failed to initialize vision system.\n\nCannot continue without camera/model."
            )
            return
    
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        messagebox.showerror(
            "Initialization Error",
            f"Failed to initialize systems:\n\n{e}\n\nSee log for details."
        )
        return
    
    # Create and run GUI
    try:
        logger.info("Starting GUI...")
        root = tk.Tk()
        app = MainWindow(root, vision, robot, state, positions)
        
        # Handle window close
        root.protocol("WM_DELETE_WINDOW", lambda: on_closing(app, root, logger))
        
        logger.info("Application ready!")
        logger.info("=" * 60)
        
        # Start main loop
        root.mainloop()
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        messagebox.showerror(
            "Application Error",
            f"An error occurred:\n\n{e}\n\nSee log file for details."
        )
    
    finally:
        logger.info("Application shutdown complete")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
