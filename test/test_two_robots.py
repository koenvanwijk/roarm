#!/usr/bin/env python3
"""
Quick test to verify we can connect to both Roarm robots.
"""
from lerobot_robot_roarm import RoarmConfig, Roarm

print("Testing connection to both robots...\n")

# Leader robot (ttyUSB0) - disable cameras for this test
print("1. Connecting to Leader (ttyUSB0)...")
leader_config = RoarmConfig(
    roarm_type="roarm_m3",
    port="/dev/ttyUSB0",
    cameras={},  # Disable cameras for teleoperation test
)
leader = Roarm(leader_config)
leader.connect(calibrate=False)
print("✓ Leader connected")

# Get leader position
leader_obs = leader.get_observation()
print("Leader joints:")
for key, value in leader_obs.items():
    if ".pos" in key:
        print(f"  {key}: {value:.3f}")

# Follower robot (ttyUSB1) - disable cameras for this test
print("\n2. Connecting to Follower (ttyUSB1)...")
follower_config = RoarmConfig(
    roarm_type="roarm_m3",
    port="/dev/ttyUSB1",
    cameras={},  # Disable cameras for teleoperation test
)
follower = Roarm(follower_config)
follower.connect(calibrate=False)
print("✓ Follower connected")

# Get follower position
follower_obs = follower.get_observation()
print("Follower joints:")
for key, value in follower_obs.items():
    if ".pos" in key:
        print(f"  {key}: {value:.3f}")

print("\n✓ Both robots connected successfully!")

# Cleanup
leader.disconnect()
follower.disconnect()
print("✓ Disconnected")
