# Config Save/Load & Figure-8 Motion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JSON config download/upload and a figure-8 prescribed motion mode that demonstrates PD control responding to terrain.

**Architecture:** Two independent features. Config save/load is pure frontend (JSON download/upload via browser APIs). Figure-8 motion adds a `figure8_motion()` function to dynamics.py that advances body_xy/body_yaw along a lemniscate path, wired through server.py and visualized via group transforms in the frontend.

**Tech Stack:** Python (FastAPI, dataclasses, math), JavaScript (Three.js, browser File API)

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `web/controls.js` | Modify | Add `saveConfig()`, `loadConfig(onApply)`, `applyConfig(json, onChange)` |
| `web/index.html` | Modify | Add Save/Load buttons, hidden file input, Motion dropdown |
| `web/simulation.js` | Modify | Wire save/load buttons, motion dropdown |
| `web/platform-viz.js` | Modify | Apply body position/yaw as group transform |
| `wheely/dynamics.py` | Modify | Add `path_theta` to SimState, add `figure8_motion()`, pass motion mode through `simulate_step` |
| `wheely/server.py` | Modify | Add `motion_mode` state, `set_motion` handler, pass body position to frame, pass motion to simulate_step |
| `tests/test_dynamics.py` | Modify | Add tests for `figure8_motion()` |

---

### Task 1: Config Save/Load (Frontend Only)

**Files:**
- Modify: `web/controls.js`
- Modify: `web/index.html`
- Modify: `web/simulation.js`

This task is **independent** of Task 2 and Task 3. No backend changes.

- [ ] **Step 1: Add Save/Load buttons and hidden file input to index.html**

In `web/index.html`, add a "Presets" section at the top of `#panel-controls` (before the Terrain h2), and a hidden file input at the end of the body:

```html
<!-- Add at the top of #panel-controls, before <h2>Terrain</h2> -->
<h2>Presets</h2>
<div class="btn-row">
  <div class="btn" id="btn-save">Save</div>
  <div class="btn" id="btn-load">Load</div>
</div>
```

```html
<!-- Add just before the closing </div> of #panel-controls -->
<input type="file" id="file-input" accept=".json" style="display:none">
```

- [ ] **Step 2: Add saveConfig and applyConfig to controls.js**

Add these two exported functions to `web/controls.js`:

```javascript
export function saveConfig() {
  const config = {
    arm_length: parseFloat(document.getElementById('arm-length').value),
    arm_splay_angle_deg: parseFloat(document.getElementById('splay-angle').value),
    brace_position: parseFloat(document.getElementById('brace-pos').value),
    wheel_radius: parseFloat(document.getElementById('wheel-radius').value),
    clearance: parseFloat(document.getElementById('clearance').value),
    arm_height: parseFloat(document.getElementById('arm-height-viz').value),
    terrain: document.getElementById('terrain-select').value,
    strategy: document.getElementById('strategy-select').value,
  };
  const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'wheely-config.json';
  a.click();
  URL.revokeObjectURL(url);
}

export function applyConfig(json, onChange) {
  if (json.arm_length !== undefined) document.getElementById('arm-length').value = json.arm_length;
  if (json.arm_splay_angle_deg !== undefined) document.getElementById('splay-angle').value = json.arm_splay_angle_deg;
  if (json.brace_position !== undefined) document.getElementById('brace-pos').value = json.brace_position;
  if (json.wheel_radius !== undefined) document.getElementById('wheel-radius').value = json.wheel_radius;
  if (json.clearance !== undefined) document.getElementById('clearance').value = json.clearance;
  if (json.arm_height !== undefined) document.getElementById('arm-height-viz').value = json.arm_height;
  if (json.terrain) document.getElementById('terrain-select').value = json.terrain;
  if (json.strategy) document.getElementById('strategy-select').value = json.strategy;

  // Update all value display spans
  const formatters = {
    'arm-length': v => v.toFixed(2) + ' m',
    'splay-angle': v => v.toFixed(0) + '\u00B0',
    'brace-pos': v => v.toFixed(2),
    'wheel-radius': v => v.toFixed(2) + ' m',
    'clearance': v => v.toFixed(3) + ' m',
    'arm-height-viz': v => v.toFixed(3) + ' m',
  };
  const valEls = {
    'arm-length': 'val-arm-length',
    'splay-angle': 'val-splay',
    'brace-pos': 'val-brace-pos',
    'wheel-radius': 'val-wheel-r',
    'clearance': 'val-clearance',
    'arm-height-viz': 'val-arm-height',
  };
  for (const [id, valId] of Object.entries(valEls)) {
    const el = document.getElementById(id);
    document.getElementById(valId).textContent = formatters[id](parseFloat(el.value));
  }

  onChange(readConfig());
}
```

- [ ] **Step 3: Wire save/load events in simulation.js**

In `web/simulation.js`, update the import line and add event listeners:

```javascript
// Update import to include saveConfig and applyConfig:
import { setupControls, readConfig, updateInfoBar, saveConfig, applyConfig } from '/static/controls.js';
```

Add after the existing `btn-sim` event listener:

```javascript
document.getElementById('btn-save').addEventListener('click', () => {
  saveConfig();
});

document.getElementById('btn-load').addEventListener('click', () => {
  document.getElementById('file-input').click();
});

document.getElementById('file-input').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (evt) => {
    try {
      const json = JSON.parse(evt.target.result);
      applyConfig(json, (config) => {
        sendConfig(config);
        send({ type: 'set_terrain', name: document.getElementById('terrain-select').value });
        sendTerrainRequest();
        send({ type: 'set_strategy', name: document.getElementById('strategy-select').value });
        send({ type: 'solve_ik' });
      });
    } catch (err) {
      console.error('Invalid config file:', err);
    }
  };
  reader.readAsText(file);
  e.target.value = '';  // reset so same file can be loaded again
});
```

- [ ] **Step 4: Test manually**

Start server: `uvicorn wheely.server:app --reload`

1. Adjust some sliders, change terrain to "bumpy", strategy to "spring_damper"
2. Click Save — verify `wheely-config.json` downloads with correct values
3. Change sliders back to defaults
4. Click Load — select the downloaded file
5. Verify all sliders, terrain dropdown, and strategy dropdown restore to saved values
6. Verify the 3D view updates (solve_ik fires)

- [ ] **Step 5: Commit**

```bash
git add web/controls.js web/index.html web/simulation.js
git commit -m "feat: add config save/load via JSON download/upload"
```

---

### Task 2: Figure-8 Motion (Backend)

**Files:**
- Modify: `wheely/dynamics.py`
- Modify: `wheely/server.py`
- Modify: `tests/test_dynamics.py`

This task is **independent** of Task 1. Task 3 depends on this task.

- [ ] **Step 1: Write failing tests for figure8_motion**

Add to `tests/test_dynamics.py`:

```python
from wheely.dynamics import figure8_motion

class TestFigure8Motion:
    def test_advances_position(self):
        """After one step, body_xy should have moved from origin."""
        state = SimState.from_config(PlatformConfig())
        new_state = figure8_motion(state, dt=0.1, speed=0.3, radius=2.0)
        assert new_state.body_xy != (0.0, 0.0)
        assert new_state.path_theta > 0.0

    def test_stays_on_path(self):
        """Position should match the lemniscate equation."""
        state = SimState.from_config(PlatformConfig())
        state = figure8_motion(state, dt=1.0, speed=0.3, radius=2.0)
        theta = state.path_theta
        R = 2.0
        expected_x = R * math.sin(2 * theta) / 2
        expected_y = R * math.sin(theta)
        assert state.body_xy[0] == pytest.approx(expected_x, abs=1e-6)
        assert state.body_xy[1] == pytest.approx(expected_y, abs=1e-6)

    def test_completes_loop(self):
        """After many steps, path_theta should exceed 2*pi (one full loop)."""
        state = SimState.from_config(PlatformConfig())
        for _ in range(5000):
            state = figure8_motion(state, dt=0.01, speed=0.5, radius=2.0)
        assert state.path_theta > 2 * math.pi

    def test_yaw_follows_tangent(self):
        """body_yaw should point along path tangent direction."""
        state = SimState.from_config(PlatformConfig())
        state = figure8_motion(state, dt=0.5, speed=0.3, radius=2.0)
        theta = state.path_theta
        R = 2.0
        dx = R * math.cos(2 * theta)
        dy = R * math.cos(theta)
        expected_yaw = math.atan2(dy, dx)
        assert state.body_yaw == pytest.approx(expected_yaw, abs=1e-6)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_dynamics.py::TestFigure8Motion -v
```

Expected: ImportError — `figure8_motion` doesn't exist yet, and `path_theta` not on SimState.

- [ ] **Step 3: Add path_theta to SimState and implement figure8_motion**

In `wheely/dynamics.py`, add `path_theta` field to `SimState`:

```python
@dataclass
class SimState:
    """Mutable simulation state."""

    body_xy: tuple[float, float] = (0.0, 0.0)
    body_yaw: float = 0.0
    tilt_pitch: float = 0.0
    tilt_roll: float = 0.0
    tilt_pitch_velocity: float = 0.0
    tilt_roll_velocity: float = 0.0
    arm_reaches: tuple[float, float] = (0.0, 0.0)
    arm_reach_velocities: tuple[float, float] = (0.0, 0.0)
    steerings: tuple[float, float, float] = (0.0, 0.0, 0.0)
    time: float = 0.0
    cumulative_energy: float = 0.0
    path_theta: float = 0.0
```

Add the `figure8_motion` function (place it after the strategy classes, before the terrain contact helpers):

```python
def figure8_motion(
    state: SimState,
    dt: float,
    speed: float = 0.3,
    radius: float = 2.0,
) -> SimState:
    """Advance vehicle along a lemniscate (figure-8) path.

    Path: x = R * sin(2*theta) / 2, y = R * sin(theta)
    Speed is constant arc-length velocity.

    Returns a new SimState with updated body_xy, body_yaw, path_theta.
    All other fields are copied from the input state.
    """
    theta = state.path_theta

    # Tangent vector: dx/dtheta, dy/dtheta
    dx_dtheta = radius * math.cos(2 * theta)
    dy_dtheta = radius * math.cos(theta)
    ds_dtheta = math.sqrt(dx_dtheta**2 + dy_dtheta**2)

    # Avoid division by zero at crossing point
    if ds_dtheta < 1e-8:
        ds_dtheta = 1e-8

    # Advance theta for constant arc-length speed
    d_theta = speed * dt / ds_dtheta
    new_theta = theta + d_theta

    # Compute new position on the lemniscate
    new_x = radius * math.sin(2 * new_theta) / 2
    new_y = radius * math.sin(new_theta)

    # Yaw follows tangent at new position
    dx_new = radius * math.cos(2 * new_theta)
    dy_new = radius * math.cos(new_theta)
    new_yaw = math.atan2(dy_new, dx_new)

    return SimState(
        body_xy=(new_x, new_y),
        body_yaw=new_yaw,
        path_theta=new_theta,
        tilt_pitch=state.tilt_pitch,
        tilt_roll=state.tilt_roll,
        tilt_pitch_velocity=state.tilt_pitch_velocity,
        tilt_roll_velocity=state.tilt_roll_velocity,
        arm_reaches=state.arm_reaches,
        arm_reach_velocities=state.arm_reach_velocities,
        steerings=state.steerings,
        time=state.time,
        cumulative_energy=state.cumulative_energy,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_dynamics.py::TestFigure8Motion -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Add motion parameter to simulate_step**

In `wheely/dynamics.py`, update `simulate_step` signature to accept `motion`:

```python
def simulate_step(
    state: SimState,
    config: PlatformConfig,
    terrain,
    strategy,
    dt: float = 0.01,
    arm_inertia: float = 1.0,
    tilt_inertia: float = 2.0,
    motion: str = "stationary",
) -> tuple[SimState, StepMetrics]:
```

Add motion handling at the very beginning of the function body, before the strategy torque computation:

```python
    # --- Apply prescribed motion if active ---
    if motion == "figure8":
        state = figure8_motion(state, dt)
```

And update the new_state construction near the end to use the (possibly updated) state values for body position:

Change:
```python
    new_state = SimState(
        body_xy=state.body_xy,
        body_yaw=state.body_yaw,
```
This line already references `state.body_xy` and `state.body_yaw`, which are correct since `figure8_motion` returns an updated state object.

Also add `path_theta` to the new_state construction:
```python
    new_state = SimState(
        body_xy=state.body_xy,
        body_yaw=state.body_yaw,
        tilt_pitch=new_tilt_pitch,
        tilt_roll=new_tilt_roll,
        tilt_pitch_velocity=new_pitch_vel,
        tilt_roll_velocity=new_roll_vel,
        arm_reaches=(new_reach_b, new_reach_c),
        arm_reach_velocities=(new_vel_b, new_vel_c),
        steerings=state.steerings,
        time=state.time + dt,
        cumulative_energy=new_cumulative_energy,
        path_theta=state.path_theta,
    )
```

- [ ] **Step 6: Run all existing tests to ensure nothing broke**

```bash
python3 -m pytest tests/ -v
```

Expected: All tests PASS (existing tests use default `motion="stationary"` and `path_theta=0.0`).

- [ ] **Step 7: Update server.py — add motion_mode state and set_motion handler**

In `wheely/server.py`, add `motion_mode` variable in the websocket handler (after `running = False`):

```python
    motion_mode = "stationary"
```

Add a handler for `set_motion` messages (after the `set_strategy` handler):

```python
            elif msg_type == "set_motion":
                name = msg.get("name", "stationary")
                if name in ("stationary", "figure8"):
                    motion_mode = name
```

Pass `motion` to `simulate_step` in the simulation loop:

```python
                    sim_state, metrics = simulate_step(
                        sim_state, config, terrain, strategy, dt=0.016,
                        motion=motion_mode,
                    )
```

- [ ] **Step 8: Update _build_frame to include body position**

In `wheely/server.py`, update `_build_frame` signature:

```python
def _build_frame(config, terrain, tilt_pitch, tilt_roll, arm_reaches, steerings,
                 body_xy=(0.0, 0.0), body_yaw=0.0, metrics=None):
```

Add body position fields to the frame dict (after `"arm_reaches"`):

```python
    bx, by = body_xy
    frame["body_xy"] = list(body_xy)
    frame["body_yaw"] = body_yaw
    frame["body_z"] = terrain.height(bx, by)
```

Update the two call sites in the simulation loop (`start_sim` block) and the `solve_ik` block to pass `body_xy` and `body_yaw`:

```python
                frame = _build_frame(
                    config, terrain,
                    sim_state.tilt_pitch, sim_state.tilt_roll,
                    sim_state.arm_reaches, sim_state.steerings,
                    body_xy=sim_state.body_xy,
                    body_yaw=sim_state.body_yaw,
                    metrics=metrics,
                )
```

Do the same for the `solve_ik`, `get_frame` call sites.

- [ ] **Step 9: Also handle set_motion during simulation loop**

In the inner message-reading `try` block inside the `start_sim` while loop, handle `set_motion` alongside `stop_sim`:

```python
                    try:
                        raw = await asyncio.wait_for(ws.receive_text(), timeout=0.001)
                        inner = json.loads(raw)
                        if inner.get("type") == "stop_sim":
                            running = False
                        elif inner.get("type") == "set_motion":
                            name = inner.get("name", "stationary")
                            if name in ("stationary", "figure8"):
                                motion_mode = name
                    except asyncio.TimeoutError:
                        pass
```

- [ ] **Step 10: Run all tests**

```bash
python3 -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 11: Commit**

```bash
git add wheely/dynamics.py wheely/server.py tests/test_dynamics.py
git commit -m "feat: add figure-8 prescribed motion mode with path_theta tracking"
```

---

### Task 3: Figure-8 Motion (Frontend)

**Files:**
- Modify: `web/index.html`
- Modify: `web/simulation.js`
- Modify: `web/platform-viz.js`

This task **depends on Task 2** (server must handle `set_motion` and include `body_xy`/`body_yaw`/`body_z` in frames).

- [ ] **Step 1: Add Motion dropdown to index.html**

In `web/index.html`, add a "Motion" section in `#panel-controls` after the Actuation section (before the Simulation h2):

```html
<h2>Motion</h2>
<div class="control">
  <select id="motion-select">
    <option value="stationary">Stationary</option>
    <option value="figure8">Figure-8</option>
  </select>
</div>
```

- [ ] **Step 2: Wire motion dropdown in simulation.js**

Add after the `strategy-select` event listener:

```javascript
document.getElementById('motion-select').addEventListener('change', (e) => {
  send({ type: 'set_motion', name: e.target.value });
});
```

- [ ] **Step 3: Apply body transform in platform-viz.js**

In `web/platform-viz.js`, update `updatePlatform` to apply the body position as a group transform. Add this at the end of the function, before the support triangle section:

```javascript
  // --- Apply body world position/yaw ---
  if (frame.body_xy) {
    viz.group.position.x = frame.body_xy[0];
    viz.group.position.y = frame.body_z || 0;
    viz.group.position.z = -(frame.body_xy[1] || 0);
    viz.group.rotation.y = -(frame.body_yaw || 0);
  }
```

Note: The support triangle positions are set in body-frame coordinates and the triMesh is a child of the group, so it transforms automatically.

- [ ] **Step 4: Test manually**

Start server: `uvicorn wheely.server:app --reload`

1. Select "bumpy" terrain
2. Select "Active Arms (IMU)" strategy
3. Select "Figure-8" motion
4. Click "Run Sim"
5. Verify the vehicle moves in a figure-8 pattern across the terrain
6. Verify pitch/roll angles oscillate and converge (visible in info bar and metrics chart)
7. Switch motion to "Stationary" during simulation — vehicle should stop moving
8. Switch back to "Figure-8" — vehicle resumes from current path position

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/simulation.js web/platform-viz.js
git commit -m "feat: add motion dropdown and figure-8 visualization with body transform"
```

---

### Task 4: Final Integration Test

- [ ] **Step 1: Run full test suite**

```bash
python3 -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 2: End-to-end manual test**

1. Hard refresh browser (Cmd+Shift+R)
2. Set terrain to "bumpy", strategy to "Active Arms (IMU)", motion to "Figure-8"
3. Click "Run Sim" — watch vehicle traverse figure-8, PD control stabilizing tilt
4. Stop sim, adjust sliders, click Save — verify JSON downloads
5. Reset sliders, click Load — verify config restores
6. Run sim again with loaded config — verify behavior matches

- [ ] **Step 3: Final commit (if any adjustments needed)**

```bash
git push
```
