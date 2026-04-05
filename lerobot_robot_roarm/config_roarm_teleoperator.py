"""
Configuration for Roarm as a teleoperator (leader arm) — lerobot >= 0.5.0.
"""
from dataclasses import dataclass, field
from pathlib import Path

from lerobot.teleoperators.config import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("roarm_teleoperator")
@dataclass
class RoarmTeleoperatorConfig(TeleoperatorConfig):
    """
    Configuration for a Roarm used as a leader arm (torque disabled).

    The teleoperator is the device you manually move to control the follower.
    """

    roarm_type: str = "roarm_m3"

    # Connection — specify exactly one
    port: str | None = None    # serial, e.g. "/dev/ttyUSB0"
    baudrate: int = 115200
    host: str | None = None    # WiFi, e.g. "192.168.86.43"

    # Joint names (must match follower robot joint order)
    joint_names: list[str] = field(default_factory=lambda: [
        "shoulder_pan",
        "shoulder_lift",
        "elbow_flex",
        "wrist_flex",
        "wrist_roll",
    ])

    # Physical joint limits in degrees (used for normalization → [-100, +100])
    joint_limits_deg: dict[str, tuple[float, float]] = field(default_factory=lambda: {
        "shoulder_pan":   (-190, 190),
        "shoulder_lift":  (-110, 110),
        "elbow_flex":     (-70, 190),
        "wrist_flex":     (-110, 110),
        "wrist_roll":     (-190, 190),
    })

    # Gripper
    has_gripper: bool = True
    gripper_name: str = "gripper"
