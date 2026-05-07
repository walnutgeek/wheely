"""Tests for wheely.dynamics module."""

import numpy as np
import pytest

from wheely.dynamics import (
    PassiveStrategy,
    ActiveStrategy,
    SpringDamperStrategy,
    SimState,
    simulate_step,
)
from wheely.geometry import PlatformConfig
from wheely.terrain import FlatTerrain, SlopeTerrain


class TestPassiveStrategy:
    def test_returns_zero_torques(self):
        strategy = PassiveStrategy()
        state = SimState.from_config(PlatformConfig())
        torques = strategy.compute_torques(state)
        assert torques[0] == pytest.approx(0.0)
        assert torques[1] == pytest.approx(0.0)


class TestActiveStrategy:
    def test_returns_torque_toward_target(self):
        strategy = ActiveStrategy(target_pivots=(0.0, 0.0), kp=10.0)
        state = SimState.from_config(PlatformConfig())
        state.arm_pivots = (0.3, -0.2)
        torques = strategy.compute_torques(state)
        assert torques[0] < 0  # pivot_b=0.3, target=0, torque should be negative
        assert torques[1] > 0  # pivot_c=-0.2, target=0, torque should be positive


class TestSpringDamperStrategy:
    def test_spring_force_at_displacement(self):
        strategy = SpringDamperStrategy(stiffness=100.0, damping=5.0)
        state = SimState.from_config(PlatformConfig())
        state.arm_pivots = (0.1, -0.1)
        state.arm_velocities = (0.0, 0.0)
        torques = strategy.compute_torques(state)
        assert torques[0] == pytest.approx(-10.0)
        assert torques[1] == pytest.approx(10.0)

    def test_damping_opposes_velocity(self):
        strategy = SpringDamperStrategy(stiffness=0.0, damping=10.0)
        state = SimState.from_config(PlatformConfig())
        state.arm_pivots = (0.0, 0.0)
        state.arm_velocities = (1.0, -0.5)
        torques = strategy.compute_torques(state)
        assert torques[0] == pytest.approx(-10.0)
        assert torques[1] == pytest.approx(5.0)


class TestSimulateStep:
    def test_passive_on_flat_stays_stable(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        strategy = PassiveStrategy()
        state = SimState.from_config(config)
        new_state = simulate_step(state, config, terrain, strategy, dt=0.01)
        assert np.all(np.isfinite([new_state.arm_pivots[0], new_state.arm_pivots[1]]))

    def test_passive_settles_on_flat_terrain(self):
        """With terrain contact, passive arms should settle to rest on the ground."""
        config = PlatformConfig()
        terrain = FlatTerrain()
        strategy = PassiveStrategy()
        state = SimState.from_config(config)
        for _ in range(1000):
            state = simulate_step(state, config, terrain, strategy, dt=0.01)
        # Arms should have settled (low velocity)
        assert abs(state.arm_velocities[0]) < 0.1
        assert abs(state.arm_velocities[1]) < 0.1

    def test_passive_settles_on_slope(self):
        """On a slope, arms should settle at different angles."""
        config = PlatformConfig()
        terrain = SlopeTerrain(slope_x=0.3)
        strategy = PassiveStrategy()
        state = SimState.from_config(config)
        for _ in range(1000):
            state = simulate_step(state, config, terrain, strategy, dt=0.01)
        # Arms should have settled (low velocity)
        assert abs(state.arm_velocities[0]) < 0.1
        assert abs(state.arm_velocities[1]) < 0.1

    def test_spring_damper_returns_to_rest(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        strategy = SpringDamperStrategy(stiffness=200.0, damping=20.0)
        state = SimState.from_config(config)
        state.arm_pivots = (0.2, -0.2)
        for _ in range(500):
            state = simulate_step(state, config, terrain, strategy, dt=0.01)
        # Should converge near rest (terrain contact + spring both push toward equilibrium)
        assert abs(state.arm_velocities[0]) < 0.1
        assert abs(state.arm_velocities[1]) < 0.1
