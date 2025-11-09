# LeRobot Roarm Integration

This package provides integration for Roarm robot arms with the [HuggingFace LeRobot](https://github.com/huggingface/lerobot) framework. It allows you to use Roarm robots for data collection, teleoperation, policy training, and inference.

## Features

- ✅ Full LeRobot Robot interface implementation
- ✅ Support for both serial (USB) and WiFi connections
- ✅ Roarm-to-Roarm teleoperation (leader-follower)
- ✅ SO-101 leader arm support with automatic percentage scaling
- ✅ Joint position control with per-joint limits
- ✅ Gripper control
- ✅ Camera integration
- ✅ Calibration support
- ✅ Processing pipelines for action/observation normalization
- ✅ Proper logging system (no debug spam)
- ✅ Safety constraints (velocity limiting, joint limits)
- ✅ Compatible with LeRobot's data collection and training tools
- ✅ VSCode debug configuration included

## Installation

### Prerequisites

1. Install LeRobot (follow [LeRobot installation guide](https://huggingface.co/docs/lerobot/installation))
2. Install the Roarm SDK:
   ```bash
   pip install roarm-sdk
   ```

### Install this package

#### From GitHub (recommended):
```bash
pip install git+https://github.com/koenvanwijk/roarm.git
```

#### From source (for development):
```bash
git clone https://github.com/koenvanwijk/roarm.git
cd roarm
pip install -e .
```

#### From PyPI (once published):
```bash
pip install lerobot-robot-roarm
```

## Quick Start

### 1. Basic Robot Control

```python
from lerobot_robot_roarm import RoarmConfig, Roarm

# Create configuration
config = RoarmConfig(
    roarm_type="roarm_m3",
    port="/dev/ttyUSB0",  # or host="192.168.1.100" for WiFi
    baudrate=115200,
)

# Initialize and connect to robot
robot = Roarm(config)
robot.connect()

# Get observation
obs = robot.get_observation()
print(f"Joint positions: {obs}")

# Send action
action = {
    "joint_1.pos": 0.0,
    "joint_2.pos": 0.5,
    "joint_3.pos": 1.0,
    "joint_4.pos": -0.5,
    "joint_5.pos": 0.0,
    "joint_6.pos": 0.0,
    "gripper.pos": 0.5,
}
robot.send_action(action)

# Disconnect
robot.disconnect()
```

### 2. Teleoperation

#### Roarm-to-Roarm (Serial):
```bash
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm \
  --robot.id follower \
  --robot.roarm_type roarm_m3 \
  --robot.port /dev/ttyUSB1 \
  --robot.cameras '{}' \
  --teleop.type lerobot_robot_roarm \
  --teleop.id leader \
  --teleop.roarm_type roarm_m3 \
  --teleop.port /dev/ttyUSB0 \
  --fps 10
```

#### Roarm-to-Roarm (WiFi):
```bash
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm \
  --robot.id follower \
  --robot.roarm_type roarm_m3 \
  --robot.host 192.168.86.55 \
  --robot.cameras '{}' \
  --teleop.type lerobot_robot_roarm \
  --teleop.id leader \
  --teleop.roarm_type roarm_m3 \
  --teleop.host 192.168.86.43 \
  --fps 10
```

#### SO-101 to Roarm:
```bash
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm \
  --robot.id follower \
  --robot.roarm_type roarm_m3 \
  --robot.port /dev/ttyUSB1 \
  --robot.cameras '{}' \
  --teleop.type so101_leader \
  --teleop.id leader \
  --teleop.port /dev/ttyACM0 \
  --fps 10
```

**Note:** SO-101 values (-100% to +100%) are automatically scaled to the full range of each Roarm joint.

### 3. Recording Demonstrations

```bash
# Record demonstrations using LeRobot CLI
lerobot-record \
  --robot.type=roarm \
  --robot.roarm_type=roarm_m3 \
  --robot.port=/dev/ttyUSB0 \
  --repo-id=my-username/roarm_demos \
  --num-episodes=10
```

### 3. Training a Policy

```bash
# Train a policy on recorded data
python lerobot/scripts/train.py \
  --dataset-repo-id=my-username/roarm_demos \
  --policy=act \
  --output-dir=outputs/roarm_act
```

### 4. Running Inference

```bash
# Run the trained policy on the robot
python lerobot/scripts/control_robot.py \
  --robot.type=roarm \
  --robot.roarm_type=roarm_m3 \
  --robot.port=/dev/ttyUSB0 \
  --policy-checkpoint=outputs/roarm_act/checkpoint.pth
```

## Configuration

### Robot Configuration

The `RoarmConfig` class supports the following parameters:

```python
@dataclass
class RoarmConfig:
    # Robot model
    roarm_type: str = "roarm_m3"  # roarm_m1, roarm_m2, roarm_m3, etc.
    
    # Connection (choose one)
    port: str | None = None  # Serial: "/dev/ttyUSB0"
    host: str | None = None  # WiFi: "192.168.1.100"
    baudrate: int = 115200
    
    # Joint configuration
    joint_names: list[str] = ["joint_1", ..., "joint_6"]
    
    # Control parameters
    default_speed: int = 1000
    default_acc: int = 50
    
    # Gripper
    has_gripper: bool = True
    gripper_name: str = "gripper"
    
    # Cameras
    cameras: dict[str, CameraConfig] = {...}
    
    # Safety limits
    max_joint_velocity: float = 3.0  # rad/s
    max_gripper_velocity: float = 2.0  # rad/s
```

### Using Processors

Processors help transform actions and observations:

```python
from lerobot_robot_roarm import (
    create_roarm_action_processor,
    create_roarm_observation_processor
)

# Create processors
action_processor = create_roarm_action_processor(
    joint_names=robot.config.joint_names,
    normalize=True,
    apply_safety=True,
)

obs_processor = create_roarm_observation_processor(
    joint_names=robot.config.joint_names,
    normalize=True,
)

# Use in your control loop
processed_action = action_processor.forward(raw_action)
robot.send_action(processed_action)
```

## Hardware Setup

### Serial Connection
1. Connect the Roarm robot to your computer via USB
2. Find the device port: `ls /dev/ttyUSB*`
3. Grant permissions: `sudo chmod 666 /dev/ttyUSB0`

### WiFi Connection
1. Configure the robot's WiFi settings (see Roarm SDK documentation)
2. Connect to the same network as your robot
3. Find the robot's IP address
4. Use the `host` parameter in your configuration

## Examples

See the `examples/` directory for complete examples:

- `basic_control.py` - Basic robot control
- `record_demos.py` - Recording demonstrations
- `teleoperation.py` - Teleoperation setup
- `train_policy.py` - Training a policy
- `run_policy.py` - Running inference

## Troubleshooting

### Connection Issues

**Serial connection fails:**
- Check USB cable connection
- Verify device permissions: `sudo chmod 666 /dev/ttyUSB0`
- Try different USB ports
- Check if another process is using the port

**WiFi connection fails:**
- Verify robot and computer are on same network
- Ping the robot: `ping <robot_ip>`
- Check firewall settings
- Ensure robot WiFi is properly configured

### Calibration Issues

If calibration fails:
1. Make sure robot has enough space to move
2. Manually move robot to home position before calibration
3. Check for mechanical obstructions
4. Verify power supply is adequate

### Teleoperation Issues

**Follower not moving:**
- Check that leader arm is properly connected
- Verify joint limits are configured correctly
- Check logs for warnings about failed commands
- For SO-101: ensure values are being scaled correctly (-100% to +100%)

**Movements are inverted or wrong:**
- Verify joint naming matches between leader and follower
- Check joint_limits_deg configuration in config_roarm.py
- Review percentage-to-degree scaling logic

### Performance Issues

If movements are jerky or slow:
- Increase `default_speed` in config
- Reduce `max_ee_step_m` for smoother trajectories
- Check USB cable quality (for serial)
- Verify network latency (for WiFi) - WiFi typically runs at ~3 Hz vs 7-10 Hz for serial
- Lower `fps` parameter if experiencing lag

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Citation

If you use this package in your research, please cite:

```bibtex
@software{lerobot_robot_roarm,
  title={LeRobot Roarm Integration},
  author={Roarm Integration Team},
  year={2024},
  url={https://github.com/yourusername/lerobot_robot_roarm}
}
```

## Acknowledgments

- [HuggingFace LeRobot](https://github.com/huggingface/lerobot) for the excellent robotics framework
- Roarm team for the robot hardware and SDK
- The robotics community for inspiration and support

## Support

- 📖 Documentation: See this README and code examples
- 💬 Issues: [GitHub Issues](https://github.com/yourusername/lerobot_robot_roarm/issues)
- 🤗 LeRobot Discord: [Join the community](https://discord.gg/s3KuuzsPFb)
