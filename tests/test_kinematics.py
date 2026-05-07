"""Tests for wheely.kinematics module."""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from wheely.geometry import PlatformConfig, compute_wheel_positions
from wheely.kinematics import (
    forward_kinematics,
    inverse_kinematics,
    compute_support_triangle,
    compute_stability_margin,
)
from wheely.terrain import FlatTerrain, SlopeTerrain


class TestForwardKinematics:
    def test_flat_ground_zero_pivots(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        result = forward_kinematics(config, arm_pivots=(0.0, 0.0), steerings=(0.0, 0.0, 0.0))
        for name in ("A", "B", "C"):
            assert np.all(np.isfinite(result.wheel_contacts[name]))
        assert np.all(np.isfinite(result.brace_center))

    def test_steerings_dont_affect_positions(self):
        config = PlatformConfig()
        r1 = forward_kinematics(config, arm_pivots=(0.0, 0.0), steerings=(0.0, 0.0, 0.0))
        r2 = forward_kinematics(config, arm_pivots=(0.0, 0.0), steerings=(0.5, -0.3, 0.2))
        for name in ("A", "B", "C"):
            np.testing.assert_array_almost_equal(
                r1.wheel_contacts[name], r2.wheel_contacts[name]
            )

    def test_pivot_changes_wheel_z(self):
        config = PlatformConfig()
        r_zero = forward_kinematics(config, arm_pivots=(0.0, 0.0), steerings=(0.0, 0.0, 0.0))
        r_down = forward_kinematics(config, arm_pivots=(0.3, 0.0), steerings=(0.0, 0.0, 0.0))
        assert r_down.wheel_contacts["B"][2] < r_zero.wheel_contacts["B"][2]


class TestInverseKinematics:
    def test_flat_terrain_gives_zero_pivots(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        result = inverse_kinematics(config, terrain, body_xy=(0.0, 0.0), body_yaw=0.0)
        assert result.arm_pivots[0] == pytest.approx(0.0, abs=0.01)
        assert result.arm_pivots[1] == pytest.approx(0.0, abs=0.01)

    def test_slope_terrain_gives_nonzero_pivots(self):
        config = PlatformConfig()
        terrain = SlopeTerrain(slope_x=0.3)
        result = inverse_kinematics(config, terrain, body_xy=(0.0, 0.0), body_yaw=0.0)
        assert not (
            result.arm_pivots[0] == pytest.approx(0.0, abs=0.01)
            and result.arm_pivots[1] == pytest.approx(0.0, abs=0.01)
        )

    def test_round_trip_fk_ik(self):
        """IK result fed back into FK should place wheels on terrain."""
        config = PlatformConfig()
        terrain = SlopeTerrain(slope_x=0.2, slope_y=0.1)
        ik = inverse_kinematics(config, terrain, body_xy=(0.0, 0.0), body_yaw=0.0)
        fk = forward_kinematics(config, arm_pivots=ik.arm_pivots, steerings=(0.0, 0.0, 0.0))
        for name in ("B", "C"):
            contact = fk.wheel_contacts[name]
            terrain_z = terrain.height(contact[0], contact[1])
            assert contact[2] == pytest.approx(terrain_z, abs=0.02)


class TestStability:
    def test_cog_inside_triangle_on_flat(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        ik = inverse_kinematics(config, terrain, body_xy=(0.0, 0.0), body_yaw=0.0)
        fk = forward_kinematics(config, arm_pivots=ik.arm_pivots, steerings=(0.0, 0.0, 0.0))
        triangle = compute_support_triangle(fk.wheel_contacts)
        margin = compute_stability_margin(fk.brace_center, triangle)
        assert margin > 0

    def test_support_triangle_has_three_vertices(self):
        config = PlatformConfig()
        fk = forward_kinematics(config, arm_pivots=(0.0, 0.0), steerings=(0.0, 0.0, 0.0))
        triangle = compute_support_triangle(fk.wheel_contacts)
        assert triangle.shape == (3, 2)
