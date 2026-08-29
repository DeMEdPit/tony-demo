#!/usr/bin/env python3
"""Restyle the Tony player sheets into "Golem Tony".

Transformation, applied per 32x32 frame of every player sheet:
  1. flood-fill enclosed hollows of the line art => solid golem body;
  2. locate the beret head stamp (template-matched against walk frame 0)
     and reshape the skull: battlement crown instead of the round beret;
  3. carve a 2x2 eye hole at a fixed offset from the head anchor (the dark
     backdrop sprite then shows through => dark eye on light body).
The ladder sheet (rear view, no beret) gets fill + crown at the head top.
Overlay ".bg" sheets are regenerated as r=2 dilations of the new art
(sprite_tool.genbg).

Run from the repo root:  python3 tools/restyle_tony.py [--preview]
"""

import sys

sys.path.insert(0, "tools")
from sprite_tool import load_mask, save_mask, frames_of, txt_of_frame, genbg

SHEETS = {  # name -> (frames, style)
    "tony chodzenie 4 klatki": (4, "front"),
    "tony kucanie 4 klatki": (4, "front"),
    "tony spoczynek 4klatki": (4, "front"),
    "tony skok 2 klatki": (2, "front"),
    "tony smierc lewo 5klatek": (5, "front-left"),
    "tony smierc prawo 5klatek": (5, "front"),
    "tony_drabina": (2, "rear"),
}

CW = CH = 32


def flood_fill_solid(fr):
    """Fill hollows: everything not reachable from outside becomes solid."""
    h, w = len(fr), len(fr[0])
    outside = [[False] * w for _ in range(h)]
    stack = [(x, y) for x in range(w) for y in (0, h - 1) if not fr[y][x]]
    stack += [(x, y) for y in range(h) for x in (0, w - 1) if not fr[y][x]]
    while stack:
        x, y = stack.pop()
        if 0 <= x < w and 0 <= y < h and not outside[y][x] and not fr[y][x]:
            outside[y][x] = True
            stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return [[1 if (fr[y][x] or not outside[y][x]) else 0 for x in range(w)]
            for y in range(h)]


# Beret templates as stamped by the artist onto the frames: the walking pose
# head and the tilted-down head used by the duck/idle sheets.
BERET = [
    ".....##......",
    "....####.....",
    "..###...##...",
    ".##...##..#..",
    "##..###....#.",
]
BERET_TILT = [
    ".....##......",
    "....####.....",
    "..##...###...",
    ".#..##...##..",
    "#....###..##.",
]
BERET_M = [[1 if c == "#" else 0 for c in row] for row in BERET]
BT_H, BT_W = len(BERET_M), len(BERET_M[0])


def find_head(fr, template=BERET_M):
    """Return (dx, dy) of the beret template in the frame, or None."""
    h, w = len(fr), len(fr[0])
    for dy in range(0, h - BT_H + 1):
        for dx in range(-4, w - BT_W + 1):
            ok = True
            for y in range(BT_H):
                for x in range(BT_W):
                    if template[y][x]:
                        xx = dx + x
                        if xx < 0 or xx >= w or not fr[dy + y][xx]:
                            ok = False
                            break
                if not ok:
                    break
            if ok:
                return dx, dy
    return None


# The new skull, stamped over the beret anchor box: a solid golem head with
# a battlement crown and a carved 2x2 eye (faces right; mirrored for the
# left-facing death sheet).  '#' = set, '.' = clear.
HEAD = [
    ".#..#..#..#..",
    ".###########.",
    "#############",
    "#############",
    "#############",
    "########..###",
    "########..###",
    "#############",
    ".###########.",
]
HEAD_L = ["".join(reversed(row)) for row in HEAD]
BERET_L = ["".join(reversed(row)) for row in BERET]


def stamp(canvas, art, dx, dy):
    h, w = len(canvas), len(canvas[0])
    for y, row in enumerate(art):
        for x, c in enumerate(row):
            xx, yy = dx + x, dy + y
            if 0 <= xx < w and 0 <= yy < h and c != " ":
                canvas[yy][xx] = 1 if c == "#" else 0


def apply_front(fr, mirrored=False):
    sources = [BERET_L, ["".join(reversed(r)) for r in BERET_TILT]] if mirrored \
        else [BERET, BERET_TILT]
    head = None
    for src in sources:
        template = [[1 if c == "#" else 0 for c in row] for row in src]
        head = find_head(fr, template)
        if head:
            break
    solid = flood_fill_solid(fr)
    if head is None:
        return solid, False
    dx, dy = head
    stamp(solid, HEAD_L if mirrored else HEAD, dx, dy)
    return solid, True


HEAD_REAR = [HEAD[i] if i not in (5, 6) else "#############" for i in range(len(HEAD))]


def apply_rear(fr):
    """Ladder frames: fill + solid rear head (no eye) on the topmost blob."""
    solid = flood_fill_solid(fr)
    h, w = len(solid), len(solid[0])
    top = next((y for y in range(h) if any(fr[y])), None)
    if top is None:
        return solid, False
    xs = [x for x in range(w) if fr[top][x]]
    cx = (min(xs) + max(xs)) // 2
    dx = cx - len(HEAD_REAR[0]) // 2
    stamp(solid, HEAD_REAR, dx, top)
    return solid, True


def restyle_sheet(name, nframes, style, preview):
    path = f"src/spritepad/{name}.png"
    mask, w, h = load_mask(path)
    frames = frames_of(mask, w, h, CW, CH)
    assert len(frames) == nframes, (name, len(frames))
    # idempotency guard: refuse to restyle art that already carries the crown
    merlons = [1, 0, 0, 1, 0, 0, 1, 0, 0, 1]
    for fr in frames:
        for row in fr:
            for x in range(len(row) - len(merlons)):
                if row[x:x + len(merlons)] == merlons and sum(row) == 4:
                    sys.exit(f"{name}: already restyled (crown found) - "
                             "restore originals with git checkout first")
    out = [[0] * w for _ in range(h)]
    report = []
    for i, fr in enumerate(frames):
        if style == "rear":
            new, found = apply_rear(fr)
        else:
            new, found = apply_front(fr, mirrored=(style == "front-left"))
        report.append("head" if found else "NO-HEAD")
        for y in range(CH):
            for x in range(CW):
                out[y][i * CW + x] = new[y][x]
    print(f"{name}: frames={nframes} [{', '.join(report)}]")
    if preview:
        for y in range(CH):
            print("  ".join("".join("#" if out[y][i * CW + x] else "."
                                     for x in range(26)) for i in range(min(nframes, 5))))
    else:
        save_mask(out, path)
        genbg(path, f"src/spritepad/{name}.bg.png", 2)


def main():
    preview = "--preview" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    for name, (nframes, style) in SHEETS.items():
        if only and name not in only:
            continue
        restyle_sheet(name, nframes, style, preview)


if __name__ == "__main__":
    main()
