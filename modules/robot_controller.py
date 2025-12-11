"""
Robot controller for Yahboom Dofbot arm
Handles all robot movements and operations
"""

import time
from typing import List, Optional, Callable, Dict
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from Arm_Lib import Arm_Device
    ARM_LIB_AVAILABLE = True
except ImportError:
    ARM_LIB_AVAILABLE = False
    print("Warning: Arm_Lib not available. Robot control will not work.")

from config.settings import (
    SPEED_NORMAL,
    SPEED_SLOW,
    SPEED_FAST
)
from utils.logger import RobotLogger
from modules.position_manager import PositionManager


class RobotController:
    """
    Control robot arm movements
    """
    
    def __init__(self, position_manager: PositionManager):
        """
        Initialize Arm_Lib device
        IMPORTANT: Arm_Lib is copied into project root
        Import as: from Arm_Lib import Arm_Device
        """
        self.logger = RobotLogger()
        self.position_manager = position_manager
        self.arm = None
        self.current_angles = [90, 90, 90, 90, 90, 90]
        
        if not ARM_LIB_AVAILABLE:
            self.logger.error("✗ Arm_Lib not available - robot control disabled")
            return
        
        try:
            self.arm = Arm_Device()
            time.sleep(0.1)
            self.logger.info("✓ Robot arm initialized")
            
            # Move to home position
            self.move_home()
            
        except Exception as e:
            self.logger.error(f"✗ Failed to initialize robot arm: {e}")
            self.arm = None
    
    def is_connected(self) -> bool:
        """Check if robot is connected"""
        return self.arm is not None
    
    def move_to_position(self, position_name: str, speed: int = SPEED_NORMAL) -> bool:
        """
        Move robot to named position from positions.json
        
        Args:
            position_name: 'home', 'drop_zone', 'chair_storage', etc.
            speed: Movement speed in ms
        
        Returns:
            success: bool
        """
        if not self.is_connected():
            self.logger.error("Robot not connected")
            return False
        
        # Get position from manager
        angles = self.position_manager.get_position(position_name)
        if angles is None:
            self.logger.error(f"Position not found: {position_name}")
            return False
        
        # Move to position
        self.logger.info(f"Moving to {position_name}: {angles}")
        return self.move_to_joint_angles(angles, speed)
    
    def move_to_joint_angles(self, angles: List[int], speed: int = SPEED_NORMAL) -> bool:
        """
        Move to specific joint angles [j1, j2, j3, j4, j5, j6]
        
        Includes:
        - Validation of angle ranges
        - Wait for movement completion
        - Error handling
        """
        if not self.is_connected():
            self.logger.error("Robot not connected")
            return False
        
        if not self.position_manager.validate_position(angles):
            self.logger.error(f"Invalid position: {angles}")
            return False
        
        try:
            # Send movement command
            self.arm.Arm_serial_servo_write6(
                angles[0], angles[1], angles[2],
                angles[3], angles[4], angles[5],
                speed
            )
            
            # Update current angles
            self.current_angles = angles.copy()
            
            # Wait for movement to complete
            # Speed is in ms, add small buffer
            wait_time = speed / 1000.0 + 0.5
            time.sleep(wait_time)
            
            self.logger.debug(f"Moved to {angles}")
            return True
            
        except Exception as e:
            self.logger.error(f"Movement error: {e}")
            return False
    
    def open_gripper(self) -> bool:
        """Open gripper to configured GRIPPER_OPEN angle"""
        if not self.is_connected():
            return False
        
        angle = self.position_manager.get_position('gripper_open')
        if angle is None:
            angle = 131  # Default fallback
            self.logger.warning("Using default gripper_open angle: 131")
        
        try:
            # Use individual servo control for gripper (servo 6)
            self.logger.debug(f"Opening gripper to angle: {angle}")
            self.arm.Arm_serial_servo_write(6, angle, 500)
            self.current_angles[5] = angle  # Update servo 6 (index 5)
            time.sleep(0.6)
            self.logger.debug("Gripper opened")
            return True
        except Exception as e:
            self.logger.error(f"Failed to open gripper: {e}")
            return False
    
    def close_gripper(self) -> bool:
        """Close gripper to configured GRIPPER_CLOSED angle"""
        if not self.is_connected():
            return False
        
        angle = self.position_manager.get_position('gripper_closed')
        if angle is None:
            angle = 15  # Default fallback
            self.logger.warning("Using default gripper_closed angle: 15")
        
        try:
            # Use individual servo control for gripper (servo 6)
            self.logger.debug(f"Closing gripper to angle: {angle}")
            self.arm.Arm_serial_servo_write(6, angle, 500)
            self.current_angles[5] = angle  # Update servo 6 (index 5)
            time.sleep(0.6)
            self.logger.debug("Gripper closed")
            return True
        except Exception as e:
            self.logger.error(f"Failed to close gripper: {e}")
            return False
    
    def move_wrist(self, angle: int, speed: int = 500) -> bool:
        """Move wrist (servo 5) to specific angle (0-270)"""
        if not self.is_connected():
            return False
        
        if angle < 0 or angle > 270:
            self.logger.error(f"Wrist angle out of range (0-270): {angle}")
            return False
        
        try:
            self.logger.debug(f"Moving wrist to angle: {angle}")
            self.arm.Arm_serial_servo_write(5, angle, speed)
            self.current_angles[4] = angle  # Update servo 5 (index 4)
            time.sleep(speed / 1000.0 + 0.1)
            return True
        except Exception as e:
            self.logger.error(f"Failed to move wrist: {e}")
            return False
    
    def get_current_angles(self) -> List[int]:
        """
        Read and return current joint angles
        Used for real-time display in GUI
        """
        # Note: Yahboom Dofbot may not support reading angles
        # Return last known angles instead
        return self.current_angles.copy()
    
    def lift_to_travel_height(self, status_callback: Optional[Callable] = None) -> bool:
        """
        Lift arm vertically to travel height from current position.
        This keeps the base (J1) rotation the same and only adjusts
        the shoulder/elbow joints (J2, J3, J4) to lift straight up.
        
        This prevents sweeping sideways while low which could knock items over.
        """
        if not self.is_connected():
            return False
        
        if status_callback:
            status_callback("Lifting to safe height...")
        
        # Get travel position angles for reference (the "safe" joint configuration)
        travel_angles = self.position_manager.get_position('travel_position')
        if travel_angles is None:
            # Fallback: just lift shoulder
            self.logger.warning("travel_position not found, using fallback lift")
            lifted_angles = self.current_angles.copy()
            lifted_angles[1] = max(0, lifted_angles[1] - 20)  # Lift shoulder
            lifted_angles[2] = min(180, lifted_angles[2] + 10)  # Adjust elbow
            return self.move_to_joint_angles(lifted_angles, SPEED_NORMAL)
        
        # Create dynamic travel position:
        # Keep current base rotation (J1), but use travel height for J2, J3, J4
        lifted_angles = self.current_angles.copy()
        lifted_angles[1] = travel_angles[1]  # Shoulder - use travel height
        lifted_angles[2] = travel_angles[2]  # Elbow - use travel configuration
        lifted_angles[3] = travel_angles[3]  # Wrist pitch - use travel configuration
        # Keep J1 (base), J5 (wrist roll), J6 (gripper) as they are
        
        self.logger.debug(f"Lifting from {self.current_angles} to {lifted_angles}")
        return self.move_to_joint_angles(lifted_angles, SPEED_NORMAL)
    
    def move_to_position_keep_gripper(self, position_name: str, speed: int = SPEED_NORMAL) -> bool:
        """
        Move robot to named position but keep current gripper angle.
        This prevents the stored gripper value in positions from overriding
        the current gripper state.
        """
        if not self.is_connected():
            self.logger.error("Robot not connected")
            return False
        
        # Get position from manager
        angles = self.position_manager.get_position(position_name)
        if angles is None:
            self.logger.error(f"Position not found: {position_name}")
            return False
        
        # Keep current gripper angle (index 5 = servo 6)
        angles_keep_gripper = angles.copy()
        angles_keep_gripper[5] = self.current_angles[5]
        
        self.logger.info(f"Moving to {position_name} (keeping gripper): {angles_keep_gripper}")
        return self.move_to_joint_angles(angles_keep_gripper, speed)
    
    def execute_pick_sequence(self, from_position: str, 
                             status_callback: Optional[Callable] = None) -> bool:
        """
        Complete pick sequence:
        1. Open gripper first
        2. Move to travel height above the target position (safe approach)
        3. Descend to pickup position (keeping gripper open)
        4. Wait briefly
        5. Close gripper
        6. Lift straight up (dynamic travel) before moving sideways
        """
        if status_callback:
            status_callback(f"Picking from {from_position}...")
        
        # Open gripper before approaching
        if not self.open_gripper():
            self.logger.warning("Failed to open gripper, continuing anyway")
        
        # Get the target position angles
        target_angles = self.position_manager.get_position(from_position)
        if target_angles is None:
            self.logger.error(f"Position not found: {from_position}")
            return False
        
        # Get travel position for safe height reference
        travel_angles = self.position_manager.get_position('travel_position')
        if travel_angles is None:
            self.logger.warning("travel_position not found, moving directly")
        else:
            # Create approach position: target's base rotation (J1) but at travel height (J2, J3, J4)
            approach_angles = target_angles.copy()
            approach_angles[1] = travel_angles[1]  # Shoulder at travel height
            approach_angles[2] = travel_angles[2]  # Elbow at travel config
            approach_angles[3] = travel_angles[3]  # Wrist pitch at travel config
            approach_angles[5] = self.current_angles[5]  # Keep gripper open
            
            if status_callback:
                status_callback(f"Moving above {from_position}...")
            
            # First move to safe height above target
            if not self.move_to_joint_angles(approach_angles, SPEED_NORMAL):
                self.logger.warning("Could not move to approach position")
        
        # Now descend to the actual pick position (keeping gripper open)
        if status_callback:
            status_callback(f"Descending to {from_position}...")
        
        if not self.move_to_position_keep_gripper(from_position, SPEED_NORMAL):
            return False
        
        # Wait for stability
        time.sleep(0.3)
        
        # Now close gripper to grab the item
        if not self.close_gripper():
            return False
        
        # Wait for grip
        time.sleep(0.3)
        
        # Lift straight up first (dynamic travel - keeps base rotation, only lifts)
        if status_callback:
            status_callback("Lifting item...")
        
        if not self.lift_to_travel_height(status_callback):
            self.logger.warning("Could not lift to travel height")
            # Continue anyway, next movement will handle it
        
        self.logger.info(f"Pick sequence completed from {from_position}")
        return True
    
    def execute_place_sequence(self, to_position: str,
                              status_callback: Optional[Callable] = None) -> bool:
        """
        Complete place sequence:
        1. Already at travel height from pick sequence
        2. Move to travel height above target position (safe approach)
        3. Descend to place position (keeping gripper closed)
        4. Open gripper to release
        5. Wait briefly
        6. Lift straight up (dynamic travel) before moving sideways
        """
        if status_callback:
            status_callback(f"Placing at {to_position}...")
        
        # Get the target position angles
        target_angles = self.position_manager.get_position(to_position)
        if target_angles is None:
            self.logger.error(f"Position not found: {to_position}")
            return False
        
        # Get travel position for safe height reference
        travel_angles = self.position_manager.get_position('travel_position')
        if travel_angles is None:
            self.logger.warning("travel_position not found, moving directly")
        else:
            # Create approach position: target's base rotation (J1) but at travel height (J2, J3, J4)
            approach_angles = target_angles.copy()
            approach_angles[1] = travel_angles[1]  # Shoulder at travel height
            approach_angles[2] = travel_angles[2]  # Elbow at travel config
            approach_angles[3] = travel_angles[3]  # Wrist pitch at travel config
            approach_angles[5] = self.current_angles[5]  # Keep gripper closed (carrying item)
            
            if status_callback:
                status_callback(f"Moving above {to_position}...")
            
            # First move to safe height above target
            if not self.move_to_joint_angles(approach_angles, SPEED_NORMAL):
                self.logger.warning("Could not move to approach position")
        
        # Now descend to the actual place position (keeping gripper closed)
        if status_callback:
            status_callback(f"Descending to {to_position}...")
        
        if not self.move_to_position_keep_gripper(to_position, SPEED_NORMAL):
            return False
        
        # Now open gripper to release item
        if not self.open_gripper():
            return False
        
        # Wait for release
        time.sleep(0.3)
        
        # Lift straight up first (dynamic travel - keeps base rotation, only lifts)
        if status_callback:
            status_callback("Lifting arm...")
        
        if not self.lift_to_travel_height(status_callback):
            self.logger.warning("Could not lift to travel height after placing")
            # Continue anyway
        
        self.logger.info(f"Place sequence completed at {to_position}")
        return True
    
    def borrow_item(self, item_name: str, 
                   status_callback: Optional[Callable] = None) -> Dict:
        """
        Complete borrow operation:
        1. Pick from item's storage position
        2. Deliver to drop zone
        3. Return to home
        
        Returns status at each step for GUI updates
        """
        try:
            # Get storage position for item
            storage_pos = self.position_manager.get_storage_position_for_item(item_name)
            if storage_pos is None:
                return {'success': False, 'message': f'No storage position for {item_name}'}
            
            # Step 1: Move to storage and pick
            if status_callback:
                status_callback(f"Moving to {item_name} storage...")
            
            if not self.execute_pick_sequence(storage_pos, status_callback):
                raise Exception(f"Failed to pick from {storage_pos}")
            
            # Step 2: Deliver to drop zone
            if status_callback:
                status_callback("Delivering to drop zone...")
            
            if not self.execute_place_sequence('drop_zone', status_callback):
                raise Exception("Failed to place at drop zone")
            
            # Step 3: Return home
            if status_callback:
                status_callback("Returning home...")
            
            if not self.move_home():
                raise Exception("Failed to return home")
            
            if status_callback:
                status_callback(f"✓ {item_name} borrowed successfully!")
            
            self.logger.info(f"Borrow completed: {item_name}")
            return {'success': True, 'message': 'Borrow completed'}
            
        except Exception as e:
            self.logger.error(f"Borrow failed: {e}")
            
            # Recovery: Try to return home safely
            try:
                self.move_home()
            except:
                pass
            
            return {'success': False, 'message': str(e)}
    
    def return_item(self, item_name: str,
                   status_callback: Optional[Callable] = None) -> Dict:
        """
        Complete return operation:
        1. Pick from drop zone
        2. Deliver to item's storage position
        3. Return to home
        
        Returns status at each step for GUI updates
        """
        try:
            # Get storage position for item
            storage_pos = self.position_manager.get_storage_position_for_item(item_name)
            if storage_pos is None:
                return {'success': False, 'message': f'No storage position for {item_name}'}
            
            # Step 1: Pick from drop zone
            if status_callback:
                status_callback("Picking item from drop zone...")
            
            if not self.execute_pick_sequence('drop_zone', status_callback):
                raise Exception("Failed to pick from drop zone")
            
            # Step 2: Deliver to storage
            if status_callback:
                status_callback(f"Storing {item_name}...")
            
            if not self.execute_place_sequence(storage_pos, status_callback):
                raise Exception(f"Failed to place at {storage_pos}")
            
            # Step 3: Return to observation position for next item
            if status_callback:
                status_callback("Returning to observation position...")
            
            if not self.move_to_observation_position(status_callback):
                # Fallback to home if observation position fails
                self.logger.warning("Could not move to observation position, going home")
                self.move_home()
            
            if status_callback:
                status_callback(f"✓ {item_name} returned successfully!")
            
            self.logger.info(f"Return completed: {item_name}")
            return {'success': True, 'message': 'Return completed'}
            
        except Exception as e:
            self.logger.error(f"Return failed: {e}")
            
            # Recovery: Try to return to observation position or home safely
            try:
                if not self.move_to_observation_position():
                    self.move_home()
            except:
                pass
            
            return {'success': False, 'message': str(e)}
    
    def move_to_observation_position(self, status_callback: Optional[Callable] = None) -> bool:
        """
        Move to observation position (camera view for classification in return mode)
        Uses the calibrated observation_position from positions.json
        """
        if status_callback:
            status_callback("Moving to observation position...")
        
        # Try to use calibrated observation position first
        observation_angles = self.position_manager.get_position('observation_position')
        
        if observation_angles is not None:
            return self.move_to_joint_angles(observation_angles, SPEED_NORMAL)
        
        # Fallback: Use drop zone position but lift higher
        self.logger.warning("observation_position not found, using fallback")
        drop_zone_angles = self.position_manager.get_position('drop_zone')
        if drop_zone_angles is None:
            return False
        
        # Lift camera higher for better view
        fallback_angles = drop_zone_angles.copy()
        fallback_angles[1] = max(0, fallback_angles[1] - 15)
        
        return self.move_to_joint_angles(fallback_angles, SPEED_NORMAL)
    
    def move_to_travel_position(self, status_callback: Optional[Callable] = None) -> bool:
        """
        Move to travel position (safe height for carrying items between positions)
        """
        if status_callback:
            status_callback("Moving to travel position...")
        
        return self.move_to_position('travel_position', SPEED_NORMAL)
    
    def emergency_stop(self):
        """
        Immediate stop of all movements
        Safe shutdown sequence
        """
        self.logger.warning("EMERGENCY STOP ACTIVATED")
        
        if not self.is_connected():
            return
        
        try:
            # Stop all servos
            for i in range(1, 7):
                self.arm.Arm_serial_servo_write(i, self.current_angles[i-1], 0)
            
            self.logger.info("Emergency stop completed")
            
        except Exception as e:
            self.logger.error(f"Emergency stop error: {e}")
    
    def move_home(self) -> bool:
        """Return to home position"""
        return self.move_to_position('home', SPEED_NORMAL)
    
    def cleanup(self):
        """Safe shutdown of robot"""
        if self.is_connected():
            try:
                self.move_home()
                time.sleep(1)
                del self.arm
                self.arm = None
                self.logger.info("Robot shutdown complete")
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
    
    def __del__(self):
        """Ensure cleanup on deletion"""
        self.cleanup()
