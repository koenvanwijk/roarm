"""
Example: Using lerobot-teleoperate with WebRTC follower

This demonstrates how to use the standard LeRobot teleoperation command
with a normal local leader and a WebRTC-enabled remote follower.

Setup:
    1. Run signaling server (on any accessible computer):
       python remote/webrtc_signaling.py --host 0.0.0.0 --port 8080
    
    2. On the follower computer, the WebRTC follower will connect to the
       signaling server and wait for the leader connection
    
    3. Run this command on the leader computer with the leader robot

Usage:
    python examples/lerobot_teleoperate_with_webrtc.py \\
        --leader-port /dev/ttyUSB0 \\
        --follower-signaling 192.168.1.100:8080
"""

import subprocess
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="LeRobot teleoperate with WebRTC follower"
    )
    
    # Leader settings
    parser.add_argument(
        "--leader-port", 
        type=str, 
        default="/dev/ttyUSB0",
        help="Leader robot serial port"
    )
    parser.add_argument(
        "--leader-type",
        type=str,
        default="lerobot_robot_roarm",
        help="Leader robot type (lerobot_robot_roarm, so101_leader, etc.)"
    )
    parser.add_argument(
        "--leader-roarm-type",
        type=str,
        default="roarm_m3",
        help="Leader Roarm model (if using lerobot_robot_roarm)"
    )
    
    # WebRTC follower settings
    parser.add_argument(
        "--follower-signaling",
        type=str,
        required=True,
        help="Signaling server for WebRTC follower (host:port), e.g., 192.168.1.100:8080"
    )
    parser.add_argument(
        "--follower-roarm-type",
        type=str,
        default="roarm_m3",
        help="Follower Roarm model"
    )
    
    # Teleoperation settings
    parser.add_argument(
        "--fps",
        type=int,
        default=10,
        help="Control frequency in Hz"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("LeRobot Teleoperate with WebRTC Follower")
    print("=" * 70)
    print(f"Leader: {args.leader_type} on {args.leader_port}")
    print(f"Follower: WebRTC (signaling server: {args.follower_signaling})")
    print(f"Control rate: {args.fps} Hz")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT:")
    print("1. Make sure the signaling server is running")
    print("2. The WebRTC follower will be started automatically")
    print("3. Move the leader robot to control the remote follower")
    print()
    
    # Build the lerobot-teleoperate command
    cmd = [
        "python", "-m", "lerobot.scripts.lerobot_teleoperate",
        
        # Follower robot (WebRTC-enabled)
        "--robot.type", "lerobot_robot_roarm_webrtc",
        "--robot.id", "follower",
        "--robot.roarm_type", args.follower_roarm_type,
        "--robot.signaling_server", args.follower_signaling,
        "--robot.cameras", "{}",  # No cameras for teleoperation
        
        # Leader robot (normal teleoperator)
        "--teleop.type", args.leader_type,
        "--teleop.id", "leader",
        "--teleop.port", args.leader_port,
        
        # Control rate
        "--fps", str(args.fps),
    ]
    
    # Add leader-specific settings if it's a Roarm
    if args.leader_type == "lerobot_robot_roarm":
        cmd.extend([
            "--teleop.roarm_type", args.leader_roarm_type,
        ])
    
    print("Command:")
    print(" ".join(cmd))
    print()
    print("=" * 70)
    print("Starting teleoperation...")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n\nError: lerobot package not found")
        print("Make sure LeRobot is installed: pip install lerobot")
        sys.exit(1)


if __name__ == "__main__":
    main()
