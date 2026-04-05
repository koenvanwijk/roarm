# WebRTC Quick Reference

## Quick Start Commands

### 1. Start Signaling Server
```bash
python remote/webrtc_signaling.py --host 0.0.0.0 --port 8080
```

### 2. Use with lerobot-teleoperate

**Roarm Leader → WebRTC Follower:**
```bash
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.port /dev/ttyUSB1 \
  --teleop.type lerobot_robot_roarm \
  --teleop.port /dev/ttyUSB0 \
  --fps 10
```

**SO-101 Leader → WebRTC Follower:**
```bash
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.port /dev/ttyUSB1 \
  --teleop.type so101_leader \
  --teleop.port /dev/ttyACM0 \
  --fps 10
```

**Helper Script:**
```bash
python examples/lerobot_teleoperate_with_webrtc.py \
  --leader-port /dev/ttyUSB0 \
  --follower-signaling 192.168.1.100:8080
```

## Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--robot.type` | Use `roarm_webrtc` for WebRTC follower | `roarm_webrtc` |
| `--robot.signaling_server` | Signaling server address | `192.168.1.100:8080` |
| `--robot.port` | Follower serial port | `/dev/ttyUSB1` |
| `--robot.host` | Follower WiFi IP (alternative) | `192.168.1.150` |
| `--teleop.type` | Leader type | `lerobot_robot_roarm`, `so101_leader` |
| `--teleop.port` | Leader serial port | `/dev/ttyUSB0` |
| `--fps` | Control frequency | `10` |

## Common Use Cases

### Local Development
```bash
# Signaling on localhost
python remote/webrtc_signaling.py --host localhost --port 8080

# Teleoperate
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.signaling_server "localhost:8080" \
  --robot.port /dev/ttyUSB1 \
  --teleop.type lerobot_robot_roarm \
  --teleop.port /dev/ttyUSB0 \
  --fps 10
```

### Remote Operation
```bash
# Signaling on network (Computer B: 192.168.1.100)
python remote/webrtc_signaling.py --host 0.0.0.0 --port 8080

# Leader side (Computer A)
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.port /dev/ttyUSB1 \
  --teleop.type lerobot_robot_roarm \
  --teleop.port /dev/ttyUSB0 \
  --fps 10
```

### Recording Demos
```bash
lerobot-record \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.port /dev/ttyUSB1 \
  --teleop.type lerobot_robot_roarm \
  --teleop.port /dev/ttyUSB0 \
  --repo-id my-username/demos \
  --num-episodes 10
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection timeout | Check signaling server is running and accessible |
| "roarm_webrtc not found" | Run `pip install -e .` from roarm directory |
| High latency | Use wired Ethernet, reduce FPS |
| No actions received | Verify both use same signaling server |
| Firewall issues | Allow UDP ports 49152-65535 for WebRTC |

## Architecture

```
Computer A (Leader)          Computer B (Signaling)          Computer C (Follower)
───────────────────          ──────────────────────          ─────────────────────
                                                             
┌────────────────┐           ┌────────────────┐             
│ Leader Robot   │           │ Signaling      │             
└───────┬────────┘           │ Server         │             
        │                    └────────┬───────┘             
┌───────▼────────┐                    │                     ┌──────────────────┐
│ lerobot-       │                    │                     │ RoarmWebRTC      │
│ teleoperate    │◄───────WebRTC──────┴────────────────────►│                  │
└────────────────┘           DataChannel                    └────────┬─────────┘
                                                                     │
                                                            ┌────────▼─────────┐
                                                            │ Follower Robot   │
                                                            └──────────────────┘
```

## Documentation

- **[LEROBOT_TELEOPERATE_WEBRTC.md](LEROBOT_TELEOPERATE_WEBRTC.md)** - Detailed guide
- **[WEBRTC_README.md](WEBRTC_README.md)** - Complete WebRTC docs
- **[README.md](README.md)** - Main package docs

## Dependencies

```bash
pip install aiortc aiohttp
```
