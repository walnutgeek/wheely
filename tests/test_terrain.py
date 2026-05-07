"""Tests for wheely.terrain module."""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from wheely.terrain import FlatTerrain, SlopeTerrain, SinusoidalTerrain, ComposedTerrain


class TestFlatTerrain:
    def test_height_is_zero(self):
        t = FlatTerrain()
        assert t.height(0.0, 0.0) == 0.0
        assert t.height(10.0, -5.0) == 0.0

    def test_height_with_elevation(self):
        t = FlatTerrain(elevation=2.5)
        assert t.height(0.0, 0.0) == 2.5

    def test_normal_is_up(self):
        t = FlatTerrain()
        n = t.normal(3.0, 4.0)
        np.testing.assert_array_almost_equal(n, [0.0, 0.0, 1.0])

    def test_height_batch(self):
        t = FlatTerrain(elevation=1.0)
        xs = np.array([0.0, 1.0, 2.0])
        ys = np.array([0.0, 1.0, 2.0])
        zs = t.height_batch(xs, ys)
        np.testing.assert_array_almost_equal(zs, [1.0, 1.0, 1.0])


class TestSlopeTerrain:
    def test_slope_in_x(self):
        t = SlopeTerrain(slope_x=0.5, slope_y=0.0)
        assert t.height(0.0, 0.0) == 0.0
        assert t.height(2.0, 0.0) == pytest.approx(1.0)

    def test_slope_in_y(self):
        t = SlopeTerrain(slope_x=0.0, slope_y=0.3)
        assert t.height(0.0, 5.0) == pytest.approx(1.5)

    def test_normal_tilted(self):
        t = SlopeTerrain(slope_x=1.0, slope_y=0.0)
        n = t.normal(0.0, 0.0)
        assert n[2] > 0
        assert np.abs(np.linalg.norm(n) - 1.0) < 1e-10


class TestSinusoidalTerrain:
    def test_zero_at_origin(self):
        t = SinusoidalTerrain(amplitude=0.5, wavelength=2.0)
        assert t.height(0.0, 0.0) == pytest.approx(0.0)

    def test_peak_at_quarter_wavelength(self):
        # amplitude * sin(k * 0.5) * sin(k * 0.5) where k = 2*pi/2 = pi
        # = 0.5 * sin(pi/2) * sin(pi/2) = 0.5 * 1.0 * 1.0 = 0.5
        t = SinusoidalTerrain(amplitude=0.5, wavelength=2.0)
        assert t.height(0.5, 0.5) == pytest.approx(0.5)

    def test_normal_is_unit_vector(self):
        t = SinusoidalTerrain(amplitude=0.3, wavelength=1.0)
        n = t.normal(0.25, 0.1)
        assert np.abs(np.linalg.norm(n) - 1.0) < 1e-10


class TestComposedTerrain:
    def test_sum_of_terrains(self):
        t1 = FlatTerrain(elevation=1.0)
        t2 = SlopeTerrain(slope_x=0.5, slope_y=0.0)
        composed = ComposedTerrain([t1, t2])
        assert composed.height(2.0, 0.0) == pytest.approx(2.0)

    def test_normal_is_unit_vector(self):
        t1 = SlopeTerrain(slope_x=0.3, slope_y=0.0)
        t2 = SinusoidalTerrain(amplitude=0.1, wavelength=1.0)
        composed = ComposedTerrain([t1, t2])
        n = composed.normal(0.5, 0.5)
        assert np.abs(np.linalg.norm(n) - 1.0) < 1e-10


@given(
    x=st.floats(min_value=-100, max_value=100),
    y=st.floats(min_value=-100, max_value=100),
)
@settings(max_examples=50)
def test_sinusoidal_normal_always_unit(x, y):
    t = SinusoidalTerrain(amplitude=0.5, wavelength=2.0)
    n = t.normal(x, y)
    assert np.abs(np.linalg.norm(n) - 1.0) < 1e-9
