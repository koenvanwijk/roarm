#!/usr/bin/env python3
"""Debug WebRTC connection."""

import requests
import time

# Check signaling server
try:
    resp = requests.get("http://localhost:8080/status", timeout=2)
    print(f"✓ Signaling server status: {resp.json()}")
except Exception as e:
    print(f"❌ Signaling server not reachable: {e}")
    exit(1)

print("\nTesting WebRTC flow...")
print("=" * 60)

# Simulate sender offering
print("\n1. Sender posts offer...")
offer_data = {
    "peer_id": "sender",
    "offer": {
        "type": "offer",
        "sdp": "v=0\r\no=- 123 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n"
    }
}

import threading

def wait_for_answer():
    time.sleep(2)
    try:
        resp = requests.post("http://localhost:8080/offer", json=offer_data, timeout=35)
        if resp.status_code == 200:
            print(f"   ✓ Sender received answer: {resp.json().get('type')}")
        else:
            print(f"   ❌ Sender failed: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Sender error: {e}")

# Start sender in background
sender_thread = threading.Thread(target=wait_for_answer, daemon=True)
sender_thread.start()

print("2. Receiver requests offer...")
time.sleep(4)  # Give sender time to post

answer_data = {
    "peer_id": "receiver",
    "answer": {
        "type": "answer",
        "sdp": "v=0\r\no=- 456 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n"
    }
}

try:
    resp = requests.post("http://localhost:8080/answer", json=answer_data, timeout=35)
    if resp.status_code == 200:
        print(f"   ✓ Receiver got offer: {resp.json().get('type')}")
    else:
        print(f"   ❌ Receiver failed: {resp.status_code}")
except Exception as e:
    print(f"   ❌ Receiver error: {e}")

sender_thread.join(timeout=5)

print("\n" + "=" * 60)
print("✓ Signaling flow test complete!")
