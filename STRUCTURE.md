# Project Structure

Complete directory structure of the Office Items Loan Robot project.

```
office-items-loan-robot/
│
├── Arm_Lib/                          # Yahboom Dofbot control library
│   ├── __init__.py                   # Library initialization
│   ├── Arm_Device.py                 # Main device control class
│   └── ...                           # Other Yahboom library files
│
├── config/                           # Configuration files
│   ├── __init__.py                   # Make config a package
│   ├── settings.py                   # System constants and settings
│   └── positions.json                # Calibrated robot positions
│
├── models/                           # Machine learning models
│   └── fine-tunedmodel.pt           # YOLOv8 classification model
│
├── modules/                          # Core system modules
│   ├── __init__.py                   # Make modules a package
│   ├── vision_system.py              # Camera and YOLO classification
│   ├── robot_controller.py           # Robot arm movement control
│   ├── state_manager.py              # Item availability tracking
│   └── position_manager.py           # Position storage and loading
│
├── gui/                              # Graphical user interface
│   ├── __init__.py                   # Make gui a package
│   ├── main_window.py                # Main application window
│   ├── borrow_screen.py              # Borrow interface
│   ├── return_screen.py              # Return interface with camera
│   ├── calibration_screen.py         # Position calibration screen
│   └── test_screen.py                # Test operations screen
│
├── utils/                            # Utility modules
│   ├── __init__.py                   # Make utils a package
│   └── logger.py                     # Logging system
│
├── venv/                             # Python virtual environment (created during setup)
│   ├── bin/                          # Executable files
│   ├── lib/                          # Python packages
│   └── ...
│
├── main.py                           # Application entry point
├── requirements.txt                  # Python dependencies
├── README.md                         # Project overview and usage
├── SETUP.md                          # Detailed setup instructions
├── LICENSE                           # MIT License
├── .gitignore                        # Git ignore rules
├── run.sh                            # Quick start script
├── robot.log                         # Application log file (created on first run)
└── STRUCTURE.md                      # This file
```

## File Descriptions

### Root Level

- **main.py**: Application entry point. Initializes all systems and launches GUI.
- **requirements.txt**: Python package dependencies for pip installation.
- **README.md**: Project overview, features, quick start guide, and usage instructions.
- **SETUP.md**: Comprehensive setup instructions with troubleshooting.
- **run.sh**: Bash script for quick application launch.
- **LICENSE**: MIT license with third-party component attributions.
- **.gitignore**: Git ignore patterns for Python, IDE, logs, and model files.
- **robot.log**: Runtime log file (created automatically).

### Arm_Lib/

Yahboom's proprietary library for Dofbot control. Copied from system installation.

**Key files:**

- `Arm_Device.py`: Main class for robot arm control
- Serial communication handlers
- Servo control functions

### config/

System configuration and settings.

- **settings.py**:

  - Detection parameters (confidence, intervals)
  - Movement speeds
  - Camera settings
  - Item class definitions
  - GUI theme colors
  - Default positions

- **positions.json**:
  - Calibrated joint angles for all positions
  - Gripper open/closed angles
  - Editable via GUI or manually
  - Example format:
    ```json
    {
      "home": [90, 90, 90, 90, 90, 90],
      "drop_zone": [100, 80, 100, 90, 90, 90],
      "gripper_open": 90,
      "gripper_closed": 135
    }
    ```

### models/

Machine learning model files.

- **fine-tunedmodel.pt**:
  - YOLOv8 classification model
  - Trained on 6 office item classes
  - PyTorch format (.pt)
  - Not included in repository (too large)
  - Must be obtained separately

### modules/

Core system functionality.

- **vision_system.py**:

  - Camera initialization and management
  - YOLOv8 model loading and inference
  - Image preprocessing and classification
  - Confidence threshold checking
  - Live feed for GUI display

- **robot_controller.py**:

  - Arm_Lib integration
  - Joint angle movement control
  - Pick and place sequences
  - Borrow/return operations
  - Emergency stop functionality
  - Safety checks and error handling

- **state_manager.py**:

  - Item availability tracking
  - Available/loaned status management
  - No persistence (resets on restart)
  - Status query methods

- **position_manager.py**:
  - Load positions from JSON
  - Save positions to JSON
  - Position validation
  - Default position management
  - Storage position mapping for items

### gui/

Tkinter-based graphical user interface.

- **main_window.py**:

  - Main application window
  - Navigation between screens
  - Header with emergency stop
  - Status bar with joint angles
  - Module initialization and cleanup

- **borrow_screen.py**:

  - Display available items
  - Item selection interface
  - Borrow operation with progress
  - State update after successful borrow

- **return_screen.py**:

  - Live camera feed display
  - Continuous item detection
  - Real-time classification results
  - Return operation with progress
  - Stability checking (multiple detections)

- **calibration_screen.py**:

  - Position selection dropdown
  - 6 joint angle sliders
  - 2 gripper position sliders
  - Test position functionality
  - Save/load position management
  - Reset to defaults option

- **test_screen.py**:
  - Test borrow operations
  - Test return operations
  - Camera classification testing
  - Live classification display
  - No state modification (pure testing)

### utils/

Utility modules for common functionality.

- **logger.py**:
  - Centralized logging system
  - Console and file logging
  - Configurable log levels
  - Timestamped entries
  - Used throughout application

## Data Flow

### Borrow Operation

```
User clicks BORROW
  → borrow_screen.py validates availability
  → robot_controller.py executes:
      1. Move to storage position
      2. Pick item
      3. Move to drop zone
      4. Place item
      5. Return home
  → state_manager.py marks item as loaned
  → GUI refreshes
```

### Return Operation

```
User places item in drop zone
  → return_screen.py activates camera
  → vision_system.py classifies continuously
  → Stable detection triggers:
      1. Safety wait
      2. robot_controller.py executes pick from drop zone
      3. Move to storage
      4. Place item
      5. Return home
  → state_manager.py marks item as available
  → GUI refreshes
```

### Calibration

```
User adjusts sliders
  → calibration_screen.py updates joint values
  → User clicks "Test Position"
  → robot_controller.py moves to test position
  → User clicks "Update Position"
  → position_manager.py stores in memory
  → User clicks "Save All Positions"
  → position_manager.py writes positions.json
```

## Module Dependencies

```
main.py
  ├── utils/logger.py
  ├── modules/vision_system.py
  │   ├── config/settings.py
  │   └── utils/logger.py
  ├── modules/robot_controller.py
  │   ├── Arm_Lib/
  │   ├── config/settings.py
  │   ├── modules/position_manager.py
  │   └── utils/logger.py
  ├── modules/state_manager.py
  │   ├── config/settings.py
  │   └── utils/logger.py
  ├── modules/position_manager.py
  │   ├── config/settings.py
  │   └── utils/logger.py
  └── gui/main_window.py
      ├── config/settings.py
      ├── utils/logger.py
      └── gui/* (other screens)
          ├── All module dependencies
          └── config/settings.py
```

## Configuration Files

### settings.py Variables

**Detection:**

- `CONFIDENCE_THRESHOLD`
- `DETECTION_INTERVAL`
- `INITIAL_WAIT_BEFORE_DETECTION`
- `SAFETY_WAIT_AFTER_DETECTION`
- `STABLE_DETECTION_COUNT`

**Movement:**

- `SPEED_NORMAL`
- `SPEED_SLOW`
- `SPEED_FAST`

**Camera:**

- `CAMERA_ID`
- `CAMERA_WIDTH`
- `CAMERA_HEIGHT`
- `CROP_PERCENTAGE`

**Items:**

- `ITEM_CLASSES` (list of 6 items)

**GUI:**

- `WINDOW_WIDTH`
- `WINDOW_HEIGHT`
- Theme colors (PRIMARY, ACCENT, SUCCESS, etc.)

**Positions:**

- `DEFAULT_HOME_POSITION`
- `DEFAULT_DROP_ZONE_POSITION`
- `DEFAULT_GRIPPER_OPEN`
- `DEFAULT_GRIPPER_CLOSED`
- `POSITION_NAMES` (list of 8 positions)
- `JOINT_MIN`, `JOINT_MAX`

### positions.json Structure

```json
{
  "home": [90, 90, 90, 90, 90, 90],
  "drop_zone": [90, 90, 90, 90, 90, 90],
  "chair_storage": [90, 90, 90, 90, 90, 90],
  "keyboard_storage": [90, 90, 90, 90, 90, 90],
  "mouse_storage": [90, 90, 90, 90, 90, 90],
  "headphones_storage": [90, 90, 90, 90, 90, 90],
  "mobile_phone_storage": [90, 90, 90, 90, 90, 90],
  "pen_storage": [90, 90, 90, 90, 90, 90],
  "gripper_open": 90,
  "gripper_closed": 135
}
```

## Logs

**robot.log** format:

```
2025-12-10 10:30:15 - OfficeRobot - INFO - Starting Office Items Loan Robot
2025-12-10 10:30:16 - OfficeRobot - INFO - ✓ Arm_Lib loaded successfully
2025-12-10 10:30:17 - OfficeRobot - INFO - ✓ Model loaded - Expected input size: 416x416
2025-12-10 10:30:18 - OfficeRobot - INFO - ✓ Camera initialized successfully
2025-12-10 10:30:19 - OfficeRobot - INFO - Moving to home: [90, 90, 90, 90, 90, 90]
```

## Adding New Features

### Adding a New Item Class

1. **Retrain model** with new class
2. **Update config/settings.py:**

   ```python
   ITEM_CLASSES = [
       'Chair',
       'Computer Keyboard',
       'Computer Mouse',
       'Headphones',
       'Mobile Phone',
       'Pen',
       'New Item'  # Add here
   ]

   POSITION_NAMES = [
       'home',
       'drop_zone',
       # ... existing ...
       'new_item_storage'  # Add here
   ]
   ```

3. **Calibrate** new storage position in GUI
4. **Update GUI layouts** if grid sizing changes

### Adding a New Screen

1. Create new file in `gui/` (e.g., `gui/new_screen.py`)
2. Implement screen class following existing patterns
3. Add navigation in `gui/main_window.py`:
   ```python
   def show_new_screen(self):
       from gui.new_screen import NewScreen
       self.clear_content()
       self.current_screen = NewScreen(...)
   ```
4. Add button in main menu

---

**For more information, see README.md and SETUP.md**
