"""
Record demonstrations with Roarm robot using LeRobot's recording tools.

This script shows how to use the LeRobot CLI for recording demonstrations.
It provides different recording modes and configurations.
"""
import subprocess
import sys


def record_with_cli():
    """
    Use LeRobot's CLI to record demonstrations.
    
    This is the recommended way to record data as it handles all the
    dataset management, episode tracking, and video recording.
    """
    
    # Basic recording command
    cmd = [
        "lerobot-record",
        
        # Robot configuration
        "--robot.type=roarm",
        "--robot.roarm_type=roarm_m3",
        "--robot.port=/dev/ttyUSB0",  # or --robot.host=192.168.1.100
        
        # Dataset configuration
        "--repo-id=my-username/roarm_demos",
        "--local-dir=data/roarm_demos",
        
        # Recording parameters
        "--num-episodes=10",
        "--fps=30",
        
        # Camera configuration (optional)
        "--robot.cameras.wrist_cam.index_or_path=0",
        "--robot.cameras.wrist_cam.fps=30",
    ]
    
    print("Starting recording with LeRobot CLI...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Recording failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
        sys.exit(0)


def record_with_teleoperation():
    """
    Record demonstrations using teleoperation.
    
    This uses two Roarm robots: one as leader (teleop) and one as follower.
    """
    
    cmd = [
        "lerobot-record",
        
        # Follower robot (the one being recorded)
        "--robot.type=roarm",
        "--robot.roarm_type=roarm_m3",
        "--robot.port=/dev/ttyUSB1",
        
        # Leader robot (for teleoperation)
        "--teleop.type=roarm",  # You'd need to implement a teleoperator
        "--teleop.roarm_type=roarm_m3",
        "--teleop.port=/dev/ttyUSB0",
        
        # Dataset
        "--repo-id=my-username/roarm_teleop_demos",
        "--local-dir=data/roarm_teleop_demos",
        
        # Recording
        "--num-episodes=20",
        "--fps=30",
    ]
    
    print("Starting teleoperation recording...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Recording failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
        sys.exit(0)


def manual_recording_example():
    """
    Example of manual recording without using the CLI.
    
    This gives you more control but requires more manual work.
    """
    from pathlib import Path
    from lerobot.dataset import LeRobotDataset
    from lerobot_robot_roarm import RoarmConfig, Roarm
    import time
    
    # Configuration
    config = RoarmConfig(
        roarm_type="roarm_m3",
        port="/dev/ttyUSB0",
    )
    
    # Initialize robot
    robot = Roarm(config)
    robot.connect()
    
    # Create dataset
    dataset_dir = Path("data/roarm_manual_demos")
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    print("Manual recording mode")
    print("Press Enter to start recording an episode")
    print("Press Ctrl+C to stop the episode\n")
    
    episode_idx = 0
    
    try:
        while True:
            input(f"Press Enter to start episode {episode_idx}...")
            
            print(f"Recording episode {episode_idx}...")
            episode_data = []
            
            try:
                # Record loop
                while True:
                    # Get observation
                    obs = robot.get_observation()
                    
                    # Here you would:
                    # 1. Get action (from teleop or human demonstration)
                    # 2. Send action to robot
                    # 3. Store (obs, action) pair
                    
                    episode_data.append(obs)
                    
                    time.sleep(0.1)  # 10 Hz
                    
            except KeyboardInterrupt:
                print(f"\nEpisode {episode_idx} stopped. Recorded {len(episode_data)} frames")
                episode_idx += 1
                
                # Save episode data here
                # (This is simplified - use LeRobot's dataset tools in practice)
    
    finally:
        robot.disconnect()


def main():
    """Main function to choose recording mode."""
    
    print("=== Roarm Recording Examples ===\n")
    print("Choose recording mode:")
    print("1. Record with LeRobot CLI (recommended)")
    print("2. Record with teleoperation")
    print("3. Manual recording example")
    print("q. Quit")
    
    choice = input("\nEnter choice (1-3, q): ").strip()
    
    if choice == "1":
        record_with_cli()
    elif choice == "2":
        record_with_teleoperation()
    elif choice == "3":
        manual_recording_example()
    elif choice.lower() == "q":
        print("Exiting")
        sys.exit(0)
    else:
        print("Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    main()
