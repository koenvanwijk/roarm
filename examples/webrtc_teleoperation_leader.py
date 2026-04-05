"""
WebRTC Remote Teleoperation example for Roarm robot.

This script demonstrates how to set up remote teleoperation using WebRTC,
where a leader robot on one computer sends actions to a follower robot
on another computer over a network.

Requirements:
    pip install aiortc aiohttp

You need to run THREE programs:
    1. A signaling server (webrtc_signaling.py)
    2. This leader script on the computer with the leader robot
    3. A follower script on the computer with the follower robot

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

from lerobot_robot_roarm import RoarmWebRTCTeleoperatorConfig, RoarmWebRTCTeleoperator


def main():
    parser = argparse.ArgumentParser(description="WebRTC Leader - Stream robot actions over network")
    
    # Leader robot settings
    parser.add_argument("--leader-port", type=str, default="/dev/ttyUSB0",
                        help="Leader robot serial port")
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
    print("WebRTC Remote Teleoperation - LEADER")
    print("=" * 60)
    print(f"Leader robot: {args.roarm_type} on {args.leader_port}")
    print(f"Signaling server: {args.signaling_server}")
    print("=" * 60)
    print()
    
    # Configure leader robot with WebRTC
    leader_config = RoarmWebRTCTeleoperatorConfig(
        roarm_type=args.roarm_type,
        port=args.leader_port,
        signaling_server=args.signaling_server,
        id="leader"
    )
    
    # Create WebRTC teleoperator
    print("Initializing WebRTC teleoperator...")
    leader = RoarmWebRTCTeleoperator(leader_config)
    
    try:
        # Connect (this will establish WebRTC connection)
        print("\nConnecting to leader robot and establishing WebRTC connection...")
        print("This may take a few seconds...")
        leader.connect()
        print("\n✓ WebRTC teleoperator connected and ready!")
        print("\n" + "=" * 60)
        print("TELEOPERATION ACTIVE")
        print("=" * 60)
        print("Move the leader robot manually.")
        print("Actions are being streamed via WebRTC to the follower.")
        print("Press Ctrl+C to stop.")
        print("=" * 60)
        print()
        
        # Keep reading and forwarding actions
        while True:
            # Get action from leader (this also forwards via WebRTC)
            action = leader.get_action()
            
            # Log occasionally
            if leader.actions_sent % 50 == 0:
                print(f"Actions sent: {leader.actions_sent}")
            
            # Control rate (10 Hz)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopping teleoperation...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect
        leader.disconnect()
        print("✓ Leader disconnected")
        print("Done!")


if __name__ == "__main__":
    main()
