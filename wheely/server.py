"""FastAPI server for wheely simulation.

Provides REST endpoints for configuration and a WebSocket for real-time simulation.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from wheely.dynamics import (
    ActiveStrategy,
    PassiveStrategy,
    SimState,
    SpringDamperStrategy,
    simulate_step,
)
from wheely.geometry import PlatformConfig
from wheely.kinematics import (
    compute_stability_margin,
    compute_support_triangle,
    forward_kinematics,
    inverse_kinematics,
)
from wheely.terrain import (
    ComposedTerrain,
    FlatTerrain,
    SinusoidalTerrain,
    SlopeTerrain,
)

app = FastAPI(title="Wheely Simulation")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

# Mount static files for the web frontend
app.mount("/static", StaticFiles(directory=str(WEB_DIR), check_dir=False), name="static")


TERRAIN_PRESETS = {
    "flat": lambda: FlatTerrain(),
    "gentle_slope": lambda: SlopeTerrain(slope_x=0.15),
    "steep_slope": lambda: SlopeTerrain(slope_x=0.4),
    "cross_slope": lambda: SlopeTerrain(slope_y=0.3),
    "bumpy": lambda: SinusoidalTerrain(amplitude=0.15, wavelength=2.0),
    "rough": lambda: ComposedTerrain([
        SlopeTerrain(slope_x=0.1),
        SinusoidalTerrain(amplitude=0.08, wavelength=1.0),
    ]),
}

STRATEGY_PRESETS = {
    "passive": lambda: PassiveStrategy(),
    "active": lambda: ActiveStrategy(target_pivots=(0.0, 0.0), kp=50.0),
    "spring_damper": lambda: SpringDamperStrategy(stiffness=200.0, damping=20.0),
}


@app.get("/")
async def index():
    return FileResponse(str(WEB_DIR / "index.html"))


@app.get("/api/config")
async def get_default_config():
    return PlatformConfig().to_dict()


@app.get("/api/terrains")
async def list_terrains():
    return list(TERRAIN_PRESETS.keys())


@app.get("/api/strategies")
async def list_strategies():
    return list(STRATEGY_PRESETS.keys())


def _build_frame(config, terrain, arm_pivots, steerings):
    """Compute a single simulation frame for sending to the client."""
    fk = forward_kinematics(config, arm_pivots=arm_pivots, steerings=steerings)
    triangle = compute_support_triangle(fk.wheel_contacts)
    margin = compute_stability_margin(fk.brace_center, triangle)

    return {
        "wheels": {k: v.tolist() for k, v in fk.wheel_contacts.items()},
        "brace_center": fk.brace_center.tolist(),
        "support_triangle": triangle.tolist(),
        "stability_margin": margin,
        "arm_pivots": list(arm_pivots),
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    config = PlatformConfig()
    terrain = FlatTerrain()
    strategy = PassiveStrategy()
    sim_state = SimState.from_config(config)
    running = False

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "set_config":
                params = msg.get("params", {})
                config = PlatformConfig(**{
                    k: v for k, v in params.items() if hasattr(PlatformConfig, k)
                })
                errors = config.validate()
                if errors:
                    await ws.send_json({"type": "error", "errors": errors})
                    continue

            elif msg_type == "set_terrain":
                name = msg.get("name", "flat")
                if name in TERRAIN_PRESETS:
                    terrain = TERRAIN_PRESETS[name]()

            elif msg_type == "set_strategy":
                name = msg.get("name", "passive")
                if name in STRATEGY_PRESETS:
                    strategy = STRATEGY_PRESETS[name]()

            elif msg_type == "set_position":
                x = msg.get("x", 0.0)
                y = msg.get("y", 0.0)
                yaw = msg.get("yaw", 0.0)
                sim_state = SimState(body_xy=(x, y), body_yaw=yaw)

            elif msg_type == "solve_ik":
                ik = inverse_kinematics(
                    config, terrain,
                    body_xy=sim_state.body_xy,
                    body_yaw=sim_state.body_yaw,
                )
                sim_state.arm_pivots = ik.arm_pivots
                frame = _build_frame(
                    config, terrain, sim_state.arm_pivots, sim_state.steerings
                )
                frame["type"] = "frame"
                frame["levelness"] = ik.levelness
                await ws.send_json(frame)

            elif msg_type == "start_sim":
                running = True
                sim_state = SimState.from_config(config)
                while running:
                    sim_state = simulate_step(
                        sim_state, config, terrain, strategy, dt=0.016
                    )
                    frame = _build_frame(
                        config, terrain, sim_state.arm_pivots, sim_state.steerings
                    )
                    frame["type"] = "frame"
                    frame["time"] = sim_state.time
                    await ws.send_json(frame)
                    await asyncio.sleep(0.033)

                    try:
                        raw = await asyncio.wait_for(ws.receive_text(), timeout=0.001)
                        inner = json.loads(raw)
                        if inner.get("type") == "stop_sim":
                            running = False
                    except asyncio.TimeoutError:
                        pass

            elif msg_type == "stop_sim":
                running = False

            elif msg_type == "get_frame":
                frame = _build_frame(
                    config, terrain, sim_state.arm_pivots, sim_state.steerings
                )
                frame["type"] = "frame"
                await ws.send_json(frame)

            elif msg_type == "get_terrain_grid":
                size = msg.get("size", 10.0)
                res = msg.get("resolution", 50)
                lin = [float(-size / 2 + i * size / res) for i in range(res + 1)]
                heights = []
                for yi in lin:
                    row = []
                    for xi in lin:
                        row.append(terrain.height(xi, yi))
                    heights.append(row)
                await ws.send_json({
                    "type": "terrain_grid",
                    "size": size,
                    "resolution": res,
                    "heights": heights,
                })

    except WebSocketDisconnect:
        pass
