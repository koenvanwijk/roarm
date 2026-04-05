#!/usr/bin/env python3
"""Test WebRTC Sender - simulates leader side."""

import numpy as np
import time
from lerobot_webrtc import WebRTCSender, WebRTCSenderConfig

def main():
    print("🔧 Initializing WebRTC Sender...")
    
    # Create sender config
    config = WebRTCSenderConfig(
        signaling_server="localhost:8080"
    )
    
    # Create sender
    sender = WebRTCSender(config)
    
    print("✓ Sender created")
    print("📡 Connecting to receiver via WebRTC...")
    
    # Give time for WebRTC connection
    time.sleep(3)
    
    print("📤 Sending test actions...")
    
    # Send some test actions
    for i in range(20):
        # Create a test action (6 joint values)
        action = np.array([
            np.sin(i * 0.1),      # Joint 1
            np.cos(i * 0.1),      # Joint 2
            i * 0.01,             # Joint 3
            -i * 0.01,            # Joint 4
            np.sin(i * 0.2),      # Joint 5
            np.cos(i * 0.2),      # Joint 6
        ], dtype=np.float32)
        
        try:
            sender.send_action(action)
            print(f"✓ Sent action #{i+1}: {action}")
        except Exception as e:
            print(f"❌ Error sending action: {e}")
            
        time.sleep(0.5)
    
    print("\n🛑 Disconnecting sender...")
    sender.disconnect()
    print("✓ Test complete")

if __name__ == "__main__":
    main()
