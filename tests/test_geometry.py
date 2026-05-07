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


class TestWheelPositions:
    def test_wheel_a_at_origin(self):
        config = PlatformConfig()
        wheels = compute_wheel_positions(config)
        np.testing.assert_array_almost_equal(wheels["A"], [0.0, 0.0, 0.0])

    def test_wheels_b_and_c_symmetric(self):
        config = PlatformConfig()
        wheels = compute_wheel_positions(config)
        # B is right (-Y), C is left (+Y)
        assert wheels["B"][1] < 0
        assert wheels["C"][1] > 0
        np.testing.assert_almost_equal(wheels["B"][0], wheels["C"][0])
        np.testing.assert_almost_equal(wheels["B"][1], -wheels["C"][1])
        np.testing.assert_almost_equal(wheels["B"][2], wheels["C"][2])

    def test_arm_length_determines_distance(self):
        config = PlatformConfig(arm_length=1.0)
        wheels = compute_wheel_positions(config)
        dist_b = np.linalg.norm(wheels["B"] - wheels["A"])
        dist_c = np.linalg.norm(wheels["C"] - wheels["A"])
        assert dist_b == pytest.approx(1.0, abs=1e-10)
        assert dist_c == pytest.approx(1.0, abs=1e-10)

    def test_pivot_angles_move_wheels_vertically(self):
        config = PlatformConfig()
        wheels_zero = compute_wheel_positions(config, arm_pivots=(0.0, 0.0))
        wheels_down = compute_wheel_positions(config, arm_pivots=(0.3, 0.3))
        assert wheels_down["B"][2] < wheels_zero["B"][2]
        assert wheels_down["C"][2] < wheels_zero["C"][2]

    def test_asymmetric_pivots(self):
        config = PlatformConfig()
        wheels = compute_wheel_positions(config, arm_pivots=(0.3, 0.0))
        wheels_zero = compute_wheel_positions(config, arm_pivots=(0.0, 0.0))
        assert wheels["B"][2] < wheels_zero["B"][2]
        np.testing.assert_array_almost_equal(wheels["C"], wheels_zero["C"])


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
