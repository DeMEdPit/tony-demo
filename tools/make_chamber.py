#!/usr/bin/env python3
"""Generate the Chamber build: the buddy game whose back wall is a MURAL drawn
from a 32-byte seed - the block hash at render time, once a contract writes it.

Produces (all generated, all committed):
  src/kickass/level/chamber/data.asm - the buddy level data pointing at
      chamber-room.bin, plus the seed block: 8-byte marker "MURAL01\\0" and
      32 seed bytes, 64-aligned so the seed never crosses a page
  src/kickass/tony-chamber.asm       - tony-buddy.asm plus the mural routine,
      hooked between the room decompression and its char translation
  build.gradle.kts                   - the new include (idempotent)

The mural: 15 x 10 slots of 2x2 dotted bricks ($B0 $B1 / $B2 $B3, the ones
behind the skull in room 11), one bit per slot, MSB first, rows 2-21, columns
5-34. 150 of the 256 seed bits are used. Change the seed with
tools/stamp_mural.py; nothing else in the PRG changes.

Run from repo root after tools/make_buddy.py and tools/build_chamber_room.py:
    python3 tools/make_chamber.py
"""
import hashlib
import os

DEFAULT_SEED = hashlib.sha256(b"block 25850250").digest()   # the sample used in the mock-ups

# ------------------------------------------------------------- level data
src = open("src/kickass/level/buddy/data.asm").read()


def sub(text, old, new, count=1):
    assert text.count(old) == count, f"anchor not found ({count}x): {old[:60]!r}"
    return text.replace(old, new)


src = sub(src, '_level_pack("pillar-room-tall.bin"', '_level_pack("chamber-room.bin"')
src = sub(src, '''// "The Colonnade + Buddy" - the TALL pillar chamber (full 25 rows, no
// dashboard) with two bats up high (sprites 3+4). Sprites 5+6 carry the
// green buddy Tony, which is engine code in tony-buddy.asm, not a level
// object. Map: tools/build_tall_room.py.''',
'''// "The Chamber" - the tall Colonnade with a brick ceiling (full 25 rows, no
// dashboard), two bats up high (sprites 3+4), the green buddy Tony (sprites
// 5+6, engine code in tony-chamber.asm) and a back wall drawn at run time
// from the seed block below. Map: tools/build_chamber_room.py; generator:
// tools/make_chamber.py; seed: tools/stamp_mural.py.''')
seed_bytes = ", ".join(f"${b:02X}" for b in DEFAULT_SEED)
src = sub(src, "materials:\n", f'''// The mural seed. A contract (or tools/stamp_mural.py) overwrites the 32
// bytes after the marker; the marker makes the block findable in any build.
.align 64
muralMarker: .byte $4D, $55, $52, $41, $4C, $30, $31, $00   // "MURAL01\\0"
muralSeed:   .byte {seed_bytes}

materials:
''')
os.makedirs("src/kickass/level/chamber", exist_ok=True)
open("src/kickass/level/chamber/data.asm", "w").write(src)
print("wrote src/kickass/level/chamber/data.asm")

# ------------------------------------------------------------- game variant
src = open("src/kickass/tony-buddy.asm").read()
src = sub(src, '.file [name="./tony-buddy.prg"', '.file [name="./tony-chamber.prg"')
src = sub(src, '#import "level/buddy/data.asm"', '#import "level/chamber/data.asm"')
src = sub(src, "    jsr _draw_playfield\n", "    jsr _draw_playfield\n    jsr muralStamp   // the back wall, from the seed\n")

MURAL = """// ---------------------------------------------------------------------
// MURAL: the back wall is drawn from muralSeed (32 bytes; the block hash at
// render time once a contract writes it). 15 x 10 slots of 2x2 dotted
// bricks ($B0 $B1 / $B2 $B3), one bit per slot, MSB first, from row 2,
// column 5. Stamped into SCREEN_MEM_0 after the room is decompressed and
// before its characters are translated, so the bricks go through the same
// character mapping and material lookup as the rest of the map.
// ---------------------------------------------------------------------
muralStamp: {
    lda #<muralSeed
    sta seedByte
    lda #>muralSeed
    sta seedByte + 1
    lda #0
    sta bitsLeft
    ldx #0
    rowLoop:
        lda muralRowA.lo, x
        sta rowA
        lda muralRowA.hi, x
        sta rowA + 1
        lda muralRowA1.lo, x
        sta rowA1
        lda muralRowA1.hi, x
        sta rowA1 + 1
        lda muralRowB.lo, x
        sta rowB
        lda muralRowB.hi, x
        sta rowB + 1
        lda muralRowB1.lo, x
        sta rowB1
        lda muralRowB1.hi, x
        sta rowB1 + 1
        stx rowIndex
        ldy #0
        colLoop:
            lda bitsLeft
            bne !+
                lda seedByte:muralSeed
                sta cur
                inc seedByte
                lda #8
                sta bitsLeft
            !:
            dec bitsLeft
            asl cur
            bcs brick
                lda #0
                sta t0
                sta t1
                sta t2
                sta t3
                jmp write
            brick:
                lda #$B0
                sta t0
                lda #$B1
                sta t1
                lda #$B2
                sta t2
                lda #$B3
                sta t3
            write:
            lda t0
            sta rowA:SCREEN_MEM_0, y
            lda t1
            sta rowA1:SCREEN_MEM_0, y
            lda t2
            sta rowB:SCREEN_MEM_0, y
            lda t3
            sta rowB1:SCREEN_MEM_0, y
            iny
            iny
            cpy #30
            beq colDone
            jmp colLoop            // the loop body is longer than a branch reaches
        colDone:
        ldx rowIndex
        inx
        cpx #10
        beq rowDone
        jmp rowLoop
    rowDone:
    rts
    cur:      .byte 0
    bitsLeft: .byte 0
    rowIndex: .byte 0
    t0:       .byte 0
    t1:       .byte 0
    t2:       .byte 0
    t3:       .byte 0
}
muralRowA:  .lohifill 10, SCREEN_MEM_0 + (2 + 2*i)*40 + 5
muralRowA1: .lohifill 10, SCREEN_MEM_0 + (2 + 2*i)*40 + 6
muralRowB:  .lohifill 10, SCREEN_MEM_0 + (3 + 2*i)*40 + 5
muralRowB1: .lohifill 10, SCREEN_MEM_0 + (3 + 2*i)*40 + 6

nextColorScheme: {"""
src = sub(src, "nextColorScheme: {", MURAL)
open("src/kickass/tony-chamber.asm", "w").write(src)
print("wrote src/kickass/tony-chamber.asm")

# ------------------------------------------------------------- build wiring
g = open("build.gradle.kts").read()
if "tony-chamber.asm" not in g:
    g = sub(g, '        "src/kickass/tony-buddy.asm",\n', '        "src/kickass/tony-buddy.asm",\n        "src/kickass/tony-chamber.asm",\n')
    open("build.gradle.kts", "w").write(g)
    print("build.gradle.kts: include added")
else:
    print("build.gradle.kts: include already present")
