"""
Processor pipelines for Roarm robot.

This module provides processing pipelines for converting between different
action and observation spaces when using the Roarm robot.
"""
from typing import Any

import numpy as np

from lerobot.processor import (
    ProcessorStep,
    RobotProcessorPipeline,
    EnvTransition,
)


class RoarmJointNormalizer(ProcessorStep):
    """
    Normalize joint positions to a standard range.
    
    This step converts joint positions from their raw ranges to normalized
    values (e.g., [-1, 1] or [0, 1]).
    """
    
    def __init__(
        self, 
        joint_names: list[str],
        joint_ranges: dict[str, tuple[float, float]] | None = None,
        output_range: tuple[float, float] = (-1.0, 1.0)
    ):
        """
        Args:
            joint_names: List of joint names to normalize
            joint_ranges: Dict mapping joint names to (min, max) tuples in radians
            output_range: Target range for normalized values
        """
        super().__init__()
        self.joint_names = joint_names
        self.output_range = output_range
        
        # Default ranges if not provided (typical for 6-DOF arms)
        if joint_ranges is None:
            joint_ranges = {
                name: (-np.pi, np.pi) for name in joint_names
            }
        self.joint_ranges = joint_ranges
    
    def forward(self, transition: EnvTransition) -> EnvTransition:
        """Normalize joint positions."""
        for joint_name in self.joint_names:
            key = f"{joint_name}.pos"
            if key in transition.action:
                value = transition.action[key]
                min_val, max_val = self.joint_ranges[joint_name]
                
                # Normalize to [0, 1]
                normalized = (value - min_val) / (max_val - min_val)
                
                # Scale to output range
                out_min, out_max = self.output_range
                scaled = normalized * (out_max - out_min) + out_min
                
                transition.action[key] = scaled
        
        return transition
    
    def inverse(self, transition: EnvTransition) -> EnvTransition:
        """Denormalize joint positions."""
        for joint_name in self.joint_names:
            key = f"{joint_name}.pos"
            if key in transition.action:
                value = transition.action[key]
                min_val, max_val = self.joint_ranges[joint_name]
                
                # Scale from output range to [0, 1]
                out_min, out_max = self.output_range
                normalized = (value - out_min) / (out_max - out_min)
                
                # Denormalize to original range
                denormalized = normalized * (max_val - min_val) + min_val
                
                transition.action[key] = denormalized
        
        return transition


class RoarmGripperNormalizer(ProcessorStep):
    """
    Normalize gripper position to a standard range.
    """
    
    def __init__(
        self,
        gripper_name: str = "gripper",
        gripper_range: tuple[float, float] = (0.0, np.pi/2),  # 0 to 90 degrees
        output_range: tuple[float, float] = (0.0, 1.0)
    ):
        """
        Args:
            gripper_name: Name of the gripper
            gripper_range: (min, max) range in radians
            output_range: Target range for normalized values
        """
        super().__init__()
        self.gripper_name = gripper_name
        self.gripper_range = gripper_range
        self.output_range = output_range
    
    def forward(self, transition: EnvTransition) -> EnvTransition:
        """Normalize gripper position."""
        key = f"{self.gripper_name}.pos"
        if key in transition.action:
            value = transition.action[key]
            min_val, max_val = self.gripper_range
            
            # Normalize to [0, 1]
            normalized = (value - min_val) / (max_val - min_val)
            
            # Scale to output range
            out_min, out_max = self.output_range
            scaled = normalized * (out_max - out_min) + out_min
            
            transition.action[key] = scaled
        
        return transition
    
    def inverse(self, transition: EnvTransition) -> EnvTransition:
        """Denormalize gripper position."""
        key = f"{self.gripper_name}.pos"
        if key in transition.action:
            value = transition.action[key]
            min_val, max_val = self.gripper_range
            
            # Scale from output range to [0, 1]
            out_min, out_max = self.output_range
            normalized = (value - out_min) / (out_max - out_min)
            
            # Denormalize to original range
            denormalized = normalized * (max_val - min_val) + min_val
            
            transition.action[key] = denormalized
        
        return transition


class RoarmActionSafety(ProcessorStep):
    """
    Apply safety constraints to actions.
    
    This includes velocity limiting and position clamping.
    """
    
    def __init__(
        self,
        joint_names: list[str],
        max_joint_velocity: float = 3.0,  # rad/s
        max_gripper_velocity: float = 2.0,  # rad/s
        gripper_name: str = "gripper",
        dt: float = 0.1,  # time step in seconds
    ):
        """
        Args:
            joint_names: List of joint names
            max_joint_velocity: Maximum joint velocity in rad/s
            max_gripper_velocity: Maximum gripper velocity in rad/s
            gripper_name: Name of gripper
            dt: Time step for velocity calculation
        """
        super().__init__()
        self.joint_names = joint_names
        self.max_joint_velocity = max_joint_velocity
        self.max_gripper_velocity = max_gripper_velocity
        self.gripper_name = gripper_name
        self.dt = dt
        self.last_positions = {}
    
    def forward(self, transition: EnvTransition) -> EnvTransition:
        """Apply safety constraints."""
        # Check joint velocities
        for joint_name in self.joint_names:
            key = f"{joint_name}.pos"
            if key in transition.action:
                target_pos = transition.action[key]
                
                # Limit velocity if we have last position
                if key in self.last_positions:
                    last_pos = self.last_positions[key]
                    max_delta = self.max_joint_velocity * self.dt
                    delta = target_pos - last_pos
                    
                    if abs(delta) > max_delta:
                        # Clamp the delta
                        delta = np.sign(delta) * max_delta
                        target_pos = last_pos + delta
                        transition.action[key] = target_pos
                
                self.last_positions[key] = target_pos
        
        # Check gripper velocity
        gripper_key = f"{self.gripper_name}.pos"
        if gripper_key in transition.action:
            target_pos = transition.action[gripper_key]
            
            if gripper_key in self.last_positions:
                last_pos = self.last_positions[gripper_key]
                max_delta = self.max_gripper_velocity * self.dt
                delta = target_pos - last_pos
                
                if abs(delta) > max_delta:
                    delta = np.sign(delta) * max_delta
                    target_pos = last_pos + delta
                    transition.action[gripper_key] = target_pos
            
            self.last_positions[gripper_key] = target_pos
        
        return transition
    
    def inverse(self, transition: EnvTransition) -> EnvTransition:
        """Safety is only applied in forward direction."""
        return transition


def create_roarm_action_processor(
    joint_names: list[str],
    gripper_name: str = "gripper",
    normalize: bool = True,
    apply_safety: bool = True,
) -> RobotProcessorPipeline:
    """
    Create a standard action processing pipeline for Roarm.
    
    Args:
        joint_names: List of joint names
        gripper_name: Name of gripper
        normalize: Whether to normalize joint/gripper values
        apply_safety: Whether to apply safety constraints
        
    Returns:
        Configured processor pipeline
    """
    steps = []
    
    if normalize:
        steps.append(RoarmJointNormalizer(joint_names=joint_names))
        steps.append(RoarmGripperNormalizer(gripper_name=gripper_name))
    
    if apply_safety:
        steps.append(RoarmActionSafety(
            joint_names=joint_names,
            gripper_name=gripper_name
        ))
    
    return RobotProcessorPipeline(steps=steps)


def create_roarm_observation_processor(
    joint_names: list[str],
    gripper_name: str = "gripper",
    normalize: bool = True,
) -> RobotProcessorPipeline:
    """
    Create a standard observation processing pipeline for Roarm.
    
    Args:
        joint_names: List of joint names
        gripper_name: Name of gripper
        normalize: Whether to normalize joint/gripper values
        
    Returns:
        Configured processor pipeline
    """
    steps = []
    
    if normalize:
        steps.append(RoarmJointNormalizer(joint_names=joint_names))
        steps.append(RoarmGripperNormalizer(gripper_name=gripper_name))
    
    return RobotProcessorPipeline(steps=steps)
