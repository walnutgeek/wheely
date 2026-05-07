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
    """Plane with constant slope: z = slope_x * x + slope_y * y."""

    slope_x: float = 0.0
    slope_y: float = 0.0

    def height(self, x: float, y: float) -> float:
        return self.slope_x * x + self.slope_y * y

    def height_batch(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        return self.slope_x * xs + self.slope_y * ys

    def normal(self, x: float, y: float) -> np.ndarray:
        n = np.array([-self.slope_x, -self.slope_y, 1.0])
        return n / np.linalg.norm(n)


@dataclass
class SinusoidalTerrain:
    """Sinusoidal bumps: z = amplitude * sin(2*pi*x/wavelength) * sin(2*pi*y/wavelength)."""

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
        eps = 1e-6
        z_xp = self.height(x + eps, y)
        z_xm = self.height(x - eps, y)
        z_yp = self.height(x, y + eps)
        z_ym = self.height(x, y - eps)
        dz_dx = (z_xp - z_xm) / (2.0 * eps)
        dz_dy = (z_yp - z_ym) / (2.0 * eps)
        n = np.array([-dz_dx, -dz_dy, 1.0])
        return n / np.linalg.norm(n)
