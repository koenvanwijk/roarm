"""
Run a trained policy on the Roarm robot.

This script demonstrates how to run inference with a trained policy on the real robot.
"""
import subprocess
import sys
from pathlib import Path


def run_policy_cli():
    """
    Run a trained policy using LeRobot's control_robot script.
    
    This is the recommended way to run inference.
    """
    
    # Get checkpoint path
    checkpoint = input("Enter checkpoint path (e.g., outputs/roarm_act/checkpoint-epoch-1000): ").strip()
    
    if not Path(checkpoint).exists():
        print(f"Checkpoint not found: {checkpoint}")
        sys.exit(1)
    
    cmd = [
        "python", "-m", "lerobot.scripts.control_robot",
        
        # Robot configuration
        "--robot.type=roarm",
        "--robot.roarm_type=roarm_m3",
        "--robot.port=/dev/ttyUSB0",  # or --robot.host=192.168.1.100
        
        # Policy checkpoint
        f"--policy-checkpoint={checkpoint}",
        
        # Control parameters
        "--fps=30",
        "--num-rollouts=10",  # Number of episodes to run
        
        # Safety
        "--max-duration=30",  # Max episode duration in seconds
        
        # Recording (optional)
        "--record",
        "--record-dir=rollouts/roarm_act",
    ]
    
    print("\n=== Running Policy ===")
    print(f"Checkpoint: {checkpoint}")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Policy execution completed!")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Execution failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user")
        sys.exit(0)


def run_policy_manual():
    """
    Manual policy execution with more control.
    
    This gives you more flexibility for custom inference loops.
    """
    import torch
    import time
    from lerobot.policy import make_policy
    from lerobot_robot_roarm import RoarmConfig, Roarm
    
    # Get checkpoint
    checkpoint = input("Enter checkpoint path: ").strip()
    
    if not Path(checkpoint).exists():
        print(f"Checkpoint not found: {checkpoint}")
        sys.exit(1)
    
    # Load policy
    print("Loading policy...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    policy = make_policy(checkpoint, device=device)
    policy.eval()
    print(f"✓ Policy loaded on {device}")
    
    # Initialize robot
    print("Connecting to robot...")
    config = RoarmConfig(
        roarm_type="roarm_m3",
        port="/dev/ttyUSB0",
    )
    robot = Roarm(config)
    robot.connect()
    print("✓ Robot connected")
    
    try:
        # Run episodes
        num_episodes = int(input("How many episodes to run? "))
        
        for episode in range(num_episodes):
            print(f"\n=== Episode {episode + 1}/{num_episodes} ===")
            input("Press Enter to start episode (Ctrl+C to stop)...")
            
            # Reset policy state
            policy.reset()
            
            # Episode loop
            step = 0
            max_steps = 300  # 10 seconds at 30 Hz
            
            print("Running policy...")
            
            while step < max_steps:
                try:
                    # Get observation
                    obs = robot.get_observation()
                    
                    # Prepare observation for policy
                    # Convert to torch tensors and add batch dimension
                    policy_obs = {}
                    for key, value in obs.items():
                        if ".pos" in key:
                            policy_obs[key] = torch.tensor([value], device=device).unsqueeze(0)
                        elif "cam" in key:
                            # Convert image to tensor
                            policy_obs[key] = torch.tensor(value, device=device).unsqueeze(0)
                    
                    # Get action from policy
                    with torch.no_grad():
                        action = policy.select_action(policy_obs)
                    
                    # Convert action to dict
                    action_dict = {}
                    for key, value in action.items():
                        action_dict[key] = value.cpu().numpy()[0]
                    
                    # Send action to robot
                    robot.send_action(action_dict)
                    
                    step += 1
                    time.sleep(1.0 / 30.0)  # 30 Hz
                    
                except KeyboardInterrupt:
                    print("\nEpisode interrupted")
                    break
            
            print(f"Episode completed ({step} steps)")
    
    finally:
        print("\nDisconnecting robot...")
        robot.disconnect()
        print("Done!")


def evaluate_policy():
    """
    Evaluate policy and compute success metrics.
    """
    
    checkpoint = input("Enter checkpoint path: ").strip()
    
    if not Path(checkpoint).exists():
        print(f"Checkpoint not found: {checkpoint}")
        sys.exit(1)
    
    cmd = [
        "python", "-m", "lerobot.scripts.eval",
        
        # Robot
        "--robot.type=roarm",
        "--robot.roarm_type=roarm_m3",
        "--robot.port=/dev/ttyUSB0",
        
        # Policy
        f"--policy-checkpoint={checkpoint}",
        
        # Evaluation
        "--num-eval-episodes=20",
        "--fps=30",
        
        # Output
        "--output-dir=eval_results/roarm_act",
    ]
    
    print("Evaluating policy...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Evaluation completed!")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Evaluation failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted")
        sys.exit(0)


def main():
    """Main function to choose execution mode."""
    
    print("=== Roarm Policy Inference ===\n")
    print("Choose mode:")
    print("1. Run policy with CLI (recommended)")
    print("2. Run policy with manual control")
    print("3. Evaluate policy performance")
    print("q. Quit")
    
    choice = input("\nEnter choice (1-3, q): ").strip()
    
    if choice == "1":
        run_policy_cli()
    elif choice == "2":
        run_policy_manual()
    elif choice == "3":
        evaluate_policy()
    elif choice.lower() == "q":
        print("Exiting")
        sys.exit(0)
    else:
        print("Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    main()
