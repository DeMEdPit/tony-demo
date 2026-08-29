#!/usr/bin/env python3
"""Generate the "Buddy" variant: the tall Colonnade plus a green follower Tony.

Produces:
  src/kickass/level/buddy/data.asm  - tall pillar room (40x25), two bats
                                      (sprites 3+4; 5+6 belong to the buddy)
  src/kickass/physics-tall.asm      - physics fork: collision scanning
                                      extended from 20 to 25 rows
  src/kickass/tony-buddy.asm        - one-room variant with:
      * NO boot menu: loads straight into the chamber (menu module dropped)
      * NO dashboard: the raster split is removed, the playfield runs the
        full 25 rows, the floor sits at the bottom of the screen
      * a green buddy Tony on sprites 5+6 wearing the player's own frames:
        follows with personal-space hysteresis, faces the player, hops when
        he jumps, and idles with the real 6-phase breathing animation
      * enemy collision masked to the bats, so touching the buddy is safe

Run from repo root: python3 tools/make_buddy.py
"""

import os
import subprocess

# ---------------------------------------------------------------- level data
src = open("src/kickass/level/pillars/data.asm").read()
src = src.replace(
    '// "The Colonnade" - an empty sealed chamber: floor, ceiling, two big\n'
    '// pillars for walls, and bats high above. Map: tools/build_pillar_room.py.',
    '// "The Colonnade + Buddy" - the TALL pillar chamber (full 25 rows, no\n'
    '// dashboard) with two bats up high (sprites 3+4). Sprites 5+6 carry the\n'
    '// green buddy Tony, which is engine code in tony-buddy.asm, not a level\n'
    '// object. Map: tools/build_tall_room.py.')
old = 'level_pack("pillar-room.bin"'
assert src.count(old) == 1
src = src.replace(old, 'level_pack("pillar-room-tall.bin"')
old = "level_startPositionY:   .byte 150   // feet on the floor (row 18)"
assert src.count(old) == 1
src = src.replace(old, "level_startPositionY:   .byte 180   // drops to the floor at row 23")
old = """        objectExt(SO_BAT, 0, 5, 3, 0),      // three bats gliding up high, each
        objectExt(SO_BAT, 0, 16, 5, 1),     // in its own air territory - enemy
        objectExt(SO_BAT, 0, 27, 4, 2)      // sprites must never touch each other"""
new = """        objectExt(SO_BAT, 0, 5, 3, 0),      // two bats, each in its own air
        objectExt(SO_BAT, 0, 27, 4, 1)      // territory (sprites must not touch)"""
assert old in src
src = src.replace(old, new)
old = """path0:          .byte   16, 0, 4, 1, 4, -1, 4, -1, 4, 1    // left third, X 64-128
path1:          .byte   8, 1, 8, -1, 8, -1, 8, 1            // middle, X 152-216
path2:          .byte   12, 0, 3, -1, 3, 1, 3, 1, 3, -1     // right, X 240-288"""
new = """path0:          .byte   16, 0, 4, 1, 4, -1, 4, -1, 4, 1    // left third, X 64-128
path1:          .byte   12, 0, 3, -1, 3, 1, 3, 1, 3, -1     // right, X 240-288"""
assert old in src
src = src.replace(old, new)
src = src.replace("pathsPtrsLo:    .byte <path0, <path1, <path2", "pathsPtrsLo:    .byte <path0, <path1")
src = src.replace("pathsPtrsHi:    .byte >path0, >path1, >path2", "pathsPtrsHi:    .byte >path0, >path1")
src = src.replace("pathLengths:    .byte 10, 8, 10", "pathLengths:    .byte 10, 10")
os.makedirs("src/kickass/level/buddy", exist_ok=True)
open("src/kickass/level/buddy/data.asm", "w").write(src)
print("wrote src/kickass/level/buddy/data.asm")

# ------------------------------------------------------------- physics fork
phys = open("src/kickass/physics.asm").read()
assert phys.count("cmp #CLSN_LAST_ROW") == 3
phys = phys.replace("cmp #CLSN_LAST_ROW", "cmp #25 // tall room: scan all 25 rows")
open("src/kickass/physics-tall.asm", "w").write(phys)
print("wrote src/kickass/physics-tall.asm")

# ------------------------------------------------------------- game variant
subprocess.run(["python3", "tools/make_variant.py", "tony-buddy", "level/buddy"],
               check=True)
src = open("src/kickass/tony-buddy.asm").read()


def sub(old, new, count=1):
    global src
    assert src.count(old) == count, f"anchor not found ({count}x): {old[:60]!r}"
    src = src.replace(old, new)


# physics with 25-row collision scanning
sub('#import "physics.asm"', '#import "physics-tall.asm"')

# no boot menu: load straight into the chamber (the stock menu is invisible
# on ROM-less targets anyway); the cheat state still needs its explicit zero
sub("""    cli
    jsr cheatMenu
    jsr blankScreen""",
    """    cli
    lda #0
    sta gameCheatState
    jsr blankScreen""")
sub("""_menuBegin:
#import "cheatmenu.asm"
_menuEnd:

.assert "Cheatmenu cannot overlap with IO memory", _menuEnd < $D000, true


""", "")
sub('.print "Cheatmenu location $" + toHexString(_menuBegin) + " - $" + toHexString(_menuEnd - 1)\n', "")

# no dashboard: drop the raster split, let the playfield run all 25 rows;
# move the second IRQ below the lowest sprite lines (floor sprites end ~248)
sub("""    dashboardColor: c64lib_copperEntry(213, c64lib.IRQH_DASHBOARD_CUTOFF, SCHEME_CLASSIC_DARK, %00010100)
    c64lib_copperEntry(220, c64lib.IRQH_JSR, <doEachFrameVisual, >doEachFrameVisual)""",
    "    c64lib_copperEntry(255, c64lib.IRQH_JSR, <doEachFrameVisual, >doEachFrameVisual)")
sub("""    lda colorDarks, x
    sta fadeIn + 3
    sta fadeOut
    sta dashboardColor + 2
    jsr setColors""",
    """    lda colorDarks, x
    sta fadeIn + 3
    sta fadeOut
    jsr setColors""")

# ink dark on the former dashboard rows too (setColors bottom loop)
sub("""    ldx #0
    lda colorLights, y
    // sta c64lib.BG_COL_0
loop2:""",
    """    ldx #0
    lda colorDarks, y // tall room: rows 20-24 are playfield now
loop2:""")

# room decode/draw across all 25 rows
sub("""translateRoom: {
    ldx #0
    loop:
        .for (var i = 0; i <= 3; i++) """,
    """translateRoom: {
    ldx #0
    loop:
        .for (var i = 0; i <= 4; i++) """)
sub("chamberLines:               .lohifill 20, SCREEN_MEM_0 + 40*i",
    "chamberLines:               .lohifill 25, SCREEN_MEM_0 + 40*i")

# hostile collisions: bats only (sprites 3+4); the buddy on 5+6 is friendly
sub("""    lda actorCollisions
    beq !+
        // kill the enemy from the screen (only works for sprites)""",
    """    lda actorCollisions
    and #%00011000 // bats only - the buddy on sprites 5+6 is friendly
    beq !+
        // kill the enemy from the screen (only works for sprites)""")

# hooks: init with the level, update once per frame
sub("    jsr initPlayerPosition\n    jsr ani_init",
    "    jsr initPlayerPosition\n    jsr buddyInit\n    jsr ani_init")
sub("    jsr playEffects\n    jsr moveActors",
    "    jsr playEffects\n    jsr moveActors\n    jsr buddyUpdate")

# the top-of-frame interrupt repaints all sprite colors before the buddy's
# scanlines are rasterized - apply his green there
sub("""    lda eyesColor
    sta c64lib.SPRITE_7_COLOR

    c64lib_debugBorderEnd()
    jsr playMusic""",
    """    lda eyesColor
    sta c64lib.SPRITE_7_COLOR
    lda #BUDDY_COLOR
    sta c64lib.SPRITE_5_COLOR
    sta c64lib.SPRITE_6_COLOR

    c64lib_debugBorderEnd()
    jsr playMusic""")

# boot straight into the room without dashboard drawing or the eyes sprite
sub("""startRoomDirect: {
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
}""",
    """startRoomDirect: {
    jsr blankScreen
    lda #0
    sta gameTitleScreen
    sta joyAccumulator
    sta joyDelayCounter
    sta joyPreviousValue
    jsr showScreen
    rts
}""")

BUDDY = """// ---------------------------------------------------------------------
// Buddy Tony: a friendly green clone on sprites 5+6, wearing the player's
// own animation frames. Follows the player with a personal-space
// hysteresis, faces him, hops whenever the player leaves the ground, and
// idles with the real 6-phase breathing/look-around cycle.
.label BUDDY_COLOR    = GREEN
.label BUDDY_FLOOR_Y  = 206 // feet on the tall room's floor (row 23)
.label BUDDY_MIN_XLO  = 64  // inner face of the left pillar
.label BUDDY_MAX_XLO  = 24  // 280 = $0118: lo byte limit while hi = 1
.label BUDDY_STOP_AT  = 40  // rest when closer than this
.label BUDDY_GO_AT    = 52  // follow when farther than this
.label BUDDY_HOP_LEN  = 14
.label BUDDY_HOP_COOL = 20

buddyInit: {
    lda #120
    sta buddyX
    lda #0
    sta buddyX + 1
    sta buddyMoving
    sta buddyHop
    sta buddyCool
    sta buddyPhase
    sta buddyDelay
    lda #BUDDY_FLOOR_Y
    sta buddyY
    lda #1
    sta buddyFacing
    rts
}

buddyUpdate: {
    // keep the clone enabled and green (self-healing every frame)
    lda c64lib.SPRITE_ENABLE
    ora #%01100000
    sta c64lib.SPRITE_ENABLE
    lda #BUDDY_COLOR
    sta c64lib.SPRITE_5_COLOR
    sta c64lib.SPRITE_6_COLOR

    // signed 16-bit distance to the player -> mag + targetRight
    sec
    lda physPlayerX
    sbc buddyX
    sta mag
    lda physPlayerX + 1
    sbc buddyX + 1
    bpl playerRight
        ldy #0
        sty targetRight
        cmp #$ff
        bne farAway
        sec
        lda #0
        sbc mag
        sta mag
        jmp haveMag
    playerRight:
        ldy #1
        sty targetRight
        cmp #0
        beq haveMag
    farAway:
        lda #$ff
        sta mag
    haveMag:

    // hysteresis: walk when far, rest when close
    lda mag
    cmp #BUDDY_GO_AT
    bcc !+
        lda #1
        sta buddyMoving
    !:
    lda mag
    cmp #BUDDY_STOP_AT
    bcs !+
        lda #0
        sta buddyMoving
    !:

    // always turn towards the player
    lda targetRight
    sta buddyFacing

    // one pixel towards him, clamped to the space between the pillars
    lda buddyMoving
    beq noMove
        lda targetRight
        beq stepLeft
            inc buddyX
            bne !+
                inc buddyX + 1
            !:
            lda buddyX + 1
            beq noMove
            lda buddyX
            cmp #BUDDY_MAX_XLO
            bcc noMove
                lda #BUDDY_MAX_XLO
                sta buddyX
            jmp noMove
        stepLeft:
            lda buddyX
            bne !+
                dec buddyX + 1
            !:
            dec buddyX
            lda buddyX + 1
            bne noMove
            lda buddyX
            cmp #BUDDY_MIN_XLO
            bcs noMove
                lda #BUDDY_MIN_XLO
                sta buddyX
    noMove:

    // hop when the player leaves the ground
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
            sta buddyHop
    doHop:
        ldx buddyHop
        lda hopArc - 1, x
        clc
        adc buddyY
        sta buddyY
        inx
        stx buddyHop
        cpx #(BUDDY_HOP_LEN + 1)
        bne hopDone
            lda #0
            sta buddyHop
            lda #BUDDY_FLOOR_Y
            sta buddyY
            lda #BUDDY_HOP_COOL
            sta buddyCool
    hopDone:

    // write the hardware position
    lda buddyX
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
    sta c64lib.SPRITE_5_Y
    clc
    adc #21
    sta c64lib.SPRITE_6_Y

    // pose: hop / walk cycle / breathing idle, in the facing direction
    lda buddyHop
    beq notHopping
        lda buddyFacing
        beq !+
            lda jumpRightAnimationTL
            ldx jumpRightAnimationBL
            jmp setPose
        !:
        lda jumpLeftAnimationTL
        ldx jumpLeftAnimationBL
        jmp setPose
    notHopping:
    lda buddyMoving
    beq standing
        inc buddyDelay
        lda buddyDelay
        cmp #6
        bcc !+
            lda #0
            sta buddyDelay
            inc buddyPhase
        !:
        lda buddyPhase
        and #%00000011
        sta buddyPhase
        tax
        lda buddyFacing
        beq walkL
            lda walkRightAnimationTL, x
            pha
            lda walkRightAnimationBL, x
            tax
            pla
            jmp setPose
        walkL:
            lda walkLeftAnimationTL, x
            pha
            lda walkLeftAnimationBL, x
            tax
            pla
            jmp setPose
    standing:
        // the real idle: 6 phases at the player's own idle tempo
        inc buddyDelay
        lda buddyDelay
        cmp #15
        bcc idleShow
        lda #0
        sta buddyDelay
        inc buddyPhase
    idleShow:
        lda buddyPhase
        cmp #6
        bcc idleOk
        lda #0
        sta buddyPhase
    idleOk:
        ldx buddyPhase
        lda buddyFacing
        beq idleL
            lda idlingRightAnimationTL, x
            pha
            lda idlingRightAnimationBL, x
            tax
            pla
            jmp setPose
        idleL:
            lda idlingLeftAnimationTL, x
            pha
            lda idlingLeftAnimationBL, x
            tax
            pla
            jmp setPose
    setPose:
        sta SCREEN_MEM_0 + 1016 + 5
        stx SCREEN_MEM_0 + 1016 + 6
    rts

    // locals
    mag:         .byte 0
    targetRight: .byte 0
}

buddyX:       .word 120
buddyY:       .byte BUDDY_FLOOR_Y
buddyFacing:  .byte 1
buddyMoving:  .byte 0
buddyHop:     .byte 0
buddyCool:    .byte 0
buddyPhase:   .byte 0
buddyDelay:   .byte 0
hopArc:       .byte 253, 253, 254, 254, 255, 255, 0, 0, 1, 1, 2, 2, 3, 3

nextColorScheme: {"""
sub("nextColorScheme: {", BUDDY)

open("src/kickass/tony-buddy.asm", "w").write(src)
print("wrote src/kickass/tony-buddy.asm")
