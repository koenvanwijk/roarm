"""
Basic control example for Roarm robot with LeRobot.

This script demonstrates how to:
1. Initialize and connect to the robot
2. Read observations (joint positions, camera)
3. Send actions (joint commands)
4. Disconnect safely
"""
import time
import numpy as np

from lerobot_robot_roarm import RoarmConfig, Roarm


def main():
    # Configuration
    # Option 1: Serial connection
    config = RoarmConfig(
        roarm_type="roarm_m3",
        port="/dev/ttyUSB0",
        baudrate=115200,
    )
    
    # Option 2: WiFi connection (uncomment to use)
    # config = RoarmConfig(
    #     roarm_type="roarm_m3",
    #     host="192.168.1.100",
    # )
    
    # Initialize robot
    print("Initializing Roarm robot...")
    robot = Roarm(config)
    
    try:
        # Connect to robot
        print("Connecting to robot...")
        robot.connect(calibrate=True)
        
        # Give robot time to stabilize
        time.sleep(1.0)
        
        # Read current observation
        print("\n=== Current State ===")
        obs = robot.get_observation()
        for key, value in obs.items():
            if ".pos" in key:
                print(f"{key}: {value:.3f} rad ({np.rad2deg(value):.1f}°)")
        
        # Move to home position
        print("\n=== Moving to Home ===")
        home_action = {
            "joint_1.pos": 0.0,
            "joint_2.pos": 0.0,
            "joint_3.pos": np.deg2rad(180),  # Elbow up
            "joint_4.pos": -np.deg2rad(90),  # Wrist down
            "joint_5.pos": 0.0,
            "joint_6.pos": 0.0,
            "gripper.pos": 0.0,
        }
        robot.send_action(home_action)
        time.sleep(3.0)
        
        # Open gripper
        print("\n=== Opening Gripper ===")
        open_gripper_action = home_action.copy()
        open_gripper_action["gripper.pos"] = np.deg2rad(60)
        robot.send_action(open_gripper_action)
        time.sleep(2.0)
        
        # Close gripper
        print("\n=== Closing Gripper ===")
        close_gripper_action = home_action.copy()
        close_gripper_action["gripper.pos"] = 0.0
        robot.send_action(close_gripper_action)
        time.sleep(2.0)
        
        # Move joints in sequence
        print("\n=== Moving Joints ===")
        for i in range(1, 7):
            print(f"Moving joint_{i}...")
            action = home_action.copy()
            action[f"joint_{i}.pos"] = np.deg2rad(30)
            robot.send_action(action)
            time.sleep(2.0)
            
            # Return to home
            robot.send_action(home_action)
            time.sleep(2.0)
        
        # Read final observation
        print("\n=== Final State ===")
        final_obs = robot.get_observation()
        for key, value in final_obs.items():
            if ".pos" in key:
                print(f"{key}: {value:.3f} rad ({np.rad2deg(value):.1f}°)")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always disconnect
        print("\n=== Disconnecting ===")
        robot.disconnect()
        print("Done!")


if __name__ == "__main__":
    main()
