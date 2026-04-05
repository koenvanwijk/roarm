#!/usr/bin/env python3
"""Simple integration test for WebRTC sender and receiver."""

import numpy as np
import time
import sys
from multiprocessing import Process
from lerobot_webrtc import WebRTCSender, WebRTCSenderConfig, WebRTCReceiver, WebRTCReceiverConfig

def run_receiver():
    """Run receiver in separate process."""
    print("[RECEIVER] 🔧 Initializing...")
    
    config = WebRTCReceiverConfig(signaling_server="localhost:8080")
    receiver = WebRTCReceiver(config)
    
    print("[RECEIVER] ✓ Created, waiting for connection...")
    
    # Wait for actions
    received_count = 0
    for i in range(60):  # Try for 60 seconds
        try:
            action = receiver.get_action()
            
            if action is not None:
                received_count += 1
                print(f"[RECEIVER] ✅ Received action #{received_count}: {action[:3]}...")
                
                if received_count >= 5:
                    print(f"[RECEIVER] ✓ Success! Received {received_count} actions")
                    break
            else:
                if i % 5 == 0 and i > 0:
                    print(f"[RECEIVER] ⏳ Waiting... ({i}s)")
                
        except Exception as e:
            if "not connected" not in str(e):
                print(f"[RECEIVER] ❌ Error: {e}")
            
        time.sleep(1)
    
    receiver.disconnect()
    return received_count > 0


def run_sender():
    """Run sender in separate process."""
    time.sleep(5)  # Give receiver more time to start and connect
    
    print("[SENDER] 🔧 Initializing...")
    
    config = WebRTCSenderConfig(signaling_server="localhost:8080")
    sender = WebRTCSender(config)
    
    print("[SENDER] ✓ Created, connecting...")
    
    # Give time for WebRTC connection
    time.sleep(5)
    
    print("[SENDER] 📤 Sending test actions...")
    
    # Send test actions
    for i in range(10):
        action = np.array([i * 0.1, -i * 0.1, np.sin(i), np.cos(i), i * 0.01, -i * 0.01], dtype=np.float32)
        
        try:
            sender.send_action(action)
            print(f"[SENDER] ✓ Sent action #{i+1}")
        except Exception as e:
            print(f"[SENDER] ❌ Error: {e}")
            
        time.sleep(1)
    
    sender.disconnect()
    print("[SENDER] ✓ Complete")


def main():
    print("=" * 60)
    print("WebRTC Integration Test")
    print("=" * 60)
    print()
    print("Make sure signaling server is running:")
    print("  python lerobot_webrtc/signaling_server.py")
    print()
    print("=" * 60)
    print()
    
    # Start receiver process
    receiver_proc = Process(target=run_receiver)
    receiver_proc.start()
    
    # Start sender process
    sender_proc = Process(target=run_sender)
    sender_proc.start()
    
    # Wait for both
    sender_proc.join(timeout=30)
    receiver_proc.join(timeout=30)
    
    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
