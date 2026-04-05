#!/usr/bin/env python3
"""
Test smooth circular motion on TWO robots simultaneously on table surface.

Usage:
    python test_table_circle_dual.py [port1] [port2] [duration_sec] [radius_mm]

Example:
    python test_table_circle_dual.py /dev/ttyUSB0 /dev/ttyUSB1 10 80
"""

import sys
import time
import numpy as np
from roarm_sdk import roarm as RoarmSDK
from threading import Thread


def circular_table_motion(robot, robot_id, center_x, center_y, z_height, radius, duration_sec=20, fps=30):
    """
    Execute smooth circular motion on table surface.
    
    Args:
        robot: RoarmSDK instance
        robot_id: Robot identifier for logging
        center_x: Circle center X coordinate (mm)
        center_y: Circle center Y coordinate (mm)
        z_height: Constant Z height (mm)
        radius: Circle radius (mm)
        duration_sec: Duration of motion (seconds)
        fps: Control frequency (Hz)
    """
    total_steps = int(duration_sec * fps)
    dt = 1.0 / fps
    
    print(f"[{robot_id}] 🔵 Starting circular motion")
    
    # LED on for motion
    robot.led_ctrl(1)
    
    for i in range(total_steps):
        # Calculate angle (full circle over duration)
        angle = 2 * np.pi * (i / total_steps)
        
        # Calculate position on circle
        x = center_x + radius * np.cos(angle)
        y = center_y + radius * np.sin(angle)
        
        # Create pose: [x, y, z, roll, pitch, yaw]
        pose = [
            x,          # X position
            y,          # Y position
            z_height,   # Z height (constant)
            90.0,       # Roll (gripper pointing down)
            0.0,        # Pitch
            0.0         # Yaw
        ]
        
        # Send command
        robot.pose_ctrl(pose)
        
        # Log progress every 2 seconds
        if i % (fps * 2) == 0:
            progress = (i / total_steps) * 100
            angle_deg = np.degrees(angle)
            print(f"[{robot_id}] t={i/fps:.1f}s ({progress:.0f}%): x={x:.1f}, y={y:.1f}, angle={angle_deg:.0f}°")
        
        time.sleep(dt)
    
    # LED off
    robot.led_ctrl(0)
    print(f"[{robot_id}] ✅ Circular motion complete!")


def main():
    # Parse arguments
    port1 = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    port2 = sys.argv[2] if len(sys.argv) > 2 else "/dev/ttyUSB1"
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    radius = float(sys.argv[4]) if len(sys.argv) > 4 else 80.0
    
    print(f"Usage: {sys.argv[0]} [port1] [port2] [duration_sec] [radius_mm]")
    print(f"Running with: port1={port1}, port2={port2}, duration={duration}s, radius={radius}mm\n")
    
    print("=== Roarm DUAL Table Circular Motion Test ===\n")
    
    # Connect to both robots
    print(f"Connecting to Robot 1 on {port1}...")
    robot1 = RoarmSDK(roarm_type='roarm_m3', port=port1)
    time.sleep(0.5)
    
    print(f"Connecting to Robot 2 on {port2}...")
    robot2 = RoarmSDK(roarm_type='roarm_m3', port=port2)
    time.sleep(0.5)
    
    try:
        # Get current poses
        print("\n[Robot 1] Current pose:")
        pose1 = robot1.pose_get()
        print(f"  Position: x={pose1[0]:.1f}, y={pose1[1]:.1f}, z={pose1[2]:.1f}")
        
        print("\n[Robot 2] Current pose:")
        pose2 = robot2.pose_get()
        print(f"  Position: x={pose2[0]:.1f}, y={pose2[1]:.1f}, z={pose2[2]:.1f}")
        
        # Circle parameters
        z_height = -80.0  # Working height
        x_min = 100.0
        x_max = 340.0
        center_x = (x_min + x_max) / 2.0  # 220 mm
        center_y = 0.0  # Center Y around 0.0
        
        print(f"\n🎯 Circle parameters:")
        print(f"   Center: ({center_x:.1f}, {center_y:.1f}) mm")
        print(f"   Radius: {radius:.1f} mm")
        print(f"   Height: {z_height:.1f} mm")
        
        # Verify radius fits in workspace
        if center_x - radius < x_min or center_x + radius > x_max:
            print(f"\n⚠️  Warning: Radius {radius}mm may exceed X limits [{x_min}, {x_max}]")
            max_radius = (x_max - x_min) / 2.0
            print(f"   Maximum safe radius: {max_radius:.1f}mm")
            radius = max_radius
        
        # Move both robots to starting position (right side of circle)
        print(f"\n📍 Moving both robots to start position...")
        start_pose = [
            center_x + radius,  # X (right side)
            center_y,           # Y (center)
            z_height,           # Z (table height)
            90.0,               # Roll
            0.0,                # Pitch
            0.0                 # Yaw
        ]
        
        robot1.pose_ctrl(start_pose)
        robot2.pose_ctrl(start_pose)
        time.sleep(2.0)
        print(f"   Both at: x={start_pose[0]:.1f}, y={start_pose[1]:.1f}, z={start_pose[2]:.1f}")
        
        # Execute circular motion on both robots simultaneously
        input("\n▶️  Press Enter to start DUAL circular motion...")
        
        print("\n🚀 Starting synchronized circular motion...\n")
        
        # Create threads for both robots
        thread1 = Thread(
            target=circular_table_motion,
            args=(robot1, "Robot 1", center_x, center_y, z_height, radius, duration, 30)
        )
        thread2 = Thread(
            target=circular_table_motion,
            args=(robot2, "Robot 2", center_x, center_y, z_height, radius, duration, 30)
        )
        
        # Start both threads
        thread1.start()
        thread2.start()
        
        # Wait for both to complete
        thread1.join()
        thread2.join()
        
        # Return both to start
        print("\n🔙 Returning both robots to start position...")
        robot1.pose_ctrl(start_pose)
        robot2.pose_ctrl(start_pose)
        time.sleep(1.0)
        
        print("\n✅ Dual test complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        robot1.led_ctrl(0)
        robot2.led_ctrl(0)
        print("Disconnecting...")


if __name__ == "__main__":
    main()
