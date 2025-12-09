"""
State management system for tracking item availability
"""

from typing import Dict, List
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import ITEM_CLASSES
from utils.logger import RobotLogger


class StateManager:
    """
    Track item availability (no persistence)
    """
    
    # Status constants
    STATUS_AVAILABLE = 'AVAILABLE'
    STATUS_LOANED_OUT = 'LOANED_OUT'
    
    def __init__(self):
        """
        Initialize all items as LOANED_OUT
        
        State structure:
        {
            'Chair': 'LOANED_OUT',
            'Computer Keyboard': 'LOANED_OUT',
            'Computer Mouse': 'LOANED_OUT',
            'Headphones': 'LOANED_OUT',
            'Mobile Phone': 'LOANED_OUT',
            'Pen': 'LOANED_OUT'
        }
        """
        self.logger = RobotLogger()
        self.state = {}
        
        # Initialize all items as loaned out
        for item in ITEM_CLASSES:
            self.state[item] = self.STATUS_LOANED_OUT
        
        self.logger.info("State initialized - all items marked as LOANED_OUT")
    
    def get_available_items(self) -> List[str]:
        """Return list of items with status 'AVAILABLE'"""
        available = [
            item for item, status in self.state.items()
            if status == self.STATUS_AVAILABLE
        ]
        self.logger.debug(f"Available items: {available}")
        return available
    
    def get_loaned_items(self) -> List[str]:
        """Return list of items with status 'LOANED_OUT'"""
        loaned = [
            item for item, status in self.state.items()
            if status == self.STATUS_LOANED_OUT
        ]
        self.logger.debug(f"Loaned items: {loaned}")
        return loaned
    
    def is_available(self, item_name: str) -> bool:
        """Check if specific item is available"""
        if item_name not in self.state:
            self.logger.error(f"Unknown item: {item_name}")
            return False
        
        return self.state[item_name] == self.STATUS_AVAILABLE
    
    def mark_available(self, item_name: str) -> bool:
        """Mark item as AVAILABLE (after return)"""
        if item_name not in self.state:
            self.logger.error(f"Cannot mark unknown item as available: {item_name}")
            return False
        
        self.state[item_name] = self.STATUS_AVAILABLE
        self.logger.info(f"Item marked as AVAILABLE: {item_name}")
        return True
    
    def mark_loaned(self, item_name: str) -> bool:
        """Mark item as LOANED_OUT (after borrow)"""
        if item_name not in self.state:
            self.logger.error(f"Cannot mark unknown item as loaned: {item_name}")
            return False
        
        self.state[item_name] = self.STATUS_LOANED_OUT
        self.logger.info(f"Item marked as LOANED_OUT: {item_name}")
        return True
    
    def get_status(self, item_name: str) -> str:
        """Get current status of item"""
        if item_name not in self.state:
            self.logger.error(f"Unknown item: {item_name}")
            return "UNKNOWN"
        
        return self.state[item_name]
    
    def reset_all_loaned(self):
        """Reset all items to LOANED_OUT (settings option)"""
        for item in self.state:
            self.state[item] = self.STATUS_LOANED_OUT
        
        self.logger.info("All items reset to LOANED_OUT")
    
    def get_all_status(self) -> Dict[str, str]:
        """Return complete status dictionary"""
        return self.state.copy()
    
    def get_item_count_by_status(self) -> Dict[str, int]:
        """Get count of items by status"""
        counts = {
            self.STATUS_AVAILABLE: len(self.get_available_items()),
            self.STATUS_LOANED_OUT: len(self.get_loaned_items())
        }
        return counts
