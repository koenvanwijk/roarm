"""Configuration for Roarm M3 as a teleoperator (leader arm)."""

from dataclasses import dataclass, field
from pathlib import Path

from lerobot.teleoperators.config import TeleoperatorConfig


@dataclass
class RoarmTeleoperatorConfig(TeleoperatorConfig):
    """Configuration for Roarm M3 robot as a teleoperator (leader arm).
    
    The teleoperator is the device you manually move to control the follower robot.
    For Roarm, this is typically another Roarm robot with torque disabled.
    """
    
    # Robot type
    roarm_type: str = "roarm_m3"  # Robot model (roarm_m3, roarm_alpha, etc.)
    
    # Connection settings
    port: str | None = None  # Serial port (e.g., "/dev/ttyUSB0")
    host: str | None = None  # WiFi IP address (alternative to serial)
    baudrate: int = 115200
    
    # Calibration
    calibration_dir: Path | None = None
    
    # ID to distinguish between multiple teleoperators
    id: str | None = None


# Register this config so lerobot-teleoperate can discover it
TeleoperatorConfig.register_subclass("lerobot_robot_roarm", RoarmTeleoperatorConfig)
