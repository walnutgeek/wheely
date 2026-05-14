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


from wheely.dynamics import figure8_motion


class TestFigure8Motion:
    def test_advances_position(self):
        """After one step, body_xy should have moved from origin."""
        state = SimState.from_config(PlatformConfig())
        new_state = figure8_motion(state, dt=0.1, speed=0.3, radius=2.0)
        assert new_state.body_xy != (0.0, 0.0)
        assert new_state.path_theta > 0.0

    def test_stays_on_path(self):
        """Position should match the lemniscate equation."""
        state = SimState.from_config(PlatformConfig())
        state = figure8_motion(state, dt=1.0, speed=0.3, radius=2.0)
        theta = state.path_theta
        R = 2.0
        expected_x = R * math.sin(2 * theta) / 2
        expected_y = R * math.sin(theta)
        assert state.body_xy[0] == pytest.approx(expected_x, abs=1e-6)
        assert state.body_xy[1] == pytest.approx(expected_y, abs=1e-6)

    def test_completes_loop(self):
        """After many steps, path_theta should exceed 2*pi (one full loop)."""
        state = SimState.from_config(PlatformConfig())
        for _ in range(5000):
            state = figure8_motion(state, dt=0.01, speed=0.5, radius=2.0)
        assert state.path_theta > 2 * math.pi

    def test_yaw_follows_tangent(self):
        """body_yaw should point along path tangent direction."""
        state = SimState.from_config(PlatformConfig())
        state = figure8_motion(state, dt=0.5, speed=0.3, radius=2.0)
        theta = state.path_theta
        R = 2.0
        dx = R * math.cos(2 * theta)
        dy = R * math.cos(theta)
        expected_yaw = math.atan2(dy, dx)
        assert state.body_yaw == pytest.approx(expected_yaw, abs=1e-6)
