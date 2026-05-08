"""Assemble captured media and code snippets into a reveal.js HTML deck.

Produces a single self-contained HTML file with all images embedded as base64
data URIs. Uses reveal.js and highlight.js from CDN.
"""

from __future__ import annotations

import ast
import base64
import html
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.scenarios import CodeSnippet, Scenario, SlideLayout


def extract_code(snippet: CodeSnippet) -> str:
    """Extract code from source file using AST parsing."""
    if snippet.raw_text:
        return snippet.raw_text

    filepath = Path(snippet.filepath)
    if not filepath.exists():
        return f"# Source not found: {snippet.filepath}"

    source = filepath.read_text()
    tree = ast.parse(source)

    target_name = snippet.function_name or snippet.class_name
    if not target_name:
        return source[:500]

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == target_name:
                lines = source.splitlines()
                extracted = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                return textwrap.dedent(extracted)

    return f"# {target_name} not found in {snippet.filepath}"


def _img_tag(data: bytes, mime: str) -> str:
    """Create an <img> tag with base64 data URI."""
    b64 = base64.b64encode(data).decode("ascii")
    return f'<img src="data:{mime};base64,{b64}" />'


def _build_title_slide(scenario: Scenario) -> str:
    content = html.escape(scenario.raw_content)
    return f'''<section>
  <h1>{html.escape(scenario.title)}</h1>
  <pre class="ascii">{content}</pre>
</section>'''


def _build_demo_slide(scenario: Scenario, primary: bytes | None) -> str:
    visual_html = ""
    if primary:
        mime = "image/gif" if scenario.capture_type.name == "GIF" else "image/png"
        visual_html = _img_tag(primary, mime)

    code_html = ""
    if scenario.code:
        code_text = html.escape(extract_code(scenario.code))
        code_html = f'<pre><code class="language-python">{code_text}</code></pre>'

    caption_html = ""
    if scenario.caption:
        caption_html = f'<p class="caption">{html.escape(scenario.caption)}</p>'

    return f'''<section>
  <h2>{html.escape(scenario.title)}</h2>
  <div class="split">
    <div class="visual">
      {visual_html}
    </div>
    <div class="code-panel">
      {code_html}
      {caption_html}
    </div>
  </div>
</section>'''


def _build_comparison_slide(
    scenario: Scenario, primary: bytes | None, secondary: bytes | None
) -> str:
    img1 = _img_tag(primary, "image/gif") if primary else ""
    img2 = _img_tag(secondary, "image/gif") if secondary else ""

    code_html = ""
    if scenario.code:
        code_text = html.escape(extract_code(scenario.code))
        code_html = f'<pre><code class="language-python">{code_text}</code></pre>'

    return f'''<section>
  <h2>{html.escape(scenario.title)}</h2>
  <div class="compare">
    <div>
      {img1}
      <p class="label">Passive</p>
    </div>
    <div>
      {img2}
      <p class="label">{html.escape(scenario.second_caption)}</p>
    </div>
  </div>
  {code_html}
  <p class="caption">{html.escape(scenario.caption)}</p>
</section>'''


def _build_text_slide(scenario: Scenario) -> str:
    content = html.escape(scenario.raw_content)
    caption_html = ""
    if scenario.caption:
        items = scenario.caption.split(" | ")
        li_items = "".join(f"<li>{html.escape(item)}</li>" for item in items)
        caption_html = f"<ul>{li_items}</ul>"

    return f'''<section>
  <h2>{html.escape(scenario.title)}</h2>
  <pre class="structure">{content}</pre>
  {caption_html}
</section>'''


DECK_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Wheely Showcase</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/black.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/monokai.min.css">
<style>
  :root {{
    --r-background-color: #1a1a2e;
    --r-main-color: #e0e0e0;
    --r-heading-color: #e94560;
    --r-link-color: #e94560;
  }}
  .reveal {{ font-size: 24px; }}
  .reveal h1 {{ color: #e94560; font-size: 2.5em; }}
  .reveal h2 {{ color: #e94560; font-size: 1.8em; margin-bottom: 0.5em; }}
  .reveal pre {{ font-size: 0.55em; }}
  .reveal pre.ascii, .reveal pre.structure {{
    text-align: left; font-size: 0.5em; background: #0a0a1a;
    padding: 20px; border-radius: 8px; display: inline-block;
  }}
  .split {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 20px; align-items: start; text-align: left;
  }}
  .split .visual img {{
    max-width: 100%; border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  .split .code-panel pre {{
    margin: 0; max-height: 400px; overflow-y: auto;
  }}
  .compare {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 20px; margin-bottom: 20px;
  }}
  .compare img {{
    max-width: 100%; border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  .compare .label {{
    text-align: center; font-weight: bold; margin-top: 8px;
    color: #e94560;
  }}
  .caption {{
    font-style: italic; color: #aaa; margin-top: 12px; font-size: 0.9em;
  }}
  ul {{ text-align: left; list-style: disc; padding-left: 1.5em; }}
</style>
</head>
<body>
<div class="reveal">
  <div class="slides">
{slides}
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/highlight.js"></script>
<script>
Reveal.initialize({{
  hash: true,
  plugins: [RevealHighlight],
  width: 1280,
  height: 720,
}});
</script>
</body>
</html>
"""


def build_deck(
    scenarios: list[Scenario],
    captures: list[tuple[bytes | None, bytes | None]],
) -> str:
    """Build the complete reveal.js HTML deck."""
    slides_html = []

    for scenario, (primary, secondary) in zip(scenarios, captures):
        if scenario.layout == SlideLayout.TITLE:
            slides_html.append(_build_title_slide(scenario))
        elif scenario.layout == SlideLayout.DEMO:
            slides_html.append(_build_demo_slide(scenario, primary))
        elif scenario.layout == SlideLayout.COMPARISON:
            slides_html.append(_build_comparison_slide(scenario, primary, secondary))
        elif scenario.layout == SlideLayout.TEXT:
            slides_html.append(_build_text_slide(scenario))

    all_slides = "\n".join(f"    {s}" for s in slides_html)
    return DECK_TEMPLATE.format(slides=all_slides)
