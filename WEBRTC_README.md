# WebRTC Remote Teleoperation

This directory contains WebRTC-enabled classes for remote teleoperation of Roarm robots over networks.

## Overview

The WebRTC implementation allows you to control a follower robot on a remote computer by moving a leader robot on your local computer. Actions are transmitted in real-time over WebRTC DataChannels.

### Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  Computer A     │         │  Computer B     │         │  Computer C     │
│  (Leader)       │         │  (Signaling)    │         │  (Follower)     │
│                 │         │                 │         │                 │
│  ┌───────────┐  │         │  ┌───────────┐  │         │  ┌───────────┐  │
│  │ Leader    │  │         │  │ Signaling │  │         │  │ Follower  │  │
│  │ Robot     │◄─┼─────────┼──┤ Server    │──┼─────────┼─►│ Robot     │  │
│  │ (Hardware)│  │         │  │ (WebRTC)  │  │         │  │ (Hardware)│  │
│  └─────▲─────┘  │         │  └───────────┘  │         │  └───────────┘  │
│        │        │         │                 │         │                 │
│  ┌─────┴─────┐  │         │                 │         │  ┌───────────┐  │
│  │ WebRTC    │  │  WebRTC │                 │  WebRTC │  │ WebRTC    │  │
│  │Teleoperator◄─┼──────────┼─────────────────┼─────────┼─►│ Follower  │  │
│  └───────────┘  │         │                 │         │  └───────────┘  │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

## Components

### 1. Configuration Classes

- **`RoarmWebRTCTeleoperatorConfig`**: Configuration for WebRTC leader
  - Inherits from `RoarmTeleoperatorConfig`
  - Adds `signaling_server` parameter for WebRTC connection

- **`RoarmWebRTCConfig`**: Configuration for WebRTC follower
  - Inherits from `RoarmConfig`
  - Adds `signaling_server` parameter for WebRTC connection

### 2. Robot Classes

- **`RoarmWebRTCTeleoperator`**: WebRTC-enabled leader
  - Wraps a local `RoarmTeleoperator`
  - Forwards actions via WebRTC DataChannel to remote follower
  - Drop-in replacement for `RoarmTeleoperator` in LeRobot framework

- **`RoarmWebRTC`**: WebRTC-enabled follower
  - Wraps a local `Roarm` robot
  - Receives actions via WebRTC DataChannel from remote leader
  - Drop-in replacement for `Roarm` in LeRobot framework

## Installation

Install WebRTC dependencies:

```bash
pip install aiortc aiohttp
```

## Usage

### Quick Start

You need THREE programs running:

1. **Signaling Server** (can be on any computer):
```bash
python remote/webrtc_signaling.py --host 0.0.0.0 --port 8080
```

2. **Leader** (on computer with leader robot):
```bash
python examples/webrtc_teleoperation_leader.py \
    --leader-port /dev/ttyUSB0 \
    --signaling-server 192.168.1.100:8080
```

3. **Follower** (on computer with follower robot):
```bash
python examples/webrtc_teleoperation_follower.py \
    --follower-port /dev/ttyUSB1 \
    --signaling-server 192.168.1.100:8080
```

Replace `192.168.1.100` with the IP address of the computer running the signaling server.

### Using in Your Code

#### Leader Side:

```python
from lerobot_robot_roarm import RoarmWebRTCTeleoperatorConfig, RoarmWebRTCTeleoperator

# Configure WebRTC leader
config = RoarmWebRTCTeleoperatorConfig(
    roarm_type="roarm_m3",
    port="/dev/ttyUSB0",
    signaling_server="192.168.1.100:8080",
    id="leader"
)

# Create and connect
leader = RoarmWebRTCTeleoperator(config)
leader.connect()

# Read and forward actions
while True:
    action = leader.get_action()  # Automatically forwards via WebRTC
    time.sleep(0.1)
```

#### Follower Side:

```python
from lerobot_robot_roarm import RoarmWebRTCConfig, RoarmWebRTC

# Configure WebRTC follower
config = RoarmWebRTCConfig(
    roarm_type="roarm_m3",
    port="/dev/ttyUSB1",
    signaling_server="192.168.1.100:8080",
    cameras={},
    id="follower"
)

# Create and connect
follower = RoarmWebRTC(config)
follower.connect()

# Apply received actions
while True:
    if follower.last_action is not None:
        follower.send_action({})  # Applies last_action from WebRTC
    time.sleep(0.05)
```

### Integration with LeRobot Framework

The WebRTC classes are drop-in replacements for the standard classes:

```python
# Standard teleoperation
from lerobot_robot_roarm import RoarmTeleoperatorConfig, RoarmTeleoperator
leader = RoarmTeleoperator(RoarmTeleoperatorConfig(port="/dev/ttyUSB0"))

# WebRTC teleoperation (just change the imports and add signaling_server)
from lerobot_robot_roarm import RoarmWebRTCTeleoperatorConfig, RoarmWebRTCTeleoperator
leader = RoarmWebRTCTeleoperator(
    RoarmWebRTCTeleoperatorConfig(
        port="/dev/ttyUSB0",
        signaling_server="192.168.1.100:8080"
    )
)
```

## How It Works

1. **Signaling Server**: A WebSocket server that facilitates WebRTC peer connection setup (SDP offer/answer exchange)

2. **WebRTC Leader**:
   - Connects to local leader robot (torque disabled for manual movement)
   - Creates WebRTC peer connection with DataChannel
   - Reads joint positions from leader robot
   - Sends actions as JSON messages via DataChannel

3. **WebRTC Follower**:
   - Connects to local follower robot
   - Waits for WebRTC connection from leader
   - Receives action messages via DataChannel
   - Applies actions to local follower robot

4. **Data Format**: Actions are sent as JSON:
```json
{
    "type": "action",
    "action": [pan, lift, elbow, wrist_flex, wrist_roll, gripper],
    "timestamp": 1234567890.123,
    "sequence": 42
}
```

## Network Requirements

- All computers must be able to reach the signaling server
- WebRTC uses UDP for data transmission (typically ports 49152-65535)
- For NAT traversal, you may need a STUN/TURN server (not included)

## Performance

- Control rate: ~10 Hz (configurable)
- Latency: Typically 50-100ms on local networks
- Bandwidth: ~1-2 KB/s per robot arm

## Troubleshooting

### Connection Timeout
- Ensure signaling server is running and accessible
- Check firewall settings (WebRTC uses UDP)
- Verify the signaling server address is correct

### High Latency
- Use wired Ethernet instead of WiFi
- Reduce control rate if needed
- Check network congestion

### Actions Not Applied
- Verify follower is connected (check logs)
- Ensure both robots are using the same signaling server
- Check that actions_received count is increasing

## Advanced Features

### Video Streaming (Future)

WebRTC supports video streaming. To add camera streaming from follower to leader:

```python
# Add video track to peer connection
@self.pc.on("track")
async def on_track(track):
    if track.kind == "video":
        # Process video frames
        pass
```

### Multiple Robots

You can control multiple follower robots from one leader by creating multiple WebRTC connections with different channel names.

## Comparison with WebSocket Implementation

| Feature | WebRTC | WebSocket |
|---------|--------|-----------|
| Protocol | UDP (DataChannel) | TCP (WebSocket) |
| Latency | Lower | Higher |
| Setup | More complex | Simpler |
| NAT Traversal | Requires STUN/TURN | Direct connection |
| Video Support | Built-in | Requires separate encoding |
| Best For | Real-time control | Reliable messaging |

## References

- [WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [aiortc Documentation](https://aiortc.readthedocs.io/)
- [LeRobot Documentation](https://github.com/huggingface/lerobot)
