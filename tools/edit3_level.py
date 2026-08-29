#!/usr/bin/env python3
"""Edit 3: background/level alterations, patched directly into the CTM files.

A) Title screen (room 29, demo-level.ctm map region x160-199/y0-19):
   writes "CLAUDE" into the empty sky with solid block chars ($F1),
   3x4 cells per letter, top-left at map cell (161, 2).

B) Start room (room 18, castle_map.ctm region x160-199/y60-79):
   adds a new standable floating platform (chars $60 $61.. $62,
   material 1 = wall) with two decorative chain links hanging below,
   in the previously empty middle of the room.

Run from the repo root: python3 tools/edit3_level.py
Idempotent: re-running produces the same cell values.
"""

import sys

sys.path.insert(0, "tools")
from ctm_tool import CTM

FONT = {
    "C": ["###", "#..", "#..", "###"],
    "L": ["#..", "#..", "#..", "###"],
    "A": ["###", "#.#", "###", "#.#"],
    "U": ["#.#", "#.#", "#.#", "###"],
    "D": ["##.", "#.#", "#.#", "##."],
    "E": ["###", "##.", "#..", "###"],
}

SOLID = 0xF1  # fully solid 8x8 block, material 0 (decorative)


def patch_title():
    ctm = CTM("src/charpad/demo-level.ctm")
    x0, y0 = 161, 2
    for li, letter in enumerate("CLAUDE"):
        for ry, row in enumerate(FONT[letter]):
            for rx, cell in enumerate(row):
                if cell == "#":
                    ctm.set_cell(x0 + li * 4 + rx, y0 + ry, SOLID)
    ctm.save()
    print("title screen: 'CLAUDE' written at (161,2)-(184,5) with char $F1")


def patch_room18():
    ctm = CTM("src/charpad/castle_map.ctm")
    bx, by = 160, 60  # room 18 = grid (4,3)
    # floating platform: left cap, 4 mid sections, right cap
    for i, code in enumerate((0x60, 0x61, 0x61, 0x61, 0x61, 0x62)):
        ctm.set_cell(bx + 16 + i, by + 13, code)
    # chain links hanging under the platform (decorative, material 0)
    ctm.set_cell(bx + 17, by + 14, 0xB2)
    ctm.set_cell(bx + 18, by + 14, 0xB3)
    ctm.set_cell(bx + 17, by + 15, 0xB0)
    ctm.set_cell(bx + 18, by + 15, 0xB1)
    ctm.save()
    print("room 18: new platform at cells (176-181,73) + chains below")


if __name__ == "__main__":
    patch_title()
    patch_room18()
