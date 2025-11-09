"""Roarm M3 Teleoperator implementation for LeRobot.

The teleoperator is used as the "leader" arm - you manually move it and the
follower robot mirrors your movements.
"""

import logging
import time
from typing import Any

import numpy as np
from roarm_sdk import roarm as RoarmSDK

from lerobot.processor import RobotAction, RobotObservation
from lerobot.teleoperators.teleoperator import Teleoperator

from .config_roarm_teleoperator import RoarmTeleoperatorConfig


class RoarmTeleoperator(Teleoperator):
    """Roarm M3 teleoperator for teleoperation (leader arm).
    
    This class reads joint positions from a Roarm robot with torque disabled,
    allowing manual movement. The positions are then sent to the follower robot.
    """
    
    def __init__(self, config: RoarmTeleoperatorConfig):
        """Initialize the Roarm teleoperator.
        
        Args:
            config: Configuration for the Roarm teleoperator
        """
        self.name = config.id or "roarm_teleoperator"
        super().__init__(config)
        self.config = config
        self.roarm = None
        self._connected = False
        
        logging.info(f"Initializing Roarm teleoperator (id={config.id})")
    
    def connect(self) -> None:
        """Connect to the Roarm robot and disable torque for manual control."""
        if self._connected:
            teleop_id = f" ({self.config.id})" if self.config.id else ""
            logging.warning(f"Roarm teleoperator{teleop_id} already connected")
            return
        
        teleop_id = f" ({self.config.id})" if self.config.id else ""
        logging.info(f"Connecting to Roarm teleoperator{teleop_id}...")
        
        if self.config.port:
            # Connect via serial
            self.roarm = RoarmSDK(
                port=self.config.port, 
                baudrate=self.config.baudrate,
                roarm_type=self.config.roarm_type
            )
        elif self.config.host:
            # Connect via WiFi
            self.roarm = RoarmSDK(
                host=self.config.host,
                roarm_type=self.config.roarm_type
            )
        else:
            raise ValueError(f"Either port or host must be specified for Roarm teleoperator{teleop_id}")
        
        # Wait for connection
        time.sleep(0.5)
        
        # Disable torque to allow manual movement
        self.roarm.torque_set(cmd=0)
        time.sleep(0.1)
        
        self._connected = True
        logging.info(f"✓ Roarm teleoperator{teleop_id} connected and torque disabled")
    
    def disconnect(self) -> None:
        """Disconnect from the Roarm robot."""
        if not self._connected:
            return
        
        teleop_id = f" ({self.config.id})" if self.config.id else ""
        
        if self.roarm:
            # Re-enable torque before disconnecting
            try:
                self.roarm.torque_set(cmd=1)
                time.sleep(0.1)
            except Exception as e:
                logging.warning(f"Could not re-enable torque on Roarm{teleop_id}: {e}")
        
        self._connected = False
        logging.info(f"✓ Roarm teleoperator{teleop_id} disconnected")
    
    def get_observation(self) -> RobotObservation:
        """Read current joint positions from the teleoperator.
        
        Returns:
            RobotObservation with joint positions and gripper state
        """
        if not self._connected:
            raise RuntimeError("Roarm teleoperator not connected")
        
        # Get current joint angles (in degrees)
        angles = self.roarm.joints_angle_get()
        if not angles or len(angles) < 6:
            raise RuntimeError("Failed to read joint angles from teleoperator")
        
        # Convert to radians
        joints = np.deg2rad(np.array(angles[:6], dtype=np.float32))
        
        # Create observation dict matching the robot's state structure
        observation = {
            'observation.state': joints,
        }
        
        return RobotObservation(**observation)
    
    def calibrate(self, *args: Any, **kwargs: Any) -> None:
        """Calibration is not required for Roarm teleoperator."""
        logging.info("Calibration not required for Roarm teleoperator")
        pass
    
    def is_connected(self) -> bool:
        """Check if teleoperator is connected."""
        return self._connected
    
    def is_calibrated(self) -> bool:
        """Check if teleoperator is calibrated (always True for Roarm)."""
        return True
    
    def configure(self) -> None:
        """Configure the teleoperator (no configuration needed for Roarm)."""
        pass
    
    def get_action(self) -> RobotAction:
        """Get action from teleoperator (reads joint positions).
        
        Returns:
            RobotAction with joint positions as percentages (-100 to +100)
        """
        if not self._connected:
            raise RuntimeError("Roarm teleoperator not connected")
        
        # Get current joint angles (in degrees)
        angles = self.roarm.joints_angle_get()
        if not angles or len(angles) < 6:
            raise RuntimeError("Failed to read joint angles from teleoperator")
        
        # Log leader position
        logging.info(f"Leader position (deg): {[f'{a:.1f}' for a in angles[:6]]}")
        
        # Joint limits in degrees for Roarm M3
        joint_limits = {
            'shoulder_pan': (-190, 190),
            'shoulder_lift': (-110, 110),
            'elbow_flex': (-70, 190),
            'wrist_flex': (-110, 110),
            'wrist_roll': (-190, 190),
            'gripper': (-10, 100)
        }
        
        # Convert to percentages [-100, +100] and create action dict
        action_dict = {}
        joint_names = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper']
        
        for i, joint_name in enumerate(joint_names):
            angle_deg = angles[i]
            min_deg, max_deg = joint_limits[joint_name]
            
            # Map [min_deg, max_deg] → [-100, +100]
            percentage = ((angle_deg - min_deg) / (max_deg - min_deg)) * 200.0 - 100.0
            percentage = np.clip(percentage, -100.0, 100.0)
            
            action_dict[f"{joint_name}.pos"] = float(percentage)
        
        return RobotAction(**action_dict)
    
    def send_feedback(self, feedback: Any) -> None:
        """Send feedback to teleoperator (not used for Roarm)."""
        pass
    
    @property
    def action_features(self) -> dict[str, Any]:
        """Get action features specification."""
        return {
            'action': {
                'dtype': 'float32',
                'shape': (6,),  # 6 joints
                'names': ['base', 'shoulder', 'elbow', 'tilt', 'rotate', 'gripper']
            }
        }
    
    @property
    def feedback_features(self) -> dict[str, Any]:
        """Get feedback features specification."""
        return {}  # No feedback for Roarm
    
    def __repr__(self) -> str:
        """String representation of the teleoperator."""
        return (
            f"{self.__class__.__name__}("
            f"port={self.config.port}, "
            f"host={self.config.host}, "
            f"id={self.config.id}, "
            f"connected={self._connected})"
        )
