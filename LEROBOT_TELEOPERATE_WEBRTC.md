# Using LeRobot Teleoperate with WebRTC Follower

This guide shows how to use the standard `lerobot-teleoperate` command with a WebRTC-enabled follower robot on a remote computer.

## Overview

The WebRTC follower (`roarm_webrtc`) is registered as a standard robot type in LeRobot, so you can use it with any LeRobot command that expects a robot, including `lerobot-teleoperate`.

## Architecture

```
┌─────────────────────┐              ┌─────────────────────┐
│  Computer A         │              │  Computer B         │
│  (Leader)           │              │  (Signaling)        │
│                     │              │                     │
│  ┌──────────────┐   │              │  ┌──────────────┐   │
│  │ Leader Robot │   │              │  │  Signaling   │   │
│  │  (Local)     │   │              │  │   Server     │   │
│  └──────┬───────┘   │              │  └──────┬───────┘   │
│         │           │              │         │           │
│  ┌──────▼───────┐   │              │         │           │
│  │ lerobot-     │   │  WebRTC      │         │           │
│  │ teleoperate  ├───┼──────────────┼─────────┤           │
│  └──────────────┘   │              │         │           │
└─────────────────────┘              │         │           │
                                     │         │           │
┌─────────────────────┐              │         │           │
│  Computer C         │              │         │           │
│  (Follower)         │  WebRTC      │         │           │
│                     ├──────────────┼─────────┘           │
│  ┌──────────────┐   │              │                     │
│  │roarm_webrtc  │   │              └─────────────────────┘
│  │  (receives   │   │
│  │   via WebRTC)│   │
│  └──────┬───────┘   │
│         │           │
│  ┌──────▼───────┐   │
│  │Follower Robot│   │
│  │  (Local)     │   │
│  └──────────────┘   │
└─────────────────────┘
```

## Prerequisites

1. **Install WebRTC dependencies** on both leader and follower computers:
   ```bash
   pip install aiortc aiohttp
   ```

2. **Ensure roarm package is installed**:
   ```bash
   cd /home/kwijk/roarm
   pip install -e .
   ```

3. **Have a signaling server accessible** to both computers

## Quick Start

### 1. Start Signaling Server

On any computer accessible to both leader and follower:

```bash
python remote/webrtc_signaling.py --host 0.0.0.0 --port 8080
```

### 2. Use lerobot-teleoperate Command

On the leader computer (with leader robot):

```bash
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.id follower \
  --robot.roarm_type roarm_m3 \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.cameras '{}' \
  --teleop.type lerobot_robot_roarm \
  --teleop.id leader \
  --teleop.roarm_type roarm_m3 \
  --teleop.port /dev/ttyUSB0 \
  --fps 10
```

Replace `192.168.1.100` with the IP address of the signaling server.

### 3. The Follower Will Connect Automatically

The WebRTC follower will:
1. Connect to its local robot hardware
2. Connect to the signaling server
3. Wait for the WebRTC connection from the leader
4. Start receiving and applying actions

## Configuration

### Robot Configuration (Follower - WebRTC)

The `roarm_webrtc` robot type accepts these parameters:

- `--robot.type lerobot_robot_roarm_webrtc` - Use WebRTC-enabled follower
- `--robot.roarm_type` - Roarm model (roarm_m3, roarm_alpha, etc.)
- `--robot.port` - Serial port for follower robot (e.g., /dev/ttyUSB1)
- `--robot.host` - WiFi IP for follower robot (alternative to port)
- `--robot.signaling_server` - Signaling server address (host:port)
- `--robot.cameras` - Camera configuration (use '{}' to disable)
- `--robot.id` - Robot ID (optional)

### Teleoperator Configuration (Leader - Normal)

Use any standard teleoperator type:

**Roarm as leader:**
```bash
--teleop.type lerobot_robot_roarm
--teleop.roarm_type roarm_m3
--teleop.port /dev/ttyUSB0
```

**SO-101 as leader:**
```bash
--teleop.type so101_leader
--teleop.port /dev/ttyACM0
```

**Koch as leader:**
```bash
--teleop.type koch_leader
--teleop.port /dev/ttyACM0
```

## Examples

### Example 1: Roarm Leader → WebRTC Follower (Serial)

```bash
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.roarm_type roarm_m3 \
  --robot.port /dev/ttyUSB1 \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.cameras '{}' \
  --teleop.type lerobot_robot_roarm \
  --teleop.roarm_type roarm_m3 \
  --teleop.port /dev/ttyUSB0 \
  --fps 10
```

### Example 2: Roarm Leader → WebRTC Follower (WiFi)

```bash
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.roarm_type roarm_m3 \
  --robot.host "192.168.1.150" \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.cameras '{}' \
  --teleop.type lerobot_robot_roarm \
  --teleop.roarm_type roarm_m3 \
  --teleop.host "192.168.1.200" \
  --fps 10
```

### Example 3: SO-101 Leader → WebRTC Follower

```bash
python -m lerobot.scripts.lerobot_teleoperate \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.roarm_type roarm_m3 \
  --robot.port /dev/ttyUSB1 \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.cameras '{}' \
  --teleop.type so101_leader \
  --teleop.port /dev/ttyACM0 \
  --fps 10
```

## Helper Script

For convenience, use the provided helper script:

```bash
python examples/lerobot_teleoperate_with_webrtc.py \
  --leader-port /dev/ttyUSB0 \
  --follower-signaling 192.168.1.100:8080
```

This script automatically constructs the full lerobot-teleoperate command.

## How It Works

1. **Leader Side**:
   - `lerobot-teleoperate` reads from local leader robot
   - Creates a `roarm_webrtc` follower instance
   - The WebRTC follower establishes connection via signaling server
   - Actions are sent via WebRTC DataChannel to remote computer

2. **Follower Side**:
   - The `roarm_webrtc` robot connects to local hardware
   - Waits for WebRTC connection from leader
   - Receives actions via DataChannel
   - Applies actions to local robot

3. **Data Flow**:
   ```
   Leader Robot → Teleoperator.get_action() → lerobot-teleoperate → 
   Robot.send_action() → RoarmWebRTC → WebRTC DataChannel → 
   Remote RoarmWebRTC → Local Roarm → Follower Robot
   ```

## Recording Demonstrations

You can also record demonstrations with WebRTC follower:

```bash
lerobot-record \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.roarm_type roarm_m3 \
  --robot.port /dev/ttyUSB1 \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.cameras '{}' \
  --teleop.type lerobot_robot_roarm \
  --teleop.roarm_type roarm_m3 \
  --teleop.port /dev/ttyUSB0 \
  --repo-id my-username/roarm_webrtc_demos \
  --num-episodes 10 \
  --fps 30
```

## Troubleshooting

### "Robot type 'roarm_webrtc' not found"

Make sure the roarm package is installed:
```bash
cd /home/kwijk/roarm
pip install -e .
```

### Connection Timeout

- Verify signaling server is running and accessible
- Check firewall settings (WebRTC uses UDP)
- Ensure both computers can reach the signaling server
- Try increasing timeout (edit config if needed)

### No Actions Received

- Check that both leader and follower are using the same signaling server
- Verify WebRTC connection established (check logs)
- Ensure leader robot is connected and moving

### High Latency

- Use wired Ethernet instead of WiFi
- Reduce FPS if needed (--fps 5)
- Check network congestion
- Ensure both computers are on same local network

## Advantages

✅ **Standard LeRobot Interface**: Use any LeRobot command  
✅ **No Code Changes**: Just change robot type to `roarm_webrtc`  
✅ **Mix and Match**: Use any teleoperator with WebRTC follower  
✅ **Full Integration**: Works with recording, replay, training  
✅ **Low Latency**: UDP-based WebRTC for real-time control  

## Comparison with Other Methods

| Method | Setup | Use Case |
|--------|-------|----------|
| **Normal Teleoperate** | Both robots on same computer | Local development |
| **WebRTC with lerobot-teleoperate** | Leader local, follower remote | Production remote control |
| **Custom WebRTC scripts** | Separate leader/follower scripts | Advanced customization |
| **WebSocket** | Similar to WebRTC | Simpler but higher latency |

## Network Requirements

- **Signaling Server**: Needs WebSocket (TCP) port open (default: 8080)
- **WebRTC Data**: Uses UDP (typically ports 49152-65535)
- **Bandwidth**: ~1-2 KB/s per robot
- **Latency**: Best on local network (50-100ms typical)

## Next Steps

- Try recording demonstrations with remote follower
- Add camera streaming (future enhancement)
- Deploy signaling server on cloud for internet access
- Use STUN/TURN servers for NAT traversal

## See Also

- [WEBRTC_README.md](../WEBRTC_README.md) - Complete WebRTC documentation
- [WEBRTC_IMPLEMENTATION.md](../WEBRTC_IMPLEMENTATION.md) - Technical details
- [README.md](../README.md) - Main Roarm documentation
