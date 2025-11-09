# Roarm LeRobot Integration - Project Structure

This document provides an overview of the complete project structure.

## Directory Structure

```
roarm/
├── lerobot_robot_roarm/          # Main package directory
│   ├── __init__.py               # Package initialization, exports main classes
│   ├── config_roarm.py           # RoarmConfig class (robot configuration)
│   ├── config_roarm_teleoperator.py  # RoarmTeleoperatorConfig class
│   ├── roarm.py                  # Roarm class (main Robot implementation)
│   ├── roarm_teleoperator.py     # RoarmTeleoperator class (leader arm)
│   └── processors.py             # Processor pipelines for actions/observations
│
├── examples/                      # Example scripts
│   ├── README.md                 # Examples documentation
│   ├── basic_control.py          # Basic robot control example
│   ├── teleoperation.py          # Leader-follower teleoperation
│   ├── record_demos.py           # Recording demonstrations
│   ├── train_policy.py           # Training policies
│   └── run_policy.py             # Running inference
│
├── test/                          # Test scripts
│   ├── test_connection.py        # Connection test
│   └── test_two_robots.py        # Two-robot test
│
├── .vscode/                       # VSCode configuration
│   └── launch.json               # Debug configuration for teleoperation
│
├── README.md                      # Main documentation
├── QUICKSTART.md                  # Quick start guide
├── CHANGELOG.md                   # Version history and changes
├── PROJECT_STRUCTURE.md           # This file - project structure overview
├── SUMMARY.md                     # Project summary
├── INTEGRATION_COMPLETE.md        # Integration completion notes
├── LICENSE                        # Apache 2.0 license
├── pyproject.toml                 # Package configuration and dependencies
├── MANIFEST.in                    # Package manifest for distribution
├── install.sh                     # Installation script
└── .gitignore                     # Git ignore patterns
```

## Core Components

### 1. RoarmConfig (`config_roarm.py`)

Configuration class for Roarm robot with:
- Robot type selection (roarm_m1, roarm_m2, roarm_m3, etc.)
- Connection options (serial or WiFi)
- Joint and gripper configuration
- Camera setup
- Safety limits and control parameters

**Key Features:**
- Registered with LeRobot's config system using `@RobotConfig.register_subclass("roarm")`
- Follows naming convention: `RoarmConfig` / `Roarm`
- Validates configuration in `__post_init__`

### 2. Roarm Robot Class (`roarm.py`)

Main robot implementation with full LeRobot Robot interface:

**Required Properties:**
- `observation_features`: Dict describing sensor outputs (joints, gripper, cameras)
- `action_features`: Dict describing action inputs (joint targets, gripper)
- `is_connected`: Connection status
- `is_calibrated`: Calibration status

**Required Methods:**
- `connect()`: Establish connection, run calibration if needed
- `disconnect()`: Gracefully disconnect and release resources
- `calibrate()`: Perform robot calibration
- `configure()`: Set up robot parameters
- `get_observation()`: Read current state (joints, gripper, cameras)
- `send_action()`: Send commands to robot (auto-detects radians vs percentages)

**Key Features:**
- Supports both serial and WiFi connections
- Automatic angle conversion (degrees ↔ radians)
- Auto-detection of input format (radians vs percentages from SO-101)
- Percentage-to-degree scaling for SO-101 leader (-100% to +100% → full joint range)
- Per-joint limit enforcement with asymmetric ranges
- Proper logging system (no debug spam)
- Safety clamping for joint positions
- Camera integration
- Torque control for teleoperation

### 3. RoarmTeleoperator Class (`roarm_teleoperator.py`)

Leader arm implementation for teleoperation:

**Key Features:**
- Disables torque for manual movement
- Reads joint positions from leader arm
- Supports both Roarm-to-Roarm and SO-101-to-Roarm teleoperation
- Proper logging of leader positions
- Automatic re-enabling of torque on disconnect

### 4. Processors (`processors.py`)

Processing pipelines for action/observation transformations:

**Processor Steps:**
- `RoarmJointNormalizer`: Normalize joint positions to standard ranges
- `RoarmGripperNormalizer`: Normalize gripper positions
- `RoarmActionSafety`: Apply velocity limits and safety constraints

**Helper Functions:**
- `create_roarm_action_processor()`: Create standard action pipeline
- `create_roarm_observation_processor()`: Create standard observation pipeline

**Key Features:**
- Forward/inverse transformations
- Configurable normalization ranges
- Velocity limiting for safety
- Modular pipeline composition

## Package Conventions

Following LeRobot's plugin system:

### 1. Package Naming
- Package name: `lerobot_robot_roarm`
- Follows required prefix: `lerobot_robot_*`

### 2. Class Naming
- Config class: `RoarmConfig` (ends with `Config`)
- Robot class: `Roarm` (matches config without `Config` suffix)

### 3. File Structure
- Config in: `config_roarm.py`
- Robot in: `roarm.py`
- Both exposed in: `__init__.py`

### 4. Registration
- Config registered with decorator: `@RobotConfig.register_subclass("roarm")`
- Robot has: `config_class = RoarmConfig` and `name = "roarm"`

## Installation Methods

### Development (Editable)
```bash
cd lerobot_robot_roarm
pip install -e .
```

### From Source
```bash
pip install lerobot_robot_roarm/
```

### From PyPI (when published)
```bash
pip install lerobot_robot_roarm
```

## Usage Patterns

### 1. Direct Python Usage
```python
from lerobot_robot_roarm import RoarmConfig, Roarm

config = RoarmConfig(roarm_type="roarm_m3", port="/dev/ttyUSB0")
robot = Roarm(config)
robot.connect()
# ... use robot ...
robot.disconnect()
```

### 2. LeRobot CLI (Auto-discovered)
```bash
lerobot-record --robot.type=roarm --robot.port=/dev/ttyUSB0 ...
```

### 3. With Processors
```python
from lerobot_robot_roarm import (
    Roarm, RoarmConfig,
    create_roarm_action_processor
)

robot = Roarm(config)
processor = create_roarm_action_processor(robot.config.joint_names)
# ... use processor in pipeline ...
```

## Dependencies

**Required:**
- `lerobot>=2.0.0` - Core LeRobot framework
- `numpy>=1.24.0` - Numerical operations
- `roarm-sdk>=0.1.0` - Roarm hardware SDK

**Development:**
- `pytest>=7.0` - Testing
- `black>=23.0` - Code formatting
- `isort>=5.12` - Import sorting
- `flake8>=6.0` - Linting

## Features Implemented

✅ **Core Robot Interface**
- Full Robot abstract class implementation
- Connection management (serial & WiFi)
- Observation reading (joints, gripper, cameras)
- Action sending (joints, gripper)
- Calibration support
- Configuration management

✅ **Processors**
- Joint/gripper normalization
- Safety constraints (velocity limiting)
- Pipeline composition
- Forward/inverse transformations

✅ **Integration**
- Auto-discovery via package naming
- LeRobot CLI compatibility
- Configuration registration
- Example scripts

✅ **Documentation**
- Comprehensive README
- Quick start guide
- API documentation
- Example documentation

✅ **Package Distribution**
- pyproject.toml setup
- Proper package structure
- License (Apache 2.0)
- Manifest for distribution

## Next Steps

### For Users:
1. Install the package
2. Follow QUICKSTART.md
3. Run examples
4. Record demonstrations
5. Train and deploy policies

### For Developers:
1. Add unit tests (`tests/`)
2. Add CI/CD pipeline (GitHub Actions)
3. Implement kinematics (forward/inverse)
4. Add end-effector control
5. Create teleoperation device class
6. Add more processor steps
7. Publish to PyPI

## Support and Resources

- **Documentation**: README.md, QUICKSTART.md, examples/README.md
- **LeRobot Docs**: https://huggingface.co/docs/lerobot
- **Examples**: See `examples/` directory
- **Issues**: GitHub issues (when repository created)
- **Community**: LeRobot Discord

## Version History

- **0.1.0** - Initial release
  - Basic robot interface
  - Serial and WiFi support
  - Processor pipelines
  - Example scripts
  - Documentation

---

Created: 2024
License: Apache 2.0
Framework: HuggingFace LeRobot
