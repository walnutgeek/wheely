# Wheely Showcase Skill Design

## Overview

A project-local Claude skill and supporting Python scripts that automatically generate a self-contained HTML slide deck demonstrating the wheely simulation platform. Uses Playwright for browser automation to capture screenshots and animated GIFs of predefined scenarios, then assembles them with code snippets and captions into a single reveal.js HTML file.

## Components

### File Structure

```
scripts/
├── showcase.py          # CLI entry point: orchestrates server, capture, and deck assembly
├── scenarios.py         # Scenario definitions (what to capture)
├── capture.py           # Playwright browser automation, screenshot/GIF capture
└── deck_builder.py      # Assemble HTML deck from captures + code + captions

.claude/
└── skills/
    └── showcase.md      # Claude skill: instructions for invoking and customizing

output/                  # Generated artifacts (gitignored)
└── showcase.html        # Self-contained reveal.js deck
```

### Dependencies

Add to `pyproject.toml` optional dependencies:

```toml
[project.optional-dependencies]
showcase = [
    "playwright>=1.40",
    "Pillow>=10.0",
]
```

Playwright browser binaries installed via `playwright install chromium`.

## Predefined Scenario Set

Each scenario is a dataclass defining what to configure, how long to wait, what to capture, and what code/caption to pair with it.

### Slide 1: Title

- Text-only slide: "Wheely -- Self-Leveling Tricycle Platform"
- One-line description and ASCII geometry diagram
- No browser capture needed

### Slide 2: Geometry Overview

- **Setup**: Default PlatformConfig, flat terrain, solve IK
- **Capture**: Single screenshot of the 3D view
- **Code**: `PlatformConfig` dataclass with defaults from `wheely/geometry.py`
- **Caption**: "All dimensions are parametric and tunable"

### Slide 3: Parameter Exploration

- **Setup**: Flat terrain. Animate arm_length from 0.4 to 1.4 in steps of 0.1, solve IK after each change
- **Capture**: Animated GIF (~20 frames, 100ms per frame)
- **Code**: `compute_wheel_positions()` signature and docstring
- **Caption**: "Arm length sweep -- geometry adapts in real time"

### Slide 4: Terrain Adaptation (IK)

- **Setup**: Switch to steep_slope terrain, solve IK
- **Capture**: Screenshot showing platform with arms at different angles on slope
- **Code**: `inverse_kinematics()` function body (core solver)
- **Caption**: "Inverse kinematics places wheels on terrain surface"

### Slide 5: Bumpy Terrain

- **Setup**: Switch to bumpy terrain, solve IK
- **Capture**: Animated GIF -- move platform position across terrain (x from -2 to 2), solve IK at each position
- **Code**: Parallelogram self-leveling explanation (from spec doc)
- **Caption**: "Arms adapt independently -- one up, one down"

### Slide 6: Dynamic Simulation (Passive)

- **Setup**: Bumpy terrain, passive strategy, start sim from displaced arm position
- **Capture**: Animated GIF of ~3 seconds of simulation (arms settling)
- **Code**: `simulate_step()` and `_compute_terrain_contact_torque()`
- **Caption**: "Passive arms settle on terrain via gravity + contact forces"

### Slide 7: Spring-Damper Comparison

- **Layout**: Comparison slide (two GIFs side by side)
- **Setup**: Bumpy terrain. Capture passive strategy first (start sim, record GIF, stop sim). Then reset state, switch to spring-damper strategy, capture second GIF. Both GIFs are captured sequentially in the same browser session.
- **Capture**: Two animated GIFs (~3 seconds each, captured one after another)
- **Code**: `SpringDamperStrategy.compute_torques()`
- **Caption**: "Spring-damper provides faster convergence"

### Slide 8: Stability Analysis

- **Setup**: Cross-slope terrain, solve IK. Show stable (green triangle) configuration.
- **Capture**: Screenshot
- **Code**: `compute_stability_margin()` function
- **Caption**: "Support triangle and stability margin visualization"

### Slide 9: Architecture

- Text-only slide: project structure, tech stack summary, design decisions
- No browser capture needed

## Capture Pipeline

### Server Lifecycle

1. `showcase.py` starts `uvicorn wheely.server:app --port 8765` as a subprocess
2. Waits for server to be ready (poll `http://localhost:8765/api/config`)
3. Runs all captures
4. Terminates server subprocess

### Playwright Automation

1. Launch headless Chromium at 1280x720 viewport
2. Navigate to `http://localhost:8765`
3. Wait for WebSocket connection (poll `document.getElementById('conn-status').textContent === 'Connected'`)
4. For each scenario:
   a. Execute JavaScript in page to send WebSocket messages (terrain, config, IK/sim)
   b. Wait for stabilization (fixed delay or poll info bar values)
   c. Capture the `#viewport` element (not full page -- just the 3D view)

### Screenshot Capture

```python
element = page.locator('#viewport')
screenshot_bytes = element.screenshot(type='png')
```

### Animated GIF Capture

```python
frames = []
for i in range(frame_count):
    frames.append(element.screenshot(type='png'))
    page.wait_for_timeout(frame_interval_ms)

# Assemble with Pillow
from PIL import Image
import io

images = [Image.open(io.BytesIO(f)) for f in frames]
gif_buffer = io.BytesIO()
images[0].save(
    gif_buffer, format='GIF', save_all=True,
    append_images=images[1:], duration=frame_interval_ms, loop=0,
)
gif_bytes = gif_buffer.getvalue()
```

### Code Snippet Extraction

Read actual source files and extract specific functions/classes by name. Use `ast` module to find the function definition and extract its source lines. This keeps the deck in sync with the codebase.

```python
import ast, inspect, textwrap

def extract_function_source(filepath: str, function_name: str) -> str:
    with open(filepath) as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == function_name:
            lines = source.splitlines()
            return '\n'.join(lines[node.lineno - 1 : node.end_lineno])
    raise ValueError(f"{function_name} not found in {filepath}")
```

## Deck Assembly

### HTML Template

Single-file reveal.js deck. reveal.js and its theme CSS loaded from CDN. All images embedded as base64 data URIs.

### Slide Layouts

**Title layout:**
```html
<section>
  <h1>Wheely</h1>
  <p class="subtitle">Self-leveling tricycle robotic platform</p>
  <pre class="ascii"><!-- geometry diagram --></pre>
</section>
```

**Demo layout (screenshot/GIF + code):**
```html
<section>
  <h2>Slide Title</h2>
  <div class="split">
    <div class="visual">
      <img src="data:image/png;base64,..." />
    </div>
    <div class="code-panel">
      <pre><code class="language-python">...</code></pre>
      <p class="caption">Caption text</p>
    </div>
  </div>
</section>
```

**Comparison layout (two GIFs):**
```html
<section>
  <h2>Slide Title</h2>
  <div class="compare">
    <div>
      <img src="data:image/gif;base64,..." />
      <p class="label">Passive</p>
    </div>
    <div>
      <img src="data:image/gif;base64,..." />
      <p class="label">Spring-Damper</p>
    </div>
  </div>
  <pre><code class="language-python">...</code></pre>
</section>
```

**Text layout:**
```html
<section>
  <h2>Architecture</h2>
  <pre class="structure"><!-- project tree --></pre>
  <ul><!-- design decisions --></ul>
</section>
```

### Styling

Dark theme matching the wheely web UI colors:
- Background: `#1a1a2e`
- Accent: `#e94560`
- Code blocks: syntax-highlighted via highlight.js (CDN)
- Images: rounded corners, subtle shadow

## Claude Skill

`.claude/skills/showcase.md` contains:
- Instructions for generating the deck: `python scripts/showcase.py`
- Prerequisites: `pip install -e ".[showcase]"` and `playwright install chromium`
- How to add/modify scenarios: edit `scripts/scenarios.py`
- How to regenerate after code changes

The skill is invoked when the user asks to generate or update the showcase deck.

## Scope Boundaries

### In scope

- Predefined set of 9 slides covering key platform features
- Playwright-based screenshot and animated GIF capture
- Single-file reveal.js HTML output
- Code snippets extracted from live source
- Claude skill file with usage instructions

### Out of scope

- Video (MP4) capture
- User-configurable scenarios (future enhancement)
- Deployment/hosting of the deck
- CI integration for auto-generating on commit
