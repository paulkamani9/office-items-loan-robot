#!/bin/bash

# Quick start script for Office Items Loan Robot
# This script activates the virtual environment and runs the application

echo "======================================"
echo "Office Items Loan Robot - Quick Start"
echo "======================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo ""
    echo "Please run setup first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Check if Arm_Lib exists
if [ ! -d "Arm_Lib" ]; then
    echo "⚠️  WARNING: Arm_Lib not found in project directory"
    echo "Robot control will not work!"
    echo ""
    echo "Please copy Arm_Lib to project root (see SETUP.md)"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if model exists
if [ ! -f "models/fine-tunedmodel.pt" ]; then
    echo "⚠️  WARNING: Model file not found!"
    echo "Expected: models/fine-tunedmodel.pt"
    echo ""
    echo "Vision system will not work!"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✓ Checks passed"
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo "Starting application..."
echo ""
python main.py

# Deactivate on exit
deactivate
