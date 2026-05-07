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
    arm_pivots: tuple[float, float]


@dataclass
class IKResult:
    """Result of inverse kinematics computation."""

    arm_pivots: tuple[float, float]
    body_z: float
    levelness: float


def forward_kinematics(
    config: PlatformConfig,
    arm_pivots: tuple[float, float] = (0.0, 0.0),
    steerings: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> FKResult:
    """Compute wheel positions and brace center from arm pivots and steering."""
    wheels = compute_wheel_positions(config, arm_pivots)
    brace = compute_brace_center(config, arm_pivots)
    headings = {"A": steerings[0], "B": steerings[1], "C": steerings[2]}
    return FKResult(
        wheel_contacts=wheels,
        wheel_headings=headings,
        brace_center=brace,
        arm_pivots=arm_pivots,
    )


def inverse_kinematics(
    config: PlatformConfig,
    terrain,
    body_xy: tuple[float, float] = (0.0, 0.0),
    body_yaw: float = 0.0,
) -> IKResult:
    """Solve arm pivot angles to place wheels B and C on terrain.

    Wheel A is at the body origin projected onto terrain.
    """
    bx, by = body_xy
    body_z = terrain.height(bx, by)

    def _solve_pivot(splay_sign: float) -> float:
        splay = config.arm_splay_angle

        def _error(pivot: float) -> float:
            dx = config.arm_length * np.cos(splay) * np.cos(pivot)
            dy = config.arm_length * splay_sign * np.sin(splay) * np.cos(pivot)
            dz = -config.arm_length * np.sin(pivot)
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

    pivot_b = _solve_pivot(-1.0)
    pivot_c = _solve_pivot(1.0)

    brace = compute_brace_center(config, (pivot_b, pivot_c))
    levelness = float(abs(brace[2]))

    return IKResult(
        arm_pivots=(pivot_b, pivot_c),
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
