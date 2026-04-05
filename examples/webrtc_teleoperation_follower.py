"""
WebRTC Remote Teleoperation example for Roarm robot - FOLLOWER.

This script demonstrates how to set up a remote follower robot that receives
actions via WebRTC from a remote leader robot.

Requirements:
    pip install aiortc aiohttp

You need to run THREE programs:
    1. A signaling server (webrtc_signaling.py)
    2. A leader script on the computer with the leader robot
    3. This follower script on the computer with the follower robot

Usage:
    # On signaling server (can be any computer):
    python remote/webrtc_signaling.py --host 0.0.0.0 --port 8080
    
    # On leader computer:
    python examples/webrtc_teleoperation_leader.py --leader-port /dev/ttyUSB0 --signaling-server 192.168.1.100:8080
    
    # On follower computer:
    python examples/webrtc_teleoperation_follower.py --follower-port /dev/ttyUSB1 --signaling-server 192.168.1.100:8080
"""

import argparse
import time
import logging

from lerobot_robot_roarm import RoarmWebRTCConfig, RoarmWebRTC


def main():
    parser = argparse.ArgumentParser(description="WebRTC Follower - Receive robot actions over network")
    
    # Follower robot settings
    parser.add_argument("--follower-port", type=str, default="/dev/ttyUSB1",
                        help="Follower robot serial port")
    parser.add_argument("--roarm-type", type=str, default="roarm_m3",
                        help="Roarm model type (roarm_m3, roarm_alpha, etc.)")
    
    # WebRTC settings
    parser.add_argument("--signaling-server", type=str, required=True,
                        help="Signaling server address (host:port), e.g., 192.168.1.100:8080")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("WebRTC Remote Teleoperation - FOLLOWER")
    print("=" * 60)
    print(f"Follower robot: {args.roarm_type} on {args.follower_port}")
    print(f"Signaling server: {args.signaling_server}")
    print("=" * 60)
    print()
    
    # Configure follower robot with WebRTC
    follower_config = RoarmWebRTCConfig(
        roarm_type=args.roarm_type,
        port=args.follower_port,
        signaling_server=args.signaling_server,
        cameras={},  # Disable cameras for teleoperation
        id="follower"
    )
    
    # Create WebRTC follower
    print("Initializing WebRTC follower...")
    follower = RoarmWebRTC(follower_config)
    
    try:
        # Connect (this will wait for WebRTC connection from leader)
        print("\nConnecting to follower robot and waiting for WebRTC connection...")
        print("Waiting for leader to connect (this may take up to 30 seconds)...")
        follower.connect(calibrate=False)
        print("\n✓ WebRTC follower connected and ready!")
        print("\n" + "=" * 60)
        print("TELEOPERATION ACTIVE")
        print("=" * 60)
        print("Receiving actions via WebRTC from leader.")
        print("Follower robot will mirror leader movements.")
        print("Press Ctrl+C to stop.")
        print("=" * 60)
        print()
        
        # Keep applying received actions
        while True:
            # Apply any pending actions from WebRTC
            if follower.last_action is not None:
                follower.send_action({})  # Will use last_action from WebRTC
            
            # Log occasionally
            if follower.actions_applied % 50 == 0 and follower.actions_applied > 0:
                print(f"Actions applied: {follower.actions_applied}, received: {follower.actions_received}")
            
            # Control rate
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n\nStopping teleoperation...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect
        follower.disconnect()
        print("✓ Follower disconnected")
        print("Done!")


if __name__ == "__main__":
    main()
