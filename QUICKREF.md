# Quick Reference Guide

Fast reference for common tasks and commands.

## Quick Start

```bash
# 1. Navigate to project
cd ~/Documents/office-items-loan-robot

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run application
python main.py

# OR use quick start script
./run.sh
```

## Common Commands

### Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy Arm_Lib
sudo cp -r /usr/lib/python3/dist-packages/Arm_Lib ./
sudo chown -R $USER:$USER Arm_Lib/

# Setup permissions
sudo usermod -aG dialout $USER
sudo reboot
```

### Running

```bash
# Normal run
python main.py

# With debug output
python main.py 2>&1 | tee debug.log

# Quick start script
./run.sh
```

### Troubleshooting

```bash
# Check logs
tail -f robot.log

# View last 50 lines
tail -n 50 robot.log

# Check camera
ls /dev/video*
cheese  # or
ffplay /dev/video0

# Check serial port
ls /dev/ttyUSB*
groups | grep dialout

# Test Arm_Lib
python3 -c "from Arm_Lib import Arm_Device; print('OK')"

# Test model
python3 -c "from ultralytics import YOLO; m=YOLO('models/fine-tunedmodel.pt'); print(m.names)"
```

### Backup

```bash
# Backup positions
cp config/positions.json config/positions.json.backup

# Backup entire config
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# Restore positions
cp config/positions.json.backup config/positions.json
```

## File Locations

| Item                | Path                        |
| ------------------- | --------------------------- |
| Main application    | `main.py`                   |
| Configuration       | `config/settings.py`        |
| Positions           | `config/positions.json`     |
| Model               | `models/fine-tunedmodel.pt` |
| Logs                | `robot.log`                 |
| Virtual environment | `venv/`                     |
| Arm_Lib             | `Arm_Lib/`                  |

## GUI Navigation

```
Main Menu
├── BORROW
│   └── Select item → Confirm → Robot retrieves → Collect from drop zone
│
├── RETURN
│   └── Place item → Wait for detection → Robot stores → Item available
│
├── SETTINGS
│   └── Select position → Adjust sliders → Test → Update → Save all
│
└── TEST
    └── Test borrow/return operations without affecting state
```

## Configuration Quick Edits

### Adjust Detection Threshold

Edit `config/settings.py`:

```python
CONFIDENCE_THRESHOLD = 0.70  # Lower = more permissive
```

### Change Camera ID

```python
CAMERA_ID = 1  # Try 0, 1, 2, etc.
```

### Adjust Speeds

```python
SPEED_NORMAL = 1000  # Higher = slower
SPEED_SLOW = 500
SPEED_FAST = 1500
```

### Change Detection Timing

```python
DETECTION_INTERVAL = 2.0  # Seconds between checks
INITIAL_WAIT_BEFORE_DETECTION = 5.0  # Initial wait
SAFETY_WAIT_AFTER_DETECTION = 3.0  # Safety buffer
```

## Position Calibration

### Recommended Order

1. `home` - Safe resting position
2. `drop_zone` - Item exchange location
3. Storage positions (chair, keyboard, mouse, headphones, mobile_phone, pen)
4. `gripper_open` and `gripper_closed`

### Tips

- Start with moderate joint angles (around 90°)
- Test each position before saving
- Keep movements smooth and collision-free
- Document physical setup with photos

## Item Classes

Default 6 classes:

1. Chair
2. Computer Keyboard
3. Computer Mouse
4. Headphones
5. Mobile Phone
6. Pen

To add new class:

1. Retrain model
2. Add to `ITEM_CLASSES` in `settings.py`
3. Add storage position name to `POSITION_NAMES`
4. Calibrate new storage position

## Keyboard Shortcuts

None implemented by default, but Tkinter supports:

- `Alt+F4` - Close window (with confirmation)
- `Ctrl+C` in terminal - Stop application

## Error Messages

| Error                  | Meaning              | Solution                               |
| ---------------------- | -------------------- | -------------------------------------- |
| `Arm_Lib not found`    | Library not copied   | Copy Arm_Lib to project root           |
| `Permission denied`    | No serial access     | Add user to dialout group, reboot      |
| `Camera not found`     | Camera not connected | Check USB connection, try different ID |
| `Model file not found` | Missing model        | Place model in `models/` directory     |
| `Failed to move`       | Robot error          | Check power, connections, positions    |

## Status Indicators

### Joint Angles Display

Bottom left of GUI shows current joint angles:

```
Joints: [90° 90° 90° 90° 90° 90°]
```

### Status Bar

Bottom right shows current operation:

```
Status: Ready
Status: Moving to storage...
Status: Picking item...
Status: Returning home...
```

### Progress Bars

Appear during operations:

- Borrow screen: Shows borrow progress
- Return screen: Shows return progress
- Settings: None (instant movement)
- Test: Shows test progress

## Logging Levels

In `config/settings.py`:

```python
LOG_LEVEL_CONSOLE = 'INFO'   # What you see in terminal
LOG_LEVEL_FILE = 'DEBUG'     # What goes to robot.log
```

Levels (least to most verbose):

- `CRITICAL` - Only critical errors
- `ERROR` - Errors only
- `WARNING` - Warnings and errors
- `INFO` - General information (default)
- `DEBUG` - Detailed debugging info

## Performance Tuning

### Slow Classification

```python
# Reduce resolution
CAMERA_WIDTH = 224
CAMERA_HEIGHT = 224

# Increase interval
DETECTION_INTERVAL = 2.0
```

### Slow Movements

```python
# Increase speeds (paradoxically, lower numbers)
SPEED_NORMAL = 800
SPEED_FAST = 1200
```

### Memory Issues

```python
# Close other applications
# Reduce camera resolution
# Add swap space (see SETUP.md)
```

## Default Values

| Setting            | Default | Range/Options |
| ------------------ | ------- | ------------- |
| Confidence         | 80%     | 0-100%        |
| Detection interval | 1.0s    | 0.5-5.0s      |
| Initial wait       | 3.0s    | 0-10s         |
| Safety wait        | 2.0s    | 0-5s          |
| Stable detections  | 3       | 1-10          |
| Speed normal       | 1000    | 100-2000      |
| Camera ID          | 0       | 0-10          |
| Camera resolution  | 416x416 | 224-640       |
| Joint range        | 0-180°  | Fixed         |

## Emergency Procedures

### Emergency Stop

1. Click red "EMERGENCY STOP" button (top right)
2. Confirm dialog
3. All movements halt immediately
4. System remains in stopped state
5. Restart application to resume

### Manual Recovery

If robot is in bad position:

1. Click SETTINGS
2. Adjust sliders carefully to safe position
3. Click "Test Position"
4. Once safe, return to home
5. Re-calibrate if needed

### Reset System

```bash
# Stop application
Ctrl+C

# Delete positions (reset to defaults)
rm config/positions.json

# Restart
python main.py

# Re-calibrate all positions
```

## Maintenance

### Regular Tasks

- **Daily:** Check logs for errors
- **Weekly:** Backup positions.json
- **Monthly:** Clean camera lens, check cable connections
- **As needed:** Re-calibrate positions if drift occurs

### Backup Checklist

- [ ] `config/positions.json` - Calibrated positions
- [ ] `config/settings.py` - Custom settings
- [ ] Model file - If retrained
- [ ] Documentation - Setup notes, photos

## Getting Help

1. **Check logs:** `tail -f robot.log`
2. **Read docs:** README.md, SETUP.md, STRUCTURE.md
3. **Test components:** Use TEST screen
4. **Search errors:** Google error messages
5. **Ask for help:** Provide logs and error messages

## Useful Python Commands

```python
# Test imports
python3 -c "import cv2; import numpy; from ultralytics import YOLO; print('OK')"

# Check Arm_Lib
python3 -c "from Arm_Lib import Arm_Device; arm = Arm_Device(); print('Connected')"

# Test camera
python3 << EOF
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f"Camera OK: {ret}, Frame shape: {frame.shape if ret else 'N/A'}")
cap.release()
EOF

# Test model
python3 << EOF
from ultralytics import YOLO
model = YOLO('models/fine-tunedmodel.pt')
print(f"Model classes: {model.names}")
EOF
```

## Directory Quick Access

```bash
# Project root
cd ~/Documents/office-items-loan-robot

# View logs
cd ~/Documents/office-items-loan-robot && tail -f robot.log

# Edit settings
cd ~/Documents/office-items-loan-robot
nano config/settings.py

# View positions
cd ~/Documents/office-items-loan-robot
cat config/positions.json
```

---

**For detailed information, refer to:**

- **Overview & Usage:** README.md
- **Setup Instructions:** SETUP.md
- **Project Structure:** STRUCTURE.md
- **This Guide:** QUICKREF.md
