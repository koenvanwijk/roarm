"""
Roarm robot implementation for LeRobot >= 0.5.0.
"""
import logging
from typing import Any

import numpy as np

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.robots.robot import Robot
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from .config_roarm import RoarmConfig

logger = logging.getLogger(__name__)

try:
    from roarm_sdk.roarm import roarm as RoarmSDK
except ImportError:
    raise ImportError(
        "roarm_sdk not found. Please install it with: pip install roarm-sdk"
    )


# ---------------------------------------------------------------------------
# Action modes — machine-readable contract (lerobot-action-space RFC)
# ---------------------------------------------------------------------------

class ActionMode:
    """Minimal action mode descriptor (lerobot-action-space compatible)."""

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
    ActionMode(
        name="joint_absolute_norm",
        space_type="joint",
        unit="normalized",
        command_mode="absolute",
        is_default=True,
        preferred_hz=30,
        description=(
            "Joint positions as percentages [-100, +100] mapped to physical joint limits "
            "(see joint_limits_deg in config). "
            "Gripper [0, 100] (0=closed, 100=open). "
            "Observations use the same normalized range."
        ),
    ),
]


class Roarm(Robot):
    """
    Roarm robot (M1/M2/M3) for LeRobot >= 0.5.0.

    Supports serial (port=) and WiFi (host=) connections via roarm_sdk.

    Action / observation contract:
      - joint positions: normalized [-100, +100]  (mapped from physical degrees)
      - gripper:         normalized [0, 100]       (0=closed, 100=open)
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
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        location = self.config.host or self.config.port
        logger.info(f"Connecting to {self.config.roarm_type} @ {location}...")

        try:
            self.robot.connect()
            self._is_connected = True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Roarm: {e}") from e

        for cam in self.cameras.values():
            cam.connect()

        logger.info(f"✓ Connected to {self.config.roarm_type} @ {location}")

    def disconnect(self) -> None:
        if not self._is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")

        for cam in self.cameras.values():
            if cam.is_connected:
                cam.disconnect()

        try:
            self.robot.disconnect()
        except Exception:
            pass

        self._is_connected = False
        logger.info(f"✓ Disconnected from {self.config.roarm_type}")

    # ------------------------------------------------------------------
    # Calibration (no-op — Roarm has no motor calibration step)
    # ------------------------------------------------------------------

    @property
    def is_calibrated(self) -> bool:
        return True

    def calibrate(self) -> None:
        logger.info("Roarm has no calibration procedure.")

    def configure(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Unit conversion helpers
    # ------------------------------------------------------------------

    def _deg_to_norm(self, deg: float, joint_name: str) -> float:
        """Physical degrees → normalized [-100, +100]."""
        if joint_name in self.config.joint_limits_deg:
            min_deg, max_deg = self.config.joint_limits_deg[joint_name]
            norm = (deg - min_deg) / (max_deg - min_deg) * 200.0 - 100.0
            return float(np.clip(norm, -100.0, 100.0))
        return float(np.clip(deg / 180.0 * 100.0, -100.0, 100.0))

    def _norm_to_deg(self, norm: float, joint_name: str) -> float:
        """Normalized [-100, +100] → physical degrees."""
        if joint_name in self.config.joint_limits_deg:
            min_deg, max_deg = self.config.joint_limits_deg[joint_name]
            pct = np.clip(norm, -100.0, 100.0)
            return float(min_deg + (pct + 100.0) * (max_deg - min_deg) / 200.0)
        return float(np.clip(norm / 100.0 * 180.0, -180.0, 180.0))

    def _gripper_deg_to_norm(self, deg: float) -> float:
        """Gripper degrees [0–90] → normalized [0, 100]."""
        return float(np.clip(deg / 90.0 * 100.0, 0.0, 100.0))

    def _gripper_norm_to_deg(self, norm: float) -> float:
        """Normalized [0, 100] → gripper degrees [0–90]."""
        return float(np.clip(norm / 100.0 * 90.0, 0.0, 90.0))

    # ------------------------------------------------------------------
    # Observation
    # ------------------------------------------------------------------

    def get_observation(self) -> dict[str, Any]:
        """
        Read current robot state.

        Returns:
            joint positions: normalized [-100, +100]
            gripper:         normalized [0, 100]
            camera images:   HxWx3 arrays
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")

        obs: dict[str, Any] = {}

        try:
            angles = self.robot.joints_angle_get()
            if angles:
                for i, joint_name in enumerate(self.config.joint_names):
                    obs[f"{joint_name}.pos"] = self._deg_to_norm(angles[i], joint_name)
        except Exception as e:
            logger.warning(f"Failed to read joint angles: {e}")
            for joint_name in self.config.joint_names:
                obs[f"{joint_name}.pos"] = 0.0

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
            action: {joint}.pos in [-100, +100], gripper.pos in [0, 100].

        Returns:
            The action as actually sent (clamped to valid ranges).
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")

        sent: dict[str, Any] = {}

        angles_deg = []
        for joint_name in self.config.joint_names:
            key = f"{joint_name}.pos"
            if key in action:
                norm = float(action[key])
                deg = self._norm_to_deg(norm, joint_name)
                angles_deg.append(deg)
                sent[key] = float(np.clip(norm, -100.0, 100.0))
            else:
                current = self.get_observation()
                norm = current.get(key, 0.0)
                angles_deg.append(self._norm_to_deg(norm, joint_name))
                sent[key] = norm

        try:
            self.robot.joints_angle_ctrl(
                angles=angles_deg,
                speed=self.config.default_speed,
                acc=self.config.default_acc,
            )
        except Exception as e:
            logger.warning(f"Failed to send joint command: {e}")

        if self.config.has_gripper:
            gripper_key = f"{self.config.gripper_name}.pos"
            if gripper_key in action:
                norm = float(np.clip(action[gripper_key], 0.0, 100.0))
                sent[gripper_key] = norm
                try:
                    self.robot.gripper_angle_ctrl(
                        angle=self._gripper_norm_to_deg(norm),
                        speed=self.config.default_speed,
                        acc=self.config.default_acc,
                    )
                except Exception as e:
                    logger.warning(f"Failed to send gripper command: {e}")

        return sent

    # ------------------------------------------------------------------
    # Safety
    # ------------------------------------------------------------------

    def teleop_safety_stop(self) -> None:
        """Release torque (emergency stop)."""
        try:
            self.robot.torque_set(cmd=0)
            logger.warning("Emergency stop activated!")
        except Exception:
            pass
