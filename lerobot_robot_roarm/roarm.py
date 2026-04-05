"""
Roarm robot implementation for LeRobot.

Compatible with lerobot >= 0.4.2 and >= 0.5.0.
"""
import logging
import time
from typing import Any

import numpy as np

# Import compatibility for lerobot >= 0.4.2 and >= 0.5.0
try:
    from lerobot.cameras import make_cameras_from_configs
except ImportError:
    from lerobot.cameras.utils import make_cameras_from_configs  # type: ignore

try:
    from lerobot.robots import Robot
except ImportError:
    from lerobot.robots.robot import Robot  # type: ignore

from .config_roarm import RoarmConfig

logger = logging.getLogger(__name__)

try:
    from roarm_sdk.roarm import roarm as RoarmSDK
except ImportError:
    raise ImportError(
        "roarm_sdk not found. Please install it with: pip install roarm-sdk"
    )


# ---------------------------------------------------------------------------
# Action modes — machine-readable contract (lerobot-action-space compatible)
# ---------------------------------------------------------------------------

class _ActionMode:
    """Minimal action mode descriptor, compatible with lerobot-action-space."""

    def __init__(self, name, space_type, unit, command_mode, is_default=True,
                 preferred_hz=30, description=""):
        self.name = name
        self.space_type = space_type
        self.unit = unit
        self.command_mode = command_mode
        self.is_default = is_default
        self.preferred_hz = preferred_hz
        self.description = description

    def __repr__(self):
        return (f"ActionMode(name={self.name!r}, space_type={self.space_type!r}, "
                f"unit={self.unit!r}, command_mode={self.command_mode!r})")


ROARM_ACTION_MODES = [
    _ActionMode(
        name="joint_absolute_norm",
        space_type="joint",
        unit="normalized",
        command_mode="absolute",
        is_default=True,
        preferred_hz=30,
        description=(
            "Joint positions as percentages [-100, +100] mapped to physical joint limits. "
            "SDK converts to degrees per joint (see joint_limits_deg in config). "
            "Gripper [0, 100] (0=closed, 100=open). "
            "Observations are also normalized: joints [-100, +100], gripper [0, 100]."
        ),
    ),
]


class Roarm(Robot):
    """
    Roarm robot implementation for LeRobot framework (M1/M2/M3).

    Supports serial (port=) and WiFi (host=) connections via roarm_sdk.

    Action format:  {joint}.pos in [-100, +100], gripper.pos in [0, 100]
    Observation format: same normalized range (consistent with action space)
    """

    config_class = RoarmConfig
    name = "lerobot_robot_roarm"

    def __init__(self, config: RoarmConfig):
        super().__init__(config)
        self.config = config

        if config.port is not None:
            self.robot = RoarmSDK(
                roarm_type=config.roarm_type,
                port=config.port,
                baudrate=config.baudrate,
            )
        else:
            self.robot = RoarmSDK(
                roarm_type=config.roarm_type,
                host=config.host,
            )

        self.cameras = make_cameras_from_configs(config.cameras)
        self._is_connected = False

    # ------------------------------------------------------------------
    # Features
    # ------------------------------------------------------------------

    @property
    def _motors_ft(self) -> dict[str, type]:
        features = {f"{j}.pos": float for j in self.config.joint_names}
        if self.config.has_gripper:
            features[f"{self.config.gripper_name}.pos"] = float
        return features

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.cameras[cam].height, self.cameras[cam].width, 3)
            for cam in self.cameras
        }

    @property
    def observation_features(self) -> dict:
        return {**self._motors_ft, **self._cameras_ft}

    @property
    def action_features(self) -> dict:
        return self._motors_ft

    @property
    def action_modes(self) -> list:
        """Machine-readable action space declaration (lerobot-action-space RFC)."""
        return ROARM_ACTION_MODES

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        cameras_connected = all(cam.is_connected for cam in self.cameras.values())
        return self._is_connected and cameras_connected

    def connect(self, calibrate: bool = True) -> None:
        if self.is_connected:
            from lerobot.errors import DeviceAlreadyConnectedError  # type: ignore
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        robot_id = f" ({self.config.host})" if self.config.host else f" ({self.config.port})"
        logger.info(f"Connecting to {self.config.roarm_type}{robot_id}...")

        try:
            self.robot.connect()
            self._is_connected = True
            logger.info(f"✓ Connected to {self.config.roarm_type}{robot_id}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Roarm: {e}") from e

        for cam in self.cameras.values():
            cam.connect()

    def disconnect(self) -> None:
        robot_id = f" ({self.config.host})" if self.config.host else f" ({self.config.port})"
        for cam in self.cameras.values():
            if cam.is_connected:
                cam.disconnect()
        try:
            self.robot.disconnect()
        except Exception:
            pass
        self._is_connected = False
        logger.info(f"✓ Disconnected from {self.config.roarm_type}{robot_id}")

    # ------------------------------------------------------------------
    # Calibration (no-op — Roarm has no motor calibration)
    # ------------------------------------------------------------------

    @property
    def is_calibrated(self) -> bool:
        return True

    def calibrate(self) -> None:
        logger.info("Roarm has no calibration procedure.")

    def configure(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Helpers: unit conversion
    # ------------------------------------------------------------------

    def _deg_to_norm(self, deg: float, joint_name: str) -> float:
        """Convert degrees to normalized [-100, +100]."""
        if joint_name in self.config.joint_limits_deg:
            min_deg, max_deg = self.config.joint_limits_deg[joint_name]
            norm = (deg - min_deg) / (max_deg - min_deg) * 200.0 - 100.0
            return float(np.clip(norm, -100.0, 100.0))
        # Fallback: assume [-180, 180]
        return float(np.clip(deg / 180.0 * 100.0, -100.0, 100.0))

    def _norm_to_deg(self, norm: float, joint_name: str) -> float:
        """Convert normalized [-100, +100] to degrees."""
        if joint_name in self.config.joint_limits_deg:
            min_deg, max_deg = self.config.joint_limits_deg[joint_name]
            pct = np.clip(norm, -100.0, 100.0)
            return float(min_deg + (pct + 100.0) * (max_deg - min_deg) / 200.0)
        return float(np.clip(norm / 100.0 * 180.0, -180.0, 180.0))

    def _gripper_deg_to_norm(self, deg: float) -> float:
        """Convert gripper angle (0–90°) to normalized [0, 100]."""
        return float(np.clip(deg / 90.0 * 100.0, 0.0, 100.0))

    def _gripper_norm_to_deg(self, norm: float) -> float:
        """Convert normalized gripper [0, 100] to degrees (0–90°)."""
        return float(np.clip(norm / 100.0 * 90.0, 0.0, 90.0))

    # ------------------------------------------------------------------
    # Observation
    # ------------------------------------------------------------------

    def get_observation(self) -> dict[str, Any]:
        """
        Read current state from robot.

        Returns normalized values:
          - joint positions: [-100, +100] (mapped from physical degrees)
          - gripper: [0, 100] (0=closed, 100=open)
          - camera images: HxWx3 arrays
        """
        if not self.is_connected:
            raise ConnectionError(f"{self} is not connected.")

        obs: dict[str, Any] = {}

        # Joint angles → normalized
        try:
            angles = self.robot.joints_angle_get()
            if angles:
                for i, joint_name in enumerate(self.config.joint_names):
                    obs[f"{joint_name}.pos"] = self._deg_to_norm(angles[i], joint_name)
        except Exception as e:
            logger.warning(f"Failed to read joint angles: {e}")
            for joint_name in self.config.joint_names:
                obs[f"{joint_name}.pos"] = 0.0

        # Gripper → normalized [0, 100]
        if self.config.has_gripper:
            try:
                gripper_deg = self.robot.gripper_angle_get()
                obs[f"{self.config.gripper_name}.pos"] = (
                    self._gripper_deg_to_norm(gripper_deg)
                    if gripper_deg is not None
                    else 0.0
                )
            except Exception as e:
                logger.warning(f"Failed to read gripper: {e}")
                obs[f"{self.config.gripper_name}.pos"] = 0.0

        # Camera frames
        for cam_key, cam in self.cameras.items():
            obs[cam_key] = cam.async_read()

        return obs

    # ------------------------------------------------------------------
    # Action
    # ------------------------------------------------------------------

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """
        Send joint position targets to the robot.

        Args:
            action: dict with {joint}.pos values in normalized [-100, +100].
                    Gripper key: {gripper_name}.pos in [0, 100]
                    (0 = fully closed, 100 = fully open).

        Returns:
            The action dict as sent (clamped to valid ranges).
        """
        if not self.is_connected:
            raise ConnectionError(f"{self} is not connected.")

        sent_action: dict[str, Any] = {}

        # Joints
        angles_deg = []
        for joint_name in self.config.joint_names:
            key = f"{joint_name}.pos"
            if key in action:
                norm = float(action[key])
                deg = self._norm_to_deg(norm, joint_name)
                angles_deg.append(deg)
                sent_action[key] = np.clip(norm, -100.0, 100.0)
            else:
                # Hold current position
                current = self.get_observation()
                norm = current.get(key, 0.0)
                angles_deg.append(self._norm_to_deg(norm, joint_name))
                sent_action[key] = norm

        try:
            self.robot.joints_angle_ctrl(
                angles=angles_deg,
                speed=self.config.default_speed,
                acc=self.config.default_acc,
            )
        except Exception as e:
            logger.warning(f"Failed to send joint command: {e}")

        # Gripper — action value is [0, 100] (normalized), NOT radians
        if self.config.has_gripper:
            gripper_key = f"{self.config.gripper_name}.pos"
            if gripper_key in action:
                norm = float(np.clip(action[gripper_key], 0.0, 100.0))
                gripper_deg = self._gripper_norm_to_deg(norm)
                sent_action[gripper_key] = norm
                try:
                    self.robot.gripper_angle_ctrl(
                        angle=gripper_deg,
                        speed=self.config.default_speed,
                        acc=self.config.default_acc,
                    )
                except Exception as e:
                    logger.warning(f"Failed to send gripper command: {e}")

        return sent_action

    # ------------------------------------------------------------------
    # Safety
    # ------------------------------------------------------------------

    def teleop_safety_stop(self) -> None:
        """Emergency stop — release torque."""
        try:
            self.robot.torque_set(cmd=0)
            logger.warning("Emergency stop activated!")
        except Exception:
            pass
