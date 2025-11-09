"""
Roarm robot implementation for LeRobot.
"""
import logging
import time
from typing import Any

import numpy as np

from lerobot.cameras import make_cameras_from_configs
from lerobot.robots import Robot

from .config_roarm import RoarmConfig

logger = logging.getLogger(__name__)

try:
    from roarm_sdk.roarm import roarm as RoarmSDK
except ImportError:
    raise ImportError(
        "roarm_sdk not found. Please install it with: pip install roarm-sdk"
    )


class Roarm(Robot):
    """
    Roarm robot implementation for LeRobot framework.
    
    This class integrates the Roarm robot arm with the LeRobot ecosystem,
    supporting both serial and WiFi connections.
    """
    
    config_class = RoarmConfig
    name = "roarm"
    
    def __init__(self, config: RoarmConfig):
        super().__init__(config)
        self.config = config
        
        # Initialize the roarm SDK instance
        if config.port is not None:
            # Serial connection
            self.robot = RoarmSDK(
                roarm_type=config.roarm_type,
                port=config.port,
                baudrate=config.baudrate
            )
        else:
            # WiFi connection
            self.robot = RoarmSDK(
                roarm_type=config.roarm_type,
                host=config.host
            )
        
        # Initialize cameras
        self.cameras = make_cameras_from_configs(config.cameras)
        
        # Track connection state
        self._is_connected = False
        self._is_calibrated = False
        
    @property
    def _motors_ft(self) -> dict[str, type]:
        """Motor features for observations and actions."""
        features = {}
        for joint_name in self.config.joint_names:
            features[f"{joint_name}.pos"] = float
        
        if self.config.has_gripper:
            features[f"{self.config.gripper_name}.pos"] = float
            
        return features
    
    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        """Camera features for observations."""
        return {
            cam: (self.cameras[cam].height, self.cameras[cam].width, 3) 
            for cam in self.cameras
        }
    
    @property
    def observation_features(self) -> dict:
        """
        Define observation features.
        
        Returns dict with joint positions and camera images.
        """
        return {**self._motors_ft, **self._cameras_ft}
    
    @property
    def action_features(self) -> dict:
        """
        Define action features.
        
        Returns dict with joint position targets.
        """
        return self._motors_ft
    
    @property
    def is_connected(self) -> bool:
        """Check if robot and cameras are connected."""
        cameras_connected = all(
            cam.is_connected for cam in self.cameras.values()
        )
        return self._is_connected and cameras_connected
    
    def connect(self, calibrate: bool = True) -> None:
        """
        Connect to the robot and cameras.
        
        Args:
            calibrate: If True and robot is not calibrated, run calibration.
        """
        # The roarm SDK connects automatically on initialization
        # We just need to verify communication
        try:
            # Try to get current position to verify connection
            _ = self.robot.joints_angle_get()
            self._is_connected = True
            robot_id = f" ({self.config.id})" if self.config.id else ""
            logger.info(f"✓ Connected to {self.config.roarm_type}{robot_id}")
        except Exception as e:
            robot_id = f" ({self.config.id})" if self.config.id else ""
            raise ConnectionError(f"Failed to connect to Roarm{robot_id}: {e}")
        
        # Connect cameras
        for cam_name, cam in self.cameras.items():
            cam.connect()
            logger.info(f"✓ Connected to camera: {cam_name}")
        
        # Calibration
        if not self.is_calibrated and calibrate:
            self.calibrate()
        
        # Configure robot
        self.configure()
    
    def disconnect(self) -> None:
        """Disconnect from robot and cameras."""
        # Disconnect cameras
        for cam in self.cameras.values():
            cam.disconnect()
        
        # The roarm SDK doesn't have explicit disconnect
        # but we can release torque for safety
        try:
            self.robot.torque_set(cmd=0)  # Release torque
        except:
            pass
        
        self._is_connected = False
        robot_id = f" ({self.config.id})" if self.config.id else ""
        logger.info(f"✓ Disconnected from Roarm{robot_id}")
    
    @property
    def is_calibrated(self) -> bool:
        """Check if robot is calibrated."""
        # For Roarm, we can check if calibration data exists
        return self._is_calibrated or self.calibration is not None
    
    def calibrate(self) -> None:
        """
        Calibrate the robot.
        
        For Roarm, this involves:
        1. Moving to a known home position
        2. Recording joint limits
        3. Saving calibration data
        """
        logger.info("\n=== Roarm Calibration ===")
        logger.info("This will move the robot to its home position.")
        
        input("Press ENTER to start calibration...")
        
        try:
            # Move to init position
            self.robot.move_init()
            time.sleep(2)
            
            # Get home position
            home_angles = self.robot.joints_angle_get()
            logger.info(f"Home position: {home_angles}")
            
            # For Roarm, we typically use the full range of motion
            # You may want to customize these based on your robot model
            calibration_data = {}
            
            for i, joint_name in enumerate(self.config.joint_names):
                calibration_data[joint_name] = {
                    'home_position': home_angles[i] if home_angles else 0.0,
                    'min_angle': -180.0,  # degrees
                    'max_angle': 180.0,   # degrees
                }
            
            if self.config.has_gripper:
                gripper_pos = self.robot.gripper_angle_get()
                calibration_data[self.config.gripper_name] = {
                    'home_position': gripper_pos if gripper_pos else 0.0,
                    'min_angle': 0.0,
                    'max_angle': 90.0,
                }
            
            self.calibration = calibration_data
            self._is_calibrated = True
            self._save_calibration()
            
            logger.info("✓ Calibration complete!")
            logger.info(f"Calibration saved to: {self.calibration_fpath}")
            
        except Exception as e:
            logger.error(f"✗ Calibration failed: {e}")
            raise
    
    def configure(self) -> None:
        """
        Configure robot parameters.
        
        This is called after connection and calibration.
        """
        # Enable torque for operation
        try:
            self.robot.torque_set(cmd=1)
            logger.info("✓ Robot configured and ready")
        except Exception as e:
            logger.warning(f"Failed to enable torque: {e}")
    
    def get_observation(self) -> dict[str, Any]:
        """
        Get current observation from robot.
        
        Returns:
            Dictionary with joint positions and camera images.
        """
        if not self.is_connected:
            raise ConnectionError(f"{self} is not connected.")
        
        obs_dict = {}
        
        # Get joint angles (in degrees from Roarm)
        try:
            angles = self.robot.joints_angle_get()
            if angles:
                for i, joint_name in enumerate(self.config.joint_names):
                    # Convert to radians and normalize to [-pi, pi]
                    angle_rad = np.deg2rad(angles[i])
                    obs_dict[f"{joint_name}.pos"] = float(angle_rad)
        except Exception as e:
            logger.warning(f"Failed to read joint angles: {e}")
            # Return zeros if read fails
            for joint_name in self.config.joint_names:
                obs_dict[f"{joint_name}.pos"] = 0.0
        
        # Get gripper position
        if self.config.has_gripper:
            try:
                gripper_angle = self.robot.gripper_angle_get()
                gripper_rad = np.deg2rad(gripper_angle) if gripper_angle is not None else 0.0
                obs_dict[f"{self.config.gripper_name}.pos"] = float(gripper_rad)
            except Exception as e:
                logger.warning(f"Failed to read gripper: {e}")
                obs_dict[f"{self.config.gripper_name}.pos"] = 0.0
        
        # Capture images from cameras
        for cam_key, cam in self.cameras.items():
            obs_dict[cam_key] = cam.async_read()
        
        return obs_dict
    
    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """
        Send action command to robot.
        
        Args:
            action: Dictionary with joint position targets as percentages [-100, +100].
                   Both SO-101 and Roarm teleoperators send values in this percentage format.
            
        Returns:
            The action that was actually sent.
        """
        if not self.is_connected:
            raise ConnectionError(f"{self} is not connected.")
        
        # Extract joint angles and convert from percentages to degrees
        angles_deg = []
        for joint_name in self.config.joint_names:
            key = f"{joint_name}.pos"
            if key in action:
                value = action[key]
                
                # All teleoperators now send percentages in range [-100, +100]
                # Map from [-100, +100] to the full range of this joint
                if joint_name in self.config.joint_limits_deg:
                    min_deg, max_deg = self.config.joint_limits_deg[joint_name]
                    # Clamp to [-100, +100] range
                    percentage = np.clip(value, -100, 100)
                    # Map [-100, +100] → [min_deg, max_deg]
                    angle_deg = min_deg + (percentage + 100) * (max_deg - min_deg) / 200.0
                else:
                    # Fallback: treat as degrees and clamp
                    angle_deg = np.clip(value, -180, 180)
                
                angles_deg.append(float(angle_deg))
            else:
                # If joint not in action, maintain current position
                current_obs = self.get_observation()
                angles_deg.append(np.rad2deg(current_obs[key]))
        
        # Send joint command
        try:
            self.robot.joints_angle_ctrl(
                angles=angles_deg,
                speed=self.config.default_speed,
                acc=self.config.default_acc
            )
        except Exception as e:
            logger.warning(f"Failed to send joint command: {e}")
        
        # Handle gripper
        if self.config.has_gripper:
            gripper_key = f"{self.config.gripper_name}.pos"
            if gripper_key in action:
                try:
                    gripper_rad = action[gripper_key]
                    gripper_deg = np.rad2deg(gripper_rad)
                    gripper_deg = np.clip(gripper_deg, 0, 90)
                    
                    self.robot.gripper_angle_ctrl(
                        angle=float(gripper_deg),
                        speed=self.config.default_speed,
                        acc=self.config.default_acc
                    )
                except Exception as e:
                    logger.warning(f"Failed to send gripper command: {e}")
        
        return action
    
    def teleop_safety_stop(self) -> None:
        """Emergency stop for teleoperation."""
        try:
            self.robot.torque_set(cmd=0)  # Release torque
            logger.warning("Emergency stop activated!")
        except:
            pass
