#!/bin/bash
# Installation script for lerobot_robot_roarm

echo "====================================="
echo "Roarm LeRobot Integration Installer"
echo "====================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if in virtual environment (recommended)
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo ""
    echo "⚠️  Warning: Not in a virtual environment"
    echo "It's recommended to use a virtual environment:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
echo ""

echo "1. Installing LeRobot..."
pip install lerobot || { echo "Failed to install lerobot"; exit 1; }

echo ""
echo "2. Installing Roarm SDK..."
pip install roarm-sdk || { echo "Failed to install roarm-sdk"; exit 1; }

echo ""
echo "3. Installing additional dependencies..."
pip install numpy>=1.24.0 || { echo "Failed to install numpy"; exit 1; }

# Install this package
echo ""
echo "4. Installing lerobot_robot_roarm..."
pip install -e . || { echo "Failed to install lerobot_robot_roarm"; exit 1; }

# Verify installation
echo ""
echo "====================================="
echo "Verifying installation..."
echo "====================================="
echo ""

python3 << 'EOF'
import sys

try:
    import lerobot
    print("✓ LeRobot installed")
except ImportError:
    print("✗ LeRobot not found")
    sys.exit(1)

try:
    import roarm_sdk
    print("✓ Roarm SDK installed")
except ImportError:
    print("✗ Roarm SDK not found")
    sys.exit(1)

try:
    from lerobot_robot_roarm import RoarmConfig, Roarm
    print("✓ lerobot_robot_roarm installed")
except ImportError as e:
    print(f"✗ lerobot_robot_roarm not found: {e}")
    sys.exit(1)

print("")
print("✓ All packages installed successfully!")
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "====================================="
    echo "Installation Complete!"
    echo "====================================="
    echo ""
    echo "Next steps:"
    echo "1. Connect your Roarm robot"
    echo "2. Check device: ls /dev/ttyUSB*"
    echo "3. Set permissions: sudo chmod 666 /dev/ttyUSB0"
    echo "4. Run example: python examples/basic_control.py"
    echo ""
    echo "See QUICKSTART.md for detailed guide"
    echo ""
else
    echo ""
    echo "✗ Installation verification failed"
    exit 1
fi
