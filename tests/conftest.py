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
