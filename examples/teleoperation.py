"""
Teleoperation example for Roarm robot.

This script demonstrates how to set up teleoperation between two Roarm robots,
where one acts as a leader (teleoperator) and the other as a follower.

Note: This example uses LeRobot's teleoperation framework. For direct control,
use the lerobot-teleoperate command instead (see README.md).
"""
import time
import threading

from lerobot_robot_roarm import RoarmConfig, Roarm


class RoarmTeleop:
    """Teleoperation handler for two Roarm robots.
    
    This is a simplified example. For production use, use LeRobot's
    teleoperation framework with RoarmTeleoperator class.
    """
    
    def __init__(
        self, 
        leader_config: RoarmConfig,
        follower_config: RoarmConfig,
        control_rate: float = 10.0  # Hz
    ):
        """
        Args:
            leader_config: Configuration for leader robot
            follower_config: Configuration for follower robot
            control_rate: Control loop frequency in Hz
        """
        self.leader = Roarm(leader_config)
        self.follower = Roarm(follower_config)
        self.control_rate = control_rate
        self.running = False
        self.thread = None
    
    def start(self):
        """Start teleoperation."""
        print("Connecting to robots...")
        
        # Connect leader (disable torque for manual control)
        self.leader.connect(calibrate=False)
        self.leader.robot.torque_set(cmd=0)  # Release torque on leader
        print("✓ Leader ready (torque disabled for manual control)")
        
        # Connect follower
        self.follower.connect(calibrate=False)
        print("✓ Follower ready")
        
        # Start control loop
        self.running = True
        self.thread = threading.Thread(target=self._control_loop)
        self.thread.start()
        
        print("\n=== Teleoperation Active ===")
        print("Move the leader robot manually.")
        print("The follower will mirror your movements.")
        print("Press Ctrl+C to stop.\n")
    
    def stop(self):
        """Stop teleoperation."""
        print("\nStopping teleoperation...")
        self.running = False
        
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        
        # Disconnect robots
        self.leader.disconnect()
        self.follower.disconnect()
        print("✓ Teleoperation stopped")
    
    def _control_loop(self):
        """Main control loop."""
        dt = 1.0 / self.control_rate
        
        while self.running:
            start_time = time.time()
            
            try:
                # Read leader position
                leader_obs = self.leader.get_observation()
                
                # Extract joint positions
                action = {}
                for key, value in leader_obs.items():
                    if ".pos" in key and "cam" not in key:
                        action[key] = value
                
                # Send to follower
                self.follower.send_action(action)
                
            except Exception as e:
                print(f"Control loop error: {e}")
            
            # Maintain control rate
            elapsed = time.time() - start_time
            sleep_time = dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)


def main():
    # Configure leader robot (the one you'll move manually)
    leader_config = RoarmConfig(
        roarm_type="roarm_m3",
        port="/dev/ttyUSB0",  # Adjust to your leader's port
        baudrate=115200,
        cameras={},  # Disable cameras for teleoperation
    )
    
    # Configure follower robot (the one that will follow)
    follower_config = RoarmConfig(
        roarm_type="roarm_m3",
        port="/dev/ttyUSB1",  # Adjust to your follower's port
        baudrate=115200,
        cameras={},  # Disable cameras for teleoperation
    )
    
    # Alternative: Use WiFi for one or both robots
    # leader_config = RoarmConfig(
    #     roarm_type="roarm_m3",
    #     host="192.168.1.100",
    # )
    # follower_config = RoarmConfig(
    #     roarm_type="roarm_m3",
    #     host="192.168.1.101",
    # )
    
    # Create teleop handler
    teleop = RoarmTeleop(
        leader_config=leader_config,
        follower_config=follower_config,
        control_rate=10.0  # 10 Hz control rate
    )
    
    try:
        # Start teleoperation
        teleop.start()
        
        # Keep running until interrupted
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop teleoperation
        teleop.stop()
        print("Done!")


if __name__ == "__main__":
    main()
