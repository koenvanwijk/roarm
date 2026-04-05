#!/usr/bin/env python3
"""Simple WebRTC test - receiver and sender in sequence."""

import numpy as np
import time
import sys
import threading
from lerobot_webrtc import WebRTCSender, WebRTCSenderConfig, WebRTCReceiver, WebRTCReceiverConfig

def run_receiver():
    """Run receiver in thread."""
    print("\n[RECEIVER] 🔧 Starting...")
    config = WebRTCReceiverConfig(signaling_server="localhost:8080")
    receiver = WebRTCReceiver(config)
    receiver.connect()  # Explicitly connect!
    print("[RECEIVER] ✓ Waiting for connection and actions...\n")
    
    received_count = 0
    for i in range(30):
        try:
            action = receiver.get_action()
            if action is not None:
                received_count += 1
                print(f"[RECEIVER] ✅ #{received_count}: {action[:3]}...")
                if received_count >= 5:
                    print(f"[RECEIVER] 🎉 Success! Got {received_count} actions!\n")
                    break
        except Exception as e:
            if "not connected" not in str(e) and i % 5 == 0:
                print(f"[RECEIVER] ⏳ Waiting... ({i}s)")
        time.sleep(1)
    
    if received_count == 0:
        print("[RECEIVER] ❌ No actions received\n")
    
    receiver.disconnect()

def main():
    print("=" * 60)
    print("WebRTC Simple Test")
    print("=" * 60)
    
    # Start receiver in background thread
    receiver_thread = threading.Thread(target=run_receiver, daemon=True)
    receiver_thread.start()
    
    # Wait for receiver to initialize
    time.sleep(3)
    
    # Start sender in main thread
    print("[SENDER] 🔧 Starting...")
    config = WebRTCSenderConfig(signaling_server="localhost:8080")
    sender = WebRTCSender(config)
    sender.connect()  # Explicitly connect!
    print("[SENDER] ✓ Connected\n")
    
    # Wait for WebRTC to establish
    time.sleep(3)
    
    print("[SENDER] 📤 Sending actions...\n")
    for i in range(10):
        action = np.array([i*0.1, -i*0.1, np.sin(i), np.cos(i), i*0.01, -i*0.01], dtype=np.float32)
        try:
            sender.send_action(action)
            print(f"[SENDER] ✓ Sent #{i+1}")
            time.sleep(0.5)
        except Exception as e:
            print(f"[SENDER] ❌ Error: {e}")
    
    print("\n[SENDER] ✓ Done sending\n")
    
    # Give receiver time to get remaining messages
    print("⏳ Waiting for receiver to finish...")
    time.sleep(5)
    
    sender.disconnect()
    receiver_thread.join(timeout=5)
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
