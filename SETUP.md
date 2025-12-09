# Setup Instructions

Complete setup guide for the Office Items Loan Robot system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Arm_Lib Installation](#arm_lib-installation)
3. [Python Environment Setup](#python-environment-setup)
4. [Model File Setup](#model-file-setup)
5. [Permissions Configuration](#permissions-configuration)
6. [First Run](#first-run)
7. [Initial Calibration](#initial-calibration)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

- ✅ Yahboom Dofbot robot arm (assembled and tested)
- ✅ Raspberry Pi 4 (4GB+ RAM recommended)
- ✅ USB webcam (720p or higher)
- ✅ HDMI monitor
- ✅ USB keyboard and mouse
- ✅ Power supply for robot arm
- ✅ USB cable for robot connection
- ✅ Adequate workspace with good lighting

### Software Requirements

- ✅ Raspberry Pi OS (Bullseye or newer)
- ✅ Python 3.8 or higher
- ✅ Yahboom Arm_Lib installed on system
- ✅ Internet connection for package installation

### Before You Start

1. **Test robot arm:** Ensure Yahboom robot works with their example code
2. **Test camera:** Verify camera works: `cheese` or `ffplay /dev/video0`
3. **Update system:**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

---

## Arm_Lib Installation

Arm_Lib is Yahboom's proprietary library and **must be copied** into the project.

### Step 1: Verify Arm_Lib is Installed on System

```bash
# Deactivate any virtual environment first
deactivate

# Check if Arm_Lib is available
python3 -c "import Arm_Lib; print('Arm_Lib found!')"
```

If you get `ModuleNotFoundError`, install Arm_Lib using Yahboom's installation package first.

### Step 2: Find Arm_Lib Location

```bash
# Find where Arm_Lib is installed
python3 -c "import Arm_Lib; print(Arm_Lib.__file__)"
```

**Example output:**

```
/usr/lib/python3/dist-packages/Arm_Lib/__init__.py
```

The directory is: `/usr/lib/python3/dist-packages/Arm_Lib/`

### Step 3: Copy Arm_Lib to Project

```bash
# Navigate to your project
cd ~/Documents/office-items-loan-robot

# Copy entire Arm_Lib folder
# (Adjust source path based on your output from Step 2)
sudo cp -r /usr/lib/python3/dist-packages/Arm_Lib ./

# Fix permissions
sudo chown -R $USER:$USER Arm_Lib/
chmod -R u+rwX Arm_Lib/
```

### Step 4: Verify Copy

Your project structure should now include:

```
office-items-loan-robot/
├── Arm_Lib/
│   ├── __init__.py
│   ├── Arm_Device.py
│   └── (other files)
├── config/
├── gui/
├── modules/
└── ...
```

**Verify it works:**

```bash
# From project root
python3 -c "from Arm_Lib import Arm_Device; print('✓ Arm_Lib accessible')"
```

### Why Copy Arm_Lib?

- Virtual environments can't access system packages by default
- Ensures consistent behavior across environments
- Project becomes self-contained and portable
- Avoids `--system-site-packages` complexity

---

## Python Environment Setup

### Step 1: Install Python Virtual Environment

```bash
# Install venv if not already installed
sudo apt install python3-venv python3-pip -y
```

### Step 2: Create Virtual Environment

```bash
# Navigate to project
cd ~/Documents/office-items-loan-robot

# Create virtual environment
python3 -m venv venv

# You should now see a 'venv' folder
ls -la venv/
```

### Step 3: Activate Virtual Environment

```bash
# Activate
source venv/bin/activate

# Your prompt should change to show (venv)
# Example: (venv) pi@raspberrypi:~/Documents/office-items-loan-robot$
```

### Step 4: Upgrade pip

```bash
# Upgrade pip to latest version
pip install --upgrade pip
```

### Step 5: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

This installs:

- `ultralytics` - YOLOv8 framework
- `opencv-python` - Computer vision
- `numpy` - Numerical operations
- `Pillow` - Image processing
- `pyserial` - Serial communication

**Note:** Installation may take 10-15 minutes on Raspberry Pi.

### Step 6: Verify Installation

```bash
# Test imports
python3 << EOF
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import serial
print("✓ All packages imported successfully")
EOF
```

### Deactivating Virtual Environment

When you're done:

```bash
deactivate
```

To activate again later:

```bash
cd ~/Documents/office-items-loan-robot
source venv/bin/activate
```

---

## Model File Setup

### Step 1: Obtain Model File

You need the fine-tuned YOLOv8 classification model file:

- **Filename:** `fine-tunedmodel.pt`
- **Format:** PyTorch model file
- **Type:** YOLOv8 classification (not detection)
- **Classes:** 6 office items

### Step 2: Place Model in Project

```bash
# Create models directory (should already exist)
mkdir -p ~/Documents/office-items-loan-robot/models

# Copy your model file
cp /path/to/fine-tunedmodel.pt ~/Documents/office-items-loan-robot/models/

# Verify
ls -lh ~/Documents/office-items-loan-robot/models/fine-tunedmodel.pt
```

### Step 3: Test Model Loading

```bash
cd ~/Documents/office-items-loan-robot
source venv/bin/activate

# Test model loading
python3 << EOF
from ultralytics import YOLO
model = YOLO('models/fine-tunedmodel.pt')
print(f"✓ Model loaded successfully")
print(f"  Classes: {model.names}")
EOF
```

**Expected output:**

```
✓ Model loaded successfully
  Classes: {0: 'Chair', 1: 'Computer Keyboard', ...}
```

---

## Permissions Configuration

### Serial Port Permissions

The robot arm communicates via serial port. You need permissions to access it.

```bash
# Add user to dialout group (serial access)
sudo usermod -aG dialout $USER

# Add user to tty group
sudo usermod -aG tty $USER
```

### I2C Permissions (if needed)

If you encounter I2C/SMBus errors:

```bash
# Add user to i2c group
sudo usermod -aG i2c $USER
```

### Camera Permissions

Usually not needed, but if camera access fails:

```bash
# Add user to video group
sudo usermod -aG video $USER
```

### Apply Permissions

**⚠️ IMPORTANT:** Permissions only take effect after reboot or re-login.

```bash
# Verify current groups
groups

# Reboot to apply permissions
sudo reboot
```

After reboot, verify:

```bash
groups
# Should see: dialout tty i2c video (among others)
```

### Test Serial Access

```bash
# List serial devices
ls -l /dev/ttyUSB* /dev/ttyAMA*

# Should show devices without permission errors
```

---

## First Run

### Step 1: Connect Hardware

1. **Power on robot arm**
2. **Connect USB cable** from robot to Raspberry Pi
3. **Connect USB camera** to Raspberry Pi
4. **Verify connections:**

   ```bash
   # Check robot serial port
   ls /dev/ttyUSB*  # or /dev/ttyAMA*

   # Check camera
   ls /dev/video*
   ```

### Step 2: Launch Application

```bash
cd ~/Documents/office-items-loan-robot
source venv/bin/activate
python main.py
```

### Step 3: Check Startup Messages

The application will check:

- ✓ Arm_Lib availability
- ✓ Model file exists
- ✓ Python packages installed
- ✓ Camera accessible
- ✓ Robot connection

**If errors appear:**

- Read error messages carefully
- Check terminal output
- Review `robot.log` file
- See [Troubleshooting](#troubleshooting) section

### Step 4: Understand Initial State

- **All items start as "LOANED OUT"**
- You cannot borrow items until they are returned
- State resets every time you restart the application
- This is intentional - system starts empty

---

## Initial Calibration

**Before using the robot, you MUST calibrate all positions.**

### Step 1: Enter Settings Mode

1. Click **SETTINGS** button on main menu
2. Calibration screen opens

### Step 2: Understand Positions to Calibrate

You need to calibrate **8 positions:**

**Core Positions:**

- `home` - Safe resting position
- `drop_zone` - Where items are placed/picked

**Storage Positions (6 items):**

- `chair_storage`
- `keyboard_storage`
- `mouse_storage`
- `headphones_storage`
- `mobile_phone_storage`
- `pen_storage`

**Gripper Positions:**

- `gripper_open` - Gripper fully open
- `gripper_closed` - Gripper holding item

### Step 3: Calibration Process (for each position)

1. **Select position** from dropdown (e.g., "home")

2. **Adjust sliders:**

   - 6 sliders control joint angles (0-180°)
   - Move sliders to position robot
   - Watch robot move in real-time

3. **Test position:**

   - Click "Test Position" button
   - Confirm movement in dialog
   - Robot moves to current slider values
   - Verify position is correct

4. **Fine-tune:**

   - Adjust sliders as needed
   - Test again
   - Repeat until perfect

5. **Update position:**

   - Click "Update Position" button
   - Position saved to memory (not yet to file)

6. **Repeat** for all 8 positions

7. **Save all:**
   - Click "Save All Positions" button
   - Writes `config/positions.json`
   - Positions persisted to disk

### Step 4: Recommended Calibration Order

1. **Start with `home`:**

   - Safe central position
   - All joints at moderate angles
   - Robot upright and stable

2. **Calibrate `drop_zone`:**

   - Where camera can see items
   - Accessible for pick/place
   - Safe for users to place items

3. **Calibrate storage positions:**

   - Arrange in accessible pattern
   - Ensure no collisions between positions
   - Test pick/place at each location

4. **Calibrate gripper:**
   - `gripper_open`: Wide enough for items
   - `gripper_closed`: Secure grip without crushing

### Step 5: Test Calibration

After calibrating:

1. Return to main menu
2. Click **TEST** button
3. Test borrow/return for each item
4. Verify robot can reach all positions
5. Adjust and re-save if needed

### Calibration Tips

✅ **Safety First:**

- Keep clear of robot workspace
- Use emergency stop if needed
- Start with small movements

✅ **Methodology:**

- Calibrate with actual items in place
- Test gripper with real items
- Ensure camera has clear view of drop zone

✅ **Optimization:**

- Minimize movement distance
- Avoid extreme joint angles
- Ensure smooth transitions

✅ **Documentation:**

- Take photos of physical setup
- Note any special configurations
- Keep backup of `positions.json`

---

## Troubleshooting

### Arm_Lib Import Fails

**Error:**

```
✗ Arm_Lib not found: No module named 'Arm_Lib'
```

**Solutions:**

1. **Verify Arm_Lib is copied:**

   ```bash
   ls -la Arm_Lib/
   ```

2. **Check Arm_Lib contents:**

   ```bash
   ls Arm_Lib/__init__.py
   ls Arm_Lib/Arm_Device.py
   ```

3. **Re-copy if needed:**

   ```bash
   sudo cp -r /usr/lib/python3/dist-packages/Arm_Lib ./
   sudo chown -R $USER:$USER Arm_Lib/
   ```

4. **Verify Python can find it:**
   ```bash
   python3 -c "from Arm_Lib import Arm_Device"
   ```

### Camera Not Found

**Error:**

```
✗ Failed to open camera
```

**Solutions:**

1. **Check camera is connected:**

   ```bash
   ls /dev/video*
   ```

   Should show `/dev/video0` or similar

2. **Test camera directly:**

   ```bash
   # Install cheese if needed
   sudo apt install cheese
   cheese
   ```

3. **Check camera permissions:**

   ```bash
   ls -l /dev/video0
   groups | grep video
   ```

4. **Try different camera ID:**
   Edit `config/settings.py`:

   ```python
   CAMERA_ID = 0  # Try 1, 2, etc.
   ```

5. **Check if camera is in use:**
   ```bash
   sudo fuser /dev/video0
   # If shows a PID, another process is using camera
   ```

### Model Not Loading

**Error:**

```
✗ Model file not found
```

**Solutions:**

1. **Verify model exists:**

   ```bash
   ls -lh models/fine-tunedmodel.pt
   ```

2. **Check file permissions:**

   ```bash
   chmod 644 models/fine-tunedmodel.pt
   ```

3. **Test model manually:**
   ```bash
   python3 << EOF
   from ultralytics import YOLO
   model = YOLO('models/fine-tunedmodel.pt')
   EOF
   ```

### Serial Permission Denied

**Error:**

```
Permission denied: '/dev/ttyUSB0'
```

**Solutions:**

1. **Add user to dialout group:**

   ```bash
   sudo usermod -aG dialout $USER
   sudo reboot
   ```

2. **Verify groups:**

   ```bash
   groups | grep dialout
   ```

3. **Check device permissions:**

   ```bash
   ls -l /dev/ttyUSB0
   # Should show: crw-rw---- 1 root dialout
   ```

4. **Temporary fix (testing only):**
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   ```

### Robot Not Moving

**Checklist:**

- [ ] Robot powered on
- [ ] USB cable connected
- [ ] User in `dialout` group
- [ ] Serial port accessible (`ls /dev/ttyUSB*`)
- [ ] Arm_Lib initialized (check logs)
- [ ] No error messages in terminal

**Debug steps:**

1. **Check logs:**

   ```bash
   tail -n 50 robot.log
   ```

2. **Test with Yahboom examples:**
   Verify robot works with official Yahboom code

3. **Check serial connection:**
   ```bash
   python3 << EOF
   from Arm_Lib import Arm_Device
   arm = Arm_Device()
   print("✓ Arm connected")
   EOF
   ```

### Low Frame Rate / Slow Performance

**Solutions:**

1. **Reduce camera resolution:**
   Edit `config/settings.py`:

   ```python
   CAMERA_WIDTH = 320
   CAMERA_HEIGHT = 320
   ```

2. **Increase detection interval:**

   ```python
   DETECTION_INTERVAL = 2.0  # Slower, less CPU
   ```

3. **Close other applications:**
   Free up CPU and memory

4. **Use MJPEG format:**
   Already configured in `vision_system.py`

### Classification Not Working

**Symptoms:**

- No items detected
- Wrong items detected
- Low confidence scores

**Solutions:**

1. **Check lighting:**

   - Ensure good lighting on drop zone
   - Avoid shadows and glare
   - Use consistent lighting

2. **Verify model classes:**

   ```python
   from ultralytics import YOLO
   model = YOLO('models/fine-tunedmodel.pt')
   print(model.names)
   ```

   Should match items in `ITEM_CLASSES`

3. **Adjust confidence threshold:**
   Edit `config/settings.py`:

   ```python
   CONFIDENCE_THRESHOLD = 0.70  # Lower if needed
   ```

4. **Test camera view:**
   Use TEST screen to see what camera sees

5. **Check item placement:**
   - Place item clearly in drop zone
   - Ensure item is upright
   - Remove other objects from view

### Out of Memory Errors

**Solutions:**

1. **Close other applications**

2. **Reduce camera resolution**

3. **Disable camera preview in return mode** (edit `return_screen.py`)

4. **Add swap space:**
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

---

## Advanced Configuration

### Custom Movement Speeds

Edit `config/settings.py`:

```python
SPEED_NORMAL = 1000  # Slower = higher number
SPEED_SLOW = 500
SPEED_FAST = 1500
```

### Custom Detection Parameters

```python
# How long to wait before starting detection
INITIAL_WAIT_BEFORE_DETECTION = 3.0

# How often to classify (seconds)
DETECTION_INTERVAL = 1.0

# Safety buffer after detection
SAFETY_WAIT_AFTER_DETECTION = 2.0

# Required consecutive detections
STABLE_DETECTION_COUNT = 3
```

### Custom GUI Colors

```python
THEME_COLOR_PRIMARY = '#2C3E50'
THEME_COLOR_ACCENT = '#3498DB'
THEME_COLOR_SUCCESS = '#27AE60'
THEME_COLOR_DANGER = '#E74C3C'
```

### Logging Configuration

```python
LOG_FILE = 'robot.log'
LOG_LEVEL_CONSOLE = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_LEVEL_FILE = 'DEBUG'
```

---

## Backup and Recovery

### Backup Important Files

```bash
# Backup positions
cp config/positions.json config/positions.json.backup

# Backup entire config
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# Backup model (if retrained)
cp models/fine-tunedmodel.pt models/fine-tunedmodel.pt.backup
```

### Restore from Backup

```bash
# Restore positions
cp config/positions.json.backup config/positions.json

# Restore config
tar -xzf config_backup_YYYYMMDD.tar.gz
```

---

## Getting Help

1. **Check logs:**

   ```bash
   tail -f robot.log
   ```

2. **Enable debug mode:**
   Edit `config/settings.py`:

   ```python
   LOG_LEVEL_CONSOLE = 'DEBUG'
   ```

3. **Test individual components:**

   - Camera: TEST screen → Test Classification
   - Robot: TEST screen → Test operations
   - Positions: SETTINGS screen → Test Position

4. **Common issues:**

   - See [Troubleshooting](#troubleshooting) section above
   - Check README.md

5. **Ask for help:**
   - Provide error messages
   - Include relevant logs
   - Describe what you tried

---

## Next Steps

After successful setup:

1. ✅ **Familiarize with interface:** Explore all screens
2. ✅ **Practice calibration:** Get comfortable with sliders
3. ✅ **Test thoroughly:** Use TEST mode extensively
4. ✅ **Document your setup:** Take notes and photos
5. ✅ **Create workflow:** Establish operating procedures
6. ✅ **Train users:** Show others how to use system

---

**Setup complete! Your Office Items Loan Robot is ready to use. 🎉**
