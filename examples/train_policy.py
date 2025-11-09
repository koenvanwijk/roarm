"""
Train a policy using recorded Roarm demonstrations.

This script demonstrates how to train a policy using LeRobot's training tools.
"""
import subprocess
import sys
from pathlib import Path


def train_act_policy():
    """
    Train an ACT (Action Chunking with Transformers) policy.
    
    ACT is a powerful policy for manipulation tasks.
    """
    
    cmd = [
        "lerobot-train",
        
        # Dataset
        "--dataset-repo-id=my-username/roarm_demos",
        # or use local: "--dataset-dir=data/roarm_demos",
        
        # Policy configuration
        "--policy=act",
        "--policy.chunk_size=100",
        "--policy.n_action_steps=100",
        "--policy.input_shapes.observation.shoulder_pan.pos=[1]",
        "--policy.input_shapes.observation.shoulder_lift.pos=[1]",
        "--policy.input_shapes.observation.elbow_flex.pos=[1]",
        "--policy.input_shapes.observation.wrist_flex.pos=[1]",
        "--policy.input_shapes.observation.wrist_roll.pos=[1]",
        "--policy.input_shapes.observation.gripper.pos=[1]",
        "--policy.input_shapes.observation.wrist_cam=[3,480,640]",
        
        # Training configuration
        "--training.num_epochs=2000",
        "--training.batch_size=8",
        "--training.learning_rate=1e-4",
        "--training.lr_scheduler.num_warmup_steps=500",
        
        # Output
        "--output-dir=outputs/roarm_act",
        
        # Logging
        "--wandb.enable=true",
        "--wandb.project=roarm-lerobot",
        "--wandb.run_name=roarm_act_v1",
        
        # Device
        "--device=cuda",  # or "cpu" if no GPU
    ]
    
    print("Training ACT policy...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Training completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Training failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        sys.exit(0)


def train_diffusion_policy():
    """
    Train a Diffusion Policy.
    
    Diffusion policies are effective for complex manipulation tasks.
    """
    
    cmd = [
        "lerobot-train",
        
        # Dataset
        "--dataset-repo-id=my-username/roarm_demos",
        
        # Policy
        "--policy=diffusion",
        "--policy.n_action_steps=8",
        "--policy.num_inference_steps=10",
        
        # Training
        "--training.num_epochs=1000",
        "--training.batch_size=16",
        "--training.learning_rate=1e-4",
        
        # Output
        "--output-dir=outputs/roarm_diffusion",
        
        # Device
        "--device=cuda",
    ]
    
    print("Training Diffusion Policy...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Training completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Training failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        sys.exit(0)


def train_simple_policy():
    """
    Train a simple feedforward policy.
    
    Good for simpler tasks or as a baseline.
    """
    
    cmd = [
        "lerobot-train",
        
        # Dataset
        "--dataset-repo-id=my-username/roarm_demos",
        
        # Policy
        "--policy=feedforward",
        "--policy.hidden_size=256",
        "--policy.n_layers=3",
        
        # Training
        "--training.num_epochs=500",
        "--training.batch_size=32",
        "--training.learning_rate=1e-3",
        
        # Output
        "--output-dir=outputs/roarm_feedforward",
        
        # Device
        "--device=cuda",
    ]
    
    print("Training Feedforward Policy...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Training completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Training failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        sys.exit(0)


def resume_training():
    """Resume training from a checkpoint."""
    
    checkpoint_path = input("Enter checkpoint path: ").strip()
    
    if not Path(checkpoint_path).exists():
        print(f"Checkpoint not found: {checkpoint_path}")
        sys.exit(1)
    
    cmd = [
        "python", "-m", "lerobot.scripts.train",
        "--resume-from-checkpoint", checkpoint_path,
    ]
    
    print(f"Resuming training from {checkpoint_path}...")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Training completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Training failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        sys.exit(0)


def main():
    """Main function to choose training mode."""
    
    print("=== Roarm Policy Training ===\n")
    print("Choose training mode:")
    print("1. Train ACT policy (recommended for manipulation)")
    print("2. Train Diffusion policy")
    print("3. Train simple feedforward policy")
    print("4. Resume training from checkpoint")
    print("q. Quit")
    
    choice = input("\nEnter choice (1-4, q): ").strip()
    
    if choice == "1":
        train_act_policy()
    elif choice == "2":
        train_diffusion_policy()
    elif choice == "3":
        train_simple_policy()
    elif choice == "4":
        resume_training()
    elif choice.lower() == "q":
        print("Exiting")
        sys.exit(0)
    else:
        print("Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    main()
