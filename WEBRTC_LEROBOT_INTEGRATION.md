# WebRTC Integration with lerobot-teleoperate - Summary

## What Was Implemented

I've enhanced the WebRTC implementation to work seamlessly with the standard `lerobot-teleoperate` command. You can now use a normal local leader robot with a WebRTC-enabled remote follower.

## Key Changes

### 1. Robot Registration

- **Registered `RoarmWebRTCConfig`** with LeRobot's factory system using `@RobotConfig.register_subclass("roarm_webrtc")`
- This makes `roarm_webrtc` available as a standard robot type for all LeRobot commands

### 2. Files Updated/Created

**Updated:**
- `lerobot_robot_roarm/config_roarm_webrtc.py` - Added `@RobotConfig.register_subclass("roarm_webrtc")`

**Created:**
- `examples/lerobot_teleoperate_with_webrtc.py` - Helper script for using lerobot-teleoperate with WebRTC
- `LEROBOT_TELEOPERATE_WEBRTC.md` - Comprehensive guide for using WebRTC with lerobot-teleoperate

**Enhanced:**
- `README.md` - Added WebRTC remote teleoperation example and feature listing

## How to Use

### Simple Usage

Just use the standard `lerobot-teleoperate` command with `roarm_webrtc` as the robot type:

```bash
# 1. Start signaling server
python remote/webrtc_signaling.py --host 0.0.0.0 --port 8080

# 2. Use lerobot-teleoperate with WebRTC follower
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

### With Helper Script

```bash
python examples/lerobot_teleoperate_with_webrtc.py \
  --leader-port /dev/ttyUSB0 \
  --follower-signaling 192.168.1.100:8080
```

## Architecture

```
Leader Computer                    Signaling Server              Follower Computer
─────────────────                  ────────────────              ─────────────────
                                                                 
┌─────────────────┐                ┌─────────────┐             
│ Leader Robot    │                │ Signaling   │              
│ (Local)         │                │ Server      │              
└────────┬────────┘                └──────┬──────┘              
         │                                │                     
         │                                │                     
┌────────▼────────┐                       │                ┌──────────────────┐
│ lerobot-        │                       │                │ RoarmWebRTC      │
│ teleoperate     │                       │                │ (started by      │
│                 │                       │                │  lerobot)        │
│ - Reads leader  │◄──────WebRTC─────────┴───────────────►│                  │
│ - Sends to      │       DataChannel                      │ - Receives via   │
│   roarm_webrtc  │                                        │   WebRTC         │
└─────────────────┘                                        │ - Applies to     │
                                                           │   local robot    │
                                                           └────────┬─────────┘
                                                                    │
                                                           ┌────────▼─────────┐
                                                           │ Follower Robot   │
                                                           │ (Local)          │
                                                           └──────────────────┘
```

## What Makes This Special

### 1. Drop-in Replacement
You don't need custom scripts - just use the standard LeRobot commands with `--robot.type lerobot_robot_roarm_webrtc`

### 2. Works with All Leaders
Any teleoperator type works with the WebRTC follower:
- `lerobot_robot_roarm` (Roarm leader)
- `so101_leader` (SO-101 leader)
- `koch_leader` (Koch leader)
- Any custom teleoperator

### 3. Full LeRobot Integration
Works with all LeRobot commands:
- `lerobot-teleoperate` ✅
- `lerobot-record` ✅
- `lerobot-replay` ✅
- Any custom scripts using LeRobot's Robot interface ✅

### 4. Same Configuration Format
Uses LeRobot's standard configuration system:
```bash
--robot.type lerobot_robot_roarm_webrtc
--robot.roarm_type roarm_m3
--robot.port /dev/ttyUSB1
--robot.signaling_server "host:port"
```

## Use Cases

### 1. Development & Testing
- Develop on one computer
- Test on robot in another room/location
- No need to move equipment

### 2. Remote Demonstrations
- Record demonstrations with operator in one location
- Robot in another location (e.g., lab, production floor)

### 3. Multi-Site Training
- Collect data from multiple locations
- All using the same policies and procedures

### 4. Safety & Convenience
- Operator stays in safe/comfortable location
- Robot operates in hazardous/difficult-to-access area

## Configuration Options

### Required Parameters
- `--robot.type lerobot_robot_roarm_webrtc` - Use WebRTC-enabled follower
- `--robot.signaling_server` - Signaling server address (host:port)

### Robot Connection (choose one)
- `--robot.port` - Serial port (e.g., /dev/ttyUSB1)
- `--robot.host` - WiFi IP address

### Optional Parameters
- `--robot.roarm_type` - Robot model (default: roarm_m3)
- `--robot.cameras` - Camera config (use '{}' to disable)
- `--robot.id` - Robot identifier
- `--fps` - Control frequency in Hz

## Examples

### Example 1: Roarm Leader → WebRTC Follower
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

### Example 2: SO-101 Leader → WebRTC Follower
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

### Example 3: Recording with WebRTC
```bash
lerobot-record \
  --robot.type lerobot_robot_roarm_webrtc \
  --robot.roarm_type roarm_m3 \
  --robot.port /dev/ttyUSB1 \
  --robot.signaling_server "192.168.1.100:8080" \
  --robot.cameras '{}' \
  --teleop.type lerobot_robot_roarm \
  --teleop.port /dev/ttyUSB0 \
  --repo-id my-username/roarm_webrtc_demos \
  --num-episodes 10
```

## Technical Details

### How It Works Internally

1. **Leader Side**:
   - `lerobot-teleoperate` creates a `RoarmWebRTC` follower instance
   - The WebRTC follower connects to signaling server
   - Establishes WebRTC peer connection with remote follower
   - Actions are forwarded via WebRTC DataChannel

2. **Follower Side**:
   - The `RoarmWebRTC` robot connects to local hardware
   - Also connects to signaling server  
   - Waits for WebRTC connection
   - Receives and applies actions from DataChannel

3. **Data Flow**:
   ```
   Leader Robot → Teleoperator → lerobot-teleoperate → 
   RoarmWebRTC (local) → WebRTC DataChannel → 
   RoarmWebRTC (remote) → Roarm → Follower Robot
   ```

### Threading Model
- Main thread: Robot control and LeRobot command execution
- Background thread: WebRTC event loop (asyncio)
- Thread-safe communication via shared state

## Advantages

✅ **No Custom Code**: Use standard LeRobot commands  
✅ **Mix and Match**: Any leader with WebRTC follower  
✅ **Full Integration**: All LeRobot features work  
✅ **Low Latency**: UDP-based for real-time control  
✅ **Transparent**: Works like a local robot from LeRobot's perspective  
✅ **Flexible**: Works with recording, replay, training, inference  

## Documentation

- **[LEROBOT_TELEOPERATE_WEBRTC.md](LEROBOT_TELEOPERATE_WEBRTC.md)** - Complete guide for using lerobot-teleoperate with WebRTC
- **[WEBRTC_README.md](WEBRTC_README.md)** - General WebRTC implementation documentation
- **[WEBRTC_IMPLEMENTATION.md](WEBRTC_IMPLEMENTATION.md)** - Technical implementation details
- **[README.md](README.md)** - Main Roarm package documentation

## Testing

1. **Local Test** (same computer):
   ```bash
   # Terminal 1: Signaling
   python remote/webrtc_signaling.py --host localhost --port 8080
   
   # Terminal 2: Teleoperate
   python examples/lerobot_teleoperate_with_webrtc.py \
     --leader-port /dev/ttyUSB0 \
     --follower-signaling localhost:8080
   ```

2. **Network Test** (different computers):
   - Start signaling server on accessible computer
   - Run lerobot-teleoperate on leader computer
   - The follower will connect automatically

## Conclusion

The WebRTC follower is now a **first-class citizen** in the LeRobot ecosystem. You can use it anywhere you would use a normal robot, just by changing the robot type to `roarm_webrtc` and adding the signaling server parameter.

This enables powerful remote teleoperation capabilities while maintaining full compatibility with LeRobot's rich feature set.
