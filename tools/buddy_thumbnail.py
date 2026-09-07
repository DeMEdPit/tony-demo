#!/usr/bin/env python3
"""Token thumbnail prototype: the buddy's idle "dance" as an animated SVG.

The buddy standing still runs the game's idling animation: four sprite frames
played in the order A, B, A, B, C, D, fifteen PAL frames (0.3 s) each, so one
loop is 1.8 s (src/kickass/animations.asm, idlingRightAnimation*). This tool
rebuilds that loop from the very same sprite bytes the PRG carries
(build/sprites/tony-idling-right_*.bin, the left 24-pixel column of each
frame: top half then bottom half) and emits one SVG per colour.

Layouts, all on a square black canvas:

  plain  (default, 48 px: the owner's pick) the buddy alone, centred.
  floor  a brick course from the level charset, the Chamber's own floor,
         flush on the bottom edge, the buddy standing flush on it: his
         lowest ink row is the row above the bricks' top line.

Each frame is one <path> of run-length pixel rows; the four are switched with
SMIL <animate opacity> in discrete steps. Frame A is drawn first so a viewer
that shows a still image (a marketplace grid, a cached thumbnail) shows the
pose the loop starts on.

  bricks a full-width course of the small running-bond bricks, no seam.
  arch   an arched doorway drawn in the level's dotted stone, small bricks
         around it (64 px); arch-brick: the doorway cut out of the brick wall.
The chosen files carry the bare name (buddy-idle-<colour>.svg); any other
layout or size gets a -<layout>-<size> suffix.

Usage:  tools/buddy_thumbnail.py [--layout LAYOUT] [--size 48]
                                 [--out deliverables/assets] [colour ...]
        tools/buddy_thumbnail.py --strip PNG        six phases of the loop
        tools/buddy_thumbnail.py --sheet PNG SPEC... comparison sheet, SPEC =
                                 colour[:layout[:size]], e.g. cyan:plain:40
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
SMALL_BRICKS = (0xAD, 0xAE, 0xAF)       # the running-bond brick wall (room 0,3's left wall), repeats every 24 px
PHASES = [2, 3, 2, 3, 0, 1]            # sprite frame per phase: A B A B C D  (frame = bank pair index)
PHASE_SECONDS = 15 / 50.0              # fifteen PAL frames
SPRITE_W = 24
FLOOR_OFFSET = 3                       # start the course mid-run so the seam between the two courses falls
                                       # under the buddy, centred, and both edges cut through a brick
DEFAULT_LAYOUT, DEFAULT_SIZE = "plain", 48   # the owner's pick: the buddy alone, the middle size
                                       # (sizes are multiples of 8 so the floor layouts use whole characters)


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


def charset(charset_path=CHARSET):
    return open(charset_path, "rb").read()


def brick_rows(width, height, cs=None, phase=0):
    """The small running-bond bricks, tiled: `width` x `height` px."""
    cs = cs or charset()
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            k = x + phase
            code = SMALL_BRICKS[(k // 8) % 3]
            row.append((cs[code * 8 + (y % 8)] >> (7 - (k % 8))) & 1)
        rows.append(row)
    return rows


def arch_rows(size, cs=None, style="stone"):
    """A wall with an arched doorway cut out, drawn in the game's own textures.

    style "stone": jambs and a ring of voussoirs in the big dotted stone of the
    level's blocks (texture sampled from the brick course), small bricks in the
    spandrels and above; "brick": the small-brick wall everywhere, the opening
    simply cut out of it. The opening is 36 px wide with a semicircular top;
    the floor is one row of small bricks along the bottom edge.
    """
    import math
    cs = cs or charset()
    course = floor_rows(48, CHARSET)                       # speckled stone interior as a texture source
    def tex(x, y):
        return course[1 + (y % 13)][1 + (x % 44)]
    bricks = brick_rows(size, size, cs)
    cx, spring, r_in, r_out, floor_y, n = size // 2, 32, 18, 28, size - 8, 7
    jamb = cx - r_in
    joints = [k * math.pi / n for k in range(1, n)]
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            dx, dy = x + 0.5 - cx, y + 0.5 - spring
            r = math.hypot(dx, dy)
            if y >= floor_y:
                v = bricks[y][x]
            elif y < spring:
                if r < r_in:
                    v = 0
                elif style == "brick":
                    v = bricks[y][x]
                elif r < r_out:
                    ang = math.atan2(-dy, dx)
                    on_joint = any(abs(ang - j) * r < 0.7 for j in joints)
                    v = 0 if (on_joint or r >= r_out - 1) else tex(x, y)
                else:
                    v = bricks[y][x]
            else:
                if jamb <= x < size - jamb:
                    v = 0
                elif style == "brick":
                    v = bricks[y][x]
                else:
                    v = 0 if ((y - spring) % 8 == 0) else tex(x, y)
            row.append(v)
        rows.append(row)
    return rows


LAYOUTS = ("floor", "plain", "bricks", "arch", "arch-brick")


def compose(frames, layout, size):
    """The scene: {"size", "layers": [(colour, rows, ox, oy)], "buddy": (bx, by)}."""
    top, feet = ink_box(frames)
    layers = []
    bx = (size - SPRITE_W) // 2
    if layout == "floor":
        floor = floor_rows(size)
        floor_y = size - len(floor)
        layers.append((FLOOR_COLOUR, floor, 0, floor_y))
        by = floor_y - 1 - feet                  # feet on the row above the bricks' top line
    elif layout == "plain":
        by = (size - (feet - top + 1)) // 2 - top
    elif layout == "bricks":
        floor = brick_rows(size, 16)
        floor_y = size - len(floor)
        layers.append((FLOOR_COLOUR, floor, 0, floor_y))
        by = floor_y - 1 - feet
    elif layout in ("arch", "arch-brick"):
        size = 64
        bx = (size - SPRITE_W) // 2
        wall = arch_rows(size, style="brick" if layout == "arch-brick" else "stone")
        layers.append((FLOOR_COLOUR, wall, 0, 0))
        by = (size - 8) - 1 - feet
    else:
        raise ValueError(layout)
    return {"size": size, "layers": layers, "buddy": (bx, by)}


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


GLITCH_CYCLE = ["#2e2c9b", "#75cec8", "#edf171", "#706deb", "#56ac4d", "#c46c71", "#8e3c97"]   # the seven token colours
TOKENS = [("the-shadow", "blue"), ("the-dancer", "cyan"), ("the-echo", "yellow"), ("the-mirror", "light-blue"),
          ("the-wanderer", "green"), ("the-shy", "light-red"), ("the-sleeper", "purple"), ("the-glitch", None)]
GLITCH_STEP = 0.4                          # seconds per colour: 2.8 s round the seven, against the 1.8 s idle loop
BLINK_PERIOD = 2.6                         # seconds between blinks (drifts against both the 1.8 s loop and the 2.8 s colours)
BLINK = [(2.39, 0), (2.47, 1), (2.51, 0), (2.59, 1)]   # (time, opacity) within a period: out, a flicker back, out, back


def blink_at(t):
    """Opacity of the figure at time t (seconds) when the blink is on: 1 except two short drops near the period's end."""
    t %= BLINK_PERIOD
    v = 1
    for at, val in BLINK:
        if t >= at:
            v = val
    return v


def svg(frames, colour_hex, layout="floor", size=DEFAULT_SIZE, glitch=False, blink=False):
    """One SVG. With glitch=True the fill cycles through the seven token colours (the Glitch's thumbnail);
    with blink=True the figure drops out twice, briefly, every BLINK_PERIOD seconds (his bursts)."""
    sc = compose(frames, layout, size)
    size, (bx, by) = sc["size"], sc["buddy"]
    n = len(PHASES)
    keytimes = ";".join(f"{i / n:.4f}" for i in range(n)) + ";1"
    dur = f"{PHASE_SECONDS * n:g}s"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" shape-rendering="crispEdges">',
             f'<rect width="{size}" height="{size}" fill="#000"/>']
    for hexcol, rows, ox, oy in sc["layers"]:
        parts.append(f'<path fill="{hexcol}" d="{runs_path(rows, ox, oy)}"/>')
    order = []                                   # frames in order of first appearance: A first
    for f in PHASES:
        if f not in order:
            order.append(f)
    if blink:
        times = [0.0] + [at / BLINK_PERIOD for at, _ in BLINK] + [1.0]
        vals = [1] + [val for _, val in BLINK] + [1]
        parts.append('<g>')
        parts.append(f'<animate attributeName="opacity" values="{";".join(str(v) for v in vals)}" '
                     f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" calcMode="discrete" '
                     f'dur="{BLINK_PERIOD:g}s" repeatCount="indefinite"/>')
    for f in order:
        values = ";".join("1" if p == f else "0" for p in PHASES) + ";" + ("1" if PHASES[0] == f else "0")
        fill = GLITCH_CYCLE[0] if glitch else colour_hex
        parts.append(f'<path fill="{fill}" d="{runs_path(frames[f], bx, by)}">')
        parts.append(f'<animate attributeName="opacity" values="{values}" keyTimes="{keytimes}" '
                     f'calcMode="discrete" dur="{dur}" repeatCount="indefinite"/>')
        if glitch:
            parts.append(f'<animate attributeName="fill" values="{";".join(GLITCH_CYCLE)}" '
                         f'calcMode="discrete" dur="{GLITCH_STEP * len(GLITCH_CYCLE):g}s" repeatCount="indefinite"/>')
        parts.append('</path>')
    if blink:
        parts.append('</g>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def gif(frames, colour_hex, layout, size, path, glitch=False, blink=False, seconds=7.8, fps=25, scale=4):
    """A GIF preview of the animated SVG's timeline (phases, the Glitch's colours, the blink), rendered from the same data."""
    from PIL import Image
    ims = []
    n = int(seconds * fps)
    for i in range(n):
        t = i / fps
        frame = PHASES[int(t / PHASE_SECONDS) % len(PHASES)]
        col = GLITCH_CYCLE[int(t / GLITCH_STEP) % len(GLITCH_CYCLE)] if glitch else colour_hex
        if blink and blink_at(t) == 0:
            im = raster(frames, "#000000", layout, size, frame, scale)      # the figure gone: ink in the ground's colour
        else:
            im = raster(frames, col, layout, size, frame, scale)
        ims.append(im.convert("P", palette=Image.ADAPTIVE, colors=32))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=int(1000 / fps), loop=0, optimize=False)


def raster(frames, colour_hex, layout, size, frame, scale):
    """One still of the composition (a given sprite frame) as a PIL image."""
    from PIL import Image
    rgb = tuple(int(colour_hex[i:i + 2], 16) for i in (1, 3, 5))
    sc = compose(frames, layout, size)
    size, (bx, by) = sc["size"], sc["buddy"]
    im = Image.new("RGB", (size, size), "black")
    px = im.load()
    for hexcol, rows, ox, oy in sc["layers"]:
        col = tuple(int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
        for y, row in enumerate(rows):
            for x, v in enumerate(row):
                if v:
                    px[ox + x, oy + y] = col
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
    cell = 64 * scale                            # every thumbnail shown at the same tile size, as a marketplace would
    pad, text_h = 10, 14
    rows = (len(specs) + columns - 1) // columns
    im = Image.new("RGB", (columns * (cell + pad) + pad, rows * (cell + pad + text_h) + pad), "#202020")
    d = ImageDraw.Draw(im)
    for i, (label, colour_hex, layout, sz) in enumerate(specs):
        x = pad + (i % columns) * (cell + pad)
        y = pad + (i // columns) * (cell + pad + text_h)
        tile = raster(frames, colour_hex, layout, sz, PHASES[0], 1).resize((cell, cell), Image.NEAREST)
        im.paste(tile, (x, y))
        d.text((x, y + cell + 1), label, fill="white")
    im.save(path)


def colour(c):
    return PALETTE[int(c)] if c.isdigit() else (c, NAMES[c])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("colours", nargs="*", default=["cyan"])
    ap.add_argument("--layout", default=DEFAULT_LAYOUT, choices=LAYOUTS)
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE)
    ap.add_argument("--out", default="deliverables/assets")
    ap.add_argument("--strip", help="write a PNG strip of the six phases (first colour) instead of SVGs")
    ap.add_argument("--sheet", help="write a comparison PNG of the given colour[:layout] specs instead of SVGs")
    ap.add_argument("--glitch", action="store_true", help="the Glitch's thumbnail: the fill cycles through the seven token colours")
    ap.add_argument("--no-blink", dest="blink", action="store_false", help="with --glitch: leave out the blink (the Glitch's thumbnail blinks by default)")
    ap.add_argument("--gif", help="with --glitch: also write a GIF preview of the timeline to this path")
    ap.add_argument("--tokens", action="store_true", help="write the eight token thumbnails by name into OUT/tokens/")
    ap.add_argument("--sprites", default=SPRITE_DIR)
    a = ap.parse_args()
    frames = load_frames(a.sprites)
    if a.sheet:
        specs = []
        for spec in a.colours:
            c, lay, sz = (spec.split(":") + ["", ""])[:3]
            name, hexval = colour(c)
            lay, sz = lay or a.layout, int(sz or a.size)
            specs.append((f"{name} {lay} {sz}px", hexval, lay, sz))
        sheet(frames, specs, a.size, a.sheet)
        print(f"{a.sheet}: {os.path.getsize(a.sheet)} bytes")
        return
    if a.strip:
        name, hexval = colour(a.colours[0])
        phase_strip(frames, hexval, a.layout, a.size, a.strip)
        print(f"{a.strip}: {os.path.getsize(a.strip)} bytes")
        return
    if a.tokens:
        d = os.path.join(a.out, "tokens")
        os.makedirs(d, exist_ok=True)
        for name, col in TOKENS:
            path = os.path.join(d, f"{name}.svg")
            open(path, "w").write(svg(frames, GLITCH_CYCLE[0], a.layout, a.size, glitch=True, blink=True) if col is None
                                  else svg(frames, NAMES[col], a.layout, a.size))
            print(f"{path}: {os.path.getsize(path)} bytes")
        return
    if a.glitch:
        path = os.path.join(a.out, "buddy-idle-glitch.svg" if a.blink else "buddy-idle-glitch-no-blink.svg")
        open(path, "w").write(svg(frames, GLITCH_CYCLE[0], a.layout, a.size, glitch=True, blink=a.blink))
        if a.gif:
            gif(frames, GLITCH_CYCLE[0], a.layout, a.size, a.gif, glitch=True, blink=a.blink)
            print(f"{a.gif}: GIF preview")
        print(f"{path}: {os.path.getsize(path)} bytes")
        return
    for c in a.colours:
        name, hexval = colour(c)
        sz = 64 if a.layout in ("arch", "arch-brick") else a.size
        suffix = "" if (a.layout, sz) == (DEFAULT_LAYOUT, DEFAULT_SIZE) else f"-{a.layout}-{sz}"
        path = os.path.join(a.out, f"buddy-idle-{name}{suffix}.svg")
        open(path, "w").write(svg(frames, hexval, a.layout, a.size))
        print(f"{path}: {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    main()
