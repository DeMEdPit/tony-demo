#!/usr/bin/env python3
"""The Chamber: the tall Colonnade (40x25, no dashboard) with a BRICK ceiling.

Ceiling and floor use the same two-row brick courses; two pillars run from
ceiling to floor. The back wall between the pillars is left empty on purpose:
at run time the game stamps a mural of dotted bricks there from a 32-byte
seed (tools/make_chamber.py, tools/stamp_mural.py). One static dotted brick
is placed in the mural area so its four characters are part of the room's
used-character set (the engine only carries the characters a room uses);
the mural routine overwrites every slot, so it never shows as such.

Emits src/level-custom/chamber-room.bin and a preview PNG.
Run from repo root: python3 tools/build_chamber_room.py
"""
import os
import sys

sys.path.insert(0, "tools")

W, H = 40, 25
g = [[0x00] * W for _ in range(H)]


def put(row, col, *codes):
    for i, c in enumerate(codes):
        g[row][col + i] = c


COURSE_A = ([0x31, 0x32, 0x33, 0x34, 0x35, 0x36], [0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C])
COURSE_B = ([0x25, 0x26, 0x27, 0x28, 0x29, 0x2A], [0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30])
for c in range(W):
    top, bot = (COURSE_A if (c // 6) % 2 == 0 else COURSE_B)
    g[0][c], g[1][c] = top[c % 6], bot[c % 6]        # brick ceiling
    g[23][c], g[24][c] = top[c % 6], bot[c % 6]      # brick floor (unchanged)

PILLAR = (
    [(0x8A, 0x8B, 0x8C, 0x8D, 0x8E)] +               # capital
    [(0x94, 0x95, 0x96, 0x97, 0x98)] * 16 +          # shaft
    [(0x94, 0x9E, 0x9F, 0xA0, 0xA1),                 # niche detail near the base
     (0xA2, 0xA3, 0xA4, 0xA5, 0xA6)] +
    [(0x94, 0x95, 0x96, 0x97, 0x98),
     (0x99, 0x9A, 0x9B, 0x9C, 0x9D)]                 # base
)
assert len(PILLAR) == 21
for i, row in enumerate(PILLAR):                     # rows 2..22
    put(2 + i, 0, *row)
    put(2 + i, 35, *row)

# the mural's four characters, so the room "uses" them (overwritten at run time)
put(2, 5, 0xB0, 0xB1)
put(3, 5, 0xB2, 0xB3)

os.makedirs("src/level-custom", exist_ok=True)
out = "src/level-custom/chamber-room.bin"
with open(out, "wb") as f:
    for row in g:
        f.write(bytes(row))
print(f"wrote {out} ({W}x{H})")

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
im.save("deliverables/assets/chamber-room-preview.png")
print("wrote deliverables/assets/chamber-room-preview.png")
