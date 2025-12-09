"""
Central configuration for Office Items Loan Robot system
"""

# Detection Parameters
CONFIDENCE_THRESHOLD = 0.80
DETECTION_INTERVAL = 1.0  # seconds between classifications in return mode
INITIAL_WAIT_BEFORE_DETECTION = 3.0  # seconds to wait after entering return mode
SAFETY_WAIT_AFTER_DETECTION = 2.0  # seconds after successful detection before picking
STABLE_DETECTION_COUNT = 3  # Number of consecutive detections required

# Movement Parameters
SPEED_NORMAL = 1000
SPEED_SLOW = 500
SPEED_FAST = 1500

# Camera Settings
CAMERA_ID = 0
CAMERA_WIDTH = 416  # Match model training size
CAMERA_HEIGHT = 416
CROP_PERCENTAGE = 0.70

# Item Classes
ITEM_CLASSES = [
    'Chair',
    'Computer Keyboard',
    'Computer Mouse',
    'Headphones',
    'Mobile Phone',
    'Pen'
]

# GUI Settings
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
THEME_COLOR_PRIMARY = '#2C3E50'
THEME_COLOR_SECONDARY = '#34495E'
THEME_COLOR_ACCENT = '#3498DB'
THEME_COLOR_SUCCESS = '#27AE60'
THEME_COLOR_DANGER = '#E74C3C'
THEME_COLOR_WARNING = '#F39C12'
THEME_COLOR_TEXT_LIGHT = '#ECF0F1'
THEME_COLOR_TEXT_DARK = '#2C3E50'

# Default Positions (overridden by positions.json if exists)
DEFAULT_HOME_POSITION = [90, 90, 90, 90, 90, 90]
DEFAULT_DROP_ZONE_POSITION = [90, 90, 90, 90, 90, 90]
DEFAULT_GRIPPER_OPEN = 90
DEFAULT_GRIPPER_CLOSED = 135

# Position names for calibration
POSITION_NAMES = [
    'home',
    'drop_zone',
    'chair_storage',
    'keyboard_storage',
    'mouse_storage',
    'headphones_storage',
    'mobile_phone_storage',
    'pen_storage'
]

# Joint angle limits (degrees)
JOINT_MIN = 0
JOINT_MAX = 180

# Logging
LOG_FILE = 'robot.log'
LOG_LEVEL_CONSOLE = 'INFO'
LOG_LEVEL_FILE = 'DEBUG'
