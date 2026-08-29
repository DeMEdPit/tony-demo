/*
 * MIT License
 *
 * Copyright (c) 2023 Maciej Małecki
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/*
 * ROM-free rework of the boot cheat menu ("official trainer").
 *
 * The original menu displays through the character ROM (VIC bank 0,
 * charset $1800 = char ROM shadow), which does not exist on ROM-less
 * targets such as minimal64 - the menu ran invisibly there.
 *
 * This version runs at the original spot in the boot sequence (before
 * unpack, while the whole loaded image is still intact) but brings its
 * own glyphs: it copies the game's embedded 37-char font (@, A-Z, 0-9)
 * from its load-time location to $E800 - free RAM above the end of the
 * loaded image - and displays a screen at $EC00 through the $C000 VIC
 * bank. Both areas are scratch: init/unpack rebuilds everything after.
 *
 * The input logic is the original's, unchanged: direct CIA1 keyboard
 * matrix scanning for Y/N/RETURN and a direct joystick read for FIRE.
 * No KERNAL, BASIC, or character ROM is touched anywhere.
 */

#import "common/lib/invoke-global.asm"
#import "chipset/lib/vic2-global.asm"
#import "chipset/lib/cia-global.asm"
#import "chipset/lib/mos6510-global.asm"

#import "_zero-page.asm"
#import "_constants.asm"

.label CMR_SCREEN  = $EC00 // free RAM above the loaded image
.label CMR_CHARSET = $E800
.label CMR_MAX_DELAY = 200

// the scratch screen and charset must lie above everything the PRG loads
.assert "romfree menu scratch area clear of the loaded image", endOfTony <= CMR_CHARSET, true

cheatMenuRomfree: {
    // VIC bank $C000, screen $EC00 (slot 11), charset $E800 (slot 5)
    c64lib_setVICBank(0)
    lda #%10111010
    sta c64lib.MEMORY_CONTROL
    lda #%00011011
    sta c64lib.CONTROL_1
    lda #%00001000
    sta c64lib.CONTROL_2
    lda #BLACK
    sta c64lib.BORDER_COL
    sta c64lib.BG_COL_0

    jsr cmrInstallFont
    jsr cmrClearScreen
    jsr cmrDisplayText

    lda #CHEAT_INITIAL
    sta gameCheatState

    // setup keyboard
    lda #0
    sta c64lib.CIA1_DATA_DIR_B

    ldy #0
    loop:
        lda #WHITE
        jsr cmrHighlightLine

    readKeyboard:
        lda #%11100111
        jsr cmrReadKey
        cmp #%10000000 // N
        beq no
        cmp #%00000010 // Y
        beq yes
        lda #%11111110
        jsr cmrReadKey
        cmp #%00000010 // CR
        beq quit
        jsr cmrReadJoy
        and #%00010000
        cmp #%00010000
        beq quit
        jmp readKeyboard
    continue:
        lda #0
        jsr cmrReadKey
        cmp #0
        bne continue

        lda #LIGHT_GRAY
        jsr cmrHighlightLine
        iny
        cpy #5
    bne loop
    quit:
        rts // boot continues with blankScreen/init, which rebuild the VIC state

    cmrReadKey: {
        pha
        lda #$ff
        sta c64lib.CIA1_DATA_DIR_A
        pla

        jsr readOnce
        cmp #0
        beq return
        sta lastValue

        ldx #CMR_MAX_DELAY
        delayLoop:
            jsr readOnce
            cmp #0
            beq return
            dex
        bne delayLoop
        rts

    readOnce:
        sta c64lib.CIA1_DATA_PORT_A
        lda c64lib.CIA1_DATA_PORT_B
        eor #$ff
    return:
        rts
    lastValue: .byte 0
    }

    cmrReadJoy: {
        lda #0
        sta c64lib.CIA1_DATA_DIR_A
        lda c64lib.CIA1_DATA_PORT_A
        eor #$ff
        rts
    }

    yes: {
        lda #1
        jsr answer
        lda gameCheatState
        ora cmrCheatFlags, y
        sta gameCheatState
        jmp continue
    }
    no: {
        lda #0
        jsr answer
        jmp continue
    }

    // A - zero no, non zero yes, Y - line number
    answer: {
        pha
        clc
        lda cmrLinesChars.lo, y
        adc #34
        sta address
        lda cmrLinesChars.hi, y
        adc #0
        sta address + 1
        pla
        beq !+
            c64lib_pushParamW(cmrTxtYes)
        jmp !++
        !:
            c64lib_pushParamW(cmrTxtNo)
        !:

        c64lib_pushParamWInd(address)
        jsr outText
        rts

        address: .word 0
    }
}

// copy the embedded game font from its load-time position to the scratch
// charset; every other glyph is zeroed so unknown codes render blank
cmrInstallFont: {
    ldx #0
    clearLoop:
        lda #0
        .for (var i = 0; i < 8; i++) {
            sta CMR_CHARSET + i*256, x
        }
        inx
    bne clearLoop
    ldx #0
    copyLoop:
        lda font, x
        sta CMR_CHARSET, x
        lda font + 148, x
        sta CMR_CHARSET + 148, x
        inx
        cpx #148
    bne copyLoop
    rts
}

cmrClearScreen: {
    ldx #0
    loop:
        lda #0 // glyph 0 = '@' = blank in the game font
        sta CMR_SCREEN, x
        sta CMR_SCREEN + 250, x
        sta CMR_SCREEN + 500, x
        sta CMR_SCREEN + 750, x
        lda #LIGHT_GRAY
        sta c64lib.COLOR_RAM, x
        sta c64lib.COLOR_RAM + 250, x
        sta c64lib.COLOR_RAM + 500, x
        sta c64lib.COLOR_RAM + 750, x
        inx
        cpx #250
    bne loop
    rts
}

.var cmrCheatTexts = List().add(cmrTxtCheat0, cmrTxtCheat1, cmrTxtCheat2, cmrTxtCheat3, cmrTxtCheat4)

cmrDisplayText: {
    c64lib_pushParamW(cmrTxtTitle0)
    c64lib_pushParamW(CMR_SCREEN + 1*40 + 8)
    jsr outText
    c64lib_pushParamW(cmrTxtTitle1)
    c64lib_pushParamW(CMR_SCREEN + 2*40 + 12)
    jsr outText

    .for(var i = 0; i < cmrCheatTexts.size(); i++) {
        c64lib_pushParamW(cmrCheatTexts.get(i))
        c64lib_pushParamW(CMR_SCREEN + (7+2*i) * 40 + 3)
        jsr outText
        c64lib_pushParamW(cmrTxtYesNo)
        c64lib_pushParamW(CMR_SCREEN + (7+2*i) * 40 + 34)
        jsr outText
    }

    c64lib_pushParamW(cmrTxtPress)
    c64lib_pushParamW(CMR_SCREEN + 21*40 + 8)
    jsr outText
    rts
}

// A - color, Y - line number
cmrHighlightLine: {
    pha
    lda cmrLinesCols.lo, y
    sta address
    lda cmrLinesCols.hi, y
    sta address + 1
    pla
    ldx #0
    loop:
        sta address:$ffff, x
        inx
        cpx #40
    bne loop
    rts
}

cmrLinesChars: .lohifill 5, CMR_SCREEN + (7+2*i)*40
cmrLinesCols:  .lohifill 5, c64lib.COLOR_RAM + (7+2*i)*40

cmrCheatFlags: .byte $04, $02, $20, $10, $08

// the game font carries @, A-Z and 0-9 only, so the wording sticks to those
cmrTxtTitle0: .text "tony@born@for@adventure"; .byte $ff
cmrTxtTitle1: .text "official@trainer"; .byte $ff

cmrTxtCheat0: .text "infinite@lives"; .byte $ff
cmrTxtCheat1: .text "resistant@to@boulders"; .byte $ff
cmrTxtCheat2: .text "resistant@to@spikes"; .byte $ff
cmrTxtCheat3: .text "resistant@to@nasties"; .byte $ff
cmrTxtCheat4: .text "pass@thru@closed@doors"; .byte $ff

cmrTxtPress:  .text "return@or@fire@to@start"; .byte $ff

cmrTxtYesNo:  .text "y@n@"; .byte $ff
cmrTxtYes:    .text "yes@"; .byte $ff
cmrTxtNo:     .text "no@@"; .byte $ff
