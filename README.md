# Office Items Loan Robot

A sophisticated office items loan management system using a Yahboom Dofbot (6 DOF robot arm) with computer vision for automated item handling.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%204-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

This system manages lending and returning of 6 office items through an intuitive GUI interface with visual calibration capabilities. The robot arm automatically retrieves items from storage when borrowed and stores them when returned, using YOLOv8 classification for item identification.

### Managed Items

- Chair
- Computer Keyboard
- Computer Mouse
- Headphones
- Mobile Phone
- Pen

## Features

✨ **Automated Item Handling**

- Borrow items with automatic retrieval from storage
- Return items with automatic visual identification
- Real-time camera feed during return operations

🎯 **Computer Vision**

- YOLOv8 classification model for item recognition
- 80% confidence threshold for reliable detection
- Continuous detection with stability checking

🎨 **Intuitive GUI**

- Modern Tkinter-based interface
- Visual position calibration with sliders
- Real-time joint angle display
- Progress indicators for all operations

🛠️ **Advanced Features**

- Position management with JSON persistence
- State tracking (available/loaned items)
- Test mode for debugging operations
- Emergency stop capability
- Comprehensive logging system

## System Requirements

### Hardware

- **Robot:** Yahboom Dofbot (6 DOF robotic arm)
- **Computer:** Raspberry Pi 4 (CPU only)
- **Camera:** USB webcam (looking down at drop zone)
- **Display:** HDMI monitor
- **Input:** Mouse and keyboard

### Software

- **OS:** Raspberry Pi OS (Debian-based)
- **Python:** 3.8 or higher
- **Libraries:** See `requirements.txt`
- **Model:** `fine-tunedmodel.pt` (YOLOv8 classification model)

## Quick Start

### 1. Clone/Copy Project

```bash
cd ~/Documents
git clone <repository-url> office-items-loan-robot
cd office-items-loan-robot
```

### 2. Copy Arm_Lib

```bash
# Find Arm_Lib location
python3 -c "import Arm_Lib; print(Arm_Lib.__file__)"

# Copy to project root (adjust path as needed)
cp -r /usr/lib/python3/dist-packages/Arm_Lib ./
```

### 3. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Add Model File

```bash
# Place your fine-tuned model
cp /path/to/fine-tunedmodel.pt models/
```

### 5. Setup Permissions

```bash
# Add user to required groups
sudo usermod -aG dialout $USER
sudo usermod -aG tty $USER
sudo usermod -aG i2c $USER

# Reboot for permissions to take effect
sudo reboot
```

### 6. Run Application

```bash
source venv/bin/activate
python main.py
```

## Usage Guide

### First Time Setup

1. **Launch application** - System starts with all items marked as "loaned out"
2. **Go to SETTINGS** - Calibrate all 8 positions using sliders
3. **Test each position** - Use "Test Position" button to verify
4. **Save positions** - Click "Save All Positions" to persist configuration
5. **Return to main menu** - Ready to use!

### Borrowing Items

1. Click **BORROW** from main menu
2. Select an **available item** from the grid
3. Click **BORROW** button
4. Robot retrieves item from storage
5. Collect item from drop zone
6. Item marked as "loaned out"

### Returning Items

1. Click **RETURN** from main menu
2. Place item in drop zone
3. Wait for detection (3-second initial wait)
4. System classifies item continuously
5. When valid item detected:
   - 2-second safety wait
   - Robot picks and stores item
   - Item marked as "available"

### Calibration

1. Click **SETTINGS** from main menu
2. Select position from dropdown
3. Adjust sliders to move robot
4. Click **Test Position** to verify
5. Fine-tune with sliders
6. Click **Update Position** when satisfied
7. Repeat for all 8 positions
8. Click **Save All Positions** to persist

### Testing

1. Click **TEST** from main menu
2. Test individual borrow/return operations
3. Test camera classification
4. View real-time detection results
5. Does NOT affect system state

## Project Structure

```
office-items-loan-robot/
│
├── Arm_Lib/                    # Yahboom arm control library (copied)
│
├── models/
│   └── fine-tunedmodel.pt      # YOLOv8 classification model
│
├── config/
│   ├── positions.json          # Calibrated robot positions
│   └── settings.py             # System constants
│
├── modules/
│   ├── vision_system.py        # Camera & YOLO classification
│   ├── robot_controller.py     # Robot movement & control
│   ├── state_manager.py        # Item availability tracking
│   └── position_manager.py     # Position storage & loading
│
├── gui/
│   ├── main_window.py          # Main application window
│   ├── borrow_screen.py        # Borrow interface
│   ├── return_screen.py        # Return interface with camera
│   ├── calibration_screen.py   # Position calibration
│   └── test_screen.py          # Test operations
│
├── utils/
│   └── logger.py               # Logging utilities
│
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── SETUP.md                    # Detailed setup instructions
```

## Configuration

### System Settings

Edit `config/settings.py` to customize:

- Detection confidence threshold (default: 80%)
- Detection interval (default: 1 second)
- Movement speeds
- Camera resolution
- GUI colors and sizes

### Positions

Positions are stored in `config/positions.json`:

- 8 named positions (home, drop_zone, 6 storage positions)
- 2 gripper positions (open, closed)
- Edit via GUI calibration screen or manually edit JSON

## Troubleshooting

### Arm_Lib Import Errors

```
✗ Arm_Lib not found
```

**Solution:** Copy Arm_Lib folder to project root (see SETUP.md)

### Camera Not Found

```
✗ Failed to open camera
```

**Solution:**

- Check camera is connected: `ls /dev/video*`
- Check camera ID in settings.py (default: 0)
- Test with: `ffplay /dev/video0`

### Model Input Size Errors

```
mp.nra error or tensor size mismatch
```

**Solution:** System auto-detects model input size, but you can manually set it in `vision_system.py` if needed

### Permission Denied

```
Permission denied: /dev/ttyUSB0
```

**Solution:**

- Add user to dialout group: `sudo usermod -aG dialout $USER`
- Reboot system
- Verify: `groups | grep dialout`

### Robot Not Moving

**Check:**

1. Robot is powered on
2. USB cable connected
3. User in dialout/tty groups
4. Arm_Lib initialized correctly (check logs)

## System Behavior

### Initial State

- All items start as **LOANED OUT**
- Items become available after being returned
- No persistence - state resets on restart

### Detection Logic

- 3-second initial wait before detection starts
- Continuous classification every 1 second
- Requires 3 consecutive stable detections
- 2-second safety wait after detection
- Only accepts items in configured class list

### Safety Features

- Emergency stop button (stops all movement)
- Position validation before movement
- Movement timeouts
- Error recovery (returns to home)
- Comprehensive logging

## Development

### Running in Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run with debug output
python main.py

# Check logs
tail -f robot.log
```

### Testing

Use the TEST screen to:

- Test individual operations without affecting state
- Verify calibrated positions
- Debug camera and classification
- View real-time detection results

### Adding New Items

1. Retrain YOLO model with new item class
2. Add class name to `ITEM_CLASSES` in `config/settings.py`
3. Add storage position to `POSITION_NAMES`
4. Calibrate new storage position
5. Update GUI if needed (currently shows 6 items in 3x2 grid)

## Performance

### Expected Timing

- Borrow operation: < 20 seconds
- Return operation: < 25 seconds (including detection)
- Classification: 1-2 seconds per frame
- GUI responsiveness: < 100ms

### Optimization Tips

- Use MJPEG camera format for better performance
- Adjust detection interval if needed
- Optimize robot movement speeds
- Consider reducing camera resolution if classification is slow

## Limitations

- **No Persistence:** State resets on each startup (intentional)
- **Single Item Handling:** One item at a time
- **Fixed Drop Zone:** One physical location for all operations
- **6 Item Classes:** Model trained for specific items only
- **Manual Calibration:** Positions must be calibrated via GUI
- **CPU Only:** No GPU acceleration on Raspberry Pi 4

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Authors

- Development Team: PDE3820 Project
- Institution: [Your Institution]
- Course: [Course Code]

## Acknowledgments

- Yahboom for Dofbot hardware and Arm_Lib
- Ultralytics for YOLOv8
- OpenCV community
- Python community

## Support

For issues, questions, or suggestions:

- Check `SETUP.md` for detailed setup instructions
- Review logs in `robot.log`
- Check troubleshooting section above
- Open an issue on the repository

## Version History

**v1.0.0** (December 2025)

- Initial release
- 6 item classes supported
- Full borrow/return functionality
- Visual calibration interface
- Test mode for debugging
- Comprehensive logging

---

**Made with ❤️ for automated office item management**
