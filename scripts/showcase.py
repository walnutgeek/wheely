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

        # Add project root to path for imports
        project_root = str(Path(__file__).resolve().parent.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

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
