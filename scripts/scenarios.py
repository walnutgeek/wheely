"""Scenario definitions for the wheely showcase deck.

Each scenario describes what to configure in the browser, how to capture it,
and what code/caption to pair with the slide.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class CaptureType(Enum):
    NONE = auto()
    SCREENSHOT = auto()
    GIF = auto()


class SlideLayout(Enum):
    TITLE = auto()
    DEMO = auto()
    COMPARISON = auto()
    TEXT = auto()


@dataclass
class CodeSnippet:
    """Reference to code to extract from source files."""
    filepath: str
    function_name: str | None = None
    class_name: str | None = None
    raw_text: str | None = None


@dataclass
class GifConfig:
    """Configuration for animated GIF capture."""
    frame_count: int = 20
    frame_interval_ms: int = 100


@dataclass
class Scenario:
    """A single slide scenario to capture and render."""
    title: str
    layout: SlideLayout
    caption: str = ""
    capture_type: CaptureType = CaptureType.NONE
    gif_config: GifConfig | None = None
    setup_messages: list[dict] = field(default_factory=list)
    frame_messages: list[dict] | None = None
    code: CodeSnippet | None = None
    second_setup_messages: list[dict] | None = None
    second_caption: str = ""
    raw_content: str = ""
    stabilize_ms: int = 500


def get_scenarios() -> list[Scenario]:
    """Return the predefined set of showcase scenarios."""
    return [
        # Slide 1: Title
        Scenario(
            title="Wheely",
            layout=SlideLayout.TITLE,
            raw_content=(
                "Self-Leveling Tricycle Platform\n\n"
                "         [Wheel A]  (apex)\n"
                "            /\\\n"
                "           /  \\\n"
                "          /    \\\n"
                "  arm1   /      \\   arm2\n"
                "        /  brace \\\n"
                "       /====[]====\\\n"
                "      /            \\\n"
                "[Wheel B]      [Wheel C]"
            ),
        ),

        # Slide 2: Geometry Overview
        Scenario(
            title="Parametric Geometry",
            layout=SlideLayout.DEMO,
            caption="All dimensions are parametric and tunable",
            capture_type=CaptureType.SCREENSHOT,
            setup_messages=[
                {"type": "set_terrain", "name": "flat"},
                {"type": "solve_ik"},
            ],
            code=CodeSnippet(
                filepath="wheely/geometry.py",
                class_name="PlatformConfig",
            ),
            stabilize_ms=800,
        ),

        # Slide 3: Parameter Exploration (arm length sweep)
        Scenario(
            title="Parameter Exploration",
            layout=SlideLayout.DEMO,
            caption="Arm length sweep -- geometry adapts in real time",
            capture_type=CaptureType.GIF,
            gif_config=GifConfig(frame_count=22, frame_interval_ms=100),
            setup_messages=[
                {"type": "set_terrain", "name": "flat"},
            ],
            frame_messages=[
                {"type": "set_config", "params": {"arm_length": round(0.4 + i * 0.05, 2)}}
                for i in range(22)
            ],
            code=CodeSnippet(
                filepath="wheely/geometry.py",
                function_name="compute_wheel_positions",
            ),
        ),

        # Slide 4: Terrain Adaptation (IK)
        Scenario(
            title="Terrain Adaptation",
            layout=SlideLayout.DEMO,
            caption="Inverse kinematics places wheels on terrain surface",
            capture_type=CaptureType.SCREENSHOT,
            setup_messages=[
                {"type": "set_terrain", "name": "steep_slope"},
                {"type": "solve_ik"},
            ],
            code=CodeSnippet(
                filepath="wheely/kinematics.py",
                function_name="inverse_kinematics",
            ),
            stabilize_ms=800,
        ),

        # Slide 5: Bumpy Terrain (position sweep GIF)
        Scenario(
            title="Bumpy Terrain Traversal",
            layout=SlideLayout.DEMO,
            caption="Arms adapt independently -- one up, one down",
            capture_type=CaptureType.GIF,
            gif_config=GifConfig(frame_count=30, frame_interval_ms=100),
            setup_messages=[
                {"type": "set_terrain", "name": "bumpy"},
            ],
            frame_messages=[
                {"type": "set_position", "x": round(-2.0 + i * (4.0 / 29), 2), "y": 0.0}
                for i in range(30)
            ],
            code=CodeSnippet(
                filepath="wheely/kinematics.py",
                function_name="inverse_kinematics",
            ),
        ),

        # Slide 6: Dynamic Simulation (Passive)
        Scenario(
            title="Passive Dynamics",
            layout=SlideLayout.DEMO,
            caption="Passive arms settle on terrain via gravity + contact forces",
            capture_type=CaptureType.GIF,
            gif_config=GifConfig(frame_count=30, frame_interval_ms=100),
            setup_messages=[
                {"type": "set_terrain", "name": "bumpy"},
                {"type": "set_strategy", "name": "passive"},
                {"type": "start_sim"},
            ],
            code=CodeSnippet(
                filepath="wheely/dynamics.py",
                function_name="simulate_step",
            ),
            stabilize_ms=200,
        ),

        # Slide 7: Spring-Damper Comparison
        Scenario(
            title="Strategy Comparison",
            layout=SlideLayout.COMPARISON,
            caption="Spring-damper provides faster convergence",
            capture_type=CaptureType.GIF,
            gif_config=GifConfig(frame_count=30, frame_interval_ms=100),
            setup_messages=[
                {"type": "set_terrain", "name": "bumpy"},
                {"type": "set_strategy", "name": "passive"},
                {"type": "start_sim"},
            ],
            second_setup_messages=[
                {"type": "stop_sim"},
                {"type": "set_position", "x": 0.0, "y": 0.0},
                {"type": "set_strategy", "name": "spring_damper"},
                {"type": "start_sim"},
            ],
            second_caption="Spring-Damper",
            code=CodeSnippet(
                filepath="wheely/dynamics.py",
                class_name="SpringDamperStrategy",
            ),
        ),

        # Slide 8: Stability Analysis
        Scenario(
            title="Stability Analysis",
            layout=SlideLayout.DEMO,
            caption="Support triangle and stability margin visualization",
            capture_type=CaptureType.SCREENSHOT,
            setup_messages=[
                {"type": "set_terrain", "name": "cross_slope"},
                {"type": "solve_ik"},
            ],
            code=CodeSnippet(
                filepath="wheely/kinematics.py",
                function_name="compute_stability_margin",
            ),
            stabilize_ms=800,
        ),

        # Slide 9: Architecture
        Scenario(
            title="Architecture",
            layout=SlideLayout.TEXT,
            raw_content=(
                "wheely/           Python package\n"
                "  geometry.py     Parametric platform geometry\n"
                "  terrain.py      Terrain models (flat, slope, sinusoidal)\n"
                "  kinematics.py   Forward/inverse kinematics, stability\n"
                "  dynamics.py     Actuation strategies, time integration\n"
                "  server.py       FastAPI + WebSocket real-time sim\n"
                "web/              Three.js frontend\n"
                "tests/            pytest test suite\n"
                "scripts/          Showcase generation tools"
            ),
            caption=(
                "Pure Python backend + Three.js frontend | "
                "WebSocket real-time communication | "
                "Parametric design, pluggable strategies"
            ),
        ),
    ]
