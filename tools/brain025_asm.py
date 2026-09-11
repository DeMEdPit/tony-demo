#!/usr/bin/env python3
"""
brain025_asm.py - BRAIN02.5 on the machine, generated into the clone's body.

BRAIN02's blocks are reused verbatim wherever nothing changes; this module widens them from twenty
senses to twenty-seven and from sixty-four inputs to eighty, adds the terrain probe to the sense packer,
takes the follow rule off the blank brain, and moves the teaching toggle from a joystick chord to a key.

Nothing in tools/brain02_asm.py is edited: it is imported and its text is transformed here.
"""
import os
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
b02asm = _load("brain02_asm", os.path.join(ROOT, "tools/brain02_asm.py"))
ref = _load("brain025_ref", os.path.join(ROOT, "tools/brain025_ref.py"))

SC = ref.SENSE_COUNT            # 27 published nibbles
NV = 29 + len(ref.TERRAIN)      # 36 values: twenty senses, nine pseudo-senses, seven terrain
N = ref.N                       # 80 inputs
LESSON_SIZE = ref.LESSON_SIZE   # 15 bytes
LESSON_PAIRS = SC // 2          # 13 whole nibble pairs; the twenty-seventh nibble sits alone in byte 13

# ------------------------------------------------------------------------------- the terrain probe
TERRAIN_ASM = r"""
    // ------------------------------------------------------------- BRAIN02.5: the local terrain probe
    // Seven quantities (deliverables/brain025/DESIGN.md), packed at sensePack + 20 .. + 26, each 0..7 so
    // each is one unsigned nibble, measured in the toward frame: the direction h that the
    // reference-relative vocabulary already resolves, from this same block's own senses 1 and 3. Every
    // one of them is where something is, computed from the room and his pose; none says what to do.
    senseTerrain: {
        lda sensePack + 1               // the toward direction, resolved exactly as the retina resolves h
        beq byFacing
        cmp #8
        bcs towardLeft                  // nibbles 8..15 are negative: the reference is to the left
            lda #1
            bne haveU
        towardLeft:
            lda #$ff
            bne haveU
        byFacing:
            lda sensePack + 3           // level with him: his own facing decides
            beq facingLeft
                lda #1
                bne haveU
            facingLeft:
                lda #$ff
        haveU:
        sta tU
        bmi uLeft
            lda rightCol
            sta tCe
            lda leftCol
            sta tCa
            jmp haveEdges
        uLeft:
            lda leftCol
            sta tCe
            lda rightCol
            sta tCa
        haveEdges:
        lda top
        clc
        adc #3
        sta tRf                         // his foot row
        clc
        adc #1
        sta tRs                         // the row his feet rest on
        lda #0
        sta sensePack + 20
        sta sensePack + 21
        sta sensePack + 22
        sta sensePack + 23
        sta sensePack + 24
        sta sensePack + 25
        sta sensePack + 26

        // 20 tSafeRun: columns toward him with support at his own floor row, before the first without
        lda tCe
        sta tCol
        lda #0
        sta tN
        safeLoop:
            lda tN
            cmp #7
            beq safeFull
            jsr tNext
            ldx tCol
            lda tRs
            jsr tSolid
            beq safeStop                // tCol stands on the first unsupported column
            inc tN
            jmp safeLoop
        safeFull:
            lda #7
            sta sensePack + 20          // his floor reaches as far as he looks: no gap, no far side
            jmp obstacle
        safeStop:
        lda tN
        sta sensePack + 20
        clc
        adc #1
        sta tI                          // the index of that first unsupported column, 1..7
        // 21 tGapW: unsupported columns in a row, counted while the index stays inside seven
        lda #0
        sta tW
        gapLoop:
            inc tW                      // the column at tI has no support
            lda tI
            cmp #7
            beq gapEnd                  // one further would be the eighth: the rule stops here
            inc tI
            jsr tNext
            ldx tCol
            lda tRs
            jsr tSolid
            beq gapLoop
        // supported: tCol is the far side
        lda tW
        sta sensePack + 21
        // 22 tFarRun: how many supported columns in a row the far side offers, from this one on
        lda #0
        sta tN
        farLoop:
            inc tN
            lda tN
            cmp #7
            beq farEnd
            jsr tNext
            ldx tCol
            lda tRs
            jsr tSolid
            bne farLoop
        farEnd:
        lda tN
        sta sensePack + 22
        jmp obstacle
        gapEnd:
        lda tW
        sta sensePack + 21              // no far side within reach: its width stays zero

        // 23 tObstH and 24 tObstTop: the first column toward him blocked at his foot row
        obstacle:
        lda tCe
        sta tCol
        lda #0
        sta tN
        obstLoop:
            inc tN
            lda tN
            cmp #8
            beq head                    // nothing in his way within seven columns
            jsr tNext
            ldx tCol
            lda tRf
            jsr tSolid
            beq obstLoop
        lda tRf
        sta tRow
        lda #0
        sta tN
        stackLoop:
            lda tN
            cmp #7
            beq stackEnd
            ldx tCol
            lda tRow
            jsr tSolid
            beq stackEnd
            inc tN
            dec tRow
            jmp stackLoop
        stackEnd:
        lda tN
        sta sensePack + 23              // its height in rows above his floor line
        lda #0
        sta tN
        topLoop:
            lda tN
            cmp #7
            beq topEnd
            ldx tCol
            lda tRow
            jsr tSolid
            bne topEnd
            inc tN
            dec tRow
            jmp topLoop
        topEnd:
        lda tN
        sta sensePack + 24              // the clear rows above its top

        // 25 tHead: the clear rows above his own head, over both his columns
        head:
        lda top
        sec
        sbc #1
        sta tRow0
        ldx leftCol
        jsr tClearUp
        lda tN
        sta tW
        ldx rightCol
        jsr tClearUp
        lda tN
        cmp tW
        bcc !+
            lda tW
        !:
        sta sensePack + 25

        // 26 tBackRoom: the columns away from the reference that are clear at his foot row
        lda tCa
        sta tCol
        lda #0
        sta tN
        backLoop:
            lda tN
            cmp #7
            beq backEnd
            jsr tPrev
            ldx tCol
            lda tRf
            jsr tSolid
            bne backEnd
            inc tN
            jmp backLoop
        backEnd:
        lda tN
        sta sensePack + 26
        rts

        // IN: X a column, tRow0 the first row. OUT: tN the clear rows going up, capped at seven
        tClearUp: {
            lda tRow0
            sta tRow
            lda #0
            sta tN
            loop:
                lda tN
                cmp #7
                beq done
                lda tRow
                jsr tSolid
                bne done
                inc tN
                dec tRow
                jmp loop
            done:
            rts
        }
        tNext: {                        // tU is 1 or $ff, so one add walks either way
            lda tCol
            clc
            adc tU
            sta tCol
            rts
        }
        tPrev: {
            lda tCol
            sec
            sbc tU
            sta tCol
            rts
        }
        tU:    .byte 0
        tCe:   .byte 0
        tCa:   .byte 0
        tRf:   .byte 0
        tRs:   .byte 0
        tCol:  .byte 0
        tRow:  .byte 0
        tRow0: .byte 0
        tN:    .byte 0
        tW:    .byte 0
        tI:    .byte 0
    }
    // IN: X a column (signed), A a row. OUT: A 1 when the cell carries wall, 0 when it does not; the
    // flags follow A. Off the sides and below the floor reads as wall, above the ceiling as open, which
    // is the same rule the offline model uses. X is kept; A and Y are not.
    tSolid: {
        sta tsRow
        txa
        bmi wall                        // left of the screen
        cmp #40
        bcs wall                        // right of it
        lda tsRow
        bmi open                        // above it
        cmp #25
        bcs wall                        // below it
        tay
        lda chamberLines.lo, y
        sta rd + 1
        lda chamberLines.hi, y
        sta rd + 2
        rd: lda $ffff, x
        tay
        lda roomMaterialsBuffer, y
        and #BG_CLSN_WALL
        beq open
        wall:
            lda #1
            rts
        open:
            lda #0
            rts
        tsRow: .byte 0
    }
"""

# ------------------------------------------------------------------- the keyboard teaching toggle
TEACHKEY_ASM = r"""
// BRAIN02.5: the teaching toggle is a key of its own. The joystick keeps every verb it had: down with
// fire still lays a brick, up with fire is still the step up, and no chord means anything new. T is row
// 2 of the keyboard matrix, column bit 6. The scan drives port A for one row and reads port B for the
// columns, with the interrupt flag saved and restored around it and the port left as io_scanJoy expects
// to find it, so the game's own joystick read never looks at a driven line. Port B is left alone, which
// is why a pressed key cannot appear as a joystick direction on port A.
teachKey: {
    php
    sei
    lda #$ff
    sta c64lib.CIA1_DATA_DIR_A          // the rows as outputs
    lda #%11111011                      // row 2 low, every other row high
    sta c64lib.CIA1_DATA_PORT_A
    lda c64lib.CIA1_DATA_PORT_B
    and #%01000000                      // column bit 6: T. A low line is a pressed key
    tax
    lda #$ff
    sta c64lib.CIA1_DATA_PORT_A
    lda #0
    sta c64lib.CIA1_DATA_DIR_A          // back to inputs, as io_scanJoy leaves them
    plp
    txa
    bne released
        lda teachKeyWas                 // held: the toggle acts on the press, once
        bne done
        lda #1
        sta teachKeyWas
        inc teachKeyEdges
        lda teachMode                   // the mode, and nothing else: never a gameplay action,
        eor #1                          // never a lesson, and nothing in flight survives the change
        sta teachMode
        lda #0
        sta brainAction
        sta macroStep
        sta cloneJoy
        sta cloneJoyOverride
        sta teachHold
        rts
    released:
    lda #0
    sta teachKeyWas
    done:
    rts
}
teachKeyWas:   .byte 0                  // the key's state last frame, for the edge
teachKeyEdges: .byte 0                  // how many times it has toggled, for the tests
"""

# ------------------------------------------------------------------------------ the block transforms
def _slot_asm(vocab):
    s = b02asm.BRAIN02_SLOT_ASM
    s = s.replace('brainMarker:    .text "BRAIN02"\n                .byte 0\n', 'brainMarker:    .text "BRAIN025"\n')
    s = s.replace("brainLayout:    .byte 2                 // +9   byte weights over a retina table, ten outputs",
                  "brainLayout:    .byte 3                 // +9   BRAIN02.5: byte weights over a retina table with terrain, ten outputs")
    s = s.replace("brainIn:        .fill 20, 0             // the think's copy of the senses (nibbles)",
                  f"brainIn:        .fill {SC}, 0             // the think's copy of the published block (nibbles): twenty senses then seven terrain")
    s = s.replace("brainVals:      .fill 29, 0             // the twenty sign-extended, then the nine pseudo-senses (indices 20..28)",
                  f"brainVals:      .fill {NV}, 0             // twenty sign-extended, nine pseudo-senses (20..28), seven terrain (29..35)")
    s = s.replace("brainTestIn:    .fill 20, 0", f"brainTestIn:    .fill {SC}, 0")
    old = "    sta brainVals + 28\n    // the table\n"
    assert s.count(old) == 1, "the retina's adx store moved"
    s = s.replace(old, "    sta brainVals + 28\n"
                       f"    ldx #{len(ref.TERRAIN) - 1}                          // BRAIN02.5: the seven terrain nibbles of the block, values 29..35\n"
                       "    !:\n        lda brainIn + 20, x\n        and #$0f\n        sta brainVals + 29, x\n        dex\n    bpl !-\n"
                       "    // the table\n")
    s = s.replace(".label B02_N = {{N}}", f".label B02_N = {{{{N}}}}\n.label B02_SENSES = {SC}\n.label B02_TERRAIN = {len(ref.TERRAIN)}")
    entries = ref.table_T1()
    ops = ", ".join(str(op) for op, a, k in entries); as_ = ", ".join(str(a) for op, a, k in entries); ks = ", ".join(f"${k & 255:02x}" for op, a, k in entries)
    return (s.replace("{{N}}", str(N)).replace("{{RETINA}}", str(ref.RETINA_ID)).replace("{{VOCAB}}", "1" if vocab == "rel" else "0")
             .replace("{{OPS}}", ops).replace("{{AS}}", as_).replace("{{KS}}", ks))

def _think_asm():
    s = b02asm.BRAIN02_THINK_ASM
    s = s.replace("        .for (var i = 0; i < 20; i++) {\n            lda brainTestIn + i\n            sta brainIn + i\n        }",
                  f"        ldx #{SC - 1}                          // BRAIN02.5: a loop, not an unrolled copy: twenty-seven would push the branch out of range\n"
                  "        !:\n            lda brainTestIn, x\n            sta brainIn, x\n            dex\n        bpl !-")
    s = s.replace("    lda brainLayout\n    cmp #2\n    bne bad", "    lda brainLayout\n    cmp #3\n    bne bad")
    s = s.replace('    markerText: .text "BRAIN02"\n                .byte 0\n', '    markerText: .text "BRAIN025"\n')
    return s

def _teach_vars_asm(shadow, lesson, cap):
    s = b02asm.BRAIN02_TEACH_VARS_ASM
    s = s.replace("// the LESSON2 ring, in the memory the level tune vacates once it is copied",
                  "// the LESSON25 ring, in the memory the level tune vacates once it is copied")
    s = s.replace("                                     // to $A000 (unpack): 32 + 11 * 300 = 3,332 bytes, to $9e03",
                  f"                                     // to $A000 (unpack): 32 + {LESSON_SIZE} * {cap} = {32 + LESSON_SIZE * cap} bytes")
    s = s.replace(".label LESSON_SIZE = 11", f".label LESSON_SIZE = {LESSON_SIZE}")
    s = s.replace(".label LESSON_CAP = 300", f".label LESSON_CAP = {cap}")
    s = s.replace('.label lessonMarker    = LESSON_BLOCK           // "LESSON2", 0',
                  '.label lessonMarker    = LESSON_BLOCK           // "LESSON25"')
    s = s.replace(".label lessonSize      = LESSON_BLOCK + 14      // 11", f".label lessonSize      = LESSON_BLOCK + 14      // {LESSON_SIZE}")
    s = s.replace(".label lessonData      = LESSON_BLOCK + 32      // 11 bytes per lesson; sequence s at slot s mod 300",
                  f".label lessonData      = LESSON_BLOCK + 32      // {LESSON_SIZE} bytes per lesson; sequence s at slot s mod {cap}")
    s = s.replace("teachHold:   .byte 0                 // frames the chord has been held; 255 once it toggled, until released",
                  "teachHold:   .byte 0                 // BRAIN02.5: no chord, so this stays zero; the checks that read it are left alone")
    s = s.replace("lessonWriteSlot: .word 0             // the slot of the next lesson, 0..299", f"lessonWriteSlot: .word 0             // the slot of the next lesson, 0..{cap - 1}")
    return s.replace("{{SHADOW}}", shadow).replace("{{LESSON}}", lesson) + TEACHKEY_ASM

def _lesson_init_asm():
    return b02asm.BRAIN02_LESSON_INIT_ASM.replace('    lessonText: .text "LESSON2"\n                .byte 0\n', '    lessonText: .text "LESSON25"\n')

def _teach_lesson_asm():
    s = b02asm.BRAIN02_TEACH_LESSON_ASM
    s = s.replace("    lda lessonWritePtr                  // the record: the twenty nibbles packed, then taught | predicted << 4\n    sta wr + 1\n    sta wr2 + 1\n    lda lessonWritePtr + 1\n    sta wr + 2\n    sta wr2 + 2\n",
                  f"    lda lessonWritePtr                  // the record: the {SC} nibbles packed, then taught | predicted << 4\n"
                  "    sta wr + 1\n    sta wr2 + 1\n    sta wr3 + 1\n    lda lessonWritePtr + 1\n    sta wr + 2\n    sta wr2 + 2\n    sta wr3 + 2\n")
    old = "        cpx #20\n    bne pack\n    lda brainPredicted\n"
    assert s.count(old) == 1
    s = s.replace(old, f"        cpx #{LESSON_PAIRS * 2}\n    bne pack\n"
                       f"    lda brainIn + {LESSON_PAIRS * 2}                    // BRAIN02.5: the last nibble has no partner; its byte's high half stays zero\n"
                       "    and #$0f\n    wr3: sta $ffff, y\n    jsr addSum\n    iny\n"
                       "    lda brainPredicted\n")
    return s

# -------------------------------------------------------------------------------------- the body
def _span(src, start, end_marker, include_end=True):
    i = src.index(start); j = src.index(end_marker, i) + (len(end_marker) if include_end else 0)
    return i, j

def brain025_apply(src, vocab="rel", shadow="$9200", lesson="$9540", cap=180, spawn_x=72):
    """BRAIN02's substitutions at eighty inputs, then what BRAIN02.5 adds"""
    def rep(start, end_marker, new, include_end=True):
        nonlocal src
        i, j = _span(src, start, end_marker, include_end); src = src[:i] + new + src[j:]
    def sub1(old, new):
        nonlocal src
        assert src.count(old) == 1, f"expected one occurrence of: {old[:70]!r}"
        src = src.replace(old, new)

    # --- the sense block grows from twenty nibbles to twenty-seven
    sub1(".label SENSE_COUNT = 20", f".label SENSE_COUNT = {SC}            // BRAIN02.5: twenty senses and seven terrain quantities")
    sub1("    .for (var i = 0; i < 20; i++) {\n        lda sensePack + i\n        sta cloneSenses + i\n    }",
         f"    .for (var i = 0; i < {SC}; i++) {{\n        lda sensePack + i\n        sta cloneSenses + i\n    }}")
    sub1("    sei\n    .for (var i = 0; i < 20; i++) {\n        lda cloneSenses + i\n        sta brainIn + i\n    }",
         f"    sei\n    .for (var i = 0; i < {SC}; i++) {{\n        lda cloneSenses + i\n        sta brainIn + i\n    }}")
    # --- the probe itself, inside senseCompute where top, leftCol and rightCol live
    sub1("    stillDone:\n    stx sensePack + 17\n    rts\n", "    stillDone:\n    stx sensePack + 17\n    jsr senseTerrain            // BRAIN02.5: the seven terrain quantities, at sensePack + 20..26\n    rts\n")
    sub1("    d:        .word 0\n    neg:      .byte 0\n", TERRAIN_ASM + "    d:        .word 0\n    neg:      .byte 0\n")

    # --- a blank Tony is blank: no follow rule behind the brain
    sub1("cloneThink: {\n    lda brainKindNow                    // the effective kind, checked in the main loop\n    beq cloneFollow\n    jmp cloneDecode\n}",
         "cloneThink: {\n"
         "    lda brainKindNow                    // BRAIN02.5: there is no fallback rule. A brain that has not\n"
         "    bne !+                              // been taught anything does nothing, by the forward pass's own\n"
         "        lda #0                          // tie: every accumulator equal, the first largest wins, IDLE.\n"
         "        sta cloneJoy                    // (cloneFollow below is left in the image and never reached.)\n"
         "        rts\n"
         "    !:\n    jmp cloneDecode\n}")

    # --- the canonical study spawn, in the lower left, clear of the ladder
    sub1("    lda #120\n    sta cloneX\n    sta cloneNextX\n", f"    lda #{spawn_x}                          // BRAIN02.5: the study spawn, columns {(spawn_x >> 3) - 2}-{((spawn_x + 8) >> 3) - 2}, by the far left pillar\n    sta cloneX\n    sta cloneNextX\n")

    # --- the teaching toggle leaves the joystick alone: the chord is gone, the key does it
    i = src.index("    // the chord: down with fire held TEACH_HOLD_FRAMES frames toggles teaching, once per hold, and takes")
    j = src.index("    notHeld:\n    lda #0\n    sta teachHold\n    route:\n")
    src = src[:i] + ("    // BRAIN02.5: no chord. Down with fire is the lay verb and nothing else; the teaching mode is\n"
                     "    // toggled by the T key (teachKey, in the main loop) or by the workbench writing teachMode.\n"
                     "    lda #0\n    sta teachHold\n    route:\n") + src[j + len("    notHeld:\n    lda #0\n    sta teachHold\n    route:\n"):]
    sub1("        jsr bodySensePack           // the body: the clone's senses, packed from the last frame's raw values\n",
         "        jsr teachKey                // BRAIN02.5: the teaching toggle, its own key\n        jsr bodySensePack           // the body: the clone's senses, packed from the last frame's raw values\n")

    # --- BRAIN02's own substitutions, at the wider shapes
    rep('.align 256\nbrainMarker:    .text "BRAIN01"', "brainMul:       .fill 256, ((((i >> 4) >= 8) ? (i >> 4) - 16 : (i >> 4)) * (((i & 15) >= 8) ? (i & 15) - 16 : (i & 15))) & 255\n", _slot_asm(vocab))
    rep("bodyThink: {\n", '    markerText: .text "BRAIN01"\n                .byte 0\n}\n', _think_asm())
    rep("// ===================================================================== learning\n", "        byte:   .byte 0\n        nib:    .byte 0\n    }\n}\n", b02asm.BRAIN02_LEARN_ASM)
    rep(".label LESSON_BLOCK = $8a00", "lessonPtr:   .word 0                 // where the next lesson goes\n", _teach_vars_asm(shadow, lesson, cap))
    rep("lessonInit: {\n", '    lessonText: .text "LESSON1"\n                .byte 0\n}\n', _lesson_init_asm())
    # (BRAIN02's two chord-driven shadow substitutions have nothing to patch here: the chord is gone.
    #  The atomic snapshot and restore stay exactly as BRAIN02 built them, driven by shadowRequest and
    #  shadowRestoreRequest, which the main loop honours before any lesson and the workbench can set.)
    rep("teachShadowSave: {\n", "    lda shadowPtr + 1\n    sta lessonPtr + 1\n    rts\n}\n", b02asm.BRAIN02_SHADOW_ASM)
    rep("teachLesson: {\n", "    pair:    .byte 0\n    wr2byte: .byte 0\n    nextLo:  .byte 0\n}\n", _teach_lesson_asm())
    sub1("    lda bodyFrames\n    sta rawFrame\n    lda bodyFrames + 1\n    sta rawFrame + 1\n    lda sensePacked\n    bne !+\n        rts\n    !:\n",
         "    lda bodyFrames\n    sta rawFrame\n    lda bodyFrames + 1\n    sta rawFrame + 1\n"
         "    lda bodyFrames                  // this frame's joystick byte and state, by frame, for the lesson pairing\n    and #7\n    tax\n"
         "    lda rawJoy\n    sta joyRing, x\n    lda rawState\n    sta stateRing, x\n    lda bodyFrames\n    sta frameRing, x\n"
         "    lda sensePacked\n    bne !+\n        rts\n    !:\n")
    sub1("cloneDecode: {\n    lda macroStep\n    bne macro\n",
         "cloneDecode: {\n    lda shadowRestoreRequest            // a restore pending: nothing until the next think decides with the restored weights\n    beq !+\n        lda #0\n        sta macroStep\n        jmp emit\n    !:\n    lda macroStep\n    bne macro\n")
    sub1("    lda muralColour                 // the clone's colour: the parameter block's, white for a lesson's flash\n    ldx cloneFlash\n    beq !+\n        dec cloneFlash\n        lda #1\n    !:\n",
         "    lda muralColour                 // the clone's colour: the parameter block's; a lesson's flash white, a refused one red\n    ldx cloneFlash\n    beq !+\n        dec cloneFlash\n        lda cloneFlashColour\n    !:\n")
    return src
