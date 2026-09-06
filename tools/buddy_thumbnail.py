#!/usr/bin/env python3
"""Token thumbnail prototype: the buddy's idle "dance" as an animated SVG.

The buddy standing still runs the game's idling animation: four sprite frames
played in the order A, B, A, B, C, D, fifteen PAL frames (0.3 s) each, so one
loop is 1.8 s (src/kickass/animations.asm, idlingRightAnimation*). This tool
rebuilds that loop from the very same sprite bytes the PRG carries
(build/sprites/tony-idling-right_*.bin, the left 24-pixel column of each
frame: top half then bottom half) and emits one SVG per colour:

  * 48x64 pixel canvas, black field, the buddy at (12,6), 24x42 pixels
  * a 16-pixel brick floor under his feet, taken from the level charset
    (the same course the Chamber uses for its floor), in Tony's light grey
  * four <path> layers, one per sprite frame, in run-length pixel rows,
    switched with SMIL <animate opacity> in discrete steps

Frame A is drawn first so that a viewer that shows a still image (a
marketplace grid, a cached thumbnail) shows the pose the loop starts on.

Usage:  tools/buddy_thumbnail.py [--out deliverables/assets] [colour ...]
        tools/buddy_thumbnail.py --strip deliverables/assets/buddy-idle-phases.png
Colour names are C64 palette names (cyan, light-green, ...) or indices 0-15.
"""
import argparse
import os
import sys

# Colodore palette, the emulator's own (index: (name, rgb))
PALETTE = [
    ("black", "#000000"), ("white", "#ffffff"), ("red", "#813338"), ("cyan", "#75cec8"),
    ("purple", "#8e3c97"), ("green", "#56ac4d"), ("blue", "#2e2c9b"), ("yellow", "#edf171"),
    ("orange", "#8e5029"), ("brown", "#553800"), ("light-red", "#c46c71"), ("dark-grey", "#4a4a4a"),
    ("grey", "#7b7b7b"), ("light-green", "#a9ff9f"), ("light-blue", "#706deb"), ("light-grey", "#b2b2b2"),
]
FLOOR_COLOUR = PALETTE[15][1]          # light grey, Tony's own colour in the classic scheme
SPRITE_DIR = "build/sprites"
CHARSET = "build/charpad/demo-level-charset.bin"   # ink = 1 bits (the game negates at load)
COURSE_A = ([0x31, 0x32, 0x33, 0x34, 0x35, 0x36], [0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C])  # one 6-char brick course
PHASES = [2, 3, 2, 3, 0, 1]            # sprite frame per phase: A B A B C D  (frame = bank pair index)
PHASE_SECONDS = 15 / 50.0              # fifteen PAL frames
BUDDY_X, BUDDY_Y = 12, 6
CANVAS_W, CANVAS_H = 48, 64
FLOOR_Y = 48


def sprite_rows(data):
    """63 sprite bytes -> 21 rows of 24 booleans."""
    rows = []
    for r in range(21):
        b = data[r * 3:r * 3 + 3]
        bits = (b[0] << 16) | (b[1] << 8) | b[2]
        rows.append([(bits >> (23 - x)) & 1 for x in range(24)])
    return rows


def load_frames(sprite_dir):
    """Four idle frames, each 42 rows x 24 px, in bank order (frame n = bank sprites 2n, 2n+1)."""
    frames = []
    for n in range(4):
        top = open(os.path.join(sprite_dir, f"tony-idling-right_{4 * n}.bin"), "rb").read()
        bot = open(os.path.join(sprite_dir, f"tony-idling-right_{4 * n + 2}.bin"), "rb").read()
        frames.append(sprite_rows(top) + sprite_rows(bot))
    return frames


def floor_rows(charset_path):
    """16 rows x 48 px: one brick course, six chars wide, two chars tall."""
    cs = open(charset_path, "rb").read()
    rows = []
    for line in COURSE_A:
        for y in range(8):
            row = []
            for code in line:
                byte = cs[code * 8 + y]
                row += [(byte >> (7 - x)) & 1 for x in range(8)]
            rows.append(row)
    return rows


def runs_path(rows, ox, oy):
    """Pixel rows -> compact SVG path of horizontal runs."""
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            if row[x]:
                x0 = x
                while x < len(row) and row[x]:
                    x += 1
                out.append(f"M{ox + x0} {oy + y}h{x - x0}v1h-{x - x0}z")
            else:
                x += 1
    return "".join(out)


def svg(frames, floor, colour_hex):
    n = len(PHASES)
    keytimes = ";".join(f"{i / n:.4f}" for i in range(n)) + ";1"
    dur = f"{PHASE_SECONDS * n:g}s"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" shape-rendering="crispEdges">',
             f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#000"/>',
             f'<path fill="{FLOOR_COLOUR}" d="{runs_path(floor, 0, FLOOR_Y)}"/>']
    # draw the frames in the order they first appear (A first, so a still render shows A)
    order = []
    for f in PHASES:
        if f not in order:
            order.append(f)
    for f in order:
        values = ";".join("1" if p == f else "0" for p in PHASES) + ";" + ("1" if PHASES[0] == f else "0")
        parts.append(f'<path fill="{colour_hex}" d="{runs_path(frames[f], BUDDY_X, BUDDY_Y)}">')
        parts.append(f'<animate attributeName="opacity" values="{values}" keyTimes="{keytimes}" '
                     f'calcMode="discrete" dur="{dur}" repeatCount="indefinite"/>')
        parts.append('</path>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def phase_strip(frames, floor, colour_hex, path, scale=4):
    from PIL import Image, ImageDraw
    rgb = tuple(int(colour_hex[i:i + 2], 16) for i in (1, 3, 5))
    grey = tuple(int(FLOOR_COLOUR[i:i + 2], 16) for i in (1, 3, 5))
    gap = 4
    im = Image.new("RGB", (len(PHASES) * (CANVAS_W * scale + gap) - gap, CANVAS_H * scale), "black")
    for i, f in enumerate(PHASES):
        ox = i * (CANVAS_W * scale + gap)
        for y, row in enumerate(floor):
            for x, v in enumerate(row):
                if v:
                    im.paste(grey, (ox + x * scale, (FLOOR_Y + y) * scale, ox + (x + 1) * scale, (FLOOR_Y + y + 1) * scale))
        for y, row in enumerate(frames[f]):
            for x, v in enumerate(row):
                if v:
                    im.paste(rgb, (ox + (BUDDY_X + x) * scale, (BUDDY_Y + y) * scale,
                                   ox + (BUDDY_X + x + 1) * scale, (BUDDY_Y + y + 1) * scale))
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("colours", nargs="*", default=["cyan", "light-green", "light-blue"])
    ap.add_argument("--out", default="deliverables/assets")
    ap.add_argument("--strip", help="also write a PNG strip of the six phases (first colour)")
    ap.add_argument("--sprites", default=SPRITE_DIR)
    ap.add_argument("--charset", default=CHARSET)
    a = ap.parse_args()
    frames = load_frames(a.sprites)
    floor = floor_rows(a.charset)
    names = {n: h for n, h in PALETTE}
    for c in a.colours:
        name, hexval = (PALETTE[int(c)] if c.isdigit() else (c, names[c]))
        path = os.path.join(a.out, f"buddy-idle-{name}.svg")
        open(path, "w").write(svg(frames, floor, hexval))
        print(f"{path}: {os.path.getsize(path)} bytes")
    if a.strip:
        first = a.colours[0]
        hexval = PALETTE[int(first)][1] if first.isdigit() else names[first]
        phase_strip(frames, floor, hexval, a.strip)
        print(f"{a.strip}: {os.path.getsize(a.strip)} bytes")


if __name__ == "__main__":
    main()
