#!/usr/bin/env python3
"""
buddy_badge_mock.py - mock-ups of a token image with a colour badge (a look-see, not the token's SVG).

Seven horizontal stripes in the token colours in a small self-contained area at the
bottom right (or a bar along the bottom); the token's own stripe pulses slowly with a
soft glow; the Glitch's pulse walks through all seven in turn. Reuses the sprite data
and the idle animation of tools/buddy_thumbnail.py. Writes SVGs; --render draws them
with Chromium at 240, 96 and 48 px into a sheet, and --gif a 3-second animation of one.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buddy_thumbnail as bt

# the seven token colours, warm to cool (a rainbow feel without the Commodore five)
STRIPES = [("light-red", "#c46c71", "the-shy"), ("yellow", "#edf171", "the-echo"), ("green", "#56ac4d", "the-wanderer"),
           ("cyan", "#75cec8", "the-dancer"), ("light-blue", "#706deb", "the-mirror"), ("blue", "#2e2c9b", "the-shadow"),
           ("purple", "#8e3c97", "the-sleeper")]
LOOP = bt.PHASE_SECONDS * len(bt.PHASES)      # the idle dance: 1.8 s
PULSE = f"{2 * LOOP:g}s"                        # one breath = two dance loops (3.6 s): swells over one, fades over the next
CASCADE = f"{7 * LOOP:g}s"                      # the Glitch: each stripe takes one loop (1.8 s), seven in 12.6 s
BLINK_PERIOD, BLINK = bt.BLINK_PERIOD, bt.BLINK

def figure(frames, sc, fill, glitch):
    """The idle-dance paths, as in buddy_thumbnail.svg."""
    size, (bx, by) = sc["size"], sc["buddy"]
    n = len(bt.PHASES)
    keytimes = ";".join(f"{i / n:.4f}" for i in range(n)) + ";1"
    dur = f"{bt.PHASE_SECONDS * n:g}s"
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
            cols = ";".join(h for _, h, _ in STRIPES) + ";" + STRIPES[0][1]
            parts.append(f'<animate attributeName="fill" values="{cols}" keyTimes="{kt}" calcMode="discrete" dur="{CASCADE}" repeatCount="indefinite"/>')
        parts.append('</path>')
    body = "\n".join(parts)
    if glitch:
        times = [0.0] + [at / BLINK_PERIOD for at, _ in BLINK] + [1.0]
        vals = [1] + [val for _, val in BLINK] + [1]
        body = (f'<g><animate attributeName="opacity" values="{";".join(str(v) for v in vals)}" keyTimes="{";".join(f"{t:.4f}" for t in times)}" '
                f'calcMode="discrete" dur="{BLINK_PERIOD:g}s" repeatCount="indefinite"/>\n' + body + '\n</g>')
    return body

def stripes(x, y, w, h, mine, glitch, rx=1, outline=True):
    """Seven stripes h/9 tall each inside a box; the token's stripe breathes with a glow, in time with the dance."""
    step = h / 9.0
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="#000"' + (' stroke="#2a2a2a" stroke-width="0.5"' if outline else '') + '/>']
    for i, (name, hexc, token) in enumerate(STRIPES):
        sy = y + step * (i + 1)
        own = (token == mine)
        if own or glitch:
            # a glow behind the stripe: the same colour, blurred, breathing
            if glitch:
                # the Glitch: a slow cascade, each stripe swelling over one dance loop and fading over the next
                kt = ";".join(f"{k / 7:.4f}" for k in range(8))
                fade = f'<animate attributeName="opacity" values="{";".join("0.9" if k == i else "0" for k in range(7))};{"0.9" if i == 0 else "0"}" keyTimes="{kt}" dur="{CASCADE}" repeatCount="indefinite"/>'
                bright = f'<animate attributeName="opacity" values="{";".join("1" if k == i else "0.55" for k in range(7))};{"1" if i == 0 else "0.55"}" keyTimes="{kt}" dur="{CASCADE}" repeatCount="indefinite"/>'
            else:
                # one breath per two dance loops, peaking on the loop's turn; a smooth ease both ways
                fade = f'<animate attributeName="opacity" values="0;0.9;0" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" dur="{PULSE}" repeatCount="indefinite"/>'
                bright = f'<animate attributeName="opacity" values="0.55;1;0.55" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" dur="{PULSE}" repeatCount="indefinite"/>'
            parts.append(f'<rect x="{x + 1}" y="{sy:.3f}" width="{w - 2}" height="{step:.3f}" fill="{hexc}" filter="url(#glow)" opacity="0">{fade}</rect>')
            parts.append(f'<rect x="{x + 1}" y="{sy:.3f}" width="{w - 2}" height="{step:.3f}" fill="{hexc}" opacity="0.55">{bright}</rect>')
        else:
            parts.append(f'<rect x="{x + 1}" y="{sy:.3f}" width="{w - 2}" height="{step:.3f}" fill="{hexc}" opacity="0.55"/>')
    return "\n".join(parts)

def svg(frames, token, variant, size=48):
    glitch = (token == "the-glitch")
    hexc = bt.GLITCH_CYCLE[0] if glitch else dict((t, h) for _, h, t in STRIPES)[token]
    sc = bt.compose(frames, "plain", size)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" shape-rendering="crispEdges">',
             '<defs><filter id="glow" x="-50%" y="-100%" width="200%" height="300%"><feGaussianBlur stdDeviation="1.2"/></filter></defs>',
             f'<rect width="{size}" height="{size}" fill="#000"/>']
    parts.append(figure(frames, sc, hexc, glitch))
    if variant == "badge":            # a self-contained rectangle, bottom right
        parts.append(stripes(size - 19, size - 12, 16, 9, token, glitch))
    elif variant == "square":         # a small square, bottom right
        parts.append(stripes(size - 12, size - 12, 9, 9, token, glitch))
    elif variant == "bar":            # a bar along the bottom, edge to edge
        parts.append(stripes(-1, size - 8, size + 2, 9, token, glitch, rx=0))
    elif variant == "floor":          # the same bar as a floor: no outline, the feet on its top line
        parts.append(stripes(-1, size - 8, size + 2, 9, token, glitch, rx=0, outline=False))
    parts.append('</svg>')
    return "\n".join(parts) + "\n"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="deliverables/assets/mock")
    ap.add_argument("--tokens", nargs="*", default=["the-dancer", "the-glitch"])
    ap.add_argument("--variants", nargs="*", default=["floor"])
    ap.add_argument("--render", help="write a PNG sheet of every SVG at 240, 96 and 48 px (Chromium)")
    ap.add_argument("--gif", help="write GIFs of every SVG at 240 px (Chromium): the token's breath, the Glitch's cascade; FILE is a prefix")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    frames = bt.load_frames()
    files = []
    for t in a.tokens:
        for v in a.variants:
            p = os.path.join(a.out, f"{t}-{v}.svg")
            open(p, "w").write(svg(frames, t, v)); files.append((t, v, p)); print(f"{p}: {os.path.getsize(p)} bytes")
    if a.render or a.gif:
        render(files, a.render, a.gif)

def render(files, sheet, gif):
    import asyncio, io
    from playwright.async_api import async_playwright
    from PIL import Image, ImageDraw
    exe = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
    async def go():
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path=exe if os.path.exists(exe) else None)
            shots = {}
            for t, v, path in files:
                for px in (240, 96, 48):
                    pg = await b.new_page(viewport={"width": px, "height": px})
                    await pg.goto("file://" + os.path.abspath(path)); await pg.wait_for_timeout(200)
                    await pg.evaluate("t => { const s=document.documentElement; s.pauseAnimations(); s.setCurrentTime(t); }", 1.0)
                    await pg.wait_for_timeout(60)
                    shots[(t, v, px)] = Image.open(io.BytesIO(await pg.screenshot())).convert("RGB"); await pg.close()
            gifs = {}
            if gif:
                for t, v, path in files:
                    secs = 7 * LOOP if t == "the-glitch" else 2 * 2 * LOOP      # the whole cascade, or two breaths
                    fps = 8 if t == "the-glitch" else 10
                    pg = await b.new_page(viewport={"width": 240, "height": 240}); await pg.goto("file://" + os.path.abspath(path)); await pg.wait_for_timeout(200)
                    fr = []
                    for i in range(int(secs * fps)):
                        await pg.evaluate("t => { const s=document.documentElement; s.pauseAnimations(); s.setCurrentTime(t); }", i / fps)
                        await pg.wait_for_timeout(30)
                        fr.append(Image.open(io.BytesIO(await pg.screenshot())).convert("RGB"))
                    await pg.close(); gifs[(t, v)] = (fr, fps)
            await b.close()
            return shots, gifs
    shots, gifs = asyncio.run(go())
    if sheet:
        pad, th = 14, 20
        rows = [(t, v) for t, v, _ in files]
        W = pad + 240 + pad + 96 + pad + 48 + pad + 260
        im = Image.new("RGB", (W, pad + len(rows) * (240 + th + pad)), (24, 24, 24)); d = ImageDraw.Draw(im)
        for r, (t, v) in enumerate(rows):
            y = pad + r * (240 + th + pad)
            d.text((pad, y + 2), f"{t} · {v}: 240 px, 96 px, 48 px (real thumbnail size)", fill=(230, 230, 230))
            x = pad
            for px in (240, 96, 48):
                im.paste(shots[(t, v, px)], (x, y + th + (240 - px))); x += px + pad
        im.save(sheet); print(sheet)
    for (t, v), (fr, fps) in gifs.items():
        path = f"{gif}-{t}-{v}.gif"
        fr[0].save(path, save_all=True, append_images=fr[1:], duration=int(1000 / fps), loop=0); print(path)

if __name__ == "__main__":
    main()
