#!/usr/bin/env python3
"""Render deliverables/assets/onchain-castles-diagram.png from the emitted castle
JSONs: which original rooms each sample castle stitches together and how the
doors are wired (arrows), with the castle's edge mode.

    python3 tools/castle_diagram.py deliverables/onchain/castles/*.json
"""
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent.parent
full = Image.open(ROOT / "deliverables/assets/castle-map-full.png")   # 5x6 rooms, 320x160 each
GRID = [(x, 0) for x in range(4)] + [(x, y) for y in range(1, 6) for x in range(5)] + [(4, 0)]
RW, RH, GAP, PAD, MX = 320, 160, 60, 12, 150   # MX: side margin for wrap-around arrows


def room(r):
    x, y = GRID[r]
    return full.crop((x * RW, y * RH, (x + 1) * RW, (y + 1) * RH))


def layout(spec):
    """Place rooms on a grid by following the wired exits from the entry."""
    pos, todo = {spec["entry"]: (0, 0)}, [spec["entry"]]
    step = {"E": (1, 0), "W": (-1, 0), "S": (0, 1), "N": (0, -1)}
    while todo:
        r = todo.pop()
        for d, t in spec["exits"].get(str(r), {}).items():
            if t == 255 or t in pos or t == r:
                continue
            gx, gy = pos[r]
            dx, dy = step[d]
            p = (gx + dx, gy + dy)
            while p in pos.values():
                p = (p[0] + dx, p[1] + dy)
            pos[t] = p
            todo.append(t)
    minx, miny = min(x for x, _ in pos.values()), min(y for _, y in pos.values())
    return {r: (x - minx, y - miny) for r, (x, y) in pos.items()}


def arrow(d, x0, y0, x1, y1):
    d.line((x0, y0, x1, y1), fill="red", width=4)
    dx, dy = (x1 - x0), (y1 - y0)
    n = max(abs(dx), abs(dy)) or 1
    ux, uy = dx / n, dy / n
    d.polygon([(x1, y1), (x1 - 12 * ux - 7 * uy, y1 - 12 * uy + 7 * ux), (x1 - 12 * ux + 7 * uy, y1 - 12 * uy - 7 * ux)], fill="red")


def render(metas):
    blocks = []
    for m in metas:
        spec, pos = m["spec"], layout(m["spec"])
        cols = max(x for x, _ in pos.values()) + 1
        rows = max(y for _, y in pos.values()) + 1
        w, h = cols * (RW + GAP) - GAP, rows * (RH + 22 + GAP) - GAP
        img = Image.new("RGB", (max(w, 980) + 2 * MX, h + 60), "white")
        d = ImageDraw.Draw(img)
        wired = sum(1 for ex in spec["exits"].values() for t in ex.values() if t != 255)
        d.text((0, 0), f"{m['name'].upper()}  -  entry room {m['entry']}, {len(m['rooms'])} rooms, {wired} wired doors, "
                       f"edge mode: {m.get('edge_mode', 'wall')}, {m['patch_bytes']} patch bytes"
                       + (", infinite lives" if m["cheat_byte"] & 4 else ""), fill="black")
        org = {}
        for r, (gx, gy) in pos.items():
            x, y = MX + gx * (RW + GAP), 26 + gy * (RH + 22 + GAP)
            img.paste(room(r), (x, y))
            org[r] = (x, y)
            g = GRID[r]
            d.text((x, y + RH + 4), f"room {r} (grid {g[0]},{g[1]})" + ("  <- ENTRY (Tony arrives at the right edge, facing left)" if r == m["entry"] else ""), fill="black")
        for r, ex in spec["exits"].items():
            r = int(r)
            x, y = org[r]
            for dd, t in ex.items():
                if t == 255:
                    continue
                if t == r:                                # self loop
                    if dd == "E":
                        arrow(d, x + RW + 4, y + 60, x + RW + GAP - 8, y + 60); d.text((x + RW + 6, y + 66), "E -> own W edge", fill="red")
                    else:
                        arrow(d, x - 4, y + 100, x - GAP + 8, y + 100); d.text((x - GAP - 40, y + 106), "W -> own E edge", fill="red")
                    continue
                tx, ty = org[t]
                if dd == "E":
                    arrow(d, x + RW + 4, y + 60, tx - 4, ty + 60) if tx > x else arrow(d, x + RW + 4, y + 60, x + RW + GAP - 8, y + 60)
                    if tx <= x:
                        d.text((x + RW + 6, y + 66), f"E -> {t}", fill="red")
                elif dd == "W":
                    arrow(d, x - 4, y + 100, tx + RW + 4, ty + 100) if tx < x else arrow(d, x - 4, y + 100, x - GAP + 8, y + 100)
                    if tx >= x:
                        d.text((x - GAP + 6, y + 106), f"W -> {t}", fill="red")
                elif dd == "S":
                    arrow(d, x + RW // 2, y + RH + 20, tx + RW // 2, ty - 4)
                elif dd == "N":
                    arrow(d, x + RW // 2 + 20, y - 4, tx + RW // 2 + 20, ty + RH + 20)
        blocks.append(img)
    W = max(b.width for b in blocks) + 2 * PAD
    H = sum(b.height for b in blocks) + PAD * (len(blocks) + 1) + 70
    out = Image.new("RGB", (W, H), "white")
    y = PAD
    for b in blocks:
        out.paste(b, (PAD, y)); y += b.height + PAD
    d = ImageDraw.Draw(out)
    d.text((PAD, y), "Every room, tile, sprite and note of music is already in the on-chain PRG; a castle rewrites the", fill="black")
    d.text((PAD, y + 14), "'which room is behind this edge' bytes, the colour scheme, a 10-byte cheat-state fix, and installs a 75-byte", fill="black")
    d.text((PAD, y + 28), "edge guard (sealed exits are NOT walls in the engine): 'wall' pushes Tony back, 'void' costs a life; a ring", fill="black")
    d.text((PAD, y + 42), "with every open edge wired ('infinite') never triggers it.  Verified by playing each castle on minimal64.", fill="black")
    out.save(ROOT / "deliverables/assets/onchain-castles-diagram.png")
    print("saved", out.size)


if __name__ == "__main__":
    render([json.loads(Path(p).read_text()) for p in sys.argv[1:]])   # in the order given
