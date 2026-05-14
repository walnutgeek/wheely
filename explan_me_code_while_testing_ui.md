# Explain me changes while testing UI

The reason I like this session is : 

I like to ask a code agents to explain and higlight to me most recent code and UI  changes in a 
html presentation deck. I like force tham to staly bit longer in self-imporoving loop by asking to take a 
screenshots from the website and sometimes videos to showcase functionality and it doubles as testing it. Because 
if CLI tool notices errors, it will... Fix them. Start over and loop until all flow is looks good. 

In this particular case, presentation itself has some visual issues and I use same technique to fix presentation as well and also at the end ask 
to modify skill to all thise steps automatically.

Skill in question is here: https://github.com/walnutgeek/wheely/tree/main/.claude/skills/showcase

And resulting deck is published on gh pages:
https://walnutgeek.github.io/wheely/

## Fix skill misnaming

❯ @.claude/skills/showcase.md does not show up as skill in claude even      
  after reload                                                              

⏺ Let me look at the file and the skills configuration to understand the issue.

⏺ Searched for 2 patterns, read 2 files (ctrl+o to expand)

⏺ claude-code-guide(Skills file structure rules)
  ⎿  Done (2 tool uses · 41.8k tokens · 12s)
  (ctrl+o to expand)

⏺ The issue is that the file needs to be named SKILL.md, not showcase.md. The
  correct structure is:

  .claude/skills/showcase/SKILL.md    ← required filename

  You currently have:

  .claude/skills/showcase/showcase.md  ← not discovered

  Let me rename it for you.

⏺ Bash(mv /Users/sergeyk/w/wheely/.claude/skills/showcase/showcase.md
      /Users/sergeyk/w/wheely/.claude/skills/showcase/SKILL.md)
  ⎿  Done

⏺ Done. The file is now at .claude/skills/showcase/SKILL.md. The skill should be
   discoverable without restarting — Claude Code detects live changes to skills.
   You can verify by typing / and looking for showcase in the menu.

✻ Crunched for 56s

## Actual prompt to do deck

❯ /showcase Create deck describing wheely robotic platform. Consult @README.md 
and designs @docs/ .Highlight simulation approach and python compomponens. Start
 simulation server. Keep window 850x600 higlight with screenshots what you see 
on screen. load @wheely-config.json, and choose figure 8 simulation. Run 
simulation,rotate view if wheely goes out of frame, take three 5-seconds videos 
of the simulation running and save them as gif files in showcase directory. 
Prompt me to inspect. I will give you one to include one to include into 
presentation and then you can finish deck 
  ⎿  Read README.md (56 lines)
  ⎿  Listed directory docs/
  ⎿  Read wheely-config.json (10 lines)

⏺ Let me start by exploring the project structure, docs, and Python components
  to understand what we're working with.

⏺ Read 4 files (ctrl+o to expand)

⏺ Let me read the key source files and docs in parallel.

⏺ Read 6 files (ctrl+o to expand)

⏺ Now let me install prerequisites and start the server.

⏺ Bash(pip install -e ".[dev]" 2>&1 | tail -5)
  ⎿  /bin/bash: pip: command not found

⏺ Searched for 1 pattern (ctrl+o to expand)

⏺ Bash(uv pip install -e ".[dev]" 2>&1 | tail -5)
  ⎿        Built wheely @ file:///Users/sergeyk/w/wheely
     Prepared 1 package in 490ms
     Uninstalled 1 package in 0.86ms
     … +2 lines (ctrl+o to expand)

⏺ Bash(python3 -c "import playwright; print('playwright installed')" 2>/dev/null
       || uv pip install playwright 2>&1 | tail -3)
  ⎿  Audited 1 package in 3ms

⏺ Read 1 file (ctrl+o to expand)

⏺ Bash(uv pip install playwright 2>&1 | tail -5)
  ⎿  Audited 1 package in 3ms

⏺ Read 1 file (ctrl+o to expand)

⏺ Bash(python3 --version && pip3 install playwright 2>&1 | tail -5)
  ⎿  Python 3.14.2

         Read more about this behavior here: <https://peps.python.org/pep-0
     … +7 lines (ctrl+o to expand)

⏺ Bash(uv pip list 2>&1 | head -5; uv pip show playwright 2>&1)
  ⎿  Package           Version   Editable project location
     ----------------- --------- -------------------------
     annotated-doc     0.0.4
     … +7 lines (ctrl+o to expand)

⏺ There's a venv. Let me use it directly.

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python -c "from playwright.sync_api
      import sync_playwright; print('OK')")
  ⎿  OK

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python -m playwright install chromium
      2>&1 | tail -5)
  ⎿  (No output)

⏺ Good. Now let me start the server and create the showcase directory.

⏺ Bash(mkdir -p /Users/sergeyk/w/wheely/showcase)
  ⎿  Done

⏺ Bash(lsof -ti:8765 2>/dev/null | xargs kill -9 2>/dev/null; echo "Port 8765
      cleared")
  ⎿  Port 8765 cleared

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/uvicorn wheely.server:app --port 8765
      2>&1)
  ⎿  Running in the background (↓ to manage)

⏺ Bash(sleep 2 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/)
  ⎿  200

⏺ Server is running. Now let me write a Playwright script to capture screenshots
   and GIFs. I need to:
  1. Take a screenshot of the default UI at 850x600
  2. Load the config from wheely-config.json
  3. Select figure-8 motion
  4. Start simulation and record 3 GIFs

⏺ Write(showcase/capture_showcase.py)
  ⎿  Wrote 260 lines to showcase/capture_showcase.py
       1 """Capture screenshots and GIF recordings of the wheely simulati
         on."""
       2 
       3 import asyncio
       4 import json
       5 import time
       6 from pathlib import Path
       7 
       8 from playwright.async_api import async_playwright
       9 
      10 SHOWCASE_DIR = Path(__file__).parent
     … +250 lines (ctrl+o to expand)

⏺ Bash(which ffmpeg && ffmpeg -version 2>&1 | head -1)
  ⎿  /opt/homebrew/bin/ffmpeg
     ffmpeg version 8.0.1 Copyright (c) 2000-2025 the FFmpeg developers

⏺ Good, ffmpeg is available. Now let me run the capture script.

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python showcase/capture_showcase.py
      2>&1)
  ⎿  Navigating to http://localhost:8765...
     Taking screenshot: default UI...
     Loading config and setting up bumpy terrain...
     … +19 lines (ctrl+o to expand)
  ⎿  (timeout 5m)

⏺ All captures completed successfully. Let me verify and view the outputs.

⏺ Read 1 file (ctrl+o to expand)

⏺ Let me view what was captured so you can inspect the results.

⏺ Read 2 files (ctrl+o to expand)

⏺ Good screenshots. Now let me view the GIFs.

⏺ Read 3 files (ctrl+o to expand)

⏺ Here's what was captured. Please inspect the files in showcase/:

  Screenshots:
  - 01_default_ui.png — Full UI with default flat terrain, showing the 3-panel
  layout with geometry sliders, controls, and 3D viewport
  - 02_configured_bumpy.png — Platform configured with your wheely-config.json
  settings (arm=0.92m, splay=30deg, brace=0.67) on bumpy terrain with IK solved

  GIFs (5 seconds each, figure-8 motion on bumpy terrain):
  1. sim_figure8_default.gif — Default camera angle, shows the platform moving
  with arm reaches adapting. The platform is visible up close with metrics chart
   updating.
  2. sim_figure8_zoomed.gif — Zoomed out view, platform has moved further along
  the figure-8 path and appears smaller in frame.
  3. sim_figure8_rotated.gif — Rotated camera angle, similar to zoomed view but
  from a different orbit position.

  The first GIF (sim_figure8_default.gif) shows the most action with the
  platform clearly visible and metrics updating. The zoomed/rotated ones show
  the platform at more distance.

  Which GIF would you like me to include in the final presentation deck?

✻ Baked for 4m 2s

## Human in the loop answer

❯ use sim_figure8_zoomed.gif 
  ⎿  [Image #1]

⏺ Let me read the design docs for additional content to include in the deck.

⏺ Read 2 files (ctrl+o to expand)

⏺ Now I have all the content needed. Let me build the reveal.js deck.

⏺ Write(showcase/showcase.html)
  ⎿  Wrote 401 lines to showcase/showcase.html
       1 <!DOCTYPE html>
       2 <html lang="en">
       3 <head>
       4 <meta charset="utf-8">
       5 <meta name="viewport" content="width=device-width, initial-scale
         =1.0">
       6 <title>Wheely — Self-Leveling Tricycle Platform</title>
       7 <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal
         .js@5.1.0/dist/reveal.css">
       8 <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal
         .js@5.1.0/dist/theme/black.css">
       9 <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highli
         ght.js@11.9.0/styles/atom-one-dark.min.css">
      10 <style>
     … +391 lines (ctrl+o to expand)

⏺ Let me verify the deck renders correctly by taking a screenshot of it.

⏺ Write(showcase/verify_deck.py)
  ⎿  Wrote 28 lines to showcase/verify_deck.py
       1 """Quick verification: screenshot each slide of the showcase dec
         k."""
       2 import asyncio
       3 from pathlib import Path
       4 from playwright.async_api import async_playwright
       5 
       6 SHOWCASE = Path(__file__).parent
       7 DECK = SHOWCASE / "showcase.html"
       8 
       9 async def main():
      10     async with async_playwright() as p:
     … +18 lines (ctrl+o to expand)

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python
      /Users/sergeyk/w/wheely/showcase/verify_deck.py 2>&1)
  ⎿  Total slides: 11
       Slide 1: _verify_slide_01.png
       Slide 2: _verify_slide_02.png
     … +9 lines (ctrl+o to expand)
  ⎿  (timeout 1m)

⏺ Let me verify a few key slides visually.

⏺ Read 4 files (ctrl+o to expand)

⏺ The deck looks good — all 11 slides render correctly. Let me clean up the
  temporary files.

⏺ Bash(rm /Users/sergeyk/w/wheely/showcase/_verify_slide_*.png
      /Users/sergeyk/w/wheely/showcase/verify_deck.py
      /Users/sergeyk/w/wheely/showcase/capture_showcase.py)
  ⎿  Done

⏺ Read 1 file (ctrl+o to expand)

⏺ Done. The showcase deck is at showcase/showcase.html. Here's what's in it:

  11 slides:
  1. Title — Wheely: A Self-Leveling Tricycle Robotic Platform (with tech tags)
  2. The Platform — ASCII diagram + key innovation (parallelogram linkages) +
  use cases
  3. Interactive Simulation — Screenshot of the default UI at 850x600
  4. Terrain Adaptation — Screenshot of configured platform on bumpy terrain
  with IK solved + config metrics
  5. Figure-8 Motion — sim_figure8_zoomed.gif showing the simulation running
  6. Python Architecture — 4-panel grid covering geometry.py, terrain.py,
  kinematics.py, dynamics.py
  7. Simulation Approach — DOFs, physics pipeline, and 4 actuation strategy
  cards
  8. Key Code: Dynamics — Annotated simulate_step showing the 6-phase pipeline
  9. Key Code: Geometry — PlatformConfig dataclass and compute_wheel_positions
  10. Frontend & Communication — Three.js stack, WebSocket protocol, file
  structure
  11. Status & Next Steps — What's working + planned features + quick start

  Open it with: open showcase/showcase.html

✻ Sautéed for 3m 8s

## Force to fix visual issues in the deck 

❯ Can you open @showcase/showcase.html in chrome/playwrite and make sure    
  that all slides look good no text cuts off on 4:3 screen.                 
  ⎿  Read showcase/showcase.html (402 lines)

⏺ Write(showcase/verify_deck.py)
  ⎿  Wrote 31 lines to showcase/verify_deck.py
       1 """Screenshot every slide at 4:3 aspect ratio to check for text 
         cutoff."""
       2 import asyncio
       3 from pathlib import Path
       4 from playwright.async_api import async_playwright
       5 
       6 SHOWCASE = Path(__file__).parent
       7 DECK = SHOWCASE / "showcase.html"
       8 
       9 # 4:3 aspect ratio
      10 WIDTH, HEIGHT = 1024, 768
     … +21 lines (ctrl+o to expand)

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python
      /Users/sergeyk/w/wheely/showcase/verify_deck.py 2>&1)
  ⎿  Total slides: 11 at 1024x768 (4:3)
       Slide 1: _check_slide_01.png
       Slide 2: _check_slide_02.png
     … +9 lines (ctrl+o to expand)
  ⎿  (timeout 1m)

⏺ Read 11 files (ctrl+o to expand)

⏺ I can see significant text cutoff on almost every slide at 4:3. Problems
  include:

  - Slide 2: Right column text clipped, "Use Cases" cut off at bottom
  - Slide 3: Caption text clipped at right edge and bottom
  - Slide 4: Metric labels cut off, terrain presets section gone
  - Slide 5: Caption text clipped
  - Slide 7: Bottom strategy cards and pipeline steps cut off
  - Slides 8-9: Code lines truncated on the right
  - Slide 10: File structure comments clipped, WebSocket protocol list missing
  - Slide 11: Bottom items and "Try It" section cut off

  Let me fix all of these by reducing font sizes, trimming content, and
  adjusting layouts.

⏺ Read 1 file (ctrl+o to expand)

⏺ Now I'll rewrite the entire file with smaller fonts, tighter layouts, and
  trimmed content to fit 4:3.

⏺ Write(showcase/showcase.html)
  ⎿  Added 115 lines, removed 146 lines
      15    }
      16    .reveal { font-family: -apple-system, BlinkMacSystemFont, 'Se
          goe UI', sans-serif; }
      17    .reveal h1, .reveal h2, .reveal h3 { color: var(--r-heading-c
          olor); font-weight: 700; text-transform: none; }
      18 -  .reveal h1 { font-size: 2.2em; }                             
      19 -  .reveal h2 { font-size: 1.5em; }                             
      20 -  .reveal h3 { font-size: 1.1em; color: #4fc3f7; }             
      18 +  .reveal h1 { font-size: 2.0em; }                             
      19 +  .reveal h2 { font-size: 1.3em; margin-bottom: 0.3em; }       
      20 +  .reveal h3 { font-size: 0.8em; color: #4fc3f7; margin-bottom:
         + 0.2em; }                                                      
      21  
      22 -  .reveal .subtitle { color: #aaa; font-size: 0.7em; margin-top
         -: 0.3em; }                                                     
      22 +  .reveal .subtitle { color: #aaa; font-size: 0.65em; margin-to
         +p: 0.3em; }                                                    
      23  
      24 -  .reveal pre { box-shadow: none; font-size: 0.52em; }         
      25 -  .reveal pre code { padding: 16px 20px; border-radius: 8px; ma
         -x-height: 480px; }                                             
      24 +  .reveal pre { box-shadow: none; font-size: 0.40em; width: 100
         +%; }                                                           
      25 +  .reveal pre code { padding: 12px 16px; border-radius: 8px; ma
         +x-height: 420px; }                                             
      26  
      27 -  .reveal .two-col { display: grid; grid-template-columns: 1fr 
         -1fr; gap: 32px; align-items: start; text-align: left; }        
      28 -  .reveal .two-col-wide { display: grid; grid-template-columns:
         - 2fr 1fr; gap: 32px; align-items: start; text-align: left; }   
      29 -  .reveal .two-col-img { display: grid; grid-template-columns: 
         -1fr 1fr; gap: 24px; align-items: center; }                     
      27 +  .reveal .two-col { display: grid; grid-template-columns: 1fr 
         +1fr; gap: 20px; align-items: start; text-align: left; }        
      28  
      31 -  .reveal .tag { display: inline-block; background: #0f3460; co
         -lor: #4fc3f7; padding: 2px 10px; border-radius: 12px; font-size
         -: 0.55em; margin: 2px; }                                       
      32 -  .reveal .tag-red { background: #5c1a2a; color: #e94560; }    
      29 +  .reveal .tag { display: inline-block; background: #0f3460; co
         +lor: #4fc3f7; padding: 2px 8px; border-radius: 12px; font-size:
         + 0.45em; margin: 2px; }                                        
      30  
      34 -  .reveal ul { font-size: 0.75em; line-height: 1.6; }          
      35 -  .reveal li { margin-bottom: 6px; }                           
      36 -  .reveal p { font-size: 0.75em; line-height: 1.5; }           
      31 +  .reveal ul, .reveal ol { font-size: 0.55em; line-height: 1.5;
         + }                                                             
      32 +  .reveal li { margin-bottom: 3px; }                           
      33 +  .reveal p { font-size: 0.55em; line-height: 1.4; }           
      34  
      38 -  .reveal .ascii-art { font-family: 'Courier New', monospace; f
         -ont-size: 0.55em; line-height: 1.3; color: #4fc3f7; background:
         - #0a0a1a; padding: 20px; border-radius: 8px; display: inline-bl
         -ock; text-align: left; }                                       
      35 +  .reveal .ascii-art { font-family: 'Courier New', monospace; f
         +ont-size: 0.42em; line-height: 1.2; color: #4fc3f7; background:
         + #0a0a1a; padding: 14px; border-radius: 8px; display: inline-bl
         +ock; text-align: left; }                                       
      36  
      40 -  .reveal .card { background: #16213e; border-radius: 10px; pad
         -ding: 20px; text-align: left; }                                
      41 -  .reveal .card h3 { margin-top: 0; font-size: 0.9em; }        
      42 -  .reveal .card p, .reveal .card ul { font-size: 0.65em; }     
      37 +  .reveal .card { background: #16213e; border-radius: 8px; padd
         +ing: 10px 12px; text-align: left; }                            
      38 +  .reveal .card h3 { margin-top: 0; margin-bottom: 2px; font-si
         +ze: 0.7em; }                                                   
      39 +  .reveal .card p { font-size: 0.48em; margin: 0; }            
      40  
      44 -  .reveal .metrics-row { display: grid; grid-template-columns: 
         -repeat(4, 1fr); gap: 16px; margin-top: 20px; }                 
      45 -  .reveal .metric { background: #0f3460; border-radius: 8px; pa
         -dding: 12px; text-align: center; }                             
      46 -  .reveal .metric .label { font-size: 0.45em; text-transform: u
         -ppercase; letter-spacing: 1px; color: #888; }                  
      47 -  .reveal .metric .val { font-size: 1.2em; font-weight: 700; co
         -lor: #4ade80; margin-top: 4px; }                               
      41 +  .reveal .metrics-row { display: grid; grid-template-columns: 
         +repeat(4, 1fr); gap: 8px; margin-top: 10px; }                  
      42 +  .reveal .metric { background: #0f3460; border-radius: 6px; pa
         +dding: 8px; text-align: center; }                              
      43 +  .reveal .metric .label { font-size: 0.38em; text-transform: u
         +ppercase; letter-spacing: 0.5px; color: #888; }                
      44 +  .reveal .metric .val { font-size: 0.9em; font-weight: 700; co
         +lor: #4ade80; margin-top: 2px; }                               
      45  
      49 -  .reveal img.screenshot { border-radius: 8px; box-shadow: 0 4p
         -x 24px rgba(0,0,0,0.5); max-height: 420px; }                   
      50 -  .reveal img.gif-demo { border-radius: 8px; box-shadow: 0 4px 
         -24px rgba(0,0,0,0.5); max-height: 400px; }                     
      46 +  .reveal img.screenshot { border-radius: 8px; box-shadow: 0 4p
         +x 24px rgba(0,0,0,0.5); }                                      
      47 +  .reveal img.gif-demo { border-radius: 8px; box-shadow: 0 4px 
         +24px rgba(0,0,0,0.5); }                                        
      48  
      52 -  .reveal .arch-grid { display: grid; grid-template-columns: 1f
         -r 1fr; gap: 16px; }                                            
      53 -  .reveal .arch-box { background: #0f3460; border-radius: 8px; 
         -padding: 14px; text-align: left; }                             
      54 -  .reveal .arch-box h3 { font-size: 0.7em; margin: 0 0 6px; }  
      55 -  .reveal .arch-box p { font-size: 0.55em; margin: 0; color: #c
         -cc; }                                                          
      49 +  .reveal .arch-grid { display: grid; grid-template-columns: 1f
         +r 1fr; gap: 12px; }                                            
      50 +  .reveal .arch-box { background: #0f3460; border-radius: 8px; 
         +padding: 10px 12px; text-align: left; }                        
      51 +  .reveal .arch-box h3 { font-size: 0.6em; margin: 0 0 4px; }  
      52 +  .reveal .arch-box p { font-size: 0.44em; margin: 0; color: #c
         +cc; }                                                          
      53    .reveal .arch-box code { font-size: 0.85em; color: #4fc3f7; }
      57 -                                                               
      58 -  .reveal .footer-note { position: absolute; bottom: 20px; left
         -: 0; right: 0; text-align: center; font-size: 0.4em; color: #55
         -5; }                                                           
      54  </style>
      55  </head>
      56  <body>
      57  <div class="reveal">
      58  <div class="slides">
      59  
      65 -<!-- ==========================================================
         -== -->                                                         
      60  <!-- SLIDE 1: Title -->
      67 -<!-- ==========================================================
         -== -->                                                         
      61  <section>
      62    <h1>Wheely</h1>
      63    <p class="subtitle">A Self-Leveling Tricycle Robotic Platform
          </p>
      71 -  <p style="font-size:0.55em; color:#888; margin-top:1.5em;">  
      64 +  <p style="font-size:0.5em; color:#888; margin-top:1.5em;">   
      65      Kinematic simulation for uneven terrain<br>
      66      <span class="tag">Python</span>
      67      <span class="tag">Three.js</span>
     ...
       70    </p>
       71  </section>
       72  
       80 -<!-- =========================================================
          -=== -->                                                       
       73  <!-- SLIDE 2: The Platform -->
       82 -<!-- =========================================================
          -=== -->                                                       
       74  <section>
       75    <h2>The Platform</h2>
       76    <div class="two-col">
       77      <div>
       78        <pre class="ascii-art">
       88 -         [Wheel A]  (apex)                                    
       89 -            /\                                                
       90 -           /  \                                               
       91 -          /    \                                              
       92 -  arm1   /      \   arm2                                      
       93 -        /  brace \                                            
       94 -       /====[]====\                                           
       95 -      /            \                                          
       96 -[Wheel B]      [Wheel C]                                      
       79 +       [Wheel A]  (apex)                                      
       80 +          /\                                                  
       81 +         /  \                                                 
       82 +        /    \                                                
       83 +arm1   /      \   arm2                                        
       84 +      /  brace \                                              
       85 +     /====[]====\                                             
       86 +    /            \                                            
       87 +[Wheel B]    [Wheel C]                                        
       88        </pre>
       98 -      <p style="margin-top:12px;">Three-wheel-drive, all wheel
          -s independently steered. Two parallelogram arms from an apex w
          -heel to two rear wheels, connected by a cross brace.</p>      
       89 +      <p style="margin-top:8px;">Three-wheel-drive, all wheels
          + independently steered. Two parallelogram arms from apex to re
          +ar wheels, connected by a cross brace.</p>                    
       90      </div>
       91      <div>
       92        <h3>Key Innovation</h3>
     ...
       96          <li>Self-leveling is <em>geometric</em>, not active co
           ntrol</li>
       97          <li>Mid-size prototype: ~1-2m footprint</li>
       98        </ul>
      108 -      <h3 style="margin-top:16px;">Use Cases</h3>             
       99 +      <h3 style="margin-top:10px;">Use Cases</h3>             
      100        <ul>
      101          <li>Forestry and rough ground logistics</li>
      102          <li>Power platform for uneven terrain</li>
     ...
      106    </div>
      107  </section>
      108  
      118 -<!-- =========================================================
          -=== -->                                                       
      109  <!-- SLIDE 3: Simulation UI Screenshot -->
      120 -<!-- =========================================================
          -=== -->                                                       
      110  <section>
      111    <h2>Interactive Simulation</h2>
      123 -  <img src="01_default_ui.png" class="screenshot" alt="Wheely 
          -simulation UI">                                               
      124 -  <p style="margin-top:12px;">Browser-based 3D visualization w
          -ith real-time parameter adjustment. WebSocket streams simulati
          -on frames at ~30fps.</p>                                      
      112 +  <img src="01_default_ui.png" class="screenshot" alt="Wheely 
          +simulation UI" style="max-height:360px;">                     
      113 +  <p style="margin-top:8px;">Browser-based 3D visualization wi
          +th real-time parameter adjustment.<br>WebSocket streams simula
          +tion frames at ~30fps.</p>                                    
      114  </section>
      115  
      127 -<!-- =========================================================
          -=== -->                                                       
      116  <!-- SLIDE 4: Configured on Bumpy Terrain -->
      129 -<!-- =========================================================
          -=== -->                                                       
      117  <section>
      118    <h2>Terrain Adaptation</h2>
      132 -  <div class="two-col-img">                                   
      133 -    <img src="02_configured_bumpy.png" class="screenshot" alt=
          -"Platform on bumpy terrain" style="max-height:360px;">        
      134 -    <div style="text-align:left;">                            
      119 +  <div style="display:grid; grid-template-columns:1fr 1fr; gap
          +:20px; align-items:start; text-align:left;">                  
      120 +    <img src="02_configured_bumpy.png" class="screenshot" alt=
          +"Platform on bumpy terrain" style="max-height:300px; width:100
          +%; object-fit:contain;">                                      
      121 +    <div>                                                     
      122        <h3>IK Solver in Action</h3>
      136 -      <p>Platform configured with custom geometry on sinusoida
          -l bumpy terrain. The inverse kinematics solver finds arm reach
          - angles that place all three wheels on the surface.</p>       
      137 -      <div class="metrics-row" style="grid-template-columns: 1
          -fr 1fr; margin-top: 16px;">                                   
      123 +      <p>IK solver finds arm reach angles that place all three
          + wheels on sinusoidal terrain surface.</p>                    
      124 +      <div class="metrics-row" style="grid-template-columns:1f
          +r 1fr; margin-top:10px;">                                     
      125          <div class="metric"><div class="label">Arm Length</div
           ><div class="val">0.92m</div></div>
      126          <div class="metric"><div class="label">Splay</div><div
            class="val">30&deg;</div></div>
      127          <div class="metric"><div class="label">Brace Pos</div>
           <div class="val">0.67</div></div>
      141 -        <div class="metric"><div class="label">Wheel R</div><d
          -iv class="val">0.14m</div></div>                              
      128 +        <div class="metric"><div class="label">Wheel Radius</d
          +iv><div class="val">0.14m</div></div>                         
      129        </div>
      143 -      <h3 style="margin-top:16px;">Terrain Presets</h3>       
      130 +      <h3 style="margin-top:10px;">6 Terrain Presets</h3>     
      131        <ul>
      145 -        <li>Flat, Gentle/Steep Slope, Cross Slope</li>        
      146 -        <li>Bumpy (sinusoidal)</li>                           
      147 -        <li>Rough (slope + sinusoidal composed)</li>          
      132 +        <li>Flat, Gentle Slope, Steep Slope, Cross Slope</li> 
      133 +        <li>Bumpy (sinusoidal), Rough (composed)</li>         
      134        </ul>
      135      </div>
      136    </div>
      137  </section>
      138  
      153 -<!-- =========================================================
          -=== -->                                                       
      139  <!-- SLIDE 5: Figure-8 Simulation GIF -->
      155 -<!-- =========================================================
          -=== -->                                                       
      140  <section>
      141    <h2>Figure-8 Motion Simulation</h2>
      158 -  <img src="sim_figure8_zoomed.gif" class="gif-demo" alt="Figu
          -re-8 simulation" style="max-height:380px;">                   
      159 -  <p style="margin-top:12px;">Platform traversing a lemniscate
          - path on bumpy terrain with passive dynamics.<br>             
      160 -  Arms adapt reach angles in real time. Stability margin and t
          -ilt metrics tracked continuously.</p>                         
      142 +  <img src="sim_figure8_zoomed.gif" class="gif-demo" alt="Figu
          +re-8 simulation" style="max-height:340px;">                   
      143 +  <p style="margin-top:8px;">Lemniscate path on bumpy terrain 
          +with passive dynamics.<br>                                    
      144 +  Arms adapt reach angles in real time. Stability margin and t
          +ilt tracked continuously.</p>                                 
      145  </section>
      146  
      163 -<!-- =========================================================
          -=== -->                                                       
      147  <!-- SLIDE 6: Python Architecture -->
      165 -<!-- =========================================================
          -=== -->                                                       
      148  <section>
      149    <h2>Python Architecture</h2>
      150    <div class="arch-grid">
      151      <div class="arch-box">
      152        <h3>geometry.py</h3>
      171 -      <p>Parametric platform geometry. <code>PlatformConfig</c
          -ode> dataclass with all tunable dimensions. Computes wheel pos
          -itions, brace endpoints, and tilt rotation matrices.</p>      
      153 +      <p><code>PlatformConfig</code> dataclass with all tunabl
          +e dimensions. Computes wheel positions, brace endpoints, tilt 
          +rotation matrices.</p>                                        
      154      </div>
      155      <div class="arch-box">
      156        <h3>terrain.py</h3>
      175 -      <p>Pluggable terrain models: <code>FlatTerrain</code>, <
          -code>SlopeTerrain</code>, <code>SinusoidalTerrain</code>, <cod
          -e>ComposedTerrain</code>. All implement <code>height(x,y)</cod
          -e> and <code>normal(x,y)</code>.</p>                          
      157 +      <p>Pluggable terrain models: <code>FlatTerrain</code>, <
          +code>SlopeTerrain</code>, <code>SinusoidalTerrain</code>, <cod
          +e>ComposedTerrain</code>. All implement <code>height(x,y)</cod
          +e>.</p>                                                       
      158      </div>
      159      <div class="arch-box">
      160        <h3>kinematics.py</h3>
      179 -      <p>Forward &amp; inverse kinematics. IK uses <code>scipy
          -.optimize</code> to solve arm reach angles that place wheels o
          -n terrain. Stability margin via support triangle analysis.</p>
      161 +      <p>Forward &amp; inverse kinematics. IK uses <code>scipy
          +.optimize</code> to solve arm reach angles. Stability margin v
          +ia support triangle.</p>                                      
      162      </div>
      163      <div class="arch-box">
      164        <h3>dynamics.py</h3>
      183 -      <p>Time integration with semi-implicit Euler. Gravity to
          -rques, terrain contact penalty forces, hard surface clamping, 
          -and pluggable actuation strategies.</p>                       
      165 +      <p>Semi-implicit Euler integration. Gravity torques, con
          +tact penalty forces, hard surface clamping, pluggable actuatio
          +n strategies.</p>                                             
      166      </div>
      167    </div>
      186 -  <div style="margin-top:16px;">                              
      168 +  <div style="margin-top:12px;">                              
      169      <span class="tag">NumPy</span>
      170      <span class="tag">SciPy</span>
      171      <span class="tag">FastAPI</span>
     ...
      174    </div>
      175  </section>
      176  
      195 -<!-- =========================================================
          -=== -->                                                       
      177  <!-- SLIDE 7: Simulation Approach -->
      197 -<!-- =========================================================
          -=== -->                                                       
      178  <section>
      179    <h2>Simulation Approach</h2>
      180    <div class="two-col">
      181      <div>
      182        <h3>Degrees of Freedom</h3>
      183        <ul>
      204 -        <li><strong>tilt_pitch</strong> &mdash; tips platform 
          -forward/backward</li>                                         
      205 -        <li><strong>tilt_roll</strong> &mdash; tips platform l
          -eft/right</li>                                                
      206 -        <li><strong>reach_b, reach_c</strong> &mdash; independ
          -ent arm extension</li>                                        
      207 -        <li>Parallelogram constraint: all shafts stay parallel
          -</li>                                                         
      184 +        <li><strong>tilt_pitch</strong> &mdash; forward/backwa
          +rd</li>                                                       
      185 +        <li><strong>tilt_roll</strong> &mdash; left/right</li>
      186 +        <li><strong>reach_b, reach_c</strong> &mdash; arm exte
          +nsion</li>                                                    
      187 +        <li>Parallelogram: all shafts parallel</li>           
      188        </ul>
      209 -      <h3 style="margin-top:16px;">Physics Pipeline</h3>      
      210 -      <ol style="font-size:0.7em;">                           
      211 -        <li>Apply prescribed motion (stationary or figure-8)</
          -li>                                                           
      189 +      <h3 style="margin-top:8px;">Physics Pipeline</h3>       
      190 +      <ol>                                                    
      191 +        <li>Apply prescribed motion</li>                      
      192          <li>Compute strategy torques (4-tuple)</li>
      213 -        <li>Compute gravity torques on tilt axes</li>         
      214 -        <li>Compute terrain contact torques per arm</li>      
      193 +        <li>Gravity torques on tilt axes</li>                 
      194 +        <li>Terrain contact torques per arm</li>              
      195          <li>Semi-implicit Euler integration</li>
      216 -        <li>Hard clamp: reach adjustment &rarr; tilt adjustmen
          -t</li>                                                        
      196 +        <li>Hard clamp: reach &rarr; tilt adjustment</li>     
      197        </ol>
      198      </div>
      199      <div>
      200        <h3>Actuation Strategies</h3>
      221 -      <div class="card" style="margin-bottom:10px;">          
      201 +      <div class="card" style="margin-bottom:6px;">           
      202          <h3>Passive</h3>
      223 -        <p>Zero torque. Arms settle under gravity + terrain co
          -ntact. Tilt drifts freely.</p>                                
      203 +        <p>Zero torque. Arms settle via gravity + contact.</p>
      204        </div>
      225 -      <div class="card" style="margin-bottom:10px;">          
      205 +      <div class="card" style="margin-bottom:6px;">           
      206          <h3>Active Arms (PD)</h3>
      227 -        <p>PD controller on both tilt axes. Two actuators cont
          -rol pitch and roll directly.</p>                              
      207 +        <p>PD on both tilt axes. Two actuators control pitch a
          +nd roll.</p>                                                  
      208        </div>
      229 -      <div class="card" style="margin-bottom:10px;">          
      209 +      <div class="card" style="margin-bottom:6px;">           
      210          <h3>Active Brace (PD)</h3>
      231 -        <p>Single brace actuator controls roll directly. Pitch
          - correction is indirect.</p>                                  
      211 +        <p>Single brace actuator. Roll directly, pitch indirec
          +tly.</p>                                                      
      212        </div>
      213        <div class="card">
      214          <h3>Spring-Damper</h3>
      235 -        <p>Spring return + viscous damping on arm reaches arou
          -nd rest position.</p>                                         
      215 +        <p>Spring return + damping on arm reaches.</p>        
      216        </div>
      217      </div>
      218    </div>
      219  </section>
      220  
      241 -<!-- =========================================================
          -=== -->                                                       
      221  <!-- SLIDE 8: Key Code — Dynamics -->
      243 -<!-- =========================================================
          -=== -->                                                       
      222  <section>
      223    <h2>Key Code: Dynamics Step</h2>
      246 -  <pre><code class="language-python">def simulate_step(state, 
          -config, terrain, strategy, dt=0.01, motion="stationary"):     
      247 -    # 1. Prescribed motion (figure-8 lemniscate path)         
      224 +  <pre><code class="language-python">def simulate_step(state, 
          +config, terrain, strategy,                                    
      225 +                   dt=0.01, motion="stationary"):             
      226      if motion == "figure8":
      249 -        state = figure8_motion(state, dt)                     
      227 +        state = figure8_motion(state, dt)       # lemniscate p
          +ath                                                           
      228  
      251 -    # 2. Strategy torques: (pitch, roll, reach_b, reach_c)    
      252 -    torques = strategy.compute_torques(state)                 
      229 +    torques = strategy.compute_torques(state)    # (pitch, rol
          +l, b, c)                                                      
      230  
      254 -    # 3. Gravity torques on tilt axes                         
      231 +    # Gravity torques on tilt axes                            
      232      grav_pitch = -M * G * L_COG * sin(state.tilt_pitch)
      233      grav_roll  = -M * G * L_COG * sin(state.tilt_roll)
      234  
      258 -    # 4. Terrain contact per arm (penalty spring + damping)   
      259 -    contact_b, _ = _compute_contact_for_arm(config, terrain, s
          -tate, "B")                                                    
      260 -    contact_c, _ = _compute_contact_for_arm(config, terrain, s
          -tate, "C")                                                    
      235 +    # Terrain contact per arm (penalty spring + damping)      
      236 +    contact_b, _ = _compute_contact_for_arm(..., "B")         
      237 +    contact_c, _ = _compute_contact_for_arm(..., "C")         
      238  
      262 -    # 5. Semi-implicit Euler integration                      
      239 +    # Semi-implicit Euler integration                         
      240      acc_pitch = net_pitch / tilt_inertia
      241      new_pitch_vel = state.tilt_pitch_velocity + acc_pitch * dt
      242      new_tilt_pitch = state.tilt_pitch + new_pitch_vel * dt
      243  
      267 -    # 6. Hard clamp: no terrain penetration                   
      268 -    #    Phase 1: adjust reach (brentq root-finding)          
      269 -    #    Phase 2: adjust tilt if reach at limit               
      244 +    # Hard clamp: no terrain penetration                      
      245 +    #   Phase 1: adjust reach (brentq root-finding)           
      246 +    #   Phase 2: adjust tilt if reach at limit                
      247      return new_state, metrics</code></pre>
      248  </section>
      249  
      273 -<!-- =========================================================
          -=== -->                                                       
      250  <!-- SLIDE 9: Key Code — Geometry -->
      275 -<!-- =========================================================
          -=== -->                                                       
      251  <section>
      252    <h2>Key Code: Parametric Geometry</h2>
      253    <pre><code class="language-python">@dataclass
      254  class PlatformConfig:
      280 -    arm_length: float = 0.8           # Length of each paralle
          -logram arm (m)                                                
      281 -    arm_splay_angle: float = rad(40)  # Angle from centerline 
          -(top-down)                                                    
      282 -    brace_position: float = 0.5       # Cross brace attach poi
          -nt along arm                                                  
      283 -    wheel_radius: float = 0.15        # Wheel radius (m)      
      284 -    clearance: float = 0.03           # Gap above wheel to arm
          - (m)                                                          
      285 -    arm_height: float = 0.06          # Parallelogram arm heig
          -ht (m)                                                        
      255 +    arm_length: float = 0.8        # parallelogram arm (m)    
      256 +    arm_splay_angle: float = rad(40)  # from centerline       
      257 +    brace_position: float = 0.5    # cross brace attach point 
      258 +    wheel_radius: float = 0.15     # wheel radius (m)         
      259 +    clearance: float = 0.03        # gap above wheel (m)      
      260 +    arm_height: float = 0.06       # arm height (m)           
      261  
      287 -def compute_wheel_positions(config, tilt_pitch, tilt_roll, arm
          -_reaches):                                                    
      262 +def compute_wheel_positions(config, tilt_pitch, tilt_roll,    
      263 +                             arm_reaches):                    
      264      """Compute wheel A, B, C positions in body frame."""
      289 -    R = tilt_rotation_matrix(tilt_pitch, tilt_roll)  # Ry(pitc
          -h) @ Rx(roll)                                                 
      265 +    R = tilt_rotation_matrix(tilt_pitch, tilt_roll)           
      266  
      267      def _arm_endpoint(reach, splay_sign):
      268          dx = config.arm_length * cos(splay) * cos(reach)
     ...
      275      return {"A": wheel_a, "B": wheel_b, "C": wheel_c}</code></
           pre>
      276  </section>
      277  
      302 -<!-- =========================================================
          -=== -->                                                       
      278  <!-- SLIDE 10: Frontend Stack -->
      304 -<!-- =========================================================
          -=== -->                                                       
      279  <section>
      280    <h2>Frontend &amp; Communication</h2>
      281    <div class="two-col">
     ...
      283        <h3>Three.js Visualization</h3>
      284        <ul>
      285          <li>Real-time 3D scene with orbit camera</li>
      312 -        <li>Platform model built from parametric config</li>  
      286 +        <li>Platform model from parametric config</li>        
      287          <li>Terrain mesh from heightmap grid</li>
      288          <li>Support triangle and stability overlay</li>
      315 -        <li>Live metrics chart (canvas-based, no deps)</li>   
      289 +        <li>Live metrics chart (canvas, no deps)</li>         
      290        </ul>
      317 -      <h3 style="margin-top:16px;">WebSocket Protocol</h3>    
      291 +      <h3 style="margin-top:8px;">WebSocket Protocol</h3>     
      292        <ul>
      319 -        <li><code>set_config</code> &mdash; geometry parameter
          -s</li>                                                        
      320 -        <li><code>set_terrain</code> / <code>set_strategy</cod
          -e></li>                                                       
      321 -        <li><code>set_motion</code> &mdash; stationary or figu
          -re-8</li>                                                     
      322 -        <li><code>start_sim</code> / <code>stop_sim</code></li
          ->                                                             
      323 -        <li><code>solve_ik</code> &mdash; snap wheels to terra
          -in</li>                                                       
      324 -        <li>Server streams <code>frame</code> messages at ~30f
          -ps</li>                                                       
      293 +        <li><code>set_config</code>, <code>set_terrain</code>,
          + <code>set_strategy</code></li>                               
      294 +        <li><code>set_motion</code> &mdash; stationary / figur
          +e-8</li>                                                      
      295 +        <li><code>start_sim</code> / <code>stop_sim</code> / <
          +code>solve_ik</code></li>                                     
      296 +        <li>Server streams <code>frame</code> at ~30fps</li>  
      297        </ul>
      298      </div>
      299      <div>
      300        <h3>File Structure</h3>
      301        <pre><code class="language-text">web/
      330 -  index.html        # Layout, sliders, info bar               
      331 -  simulation.js     # WebSocket, animation loop               
      332 -  scene.js          # Three.js scene setup                    
      333 -  platform-viz.js   # 3D platform from params                 
      334 -  terrain-viz.js    # Terrain mesh rendering                  
      335 -  controls.js       # Slider bindings                         
      336 -  metrics-chart.js  # Live time-series chart</code></pre>     
      337 -      <h3 style="margin-top:16px;">Tech Choices</h3>          
      302 +  index.html       # Layout, sliders                          
      303 +  simulation.js    # WS, animation loop                       
      304 +  scene.js         # Three.js setup                           
      305 +  platform-viz.js  # 3D platform                              
      306 +  terrain-viz.js   # Terrain mesh                             
      307 +  controls.js      # Slider bindings                          
      308 +  metrics-chart.js # Time-series chart</code></pre>           
      309 +      <h3 style="margin-top:8px;">Tech Choices</h3>           
      310        <ul>
      339 -        <li>Vanilla JS &mdash; no framework overhead</li>     
      340 -        <li>ES modules with importmap for Three.js</li>       
      311 +        <li>Vanilla JS, ES modules + importmap</li>           
      312          <li>CSS Grid layout, dark theme</li>
      313          <li>FastAPI serves static + WebSocket</li>
      314        </ul>
     ...
      316    </div>
      317  </section>
      318  
      348 -<!-- =========================================================
          -=== -->                                                       
      319  <!-- SLIDE 11: What's Next -->
      350 -<!-- =========================================================
          -=== -->                                                       
      320  <section>
      321    <h2>Status &amp; Next Steps</h2>
      322    <div class="two-col">
     ...
      328          <li>Forward &amp; inverse kinematics</li>
      329          <li>4 actuation strategies with live comparison</li>
      330          <li>Figure-8 prescribed motion</li>
      362 -        <li>Two-axis tilt dynamics with hard surface constrain
          -t</li>                                                        
      331 +        <li>Two-axis tilt dynamics, hard surface clamp</li>   
      332          <li>Stability margin tracking</li>
      333          <li>Config save/load (JSON)</li>
      334        </ul>
     ...
      337        <h3>Planned</h3>
      338        <ul>
      339          <li>Driven motion: steering + speed control</li>
      371 -        <li>Path planning and waypoint following</li>         
      340 +        <li>Path planning and waypoints</li>                  
      341          <li>Motor selection and power budget</li>
      342          <li>Deformable terrain (mud, soft ground)</li>
      343          <li>Physical prototype construction</li>
      344        </ul>
      376 -      <h3 style="margin-top:16px;">Try It</h3>                
      345 +      <h3 style="margin-top:10px;">Try It</h3>                
      346        <pre style="text-align:left;"><code class="language-bash
           ">pip install -e ".[dev]"
      347  uvicorn wheely.server:app --port 8000
      348  # Open http://localhost:8000</code></pre>
     ...
      350    </div>
      351  </section>
      352  
      384 -</div><!-- /slides -->                                        
      385 -</div><!-- /reveal -->                                        
      353 +</div>                                                        
      354 +</div>                                                        
      355  
      356  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist
           /reveal.js"></script>
      357  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plug
           in/highlight/highlight.js"></script>

⏺ Now let me re-run the verification at 4:3.

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python
      /Users/sergeyk/w/wheely/showcase/verify_deck.py 2>&1)
  ⎿  Total slides: 11 at 1024x768 (4:3)
       Slide 1: _check_slide_01.png
       Slide 2: _check_slide_02.png
     … +9 lines (ctrl+o to expand)
  ⎿  (timeout 1m)

⏺ Read 6 files (ctrl+o to expand)

⏺ Slides 1, 3, 5 look good. But I can see clipping on slides 2, 4, and 6 still.
  Let me check the rest.

⏺ Read 5 files (ctrl+o to expand)

⏺ Remaining clipping issues:
  - Slide 2: "keep all whe..." right edge
  - Slide 4: "place a...", metrics "WHEEL RADIUS" clipped
  - Slide 6: "SlopeTerra...", "implemen..." in terrain.py box
  - Slide 7: "pitc...", "indirec..." in strategy cards
  - Slide 8: Bottom code lines cut off
  - Slide 9: Bottom code line cut off
  - Slide 11: "cont...", "ground..." clipped in Planned column

  I need to increase Reveal margins and shorten the clipping text.

⏺ Update(showcase/showcase.html)
  ⎿  Added 1 line
      363    progress: true,
      364    center: true,
      365    transition: 'slide',
      366 +  margin: 0.08,                                               
      367    plugins: [RevealHighlight],
      368  });
      369  </script>

⏺ Now fix the clipping text on individual slides.

⏺ Update(showcase/showcase.html)
  ⎿  Added 3 lines, removed 3 lines
      91      <div>
      92        <h3>Key Innovation</h3>
      93        <ul>
      94 -        <li><strong>Parallelogram linkages</strong> keep all wh
         -eel shafts parallel</li>                                       
      95 -        <li>Cargo platform stays level as arms conform to terra
         -in</li>                                                        
      96 -        <li>Self-leveling is <em>geometric</em>, not active con
         -trol</li>                                                      
      94 +        <li><strong>Parallelogram linkages</strong> keep wheel 
         +shafts parallel</li>                                           
      95 +        <li>Cargo platform stays level as arms adapt</li>      
      96 +        <li>Self-leveling is <em>geometric</em>, not active</li
         +>                                                              
      97          <li>Mid-size prototype: ~1-2m footprint</li>
      98        </ul>
      99        <h3 style="margin-top:10px;">Use Cases</h3>

⏺ Update(showcase/showcase.html)
  ⎿  Added 5 lines, removed 5 lines
      120      <img src="02_configured_bumpy.png" class="screenshot" alt=
           "Platform on bumpy terrain" style="max-height:300px; width:100
           %; object-fit:contain;">
      121      <div>
      122        <h3>IK Solver in Action</h3>
      123 -      <p>IK solver finds arm reach angles that place all three
          - wheels on sinusoidal terrain surface.</p>                    
      123 +      <p>IK solver finds arm reach angles placing all wheels o
          +n the terrain surface.</p>                                    
      124        <div class="metrics-row" style="grid-template-columns:1f
           r 1fr; margin-top:10px;">
      125 -        <div class="metric"><div class="label">Arm Length</div
          -><div class="val">0.92m</div></div>                           
      125 +        <div class="metric"><div class="label">Arm</div><div c
          +lass="val">0.92m</div></div>                                  
      126          <div class="metric"><div class="label">Splay</div><div
            class="val">30&deg;</div></div>
      127 -        <div class="metric"><div class="label">Brace Pos</div>
          -<div class="val">0.67</div></div>                             
      128 -        <div class="metric"><div class="label">Wheel Radius</d
          -iv><div class="val">0.14m</div></div>                         
      127 +        <div class="metric"><div class="label">Brace</div><div
          + class="val">0.67</div></div>                                 
      128 +        <div class="metric"><div class="label">Wheel</div><div
          + class="val">0.14m</div></div>                                
      129        </div>
      130        <h3 style="margin-top:10px;">6 Terrain Presets</h3>
      131        <ul>
      132 -        <li>Flat, Gentle Slope, Steep Slope, Cross Slope</li> 
      132 +        <li>Flat, Gentle/Steep/Cross Slope</li>               
      133          <li>Bumpy (sinusoidal), Rough (composed)</li>
      134        </ul>
      135      </div>

⏺ Update(showcase/showcase.html)
  ⎿  Added 1 line, removed 1 line
      154      </div>
      155      <div class="arch-box">
      156        <h3>terrain.py</h3>
      157 -      <p>Pluggable terrain models: <code>FlatTerrain</code>, <
          -code>SlopeTerrain</code>, <code>SinusoidalTerrain</code>, <cod
          -e>ComposedTerrain</code>. All implement <code>height(x,y)</cod
          -e>.</p>                                                       
      157 +      <p>Pluggable terrain: <code>Flat</code>, <code>Slope</co
          +de>, <code>Sinusoidal</code>, <code>Composed</code>. All imple
          +ment <code>height(x,y)</code> and <code>normal(x,y)</code>.</p
          +>                                                             
      158      </div>
      159      <div class="arch-box">
      160        <h3>kinematics.py</h3>

⏺ Update(showcase/showcase.html)
  ⎿  Added 2 lines, removed 2 lines
      204        </div>
      205        <div class="card" style="margin-bottom:6px;">
      206          <h3>Active Arms (PD)</h3>
      207 -        <p>PD on both tilt axes. Two actuators control pitch a
          -nd roll.</p>                                                  
      207 +        <p>PD on both tilt axes. Controls pitch and roll.</p> 
      208        </div>
      209        <div class="card" style="margin-bottom:6px;">
      210          <h3>Active Brace (PD)</h3>
      211 -        <p>Single brace actuator. Roll directly, pitch indirec
          -tly.</p>                                                      
      211 +        <p>Brace actuator. Roll direct, pitch indirect.</p>   
      212        </div>
      213        <div class="card">
      214          <h3>Spring-Damper</h3>

⏺ Now fix the code slides — trim bottom lines and reduce font size slightly
  more.

⏺ Update(showcase/showcase.html)
  ⎿  Added 2 lines, removed 2 lines
      21  
      22    .reveal .subtitle { color: #aaa; font-size: 0.65em; margin-to
          p: 0.3em; }
      23  
      24 -  .reveal pre { box-shadow: none; font-size: 0.40em; width: 100
         -%; }                                                           
      25 -  .reveal pre code { padding: 12px 16px; border-radius: 8px; ma
         -x-height: 420px; }                                             
      24 +  .reveal pre { box-shadow: none; font-size: 0.38em; width: 100
         +%; }                                                           
      25 +  .reveal pre code { padding: 10px 14px; border-radius: 8px; ma
         +x-height: 400px; }                                             
      26  
      27    .reveal .two-col { display: grid; grid-template-columns: 1fr 
          1fr; gap: 20px; align-items: start; text-align: left; }
      28  

⏺ Now fix slide 11 — shorten the clipped items in the Planned column.

⏺ Update(showcase/showcase.html)
  ⎿  Added 2 lines, removed 2 lines
      336      <div>
      337        <h3>Planned</h3>
      338        <ul>
      339 -        <li>Driven motion: steering + speed control</li>      
      339 +        <li>Driven motion: steering + speed</li>              
      340          <li>Path planning and waypoints</li>
      341          <li>Motor selection and power budget</li>
      342 -        <li>Deformable terrain (mud, soft ground)</li>        
      342 +        <li>Deformable terrain (mud, sand)</li>               
      343          <li>Physical prototype construction</li>
      344        </ul>
      345        <h3 style="margin-top:10px;">Try It</h3>

⏺ Now re-verify.

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python
      /Users/sergeyk/w/wheely/showcase/verify_deck.py 2>&1)
  ⎿  Total slides: 11 at 1024x768 (4:3)
       Slide 1: _check_slide_01.png
       Slide 2: _check_slide_02.png
     … +9 lines (ctrl+o to expand)
  ⎿  (timeout 1m)

⏺ Read 8 files (ctrl+o to expand)

⏺ Much better. A few remaining clips to fix:

  - Slide 2: "as arms ada..." still clipped
  - Slide 4: "Rough (composed..." clipped at bottom right
  - Slide 8: Last 2 code lines cut off at bottom
  - Slide 9: Last 2 code lines cut off at bottom

⏺ Update(showcase/showcase.html)
  ⎿  Added 1 line, removed 1 line
      92        <h3>Key Innovation</h3>
      93        <ul>
      94          <li><strong>Parallelogram linkages</strong> keep wheel 
          shafts parallel</li>
      95 -        <li>Cargo platform stays level as arms adapt</li>      
      95 +        <li>Platform stays level as arms adapt</li>            
      96          <li>Self-leveling is <em>geometric</em>, not active</li
          >
      97          <li>Mid-size prototype: ~1-2m footprint</li>
      98        </ul>

⏺ Update(showcase/showcase.html)
  ⎿  Added 1 line, removed 1 line
      130        <h3 style="margin-top:10px;">6 Terrain Presets</h3>
      131        <ul>
      132          <li>Flat, Gentle/Steep/Cross Slope</li>
      133 -        <li>Bumpy (sinusoidal), Rough (composed)</li>         
      133 +        <li>Bumpy (sinusoidal), Rough (mixed)</li>            
      134        </ul>
      135      </div>
      136    </div>

⏺ Now trim the code blocks on slides 8 and 9 to remove the lines that get cut
  off.

⏺ Update(showcase/showcase.html)
  ⎿  Added 1 line, removed 3 lines
      241      new_pitch_vel = state.tilt_pitch_velocity + acc_pitch * dt
      242      new_tilt_pitch = state.tilt_pitch + new_pitch_vel * dt
      243  
      244 -    # Hard clamp: no terrain penetration                      
      245 -    #   Phase 1: adjust reach (brentq root-finding)           
      246 -    #   Phase 2: adjust tilt if reach at limit                
      244 +    # Hard clamp: adjust reach (brentq), then tilt if needed  
      245      return new_state, metrics</code></pre>
      246  </section>
      247  

⏺ Update(showcase/showcase.html)
  ⎿  Added 3 lines, removed 3 lines
      268          dz = -config.arm_length * sin(reach)
      269          return R @ np.array([dx, dy, dz])
      270  
      271 -    wheel_b = wheel_a + _arm_endpoint(reach_b, -1.0)          
      272 -    wheel_c = wheel_a + _arm_endpoint(reach_c, +1.0)          
      273 -    return {"A": wheel_a, "B": wheel_b, "C": wheel_c}</code></
          -pre>                                                          
      271 +    wheel_b = wheel_a + _arm_endpoint(reach_b, -1.0)  # right 
      272 +    wheel_c = wheel_a + _arm_endpoint(reach_c, +1.0)  # left  
      273 +    return {"A": wheel_a, "B": wheel_b, "C": wheel_c}  </code>
          +</pre>                                                        
      274  </section>
      275  
      276  <!-- SLIDE 10: Frontend Stack -->

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python
      /Users/sergeyk/w/wheely/showcase/verify_deck.py 2>&1)
  ⎿  Total slides: 11 at 1024x768 (4:3)
       Slide 1: _check_slide_01.png
       Slide 2: _check_slide_02.png
     … +9 lines (ctrl+o to expand)
  ⎿  (timeout 1m)

⏺ Read 4 files (ctrl+o to expand)

⏺ Slides 2 and 4 are fixed. Slides 8 and 9 still have the last line partially
  cut off at the bottom. I need to trim a bit more from each code block.

⏺ Update(showcase/showcase.html)
  ⎿  Added 2 lines, removed 2 lines
      241      new_pitch_vel = state.tilt_pitch_velocity + acc_pitch * dt
      242      new_tilt_pitch = state.tilt_pitch + new_pitch_vel * dt
      243  
      244 -    # Hard clamp: adjust reach (brentq), then tilt if needed  
      245 -    return new_state, metrics</code></pre>                    
      244 +    # Hard clamp: adjust reach (brentq), then tilt            
      245 +    return new_state, metrics  </code></pre>                  
      246  </section>
      247  
      248  <!-- SLIDE 9: Key Code — Geometry -->

⏺ The issue is the code block's max-height. Let me reduce the code blocks to
  fewer lines rather than relying on overflow.

⏺ Update(showcase/showcase.html)
  ⎿  Added 6 lines, removed 9 lines
      233      grav_roll  = -M * G * L_COG * sin(state.tilt_roll)
      234  
      235      # Terrain contact per arm (penalty spring + damping)
      236 -    contact_b, _ = _compute_contact_for_arm(..., "B")         
      237 -    contact_c, _ = _compute_contact_for_arm(..., "C")         
      236 +    contact_b = _compute_contact_for_arm(config, terrain, stat
          +e, "B")                                                       
      237 +    contact_c = _compute_contact_for_arm(config, terrain, stat
          +e, "C")                                                       
      238  
      239 -    # Semi-implicit Euler integration                         
      240 -    acc_pitch = net_pitch / tilt_inertia                      
      241 -    new_pitch_vel = state.tilt_pitch_velocity + acc_pitch * dt
      242 -    new_tilt_pitch = state.tilt_pitch + new_pitch_vel * dt    
      243 -                                                              
      244 -    # Hard clamp: adjust reach (brentq), then tilt            
      245 -    return new_state, metrics  </code></pre>                  
      239 +    # Semi-implicit Euler → hard clamp (brentq) → return      
      240 +    new_pitch_vel = pitch_vel + (net_pitch / inertia) * dt    
      241 +    new_tilt_pitch = tilt_pitch + new_pitch_vel * dt          
      242 +    return new_state, metrics</code></pre>                    
      243  </section>
      244  
      245  <!-- SLIDE 9: Key Code — Geometry -->

⏺ Update(showcase/showcase.html)
  ⎿  Added 7 lines, removed 8 lines
      256  
      257  def compute_wheel_positions(config, tilt_pitch, tilt_roll,
      258                               arm_reaches):
      259 -    """Compute wheel A, B, C positions in body frame."""      
      260 -    R = tilt_rotation_matrix(tilt_pitch, tilt_roll)           
      259 +    R = tilt_rotation_matrix(tilt_pitch, tilt_roll)  # Ry @ Rx
      260  
      261      def _arm_endpoint(reach, splay_sign):
      263 -        dx = config.arm_length * cos(splay) * cos(reach)      
      264 -        dy = config.arm_length * splay_sign * sin(splay) * cos
          -(reach)                                                       
      265 -        dz = -config.arm_length * sin(reach)                  
      262 +        dx = arm_length * cos(splay) * cos(reach)             
      263 +        dy = arm_length * splay_sign * sin(splay) * cos(reach)
      264 +        dz = -arm_length * sin(reach)                         
      265          return R @ np.array([dx, dy, dz])
      266  
      268 -    wheel_b = wheel_a + _arm_endpoint(reach_b, -1.0)  # right 
      269 -    wheel_c = wheel_a + _arm_endpoint(reach_c, +1.0)  # left  
      270 -    return {"A": wheel_a, "B": wheel_b, "C": wheel_c}  </code>
          -</pre>                                                        
      267 +    return {"A": origin,                                      
      268 +            "B": origin + _arm_endpoint(reach_b, -1.0),       
      269 +            "C": origin + _arm_endpoint(reach_c, +1.0)}</code>
          +</pre>                                                        
      270  </section>
      271  
      272  <!-- SLIDE 10: Frontend Stack -->

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python
      /Users/sergeyk/w/wheely/showcase/verify_deck.py 2>&1)
  ⎿  Total slides: 11 at 1024x768 (4:3)
       Slide 1: _check_slide_01.png
       Slide 2: _check_slide_02.png
     … +9 lines (ctrl+o to expand)
  ⎿  (timeout 1m)

⏺ Read 2 files (ctrl+o to expand)

⏺ Slide 8 is perfect now. Slide 9 still has the last line ("C": ...) cut off.
  Let me compact the return statement.

⏺ Update(showcase/showcase.html)
  ⎿  Added 3 lines, removed 3 lines
      264          dz = -arm_length * sin(reach)
      265          return R @ np.array([dx, dy, dz])
      266  
      267 -    return {"A": origin,                                      
      268 -            "B": origin + _arm_endpoint(reach_b, -1.0),       
      269 -            "C": origin + _arm_endpoint(reach_c, +1.0)}</code>
          -</pre>                                                        
      267 +    b = origin + _arm_endpoint(reach_b, -1.0)                 
      268 +    c = origin + _arm_endpoint(reach_c, +1.0)                 
      269 +    return {"A": origin, "B": b, "C": c}</code></pre>         
      270  </section>
      271  
      272  <!-- SLIDE 10: Frontend Stack -->

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python
      /Users/sergeyk/w/wheely/showcase/verify_deck.py 2>&1)
  ⎿  Total slides: 11 at 1024x768 (4:3)
       Slide 1: _check_slide_01.png
       Slide 2: _check_slide_02.png
     … +9 lines (ctrl+o to expand)
  ⎿  (timeout 1m)

⏺ Read 1 file (ctrl+o to expand)

⏺ Still one line short. Let me trim a field from the dataclass to save a line.

⏺ Update(showcase/showcase.html)
  ⎿  File must be read first

⏺ Read 1 file (ctrl+o to expand)

⏺ Update(showcase/showcase.html)
  ⎿  Removed 1 line
      252      brace_position: float = 0.5    # cross brace attach point
      253      wheel_radius: float = 0.15     # wheel radius (m)
      254      clearance: float = 0.03        # gap above wheel (m)
      255 -    arm_height: float = 0.06       # arm height (m)           
      255  
      256  def compute_wheel_positions(config, tilt_pitch, tilt_roll,
      257                               arm_reaches):

⏺ Bash(/Users/sergeyk/w/wheely/.venv/bin/python
      /Users/sergeyk/w/wheely/showcase/verify_deck.py 2>&1)
  ⎿  Total slides: 11 at 1024x768 (4:3)
       Slide 1: _check_slide_01.png
       Slide 2: _check_slide_02.png
     … +9 lines (ctrl+o to expand)
  ⎿  (timeout 1m)

⏺ Read 1 file (ctrl+o to expand)

⏺ All 11 slides now fit cleanly at 4:3 (1024x768) with no text cutoff. Let me
  clean up the temp files.

⏺ Bash(rm /Users/sergeyk/w/wheely/showcase/_check_slide_*.png
      /Users/sergeyk/w/wheely/showcase/verify_deck.py)
  ⎿  Done

⏺ All 11 slides verified at 4:3 — no text cutoff on any slide. The deck is at
  showcase/showcase.html.

✻ Worked for 14m 41s

❯ showcase/showcase.html Make it self-containing by embedding all images    
  into XML itself and clean images from directory once you do that.         

⏺ Read 1 file (ctrl+o to expand)

⏺ Now let me base64-encode the three image files and embed them as data URIs.

⏺ Bash(base64 -i /Users/sergeyk/w/wheely/showcase/01_default_ui.png | wc -c)
  ⎿  174533

⏺ Bash(base64 -i /Users/sergeyk/w/wheely/showcase/02_configured_bumpy.png | wc
      -c)
  ⎿  332393

⏺ Bash(base64 -i /Users/sergeyk/w/wheely/showcase/sim_figure8_zoomed.gif | wc
      -c)
  ⎿  604929

⏺ The images total ~1.1MB in base64 — fine for embedding. Let me write a script
  to do the replacement cleanly.

⏺ Bash(cd /Users/sergeyk/w/wheely/showcase &&
      /Users/sergeyk/w/wheely/.venv/bin/python3 -c "
      import base64, re…)
  ⎿  Embedded 01_default_ui.png: 174532 chars
     Embedded 02_configured_bumpy.png: 332392 chars
     Embedded sim_figure8_zoomed.gif: 604928 chars
     Final HTML size: 1126020 chars

⏺ Now remove the image files and the other unused GIFs.

⏺ Bash(rm /Users/sergeyk/w/wheely/showcase/01_default_ui.png
      /Users/sergeyk/w/wheely/showcase/02_configured_bumpy.png
      /Users/sergeyk/w/wheely/showcase/sim_figure8_zoom…)
  ⎿  Done

⏺ Read 1 file (ctrl+o to expand)

⏺ Done. showcase/showcase.html is now fully self-contained at 1.1MB — all three
  images (2 PNGs + 1 GIF) are embedded as base64 data URIs. The directory
  contains only the single HTML file.

✻ Crunched for 1m 19s

## Make skill to always do visual check, correct and be self contained with all images inlined

❯ can you update /showcase skill to peform deck visual check for all slides 
   to fit 4:3 aspect  and image embedding                                   

⏺ Read 1 file (ctrl+o to expand)

⏺ Update(.claude/skills/showcase/SKILL.md)
  ⎿  Added 79 lines, removed 26 lines
        8  
        9  Generate a self-contained HTML slide deck demonstrating the wh
           eely simulation platform.
       10  
       11 +## Output                                                     
       12 +                                                              
       13 +`showcase/showcase.html` — a single self-contained HTML file (
          +all images embedded as base64 data URIs). No external image fi
          +les should remain in the directory.                           
       14 +                                                              
       15  ## Prerequisites
       16  
       17 +Ensure playwright and chromium are available in the project ve
          +nv:                                                           
       18 +                                                              
       19  ```bash
       14 -pip install -e ".[showcase]"                                  
       15 -playwright install chromium                                   
       20 +pip install -e ".[dev]"                                       
       21 +.venv/bin/python -m playwright install chromium               
       22  ```
       23  
       18 -## Generate the deck                                          
       24 +Also requires `ffmpeg` for GIF generation from frame sequences
          +.                                                             
       25  
       26 +## Workflow                                                   
       27 +                                                              
       28 +### 1. Start the simulation server                            
       29 +                                                              
       30  ```bash
       21 -python scripts/showcase.py                                    
       31 +.venv/bin/uvicorn wheely.server:app --port 8765               
       32  ```
       33  
       24 -Output: `output/showcase.html` (open in any browser)          
       34 +Run in background. Verify with `curl -s -o /dev/null -w "%{htt
          +p_code}" http://localhost:8765/`.                             
       35  
       26 -## Options                                                    
       36 +### 2. Capture screenshots and GIFs                           
       37  
       28 -- `--port PORT` - Use a different server port (default: 8765) 
       29 -- `--output PATH` - Write deck to a different path            
       38 +Use Playwright (headless Chromium) at **850x600** viewport wit
          +h `device_scale_factor: 2` for retina quality.                
       39  
       31 -## Customizing scenarios                                      
       40 +- Navigate to `http://localhost:8765`, wait for WebSocket `Con
          +nected` status                                                
       41 +- Interact with the UI via `page.evaluate()`, `page.select_opt
          +ion()`, `page.click()` etc.                                   
       42 +- Take screenshots with `page.screenshot()`                   
       43 +- Record GIFs by capturing frame sequences (e.g., 5 seconds at
          + 15fps = 75 frames), then convert with ffmpeg:                
       44 +  ```bash                                                     
       45 +  ffmpeg -y -framerate 15 -i frame_%04d.png \                 
       46 +    -vf "scale=850:600:flags=lanczos,split[s0][s1];[s0]palette
          +gen[p];[s1][p]paletteuse" \                                   
       47 +    output.gif                                                
       48 +  ```                                                         
       49 +- Clean up frame directories after conversion                 
       50  
       33 -Edit `scripts/scenarios.py` to add/modify/remove slides. Each 
          -`Scenario` dataclass defines:                                 
       34 -- `title`: Slide heading                                      
       35 -- `layout`: TITLE, DEMO, COMPARISON, or TEXT                  
       36 -- `capture_type`: NONE, SCREENSHOT, or GIF                    
       37 -- `setup_messages`: WebSocket messages to configure the scene 
       38 -- `frame_messages`: Per-frame messages for GIF animations (par
          -ameter sweeps, position changes)                              
       39 -- `code`: CodeSnippet reference to extract from source        
       40 -- `caption`: Explanatory text                                 
       51 +### 3. Build the reveal.js deck                               
       52  
       42 -## Regenerating after code changes                            
       53 +Write `showcase/showcase.html` as a self-contained reveal.js p
          +resentation:                                                  
       54  
       44 -Run `python scripts/showcase.py` again. Code snippets are extr
          -acted from live source files, so the deck always reflects curr
          -ent implementation.                                           
       55 +- Load reveal.js and highlight.js from CDN (`cdn.jsdelivr.net`
          +)                                                             
       56 +- Use `<img src="filename.png">` initially while authoring    
       57 +- Set Reveal config with `margin: 0.08` for safe text area    
       58  
       46 -## Architecture                                               
       59 +### 4. Visual check — 4:3 fit verification                    
       60  
       61 +**This step is mandatory.** After building the deck, verify ev
          +ery slide fits a 4:3 screen with no text cutoff:              
       62 +                                                              
       63 +1. Write a temporary verification script that:                
       64 +   - Opens the deck HTML via `file://` URL in headless Playwri
          +ght                                                           
       65 +   - Sets viewport to **1024x768** (4:3 aspect ratio)         
       66 +   - Iterates `Reveal.getTotalSlides()`, calling `Reveal.slide
          +(i)` for each                                                 
       67 +   - Screenshots each slide to a temp file                    
       68 +2. **Visually inspect every screenshot** using the Read tool  
       69 +3. If any text is clipped or cut off at edges/bottom:         
       70 +   - Reduce font sizes, shorten text, trim code blocks, or rem
          +ove lines                                                     
       71 +   - Re-run the verification loop until all slides pass       
       72 +4. Common fixes for overflow:                                 
       73 +   - Reduce `font-size` in CSS (body text: `0.55em`, code: `0.
          +38em`, lists: `0.55em`)                                       
       74 +   - Shorten bullet text that wraps to right edge             
       75 +   - Trim code blocks — remove blank lines, collapse comments,
          + cut fields                                                   
       76 +   - Use shorter labels in metric boxes                       
       77 +5. Clean up verification script and temp screenshots when done
       78 +                                                              
       79 +### 5. Embed images as base64 data URIs                       
       80 +                                                              
       81 +**This step is mandatory.** The final HTML must be fully self-
          +contained:                                                    
       82 +                                                              
       83 +1. For each image referenced in the HTML (`src="filename.png"`
          + or `src="filename.gif"`):                                    
       84 +   - Read the file, base64-encode it                          
       85 +   - Replace `src="filename.ext"` with `src="data:image/<type>
          +;base64,<data>"`                                              
       86 +2. Delete all image files (PNGs, GIFs) from the `showcase/` di
          +rectory                                                       
       87 +3. Also delete any unused GIFs that were captured but not incl
          +uded in the deck                                              
       88 +4. Verify `showcase/` contains only `showcase.html`           
       89 +                                                              
       90 +This can be done with a Python one-liner:                     
       91 +```python                                                     
       92 +import base64; from pathlib import Path                       
       93 +html = Path('showcase.html').read_text()                      
       94 +for f, mime in [('img.png','image/png'), ('anim.gif','image/gi
          +f')]:                                                         
       95 +    d = base64.b64encode(Path(f).read_bytes()).decode()       
       96 +    html = html.replace(f'src="{f}"', f'src="data:{mime};base6
          +4,{d}"')                                                      
       97 +Path('showcase.html').write_text(html)                        
       98  ```
       49 -scripts/                                                      
       50 -├── showcase.py      # CLI orchestrator (server lifecycle, pip
          -eline)                                                        
       51 -├── scenarios.py     # Scenario definitions (what to capture) 
       52 -├── capture.py       # Playwright browser automation, screensh
          -ot/GIF capture                                                
       53 -└── deck_builder.py  # HTML assembly with reveal.js + highligh
          -t.js                                                          
       54 -```                                                           
       99 +                                                              
      100 +## Style Guide                                                
      101 +                                                              
      102 +- Dark theme: background `#1a1a2e`, headings `#e94560`, accent
          +s `#4fc3f7`                                                   
      103 +- Code blocks: `atom-one-dark` highlight.js theme             
      104 +- Architecture boxes: `#0f3460` background, `#16213e` for card
          +s                                                             
      105 +- Tags/chips: `#0f3460` background with `#4fc3f7` text        
      106 +- Metrics: `#4ade80` green values                             
      107 +- Keep all text, code, and images within the safe area at 1024
          +x768 viewport                                                 

⏺ Updated. The skill now documents the full workflow with two new mandatory
  steps:

  - Step 4 — 4:3 fit verification: Screenshot every slide at 1024x768 in
  headless Playwright, visually inspect each one, and iterate fixes until
  nothing is clipped. Includes common fix patterns (font sizes, text shortening,
   code trimming).
  - Step 5 — Image embedding: Base64-encode all images into data URIs, replace
  src attributes, delete all image files so showcase/ contains only the single
  HTML file.

✻ Sautéed for 1m 10s

❯ can you extract gif from @showcase.html slide 5 and store it ./demo.gif   
  and display it in README.md                                               

⏺ Bash(cd /Users/sergeyk/w/wheely && /Users/sergeyk/w/wheely/.venv/bin/python3
      -c "
      import base64, re…)
  ⎿  Extracted demo.gif: 453696 bytes

⏺ Now add it to the README.

⏺ Read 1 file (ctrl+o to expand)

⏺ Update(README.md)
  ⎿  Added 2 lines
      2  
      3  A kinematic simulation tool for a self-leveling tricycle robotic
          platform with parallelogram arm linkages. Designed as a power p
         latform for uneven terrain (forestry, rough ground).
      4  
      5 +![Wheely figure-8 simulation on bumpy terrain](demo.gif)        
      6 +                                                                
      7  ## The Platform
      8  
      9  Three-wheel-drive with all wheels independently steered. Two par
         allelogram arms extend from an apex wheel to two rear wheels, wi
         th a cross brace connecting them. The parallelogram geometry kee
         ps the cargo platform level as the arms conform to terrain.

⏺ Done. Extracted the GIF to demo.gif (443KB) and added it to the README right
  below the project description.

✻ Brewed for 52s

❯ commit this 

⏺ Bash(git status)
  ⎿  On branch main
     Your branch is up to date with 'origin/main'.
     … +18 lines (ctrl+o to expand)

⏺ Bash(git diff --stat)
  ⎿   .claude/skills/showcase.md | 54 -------------------------------------
     ---------
      README.md                  |  2 ++
     … +2 lines (ctrl+o to expand)

⏺ Bash(git log --oneline -5)
  ⎿  942a60d feat: add motion dropdown and figure-8 visualization with body
      transform
     995943d Merge branch 'worktree-agent-a6744db1'
     … +4 lines (ctrl+o to expand)

⏺ Bash(git diff README.md)
  ⎿  diff --git a/README.md b/README.md
     index 9cc720d..0cb09ef 100644
     --- a/README.md
     … +15 lines (ctrl+o to expand)

⏺ Bash(git add README.md demo.gif showcase/showcase.html
      .claude/skills/showcase/SKILL.md .claude/skills/showcase.md)
  ⎿  Error: Exit code 1
     The following paths are ignored by one of your .gitignore files:
     .claude
     hint: Use -f if you really want to add them.
     hint: Disable this message with "git config set advice.addIgnoredFile 
     false"

     The following paths are ignored by one of your .gitignore files:
     .claude
     hint: Use -f if you really want to add them.
     hint: Disable this message with "git config set advice.addIgnoredFile 
     false"

⏺ The .claude/ directory is gitignored. Let me stage only the non-ignored files.

⏺ Bash(git add README.md demo.gif showcase/showcase.html)
  ⎿  (No output)

⏺ Bash(git diff --cached --stat)
  ⎿   .claude/skills/showcase.md |  54 -------
      README.md                  |   2 +
      demo.gif                   | Bin 0 -> 453696 bytes
     … +3 lines (ctrl+o to expand)

⏺ Bash(git commit -m "feat: add self-contained showcase deck and demo GIF…)
  ⎿  [main b3afa46] feat: add self-contained showcase deck and demo GIF
      4 files changed, 366 insertions(+), 54 deletions(-)
      delete mode 100644 .claude/skills/showcase.md
     … +2 lines (ctrl+o to expand)

⏺ Bash(git status)
  ⎿  On branch main
     Your branch is ahead of 'origin/main' by 1 commit.
       (use "git push" to publish your local commits)
     … +15 lines (ctrl+o to expand)

⏺ Committed as b3afa46:
  - showcase/showcase.html — self-contained reveal.js deck (1.1MB, all images
  embedded)
  - demo.gif — figure-8 simulation GIF extracted for README
  - README.md — added demo GIF display
  - Removed old .claude/skills/showcase.md (replaced by SKILL.md in the correct
  location, which is gitignored)

✻ Brewed for 1m 28s

❯ push it 

⏺ Bash(git push)
  ⎿  To github.com:walnutgeek/wheely.git
        942a60d..b3afa46  main -> main

⏺ Pushed to main.

✻ Cogitated for 33s

❯ describe commit and push all changes 

⏺ Bash(git status)
  ⎿  On branch main
     Your branch is up to date with 'origin/main'.
     … +14 lines (ctrl+o to expand)

⏺ Bash(git diff)
  ⎿  diff --git a/wheely/dynamics.py b/wheely/dynamics.py
     index ac938ef..8786bdc 100644
     --- a/wheely/dynamics.py
     … +21 lines (ctrl+o to expand)

⏺ Bash(git log --oneline -3)
  ⎿  b3afa46 feat: add self-contained showcase deck and demo GIF
     942a60d feat: add motion dropdown and figure-8 visualization with body
      transform
     995943d Merge branch 'worktree-agent-a6744db1'

⏺ Read 1 file (ctrl+o to expand)

⏺ Here's what's pending:

  Modified:
  - wheely/dynamics.py — Increases arm weight from 2N to 10N, adds arm reach
  damping (friction at pivots) to reduce oscillation in arm motion

  Untracked:
  - docs/ai/2026-05-13-parallelogram-viz-overhaul.md — Design doc for
  parallelogram visualization
  - uv.lock — Lock file from uv package manager
  - wheely-config.json — Saved platform configuration
  - .DS_Store — macOS metadata (should not commit)

⏺ Bash(git add wheely/dynamics.py docs/ai/ uv.lock wheely-config.json && git
      commit -m "feat: add arm reach damping and increase arm weight…)
  ⎿  [main 009b70e] feat: add arm reach damping and increase arm weight
      4 files changed, 1189 insertions(+), 3 deletions(-)
      create mode 100644 docs/ai/2026-05-13-parallelogram-viz-overhaul.md
     … +2 lines (ctrl+o to expand)

⏺ Bash(git push)
  ⎿  To github.com:walnutgeek/wheely.git
        b3afa46..009b70e  main -> main

⏺ Pushed 009b70e to main. Changes:

  - wheely/dynamics.py — Arm weight 2N → 10N, added arm reach damping (3.0
  Ns/rad) to reduce pivot oscillation
  - docs/ai/ — Parallelogram viz overhaul design doc
  - uv.lock — Package lock file
  - wheely-config.json — Saved platform configuration

✻ Worked for 1m 5s

❯ can you create github action that publish @showcase/showcase.html on      
  ghpages                                                                   

⏺ Read 1 file (ctrl+o to expand)

⏺ Bash(mkdir -p /Users/sergeyk/w/wheely/.github/workflows)
  ⎿  Done

⏺ Write(.github/workflows/gh-pages.yml)
  ⎿  Wrote 38 lines to .github/workflows/gh-pages.yml
       1 name: Deploy showcase to GitHub Pages
       2 
       3 on:
       4   push:
       5     branches: [main]
       6     paths: [showcase/**]
       7   workflow_dispatch:
       8 
       9 permissions:
      10   pages: write
     … +28 lines (ctrl+o to expand)

⏺ Bash(git add .github/workflows/gh-pages.yml && git commit -m "ci: add GitHub
      Pages deployment for showcase deck…)
  ⎿  [main 3d28201] ci: add GitHub Pages deployment for showcase deck
      1 file changed, 38 insertions(+)
      create mode 100644 .github/workflows/gh-pages.yml
     … +2 lines (ctrl+o to expand)

⏺ Pushed. One thing left — GitHub Pages needs to be configured to use "GitHub
  Actions" as the source (not the older branch-based method). Let me check and
  set that up.

⏺ Bash(gh api repos/walnutgeek/wheely/pages 2>&1 || echo "Pages not configured
      yet")
  ⎿  /bin/bash: gh: command not found
     Pages not configured yet

⏺ Bash(which gh 2>/dev/null || brew list gh 2>/dev/null || echo "gh CLI not
      installed")
  ⎿  gh CLI not installed

⏺ The gh CLI isn't installed, so I can't configure Pages programmatically.
  You'll need to enable it in the GitHub repo settings:

  1. Go to github.com/walnutgeek/wheely/settings/pages
  2. Under Source, select GitHub Actions
  3. Save

  The workflow will run automatically on the next push to showcase/, or you can
  trigger it manually from the Actions tab → "Deploy showcase to GitHub Pages" →
   Run workflow.

  Once deployed, the deck will be live at https://walnutgeek.github.io/wheely/.

✻ Churned for 1m 39s

