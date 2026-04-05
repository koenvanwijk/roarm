"""
Roarm teleoperator (leader arm) for LeRobot >= 0.5.0.

Use a Roarm with torque disabled as a leader arm. Joint positions are read
and returned as normalized values [-100, +100] so they can be sent directly
to a Roarm follower robot.
"""

import logging
import time
from typing import Any

import numpy as np
from roarm_sdk import roarm as RoarmSDK

from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from .config_roarm_teleoperator import RoarmTeleoperatorConfig
from .roarm import ROARM_ACTION_MODES

logger = logging.getLogger(__name__)


class RoarmTeleoperator(Teleoperator):
    """
    Roarm leader arm teleoperator for LeRobot >= 0.5.0.

    Connects to a Roarm with torque disabled. Reads joint positions and
    returns them as normalized values matching the follower robot's action space.

    Action / feedback contract:
      - {joint}.pos: normalized [-100, +100]
      - gripper.pos: normalized [0, 100]
    """

    config_class = RoarmTeleoperatorConfig
    name = "roarm_teleoperator"

    def __init__(self, config: RoarmTeleoperatorConfig):
        super().__init__(config)
        self.config = config
        self.roarm = None
        self._is_connected = False

    # ------------------------------------------------------------------
    # Features
    # ------------------------------------------------------------------

    @property
    def action_features(self) -> dict[str, type]:
        """Joint positions in normalized format, matching the follower robot."""
        joint_names = self.config.joint_names
        features = {f"{j}.pos": float for j in joint_names}
        if self.config.has_gripper:
            features[f"{self.config.gripper_name}.pos"] = float
        return features

    @property
    def feedback_features(self) -> dict[str, type]:
        return {}

    @property
    def action_modes(self) -> list:
        """Machine-readable action space declaration (lerobot-action-space RFC)."""
        return ROARM_ACTION_MODES

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self, calibrate: bool = True) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        location = self.config.host or self.config.port
        logger.info(f"Connecting to Roarm teleoperator @ {location}...")

        if self.config.port:
            self.roarm = RoarmSDK(
                roarm_type=self.config.roarm_type,
                port=self.config.port,
                baudrate=self.config.baudrate,
            )
        elif self.config.host:
            self.roarm = RoarmSDK(
                roarm_type=self.config.roarm_type,
                host=self.config.host,
            )
        else:
            raise ValueError("Either 'port' or 'host' must be set in config.")

        time.sleep(0.5)
        self.roarm.torque_set(cmd=0)  # disable torque → allow manual movement
        time.sleep(0.1)

        self._is_connected = True
        logger.info(f"✓ Connected (torque disabled, ready for manual control)")

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")

        try:
            self.roarm.torque_set(cmd=1)  # re-enable torque on disconnect
            time.sleep(0.1)
        except Exception as e:
            logger.warning(f"Could not re-enable torque: {e}")

        self._is_connected = False
        logger.info(f"✓ Disconnected from Roarm teleoperator")

    # ------------------------------------------------------------------
    # Calibration (no-op)
    # ------------------------------------------------------------------

    @property
    def is_calibrated(self) -> bool:
        return True

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Unit conversion helpers (same logic as Roarm robot)
    # ------------------------------------------------------------------

    def _deg_to_norm(self, deg: float, joint_name: str) -> float:
        """Physical degrees → normalized [-100, +100]."""
        limits = self.config.joint_limits_deg
        if joint_name in limits:
            min_deg, max_deg = limits[joint_name]
            norm = (deg - min_deg) / (max_deg - min_deg) * 200.0 - 100.0
            return float(np.clip(norm, -100.0, 100.0))
        return float(np.clip(deg / 180.0 * 100.0, -100.0, 100.0))

    def _gripper_deg_to_norm(self, deg: float) -> float:
        """Gripper degrees [0–90] → normalized [0, 100]."""
        return float(np.clip(deg / 90.0 * 100.0, 0.0, 100.0))

    # ------------------------------------------------------------------
    # Action
    # ------------------------------------------------------------------

    def get_action(self) -> dict[str, Any]:
        """
        Read current joint positions from the leader arm.

        Returns:
            dict: {joint}.pos in [-100, +100], gripper.pos in [0, 100]
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")

        angles = self.roarm.joints_angle_get()
        if not angles or len(angles) < len(self.config.joint_names):
            raise RuntimeError("Failed to read joint angles from Roarm teleoperator")

        action: dict[str, Any] = {}

        for i, joint_name in enumerate(self.config.joint_names):
            action[f"{joint_name}.pos"] = self._deg_to_norm(angles[i], joint_name)

        if self.config.has_gripper:
            gripper_key = f"{self.config.gripper_name}.pos"
            gripper_idx = len(self.config.joint_names)
            if len(angles) > gripper_idx:
                action[gripper_key] = self._gripper_deg_to_norm(angles[gripper_idx])
            else:
                action[gripper_key] = 0.0

        return action

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        pass

    def __repr__(self) -> str:
        location = self.config.host or self.config.port
        return f"RoarmTeleoperator(location={location!r}, connected={self._is_connected})"
