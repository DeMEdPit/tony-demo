#!/usr/bin/env python3
"""
buddy_retro_svg.py - the token thumbnail, the retro layout, as an animated SVG: the seven colours as a row
of squares top left, the buddy dancing in the middle, a dithered gradient floor under his feet.
`--final` writes the eight token files with the owner's decisions (FINAL below) into deliverables/assets/tokens/;
every other option is for mock-ups, which go to deliverables/assets/mock/.
His own square breathes in time with the dance (one breath per two loops); the Glitch's squares light up
one after another, a loop each, and his body follows. Everything on the 48-pixel grid, drawn as pixel runs;
the floor may be dithered on a half-pixel grid ("fine") and the tag squares may sit a half pixel apart.

Glitch options: the colour his cascade starts on, and what his floor is made of -
  own        the floor of whichever buddy owns the start colour (the default)
  spectrum   all seven colours, warm to cool, then black
  luminance  all seven colours, brightest first, then black
  follow     the floor changes with his body, a loop at a time (looks like "own" in a still)
  grey       white through the greys to black, so his body is the only colour
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buddy_thumbnail as bt
import buddy_retro_mock as rm

LOOP = bt.PHASE_SECONDS * len(bt.PHASES)          # 1.8 s
BREATH = f"{2 * LOOP:g}s"                          # 3.6 s
CASCADE = f"{7 * LOOP:g}s"                         # 12.6 s
SIZE = 48
BLACK = rm.PAL[0]
NAMES = {"light-red": 10, "yellow": 7, "green": 5, "cyan": 3, "light-blue": 14, "blue": 6, "purple": 4}
NAME_OF = {v: k for k, v in NAMES.items()}
GREY_RAMP = [1, 15, 12, 11, 0]                     # white, light grey, medium grey, dark grey, black
GREY_SOFT = [15, 12, 11, 0]                        # the same floor starting on light grey
GREY_DUSK = [12, 11, 0]                            # medium grey down to black
GREY_DARK = [11, 0]                                # dark grey down to black: the room with the lights out
GREYS = {"white": 1, "light-grey": 15, "grey": 12, "dark-grey": 11, "static": 1, "dark-static": 11, "sparks": 1, "dark-sparks": 11}
# "sparks": the same bursts, but the light-grey flips become colours, a different pair each burst, over a seven-burst cycle
SPARKS = [3, 10, 6, 7, 14, 4, 5, 7, 3, 4, 10, 5, 14, 6]          # a scrambled deal: each of the seven twice, never twice running
# a burst of static once per breath: a third of a second of quick flips between the greys, then back to the body's grey
STATIC = {"static": [(1.20, 15), (1.24, 1), (1.27, 12), (1.30, 1), (1.36, 15), (1.39, 1), (1.45, 12), (1.47, 1), (1.52, 15), (1.54, 1)],
          "dark-static": [(1.20, 12), (1.24, 11), (1.27, 15), (1.30, 11), (1.36, 12), (1.39, 11), (1.45, 15), (1.47, 11), (1.52, 12), (1.54, 11)]}
SWEEPS = {"sweep": (0.15, 0.05, 0.45), "comet": (0.22, 0.05, 1.0)}   # seconds per square, rise, decay
def luma(c): r, g, b = rm.rgb(c); return 0.299 * r + 0.587 * g + 0.114 * b
LUMINANCE = sorted(rm.STRIP, key=lambda c: -luma(c))
ROSTER = [6, 3, 7, 14, 5, 10, 4]                   # token 1..7: Shadow, Dancer, Echo, Mirror, Wanderer, Shy, Sleeper
COMPLEMENTS = [6, 7, 4, 5, 10, 3, 14]              # opposite pairs side by side, green in the middle, ends on light blue
ORDERS = {"hue": rm.STRIP, "roster": ROSTER, "luminance": LUMINANCE, "complements": COMPLEMENTS}

def order_of(spec):
    """A named order, or seven colour names separated by commas."""
    if spec in ORDERS: return ORDERS[spec]
    order = [NAMES[n.strip()] for n in spec.split(",")]
    assert sorted(order) == sorted(rm.STRIP), f"{spec}: need each of the seven colours once"
    return order
EXE = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

def own_ramp(colour):
    """A token colour's floor: its ramp from that colour down to black."""
    for c, ramp in rm.TOKENS.values():
        if c == colour: return ramp[ramp.index(c):]
    return [colour, 0]

def pad_ramp(r, n=4):
    r = list(r)
    while len(r) < n: r.insert(-1, r[-2])
    return r

def floor_geometry(bands, depth):
    """Rows of ramp indices for the floor band, plus its height in pixels and its grid scale."""
    h = 11 if "deep" in depth else 8
    scale = 2 if "fine" in depth else 1              # "fine": dithered on a half-pixel grid
    return rm.dither_column_fine(SIZE * scale, h * scale, list(range(bands))), h, scale

def floor_paths(rows, y0, scale, fills):
    """One path per ramp index; fills[i] is a colour, or a list of colours (one per cascade step) to animate."""
    parts = []
    for i in sorted(set(v for row in rows for v in row)):
        f = fills[i]
        mask = [[1 if v == i else 0 for v in row] for row in rows]
        d = bt.runs_path(mask, 0, y0 * scale)
        if isinstance(f, list):
            if all(x == BLACK for x in f): continue
            kt = ";".join(f"{k / len(f):.4f}" for k in range(len(f) + 1))
            parts.append(f'<path fill="{f[0]}" d="{d}"><animate attributeName="fill" values="{";".join(f + [f[0]])}" '
                         f'keyTimes="{kt}" calcMode="discrete" dur="{CASCADE}" repeatCount="indefinite"/></path>')
        elif f != BLACK:
            parts.append(f'<path fill="{f}" d="{d}"/>')
    body = "\n".join(parts)
    return body if scale == 1 else f'<g transform="scale({1 / scale:g})">\n{body}\n</g>'

def floor(token, depth, glitch, mode, seq):
    """The floor band for a token: (rows, height, scale, fills)."""
    if not glitch:
        colour, ramp = rm.TOKENS[token]
        fr = ramp[ramp.index(colour):]
        if "lit" in depth:
            lighter = ramp[max(0, ramp.index(colour) - 1)]
            if lighter != colour: fr = [lighter] + fr
        fills = [rm.PAL[c] for c in fr]
    elif mode == "own": fills = [rm.PAL[c] for c in own_ramp(seq[0])]
    elif mode == "spectrum": fills = [rm.PAL[c] for c in rm.STRIP + [0]]
    elif mode == "luminance": fills = [rm.PAL[c] for c in LUMINANCE + [0]]
    elif mode == "grey": fills = [rm.PAL[c] for c in GREY_RAMP]
    elif mode == "grey-soft": fills = [rm.PAL[c] for c in GREY_SOFT]
    elif mode == "grey-dusk": fills = [rm.PAL[c] for c in GREY_DUSK]
    elif mode == "grey-dark": fills = [rm.PAL[c] for c in GREY_DARK]
    elif mode == "follow":
        ramps = [pad_ramp(own_ramp(c)) for c in seq]
        fills = [[rm.PAL[r[i]] for r in ramps] for i in range(4)]
    else: raise SystemExit(f"unknown glitch floor {mode}")
    rows, h, scale = floor_geometry(len(fills), depth)
    return rows, h, scale, fills

def figure_paths(frames, fill, bx, by, glitch, seq, body="cascade"):
    n = len(bt.PHASES)
    keytimes = ";".join(f"{i / n:.4f}" for i in range(n)) + ";1"
    dur = f"{LOOP:g}s"
    order = []
    for f in bt.PHASES:
        if f not in order: order.append(f)
    parts = []
    for f in order:
        values = ";".join("1" if p == f else "0" for p in bt.PHASES) + ";" + ("1" if bt.PHASES[0] == f else "0")
        parts.append(f'<path fill="{fill}" d="{bt.runs_path(frames[f], bx, by)}">')
        parts.append(f'<animate attributeName="opacity" values="{values}" keyTimes="{keytimes}" calcMode="discrete" dur="{dur}" repeatCount="indefinite"/>')
        if glitch and body == "cascade":
            kt = ";".join(f"{k / 7:.4f}" for k in range(8))
            cols = ";".join(rm.PAL[c] for c in seq) + ";" + rm.PAL[seq[0]]
            parts.append(f'<animate attributeName="fill" values="{cols}" keyTimes="{kt}" calcMode="discrete" dur="{CASCADE}" repeatCount="indefinite"/>')
        elif glitch and body in STATIC:
            burst = STATIC[body]; base = rm.PAL[GREYS[body]]
            kt = "0;" + ";".join(f"{t / (2 * LOOP):.4f}" for t, _ in burst) + ";1"
            cols = base + ";" + ";".join(rm.PAL[c] for _, c in burst) + ";" + base
            parts.append(f'<animate attributeName="fill" values="{cols}" keyTimes="{kt}" calcMode="discrete" dur="{BREATH}" repeatCount="indefinite"/>')
        elif glitch and body in ("sparks", "dark-sparks"):
            burst = STATIC["static" if body == "sparks" else "dark-static"]; base = rm.PAL[GREYS[body]]
            import itertools
            cycle = 7 * 2 * LOOP; times, vals = [], []; deal = itertools.cycle(SPARKS)
            for k in range(7):
                for t, c in burst:
                    times.append(k * 2 * LOOP + t); vals.append(rm.PAL[next(deal)] if c == 15 else rm.PAL[c])
            kt = "0;" + ";".join(f"{t / cycle:.5f}" for t in times) + ";1"
            cols = base + ";" + ";".join(vals) + ";" + base
            parts.append(f'<animate attributeName="fill" values="{cols}" keyTimes="{kt}" calcMode="discrete" dur="{cycle:g}s" repeatCount="indefinite"/>')
        parts.append('</path>')
    body = "\n".join(parts)
    if glitch:
        times = [0.0] + [at / bt.BLINK_PERIOD for at, _ in bt.BLINK] + [1.0]
        vals = [1] + [val for _, val in bt.BLINK] + [1]
        body = (f'<g><animate attributeName="opacity" values="{";".join(str(v) for v in vals)}" keyTimes="{";".join(f"{t:.4f}" for t in times)}" '
                f'calcMode="discrete" dur="{bt.BLINK_PERIOD:g}s" repeatCount="indefinite"/>\n' + body + '\n</g>')
    return body

def tag(token, glitch, gap, dim, seq, tagmode="cascade", order=None):
    """Seven 2x2 squares straight across the top left, at gap pixels apart (may be a half pixel), the
    resting ones at opacity dim. Drawn anti-aliased so a half-pixel gap never snaps unevenly."""
    colour = rm.TOKENS.get(token, (None, None))[0]
    kt = ";".join(f"{k / 7:.4f}" for k in range(8))
    spline = 'keyTimes="0;0.5;1" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"'
    parts = ['<g shape-rendering="geometricPrecision">']
    for i, c in enumerate(order or rm.STRIP):
        x = f"{2 + i * (2 + gap):g}"
        if glitch or c == colour:
            if glitch and tagmode in SWEEPS:
                # a wave of light runs straight across the row once per breath: square i peaks at s0 + i * step
                step, rise, decay = SWEEPS[tagmode]; P = 2 * LOOP; peak = 0.3 + i * step
                kt = f"0;{(peak - rise) / P:.4f};{peak / P:.4f};{(peak + decay) / P:.4f};1"
                glow = f'<animate attributeName="opacity" values="0;0;0.9;0;0" keyTimes="{kt}" dur="{BREATH}" repeatCount="indefinite"/>'
                bright = f'<animate attributeName="opacity" values="{dim:g};{dim:g};1;{dim:g};{dim:g}" keyTimes="{kt}" dur="{BREATH}" repeatCount="indefinite"/>'
            elif glitch:
                step = seq.index(c)
                on = lambda k, a, b: a if k == step else b
                glow = f'<animate attributeName="opacity" values="{";".join(on(k, "0.9", "0") for k in range(7))};{on(0, "0.9", "0")}" keyTimes="{kt}" dur="{CASCADE}" repeatCount="indefinite"/>'
                bright = f'<animate attributeName="opacity" values="{";".join(on(k, "1", f"{dim:g}") for k in range(7))};{on(0, "1", f"{dim:g}")}" keyTimes="{kt}" dur="{CASCADE}" repeatCount="indefinite"/>'
            else:
                glow = f'<animate attributeName="opacity" values="0;0.9;0" {spline} dur="{BREATH}" repeatCount="indefinite"/>'
                bright = f'<animate attributeName="opacity" values="{dim:g};1;{dim:g}" {spline} dur="{BREATH}" repeatCount="indefinite"/>'
            parts.append(f'<rect x="{x}" y="2" width="2" height="2" fill="{rm.PAL[c]}" filter="url(#glow)" opacity="0">{glow}</rect>')
            parts.append(f'<rect x="{x}" y="2" width="2" height="2" fill="{rm.PAL[c]}" opacity="{dim:g}">{bright}</rect>')
        else:
            parts.append(f'<rect x="{x}" y="2" width="2" height="2" fill="{rm.PAL[c]}" opacity="{dim:g}"/>')
    parts.append('</g>')
    return "\n".join(parts)

def svg(frames, token, depth="deep", gap=1.0, dim=0.6, mode="own", start="light-red", body="cascade", tagmode="cascade", order="hue"):
    glitch = (token == "the-glitch")
    k = rm.STRIP.index(NAMES[start]); seq = rm.STRIP[k:] + rm.STRIP[:k]
    rows, h, scale, fills = floor(token, depth, glitch, mode, seq)
    fill = (rm.PAL[seq[0]] if body == "cascade" else rm.PAL[GREYS.get(body, 1)]) if glitch else rm.PAL[rm.TOKENS[token][0]]
    fh = bt.ink_box(frames)[1] + 1; fw = len(frames[0][0])
    bx, by = (SIZE - fw) // 2, SIZE - h - fh
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" shape-rendering="crispEdges">',
             '<defs><filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="1.1"/></filter></defs>',
             f'<rect width="{SIZE}" height="{SIZE}" fill="#000"/>',
             floor_paths(rows, SIZE - h, scale, fills), tag(token, glitch, gap, dim, seq, tagmode, order_of(order)),
             figure_paths(frames, fill, bx, by, glitch, seq, body), '</svg>']
    return "\n".join(parts) + "\n"

def shoot(browser, source, px, t=1.0):
    """Render an SVG file or string at px pixels, paused at t seconds; returns a PIL image."""
    import io
    from PIL import Image
    pg = browser.new_page(viewport={"width": px, "height": px})
    if os.path.exists(source): pg.goto("file://" + os.path.abspath(source))
    else: pg.set_content(f'<html><body style="margin:0">{source}</body></html>')
    pg.wait_for_timeout(150)
    pg.evaluate("t => { const s=document.querySelector('svg'); s.setAttribute('width', innerWidth); s.setAttribute('height', innerHeight); s.pauseAnimations(); s.setCurrentTime(t); }", t)
    pg.wait_for_timeout(60)
    im = Image.open(io.BytesIO(pg.screenshot())).convert("RGB"); pg.close()
    return im

def lineup(files, path, columns=4, t=1.0):
    """All the files at 240 px with the true 48 px beside each, in a grid; files are (label, variant, path)."""
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw
    pad, th, cw, chh = 14, 20, 240 + 14 + 48 + 14, 20 + 240 + 14
    rows = (len(files) + columns - 1) // columns
    im = Image.new("RGB", (pad + columns * cw, pad + rows * chh), (24, 24, 24)); d = ImageDraw.Draw(im)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE if os.path.exists(EXE) else None)
        for k, entry in enumerate(files):
            (label, v, f), tt = entry[:3], (entry[3] if len(entry) > 3 else t)     # an optional fourth field: its own moment
            x, y = pad + (k % columns) * cw, pad + (k // columns) * chh
            d.text((x, y + 2), f"{label} · {v}", fill=(230, 230, 230))
            im.paste(shoot(b, f, 240, tt), (x, y + th)); im.paste(shoot(b, f, 48, tt), (x + 240 + pad, y + th + 240 - 48))
        b.close()
    im.save(path); print(path)

def strip(docs, path, crops=((1.0, "peak"),), crop_h=60):
    """Thumbnails at 240 px with 10x crops of the tag below; docs are (label, svg text)."""
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw
    pad, th = 14, 20
    im = Image.new("RGB", (pad + len(docs) * (240 + pad), pad + th + 240 + len(crops) * (8 + crop_h) + pad), (24, 24, 24)); d = ImageDraw.Draw(im)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE if os.path.exists(EXE) else None)
        for k, (label, doc) in enumerate(docs):
            x = pad + k * (240 + pad)
            d.text((x, pad + 2), label, fill=(230, 230, 230))
            im.paste(shoot(b, doc, 240, crops[0][0]), (x, pad + th))
            for j, (t, name) in enumerate(crops):
                y = pad + th + 240 + 8 + j * (8 + crop_h)
                im.paste(shoot(b, doc, 480, t).crop((0, 0, 240, crop_h)), (x, y))
                d.text((x + 244 - 8 * len(name) - 4, y + crop_h - 12), name, fill=(150, 150, 150))
        b.close()
    im.save(path); print(path)

def burst_times(breaths=2, coarse=0.1, fine=0.02, window=(1.15, 1.62)):
    """Moments for a GIF: coarse steps, and fine steps through each breath's static burst; (t, milliseconds)."""
    out, t = [], 0.0
    while t < breaths * 2 * LOOP:
        step = fine if window[0] <= (t % (2 * LOOP)) < window[1] else coarse
        out.append((round(t, 3), int(step * 1000))); t += step
    return out

def gif(files, prefix, seconds, fps, px=240, times=None):
    """Animated GIFs of the files, seeking one page through the SVG clock; times overrides seconds/fps with (t, ms) pairs."""
    import io
    from playwright.sync_api import sync_playwright
    from PIL import Image
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE if os.path.exists(EXE) else None)
        for label, v, f in files:
            pg = b.new_page(viewport={"width": px, "height": px}); pg.goto("file://" + os.path.abspath(f)); pg.wait_for_timeout(150)
            pg.evaluate("() => { const s=document.querySelector('svg'); s.setAttribute('width', innerWidth); s.setAttribute('height', innerHeight); s.pauseAnimations(); }")
            moments = times or [(i / fps, int(1000 / fps)) for i in range(int(seconds * fps))]
            fr = []
            for t, _ in moments:
                pg.evaluate("t => document.querySelector('svg').setCurrentTime(t)", t); pg.wait_for_timeout(20)
                fr.append(Image.open(io.BytesIO(pg.screenshot())).convert("RGB"))
            pg.close()
            out = f"{prefix}-{label}-{v}.gif"
            fr[0].save(out, save_all=True, append_images=fr[1:], duration=[ms for _, ms in moments], loop=0); print(out)
        b.close()

# the owner's decisions, 2026-09-07: see deliverables/THUMBNAILS.md
FINAL = dict(depth="deep-fine", gap=0.5, dim=0.3, order="complements")
FINAL_GLITCH = dict(mode="grey-soft", body="dark-sparks", tagmode="sweep")
TOKENS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deliverables", "assets", "tokens")
ALL = ["the-shadow", "the-dancer", "the-echo", "the-mirror", "the-wanderer", "the-shy", "the-sleeper", "the-glitch"]

def final(frames, out=TOKENS_DIR):
    """The eight token files."""
    os.makedirs(out, exist_ok=True); files = []
    for t in ALL:
        doc = svg(frames, t, FINAL["depth"], FINAL["gap"], FINAL["dim"], FINAL_GLITCH["mode"], "light-red", FINAL_GLITCH["body"], FINAL_GLITCH["tagmode"], FINAL["order"])
        p = os.path.join(out, f"{t}.svg"); open(p, "w").write(doc); files.append((t, "final", p))
        print(f"{p}: {os.path.getsize(p)} bytes")
    return files

GLITCH_SHEET = [("own", "light-red"), ("spectrum", "light-red"), ("luminance", "light-red"), ("grey", "light-red"),
                ("own", "yellow"), ("spectrum", "yellow"), ("luminance", "yellow"), ("grey", "yellow"),
                ("own", "cyan"), ("spectrum", "cyan"), ("own", "purple"), ("spectrum", "purple")]

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokens", nargs="*", default=["the-dancer", "the-echo", "the-glitch"])
    ap.add_argument("--floor", default="deep", help="eight, deep, deep-lit, deep-fine (half-pixel dither), deep-lit-fine")
    ap.add_argument("--tag-gap", type=float, default=1.0, help="space between the tag squares in pixels (0.5 = a half pixel)")
    ap.add_argument("--tag-dim", type=float, default=0.6, help="opacity of the resting tag squares; the live one rises to 1")
    ap.add_argument("--glitch-start", default="light-red", choices=sorted(NAMES), help="the colour the Glitch's cascade starts on")
    ap.add_argument("--glitch-floor", default="own", choices=["own", "spectrum", "luminance", "follow", "grey", "grey-soft", "grey-dusk", "grey-dark"])
    ap.add_argument("--glitch-body", default="cascade", choices=["cascade", "white", "light-grey", "grey", "dark-grey", "static", "dark-static", "sparks", "dark-sparks"], help="his body: the seven-colour cascade, a grey, or grey with bursts of static")
    ap.add_argument("--glitch-tag", default="cascade", choices=["cascade", "sweep", "comet"], help="his tag: one square per loop, or a wave across the row once per breath")
    ap.add_argument("--tag-order", default="hue", help="the order of the seven squares: hue (round the colour wheel), roster, luminance, or seven colour names separated by commas")
    ap.add_argument("--order-strip", help="sheet of the first token with the tag in each of the orders given by --orders")
    ap.add_argument("--orders", nargs="*", default=["hue", "roster", "luminance"], help="label=order entries for --order-strip")
    ap.add_argument("--fps", type=float, default=10); ap.add_argument("--seconds", type=float, default=2 * 2 * LOOP)
    ap.add_argument("--still", type=float, default=1.0, help="the moment (seconds) the sheets are taken at")
    ap.add_argument("--burst-gif", action="store_true", help="GIF frames every 20 ms through the static bursts, every 100 ms elsewhere, two breaths")
    ap.add_argument("--final", action="store_true", help="write the eight token files (FINAL options) to deliverables/assets/tokens/; --lineup and --gif then apply to them")
    ap.add_argument("--out", default="deliverables/assets/mock")
    ap.add_argument("--render"); ap.add_argument("--gif")
    ap.add_argument("--lineup", help="grid sheet of all the tokens given, 240 px and 48 px")
    ap.add_argument("--tag-strip", help="sheet of the first token at tag gaps 1, 0.75, 0.5 and 0.25")
    ap.add_argument("--dim-strip", help="sheet of the first token at the tag dims given by --dims, resting and at the peak")
    ap.add_argument("--dims", nargs="*", type=float, default=[0.6, 0.45, 0.3])
    ap.add_argument("--glitch-sheet", help="grid sheet of the Glitch's floor and start-colour options")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    frames = bt.load_frames(); files = []
    if a.final:
        files = final(frames)
        if a.lineup: lineup(files, a.lineup, t=a.still)
        if a.gif: gif(files, a.gif, a.seconds, a.fps, times=burst_times() if a.burst_gif else None)
        return
    variant = a.floor + (f"-gap{a.tag_gap:g}" if a.tag_gap != 1 else "") + (f"-dim{a.tag_dim:g}" if a.tag_dim != 0.6 else "")
    for t in a.tokens:
        v = variant
        if t == "the-glitch":
            v += f"-{a.glitch_floor}-{a.glitch_start}" if (a.glitch_floor, a.glitch_start) != ("own", "light-red") else ""
            v += f"-{a.glitch_body}" if a.glitch_body != "cascade" else ""
            v += f"-{a.glitch_tag}" if a.glitch_tag != "cascade" else ""
        p = os.path.join(a.out, f"{t}-retro-{v}.svg")
        v += f"-{a.tag_order}" if a.tag_order != "hue" else ""
        p = os.path.join(a.out, f"{t}-retro-{v}.svg")
        open(p, "w").write(svg(frames, t, a.floor, a.tag_gap, a.tag_dim, a.glitch_floor, a.glitch_start, a.glitch_body, a.glitch_tag, a.tag_order)); files.append((t, v, p))
        print(f"{p}: {os.path.getsize(p)} bytes")
    if a.lineup: lineup(files, a.lineup, t=a.still)
    if a.tag_strip:
        strip([(f"{a.tokens[0]} · gap {g:g} px", svg(frames, a.tokens[0], a.floor, g, a.tag_dim)) for g in (1, 0.75, 0.5, 0.25)], a.tag_strip)
    if a.dim_strip:
        strip([(f"{a.tokens[0]} · resting squares at {d:g}", svg(frames, a.tokens[0], a.floor, a.tag_gap, d, order=a.tag_order)) for d in a.dims],
              a.dim_strip, crops=((1.8, "peak"), (0.0, "resting")))
    if a.order_strip:
        names = {"hue": "round the colour wheel (now)", "roster": "token order, Shadow to Sleeper", "luminance": "brightest first"}
        docs = []
        for o in a.orders:
            label, spec = o.split("=", 1) if "=" in o else (names.get(o, o), o)
            docs.append((label, svg(frames, a.tokens[0], a.floor, a.tag_gap, a.tag_dim, order=spec)))
        strip(docs, a.order_strip, crops=((1.8, "peak"),))
    if a.glitch_sheet:
        gs = []
        for mode, start in GLITCH_SHEET:
            p = os.path.join(a.out, f"the-glitch-retro-{variant}-{mode}-{start}.svg")
            open(p, "w").write(svg(frames, "the-glitch", a.floor, a.tag_gap, a.tag_dim, mode, start)); gs.append(("the-glitch", f"{mode} floor, starts {start}", p))
        lineup(gs, a.glitch_sheet)
    if a.render:
        import buddy_badge_mock as bm
        bm.LOOP = LOOP
        bm.render(files, a.render, None)
    if a.gif: gif(files, a.gif, a.seconds, a.fps, times=burst_times() if a.burst_gif else None)

if __name__ == "__main__":
    main()
