"""Forward and inverse kinematics for the wheely platform."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize_scalar

from wheely.geometry import (
    PlatformConfig,
    compute_brace_center,
    compute_wheel_positions,
)


@dataclass
class FKResult:
    """Result of forward kinematics computation."""

    wheel_contacts: dict[str, np.ndarray]
    wheel_headings: dict[str, float]
    brace_center: np.ndarray
    tilt_pitch: float
    tilt_roll: float
    arm_reaches: tuple[float, float]


@dataclass
class IKResult:
    """Result of inverse kinematics computation."""

    tilt_pitch: float
    tilt_roll: float
    arm_reaches: tuple[float, float]
    body_z: float
    levelness: float


def forward_kinematics(
    config: PlatformConfig,
    tilt_pitch: float = 0.0,
    tilt_roll: float = 0.0,
    arm_reaches: tuple[float, float] = (0.0, 0.0),
    steerings: tuple[float, float, float] = (0.0, 0.0, 0.0),
    *,
    arm_pivots: tuple[float, float] | None = None,
) -> FKResult:
    """Compute wheel positions and brace center from tilt, reaches, and steering.

    Args:
        config: Platform geometry parameters.
        tilt_pitch: Shared pitch tilt angle (radians).
        tilt_roll: Shared roll tilt angle (radians).
        arm_reaches: (reach_b, reach_c) angles in radians.
        steerings: (steer_a, steer_b, steer_c) wheel steering angles.
        arm_pivots: DEPRECATED. If provided, used as arm_reaches with zero tilt
            for backward compatibility.

    Returns:
        FKResult with wheel positions, headings, brace center, and DOF values.
    """
    if arm_pivots is not None:
        arm_reaches = arm_pivots
        tilt_pitch = 0.0
        tilt_roll = 0.0

    wheels = compute_wheel_positions(
        config, tilt_pitch=tilt_pitch, tilt_roll=tilt_roll, arm_reaches=arm_reaches
    )
    brace = compute_brace_center(
        config, tilt_pitch=tilt_pitch, tilt_roll=tilt_roll, arm_reaches=arm_reaches
    )
    headings = {"A": steerings[0], "B": steerings[1], "C": steerings[2]}
    return FKResult(
        wheel_contacts=wheels,
        wheel_headings=headings,
        brace_center=brace,
        tilt_pitch=tilt_pitch,
        tilt_roll=tilt_roll,
        arm_reaches=arm_reaches,
    )


def inverse_kinematics(
    config: PlatformConfig,
    terrain,
    body_xy: tuple[float, float] = (0.0, 0.0),
    body_yaw: float = 0.0,
) -> IKResult:
    """Solve arm reach angles to place wheels B and C on terrain.

    IK assumes vertical shafts (tilt_pitch=0, tilt_roll=0) and solves only
    the reach angles that place each wheel on the terrain surface.

    Wheel A is at the body origin projected onto terrain.
    """
    bx, by = body_xy
    body_z = terrain.height(bx, by)

    def _solve_reach(splay_sign: float) -> float:
        splay = config.arm_splay_angle

        def _error(reach: float) -> float:
            dx = config.arm_length * np.cos(splay) * np.cos(reach)
            dy = config.arm_length * splay_sign * np.sin(splay) * np.cos(reach)
            dz = -config.arm_length * np.sin(reach)
            cos_y, sin_y = np.cos(body_yaw), np.sin(body_yaw)
            wx = bx + cos_y * dx - sin_y * dy
            wy = by + sin_y * dx + cos_y * dy
            wz = body_z + dz
            terrain_z = terrain.height(wx, wy)
            return (wz - terrain_z) ** 2

        result = minimize_scalar(
            _error,
            bounds=(-config.pivot_range, config.pivot_range),
            method="bounded",
        )
        return float(result.x)

    reach_b = _solve_reach(-1.0)
    reach_c = _solve_reach(1.0)

    brace = compute_brace_center(
        config, tilt_pitch=0.0, tilt_roll=0.0, arm_reaches=(reach_b, reach_c)
    )
    levelness = float(abs(brace[2]))

    return IKResult(
        tilt_pitch=0.0,
        tilt_roll=0.0,
        arm_reaches=(reach_b, reach_c),
        body_z=body_z,
        levelness=levelness,
    )


def compute_support_triangle(
    wheel_contacts: dict[str, np.ndarray],
) -> np.ndarray:
    """Compute the support triangle from wheel contact points (XY projection)."""
    return np.array([
        wheel_contacts["A"][:2],
        wheel_contacts["B"][:2],
        wheel_contacts["C"][:2],
    ])


def compute_stability_margin(
    cog: np.ndarray,
    triangle: np.ndarray,
) -> float:
    """Compute stability margin: signed distance from CoG to nearest triangle edge.

    Positive = inside (stable). Negative = outside (tipping).
    """
    p = cog[:2]
    min_dist = float("inf")

    for i in range(3):
        a = triangle[i]
        b = triangle[(i + 1) % 3]
        edge = b - a
        to_point = p - a
        cross = edge[0] * to_point[1] - edge[1] * to_point[0]
        edge_len = np.linalg.norm(edge)
        if edge_len < 1e-12:
            continue
        signed_dist = cross / edge_len
        min_dist = min(min_dist, signed_dist)

    return float(min_dist)
