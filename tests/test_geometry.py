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
