#!/usr/bin/env python3
"""
Test smooth Cartesian control on TWO robots simultaneously!

This demonstrates synchronized choreography with dual arm coordination.

Usage:
    python test_cartesian_dual.py [port1] [port2] [duration_sec]
    
Example:
    python test_cartesian_dual.py /dev/ttyUSB0 /dev/ttyUSB1 10
"""

import sys
import time
import math
import threading
from roarm_sdk import roarm as RoarmSDK


def smooth_dual_motion(robot, robot_id, initial_pose, duration_sec=10, fps=30, cycles=3, invert_z=False):
    """
    Smooth vertical motion with yaw, pitch and LED synchronized.
    
    Args:
        robot: Robot instance
        robot_id: "Robot 1" or "Robot 2" for logging
        initial_pose: Starting pose
        duration_sec: Total duration
        fps: Frames per second
        cycles: Number of up/down cycles
        invert_z: If True, invert Z motion (up becomes down)
    """
    distance_mm = 180  # Reduced from 240 to avoid going too low
    total_steps = int(duration_sec * fps)
    dt = 1.0 / fps
    
    print(f"{robot_id} starting motion (Z inverted: {invert_z})")
    
    for i in range(total_steps):
        # Calculate progress
        angle = 2 * math.pi * cycles * i / total_steps
        progress = math.sin(angle)
        
        # Invert Z motion if requested
        z_progress = -progress if invert_z else progress
        z_offset = distance_mm * z_progress / 2.0
        
        new_pose = initial_pose.copy()
        new_pose[2] = initial_pose[2] + z_offset
        
        # Yaw and pitch are NOT inverted - they stay synchronized
        yaw_offset = 15.0 * progress
        new_yaw = initial_pose[5] + yaw_offset
        new_pose[5] = max(0.0, min(85.0, new_yaw))
        
        pitch_offset = 30.0 * progress
        new_pitch = initial_pose[4] + pitch_offset
        new_pose[4] = max(-85.0, min(85.0, new_pitch))
        
        # Ensure Z stays positive
        new_pose[2] = max(50.0, new_pose[2])
        
        # LED control - on when near top (based on original progress, not inverted)
        if progress > 0.85:
            robot.led_ctrl(25)  # 10% brightness
        else:
            robot.led_ctrl(0)
        
        # Send command
        robot.pose_ctrl(new_pose)
        
        # Progress logging (only log every second)
        if i % fps == 0:
            print(f"  {robot_id} t={i/fps:.1f}s: z={new_pose[2]:.1f}mm, yaw={new_pose[5]:.1f}°, pitch={new_pose[4]:.1f}°")
        
        time.sleep(dt)
    
    # Turn off LED
    robot.led_ctrl(0)
    print(f"{robot_id} motion complete!")


def main():
    # Parse arguments
    port1 = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    port2 = sys.argv[2] if len(sys.argv) > 2 else "/dev/ttyUSB1"
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    
    print(f"Usage: {sys.argv[0]} [port1] [port2] [duration_sec]")
    print(f"Running with: port1={port1}, port2={port2}, duration={duration}s\n")
    
    print("=== Roarm DUAL Smooth Cartesian Motion Test ===\n")
    
    # Connect to both robots
    print(f"Connecting to Robot 1 on {port1}...")
    robot1 = RoarmSDK(roarm_type='roarm_m3', port=port1)
    time.sleep(0.5)
    
    print(f"Connecting to Robot 2 on {port2}...")
    robot2 = RoarmSDK(roarm_type='roarm_m3', port=port2)
    time.sleep(0.5)
    
    try:
        # Get initial poses
        print("\nRobot 1 initial pose:")
        pose1 = robot1.pose_get()
        print(f"  Position: x={pose1[0]:.1f}, y={pose1[1]:.1f}, z={pose1[2]:.1f}")
        
        print("\nRobot 2 initial pose:")
        pose2 = robot2.pose_get()
        print(f"  Position: x={pose2[0]:.1f}, y={pose2[1]:.1f}, z={pose2[2]:.1f}")
        
        # Move both to safe starting positions
        print("\nMoving both robots to starting positions...")
        safe_pose = [
            150.0,  # x
            0.0,    # y
            220.0,  # z - higher starting height to avoid going too low
            0.0,    # roll
            0.0,    # pitch
            0.0     # yaw
        ]
        
        robot1.pose_ctrl(safe_pose)
        robot2.pose_ctrl(safe_pose)
        time.sleep(2.0)
        
        # Use the same safe_pose as starting position for both robots
        # This ensures they start at exactly the same height
        start_pose1 = safe_pose.copy()
        start_pose2 = safe_pose.copy()
        
        # Verify actual positions
        actual1 = robot1.pose_get()
        actual2 = robot2.pose_get()
        
        print(f"\nRobot 1 commanded z={start_pose1[2]:.1f}mm, actual z={actual1[2]:.1f}mm")
        print(f"Robot 2 commanded z={start_pose2[2]:.1f}mm, actual z={actual2[2]:.1f}mm")
        
        # Create threads for simultaneous control
        print("\n=== Starting synchronized choreography ===\n")
        
        # Robot 1: normal Z motion
        # Robot 2: inverted Z motion (mirrored on vertical axis)
        thread1 = threading.Thread(
            target=smooth_dual_motion,
            args=(robot1, "Robot 1", start_pose1, duration, 30, 3, False)
        )
        
        thread2 = threading.Thread(
            target=smooth_dual_motion,
            args=(robot2, "Robot 2", start_pose2, duration, 30, 3, True)
        )
        
        # Start both threads
        start_time = time.time()
        thread1.start()
        thread2.start()
        
        # Wait for both to complete
        thread1.join()
        thread2.join()
        
        elapsed = time.time() - start_time
        print(f"\n=== Choreography completed in {elapsed:.2f}s ===\n")
        
        # Check final positions
        final1 = robot1.pose_get()
        final2 = robot2.pose_get()
        
        error1 = math.sqrt(
            (final1[0] - start_pose1[0])**2 +
            (final1[1] - start_pose1[1])**2 +
            (final1[2] - start_pose1[2])**2
        )
        
        error2 = math.sqrt(
            (final2[0] - start_pose2[0])**2 +
            (final2[1] - start_pose2[1])**2 +
            (final2[2] - start_pose2[2])**2
        )
        
        print(f"Robot 1 position error: {error1:.2f}mm")
        print(f"Robot 2 position error: {error2:.2f}mm")
        
        if error1 < 25.0 and error2 < 25.0:
            print("✓ DUAL choreography SUCCESSFUL!")
        else:
            print("✗ One or both robots had large position errors")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
