#!/usr/bin/env python3
"""Generate the Chamber build: the buddy game whose back wall is a MURAL drawn
from a 32-byte seed - the block hash at render time, once a contract writes it.

Produces (all generated, all committed):
  src/kickass/level/chamber/data.asm - the buddy level data pointing at
      chamber-room.bin, plus the parameter block: 8-byte marker "MURAL02\\0",
      32 seed bytes, 8 digits, the behaviour byte and the colour byte,
      64-aligned so the block never crosses a page
  src/kickass/tony-chamber.asm       - tony-buddy.asm plus the mural routine,
      hooked between the room decompression and its char translation
  build.gradle.kts                   - the new include (idempotent)

The parameter block (50 bytes, 64-aligned): marker "MURAL02\0", 32 seed
bytes (the block hash), 8 block-number digits (0-9 each), one BEHAVIOUR byte
(0 Follow, 1 Dance; 2-6 reserved for Echo, Mirror, Wander, Shy, Sleeper, which
stand still until they exist) and one COLOUR byte (a C64 colour index, the
buddy's own).  What the seed draws:
  - the WALL: 15 x 10 slots of 2x2 dotted bricks ($B0 $B1 / $B2 $B3), rows 2-21,
    cols 5-34.  Three bit streams run through the 32 bytes (A from byte 0, B from
    byte 19, C from byte 25, each wrapping at 32) and the DENSITY mode decides how
    they combine per slot. Three seed bits (seed[31] & 7) pick the mode through
    the table 3,3,3,0,0,1,1,2 - fewer bricks is always more common: 3 = A&B&C (~1/8
    filled, 3 in 8), 0 = A&B (~1/4, 2 in 8), 1 = A (~1/2, 2 in 8), 2 = A|B (~3/4,
    the rare one, 1 in 8);
  - the CANDLE: at most one. Present when seed[30] & 3 is not zero (3 times in 4).
    Its niche comes from seed[29]: the low 4 bits pick a column through a 16-entry
    table onto 14 slot columns (left column 5 + 2k, k = 0..13), the next 3 bits
    pick a row through an 8-entry table onto rows 4/6/8/10/12 (top row 2 + 2j,
    j = 1..5) - 70 positions, all on the upper and middle wall, never within
    eight rows of the floor. The niche (4x4, rows top..top+3, two wall slots by
    two) is cleared, then the glowing candle of room 10, a 3x3 block $BD-$C5, is
    drawn at rows top..top+2, columns left+1..left+3;
  - the FLOOR: the eight block digits carved into the top course, right-aligned
    against the right pillar (columns 27-34);
  - the BATS: seed bytes 24-27 choose each bat's flight path (eight authored
    ones), start column and row, and whether it is there: one render in
    sixteen has no bats, one in four a single bat. All within a band 30 px
    above Tony's highest jump: they are scenery, never a danger.
The buddy gets the player's own dark backdrop (sprite 7, Y-expanded, the BG
frame of whatever pose he wears) so the wall no longer shows through him.
The buddy's mechanics: buddyUpdate is split into a DECIDE part (what does he
want this frame: buddyMoving, buddyFacing, wantHop) and an ACT part (step,
hop, write the sprite, choose the pose). Follow is the original decide code;
the others live in buddyDecide. DANCE reads voice 3's envelope back from the
SID ($D41C, a register the chip exposes in hardware): a rise of DANCE_RISE or
more since the previous frame is a note hit, and on every hit he hops and
turns round. No timing table, no outside data: he listens to the chip.
tools/stamp_mural.py writes seed, block number, behaviour and colour.

Run from repo root after tools/make_buddy.py and tools/build_chamber_room.py:
    python3 tools/make_chamber.py
"""
import hashlib
import os
import sys

import re as _re

# Options: --music PATH   the level tune (a PSID assembled for $A000; default src/music/TonyLevelA000_V2.sid)
#          --intro PATH   the Glitch's tune (a PSID assembled for $8000; default src/music/TonyIntro8000_reloc.sid)
#          --variant NAME the .asm/.prg name (default tony-chamber)
#          --glitch-ink N the colour of the block number's cells in the Glitch's blackout
#                         (default 0, black on the dark grey stone, the owner's choice; 15 was light grey)
# The base carries both tunes. Behaviour 7 (the Glitch) plays the intro tune; the seven play the
# level tune. The Dancer steps to voice 1 of the level tune and bounces the moment he lands; the
# Glitch's Dance phase steps to voice 2 of the intro tune and keeps the engine's pause after a
# landing (measured: the intro tune's lead would otherwise keep him in the air 99% of the time).
MUSIC = "src/music/TonyLevelA000_V2.sid"
INTRO = "src/music/TonyIntro8000_reloc.sid"
VARIANT = "tony-chamber"
GLITCH_INK = 0
GLITCH_DANCE_VOICE = 2
_args = sys.argv[1:]
while _args:
    _flag = _args.pop(0)
    if _flag == "--music": MUSIC = _args.pop(0)
    elif _flag == "--intro": INTRO = _args.pop(0)
    elif _flag == "--variant": VARIANT = _args.pop(0)
    elif _flag == "--glitch-ink": GLITCH_INK = int(_args.pop(0)); assert 0 <= GLITCH_INK <= 15
    else: raise SystemExit("unknown option " + _flag)
_sid = open(MUSIC, "rb").read()
assert _sid[:4] == b"PSID" and _sid[124:126] == b"\x00\xa0", "the level tune must be a PSID assembled for $A000"
_m = _re.search(rb"\xBD(..)\x9D\x00\xD4", _sid[124 + 2:], _re.S)      # LDA image,X / STA $D400,X
SID_IMAGE = _m.group(1)[0] | (_m.group(1)[1] << 8)                       # the level player's register image ($A474), voice 1
_isid = open(INTRO, "rb").read()
assert _isid[:4] == b"PSID" and _isid[124:126] == b"\x00\x80", "the intro tune must be a PSID assembled for $8000"
_m = _re.search(rb"\xBD(..)\x9D\x00\xD4", _isid[124 + 2:], _re.S)
INTRO_IMAGE = (_m.group(1)[0] | (_m.group(1)[1] << 8)) + 7 * (GLITCH_DANCE_VOICE - 1)   # the intro player's image ($844B), at the Glitch's voice
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
src = sub(src, "materials:\n", f'''// The parameter block. A contract (or tools/stamp_mural.py) overwrites the 42
// bytes after the marker: 32 seed bytes (the block hash), 8 block-number
// digits, the behaviour byte and the colour byte. The marker makes the block
// findable in any build; 64-aligned so it never crosses a page.
.align 64
muralMarker:     .byte $4D, $55, $52, $41, $4C, $30, $32, $00   // "MURAL02\\0"
muralSeed:       .byte {seed_bytes}
muralBlock:      .byte 2, 5, 8, 5, 0, 2, 6, 7                   // block 25850267
muralBehaviour:  .byte 0                                        // 0 Follow, 1 Dance
muralColour:     .byte 5                                        // green, the buddy's original colour
muralBats:       .byte 0, 0, 0, 0, 0, 0, 0, 0                   // written by the game at room entry, for the tests:
                                                                // presence, pathA, colA, rowA, pathB, colB, rowB, 0

materials:
''')
src = sub(src, """// bat flight paths: long glides with slight rises and dips, all up high
path0:          .byte   16, 0, 4, 1, 4, -1, 4, -1, 4, 1    // left third, X 64-128
path1:          .byte   12, 0, 3, -1, 3, 1, 3, 1, 3, -1     // right, X 240-288

pathsPtrsLo:    .byte <path0, <path1
pathsPtrsHi:    .byte >path0, >path1
pathLengths:    .byte 10, 10
""", """// bat flight paths, eight of them, chosen per bat from the seed at every
// render (pairs of frames and a rise or dip per frame; the bat turns round at
// the end of its path; every path nets to zero so it keeps its height, and
// none strays more than 8 px, so the bats stay 30 px above Tony's highest
// jump). Travel = 2 px a frame times the frames: 24..64 px.
path0:          .byte   16, 0, 4, 1, 4, -1, 4, -1, 4, 1    // the long glide (64 px)
path1:          .byte   12, 0, 3, -1, 3, 1, 3, 1, 3, -1     // a shorter glide (48 px)
path2:          .byte   8, 0, 4, 1, 4, -1                   // a short flutter (32 px)
path3:          .byte   6, -1, 6, 1, 6, 1, 6, -1            // a wave (48 px)
path4:          .byte   10, 0, 2, 2, 2, -2, 10, 0, 2, -2, 2, 2  // glides with two hops (56 px)
path5:          .byte   4, 1, 4, -1, 4, 1, 4, -1, 4, 1, 4, -1   // bobbing (48 px)
path6:          .byte   20, 0, 6, 1, 6, -1                  // a long glide with one dip (64 px)
path7:          .byte   3, -2, 3, 2, 3, 2, 3, -2            // a tight nervous flutter (24 px)

pathsPtrsLo:    .byte <path0, <path1, <path2, <path3, <path4, <path5, <path6, <path7
pathsPtrsHi:    .byte >path0, >path1, >path2, >path3, >path4, >path5, >path6, >path7
pathLengths:    .byte 10, 10, 6, 8, 12, 12, 6, 8
""")
src = sub(src, '.import binary "demo-level-materials.bin"', '.import binary "chamber-materials.bin"')
src = sub(src, 'loadNegated("demo-level-charset.bin")', 'loadNegated("chamber-charset.bin")')
os.makedirs("src/kickass/level/chamber", exist_ok=True)
open("src/kickass/level/chamber/data.asm", "w").write(src)
print("wrote src/kickass/level/chamber/data.asm")

# ------------------------------------------------------------- game variant
src = open("src/kickass/tony-buddy.asm").read()
src = sub(src, '.file [name="./tony-buddy.prg"', f'.file [name="./{VARIANT}.prg"')
src = sub(src, '.var music = LoadSid("TonyLevelA000_V2.sid")\n',
          f'.var music = LoadSid("{os.path.basename(MUSIC)}")\n.var intro = LoadSid("{os.path.basename(INTRO)}")   // the Glitch\'s tune, at $8000\n')
# both tunes in the load image: the intro tune first in the Movable segment, copied out last
src = sub(src, ".segment Movable\n\nmusicData:\n", ".segment Movable\n\nintroData:\n    .fill intro.size, intro.getData(i)\nmusicData:\n")
src = sub(src, """    c64lib_pushParamW(musicData)
    c64lib_pushParamW(MUSIC_MEM)
    c64lib_pushParamW(musicSize)
    jsr copyLargeMemForward
""", """    c64lib_pushParamW(musicData)
    c64lib_pushParamW(MUSIC_MEM)
    c64lib_pushParamW(musicSize)
    jsr copyLargeMemForward

    c64lib_pushParamW(introData)        // the Glitch's tune, to $8000 (free at run time), after the level tune
    c64lib_pushParamW(intro.location)   // whose source it would otherwise overwrite
    c64lib_pushParamW(intro.size)
    jsr copyLargeMemForward
""")
src = sub(src, """initSound: {
    ldx #0
    ldy #0
    lda #0
    jsr music.init
    rts
}""", """initSound: {
    ldx #0
    ldy #0
    lda #0
    ldy muralBehaviour          // the Glitch plays the intro tune, the seven the level tune
    cpy #7
    beq !+
        jsr music.init
        rts
    !:
    jsr intro.init
    rts
}""")
src = sub(src, """    doPlay:
        jsr music.play
    rts
}""", """    doPlay:
        ldx muralBehaviour
        cpx #7
        beq !+
            jsr music.play
            rts
        !:
        jsr intro.play
    rts
}""")
src = sub(src, '.print "Music size = " + music.size\n', '.print "Music size = " + music.size\n.print "Intro tune (the Glitch) = $" + toHexString(intro.location) + ", size " + intro.size + ", init $" + toHexString(intro.init) + " play $" + toHexString(intro.play)\n')
src = sub(src, '#import "level/buddy/data.asm"', '#import "level/chamber/data.asm"')
src = sub(src, """buddyInit: {
    lda #120
    sta buddyX
""", """buddyInit: {
    lda muralSeed + 28          // the dice, seeded from the block: bytes the contract leaves to the hash
    eor muralSeed + 15
    sta wanderRng
    lda muralSeed + 3
    eor muralSeed + 20
    sta wanderRngHi
    ora wanderRng
    bne !+
        lda #$5A                // a register at zero would stay at zero
        sta wanderRng
        lda #$A5
        sta wanderRngHi
    !:
    lda #120
    sta buddyX
""")
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
//         3 = A&B&C (3/8)  0 = A&B (2/8)  1 = A (2/8)  2 = A|B (1/8, rare)
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
    lda muralBehaviour          // the Glitch's room is the blackout: no bricks at all
    cmp #7
    bne !+
        lda #4
        sta mode
    !:

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
            cmp #4
            bne !+
                lda #0          // mode 4: bare
                jmp decide
            !:
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
    lda muralBehaviour          // the blackout has no candle
    cmp #7
    bne !+
        jmp candleDone
    !:
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
    lda muralBehaviour          // the blackout: the block number's cells take the blackout's ink (black) on the dark stone
    cmp #7
    bne digitsInked
        ldx #0
        lda #{GLITCH_INK}
        inkLoop:
            sta c64lib.COLOR_RAM + 23*40 + 27, x
            inx
            cpx #8
            bne inkLoop
    digitsInked:
    jsr muralBatsStamp
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
    modeTable:   .byte 3, 3, 3, 0, 0, 1, 1, 2         // eighth x3, quarter x2, half x2, dense x1: fewer bricks = more common
    kTable:      .byte 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 4, 9
    jTable:      .byte 1, 2, 3, 4, 5, 2, 3, 4
}
// BATS from the seed (the owner's ask): each bat's flight path (eight to
// choose from), start column and row, and whether it is there at all, written
// into the room's object tables before initObjects reads them, and reported
// in muralBats. Seed bytes 24-27. Presence from seed[27] & 15: 0 none (one
// render in sixteen), 1-2 only the left bat, 3-4 only the right, else both.
// Rows 2-9 keep every path's lowest point 30 px above Tony's highest jump;
// the left bat starts in columns 2-9 and the right in 24-29, so with travel
// of at most 64 px they never meet (their sprites must not touch).
muralBatsStamp: {
    lda level_objectPositionXPtr.lo
    sta writeX
    sta writeX2
    lda level_objectPositionXPtr.hi
    sta writeX + 1
    sta writeX2 + 1
    lda level_objectPositionYPtr.lo
    sta writeY
    sta writeY2
    lda level_objectPositionYPtr.hi
    sta writeY + 1
    sta writeY2 + 1
    lda level_movableObjectValue2Ptr.lo
    sta writeV
    sta writeV2
    lda level_movableObjectValue2Ptr.hi
    sta writeV + 1
    sta writeV2 + 1
    // the left bat: path seed[24] & 7, column 2 + (seed[24] >> 3 & 7), row 2 + (seed[25] & 7)
    ldy #0
    lda muralSeed + 24
    and #7
    sta muralBats + 1
    sta writeV: $ffff, y
    lda muralSeed + 24
    lsr
    lsr
    lsr
    and #7
    clc
    adc #2
    sta muralBats + 2
    sta writeX: $ffff, y
    lda muralSeed + 25
    and #7
    clc
    adc #2
    sta muralBats + 3
    sta writeY: $ffff, y
    // the right bat: path seed[25] >> 3 & 7, column 24 + colB[seed[26] & 7], row 2 + (seed[26] >> 3 & 7)
    iny
    lda muralSeed + 25
    lsr
    lsr
    lsr
    and #7
    sta muralBats + 4
    sta writeV2: $ffff, y
    lda muralSeed + 26
    and #7
    tax
    lda colB, x
    sta muralBats + 5
    sta writeX2: $ffff, y
    lda muralSeed + 26
    lsr
    lsr
    lsr
    and #7
    clc
    adc #2
    sta muralBats + 6
    sta writeY2: $ffff, y
    // presence
    lda muralSeed + 27
    and #15
    ldy muralBehaviour          // the blackout has no bats
    cpy #7
    bne !+
        lda #0
    !:
    sta muralBats
    ldx #%11111111              // both
    cmp #5
    bcs presence
    ldx #%11111110              // 3-4: the right bat only (bit 0 is the left bat)
    cmp #3
    bcs presence
    ldx #%11111101              // 1-2: the left bat only
    cmp #1
    bcs presence
    ldx #%11111100              // 0: a quiet night
    presence:
    txa
    and level_roomStates
    sta level_roomStates
    rts
    colB: .byte 24, 25, 26, 27, 28, 29, 26, 28
}
muralRowA:  .lohifill 10, SCREEN_MEM_0 + (2 + 2*i)*40 + 5
muralRowA1: .lohifill 10, SCREEN_MEM_0 + (2 + 2*i)*40 + 6
muralRowB:  .lohifill 10, SCREEN_MEM_0 + (3 + 2*i)*40 + 5
muralRowB1: .lohifill 10, SCREEN_MEM_0 + (3 + 2*i)*40 + 6

nextColorScheme: {"""
MURAL = MURAL.replace("lda #{GLITCH_INK}", f"lda #{GLITCH_INK}")   # the Glitch's digit ink, an option
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
    lda buddyColourNow          // the buddy's colour: the parameter block's, or the Glitch's cycle""")
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
    lda buddyColourNow""")

# --- the mechanics: split buddyUpdate into decide and act, dispatch on the behaviour byte
src = sub(src, """.label BUDDY_HOP_LEN  = 14
""", """.label BUDDY_HOP_LEN  = 26  // Tony's own jump, measured: 26 frames to a 23-pixel apex
""")
src = sub(src, """.label BUDDY_HOP_COOL = 20
""", """.label BUDDY_HOP_COOL = 20
.label DANCE_RISE     = 6   // ENV3 must climb this much in one frame to count as a hit
.label DANCE_SLIDE    = 6   // pixels he side-steps on every note (one per frame)
.label ECHO_DELAY     = 200 // frames behind the player (4 s); the ring holds 256
.label MIRROR_SUM     = 344 // twice the centre line between the pillars (64..280)
.label SHY_FLEE_AT    = 56  // closer than this: he runs
.label SHY_CALM_AT    = 110 // farther than this: he creeps back
.label SHY_BOLT_AT    = 16  // cornered and the player this close: he bolts straight past him
.label SLEEP_WAKE_AT  = 48  // an approach inside this wakes him
.label SLEEP_AWAKE    = 150 // half-frames awake before he dozes off again (300 frames, 6 s)
""")
src = sub(src, """    // signed 16-bit distance to the player -> mag + targetRight
""", """    // decide: which mechanic runs this frame. Follow is below; the others
    // are in buddyDecide; the Sleeper is Follow while he is awake.
    lda #0
    sta nextPoseMoving
    sta nextCrouch
    sta nextJumpPose
    lda muralColour
    sta buddyColourNow
    lda muralBehaviour
    cmp #7
    bne !+
        jsr glitchTick          // the Glitch: returns the mechanic he wears this frame (0-6)
    !:
    sta buddyMode
    cmp #6
    bne !+
        jsr sleeperDecide       // returns 0 (awake: Follow) or 8 (dozing)
        sta buddyMode
    !:
    lda buddyMode
    beq follow
        jsr buddyDecide
        jmp act
    follow:

    // signed 16-bit distance to the player -> mag + targetRight
""")
src = sub(src, """    // always turn towards the player
    lda targetRight
    sta buddyFacing

    // one pixel towards him, clamped to the space between the pillars
    lda buddyMoving
    beq noMove
        lda targetRight
        beq stepLeft""", """    // always turn towards the player
    lda targetRight
    sta buddyFacing

    // hop when the player leaves the ground
    lda #0
    sta wantHop
    lda physPlayerY
    cmp #(BUDDY_FLOOR_Y - 8)
    bcs !+
        inc wantHop
    !:
    jsr playerCrouch            // and crouch when he crouches

    act:
    lda nextCrouch                  // the pose flags, committed once per frame
    sta buddyCrouch
    lda nextPoseMoving
    sta buddyPoseMoving
    lda nextJumpPose
    sta buddyJumpPose
    // one pixel the way he faces, clamped to the space between the pillars
    lda buddyMoving
    beq noMove
        lda buddyFacing
        beq stepLeft""")
src = sub(src, """    // hop when the player leaves the ground
    lda buddyHop
    bne doHop
        lda buddyCool
        beq !+
            dec buddyCool
            jmp hopDone
        !:
        lda physPlayerY
        cmp #(BUDDY_FLOOR_Y - 8)
        bcs hopDone
            lda #1
            sta buddyHop""", """    // hop when the decide part asked for one
    lda buddyHop
    bne doHop
        lda buddyCool
        beq !+
            dec buddyCool
            jmp hopDone
        !:
        lda wantHop
        beq hopDone
            lda #1
            sta buddyHop
            lda #0
            sta wantHop""")
# the pose: walking when he moves or only looks as if he does; crouched when a mechanic says so
src = sub(src, """    lda currentColor
    sta c64lib.BG_COL_0
    ldx #0
    !:
        cpx #2
        beq skip
            sta c64lib.SPRITE_0_COLOR, x""", """    lda currentColor
    ldx muralBehaviour          // the Glitch's blackout: the room in dark grey, Tony in grey
    cpx #7
    bne !+
        lda #11
    !:
    sta c64lib.BG_COL_0
    lda currentColor
    cpx #7
    bne !+
        lda #12
    !:
    ldx #0
    !:
        cpx #2
        beq skip
            sta c64lib.SPRITE_0_COLOR, x""")
src = sub(src, """    lda buddyHop
    beq notHopping""", """    lda buddyHop
    ora buddyJumpPose
    beq notHopping""")
src = sub(src, """    notHopping:
    lda buddyMoving
    beq standing""", """    notHopping:
    lda buddyMoving
    ora buddyPoseMoving
    beq standing""")
src = sub(src, """    standing:
        // the real idle: 6 phases at the player's own idle tempo
""", """    standing:
        lda buddyCrouch             // sitting, hiding or dozing: the crouch, fully down (frame 2 of the duck)
        beq idleCycle
            lda buddyFacing
            beq crouchL
                lda duckRightAnimationBG + 2
                sta buddyBg
                lda duckRightAnimationTL + 2
                ldx duckRightAnimationBL + 2
                jmp setPose
            crouchL:
                lda duckLeftAnimationBG + 2
                sta buddyBg
                lda duckLeftAnimationTL + 2
                ldx duckLeftAnimationBL + 2
                jmp setPose
        idleCycle:
        // the real idle: 6 phases at the player's own idle tempo
""")
src = sub(src, """hopArc:       .byte 253, 253, 254, 254, 255, 255, 0, 0, 1, 1, 2, 2, 3, 3
""", f"""// Tony's jump, frame by frame (physPlayerY deltas measured on minimal64): the buddy jumps exactly as he does
hopArc:       .byte 252, 252, 252, 254, 254, 254, 255, 255, 255, 0, 255, 0, 255, 1, 0, 1, 0, 1, 1, 1, 2, 2, 2, 4, 4, 4
// mechanics state, in this order (tools/verify_buddy.py finds it from the hop arc)
wantHop:      .byte 0        // +14
envPrev:      .byte 0        // +15
stepCount:    .byte 0        // +16
slideCount:   .byte 0        // +17
noteOld:      .word 0        // +18
noteNew:      .word 0        // +20
noteDiff:     .word 0        // +22
noteStep:     .word 0        // +24
buddyMode:    .byte 0        // +26  the mechanic running this frame (8 = the Sleeper dozing)
buddyPoseMoving: .byte 0     // +27  show the walk although the act part does not step
buddyCrouch:  .byte 0        // +28  show the crouch
distMag:      .byte 0        // +29  |player - buddy|, saturated at 255
distRight:    .byte 0        // +30  1 when the player is to the right
echoHead:     .byte 0        // +31
echoFill:     .byte 0        // +32
echoAirPrev:  .byte 0        // +33
mirrorAirPrev: .byte 0       // +34
wanderTimer:  .byte 0        // +35
wanderState:  .byte 0        // +36  0 pause, 1 stroll, 2 sit
shyToggle:    .byte 0        // +37
sleepAwake:   .byte 0        // +38
sleepFar:     .byte 0        // +39
sleepTimer:   .byte 0        // +40
sleepHalf:    .byte 0        // +41
target:       .word 0        // +42  scratch: where Echo and Mirror put him
nextCrouch:   .byte 0        // +44  the pose flags the mechanics ask for, committed by the act part
nextPoseMoving: .byte 0      // +45
wanderRng:    .byte 0        // +46  the dice, low byte: a 16-bit shift register seeded from the block (see rollDice)
nextJumpPose: .byte 0        // +47  show the jump although the act part is not hopping (Echo)
buddyJumpPose: .byte 0       // +48
shyBolt:      .byte 0        // +49  the Shy is bolting out of a corner, past the player
buddyColourNow: .byte 0      // +50  the colour the sprites wear this frame
glitchMode:   .byte 0        // +51  the Glitch: the mechanic he wears now
glitchTimer:  .word 0        // +52  frames until he changes it
glitchBurst:  .byte 0        // +54  frames left of a burst of flicker and jitter
glitchStep:   .byte 0        // +55  where he is in the colour cycle
glitchFrame:  .byte 0        // +56
glitchWarp:   .byte 0        // +57  frames left of a teleport: out, elsewhere, in
wanderRngHi:  .byte 0        // +58  the dice's high byte (wanderRng is the low byte, the byte the mechanics read)

// The dice: a 16-bit Galois shift register (x^16 + x^14 + x^13 + x^11 + 1, period
// 65,535), seeded from the block in buddyInit and stepped eight times a frame by
// whoever rolls (the Wanderer's plan, the Glitch's every frame), so a render's
// dice are a pure function of its seed and the frame count: nothing from the
// chip, the raster or the player is stirred in. Returns A = the low byte.
rollDice:
    ldx #8
rollStep:
    lsr wanderRngHi
    ror wanderRng
    bcc rollNext
        lda wanderRngHi
        eor #$B4
        sta wanderRngHi
    rollNext:
    dex
    bne rollStep
    lda wanderRng
    rts

// |player - buddy| and which side he is on (the Follow code has its own copy inline)
buddyDistance: {{
    sec
    lda physPlayerX
    sbc buddyX
    sta distMag
    lda physPlayerX + 1
    sbc buddyX + 1
    bpl right
        ldy #0
        sty distRight
        cmp #$ff
        bne far
        sec
        lda #0
        sbc distMag
        sta distMag
        rts
    right:
        ldy #1
        sty distRight
        cmp #0
        beq done
    far:
        lda #$ff
        sta distMag
    done:
    rts
}}

// Crouch when the player crouches (Follow and Mirror); the act part shows it
// once he stands still.
playerCrouch: {{
    lda physPlayerAnimation
    cmp #ANIM_DUCK_LEFT
    beq yes
    cmp #ANIM_DUCK_RIGHT
    beq yes
    cmp #ANIM_DUCK_QUICK_LEFT
    beq yes
    cmp #ANIM_DUCK_QUICK_RIGHT
    bne no
    yes:
        lda #1
        sta nextCrouch
    no:
    rts
}}

// Put him at `target` (Echo, Mirror): facing and the walking pose follow from
// the move; the act part does not step, it only writes the sprite.
buddyPlace: {{
    sec
    lda target
    sbc buddyX
    sta noteDiff
    lda target + 1
    sbc buddyX + 1
    bmi left
        ora noteDiff
        beq done                    // no move: keep facing, stand
        lda #1
        sta buddyFacing
        bne moved
    left:
        lda #0
        sta buddyFacing
    moved:
        lda #1
        sta nextPoseMoving
    done:
    lda target
    sta buddyX
    lda target + 1
    sta buddyX + 1
    rts
}}

// The Sleeper: dozes until the player comes close, is awake (and Follow) for
// SLEEP_AWAKE half-frames, then dozes off again. Returns A = 0 awake, 8 dozing.
sleeperDecide: {{
    jsr buddyDistance
    lda sleepAwake
    bne awake
        lda distMag
        cmp #SLEEP_WAKE_AT
        bcs stillFar
            lda sleepFar            // an approach: he was far a moment ago
            beq dozing
                lda #1
                sta sleepAwake
                lda #SLEEP_AWAKE
                sta sleepTimer
                lda #0
                sta sleepFar
                rts                 // A = 0: awake, Follow runs
        stillFar:
            lda #1
            sta sleepFar
        dozing:
            lda #8
            rts
    awake:
        lda sleepHalf
        eor #1
        sta sleepHalf
        beq !+
            lda #0
            rts
        !:
        dec sleepTimer
        bne !+
            lda #0
            sta sleepAwake
            sta sleepFar
            lda #8
            rts
        !:
        lda #0
        rts
}}

// The Glitch (mechanic 7): the buddy in the ordinary slot, wearing one of the
// seven mechanics at a time and changing it every 3-8 s on the same dice as
// the Wanderer; cycling through the seven token colours, one every eight
// frames; now and then a burst of 8-15 frames in which his colour goes
// random, he blinks out one frame in four, and he jitters a pixel sideways;
// and a teleport at every change of mechanic (and one burst in eight): he
// blinks out for twelve frames and is somewhere else in the room when he
// comes back.
// His room is the blackout: the mural routine draws no wall, no candle and
// no bats when the behaviour byte is 7, the interrupt paints the room dark
// grey and Tony grey, and the block number's cells keep light-grey ink.
// Returns A = the mechanic worn.
glitchTick: {{
    jsr rollDice                // the dice, from the seed
    lda glitchTimer
    ora glitchTimer + 1
    bne holding
        lda wanderRng           // a new mechanic: 0-6, a 7 becomes the Wanderer
        and #7
        cmp #7
        bne !+
            lda #4
        !:
        sta glitchMode
        lda wanderRng           // and a new hold: 150 + 0..255 frames
        clc
        adc #150
        sta glitchTimer
        lda #0
        adc #0
        sta glitchTimer + 1
        lda #0                  // the stateful mechanics start afresh
        sta sleepAwake
        sta sleepFar
        sta shyBolt
        sta wanderTimer
        lda #12                 // and he teleports
        sta glitchWarp
    holding:
    lda glitchTimer
    bne !+
        dec glitchTimer + 1
    !:
    dec glitchTimer
    inc glitchFrame             // the colour cycle
    lda glitchFrame
    and #7
    bne !+
        inc glitchStep
    !:
    lda glitchStep
    cmp #7
    bcc !+
        lda #0
        sta glitchStep
    !:
    tax
    lda glitchColours, x
    sta buddyColourNow
    lda glitchWarp              // a teleport in progress: out for twelve frames, elsewhere at the sixth
    beq noWarp
        dec glitchWarp
        lda #0
        sta buddyColourNow
        lda glitchWarp
        cmp #6
        beq warpNow
        jmp done
        warpNow:
            lda wanderRng       // somewhere between the pillars: 64 + (0..127), or 88 farther right
            and #127
            clc
            adc #64
            sta buddyX
            lda #0
            sta buddyX + 1
            lda wanderRng
            bmi warpFar
            jmp done
            warpFar:
                lda buddyX
                clc
                adc #88
                sta buddyX
                bcc !+
                    inc buddyX + 1
                !:
            jmp done
    noWarp:
    lda glitchBurst             // bursts
    bne inBurst
        lda wanderRng
        cmp #3                  // three chances in 256 a frame: one burst in about 85 frames
        bcc burstStart
        jmp done
        burstStart:
        lda wanderRng
        and #7
        clc
        adc #8
        sta glitchBurst
        lda wanderRng           // one burst in eight is a teleport instead
        and #%00111000
        bne inBurst
            lda #12
            sta glitchWarp
            lda #0
            sta glitchBurst
            jmp done
    inBurst:
        dec glitchBurst
        lda wanderRng
        and #3
        bne !+
            lda #0              // blinks out
            sta buddyColourNow
            jmp jitter
        !:
        lda wanderRng
        lsr
        lsr
        and #15
        sta buddyColourNow
        jitter:
        lda wanderRng
        and #%00110000
        beq done
        cmp #%00100000
        bcc jitterLeft
            lda buddyX + 1      // a pixel to the right, short of the pillar
            beq !+
                lda buddyX
                cmp #(BUDDY_MAX_XLO - 2)
                bcs done
            !:
            inc buddyX
            bne done
                inc buddyX + 1
            jmp done
        jitterLeft:
            lda buddyX + 1      // a pixel to the left, short of the pillar
            bne !+
                lda buddyX
                cmp #(BUDDY_MIN_XLO + 2)
                bcc done
            !:
            lda buddyX
            bne !+
                dec buddyX + 1
            !:
            dec buddyX
    done:
    lda glitchMode
    rts
    glitchColours: .byte 6, 3, 7, 14, 5, 10, 4
}}

// The mechanics other than Follow. Each leaves buddyMoving, buddyFacing,
// wantHop, buddyPoseMoving and buddyCrouch for this frame; the act part of
// buddyUpdate does the rest.
//
// DANCE listens to two things, both inside the machine:
//  - the beat: voice 1's note, read from the image of the sound-chip registers
//    that the tune's player keeps in RAM and copies to the chip every frame
//    (SID_IMAGE, found in the player by its copy loop). A move of half a
//    semitone or more (|new - old| >= old / 32) is a step: the pose advances
//    one phase and he side-steps DANCE_SLIDE pixels the way he faces; every
//    fourth step he turns round, so he shuffles a body-width each way.
//    Between steps the pose holds: he moves only when the music moves.
//  - the hits: voice 3's envelope read back from the chip itself ($D41C). A
//    rise of DANCE_RISE or more in a frame is a note hit: a hop, queued until
//    he is on the ground again, so a double hit is a double bounce.
// ECHO records the player every frame - where he is, how high, which pose he
//    wears - in a 256-entry ring, and plays it back ECHO_DELAY frames later,
//    frame for frame: every step, every jump, every duck, in order, until the
//    recording runs out (which it never does: it is always the last 4 s).
// MIRROR stands at the player's reflection about the centre line between the
//    pillars (x' = MIRROR_SUM - x, clamped to the pillars), faces the way the
//    player's reflection would (the opposite of the player's facing, read from
//    his animation every frame, so a turn in place is answered too), and
//    contradicts him the other way as well: crouches while he is in the air,
//    bounces while he is crouched (a funhouse mirror, the owner's idea).
// WANDER lives there: a plan at a time (stroll, pause, sit, a jump on the
//    spot), the choice and its length rolled from a shift register seeded
//    from the block (rollDice: eight bits a frame, nothing else stirred in),
//    the pauses lengthened by the render's mood (two seed bits); one stroll
//    in eight starts with a running jump. He turns at the pillars and takes no notice of the player.
// SHY runs when the player is closer than SHY_FLEE_AT, cowers at the pillar
//    when he can run no farther, and bolts straight past the player when he
//    comes within SHY_BOLT_AT of the cornered buddy (keeping on until the
//    player is behind him, when the ordinary flee carries him on); creeps back
//    at half speed when the player is farther than SHY_CALM_AT; watches him in
//    between.
.label SID_IMAGE = ${SID_IMAGE:04X}
.label INTRO_IMAGE = ${INTRO_IMAGE:04X}
buddyDecide: {{
    lda #0
    sta buddyMoving
    ldx buddyMode
    cpx #1
    bne !+
        jmp dance
    !:
    cpx #2
    bne !+
        jmp echo
    !:
    cpx #3
    bne !+
        jmp mirror
    !:
    cpx #4
    bne !+
        jmp wander
    !:
    cpx #5
    bne !+
        jmp shy
    !:
    cpx #8
    bne !+
        jmp doze
    !:
    lda #0
    sta wantHop
    rts

    dance:
    lda muralBehaviour              // the Glitch dances to the intro tune's voice 2
    cmp #7
    beq rereadIntro
    reread:                         // the player runs in the interrupt: read lo, hi, lo again
        lda SID_IMAGE
        sta noteNew
        lda SID_IMAGE + 1
        sta noteNew + 1
        lda SID_IMAGE
        cmp noteNew
        bne reread
    jmp noteRead
    rereadIntro:
        lda INTRO_IMAGE
        sta noteNew
        lda INTRO_IMAGE + 1
        sta noteNew + 1
        lda INTRO_IMAGE
        cmp noteNew
        bne rereadIntro
    noteRead:
    sec                             // diff = |new - old|
    lda noteNew
    sbc noteOld
    sta noteDiff
    lda noteNew + 1
    sbc noteOld + 1
    sta noteDiff + 1
    bpl absDone
        sec
        lda #0
        sbc noteDiff
        sta noteDiff
        lda #0
        sbc noteDiff + 1
        sta noteDiff + 1
    absDone:
    lda noteOld                     // step = old / 32
    sta noteStep
    lda noteOld + 1
    sta noteStep + 1
    ldx #5
    shift:
        lsr noteStep + 1
        ror noteStep
        dex
        bne shift
    lda noteNew
    sta noteOld
    lda noteNew + 1
    sta noteOld + 1
    lda noteDiff                    // diff >= step ?
    cmp noteStep
    lda noteDiff + 1
    sbc noteStep + 1
    bcc noStep
        inc buddyPhase              // one pose per note
        lda #DANCE_SLIDE            // and one side-step
        sta slideCount
        inc stepCount
        lda stepCount
        and #3
        bne noStep
            lda buddyFacing         // every fourth note: turn round
            eor #1
            sta buddyFacing
    noStep:
    lda slideCount                  // a side-step in progress: one pixel per frame
    beq noSlide
        dec slideCount
        lda #1
        sta buddyMoving
    noSlide:
    lda #0
    sta buddyDelay                  // the pose moves only with the music
    ldx muralBehaviour              // the Dancer may bounce again the moment he lands;
    cpx #7                          // the Glitch keeps the engine's pause (his tune's hits never stop)
    beq !+
        sta buddyCool
    !:
    lda $D41C                       // ENV3: voice 3's envelope, from the chip
    tax
    sec
    sbc envPrev
    stx envPrev
    bcc danceDone                   // falling or flat: no hit
    cmp #DANCE_RISE
    bcc danceDone
        lda #1
        sta wantHop                 // queued until he is on the ground
    danceDone:
    rts

    echo:
    lda #0
    sta wantHop
    ldx echoHead                    // record this frame: where he is, how high, what he looks like
    lda physPlayerX
    sta echoLo, x
    lda physPlayerX + 1
    sta echoHi, x
    lda physPlayerY
    sta echoY, x
    lda physPlayerAnimation
    sta echoAnim, x
    inc echoHead
    lda echoFill                    // nothing to replay until the ring holds the delay
    cmp #ECHO_DELAY
    bcs replay
        inc echoFill
        rts
    replay:
    lda echoHead
    sec
    sbc #(ECHO_DELAY + 1)           // the entry recorded ECHO_DELAY frames ago
    tax
    lda echoLo, x
    sta buddyX
    lda echoHi, x
    sta buddyX + 1
    lda echoY, x
    sta buddyY
    lda echoAnim, x                 // the pose he wore, and the way he faced
    cmp #20
    bcc !+
        lda #6                      // anything unknown: idle, keep facing
    !:
    tay
    lda echoPose, y
    pha
    and #3
    cmp #2
    beq keepFacing
        sta buddyFacing
    keepFacing:
    pla
    lsr
    lsr                             // 0 idle, 1 walk, 2 crouch, 3 jump
    beq echoDone
    cmp #1
    bne !+
        sta nextPoseMoving
        rts
    !:
    cmp #2
    bne !+
        lda #1
        sta nextCrouch
        rts
    !:
    lda #1
    sta nextJumpPose
    echoDone:
    rts

    mirror:
    lda #0
    sta wantHop
    sta buddyCool                   // no pause between bounces
    sec                             // target = MIRROR_SUM - playerX
    lda #<MIRROR_SUM
    sbc physPlayerX
    sta target
    lda #>MIRROR_SUM
    sbc physPlayerX + 1
    sta target + 1
    bne highSide
        lda target                  // 0..255: not left of the left pillar
        cmp #BUDDY_MIN_XLO
        bcs placed
            lda #BUDDY_MIN_XLO
            sta target
            jmp placed
    highSide:
        cmp #1                      // 256..: not right of the right pillar
        bne clampRight
        lda target
        cmp #(BUDDY_MAX_XLO + 1)
        bcc placed
        clampRight:
            lda #1
            sta target + 1
            lda #BUDDY_MAX_XLO
            sta target
    placed:
    jsr buddyPlace
    lda physPlayerAnimation         // face the way his reflection faces: the opposite of him
    cmp #20
    bcs mirrorFaced
    tay
    lda echoPose, y
    and #3
    cmp #2
    beq mirrorFaced                 // an animation without a side: keep facing
    eor #1
    sta buddyFacing
    mirrorFaced:
    lda physPlayerY                 // he is in the air: crouch (shown once the buddy is on the ground)
    cmp #(BUDDY_FLOOR_Y - 8)
    bcs mirrorGround
        lda #1
        sta nextCrouch
        rts
    mirrorGround:
    lda physPlayerAnimation         // he is crouched: bounce, and keep bouncing while he stays down
    cmp #ANIM_DUCK_LEFT
    beq mirrorBounce
    cmp #ANIM_DUCK_RIGHT
    beq mirrorBounce
    cmp #ANIM_DUCK_QUICK_LEFT
    beq mirrorBounce
    cmp #ANIM_DUCK_QUICK_RIGHT
    bne mirrorDone
    mirrorBounce:
        lda #1
        sta wantHop
    mirrorDone:
    rts

    wander:
    lda #0
    sta wantHop
    jsr rollDice                    // the dice: from the seed, eight bits a frame
    lda wanderTimer
    beq newPlan
        dec wanderTimer
        jmp wanderAct
    newPlan:
        lda wanderRng
        sta noteDiff                // (scratch)
        and #7                      // 0-3 stroll, 4-5 pause, 6 a jump on the spot, 7 sit
        cmp #4
        bcc planStroll
        cmp #7
        beq planSit
        cmp #6
        bne planPause
            lda #1                  // a jump on the spot, then he stands a moment
            sta wantHop
        planPause:
            lda #0
            sta wanderState
            lda noteDiff
            lsr
            lsr
            lsr
            and #63
            clc
            adc #30
            jmp moodier
        planSit:
            lda #2
            sta wanderState
            lda noteDiff
            lsr
            lsr
            lsr
            and #127
            clc
            adc #90
            jmp moodier
        planStroll:
            lda #1
            sta wanderState
            lda noteDiff
            lsr
            lsr
            lsr
            and #1
            sta buddyFacing         // the dice pick the way
            lda noteDiff
            and #%11100000          // one stroll in eight starts with a running jump
            cmp #%11100000
            bne !+
                lda #1
                sta wantHop
            !:
            lda noteDiff
            lsr
            lsr
            and #63
            clc
            adc #40                 // 40..103 pixels
            sta wanderTimer
            jmp wanderAct
        moodier:                    // the render's mood: seed bits lengthen the rests
            sta wanderTimer
            lda muralSeed + 28
            and #3
            beq wanderAct
            tax
            !:
                lda wanderTimer
                clc
                adc #20
                bcs !+
                sta wanderTimer
                dex
                bne !-
            !:
    wanderAct:
        lda wanderState
        cmp #1
        bne notStroll
            lda buddyX + 1          // turn at the pillars
            bne rightHalf
                lda buddyX
                cmp #(BUDDY_MIN_XLO + 1)
                bcs strollOn
                    lda #1
                    sta buddyFacing
                    bne strollOn
            rightHalf:
                lda buddyX
                cmp #BUDDY_MAX_XLO
                bcc strollOn
                    lda #0
                    sta buddyFacing
            strollOn:
            lda #1
            sta buddyMoving
            rts
        notStroll:
        cmp #2
        bne wanderDone
            lda #1
            sta nextCrouch
        wanderDone:
        rts

    shy:
    lda #0
    sta wantHop
    jsr buddyDistance
    lda shyBolt                     // bolting out of a corner: keep going until the player is behind him
    beq notBolting
        lda distMag
        cmp #SHY_FLEE_AT
        bcs boltDone                // far enough away: the ordinary rules again
        lda buddyFacing
        cmp distRight
        bne boltDone                // past him now: the ordinary flee carries on this way
        jmp fleeOn
        boltDone:
            lda #0
            sta shyBolt
    notBolting:
    lda distMag
    cmp #SHY_FLEE_AT
    bcs notClose
        lda distRight               // run the other way
        eor #1
        sta buddyFacing
        beq fleeLeft
            lda buddyX + 1
            beq fleeOn
            lda buddyX
            cmp #BUDDY_MAX_XLO
            bcc fleeOn
            jmp cower
        fleeLeft:
            lda buddyX + 1
            bne fleeOn
            lda buddyX
            cmp #(BUDDY_MIN_XLO + 1)
            bcs fleeOn
        cower:                      // nowhere left to run: hide, and bolt past him if he comes too close
            lda distMag
            cmp #SHY_BOLT_AT
            bcs hide
                lda distRight       // straight at him, and through
                sta buddyFacing
                lda #1
                sta shyBolt
                jmp fleeOn
            hide:
            lda #1
            sta nextCrouch
            rts
        fleeOn:                     // two pixels a frame, the player's own speed: one here, one in the act part
            lda buddyFacing
            beq fleeStepLeft
                inc buddyX
                bne fleeMove
                    inc buddyX + 1
                jmp fleeMove
            fleeStepLeft:
                lda buddyX
                bne !+
                    dec buddyX + 1
                !:
                dec buddyX
            fleeMove:
            lda #1
            sta buddyMoving
            rts
    notClose:
    lda distRight                   // watch him
    sta buddyFacing
    lda distMag
    cmp #SHY_CALM_AT
    bcc shyDone
        lda #1                      // far away: creep back at half speed
        sta nextPoseMoving
        lda shyToggle
        eor #1
        sta shyToggle
        beq shyDone
            lda #1
            sta buddyMoving
    shyDone:
    rts

    doze:                           // the Sleeper, asleep
    lda #0
    sta wantHop
    lda #1
    sta nextCrouch
    rts
}}
echoLo:   .fill 256, 0
echoHi:   .fill 256, 0
echoY:    .fill 256, BUDDY_FLOOR_Y
echoAnim: .fill 256, ANIM_IDLING_RIGHT
// the player's animation number -> pose * 4 + facing (0 left, 1 right, 2 keep):
// walk L/R, duck L/R, idle L/R, ladder, jump L/R, ladder stop, death L/R,
// skull, bat, deadman L/R, bat L/R, quick duck L/R
echoPose: .byte 4, 5, 8, 9, 0, 1, 2, 12, 13, 2, 0, 1, 2, 2, 0, 1, 2, 2, 8, 9
""")
open(f"src/kickass/{VARIANT}.asm", "w").write(src)
print(f"wrote src/kickass/{VARIANT}.asm (level tune {os.path.basename(MUSIC)}, image ${SID_IMAGE:04X}; "
      f"the Glitch's tune {os.path.basename(INTRO)} at $8000, his Dance voice at ${INTRO_IMAGE:04X})")

# ------------------------------------------------------------- build wiring
g = open("build.gradle.kts").read()
if f"{VARIANT}.asm" not in g:
    g = sub(g, '        "src/kickass/tony-buddy.asm",\n', f'        "src/kickass/tony-buddy.asm",\n        "src/kickass/{VARIANT}.asm",\n')
    open("build.gradle.kts", "w").write(g)
    print("build.gradle.kts: include added")
else:
    print("build.gradle.kts: include already present")
