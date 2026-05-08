---
name: showcase
description: Generate or update the wheely showcase deck (reveal.js HTML with screenshots and GIFs)
user_invocable: true
---

# Showcase Deck Generation

Generate a self-contained HTML slide deck demonstrating the wheely simulation platform.

## Prerequisites

```bash
pip install -e ".[showcase]"
playwright install chromium
```

## Generate the deck

```bash
python scripts/showcase.py
```

Output: `output/showcase.html` (open in any browser)

## Options

- `--port PORT` - Use a different server port (default: 8765)
- `--output PATH` - Write deck to a different path

## Customizing scenarios

Edit `scripts/scenarios.py` to add/modify/remove slides. Each `Scenario` dataclass defines:
- `title`: Slide heading
- `layout`: TITLE, DEMO, COMPARISON, or TEXT
- `capture_type`: NONE, SCREENSHOT, or GIF
- `setup_messages`: WebSocket messages to configure the scene
- `frame_messages`: Per-frame messages for GIF animations (parameter sweeps, position changes)
- `code`: CodeSnippet reference to extract from source
- `caption`: Explanatory text

## Regenerating after code changes

Run `python scripts/showcase.py` again. Code snippets are extracted from live source files, so the deck always reflects current implementation.

## Architecture

```
scripts/
├── showcase.py      # CLI orchestrator (server lifecycle, pipeline)
├── scenarios.py     # Scenario definitions (what to capture)
├── capture.py       # Playwright browser automation, screenshot/GIF capture
└── deck_builder.py  # HTML assembly with reveal.js + highlight.js
```
