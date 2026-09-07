#!/usr/bin/env python3
"""
buddy_retro_svg.py - the retro layout as an animated SVG (a mock, not the token files): the seven colours
as a row of squares top left, the buddy dancing in the middle, a dithered gradient floor under his feet.
His own square breathes in time with the dance (one breath per two loops); the Glitch's squares cascade
one loop each and his body follows. Everything on the 48-pixel grid, drawn as pixel runs.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buddy_thumbnail as bt
import buddy_retro_mock as rm

LOOP = bt.PHASE_SECONDS * len(bt.PHASES)          # 1.8 s
BREATH = f"{2 * LOOP:g}s"                          # 3.6 s
CASCADE = f"{7 * LOOP:g}s"                         # 12.6 s
SIZE = 48

def floor_rows(token, depth):
    colour, ramp = rm.TOKENS[token]
    fr = ramp[ramp.index(colour):]
    if "lit" in depth:
        lighter = ramp[max(0, ramp.index(colour) - 1)]
        if lighter != colour: fr = [lighter] + fr
    h = 11 if "deep" in depth else 8
    scale = 2 if "fine" in depth else 1              # "fine": the floor dithered on a half-pixel grid
    return rm.dither_column_fine(SIZE * scale, h * scale, fr), h, scale

def floor_paths(rows, y0, scale=1):
    """One path per palette colour in the band, as pixel runs (scaled down when the band is on a finer grid)."""
    parts = []
    for c in sorted(set(v for row in rows for v in row)):
        if c == 0: continue
        mask = [[1 if v == c else 0 for v in row] for row in rows]
        parts.append(f'<path fill="{rm.PAL[c]}" d="{bt.runs_path(mask, 0, y0 * scale)}"/>')
    body = "\n".join(parts)
    return body if scale == 1 else f'<g transform="scale({1 / scale:g})">\n{body}\n</g>'

def figure_paths(frames, fill, bx, by, glitch):
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
        if glitch:
            kt = ";".join(f"{k / 7:.4f}" for k in range(8))
            cols = ";".join(rm.PAL[c] for c in rm.STRIP) + ";" + rm.PAL[rm.STRIP[0]]
            parts.append(f'<animate attributeName="fill" values="{cols}" keyTimes="{kt}" calcMode="discrete" dur="{CASCADE}" repeatCount="indefinite"/>')
        parts.append('</path>')
    body = "\n".join(parts)
    if glitch:
        times = [0.0] + [at / bt.BLINK_PERIOD for at, _ in bt.BLINK] + [1.0]
        vals = [1] + [val for _, val in bt.BLINK] + [1]
        body = (f'<g><animate attributeName="opacity" values="{";".join(str(v) for v in vals)}" keyTimes="{";".join(f"{t:.4f}" for t in times)}" '
                f'calcMode="discrete" dur="{bt.BLINK_PERIOD:g}s" repeatCount="indefinite"/>\n' + body + '\n</g>')
    return body

def tag(token, glitch):
    colour = rm.TOKENS.get(token, (None, None))[0]
    parts = []
    for i, c in enumerate(rm.STRIP):
        x = 2 + i * 3
        own = (c == colour)
        if own or glitch:
            if glitch:
                kt = ";".join(f"{k / 7:.4f}" for k in range(8))
                glow = f'<animate attributeName="opacity" values="{";".join("0.9" if k == i else "0" for k in range(7))};{"0.9" if i == 0 else "0"}" keyTimes="{kt}" dur="{CASCADE}" repeatCount="indefinite"/>'
                bright = f'<animate attributeName="opacity" values="{";".join("1" if k == i else "0.5" for k in range(7))};{"1" if i == 0 else "0.5"}" keyTimes="{kt}" dur="{CASCADE}" repeatCount="indefinite"/>'
                base = "0.5"
            else:
                glow = f'<animate attributeName="opacity" values="0;0.9;0" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" dur="{BREATH}" repeatCount="indefinite"/>'
                bright = f'<animate attributeName="opacity" values="0.6;1;0.6" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" dur="{BREATH}" repeatCount="indefinite"/>'
                base = "0.6"
            parts.append(f'<rect x="{x}" y="2" width="2" height="2" fill="{rm.PAL[c]}" filter="url(#glow)" opacity="0">{glow}</rect>')
            parts.append(f'<rect x="{x}" y="2" width="2" height="2" fill="{rm.PAL[c]}" opacity="{base}">{bright}</rect>')
        else:
            parts.append(f'<rect x="{x}" y="2" width="2" height="2" fill="{rm.PAL[c]}"' + (' opacity="0.6"' if not glitch else ' opacity="0.5"') + '/>')
    return "\n".join(parts)

def svg(frames, token, depth="deep"):
    glitch = (token == "the-glitch")
    rows, h, scale = floor_rows("the-shy" if glitch else token, depth)
    fill = rm.PAL[rm.STRIP[0]] if glitch else rm.PAL[rm.TOKENS[token][0]]
    fh = bt.ink_box(frames)[1] + 1; fw = len(frames[0][0])
    bx, by = (SIZE - fw) // 2, SIZE - h - fh
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" shape-rendering="crispEdges">',
             '<defs><filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="1.1"/></filter></defs>',
             f'<rect width="{SIZE}" height="{SIZE}" fill="#000"/>',
             floor_paths(rows, SIZE - h, scale), tag(token, glitch), figure_paths(frames, fill, bx, by, glitch), '</svg>']
    return "\n".join(parts) + "\n"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokens", nargs="*", default=["the-dancer", "the-echo", "the-glitch"])
    ap.add_argument("--floor", default="deep", help="eight, deep, deep-lit, deep-fine (half-pixel dither), deep-lit-fine")
    ap.add_argument("--out", default="deliverables/assets/mock")
    ap.add_argument("--render"); ap.add_argument("--gif")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    frames = bt.load_frames(); files = []
    for t in a.tokens:
        p = os.path.join(a.out, f"{t}-retro-{a.floor}.svg"); open(p, "w").write(svg(frames, t, a.floor)); files.append((t, a.floor, p))
        print(f"{p}: {os.path.getsize(p)} bytes")
    if a.render or a.gif:
        import buddy_badge_mock as bm
        bm.LOOP = LOOP
        bm.render(files, a.render, a.gif)

if __name__ == "__main__":
    main()
