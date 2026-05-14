# Parallelogram Arm & Brace Visualization Overhaul

## Context

The user can now see wheels tracking terrain correctly (Y-flip bug fixed). The current 3D visualization uses simple lines for arms and brace, cylinder wheels, and has no shaft structure. The goal is to show the actual mechanical structure: parallelogram arm linkages, cross brace with height, vertical shafts with clearance above wheels, and sphere wheels.

## Files to Modify

1. **`wheely/geometry.py`** — Add `clearance` and `arm_height` to `PlatformConfig`
2. **`web/index.html`** — Add two new sliders after Wheel Radius
3. **`web/controls.js`** — Wire new sliders into `readConfig()` and `setupControls()`
4. **`web/platform-viz.js`** — Rewrite visualization with parallelogram structure

No server.py changes needed — it already accepts any PlatformConfig field via `hasattr()` filtering.

## Step 1: PlatformConfig (geometry.py)

Add two fields to the dataclass:

```python
clearance: float = 0.03      # gap above wheel top to lower arm attachment (m)
arm_height: float = 0.06     # vertical height of arm/brace parallelogram (m)
```

Add validation in `validate()`:
- clearance: [0.01, 0.2]
- arm_height: [0.02, 0.3]

Add both to `to_dict()`.

## Step 2: UI Sliders (index.html)

After the Wheel Radius slider (line 71), add:

```html
<div class="control">
  <label>Clearance <span id="val-clearance">0.03 m</span></label>
  <input type="range" id="clearance" min="0.01" max="0.2" step="0.005" value="0.03">
</div>
<div class="control">
  <label>Arm Height <span id="val-arm-height">0.06 m</span></label>
  <input type="range" id="arm-height-viz" min="0.02" max="0.3" step="0.005" value="0.06">
</div>
```

## Step 3: Controls (controls.js)

- Add `clearance` and `arm-height-viz` to sliders array, valEls, and formatters
- Add to `readConfig()`: `clearance: parseFloat(...)`, `arm_height: parseFloat(...)`

## Step 4: Visualization Rewrite (platform-viz.js)

### 3D Structure Per Wheel

For each wheel (A, B, C) at contact point `w`:
- **Wheel**: SphereGeometry(wheel_radius) centered at `w + (0, r, 0)` in Three.js
- **Shaft**: thin cylinder from wheel top `w + (0, 2r, 0)` up to upper attachment `w + (0, 2r + clearance + arm_height, 0)`

Key attachment points (Three.js Y-up coords):
- `shaft_lower[name]` = w + (0, 2r + clearance, 0) — lower arm bar attachment
- `shaft_upper[name]` = w + (0, 2r + clearance + arm_height, 0) — upper arm bar attachment

### Vertical Tubes (3 total)

Three vertical tubes run through the structure — one at each wheel. Each shaft serves double duty as both the vertical post above the wheel and the vertical side of the parallelogram:
- **Body tube** (at wheel A): shaft_lower[A] → shaft_upper[A]
- **Shaft B tube** (at wheel B): shaft_lower[B] → shaft_upper[B]
- **Shaft C tube** (at wheel C): shaft_lower[C] → shaft_upper[C]

These are the same shaft meshes listed above — no separate objects needed.

### Parallelogram Arms (B and C)

Each arm has 2 horizontal bars connecting body tube to shaft tube:
- **Lower bar**: shaft_lower[A] → shaft_lower[B or C]
- **Upper bar**: shaft_upper[A] → shaft_upper[B or C]

Together with the body tube and shaft tube, these 2 bars complete the 4-sided parallelogram.

### Cross Brace

Brace attachment at fraction `t = brace_position` along each arm:
- `brace_B_lower` = lerp(shaft_lower[A], shaft_lower[B], t)
- `brace_B_upper` = lerp(shaft_upper[A], shaft_upper[B], t)
- Same for C side

4 brace bars:
- **Lower bar**: brace_B_lower → brace_C_lower
- **Upper bar**: brace_B_upper → brace_C_upper
- **Vertical B**: brace_B_lower → brace_B_upper
- **Vertical C**: brace_C_lower → brace_C_upper

### Bar Positioning Helper

```javascript
function positionBar(mesh, from, to) {
  const dir = new THREE.Vector3().subVectors(to, from);
  const len = dir.length();
  mesh.scale.set(1, len, 1);
  mesh.position.copy(from).add(to).multiplyScalar(0.5);
  const quat = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0), dir.normalize()
  );
  mesh.quaternion.copy(quat);
}
```

Uses pre-created unit-height CylinderGeometry(BAR_RADIUS, BAR_RADIUS, 1, 8) meshes that get repositioned each frame — no geometry allocation per frame.

### Mesh Inventory

| Object | Count | Geometry | Purpose |
|--------|-------|----------|---------|
| Wheels | 3 | SphereGeometry | A, B, C |
| Shafts/verticals | 3 | CylinderGeometry (unit, thin) | Vertical tubes at each wheel (body + 2 shafts) |
| Arm bars | 4 | CylinderGeometry (unit, thin) | Upper + lower bar for each arm (B, C) |
| Brace bars | 4 | CylinderGeometry (unit, thin) | Lower, upper, vert-B, vert-C |
| Joints | ~10 | SphereGeometry (small) | Connection point indicators |
| Cargo | 1 | BoxGeometry | At upper brace center |
| Support triangle | 1 | BufferGeometry | Ground overlay |

Total: ~26 meshes (up from ~8), well within Three.js performance limits.

### Materials

```
WHEEL_MAT: dark gray, rough
SHAFT_MAT: medium gray, metallic
ARM_BAR_MAT: blue (#4488aa), slight metalness
BRACE_BAR_MAT: green (#44aa66), slight metalness
JOINT_MAT: red (#e94560)
```

### Wheel Geometry Update

Only recreate SphereGeometry when wheel_radius actually changes (track `viz._lastRadius`).

## Verification

1. Run `python3 -m pytest tests/ -v` — all tests pass (new config field validation tests)
2. Start server: `uvicorn wheely.server:app --reload`
3. Hard refresh browser (Cmd+Shift+R)
4. Check flat terrain: all 3 wheels spheres sitting on ground, parallelogram arms visible, brace connecting arms
5. Adjust clearance slider: gap between wheel top and arm attachment changes
6. Adjust arm_height slider: parallelogram arm bars get taller/shorter, brace matches
7. Test on cross_slope terrain: arms at different reaches, parallelogram shapes show angles clearly
8. Test on bumpy terrain: verify all structures track correctly
9. Run simulation: verify structures update in real-time
