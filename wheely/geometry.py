"""Parametric geometry for the wheely tricycle platform.

Coordinate system: right-hand, Z-up.
Origin at Wheel A (apex). X points rearward (toward B/C), Y points left, Z up.

Arms extend from the origin (Wheel A) rearward. Arm 1 goes to Wheel B (right, -Y),
Arm 2 goes to Wheel C (left, +Y). The splay angle is measured from the X axis
in the XY plane.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class PlatformConfig:
    """All tunable parameters of the platform geometry."""

    arm_length: float = 0.8
    arm_splay_angle: float = np.radians(40)
    brace_position: float = 0.5
    brace_length: float = 0.5
    wheel_radius: float = 0.15
    wheel_width: float = 0.08
    pivot_range: float = np.radians(45)
    steering_range: float = np.radians(90)

    def validate(self) -> list[str]:
        """Return a list of validation error strings (empty if valid)."""
        errors: list[str] = []
        if not 0.3 <= self.arm_length <= 1.5:
            errors.append(f"arm_length {self.arm_length} outside [0.3, 1.5]")
        if not np.radians(20) <= self.arm_splay_angle <= np.radians(60):
            errors.append(
                f"arm_splay_angle {np.degrees(self.arm_splay_angle):.1f}deg outside [20, 60]"
            )
        if not 0.3 <= self.brace_position <= 0.7:
            errors.append(f"brace_position {self.brace_position} outside [0.3, 0.7]")
        if not 0.2 <= self.brace_length <= 1.0:
            errors.append(f"brace_length {self.brace_length} outside [0.2, 1.0]")
        if not 0.05 <= self.wheel_radius <= 0.3:
            errors.append(f"wheel_radius {self.wheel_radius} outside [0.05, 0.3]")
        if not 0.03 <= self.wheel_width <= 0.15:
            errors.append(f"wheel_width {self.wheel_width} outside [0.03, 0.15]")
        return errors

    def to_dict(self) -> dict:
        """Serialize to a plain dict (for JSON transport)."""
        return {
            "arm_length": self.arm_length,
            "arm_splay_angle": self.arm_splay_angle,
            "brace_position": self.brace_position,
            "brace_length": self.brace_length,
            "wheel_radius": self.wheel_radius,
            "wheel_width": self.wheel_width,
            "pivot_range": self.pivot_range,
            "steering_range": self.steering_range,
        }


def compute_wheel_positions(
    config: PlatformConfig,
    arm_pivots: tuple[float, float] = (0.0, 0.0),
) -> dict[str, np.ndarray]:
    """Compute wheel A, B, C positions in the body frame.

    Args:
        config: Platform geometry parameters.
        arm_pivots: (pivot_b, pivot_c) angles in radians. Positive = wheel moves down.

    Returns:
        Dict with keys "A", "B", "C" mapping to 3D position arrays.
    """
    wheel_a = np.array([0.0, 0.0, 0.0])
    splay = config.arm_splay_angle
    pivot_b, pivot_c = arm_pivots

    # Arm to Wheel B (right side, -Y direction)
    wheel_b = wheel_a + config.arm_length * np.array([
        np.cos(splay) * np.cos(pivot_b),
        -np.sin(splay) * np.cos(pivot_b),
        -np.sin(pivot_b),
    ])

    # Arm to Wheel C (left side, +Y direction)
    wheel_c = wheel_a + config.arm_length * np.array([
        np.cos(splay) * np.cos(pivot_c),
        np.sin(splay) * np.cos(pivot_c),
        -np.sin(pivot_c),
    ])

    return {"A": wheel_a, "B": wheel_b, "C": wheel_c}


def compute_brace_endpoints(
    config: PlatformConfig,
    arm_pivots: tuple[float, float] = (0.0, 0.0),
) -> tuple[np.ndarray, np.ndarray]:
    """Compute cross brace attachment points on each arm.

    Returns:
        (point_on_arm_b, point_on_arm_c) as 3D arrays.
    """
    wheels = compute_wheel_positions(config, arm_pivots)
    t = config.brace_position
    point_b = wheels["A"] + t * (wheels["B"] - wheels["A"])
    point_c = wheels["A"] + t * (wheels["C"] - wheels["A"])
    return point_b, point_c


def compute_brace_center(
    config: PlatformConfig,
    arm_pivots: tuple[float, float] = (0.0, 0.0),
) -> np.ndarray:
    """Compute center of the cross brace (primary cargo mount)."""
    left, right = compute_brace_endpoints(config, arm_pivots)
    return (left + right) / 2.0
