#!/usr/bin/env python3
"""Test WebRTC Receiver - simulates follower side."""

import numpy as np
import time
from lerobot_webrtc import WebRTCReceiver, WebRTCReceiverConfig

def main():
    print("🔧 Initializing WebRTC Receiver...")
    
    # Create receiver config
    config = WebRTCReceiverConfig(
        signaling_server="localhost:8080"
    )
    
    # Create receiver
    receiver = WebRTCReceiver(config)
    
    print("✓ Receiver created")
    print("📡 Waiting for WebRTC connection and actions...")
    
    # Wait for actions
    for i in range(50):  # Try for 50 seconds
        try:
            action = receiver.get_action()
            
            if action is not None:
                print(f"\n✅ Received action #{i+1}:")
                print(f"   Shape: {action.shape}")
                print(f"   Values: {action}")
                print(f"   Min: {action.min():.3f}, Max: {action.max():.3f}")
            else:
                if i % 10 == 0:
                    print(f"⏳ Still waiting for actions... ({i}s)")
                
        except Exception as e:
            print(f"❌ Error getting action: {e}")
            
        time.sleep(1)
    
    print("\n🛑 Disconnecting receiver...")
    receiver.disconnect()
    print("✓ Test complete")

if __name__ == "__main__":
    main()
