---
name: showcase
description: Generate or update the wheely showcase deck (reveal.js HTML with screenshots and GIFs)
user_invocable: true
---

# Showcase Deck Generation

Generate a self-contained HTML slide deck demonstrating the wheely simulation platform.

## Output

`showcase/showcase.html` — a single self-contained HTML file (all images embedded as base64 data URIs). No external image files should remain in the directory.

## Prerequisites

Ensure playwright and chromium are available in the project venv:

```bash
pip install -e ".[dev]"
.venv/bin/python -m playwright install chromium
```

Also requires `ffmpeg` for GIF generation from frame sequences.

## Workflow

### 1. Start the simulation server

```bash
.venv/bin/uvicorn wheely.server:app --port 8765
```

Run in background. Verify with `curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/`.

### 2. Capture screenshots and GIFs

Use Playwright (headless Chromium) at **850x600** viewport with `device_scale_factor: 2` for retina quality.

- Navigate to `http://localhost:8765`, wait for WebSocket `Connected` status
- Interact with the UI via `page.evaluate()`, `page.select_option()`, `page.click()` etc.
- Take screenshots with `page.screenshot()`
- Record GIFs by capturing frame sequences (e.g., 5 seconds at 15fps = 75 frames), then convert with ffmpeg:
  ```bash
  ffmpeg -y -framerate 15 -i frame_%04d.png \
    -vf "scale=850:600:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
    output.gif
  ```
- Clean up frame directories after conversion

### 3. Build the reveal.js deck

Write `showcase/showcase.html` as a self-contained reveal.js presentation:

- Load reveal.js and highlight.js from CDN (`cdn.jsdelivr.net`)
- Use `<img src="filename.png">` initially while authoring
- Set Reveal config with `margin: 0.08` for safe text area

### 4. Visual check — 4:3 fit verification

**This step is mandatory.** After building the deck, verify every slide fits a 4:3 screen with no text cutoff:

1. Write a temporary verification script that:
   - Opens the deck HTML via `file://` URL in headless Playwright
   - Sets viewport to **1024x768** (4:3 aspect ratio)
   - Iterates `Reveal.getTotalSlides()`, calling `Reveal.slide(i)` for each
   - Screenshots each slide to a temp file
2. **Visually inspect every screenshot** using the Read tool
3. If any text is clipped or cut off at edges/bottom:
   - Reduce font sizes, shorten text, trim code blocks, or remove lines
   - Re-run the verification loop until all slides pass
4. Common fixes for overflow:
   - Reduce `font-size` in CSS (body text: `0.55em`, code: `0.38em`, lists: `0.55em`)
   - Shorten bullet text that wraps to right edge
   - Trim code blocks — remove blank lines, collapse comments, cut fields
   - Use shorter labels in metric boxes
5. Clean up verification script and temp screenshots when done

### 5. Embed images as base64 data URIs

**This step is mandatory.** The final HTML must be fully self-contained:

1. For each image referenced in the HTML (`src="filename.png"` or `src="filename.gif"`):
   - Read the file, base64-encode it
   - Replace `src="filename.ext"` with `src="data:image/<type>;base64,<data>"`
2. Delete all image files (PNGs, GIFs) from the `showcase/` directory
3. Also delete any unused GIFs that were captured but not included in the deck
4. Verify `showcase/` contains only `showcase.html`

This can be done with a Python one-liner:
```python
import base64; from pathlib import Path
html = Path('showcase.html').read_text()
for f, mime in [('img.png','image/png'), ('anim.gif','image/gif')]:
    d = base64.b64encode(Path(f).read_bytes()).decode()
    html = html.replace(f'src="{f}"', f'src="data:{mime};base64,{d}"')
Path('showcase.html').write_text(html)
```

## Style Guide

- Dark theme: background `#1a1a2e`, headings `#e94560`, accents `#4fc3f7`
- Code blocks: `atom-one-dark` highlight.js theme
- Architecture boxes: `#0f3460` background, `#16213e` for cards
- Tags/chips: `#0f3460` background with `#4fc3f7` text
- Metrics: `#4ade80` green values
- Keep all text, code, and images within the safe area at 1024x768 viewport
