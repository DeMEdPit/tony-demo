#!/usr/bin/env python3
"""Token thumbnail prototype: the buddy's idle "dance" as an animated SVG.

The buddy standing still runs the game's idling animation: four sprite frames
played in the order A, B, A, B, C, D, fifteen PAL frames (0.3 s) each, so one
loop is 1.8 s (src/kickass/animations.asm, idlingRightAnimation*). This tool
rebuilds that loop from the very same sprite bytes the PRG carries
(build/sprites/tony-idling-right_*.bin, the left 24-pixel column of each
frame: top half then bottom half) and emits one SVG per colour.

Two layouts, both on a square black canvas (56x56 pixels by default):

  floor  (default) a brick course from the level charset, the Chamber's own
         floor, sits flush on the bottom edge and the buddy stands flush on
         it: his lowest ink row is the row above the bricks' top line.
  plain  no bricks; the buddy alone, centred.

Each frame is one <path> of run-length pixel rows; the four are switched with
SMIL <animate opacity> in discrete steps. Frame A is drawn first so a viewer
that shows a still image (a marketplace grid, a cached thumbnail) shows the
pose the loop starts on.

Usage:  tools/buddy_thumbnail.py [--layout floor|plain] [--size 56]
                                 [--out deliverables/assets] [colour ...]
        tools/buddy_thumbnail.py --strip PNG        six phases of the loop
        tools/buddy_thumbnail.py --sheet PNG SPEC... comparison sheet, SPEC =
                                 colour[:layout], e.g. cyan:plain
Colour names are C64 palette names (cyan, light-green, ...) or indices 0-15.
"""
import argparse
import os

# Colodore palette, the emulator's own (index: (name, rgb))
PALETTE = [
    ("black", "#000000"), ("white", "#ffffff"), ("red", "#813338"), ("cyan", "#75cec8"),
    ("purple", "#8e3c97"), ("green", "#56ac4d"), ("blue", "#2e2c9b"), ("yellow", "#edf171"),
    ("orange", "#8e5029"), ("brown", "#553800"), ("light-red", "#c46c71"), ("dark-grey", "#4a4a4a"),
    ("grey", "#7b7b7b"), ("light-green", "#a9ff9f"), ("light-blue", "#706deb"), ("light-grey", "#b2b2b2"),
]
NAMES = {n: h for n, h in PALETTE}
FLOOR_COLOUR = PALETTE[15][1]          # light grey, Tony's own colour in the classic scheme
SPRITE_DIR = "build/sprites"
CHARSET = "build/charpad/demo-level-charset.bin"   # ink = 1 bits (the game negates at load)
# the two 6-char brick courses the Chamber alternates along its floor (tools/build_chamber_room.py)
COURSE_A = ([0x31, 0x32, 0x33, 0x34, 0x35, 0x36], [0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C])
COURSE_B = ([0x25, 0x26, 0x27, 0x28, 0x29, 0x2A], [0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30])
PHASES = [2, 3, 2, 3, 0, 1]            # sprite frame per phase: A B A B C D  (frame = bank pair index)
PHASE_SECONDS = 15 / 50.0              # fifteen PAL frames
SPRITE_W = 24
FLOOR_OFFSET = 3                       # start the course mid-run so the seam between the two courses falls
                                       # under the buddy, centred, and both edges cut through a brick
DEFAULT_SIZE = 56                      # square canvas; a multiple of 8 so the floor is whole characters


def sprite_rows(data):
    """63 sprite bytes -> 21 rows of 24 booleans."""
    rows = []
    for r in range(21):
        b = data[r * 3:r * 3 + 3]
        bits = (b[0] << 16) | (b[1] << 8) | b[2]
        rows.append([(bits >> (23 - x)) & 1 for x in range(24)])
    return rows


def load_frames(sprite_dir=SPRITE_DIR):
    """Four idle frames, each 42 rows x 24 px, in bank order (frame n = bank sprites 2n, 2n+1)."""
    frames = []
    for n in range(4):
        top = open(os.path.join(sprite_dir, f"tony-idling-right_{4 * n}.bin"), "rb").read()
        bot = open(os.path.join(sprite_dir, f"tony-idling-right_{4 * n + 2}.bin"), "rb").read()
        frames.append(sprite_rows(top) + sprite_rows(bot))
    return frames


def ink_box(frames):
    """(first, last) ink row over all frames: the buddy's hat top and his feet."""
    rows = [y for f in frames for y, row in enumerate(f) if any(row)]
    return min(rows), max(rows)


def floor_rows(width, charset_path=CHARSET):
    """One brick course, `width` px wide, blank rows trimmed off the bottom."""
    cs = open(charset_path, "rb").read()
    rows = []
    for line in range(2):
        for y in range(8):
            row = []
            for c in range(width // 8):
                k = c + FLOOR_OFFSET
                code = (COURSE_A if (k // 6) % 2 == 0 else COURSE_B)[line][k % 6]
                byte = cs[code * 8 + y]
                row += [(byte >> (7 - x)) & 1 for x in range(8)]
            rows.append(row)
    while rows and not any(rows[-1]):
        rows.pop()
    return rows


def compose(frames, layout, size):
    """Where things go: (buddy_x, buddy_y, floor rows or None, floor_y)."""
    top, feet = ink_box(frames)
    bx = (size - SPRITE_W) // 2
    if layout == "floor":
        floor = floor_rows(size)
        floor_y = size - len(floor)
        by = floor_y - 1 - feet                  # feet on the row above the bricks' top line
        return bx, by, floor, floor_y
    if layout == "plain":
        by = (size - (feet - top + 1)) // 2 - top
        return bx, by, None, None
    raise ValueError(layout)


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


def svg(frames, colour_hex, layout="floor", size=DEFAULT_SIZE):
    bx, by, floor, floor_y = compose(frames, layout, size)
    n = len(PHASES)
    keytimes = ";".join(f"{i / n:.4f}" for i in range(n)) + ";1"
    dur = f"{PHASE_SECONDS * n:g}s"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" shape-rendering="crispEdges">',
             f'<rect width="{size}" height="{size}" fill="#000"/>']
    if floor:
        parts.append(f'<path fill="{FLOOR_COLOUR}" d="{runs_path(floor, 0, floor_y)}"/>')
    order = []                                   # frames in order of first appearance: A first
    for f in PHASES:
        if f not in order:
            order.append(f)
    for f in order:
        values = ";".join("1" if p == f else "0" for p in PHASES) + ";" + ("1" if PHASES[0] == f else "0")
        parts.append(f'<path fill="{colour_hex}" d="{runs_path(frames[f], bx, by)}">')
        parts.append(f'<animate attributeName="opacity" values="{values}" keyTimes="{keytimes}" '
                     f'calcMode="discrete" dur="{dur}" repeatCount="indefinite"/>')
        parts.append('</path>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def raster(frames, colour_hex, layout, size, frame, scale):
    """One still of the composition (a given sprite frame) as a PIL image."""
    from PIL import Image
    rgb = tuple(int(colour_hex[i:i + 2], 16) for i in (1, 3, 5))
    grey = tuple(int(FLOOR_COLOUR[i:i + 2], 16) for i in (1, 3, 5))
    bx, by, floor, floor_y = compose(frames, layout, size)
    im = Image.new("RGB", (size, size), "black")
    px = im.load()
    if floor:
        for y, row in enumerate(floor):
            for x, v in enumerate(row):
                if v:
                    px[x, floor_y + y] = grey
    for y, row in enumerate(frames[frame]):
        for x, v in enumerate(row):
            if v and 0 <= bx + x < size and 0 <= by + y < size:
                px[bx + x, by + y] = rgb
    return im.resize((size * scale, size * scale), Image.NEAREST)


def phase_strip(frames, colour_hex, layout, size, path, scale=4):
    from PIL import Image
    gap = 4
    im = Image.new("RGB", (len(PHASES) * (size * scale + gap) - gap, size * scale), "black")
    for i, f in enumerate(PHASES):
        im.paste(raster(frames, colour_hex, layout, size, f, scale), (i * (size * scale + gap), 0))
    im.save(path)


def sheet(frames, specs, size, path, scale=3, columns=6):
    """Comparison sheet: one still (frame A) per spec, labelled."""
    from PIL import Image, ImageDraw
    cell = size * scale
    pad, text_h = 10, 14
    rows = (len(specs) + columns - 1) // columns
    im = Image.new("RGB", (columns * (cell + pad) + pad, rows * (cell + pad + text_h) + pad), "#202020")
    d = ImageDraw.Draw(im)
    for i, (label, colour_hex, layout) in enumerate(specs):
        x = pad + (i % columns) * (cell + pad)
        y = pad + (i // columns) * (cell + pad + text_h)
        im.paste(raster(frames, colour_hex, layout, size, PHASES[0], scale), (x, y))
        d.text((x, y + cell + 1), label, fill="white")
    im.save(path)


def colour(c):
    return PALETTE[int(c)] if c.isdigit() else (c, NAMES[c])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("colours", nargs="*", default=["cyan"])
    ap.add_argument("--layout", default="floor", choices=("floor", "plain"))
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE)
    ap.add_argument("--out", default="deliverables/assets")
    ap.add_argument("--strip", help="write a PNG strip of the six phases (first colour) instead of SVGs")
    ap.add_argument("--sheet", help="write a comparison PNG of the given colour[:layout] specs instead of SVGs")
    ap.add_argument("--sprites", default=SPRITE_DIR)
    a = ap.parse_args()
    frames = load_frames(a.sprites)
    if a.sheet:
        specs = []
        for spec in a.colours:
            c, _, lay = spec.partition(":")
            name, hexval = colour(c)
            specs.append((f"{name} ({PALETTE.index((name, hexval))}) {lay or a.layout}", hexval, lay or a.layout))
        sheet(frames, specs, a.size, a.sheet)
        print(f"{a.sheet}: {os.path.getsize(a.sheet)} bytes")
        return
    if a.strip:
        name, hexval = colour(a.colours[0])
        phase_strip(frames, hexval, a.layout, a.size, a.strip)
        print(f"{a.strip}: {os.path.getsize(a.strip)} bytes")
        return
    for c in a.colours:
        name, hexval = colour(c)
        suffix = "" if a.layout == "floor" else f"-{a.layout}"
        path = os.path.join(a.out, f"buddy-idle-{name}{suffix}.svg")
        open(path, "w").write(svg(frames, hexval, a.layout, a.size))
        print(f"{path}: {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    main()
