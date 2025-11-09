#!/usr/bin/env python3
"""
Test smooth Cartesian control by continuously streaming pose commands.

This test demonstrates:
1. Continuous Cartesian trajectory execution
2. Smooth circular or linear motion paths
3. Real-time pose streaming at high frequency

SDK Validation Limits:
- Position: x, y ∈ [-600, 600] mm, z ∈ [0, 600] mm
- Orientation: roll ∈ [-90, 90]°, pitch/yaw ∈ [-180, 180]°

Usage:
    python test_cartesian_smooth.py [port] [trajectory] [duration_sec]
    
Trajectories:
    circle_xy   - Circular motion in XY plane
    circle_xz   - Circular motion in XZ plane (vertical)
    line_x      - Smooth linear motion along X
    line_y      - Smooth linear motion along Y
    line_z      - Smooth vertical motion along Z
    
Example:
    python test_cartesian_smooth.py /dev/ttyUSB0 circle_xy 10
"""

import sys
import time
import math
from roarm_sdk import roarm as RoarmSDK


def smooth_circle_xy(robot, initial_pose, radius_mm=30, duration_sec=10, fps=20):
    """Move in smooth circle in XY plane."""
    print(f"Smooth circular motion (XY plane):")
    print(f"  Radius: {radius_mm}mm, Duration: {duration_sec}s, FPS: {fps}\n")
    
    center_x = initial_pose[0]
    center_y = initial_pose[1]
    
    total_steps = int(duration_sec * fps)
    dt = 1.0 / fps
    
    for i in range(total_steps):
        # Calculate angle (full circle in duration_sec)
        angle = 2 * math.pi * i / total_steps
        
        # Calculate position on circle
        new_pose = initial_pose.copy()
        new_pose[0] = center_x + radius_mm * math.cos(angle)
        new_pose[1] = center_y + radius_mm * math.sin(angle)
        
        # Send command
        robot.pose_ctrl(new_pose)
        
        # Progress indicator
        if i % fps == 0:
            current = robot.pose_get()
            print(f"  t={i/fps:.1f}s: target=[{new_pose[0]:.1f}, {new_pose[1]:.1f}], "
                  f"actual=[{current[0]:.1f}, {current[1]:.1f}]")
        
        time.sleep(dt)


def smooth_circle_xz(robot, initial_pose, radius_mm=30, duration_sec=10, fps=20):
    """Move in smooth circle in XZ plane (vertical)."""
    print(f"Smooth circular motion (XZ plane - vertical):")
    print(f"  Radius: {radius_mm}mm, Duration: {duration_sec}s, FPS: {fps}\n")
    
    center_x = initial_pose[0]
    center_z = initial_pose[2]
    
    # Ensure circle stays above ground
    if center_z - radius_mm < 50:
        center_z = 50 + radius_mm
        print(f"  Adjusted center Z to {center_z}mm to stay above ground\n")
    
    total_steps = int(duration_sec * fps)
    dt = 1.0 / fps
    
    for i in range(total_steps):
        angle = 2 * math.pi * i / total_steps
        
        new_pose = initial_pose.copy()
        new_pose[0] = center_x + radius_mm * math.cos(angle)
        new_pose[2] = center_z + radius_mm * math.sin(angle)
        
        # Clamp Z
        if new_pose[2] < 50.0:
            new_pose[2] = 50.0
        
        robot.pose_ctrl(new_pose)
        
        if i % fps == 0:
            current = robot.pose_get()
            print(f"  t={i/fps:.1f}s: target=[{new_pose[0]:.1f}, {new_pose[2]:.1f}], "
                  f"actual=[{current[0]:.1f}, {current[2]:.1f}]")
        
        time.sleep(dt)


def smooth_line(robot, initial_pose, axis, distance_mm=50, duration_sec=10, fps=20, cycles=1, rotate_with_motion=False, tilt_with_motion=False, led_at_top=False):
    """Smooth linear motion along specified axis."""
    axis_names = {0: 'X', 1: 'Y', 2: 'Z'}
    print(f"Smooth linear motion along {axis_names[axis]}-axis:")
    print(f"  Distance: {distance_mm}mm, Duration: {duration_sec}s, FPS: {fps}, Cycles: {cycles}")
    if rotate_with_motion:
        print(f"  Yaw rotation: synchronized with motion")
    if tilt_with_motion:
        print(f"  Pitch tilt: synchronized with motion")
    if led_at_top:
        print(f"  LED: On when at top position")
    if not rotate_with_motion and not tilt_with_motion:
        print()
    else:
        print()
    
    total_steps = int(duration_sec * fps)
    dt = 1.0 / fps
    
    for i in range(total_steps):
        # Smooth sinusoidal motion (multiple cycles)
        progress = math.sin(2 * math.pi * cycles * i / total_steps)
        offset = distance_mm * progress / 2.0
        
        new_pose = initial_pose.copy()
        new_pose[axis] = initial_pose[axis] + offset
        
        # If rotating with motion, modulate yaw angle
        if rotate_with_motion:
            # Yaw oscillates (rotation around Z-axis)
            # Keep within SDK limits: typically 0-90° for yaw
            yaw_offset = 15.0 * progress  # Small range to stay safe
            new_yaw = initial_pose[5] + yaw_offset
            # Clamp to safe range
            new_pose[5] = max(0.0, min(85.0, new_yaw))
        
        # If tilting with motion, modulate pitch angle
        if tilt_with_motion:
            # Pitch oscillates (tilt up/down)
            # SDK limits: -90 to +90° for pitch
            pitch_offset = 30.0 * progress  # Larger range for dramatic tilt
            new_pitch = initial_pose[4] + pitch_offset
            # Clamp to safe range
            new_pose[4] = max(-85.0, min(85.0, new_pitch))
        
        # Ensure Z stays positive
        if axis == 2 or new_pose[2] < 50.0:
            new_pose[2] = max(50.0, new_pose[2])
        
        # Control LED based on position (only for Z-axis movements)
        if led_at_top and axis == 2:
            # Turn on LED when near top (progress > 0.85), very dim
            if progress > 0.85:
                robot.led_ctrl(25)  # 10% brightness when at top
            else:
                robot.led_ctrl(0)   # Off when not at top
        
        robot.pose_ctrl(new_pose)
        
        if i % fps == 0:
            current = robot.pose_get()
            if rotate_with_motion and tilt_with_motion:
                print(f"  t={i/fps:.1f}s: z={new_pose[axis]:.1f}mm, yaw={new_pose[5]:.1f}°, pitch={new_pose[4]:.1f}°")
            elif rotate_with_motion:
                print(f"  t={i/fps:.1f}s: target={new_pose[axis]:.1f}mm, yaw={new_pose[5]:.1f}°, "
                      f"actual={current[axis]:.1f}mm, yaw={current[5]:.1f}°")
            elif tilt_with_motion:
                print(f"  t={i/fps:.1f}s: target={new_pose[axis]:.1f}mm, pitch={new_pose[4]:.1f}°, "
                      f"actual={current[axis]:.1f}mm, pitch={current[4]:.1f}°")
            else:
                print(f"  t={i/fps:.1f}s: target={new_pose[axis]:.1f}mm, "
                      f"actual={current[axis]:.1f}mm, error={abs(current[axis]-new_pose[axis]):.1f}mm")
        
        time.sleep(dt)


def main():
    # Parse arguments
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    trajectory = sys.argv[2] if len(sys.argv) > 2 else "circle_xy"
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    
    print(f"Usage: {sys.argv[0]} [port] [trajectory] [duration_sec]")
    print(f"Running with: port={port}, trajectory={trajectory}, duration={duration}s\n")
    
    print("=== Roarm Smooth Cartesian Motion Test ===\n")
    
    # Connect to robot
    print(f"Connecting to Roarm on {port}...")
    robot = RoarmSDK(roarm_type='roarm_m3', port=port)
    time.sleep(0.5)
    
    try:
        # Get initial pose
        initial_pose = robot.pose_get()
        print(f"Initial pose: {initial_pose}")
        print(f"  Position (mm): x={initial_pose[0]:.1f}, y={initial_pose[1]:.1f}, z={initial_pose[2]:.1f}")
        print(f"  Orientation (deg): roll={initial_pose[3]:.1f}, pitch={initial_pose[4]:.1f}, yaw={initial_pose[5]:.1f}\n")
        
        # Move to safe starting position
        print("Moving to safe starting position (250mm height)...\n")
        safe_pose = [
            150.0,  # x: 150mm in front
            0.0,    # y: centered
            250.0,  # z: 250mm above base (high enough for large movements)
            0.0,    # roll: horizontal
            0.0,    # pitch
            0.0     # yaw
        ]
        robot.pose_ctrl(safe_pose)
        time.sleep(2.0)
        initial_pose = robot.pose_get()
        print(f"Starting pose: {initial_pose}")
        print(f"  Position (mm): x={initial_pose[0]:.1f}, y={initial_pose[1]:.1f}, z={initial_pose[2]:.1f}\n")
        
        # Clamp orientation to SDK limits
        initial_pose[3] = max(-85.0, min(85.0, initial_pose[3]))
        initial_pose[4] = max(-85.0, min(85.0, initial_pose[4]))
        initial_pose[5] = max(-85.0, min(85.0, initial_pose[5]))
        
        # Execute trajectory
        start_time = time.time()
        
        if trajectory == "circle_xy":
            smooth_circle_xy(robot, initial_pose, radius_mm=30, duration_sec=duration, fps=20)
        elif trajectory == "circle_xz":
            smooth_circle_xz(robot, initial_pose, radius_mm=30, duration_sec=duration, fps=20)
        elif trajectory == "line_x":
            smooth_line(robot, initial_pose, axis=0, distance_mm=150, duration_sec=duration, fps=30, cycles=3, rotate_with_motion=False, tilt_with_motion=False, led_at_top=False)
        elif trajectory == "line_y":
            smooth_line(robot, initial_pose, axis=1, distance_mm=150, duration_sec=duration, fps=30, cycles=3, rotate_with_motion=False, tilt_with_motion=False, led_at_top=False)
        elif trajectory == "line_z":
            smooth_line(robot, initial_pose, axis=2, distance_mm=240, duration_sec=duration, fps=30, cycles=3, rotate_with_motion=True, tilt_with_motion=True, led_at_top=True)
        else:
            print(f"Unknown trajectory: {trajectory}")
            print("Available: circle_xy, circle_xz, line_x, line_y, line_z")
            return
        
        elapsed = time.time() - start_time
        print(f"\nTrajectory completed in {elapsed:.2f}s")
        
        # Make sure LED is off at end
        robot.led_ctrl(0)
        
        # Check final position
        time.sleep(0.5)
        final_pose = robot.pose_get()
        print(f"\nFinal pose: {final_pose}")
        
        position_error = [
            abs(final_pose[0] - initial_pose[0]),
            abs(final_pose[1] - initial_pose[1]),
            abs(final_pose[2] - initial_pose[2])
        ]
        print(f"Position error (mm): x={position_error[0]:.2f}, y={position_error[1]:.2f}, z={position_error[2]:.2f}")
        
        total_error = math.sqrt(sum(e**2 for e in position_error))
        print(f"Total position error: {total_error:.2f}mm")
        
        if total_error < 15.0:
            print("✓ Test PASSED - Smooth motion completed successfully")
        else:
            print(f"✗ Test FAILED - Position error: {total_error:.2f}mm")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
