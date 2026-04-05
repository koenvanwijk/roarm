# WebRTC Teleoperation - Clean Architecture

## Overview

Simple WebRTC-based teleoperation using two components:
- **WebRTCSender**: Robot (on leader computer) that sends actions via WebRTC
- **WebRTCReceiver**: Teleoperator (on follower computer) that receives actions via WebRTC

This works with ANY robot and teleoperator types!

## Testing

### Quick Test

1. Start signaling server:
```bash
python lerobot_webrtc/signaling_server.py --host 0.0.0.0 --port 8080
```

2. Run integration test:
```bash
PYTHONPATH=/home/kwijk/roarm:$PYTHONPATH python lerobot_webrtc/test_integration.py
```

### Direct WebRTC Test
```bash
python lerobot_webrtc/test_direct_webrtc.py
```

### Signaling Server Test
```bash
python lerobot_webrtc/test_signaling.py
```

## Architecture

```
┌─────────────────────────────────────┐         ┌─────────────────────────────────────┐
│  LEADER COMPUTER (Computer A)       │         │  FOLLOWER COMPUTER (Computer B)     │
│                                     │         │                                     │
│  ┌──────────────────┐               │         │                                     │
│  │ Leader Robot     │               │         │  ┌──────────────────┐               │
│  │ (any type)       │               │         │  │ Follower Robot   │               │
│  └────────┬─────────┘               │         │  │ (any type)       │               │
│           │                         │         │  └────────▲─────────┘               │
│  ┌────────▼─────────┐               │         │           │                         │
│  │ Teleoperator     │               │         │  ┌────────┴─────────┐               │
│  │ (reads actions)  │               │         │  │ lerobot-         │               │
│  └────────┬─────────┘               │         │  │ teleoperate      │               │
│           │                         │         │  │ (sends actions)  │               │
│  ┌────────▼─────────┐               │         │  └────────▲─────────┘               │
│  │ lerobot-         │               │         │           │                         │
│  │ teleoperate      │               │         │  ┌────────┴─────────┐               │
│  └────────┬─────────┘               │         │  │ WebRTCReceiver   │               │
│           │                         │         │  │ (teleop)         │               │
│  ┌────────▼─────────┐               │         │  └────────▲─────────┘               │
│  │ WebRTCSender     │               │         │           │                         │
│  │ (robot)          │               │         │           │                         │
│  └────────┬─────────┘               │         │           │                         │
│           │                         │         │           │                         │
│           └─────────────WebRTC──────┼─────────┴───────────┘                         │
│                      DataChannel    │                                               │
└─────────────────────────────────────┘         └─────────────────────────────────────┘
```

## Setup

### 1. Start Signaling Server

On any computer accessible to both leader and follower:

```bash
python remote/webrtc_signaling.py --host 0.0.0.0 --port 8080
```

### 2. Leader Computer

```bash
lerobot-teleoperate \
  --robot.type lerobot_robot_webrtc_sender \
  --robot.signaling_server "192.168.1.100:8080" \
  --teleop.type lerobot_robot_roarm \
  --teleop.port /dev/ttyUSB0 \
  --fps 10
```

The leader computer:
- Uses **any teleoperator** (Roarm, SO-101, Koch, etc.) to read actions
- Uses **lerobot_robot_webrtc_sender** as the "robot" to forward actions via WebRTC

### 3. Follower Computer

```bash
lerobot-teleoperate \
  --robot.type lerobot_robot_roarm \
  --robot.port /dev/ttyUSB1 \
  --teleop.type lerobot_teleoperator_webrtc_receiver \
  --teleop.signaling_server "192.168.1.100:8080" \
  --fps 10
```

The follower computer:
- Uses **lerobot_teleoperator_webrtc_receiver** as the "teleoperator" to receive actions via WebRTC
- Uses **any robot** (Roarm, Koch, etc.) to execute actions

## Examples

### Example 1: Roarm Leader → Roarm Follower

**Leader:**
```bash
lerobot-teleoperate \
  --robot.type webrtc_sender \
  --robot.signaling_server "192.168.1.100:8080" \
  --teleop.type lerobot_robot_roarm \
  --teleop.roarm_type roarm_m3 \
  --teleop.port /dev/ttyUSB0 \
  --fps 10
```

**Follower:**
```bash
lerobot-teleoperate \
  --robot.type lerobot_robot_roarm \
  --robot.roarm_type roarm_m3 \
  --robot.port /dev/ttyUSB1 \
  --teleop.type webrtc_receiver \
  --teleop.signaling_server "192.168.1.100:8080" \
  --fps 10
```

### Example 2: SO-101 Leader → Roarm Follower

**Leader:**
```bash
lerobot-teleoperate \
  --robot.type webrtc_sender \
  --robot.signaling_server "192.168.1.100:8080" \
  --teleop.type so101_leader \
  --teleop.port /dev/ttyACM0 \
  --fps 10
```

**Follower:**
```bash
lerobot-teleoperate \
  --robot.type lerobot_robot_roarm \
  --robot.roarm_type roarm_m3 \
  --robot.port /dev/ttyUSB1 \
  --teleop.type webrtc_receiver \
  --teleop.signaling_server "192.168.1.100:8080" \
  --fps 10
```

### Example 3: Roarm Leader → Koch Follower

**Leader:**
```bash
lerobot-teleoperate \
  --robot.type webrtc_sender \
  --robot.signaling_server "192.168.1.100:8080" \
  --teleop.type lerobot_robot_roarm \
  --teleop.port /dev/ttyUSB0 \
  --fps 10
```

**Follower:**
```bash
lerobot-teleoperate \
  --robot.type koch \
  --robot.port /dev/ttyUSB1 \
  --teleop.type webrtc_receiver \
  --teleop.signaling_server "192.168.1.100:8080" \
  --fps 10
```

## Key Advantages

✅ **Robot-Agnostic**: Works with ANY robot and teleoperator type  
✅ **Clean Architecture**: WebRTC is just a network transport layer  
✅ **No Code Duplication**: One sender, one receiver, works for everything  
✅ **Standard LeRobot**: Uses normal `lerobot-teleoperate` command  
✅ **Flexible**: Mix and match any leader/follower combinations  

## Files

- `lerobot_robot_roarm/webrtc_sender.py` - WebRTC Sender (Robot)
- `lerobot_robot_roarm/webrtc_receiver.py` - WebRTC Receiver (Teleoperator)

## Dependencies

```bash
pip install aiortc aiohttp
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection timeout | Check signaling server is running and accessible |
| No actions received | Ensure both use same signaling server address |
| High latency | Use wired Ethernet, reduce FPS |

## Technical Details

- **Protocol**: WebRTC DataChannel (UDP-based)
- **Signaling**: WebSocket to coordinate peer connection
- **Data Format**: JSON with action arrays
- **Control Rate**: Configurable via --fps parameter
- **Latency**: 50-100ms typical on local network
