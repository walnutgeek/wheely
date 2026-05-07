# Wheely Kinematic Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python simulation tool with web-based Three.js visualization for a self-leveling tricycle robotic platform with parallelogram arm linkages.

**Architecture:** Python backend (NumPy/SciPy) computes kinematics and dynamics. FastAPI serves a WebSocket API. Three.js frontend renders interactive 3D visualization with parameter controls. All geometry is parametric.

**Tech Stack:** Python 3.11+, NumPy, SciPy, FastAPI, uvicorn, websockets, pytest, hypothesis; Three.js (via CDN), vanilla JS, HTML/CSS.

---

## File Map

```
wheely/
├── pyproject.toml              # Package config, dependencies
├── wheely/
│   ├── __init__.py             # Version, package exports
│   ├── geometry.py             # PlatformConfig dataclass, parametric point computation
│   ├── terrain.py              # Terrain interface + implementations (flat, slope, sinusoidal)
│   ├── kinematics.py           # Forward/inverse kinematics, workspace analysis
│   ├── dynamics.py             # Stability analysis, actuation strategies, time integration
│   └── server.py               # FastAPI app, WebSocket handler, REST endpoints
├── web/
│   ├── index.html              # Main page shell, CSS, panel layout
│   ├── scene.js                # Three.js scene, camera, renderer, lighting
│   ├── platform-viz.js         # Build 3D meshes from platform geometry
│   ├── terrain-viz.js          # Build terrain mesh from heightmap data
│   ├── controls.js             # Parameter sliders, terrain selector, UI state
│   └── simulation.js           # WebSocket client, animation loop, coordination
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── test_geometry.py        # PlatformConfig validation, point computation
│   ├── test_terrain.py         # Terrain height/normal correctness
│   ├── test_kinematics.py      # FK/IK round-trips, leveling on flat ground
│   └── test_dynamics.py        # Stability analysis, actuation strategy interface
└── README.md
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `wheely/__init__.py`
- Create: `tests/conftest.py`

**Dependencies:** None (start here)

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "wheely"
version = "0.1.0"
description = "Kinematic simulation for a self-leveling tricycle robotic platform"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.26",
    "scipy>=1.12",
    "fastapi>=0.109",
    "uvicorn[standard]>=0.27",
    "websockets>=12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "hypothesis>=6.98",
    "httpx>=0.27",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create wheely/__init__.py**

```python
"""Wheely: kinematic simulation for a self-leveling tricycle robotic platform."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create tests/conftest.py**

```python
"""Shared test fixtures for wheely tests."""

import numpy as np
import pytest

from wheely.geometry import PlatformConfig


@pytest.fixture
def default_config() -> PlatformConfig:
    """A PlatformConfig with default parameters."""
    return PlatformConfig()


@pytest.fixture
def rng() -> np.random.Generator:
    """Seeded random generator for reproducible tests."""
    return np.random.default_rng(42)
```

- [ ] **Step 4: Install in dev mode and verify**

Run: `cd /Users/sergeyk/w/wheely && pip install -e ".[dev]"`
Expected: installs successfully (geometry import will fail until Task 2, that's fine)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml wheely/__init__.py tests/conftest.py
git commit -m "feat: project scaffolding with dependencies"
```

---

### Task 2: Terrain Module

**Files:**
- Create: `wheely/terrain.py`
- Create: `tests/test_terrain.py`

**Dependencies:** Task 1 (scaffolding)

- [ ] **Step 1: Write terrain tests**

```python
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
        assert n[2] > 0  # z component positive (pointing up)
        assert np.abs(np.linalg.norm(n) - 1.0) < 1e-10  # unit vector


class TestSinusoidalTerrain:
    def test_zero_at_origin(self):
        t = SinusoidalTerrain(amplitude=0.5, wavelength=2.0)
        assert t.height(0.0, 0.0) == pytest.approx(0.0)

    def test_peak_at_quarter_wavelength(self):
        t = SinusoidalTerrain(amplitude=0.5, wavelength=2.0)
        assert t.height(0.5, 0.0) == pytest.approx(0.5)

    def test_normal_is_unit_vector(self):
        t = SinusoidalTerrain(amplitude=0.3, wavelength=1.0)
        n = t.normal(0.25, 0.1)
        assert np.abs(np.linalg.norm(n) - 1.0) < 1e-10


class TestComposedTerrain:
    def test_sum_of_terrains(self):
        t1 = FlatTerrain(elevation=1.0)
        t2 = SlopeTerrain(slope_x=0.5, slope_y=0.0)
        composed = ComposedTerrain([t1, t2])
        assert composed.height(2.0, 0.0) == pytest.approx(2.0)  # 1.0 + 0.5*2

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_terrain.py -v`
Expected: ImportError -- module `wheely.terrain` does not exist

- [ ] **Step 3: Implement terrain module**

```python
"""Terrain models for wheely simulation.

Each terrain provides height(x, y) -> z and normal(x, y) -> unit vector.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FlatTerrain:
    """Flat horizontal plane at a given elevation."""

    elevation: float = 0.0

    def height(self, x: float, y: float) -> float:
        return self.elevation

    def height_batch(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        return np.full_like(xs, self.elevation, dtype=float)

    def normal(self, x: float, y: float) -> np.ndarray:
        return np.array([0.0, 0.0, 1.0])


@dataclass
class SlopeTerrain:
    """Plane with constant slope in X and/or Y: z = slope_x * x + slope_y * y."""

    slope_x: float = 0.0
    slope_y: float = 0.0

    def height(self, x: float, y: float) -> float:
        return self.slope_x * x + self.slope_y * y

    def height_batch(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        return self.slope_x * xs + self.slope_y * ys

    def normal(self, x: float, y: float) -> np.ndarray:
        # Surface: z = slope_x * x + slope_y * y
        # Gradient: (slope_x, slope_y, -1), normal = -gradient normalized
        n = np.array([-self.slope_x, -self.slope_y, 1.0])
        return n / np.linalg.norm(n)


@dataclass
class SinusoidalTerrain:
    """Sinusoidal bumps: z = amplitude * sin(2*pi*x / wavelength) * sin(2*pi*y / wavelength)."""

    amplitude: float = 0.3
    wavelength: float = 2.0

    def height(self, x: float, y: float) -> float:
        k = 2.0 * np.pi / self.wavelength
        return float(self.amplitude * np.sin(k * x) * np.sin(k * y))

    def height_batch(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        k = 2.0 * np.pi / self.wavelength
        return self.amplitude * np.sin(k * xs) * np.sin(k * ys)

    def normal(self, x: float, y: float) -> np.ndarray:
        k = 2.0 * np.pi / self.wavelength
        dz_dx = self.amplitude * k * np.cos(k * x) * np.sin(k * y)
        dz_dy = self.amplitude * k * np.sin(k * x) * np.cos(k * y)
        n = np.array([-dz_dx, -dz_dy, 1.0])
        return n / np.linalg.norm(n)


@dataclass
class ComposedTerrain:
    """Sum of multiple terrain layers."""

    layers: list[FlatTerrain | SlopeTerrain | SinusoidalTerrain]

    def height(self, x: float, y: float) -> float:
        return sum(layer.height(x, y) for layer in self.layers)

    def height_batch(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        return sum(layer.height_batch(xs, ys) for layer in self.layers)

    def normal(self, x: float, y: float) -> np.ndarray:
        # Numerical normal via central differences
        eps = 1e-6
        z_xp = self.height(x + eps, y)
        z_xm = self.height(x - eps, y)
        z_yp = self.height(x, y + eps)
        z_ym = self.height(x, y - eps)
        dz_dx = (z_xp - z_xm) / (2.0 * eps)
        dz_dy = (z_yp - z_ym) / (2.0 * eps)
        n = np.array([-dz_dx, -dz_dy, 1.0])
        return n / np.linalg.norm(n)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_terrain.py -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add wheely/terrain.py tests/test_terrain.py
git commit -m "feat: terrain module with flat, slope, sinusoidal, and composed terrains"
```

---

### Task 3: Geometry Module

**Files:**
- Create: `wheely/geometry.py`
- Create: `tests/test_geometry.py`

**Dependencies:** Task 1 (scaffolding)

- [ ] **Step 1: Write geometry tests**

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
        # B and C should be symmetric about the XZ plane (Y=0)
        assert wheels["B"][1] < 0  # B is to the right (negative Y in right-hand Z-up with X forward... actually let me think)
        assert wheels["C"][1] > 0  # C is to the left
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
        # Positive pivot should move wheels down (negative Z)
        assert wheels_down["B"][2] < wheels_zero["B"][2]
        assert wheels_down["C"][2] < wheels_zero["C"][2]

    def test_asymmetric_pivots(self):
        config = PlatformConfig()
        wheels = compute_wheel_positions(config, arm_pivots=(0.3, 0.0))
        # Only wheel B should have moved down
        wheels_zero = compute_wheel_positions(config, arm_pivots=(0.0, 0.0))
        assert wheels["B"][2] < wheels_zero["B"][2]
        np.testing.assert_array_almost_equal(wheels["C"], wheels_zero["C"])


class TestBraceEndpoints:
    def test_brace_midway_on_arms(self):
        config = PlatformConfig(brace_position=0.5)
        wheels = compute_wheel_positions(config)
        left, right = compute_brace_endpoints(config)
        # Each brace endpoint should be halfway between A and B/C
        expected_left = (wheels["A"] + wheels["B"]) / 2.0
        expected_right = (wheels["A"] + wheels["C"]) / 2.0
        np.testing.assert_array_almost_equal(left, expected_left)
        np.testing.assert_array_almost_equal(right, expected_right)

    def test_brace_center_on_centerline(self):
        config = PlatformConfig()
        center = compute_brace_center(config)
        # Center should be on the XZ plane (Y ~= 0) for symmetric config
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
    # All wheel positions should be finite
    for name in ("A", "B", "C"):
        assert np.all(np.isfinite(wheels[name]))
    # Arm lengths preserved
    for name in ("B", "C"):
        dist = np.linalg.norm(wheels[name] - wheels["A"])
        assert dist == pytest.approx(arm_length, abs=1e-9)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_geometry.py -v`
Expected: ImportError -- module `wheely.geometry` does not exist

- [ ] **Step 3: Implement geometry module**

```python
"""Parametric geometry for the wheely tricycle platform.

Coordinate system: right-hand, Z-up.
Origin at Wheel A (apex). X points rearward (toward B/C), Y points left, Z up.

Arms extend from the origin (Wheel A) rearward. Arm 1 goes to Wheel B (right, -Y),
Arm 2 goes to Wheel C (left, +Y). The splay angle is measured from the X axis
in the XY plane.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class PlatformConfig:
    """All tunable parameters of the platform geometry."""

    arm_length: float = 0.8
    arm_splay_angle: float = np.radians(40)  # radians, from centerline in XY plane
    brace_position: float = 0.5  # 0.0 = apex, 1.0 = wheel
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


def compute_wheel_positions(
    config: PlatformConfig,
    arm_pivots: tuple[float, float] = (0.0, 0.0),
) -> dict[str, np.ndarray]:
    """Compute wheel A, B, C positions in the body frame.

    Args:
        config: Platform geometry parameters.
        arm_pivots: (pivot_b, pivot_c) angles in radians. Positive = wheel moves down.

    Returns:
        Dict with keys "A", "B", "C" mapping to 3D position arrays.
    """
    wheel_a = np.array([0.0, 0.0, 0.0])
    splay = config.arm_splay_angle
    pivot_b, pivot_c = arm_pivots

    # Arm to Wheel B (right side, -Y direction)
    wheel_b = wheel_a + config.arm_length * np.array([
        np.cos(splay) * np.cos(pivot_b),
        -np.sin(splay) * np.cos(pivot_b),
        -np.sin(pivot_b),
    ])

    # Arm to Wheel C (left side, +Y direction)
    wheel_c = wheel_a + config.arm_length * np.array([
        np.cos(splay) * np.cos(pivot_c),
        np.sin(splay) * np.cos(pivot_c),
        -np.sin(pivot_c),
    ])

    return {"A": wheel_a, "B": wheel_b, "C": wheel_c}


def compute_brace_endpoints(
    config: PlatformConfig,
    arm_pivots: tuple[float, float] = (0.0, 0.0),
) -> tuple[np.ndarray, np.ndarray]:
    """Compute cross brace attachment points on each arm.

    Returns:
        (point_on_arm_b, point_on_arm_c) as 3D arrays.
    """
    wheels = compute_wheel_positions(config, arm_pivots)
    t = config.brace_position
    point_b = wheels["A"] + t * (wheels["B"] - wheels["A"])
    point_c = wheels["A"] + t * (wheels["C"] - wheels["A"])
    return point_b, point_c


def compute_brace_center(
    config: PlatformConfig,
    arm_pivots: tuple[float, float] = (0.0, 0.0),
) -> np.ndarray:
    """Compute center of the cross brace (primary cargo mount)."""
    left, right = compute_brace_endpoints(config, arm_pivots)
    return (left + right) / 2.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_geometry.py -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add wheely/geometry.py tests/test_geometry.py
git commit -m "feat: parametric geometry module with platform config and point computation"
```

---

### Task 4: Kinematics Module

**Files:**
- Create: `wheely/kinematics.py`
- Create: `tests/test_kinematics.py`

**Dependencies:** Task 2 (terrain), Task 3 (geometry)

- [ ] **Step 1: Write kinematics tests**

```python
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
        # All wheel positions should be finite
        for name in ("A", "B", "C"):
            assert np.all(np.isfinite(result.wheel_contacts[name]))
        # Brace center should be finite
        assert np.all(np.isfinite(result.brace_center))

    def test_steerings_dont_affect_positions(self):
        config = PlatformConfig()
        r1 = forward_kinematics(config, arm_pivots=(0.0, 0.0), steerings=(0.0, 0.0, 0.0))
        r2 = forward_kinematics(config, arm_pivots=(0.0, 0.0), steerings=(0.5, -0.3, 0.2))
        # Steering only rotates wheel heading, not contact position
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
        # On a slope in X, wheels at different X positions have different heights
        # so pivot angles should be nonzero
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
        assert margin > 0  # positive = stable

    def test_support_triangle_has_three_vertices(self):
        config = PlatformConfig()
        fk = forward_kinematics(config, arm_pivots=(0.0, 0.0), steerings=(0.0, 0.0, 0.0))
        triangle = compute_support_triangle(fk.wheel_contacts)
        assert triangle.shape == (3, 2)  # 3 vertices, 2D (XY projection)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_kinematics.py -v`
Expected: ImportError

- [ ] **Step 3: Implement kinematics module**

```python
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

    wheel_contacts: dict[str, np.ndarray]  # "A", "B", "C" -> 3D position
    wheel_headings: dict[str, float]  # "A", "B", "C" -> heading angle
    brace_center: np.ndarray  # 3D position of cargo mount
    arm_pivots: tuple[float, float]


@dataclass
class IKResult:
    """Result of inverse kinematics computation."""

    arm_pivots: tuple[float, float]
    body_z: float  # computed body height
    levelness: float  # 0.0 = perfectly level, higher = more tilt


def forward_kinematics(
    config: PlatformConfig,
    arm_pivots: tuple[float, float] = (0.0, 0.0),
    steerings: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> FKResult:
    """Compute wheel positions and brace center from arm pivots and steering.

    Args:
        config: Platform geometry.
        arm_pivots: (pivot_b, pivot_c) in radians.
        steerings: (steer_a, steer_b, steer_c) in radians.

    Returns:
        FKResult with all computed positions.
    """
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
    Arms pivot to place wheels B and C at the terrain surface.

    Args:
        config: Platform geometry.
        terrain: Object with height(x, y) method.
        body_xy: (x, y) position of the body (Wheel A) in world frame.
        body_yaw: Heading of the body in world frame.

    Returns:
        IKResult with solved pivot angles.
    """
    bx, by = body_xy
    body_z = terrain.height(bx, by)

    def _solve_pivot(splay_sign: float) -> float:
        """Solve pivot for one arm. splay_sign: -1 for B (right), +1 for C (left)."""
        splay = config.arm_splay_angle

        def _error(pivot: float) -> float:
            # Compute wheel position at this pivot
            dx = config.arm_length * np.cos(splay) * np.cos(pivot)
            dy = config.arm_length * splay_sign * np.sin(splay) * np.cos(pivot)
            dz = -config.arm_length * np.sin(pivot)
            # Rotate by body_yaw
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

    # Compute levelness: angle of brace center relative to horizontal
    brace = compute_brace_center(config, (pivot_b, pivot_c))
    # Levelness = magnitude of tilt from horizontal (0 = level)
    levelness = float(abs(brace[2]))

    return IKResult(
        arm_pivots=(pivot_b, pivot_c),
        body_z=body_z,
        levelness=levelness,
    )


def compute_support_triangle(
    wheel_contacts: dict[str, np.ndarray],
) -> np.ndarray:
    """Compute the support triangle from wheel contact points (XY projection).

    Returns:
        (3, 2) array of triangle vertices in XY plane.
    """
    return np.array([
        wheel_contacts["A"][:2],
        wheel_contacts["B"][:2],
        wheel_contacts["C"][:2],
    ])


def compute_stability_margin(
    cog: np.ndarray,
    triangle: np.ndarray,
) -> float:
    """Compute stability margin: signed distance from CoG projection to nearest triangle edge.

    Positive = inside triangle (stable). Negative = outside (tipping).

    Args:
        cog: 3D or 2D center of gravity position.
        triangle: (3, 2) array from compute_support_triangle.

    Returns:
        Stability margin (positive = stable).
    """
    p = cog[:2]
    min_dist = float("inf")

    for i in range(3):
        # Edge from vertex i to vertex (i+1) % 3
        a = triangle[i]
        b = triangle[(i + 1) % 3]
        # Signed distance from point to line (positive = left of edge when traversing CCW)
        edge = b - a
        to_point = p - a
        # Cross product (2D): edge x to_point
        cross = edge[0] * to_point[1] - edge[1] * to_point[0]
        edge_len = np.linalg.norm(edge)
        if edge_len < 1e-12:
            continue
        signed_dist = cross / edge_len
        min_dist = min(min_dist, signed_dist)

    return float(min_dist)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_kinematics.py -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add wheely/kinematics.py tests/test_kinematics.py
git commit -m "feat: forward/inverse kinematics with stability analysis"
```

---

### Task 5: Dynamics Module

**Files:**
- Create: `wheely/dynamics.py`
- Create: `tests/test_dynamics.py`

**Dependencies:** Task 3 (geometry), Task 4 (kinematics)

- [ ] **Step 1: Write dynamics tests**

```python
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
        # Torque should oppose the displacement
        assert torques[0] < 0  # pivot_b=0.3, target=0, torque should be negative
        assert torques[1] > 0  # pivot_c=-0.2, target=0, torque should be positive


class TestSpringDamperStrategy:
    def test_spring_force_at_displacement(self):
        strategy = SpringDamperStrategy(stiffness=100.0, damping=5.0)
        state = SimState.from_config(PlatformConfig())
        state.arm_pivots = (0.1, -0.1)
        state.arm_velocities = (0.0, 0.0)
        torques = strategy.compute_torques(state)
        assert torques[0] == pytest.approx(-10.0)  # -k * x = -100 * 0.1
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
        # On flat terrain with passive strategy, should remain near-stable
        assert np.all(np.isfinite([new_state.arm_pivots[0], new_state.arm_pivots[1]]))

    def test_spring_damper_returns_to_rest(self):
        config = PlatformConfig()
        terrain = FlatTerrain()
        strategy = SpringDamperStrategy(stiffness=200.0, damping=20.0)
        state = SimState.from_config(config)
        state.arm_pivots = (0.2, -0.2)  # displaced from rest
        # Simulate many steps
        for _ in range(500):
            state = simulate_step(state, config, terrain, strategy, dt=0.01)
        # Should have returned close to zero
        assert state.arm_pivots[0] == pytest.approx(0.0, abs=0.05)
        assert state.arm_pivots[1] == pytest.approx(0.0, abs=0.05)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_dynamics.py -v`
Expected: ImportError

- [ ] **Step 3: Implement dynamics module**

```python
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
        """Create a default state from config."""
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
    """Advance the simulation by one time step using semi-implicit Euler.

    Args:
        state: Current simulation state.
        config: Platform geometry.
        terrain: Terrain object with height(x, y).
        strategy: Actuation strategy with compute_torques(state).
        dt: Time step in seconds.
        arm_inertia: Moment of inertia for each arm pivot (kg*m^2).

    Returns:
        New SimState after one step.
    """
    torques = strategy.compute_torques(state)

    # Gravity torque on each arm (simplified: arm acts as pendulum)
    gravity = 9.81
    arm_mass = 2.0  # kg, simplified
    grav_torque_b = -arm_mass * gravity * config.arm_length * 0.5 * np.cos(state.arm_pivots[0])
    grav_torque_c = -arm_mass * gravity * config.arm_length * 0.5 * np.cos(state.arm_pivots[1])

    # Net torque
    net_b = torques[0] + grav_torque_b
    net_c = torques[1] + grav_torque_c

    # Semi-implicit Euler: update velocity first, then position
    acc_b = net_b / arm_inertia
    acc_c = net_c / arm_inertia
    new_vel_b = state.arm_velocities[0] + acc_b * dt
    new_vel_c = state.arm_velocities[1] + acc_c * dt
    new_pivot_b = state.arm_pivots[0] + new_vel_b * dt
    new_pivot_c = state.arm_pivots[1] + new_vel_c * dt

    # Clamp to pivot range
    limit = config.pivot_range
    new_pivot_b = float(np.clip(new_pivot_b, -limit, limit))
    new_pivot_c = float(np.clip(new_pivot_c, -limit, limit))
    # Zero velocity if clamped
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_dynamics.py -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add wheely/dynamics.py tests/test_dynamics.py
git commit -m "feat: dynamics module with actuation strategies and time integration"
```

---

### Task 6: FastAPI Server

**Files:**
- Create: `wheely/server.py`

**Dependencies:** Task 2 (terrain), Task 3 (geometry), Task 4 (kinematics), Task 5 (dynamics)

- [ ] **Step 1: Implement server**

```python
"""FastAPI server for wheely simulation.

Provides REST endpoints for configuration and a WebSocket for real-time simulation.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from wheely.dynamics import (
    ActiveStrategy,
    PassiveStrategy,
    SimState,
    SpringDamperStrategy,
    simulate_step,
)
from wheely.geometry import PlatformConfig
from wheely.kinematics import (
    compute_stability_margin,
    compute_support_triangle,
    forward_kinematics,
    inverse_kinematics,
)
from wheely.terrain import (
    ComposedTerrain,
    FlatTerrain,
    SinusoidalTerrain,
    SlopeTerrain,
)

app = FastAPI(title="Wheely Simulation")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

# Mount static files for the web frontend
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


TERRAIN_PRESETS = {
    "flat": lambda: FlatTerrain(),
    "gentle_slope": lambda: SlopeTerrain(slope_x=0.15),
    "steep_slope": lambda: SlopeTerrain(slope_x=0.4),
    "cross_slope": lambda: SlopeTerrain(slope_y=0.3),
    "bumpy": lambda: SinusoidalTerrain(amplitude=0.15, wavelength=2.0),
    "rough": lambda: ComposedTerrain([
        SlopeTerrain(slope_x=0.1),
        SinusoidalTerrain(amplitude=0.08, wavelength=1.0),
    ]),
}

STRATEGY_PRESETS = {
    "passive": lambda: PassiveStrategy(),
    "active": lambda: ActiveStrategy(target_pivots=(0.0, 0.0), kp=50.0),
    "spring_damper": lambda: SpringDamperStrategy(stiffness=200.0, damping=20.0),
}


@app.get("/")
async def index():
    return FileResponse(str(WEB_DIR / "index.html"))


@app.get("/api/config")
async def get_default_config():
    return PlatformConfig().to_dict()


@app.get("/api/terrains")
async def list_terrains():
    return list(TERRAIN_PRESETS.keys())


@app.get("/api/strategies")
async def list_strategies():
    return list(STRATEGY_PRESETS.keys())


def _build_frame(config, terrain, arm_pivots, steerings):
    """Compute a single simulation frame for sending to the client."""
    fk = forward_kinematics(config, arm_pivots=arm_pivots, steerings=steerings)
    triangle = compute_support_triangle(fk.wheel_contacts)
    margin = compute_stability_margin(fk.brace_center, triangle)

    return {
        "wheels": {k: v.tolist() for k, v in fk.wheel_contacts.items()},
        "brace_center": fk.brace_center.tolist(),
        "support_triangle": triangle.tolist(),
        "stability_margin": margin,
        "arm_pivots": list(arm_pivots),
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    config = PlatformConfig()
    terrain = FlatTerrain()
    strategy = PassiveStrategy()
    sim_state = SimState.from_config(config)
    running = False

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "set_config":
                params = msg.get("params", {})
                config = PlatformConfig(**{
                    k: v for k, v in params.items() if hasattr(PlatformConfig, k)
                })
                errors = config.validate()
                if errors:
                    await ws.send_json({"type": "error", "errors": errors})
                    continue

            elif msg_type == "set_terrain":
                name = msg.get("name", "flat")
                if name in TERRAIN_PRESETS:
                    terrain = TERRAIN_PRESETS[name]()

            elif msg_type == "set_strategy":
                name = msg.get("name", "passive")
                if name in STRATEGY_PRESETS:
                    strategy = STRATEGY_PRESETS[name]()

            elif msg_type == "set_position":
                x = msg.get("x", 0.0)
                y = msg.get("y", 0.0)
                yaw = msg.get("yaw", 0.0)
                sim_state = SimState(body_xy=(x, y), body_yaw=yaw)

            elif msg_type == "solve_ik":
                ik = inverse_kinematics(
                    config, terrain,
                    body_xy=sim_state.body_xy,
                    body_yaw=sim_state.body_yaw,
                )
                sim_state.arm_pivots = ik.arm_pivots
                frame = _build_frame(
                    config, terrain, sim_state.arm_pivots, sim_state.steerings
                )
                frame["type"] = "frame"
                frame["levelness"] = ik.levelness
                await ws.send_json(frame)

            elif msg_type == "start_sim":
                running = True
                sim_state = SimState.from_config(config)
                # Run simulation loop in background
                while running:
                    sim_state = simulate_step(
                        sim_state, config, terrain, strategy, dt=0.016
                    )
                    frame = _build_frame(
                        config, terrain, sim_state.arm_pivots, sim_state.steerings
                    )
                    frame["type"] = "frame"
                    frame["time"] = sim_state.time
                    await ws.send_json(frame)
                    await asyncio.sleep(0.033)  # ~30fps

                    # Check for incoming messages without blocking
                    try:
                        raw = await asyncio.wait_for(ws.receive_text(), timeout=0.001)
                        inner = json.loads(raw)
                        if inner.get("type") == "stop_sim":
                            running = False
                    except asyncio.TimeoutError:
                        pass

            elif msg_type == "stop_sim":
                running = False

            elif msg_type == "get_frame":
                frame = _build_frame(
                    config, terrain, sim_state.arm_pivots, sim_state.steerings
                )
                frame["type"] = "frame"
                await ws.send_json(frame)

            elif msg_type == "get_terrain_grid":
                # Send terrain heightmap as a grid for 3D rendering
                size = msg.get("size", 10.0)
                res = msg.get("resolution", 50)
                xs = [float(x) for x in range(-int(size / 2 * res), int(size / 2 * res) + 1)]
                xs = [x / res * size / (size * res / 2) * size / 2 for x in range(res + 1)]
                # Simpler: evenly spaced grid
                lin = [float(-size / 2 + i * size / res) for i in range(res + 1)]
                heights = []
                for yi in lin:
                    row = []
                    for xi in lin:
                        row.append(terrain.height(xi, yi))
                    heights.append(row)
                await ws.send_json({
                    "type": "terrain_grid",
                    "size": size,
                    "resolution": res,
                    "heights": heights,
                })

    except WebSocketDisconnect:
        pass
```

- [ ] **Step 2: Quick smoke test (manual)**

Run: `cd /Users/sergeyk/w/wheely && python -c "from wheely.server import app; print('Server module loads OK')"`
Expected: `Server module loads OK`

- [ ] **Step 3: Commit**

```bash
git add wheely/server.py
git commit -m "feat: FastAPI server with WebSocket simulation and REST config endpoints"
```

---

### Task 7: Web Frontend

**Files:**
- Create: `web/index.html`
- Create: `web/scene.js`
- Create: `web/platform-viz.js`
- Create: `web/terrain-viz.js`
- Create: `web/controls.js`
- Create: `web/simulation.js`

**Dependencies:** Task 6 (server API defined)

- [ ] **Step 1: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wheely – Tricycle Platform Simulator</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0; overflow: hidden; }

  #app { display: grid; grid-template-columns: 1fr 320px; grid-template-rows: 48px 1fr 180px; height: 100vh; }

  /* Header */
  #header { grid-column: 1 / -1; display: flex; align-items: center; padding: 0 16px; background: #16213e; border-bottom: 1px solid #0f3460; }
  #header h1 { font-size: 18px; font-weight: 600; color: #e94560; }
  #header .status { margin-left: auto; font-size: 13px; color: #888; }

  /* 3D viewport */
  #viewport { position: relative; overflow: hidden; background: #0a0a1a; }
  #viewport canvas { display: block; width: 100%; height: 100%; }

  /* Side panel */
  #panel { background: #16213e; border-left: 1px solid #0f3460; padding: 12px; overflow-y: auto; grid-row: 2 / 4; }
  #panel h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #e94560; margin: 12px 0 8px; }
  #panel h2:first-child { margin-top: 0; }

  /* Slider controls */
  .control { margin-bottom: 10px; }
  .control label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 3px; }
  .control label span { color: #aaa; }
  .control input[type="range"] { width: 100%; accent-color: #e94560; }

  /* Select dropdowns */
  .control select { width: 100%; padding: 4px 8px; background: #0f3460; color: #e0e0e0; border: 1px solid #1a4080; border-radius: 4px; font-size: 13px; }

  /* Buttons */
  .btn-row { display: flex; gap: 8px; margin: 8px 0; }
  .btn { flex: 1; padding: 6px 12px; background: #0f3460; color: #e0e0e0; border: 1px solid #1a4080; border-radius: 4px; cursor: pointer; font-size: 13px; text-align: center; }
  .btn:hover { background: #1a4080; }
  .btn.active { background: #e94560; border-color: #e94560; }

  /* Info bar */
  #infobar { grid-column: 1 / 2; background: #16213e; border-top: 1px solid #0f3460; padding: 12px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; align-items: start; }
  .info-card { background: #0f3460; border-radius: 6px; padding: 10px; }
  .info-card .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; margin-bottom: 4px; }
  .info-card .value { font-size: 20px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .info-card .value.stable { color: #4ade80; }
  .info-card .value.unstable { color: #f87171; }
</style>
</head>
<body>
<div id="app">
  <div id="header">
    <h1>Wheely</h1>
    <div class="status" id="conn-status">Disconnected</div>
  </div>

  <div id="viewport"></div>

  <div id="panel">
    <h2>Geometry</h2>
    <div class="control">
      <label>Arm Length <span id="val-arm-length">0.80 m</span></label>
      <input type="range" id="arm-length" min="0.3" max="1.5" step="0.01" value="0.8">
    </div>
    <div class="control">
      <label>Splay Angle <span id="val-splay">40°</span></label>
      <input type="range" id="splay-angle" min="20" max="60" step="1" value="40">
    </div>
    <div class="control">
      <label>Brace Position <span id="val-brace-pos">0.50</span></label>
      <input type="range" id="brace-pos" min="0.3" max="0.7" step="0.01" value="0.5">
    </div>
    <div class="control">
      <label>Wheel Radius <span id="val-wheel-r">0.15 m</span></label>
      <input type="range" id="wheel-radius" min="0.05" max="0.3" step="0.01" value="0.15">
    </div>

    <h2>Terrain</h2>
    <div class="control">
      <select id="terrain-select">
        <option value="flat">Flat</option>
        <option value="gentle_slope">Gentle Slope</option>
        <option value="steep_slope">Steep Slope</option>
        <option value="cross_slope">Cross Slope</option>
        <option value="bumpy">Bumpy</option>
        <option value="rough">Rough</option>
      </select>
    </div>

    <h2>Actuation</h2>
    <div class="control">
      <select id="strategy-select">
        <option value="passive">Passive</option>
        <option value="active">Active (PID)</option>
        <option value="spring_damper">Spring-Damper</option>
      </select>
    </div>

    <h2>Simulation</h2>
    <div class="btn-row">
      <div class="btn" id="btn-ik">Solve IK</div>
      <div class="btn" id="btn-sim">Run Sim</div>
    </div>
  </div>

  <div id="infobar">
    <div class="info-card">
      <div class="label">Stability Margin</div>
      <div class="value" id="info-margin">--</div>
    </div>
    <div class="info-card">
      <div class="label">Pivot B</div>
      <div class="value" id="info-pivot-b">0.0°</div>
    </div>
    <div class="info-card">
      <div class="label">Pivot C</div>
      <div class="value" id="info-pivot-c">0.0°</div>
    </div>
    <div class="info-card">
      <div class="label">Sim Time</div>
      <div class="value" id="info-time">0.00 s</div>
    </div>
  </div>
</div>

<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.162.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.162.0/examples/jsm/"
  }
}
</script>
<script type="module" src="/static/simulation.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create web/scene.js**

```javascript
/**
 * Three.js scene setup: camera, renderer, lights, grid.
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export function createScene(container) {
  const width = container.clientWidth;
  const height = container.clientHeight;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0a1a);

  // Camera
  const camera = new THREE.PerspectiveCamera(50, width / height, 0.01, 100);
  camera.position.set(2, 2, 1.5);
  camera.lookAt(0, 0, 0);

  // Renderer
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(renderer.domElement);

  // Controls
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.1;
  controls.target.set(0.3, 0, -0.2);

  // Lights
  const ambient = new THREE.AmbientLight(0x404060, 1.5);
  scene.add(ambient);
  const dirLight = new THREE.DirectionalLight(0xffffff, 2);
  dirLight.position.set(3, 5, 4);
  scene.add(dirLight);

  // Grid
  const grid = new THREE.GridHelper(10, 20, 0x1a4080, 0x0f2040);
  grid.rotation.x = Math.PI / 2; // rotate to XY plane (Z is up)
  scene.add(grid);

  // Axes helper (small)
  const axes = new THREE.AxesHelper(0.3);
  scene.add(axes);

  // Handle resize
  const onResize = () => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  };
  window.addEventListener('resize', onResize);

  return { scene, camera, renderer, controls };
}
```

- [ ] **Step 3: Create web/platform-viz.js**

```javascript
/**
 * Build and update the 3D platform mesh from simulation data.
 *
 * Coordinate mapping: simulation uses Z-up, Three.js uses Y-up.
 * We convert: sim(x,y,z) -> three(x, z, -y)
 */
import * as THREE from 'three';

// Convert sim coords (Z-up) to Three.js coords (Y-up)
function toThree(v) {
  return new THREE.Vector3(v[0], v[2], -v[1]);
}

export function createPlatformGroup() {
  const group = new THREE.Group();

  const wheelGeo = new THREE.CylinderGeometry(0.15, 0.15, 0.08, 16);
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 });
  const hubMat = new THREE.MeshStandardMaterial({ color: 0xe94560 });
  const armMat = new THREE.MeshStandardMaterial({ color: 0x4488aa, roughness: 0.5 });
  const braceMat = new THREE.MeshStandardMaterial({ color: 0x44aa66, roughness: 0.5 });

  // Wheels (cylinder rotated to stand upright)
  const wheels = {};
  for (const name of ['A', 'B', 'C']) {
    const wheel = new THREE.Mesh(wheelGeo, wheelMat);
    // Hub marker
    const hubGeo = new THREE.SphereGeometry(0.03, 8, 8);
    const hub = new THREE.Mesh(hubGeo, hubMat);
    wheel.add(hub);
    wheels[name] = wheel;
    group.add(wheel);
  }

  // Arms (lines)
  const armLineGeo1 = new THREE.BufferGeometry();
  const armLine1 = new THREE.Line(armLineGeo1, new THREE.LineBasicMaterial({ color: 0x4488aa, linewidth: 2 }));
  const armLineGeo2 = new THREE.BufferGeometry();
  const armLine2 = new THREE.Line(armLineGeo2, new THREE.LineBasicMaterial({ color: 0x4488aa, linewidth: 2 }));
  group.add(armLine1, armLine2);

  // Brace (line)
  const braceLineGeo = new THREE.BufferGeometry();
  const braceLine = new THREE.Line(braceLineGeo, new THREE.LineBasicMaterial({ color: 0x44aa66, linewidth: 2 }));
  group.add(braceLine);

  // Brace center marker (cargo mount)
  const cargoGeo = new THREE.BoxGeometry(0.1, 0.05, 0.1);
  const cargo = new THREE.Mesh(cargoGeo, braceMat);
  group.add(cargo);

  // Support triangle (flat, semi-transparent)
  const triGeo = new THREE.BufferGeometry();
  const triVerts = new Float32Array(9); // 3 vertices * 3 coords
  triGeo.setAttribute('position', new THREE.BufferAttribute(triVerts, 3));
  const triMat = new THREE.MeshBasicMaterial({
    color: 0x4ade80, transparent: true, opacity: 0.2, side: THREE.DoubleSide
  });
  const triMesh = new THREE.Mesh(triGeo, triMat);
  group.add(triMesh);

  return {
    group, wheels,
    armLine1, armLine2, braceLine,
    cargo, triMesh,
    _wheelGeo: wheelGeo,
  };
}

export function updatePlatform(viz, frame, config) {
  const { wheels, armLine1, armLine2, braceLine, cargo, triMesh, _wheelGeo } = viz;

  // Update wheel positions
  for (const name of ['A', 'B', 'C']) {
    const pos = toThree(frame.wheels[name]);
    wheels[name].position.copy(pos);
  }

  // Update wheel geometry if radius changed
  if (config && config.wheel_radius) {
    const r = config.wheel_radius;
    const w = config.wheel_width || 0.08;
    const newGeo = new THREE.CylinderGeometry(r, r, w, 16);
    for (const name of ['A', 'B', 'C']) {
      wheels[name].geometry.dispose();
      wheels[name].geometry = newGeo;
    }
  }

  // Arm lines
  const a = toThree(frame.wheels.A);
  const b = toThree(frame.wheels.B);
  const c = toThree(frame.wheels.C);

  armLine1.geometry.dispose();
  armLine1.geometry = new THREE.BufferGeometry().setFromPoints([a, b]);
  armLine2.geometry.dispose();
  armLine2.geometry = new THREE.BufferGeometry().setFromPoints([a, c]);

  // Brace line (between midpoints of arms, approximated from brace_center)
  const bc = toThree(frame.brace_center);
  // Brace endpoints: approximate as symmetric around brace_center along B-C direction
  const midBC = new THREE.Vector3().addVectors(b, c).multiplyScalar(0.5);
  const halfBrace = new THREE.Vector3().subVectors(b, c).multiplyScalar(0.25);
  const braceL = new THREE.Vector3().copy(bc).add(halfBrace);
  const braceR = new THREE.Vector3().copy(bc).sub(halfBrace);
  braceLine.geometry.dispose();
  braceLine.geometry = new THREE.BufferGeometry().setFromPoints([braceL, braceR]);

  // Cargo marker
  cargo.position.copy(bc);

  // Support triangle
  if (frame.support_triangle) {
    const verts = triMesh.geometry.attributes.position.array;
    for (let i = 0; i < 3; i++) {
      const sv = [frame.support_triangle[i][0], 0.001, -frame.support_triangle[i][1]];
      verts[i * 3] = sv[0];
      verts[i * 3 + 1] = sv[1];
      verts[i * 3 + 2] = sv[2];
    }
    triMesh.geometry.attributes.position.needsUpdate = true;
    triMesh.geometry.computeBoundingSphere();

    // Color based on stability
    const stable = frame.stability_margin > 0;
    triMesh.material.color.setHex(stable ? 0x4ade80 : 0xf87171);
  }
}
```

- [ ] **Step 4: Create web/terrain-viz.js**

```javascript
/**
 * Render terrain as a mesh from server-provided heightmap grid.
 */
import * as THREE from 'three';

export function createTerrainMesh(gridData) {
  const { size, resolution, heights } = gridData;
  const rows = heights.length;
  const cols = heights[0].length;
  const geo = new THREE.PlaneGeometry(size, size, cols - 1, rows - 1);

  // PlaneGeometry is in XY by default; we want XZ (Y-up in Three.js)
  // Actually: sim X -> three X, sim Y -> three -Z, sim Z -> three Y
  const pos = geo.attributes.position;
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const idx = j * cols + i;
      const x = pos.getX(idx);
      const y = pos.getY(idx);
      // Map: plane's (x, y) -> world (x, height, -y)
      // Note: PlaneGeometry (x, y) maps to our sim (x, y)
      const h = heights[j][i];
      pos.setXYZ(idx, x, h, -y);
    }
  }

  geo.computeVertexNormals();

  const mat = new THREE.MeshStandardMaterial({
    color: 0x2d5a27,
    roughness: 0.9,
    flatShading: true,
    side: THREE.DoubleSide,
  });

  return new THREE.Mesh(geo, mat);
}
```

- [ ] **Step 5: Create web/controls.js**

```javascript
/**
 * UI controls: read slider values, bind events, send config to server.
 */

export function readConfig() {
  return {
    arm_length: parseFloat(document.getElementById('arm-length').value),
    arm_splay_angle: parseFloat(document.getElementById('splay-angle').value) * Math.PI / 180,
    brace_position: parseFloat(document.getElementById('brace-pos').value),
    wheel_radius: parseFloat(document.getElementById('wheel-radius').value),
  };
}

export function setupControls(onChange) {
  const sliders = ['arm-length', 'splay-angle', 'brace-pos', 'wheel-radius'];
  const valEls = {
    'arm-length': 'val-arm-length',
    'splay-angle': 'val-splay',
    'brace-pos': 'val-brace-pos',
    'wheel-radius': 'val-wheel-r',
  };
  const formatters = {
    'arm-length': v => v.toFixed(2) + ' m',
    'splay-angle': v => v.toFixed(0) + '°',
    'brace-pos': v => v.toFixed(2),
    'wheel-radius': v => v.toFixed(2) + ' m',
  };

  for (const id of sliders) {
    const el = document.getElementById(id);
    el.addEventListener('input', () => {
      const v = parseFloat(el.value);
      document.getElementById(valEls[id]).textContent = formatters[id](v);
      onChange(readConfig());
    });
  }
}

export function updateInfoBar(frame) {
  const marginEl = document.getElementById('info-margin');
  if (frame.stability_margin !== undefined) {
    const m = frame.stability_margin;
    marginEl.textContent = m.toFixed(3);
    marginEl.className = 'value ' + (m > 0 ? 'stable' : 'unstable');
  }

  if (frame.arm_pivots) {
    document.getElementById('info-pivot-b').textContent =
      (frame.arm_pivots[0] * 180 / Math.PI).toFixed(1) + '°';
    document.getElementById('info-pivot-c').textContent =
      (frame.arm_pivots[1] * 180 / Math.PI).toFixed(1) + '°';
  }

  if (frame.time !== undefined) {
    document.getElementById('info-time').textContent = frame.time.toFixed(2) + ' s';
  }
}
```

- [ ] **Step 6: Create web/simulation.js**

```javascript
/**
 * Main entry point: connects WebSocket, wires controls to scene, runs render loop.
 */
import { createScene } from '/static/scene.js';
import { createPlatformGroup, updatePlatform } from '/static/platform-viz.js';
import { createTerrainMesh } from '/static/terrain-viz.js';
import { setupControls, readConfig, updateInfoBar } from '/static/controls.js';

// -- State --
let ws = null;
let platformViz = null;
let terrainMesh = null;
let currentConfig = null;
let simRunning = false;

// -- Scene setup --
const viewport = document.getElementById('viewport');
const { scene, camera, renderer, controls } = createScene(viewport);

// Platform
platformViz = createPlatformGroup();
scene.add(platformViz.group);

// -- WebSocket --
function connect() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws`);

  ws.onopen = () => {
    document.getElementById('conn-status').textContent = 'Connected';
    // Send initial config
    sendConfig(readConfig());
    // Request terrain grid
    sendTerrainRequest();
    // Request initial frame
    ws.send(JSON.stringify({ type: 'solve_ik' }));
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'frame') {
      updatePlatform(platformViz, msg, currentConfig);
      updateInfoBar(msg);
    } else if (msg.type === 'terrain_grid') {
      if (terrainMesh) scene.remove(terrainMesh);
      terrainMesh = createTerrainMesh(msg);
      scene.add(terrainMesh);
    } else if (msg.type === 'error') {
      console.error('Server error:', msg.errors);
    }
  };

  ws.onclose = () => {
    document.getElementById('conn-status').textContent = 'Disconnected';
    setTimeout(connect, 2000);
  };
}

function send(msg) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(msg));
  }
}

function sendConfig(config) {
  currentConfig = config;
  send({ type: 'set_config', params: config });
}

function sendTerrainRequest() {
  send({ type: 'get_terrain_grid', size: 6, resolution: 40 });
}

// -- Controls --
setupControls((config) => {
  sendConfig(config);
  send({ type: 'solve_ik' });
});

// Terrain selector
document.getElementById('terrain-select').addEventListener('change', (e) => {
  send({ type: 'set_terrain', name: e.target.value });
  sendTerrainRequest();
  send({ type: 'solve_ik' });
});

// Strategy selector
document.getElementById('strategy-select').addEventListener('change', (e) => {
  send({ type: 'set_strategy', name: e.target.value });
});

// Buttons
document.getElementById('btn-ik').addEventListener('click', () => {
  send({ type: 'solve_ik' });
});

document.getElementById('btn-sim').addEventListener('click', () => {
  const btn = document.getElementById('btn-sim');
  if (simRunning) {
    send({ type: 'stop_sim' });
    btn.classList.remove('active');
    btn.textContent = 'Run Sim';
    simRunning = false;
  } else {
    send({ type: 'start_sim' });
    btn.classList.add('active');
    btn.textContent = 'Stop';
    simRunning = true;
  }
});

// -- Render loop --
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

// -- Start --
connect();
animate();
```

- [ ] **Step 7: Commit**

```bash
git add web/
git commit -m "feat: Three.js web frontend with interactive controls and WebSocket client"
```

---

### Task 8: Integration Test and Polish

**Files:**
- Modify: `wheely/server.py` (if needed for bug fixes)
- No new test files -- manual integration test

**Dependencies:** All previous tasks

- [ ] **Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Start the server and verify in browser**

Run: `cd /Users/sergeyk/w/wheely && uvicorn wheely.server:app --reload --port 8000`
Expected: Server starts. Open `http://localhost:8000` in browser, see 3D platform with controls.

- [ ] **Step 3: Test interactions**

- Move geometry sliders -> platform should update in real-time
- Switch terrain preset -> terrain mesh and platform adaptation should change
- Click "Solve IK" -> platform adapts to current terrain
- Click "Run Sim" -> dynamic simulation starts, arms respond to actuation strategy
- Info bar shows stability margin, pivot angles, sim time

- [ ] **Step 4: Fix any issues found during manual testing**

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "fix: integration fixes from manual testing"
```
