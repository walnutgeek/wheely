# Wheely: Tricycle Robotic Platform -- Kinematic Simulation Design

## Overview

Wheely is a three-wheel-drive robotic platform designed for uneven terrain (forestry, rough ground). All three wheels are independently steered and driven. Two parallelogram arms extend from a single apex wheel to two rear wheels, with a parallelogram cross brace connecting the arms. The geometry naturally keeps the body/cargo area level as the arms conform to terrain.

Target scale: mid-size prototype (~1-2m footprint, tens of kg payload).

This spec covers the simulation and design exploration tool -- a Python backend with a web-based Three.js frontend for modeling geometry, kinematics, dynamics, and parametric design space exploration.

## Mechanical Model

### Geometry

```
Top-down view:

           [Wheel A]  (apex)
              /\
             /  \
            /    \
    arm1   /      \   arm2
          /  brace \
         /====[]====\    (cross brace with cargo bay)
        /            \
  [Wheel B]      [Wheel C]
```

- **Wheel A**: Single wheel at the apex of the platform
- **Parallelogram arms**: Two arms extending from the apex to wheels B and C. Each arm is a 4-bar parallelogram linkage that preserves the orientation of the distal link as the arm pivots
- **Cross brace**: A parallelogram linkage connecting the two arms at a configurable midpoint. Provides structural rigidity and a mounting surface for cargo
- **Cargo bays**: On each arm and on the cross brace

### Self-Leveling Mechanism

The parallelogram linkages are the key innovation. As wheels follow terrain contours, the arms pivot but the body/cargo platform maintains its orientation. The body stays level not because of active control, but because the parallelogram geometry naturally preserves orientation.

The wheels are on the terrain (ground truth). The arms are the linkages. The body is the output that stays level.

### Parameters

All dimensions are parametric and tunable:

| Parameter | Description | Default | Valid range |
|-----------|-------------|---------|-------------|
| `arm_length` | Length of each parallelogram arm | 0.8 m | 0.3 - 1.5 m |
| `arm_splay_angle` | Angle of each arm from centerline (top-down) | 40 deg | 20 - 60 deg |
| `brace_position` | Where cross brace attaches along arm (0.0 = apex, 1.0 = wheel) | 0.5 | 0.3 - 0.7 |
| `brace_length` | Length of the cross brace | 0.5 m | 0.2 - 1.0 m |
| `wheel_radius` | Radius of each wheel (per-wheel configurable) | 0.15 m | 0.05 - 0.3 m |
| `wheel_width` | Width of each wheel (per-wheel configurable) | 0.08 m | 0.03 - 0.15 m |
| `pivot_range` | Range of motion for arm pivot joints | +/- 45 deg | +/- 30 - 60 deg |
| `steering_range` | Range of motion for wheel steering | +/- 90 deg | +/- 45 - 180 deg |

### Degrees of Freedom

- 6 DOF for platform pose (x, y, z, roll, pitch, yaw)
- 2 arm pivot angles (each arm up/down)
- 3 steering angles (each wheel independently)
- 3 drive speeds (each wheel independently)
- Cross brace is constrained by the two arm pivots (not independent)

## Software Architecture

### Project Structure

```
wheely/
├── wheely/                    # Python package
│   ├── __init__.py
│   ├── geometry.py            # Parametric geometry definitions
│   ├── kinematics.py          # Forward/inverse kinematics solver
│   ├── dynamics.py            # Rigid body dynamics, terrain contact
│   ├── terrain.py             # Heightmap terrain model
│   ├── platform.py            # Platform state, configuration
│   └── server.py              # FastAPI backend serving simulation data
├── web/                       # Three.js frontend
│   ├── index.html
│   ├── scene.js               # 3D scene setup, rendering
│   ├── platform-viz.js        # Platform 3D model from params
│   ├── terrain-viz.js         # Terrain mesh rendering
│   ├── controls.js            # Parameter sliders, interaction
│   └── simulation.js          # Animation loop, server communication
├── tests/
│   ├── test_geometry.py
│   ├── test_kinematics.py
│   ├── test_dynamics.py
│   └── test_terrain.py
├── docs/
├── pyproject.toml
└── README.md
```

### Tech Stack

- **Backend**: Python 3.11+, NumPy, SciPy, FastAPI, WebSocket
- **Frontend**: Three.js, vanilla JS, CSS grid
- **Communication**: WebSocket for real-time simulation (~30fps), REST for parameter changes
- **Testing**: pytest, hypothesis (property-based tests)

### Key Design Decisions

1. **Python backend, JS frontend**: Math in Python (strongest tool), visualization in the browser (shareable)
2. **Parametric everything**: Every dimension is a function parameter, enabling sweeps and optimization
3. **Kinematics/dynamics separation**: Kinematics module runs standalone; dynamics adds forces and terrain contact on top
4. **Terrain as a function interface**: `height(x, y) -> z` and `normal(x, y) -> vec3` -- implementations are pluggable
5. **Pluggable actuation strategies**: Each strategy is a Python class with the same interface

## Kinematics Engine

### Coordinate System

Right-hand, Z-up. Origin at center of apex body (Wheel A mount). X forward, Y left, Z up.

### Forward Kinematics

Given body pose + arm pivot angles + steering angles, compute each wheel's contact point and orientation in world frame.

The parallelogram linkage math: each arm has a pivot angle theta. The distal link (wheel mount) position is computed from the proximal link position, arm length, and theta. The distal link orientation equals the proximal link orientation (parallelogram property).

### Inverse Kinematics (Terrain Adaptation)

The primary solver: given 3 wheel contact points on terrain, compute arm pivot angles and verify that the body stays level.

1. For each wheel, the contact point is determined by terrain height at the wheel's ground-projected position
2. Solve arm pivot angles to place wheels B and C at their contact points
3. Compute the resulting body pose
4. Evaluate levelness: how close to horizontal is the cargo platform?

### Workspace Analysis

Parametric sweeps to visualize:
- Reachable ground area for each wheel
- Maximum traversable slope angle
- Stability regions (center of gravity within support triangle)
- Self-leveling quality metric across terrain types

## Dynamics (Phase 2)

### Terrain Model

`height(x, y) -> z` function with pluggable implementations:
- Flat plane with configurable slope
- Sinusoidal / procedural noise bumps
- Loaded from heightmap image
- Composed obstacles (steps, ramps, ditches)

### Rigid Body Dynamics

- Mass and inertia for each rigid body (platform body, arms, wheels)
- SciPy ODE integration for time stepping
- Wheel-terrain contact: normal force from terrain surface, Coulomb friction
- Gravity and load distribution

### Stability Analysis

- Support triangle defined by 3 wheel contact points
- Center of gravity projection onto ground plane
- Tipping threshold: when CoG projection exits support triangle
- Stability margin: distance from CoG projection to nearest triangle edge

### Pluggable Actuation Strategies

Each strategy implements a common interface:

```python
class ActuationStrategy:
    def compute_torques(self, state: PlatformState) -> ArmTorques:
        """Given current state, return torques for arm pivot joints."""
        ...
```

Implementations:
- **Passive**: Zero torque, arms pivot freely under gravity
- **Active**: PID control to target arm angles
- **SpringDamper**: Spring return force + viscous damping
- **Coupled**: Arm torque coupled to steering or drive signals

## Web Visualization

### Core Views

1. **Interactive 3D view**: Three.js scene with orbit camera. Real-time parameter adjustment via sliders. Platform adapts as parameters change.

2. **Terrain playground**: Place platform on different terrain configurations. Drag to see arm adaptation, tipping behavior, slope handling.

3. **Workspace visualization**: Overlay of reachable wheel space, stability region, constraint boundaries.

4. **Parameter sweep dashboard**: Heatmaps/contour plots from parameter sweeps alongside the 3D model.

### Communication Protocol

- WebSocket: frontend sends parameter changes and user interactions, backend streams kinematics/dynamics results
- Target ~30fps for real-time interaction
- REST endpoints for batch operations (parameter sweeps)

### Shareability

The web frontend is the primary communication tool for the project. Anyone with the URL can interact with the simulation, adjust parameters, and understand the platform's behavior. This is critical for recruiting collaborators.

## Testing Strategy

### Unit Tests (pytest)

- **test_geometry.py**: Parametric geometry produces valid linkage dimensions. Parallelogram constraints hold. Degenerate configurations detected.
- **test_kinematics.py**: Forward kinematics matches known configurations. Inverse kinematics places wheels on flat ground correctly. Body stays level on symmetric terrain. Joint limits respected.
- **test_dynamics.py**: Conservation of energy on flat ground. Stable configurations don't tip. Known unstable configurations do tip. Contact forces are physically correct.
- **test_terrain.py**: Heightmap returns correct values. Normals are unit vectors. Composed terrains combine correctly.

### Property-Based Tests (hypothesis)

- Random parameter combinations within valid ranges always produce valid geometry
- Parallelogram constraint is preserved regardless of pivot angle
- Forward then inverse kinematics round-trips correctly

### Integration Tests

- Full simulation loop: create platform, place on terrain, run kinematics, verify results
- WebSocket round-trip: parameter change from frontend, backend simulation, result back to frontend

## Scope Boundaries

### In scope (this spec)

- Parametric mechanical model of the tricycle platform
- Forward and inverse kinematics
- Simple dynamics with rigid terrain contact
- Web-based 3D visualization with parameter controls
- Parametric design space exploration
- Multiple actuation strategies

### Out of scope (future specs)

- Control system / path planning
- Deformable terrain (mud, soft ground)
- Motor selection and electrical design
- Physical prototype construction
- Community building and collaboration strategy (separate design cycle)
