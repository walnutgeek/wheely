# Wheely Showcase Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Playwright-based capture pipeline that generates a self-contained reveal.js HTML slide deck showcasing the wheely platform's features.

**Architecture:** CLI script orchestrates a uvicorn server, uses Playwright to drive the browser and capture screenshots/GIFs of predefined scenarios, then assembles them with extracted code snippets into a single HTML file using base64-embedded media.

**Tech Stack:** Python, Playwright, Pillow, ast module, reveal.js (CDN), highlight.js (CDN)

---

### Task 1: Add showcase dependencies to pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add showcase optional dependency group**

Add to `pyproject.toml` after the `dev` section:

```toml
showcase = [
    "playwright>=1.40",
    "Pillow>=10.0",
]
```

The full `[project.optional-dependencies]` section becomes:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "hypothesis>=6.98",
    "httpx>=0.27",
]
showcase = [
    "playwright>=1.40",
    "Pillow>=10.0",
]
```

- [ ] **Step 2: Verify installation**

Run: `pip install -e ".[showcase]"`
Expected: installs without errors

- [ ] **Step 3: Add output/ to .gitignore**

Append `output/` to `.gitignore`:

```
output/
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml .gitignore
git commit -m "feat: add showcase optional dependencies (playwright, Pillow)"
```

---

### Task 2: Create scenarios.py with scenario definitions

**Files:**
- Create: `scripts/scenarios.py`

- [ ] **Step 1: Write the scenario module**

```python
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
    raw_text: str | None = None  # For inline text (non-extracted)


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

    # WebSocket messages to send before capture
    setup_messages: list[dict] = field(default_factory=list)

    # For GIF: messages to send between frames (e.g., parameter sweep)
    frame_messages: list[dict] | None = None

    # Code to display on the slide
    code: CodeSnippet | None = None

    # For COMPARISON layout: second capture config
    second_setup_messages: list[dict] | None = None
    second_caption: str = ""

    # For TITLE/TEXT layouts: raw content
    raw_content: str = ""

    # Wait time after setup (ms)
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
            ] + [{"type": "solve_ik"}] * 22,  # will be interleaved in capture
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
```

- [ ] **Step 2: Verify module imports**

Run: `python3 -c "from scripts.scenarios import get_scenarios, Scenario; print(len(get_scenarios()))"`

This will fail because `scripts/` isn't a package. Instead test directly:

Run: `python3 -c "import sys; sys.path.insert(0, '.'); exec(open('scripts/scenarios.py').read()); print(len(get_scenarios()))"`
Expected: `9`

- [ ] **Step 3: Commit**

```bash
git add scripts/scenarios.py
git commit -m "feat: add showcase scenario definitions (9 slides)"
```

---

### Task 3: Create capture.py with Playwright automation

**Files:**
- Create: `scripts/capture.py`

- [ ] **Step 1: Write the capture module**

```python
"""Playwright browser automation for capturing screenshots and GIFs.

Drives a headless Chromium browser, connects to the wheely server via WebSocket,
sends scenario setup messages, and captures the #viewport element.
"""

from __future__ import annotations

import io
import json
import time

from PIL import Image
from playwright.sync_api import Page, sync_playwright

from scripts.scenarios import CaptureType, GifConfig, Scenario


def wait_for_connection(page: Page, timeout_ms: int = 10000) -> None:
    """Wait until the WebSocket connection status shows 'Connected'."""
    page.wait_for_function(
        "() => document.getElementById('conn-status').textContent === 'Connected'",
        timeout=timeout_ms,
    )


def send_ws_message(page: Page, message: dict) -> None:
    """Send a WebSocket message from the browser page."""
    page.evaluate(f"window._ws.send(JSON.stringify({json.dumps(message)}))")


def capture_screenshot(page: Page) -> bytes:
    """Capture the #viewport element as PNG bytes."""
    element = page.locator("#viewport")
    return element.screenshot(type="png")


def capture_gif(page: Page, gif_config: GifConfig, frame_messages: list[dict] | None = None) -> bytes:
    """Capture an animated GIF of the #viewport element.

    Args:
        page: Playwright page with active WebSocket.
        gif_config: Frame count and interval.
        frame_messages: Optional per-frame messages to send before each capture.
                       If provided, one message is sent per frame.

    Returns:
        GIF image bytes.
    """
    element = page.locator("#viewport")
    frames: list[bytes] = []

    for i in range(gif_config.frame_count):
        if frame_messages and i < len(frame_messages):
            send_ws_message(page, frame_messages[i])
            # After config/position change, send solve_ik to update
            if frame_messages[i].get("type") in ("set_config", "set_position"):
                send_ws_message(page, {"type": "solve_ik"})
            page.wait_for_timeout(gif_config.frame_interval_ms)
        else:
            page.wait_for_timeout(gif_config.frame_interval_ms)

        frames.append(element.screenshot(type="png"))

    return _assemble_gif(frames, gif_config.frame_interval_ms)


def _assemble_gif(frames: list[bytes], duration_ms: int) -> bytes:
    """Assemble PNG frame bytes into an animated GIF."""
    images = [Image.open(io.BytesIO(f)) for f in frames]
    # Convert RGBA to RGB with white background for GIF compatibility
    rgb_images = []
    for img in images:
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (26, 26, 46))  # Match dark theme background
            bg.paste(img, mask=img.split()[3])
            rgb_images.append(bg)
        else:
            rgb_images.append(img.convert("RGB"))

    gif_buffer = io.BytesIO()
    rgb_images[0].save(
        gif_buffer,
        format="GIF",
        save_all=True,
        append_images=rgb_images[1:],
        duration=duration_ms,
        loop=0,
    )
    return gif_buffer.getvalue()


def run_scenario_capture(
    page: Page,
    scenario: Scenario,
) -> tuple[bytes | None, bytes | None]:
    """Execute a scenario and capture its output.

    Returns:
        (primary_capture, secondary_capture) - bytes or None depending on scenario.
        For COMPARISON layout, both are populated. Otherwise only primary.
    """
    if scenario.capture_type == CaptureType.NONE:
        return None, None

    # Send setup messages
    for msg in scenario.setup_messages:
        send_ws_message(page, msg)
        page.wait_for_timeout(100)

    # Wait for stabilization
    page.wait_for_timeout(scenario.stabilize_ms)

    primary: bytes | None = None
    secondary: bytes | None = None

    if scenario.capture_type == CaptureType.SCREENSHOT:
        primary = capture_screenshot(page)

    elif scenario.capture_type == CaptureType.GIF:
        gif_config = scenario.gif_config or GifConfig()
        primary = capture_gif(page, gif_config, scenario.frame_messages)

        # For comparison layout, capture second GIF
        if scenario.second_setup_messages:
            for msg in scenario.second_setup_messages:
                send_ws_message(page, msg)
                page.wait_for_timeout(100)
            page.wait_for_timeout(scenario.stabilize_ms)
            secondary = capture_gif(page, gif_config)

    # Stop any running simulation
    send_ws_message(page, {"type": "stop_sim"})
    page.wait_for_timeout(200)

    return primary, secondary


def run_all_captures(
    url: str = "http://localhost:8765",
    viewport_width: int = 1280,
    viewport_height: int = 720,
) -> list[tuple[bytes | None, bytes | None]]:
    """Launch browser and capture all scenarios.

    Args:
        url: URL of the running wheely server.
        viewport_width: Browser viewport width.
        viewport_height: Browser viewport height.

    Returns:
        List of (primary_bytes, secondary_bytes) per scenario.
    """
    from scripts.scenarios import get_scenarios

    scenarios = get_scenarios()
    results: list[tuple[bytes | None, bytes | None]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": viewport_width, "height": viewport_height})
        page.goto(url)

        # Wait for WebSocket connection
        wait_for_connection(page)

        # Expose the WebSocket for message sending
        page.evaluate("""() => {
            // The app's WebSocket is stored on window by simulation.js
            // We need to find it - check common patterns
            if (!window._ws) {
                // Find the WebSocket instance
                const origWS = WebSocket;
                const sockets = [];
                // It should already be connected, find it via prototype
                // Fallback: create a reference
            }
        }""")

        # Give a moment for the page to fully initialize
        page.wait_for_timeout(1000)

        for scenario in scenarios:
            print(f"  Capturing: {scenario.title}")
            result = run_scenario_capture(page, scenario)
            results.append(result)

        browser.close()

    return results
```

- [ ] **Step 2: Commit**

```bash
git add scripts/capture.py
git commit -m "feat: add Playwright capture module for screenshots and GIFs"
```

---

### Task 4: Create deck_builder.py for HTML assembly

**Files:**
- Create: `scripts/deck_builder.py`

- [ ] **Step 1: Write the deck builder module**

```python
"""Assemble captured media and code snippets into a reveal.js HTML deck.

Produces a single self-contained HTML file with all images embedded as base64
data URIs. Uses reveal.js and highlight.js from CDN.
"""

from __future__ import annotations

import ast
import base64
import html
import textwrap
from pathlib import Path

from scripts.scenarios import CodeSnippet, Scenario, SlideLayout


def extract_code(snippet: CodeSnippet) -> str:
    """Extract code from source file using AST parsing.

    Handles function_name, class_name, or raw_text.
    """
    if snippet.raw_text:
        return snippet.raw_text

    filepath = Path(snippet.filepath)
    if not filepath.exists():
        return f"# Source not found: {snippet.filepath}"

    source = filepath.read_text()
    tree = ast.parse(source)

    target_name = snippet.function_name or snippet.class_name
    if not target_name:
        return source[:500]  # Fallback: first 500 chars

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == target_name:
                lines = source.splitlines()
                extracted = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                return textwrap.dedent(extracted)

    return f"# {target_name} not found in {snippet.filepath}"


def _img_tag(data: bytes, mime: str) -> str:
    """Create an <img> tag with base64 data URI."""
    b64 = base64.b64encode(data).decode("ascii")
    return f'<img src="data:{mime};base64,{b64}" />'


def _build_title_slide(scenario: Scenario) -> str:
    """Build a title layout slide."""
    content = html.escape(scenario.raw_content)
    return f"""<section>
  <h1>{html.escape(scenario.title)}</h1>
  <pre class="ascii">{content}</pre>
</section>"""


def _build_demo_slide(scenario: Scenario, primary: bytes | None) -> str:
    """Build a demo layout slide (visual + code)."""
    visual_html = ""
    if primary:
        mime = "image/gif" if scenario.capture_type.name == "GIF" else "image/png"
        visual_html = _img_tag(primary, mime)

    code_html = ""
    if scenario.code:
        code_text = html.escape(extract_code(scenario.code))
        code_html = f'<pre><code class="language-python">{code_text}</code></pre>'

    caption_html = ""
    if scenario.caption:
        caption_html = f'<p class="caption">{html.escape(scenario.caption)}</p>'

    return f"""<section>
  <h2>{html.escape(scenario.title)}</h2>
  <div class="split">
    <div class="visual">
      {visual_html}
    </div>
    <div class="code-panel">
      {code_html}
      {caption_html}
    </div>
  </div>
</section>"""


def _build_comparison_slide(
    scenario: Scenario, primary: bytes | None, secondary: bytes | None
) -> str:
    """Build a comparison layout slide (two GIFs side by side)."""
    img1 = _img_tag(primary, "image/gif") if primary else ""
    img2 = _img_tag(secondary, "image/gif") if secondary else ""

    code_html = ""
    if scenario.code:
        code_text = html.escape(extract_code(scenario.code))
        code_html = f'<pre><code class="language-python">{code_text}</code></pre>'

    return f"""<section>
  <h2>{html.escape(scenario.title)}</h2>
  <div class="compare">
    <div>
      {img1}
      <p class="label">Passive</p>
    </div>
    <div>
      {img2}
      <p class="label">{html.escape(scenario.second_caption)}</p>
    </div>
  </div>
  {code_html}
  <p class="caption">{html.escape(scenario.caption)}</p>
</section>"""


def _build_text_slide(scenario: Scenario) -> str:
    """Build a text-only layout slide."""
    content = html.escape(scenario.raw_content)
    caption_html = ""
    if scenario.caption:
        items = scenario.caption.split(" | ")
        li_items = "".join(f"<li>{html.escape(item)}</li>" for item in items)
        caption_html = f"<ul>{li_items}</ul>"

    return f"""<section>
  <h2>{html.escape(scenario.title)}</h2>
  <pre class="structure">{content}</pre>
  {caption_html}
</section>"""


DECK_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Wheely Showcase</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/black.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/monokai.min.css">
<style>
  :root {{
    --r-background-color: #1a1a2e;
    --r-main-color: #e0e0e0;
    --r-heading-color: #e94560;
    --r-link-color: #e94560;
  }}
  .reveal {{ font-size: 24px; }}
  .reveal h1 {{ color: #e94560; font-size: 2.5em; }}
  .reveal h2 {{ color: #e94560; font-size: 1.8em; margin-bottom: 0.5em; }}
  .reveal pre {{ font-size: 0.55em; }}
  .reveal pre.ascii, .reveal pre.structure {{
    text-align: left; font-size: 0.5em; background: #0a0a1a;
    padding: 20px; border-radius: 8px; display: inline-block;
  }}
  .split {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 20px; align-items: start; text-align: left;
  }}
  .split .visual img {{
    max-width: 100%; border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  .split .code-panel pre {{
    margin: 0; max-height: 400px; overflow-y: auto;
  }}
  .compare {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 20px; margin-bottom: 20px;
  }}
  .compare img {{
    max-width: 100%; border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  .compare .label {{
    text-align: center; font-weight: bold; margin-top: 8px;
    color: #e94560;
  }}
  .caption {{
    font-style: italic; color: #aaa; margin-top: 12px; font-size: 0.9em;
  }}
  ul {{ text-align: left; list-style: disc; padding-left: 1.5em; }}
</style>
</head>
<body>
<div class="reveal">
  <div class="slides">
{slides}
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/highlight.js"></script>
<script>
Reveal.initialize({{
  hash: true,
  plugins: [RevealHighlight],
  width: 1280,
  height: 720,
}});
</script>
</body>
</html>
"""


def build_deck(
    scenarios: list[Scenario],
    captures: list[tuple[bytes | None, bytes | None]],
) -> str:
    """Build the complete reveal.js HTML deck.

    Args:
        scenarios: List of scenario definitions.
        captures: List of (primary_bytes, secondary_bytes) per scenario.

    Returns:
        Complete HTML string for the deck.
    """
    slides_html = []

    for scenario, (primary, secondary) in zip(scenarios, captures):
        if scenario.layout == SlideLayout.TITLE:
            slides_html.append(_build_title_slide(scenario))
        elif scenario.layout == SlideLayout.DEMO:
            slides_html.append(_build_demo_slide(scenario, primary))
        elif scenario.layout == SlideLayout.COMPARISON:
            slides_html.append(_build_comparison_slide(scenario, primary, secondary))
        elif scenario.layout == SlideLayout.TEXT:
            slides_html.append(_build_text_slide(scenario))

    all_slides = "\n".join(f"    {s}" for s in slides_html)
    return DECK_TEMPLATE.format(slides=all_slides)
```

- [ ] **Step 2: Commit**

```bash
git add scripts/deck_builder.py
git commit -m "feat: add deck builder for reveal.js HTML assembly"
```

---

### Task 5: Create showcase.py CLI orchestrator

**Files:**
- Create: `scripts/showcase.py`

- [ ] **Step 1: Write the orchestrator script**

```python
"""CLI entry point for generating the wheely showcase deck.

Orchestrates:
1. Start uvicorn server
2. Wait for server ready
3. Run Playwright captures for all scenarios
4. Assemble HTML deck
5. Shut down server

Usage:
    python scripts/showcase.py [--port 8765] [--output output/showcase.html]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import httpx


def start_server(port: int) -> subprocess.Popen:
    """Start the wheely uvicorn server as a subprocess."""
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "wheely.server:app",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


def wait_for_server(port: int, timeout: float = 15.0) -> bool:
    """Poll the server until it's ready or timeout."""
    url = f"http://localhost:{port}/api/config"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200:
                return True
        except (httpx.ConnectError, httpx.ReadTimeout):
            pass
        time.sleep(0.3)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate wheely showcase deck")
    parser.add_argument("--port", type=int, default=8765, help="Server port (default: 8765)")
    parser.add_argument(
        "--output",
        type=str,
        default="output/showcase.html",
        help="Output HTML path (default: output/showcase.html)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting wheely server on port {args.port}...")
    server_proc = start_server(args.port)

    try:
        if not wait_for_server(args.port):
            print("ERROR: Server failed to start within timeout")
            server_proc.terminate()
            return 1

        print("Server ready. Starting capture...")
        url = f"http://localhost:{args.port}"

        # Import here to avoid import errors if playwright not installed
        from scripts.capture import run_all_captures
        from scripts.deck_builder import build_deck
        from scripts.scenarios import get_scenarios

        scenarios = get_scenarios()
        captures = run_all_captures(url=url)

        print("Building deck...")
        deck_html = build_deck(scenarios, captures)

        output_path.write_text(deck_html)
        print(f"Showcase deck saved to: {output_path}")
        print(f"  File size: {output_path.stat().st_size / 1024:.0f} KB")
        print(f"  Slides: {len(scenarios)}")

        return 0

    finally:
        print("Shutting down server...")
        server_proc.terminate()
        server_proc.wait(timeout=5)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Commit**

```bash
git add scripts/showcase.py
git commit -m "feat: add showcase CLI orchestrator (server + capture + build)"
```

---

### Task 6: Wire up WebSocket access in the frontend for Playwright

**Files:**
- Modify: `web/simulation.js`

The capture module needs `window._ws` to be accessible. We need to ensure the WebSocket reference is stored on `window` so Playwright's `page.evaluate()` can send messages through it.

- [ ] **Step 1: Read current simulation.js to find WebSocket creation**

Read `web/simulation.js` and locate where the WebSocket is created. Add `window._ws = ws;` after creation so Playwright can access it.

- [ ] **Step 2: Add window._ws assignment**

Find the line where the WebSocket is created (likely `const ws = new WebSocket(...)` or `let ws = new WebSocket(...)`) and add `window._ws = ws;` immediately after.

If the file already assigns it to a module-scoped variable, add an explicit `window._ws = ws;` after the WebSocket is opened, e.g.:

```javascript
// After ws = new WebSocket(wsUrl);
window._ws = ws;
```

- [ ] **Step 3: Commit**

```bash
git add web/simulation.js
git commit -m "feat: expose WebSocket as window._ws for Playwright automation"
```

---

### Task 7: Create the Claude skill file

**Files:**
- Create: `.claude/skills/showcase.md`

- [ ] **Step 1: Write the skill file**

```markdown
---
name: showcase
description: Generate or update the wheely showcase deck (reveal.js HTML with screenshots and GIFs)
user_invocable: true
---

# Showcase Deck Generation

Generate a self-contained HTML slide deck demonstrating the wheely simulation platform.

## Prerequisites

```bash
pip install -e ".[showcase]"
playwright install chromium
```

## Generate the deck

```bash
python scripts/showcase.py
```

Output: `output/showcase.html` (open in any browser)

## Options

- `--port PORT` - Use a different server port (default: 8765)
- `--output PATH` - Write deck to a different path

## Customizing scenarios

Edit `scripts/scenarios.py` to add/modify/remove slides. Each `Scenario` dataclass defines:
- `title`: Slide heading
- `layout`: TITLE, DEMO, COMPARISON, or TEXT
- `capture_type`: NONE, SCREENSHOT, or GIF
- `setup_messages`: WebSocket messages to configure the scene
- `frame_messages`: Per-frame messages for GIF animations (parameter sweeps, position changes)
- `code`: CodeSnippet reference to extract from source
- `caption`: Explanatory text

## Regenerating after code changes

Run `python scripts/showcase.py` again. Code snippets are extracted from live source files, so the deck always reflects current implementation.

## Architecture

```
scripts/
├── showcase.py      # CLI orchestrator (server lifecycle, pipeline)
├── scenarios.py     # Scenario definitions (what to capture)
├── capture.py       # Playwright browser automation, screenshot/GIF capture
└── deck_builder.py  # HTML assembly with reveal.js + highlight.js
```
```

- [ ] **Step 2: Commit**

```bash
mkdir -p .claude/skills
git add .claude/skills/showcase.md
git commit -m "feat: add Claude showcase skill for deck generation"
```

---

### Task 8: Integration test -- generate the deck end-to-end

**Files:**
- No new files (verification task)

- [ ] **Step 1: Ensure dependencies are installed**

Run: `pip install -e ".[showcase]" && playwright install chromium`
Expected: Successful installation

- [ ] **Step 2: Run the showcase generator**

Run: `python3 scripts/showcase.py --port 8766`
Expected: Server starts, captures complete, deck saved to `output/showcase.html`

- [ ] **Step 3: Verify output**

Run: `python3 -c "from pathlib import Path; p = Path('output/showcase.html'); print(f'Size: {p.stat().st_size / 1024:.0f} KB'); content = p.read_text(); print(f'Slides: {content.count(\"<section>\")}'); assert '<section>' in content; assert 'reveal.js' in content; print('OK')"`
Expected: Reports file size, 9 slides, prints OK

- [ ] **Step 4: Fix any issues found during integration test**

If the end-to-end run fails, fix the issue in the appropriate script and re-run.

- [ ] **Step 5: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: integration fixes for showcase generation"
```
