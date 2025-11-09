"""
Basic control example for Roarm robot with LeRobot.

This script demonstrates how to:
1. Initialize and connect to the robot
2. Read observations (joint positions)
3. Send actions (joint commands in percentage format -100 to +100)
4. Disconnect safely

Note: Actions use percentage format (-100 to +100) which maps to the full range
of each joint. This matches LeRobot's convention of using motor-native units.
"""
import time

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
            if ".pos" in key and "cam" not in key:
                print(f"{key}: {value:.2f}%")
        
        # Move to home position (center position = 0%)
        # Values are percentages: -100 (min) to +100 (max) for each joint
        print("\n=== Moving to Home ===")
        home_action = {
            "shoulder_pan.pos": 0.0,     # Center
            "shoulder_lift.pos": 0.0,    # Center
            "elbow_flex.pos": 38.5,      # ~180° (upper part of range)
            "wrist_flex.pos": 0.0,       # Center
            "wrist_roll.pos": 0.0,       # Center
            "gripper.pos": 0.0,          # Center
        }
        robot.send_action(home_action)
        time.sleep(3.0)
        
        # Open gripper
        print("\n=== Opening Gripper ===")
        open_gripper_action = home_action.copy()
        open_gripper_action["gripper.pos"] = 50.0  # Open position
        robot.send_action(open_gripper_action)
        time.sleep(2.0)
        
        # Close gripper
        print("\n=== Closing Gripper ===")
        close_gripper_action = home_action.copy()
        close_gripper_action["gripper.pos"] = -50.0  # Closed position
        robot.send_action(close_gripper_action)
        time.sleep(2.0)
        
        # Move joints in sequence
        print("\n=== Moving Joints ===")
        joint_names = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
        for joint_name in joint_names:
            print(f"Moving {joint_name}...")
            action = home_action.copy()
            action[f"{joint_name}.pos"] = 30.0  # Move to +30%
            robot.send_action(action)
            time.sleep(2.0)
            
            # Return to home
            robot.send_action(home_action)
            time.sleep(2.0)
        
        # Read final observation
        print("\n=== Final State ===")
        final_obs = robot.get_observation()
        for key, value in final_obs.items():
            if ".pos" in key and "cam" not in key:
                print(f"{key}: {value:.2f}%")
        
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
