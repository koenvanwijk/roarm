# Quick Start Guide

Get up and running with Roarm and LeRobot in minutes!

## Installation Steps

### 1. Install Prerequisites

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install LeRobot
pip install lerobot

# Install Roarm SDK
pip install roarm-sdk
```

### 2. Install This Package

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

### 3. Connect Your Robot

#### Serial Connection (Recommended)
```bash
# Find your device
ls /dev/ttyUSB*

# Grant permissions
sudo chmod 666 /dev/ttyUSB0
```

#### WiFi Connection
```bash
# Make sure robot and computer are on same network
# Find robot IP (check robot documentation)
ping 192.168.1.100
```

### 4. Test the Connection

Create a test script `test_connection.py`:

```python
from lerobot_robot_roarm import RoarmConfig, Roarm

# Serial connection
config = RoarmConfig(
    roarm_type="roarm_m3",
    port="/dev/ttyUSB0",
)

# Or WiFi
# config = RoarmConfig(
#     roarm_type="roarm_m3",
#     host="192.168.1.100",
# )

robot = Roarm(config)
robot.connect()

print("✓ Connected successfully!")
print("Current joint positions:")
obs = robot.get_observation()
for key, value in obs.items():
    if ".pos" in key:
        print(f"  {key}: {value:.3f}")

robot.disconnect()
```

Run it:
```bash
python test_connection.py
```

## First Recording Session

### 1. Prepare Your Setup

- Clear workspace around the robot
- Set up camera(s) if using vision
- Have a task in mind (e.g., pick and place)

### 2. Record Demonstrations

```bash
lerobot-record \
  --robot.type=roarm \
  --robot.roarm_type=roarm_m3 \
  --robot.port=/dev/ttyUSB0 \
  --repo-id=my-username/my-first-task \
  --num-episodes=10 \
  --fps=30
```

### 3. Check Your Data

```python
from lerobot.dataset import LeRobotDataset

dataset = LeRobotDataset("my-username/my-first-task")
print(f"Dataset has {len(dataset)} frames")
print(f"Features: {dataset.features}")

# Visualize an episode
episode = dataset.get_episode(0)
```

## Train Your First Policy

### 1. Train ACT Policy

```bash
python -m lerobot.scripts.train \
  --dataset-repo-id=my-username/my-first-task \
  --policy=act \
  --output-dir=outputs/my_first_policy \
  --training.num_epochs=1000 \
  --training.batch_size=8 \
  --device=cuda
```

### 2. Monitor Training

Training logs will be printed to console. If you enabled Weights & Biases:

```bash
# View at https://wandb.ai/your-username/roarm-lerobot
```

## Run Your Policy

### 1. Test the Trained Policy

```bash
python -m lerobot.scripts.control_robot \
  --robot.type=roarm \
  --robot.roarm_type=roarm_m3 \
  --robot.port=/dev/ttyUSB0 \
  --policy-checkpoint=outputs/my_first_policy/checkpoint-epoch-1000 \
  --num-rollouts=5
```

### 2. Evaluate Performance

Watch the robot execute the policy and note:
- Success rate
- Smoothness of movements
- Any issues or failures

### 3. Iterate

If results aren't good:
- Record more demonstrations (10-20+ episodes)
- Try different policy architectures
- Adjust training hyperparameters
- Improve data quality (consistent demonstrations)

## Next Steps

### Improve Your Policy

1. **Record more data**: 20-50 episodes often work better
2. **Add cameras**: Vision helps for many tasks
3. **Try different policies**: ACT, Diffusion, etc.
4. **Tune hyperparameters**: Learning rate, batch size, etc.

### Advanced Features

1. **Teleoperation**: Use a leader robot to control follower
2. **Multi-camera setup**: Add multiple viewpoints
3. **Processor pipelines**: Normalize actions/observations
4. **Custom tasks**: Define your own tasks and metrics

### Example Projects

Try these tasks:
- Pick and place objects
- Stacking blocks
- Opening/closing drawers
- Pouring liquids
- Assembly tasks

## Troubleshooting

### Robot won't connect
```bash
# Check device
ls /dev/ttyUSB*

# Check permissions
sudo chmod 666 /dev/ttyUSB0

# Test with roarm SDK directly
python -c "from roarm_sdk.roarm import roarm; r = roarm(roarm_type='roarm_m3', port='/dev/ttyUSB0'); print(r.joints_angle_get())"
```

### Camera issues
```bash
# List cameras
ls /dev/video*

# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera failed')"
```

### Training too slow
- Use GPU: `--device=cuda`
- Reduce batch size if OOM
- Use smaller model/policy
- Reduce dataset size for testing

### Policy performs poorly
- Record more diverse demonstrations
- Ensure demonstrations are consistent
- Check observation/action spaces match
- Verify camera calibration
- Try different policies

## Resources

- **LeRobot Docs**: https://huggingface.co/docs/lerobot
- **Examples**: See `examples/` directory
- **Discord**: https://discord.gg/s3KuuzsPFb
- **Roarm SDK**: Check Roarm documentation

## Getting Help

1. Check this guide and main README
2. Look at example scripts
3. Search LeRobot documentation
4. Ask on Discord
5. Open a GitHub issue

Happy robot learning! 🤖✨
