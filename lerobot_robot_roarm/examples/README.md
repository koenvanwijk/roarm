# Roarm LeRobot Examples

This directory contains example scripts demonstrating how to use the Roarm robot with LeRobot.

## Examples

### 1. Basic Control (`basic_control.py`)

Demonstrates basic robot control:
- Connecting to the robot
- Reading observations (joint positions)
- Sending actions (joint commands)
- Moving the gripper

**Run:**
```bash
python examples/basic_control.py
```

### 2. Teleoperation (`teleoperation.py`)

Shows how to set up teleoperation between two Roarm robots (leader-follower):
- Leader robot: moved manually (torque disabled)
- Follower robot: mirrors leader's movements

**Run:**
```bash
python examples/teleoperation.py
```

**Requirements:** Two Roarm robots

### 3. Recording Demonstrations (`record_demos.py`)

Explains how to record demonstrations using LeRobot's recording tools:
- Recording with LeRobot CLI (recommended)
- Recording with teleoperation
- Manual recording

**Run:**
```bash
python examples/record_demos.py
```

**Alternative (direct CLI):**
```bash
lerobot-record \
  --robot.type=roarm \
  --robot.roarm_type=roarm_m3 \
  --robot.port=/dev/ttyUSB0 \
  --repo-id=my-username/roarm_demos \
  --num-episodes=10
```

### 4. Training Policies (`train_policy.py`)

Shows how to train policies on recorded data:
- ACT (Action Chunking with Transformers)
- Diffusion Policy
- Simple feedforward policy

**Run:**
```bash
python examples/train_policy.py
```

**Alternative (direct):**
```bash
python -m lerobot.scripts.train \
  --dataset-repo-id=my-username/roarm_demos \
  --policy=act \
  --output-dir=outputs/roarm_act \
  --device=cuda
```

### 5. Running Inference (`run_policy.py`)

Demonstrates how to run trained policies on the robot:
- Running with LeRobot CLI
- Manual control loop
- Policy evaluation

**Run:**
```bash
python examples/run_policy.py
```

**Alternative (direct CLI):**
```bash
python -m lerobot.scripts.control_robot \
  --robot.type=roarm \
  --robot.roarm_type=roarm_m3 \
  --robot.port=/dev/ttyUSB0 \
  --policy-checkpoint=outputs/roarm_act/checkpoint-epoch-1000
```

## Configuration

All examples use `RoarmConfig` for robot configuration. You can customize:

### Serial Connection
```python
config = RoarmConfig(
    roarm_type="roarm_m3",
    port="/dev/ttyUSB0",
    baudrate=115200,
)
```

### WiFi Connection
```python
config = RoarmConfig(
    roarm_type="roarm_m3",
    host="192.168.1.100",
)
```

### Camera Setup
```python
config = RoarmConfig(
    roarm_type="roarm_m3",
    port="/dev/ttyUSB0",
    cameras={
        "wrist_cam": OpenCVCameraConfig(
            index_or_path=0,
            fps=30,
            width=640,
            height=480,
        ),
    },
)
```

## Workflow

The typical workflow is:

1. **Test connection** with `basic_control.py`
2. **Record demonstrations** with `record_demos.py` or teleoperation
3. **Train a policy** with `train_policy.py`
4. **Run the policy** with `run_policy.py`

## Troubleshooting

### Permission Denied
```bash
sudo chmod 666 /dev/ttyUSB0
```

### Camera Not Found
List available cameras:
```bash
ls /dev/video*
```

Update camera index in config:
```python
cameras={"wrist_cam": OpenCVCameraConfig(index_or_path=2)}
```

### Import Errors
Make sure you've installed the package:
```bash
cd lerobot_robot_roarm
pip install -e .
```

## Support

For more help:
- Check the main README
- Visit LeRobot documentation: https://huggingface.co/docs/lerobot
- Join LeRobot Discord: https://discord.gg/s3KuuzsPFb
