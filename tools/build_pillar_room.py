#!/usr/bin/env python3
"""Generate the minimal "Colonnade" room: an empty chamber.

Floor, ceiling, and two big pillars (floor to ceiling) standing in for the
side walls.  Nothing else on the map - the bats live in the object list of
the level, not in the tiles.

Emits src/level-custom/pillar-room.bin (40x20, 1 byte/cell) and a preview.
Run from repo root: python3 tools/build_pillar_room.py
"""

import os
import sys

sys.path.insert(0, "tools")

W, H = 40, 20
g = [[0x00] * W for _ in range(H)]


def put(row, col, *codes):
    for i, c in enumerate(codes):
        g[row][col + i] = c


# ceiling
put(0, 0, *([0xF1] * W))
put(1, 0, *([0xF5, 0xF4] * (W // 2)))

# floor (two-row stone floor, alternating 6-column motifs)
FLOOR_A = ([0x31, 0x32, 0x33, 0x34, 0x35, 0x36], [0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C])
FLOOR_B = ([0x25, 0x26, 0x27, 0x28, 0x29, 0x2A], [0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30])
for c in range(W):
    top, bot = (FLOOR_A if (c // 6) % 2 == 0 else FLOOR_B)
    g[18][c] = top[c % 6]
    g[19][c] = bot[c % 6]

# two big pillars, floor to ceiling, standing in for the walls
PILLAR = (
    [(0x8A, 0x8B, 0x8C, 0x8D, 0x8E)] +          # capital
    [(0x94, 0x95, 0x96, 0x97, 0x98)] * 11 +     # shaft
    [(0x94, 0x9E, 0x9F, 0xA0, 0xA1),            # niche detail near the base
     (0xA2, 0xA3, 0xA4, 0xA5, 0xA6)] +
    [(0x94, 0x95, 0x96, 0x97, 0x98),            # shaft
     (0x99, 0x9A, 0x9B, 0x9C, 0x9D)]            # base
)
for i, row in enumerate(PILLAR):                # rows 2..17
    put(2 + i, 0, *row)
    put(2 + i, 35, *row)

# emit
os.makedirs("src/level-custom", exist_ok=True)
out = "src/level-custom/pillar-room.bin"
with open(out, "wb") as f:
    for row in g:
        f.write(bytes(row))
print(f"wrote {out}")

from ctm_tool import CTM, char_rows
from PIL import Image
ctm = CTM("src/charpad/castle_map.ctm")
im = Image.new("L", (W * 8, H * 8), 0)
px = im.load()
for cy in range(H):
    for cx in range(W):
        rows = char_rows(ctm.char_bitmap(g[cy][cx]))
        for ry in range(8):
            for rx in range(8):
                if rows[ry][rx]:
                    px[cx * 8 + rx, cy * 8 + ry] = 255
im.save("deliverables/assets/pillar-room-preview.png")
print("wrote deliverables/assets/pillar-room-preview.png")
