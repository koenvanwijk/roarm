#!/usr/bin/env python3
"""
Example: Using WebRTC Robot Proxy with lerobot-teleoperate

This shows how to use WebRTC as a network transport layer with ANY robot type.

The WebRTC proxy receives actions from a remote leader and forwards them to
a local robot (can be Roarm, Koch, or any other robot type).

Usage:
    # 1. Start signaling server
    python remote/webrtc_signaling.py --host 0.0.0.0 --port 8080
    
    # 2. On leader computer - use normal teleoperator with WebRTC robot
    python -m lerobot.scripts.lerobot_teleoperate \\
      --robot.type lerobot_robot_roarm_webrtc \\
      --robot.roarm_type roarm_m3 \\
      --robot.port /dev/ttyUSB1 \\
      --robot.signaling_server "192.168.1.100:8080" \\
      --teleop.type lerobot_robot_roarm \\
      --teleop.port /dev/ttyUSB0 \\
      --fps 10
    
    # The WebRTC robot will:
    # 1. Connect to local robot (/dev/ttyUSB1)
    # 2. Wait for WebRTC connection
    # 3. Receive actions via WebRTC
    # 4. Forward actions to local robot
"""

print(__doc__)
