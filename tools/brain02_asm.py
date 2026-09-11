# brain02_asm.py - the BRAIN02 machine code (deliverables/bakeoff/PREREG-PHASE3.md), spliced into the body's
# assembly by make_chamber.py --brain02 RETINA --vocab rel|abs. Exec'd by the generator; brain02_apply(src,
# retina_name, vocab) returns the source with the BRAIN01 blocks replaced. The reference is
# tools/brain02_ref.py; the tables are generated from it so the bytes cannot drift.
import importlib.util as _ilu, os as _os
_s = _ilu.spec_from_file_location("brain02_ref", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "brain02_ref.py"))
brain02_ref = _ilu.module_from_spec(_s); _s.loader.exec_module(brain02_ref)

BRAIN02_NAMES = {"R0": 1, "R1b": 2, "R0s": 3, "R1s": 4, "p128": 0}

BRAIN02_SLOT_ASM = r"""
// ===================================================================== BRAIN02 (PREREG-PHASE3.md)
// The research brain: byte weights over a published retina table of B02_N flags, the symmetric rule at
// the byte box, the reference-relative vocabulary resolved once per think from the block's own reference
// vector, the LESSON2 ring with a validated drain, the atomic teaching shadow, and the machine's own
// cycle counts (CIA 2 timer A, unused by the game).
.label B02_N = {{N}}
.label B02_RETINA = {{RETINA}}
.label B02_VOCAB = {{VOCAB}}
.label B02_WEIGHT_BYTES = 10 * B02_N
.align 256
brainMarker:    .text "BRAIN02"
                .byte 0
brainHeader:
brainKind:      .byte 0                 // +8
brainLayout:    .byte 2                 // +9   byte weights over a retina table, ten outputs
brainInputCount: .byte B02_N            // +10  must equal the program's retina
brainHiddenCount: .byte 0               // +11
brainOutputCount: .byte 10              // +12
brainPeriod:    .byte 4                 // +13  frames between thinks
brainLineage:   .byte 0                 // +14  lineage bits, the contract's
brainRule:      .byte 2                 // +15  the symmetric rule, clamp -128..127
brainVocab:     .byte B02_VOCAB         // +16  0 absolute, 1 reference-relative
brainRetinaId:  .byte B02_RETINA        // +17  must equal the program's retina
brainEducation: .word 0                 // +18  lessons applied to these weights over their life (provenance)
                .fill 4, 0              // +20  reserved
brainWeights:   .fill B02_WEIGHT_BYTES, 0   // +24  row o at o * B02_N, one signed byte per flag
brainMood:      .fill 10, 0             // +24 + 10 N  one signed byte per output, added directly; zero in Phase 3
.label BRAIN_BLOCK_SIZE = * - brainMarker

// the live state (not stamped)
brainAction:    .byte 0                 // the absolute action the decoder reads every frame (resolved at the think)
brainOutput:    .byte 0                 // the raw output index of the last think (relative under vocabulary 1)
brainH:         .byte 0                 // 1: the reference is to the right, or level and he faces right
brainGap:       .word 0                 // the last think's score gap: the winner's accumulator minus the runner-up's
brainThinkFrame: .byte 0
brainThinks:    .word 0
brainIn:        .fill 20, 0             // the think's copy of the senses (nibbles)
brainVals:      .fill 29, 0             // the twenty sign-extended, then the nine pseudo-senses (indices 20..28)
brainFlags:     .fill B02_N, 0          // the flag vector, 0/1
brainActive:    .fill B02_N, 0          // the indices of the set flags
brainActiveCount: .byte 0
brainAcc:       .fill 20, 0             // the ten accumulators, low byte then high
brainTestRun:   .byte 0                 // 1: run the retina (mode 0) and the forward pass on the test inputs
brainTestMode:  .byte 0                 // 0: brainTestIn through the retina; 1: brainTestFlags as the flag vector, h left
brainTestIn:    .fill 20, 0
brainTestFlags: .fill B02_N, 0
brainTestAcc:   .fill 20, 0
brainTestOutput: .byte 0
brainTestAction: .byte 0
brainTestH:     .byte 0
// the retina table: the count, then the op, the operand a and k (or b) of every flag, three arrays
retinaTable:
retinaCount:    .byte B02_N
retinaOp:       .byte {{OPS}}
retinaA:        .byte {{AS}}
retinaK:        .byte {{KS}}
sextTab:        .byte 0, 1, 2, 3, 4, 5, 6, 7, $f8, $f9, $fa, $fb, $fc, $fd, $fe, $ff
lastDirTab:     .byte 0, $ff, 1, 0, 0, 0, $ff, 1, $ff, 1, 0, 0, 0, 0, 0, 0     // the action's horizontal direction
absTabR:        .byte 0, 2, 1, 3, 4, 5, 7, 6, 9, 8     // relative -> absolute when h is right (the identity when left)
relTabR:        .byte 0, 2, 1, 3, 4, 5, 7, 6, 9, 8     // absolute -> relative when h is right (the identity when left)
// the machine's cycle counts: CIA 2 timer A free-running; latest and maximum per kind
.label PROF_THINK = 0
.label PROF_LESSON = 4
.label PROF_SHADOW = 8
.label PROF_DRAIN = 12
.label PROF_THINK_PURE = 16
.label PROF_LESSON_PURE = 20
profTable:
profThink:      .word 0
profThinkMax:   .word 0
profLesson:     .word 0
profLessonMax:  .word 0
profShadow:     .word 0
profShadowMax:  .word 0
profDrain:      .word 0
profDrainMax:   .word 0
profThinkPure:  .word 0                 // the hooks' think and lesson with the interrupts held off: the work itself
profThinkPureMax: .word 0
profLessonPure: .word 0
profLessonPureMax: .word 0
profStart:      .word 0
profTmp:        .word 0
gapMin:         .word $7fff
gapMax:         .word 0
gapSum:         .fill 4, 0
gapCount:       .word 0
profInit: {
    lda #$ff
    sta $dd04
    sta $dd05
    lda #%00010001                  // start, force load, continuous
    sta $dd0e
    rts
}
profRead: {                         // -> profTmp, consistent across the two bytes
    !:
    lda $dd05
    sta profTmp + 1
    lda $dd04
    sta profTmp
    lda $dd05
    cmp profTmp + 1
    bne !-
    rts
}
profBegin: {
    jsr profRead
    lda profTmp
    sta profStart
    lda profTmp + 1
    sta profStart + 1
    rts
}
// IN: X - the offset in profTable (latest word, then the maximum word)
profEnd: {
    jsr profRead
    sec                             // the timer counts down: elapsed = start - now
    lda profStart
    sbc profTmp
    sta profTable, x
    lda profStart + 1
    sbc profTmp + 1
    sta profTable + 1, x
    cmp profTable + 3, x
    bcc done
    bne set
    lda profTable, x
    cmp profTable + 2, x
    bcc done
    set:
    lda profTable, x
    sta profTable + 2, x
    lda profTable + 1, x
    sta profTable + 3, x
    done:
    rts
}

// brainIn (twenty nibbles) -> brainVals (sign-extended, then the pseudo-senses), brainH, then the table ->
// brainFlags, brainActive, brainActiveCount
brainRetina: {
    ldx #19
    !:
        lda brainIn, x
        and #$0f
        tay
        lda sextTab, y
        sta brainVals, x
        dex
    bpl !-
    lda brainVals + 1               // 20 hRight: refDx > 0, or refDx == 0 and facing right
    bmi hLeft
    bne hRight
    lda brainVals + 3
    beq hLeft
    hRight:
        lda #1
        bne haveH
    hLeft:
        lda #0
    haveH:
    sta brainVals + 20
    sta brainH
    lda #1
    ldx brainH
    bne !+
        lda #$ff
    !:
    sta hSign
    lda #0                          // 21, 22: the last action's direction against h
    sta brainVals + 21
    sta brainVals + 22
    lda brainIn + 16
    and #$0f
    tax
    lda lastDirTab, x
    beq noDir
    cmp hSign
    bne away
        inc brainVals + 21
        jmp noDir
    away:
        inc brainVals + 22
    noDir:
    lda #0                          // 23 refAbove: refDy > 0
    sta brainVals + 23
    lda brainVals + 2
    beq !+
    bmi !+
        inc brainVals + 23
    !:
    lda brainVals + 3               // 24 facingRef: (facingRight != 0) == hRight
    beq !+
        lda #1
    !:
    cmp brainH
    bne notFacing
        lda #1
        bne haveFacing
    notFacing:
        lda #0
    haveFacing:
    sta brainVals + 24
    lda #0                          // 25 stepAhead, 26 wallAhead, 27 buildableAndClear
    sta brainVals + 25
    sta brainVals + 26
    sta brainVals + 27
    lda brainVals + 9
    beq noFoot
        lda brainVals + 10
        bne wall
            inc brainVals + 25
            jmp haveStep
        wall:
            inc brainVals + 26
            jmp haveStep
    noFoot:
        lda brainVals + 14
        beq haveStep
            inc brainVals + 27
    haveStep:
    lda brainVals + 1               // 28 adx
    bpl !+
        eor #$ff
        clc
        adc #1
    !:
    sta brainVals + 28
    // the table
    lda #0
    sta brainActiveCount
    ldx #0
    entry:
        lda retinaA, x
        tay
        lda brainVals, y
        sta va
        lda retinaK, x
        sta kb
        lda retinaOp, x
        bne notGE
            lda va                  // GE: va - k >= 0, signed
            sec
            sbc kb
            bvc !+
                eor #$80
            !:
            bpl set
            jmp clear
        notGE:
        cmp #1
        bne notLE
            lda kb                  // LE: k - va >= 0, signed
            sec
            sbc va
            bvc !+
                eor #$80
            !:
            bpl set
            jmp clear
        notLE:
        cmp #2
        bne twoOperand
            lda va                  // EQN: the raw nibble equals k
            and #$0f
            cmp kb
            beq set
            jmp clear
        twoOperand:
            ldy kb
            lda brainVals, y
            beq qZero
                lda #1
            qZero:
            sta qb
            lda va
            beq pZero
                lda #1
            pZero:
            sta pb
            lda retinaOp, x
            cmp #3
            bne notAnd
                lda pb              // AND
                and qb
                jmp result
            notAnd:
            cmp #4
            bne notAndNot
                lda qb              // ANDNOT
                eor #1
                and pb
                jmp result
            notAndNot:
            cmp #5
            bne xnor
                lda pb              // OR
                ora qb
                jmp result
            xnor:
                lda pb              // XNOR
                eor qb
                eor #1
            result:
            bne set
        clear:
            lda #0
            sta brainFlags, x
            jmp next
        set:
            lda #1
            sta brainFlags, x
            txa
            ldy brainActiveCount
            sta brainActive, y
            inc brainActiveCount
        next:
        inx
        cpx retinaCount
        beq done
        jmp entry
    done:
    rts
    va:    .byte 0
    kb:    .byte 0
    pb:    .byte 0
    qb:    .byte 0
    hSign: .byte 0
}
"""

BRAIN02_THINK_ASM = r"""
bodyThink: {
    jsr brainCheck                      // the slot as it is now -> brainKindNow (0 when malformed)
    lda shadowRestoreRequest            // the teaching shadow: a restore, then a snapshot, before any lesson
    beq !+
        jsr profBegin
        jsr teachShadowRestore
        ldx #PROF_SHADOW
        jsr profEnd
        lda #0
        sta shadowRestoreRequest
        sta shadowRequest
    !:
    lda shadowRequest
    beq !+
        jsr profBegin
        jsr teachShadowSave
        ldx #PROF_SHADOW
        jsr profEnd
        lda #0
        sta shadowRequest
    !:
    lda lessonAckRequest                // the drain handshake, before any lesson
    beq !+
        jsr profBegin
        jsr lessonAck
        ldx #PROF_DRAIN
        jsr profEnd
    !:
    lda brainLearnRun
    bne learnTest
    jmp noLearnTest
    learnTest:
        jsr testInputs
        lda brainTestMode
        sta learnRaw
        lda brainLearnTestT
        sta brainTaught
        lda brainAction
        pha
        sei
        jsr profBegin
        jsr brainLearn
        ldx #PROF_LESSON_PURE
        jsr profEnd
        cli
        lda #0
        sta learnRaw
        lda brainPredicted
        sta brainLearnTestP
        lda brainLearned
        sta brainLearnTestTook
        lda brainTaughtRaw
        sta brainLearnTestTrel
        pla
        sta brainAction
        lda #0
        sta brainLearnRun
    noLearnTest:
    lda brainTestRun
    bne test
    jmp noTest
    test:
        jsr testInputs
        lda brainAction
        pha
        sei
        jsr profBegin
        lda brainTestMode
        bne !+
            jsr brainRetina
        !:
        jsr brainForward
        ldx #PROF_THINK_PURE
        jsr profEnd
        cli
        ldx #19
        !:
            lda brainAcc, x
            sta brainTestAcc, x
            dex
        bpl !-
        ldx #0
        !:
            lda brainFlags, x
            sta brainTestFlags, x
            inx
            cpx #B02_N
            bne !-
        lda brainOutput
        sta brainTestOutput
        lda brainAction
        sta brainTestAction
        lda brainH
        sta brainTestH
        pla
        sta brainAction
        lda #0
        sta brainTestRun
    noTest:
    // the edge: when the action applied this frame differs from the last frame's (a press or a release),
    // teaching takes a lesson now, whatever the period
    lda #0
    sta lessonEdge
    lda sensePackFrame                  // a fresh pack this frame?
    cmp packSeenFrame
    bne fresh
    lda sensePackFrame + 1
    cmp packSeenFrame + 1
    beq period
    fresh:
    lda sensePackFrame
    sta packSeenFrame
    lda sensePackFrame + 1
    sta packSeenFrame + 1
    lda sensePack + 16
    cmp packLastAction
    sta packLastAction
    beq period
    lda teachMode
    beq period
    lda teachHold                       // not from a spent chord: the stick is dead until let go
    cmp #255
    beq period
    lda brainKindNow
    cmp #2                              // the builder is not taught
    beq period
        jsr teachInputs
        jsr teachLesson
        jsr brainCheck
        lda #1
        sta lessonEdge
    period:
    lda bodyFrames
    sec
    sbc brainThinkFrame
    cmp brainPeriod
    bcs !+
        rts                             // not yet
    !:
    lda bodyFrames
    sta brainThinkFrame
    jsr teachInputs                     // the published senses, whole
    lda teachMode                       // teaching: the lesson first, kind 0 or 1 (the builder is not taught)
    beq !+
        lda lessonEdge                  // unless the edge took it this frame
        bne !+
        lda teachHold                   // not from a spent chord: the stick is dead until let go
        cmp #255
        beq !+
        lda brainKindNow
        cmp #2
        beq !+
        jsr teachLesson
        jsr brainCheck
        lda brainLessonRan              // the lesson evaluated this block already (the retina, the mood-free
        beq !+                          // forward pass, the resolution): that is the think; the override drives
        lda brainKindNow                // him while teaching, so the pre-lesson choice is only telemetry
        beq !+
        cmp #2
        beq !+
        jmp thought
    !:
    lda brainKindNow
    bne !+
        rts                             // kind 0: the follow rule, in his turn
    !:
    lda brainKindNow
    cmp #2
    bne !+
        jsr builderThink
        jmp thought
    !:
    jsr profBegin                       // the think: the retina, the forward pass, the resolution
    jsr brainRetina
    jsr brainForward
    ldx #PROF_THINK
    jsr profEnd
    jsr gapStats
    thought:
    inc brainThinks
    bne !+
        inc brainThinks + 1
    !:
    rts
}
// the hooks' inputs: mode 0 the senses; mode 1 the flag vector as given, the active list from it, h left
testInputs: {
    lda brainTestMode
    bne flags
        .for (var i = 0; i < 20; i++) {
            lda brainTestIn + i
            sta brainIn + i
        }
        rts
    flags:
    lda #0
    sta brainActiveCount
    sta brainH
    ldx #0
    loop:
        lda brainTestFlags, x
        sta brainFlags, x
        beq !+
            txa
            ldy brainActiveCount
            sta brainActive, y
            inc brainActiveCount
        !:
        inx
        cpx #B02_N
        bne loop
    rts
}
// the score gap of the last think into the running minimum, maximum, sum and count
gapStats: {
    lda brainGap + 1
    cmp gapMin + 1
    bcc setMin
    bne !+
    lda brainGap
    cmp gapMin
    bcs !+
    setMin:
        lda brainGap
        sta gapMin
        lda brainGap + 1
        sta gapMin + 1
    !:
    lda brainGap + 1
    cmp gapMax + 1
    bcc !+
    bne setMax
    lda brainGap
    cmp gapMax
    bcc !+
    setMax:
        lda brainGap
        sta gapMax
        lda brainGap + 1
        sta gapMax + 1
    !:
    clc
    lda gapSum
    adc brainGap
    sta gapSum
    lda gapSum + 1
    adc brainGap + 1
    sta gapSum + 1
    bcc !+
        inc gapSum + 2
        bne !+
            inc gapSum + 3
    !:
    inc gapCount
    bne !+
        inc gapCount + 1
    !:
    rts
}

// brainFlags/brainActive and brainWeights -> brainAcc, brainOutput (the first largest), brainGap, and
// brainAction resolved from brainOutput with brainH under the slot's vocabulary. Interruptible.
brainForward: {
    lda #<brainWeights
    sta rowOp + 1
    lda #>brainWeights
    sta rowOp + 2
    lda #0
    sta o
    outputs:
        lda #0
        sta acc
        sta acc + 1
        lda brainNoMood
        bne noMood
            ldx o
            lda brainMood, x
            sta acc
            bpl noMood
                dec acc + 1             // a negative mood: the high byte is $ff
        noMood:
        ldx brainActiveCount
        beq rowDone
        adds:
            dex
            ldy brainActive, x
            rowOp: lda brainWeights, y
            bpl !+
                dec acc + 1
            !:
            clc
            adc acc
            sta acc
            bcc !+
                inc acc + 1
            !:
            cpx #0
            bne adds
        rowDone:
        lda o
        asl
        tax
        lda acc
        sta brainAcc, x
        lda acc + 1
        sta brainAcc + 1, x
        clc                             // the next row
        lda rowOp + 1
        adc #B02_N
        sta rowOp + 1
        bcc !+
            inc rowOp + 2
        !:
        inc o
        lda o
        cmp #10
        beq chosen
        jmp outputs
    chosen:
    lda #0                              // the first largest, signed 16-bit
    sta best
    ldx #2
    compare:
        sec
        lda brainAcc, x
        ldy best
        sbc brainAcc, y
        lda brainAcc + 1, x
        sbc brainAcc + 1, y
        bvc !+
            eor #$80
        !:
        bmi !+                          // acc[x] < acc[best]: keep it
        beq check                       // the high bytes agree: equal or larger?
        jmp larger
        check:
        lda brainAcc, x
        cmp brainAcc, y
        beq !+                          // equal: the first keeps
        larger:
        stx best
        !:
        inx
        inx
        cpx #20
    bne compare
    lda best
    lsr
    sta brainOutput
    // the runner-up: the first largest among the other nine
    ldx #0
    cpx best
    bne !+
        ldx #2
    !:
    stx second
    ldx #0
    compare2:
        cpx best
        beq skip2
        cpx second
        beq skip2
        sec
        lda brainAcc, x
        ldy second
        sbc brainAcc, y
        lda brainAcc + 1, x
        sbc brainAcc + 1, y
        bvc !+
            eor #$80
        !:
        bmi skip2
        beq check2
        jmp larger2
        check2:
        lda brainAcc, x
        cmp brainAcc, y
        beq skip2
        larger2:
        stx second
        skip2:
        inx
        inx
        cpx #20
    bne compare2
    sec                                 // the gap
    ldx best
    ldy second
    lda brainAcc, x
    sbc brainAcc, y
    sta brainGap
    lda brainAcc + 1, x
    sbc brainAcc + 1, y
    sta brainGap + 1
    lda brainOutput                     // the resolution: the identity under the absolute vocabulary or h left
    ldx brainVocab
    beq resolved
    ldx brainH
    beq resolved
        tax
        lda absTabR, x
    resolved:
    sta brainAction
    rts
    o:      .byte 0
    acc:    .word 0
    best:   .byte 0
    second: .byte 0
}

// the slot as it is now: the marker, the layout, the kind, the sizes, the rule, the vocabulary and the
// retina id must be what this build expects, or the clone behaves as kind 0 (PREREG-PHASE3.md section 4)
brainKindNow:     .byte 0
brainCheck: {
    ldx #7
    !:
        lda brainMarker, x
        cmp markerText, x
        bne bad
        dex
    bpl !-
    lda brainLayout
    cmp #2
    bne bad
    lda brainKind
    cmp #3
    bcs bad
    lda brainInputCount
    cmp #B02_N
    bne bad
    lda brainHiddenCount
    bne bad
    lda brainOutputCount
    cmp #10
    bne bad
    lda brainRule
    cmp #2
    bne bad
    lda brainVocab
    cmp #2
    bcs bad
    lda brainRetinaId
    cmp #B02_RETINA
    bne bad
    lda brainKind
    sta brainKindNow
    rts
    bad:
    lda #0
    sta brainKindNow
    rts
    markerText: .text "BRAIN02"
                .byte 0
}
"""

BRAIN02_LEARN_ASM = r"""
// ===================================================================== learning (BRAIN02)
// The rule at the byte box (PREREG-PHASE3.md section 5): the mood-free prediction p (the raw output); the
// taught raw index t is the applied absolute action translated with the block's h under the relative
// vocabulary (the identity under the absolute one, or when the hook supplies a raw index); no lesson
// if p == t; else for every set flag w[t][i] += 1 and w[p][i] -= 1, saturating at 127 and -128; the
// education count advances. brainLearn leaves p in brainPredicted, t in brainTaughtRaw and whether the
// lesson was taken in brainLearned.
brainTaught:        .byte 0             // the taught absolute action (or the raw index when learnRaw)
brainTaughtRaw:     .byte 0
brainPredicted:     .byte 0
brainLearned:       .byte 0
brainLessonRan:     .byte 0             // 1: brainLearn evaluated brainIn this pass (the think is done)
brainNoMood:        .byte 0
learnRaw:           .byte 0             // 1: the flags and the taught index are given (the hook's mode 1)
brainLearnRun:      .byte 0
brainLearnTestT:    .byte 0
brainLearnTestP:    .byte 0
brainLearnTestTook: .byte 0
brainLearnTestTrel: .byte 0
brainLearn: {
    lda learnRaw
    bne haveFlags
        jsr brainRetina
    haveFlags:
    lda #1
    sta brainNoMood
    sta brainLessonRan
    jsr brainForward
    lda #0
    sta brainNoMood
    sta brainLearned
    lda brainOutput
    sta brainPredicted
    lda brainTaught                     // the taught raw index
    ldx learnRaw
    bne haveT
    ldx brainVocab
    beq haveT
    ldx brainH
    beq haveT                           // h left: the identity
        tax
        lda relTabR, x
    haveT:
    sta brainTaughtRaw
    cmp brainPredicted
    bne !+
        rts                             // he would have done it: no lesson
    !:
    lda brainTaughtRaw                  // the taught row up
    tax
    clc
    lda rowLo, x
    adc #<brainWeights
    sta rdUp + 1
    sta wrUp + 1
    lda rowHi, x
    adc #>brainWeights
    sta rdUp + 2
    sta wrUp + 2
    ldx brainActiveCount
    beq upDone
    up:
        dex
        ldy brainActive, x
        rdUp: lda brainWeights, y
        cmp #$7f
        beq !+
            clc
            adc #1
            wrUp: sta brainWeights, y
        !:
        cpx #0
        bne up
    upDone:
    lda brainPredicted                  // the predicted row down
    tax
    clc
    lda rowLo, x
    adc #<brainWeights
    sta rdDn + 1
    sta wrDn + 1
    lda rowHi, x
    adc #>brainWeights
    sta rdDn + 2
    sta wrDn + 2
    ldx brainActiveCount
    beq downDone
    down:
        dex
        ldy brainActive, x
        rdDn: lda brainWeights, y
        cmp #$80
        beq !+
            sec
            sbc #1
            wrDn: sta brainWeights, y
        !:
        cpx #0
        bne down
    downDone:
    inc brainEducation
    bne !+
        inc brainEducation + 1
    !:
    lda #1
    sta brainLearned
    rts
    rowLo: .fill 10, (i * B02_N) & 255
    rowHi: .fill 10, ((i * B02_N) >> 8) & 255
}
"""

BRAIN02_TEACH_VARS_ASM = r"""
.label LESSON_BLOCK = {{LESSON}}          // the LESSON2 ring, in the memory the level tune vacates once it is copied
                                     // to $A000 (unpack): 32 + 11 * 300 = 3,332 bytes, to $9e03
.label LESSON_SIZE = 11
.label LESSON_CAP = 300
.label lessonMarker    = LESSON_BLOCK           // "LESSON2", 0
.label lessonWriteSeq  = LESSON_BLOCK + 8       // word: the sequence number of the next lesson; the lessons applied this session
.label lessonReadSeq   = LESSON_BLOCK + 10      // word: acknowledged and reclaimed up to here (exclusive)
.label lessonCap       = LESSON_BLOCK + 12      // word: the ring's capacity
.label lessonSize      = LESSON_BLOCK + 14      // 11
.label lessonStatus    = LESSON_BLOCK + 15      // bit 0 full (learning paused), 1 ack stale, 2 ack bad sum, 3 ack during a hold, 4 shadow pending, 7 ack accepted
.label lessonAckSeq    = LESSON_BLOCK + 16      // word, the host's: must equal lessonWriteSeq
.label lessonAckSum    = LESSON_BLOCK + 18      // word, the host's: the sum of every byte of the unread entries
.label lessonAckRequest = LESSON_BLOCK + 20     // the host writes 1; cleared when processed
.label lessonDrains    = LESSON_BLOCK + 21      // accepted acknowledgements this session
.label lessonCumWrite  = LESSON_BLOCK + 22      // word: the running sum of every byte recorded this session
.label lessonCumRead   = LESSON_BLOCK + 24      // word: the same up to lessonReadSeq
.label lessonData      = LESSON_BLOCK + 32      // 11 bytes per lesson; sequence s at slot s mod 300
.label lessonTotal     = lessonWriteSeq         // the old name: the lessons applied this session
teachMode:   .byte 0                 // 1 while teaching
teachHold:   .byte 0                 // frames the chord has been held; 255 once it toggled, until released
holdCount:   .byte 0                 // the brick count when the hold began
// the hold's shadow: the weights and the counters as they were when the chord was pressed, taken and put
// back by the main loop before any lesson (PREREG-PHASE3.md section 7), so a saved brain is one state
.label TEACH_SHADOW = {{SHADOW}}          // the weights' copy, 10 * B02_N bytes, in the vacated memory below the ring
shadowRequest:        .byte 0        // 1: the frame path asks for a snapshot
shadowRestoreRequest: .byte 0        // 1: the frame path asks for the restore
shadowValid: .byte 0                 // 1: the shadow holds this hold's starting state
shadowKind:  .byte 0
shadowEdu:   .word 0
shadowSeq:   .word 0
shadowSlot:  .word 0
shadowPtr:   .word 0
shadowCum:   .word 0
cloneUndo:   .byte 0                 // 1: the clone takes back his chord's brick at his next turn
teachWas:    .byte 0                 // teachMode last frame, to clear the override on the way out
portRaw:     .byte 0
cloneFlash:  .byte 0                 // frames left of the lesson's flash
cloneFlashColour: .byte 1            // the flash: 1 white, a lesson; 2 red, a lesson refused (the ring is full)
lessonWriteSlot: .word 0             // the slot of the next lesson, 0..299
lessonNotPaired: .word 0             // lessons lost because the block's next frame was not packed in time (telemetry)
joyRing:     .fill 8, 0              // the frame path's record of the last eight frames: the joystick byte applied,
stateRing:   .fill 8, 0              // the clone's state (bit 7 the facing), and the frame's low byte, at frame & 7,
frameRing:   .fill 8, 0              // so a lesson pairs the published block with the next frame's action whatever the main loop's pace
joyByte:     .byte 0
stateByte:   .byte 0
lessonWritePtr:  .word 0             // its address
"""

BRAIN02_LESSON_INIT_ASM = r"""
lessonInit: {
    ldx #7
    !:
        lda lessonText, x
        sta lessonMarker, x
        dex
    bpl !-
    lda #0
    ldx #8                              // the header's bytes 8..31 cleared
    !:
        sta lessonMarker, x
        inx
        cpx #32
    bne !-
    lda #<LESSON_CAP
    sta lessonCap
    lda #>LESSON_CAP
    sta lessonCap + 1
    lda #LESSON_SIZE
    sta lessonSize
    lda #<lessonData
    sta lessonWritePtr
    lda #>lessonData
    sta lessonWritePtr + 1
    lda #0
    sta lessonWriteSlot
    sta lessonWriteSlot + 1
    sta teachMode
    sta teachHold
    sta teachWas
    sta cloneFlash
    sta cloneUndo
    sta holdCount
    sta shadowValid
    sta shadowRequest
    sta shadowRestoreRequest
    sta lessonNotPaired
    sta lessonNotPaired + 1
    lda #1
    sta cloneFlashColour
    jsr profInit
    rts
    lessonText: .text "LESSON2"
                .byte 0
}
"""

BRAIN02_SHADOW_ASM = r"""
// the hold's shadow, taken and put back by the main loop (bodyThink) before any lesson
teachShadowSave: {
    lda #<brainWeights
    sta copyWeights.rd + 1
    lda #>brainWeights
    sta copyWeights.rd + 2
    lda #<TEACH_SHADOW
    sta copyWeights.wr + 1
    lda #>TEACH_SHADOW
    sta copyWeights.wr + 2
    jsr copyWeights
    lda brainKind
    sta shadowKind
    lda brainEducation
    sta shadowEdu
    lda brainEducation + 1
    sta shadowEdu + 1
    lda lessonWriteSeq
    sta shadowSeq
    lda lessonWriteSeq + 1
    sta shadowSeq + 1
    lda lessonWriteSlot
    sta shadowSlot
    lda lessonWriteSlot + 1
    sta shadowSlot + 1
    lda lessonWritePtr
    sta shadowPtr
    lda lessonWritePtr + 1
    sta shadowPtr + 1
    lda lessonCumWrite
    sta shadowCum
    lda lessonCumWrite + 1
    sta shadowCum + 1
    lda #1
    sta shadowValid
    rts
}
teachShadowRestore: {
    lda #0
    sta shadowValid
    lda #<TEACH_SHADOW
    sta copyWeights.rd + 1
    lda #>TEACH_SHADOW
    sta copyWeights.rd + 2
    lda #<brainWeights
    sta copyWeights.wr + 1
    lda #>brainWeights
    sta copyWeights.wr + 2
    jsr copyWeights
    lda shadowKind
    sta brainKind
    lda shadowEdu
    sta brainEducation
    lda shadowEdu + 1
    sta brainEducation + 1
    lda shadowSeq
    sta lessonWriteSeq
    lda shadowSeq + 1
    sta lessonWriteSeq + 1
    lda shadowSlot
    sta lessonWriteSlot
    lda shadowSlot + 1
    sta lessonWriteSlot + 1
    lda shadowPtr
    sta lessonWritePtr
    lda shadowPtr + 1
    sta lessonWritePtr + 1
    lda shadowCum
    sta lessonCumWrite
    lda shadowCum + 1
    sta lessonCumWrite + 1
    lda lessonStatus                    // the ring cannot be full after a rewind
    and #%11111110
    sta lessonStatus
    lda #0                              // and the next think decides with the restored weights
    sta brainAction
    rts
}
// B02_WEIGHT_BYTES bytes from rd to wr (the operands set by the caller)
copyWeights: {
    ldx #>B02_WEIGHT_BYTES
    ldy #0
    loop:
        cpx #0
        bne copy
        cpy #<B02_WEIGHT_BYTES
        beq done
    copy:
        rd: lda $ffff, y
        wr: sta $ffff, y
        iny
        bne loop
        inc rd + 2
        inc wr + 2
        dex
        jmp loop
    done:
    rts
}
// the drain handshake (PREREG-PHASE3.md section 6): the host acknowledges the whole unread range with
// its checksum; the program validates and reclaims, or rejects and says why
lessonAck: {
    lda lessonStatus
    and #%00000001                      // keep the full bit, clear the outcome bits
    sta lessonStatus
    lda teachHold                       // a chord hold in progress: busy
    beq notBusy
    cmp #255
    beq notBusy
        lda lessonStatus
        ora #%00001000
        sta lessonStatus
        jmp done
    notBusy:
    lda lessonAckSeq
    cmp lessonWriteSeq
    bne stale
    lda lessonAckSeq + 1
    cmp lessonWriteSeq + 1
    bne stale
    sec                                 // the sum over the unread range: cumWrite - cumRead
    lda lessonCumWrite
    sbc lessonCumRead
    sta d
    lda lessonCumWrite + 1
    sbc lessonCumRead + 1
    sta d + 1
    lda d
    cmp lessonAckSum
    bne badSum
    lda d + 1
    cmp lessonAckSum + 1
    bne badSum
    lda lessonWriteSeq                  // accepted
    sta lessonReadSeq
    lda lessonWriteSeq + 1
    sta lessonReadSeq + 1
    lda lessonCumWrite
    sta lessonCumRead
    lda lessonCumWrite + 1
    sta lessonCumRead + 1
    inc lessonDrains
    lda lessonStatus
    and #%11111110
    ora #%10000000
    sta lessonStatus
    jmp done
    stale:
        lda lessonStatus
        ora #%00000010
        sta lessonStatus
        jmp done
    badSum:
        lda lessonStatus
        ora #%00000100
        sta lessonStatus
    done:
    lda #0
    sta lessonAckRequest
    rts
    d: .word 0
}
"""

BRAIN02_TEACH_LESSON_ASM = r"""
// at a think tick or an edge while teaching: the lesson from the block in brainIn (x, the state of frame
// N) and the action applied in frame N + 1 (t: the packer's sense 16 of the frame after). No lesson when
// the two frames are not consecutive, while a snapshot or a restore is pending, or while the ring is
// full (learning pauses: the clone flashes red, the status says so).
teachLesson: {
    lda #0
    sta brainLessonRan
    clc                                 // the action applied in the frame after the block's, from the ring the frame
    lda brainInFrame                    // path fills: the pairing no longer depends on the main loop keeping pace
    adc #1
    sta nextLo
    and #7
    tax
    lda frameRing, x
    cmp nextLo
    beq next
    notNext:
        inc lessonNotPaired             // a pack was missed (the main loop ran long): no lesson from this block
        bne !+
            inc lessonNotPaired + 1
        !:
        lda #0
        sta brainLearned
        rts
    next:
    lda joyRing, x
    sta joyByte
    lda stateRing, x
    sta stateByte
    lda shadowRequest
    ora shadowRestoreRequest
    beq !+
        lda #0
        sta brainLearned
        rts
    !:
    sec                                 // full: writeSeq - readSeq == the capacity (the header's, so a research
    lda lessonWriteSeq                  // control may lower it at boot, before any lesson)
    sbc lessonReadSeq
    sta dLo
    lda lessonWriteSeq + 1
    sbc lessonReadSeq + 1
    cmp lessonCap + 1
    bne notFull
    lda dLo
    cmp lessonCap
    bne notFull
        lda lessonStatus
        ora #%00000001
        sta lessonStatus
        lda #6
        sta cloneFlash
        lda #2
        sta cloneFlashColour
        lda #0
        sta brainLearned
        rts
    notFull:
    jsr actionOf                        // the applied action of that frame (as sense 16 derives it)
    sta brainTaught
    jsr profBegin
    jsr brainLearn
    ldx #PROF_LESSON
    jsr profEnd
    lda brainLearned
    bne taken
        rts
    taken:
    lda #6                              // the flash
    sta cloneFlash
    lda #1
    sta cloneFlashColour
    lda brainKind                       // the first lesson makes a brain of him
    bne !+
        lda #1
        sta brainKind
    !:
    lda lessonWritePtr                  // the record: the twenty nibbles packed, then taught | predicted << 4
    sta wr + 1
    sta wr2 + 1
    lda lessonWritePtr + 1
    sta wr + 2
    sta wr2 + 2
    ldx #0
    ldy #0
    pack:
        lda brainIn + 1, x
        and #$0f
        asl
        asl
        asl
        asl
        sta pair
        lda brainIn, x
        and #$0f
        ora pair
        wr: sta $ffff, y
        jsr addSum
        iny
        inx
        inx
        cpx #20
    bne pack
    lda brainPredicted
    asl
    asl
    asl
    asl
    sta pair
    lda brainTaught
    and #$0f
    ora pair
    wr2: sta $ffff, y
    jsr addSum
    inc lessonWriteSeq                  // advance
    bne !+
        inc lessonWriteSeq + 1
    !:
    inc lessonWriteSlot
    bne !+
        inc lessonWriteSlot + 1
    !:
    clc
    lda lessonWritePtr
    adc #LESSON_SIZE
    sta lessonWritePtr
    bcc !+
        inc lessonWritePtr + 1
    !:
    lda lessonWriteSlot + 1             // the wrap, at the header's capacity
    cmp lessonCap + 1
    bne notWrap
    lda lessonWriteSlot
    cmp lessonCap
    bne notWrap
        lda #0
        sta lessonWriteSlot
        sta lessonWriteSlot + 1
        lda #<lessonData
        sta lessonWritePtr
        lda #>lessonData
        sta lessonWritePtr + 1
    notWrap:
    sec                                 // full now? say so
    lda lessonWriteSeq
    sbc lessonReadSeq
    sta dLo
    lda lessonWriteSeq + 1
    sbc lessonReadSeq + 1
    cmp lessonCap + 1
    bne done
    lda dLo
    cmp lessonCap
    bne done
        lda lessonStatus
        ora #%00000001
        sta lessonStatus
    done:
    rts
    addSum: {                           // A: the byte just recorded -> lessonCumWrite
        clc
        adc lessonCumWrite
        sta lessonCumWrite
        bcc !+
            inc lessonCumWrite + 1
        !:
        rts
    }
    pair:   .byte 0
    dLo:    .byte 0
    nextLo: .byte 0
}
// IN: joyByte, stateByte (a frame's applied joystick byte and the clone's state) -> A: the action index, as the
// packer derives sense 16 (0 idle, 1 left, 2 right, 3 up, 4 down, 5 jump, 6 jump left, 7 jump right, 8/9 build the way he faces)
actionOf: {
    lda joyByte
    and #%01100000
    beq notBuild
        ldx #8
        lda stateByte
        bpl !+
            inx
        !:
        jmp known
    notBuild:
    lda joyByte
    and #%00010000
    beq notFire
        ldx #6
        lda joyByte
        and #%00000100
        bne known
        ldx #7
        lda joyByte
        and #%00001000
        bne known
        ldx #5
        jmp known
    notFire:
    ldx #1
    lda joyByte
    and #%00000100
    bne known
    ldx #2
    lda joyByte
    and #%00001000
    bne known
    ldx #3
    lda joyByte
    and #%00000001
    bne known
    ldx #4
    lda joyByte
    and #%00000010
    bne known
    ldx #0
    known:
    txa
    rts
}
"""

def _span(src, start, end_marker, include_end=True):
    i = src.index(start); j = src.index(end_marker, i) + (len(end_marker) if include_end else 0)
    return i, j

def brain02_apply(src, retina_name, vocab):
    """replace the BRAIN01 blocks of the body's assembly with BRAIN02's"""
    rid = BRAIN02_NAMES[retina_name]
    if retina_name == "p128":
        entries = [(brain02_ref.GE, 0, 1)] * 128                       # a parity build: 128 inputs, the retina never used (mode 1 hooks)
    else:
        entries = brain02_ref.TABLES[rid][1]()
    n = len(entries)
    ops = ", ".join(str(op) for op, a, k in entries); as_ = ", ".join(str(a) for op, a, k in entries); ks = ", ".join(f"${k & 255:02x}" for op, a, k in entries)
    slot = (BRAIN02_SLOT_ASM.replace("{{N}}", str(n)).replace("{{RETINA}}", str(rid)).replace("{{VOCAB}}", "1" if vocab == "rel" else "0")
            .replace("{{OPS}}", ops).replace("{{AS}}", as_).replace("{{KS}}", ks))
    def rep(start, end_marker, new, include_end=True):
        nonlocal src
        i, j = _span(src, start, end_marker, include_end); src = src[:i] + new + src[j:]
    # 1. the slot, the live state, the tables, the retina (through the multiply table)
    rep('.align 256\nbrainMarker:    .text "BRAIN01"', "brainMul:       .fill 256, ((((i >> 4) >= 8) ? (i >> 4) - 16 : (i >> 4)) * (((i & 15) >= 8) ? (i & 15) - 16 : (i & 15))) & 255\n", slot)
    # 2. bodyThink, brainForward, brainCheck
    rep("bodyThink: {\n", '    markerText: .text "BRAIN01"\n                .byte 0\n}\n', BRAIN02_THINK_ASM)
    # 3. learning
    rep("// ===================================================================== learning\n", "        byte:   .byte 0\n        nib:    .byte 0\n    }\n}\n", BRAIN02_LEARN_ASM)
    # 4. the teaching variables and labels
    shadow, lesson = ("$9200", "$9800") if retina_name == "p128" else ("$8e00", "$9100")     # the parity build's slot is 1,314 bytes: its blocks sit higher
    rep(".label LESSON_BLOCK = $8a00", "lessonPtr:   .word 0                 // where the next lesson goes\n", BRAIN02_TEACH_VARS_ASM.replace("{{SHADOW}}", shadow).replace("{{LESSON}}", lesson))
    # 5. lessonInit
    rep("lessonInit: {\n", '    lessonText: .text "LESSON1"\n                .byte 0\n}\n', BRAIN02_LESSON_INIT_ASM)
    # 6. teachRoute: the snapshot and the restore become requests for the main loop
    old = ("            lda teachMode                   // teaching: the weights and lesson counters before its lessons\n"
           "            beq !+                          // (not otherwise: no lesson can happen, and the copy's 57 raster\n"
           "            jsr teachShadowSave             // lines would land in the frame of Tony's own lay, the heaviest)\n")
    assert src.count(old) == 1; src = src.replace(old, "            lda teachMode                   // teaching: the main loop snapshots before any lesson (BRAIN02)\n            beq !+\n            lda #1\n            sta shadowRequest\n")
    old = ("            lda shadowValid                 // and the lessons the press taught, if any, are forgotten\n"
           "            beq !+\n            jsr teachShadowRestore\n            !:\n")
    assert src.count(old) == 1; src = src.replace(old, ("            lda #0                          // a snapshot still pending means no lesson happened: nothing to undo\n"
                                                        "            sta shadowRequest\n"
                                                        "            sta brainAction                 // the last think was the hold-time brain: idle until the next think, after the restore\n"
                                                        "            sta macroStep                   // a build macro in progress is dropped with it\n"
                                                        "            lda shadowValid                 // and the lessons the press taught, if any, are forgotten (the main loop restores)\n"
                                                        "            beq !+\n            lda #1\n            sta shadowRestoreRequest\n            !:\n"))
    # 7. the shadow copies and the lesson
    rep("teachShadowSave: {\n", "    lda shadowPtr + 1\n    sta lessonPtr + 1\n    rts\n}\n", BRAIN02_SHADOW_ASM)
    rep("teachLesson: {\n", "    pair:    .byte 0\n    wr2byte: .byte 0\n    nextLo:  .byte 0\n}\n", BRAIN02_TEACH_LESSON_ASM)
    # 7b. the frame path records each frame's applied joystick byte and state by frame, for the lesson pairing
    old = "    lda bodyFrames\n    sta rawFrame\n    lda bodyFrames + 1\n    sta rawFrame + 1\n    lda sensePacked\n    bne !+\n        rts\n    !:\n"
    assert src.count(old) == 1; src = src.replace(old, ("    lda bodyFrames\n    sta rawFrame\n    lda bodyFrames + 1\n    sta rawFrame + 1\n"
                                                        "    lda bodyFrames                  // BRAIN02: this frame's joystick byte and state, by frame, for the lesson pairing\n    and #7\n    tax\n"
                                                        "    lda rawJoy\n    sta joyRing, x\n    lda rawState\n    sta stateRing, x\n    lda bodyFrames\n    sta frameRing, x\n"
                                                        "    lda sensePacked\n    bne !+\n        rts\n    !:\n"))
    # 8. the clone's turn does nothing while a restore is pending: a think already in flight at the toggle would
    # otherwise hand the decoder the hold's choice before the main loop has put the weights back
    old = "cloneDecode: {\n    lda macroStep\n    bne macro\n"
    assert src.count(old) == 1; src = src.replace(old, "cloneDecode: {\n    lda shadowRestoreRequest            // BRAIN02: a restore pending: nothing until the next think decides with the restored weights\n    beq !+\n        lda #0\n        sta macroStep\n        jmp emit\n    !:\n    lda macroStep\n    bne macro\n")
    # 9. the flash's colour
    old = "    lda muralColour                 // the clone's colour: the parameter block's, white for a lesson's flash\n    ldx cloneFlash\n    beq !+\n        dec cloneFlash\n        lda #1\n    !:\n"
    assert src.count(old) == 1; src = src.replace(old, "    lda muralColour                 // the clone's colour: the parameter block's; a lesson's flash white, a refused one red\n    ldx cloneFlash\n    beq !+\n        dec cloneFlash\n        lda cloneFlashColour\n    !:\n")
    # the comment that describes the old lesson block's placement is gone with its labels; the guard stands
    return src
