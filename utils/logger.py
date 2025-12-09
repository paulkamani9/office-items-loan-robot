"""
Centralized logging system for Office Items Loan Robot
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

class RobotLogger:
    """
    Unified logging system for all operations
    
    Logs to:
    - Console (INFO and above)
    - File (DEBUG and above)
    """
    
    def __init__(self, log_file='robot.log', console_level='INFO', file_level='DEBUG'):
        """Setup logging configuration"""
        self.logger = logging.getLogger('OfficeRobot')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level))
        console_format = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, file_level))
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def info(self, message):
        """Log informational message"""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message):
        """Log error message"""
        self.logger.error(message)
    
    def debug(self, message):
        """Log debug message (file only)"""
        self.logger.debug(message)
    
    def critical(self, message):
        """Log critical message"""
        self.logger.critical(message)
