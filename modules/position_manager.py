"""
Position management system for robot arm
Handles loading, saving, and validating robot positions
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    DEFAULT_HOME_POSITION,
    DEFAULT_DROP_ZONE_POSITION,
    DEFAULT_GRIPPER_OPEN,
    DEFAULT_GRIPPER_CLOSED,
    POSITION_NAMES,
    JOINT_MIN,
    JOINT_MAX
)
from utils.logger import RobotLogger


class PositionManager:
    """
    Manage robot positions (save/load from JSON)
    """
    
    def __init__(self, config_file='config/positions.json'):
        """
        Load positions from file or use defaults
        
        Position structure:
        {
            'home': [90, 90, 90, 90, 90, 90],
            'drop_zone': [90, 90, 90, 90, 90, 90],
            'chair_storage': [90, 90, 90, 90, 90, 90],
            ...
            'gripper_open': 90,
            'gripper_closed': 135
        }
        """
        self.logger = RobotLogger()
        self.config_file = config_file
        self.positions = {}
        
        # Initialize with defaults
        self._load_defaults()
        
        # Try to load from file
        if os.path.exists(config_file):
            self.load_positions()
        else:
            self.logger.warning(f"Position file not found: {config_file}. Using defaults.")
            self.save_positions()  # Create default file
    
    def _load_defaults(self):
        """Load default positions"""
        self.positions = {
            'home': DEFAULT_HOME_POSITION.copy(),
            'drop_zone': DEFAULT_DROP_ZONE_POSITION.copy(),
            'chair_storage': DEFAULT_HOME_POSITION.copy(),
            'keyboard_storage': DEFAULT_HOME_POSITION.copy(),
            'mouse_storage': DEFAULT_HOME_POSITION.copy(),
            'headphones_storage': DEFAULT_HOME_POSITION.copy(),
            'mobile_phone_storage': DEFAULT_HOME_POSITION.copy(),
            'pen_storage': DEFAULT_HOME_POSITION.copy(),
            'gripper_open': DEFAULT_GRIPPER_OPEN,
            'gripper_closed': DEFAULT_GRIPPER_CLOSED
        }
    
    def get_position(self, position_name: str) -> Optional[List[int]]:
        """Get joint angles for named position"""
        if position_name not in self.positions:
            self.logger.error(f"Position not found: {position_name}")
            return None
        
        position = self.positions[position_name]
        
        # Handle gripper positions (single value)
        if position_name in ['gripper_open', 'gripper_closed']:
            return position
        
        # Return copy to prevent modification
        return position.copy() if isinstance(position, list) else position
    
    def set_position(self, position_name: str, angles: List[int]) -> bool:
        """Update position (not saved until save_positions called)"""
        # Validate position name
        if position_name not in ['gripper_open', 'gripper_closed']:
            if position_name not in POSITION_NAMES:
                self.logger.error(f"Invalid position name: {position_name}")
                return False
        
        # Validate angles
        if position_name in ['gripper_open', 'gripper_closed']:
            # Single value for gripper
            if not isinstance(angles, (int, float)):
                self.logger.error(f"Gripper position must be a single value")
                return False
            if not self.validate_angle(angles):
                return False
            self.positions[position_name] = int(angles)
        else:
            # List of 6 angles for joint positions
            if not self.validate_position(angles):
                return False
            self.positions[position_name] = [int(a) for a in angles]
        
        self.logger.debug(f"Position updated: {position_name} = {angles}")
        return True
    
    def save_positions(self) -> bool:
        """Save current positions to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.positions, f, indent=2)
            
            self.logger.info(f"Positions saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save positions: {e}")
            return False
    
    def load_positions(self) -> bool:
        """Load positions from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                loaded = json.load(f)
            
            # Validate and update positions
            for name, value in loaded.items():
                if name in ['gripper_open', 'gripper_closed']:
                    if self.validate_angle(value):
                        self.positions[name] = value
                elif name in POSITION_NAMES:
                    if self.validate_position(value):
                        self.positions[name] = value
            
            self.logger.info(f"Positions loaded from {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load positions: {e}")
            return False
    
    def get_all_positions(self) -> Dict:
        """Return all positions dictionary"""
        return self.positions.copy()
    
    def validate_angle(self, angle: float) -> bool:
        """Validate single angle is within safe range"""
        if not isinstance(angle, (int, float)):
            self.logger.error(f"Angle must be numeric: {angle}")
            return False
        
        if not (JOINT_MIN <= angle <= JOINT_MAX):
            self.logger.error(f"Angle out of range ({JOINT_MIN}-{JOINT_MAX}): {angle}")
            return False
        
        return True
    
    def validate_position(self, angles: List[int]) -> bool:
        """
        Validate joint angles are within safe ranges
        Typically: 0-180 degrees per joint
        """
        if not isinstance(angles, list):
            self.logger.error(f"Position must be a list: {type(angles)}")
            return False
        
        if len(angles) != 6:
            self.logger.error(f"Position must have 6 angles, got {len(angles)}")
            return False
        
        for i, angle in enumerate(angles):
            if not self.validate_angle(angle):
                self.logger.error(f"Invalid angle at joint {i+1}: {angle}")
                return False
        
        return True
    
    def reset_to_defaults(self):
        """Reset all positions to defaults"""
        self._load_defaults()
        self.logger.info("Positions reset to defaults")
    
    def get_storage_position_for_item(self, item_name: str) -> Optional[str]:
        """
        Get storage position name for an item
        
        Args:
            item_name: e.g., 'Chair', 'Computer Mouse'
        
        Returns:
            position_name: e.g., 'chair_storage', 'mouse_storage'
        """
        # Convert item name to position name
        # 'Chair' -> 'chair_storage'
        # 'Computer Mouse' -> 'mouse_storage'
        
        item_lower = item_name.lower()
        
        # Handle 'Computer X' items
        if item_lower.startswith('computer '):
            item_lower = item_lower.replace('computer ', '')
        
        # Replace spaces with underscores
        position_name = item_lower.replace(' ', '_') + '_storage'
        
        if position_name in self.positions:
            return position_name
        
        self.logger.error(f"No storage position found for item: {item_name}")
        return None
