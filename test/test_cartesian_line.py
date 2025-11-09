#!/usr/bin/env python3
"""
Test Cartesian control by moving the end-effector in a straight line along the Z-axis.

This test demonstrates:
1. Reading current end-effector pose using pose_get()
2. Commanding Cartesian targets using pose_ctrl()
3. Verifying position accuracy
4. SDK validation constraints

SDK Validation Limits (discovered through testing):
- Position: x, y ∈ [-600, 600] mm, z ∈ [0, 600] mm
- Orientation: roll ∈ [-90, 90]°, pitch/yaw ∈ [-180, 180]°

Observed Accuracy:
- X-axis: 10-20mm errors, better at lower Z (200-300mm)
- Y-axis: Needs higher Z (>190mm) for workspace freedom, excellent return accuracy
- Z-axis: Vertical movement, testing now...
- Likely due to: mechanical backlash, IK convergence, servo resolution
- Suitable for coarse positioning, not precision tasks

Usage:
    python test_cartesian_line.py [port] [distance_mm] [steps]
    
Example:
    python test_cartesian_line.py /dev/ttyUSB0 50 10
"""
import time
from roarm_sdk import roarm as RoarmSDK


def test_x_axis_line(port='/dev/ttyUSB0', distance_mm=50, steps=10, speed_mm_per_sec=20):
    """
    Move the end-effector in a straight line along X-axis.
    
    Args:
        port: Serial port for the robot
        distance_mm: Total distance to move in mm
        steps: Number of steps for the movement
        speed_mm_per_sec: Movement speed
    """
    print("=== Roarm Cartesian Line Test ===\n")
    
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
        
        # Move to low, safe starting position for testing
        print("Moving to low starting position (250mm height)...\n")
        safe_pose = [
            150.0,  # x: 150mm in front (closer to base)
            0.0,    # y: centered
            250.0,  # z: 250mm above base (good for Y-axis movement)
            0.0,    # roll: horizontal (SDK limit: -90 to +90)
            0.0,    # pitch
            0.0     # yaw
        ]
        robot.pose_ctrl(safe_pose)
        time.sleep(2.0)
        initial_pose = robot.pose_get()
        print(f"New starting pose: {initial_pose}")
        print(f"  Position (mm): x={initial_pose[0]:.1f}, y={initial_pose[1]:.1f}, z={initial_pose[2]:.1f}\n")
        
        # Clamp orientation to SDK limits
        initial_pose[3] = max(-85.0, min(85.0, initial_pose[3]))  # roll: -90 to +90
        initial_pose[4] = max(-85.0, min(85.0, initial_pose[4]))  # pitch: -90 to +90
        initial_pose[5] = max(-85.0, min(85.0, initial_pose[5]))  # yaw: -90 to +90
        
        # Calculate step size
        step_size = distance_mm / steps
        delay = step_size / speed_mm_per_sec
        
        print(f"Moving {distance_mm}mm along Z-axis in {steps} steps...")
        print(f"Step size: {step_size:.1f}mm, delay: {delay:.2f}s\n")
        
        # Move upward along Z-axis
        print("Upward movement:")
        for i in range(steps + 1):
            # Create new pose with only Z changed
            new_pose = initial_pose.copy()
            new_pose[2] = initial_pose[2] + (i * step_size)
            
            # Ensure Z is always positive (SDK requirement)
            if new_pose[2] < 50.0:
                new_pose[2] = 50.0
            
            # Send pose command
            print(f"  Step {i}/{steps}: z={new_pose[2]:.1f}mm", end='')
            robot.pose_ctrl(new_pose)
            time.sleep(delay)
            
            # Verify position
            current = robot.pose_get()
            error = abs(current[2] - new_pose[2])
            print(f" -> actual z={current[2]:.1f}mm (error: {error:.1f}mm)")
        
        time.sleep(1.0)
        
        # Move back down to initial position
        print("\nDownward movement (returning to start):")
        for i in range(steps, -1, -1):
            new_pose = initial_pose.copy()
            new_pose[2] = initial_pose[2] + (i * step_size)
            
            # Ensure Z is always positive (SDK requirement)
            if new_pose[2] < 50.0:
                new_pose[2] = 50.0
            
            print(f"  Step {steps-i}/{steps}: z={new_pose[2]:.1f}mm", end='')
            robot.pose_ctrl(new_pose)
            time.sleep(delay)
            
            current = robot.pose_get()
            error = abs(current[2] - new_pose[2])
            print(f" -> actual z={current[2]:.1f}mm (error: {error:.1f}mm)")
        
        # Final position check
        time.sleep(0.5)
        final_pose = robot.pose_get()
        print(f"\nFinal pose: {final_pose}")
        
        # Calculate total error
        position_error = [
            abs(final_pose[0] - initial_pose[0]),
            abs(final_pose[1] - initial_pose[1]),
            abs(final_pose[2] - initial_pose[2])
        ]
        print(f"\nPosition error (mm): x={position_error[0]:.2f}, y={position_error[1]:.2f}, z={position_error[2]:.2f}")
        
        if position_error[2] < 5.0:  # Less than 5mm error in Z
            print("✓ Test PASSED - Robot returned to initial position within tolerance")
        else:
            print(f"✗ Test FAILED - Position error too large: {position_error[2]:.2f}mm")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect
        robot.disconnect()
        print("\n=== Test Complete ===")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyUSB0'
    distance = float(sys.argv[2]) if len(sys.argv) > 2 else 50.0
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    print(f"Usage: {sys.argv[0]} [port] [distance_mm] [steps]")
    print(f"Running with: port={port}, distance={distance}mm, steps={steps}\n")
    
    test_x_axis_line(port=port, distance_mm=distance, steps=steps)
