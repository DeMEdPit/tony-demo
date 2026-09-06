#!/usr/bin/env python3
"""The Chamber: the tall Colonnade (40x25, no dashboard) with a BRICK ceiling,
its own character set and material table.

Ceiling and floor use the same two-row brick courses; two pillars run from
ceiling to floor. The back wall between the pillars is left empty on purpose:
at run time the game stamps a mural of dotted bricks there from a 32-byte
seed, up to three wall candles, and carves the block number into the floor
(tools/make_chamber.py, tools/stamp_mural.py).

Characters the run-time routine needs must be part of the room's used set
(the engine only carries the characters a room uses), so they are placed in
the static map INSIDE the mural area, which the routine overwrites entirely:
the four dotted-brick chars, the four candle chars, and the ten carved digits.

The ten carved digits are new glyphs: a smooth stone cell with a small 4x6
digit cut into it (dark on light). They replace characters $01-$0A
(unused by this room) in a copy of the level charset, `chamber-charset.bin`,
and get wall material in `chamber-materials.bin` so Tony can stand on them.

Emits src/level-custom/chamber-room.bin, chamber-charset.bin,
chamber-materials.bin and preview PNGs. Run from repo root.
"""
import os
import sys

sys.path.insert(0, "tools")

W, H = 40, 25
DIGIT_BASE = 0x01                 # carved digits live at $01..$0A
DIGIT_TEXTURE = 0x32              # the floor brick face the digits are cut into
CANDLE = (0x70, 0x72, 0x5B, 0xFA)   # flame-topped candle, its body, a stone ledge, a drip
MURAL = (0xB0, 0xB1, 0xB2, 0xB3)
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

# run-time characters, parked inside the mural area (rows 2-21, cols 5-34)
put(2, 5, MURAL[0], MURAL[1]); put(3, 5, MURAL[2], MURAL[3])
put(4, 5, *CANDLE)
put(6, 5, *[DIGIT_BASE + d for d in range(10)])

os.makedirs("src/level-custom", exist_ok=True)
with open("src/level-custom/chamber-room.bin", "wb") as f:
    for row in g:
        f.write(bytes(row))
print("wrote src/level-custom/chamber-room.bin (40x25)")

# --- the chamber's own charset and materials -------------------------------
cs = bytearray(open("build/charpad/demo-level-charset.bin", "rb").read())   # ink = 1 bits (negated at load)
mt = bytearray(open("build/charpad/demo-level-materials.bin", "rb").read())
prg = open("deliverables/onchain/tony-token-edition.prg", "rb").read()
font = prg[0xBC20 - 0x0801 + 2:][:296]                                       # title font: @ A-Z 0-9
# a smooth stone cell with a small 4x6 digit carved into it (dark on light),
# 2 px in from the left, 1 px down: small and legible at C64 resolution
F46 = {"0": [".##.", "#..#", "#..#", "#..#", "#..#", ".##."], "1": ["..#.", ".##.", "..#.", "..#.", "..#.", ".###"],
       "2": [".##.", "#..#", "...#", "..#.", ".#..", "####"], "3": ["###.", "...#", ".##.", "...#", "...#", "###."],
       "4": ["#..#", "#..#", "####", "...#", "...#", "...#"], "5": ["####", "#...", "###.", "...#", "...#", "###."],
       "6": [".##.", "#...", "###.", "#..#", "#..#", ".##."], "7": ["####", "...#", "..#.", "..#.", ".#..", ".#.."],
       "8": [".##.", "#..#", ".##.", "#..#", "#..#", ".##."], "9": [".##.", "#..#", ".###", "...#", "...#", ".##."]}
for d in range(10):
    rows = [0xFF] * 8                                                        # smooth light stone
    for y, line in enumerate(F46[str(d)]):
        for x, ch in enumerate(line):
            if ch == "#":
                rows[1 + y] &= ~(0x80 >> (2 + x)) & 0xFF                     # carve the digit
    cs[(DIGIT_BASE + d) * 8:(DIGIT_BASE + d) * 8 + 8] = bytes(rows)
    mt[DIGIT_BASE + d] = 1                                                   # wall: Tony stands on them
for c in CANDLE:
    mt[c] = 0                                                                # decoration only (the game marks candle flames deadly)
open("src/level-custom/chamber-charset.bin", "wb").write(bytes(cs))
open("src/level-custom/chamber-materials.bin", "wb").write(bytes(mt))
print("wrote src/level-custom/chamber-charset.bin and chamber-materials.bin")

# --- previews ----------------------------------------------------------------
from PIL import Image
def rows_of(code):
    return [[(cs[code * 8 + r] >> (7 - x)) & 1 for x in range(8)] for r in range(8)]
im = Image.new("L", (W * 8, H * 8), 0)
px = im.load()
for cy in range(H):
    for cx in range(W):
        rows = rows_of(g[cy][cx])
        for ry in range(8):
            for rx in range(8):
                if rows[ry][rx]:
                    px[cx * 8 + rx, cy * 8 + ry] = 255
im.save("deliverables/assets/chamber-room-preview.png")
S = 6
strip = Image.new("L", ((10 + 4) * 8 * S, 8 * S), 0); sp = strip.load()
for i, code in enumerate([DIGIT_TEXTURE, DIGIT_TEXTURE] + [DIGIT_BASE + d for d in range(10)] + [DIGIT_TEXTURE, DIGIT_TEXTURE]):
    rows = rows_of(code)
    for ry in range(8):
        for rx in range(8):
            if rows[ry][rx]:
                for yy in range(S):
                    for xx in range(S):
                        sp[(i * 8 + rx) * S + xx, ry * S + yy] = 255
strip.save("deliverables/assets/chamber-digits-preview.png")
print("wrote previews")
