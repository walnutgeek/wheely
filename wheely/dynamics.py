"""Dynamics simulation for the wheely platform.

Includes actuation strategies and time integration for arm pivot dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from wheely.geometry import PlatformConfig


@dataclass
class SimState:
    """Mutable simulation state."""

    body_xy: tuple[float, float] = (0.0, 0.0)
    body_yaw: float = 0.0
    arm_pivots: tuple[float, float] = (0.0, 0.0)
    arm_velocities: tuple[float, float] = (0.0, 0.0)
    steerings: tuple[float, float, float] = (0.0, 0.0, 0.0)
    time: float = 0.0

    @classmethod
    def from_config(cls, config: PlatformConfig) -> SimState:
        return cls()


class PassiveStrategy:
    """No actuation -- arms pivot freely."""

    def compute_torques(self, state: SimState) -> tuple[float, float]:
        return (0.0, 0.0)


@dataclass
class ActiveStrategy:
    """PID-like control to target arm angles."""

    target_pivots: tuple[float, float] = (0.0, 0.0)
    kp: float = 10.0

    def compute_torques(self, state: SimState) -> tuple[float, float]:
        error_b = state.arm_pivots[0] - self.target_pivots[0]
        error_c = state.arm_pivots[1] - self.target_pivots[1]
        return (-self.kp * error_b, -self.kp * error_c)


@dataclass
class SpringDamperStrategy:
    """Spring return + viscous damping around neutral position."""

    stiffness: float = 100.0
    damping: float = 10.0
    rest_pivots: tuple[float, float] = (0.0, 0.0)

    def compute_torques(self, state: SimState) -> tuple[float, float]:
        disp_b = state.arm_pivots[0] - self.rest_pivots[0]
        disp_c = state.arm_pivots[1] - self.rest_pivots[1]
        vel_b, vel_c = state.arm_velocities
        torque_b = -self.stiffness * disp_b - self.damping * vel_b
        torque_c = -self.stiffness * disp_c - self.damping * vel_c
        return (torque_b, torque_c)


def simulate_step(
    state: SimState,
    config: PlatformConfig,
    terrain,
    strategy,
    dt: float = 0.01,
    arm_inertia: float = 1.0,
) -> SimState:
    """Advance simulation by one time step using semi-implicit Euler."""
    torques = strategy.compute_torques(state)

    gravity = 9.81
    arm_mass = 2.0
    grav_torque_b = -arm_mass * gravity * config.arm_length * 0.5 * np.cos(state.arm_pivots[0])
    grav_torque_c = -arm_mass * gravity * config.arm_length * 0.5 * np.cos(state.arm_pivots[1])

    net_b = torques[0] + grav_torque_b
    net_c = torques[1] + grav_torque_c

    acc_b = net_b / arm_inertia
    acc_c = net_c / arm_inertia
    new_vel_b = state.arm_velocities[0] + acc_b * dt
    new_vel_c = state.arm_velocities[1] + acc_c * dt
    new_pivot_b = state.arm_pivots[0] + new_vel_b * dt
    new_pivot_c = state.arm_pivots[1] + new_vel_c * dt

    limit = config.pivot_range
    new_pivot_b = float(np.clip(new_pivot_b, -limit, limit))
    new_pivot_c = float(np.clip(new_pivot_c, -limit, limit))
    if abs(new_pivot_b) >= limit:
        new_vel_b = 0.0
    if abs(new_pivot_c) >= limit:
        new_vel_c = 0.0

    return SimState(
        body_xy=state.body_xy,
        body_yaw=state.body_yaw,
        arm_pivots=(new_pivot_b, new_pivot_c),
        arm_velocities=(new_vel_b, new_vel_c),
        steerings=state.steerings,
        time=state.time + dt,
    )
