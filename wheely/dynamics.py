"""Dynamics simulation for the wheely platform.

Two-axis tilt model with arm reaches, gravity torques, terrain contact
penalty forces, hard surface clamping, and active leveling strategies.

Degrees of freedom:
- tilt_pitch: rotation around Y axis (tips platform forward/backward)
- tilt_roll: rotation around X axis (tips platform left/right)
- arm_reaches: (reach_b, reach_c) angles controlling how far each arm extends down

Strategies return 4-tuple: (torque_pitch, torque_roll, torque_reach_b, torque_reach_c)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq

from wheely.geometry import PlatformConfig, compute_wheel_positions, tilt_rotation_matrix


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
_M = 5.0        # Body mass (kg)
_G = 9.81       # Gravity (m/s^2)
_L_COG = 0.3    # Distance from pivot to center-of-gravity along arm (m)

_CONTACT_STIFFNESS = 5000.0
_CONTACT_DAMPING = 100.0


# ---------------------------------------------------------------------------
# SimState
# ---------------------------------------------------------------------------
@dataclass
class SimState:
    """Mutable simulation state."""

    body_xy: tuple[float, float] = (0.0, 0.0)
    body_yaw: float = 0.0
    tilt_pitch: float = 0.0
    tilt_roll: float = 0.0
    tilt_pitch_velocity: float = 0.0
    tilt_roll_velocity: float = 0.0
    arm_reaches: tuple[float, float] = (0.0, 0.0)
    arm_reach_velocities: tuple[float, float] = (0.0, 0.0)
    steerings: tuple[float, float, float] = (0.0, 0.0, 0.0)
    time: float = 0.0
    cumulative_energy: float = 0.0

    @classmethod
    def from_config(cls, config: PlatformConfig) -> SimState:
        return cls()


# ---------------------------------------------------------------------------
# StepMetrics
# ---------------------------------------------------------------------------
@dataclass
class StepMetrics:
    """Metrics produced by a single simulation step."""

    tilt_pitch_deg: float = 0.0
    tilt_roll_deg: float = 0.0
    tilt_total_deg: float = 0.0
    actuator_torque_pitch: float = 0.0
    actuator_torque_roll: float = 0.0
    actuator_power: float = 0.0
    cumulative_energy: float = 0.0
    reach_b_deg: float = 0.0
    reach_c_deg: float = 0.0
    in_contact_b: bool = False
    in_contact_c: bool = False


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------
class PassiveStrategy:
    """No actuation -- platform tilts freely."""

    def compute_torques(self, state: SimState) -> tuple[float, float, float, float]:
        return (0.0, 0.0, 0.0, 0.0)


@dataclass
class ActiveArmsLeveling:
    """PD controller on both tilt axes to keep platform level."""

    kp: float = 10.0
    kd: float = 1.0

    def compute_torques(self, state: SimState) -> tuple[float, float, float, float]:
        torque_pitch = -self.kp * state.tilt_pitch - self.kd * state.tilt_pitch_velocity
        torque_roll = -self.kp * state.tilt_roll - self.kd * state.tilt_roll_velocity
        return (torque_pitch, torque_roll, 0.0, 0.0)


@dataclass
class ActiveBraceLeveling:
    """PD controller on roll axis only (via brace mechanism)."""

    kp_roll: float = 10.0
    kd_roll: float = 1.0
    brace_gain: float = 1.0

    def compute_torques(self, state: SimState) -> tuple[float, float, float, float]:
        torque_roll = -self.kp_roll * state.tilt_roll - self.kd_roll * state.tilt_roll_velocity
        return (0.0, torque_roll, 0.0, 0.0)


@dataclass
class SpringDamperStrategy:
    """Spring-damper acting on arm reaches."""

    stiffness: float = 100.0
    damping: float = 10.0
    rest_reaches: tuple[float, float] = (0.0, 0.0)

    def compute_torques(self, state: SimState) -> tuple[float, float, float, float]:
        disp_b = state.arm_reaches[0] - self.rest_reaches[0]
        disp_c = state.arm_reaches[1] - self.rest_reaches[1]
        vel_b, vel_c = state.arm_reach_velocities
        torque_b = -self.stiffness * disp_b - self.damping * vel_b
        torque_c = -self.stiffness * disp_c - self.damping * vel_c
        return (0.0, 0.0, torque_b, torque_c)


# ---------------------------------------------------------------------------
# Terrain contact helpers
# ---------------------------------------------------------------------------

def _wheel_z_for_reach(
    config: PlatformConfig,
    tilt_pitch: float,
    tilt_roll: float,
    reach: float,
    splay_sign: float,
    other_reach: float,
    which: str,
) -> float:
    """Compute the Z position of a single wheel given reach angle.

    Args:
        which: "B" or "C" to select which arm.
    """
    if which == "B":
        reaches = (reach, other_reach)
    else:
        reaches = (other_reach, reach)
    wheels = compute_wheel_positions(config, tilt_pitch, tilt_roll, reaches)
    return float(wheels[which][2])


def _wheel_world_z(
    config: PlatformConfig,
    terrain,
    body_xy: tuple[float, float],
    body_yaw: float,
    tilt_pitch: float,
    tilt_roll: float,
    arm_reaches: tuple[float, float],
    which: str,
) -> tuple[float, float, np.ndarray]:
    """Compute world-frame wheel Z and terrain Z for a given wheel.

    Returns:
        (wheel_z_world, terrain_z, wheel_pos_body)
    """
    wheels = compute_wheel_positions(config, tilt_pitch, tilt_roll, arm_reaches)
    wheel_body = wheels[which]

    # Transform to world coordinates
    bx, by = body_xy
    body_z = terrain.height(bx, by)
    cos_y, sin_y = np.cos(body_yaw), np.sin(body_yaw)

    wx = bx + cos_y * wheel_body[0] - sin_y * wheel_body[1]
    wy = by + sin_y * wheel_body[0] + cos_y * wheel_body[1]
    wz = body_z + wheel_body[2]

    terrain_z = terrain.height(wx, wy)
    return float(wz), float(terrain_z), wheel_body


def _compute_contact_for_arm(
    config: PlatformConfig,
    terrain,
    body_xy: tuple[float, float],
    body_yaw: float,
    tilt_pitch: float,
    tilt_roll: float,
    arm_reaches: tuple[float, float],
    which: str,
    reach_velocity: float,
    tilt_pitch_velocity: float,
    tilt_roll_velocity: float,
) -> tuple[float, float, float, bool]:
    """Compute contact torques for one arm.

    Returns:
        (torque_on_pitch, torque_on_roll, torque_on_reach, in_contact)
    """
    wz, terrain_z, wheel_body = _wheel_world_z(
        config, terrain, body_xy, body_yaw, tilt_pitch, tilt_roll, arm_reaches, which
    )

    penetration = terrain_z - wz  # positive when below terrain
    if penetration <= 0:
        return 0.0, 0.0, 0.0, False

    # Contact force magnitude (upward)
    # Use reach velocity as proxy for vertical velocity of wheel
    contact_force = _CONTACT_STIFFNESS * penetration - _CONTACT_DAMPING * reach_velocity

    # Compute Jacobian: how does wheel_z change with each DOF?
    # We use numerical partial derivatives for accuracy with the tilt coupling.
    eps = 1e-6
    splay = config.arm_splay_angle
    idx = 0 if which == "B" else 1
    splay_sign = -1.0 if which == "B" else 1.0

    # d(wheel_z)/d(reach) -- partial derivative
    reach_plus = list(arm_reaches)
    reach_minus = list(arm_reaches)
    reach_plus[idx] = arm_reaches[idx] + eps
    reach_minus[idx] = arm_reaches[idx] - eps
    wz_plus, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                     tilt_pitch, tilt_roll, tuple(reach_plus), which)
    wz_minus, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                      tilt_pitch, tilt_roll, tuple(reach_minus), which)
    dwz_dreach = (wz_plus - wz_minus) / (2 * eps)

    # d(wheel_z)/d(tilt_pitch)
    wz_pp, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                   tilt_pitch + eps, tilt_roll, arm_reaches, which)
    wz_pm, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                   tilt_pitch - eps, tilt_roll, arm_reaches, which)
    dwz_dpitch = (wz_pp - wz_pm) / (2 * eps)

    # d(wheel_z)/d(tilt_roll)
    wz_rp, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                   tilt_pitch, tilt_roll + eps, arm_reaches, which)
    wz_rm, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                   tilt_pitch, tilt_roll - eps, arm_reaches, which)
    dwz_droll = (wz_rp - wz_rm) / (2 * eps)

    # Virtual work principle: generalized torque = F * (dz/dq)
    # Contact force F is upward (positive). If increasing q lowers wheel
    # (dz/dq < 0), torque is negative, correctly opposing the motion that
    # caused penetration.
    torque_reach = contact_force * dwz_dreach
    torque_pitch = contact_force * dwz_dpitch
    torque_roll = contact_force * dwz_droll

    return torque_pitch, torque_roll, torque_reach, True


# ---------------------------------------------------------------------------
# Hard surface clamp
# ---------------------------------------------------------------------------

def _hard_clamp_reach(
    config: PlatformConfig,
    terrain,
    body_xy: tuple[float, float],
    body_yaw: float,
    tilt_pitch: float,
    tilt_roll: float,
    arm_reaches: tuple[float, float],
    which: str,
) -> float | None:
    """If wheel is below terrain, find the reach that places it on the surface.

    Returns the corrected reach, or None if no correction needed.
    """
    wz, terrain_z, _ = _wheel_world_z(
        config, terrain, body_xy, body_yaw, tilt_pitch, tilt_roll, arm_reaches, which
    )

    if wz >= terrain_z - 1e-9:
        return None  # no correction needed

    idx = 0 if which == "B" else 1
    current_reach = arm_reaches[idx]
    limit = config.pivot_range

    # Define function: f(reach) = wheel_z(reach) - terrain_z(reach)
    # We want f(reach) == 0
    def residual(r):
        reaches_test = list(arm_reaches)
        reaches_test[idx] = r
        wz_test, tz_test, _ = _wheel_world_z(
            config, terrain, body_xy, body_yaw,
            tilt_pitch, tilt_roll, tuple(reaches_test), which
        )
        return wz_test - tz_test

    # The wheel goes more negative Z as reach increases (arm extends down).
    # We need to find a reach that brings wheel_z up to terrain_z.
    # Try a bisection: search from current_reach toward -limit (less reach = higher wheel)
    # First check if the range has a sign change
    try:
        # Try bracket: from a smaller reach (wheel higher) to current reach (wheel lower)
        r_low = -limit
        r_high = current_reach

        f_low = residual(r_low)
        f_high = residual(r_high)

        if f_low * f_high > 0:
            # Both same sign: try expanding bracket
            # If f_low > 0 (wheel above terrain at low reach), solution is between
            # If f_low < 0 too, wheel is below terrain even at minimum reach
            if f_low < 0:
                # Can't fix -- clamp to minimum reach
                return float(-limit)
            else:
                # Shouldn't happen -- f_high should be negative
                return current_reach

        solved_reach = brentq(residual, r_low, r_high, xtol=1e-8, maxiter=50)
        return float(solved_reach)
    except (ValueError, RuntimeError):
        # Fallback: just use minimum reach
        return float(-limit)


def _hard_clamp_tilt(
    config: PlatformConfig,
    terrain,
    body_xy: tuple[float, float],
    body_yaw: float,
    tilt_pitch: float,
    tilt_roll: float,
    pitch_vel: float,
    roll_vel: float,
    arm_reaches: tuple[float, float],
) -> tuple[float, float, float, float]:
    """Adjust tilt angles if wheels still penetrate terrain after reach clamping.

    For each penetrating wheel, adjust the tilt component that most affects
    that wheel's Z position, to bring the wheel onto the surface.

    Returns:
        (tilt_pitch, tilt_roll, pitch_vel, roll_vel)
    """
    for _iteration in range(5):  # iterate a few times for convergence
        any_correction = False
        for which in ("B", "C"):
            wz, terrain_z, _ = _wheel_world_z(
                config, terrain, body_xy, body_yaw,
                tilt_pitch, tilt_roll, arm_reaches, which
            )
            if wz >= terrain_z - 1e-9:
                continue

            # Wheel is below terrain. Find which tilt DOF to adjust.
            eps = 1e-5
            # Jacobian of wheel_z w.r.t. tilt_pitch and tilt_roll
            wz_pp, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                          tilt_pitch + eps, tilt_roll, arm_reaches, which)
            wz_pm, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                          tilt_pitch - eps, tilt_roll, arm_reaches, which)
            dwz_dp = (wz_pp - wz_pm) / (2 * eps)

            wz_rp, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                          tilt_pitch, tilt_roll + eps, arm_reaches, which)
            wz_rm, _, _ = _wheel_world_z(config, terrain, body_xy, body_yaw,
                                          tilt_pitch, tilt_roll - eps, arm_reaches, which)
            dwz_dr = (wz_rp - wz_rm) / (2 * eps)

            penetration = terrain_z - wz  # positive amount below surface

            # Use Newton-Raphson: distribute correction proportionally to Jacobian
            jac_sq = dwz_dp**2 + dwz_dr**2
            if jac_sq < 1e-12:
                continue  # can't fix via tilt

            # Delta such that dwz_dp * dp + dwz_dr * dr = penetration
            # Use least-norm solution: dp = dwz_dp * lam, dr = dwz_dr * lam
            # where lam = penetration / jac_sq
            lam = penetration / jac_sq
            dp = dwz_dp * lam
            dr = dwz_dr * lam

            tilt_pitch += dp
            tilt_roll += dr
            any_correction = True

        if not any_correction:
            break

    # Zero velocities if we made corrections
    # Check final state
    for which in ("B", "C"):
        wz, terrain_z, _ = _wheel_world_z(
            config, terrain, body_xy, body_yaw,
            tilt_pitch, tilt_roll, arm_reaches, which
        )
        if wz < terrain_z - 1e-6:
            # Still penetrating -- zero tilt velocities to prevent further divergence
            pitch_vel = 0.0
            roll_vel = 0.0
            break

    return tilt_pitch, tilt_roll, pitch_vel, roll_vel


# ---------------------------------------------------------------------------
# Main simulation step
# ---------------------------------------------------------------------------

def simulate_step(
    state: SimState,
    config: PlatformConfig,
    terrain,
    strategy,
    dt: float = 0.01,
    arm_inertia: float = 1.0,
    tilt_inertia: float = 2.0,
) -> tuple[SimState, StepMetrics]:
    """Advance simulation by one time step using semi-implicit Euler.

    Returns:
        (new_state, metrics) tuple.
    """
    # Get strategy torques: (torque_pitch, torque_roll, torque_reach_b, torque_reach_c)
    torques = strategy.compute_torques(state)
    strat_pitch, strat_roll, strat_reach_b, strat_reach_c = torques

    # --- Gravity torques on tilt axes ---
    # gravity_torque = -M * g * L_cog * sin(tilt)
    grav_torque_pitch = -_M * _G * _L_COG * math.sin(state.tilt_pitch)
    grav_torque_roll = -_M * _G * _L_COG * math.sin(state.tilt_roll)

    # --- Terrain contact torques ---
    contact_pitch_b, contact_roll_b, contact_reach_b, in_contact_b = _compute_contact_for_arm(
        config, terrain, state.body_xy, state.body_yaw,
        state.tilt_pitch, state.tilt_roll, state.arm_reaches, "B",
        state.arm_reach_velocities[0],
        state.tilt_pitch_velocity, state.tilt_roll_velocity,
    )
    contact_pitch_c, contact_roll_c, contact_reach_c, in_contact_c = _compute_contact_for_arm(
        config, terrain, state.body_xy, state.body_yaw,
        state.tilt_pitch, state.tilt_roll, state.arm_reaches, "C",
        state.arm_reach_velocities[1],
        state.tilt_pitch_velocity, state.tilt_roll_velocity,
    )

    # --- Net torques ---
    net_pitch = strat_pitch + grav_torque_pitch + contact_pitch_b + contact_pitch_c
    net_roll = strat_roll + grav_torque_roll + contact_roll_b + contact_roll_c
    net_reach_b = strat_reach_b + contact_reach_b
    net_reach_c = strat_reach_c + contact_reach_c

    # --- Semi-implicit Euler integration ---
    # Tilt
    acc_pitch = net_pitch / tilt_inertia
    acc_roll = net_roll / tilt_inertia
    new_pitch_vel = state.tilt_pitch_velocity + acc_pitch * dt
    new_roll_vel = state.tilt_roll_velocity + acc_roll * dt
    new_tilt_pitch = state.tilt_pitch + new_pitch_vel * dt
    new_tilt_roll = state.tilt_roll + new_roll_vel * dt

    # Reaches
    acc_reach_b = net_reach_b / arm_inertia
    acc_reach_c = net_reach_c / arm_inertia
    new_vel_b = state.arm_reach_velocities[0] + acc_reach_b * dt
    new_vel_c = state.arm_reach_velocities[1] + acc_reach_c * dt
    new_reach_b = state.arm_reaches[0] + new_vel_b * dt
    new_reach_c = state.arm_reaches[1] + new_vel_c * dt

    # --- Hard clamp: ensure no penetration ---
    # Phase 1: Clamp reaches to pivot range first
    limit = config.pivot_range
    new_reach_b = float(np.clip(new_reach_b, -limit, limit))
    new_reach_c = float(np.clip(new_reach_c, -limit, limit))
    if abs(new_reach_b) >= limit - 1e-10:
        new_vel_b = 0.0
    if abs(new_reach_c) >= limit - 1e-10:
        new_vel_c = 0.0

    # Phase 2: Try to fix penetration by adjusting reach
    for which, idx in [("B", 0), ("C", 1)]:
        reaches = (new_reach_b, new_reach_c)
        corrected = _hard_clamp_reach(
            config, terrain, state.body_xy, state.body_yaw,
            new_tilt_pitch, new_tilt_roll, reaches, which
        )
        if corrected is not None:
            corrected = float(np.clip(corrected, -limit, limit))
            if idx == 0:
                new_reach_b = corrected
                new_vel_b = 0.0
            else:
                new_reach_c = corrected
                new_vel_c = 0.0

    # Phase 3: If reach clamp wasn't enough (reach hit limit but still penetrating),
    # adjust tilt to prevent penetration. This handles cases where the tilt
    # has moved the wheel below terrain and reach alone can't fix it.
    new_tilt_pitch, new_tilt_roll, new_pitch_vel, new_roll_vel = _hard_clamp_tilt(
        config, terrain, state.body_xy, state.body_yaw,
        new_tilt_pitch, new_tilt_roll,
        new_pitch_vel, new_roll_vel,
        (new_reach_b, new_reach_c),
    )

    # --- Compute energy ---
    actuator_power = abs(strat_pitch * new_pitch_vel) + abs(strat_roll * new_roll_vel) \
        + abs(strat_reach_b * new_vel_b) + abs(strat_reach_c * new_vel_c)
    new_cumulative_energy = state.cumulative_energy + actuator_power * dt

    # --- Build new state ---
    new_state = SimState(
        body_xy=state.body_xy,
        body_yaw=state.body_yaw,
        tilt_pitch=new_tilt_pitch,
        tilt_roll=new_tilt_roll,
        tilt_pitch_velocity=new_pitch_vel,
        tilt_roll_velocity=new_roll_vel,
        arm_reaches=(new_reach_b, new_reach_c),
        arm_reach_velocities=(new_vel_b, new_vel_c),
        steerings=state.steerings,
        time=state.time + dt,
        cumulative_energy=new_cumulative_energy,
    )

    # --- Build metrics ---
    tilt_pitch_deg = math.degrees(new_tilt_pitch)
    tilt_roll_deg = math.degrees(new_tilt_roll)
    tilt_total_deg = math.degrees(math.sqrt(new_tilt_pitch**2 + new_tilt_roll**2))

    metrics = StepMetrics(
        tilt_pitch_deg=tilt_pitch_deg,
        tilt_roll_deg=tilt_roll_deg,
        tilt_total_deg=tilt_total_deg,
        actuator_torque_pitch=strat_pitch,
        actuator_torque_roll=strat_roll,
        actuator_power=actuator_power,
        cumulative_energy=new_cumulative_energy,
        reach_b_deg=math.degrees(new_reach_b),
        reach_c_deg=math.degrees(new_reach_c),
        in_contact_b=in_contact_b,
        in_contact_c=in_contact_c,
    )

    return new_state, metrics
