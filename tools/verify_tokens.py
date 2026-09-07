#!/usr/bin/env python3
"""
verify_tokens.py - checks the eight token thumbnails (deliverables/assets/tokens/the-<name>.svg) in Chromium
by seeking the SVG clock: body colour and floor, the seven squares in the complements order resting at 0.3,
the own square at full colour at the peak of its breath, the four dance frames; for the Glitch the colour
sparks in the static, the blink, and the sweep across the squares. Prints one line per check and ALL OK.
"""
import io, os, sys
from collections import Counter
from playwright.sync_api import sync_playwright
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import buddy_retro_svg as rs, buddy_retro_mock as rm
def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
PAL = {c: rgb(rm.PAL[c]) for c in range(16)}
NAME = {v: k for k, v in rs.NAMES.items()}; NAME.update({11: "dark grey", 15: "light grey", 12: "grey", 1: "white"})
def near(a, b, tol=8): return all(abs(x - y) <= tol for x, y in zip(a, b))
def scaled(c, k): return tuple(round(v * k) for v in c)
ok = True
def check(cond, msg):
    global ok
    ok &= bool(cond); print(("  ok   " if cond else "  FAIL ") + msg)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=rs.EXE)
    for t in rs.ALL:
        f = os.path.join(rs.TOKENS_DIR, f"{t}.svg"); glitch = t == "the-glitch"
        pg = b.new_page(viewport={"width": 240, "height": 240}); pg.goto("file://" + f); pg.wait_for_timeout(150)
        pg.evaluate("() => { const s=document.querySelector('svg'); s.setAttribute('width', 240); s.setAttribute('height', 240); s.pauseAnimations(); }")
        def shot(tt):
            pg.evaluate("t => document.querySelector('svg').setCurrentTime(t)", tt); pg.wait_for_timeout(25)
            return Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        def body(im):
            c = Counter(im.getpixel((x, y)) for x in range(60, 180) for y in range(25, 180) if im.getpixel((x, y)) != (0, 0, 0))
            return c.most_common(1)[0] if c else (None, 0)
        def tag(im): return [im.getpixel((15 + round(12.5 * i), 15)) for i in range(7)]
        colour = 11 if glitch else rm.TOKENS[t][0]
        print(f"{t} ({os.path.getsize(f)} bytes)")
        im = shot(0.0); bc, n = body(im)
        check(bc is not None and near(bc, PAL[colour]), f"body at rest is {NAME[colour]} ({bc})")
        floor_top = Counter(im.getpixel((x, 37 * 5 + 2)) for x in range(0, 240)).most_common(1)[0][0]
        check(near(floor_top, PAL[15 if glitch else colour]), f"floor's top row is {NAME[15 if glitch else colour]}")
        sq = tag(im)
        check(all(near(sq[i], scaled(PAL[c], 0.3), 10) for i, c in enumerate(rs.COMPLEMENTS)), "seven squares in the complements order, resting at 0.3")
        if not glitch:
            own = rs.COMPLEMENTS.index(colour); peak = tag(shot(1.8))
            check(near(peak[own], PAL[colour], 4) and all(near(peak[i], scaled(PAL[c], 0.3), 20) for i, c in enumerate(rs.COMPLEMENTS) if i != own),
                  f"at 1.8 s his own square (no. {own + 1}) is at full colour and the others rest (a faint halo allowed)")
            for phase_t, frame in ((0.0, 0), (0.3, 1), (1.2, 2), (1.5, 3)):
                fr = shot(phase_t); check(body(fr)[1] > 0, f"dance frame visible at {phase_t} s")
        else:
            for tt, c in ((1.28, 3), (1.46, 10), (4.88, 6), (8.48, 14), (8.66, 4)):
                bc, _ = body(shot(tt)); check(bc is not None and near(bc, PAL[c]), f"spark at {tt} s is {NAME[c]} ({bc})")
            check(body(shot(2.40))[1] == 0, "blink: gone at 2.40 s")
            check(body(shot(2.48))[1] > 0, "blink: back at 2.48 s")
            sw = tag(shot(0.78)); bright = max(range(7), key=lambda i: sum(sw[i]) / sum(PAL[rs.COMPLEMENTS[i]]))
            check(bright == 3, f"sweep: at 0.78 s the brightest square is no. {bright + 1} (green, the middle)")
            sw2 = tag(shot(1.25)); bright2 = max(range(7), key=lambda i: sum(sw2[i]) / sum(PAL[rs.COMPLEMENTS[i]]))
            check(bright2 == 6, f"sweep: at 1.25 s the brightest square is no. {bright2 + 1} (light blue, the last)")
        pg.close()
    b.close()
print("ALL OK" if ok else "SOMETHING FAILED")
