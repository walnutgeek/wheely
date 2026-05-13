# Dynamics Rework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the independent arm pivot model with a parallelogram-constrained two-axis tilt model, add hard surface constraints, gravity tipping, and two active leveling strategies with metrics.

**Architecture:** geometry.py gets a tilt rotation matrix and new wheel position computation. dynamics.py gets a completely rewritten SimState, new strategies, and revised simulate_step with hard surface clamp. kinematics.py IK solver adapts to the new DOF space. server.py and frontend updated for new state format, strategies, and metrics chart.

**Tech Stack:** Python (numpy, scipy), JavaScript (Three.js, Canvas 2D for charts)

---

### Task 1: Update geometry.py -- tilt rotation and wheel positions

**Files:**
- Modify: `wheely/geometry.py`
- Test: `tests/test_geometry.py`

- [ ] **Step 1: Write failing tests for the new geometry API**

Replace the contents of `tests/test_geometry.py`:

```python
"""Tests for wheely.geometry module."""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from wheely.geometry import (
    PlatformConfig,
    compute_wheel_positions,
    compute_brace_endpoints,
    compute_brace_center,
    tilt_rotation_matrix,
)


class TestPlatformConfig:
    def test_defaults_are_valid(self):
        config = PlatformConfig()
        errors = config.validate()
        assert errors == []

    def test_arm_length_too_short(self):
        config = PlatformConfig(arm_length=0.1)
        errors = config.validate()
        assert any("arm_length" in e for e in errors)

    def test_arm_length_too_long(self):
        config = PlatformConfig(arm_length=2.0)
        errors = config.validate()
        assert any("arm_length" in e for e in errors)

    def test_brace_position_out_of_range(self):
        config = PlatformConfig(brace_position=0.1)
        errors = config.validate()
        assert any("brace_position" in e for e in errors)


class TestTiltRotationMatrix:
    def test_identity_at_zero(self):
        R = tilt_rotation_matrix(0.0, 0.0)
        np.testing.assert_array_almost_equal(R, np.eye(3))

    def test_pitch_only_rotates_xz(self):
        R = tilt_rotation_matrix(tilt_pitch=0.3, tilt_roll=0.0)
        # Pure pitch: Y component unchanged for unit Y vector
        v = R @ np.array([0.0, 1.0, 0.0])
        assert v[1] == pytest.approx(1.0, abs=1e-10)

    def test_roll_only_rotates_yz(self):
        R = tilt_rotation_matrix(tilt_pitch=0.0, tilt_roll=0.3)
        # Pure roll: X component unchanged for unit X vector
        v = R @ np.array([1.0, 0.0, 0.0])
        assert v[0] == pytest.approx(1.0, abs=1e-10)

    def test_determinant_is_one(self):
        R = tilt_rotation_matrix(0.2, 0.3)
        assert np.linalg.det(R) == pytest.approx(1.0, abs=1e-10)


class TestWheelPositions:
    def test_wheel_a_at_origin(self):
        config = PlatformConfig()
        wheels = compute_wheel_positions(config)
        np.testing.assert_array_almost_equal(wheels["A"], [0.0, 0.0, 0.0])

    def test_wheels_b_and_c_symmetric_at_zero_tilt(self):
        config = PlatformConfig()
        wheels = compute_wheel_positions(config, tilt_pitch=0.0, tilt_roll=0.0,
                                         arm_reaches=(0.0, 0.0))
        assert wheels["B"][1] < 0
        assert wheels["C"][1] > 0
        np.testing.assert_almost_equal(wheels["B"][0], wheels["C"][0])
        np.testing.assert_almost_equal(wheels["B"][1], -wheels["C"][1])
        np.testing.assert_almost_equal(wheels["B"][2], wheels["C"][2])

    def test_arm_length_determines_distance(self):
        config = PlatformConfig(arm_length=1.0)
        wheels = compute_wheel_positions(config, tilt_pitch=0.0, tilt_roll=0.0,
                                         arm_reaches=(0.0, 0.0))
        dist_b = np.linalg.norm(wheels["B"] - wheels["A"])
        dist_c = np.linalg.norm(wheels["C"] - wheels["A"])
        assert dist_b == pytest.approx(1.0, abs=1e-10)
        assert dist_c == pytest.approx(1.0, abs=1e-10)

    def test_reach_moves_wheels_down(self):
        config = PlatformConfig()
        wheels_zero = compute_wheel_positions(config, tilt_pitch=0.0, tilt_roll=0.0,
                                              arm_reaches=(0.0, 0.0))
        wheels_down = compute_wheel_positions(config, tilt_pitch=0.0, tilt_roll=0.0,
                                              arm_reaches=(0.3, 0.3))
        assert wheels_down["B"][2] < wheels_zero["B"][2]
        assert wheels_down["C"][2] < wheels_zero["C"][2]

    def test_asymmetric_reaches(self):
        config = PlatformConfig()
        wheels = compute_wheel_positions(config, tilt_pitch=0.0, tilt_roll=0.0,
                                         arm_reaches=(0.3, 0.0))
        wheels_zero = compute_wheel_positions(config, tilt_pitch=0.0, tilt_roll=0.0,
                                              arm_reaches=(0.0, 0.0))
        assert wheels["B"][2] < wheels_zero["B"][2]
        np.testing.assert_array_almost_equal(wheels["C"], wheels_zero["C"])

    def test_pitch_tilt_moves_both_wheels_same_direction(self):
        """Pitch tilt should move both B and C in the same Z direction."""
        config = PlatformConfig()
        w0 = compute_wheel_positions(config, tilt_pitch=0.0, tilt_roll=0.0,
                                     arm_reaches=(0.0, 0.0))
        w1 = compute_wheel_positions(config, tilt_pitch=0.2, tilt_roll=0.0,
                                     arm_reaches=(0.0, 0.0))
        delta_b = w1["B"][2] - w0["B"][2]
        delta_c = w1["C"][2] - w0["C"][2]
        # Both should move in the same direction
        assert delta_b * delta_c > 0

    def test_roll_tilt_moves_wheels_opposite_z(self):
        """Roll tilt should move B and C in opposite Z directions."""
        config = PlatformConfig()
        w0 = compute_wheel_positions(config, tilt_pitch=0.0, tilt_roll=0.0,
                                     arm_reaches=(0.0, 0.0))
        w1 = compute_wheel_positions(config, tilt_pitch=0.0, tilt_roll=0.2,
                                     arm_reaches=(0.0, 0.0))
        delta_b = w1["B"][2] - w0["B"][2]
        delta_c = w1["C"][2] - w0["C"][2]
        # Should move in opposite directions
        assert delta_b * delta_c < 0

    def test_backward_compat_default_args(self):
        """compute_wheel_positions() with no args should still work."""
        config = PlatformConfig()
        wheels = compute_wheel_positions(config)
        assert "A" in wheels and "B" in wheels and "C" in wheels


class TestBraceEndpoints:
    def test_brace_midway_on_arms(self):
        config = PlatformConfig(brace_position=0.5)
        wheels = compute_wheel_positions(config)
        left, right = compute_brace_endpoints(config)
        expected_left = (wheels["A"] + wheels["B"]) / 2.0
        expected_right = (wheels["A"] + wheels["C"]) / 2.0
        np.testing.assert_array_almost_equal(left, expected_left)
        np.testing.assert_array_almost_equal(right, expected_right)

    def test_brace_center_on_centerline(self):
        config = PlatformConfig()
        center = compute_brace_center(config)
        assert center[1] == pytest.approx(0.0, abs=1e-10)


@given(
    arm_length=st.floats(min_value=0.3, max_value=1.5),
    splay_deg=st.floats(min_value=20, max_value=60),
    brace_pos=st.floats(min_value=0.3, max_value=0.7),
)
@settings(max_examples=50)
def test_random_configs_produce_valid_geometry(arm_length, splay_deg, brace_pos):
    config = PlatformConfig(
        arm_length=arm_length,
        arm_splay_angle=np.radians(splay_deg),
        brace_position=brace_pos,
    )
    wheels = compute_wheel_positions(config)
    for name in ("A", "B", "C"):
        assert np.all(np.isfinite(wheels[name]))
    for name in ("B", "C"):
        dist = np.linalg.norm(wheels[name] - wheels["A"])
        assert dist == pytest.approx(arm_length, abs=1e-9)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_geometry.py -v`
Expected: Failures on `tilt_rotation_matrix` import and new API calls.

- [ ] **Step 3: Implement the new geometry**

Rewrite `wheely/geometry.py`. Keep `PlatformConfig` and `validate()` and `to_dict()` unchanged. Replace `compute_wheel_positions` to accept the new tilt/reach parameters (with backward-compatible defaults). Add `tilt_rotation_matrix`.

```python
"""Parametric geometry for the wheely tricycle platform.

Coordinate system: right-hand, Z-up.
Origin at Wheel A (apex). X points rearward (toward B/C), Y points left, Z up.

Arms extend from the origin (Wheel A) rearward. Arm 1 goes to Wheel B (right, -Y),
Arm 2 goes to Wheel C (left, +Y). The splay angle is measured from the X axis
in the XY plane.

Tilt axes:
- tilt_pitch: rotation around Y axis (parallel to brace). Tips platform forward/backward.
- tilt_roll: rotation around X axis (perpendicular to brace). Tips platform left/right.
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


def tilt_rotation_matrix(tilt_pitch: float = 0.0, tilt_roll: float = 0.0) -> np.ndarray:
    """Compute combined tilt rotation matrix R = Ry(pitch) @ Rx(roll).

    Args:
        tilt_pitch: Rotation around Y axis (tips forward/backward).
        tilt_roll: Rotation around X axis (tips left/right).

    Returns:
        3x3 rotation matrix.
    """
    cp, sp = np.cos(tilt_pitch), np.sin(tilt_pitch)
    cr, sr = np.cos(tilt_roll), np.sin(tilt_roll)

    # Ry(pitch) @ Rx(roll)
    return np.array([
        [cp,      sp * sr,   sp * cr],
        [0.0,     cr,        -sr],
        [-sp,     cp * sr,   cp * cr],
    ])


def compute_wheel_positions(
    config: PlatformConfig,
    tilt_pitch: float = 0.0,
    tilt_roll: float = 0.0,
    arm_reaches: tuple[float, float] = (0.0, 0.0),
    *,
    arm_pivots: tuple[float, float] | None = None,
) -> dict[str, np.ndarray]:
    """Compute wheel A, B, C positions in the body frame.

    Args:
        config: Platform geometry parameters.
        tilt_pitch: Shared pitch tilt angle (radians). 0 = vertical shafts.
        tilt_roll: Shared roll tilt angle (radians). 0 = vertical shafts.
        arm_reaches: (reach_b, reach_c) angles in radians. How far each arm
            extends downward. Positive = wheel moves down.
        arm_pivots: DEPRECATED. If provided, used as arm_reaches with zero tilt
            for backward compatibility.

    Returns:
        Dict with keys "A", "B", "C" mapping to 3D position arrays.
    """
    # Backward compatibility: old code passes arm_pivots=(b, c)
    if arm_pivots is not None:
        arm_reaches = arm_pivots
        tilt_pitch = 0.0
        tilt_roll = 0.0

    wheel_a = np.array([0.0, 0.0, 0.0])
    splay = config.arm_splay_angle
    reach_b, reach_c = arm_reaches

    R = tilt_rotation_matrix(tilt_pitch, tilt_roll)

    def _arm_endpoint(reach: float, splay_sign: float) -> np.ndarray:
        # Arm direction in body frame before tilt
        dx = config.arm_length * np.cos(splay) * np.cos(reach)
        dy = config.arm_length * splay_sign * np.sin(splay) * np.cos(reach)
        dz = -config.arm_length * np.sin(reach)
        offset = np.array([dx, dy, dz])
        # Apply tilt rotation
        return R @ offset

    wheel_b = wheel_a + _arm_endpoint(reach_b, -1.0)
    wheel_c = wheel_a + _arm_endpoint(reach_c, 1.0)

    return {"A": wheel_a, "B": wheel_b, "C": wheel_c}


def compute_brace_endpoints(
    config: PlatformConfig,
    tilt_pitch: float = 0.0,
    tilt_roll: float = 0.0,
    arm_reaches: tuple[float, float] = (0.0, 0.0),
    *,
    arm_pivots: tuple[float, float] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute cross brace attachment points on each arm."""
    wheels = compute_wheel_positions(config, tilt_pitch, tilt_roll, arm_reaches,
                                     arm_pivots=arm_pivots)
    t = config.brace_position
    point_b = wheels["A"] + t * (wheels["B"] - wheels["A"])
    point_c = wheels["A"] + t * (wheels["C"] - wheels["A"])
    return point_b, point_c


def compute_brace_center(
    config: PlatformConfig,
    tilt_pitch: float = 0.0,
    tilt_roll: float = 0.0,
    arm_reaches: tuple[float, float] = (0.0, 0.0),
    *,
    arm_pivots: tuple[float, float] | None = None,
) -> np.ndarray:
    """Compute center of the cross brace (primary cargo mount)."""
    left, right = compute_brace_endpoints(config, tilt_pitch, tilt_roll, arm_reaches,
                                           arm_pivots=arm_pivots)
    return (left + right) / 2.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_geometry.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add wheely/geometry.py tests/test_geometry.py
git commit -m "feat: add two-axis tilt rotation to geometry (pitch + roll)"
```

---

### Task 2: Update dynamics.py -- new SimState, strategies, simulate_step

**Files:**
- Modify: `wheely/dynamics.py`
- Test: `tests/test_dynamics.py`

- [ ] **Step 1: Write failing tests for the new dynamics API**

Replace the contents of `tests/test_dynamics.py`:

```python
"""Tests for wheely.dynamics module."""

import math

import numpy as np
import pytest

from wheely.dynamics import (
    ActiveArmsLeveling,
    ActiveBraceLeveling,
    PassiveStrategy,
    SimState,
    SpringDamperStrategy,
    StepMetrics,
    simulate_step,
)
from wheely.geometry import PlatformConfig, compute_wheel_positions
from wheely.terrain import FlatTerrain, SlopeTerrain, SinusoidalTerrain


class TestSimState:
    def test_from_config_defaults(self):
        state = SimState.from_config(PlatformConfig())
        assert state.tilt_pitch == 0.0
        assert state.tilt_roll == 0.0
        assert state.arm_reaches == (0.0, 0.0)


class TestPassiveStrategy:
    def test_returns_zero_torques(self):
        strategy = PassiveStrategy()
        state = SimState.from_config(PlatformConfig())
        torques = strategy.compute_torques(state)
        assert torques == (0.0, 0.0, 0.0, 0.0)


class TestActiveArmsLeveling:
    def test_pitch_correction(self):
        strategy = ActiveArmsLeveling(kp=10.0, kd=1.0)
        state = SimState.from_config(PlatformConfig())
        state.tilt_pitch = 0.1
        torques = strategy.compute_torques(state)
        # pitch torque should oppose the tilt
        assert torques[0] < 0  # torque_pitch negative to correct positive pitch

    def test_roll_correction(self):
        strategy = ActiveArmsLeveling(kp=10.0, kd=1.0)
        state = SimState.from_config(PlatformConfig())
        state.tilt_roll = 0.1
        torques = strategy.compute_torques(state)
        # roll torque should oppose the tilt
        assert torques[1] < 0  # torque_roll negative to correct positive roll

    def test_zero_tilt_zero_torque(self):
        strategy = ActiveArmsLeveling(kp=10.0, kd=1.0)
        state = SimState.from_config(PlatformConfig())
        torques = strategy.compute_torques(state)
        assert all(t == pytest.approx(0.0) for t in torques)


class TestActiveBraceLeveling:
    def test_roll_correction(self):
        strategy = ActiveBraceLeveling(kp_roll=10.0, kd_roll=1.0)
        state = SimState.from_config(PlatformConfig())
        state.tilt_roll = 0.1
        torques = strategy.compute_torques(state)
        # Should produce roll torque but no direct pitch torque
        assert torques[1] < 0  # roll correction
        assert torques[0] == pytest.approx(0.0)  # no direct pitch control


class TestSpringDamperStrategy:
    def test_spring_force_at_displacement(self):
        strategy = SpringDamperStrategy(stiffness=100.0, damping=5.0)
        state = SimState.from_config(PlatformConfig())
        state.arm_reaches = (0.1, -0.1)
        state.arm_reach_velocities = (0.0, 0.0)
        torques = strategy.compute_torques(state)
        # Spring on reaches: torques[2] and torques[3]
        assert torques[2] == pytest.approx(-10.0)
        assert torques[3] == pytest.approx(10.0)


class TestSimulateStep:
    def test_returns_state_and_metrics(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        strategy = PassiveStrategy()
        state = SimState.from_config(config)
        new_state, metrics = simulate_step(state, config, terrain, strategy, dt=0.01)
        assert isinstance(new_state, SimState)
        assert isinstance(metrics, StepMetrics)

    def test_no_penetration_on_flat(self):
        """Wheels should never go below terrain surface."""
        config = PlatformConfig()
        terrain = FlatTerrain()
        strategy = PassiveStrategy()
        state = SimState.from_config(config)
        for _ in range(200):
            state, _ = simulate_step(state, config, terrain, strategy, dt=0.01)
            wheels = compute_wheel_positions(
                config, state.tilt_pitch, state.tilt_roll, state.arm_reaches)
            for name in ("B", "C"):
                wheel_z = wheels[name][2]
                terrain_z = terrain.height(wheels[name][0], wheels[name][1])
                assert wheel_z >= terrain_z - 1e-6, \
                    f"Wheel {name} penetrated terrain at step: {wheel_z} < {terrain_z}"

    def test_no_penetration_on_bumpy(self):
        """Wheels should never go below terrain on bumpy terrain."""
        config = PlatformConfig()
        terrain = SinusoidalTerrain(amplitude=0.15, wavelength=2.0)
        strategy = PassiveStrategy()
        state = SimState.from_config(config)
        for _ in range(200):
            state, _ = simulate_step(state, config, terrain, strategy, dt=0.01)
            wheels = compute_wheel_positions(
                config, state.tilt_pitch, state.tilt_roll, state.arm_reaches)
            for name in ("B", "C"):
                wheel_z = wheels[name][2]
                terrain_z = terrain.height(wheels[name][0], wheels[name][1])
                assert wheel_z >= terrain_z - 1e-6

    def test_passive_settles_on_flat(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        strategy = PassiveStrategy()
        state = SimState.from_config(config)
        for _ in range(1000):
            state, _ = simulate_step(state, config, terrain, strategy, dt=0.01)
        assert abs(state.arm_reach_velocities[0]) < 0.1
        assert abs(state.arm_reach_velocities[1]) < 0.1

    def test_active_arms_converges_on_forward_slope(self):
        config = PlatformConfig()
        terrain = SlopeTerrain(slope_x=0.3)
        strategy = ActiveArmsLeveling(kp=50.0, kd=10.0)
        state = SimState.from_config(config)
        for _ in range(500):
            state, metrics = simulate_step(state, config, terrain, strategy, dt=0.01)
        assert abs(math.degrees(state.tilt_pitch)) < 5.0

    def test_active_arms_converges_on_cross_slope(self):
        config = PlatformConfig()
        terrain = SlopeTerrain(slope_y=0.3)
        strategy = ActiveArmsLeveling(kp=50.0, kd=10.0)
        state = SimState.from_config(config)
        for _ in range(500):
            state, metrics = simulate_step(state, config, terrain, strategy, dt=0.01)
        assert abs(math.degrees(state.tilt_roll)) < 5.0

    def test_active_brace_converges_roll_on_cross_slope(self):
        config = PlatformConfig()
        terrain = SlopeTerrain(slope_y=0.3)
        strategy = ActiveBraceLeveling(kp_roll=50.0, kd_roll=10.0)
        state = SimState.from_config(config)
        for _ in range(500):
            state, metrics = simulate_step(state, config, terrain, strategy, dt=0.01)
        assert abs(math.degrees(state.tilt_roll)) < 5.0

    def test_metrics_energy_monotonic(self):
        config = PlatformConfig()
        terrain = SlopeTerrain(slope_x=0.2)
        strategy = ActiveArmsLeveling(kp=50.0, kd=10.0)
        state = SimState.from_config(config)
        prev_energy = 0.0
        for _ in range(100):
            state, metrics = simulate_step(state, config, terrain, strategy, dt=0.01)
            assert metrics.cumulative_energy >= prev_energy - 1e-10
            prev_energy = metrics.cumulative_energy
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_dynamics.py -v`
Expected: Import errors and failures.

- [ ] **Step 3: Implement the new dynamics**

Rewrite `wheely/dynamics.py` completely with:
- Revised `SimState` with `tilt_pitch`, `tilt_roll`, `arm_reaches`, etc.
- `StepMetrics` dataclass.
- `PassiveStrategy` returning 4-tuple `(torque_pitch, torque_roll, torque_reach_b, torque_reach_c)`.
- `ActiveArmsLeveling(kp, kd)` -- PD controller on both tilt axes.
- `ActiveBraceLeveling(kp_roll, kd_roll, brace_gain)` -- PD on roll only.
- `SpringDamperStrategy` acting on reaches (torques[2], torques[3]).
- `simulate_step` returning `(SimState, StepMetrics)` with:
  - Gravity torques on both tilt axes.
  - Terrain contact torques (penalty spring, stiffer: 5000/100).
  - Semi-implicit Euler integration.
  - **Hard clamp**: after integration, if wheel is below terrain, solve for the reach that places wheel exactly on surface and zero reach velocity.
  - Energy accumulation in metrics.

Key implementation detail for `_compute_terrain_contact`:
- Compute wheel position from `(tilt_pitch, tilt_roll, reach)` using `compute_wheel_positions`.
- Check penetration. If positive, compute penalty force.
- Decompose contact force into torque contributions on `tilt_pitch`, `tilt_roll`, and `reach` based on the Jacobian (partial derivatives of wheel_z with respect to each DOF).

Key implementation detail for **hard clamp**:
- After integration, compute wheel Z for each arm.
- If `wheel_z < terrain_z`, use a numerical solve (or analytical approximation) to find the reach that places the wheel on the surface:
  - Since `wheel_z ≈ body_z - arm_length * sin(reach)` (ignoring tilt coupling), solve `reach = arcsin((body_z - terrain_z) / arm_length)`.
  - For the exact solution with tilt, compute the tilt-rotated offset and solve for reach.
- Set reach velocity to 0 (inelastic contact).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_dynamics.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add wheely/dynamics.py tests/test_dynamics.py
git commit -m "feat: rewrite dynamics with two-axis tilt, hard surface clamp, active leveling"
```

---

### Task 3: Update kinematics.py -- IK solver for new DOF space

**Files:**
- Modify: `wheely/kinematics.py`
- Test: `tests/test_kinematics.py`

- [ ] **Step 1: Write failing tests for the new kinematics API**

Replace `tests/test_kinematics.py`:

```python
"""Tests for wheely.kinematics module."""

import numpy as np
import pytest

from wheely.geometry import PlatformConfig, compute_wheel_positions
from wheely.kinematics import (
    forward_kinematics,
    inverse_kinematics,
    compute_support_triangle,
    compute_stability_margin,
)
from wheely.terrain import FlatTerrain, SlopeTerrain


class TestForwardKinematics:
    def test_flat_ground_zero_tilt(self):
        config = PlatformConfig()
        result = forward_kinematics(config, tilt_pitch=0.0, tilt_roll=0.0,
                                    arm_reaches=(0.0, 0.0))
        for name in ("A", "B", "C"):
            assert np.all(np.isfinite(result.wheel_contacts[name]))
        assert np.all(np.isfinite(result.brace_center))

    def test_steerings_dont_affect_positions(self):
        config = PlatformConfig()
        r1 = forward_kinematics(config, tilt_pitch=0.0, tilt_roll=0.0,
                                arm_reaches=(0.0, 0.0), steerings=(0.0, 0.0, 0.0))
        r2 = forward_kinematics(config, tilt_pitch=0.0, tilt_roll=0.0,
                                arm_reaches=(0.0, 0.0), steerings=(0.5, -0.3, 0.2))
        for name in ("A", "B", "C"):
            np.testing.assert_array_almost_equal(
                r1.wheel_contacts[name], r2.wheel_contacts[name]
            )

    def test_reach_changes_wheel_z(self):
        config = PlatformConfig()
        r_zero = forward_kinematics(config, tilt_pitch=0.0, tilt_roll=0.0,
                                    arm_reaches=(0.0, 0.0))
        r_down = forward_kinematics(config, tilt_pitch=0.0, tilt_roll=0.0,
                                    arm_reaches=(0.3, 0.0))
        assert r_down.wheel_contacts["B"][2] < r_zero.wheel_contacts["B"][2]

    def test_backward_compat_arm_pivots(self):
        config = PlatformConfig()
        result = forward_kinematics(config, arm_pivots=(0.1, 0.2),
                                    steerings=(0.0, 0.0, 0.0))
        assert "A" in result.wheel_contacts


class TestInverseKinematics:
    def test_flat_terrain_gives_zero_reaches(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        result = inverse_kinematics(config, terrain, body_xy=(0.0, 0.0))
        assert result.arm_reaches[0] == pytest.approx(0.0, abs=0.02)
        assert result.arm_reaches[1] == pytest.approx(0.0, abs=0.02)
        assert result.tilt_pitch == pytest.approx(0.0, abs=0.02)
        assert result.tilt_roll == pytest.approx(0.0, abs=0.02)

    def test_forward_slope_gives_nonzero_reaches(self):
        config = PlatformConfig()
        terrain = SlopeTerrain(slope_x=0.3)
        result = inverse_kinematics(config, terrain, body_xy=(0.0, 0.0))
        # At least one reach should be nonzero on a slope
        assert not (
            result.arm_reaches[0] == pytest.approx(0.0, abs=0.01)
            and result.arm_reaches[1] == pytest.approx(0.0, abs=0.01)
        )

    def test_round_trip_fk_ik(self):
        """IK result fed back into FK should place wheels on terrain."""
        config = PlatformConfig()
        terrain = SlopeTerrain(slope_x=0.2, slope_y=0.1)
        ik = inverse_kinematics(config, terrain, body_xy=(0.0, 0.0))
        fk = forward_kinematics(config, tilt_pitch=ik.tilt_pitch,
                                tilt_roll=ik.tilt_roll,
                                arm_reaches=ik.arm_reaches)
        for name in ("B", "C"):
            contact = fk.wheel_contacts[name]
            terrain_z = terrain.height(contact[0], contact[1])
            assert contact[2] == pytest.approx(terrain_z, abs=0.05)


class TestStability:
    def test_cog_inside_triangle_on_flat(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        ik = inverse_kinematics(config, terrain, body_xy=(0.0, 0.0))
        fk = forward_kinematics(config, tilt_pitch=ik.tilt_pitch,
                                tilt_roll=ik.tilt_roll,
                                arm_reaches=ik.arm_reaches)
        triangle = compute_support_triangle(fk.wheel_contacts)
        margin = compute_stability_margin(fk.brace_center, triangle)
        assert margin > 0

    def test_support_triangle_has_three_vertices(self):
        config = PlatformConfig()
        fk = forward_kinematics(config, tilt_pitch=0.0, tilt_roll=0.0,
                                arm_reaches=(0.0, 0.0))
        triangle = compute_support_triangle(fk.wheel_contacts)
        assert triangle.shape == (3, 2)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_kinematics.py -v`
Expected: Failures due to new API.

- [ ] **Step 3: Implement the new kinematics**

Update `wheely/kinematics.py`:
- `FKResult`: Replace `arm_pivots` with `tilt_pitch`, `tilt_roll`, `arm_reaches`.
- `IKResult`: Replace `arm_pivots` with `tilt_pitch`, `tilt_roll`, `arm_reaches`.
- `forward_kinematics`: Accept `(tilt_pitch, tilt_roll, arm_reaches)` with `arm_pivots` backward compat.
- `inverse_kinematics`: Solve for `(reach_b, reach_c)` that place wheels on terrain. For flat/slope terrain, `tilt_pitch=0, tilt_roll=0` (IK assumes vertical shafts and solves only reaches). The tilt is what the active leveling controller corrects dynamically.
- `compute_support_triangle` and `compute_stability_margin`: unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_kinematics.py -v`
Expected: All PASS

- [ ] **Step 5: Run ALL tests to verify nothing is broken**

Run: `pytest tests/ -v`
Expected: All PASS across geometry, kinematics, dynamics, terrain.

- [ ] **Step 6: Commit**

```bash
git add wheely/kinematics.py tests/test_kinematics.py
git commit -m "feat: update kinematics for two-axis tilt DOF model"
```

---

### Task 4: Update server.py -- new strategies, metrics in frames

**Files:**
- Modify: `wheely/server.py`

- [ ] **Step 1: Update server to use new state format and strategies**

Changes:
- Import `ActiveArmsLeveling`, `ActiveBraceLeveling`, `StepMetrics` from dynamics.
- Add strategy presets: `active_arms_leveling` and `active_brace_leveling`.
- Update `_build_frame` to pass `tilt_pitch`, `tilt_roll`, `arm_reaches` to geometry functions instead of `arm_pivots`.
- Update `_build_frame` return dict to include new state fields instead of `arm_pivots`.
- Update sim loop: `simulate_step` now returns `(state, metrics)`. Include `metrics` dict in frame.
- Update `solve_ik` handler to set `arm_reaches` and `tilt_pitch`/`tilt_roll` from IK result.
- Track `cumulative_energy` across sim steps (reset on `start_sim`).

- [ ] **Step 2: Verify server starts without errors**

Run: `python3 -c "from wheely.server import app; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add wheely/server.py
git commit -m "feat: update server for two-axis tilt, new strategies, metrics"
```

---

### Task 5: Update frontend -- info bar, strategy dropdown, metrics chart

**Files:**
- Modify: `web/index.html`
- Modify: `web/controls.js`
- Create: `web/metrics-chart.js`

- [ ] **Step 1: Update index.html**

- Change info bar cards: "Pivot B" → "Pitch", "Pivot C" → "Roll". Update IDs to `info-pitch` and `info-roll`.
- Add strategy options to the `#strategy-select`: `<option value="active_arms_leveling">Active Arms (IMU)</option>` and `<option value="active_brace_leveling">Active Brace (IMU)</option>`.
- Add a `<canvas id="metrics-chart" width="600" height="150"></canvas>` element in or near the info bar area.
- Import `metrics-chart.js` module.

- [ ] **Step 2: Update controls.js**

Update `updateInfoBar` function:
- Replace `frame.arm_pivots` references with `frame.metrics.tilt_pitch_deg` and `frame.metrics.tilt_roll_deg`.
- Update element IDs to `info-pitch` and `info-roll`.
- Display pitch/roll in degrees.

- [ ] **Step 3: Create web/metrics-chart.js**

Canvas-based rolling time-series chart:
- Accepts data points `{time, pitch, roll, torque}`.
- Keeps a buffer of ~300 points (rolling ~10 seconds at 30fps).
- Draws pitch line (blue), roll line (red), torque magnitude line (yellow, secondary axis).
- Auto-scales Y axes.
- Clears buffer on `clear()` call.
- Export `updateChart(metrics)` and `clearChart()`.

- [ ] **Step 4: Wire chart into simulation.js**

In `web/simulation.js`, import and call `updateChart` on each frame, and `clearChart` on strategy change or sim start.

- [ ] **Step 5: Verify frontend loads**

Start server: `source .venv/bin/activate && uvicorn wheely.server:app --port 8767 &`
Navigate to `http://localhost:8767`, verify page loads, strategy dropdown shows new options, info bar shows "Pitch" and "Roll".

- [ ] **Step 6: Commit**

```bash
git add web/index.html web/controls.js web/metrics-chart.js web/simulation.js
git commit -m "feat: update frontend for two-axis tilt, metrics chart, new strategies"
```

---

### Task 6: Update platform-viz.js for tilt-aware rendering

**Files:**
- Modify: `web/platform-viz.js`

- [ ] **Step 1: Update updatePlatform to handle new frame format**

The frame no longer sends `arm_pivots`. The wheel positions are still sent as `frame.wheels`, so the 3D rendering of wheel/arm positions doesn't need to change conceptually -- it positions meshes based on the `wheels` dict.

Verify that `updatePlatform` still works with the new frame format. The main change is that `frame.arm_pivots` is gone -- if anything references it, update to use `frame.metrics.reach_b_deg` / `frame.metrics.reach_c_deg` or remove the reference.

- [ ] **Step 2: Verify 3D view renders correctly**

With the server running, confirm that the Three.js viewport shows the platform correctly with different strategies.

- [ ] **Step 3: Commit (if changes needed)**

```bash
git add web/platform-viz.js
git commit -m "fix: update platform-viz for new frame format"
```

---

### Task 7: Integration test -- full end-to-end verification

**Files:**
- No new files (verification task)

- [ ] **Step 1: Run full test suite**

Run: `source .venv/bin/activate && pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 2: Test server with each strategy**

Start server and manually test via curl/WebSocket that each strategy produces valid frames:

```bash
source .venv/bin/activate && python3 -c "
import asyncio, json, websockets

async def test():
    async with websockets.connect('ws://localhost:8767/ws') as ws:
        for strat in ['passive', 'spring_damper', 'active_arms_leveling', 'active_brace_leveling']:
            await ws.send(json.dumps({'type': 'set_strategy', 'name': strat}))
            await ws.send(json.dumps({'type': 'set_terrain', 'name': 'bumpy'}))
            await ws.send(json.dumps({'type': 'solve_ik'}))
            msg = json.loads(await ws.recv())
            print(f'{strat}: {\"metrics\" in msg}')
            assert 'wheels' in msg
        print('All strategies OK')

asyncio.run(test())
"
```

- [ ] **Step 3: Verify no penetration across terrain types**

```bash
source .venv/bin/activate && python3 -c "
from wheely.dynamics import *
from wheely.geometry import PlatformConfig, compute_wheel_positions
from wheely.terrain import *

for TerrainCls in [FlatTerrain, SinusoidalTerrain]:
    terrain = TerrainCls() if TerrainCls == FlatTerrain else TerrainCls(amplitude=0.15, wavelength=2.0)
    config = PlatformConfig()
    state = SimState.from_config(config)
    for i in range(500):
        state, m = simulate_step(state, config, terrain, PassiveStrategy(), dt=0.01)
        wheels = compute_wheel_positions(config, state.tilt_pitch, state.tilt_roll, state.arm_reaches)
        for name in ('B', 'C'):
            wz = wheels[name][2]
            tz = terrain.height(wheels[name][0], wheels[name][1])
            assert wz >= tz - 1e-5, f'Penetration at step {i}: {name} {wz} < {tz}'
    print(f'{TerrainCls.__name__}: 500 steps, no penetration')
print('All OK')
"
```

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: integration fixes for dynamics rework"
```
