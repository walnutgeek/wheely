# Dynamics Rework: Parallelogram Constraints & Active Leveling

## Overview

Rework the wheely dynamics simulation to accurately model the parallelogram linkage mechanics and add active leveling control. The current sim treats each arm pivot as independent and uses only a soft penalty spring for terrain contact. The revised model enforces parallelogram coupling (all shafts parallel, two-axis tilt), adds a hard surface constraint (wheels never penetrate terrain), models body tipping under gravity, and introduces two competing active leveling strategies for comparison.

## Problem Statement

Three issues with the current dynamics:

1. **Wheels penetrate terrain**: The penalty spring (`contact_stiffness=2000`) is soft enough that wheels oscillate through the surface. No hard constraint prevents negative penetration.
2. **No body tipping**: The body (Wheel A) is pinned to the terrain. When wheels lose contact, the platform should tip under gravity.
3. **No active leveling**: The parallelogram linkages keep all three wheel shafts parallel, but nothing passively keeps them vertical. An actuator + IMU control loop is needed to drive shafts back to vertical.

## Revised Mechanical Model

### Degrees of Freedom

The three parallelogram linkages (two in the arms, one in the brace) create a kinematic constraint: all three wheel shafts remain parallel. This reduces the system to:

- **Shaft tilt -- two axes** (`tilt_pitch`, `tilt_roll`: floats, radians): The orientation of all three shafts, decomposed into two components:
  - `tilt_pitch`: Tilt perpendicular to the brace axis. When the platform pitches forward/backward, both arms need to adjust in the same direction. Controlled by both arm actuators moving together.
  - `tilt_roll`: Tilt along the brace axis. When the platform rolls left/right (cross-slope), one arm extends while the other retracts. Controlled by the brace actuator directly, or by arm actuators moving in opposite directions.
  - When both are zero, shafts are vertical. The parallelogram linkages enforce that all three shafts share the same `(tilt_pitch, tilt_roll)`.
- **Arm reaches** (`reach_b`, `reach_c`: floats, radians): How far each arm extends downward. These are independent -- on bumpy terrain one arm reaches further than the other. The parallelogram ensures the shaft orientation at the wheel end stays at `(tilt_pitch, tilt_roll)` regardless of reach angle.

### Tilt Axis Decomposition

The brace connects the two arms laterally. Define the coordinate system for tilt:
- **Brace direction**: The vector from arm B attachment to arm C attachment (roughly the Y axis in body frame).
- **Pitch axis**: Parallel to brace direction. Rotation around this axis tips the platform forward/backward.
- **Roll axis**: Perpendicular to brace direction (roughly the X axis in body frame). Rotation around this axis tips the platform left/right.

This decomposition is natural because:
- The brace actuator (in Active Brace strategy) directly controls rotation around the brace direction → it directly controls **roll**.
- The arm actuators (in Active Arms strategy) control rotation around both axes: moving arms in the same direction → pitch; moving arms in opposite directions → roll.
- The IMU mounted on any shaft measures both `tilt_pitch` and `tilt_roll` (2-axis inclinometer is sufficient since both angles are relative to gravity).

### Relation to Current State

Current `SimState`:
```python
arm_pivots: tuple[float, float]      # independent pivot angles
arm_velocities: tuple[float, float]  # independent velocities
```

Revised `SimState`:
```python
tilt_pitch: float                     # pitch tilt (perpendicular to brace), 0 = vertical
tilt_roll: float                      # roll tilt (along brace), 0 = vertical
tilt_pitch_velocity: float
tilt_roll_velocity: float
arm_reaches: tuple[float, float]      # (reach_b, reach_c), independent
arm_reach_velocities: tuple[float, float]
```

### Geometry Mapping

The wheel position for arm B in world frame becomes a function of `(tilt_pitch, tilt_roll, reach_b)`:
- `tilt_pitch` and `tilt_roll` together define the shaft orientation (applied as rotations to the arm assembly)
- `reach_b` affects how far down the arm extends (determines wheel height relative to body)

The `compute_wheel_positions` function in `geometry.py` needs to accept `(tilt_pitch, tilt_roll, reach_b, reach_c)` instead of `(pivot_b, pivot_c)`.

### Geometry Math

For arm B (splay_sign = -1), wheel position in body frame:

```
# The arm direction in XY plane (from apex toward wheel B)
arm_dir_x = cos(splay)
arm_dir_y = splay_sign * sin(splay)   # -sin(splay) for B, +sin(splay) for C

# reach determines how far the arm extends (angle from horizontal)
dx = arm_length * arm_dir_x * cos(reach_b)
dy = arm_length * arm_dir_y * cos(reach_b)
dz = -arm_length * sin(reach_b)

# Apply tilt as two sequential rotations:
# 1. tilt_roll rotates around X axis (perpendicular to brace)
# 2. tilt_pitch rotates around Y axis (parallel to brace)
# Combined as a rotation matrix R = Ry(tilt_pitch) @ Rx(tilt_roll)
# Applied to the arm endpoint vector (dx, dy, dz)

R = rotation_matrix(tilt_pitch, tilt_roll)
wheel_offset = R @ [dx, dy, dz]

wheel_x = body_x + cos(yaw) * wheel_offset[0] - sin(yaw) * wheel_offset[1]
wheel_y = body_y + sin(yaw) * wheel_offset[0] + cos(yaw) * wheel_offset[1]
wheel_z = body_z + wheel_offset[2]
```

The implementation will define the rotation matrix and verify with tests that `(tilt_pitch=0, tilt_roll=0)` → vertical shafts, and that both tilt components independently rotate all shafts by the same angle.

## Hard Surface Constraint

### During Integration

The penalty spring contact model stays (it provides physically-meaningful reaction forces and smooth dynamics), but parameters increase for stiffer response:
- `contact_stiffness`: 2000 → 5000
- `contact_damping`: 50 → 100

### Post-Integration Clamp

After semi-implicit Euler integration, enforce:

```
for each arm (b, c):
    compute wheel_z from (tilt_pitch, tilt_roll, reach)
    terrain_z = terrain.height(wheel_x, wheel_y)
    if wheel_z < terrain_z:
        adjust reach so wheel_z == terrain_z  (solve analytically)
        set reach_velocity = 0  (inelastic contact)
```

This guarantees no visual penetration regardless of timestep or stiffness.

## Tipping Under Gravity

When the platform is on a slope or when wheels lose terrain contact, gravity creates torques on both tilt axes:

- **Pitch torque**: `gravity_pitch = -M * g * L_cog * sin(tilt_pitch)` -- tips the platform forward/backward.
- **Roll torque**: `gravity_roll = -M * g * L_cog * sin(tilt_roll)` -- tips the platform left/right.
- `M` is total mass, `L_cog` is the distance from the tilt axis to the center of gravity.
- When wheels are in contact with terrain, the terrain reaction forces counteract these torques.
- When wheels are NOT in contact (e.g., one arm is reaching into a dip), the unbalanced torques cause the platform to tip on both axes.

## Active Leveling Strategies

Both strategies use a PD controller reading `(tilt_pitch, tilt_roll)` from a 2-axis IMU:

```python
torque_pitch = -kp * tilt_pitch - kd * tilt_pitch_velocity
torque_roll  = -kp * tilt_roll  - kd * tilt_roll_velocity
```

### Strategy 1: Active Arms Leveling (`ActiveArmsLeveling`)

- Actuators on both arm parallelograms.
- Two independent actuators → can control both tilt axes directly.
- **Pitch correction**: Both arms adjust in the same direction (same torque sign).
- **Roll correction**: Arms adjust in opposite directions (opposite torque signs).
- The controller decomposes the two tilt errors into per-arm torques:
  ```
  torque_arm_b = torque_pitch + torque_roll
  torque_arm_c = torque_pitch - torque_roll
  ```
- Arm reaches adjust as a consequence to maintain terrain contact.
- **Parameters**: `kp` (proportional gain), `kd` (derivative gain).

### Strategy 2: Active Brace Leveling (`ActiveBraceLeveling`)

- Single actuator on the brace parallelogram.
- Arms are passive (gravity + terrain contact determines reach).
- The brace actuator directly controls **roll** (tilt along the brace axis) since the brace connects the two arms laterally.
- **Pitch correction is indirect**: The brace can't directly pitch the platform forward/backward. It can only influence pitch through the coupling between roll correction and arm geometry. This is the key limitation that makes this strategy interesting to compare.
- **Parameters**: `kp_roll` (proportional gain for roll), `kd_roll` (derivative gain for roll), `brace_gain` (mechanical advantage factor).

### Existing Strategies (Retained)

- `PassiveStrategy`: No actuation. Arms settle via gravity + terrain contact. Tilt drifts freely on both axes.
- `SpringDamperStrategy`: Spring return on reaches around neutral. No tilt control.

## Metrics & Comparison

### Per-Timestep Metrics

The `simulate_step` function returns both the new state and a metrics dict:

```python
@dataclass
class StepMetrics:
    tilt_pitch_deg: float       # pitch tilt in degrees
    tilt_roll_deg: float        # roll tilt in degrees
    tilt_total_deg: float       # total tilt magnitude (sqrt(pitch^2 + roll^2))
    actuator_torque_pitch: float  # pitch torque this step (N*m)
    actuator_torque_roll: float   # roll torque this step (N*m)
    actuator_power: float       # total |torque * velocity| this step (W)
    cumulative_energy: float    # running total of energy used (J)
    reach_b_deg: float          # arm B reach in degrees
    reach_c_deg: float          # arm C reach in degrees
    in_contact_b: bool          # whether wheel B is on terrain
    in_contact_c: bool          # whether wheel C is on terrain
```

### Comparison Criteria

- **Convergence speed**: Time to reach `tilt_total < 1 degree` from a disturbed initial state.
- **Energy efficiency**: Total actuator energy to reach steady state.
- **Steady-state accuracy**: Residual tilt magnitude in steady state.
- **Pitch vs roll performance**: Active Brace can directly control roll but not pitch -- how does this affect convergence on different terrain types (forward slope vs cross-slope vs bumpy)?
- **Robustness**: Behavior when traversing bumpy terrain (does tilt stay controlled on both axes?).

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
    "metrics": {
        "tilt_pitch_deg": 2.87,
        "tilt_roll_deg": -1.05,
        "tilt_total_deg": 3.06,
        "actuator_torque_pitch": -1.23,
        "actuator_torque_roll": 0.45,
        "actuator_power": 0.67,
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
- "Pivot B" → "Pitch" (tilt_pitch in degrees)
- "Pivot C" → "Roll" (tilt_roll in degrees)
- Keep "Stability Margin" and "Sim Time"

### Metrics Chart

A new panel (below viewport, beside info bar, or as a collapsible overlay) showing a live time-series line chart:
- **Line 1**: Pitch tilt (degrees) over time
- **Line 2**: Roll tilt (degrees) over time
- **Line 3**: Total actuator torque magnitude over time (secondary axis)
- Canvas-based rendering, no external charting library
- Rolling window of ~10 seconds of data
- Clears on strategy change or sim restart

### Strategy Dropdown

Add to the existing strategy select:
- `active_arms_leveling` ("Active Arms (IMU)")
- `active_brace_leveling` ("Active Brace (IMU)")

## Backend Changes

### `wheely/dynamics.py`

- Revise `SimState` to use `tilt_pitch`, `tilt_roll`, `tilt_pitch_velocity`, `tilt_roll_velocity`, `arm_reaches`, `arm_reach_velocities`.
- Add `StepMetrics` dataclass.
- Add `ActiveArmsLeveling` strategy class (controls both pitch and roll).
- Add `ActiveBraceLeveling` strategy class (controls roll directly, pitch indirectly).
- Revise `simulate_step` to:
  1. Compute strategy torques on `tilt_pitch` and `tilt_roll`
  2. Compute gravity torques on both tilt axes
  3. Compute terrain contact per arm (affects `arm_reaches`)
  4. Integrate `tilt_pitch`, `tilt_roll`, and `arm_reaches` (semi-implicit Euler)
  5. Hard clamp: enforce no-penetration on each arm
  6. Return `(new_state, metrics)`
- Revise `_compute_terrain_contact_torque` to work with the new two-axis tilt + reach model. Terrain contact on each arm contributes to both pitch and roll torques depending on the arm's position relative to the brace axis.

### `wheely/geometry.py`

- Update `compute_wheel_positions` to accept `(tilt_pitch, tilt_roll, reach_b, reach_c)` instead of `(pivot_b, pivot_c)`.
- The mapping: the old `pivot` was a single angle per arm. Now it decomposes into two shared tilt angles affecting the entire arm assembly orientation, and per-arm reach affecting extension.
- Add a rotation matrix helper that composes pitch and roll rotations.
- Update `compute_brace_endpoints` and `compute_brace_center` accordingly.

### `wheely/kinematics.py`

- Update `inverse_kinematics` to solve for `(tilt_pitch, tilt_roll, reach_b, reach_c)` instead of `(pivot_b, pivot_c)`. This becomes a 4-variable optimization (or can be decomposed: solve reaches first to place wheels on terrain, then compute the tilt that results).
- Update `forward_kinematics` to accept the new state format.

### `wheely/server.py`

- Add new strategy presets for `active_arms_leveling` and `active_brace_leveling`.
- Update `_build_frame` to include metrics in the response.
- Update `simulate_step` call to handle the new return signature `(state, metrics)`.

### Backward Compatibility

The old `arm_pivots` concept is replaced entirely. The WebSocket API changes:
- Frame responses use `tilt_pitch`, `tilt_roll`, `reach_b`, `reach_c` instead of `arm_pivots`.
- The `set_config` message stays the same (geometry parameters unchanged).
- The `set_strategy` message gains two new valid names.

## Testing

### Hard Surface Constraint
- Property test: For any terrain and initial state, after `simulate_step`, wheel Z >= terrain Z at wheel XY.
- Specific test: Start with wheel above bumpy terrain, run 100 steps, verify no penetration ever occurs.

### Parallelogram Coupling
- Test that FK with `(tilt_pitch, tilt_roll, reach_b, reach_c)` produces shaft orientations that are parallel for both wheels.
- Test that changing `tilt_pitch` rotates all shafts by the same pitch angle.
- Test that changing `tilt_roll` rotates all shafts by the same roll angle.
- Test that `(tilt_pitch=0, tilt_roll=0)` gives vertical shafts.

### Active Leveling Convergence
- **Forward slope test**: Start on a 20-degree forward slope. Both strategies should converge `tilt_pitch → 0`. `ActiveArmsLeveling` corrects directly. `ActiveBraceLeveling` must correct pitch indirectly -- test whether it can.
- **Cross-slope test**: Start on a 20-degree cross-slope. Both strategies should converge `tilt_roll → 0`. `ActiveBraceLeveling` corrects roll directly here.
- **Combined slope test**: Start on a slope with both pitch and roll components. `ActiveArmsLeveling` should handle both. `ActiveBraceLeveling` may struggle with the pitch component.
- Compare energy used across all scenarios.

### Passive Settling
- Existing tests for `PassiveStrategy` continue to work with the new state format.
- Arms should settle via gravity + terrain contact (reaches adapt, tilt drifts on both axes).

### Metrics
- Test that `cumulative_energy` increases monotonically.
- Test that `actuator_torque_pitch` and `actuator_torque_roll` signs match the correction direction.

## Scope Boundaries

### In Scope
- Revised DOF model (tilt_pitch + tilt_roll + arm_reaches)
- Two-axis tilt: pitch (perpendicular to brace) and roll (along brace)
- Hard surface constraint (no penetration)
- Gravity tipping on both tilt axes
- Two active leveling strategies (arms vs brace) with 2-axis IMU
- Per-step metrics (pitch, roll, torque, energy)
- Live metrics chart in frontend (pitch + roll + torque lines)
- Updated info bar
- Updated strategy dropdown
- Tests for all new physics including per-axis convergence

### Out of Scope
- Body XY motion (driving/steering simulation)
- Flex or compliance in the parallelogram linkages
- Terrain friction model
