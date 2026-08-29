#!/usr/bin/env python3
"""Generate the "Buddy" variant: the Colonnade plus a green follower Tony.

Produces:
  src/kickass/level/buddy/data.asm  - pillar room, two bats (sprites 3+4;
                                      sprites 5+6 belong to the buddy)
  src/kickass/tony-buddy.asm        - one-room variant with the buddy AI:
      * buddy = enemy-slot sprites 5+6 wearing Tony's animation frames,
        colored green every frame (independent of the color scheme)
      * follows the player with a personal-space hysteresis, faces him,
        and does a canned hop whenever the player leaves the ground
      * enemy collision check masked to the bats only, so touching the
        buddy is harmless (the engine reads any enemy sprite-sprite
        contact as a player hit)

Run from repo root: python3 tools/make_buddy.py
"""

import os
import subprocess

# ---------------------------------------------------------------- level data
src = open("src/kickass/level/pillars/data.asm").read()
src = src.replace(
    '// "The Colonnade" - an empty sealed chamber: floor, ceiling, two big\n'
    '// pillars for walls, and bats high above. Map: tools/build_pillar_room.py.',
    '// "The Colonnade + Buddy" - the empty pillar chamber with two bats up\n'
    '// high (sprites 3+4). Sprites 5+6 are taken by the green buddy Tony,\n'
    '// which is engine code in tony-buddy.asm, not a level object.')
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

# ------------------------------------------------------------- game variant
subprocess.run(["python3", "tools/make_variant.py", "tony-buddy", "level/buddy"],
               check=True)
src = open("src/kickass/tony-buddy.asm").read()

# hostile collisions: bats only (sprites 3+4); the buddy on 5+6 is friendly
old = """    lda actorCollisions
    beq !+
        // kill the enemy from the screen (only works for sprites)"""
new = """    lda actorCollisions
    and #%00011000 // bats only - the buddy on sprites 5+6 is friendly
    beq !+
        // kill the enemy from the screen (only works for sprites)"""
assert src.count(old) == 1
src = src.replace(old, new)

# hooks: init with the level, update once per frame
old = "    jsr initPlayerPosition\n    jsr ani_init"
assert src.count(old) == 1
src = src.replace(old, "    jsr initPlayerPosition\n    jsr buddyInit\n    jsr ani_init")
old = "    jsr playEffects\n    jsr moveActors"
assert src.count(old) == 1
src = src.replace(old, "    jsr playEffects\n    jsr moveActors\n    jsr buddyUpdate")

# the top-of-frame interrupt repaints all sprite colors before the buddy's
# scanlines are rasterized - re-apply green there, or he shows up grey
old = """    lda eyesColor
    sta c64lib.SPRITE_7_COLOR

    c64lib_debugBorderEnd()
    jsr playMusic"""
assert src.count(old) == 1
src = src.replace(old, """    lda eyesColor
    sta c64lib.SPRITE_7_COLOR
    lda #BUDDY_COLOR
    sta c64lib.SPRITE_5_COLOR
    sta c64lib.SPRITE_6_COLOR

    c64lib_debugBorderEnd()
    jsr playMusic""")

BUDDY = """// ---------------------------------------------------------------------
// Buddy Tony: a friendly green clone on sprites 5+6, wearing the player's
// own animation frames. Follows the player with a personal-space
// hysteresis, faces him, and hops whenever the player leaves the ground.
.label BUDDY_COLOR    = GREEN
.label BUDDY_FLOOR_Y  = 166
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

    // pose: hop / walk cycle / idle, in the facing direction
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
        lda buddyFacing
        beq !+
            lda idlingRightAnimationTL
            ldx idlingRightAnimationBL
            jmp setPose
        !:
        lda idlingLeftAnimationTL
        ldx idlingLeftAnimationBL
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
assert src.count("nextColorScheme: {") == 1
src = src.replace("nextColorScheme: {", BUDDY)

open("src/kickass/tony-buddy.asm", "w").write(src)
print("wrote src/kickass/tony-buddy.asm")
