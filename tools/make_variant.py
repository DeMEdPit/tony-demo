#!/usr/bin/env python3
"""Generate a standalone one-room game variant from tony.asm.

Usage: make_variant.py <name> <level-dir>
  e.g.  make_variant.py tony-pillars level/pillars

Writes src/kickass/<name>.asm: identical to tony.asm except that it
  - assembles to ./<name>.prg,
  - imports <level-dir>/data.asm instead of level/demo/data.asm,
  - boots straight into the room (and returns there after game over) via a
    startRoomDirect subroutine instead of the title-screen flow.
"""

import sys


def main():
    name, leveldir = sys.argv[1], sys.argv[2]
    src = open("src/kickass/tony.asm").read()

    src = src.replace('.file [name="./tony.prg"', f'.file [name="./{name}.prg"', 1)
    src = src.replace('#import "level/demo/data.asm"', f'#import "{leveldir}/data.asm"', 1)

    assert src.count("jsr startTitle") == 2
    src = src.replace("jsr startTitle", "jsr startRoomDirect")

    sub = """startRoomDirect: {
    jsr blankScreen
    lda #0
    sta gameTitleScreen
    sta joyAccumulator
    sta joyDelayCounter
    sta joyPreviousValue
    jsr drawScreen
    jsr showEyes
    jsr showScreen
    rts
}

setColors: {"""
    assert src.count("setColors: {") == 1
    src = src.replace("setColors: {", sub, 1)

    out = f"src/kickass/{name}.asm"
    open(out, "w").write(src)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
