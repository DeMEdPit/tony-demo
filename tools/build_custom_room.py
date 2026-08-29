#!/usr/bin/env python3
"""Generate the custom single-screen room "The Idol Vault".

Emits src/level-custom/custom-room.bin — a raw 40x20 char-code matrix in the
same format the charpad preprocessor writes (1 byte per cell, row-major), so
the level macro `_level_pack` can LoadBinary() it like any sliced room.
Also renders a preview PNG using the castle charset.

Layout (char codes from castle_map.ctm, materials verified:
1=wall/standable, 2=ladder, 0=decor):

  - sealed chamber: solid ceiling, 3-thick brick walls, full-width floor
  - central dais (row 13) on a 5-wide pillar, with the solid stone idol
    (rows 6-12) standing on it — the pillar splits the floor in two zones
  - side platforms (row 9) reached by 4-wide ladders (rows 9-17)
  - route: floor -> ladder -> side platform -> drop-jump onto the dais
    between the two flames; walk off the dais to fall back to the floor
  - decor: hanging chains above the idol, vines, candelabra high on walls

Run from repo root: python3 tools/build_custom_room.py
"""

import os
import sys

sys.path.insert(0, "tools")

W, H = 40, 20
g = [[0x00] * W for _ in range(H)]


def put(row, col, *codes):
    for i, c in enumerate(codes):
        g[row][col + i] = c


def vfill(col, row0, row1, code):
    for r in range(row0, row1 + 1):
        g[r][col] = code


# --- shell ------------------------------------------------------------
put(0, 0, *([0xF1] * W))                          # solid ceiling
put(1, 0, *([0xF5, 0xF4] * (W // 2)))             # mossy underside
for r in range(2, 18):                            # side walls, 3 thick
    pat = (0xA7, 0xA8, 0xA9) if r % 2 else (0xAA, 0xAB, 0xA7)
    put(r, 0, *pat)
    put(r, 37, *pat)
FLOOR_A = ([0x31, 0x32, 0x33, 0x34, 0x35, 0x36], [0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C])
FLOOR_B = ([0x25, 0x26, 0x27, 0x28, 0x29, 0x2A], [0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30])
for c in range(W):                                # two-row stone floor
    top, bot = (FLOOR_A if (c // 6) % 2 == 0 else FLOOR_B)
    g[18][c] = top[c % 6]
    g[19][c] = bot[c % 6]

# --- centre: pillar, dais, idol --------------------------------------
put(13, 14, 0x60, *([0x61] * 11), 0x62)           # dais platform, cols 14-26
put(14, 18, 0x94, 0x95, 0x96, 0x97, 0x98)         # pillar body
put(15, 18, 0x94, 0x9E, 0x9F, 0xA0, 0xA1)         # pillar niche
put(16, 18, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6)
put(17, 18, 0x99, 0x9A, 0x9B, 0x9C, 0x9D)         # pillar base
g[14][15] = 0xFA                                  # tiny deco under dais lip
g[14][25] = 0xFA

IDOL = [                                          # the solid stone idol
    (0x01, 0x02, 0x03, 0x04, 0x05),
    (0x00, 0x07, 0x08, 0x00, 0x09),
    (0x00, 0x0A, 0x0B, 0x0C, 0x0D),
    (0x00, 0x0E, 0x0F, 0x10, 0x11),
    (0x00, 0x15, 0x16, 0x17, 0x18),
    (0x1C, 0x1D, 0x1E, 0x1E, 0x1F),
    (0x20, 0x21, 0x22, 0x23, 0x24),
]
for i, row in enumerate(IDOL):
    put(6 + i, 18, *row)

# --- side routes ------------------------------------------------------
put(9, 3, 0x60, 0x61, 0x61, 0x61, 0x62)           # left platform, cols 3-7
put(9, 32, 0x60, 0x61, 0x61, 0x61, 0x62)          # right platform, cols 32-36
for r in range(9, 18):                            # ladders (4 wide, rungs mat 2)
    rung = (0x7B, 0x7C, 0x7D, 0x7E) if r % 2 else (0x7B, 0x7F, 0x80, 0x7E)
    put(r, 8, *rung)                              # left ladder, cols 8-11
    put(r, 28, *rung)                             # right ladder, cols 28-31

# --- decor ------------------------------------------------------------
put(3, 3, 0x82, 0x83, 0x84, 0x85)                 # candelabra high on walls
put(4, 3, 0x86, 0x87, 0x88, 0x89)
put(3, 33, 0x82, 0x83, 0x84, 0x85)
put(4, 33, 0x86, 0x87, 0x88, 0x89)
for col in (13, 27):                              # vines
    vfill(col, 2, 2, 0xB4)
    vfill(col, 3, 3, 0xB7)
    vfill(col, 4, 4, 0xBA)
for c0 in (15, 24):                               # chains above the idol
    put(2, c0, 0xB2, 0xB3)
    put(3, c0, 0xB0, 0xB1)
    put(4, c0, 0xB0, 0xB1)
    put(5, c0, 0xB0, 0xB1)

# --- emit -------------------------------------------------------------
os.makedirs("src/level-custom", exist_ok=True)
out = "src/level-custom/custom-room.bin"
with open(out, "wb") as f:
    for row in g:
        f.write(bytes(row))
print(f"wrote {out} ({W}x{H})")

distinct = len({c for row in g for c in row if c})
print(f"distinct non-zero chars: {distinct} (MAX_BG_CHARS is 170)")

# preview using the castle charset
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
im.save("deliverables/assets/custom-room-preview.png")
print("wrote deliverables/assets/custom-room-preview.png")
