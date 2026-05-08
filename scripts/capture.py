"""Playwright browser automation for capturing screenshots and GIFs.

Drives a headless Chromium browser, connects to the wheely server via WebSocket,
sends scenario setup messages, and captures the #viewport element.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.scenarios import CaptureType, GifConfig, Scenario, get_scenarios


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


def capture_gif(
    page: Page, gif_config: GifConfig, frame_messages: list[dict] | None = None
) -> bytes:
    """Capture an animated GIF of the #viewport element.

    Args:
        page: Playwright page with active WebSocket.
        gif_config: Frame count and interval.
        frame_messages: Optional per-frame messages to send before each capture.

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
    rgb_images = []
    for img in images:
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (26, 26, 46))
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
    scenarios = get_scenarios()
    results: list[tuple[bytes | None, bytes | None]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": viewport_width, "height": viewport_height}
        )
        page.goto(url)

        # Wait for WebSocket connection
        wait_for_connection(page)

        # Give a moment for the page to fully initialize
        page.wait_for_timeout(1000)

        for scenario in scenarios:
            print(f"  Capturing: {scenario.title}")
            result = run_scenario_capture(page, scenario)
            results.append(result)

        browser.close()

    return results
