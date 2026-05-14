# Config Save/Load & Figure-8 Motion

## Overview

Two features:
1. **Config save/load** — download/upload all UI settings as a JSON file
2. **Figure-8 motion** — vehicle follows a prescribed lemniscate path during simulation, demonstrating PD control response to terrain

## Feature 1: Config Save/Load

### Behavior

- **Save**: "Save" button in controls panel triggers browser download of a JSON file named `wheely-config.json`
- **Load**: "Load" button opens a file picker (`<input type="file" accept=".json">`). On file selection, parse JSON, update all sliders/dropdowns, fire config change + solve_ik

### JSON Format

```json
{
  "arm_length": 0.8,
  "arm_splay_angle_deg": 40,
  "brace_position": 0.5,
  "wheel_radius": 0.15,
  "clearance": 0.03,
  "arm_height": 0.06,
  "terrain": "bumpy",
  "strategy": "spring_damper"
}
```

Splay angle is stored in degrees for human readability. All other numeric values match slider values directly.

### UI Placement

Add a "Presets" section at the top of the controls panel (middle column) with Save and Load buttons in a `btn-row`.

### Files Modified

- `web/index.html` — add hidden file input, Save/Load buttons
- `web/controls.js` — add `saveConfig()`, `loadConfig()` exports; add `applyConfig(json)` that sets slider values, dropdown selections, and triggers onChange
- `web/simulation.js` — wire Save/Load button events

### No Server Changes

Pure frontend feature.

## Feature 2: Figure-8 Prescribed Motion

### Concept

During simulation, the vehicle follows a lemniscate (figure-8) path at constant speed. The terrain is sampled at the actual wheel world positions, naturally exciting tilt and reach dynamics. The PD controller (active arms, spring-damper, etc.) responds to these perturbations, and the user sees pitch/roll angles oscillate then converge — demonstrating closed-loop control.

### Path Definition

Lemniscate of Bernoulli parameterized by angle `theta`:

```
x(theta) = R * sin(2 * theta) / 2     (= R * sin(theta) * cos(theta))
y(theta) = R * sin(theta)
```

Where `R = 2.0 m`. The path crosses itself at the origin.

`theta` advances at a rate derived from constant arc-length speed `v = 0.3 m/s`:

```
d_theta = v * dt / ds_dtheta
```

where `ds_dtheta` is the local arc-length derivative (computed from dx/dtheta, dy/dtheta).

`body_yaw` is set to the path tangent direction: `atan2(dy/dtheta, dx/dtheta)`.

### Motion Modes

Two modes, controlled by a new dropdown or the existing simulation controls:

- **Stationary** (default): current behavior, vehicle stays at origin
- **Figure-8**: vehicle follows the lemniscate path

### Server Changes

**`wheely/dynamics.py`**:
- Add a `figure8_motion(state, dt, speed=0.3, radius=2.0)` function that:
  - Computes current theta from `state.body_xy` (or track theta in state)
  - Advances theta by `v * dt / |path_tangent|`
  - Updates `body_xy` and `body_yaw`
  - Returns updated state
- Call this function at the start of `simulate_step` when motion mode is active
- Add `path_theta: float = 0.0` field to `SimState` to track path parameter

**`wheely/server.py`**:
- Add `motion_mode: str = "stationary"` to connection state
- Handle `set_motion` WebSocket message: `{"type": "set_motion", "name": "stationary" | "figure8"}`
- Pass motion mode to `simulate_step`

### Frontend Changes

**`web/index.html`**:
- Add a "Motion" dropdown in the controls panel with options: Stationary, Figure-8

**`web/simulation.js`**:
- Wire motion dropdown to send `set_motion` message

### Camera Behavior

The camera stays fixed (OrbitControls). The vehicle moves across the visible terrain grid. The terrain grid is 6m x 6m, and the figure-8 fits within ~4m x 4m, so it stays well within view.

### Expected Behavior

1. User selects "bumpy" or "cross_slope" terrain
2. User selects "Active Arms (IMU)" or "Spring-Damper" strategy
3. User selects "Figure-8" motion
4. User clicks "Run Sim"
5. Vehicle moves along the path. As it encounters terrain features:
   - Pitch/roll angles get perturbed away from zero
   - The PD controller applies torques to bring them back
   - The info bar shows oscillating then converging angles
   - The metrics chart shows the control response over time

## Testing

- Config save/load: manual testing (download, edit JSON, re-upload, verify sliders update)
- Figure-8 motion: add a unit test for `figure8_motion()` verifying path position after N steps; verify existing dynamics tests still pass (they use stationary mode by default)
