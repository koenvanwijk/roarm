"""
Configuration for Roarm robot (lerobot >= 0.5.0).
"""
from dataclasses import dataclass, field

from lerobot.cameras.configs import CameraConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.robots.config import RobotConfig


@RobotConfig.register_subclass("lerobot_robot_roarm")
@dataclass
class RoarmConfig(RobotConfig):
    """Configuration for Roarm robot (M1/M2/M3)."""

    # Robot type: roarm_m1, roarm_m2, roarm_m3
    roarm_type: str = "roarm_m3"

    # Connection — specify exactly one
    port: str | None = None   # serial, e.g. "/dev/ttyUSB0"
    baudrate: int = 115200
    host: str | None = None   # WiFi, e.g. "192.168.86.43"

    # Joint names (in SDK order)
    joint_names: list[str] = field(default_factory=lambda: [
        "shoulder_pan",
        "shoulder_lift",
        "elbow_flex",
        "wrist_flex",
        "wrist_roll",
        "gripper",
    ])

    # Physical joint limits in degrees (used for normalization)
    joint_limits_deg: dict[str, tuple[float, float]] = field(default_factory=lambda: {
        "shoulder_pan":   (-190, 190),
        "shoulder_lift":  (-110, 110),
        "elbow_flex":     (-70, 190),
        "wrist_flex":     (-110, 110),
        "wrist_roll":     (-190, 190),
        "gripper":        (-10, 100),
    })

    # Control parameters
    default_speed: int = 1000
    default_acc: int = 50

    # Gripper
    has_gripper: bool = True
    gripper_name: str = "gripper"

    # Kinematics (optional — enables EE mode)
    urdf_path: str | None = None          # e.g. "urdf/roarm_m3_kinematics.urdf"
    ee_frame_name: str = "hand_tcp"       # EE frame in URDF
    ik_joint_names: list[str] = field(default_factory=lambda: [
        "base_link_to_link1",
        "link1_to_link2",
        "link2_to_link3",
        "link3_to_link4",
        "link4_to_link5",
    ])

    # Cameras
    cameras: dict[str, CameraConfig] = field(
        default_factory=lambda: {
            "wrist_cam": OpenCVCameraConfig(
                index_or_path=0,
                fps=30,
                width=640,
                height=480,
            ),
        }
    )

    def __post_init__(self):
        super().__post_init__()
        if self.port is None and self.host is None:
            raise ValueError("Either 'port' (serial) or 'host' (WiFi) must be specified.")
        if self.port is not None and self.host is not None:
            raise ValueError("Specify either 'port' or 'host', not both.")
