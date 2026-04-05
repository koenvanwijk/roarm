#!/usr/bin/env python3
"""
Test smooth circular motion on table surface.

Current position: x=340.5, y=-28.8, z=-131.4, roll=90°, pitch=-0.0°, yaw=0.0°
Constraints:
- x: 100 to 340 mm
- y: assumes circular reach
- z: constant (table height)
- orientation: constant (roll=90°, pitch=0°, yaw=0°)

Usage:
    python test_table_circle.py [port] [duration_sec] [radius_mm]

Example:
    python test_table_circle.py /dev/ttyUSB0 20 120
"""

import sys
import time
import numpy as np
from roarm_sdk import roarm as RoarmSDK


def circular_table_motion(robot, center_x, center_y, z_height, radius, duration_sec=20, fps=30):
    """
    Execute smooth circular motion on table surface.
    
    Args:
        robot: RoarmSDK instance
        center_x: Circle center X coordinate (mm)
        center_y: Circle center Y coordinate (mm)
        z_height: Constant Z height (mm)
        radius: Circle radius (mm)
        duration_sec: Duration of motion (seconds)
        fps: Control frequency (Hz)
    """
    total_steps = int(duration_sec * fps)
    dt = 1.0 / fps
    
    print(f"\n🔵 Starting circular motion:")
    print(f"   Center: ({center_x:.1f}, {center_y:.1f}) mm")
    print(f"   Radius: {radius:.1f} mm")
    print(f"   Height: {z_height:.1f} mm")
    print(f"   Duration: {duration_sec}s at {fps} Hz")
    print(f"   Total steps: {total_steps}\n")
    
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
        
        # Log progress every second
        if i % fps == 0:
            progress = (i / total_steps) * 100
            angle_deg = np.degrees(angle)
            print(f"  t={i/fps:.1f}s ({progress:.0f}%): x={x:.1f}, y={y:.1f}, angle={angle_deg:.0f}°")
        
        time.sleep(dt)
    
    # LED off
    robot.led_ctrl(0)
    print(f"\n✅ Circular motion complete!")


def main():
    # Parse arguments
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
    radius = float(sys.argv[3]) if len(sys.argv) > 3 else 120.0
    
    print(f"Usage: {sys.argv[0]} [port] [duration_sec] [radius_mm]")
    print(f"Running with: port={port}, duration={duration}s, radius={radius}mm\n")
    
    print("=== Roarm Table Circular Motion Test ===\n")
    
    # Connect to robot
    print(f"Connecting to robot on {port}...")
    robot = RoarmSDK(roarm_type='roarm_m3', port=port)
    time.sleep(0.5)
    
    try:
        # Get current pose
        print("\nCurrent pose:")
        current_pose = robot.pose_get()
        print(f"  Position: x={current_pose[0]:.1f}, y={current_pose[1]:.1f}, z={current_pose[2]:.1f}")
        print(f"  Orientation: roll={current_pose[3]:.1f}°, pitch={current_pose[4]:.1f}°, yaw={current_pose[5]:.1f}°")
        
        z_height = -80.0  # Working height - corresponds to ~-120mm from base
        print(f"  Using working height: {z_height}mm")
        
        # Calculate circle center (midpoint between x limits)
        x_min = 100.0
        x_max = 340.0
        center_x = (x_min + x_max) / 2.0  # 220 mm
        center_y = 0.0  # Center Y around 0.0
        
        # Verify radius fits in workspace
        if center_x - radius < x_min or center_x + radius > x_max:
            print(f"\n⚠️  Warning: Radius {radius}mm may exceed X limits [{x_min}, {x_max}]")
            max_radius = (x_max - x_min) / 2.0
            print(f"   Maximum safe radius: {max_radius:.1f}mm")
            
            # Ask user to confirm or adjust
            response = input(f"   Use maximum safe radius {max_radius:.1f}mm? (y/n): ")
            if response.lower() == 'y':
                radius = max_radius
            else:
                print("   Aborting.")
                return
        
        # Move to starting position (right side of circle)
        print(f"\n📍 Moving to start position...")
        start_pose = [
            center_x + radius,  # X (right side)
            center_y,           # Y (center)
            z_height,           # Z (table height)
            90.0,               # Roll
            0.0,                # Pitch
            0.0                 # Yaw
        ]
        print(f"   Start pose: {start_pose}")
        robot.pose_ctrl(start_pose)
        time.sleep(2.0)
        print(f"   At: x={start_pose[0]:.1f}, y={start_pose[1]:.1f}, z={start_pose[2]:.1f}")
        
        # Execute circular motion
        input("\n▶️  Press Enter to start circular motion...")
        circular_table_motion(robot, center_x, center_y, z_height, radius, duration, fps=30)
        
        # Return to start
        print("\n🔙 Returning to start position...")
        robot.pose_ctrl(start_pose)
        time.sleep(1.0)
        
        print("\n✅ Test complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        robot.led_ctrl(0)
        print("Disconnecting...")


if __name__ == "__main__":
    main()
