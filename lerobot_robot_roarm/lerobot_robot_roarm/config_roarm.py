"""
Configuration for Roarm robot.
"""
from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.robots import RobotConfig


@RobotConfig.register_subclass("lerobot_robot_roarm")
@dataclass
class RoarmConfig(RobotConfig):
    """Configuration for Roarm robot."""
    
    # Robot type: roarm_m1, roarm_m2, roarm_m3, etc.
    roarm_type: str = "roarm_m3"
    
    # Serial connection parameters (primary method)
    port: str | None = None  # e.g., "/dev/ttyUSB0"
    baudrate: int = 115200
    
    # WiFi connection parameters (alternative)
    host: str | None = None  # e.g., "192.168.86.43"
    
    # Joint names for the robot (matching LeRobot standard names)
    joint_names: list[str] = field(default_factory=lambda: [
        "shoulder_pan",
        "shoulder_lift", 
        "elbow_flex",
        "wrist_flex",
        "wrist_roll",
        "gripper"
    ])
    
    # Joint angle limits in degrees (min, max) for each joint
    # These are the physical limits of the Roarm M3 robot from the SDK
    joint_limits_deg: dict[str, tuple[float, float]] = field(default_factory=lambda: {
        "shoulder_pan": (-190, 190),
        "shoulder_lift": (-110, 110),
        "elbow_flex": (-70, 190),
        "wrist_flex": (-110, 110),
        "wrist_roll": (-190, 190),
        "gripper": (-10, 100)
    })
    
    # Control parameters
    default_speed: int = 1000  # Default movement speed
    default_acc: int = 50  # Default acceleration
    
    # Gripper configuration
    has_gripper: bool = True
    gripper_name: str = "gripper"
    
    # Camera configuration
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
    
    # Safety limits
    max_joint_velocity: float = 3.0  # radians per second
    max_gripper_velocity: float = 2.0  # radians per second
    
    # End effector bounds (in meters, relative to base)
    ee_bounds_min: list[float] = field(default_factory=lambda: [-0.4, -0.4, 0.0])
    ee_bounds_max: list[float] = field(default_factory=lambda: [0.4, 0.4, 0.5])
    
    # Maximum end effector step size per action (in meters)
    max_ee_step_m: float = 0.05
    
    def __post_init__(self):
        """Validate configuration."""
        super().__post_init__()
        
        if self.port is None and self.host is None:
            raise ValueError("Either 'port' (serial) or 'host' (WiFi) must be specified")
        
        if self.port is not None and self.host is not None:
            raise ValueError("Cannot specify both 'port' and 'host'. Choose one connection method.")
