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

The seed block (48 bytes, 64-aligned): marker "MURAL01\0", 32 seed bytes
(the block hash), 8 block-number digits (0-9 each).  What the seed draws:
  - the WALL: 15 x 10 slots of 2x2 dotted bricks ($B0 $B1 / $B2 $B3), rows 2-21,
    cols 5-34.  Three bit streams run through the 32 bytes (A from byte 0, B from
    byte 19, C from byte 25, each wrapping at 32) and the DENSITY mode decides how
    they combine per slot. Three seed bits (seed[31] & 7) pick the mode through
    the table 0,0,1,1,1,3,3,2: 0 = A&B (~1/4 filled, 2 in 8), 1 = A (~1/2, 3 in 8),
    3 = A&B&C (~1/8, 2 in 8), 2 = A|B (~3/4, the rare one, 1 in 8);
  - the CANDLE: at most one. Present when seed[30] & 3 is not zero (3 times in 4).
    Its niche comes from seed[29]: the low 4 bits pick a column through a 16-entry
    table onto 14 slot columns (left column 5 + 2k, k = 0..13), the next 3 bits
    pick a row through an 8-entry table onto rows 4/6/8/10/12 (top row 2 + 2j,
    j = 1..5) - 70 positions, all on the upper and middle wall, never within
    eight rows of the floor. The niche (4x4, rows top..top+3, two wall slots by
    two) is cleared, then the glowing candle of room 10, a 3x3 block $BD-$C5, is
    drawn at rows top..top+2, columns left+1..left+3;
  - the FLOOR: the eight block digits carved into the top course, right-aligned
    against the right pillar (columns 27-34).
The buddy gets the player's own dark backdrop (sprite 7, Y-expanded, the BG
frame of whatever pose he wears) so the wall no longer shows through him.
tools/stamp_mural.py writes seed and block number and predicts the wall.

Run from repo root after tools/make_buddy.py and tools/build_chamber_room.py:
    python3 tools/make_chamber.py
"""
import hashlib
import os

DEFAULT_SEED = hashlib.sha256(b"block 25850267").digest()   # a typical roll: half-density wall, one candle high on the left

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
src = sub(src, "materials:\n", f'''// The seed block. A contract (or tools/stamp_mural.py) overwrites the 40
// bytes after the marker: 32 seed bytes (the block hash) and 8 block-number
// digits. The marker makes the block findable in any build; 64-aligned so it
// never crosses a page.
.align 64
muralMarker: .byte $4D, $55, $52, $41, $4C, $30, $31, $00   // "MURAL01\\0"
muralSeed:   .byte {seed_bytes}
muralBlock:  .byte 2, 5, 8, 5, 0, 2, 6, 7                   // block 25850267

materials:
''')
src = sub(src, '.import binary "demo-level-materials.bin"', '.import binary "chamber-materials.bin"')
src = sub(src, 'loadNegated("demo-level-charset.bin")', 'loadNegated("chamber-charset.bin")')
os.makedirs("src/kickass/level/chamber", exist_ok=True)
open("src/kickass/level/chamber/data.asm", "w").write(src)
print("wrote src/kickass/level/chamber/data.asm")

# ------------------------------------------------------------- game variant
src = open("src/kickass/tony-buddy.asm").read()
src = sub(src, '.file [name="./tony-buddy.prg"', '.file [name="./tony-chamber.prg"')
src = sub(src, '#import "level/buddy/data.asm"', '#import "level/chamber/data.asm"')
src = sub(src, "    jsr _draw_playfield\n", "    jsr _draw_playfield\n    jsr muralStamp   // the back wall, from the seed\n")

MURAL = """// ---------------------------------------------------------------------
// MURAL: the back wall, the sconces and the floor inscription are drawn from
// the seed block (muralSeed, 32 bytes = the block hash at render time once a
// contract writes it; muralBlock, 8 digits = the block number). Stamped into
// SCREEN_MEM_0 after the room is decompressed and before its characters are
// translated, so everything goes through the same char mapping and material
// lookup as the rest of the map.
//   wall: 15 x 10 slots of 2x2 dotted bricks ($B0 $B1 / $B2 $B3) from row 2,
//         column 5. Three bit streams (A from byte 0, B from 19, C from 25,
//         wrapping at 32); density mode = modeTable[seed[31] & 7]:
//         0 = A&B (2/8)  1 = A (3/8)  3 = A&B&C (2/8)  2 = A|B (1/8, rare)
//   candle: one at most, present when seed[30] & 3 != 0 (3 in 4). Column:
//         kTable[seed[29] & 15] -> left = 5 + 2k; row: jTable[seed[29] >> 4 & 7]
//         -> top = 2 + 2j (rows 4..12 only, never near the floor). The 4x4
//         niche (rows top..top+3, columns left..left+3) is cleared, then the
//         3x3 glowing candle $BD-$C5 is drawn at rows top..top+2, columns
//         left+1..left+3.
//   floor: the 8 block digits carved into row 23, columns 27-34 ($01 + digit).
// ---------------------------------------------------------------------
.label MURAL_DIGIT_BASE = $01

muralStamp: {
    // stream states
    lda #0
    sta sIdx
    sta sLeft
    sta sLeft + 1
    sta sLeft + 2
    lda #19
    sta sIdx + 1
    lda #25
    sta sIdx + 2
    lda muralSeed + 31
    and #7
    tax
    lda modeTable, x
    sta mode

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
            ldx #0
            jsr readBit
            lda #0
            rol
            sta bitA
            ldx #1
            jsr readBit
            lda #0
            rol
            sta bitB
            ldx #2
            jsr readBit
            lda #0
            rol
            sta bitC
            lda mode
            cmp #1
            beq useA
            cmp #2
            beq useOr
            cmp #3
            beq useAnd3
            lda bitA            // mode 0: A & B
            and bitB
            jmp decide
            useA:
            lda bitA
            jmp decide
            useOr:
            lda bitA
            ora bitB
            jmp decide
            useAnd3:
            lda bitA
            and bitB
            and bitC
            decide:
            bne brick
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

    // the candle: present three times in four, its niche chosen from the seed
    lda muralSeed + 30
    and #3
    beq candleDone
    lda muralSeed + 29
    and #15
    tax
    lda kTable, x                  // slot column 0..13 -> left column 5 + 2k
    asl
    clc
    adc #5
    sta candleLeft
    clc
    adc #4
    sta candleRight
    lda muralSeed + 29
    lsr
    lsr
    lsr
    lsr
    and #7
    tax
    lda jTable, x                  // slot row 1..5 -> top row 2 + 2j
    asl
    clc
    adc #2
    tax                            // X = screen row
    lda #0
    sta rowCount
    lda #$BD
    sta charBase
    nicheRow:
        lda chamberLines.lo, x
        sta clrPtr
        sta drwPtr
        lda chamberLines.hi, x
        sta clrPtr + 1
        sta drwPtr + 1
        ldy candleLeft
        lda #0
        clr:                       // clear the niche row, four columns
            sta clrPtr:$ffff, y
            iny
            cpy candleRight
        bne clr
        lda rowCount
        cmp #3
        bcs nextRow                // the fourth row is only cleared
        ldy candleLeft
        iny
        lda charBase
        drw:                       // three candle characters, one column in
            sta drwPtr:$ffff, y
            clc
            adc #1
            iny
            cpy candleRight
        bne drw
        sta charBase               // next row's characters ($BD, $C0, $C3)
        nextRow:
        inx
        inc rowCount
        lda rowCount
        cmp #4
    bne nicheRow
    candleDone:

    // the floor inscription
    ldx #0
    digitLoop:
        lda muralBlock, x
        clc
        adc #MURAL_DIGIT_BASE
        sta SCREEN_MEM_0 + 23*40 + 27, x
        inx
        cpx #8
    bne digitLoop
    rts

    // in: X = stream (0-2); out: carry = next bit (MSB first); preserves X and Y
    readBit: {
        sty saveY
        lda sLeft, x
        bne have
            ldy sIdx, x
            lda muralSeed, y
            sta sCur, x
            iny
            tya
            and #31
            sta sIdx, x
            lda #8
            sta sLeft, x
        have:
        dec sLeft, x
        lda sCur, x
        asl
        sta sCur, x
        ldy saveY
        rts
    }

    sIdx:        .byte 0, 19, 25
    sCur:        .byte 0, 0, 0
    sLeft:       .byte 0, 0, 0
    saveY:       .byte 0
    mode:        .byte 0
    bitA:        .byte 0
    bitB:        .byte 0
    bitC:        .byte 0
    rowIndex:    .byte 0
    t0:          .byte 0
    t1:          .byte 0
    t2:          .byte 0
    t3:          .byte 0
    candleLeft:  .byte 0
    candleRight: .byte 0
    rowCount:    .byte 0
    charBase:    .byte 0
    modeTable:   .byte 0, 0, 1, 1, 1, 3, 3, 2         // quarter x2, half x3, eighth x2, dense x1
    kTable:      .byte 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 4, 9
    jTable:      .byte 1, 2, 3, 4, 5, 2, 3, 4
}
muralRowA:  .lohifill 10, SCREEN_MEM_0 + (2 + 2*i)*40 + 5
muralRowA1: .lohifill 10, SCREEN_MEM_0 + (2 + 2*i)*40 + 6
muralRowB:  .lohifill 10, SCREEN_MEM_0 + (3 + 2*i)*40 + 5
muralRowB1: .lohifill 10, SCREEN_MEM_0 + (3 + 2*i)*40 + 6

nextColorScheme: {"""
src = sub(src, "nextColorScheme: {", MURAL)

# --- the buddy's dark backdrop on sprite 7 (the player's own mechanism: sprite 2)
src = sub(src, """    lda c64lib.SPRITE_ENABLE
    ora #%01100000
    sta c64lib.SPRITE_ENABLE
    lda #BUDDY_COLOR""", """    lda c64lib.SPRITE_ENABLE
    ora #%11100000              // 5+6 the buddy, 7 his backdrop
    sta c64lib.SPRITE_ENABLE
    lda c64lib.SPRITE_EXPAND_Y
    ora #%10000000              // the backdrop is Y-expanded, like the player's
    sta c64lib.SPRITE_EXPAND_Y
    lda c64lib.SPRITE_2_COLOR   // and wears the player's backdrop colour
    sta c64lib.SPRITE_7_COLOR
    lda #BUDDY_COLOR""")
src = sub(src, """    lda buddyX
    sta c64lib.SPRITE_5_X
    sta c64lib.SPRITE_6_X
    lda buddyX + 1
    beq msbClear
        lda c64lib.SPRITE_MSB_X
        ora #%01100000
        jmp !+
    msbClear:
        lda c64lib.SPRITE_MSB_X
        and #%10011111
    !:
    sta c64lib.SPRITE_MSB_X
    lda buddyY
    sta c64lib.SPRITE_5_Y""", """    lda buddyX
    sta c64lib.SPRITE_5_X
    sta c64lib.SPRITE_6_X
    sta c64lib.SPRITE_7_X
    lda buddyX + 1
    beq msbClear
        lda c64lib.SPRITE_MSB_X
        ora #%11100000
        jmp !+
    msbClear:
        lda c64lib.SPRITE_MSB_X
        and #%00011111
    !:
    sta c64lib.SPRITE_MSB_X
    lda buddyY
    sta c64lib.SPRITE_5_Y
    sta c64lib.SPRITE_7_Y""")
# the BG frame of each pose
src = sub(src, """        lda buddyFacing
        beq !+
            lda jumpRightAnimationTL
            ldx jumpRightAnimationBL
            jmp setPose
        !:
        lda jumpLeftAnimationTL
        ldx jumpLeftAnimationBL
        jmp setPose""", """        lda buddyFacing
        beq !+
            lda jumpRightAnimationBG
            sta buddyBg
            lda jumpRightAnimationTL
            ldx jumpRightAnimationBL
            jmp setPose
        !:
        lda jumpLeftAnimationBG
        sta buddyBg
        lda jumpLeftAnimationTL
        ldx jumpLeftAnimationBL
        jmp setPose""")
for name in ("walkRight", "walkLeft", "idlingRight", "idlingLeft"):
    src = sub(src, f"""            lda {name}AnimationTL, x
            pha""", f"""            lda {name}AnimationBG, x
            sta buddyBg
            lda {name}AnimationTL, x
            pha""")
src = sub(src, """    setPose:
        sta SCREEN_MEM_0 + 1016 + 5
        stx SCREEN_MEM_0 + 1016 + 6
    rts""", """    setPose:
        sta SCREEN_MEM_0 + 1016 + 5
        stx SCREEN_MEM_0 + 1016 + 6
        lda buddyBg
        sta SCREEN_MEM_0 + 1016 + 7
    rts""")
src = sub(src, "    mag:         .byte 0", "    mag:         .byte 0\n    buddyBg:     .byte 0")
# the top-of-frame interrupt repaints sprite 7 with the eyes colour: make it the backdrop colour
src = sub(src, """    lda eyesColor
    sta c64lib.SPRITE_7_COLOR
    lda #BUDDY_COLOR""", """    lda c64lib.SPRITE_2_COLOR   // sprite 7 is the buddy's backdrop now
    sta c64lib.SPRITE_7_COLOR
    lda #BUDDY_COLOR""")
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
