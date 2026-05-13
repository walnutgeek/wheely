# Dynamics Rework: Parallelogram Constraints & Active Leveling

## Overview

Rework the wheely dynamics simulation to accurately model the parallelogram linkage mechanics and add active leveling control. The current sim treats each arm pivot as independent and uses only a soft penalty spring for terrain contact. The revised model enforces parallelogram coupling (all shafts parallel, single tilt DOF), adds a hard surface constraint (wheels never penetrate terrain), models body tipping under gravity, and introduces two competing active leveling strategies for comparison.

## Problem Statement

Three issues with the current dynamics:

1. **Wheels penetrate terrain**: The penalty spring (`contact_stiffness=2000`) is soft enough that wheels oscillate through the surface. No hard constraint prevents negative penetration.
2. **No body tipping**: The body (Wheel A) is pinned to the terrain. When wheels lose contact, the platform should tip under gravity.
3. **No active leveling**: The parallelogram linkages keep all three wheel shafts parallel, but nothing passively keeps them vertical. An actuator + IMU control loop is needed to drive shafts back to vertical.

## Revised Mechanical Model

### Degrees of Freedom

The three parallelogram linkages (two in the arms, one in the brace) create a kinematic constraint: all three wheel shafts remain parallel. This reduces the system to:

- **Shaft tilt** (`shaft_tilt`: float, radians): The angle of all three shafts from vertical. Shared across the entire platform. When `shaft_tilt=0`, shafts are vertical. Positive tilt means shafts lean in the +X direction (forward).
- **Arm reaches** (`reach_b`, `reach_c`: floats, radians): How far each arm extends downward. These are independent -- on bumpy terrain one arm reaches further than the other. The parallelogram ensures the shaft orientation at the wheel end stays at `shaft_tilt` regardless of reach angle.

### Relation to Current State

Current `SimState`:
```python
arm_pivots: tuple[float, float]      # independent pivot angles
arm_velocities: tuple[float, float]  # independent velocities
```

Revised `SimState`:
```python
shaft_tilt: float                     # shared tilt (theta), 0 = vertical
shaft_tilt_velocity: float            # angular velocity of tilt
arm_reaches: tuple[float, float]      # (reach_b, reach_c), independent
arm_reach_velocities: tuple[float, float]
```

### Geometry Mapping

The wheel position for arm B in world frame becomes a function of both `shaft_tilt` and `reach_b`:
- `shaft_tilt` affects the orientation of the entire arm assembly (rotates the arm base)
- `reach_b` affects how far down the arm extends (determines wheel height relative to body)

The `compute_wheel_positions` function in `geometry.py` needs to accept `(shaft_tilt, reach_b, reach_c)` instead of `(pivot_b, pivot_c)`. The old `pivot_b` was conflating tilt and reach into one angle.

### Geometry Math

For arm B (splay_sign = -1), wheel position in body frame:

```
# The arm direction in XY plane (from apex toward wheel B)
arm_dir_x = cos(splay)
arm_dir_y = splay_sign * sin(splay)   # -sin(splay) for B, +sin(splay) for C

# reach_b determines how far the arm extends (angle from horizontal)
# shaft_tilt rotates the entire arm assembly around the arm direction axis
dx = arm_length * arm_dir_x * cos(reach_b)
dy = arm_length * arm_dir_y * cos(reach_b)
dz = -arm_length * sin(reach_b)

# Then apply shaft_tilt rotation around the arm's horizontal axis
# This tilts the shaft (and the arm endpoint) by shaft_tilt
# The tilt axis is perpendicular to the arm direction in the XY plane
wheel_x = body_x + cos(yaw) * dx - sin(yaw) * dy + tilt_offset_x(shaft_tilt)
wheel_y = body_y + sin(yaw) * dx + cos(yaw) * dy + tilt_offset_y(shaft_tilt)
wheel_z = body_z + dz + tilt_offset_z(shaft_tilt)
```

The exact `tilt_offset` terms depend on how shaft_tilt is defined relative to the arm pivot axis. The implementation will work this out in `geometry.py` with tests to verify the expected behavior (shaft_tilt=0 → vertical shafts, shaft_tilt=angle → all shafts tilted by that angle).

## Hard Surface Constraint

### During Integration

The penalty spring contact model stays (it provides physically-meaningful reaction forces and smooth dynamics), but parameters increase for stiffer response:
- `contact_stiffness`: 2000 → 5000
- `contact_damping`: 50 → 100

### Post-Integration Clamp

After semi-implicit Euler integration, enforce:

```
for each arm (b, c):
    compute wheel_z from (shaft_tilt, reach)
    terrain_z = terrain.height(wheel_x, wheel_y)
    if wheel_z < terrain_z:
        adjust reach so wheel_z == terrain_z  (solve analytically)
        set reach_velocity = 0  (inelastic contact)
```

This guarantees no visual penetration regardless of timestep or stiffness.

## Tipping Under Gravity

When the platform is on a slope or when wheels lose terrain contact:

- Gravity creates a torque on the `shaft_tilt` DOF proportional to the platform's center of mass offset from the support base.
- `gravity_torque = -M * g * L_cog * sin(shaft_tilt)` where `M` is total mass, `L_cog` is the distance from the tilt axis to the center of gravity.
- When wheels are in contact with terrain, the terrain reaction force counteracts this torque.
- When wheels are NOT in contact (e.g., one arm is reaching into a dip), the unbalanced torque causes the platform to tip.

## Active Leveling Strategies

Both strategies use a PD controller reading `shaft_tilt` from an IMU:

```python
torque = -kp * shaft_tilt - kd * shaft_tilt_velocity
```

### Strategy 1: Active Arms Leveling (`ActiveArmsLeveling`)

- Actuators on both arm parallelograms.
- The controller torque applies directly to the `shaft_tilt` DOF.
- Both arms simultaneously adjust their geometry to drive `shaft_tilt → 0`.
- Arm reaches adjust as a consequence to maintain terrain contact.
- **Parameters**: `kp` (proportional gain), `kd` (derivative gain).

### Strategy 2: Active Brace Leveling (`ActiveBraceLeveling`)

- Single actuator on the brace parallelogram.
- Arms are passive (gravity + terrain contact determines reach).
- The brace actuator applies torque to `shaft_tilt` through the coupling between the brace and arm geometry.
- Potentially different effective gain and response dynamics due to the indirect actuation path.
- The brace actuator changes the coupling geometry, which indirectly affects how the arm reaches translate to shaft tilt.
- **Parameters**: `kp` (proportional gain), `kd` (derivative gain), `brace_gain` (mechanical advantage factor for the indirect actuation path).

### Existing Strategies (Retained)

- `PassiveStrategy`: No actuation. Arms settle via gravity + terrain contact. Shaft tilt drifts freely.
- `SpringDamperStrategy`: Spring return on reaches around neutral. No shaft tilt control.

## Metrics & Comparison

### Per-Timestep Metrics

The `simulate_step` function returns both the new state and a metrics dict:

```python
@dataclass
class StepMetrics:
    shaft_tilt_deg: float       # current tilt in degrees
    actuator_torque: float      # torque applied this step (N*m)
    actuator_power: float       # |torque * velocity| this step (W)
    cumulative_energy: float    # running total of energy used (J)
    reach_b_deg: float          # arm B reach in degrees
    reach_c_deg: float          # arm C reach in degrees
    in_contact_b: bool          # whether wheel B is on terrain
    in_contact_c: bool          # whether wheel C is on terrain
```

### Comparison Criteria

- **Convergence speed**: Time to reach `|shaft_tilt| < 1 degree` from a disturbed initial state.
- **Energy efficiency**: Total actuator energy to reach steady state.
- **Steady-state accuracy**: Residual shaft tilt in steady state.
- **Robustness**: Behavior when traversing bumpy terrain (does tilt stay controlled?).

## Frontend Changes

### WebSocket Frame Update

The frame message adds a `metrics` dict:
```json
{
    "type": "frame",
    "wheels": {...},
    "brace_center": [...],
    "support_triangle": [...],
    "stability_margin": 0.12,
    "shaft_tilt": 0.05,
    "metrics": {
        "shaft_tilt_deg": 2.87,
        "actuator_torque": -1.23,
        "actuator_power": 0.45,
        "cumulative_energy": 12.3,
        "reach_b_deg": 15.2,
        "reach_c_deg": -8.1,
        "in_contact_b": true,
        "in_contact_c": true
    }
}
```

### Info Bar Updates

Replace current info cards:
- "Pivot B" → "Shaft Tilt" (degrees from vertical)
- "Pivot C" → "Energy" (cumulative actuator energy, J)
- Keep "Stability Margin" and "Sim Time"

### Metrics Chart

A new panel (below viewport, beside info bar, or as a collapsible overlay) showing a live time-series line chart:
- **Line 1**: Shaft tilt (degrees) over time -- primary axis
- **Line 2**: Actuator torque (N*m) over time -- secondary axis
- Canvas-based rendering, no external charting library
- Rolling window of ~10 seconds of data
- Clears on strategy change or sim restart

### Strategy Dropdown

Add to the existing strategy select:
- `active_arms_leveling` ("Active Arms (IMU)")
- `active_brace_leveling` ("Active Brace (IMU)")

## Backend Changes

### `wheely/dynamics.py`

- Revise `SimState` to use `shaft_tilt`, `shaft_tilt_velocity`, `arm_reaches`, `arm_reach_velocities`.
- Add `StepMetrics` dataclass.
- Add `ActiveArmsLeveling` strategy class.
- Add `ActiveBraceLeveling` strategy class.
- Revise `simulate_step` to:
  1. Compute strategy torque on `shaft_tilt`
  2. Compute gravity torque on `shaft_tilt`
  3. Compute terrain contact per arm (affects `arm_reaches`)
  4. Integrate `shaft_tilt` and `arm_reaches` (semi-implicit Euler)
  5. Hard clamp: enforce no-penetration on each arm
  6. Return `(new_state, metrics)`
- Revise `_compute_terrain_contact_torque` to work with the new reach-based model.

### `wheely/geometry.py`

- Update `compute_wheel_positions` to accept `(shaft_tilt, reach_b, reach_c)` instead of `(pivot_b, pivot_c)`.
- The mapping: the old `pivot` was a single angle. Now it decomposes into `shaft_tilt` (shared) affecting arm base orientation, and `reach` (per-arm) affecting extension.
- Update `compute_brace_endpoints` and `compute_brace_center` accordingly.

### `wheely/kinematics.py`

- Update `inverse_kinematics` to solve for `(shaft_tilt, reach_b, reach_c)` instead of `(pivot_b, pivot_c)`.
- Update `forward_kinematics` to accept the new state format.

### `wheely/server.py`

- Add new strategy presets for `active_arms_leveling` and `active_brace_leveling`.
- Update `_build_frame` to include metrics in the response.
- Update `simulate_step` call to handle the new return signature `(state, metrics)`.

### Backward Compatibility

The old `arm_pivots` concept is replaced entirely. The WebSocket API changes:
- Frame responses use `shaft_tilt`, `reach_b`, `reach_c` instead of `arm_pivots`.
- The `set_config` message stays the same (geometry parameters unchanged).
- The `set_strategy` message gains two new valid names.

## Testing

### Hard Surface Constraint
- Property test: For any terrain and initial state, after `simulate_step`, wheel Z >= terrain Z at wheel XY.
- Specific test: Start with wheel above bumpy terrain, run 100 steps, verify no penetration ever occurs.

### Parallelogram Coupling
- Test that FK with `(shaft_tilt, reach_b, reach_c)` produces shaft orientations that are parallel for both wheels.
- Test that changing `shaft_tilt` rotates all shafts by the same amount.

### Active Leveling Convergence
- Start on a 20-degree slope with `shaft_tilt = 0` (shafts initially vertical but terrain is tilted, so tilt will develop).
- Run `ActiveArmsLeveling` for 500 steps. Assert `|shaft_tilt| < 1 degree`.
- Run `ActiveBraceLeveling` for 500 steps. Assert `|shaft_tilt| < 1 degree`.
- Compare energy used.

### Passive Settling
- Existing tests for `PassiveStrategy` continue to work with the new state format.
- Arms should settle via gravity + terrain contact (reaches adapt, tilt may drift).

### Metrics
- Test that `cumulative_energy` increases monotonically.
- Test that `actuator_torque` sign matches the correction direction.

## Scope Boundaries

### In Scope
- Revised DOF model (shaft_tilt + arm_reaches)
- Hard surface constraint (no penetration)
- Gravity tipping on shaft_tilt
- Two active leveling strategies (arms vs brace)
- Per-step metrics (tilt, torque, energy)
- Live metrics chart in frontend
- Updated info bar
- Updated strategy dropdown
- Tests for all new physics

### Out of Scope
- Body XY motion (driving/steering simulation)
- Multiple tilt axes (only single-axis tilt for now)
- Flex or compliance in the parallelogram linkages
- Terrain friction model
- 3D IMU (roll + pitch) -- single axis tilt only for now
