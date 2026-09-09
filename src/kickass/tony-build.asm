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

// #define VISUAL_DEBUG

#import "common/lib/invoke-global.asm"
#import "chipset/lib/vic2-global.asm"
#import "chipset/lib/cia-global.asm"
#import "chipset/lib/mos6510-global.asm"
#import "copper64/lib/copper64-global.asm"

#import "_zero-page.asm"
#import "_constants.asm"
#import "_loader.asm"

.segmentdef Code [start=LDR_MAIN_START_ADDRESS]
.segmentdef Movable [startAfter="Code"]

.file [name="./tony-build.prg", segments="Code, Movable", modify="BasicUpstart", _start=LDR_MAIN_START_ADDRESS]

.var music = LoadSid("TonyLevelA000_V2.sid")
.var intro = LoadSid("TonyIntro8000_reloc.sid")   // the Glitch's tune, at $8000


.label musicLocation = music.location
.label musicSize = music.size

.segment Code

start:
    jmp startAfter

copperList: // must fit into a single page
    c64lib_copperEntry(40, c64lib.IRQH_JSR, <doEachFrameTop, >doEachFrameTop)
    c64lib_copperEntry(255, c64lib.IRQH_JSR, <doEachFrameVisual, >doEachFrameVisual)
    c64lib_copperLoop()
copperListEnd:

.assert "copper list(s) must fit into a single memory page", >copperList, >copperListEnd

startAfter:
    jsr detectNTSC
    sei
    c64lib_disableCIAInterrupts()
    c64lib_configureMemory(c64lib.RAM_IO_RAM)
    c64lib_setVICBank(3)
    cli
    lda #0
    sta gameCheatState
    jsr blankScreen
    seq_setUp(0, 0, 0, 0)
    jsr init
    jsr startRoomDirect
    jmp startLevel

init: {
    // set up C64
    sei
    c64lib_disableCIAInterrupts()
    c64lib_configureMemory(c64lib.RAM_RAM_RAM)
    jsr unpack
    c64lib_configureMemory(c64lib.RAM_IO_RAM)
    c64lib_setVICBank(0)
    cli
    // set up VIC-2
    lda #%00010111
    sta c64lib.CONTROL_1
    lda #%00001000
    sta c64lib.CONTROL_2
    lda #%00000010
    sta c64lib.MEMORY_CONTROL
    ldx #DEFAULT_COLOR_SCHEME
    stx colorScheme
    lda colorLights, x
    sta currentColor
    jsr setColors
    // NTSC counter
    lda #0
    sta ntscCounter

    // turn off decimal mode (just in case)
    cld
    jsr io_init

    // fill up buffers (remove when buffers goes back to the code segment!)
    lda #<roomCharsDecodingBuffer
    sta cleanBuffer.address
    lda #>roomCharsDecodingBuffer
    sta cleanBuffer.address + 1
    jsr cleanBuffer

    lda #<roomMaterialsBuffer
    sta cleanBuffer.address
    lda #>roomMaterialsBuffer
    sta cleanBuffer.address + 1
    jsr cleanBuffer

    rts

    cleanBuffer: {
        lda #0
        ldx #0
        loop:
            sta address:$ffff, x
            inx
            bne loop
        rts
    }
}

unpack: {

    c64lib_pushParamW(font)
    c64lib_pushParamW(FONT_BUFFER_MEM)
    c64lib_pushParamW(37*8)
    jsr copyLargeMemForward

    c64lib_pushParamW(gameEnd)
    c64lib_pushParamW(ENDGAME_BUFFER_MEM)
    c64lib_pushParamW(84*8)
    jsr copyLargeMemForward

    c64lib_pushParamW(firstSpriteBank)
    c64lib_pushParamW(SPRITES_MEM)
    c64lib_pushParamW(firstSpriteBankEnd - firstSpriteBank)
    jsr copyLargeMemForward

    jsr fillEmptySprite

    c64lib_pushParamW(dasboardCharset)
    c64lib_pushParamW(TEXT_DASHBOARD_CHARS_MEM)
    c64lib_pushParamW(DASHBOARD_CHAR_COUNT*8)
    jsr copyLargeMemForward

    c64lib_pushParamW(thirdSpriteBank) // bat h
    c64lib_pushParamW(SPRITES_BANK3)
    c64lib_pushParamW(thirdSpriteBankEnd - thirdSpriteBank)
    jsr copyLargeMemForward

    c64lib_pushParamW(secondSpriteBank) // deadman & batv
    c64lib_pushParamW(SCREEN_MEM_1)
    c64lib_pushParamW(secondSpriteBankEnd - secondSpriteBank)
    jsr copyLargeMemForward

    c64lib_pushParamW(musicData)
    c64lib_pushParamW(MUSIC_MEM)
    c64lib_pushParamW(musicSize)
    jsr copyLargeMemForward

    rts
}


setNTSC: {
    lda #1
    sta ntscFlag
    rts
}
detectNTSC: {
    lda #0
    sta ntscFlag
    c64lib_detectNtsc(0, setNTSC)
    rts
}


fillEmptySprite: {
    ldx #0
    lda #0
!:
    sta $ff80, x
    inx
    cpx #63
    bne !-

    rts
}

startTitle: {
    jsr hideEyes
    lda #1
    sta gameTitleScreen
    jsr aux_cleanBottomPart
    jsr setColors
    jsr exchangeFonts

    ldx #(MAX_TITLE_TEXT - 1)
    stx txtCounter

    c64lib_pushParamW(txtPressFire)
    c64lib_pushParamW(SCREEN_MEM_1 + 23*40 + 10)
    jsr outText
    jsr displayNext

    rts

    displayNext: {
        ldx txtCounter
        inx
        cpx #MAX_TITLE_TEXT
        bne !+
            ldx #0
        !:
        stx txtCounter

        lda txtPtrLo, x
        sta displayLine.lineAddr
        lda txtPtrHi, x
        sta displayLine.lineAddr + 1
        jsr displayLine

        seq_setUpExt(20, 6, doNothing, displayNext, true)

        rts
    }

    displayLine: {
        lda #0
        ldx #0
        loop:
            sta SCREEN_MEM_1 + 21*40, x
            inx
            cpx #40
        bne loop

        lda #<(SCREEN_MEM_1 + 21*40)
        clc
        adc lineAddr:$ffff
        sta screenLocation
        lda #>(SCREEN_MEM_1 + 21*40)
        adc #0
        sta screenLocation + 1

        clc
        lda lineAddr
        adc #1
        sta lineAddr1
        lda lineAddr + 1
        adc #0
        sta lineAddr1 + 1

        c64lib_pushParamWInd(lineAddr1)
        c64lib_pushParamWInd(screenLocation)
        jsr outText

        rts
        screenLocation: .word 0
        lineAddr1: .word 0
    }
}

startGame: {
    jsr blankScreen
    lda #0
    sta gameTitleScreen
    sta joyAccumulator
    sta joyDelayCounter
    sta joyPreviousValue
    jsr exchangeFonts
    jsr drawScreen
    jsr showEyes
    jsr showScreen
    rts
}

startRoomDirect: {
    jsr blankScreen
    lda #0
    sta gameTitleScreen
    sta joyAccumulator
    sta joyDelayCounter
    sta joyPreviousValue
    jsr showScreen
    rts
}

setColors: {
    ldy colorScheme
    ldx #0

    lda colorDarks, y
    sta c64lib.BORDER_COL
    sta c64lib.SPRITE_2_COLOR
    sta c64lib.SPRITE_7_COLOR
    sta eyesColor
loop1:
    .for (var i = 0; i <= 3; i++) {
        sta c64lib.COLOR_RAM + i*200, x
    }
    inx
    cpx #200
    bne loop1

    ldx #0
    lda colorDarks, y // tall room: rows 20-24 are playfield now
loop2:
    sta c64lib.COLOR_RAM + 800, x
    inx
    cpx #200
    bne loop2
    ldx #0
loop3:
    cpx #2
    beq !+
        sta c64lib.SPRITE_0_COLOR, x
    !:
    inx
    cpx #7
    bne loop3
    rts
}

exchangeFonts: {
    sei
    c64lib_configureMemory(c64lib.RAM_RAM_RAM)
    ldx #0
    loop:
        ldy FONT_BUFFER_MEM, x
        lda TEXT_DASHBOARD_CHARS_MEM, x
        sta FONT_BUFFER_MEM, x
        tya
        sta TEXT_DASHBOARD_CHARS_MEM, x

        ldy FONT_BUFFER_MEM + 148, x
        lda TEXT_DASHBOARD_CHARS_MEM + 148, x
        sta FONT_BUFFER_MEM + 148, x
        tya
        sta TEXT_DASHBOARD_CHARS_MEM + 148, x

        inx
        cpx #148
    bne loop
    c64lib_configureMemory(c64lib.RAM_IO_RAM)
    cli
    rts
}

startLevel: {
    jsr initRoom
    jsr initGameState
    jsr resetRoomStates
    jsr chooseRoom
    jsr initStaticObjectsCharset
    jsr initStaticObjectsMaterials
    jsr drawPlayfield
    jsr initEffects
    jsr initPlayerPosition
    jsr buddyInit
    jsr ani_init
    jsr updatePlayerPosition
    jsr phys_init
    jsr checkBGCollision // TODO: to have collision flag initialized
    jsr initSound
    lda #<copperList
    sta COPPER_LIST_ADDR
    lda #>copperList
    sta COPPER_LIST_ADDR + 1
    jsr startCopper

    loop:
        cld
        jsr turnOneSnake
        jsr changeRoomIfNeeded
        lda objCollisionDetected
        cmp #$ff
        beq !+
            jsr handleObjCollision
        !:
        lda gameState
        cmp #STATE_GAMEOVER
        beq gameOver
        cmp #STATE_ENDOFGAME
        beq endOfGame
    jmp loop

    gameOver: {
        jsr commonEntry
        jsr aux_drawEndGameScreen

        c64lib_pushParamW(txtGameOver)
        c64lib_pushParamW(SCREEN_MEM_0 + 40*13 + 15)
        jsr outText

        c64lib_pushParamW(txtPressFireCnt)
        c64lib_pushParamW(SCREEN_MEM_0 + 40*15 + 9)
        jsr outText

        jmp commonOutry
    }

    endOfGame: {
        jsr commonEntry
        jsr aux_drawEndGameScreen

        c64lib_pushParamW(textEnd0)
        c64lib_pushParamW(SCREEN_MEM_0 + 40*12 + 14)
        jsr outText

        c64lib_pushParamW(textEnd1)
        c64lib_pushParamW(SCREEN_MEM_0 + 40*14 + 4)
        jsr outText

        c64lib_pushParamW(textEnd2)
        c64lib_pushParamW(SCREEN_MEM_0 + 40*15 + 11)
        jsr outText

        c64lib_pushParamW(txtPressFireCnt)
        c64lib_pushParamW(SCREEN_MEM_0 + 40*17 + 9)
        jsr outText

        jmp commonOutry
    }

    commonEntry: {
        jsr playboardFadeOut
        waitFor()

        lda #0
        sta c64lib.SPRITE_ENABLE
        jsr aux_copyEndGameData
        rts
    }

    commonOutry: {
        jsr playboardFadeIn
        waitFor()

        !:
            jsr io_scanJoy
            and #%00011111
            eor #%00011111
            sta io_oldJoy
            cmp #%00010000
        bne !-

        jsr playboardFadeOut
        waitFor()

        jsr stopCopper

        lda #0
        sta gameState
        lda #1
        sta gameTitleScreen

        jsr startRoomDirect
        jmp startLevel
    }
}

resetRoomStates: {
    ldx #0
    lda #$ff
    !:
        sta level_roomStates, x
        inx
        cpx #30
        bne !-
    rts
}

.macro checkCopperHalt() {
    lda gameState
    beq !+
        rts
    !:
    lda roomChange
    cmp #$ff
    beq !+
        rts
    !:
}

doEachFrameTop: {
    cld

    lda #%00000010
    sta c64lib.MEMORY_CONTROL
    
    lda currentColor
    ldx muralBehaviour          // the Glitch's blackout: the room in dark grey, Tony in grey
    cpx #7
    bne !+
        lda #11
    !:
    ldy muralDim                // no candle: the stone in medium grey
    beq !+
        lda #12
    !:
    sta c64lib.BG_COL_0
    lda currentColor
    cpx #7
    bne !+
        lda #12
    !:
    ldy muralDim                // and Tony in the same medium grey, as the owner asked
    beq !+
        lda #12
    !:
    ldx #0
    !:
        cpx #2
        beq skip
            sta c64lib.SPRITE_0_COLOR, x
        skip:
        inx
        cpx #7
    bne !-
    lda c64lib.SPRITE_2_COLOR   // sprite 7 is the buddy's backdrop now
    sta c64lib.SPRITE_7_COLOR
    lda buddyColourNow
    sta c64lib.SPRITE_5_COLOR
    sta c64lib.SPRITE_6_COLOR

    c64lib_debugBorderEnd()
    jsr playMusic
    c64lib_debugBorderStart()

    checkCopperHalt()

    c64lib_debugBorderStart()

    // clear collision register
    lda c64lib.SPRITE_2S_COLLISION

    jsr io_scanJoy
    ldx gameTitleScreen
    bne !+
        jsr buildVerb               // the build demo: down + fire lays or lifts a brick
        jsr dispatchPlayerCommand
        jmp !++
    !:
        jsr handleTitleScreenCommand
    !:

    jsr phys_transitState
    jsr onStateChange

    jsr phys_executeState
    jsr onStateChange // TODO another problem: execute state transits state

    lda playerDying
    bne noAction1
        jsr checkBGCollision // TODO big problem this must be run twice per a loop

        lda physPlayerBGCollision
        and #BG_CLSN_KILLING
        beq !+
            lda playerDying
            bne !+
                jsr killPlayer
        !:
    noAction1:

    // check for die request (main -> raster thread communication)
    lda playerDieRequest
    beq !+
        lda #0
        sta playerDieRequest
        jsr killPlayer
    !:

    // killing for snakes
    lda gameCheatState
    and #CHEAT_SPRITE_INVINCIBLE
    bne skipActorCollisions

    lda actorCollisions
    and #%00011000 // bats only - the buddy on sprites 5+6 is friendly
    beq !+
        // kill the enemy from the screen (only works for sprites)
        jsr findCollidingSprite
        cpx #MAX_SPRITES
        beq !+

        lda spriteMask, x
        eor #$ff
        and c64lib.SPRITE_ENABLE
        sta c64lib.SPRITE_ENABLE
    
        // update game state
        lda enemiesToObjects, x
        tax
        lda objMask, x
        eor #$ff
        ldx currentChamberNumber
        and level_roomStates, x
        sta level_roomStates, x

        // check potion in inventory
        ldy #SO_POTION
        jsr findItemInInventory
        cpx #INV_NOT_FOUND
        beq noPotion

        // use potion
        jsr blinkEyes
        jsr removeItemFromInventory

        // add points
        lda #<PTS_KILL
        ldx #>PTS_KILL
        jsr addGameScore

        lda c64lib.SPRITE_2S_COLLISION // clear collision register
        jmp !+

        // otherwise kill the player
        noPotion:
        lda playerDying
        bne !+
            jsr killPlayer

!:
    skipActorCollisions:

    // clear collisions
    lda #0
    sta actorCollisions

    // was in frame bottom
    lda playerDying
    bne !+
        jsr phys_blockMovement
        jsr checkBGCollision
    !:
    jsr onStateChange // and block movement transits state

    // update colX
    jsr phys_player2charX
    stx playerColX
    jsr phys_player2charY
    sty playerColY

    //  check bg object collisions
    lda physPlayerBGCollisionObj
    and #BG_CLSN_COLLECTIBLE
    beq !+
        jsr findObjCollision
        cpx #$ff
        beq !+
            lda objCollisionDetected
            cmp #$ff
            bne !+
                stx objCollisionDetected
    !:

    jsr checkForRoomChange

    // update enemy actors
    jsr runActors

    c64lib_debugBorderEnd()
    rts
}

findCollidingSprite: {
    ldx #0
    loop:
        lda actorCollisions
        and spriteMask, x
        bne !+
        inx
        cpx #MAX_SPRITES
        beq !+
        jmp loop
    !:
    rts
}

doEachFrameVisual: {
    cld
    // only visible stuff, to be executed out of the visible area
    jsr seq_play
    checkCopperHalt()

    c64lib_debugBorderStart()

    ldx #0
    jsr ani_animatePlayer
    ldx #0
    !:
        cpx enemiesCounter
        beq skip
        inx
        stx ZR_0
        jsr ani_animatePlayer
        ldx ZR_0
    jmp !-

    skip:

    c64lib_debugBorderStart()
    jsr updatePlayerPosition
    c64lib_debugBorderEnd()
    jsr playEffects
    jsr moveActors
    jsr buddyUpdate
    jsr actor_checkCollision

    c64lib_debugBorderEnd()
    rts
}

showEyes: {
    lda c64lib.SPRITE_MSB_X
    and #%01111111
    sta c64lib.SPRITE_MSB_X
    lda c64lib.SPRITE_ENABLE
    ora #%10000000
    sta c64lib.SPRITE_ENABLE

    lda eyesColor
    sta c64lib.SPRITE_7_COLOR
    lda #176
    sta c64lib.SPRITE_7_X
    lda #227
    sta c64lib.SPRITE_7_Y
    rts
}

hideEyes: {
    lda c64lib.SPRITE_ENABLE
    and #%01111111
    sta c64lib.SPRITE_ENABLE
    rts
}

blinkEyes: {
    lda #0
    sta fadeCounter
    seq_setUp(EYE_FADE_DELAY, 4, fadeInCallback, doNothing)
    rts
    fadeInCallback: {
        ldx fadeCounter
        lda fadeIn, x
        sta eyesColor
        inc fadeCounter
        rts
    }
}

killPlayer: {
    lda #1
    sta playerDying 
    jsr phys_die
    seq_setUp(DIE_DELAY, 10, doNothing, dieSequenceFinished)
    rts

    dieSequenceFinished: {
        jsr respawnPlayerPosition
        lda playerRespawnState
        cmp #STATE_JUMPING_LEFT
        bne !+
            lda #STATE_FALLING_DOWN_FACING_LEFT
        !:
        cmp #STATE_JUMPING_RIGHT
        bne !+
            lda #STATE_FALLING_DOWN_FACING_RIGHT
        !:
        jsr phys_forceTransitState
        jsr onStateChange
        jsr checkBGCollision
        lda #0
        sta playerDying
        lda gameCheatState
        and #CHEAT_INFINITE_LIVES
        bne infiniteLives
        dec gameLivesLeft
        bne !+
            lda #STATE_GAMEOVER
            sta gameState
        !:
        jsr drawLives
        infiniteLives:
        rts
    }
}

// out X -> found object id or $ff if none is found
findObjCollision: {
    clc
    lda playerColX
    adc #1
    sta normColLeft
    adc #3
    sta normColRight
    clc
    lda playerColY
    adc #1
    sta normRowTop
    adc #3
    sta normRowBottom

    ldx #0
    loop:
        ldy currentChamberNumber
        lda level_roomStates, y
        and objMask, x
        beq noCollision

        jsr getObjectControl
        and #%00001111
        cmp #SO_DOOR
        beq set4
        cmp #SO_DOORCODE
        beq set4
        lda #1
        sta addOtherSide.value
        
    continue:
        jsr getObjectPositionX
        sta objPos

        lda normColRight
        cmp objPos
        beq !+
            bcc noCollision     // Pla >> Obj
        !:

        jsr addOtherSide    // Obj := Obj + Epsilon

        lda normColLeft
        cmp objPos
        beq !+
            bcs noCollision             
        !:

        jsr getObjectPositionY
        sty objPos

        lda normRowBottom
        cmp objPos
        bcc noCollision

        jsr addOtherSide
        lda normRowTop

        cmp objPos

        beq !+
            bcs noCollision
        !:

        rts // found X -> object number
        noCollision:
            inx
            cpx staticObjectCount
            beq !+
                cpx #8
                bne loop
            !:
    ldx #$ff
    rts
    set4: {
        lda #4
        sta addOtherSide.value
        jmp continue
    }
    addOtherSide: {
        clc
        lda objPos
        adc value:#1
        sta objPos
        rts
    }
    normColLeft:    .byte 0
    normColRight:   .byte 0
    normRowTop:     .byte 0
    normRowBottom:  .byte 0
    objPos:         .byte 0
}

// in X -> obj id to be handled
handleObjCollision: {
    ldx objCollisionDetected
    jsr getObjectControl
    and #%00001111
    cmp #SO_KEY
    bne !+
        jmp handleKey
    !:
    cmp #SO_JEWEL
    bne !+
        jmp handleJewel
    !:
    cmp #SO_POTION
    bne !+
        jmp handlePotion
    !:
    cmp #SO_KEYCODE
    bne !+
        jmp handleKeyCode
    !:
    cmp #SO_SNAKE_L
    bne !+
        jmp handleSnake
    !:
    cmp #SO_SNAKE_R
    bne !+
        jmp handleSnake
    !:
    cmp #SO_DOOR
    bne !+
        jmp handleDoor
    !:
    cmp #SO_DOORCODE
    bne !+
        jmp handleDoorCode
    !:
    lda #$ff
    sta objCollisionDetected
    rts
    handleKey:
        txa
        pha
        jsr collectItemToInventory
        pla
        tax
        bcc !+
            lda #$ff
            sta objCollisionDetected
            jmp doNothing
        !:
        jmp wipeOut
    handleJewel:
        txa
        pha
        jsr collectItemToInventory
        lda #<PTS_JEWEL
        ldx #>PTS_JEWEL
        jsr addGameScore
        pla
        tax
        jmp wipeOut
    handlePotion:
        txa
        pha
        jsr collectItemToInventory
        bcc !+
            pla
            tax
            lda #$ff
            sta objCollisionDetected
            jmp doNothing
        !:
        lda #<PTS_POTION
        ldx #>PTS_POTION
        jsr addGameScore
        pla
        tax
        jmp wipeOut
    handleKeyCode:
        txa
        pha
        jsr collectItemToInventory
        pla
        tax
        bcc !+
            lda #$ff
            sta objCollisionDetected
            jmp doNothing
        !:
        jmp wipeOut
    handleSnake:
        txa
        pha
        // check potion in inventory
        ldy #SO_POTION
        jsr findItemInInventory
        cpx #INV_NOT_FOUND
        beq noPotion

        // use potion
        jsr blinkEyes
        jsr removeItemFromInventory

        // add points
        lda #<PTS_KILL
        ldx #>PTS_KILL
        jsr addGameScore

        jmp !+

        // otherwise kill the player
        noPotion:
        lda playerDying

        // TODO add cheat mode here!
        bne !+
            lda #1
            sta playerDieRequest
        !:

        pla
        tax
        jmp wipeOut
    handleDoor:
        txa
        pha
        ldy #SO_KEY
        jsr findItemInInventory
        cpx #INV_NOT_FOUND
        beq notFound
        jsr removeItemFromInventory
        pla
        tax
        jmp wipeOutDoor
    handleDoorCode:
        txa
        pha
        ldy #SO_KEYCODE
        jsr findItemInInventory
        cpx #INV_NOT_FOUND
        beq notFound
        jsr removeItemFromInventory
        pla
        tax
        jsr wipeOutDoor
        lda #STATE_ENDOFGAME
        sta gameState
        rts
    notFound:
        pla
        tax // deliberately takes next rts
    doNothing:
        rts

    wipeOutCommon: {
        // turn off object in the state
        ldy currentChamberNumber
        lda level_roomStates, y
        eor objMask, x
        sta level_roomStates, y

        // wipe out the object from screen
        lda #<wipeOutData
        sta MAIN_SOURCE_PTR
        lda #>wipeOutData
        sta MAIN_SOURCE_PTR + 1
        rts
    }
    wipeOut: {
        jsr wipeOutCommon

        jsr getObjectPositionY
        jsr getObjectPositionX

        jsr draw2x2m
        lda #$ff
        sta objCollisionDetected
        rts
    }
    wipeOutDoor: {
        jsr wipeOutCommon

        jsr getObjectPositionY
        sty storeY
        jsr getObjectPositionX
        sta storeX

        jsr draw2x2m
        lda storeX
        ldy storeY
        iny 
        iny
        jsr draw2x2m
        inc storeX
        inc storeX
        lda storeX
        ldy storeY
        jsr draw2x2m
        lda storeX
        ldy storeY
        iny
        iny
        jsr draw2x2m

        lda #$ff
        sta objCollisionDetected
        rts
        storeX: .byte 0
        storeY: .byte 0
    }
    wipeOutData: .fill 4, 0 // 2x2 wipeout block
}

initGameState: {
    lda #INITIAL_LIVES
    sta gameLivesLeft
    lda #$00
    sta gameScore
    sta gameScore + 1
    sta gameScore + 2
    sta gameInventory
    sta gameInventory + 1
    sta gameInventory + 2
    sta gameInventory + 3
    rts
}

// IN: A score low, ZR_0 score hi
addGameScore: {
    sed
    clc
    adc gameScore
    sta gameScore
    txa
    adc gameScore + 1
    sta gameScore + 1
    lda #0
    adc gameScore + 2
    sta gameScore + 2
    cld
    jmp drawScore
}

// in: X item to be removed
removeItemFromInventory: {
    loop:
        lda gameInventory + 1, x
        sta gameInventory, x
        inx
        cpx #4
    bne loop
    lda #0
    sta gameInventory + 3
    jsr drawInventory
    rts
}

// in: Y item code to be found
// out: X found potion or 4 if not found
findItemInInventory: {
    sty itemCode
    ldx #0
    loop:
        lda gameInventory, x
        cmp itemCode:#SO_POTION
        beq end
        inx
        cpx #4
        beq end
        jmp loop
    end:
    rts
}

// in: A item type; out: X found item or 4 if not found
findLastItemInInvetory: {
    sta item
    ldx #4
    loop:
        dex
        lda gameInventory, x
        cmp item:#SO_POTION
        bne !+
            rts
        !:
        cpx #0
    bne loop
    ldx #4
    rts
}

collectItemToInventory: {
    jsr blinkEyes
    jsr getObjectControl
    and #%00001111
    sta item
    cmp #SO_POTION
    bne !+
        jmp findAndCollect
    !:
    cmp #SO_KEY
    bne !+++
        jsr findAndCollect
        bcs !+
            rts
        !:
        lda #SO_POTION
        jsr findLastItemInInvetory
        cpx #4
        bne !+
            rts
        !:
        jsr removeItemFromInventory
        jmp findAndCollect
    !:
    cmp #SO_KEYCODE
    bne !+++
        jsr findAndCollect
        bcs !+
            rts
        !:
        lda #SO_POTION
        jsr findLastItemInInvetory
        cpx #4
        bne !+
            lda #SO_KEY
            jsr findLastItemInInvetory
            cpx #4
            bne !+
                rts
        !:
        jsr removeItemFromInventory
        jmp findAndCollect
    !:
    clc
    rts

    findAndCollect: {
        jsr findFreeSlot
        cpx #4
        beq !+
            jmp collect
        !:
        sec
        rts
    }
    findFreeSlot: {
        ldx #0
        loop:
            lda gameInventory, x
            bne !+
                rts
            !:
            inx
            cpx #4
        bne loop
        rts
    }
    collect: {
        lda item
        sta gameInventory, x
        jsr drawInventory
        clc
        rts
    }
    item: .byte 0
}

runActors: {
    ldx #0
    cpx enemiesCounter
    bne !+
        rts
    !:

    loop:
        stx ZR_0
        lda enemiesToObjects, x
        tax
        jsr getObjectControl
        ldx ZR_0
        and #%00001111
        cmp #SO_SKULL
        bne !+
            jmp runSkull
        !:
        cmp #SO_BAT
        bne !+
            jmp runBat
        !:
        cmp #SO_BAT_VERTICAL
        bne !+
            jmp runSkull
        !:
        cmp #SO_DEAD
        bne !+
            jmp runDead
        !:
        continue:
        inx
        cpx enemiesCounter
    bne loop

    rts

    runSkull: {
        lda actorValue2, x
        bne !+
            jmp continue
        !:

        jsr incrementCounter
        lda actorModes
        and spriteMask, x
        beq !+
            lda #STEP_SKULLx1
            sta speed1
            sta speed2
            jmp !++
        !:
            lda #STEP_SKULLx2
            sta speed1
            sta speed2
        !:
        lda actorDirections
        and spriteMask, x
        beq moveDown
        // move up
            sec
            lda actorPositionY, x
            sbc speed1:#STEP_SKULLx2
            sta actorPositionY, x
            jmp continue
        moveDown:
            clc
            lda actorPositionY, x
            adc speed2:#STEP_SKULLx2
            sta actorPositionY, x
            jmp continue
    }

    // this one uses ZR_1 as additional accumulator (ZR_1 stores next Y adjustment value)
    runBat: {
        // set up path reading
        lda actorValue2, x
        stx storeX
        tax
        lda pathLengths, x
        sta fetchNext.cmpPathLength
        sta updateDirection.value
        lda pathsPtrsLo, x
        sta readPath.address
        lda pathsPtrsHi, x
        sta readPath.address + 1
        ldx storeX
        jsr updateDirection

        // check if decrunch
        lda actorDepackCounter, x
        beq nextForDecrunch
            // decrunch
            lda actorDepackValue, x
            sta ZR_1
            dec actorDepackCounter, x
            bne !+
                jmp nextForDecrunch
            !:
            jmp updatePositions

        nextForDecrunch:
            jsr fetchNext

        updatePositions:

        lda direction
        beq !+
            sec
            lda actorPositionY, x
            sbc ZR_1
            jmp !++
        !:
            clc
            lda ZR_1
            adc actorPositionY, x
        !:
        sta actorPositionY, x

        lda actorDirections
        and spriteMask, x
        beq moveRight
        // move left
            sec
            lda actorPositionX, x
            sbc #STEP_BAT
            sta actorPositionX, x
            jmp !+
        moveRight:
            clc
            lda actorPositionX, x
            adc #STEP_BAT
            sta actorPositionX, x
        !:
        jmp continue
        // vars
        storeX:     .byte 0
        direction:  .byte 0

        // subs
        readPath: {
            lda address:$ffff, x
            rts
        }

        fetchNext: {
            lda enemiesCounters, x
            cmp cmpPathLength:#$ff
            bne readNext
                lda actorDirections
                eor spriteMask, x
                sta actorDirections
                stx storeX
                lda actorDirections
                and spriteMask, x
                bne !+
                    txa
                    tay
                    iny
                    ldx #ANIM_BAT_RIGHT
                    jsr ani_setAnimation
                    jmp cont
                !:
                    txa
                    tay
                    iny
                    ldx #ANIM_BAT_LEFT
                    jsr ani_setAnimation
                cont:
                    ldx storeX
                    jsr updateDirection
                    jsr incEnemies // hack, but it works
                    jsr incEnemies
            readNext:
                stx storeX
                lda enemiesCounters, x
                jsr incEnemies
                jsr incEnemies
                tax
                jsr readPath
                ldy storeX
                sta actorDepackCounter, y
                inx
                jsr readPath
                sta actorDepackValue, y
                sta ZR_1
                ldx storeX
            rts
        }
        incEnemies: {
            instr:inc enemiesCounters, x
            rts
        }
        updateDirection: {
            lda actorDirections
            and spriteMask, x
            sta direction
            bne !+
                // right
                lda #INC_ABSX
                sta incEnemies.instr
                lda value:#0
                sta fetchNext.cmpPathLength
                jmp !++
            !:
                // left
                lda #DEC_ABSX
                sta incEnemies.instr
                lda #(-2) // hack, but it works!
                sta fetchNext.cmpPathLength
            !:
            rts
        }
    }

    runDead: {
        jsr incrementCounter
        bcc !++
            // direction changed
            stx storeX
            lda actorDirections
            and spriteMask, x
            bne !+
                txa
                tay
                iny
                ldx #ANIM_DEADMAN_RIGHT
                jsr ani_setAnimation
                jmp cont
            !:
                txa
                tay
                iny
                ldx #ANIM_DEADMAN_LEFT
                jsr ani_setAnimation
            cont:
                ldx storeX
        !:
        lda actorDirections
        and spriteMask, x
        beq moveRight
        // move left
            sec
            lda actorPositionX, x
            sbc #STEP_DEADMAN
            sta actorPositionX, x
            jmp continue
        moveRight:
            clc
            lda actorPositionX, x
            adc #STEP_DEADMAN
            sta actorPositionX, x
            jmp continue
        // vars
        storeX: .byte 0
    }

    incrementCounter: 
        clc
        inc enemiesCounters, x
        lda enemiesCounters, x
        cmp actorValue2, x
        bne !+
            lda #0
            sta enemiesCounters, x
            lda actorDirections
            eor spriteMask, x
            sta actorDirections
            sec
        !:
        rts
}

moveActors: {
    ldx #0
    cpx enemiesCounter
    bne !+
        rts
    !:

    loop:
        lda spriteYPos.lo, x
        sta posYAddr
        lda spriteYPos.hi, x
        sta posYAddr + 1
        lda spriteXPos.lo, x
        sta posXAddr
        lda spriteYPos.hi, x
        sta posXAddr + 1
        
        lda actorPositionY, x
        sta posYAddr:$ffff
        lda actorPositionX, x
        asl
        sta ZR_0
        jsr setMSB
        lda ZR_0
        sta posXAddr:$ffff
        inx
        cpx enemiesCounter
    bne loop
    rts

    setMSB: {
        bcc !+
            lda c64lib.SPRITE_MSB_X
            ora spriteMask, x
            sta c64lib.SPRITE_MSB_X
            rts
        !:
        lda spriteMask, x
        eor #$ff
        and c64lib.SPRITE_MSB_X
        sta c64lib.SPRITE_MSB_X
        rts
    }
    spriteXPos: .lohifill ANI_MAX_ACTORS, c64lib.SPRITE_3_X + 2*i
    spriteYPos: .lohifill ANI_MAX_ACTORS, c64lib.SPRITE_3_Y + 2*i
}

spriteMask: .byte %00001000, %00010000, %00100000, %01000000, %10000000
objMask:    .byte 1, 2, 4, 8, 16, 32, 64, 128

onStateChange: {
    lda _phys_stateChange
    beq !+
        ldx physPlayerAnimation
        ldy #ANI_ACTOR_PLAYER
        jsr ani_setAnimation
        lda #0
        sta _phys_stateChange
    !:
    rts
}

doNothing: {
    rts
}

doTriggerWait: {
    lda #0
    sta waitFor
    rts
}

drawScreen: {
    jsr drawDashboard
    jsr drawLives
    jsr drawScore
    jsr drawInventory
    rts
}

initRoom: {
    lda level_startRoom
    sta currentChamberNumber
    lda level_startState
    sta phys_initialState
    sta playerRespawnState
    lda #$ff
    sta roomChange
    sta objCollisionDetected
    sta drawCommand
    lda #0
    sta playerDieRequest // TODO should it be there?
    sta actorCollisions
    sta gameState
    rts
}

chooseRoom: {
    ldx currentChamberNumber
    // set chamber map
    lda level_roomPtr.lo, x
    sta chamberMapAddr
    lda level_roomPtr.hi, x
    sta chamberMapAddr + 1
    // set static objects
    lda level_objectControlPtr.lo, x
    sta getObjectControl.address
    sta setObjectControl.address
    lda level_objectControlPtr.hi, x
    sta getObjectControl.address + 1
    sta setObjectControl.address + 1

    lda level_objectPositionXPtr.lo, x
    sta getObjectPositionX.address
    lda level_objectPositionXPtr.hi, x
    sta getObjectPositionX.address + 1

    lda level_objectPositionYPtr.lo, x
    sta getObjectPositionY.address
    lda level_objectPositionYPtr.hi, x
    sta getObjectPositionY.address + 1
    
    lda level_objectSizes, x
    sta staticObjectCount
    // set additional moveable object data
    lda level_movableObjectValue2Ptr.lo, x
    sta getObjectValue2.address
    lda level_movableObjectValue2Ptr.hi, x
    sta getObjectValue2.address + 1

    rts
}

checkForRoomChange: {
    ldx currentChamberNumber
    lda #ROOM_NORTH_LIMIT
    cmp physPlayerY
    bcs transitN
    lda physPlayerY
    cmp #224                    // the build demo: only the ladder down the floor reaches this
    bcs transitS
    lda physPlayerX + 1
    bne checkE
        lda #ROOM_WEST_LIMIT
        cmp physPlayerX
        bcs transitW
        rts
    checkE:
        lda physPlayerX
        cmp #ROOM_EAST_LIMIT
        bcs transitE
    rts
    transitN: {
        lda #ROOM_TRANSIT_DIRECTION_NORTH
        sta roomChangeDirection
        lda level_roomExitsN, x
        jmp end
    }
    transitE: {
        lda #ROOM_TRANSIT_DIRECTION_EAST
        sta roomChangeDirection
        lda level_roomExitsE, x
        jmp end
    }
    transitS: {
        lda #ROOM_TRANSIT_DIRECTION_SOUTH
        sta roomChangeDirection
        lda level_roomExitsS, x
        jmp end
    }
    transitW: {
        lda #ROOM_TRANSIT_DIRECTION_WEST
        sta roomChangeDirection
        lda level_roomExitsW, x
        jmp end
    }
    end: 
    sta roomChange
    rts
}

showEnemies: {
    lda c64lib.SPRITE_ENABLE
    and #%10000111
    sta c64lib.SPRITE_ENABLE
    lda enemiesCounter
    cmp #0
    bne !+
        rts
    !:
    ldx #0
    loop:
        stx ZR_0
        lda enemiesToObjects, x
        tax

        cpx #8
        bcs !+
        ldy currentChamberNumber
        lda level_roomStates, y
        and objMask, x
        bne !+
            jmp continueHidden
        !:
        jsr getObjectControl
        and #%00001111
        cmp #SO_SKULL
        bne !+
            jmp doSkull
        !:
        cmp #SO_BAT_VERTICAL
        bne !+
            jmp doBatVertical
        !:
        cmp #SO_DEAD
        bne !+
            jmp doDeadman
        !:
        cmp #SO_BAT
        bne !+
            jmp doBat
        !:
        continue:
        ldx ZR_0
        lda c64lib.SPRITE_ENABLE
        ora spriteMask, x
        sta c64lib.SPRITE_ENABLE
        continueHidden:
        ldx ZR_0
        inx
        cpx enemiesCounter
    bne loop

    rts

    doSkull: {
        ldy ZR_0
        iny
        ldx #ANIM_SKULL
        jsr ani_setAnimation
        jmp continue
    }

    doBatVertical: {
        ldy ZR_0
        iny
        ldx #ANIM_BAT_VERTICAL
        jsr ani_setAnimation
        jmp continue
    }

    doDeadman: {
        ldy ZR_0
        iny
        ldx #ANIM_DEADMAN_RIGHT
        jsr ani_setAnimation
        jmp continue
    }

    doBat: {
        ldy ZR_0
        lda #0
        sta actorDepackValue, y
        sta actorDepackCounter, y
        iny
        ldx #ANIM_BAT_RIGHT
        jsr ani_setAnimation
        jmp continue
    }
}

// ---------------------------------------------------------------------
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
.label BUDDY_HOP_LEN  = 26  // Tony's own jump, measured: 26 frames to a 23-pixel apex
.label BUDDY_HOP_COOL = 20
.label DANCE_RISE     = 6   // ENV3 must climb this much in one frame to count as a hit
.label DANCE_SLIDE    = 6   // pixels he side-steps on every note (one per frame)
.label ECHO_DELAY     = 200 // frames behind the player (4 s); the ring holds 256
.label MIRROR_SUM     = 344 // twice the centre line between the pillars (64..280)
.label SHY_FLEE_AT    = 56  // closer than this: he runs
.label SHY_CALM_AT    = 110 // farther than this: he creeps back
.label SHY_BOLT_AT    = 16  // cornered and the player this close: he bolts straight past him
.label SLEEP_WAKE_AT  = 48  // an approach inside this wakes him
.label SLEEP_AWAKE    = 150 // half-frames awake before he dozes off again (300 frames, 6 s)

buddyInit: {
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
    lda currentChamberNumber        // the build demo: the Shadow stays in the room below
    beq !+
        lda c64lib.SPRITE_ENABLE
        and #%00011111
        sta c64lib.SPRITE_ENABLE
        rts
    !:
    // keep the clone enabled and green (self-healing every frame)
    lda c64lib.SPRITE_ENABLE
    ora #%11100000              // 5+6 the buddy, 7 his backdrop
    sta c64lib.SPRITE_ENABLE
    lda c64lib.SPRITE_EXPAND_Y
    ora #%10000000              // the backdrop is Y-expanded, like the player's
    sta c64lib.SPRITE_EXPAND_Y
    lda c64lib.SPRITE_2_COLOR   // and wears the player's backdrop colour
    sta c64lib.SPRITE_7_COLOR
    lda buddyColourNow          // the buddy's colour: the parameter block's, or the Glitch's cycle
    sta c64lib.SPRITE_5_COLOR
    sta c64lib.SPRITE_6_COLOR

    // decide: which mechanic runs this frame. Follow is below; the others
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
        beq stepLeft
            jsr buildBlockedRight   // the build demo: a placed brick is a wall to him
            bcs noMove
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
            jsr buildBlockedLeft
            bcs noMove
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

    // hop when the decide part asked for one
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
            sta wantHop
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
    sta c64lib.SPRITE_7_Y
    clc
    adc #21
    sta c64lib.SPRITE_6_Y

    // pose: hop / walk cycle / breathing idle, in the facing direction
    lda buddyHop
    ora buddyJumpPose
    beq notHopping
        lda buddyFacing
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
        jmp setPose
    notHopping:
    lda buddyMoving
    ora buddyPoseMoving
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
            lda walkRightAnimationBG, x
            sta buddyBg
            lda walkRightAnimationTL, x
            pha
            lda walkRightAnimationBL, x
            tax
            pla
            jmp setPose
        walkL:
            lda walkLeftAnimationBG, x
            sta buddyBg
            lda walkLeftAnimationTL, x
            pha
            lda walkLeftAnimationBL, x
            tax
            pla
            jmp setPose
    standing:
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
            lda idlingRightAnimationBG, x
            sta buddyBg
            lda idlingRightAnimationTL, x
            pha
            lda idlingRightAnimationBL, x
            tax
            pla
            jmp setPose
        idleL:
            lda idlingLeftAnimationBG, x
            sta buddyBg
            lda idlingLeftAnimationTL, x
            pha
            lda idlingLeftAnimationBL, x
            tax
            pla
            jmp setPose
    setPose:
        sta SCREEN_MEM_0 + 1016 + 5
        stx SCREEN_MEM_0 + 1016 + 6
        lda buddyBg
        sta SCREEN_MEM_0 + 1016 + 7
    rts

    // locals
    mag:         .byte 0
    buddyBg:     .byte 0
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
// Tony's jump, frame by frame (physPlayerY deltas measured on minimal64): the buddy jumps exactly as he does
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
buddyDistance: {
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
}

// Crouch when the player crouches (Follow and Mirror); the act part shows it
// once he stands still.
playerCrouch: {
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
}

// Put him at `target` (Echo, Mirror): facing and the walking pose follow from
// the move; the act part does not step, it only writes the sprite.
buddyPlace: {
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
}

// The Sleeper: dozes until the player comes close, is awake (and Follow) for
// SLEEP_AWAKE half-frames, then dozes off again. Returns A = 0 awake, 8 dozing.
sleeperDecide: {
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
}

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
glitchTick: {
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
}

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
.label SID_IMAGE = $A474
.label INTRO_IMAGE = $8452
buddyDecide: {
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
}
echoLo:   .fill 256, 0
echoHi:   .fill 256, 0
echoY:    .fill 256, BUDDY_FLOOR_Y
echoAnim: .fill 256, ANIM_IDLING_RIGHT
// the player's animation number -> pose * 4 + facing (0 left, 1 right, 2 keep):
// walk L/R, duck L/R, idle L/R, ladder, jump L/R, ladder stop, death L/R,
// skull, bat, deadman L/R, bat L/R, quick duck L/R
echoPose: .byte 4, 5, 8, 9, 0, 1, 2, 12, 13, 2, 0, 1, 2, 2, 0, 1, 2, 2, 8, 9

// ---------------------------------------------------------------------
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
    bne !+
        lda #1                      // no candle: remembered for the dim room
        sta muralDim
        jmp candleDone
    !:
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
        lda #0
        inkLoop:
            sta c64lib.COLOR_RAM + 23*40 + 27, x
            inx
            cpx #8
            bne inkLoop
    digitsInked:
    // the build demo: the ladder. Its slot k from the seed (byte 30, bits 2-5), moved off the candle's
    // niche; the room below hangs it from the ceiling down to row LADDER_BOTTOM, the room above has it
    // as the hole in its floor, rows 23-24 (the game's own maps run a ladder through the floor rows only:
    // Tony stands in its top cell and steps sideways onto the floor). Map codes $7C $7D, two columns wide.
    lda muralSeed + 30
    lsr
    lsr
    and #15
    cmp #15
    bne !+
        lda #14
    !:
    sta buildLadderK
    lda muralDim
    bne ladderColumn            // no candle, nothing to avoid
    lda candleLeft              // 5 + 2 kc
    sec
    sbc #5
    lsr
    sta buildLadderTmp          // kc
    lda buildLadderK
    sec
    sbc buildLadderTmp
    clc
    adc #1
    cmp #3
    bcs ladderColumn            // more than a slot apart
        lda #14
        sec
        sbc buildLadderK        // mirror it
        sta buildLadderK
        sec
        sbc buildLadderTmp
        clc
        adc #1
        cmp #3
        bcs ladderColumn
            lda buildLadderK    // the candle in the middle: four slots along
            clc
            adc #4
            cmp #15
            bcc !+
                sbc #15
            !:
            sta buildLadderK
    ladderColumn:
    lda buildLadderK
    asl
    clc
    adc #5
    sta buildLadderCol
    lda currentChamberNumber
    bne ladderAbove
        ldy #0
        ladderRows:
            ldx buildLadderCol
            lda #$7C
            jsr buildWriteCell
            inx
            lda #$7D
            jsr buildWriteCell
            iny
            cpy #(LADDER_BOTTOM + 1)
        bne ladderRows
        jmp ladderDone
    ladderAbove:
        ldy #23                 // the floor rows only, as the game's own maps do it: its top cell is the floor row
        ladderFloor:
            ldx buildLadderCol
            lda #$7C
            jsr buildWriteCell
            inx
            lda #$7D
            jsr buildWriteCell
            iny
            cpy #25
        bne ladderFloor
    ladderDone:
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
    lda #0                      // the build demo: no bats
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

nextColorScheme: {
    lda c64lib.CONTROL_1
    and #%11101111
    sta c64lib.CONTROL_1
    ldx colorScheme
    inx
    cpx #MAX_COLOR_SCHEME
    bne !+
        ldx #0
    !:
    stx colorScheme
    lda colorLights, x
    sta currentColor
    sta fadeIn
    lda colorDarks, x
    sta fadeIn + 3
    sta fadeOut
    jsr setColors
    lda c64lib.CONTROL_1
    ora #%00010000
    sta c64lib.CONTROL_1
    rts
}

changeRoomIfNeeded: {
    lda roomChange
    cmp #$ff
    bne !+
        jmp end
    !:
        lda #$ff
        sta playerColX
        // redraw room
        lda currentChamberNumber
        cmp #29 // title screen
        bne !+
            jsr startGame
        !:
        lda roomChange
        sta currentChamberNumber
        jsr chooseRoom

        jsr playboardFadeOut
        waitFor()

        
        jsr drawPlayfieldFading
        // set up enemies
        jsr hideEnemiesFaces
        jsr moveActors
        jsr showEnemies
        // reposition Tony
        lda roomChangeDirection
        cmp #ROOM_TRANSIT_DIRECTION_NORTH
        bne !+
            lda #216                    // the build demo: arriving from below, on the ladder in the floor
            sta physPlayerY
            jmp updatePosition
        !:
        cmp #ROOM_TRANSIT_DIRECTION_SOUTH
        bne !+
            lda #ROOM_TRANSIT_SOUTH
            sta physPlayerY
            jmp updatePosition
        !:
        cmp #ROOM_TRANSIT_DIRECTION_EAST
        bne !+
            lda #<ROOM_TRANSIT_EAST
            sta physPlayerX
            lda #>ROOM_TRANSIT_EAST
            sta physPlayerX + 1
            jmp updatePosition
        !:
        cmp #ROOM_TRANSIT_DIRECTION_WEST
        bne !+
            lda #<ROOM_TRANSIT_WEST
            sta physPlayerX
            lda #>ROOM_TRANSIT_WEST
            sta physPlayerX + 1
            jmp updatePosition
        !:
        jmp endTransit
        updatePosition: {
            jsr physResetActorPosition
            jsr updatePlayerPosition
        }

        lda physPlayerX
        sta playerRespawnPositionX
        lda physPlayerX + 1
        sta playerRespawnPositionX + 1
        lda physPlayerY
        sta playerRespawnPositionY
        lda physPlayerState
        sta playerRespawnState

        jsr playboardFadeIn
        waitFor()

        endTransit:
        lda #$ff
        sta roomChange
    end: rts
}

hideEnemiesFaces: {
    ldx #3
    lda #EMPTY_SPRITE
    !:
        sta SCREEN_MEM_0 + 1024 - 8, x
        inx
        cpx #8
    bne !-
    rts
}

initStaticObjectsCharset: {
    .for (var i = 0; i < 4; i++) {
        copyStaticCharset(level_potion + i*8, SOC_POTION + i)
        copyStaticCharset(level_jewel + i*8, SOC_JEWEL + i)
        copyStaticCharset(level_keycode + i*8, SOC_KEYCODE + i)
        copyStaticCharset(level_key + i*8, SOC_KEY + i)
        copyStaticCharset(level_snakeLeft + i*8, SOC_SNAKE_L + i)
        copyStaticCharset(level_snakeRight + i*8, SOC_SNAKE_R + i)
    }
    .for (var i = 0; i < 10; i++) {
        copyStaticCharset(level_pikes + i*8, SOC_PIKES + i)
    }
    .for (var i = 0; i < 16; i++) {
        copyStaticCharset(level_door + i*8, SOC_DOOR + i)
        copyStaticCharset(level_doorcode + i*8, SOC_DOORCODE + i)
    }
    copyStaticCharset(level_fire, SOC_FLAME_1)
    copyStaticCharset(level_fire + 8, SOC_FLAME_1 + 1)
    copyStaticCharset(level_fire + 32, SOC_FLAME_2)
    copyStaticCharset(level_fire + 32 + 8, SOC_FLAME_2 + 1)
    rts
}

initStonesCharset: {
    .for (var i = 0; i < 44; i++) {
        copyStaticCharset(level_stones + i*8, SOC_STONE + i)
    }
    lda gameCheatState
    and #CHEAT_STONE_INVINCIBLE
    bne !+
        jmp initStonesMaterials
    !:
}

initStonesMaterials: {
    ldx #SOC_STONE
    lda #0
    !:
        sta roomMaterialsBuffer, x
        inx
        cpx #(SOC_STONE + 44)
    bne !-
    lda gameCheatState
    and #CHEAT_STONE_INVINCIBLE
    bne !+
        lda #BG_CLSN_WALL
        ldx #(SOC_STONE + 12)
        sta roomMaterialsBuffer, x
        inx
        lda #BG_CLSN_KILLING
        jsr setMaterials
        inx
        lda #BG_CLSN_WALL
        sta roomMaterialsBuffer, x


        lda #BG_CLSN_WALL
        ldx #(SOC_STONE + 16)
        sta roomMaterialsBuffer, x
        inx
        lda #BG_CLSN_KILLING
        jsr setMaterials
        inx
        lda #BG_CLSN_WALL
        sta roomMaterialsBuffer, x

        lda #BG_CLSN_WALL
        ldx #(SOC_STONE + 34)
        sta roomMaterialsBuffer, x
        inx
        lda #BG_CLSN_KILLING
        jsr setMaterials
        inx
        lda #BG_CLSN_WALL
        sta roomMaterialsBuffer, x

        // chains 
        lda #BG_CLSN_KILLING
        ldx #(SOC_STONE + 0)
        jsr setMaterials
        inx
        jsr setMaterials
        ldx #(SOC_STONE + 20)
        jsr setMaterials
    !:
    rts
setMaterials: 
    sta roomMaterialsBuffer, x
    inx
    sta roomMaterialsBuffer, x
    rts
}

initStaticObjectsMaterials: {
    // killing for pikes
    lda gameCheatState
    and #CHEAT_PIKES_INVINCIBLE
    bne !++
        ldx #(SOC_PIKES + 2)
        lda #BG_CLSN_KILLING
        !:
            sta roomMaterialsBuffer, x
            inx
            cpx #(SOC_PIKES + 10)
        bne !-
    !:
    // killing for flames
    lda #BG_CLSN_KILLING
    ldx #(SOC_FLAME_1 + 2)
    sta roomMaterialsBuffer, x
    inx
    sta roomMaterialsBuffer, x
    ldx #(SOC_FLAME_2 + 2)
    sta roomMaterialsBuffer, x
    inx
    sta roomMaterialsBuffer, x
    // killing for snakes
    lda gameCheatState
    // and #CHEAT_SNAKE_INVINCIBLE
    and #CHEAT_SPRITE_INVINCIBLE
    bne !++
        ldx #(SOC_SNAKE_R + 2)
        lda #BG_CLSN_COLLECTIBLE
        !:
            sta roomMaterialsBuffer, x
            sta roomMaterialsBuffer + 4, x
            inx
            cpx #(SOC_SNAKE_R + 4)
        bne !-
    !:
    // blocking for doors
    lda gameCheatState
    and #CHEAT_PASS_THRU_DOORS
    bne !+++
        ldx #SOC_DOOR
        lda #(BG_CLSN_COLLECTIBLE)
        !:
            sta roomMaterialsBuffer, x
            inx
            cpx #(SOC_DOOR + 16)
        bne !-
        ldx #SOC_DOOR
        lda #(BG_CLSN_WALL + BG_CLSN_COLLECTIBLE)
        !:
            inx
            sta roomMaterialsBuffer, x
            inx
            sta roomMaterialsBuffer, x
            inx
            inx
            cpx #(SOC_DOOR + 16)
        bne !-
    !:
    // blocking for door code
    ldx #SOC_DOORCODE
    lda #(BG_CLSN_COLLECTIBLE)
    !:
        sta roomMaterialsBuffer, x
        inx
        cpx #(SOC_DOORCODE + 16)
    bne !-
    // collectibles
    ldx #SOC_KEY
    lda #BG_CLSN_COLLECTIBLE
    !:
        sta roomMaterialsBuffer, x
        inx
        cpx #(SOC_JEWEL + 4)
    bne !-
    ldx #SOC_KEYCODE
    lda #BG_CLSN_COLLECTIBLE
    !:
        sta roomMaterialsBuffer, x
        inx
        cpx #(SOC_KEYCODE + 4)
    bne !-
    ldx #SOC_POTION
    lda #BG_CLSN_COLLECTIBLE
    !:
        sta roomMaterialsBuffer, x
        inx
        cpx #(SOC_POTION + 4)
    bne !-

    rts
}

.macro copyStaticCharset(obj, charsetPos) {
    lda #<obj
    sta SOURCE_PTR
    lda #>obj
    sta SOURCE_PTR + 1
    ldx #charsetPos
    jsr copyStaticCharsetDest
}

copyStaticCharsetDest: {
    lda targetCharset.lo, x
    sta DEST_PTR
    lda targetCharset.hi, x
    sta DEST_PTR + 1
    jmp copyBitmapChar
}

decodeRoom: {
    ldx currentChamberNumber
    lda level_usedCharsCount, x
    sta comparePrt
    lda level_usedCharsPtr.lo, x
    sta unpackSourcePtr
    lda level_usedCharsPtr.hi, x
    sta unpackSourcePtr + 1

    ldx #0
    unpackCharMapperLoop:
        ldy unpackSourcePtr:$ffff, x // Y - original char code, X - new char code
        txa
        sta roomCharsDecodingBuffer, y
        // translate materials
        lda materials, y
        sta roomMaterialsBuffer, x
        // copy character data
        lda sourceCharset.lo, y
        sta SOURCE_PTR
        lda sourceCharset.hi, y
        sta SOURCE_PTR + 1

        lda targetCharset.lo, x
        sta DEST_PTR
        lda targetCharset.hi, x
        sta DEST_PTR + 1

        jsr copyBitmapChar

        inx
        cpx comparePrt:#00
    bne unpackCharMapperLoop
    rts
}

translateRoom: {
    ldx #0
    loop:
        .for (var i = 0; i <= 4; i++) 
        {
            ldy SCREEN_MEM_0 + i*200, x
            lda roomCharsDecodingBuffer, y
            sta SCREEN_MEM_0 + i*200, x
        }
        inx
        cpx #200
    bne loop
    rts
}

playboardFadeIn: {
    lda #2
    sta fadeCounter
    lda #1
    sta waitFor
    seq_setUp(FADE_DELAY, 3, fadeInCallback, doTriggerWait)
    rts
    fadeInCallback: {
        ldx fadeCounter
        lda fadeIn, x
        sta currentColor
        dec fadeCounter
        rts
    }
}

playboardFadeOut: {
    lda #2
    sta fadeCounter
    lda #1
    sta waitFor
    seq_setUp(FADE_DELAY, 3, fadeOutCallback, doTriggerWait)
    rts
    fadeOutCallback: {
        ldx fadeCounter
        lda fadeOut, x
        sta currentColor
        dec fadeCounter
        rts
    }
}

drawDashboard: grab_drawDashboard(dashboardMap, copyLargeMemForward)

drawLives: {
    ldx #0
    ldy colorScheme
    !:
        lda #DASHBOARD_LIFE_CHAR
        sta SCREEN_MEM_1 + 20*40 + DASHBOARD_LIFE_INDICATOR_POS, x
        lda colorBright, y
        cpx gameLivesLeft
        bcc !+
            lda colorDimmed, y
        !:
        sta c64lib.COLOR_RAM + 20*40 + DASHBOARD_LIFE_INDICATOR_POS, x
        inx
        cpx #DASHBOARD_MAX_LIVES
    bne !--
    rts
}

drawInventory: {
    ldx colorScheme
    lda colorBright, x
    sta setBrightColor.value
    lda colorLights, x
    sta setLightColor.value
    ldx #0
    stx ptr
    loop:
        lda gameInventory, x
        cmp #SO_KEY
        bne !+
            lda #<key
            sta fetchSourceChar.address
            lda #>key
            sta fetchSourceChar.address + 1
            jsr setBrightColor
            jmp next
        !:
        cmp #SO_POTION
        bne !+
            lda #<potion
            sta fetchSourceChar.address
            lda #>potion
            sta fetchSourceChar.address + 1
            jsr setBrightColor
            jmp next
        !:
        cmp #SO_KEYCODE
        bne !+
            lda #<keyCode
            sta fetchSourceChar.address
            lda #>keyCode
            sta fetchSourceChar.address + 1
            jsr setBrightColor
            jmp next
        !:
        lda #<empty
        sta fetchSourceChar.address
        lda #>empty
        sta fetchSourceChar.address + 1
        jsr setLightColor
        next:
            sta color
            txa
            pha
            ldx ptr

            ldy #0
            jsr fetchSourceChar
            sta SCREEN_MEM_1 + 40*20 + DASHBOARD_INVENTORY_START_CHAR, x
            lda color
            sta c64lib.COLOR_RAM + 40*20 + DASHBOARD_INVENTORY_START_CHAR, x
            inx
            iny
            jsr fetchSourceChar
            sta SCREEN_MEM_1 + 40*20 + DASHBOARD_INVENTORY_START_CHAR, x
            lda color
            sta c64lib.COLOR_RAM + 40*20 + DASHBOARD_INVENTORY_START_CHAR, x
            dex
            iny
            jsr fetchSourceChar
            sta SCREEN_MEM_1 + 40*20 + DASHBOARD_INVENTORY_START_CHAR1, x
            lda color
            sta c64lib.COLOR_RAM + 40*20 + DASHBOARD_INVENTORY_START_CHAR1, x
            inx
            iny
            jsr fetchSourceChar
            sta SCREEN_MEM_1 + 40*20 + DASHBOARD_INVENTORY_START_CHAR1, x
            lda color
            sta c64lib.COLOR_RAM + 40*20 + DASHBOARD_INVENTORY_START_CHAR1, x

            clc
            lda ptr
            adc #3
            sta ptr

            pla
            tax
        inx
        cpx #4
    beq !+
    jmp loop
    !:
    rts

    fetchSourceChar: {
        lda address:$ffff, y
        rts
    }
    setBrightColor: {
        lda value:#0
        rts
    }
    setLightColor: {
        lda value:#0
        rts
    }
    empty:      .byte 132, 133, 138, 139
    keyCode:    .byte 155, 156, 157, 158
    potion:     .byte 136, 137, 142, 143
    key:        .byte 134, 135, 140, 141
    ptr:        .byte 0
    color:      .byte 0
}

drawScore: {
    ldx #0
    ldy colorScheme
    lda colorDimmed, y
    sta ZR_0
    .for(var i = 0; i < 3; i++) {
        lda gameScore + 2 - i
        lsr
        lsr
        lsr
        lsr
        pha
        beq !+
            lda colorBright, y
            sta ZR_0
        !:
        pla
        jsr drawDigit
        
        lda gameScore + 2 - i
        and #%00001111
        pha
        beq !+
            lda colorBright, y
            sta ZR_0
        !:
        pla
        jsr drawDigit
    }
    rts
    drawDigit: 
        clc
        adc #DASHBOARD_NUMBER_START_CHAR
        sta SCREEN_MEM_1 + 20*40 + DASHBOARD_SCORE_INDICATOR_POS, x
        lda ZR_0
        sta c64lib.COLOR_RAM + 20*40 + DASHBOARD_SCORE_INDICATOR_POS, x
        inx
        rts
}

drawPlayfield: {
    ldy colorScheme
    lda colorDarks, y
    sta c64lib.BG_COL_0
    jsr drawPlayfieldFading
    ldy colorScheme
    lda colorLights, y
    sta c64lib.BG_COL_0
    sta currentColor
    rts
   
}

drawPlayfieldFading: {
    jsr decodeRoom
    jsr _draw_playfield
    jsr muralStamp   // the back wall, from the seed
    jsr translateRoom
    jsr buildInit               // the build demo
    lda currentChamberNumber
    // TODO: currently rooms with stones are hardcoded in this place!
    cmp #22
    beq copyInStones
    cmp #23
    beq copyInStones
    jmp skipStones
    copyInStones:
        jsr initStonesCharset
    skipStones:
    jsr initObjects
    jsr moveActors // TODO itchy?!
    jsr showEnemies
    rts
}

_draw_playfield: {
    doDraw: grab_drawPlayfield(chamberMapAddr)
}

initObjects: {
    ldx #0 // TODO something is wrong here, why this initalization must be also below?
    stx snakeCounter
    stx pikesCounter
    stx stonesCounter
    stx stoneCurrent
    stx enemiesCounter
    stx actorDirections
    stx actorModes

    ldx staticObjectCount
    bne !+
        jmp end
    !:
    ldx #0 // TODO ???!
    stx snakeCounter
    stx pikesCounter
    stx stonesCounter
    loop:
        stx storeX
        jsr getObjectPositionY
        sty storeY
        jsr getObjectControl
        and #%00001111
        sta control

        // moveable
        cmp #SO_SKULL
        bne !+
            jmp doVerticalEnemy
        !:
        cmp #SO_BAT_VERTICAL
        bne !+
            jmp doVerticalEnemy
        !:
        cmp #SO_DEAD
        bne !+
            jmp doDeadman
        !:
        cmp #SO_BAT
        bne !+
            jmp doBat
        !:

        ldx storeX
        cpx #8
        bcs !+
        ldy currentChamberNumber
        lda level_roomStates, y
        and objMask, x
        bne !+
            // do not display, turned off
            jmp continue
        !:

        ldy storeY
        lda control
        cmp #SO_FLAME_1
        bne !+
            jmp drawFlame1
        !:
        cmp #SO_FLAME_2
        bne !+
            jmp drawFlame2
        !:
        cmp #SO_POTION
        bne !+
            jmp drawPotion
        !:
        cmp #SO_JEWEL
        bne !+
            jmp drawJewel
        !:
        cmp #SO_KEYCODE
        bne !+
            jmp drawKeyCode
        !:
        cmp #SO_KEY
        bne !+
            jmp drawKey
        !:
        cmp #SO_DOOR
        bne !+
            jmp drawDoor
        !:
        cmp #SO_DOORCODE
        bne !+
            jmp drawDoorCode
        !:
        cmp #SO_SNAKE_L
        bne !+
            txa
            ldx snakeCounter
            sta snakesToObjects, x
            inc snakeCounter
            tax
            jsr drawSnakeL
            jmp continue
        !:
        cmp #SO_SNAKE_R
        bne !+
            txa
            ldx snakeCounter
            sta snakesToObjects, x
            inc snakeCounter
            tax
            jsr drawSnakeR
            jmp continue
        !:
        cmp #SO_PIKES
        bne !+
            txa
            ldx pikesCounter
            sta pikesToObjects, x
            tax
            sta ZR_0
            jsr getObjectControl
            lsr
            lsr
            lsr
            lsr
            ldx pikesCounter
            sta pikesCounters, x
            inc pikesCounter
            ldx #0
            jsr drawPikes
            jmp continue
        !:
        cmp #SO_STONE
        bne !+
            txa
            ldx stonesCounter
            sta stonesToObjects, x
            tax
            sta ZR_0
            jsr getObjectControl
            lsr
            lsr
            lsr
            lsr
            ldx stonesCounter
            sta stonesCounters, x
            inc stonesCounter
            ldx #0
            jsr drawStone
            jmp continue
        !:
        continue:
            ldx storeX
            inx
            cpx staticObjectCount
    beq !+
        jmp loop
    !:
    end: rts

    control: .byte 0
    storeX: .byte 0
    storeY: .byte 0

    doVerticalEnemy: {
        txa
        stx ZR_0
        ldx enemiesCounter
        sta enemiesToObjects, x
        tax
        jsr getObjectControl
        sta objectControlStore
        and #%10000000 // TODO cannot use this bit
        beq !+
            ldx enemiesCounter
            lda actorModes
            ora spriteMask, x
            sta actorModes
            lda #LSR
            sta multiply
            jmp !++
        !:
            lda #NOP
            sta multiply
        !:
        lda objectControlStore
        and #%01110000
        lsr
        sta phaseShiftStore // TODO works only for step = 2
        lsr
        ldx enemiesCounter
        sta enemiesCounters, x
        jsr getObjectValue2
        sta actorValue2, x
        // set starting coords
        jsr setStartingCoords
        clc
        lda phaseShiftStore
        multiply: nop
        adc actorPositionY, x
        sta actorPositionY, x
        inc enemiesCounter
        jmp continue
        // local vars
        phaseShiftStore: .byte 0
        objectControlStore: .byte 0
    }

    doDeadman: {
        txa
        stx ZR_0
        ldx enemiesCounter
        sta enemiesToObjects, x
        tax
        jsr getObjectControl
        and #%01110000
        lsr
        lsr
        sta phaseShiftStore
        ldx enemiesCounter
        sta enemiesCounters, x
        jsr getObjectValue2
        sta actorValue2, x
        // set starting coords
        jsr setStartingCoords
        clc
        lda phaseShiftStore
        adc actorPositionX, x
        sta actorPositionX, x
        inc enemiesCounter
        jmp continue
        // local vars
        phaseShiftStore: .byte 0
    }

    doBat: {
        txa
        stx ZR_0
        ldx enemiesCounter
        sta enemiesToObjects, x
        tax
        jsr getObjectControl
        and #%01110000
        lsr
        lsr
        sta phaseShiftStore
        ldx enemiesCounter
        sta enemiesCounters, x
        jsr getObjectValue2
        sta actorValue2, x
        // set starting coords
        jsr setStartingCoords
        clc
        lda phaseShiftStore
        adc actorPositionX, x
        sta actorPositionX, x
        // TODO set Y according to the path
        inc enemiesCounter
        jmp continue
        // local vars
        phaseShiftStore: .byte 0
    }

    setStartingCoords: {
        lda enemiesToObjects, x
        tax
        jsr getObjectPositionX
        ldx enemiesCounter
        asl
        asl
        clc
        adc #12
        sta actorPositionX, x
        lda enemiesToObjects, x
        tax
        jsr getObjectPositionY
        tya
        asl
        asl
        asl
        clc
        adc #54
        ldx enemiesCounter
        sta actorPositionY, x
        rts
    }

    // TODO temporary
    flame1: .byte SOC_FLAME_1, SOC_FLAME_1 + 1
    flame2: .byte SOC_FLAME_2, SOC_FLAME_2 + 1
    potion: .fill 4, SOC_POTION + i
    jewel:  .fill 4, SOC_JEWEL + i
    keyCode: .fill 4, SOC_KEYCODE + i
    key: .fill 4, SOC_KEY + i
    door: .fill 16, SOC_DOOR + i
    doorCode: .fill 16, SOC_DOORCODE + i

    drawFlame1: 
        lda #<flame1
        sta SOURCE_PTR
        lda #>flame1
        jsr _drawRest1x2
        jmp continue
    drawFlame2:
        lda #<flame2
        sta SOURCE_PTR
        lda #>flame2
        jsr _drawRest1x2
        jmp continue
    drawPotion:
        lda #<potion
        sta SOURCE_PTR
        lda #>potion
        jsr _drawRest2x2
        jmp continue
    drawJewel:
        lda #<jewel
        sta SOURCE_PTR
        lda #>jewel
        jsr _drawRest2x2
        jmp continue
    drawKeyCode:
        lda #<keyCode
        sta SOURCE_PTR
        lda #>keyCode
        jsr _drawRest2x2
        jmp continue
    drawKey:
        lda #<key
        sta SOURCE_PTR
        lda #>key
        jsr _drawRest2x2
        jmp continue
    drawDoor:
        lda #<door
        sta SOURCE_PTR
        lda #>door
        jsr _drawDoor
        jmp continue
    drawDoorCode:
        lda #<doorCode
        sta SOURCE_PTR
        lda #>doorCode
        jsr _drawDoor
        jmp continue
    _drawRest1x2:
        sta SOURCE_PTR + 1
        jsr getObjectPositionX
        jmp draw1x2
}

_drawDoor: {
    sta SOURCE_PTR + 1
    lda #4
    sta ZR_0
    jsr getObjectPositionX
    ldx #4
    jmp drawRect
}

_drawRest2x2: {
    sta SOURCE_PTR + 1
    jsr getObjectPositionX
    jmp draw2x2
}

_drawRest2x2m: {
    sta MAIN_SOURCE_PTR + 1
    jsr getObjectPositionX
    jmp draw2x2m
}

drawSnakeL: {
    lda #<snakeL
    sta SOURCE_PTR
    lda #>snakeL
    jsr _drawRest2x2
    rts
}
drawSnakeLm: {
    lda #<snakeL
    sta MAIN_SOURCE_PTR
    lda #>snakeL
    jsr _drawRest2x2m
    rts
}
snakeL: .fill 4, SOC_SNAKE_L + i

drawSnakeR: {
    lda #<snakeR
    sta SOURCE_PTR
    lda #>snakeR
    jsr _drawRest2x2
    rts
}
drawSnakeRm: {
    lda #<snakeR
    sta MAIN_SOURCE_PTR
    lda #>snakeR
    jsr _drawRest2x2m
    rts
}
snakeR: .fill 4, SOC_SNAKE_R + i

drawPikes: {
    lda pikesLo, x
    sta SOURCE_PTR
    lda pikesHi, x
    ldx ZR_0
    jsr _drawRest2x2
    rts
    pikesLo: .byte <pikes0, <pikes1, <pikes2, <pikes3
    pikesHi: .byte >pikes0, >pikes1, >pikes2, >pikes3 
    pikes0: .byte SOC_NULL, SOC_NULL, SOC_PIKES, SOC_PIKES + 1
    pikes1: .byte SOC_NULL, SOC_NULL, SOC_PIKES + 2, SOC_PIKES + 3
    pikes2: .byte SOC_PIKES + 2, SOC_PIKES + 3, SOC_PIKES + 4, SOC_PIKES + 5
    pikes3: .byte SOC_PIKES + 6, SOC_PIKES + 7, SOC_PIKES + 8, SOC_PIKES + 9
}

drawStone: {
    lda stoneLo, x
    sta SOURCE_PTR
    lda stoneHi, x
    sta SOURCE_PTR + 1
    lda #9
    sta ZR_1
    ldx ZR_0
    lda #4
    sta ZR_0
    jsr getObjectPositionX
    ldx ZR_1
    jsr drawRect
    rts
    stoneLo: .byte <stone0, <stone1, <stone2, <stone3, <stone4, <stone5
    stoneHi: .byte >stone0, >stone1, >stone2, >stone3, >stone4, >stone5
    stone0: // ok
        .byte SOC_NULL, SOC_STONE, SOC_STONE + 1, SOC_NULL
        .byte SOC_NULL, SOC_STONE, SOC_STONE + 1, SOC_NULL
        .byte SOC_NULL, SOC_STONE, SOC_STONE + 1, SOC_NULL
        .byte SOC_NULL, SOC_STONE, SOC_STONE + 1, SOC_NULL
        .byte SOC_NULL, SOC_STONE + 2, SOC_STONE + 3, SOC_NULL
        .fill 16, SOC_STONE + 4 + i
    stone1: // ok
        .byte SOC_NULL, SOC_STONE + 20, SOC_STONE + 21, SOC_NULL
        .byte SOC_NULL, SOC_STONE + 20, SOC_STONE + 21, SOC_NULL
        .byte SOC_NULL, SOC_STONE + 20, SOC_STONE + 21, SOC_NULL
        .byte SOC_NULL, SOC_STONE + 20, SOC_STONE + 21, SOC_NULL
        .fill 20, SOC_STONE + 22 + i
    stone2: // ok
        .byte SOC_NULL, SOC_STONE, SOC_STONE + 1, SOC_NULL
        .byte SOC_NULL, SOC_STONE, SOC_STONE + 1, SOC_NULL
        .byte SOC_NULL, SOC_STONE, SOC_STONE + 1, SOC_NULL
        .byte SOC_NULL, SOC_STONE + 2, SOC_STONE + 3, SOC_NULL
        .fill 16, SOC_STONE + 4 + i
        .fill 4, SOC_NULL
    stone3: // ok
        .byte SOC_NULL, SOC_STONE + 20, SOC_STONE + 21, SOC_NULL
        .byte SOC_NULL, SOC_STONE + 20, SOC_STONE + 21, SOC_NULL
        .fill 20, SOC_STONE + 22 + i
        .fill 8, SOC_NULL
    stone4: // ok
        .byte SOC_NULL, SOC_STONE + 2, SOC_STONE + 3, SOC_NULL
        .fill 16, SOC_STONE + 4 + i
        .fill 16, SOC_NULL
    stone5: // ok
        .fill 16, SOC_STONE + 26 + i
        .fill 20, SOC_NULL
}

turnOneSnake: {
    ldy playerColX
    cpy #$ff
    bne !+
        // playerColX not yet ready, skip
        rts
    !:
    ldy #0
    cpy snakeCounter
    bne !+
        rts
    !:
    loop:
        // check is snake is still alive
        ldx snakesToObjects, y
        lda objMask, x
        ldx currentChamberNumber
        and level_roomStates, x
        beq continue

        ldx snakesToObjects, y
        jsr getObjectPositionX
        cmp playerColX
        bcc playerLeftToSnake
            jmp turnRight
        playerLeftToSnake:
            jmp turnLeft
    continue:
        iny
        cpy snakeCounter
        bne loop
    rts
    turnLeft: {
        ldx snakesToObjects, y
        jsr getObjectControl
        and #%00001111
        cmp #SO_SNAKE_L
        beq !+
            jmp continue
        !:
        lda #SO_SNAKE_R
        jsr setObjectControl
        // draw snake
        jsr getObjectPositionY
        jsr drawSnakeRm
        rts
    }
    turnRight: {
        ldx snakesToObjects, y
        jsr getObjectControl
        and #%00001111
        cmp #SO_SNAKE_R
        beq !+
            jmp continue
        !:
        lda #SO_SNAKE_L
        jsr setObjectControl
        // draw snake
        jsr getObjectPositionY
        jsr drawSnakeLm
        rts
    }
}

draw1x2: grab_draw1x2(chamberLines)
draw2x2: grab_draw2x2(chamberLines, SOURCE_PTR)
draw2x2m: grab_draw2x2(chamberLines, MAIN_SOURCE_PTR)
drawRect: grab_drawRect(chamberLines)

copyBitmapChar: grab_copyBitmapChar(true)

initEffects: {
    lda #0
    sta effectCounter
    sta efxFlame1Phase
    sta efxJewelPhase
    sta efxSnakePhase
    lda #2
    sta efxFlame2Phase
    rts
}

playEffects: {
    inc effectCounter
    lda #MAX_EFFECTS
    cmp effectCounter
    bne !+
        lda #0
        sta effectCounter
    !:
    lda effectCounter
    _checkEfx(EFX_ANIM_FLAME, animFlame)
    _checkEfx(EFX_ANIM_SNAKE, animSnake)
    _checkEfx(EFX_ANIM_JEWEL, animJewel)
    _checkEfx(EFX_RUN_PIKES_1, runPikes)
    _checkEfx(EFX_RUN_STONE_1, runStones)
    _checkEfx(EFX_RUN_STONE_2, runStones)
    _checkEfx(EFX_RUN_STONE_3, runStones)
    _checkEfx(EFX_RUN_PIKES_2, runPikes)
    end: rts

    animJewel: {
        // set source 1
        inc efxJewelPhase
        lda efxJewelPhase
        cmp #4
        bne !+
            lda #0
            sta efxJewelPhase
        !:
        lda efxJewelPhase
        asl
        asl
        asl
        asl
        asl
        
        // do jewel
        ldx #SOC_JEWEL
        copyChar(level_jewel)
        copyChar(level_jewel + 8)
        copyChar(level_jewel + 16)
        copyChar(level_jewel + 24)

        // do keycode
        ldx #SOC_KEYCODE
        copyChar(level_keycode)
        copyChar(level_keycode + 8)
        copyChar(level_keycode + 16)
        copyChar(level_keycode + 24)

        rts
    }
    animSnake: {
        // set source 1
        inc efxSnakePhase
        lda efxSnakePhase
        cmp #4
        bne !+
            lda #0
            sta efxSnakePhase
        !:
        lda efxSnakePhase
        asl
        asl
        asl
        asl
        asl
        
        // do snake L
        ldx #SOC_SNAKE_L
        copyChar(level_snakeLeft)
        copyChar(level_snakeLeft + 8)
        copyChar(level_snakeLeft + 16)
        copyChar(level_snakeLeft + 24)

        // do snake R
        ldx #SOC_SNAKE_R
        copyChar(level_snakeRight)
        copyChar(level_snakeRight + 8)
        copyChar(level_snakeRight + 16)
        copyChar(level_snakeRight + 24)
        rts
    }
    animFlame: {
        inc efxFlame1Phase
        lda efxFlame1Phase
        cmp #4
        bne !+
            lda #0
            sta efxFlame1Phase
        !:
        lda efxFlame1Phase
        asl
        asl
        asl
        asl

        // set flame 1
        ldx #SOC_FLAME_1
        copyChar(level_fire)
        copyChar(level_fire + 8)
        
        asl

        // set potion
        ldx #SOC_POTION
        copyChar(level_potion)
        copyChar(level_potion + 8)
        copyChar(level_potion + 16)
        copyChar(level_potion + 24)

        // set flame 2
        inc efxFlame2Phase
        lda efxFlame2Phase
        cmp #4
        bne !+
            lda #0
            sta efxFlame2Phase
        !:
        lda efxFlame2Phase
        asl
        asl
        asl
        asl
        ldx #SOC_FLAME_2
        copyChar(level_fire)
        copyChar(level_fire + 8)

        rts
    }
    runPikes: {
        lda pikesCounter
        cmp #0
        bne !+
            rts
        !:
        ldx #0
        loop:
            lda pikesCounters, x
            cmp #PIKES_MAX_FRAME
            bne !+
                lda #0
                sta pikesCounters, x
            !:
            stx storeX
            lda pikesToObjects, x
            tax
            jsr getObjectPositionY
            sta ZR_0
            ldx storeX
            lda pikesCounters, x
            ldx #$ff
            cmp #PIKES_PHASE_0
            bne !+
                ldx #0
            !:
            cmp #PIKES_PHASE_1
            bne !+
                ldx #1
            !:
            cmp #PIKES_PHASE_2
            bne !+
                ldx #2
            !:
            cmp #PIKES_PHASE_3
            bne !+
                ldx #3
            !:
            cpx #$ff
            beq !+
                jsr drawPikes
            !:
            ldx storeX
            inc pikesCounters, x
            inx
            cpx pikesCounter
        bne loop
        rts
        // local vars
        storeX: .byte 0
    }
    runStones: {
        lda stonesCounter
        cmp #0
        bne !+
            rts
        !:
        ldx stoneCurrent
        cpx stonesCounter
        bcc continue
            jmp increment
        continue:

        lda stonesCounters, x
        cmp #STONES_MAX_FRAME
        bne !+
            lda #0
            sta stonesCounters, x
        !:
        stx storeX
        lda stonesToObjects, x
        sta ZR_0
        tax
        jsr getObjectPositionY
        ldx storeX
        lda stonesCounters, x
        ldx #$ff
        cmp #STONES_PHASE_0
        bne !+
            ldx #0
        !:
        cmp #STONES_PHASE_1
        bne !+
            ldx #1
        !:
        cmp #STONES_PHASE_2
        bne !+
            ldx #2
        !:
        cmp #STONES_PHASE_3
        bne !+
            ldx #3
        !:
        cmp #STONES_PHASE_4
        bne !+
            ldx #4
        !:
        cmp #STONES_PHASE_5
        bne !+
            ldx #5
        !:
        cmp #STONES_PHASE_3d
        bne !+
            ldx #4
        !:
        cpx #$ff
        beq !+
            jsr drawStone
        !:
        ldx storeX
        inc stonesCounters, x
    increment:
        inx
        cpx #3
        bne !+
            ldx #0
        !:
        stx stoneCurrent
        rts
        // local vars
        storeX: .byte 0
    }
}

.macro copyChar(sourceAddr) {
    pha
    clc
    adc #<sourceAddr
    sta SOURCE_PTR
    lda #0
    adc #>sourceAddr
    sta SOURCE_PTR + 1
    jsr _copyChar
    inx
    pla
}

_copyChar: {
    // set target
    lda targetCharset.lo, x
    sta DEST_PTR
    lda targetCharset.hi, x
    sta DEST_PTR + 1
    // copy 1st char
    jmp copyBitmapChar
}

.macro _checkEfx(efx, jumpTo) {
    cmp #efx
    bne !+
    jmp jumpTo
    !:
}

.macro waitFor() {
    !: 
        lda waitFor
    bne !-
}

copyLargeMemForward: {
    #import "common/lib/sub/copy-large-mem-forward.asm"
}
outText: {
    #import "text/lib/sub/out-text.asm"
}

initPlayerPosition: {
    lda level_startPositionX
    sta physPlayerX
    sta playerRespawnPositionX
    lda level_startPositionX + 1
    sta physPlayerX + 1
    sta playerRespawnPositionX + 1
    lda level_startPositionY
    sta physPlayerY
    sta playerRespawnPositionY
    jsr physResetActorPosition
    lda #0
    sta playerDying
    rts
}

respawnPlayerPosition: {
    lda playerRespawnPositionX
    sta physPlayerX
    lda playerRespawnPositionX + 1
    sta physPlayerX + 1
    lda playerRespawnPositionY
    sta physPlayerY
    jsr physResetActorPosition
    rts
}

updatePlayerPosition: ani_updatePlayerPosition(physPlayerX, physPlayerY)

handleTitleScreenCommand: {
    and #%00011111
    eor #%00011111
    cmp #%00000001
    beq joyUp
    cmp #%00010000
    beq joyFire
    sta io_oldJoy
    rts
    
    joyUp:
        // change color scheme
        cmp io_oldJoy
        sta io_oldJoy
        beq !+
            jsr nextColorScheme
        !:
        rts
    joyFire:
        // start the game
        cmp io_oldJoy
        sta io_oldJoy
        beq !+
            seq_setUp(1, 60, walkLeft, doNothing)    
        !:
        rts
    walkLeft:
        lda #CMD_WALK_LEFT
        jsr phys_commandPlayer
        rts
}

joyHandlingForBorg: {
    sta storeA
    cmp #0
    bne !+
        sta joyAccumulator
        sta joyPreviousValue
        sta joyDelayCounter
    !:
    and #%00010000
    bne !+
        lda storeA
        and #%11101111
        sta joyPreviousValue
        sta joyAccumulator
    !:
    lda storeA
    sta joyAccumulator
    cmp joyPreviousValue
    beq !+
        inc joyDelayCounter
    !:
    lda joyDelayCounter
    cmp #JOY_MAX_DELAY
    bne !+
        lda joyAccumulator
        sta joyPreviousValue
        lda #0
        sta joyDelayCounter
    !:
    lda joyPreviousValue
    rts
    storeA: .byte 0
}

dispatchPlayerCommand: {
    // fix #110, do not move if room in change
    ldy roomChange
    cpy #$ff
    beq !+
        lda #CMD_IDLE
        jmp doCommand
    !:
    ldy #0
    ldx physPlayerState
    cpx #STATE_ON_LADDER_FACING_LEFT
    bne !+
        ldy #1
    !:
    cpx #STATE_ON_LADDER_FACING_RIGHT
    bne !+
        ldy #1
    !:
    and #%00011111
    eor #%00011111
    jsr joyHandlingForBorg
    cmp #%00001000 // right
    beq joyRight
    cmp #%00000100 // left
    beq joyLeft 
    cmp #%00000010 // down
    beq joyDown
    cmp #%00000001 // up
    beq joyUp
    cmp #%00010000 // fire
    beq joyFire
    cmp #%00010100 // fire and left
    beq joyFireLeft
    cmp #%00011000 // fire and right
    beq joyFireRight
    cmp #%00010010 // fire, down
    beq joyDown
    cmp #%00010001 // fire, up
    beq joyUp
    cpy #1
    beq !+ 
        // not on ladder
        cmp #%00001001 // right-up
        beq joyUp
        cmp #%00000101 // left-up
        beq joyUp
        cmp #%00001010  // right-dn
        beq joyRightDown
        cmp #%00000110 // left-down
        beq joyLeftDown
        cmp #%00010110 // fire, left and down
        beq joyFireLeft 
        cmp #%00010101 // fire, left and up
        beq joyFireLeft
        cmp #%00011010 // fire, right and fown
        beq joyFireRight
        cmp #%00011001 // fire, right and up
        beq joyFireRight
        jmp idle
    !: 
        // on ladder
        cmp #%00001001 // right-up
        beq joyUp
        cmp #%00000101 // left-up
        beq joyUp
        cmp #%00001010  // right-dn
        beq joyDown
        cmp #%00000110 // left-down
        beq joyDown
        cmp #%00010110 // fire, left and down
        beq joyDown
        cmp #%00010101 // fire, left and up
        beq joyUp
        cmp #%00011010 // fire, right and down
        beq joyDown
        cmp #%00011001 // fire, right and up
        beq joyUp
    idle:
    lda #CMD_IDLE
    jmp doCommand
joyRight:
    lda #CMD_WALK_RIGHT
    jmp doCommand
joyLeft:
    lda #CMD_WALK_LEFT
    jmp doCommand
joyDown:
    lda #CMD_CLIMB_DOWN
    jmp doCommand
joyUp:
    lda #CMD_CLIMB_UP
    jmp doCommand
joyFire:
    lda #CMD_JUMP
    jmp doCommand
joyFireLeft:
    lda #CMD_JUMP_LEFT
    jmp doCommand
joyFireRight:
    lda #CMD_JUMP_RIGHT
    jmp doCommand
joyLeftDown:
    lda physPlayerState
    cmp #STATE_DUCK_RIGHT
    bne !+
        lda #CMD_DUCK_LEFT
        jmp !++
    !:
    lda #CMD_CLIMB_DOWN
    !:
    jmp doCommand
joyRightDown:
    lda physPlayerState
    cmp #STATE_DUCK_LEFT
    bne !+
        lda #CMD_DUCK_RIGHT
        jmp !++
    !:
    lda #CMD_CLIMB_DOWN
    !:
    lda #CMD_DUCK_RIGHT
    jmp doCommand
doCommand:
    sta io_oldJoy
    jsr phys_commandPlayer
    rts
}

initSound: {
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
}

playMusic: {
    lda ntscFlag
    beq doPlay
        ldx ntscCounter
        inx
        stx ntscCounter
        cpx #6
        bne doPlay
        ldx #0
        stx ntscCounter
        rts
    doPlay:
        ldx muralBehaviour
        cpx #7
        beq !+
            jsr music.play
            rts
        !:
        jsr intro.play
    rts
}

blankScreen: {
    lda c64lib.CONTROL_1
    and #%11101111
    sta c64lib.CONTROL_1
    rts
}

showScreen: {
    lda c64lib.CONTROL_1
    ora #%00010000
    sta c64lib.CONTROL_1
    rts
}

#import "graph-text.asm"
#import "animations.asm"
#import "io.asm"
#import "physics-tall.asm"
#import "sequencer.asm"
#import "static-objects.asm"
#import "actors.asm"
#import "aux-screens.asm"

checkBGCollision: phys_checkBGCollisionExt2(roomMaterialsBuffer, chamberLines)

startCopper: c64lib_startCopper(COPPER_LIST_ADDR, COPPER_LIST_PTR, List().add(c64lib.IRQH_JSR, c64lib.IRQH_DASHBOARD_CUTOFF).lock())
stopCopper: c64lib_stopCopper()

// vars
currentChamberNumber:       .byte 0
chamberMapAddr:             .word 0
staticObjectCount:          .byte 0
roomChange:                 .byte $ff
objCollisionDetected:       .byte $ff
drawCommand:                .byte $ff
playerDieRequest:           .byte 0
roomChangeDirection:        .byte 0
// roomCharsDecodingBuffer:    .fill 256, 0 // change to MAX_BG_CHARS
// roomMaterialsBuffer:        .fill 256, 0
.label roomCharsDecodingBuffer = $BF00
.label roomMaterialsBuffer     = $BE00
// to save extra 0.5kB this is allocated on upper music area, as music in demo level does not use full 8kB
joyDelayCounter:            .byte 0
joyAccumulator:             .byte 0
joyPreviousValue:           .byte 0
// ...to handle snakes
snakesToObjects:            .fill MAX_SNAKES, 0
snakeCounter:               .byte 0
// ...to handle pikes
pikesToObjects:             .fill MAX_PIKES, 0
pikesCounters:              .fill MAX_PIKES, 0
pikesCounter:               .byte 0
// ...to handle stones
stonesToObjects:            .fill MAX_STONES, 0
stonesCounters:             .fill MAX_STONES, 0
stonesCounter:              .byte 0
stoneCurrent:               .byte 0
// ...to handle enemies
enemiesCounter:             .byte 0
enemiesToObjects:           .fill ANI_MAX_ACTORS, 0
enemiesCounters:            .fill ANI_MAX_ACTORS, 0
// fade effect
currentColor:               .byte SCHEME_CLASSIC_LIGHT
fadeCounter:                .byte 0
// actual player position in columns
playerColX:                 .byte 0
playerColY:                 .byte 0
// speed tabs
sourceCharset:              .lohifill 256, demoLevelCharset + i*8
targetCharset:              .lohifill 256, TEXT_CHARSET_MEM + i*8
// auxiliary data structures
chamberLines:               .lohifill 25, SCREEN_MEM_0 + 40*i // indexed start of screen lines for faster collision detection
// color ramps
fadeOut:                    .byte SCHEME_CLASSIC_DARK, DARK_GREY, GREY
fadeIn:                     .byte SCHEME_CLASSIC_LIGHT, GREY, DARK_GREY, BLACK
waitFor:                    .byte 0
// effects & aux mechanics
effectCounter:              .byte 0
efxFlame1Phase:             .byte 0
efxFlame2Phase:             .byte 0
efxJewelPhase:              .byte 0
efxSnakePhase:              .byte 0
// player respawn
playerRespawnPositionX:     .byte 0, 0
playerRespawnPositionY:     .byte 0
playerRespawnState:         .byte 0
playerDying:                .byte 0
// game state
gameLivesLeft:              .byte 0
gameScore:                  .fill 3, 0
gameInventory:              .fill 4, 0
gameTitleScreen:            .byte 0
gameState:                  .byte 0
// NTSC handling
ntscCounter:                .byte 0
// eyes buffer
eyesColor:                  .byte BLACK
// color schemes
colorScheme:                .byte DEFAULT_COLOR_SCHEME
colorLights:                .byte SCHEME_CLASSIC_LIGHT,     SCHEME_AMBER_LIGHT,     SCHEME_GREEN_LIGHT,     SCHEME_BLUE_LIGHT,     SCHEME_C64_LIGHT,   SCHEME_C128_LIGHT,  SCHEME_EMBER_LIGHT
colorDarks:                 .byte SCHEME_CLASSIC_DARK,      SCHEME_AMBER_DARK,      SCHEME_GREEN_DARK,      SCHEME_BLUE_DARK,      SCHEME_C64_DARK,    SCHEME_C128_DARK,   SCHEME_EMBER_DARK
colorBright:                .byte SCHEME_CLASSIC_BRIGHT,    SCHEME_AMBER_BRIGHT,    SCHEME_GREEN_BRIGHT,    SCHEME_BLUE_BRIGHT,    SCHEME_C64_BRIGHT,  SCHEME_C128_BRIGHT, SCHEME_EMBER_BRIGHT
colorDimmed:                .byte SCHEME_CLASSIC_DIMMED,    SCHEME_AMBER_DIMMED,    SCHEME_GREEN_DIMMED,    SCHEME_BLUE_DIMMED,    SCHEME_C64_DIMMED,  SCHEME_C128_DIMMED, SCHEME_EMBER_DIMMED
// texts

.macro textC(value) {
    .byte (40-value.size())/2
    .text value
    .byte $ff
}

txtCounter:     .byte 0
txtLine0:       textC("tony@demo@version")
txtLine1:       textC("concept@and@graphics@by@rafal@dudek")
txtLine2:       textC("music@by@@sami@juntunen")
txtLine3:       textC("code@by@@maciej@malecki")
txtLine4:       textC("push@joy@up@to@change@colors")
txtPtrLo:       .byte <txtLine0, <txtLine1, <txtLine2, <txtLine3, <txtLine4
txtPtrHi:       .byte >txtLine0, >txtLine1, >txtLine2, >txtLine3, >txtLine4
txtPressFire:   .text "press@fire@to@start"; .byte $ff
txtGameOver:    .text "game@@over"; .byte $ff
txtPressFireCnt:    .text "press@fire@to@continue"; .byte $ff
textEnd0:       .text "see@you@soon"; .byte $ff
textEnd1:       .text "playing@whole@five@levels@of@tony"; .byte $ff
textEnd2:       .text "born@for@adventure"; .byte $ff

.label MAX_TITLE_TEXT = 5

dashboardMap: 
    .import binary "dashboard-map.bin"
endOfCode:

// temporarily...
levelDataStart:
    #import "level/build/data.asm"
levelDataEnd:

endOfNonMovable:


// ===================================================================== the build demo
// Down + fire lays a 2x2 brick in the wall slot in front of Tony at his foot level, or
// lifts it again if it is one he laid. A placed brick is four screen codes of its own
// ($40-$43, with the glyphs of a small stone block: the two ends of a floor brick, so it reads as
// built, not as the dotted mural) carrying wall material, so the engine's own collision makes it
// floor and wall with no change to the physics. The mural's
// seeded bricks stay decoration; a placed brick may cover them and they come back when
// it is lifted (muralBits remembers where they were). The second Tony checks the column
// ahead of every step against the same materials, so a placed brick is a wall to him.
.label BUILD_CODE   = $50         // above the room's own screen codes (the two-room map uses up to $42)
.label LADDER_BOTTOM = 9          // the dangling ladder's lowest row in the room below: five bricks to reach it
.label BUILD_COL0   = 5           // the wall's first column (slots at 5 + 2i, i = 0..14)
.label BUILD_ROW_LO = 21          // the lowest level's top row: rows 21-22 sit on the floor at 23
buildJoy:      .byte 0
buildPrev:     .byte 0
buildCount:    .byte 0
buildRow:      .byte 0            // the target's top row
buildCol:      .byte 0            // the target's left column
buildTop:      .byte 0
buildLeftCol:  .byte 0
buildRightCol: .byte 0
buildCell:     .byte 0
buildK:        .byte 0
buildI:        .byte 0
buildBCol:     .byte 0
buildMask:     .byte 0
buildTmp:      .word 0
brickCodes:    .fill 4, 0         // the mural bricks' screen codes, TL TR BL BR (from the decoding table)
ladderCodes:   .fill 2, 0         // the ladder's two screen codes
buildOnce:     .byte 0            // the bitmaps are cleared once, at the start
buildRoomOff:  .byte 0            // 0 or 19: this room's bitmap in placedBits
placedBits:    .fill 38, 0        // the bricks laid, 150 slots per room, two rooms
buildRoomCounts: .byte 0, 0
buildLadderK:  .byte 0
buildLadderTmp: .byte 0
buildLadderCol: .byte 0
stoneCodes:    .byte $31, $36, $37, $3C   // the placed brick's look: a floor brick's left and right ends, map codes
muralBits:     .fill 19, 0        // 150 slots (15 x 10), bit set = a seeded brick

// once the room's characters are translated: the codes, glyphs, materials, the bitmap, this room's bricks, the count
buildInit: {
    lda buildOnce
    bne !++
        inc buildOnce
        ldx #37
        lda #0
        !:
            sta placedBits, x
            dex
        bpl !-
        sta buildRoomCounts
        sta buildRoomCounts + 1
    !:
    lda #0
    ldx currentChamberNumber
    beq !+
        lda #19
    !:
    sta buildRoomOff
    ldx #0
    !:
        lda roomCharsDecodingBuffer + $B0, x
        sta brickCodes, x
        inx
        cpx #4
    bne !-
    lda roomCharsDecodingBuffer + $7C
    sta ladderCodes
    lda roomCharsDecodingBuffer + $7D
    sta ladderCodes + 1
    lda #BG_CLSN_WALL
    sta roomMaterialsBuffer + BUILD_CODE
    sta roomMaterialsBuffer + BUILD_CODE + 1
    sta roomMaterialsBuffer + BUILD_CODE + 2
    sta roomMaterialsBuffer + BUILD_CODE + 3
    // glyphs: a floor brick's two ends copied to the placed codes (the room's charset is at TEXT_CHARSET_MEM)
    ldx #0
    glyphLoop:
        ldy stoneCodes, x
        lda roomCharsDecodingBuffer, y
        tay
        lda targetCharset.lo, y
        sta SOURCE_PTR
        lda targetCharset.hi, y
        sta SOURCE_PTR + 1
        txa
        clc
        adc #BUILD_CODE
        tay
        lda targetCharset.lo, y
        sta DEST_PTR
        lda targetCharset.hi, y
        sta DEST_PTR + 1
        ldy #7
        !:
            lda (SOURCE_PTR), y
            sta (DEST_PTR), y
            dey
        bpl !-
        inx
        cpx #4
    bne glyphLoop
    // the mural bitmap: slot (i, j) holds a brick when its top-left cell shows the brick's code
    ldx #0
    !:
        lda #0
        sta muralBits, x
        inx
        cpx #19
    bne !-
    lda #0
    sta buildK
    slotRows:
        lda #0
        sta buildI
        slotCols:
            lda buildK
            asl
            clc
            adc #2
            tay                     // row = 2 + 2j
            lda buildI
            asl
            clc
            adc #BUILD_COL0
            tax                     // col = 5 + 2i
            jsr buildReadCell
            cmp brickCodes
            bne notBrick
                jsr buildSlotBit    // A = mask, X = byte
                ora muralBits, x
                sta muralBits, x
            notBrick:
            inc buildI
            lda buildI
            cmp #15
        bne slotCols
        inc buildK
        lda buildK
        cmp #10
    bne slotRows
    // the floor under the block number back to plain stone (the ladder's cells, if it stands there, kept)
    ldx #0
    floorLoop:
        lda SCREEN_MEM_0 + 23*40 + 27, x
        cmp ladderCodes
        beq floorNext
        cmp ladderCodes + 1
        beq floorNext
        ldy floorPattern, x
        lda roomCharsDecodingBuffer, y
        sta SCREEN_MEM_0 + 23*40 + 27, x
        floorNext:
        inx
        cpx #8
    bne floorLoop
    // this room's bricks back on the wall
    lda #0
    sta buildK
    layRows:
        lda #0
        sta buildI
        layCols:
            jsr buildSlotBit
            txa
            clc
            adc buildRoomOff
            tax
            lda placedBits, x
            and buildMask
            beq notLaid
                lda buildK
                asl
                sta buildRow
                lda #BUILD_ROW_LO
                sec
                sbc buildRow
                sta buildRow
                lda buildI
                asl
                clc
                adc #BUILD_COL0
                sta buildCol
                jsr buildLayCells
            notLaid:
            inc buildI
            lda buildI
            cmp #15
        bne layCols
        inc buildK
        lda buildK
        cmp #10
    bne layRows
    ldx currentChamberNumber
    lda buildRoomCounts, x
    sta buildCount
    lda #0
    sta buildPrev
    jmp buildDrawCount
    floorPattern: .byte $34, $35, $36, $25, $26, $27, $28, $29     // the floor course's map codes at columns 27-34
}

// the four placed codes at buildRow, buildCol
buildLayCells: {
    ldy buildRow
    ldx buildCol
    lda #BUILD_CODE
    jsr buildWriteCell
    inx
    lda #BUILD_CODE + 1
    jsr buildWriteCell
    iny
    lda #BUILD_CODE + 3
    jsr buildWriteCell
    dex
    lda #BUILD_CODE + 2
    jmp buildWriteCell
}

// the bit of the slot at buildRow, buildCol in this room's bitmap: X = its byte, buildMask = its bit
buildSlotOfTarget: {
    lda buildCol
    sec
    sbc #BUILD_COL0
    lsr
    sta buildI
    lda #BUILD_ROW_LO
    sec
    sbc buildRow
    lsr
    sta buildK
    jsr buildSlotBit
    txa
    clc
    adc buildRoomOff
    tax
    rts
}

// A = the screen code at row Y, column X (X and Y kept)
buildReadCell: {
    lda chamberLines.lo, y
    sta rd + 1
    lda chamberLines.hi, y
    sta rd + 2
    rd: lda $ffff, x
    rts
}
// A written at row Y, column X (X and Y kept)
buildWriteCell: {
    pha
    lda chamberLines.lo, y
    sta wr + 1
    lda chamberLines.hi, y
    sta wr + 2
    pla
    wr: sta $ffff, x
    rts
}
// slot (buildI, buildK) -> X = byte index, A = bit mask; n = i + 15 j
buildSlotBit: {
    lda buildK
    asl
    asl
    asl
    asl                 // 16 j
    sec
    sbc buildK          // 15 j
    clc
    adc buildI          // n
    pha
    lsr
    lsr
    lsr
    tax                 // n / 8
    pla
    and #7
    tay
    lda bitMask, y
    sta buildMask
    rts
    bitMask: .byte 1, 2, 4, 8, 16, 32, 64, 128
}

// every frame, before the joystick is dispatched (A = the raw joystick, kept). Two chords, each on
// its press: down + fire lays or lifts, up + fire steps up onto the brick in front.
buildVerb: {
    sta buildJoy
    eor #$1f
    tax
    and #%00010010
    cmp #%00010010
    beq layChord
    txa
    and #%00010001
    cmp #%00010001
    beq upChord
        lda #0
        sta buildPrev
        jmp done
    layChord:
        lda buildPrev
        bne done
        lda #1
        sta buildPrev
        jsr buildAct
        jmp done
    upChord:
        lda buildPrev
        bne done
        lda #2
        sta buildPrev
        jsr buildStepUp
    done:
    lda buildJoy
    rts
}

// the slot in front of Tony at his foot level -> buildRow, buildCol; carry set when there is none
buildTarget: {
    // only with his feet on something: on the ground, walking or ducking
    lda physPlayerState
    and #%01111111
    cmp #STATE_ON_GROUND_LEFT
    beq ok
    cmp #STATE_WALKING_LEFT
    beq ok
    cmp #STATE_DUCK_LEFT
    beq ok
    sec
    rts
    ok:
    // his box, as the physics counts it: top row Y / 8 - 6, columns X / 8 - 2 and (X + 8) / 8 - 2
    lda physPlayerY
    lsr
    lsr
    lsr
    sec
    sbc #6
    sta buildTop
    _phys_div8_16(physPlayerX, 0, -2, buildLeftCol)
    _phys_div8_16(physPlayerX, 8, -2, buildRightCol)
    // the level: the brick's bottom row is the row above his feet, so k = (19 - top) / 2, a whole number
    lda #19
    sec
    sbc buildTop
    bmi no
    cmp #19
    bcs no
    lsr
    bcs no
    sta buildK
    asl
    sta buildRow
    lda #BUILD_ROW_LO
    sec
    sbc buildRow
    sta buildRow                // top row = 21 - 2k
    // the slot in front: past his right column when he faces right, before his left column when he faces left
    lda physPlayerState
    bmi right
        lda buildLeftCol
        sec
        sbc #1                  // the slot's right column, made even (6, 8, ... 34)
        and #%11111110
        sec
        sbc #1                  // its left column
        jmp haveCol
    right:
        lda buildRightCol
        clc
        adc #1
        ora #1                  // the slot's left column, made odd (5, 7, ... 33)
    haveCol:
    sta buildCol
    cmp #BUILD_COL0
    bcc no
    cmp #(BUILD_COL0 + 29)
    bcs no
    clc
    rts
    no:
    sec
    rts
}

// down + fire: lay a brick in the slot in front, or lift the one he laid there
buildAct: {
    jsr buildTarget
    bcc decide
        rts
    decide:
    ldy buildRow
    ldx buildCol
    jsr buildReadCell
    cmp #BUILD_CODE
    beq lift
    jsr buildFourFree
    bcs no
    jsr buildBuddyClear
    bcs no
    jmp lay
    no:
    rts
    lay:
    jsr buildLayCells
    jsr buildSlotOfTarget
    lda placedBits, x
    ora buildMask
    sta placedBits, x
    inc buildCount
    jmp buildCounted
    lift:
    ldy buildRow
    ldx buildCol
    jsr buildRestoreCell
    inx
    jsr buildRestoreCell
    iny
    jsr buildRestoreCell
    dex
    jsr buildRestoreCell
    jsr buildSlotOfTarget
    lda buildMask
    eor #$ff
    and placedBits, x
    sta placedBits, x
    dec buildCount
    buildCounted:
    ldx currentChamberNumber
    lda buildCount
    sta buildRoomCounts, x
    jmp buildDrawCount
}

// up + fire: step up onto the brick he laid in front, when the four rows above it are clear
buildStepUp: {
    jsr buildTarget
    bcs no
    ldy buildRow
    ldx buildCol
    jsr buildReadCell
    cmp #BUILD_CODE
    bne no
    lda buildRow
    sec
    sbc #4
    bcc no
    tay
    check:
        ldx buildCol
        jsr buildReadCell
        tax
        lda roomMaterialsBuffer, x
        and #BG_CLSN_WALL
        bne no
        ldx buildCol
        inx
        jsr buildReadCell
        tax
        lda roomMaterialsBuffer, x
        and #BG_CLSN_WALL
        bne no
        iny
        cpy buildRow
    bne check
    // up he goes: his box on the brick's two columns (X = (col + 2) * 8 + 3), one brick higher
    lda #0
    sta buildTmp + 1
    lda buildCol
    asl
    rol buildTmp + 1
    asl
    rol buildTmp + 1
    asl
    rol buildTmp + 1
    clc
    adc #19
    sta physPlayerX
    lda buildTmp + 1
    adc #0
    sta physPlayerX + 1
    lda physPlayerY
    sec
    sbc #16
    sta physPlayerY
    jsr physResetActorPosition
    lda physPlayerState
    and #%10000000
    jsr phys_forceTransitState      // on the ground, the way he faces
    jsr onStateChange
    jsr checkBGCollision
    no:
    rts
}

// carry clear when the four target cells are empty or mural bricks
buildFourFree: {
    ldy buildRow
    ldx buildCol
    jsr cellOk
    bcs bad
    inx
    jsr cellOk
    bcs bad
    iny
    jsr cellOk
    bcs bad
    dex
    jsr cellOk
    bad:
    rts
    cellOk: {
        jsr buildReadCell
        beq fine
        cmp brickCodes
        beq fine
        cmp brickCodes + 1
        beq fine
        cmp brickCodes + 2
        beq fine
        cmp brickCodes + 3
        beq fine
        sec
        rts
        fine:
        clc
        rts
    }
}

// carry set when the target 2x2 overlaps the second Tony's box
buildBuddyClear: {
    lda buddyY
    lsr
    lsr
    lsr
    sec
    sbc #6
    sta bTop
    _phys_div8_16(buddyX, 0, -2, bLeft)
    _phys_div8_16(buddyX, 8, -2, bRight)
    lda buildCol
    clc
    adc #1
    cmp bLeft
    bcc clear               // the target ends before his left column
    lda bRight
    cmp buildCol
    bcc clear               // his right column ends before the target
    lda buildRow
    clc
    adc #1
    cmp bTop
    bcc clear               // the target ends above him
    lda bTop
    clc
    adc #3
    cmp buildRow
    bcc clear               // he ends above the target
    sec
    rts
    clear:
    clc
    rts
    bTop: .byte 0
    bLeft: .byte 0
    bRight: .byte 0
}

// the cell at row Y, column X back to what the mural had there (X and Y kept)
buildRestoreCell: {
    sty rowSave
    stx colSave
    cpy #22
    bcs empty               // row 22 and below: never a mural row
    txa
    sec
    sbc #BUILD_COL0
    lsr
    sta buildI
    tya
    sec
    sbc #2
    lsr
    sta buildK
    jsr buildSlotBit
    and muralBits, x
    beq empty
    lda rowSave             // which of the four: (row - 2) & 1 doubled, plus (col - 5) & 1
    sec
    sbc #2
    and #1
    asl
    sta buildCell
    lda colSave
    sec
    sbc #BUILD_COL0
    and #1
    ora buildCell
    tax
    lda brickCodes, x
    jmp write
    empty:
    lda #0
    write:
    ldy rowSave
    ldx colSave
    jmp buildWriteCell
    rowSave: .byte 0
    colSave: .byte 0
}

// the count, three carved digits in the floor at columns 1-3
buildDrawCount: {
    lda buildCount
    ldx #0
    !:
        cmp #100
        bcc !+
        sbc #100
        inx
        jmp !-
    !:
    stx d0
    ldx #0
    !:
        cmp #10
        bcc !+
        sbc #10
        inx
        jmp !-
    !:
    stx d1
    sta d2
    ldx #0
    !:
        lda d0, x
        clc
        adc #MURAL_DIGIT_BASE
        tay
        lda roomCharsDecodingBuffer, y
        sta SCREEN_MEM_0 + 23*40 + 1, x      // under the left pillar, where no ladder can stand
        inx
        cpx #3
    bne !-
    rts
    d0: .byte 0
    d1: .byte 0
    d2: .byte 0
}

// the second Tony's next step: carry set when a wall stands in the column ahead, from his top row to the floor
buildBlockedRight: {
    _phys_div8_16(buddyX, 9, -2, buildBCol)      // (X + 1 + 8) / 8 - 2: his right column after the step
    jmp buildColumnWall
}
buildBlockedLeft: {
    sec
    lda buddyX
    sbc #1
    sta buildTmp
    lda buddyX + 1
    sbc #0
    sta buildTmp + 1
    _phys_div8_16(buildTmp, 0, -2, buildBCol)    // (X - 1) / 8 - 2: his left column after the step
    jmp buildColumnWall
}
buildColumnWall: {
    lda buddyY
    lsr
    lsr
    lsr
    sec
    sbc #6
    tay
    rows:
        ldx buildBCol
        jsr buildReadCell
        tax
        lda roomMaterialsBuffer, x
        and #BG_CLSN_WALL
        bne wall
        iny
        cpy #23
    bne rows
    clc
    rts
    wall:
    sec
    rts
}

.segment Movable

musicData:
    .fill music.size, music.getData(i)
    // .fill 8*1024 - music.size, random()*256 // filler to the whole 8kb
musicDataEnd:

dasboardCharset:
    .import binary "dashboard-charset.bin"
dashboardCharsetEnd:

font:
    .import binary "font.bin"
fontEnd:

gameEnd:
    loadNegated("game-end.bin")
gameEndEnd:

// second sprite bank
secondSpriteBank:
    #import "level/demo/bitmaps/bat-vertical.asm"
    #import "level/demo/bitmaps/deadman.asm"
secondSpriteBankEnd:
.assert "Second sprite bank overflown", (secondSpriteBankEnd - secondSpriteBank) <= 12*64, true

// third sprite bank
thirdSpriteBank:
    #import "level/demo/bitmaps/bat.asm"
thirdSpriteBankEnd:
.assert "Third sprite bank overflown", (thirdSpriteBankEnd - thirdSpriteBank) <= SPRITES_IN_ZONE_3*64, true

// first sprite bank
firstSpriteBank:
    tonySprites:
        #import "sprites/player.asm"
    tonySpritesEnd:

    skullSprites:
        #import "level/demo/bitmaps/skull.asm"
    skullSpritesEnd:

    .import binary "eyes.bin"
firstSpriteBankEnd:

.assert "First sprite bank overflown", (firstSpriteBankEnd - firstSpriteBank) <= 126*64, true

endOfTony:
.function formatRange(title, from, to) {
    .return title + " = $" + toHexString(from) + " - $" + toHexString(to)
}


.print ""
.print "----------------------------"
.print "Tony's memory usage summary:"
.print "----------------------------"
.print "Sprites slots used: " + (firstSpriteBankEnd - firstSpriteBank)/64
.print "Second sprites slots used: " + (secondSpriteBankEnd - secondSpriteBank)/64
.print "Code size: " + (endOfCode - start) + " bytes."
.print "Size of level data: " + (levelDataEnd - levelDataStart) + " bytes."
.print "Total size: " + (endOfTony - start) + " bytes."
.print "End of non movable: $" + toHexString(endOfNonMovable - 1)
.print "Beginning of music data: $" + toHexString(MUSIC_MEM)
.print "Bytes left: " + (MUSIC_MEM - endOfNonMovable)
.print "Bytes left: " + (MUSIC_MEM - endOfNonMovable)
.print "Copper list(s) size: " + (copperListEnd - copperList) + " bytes."
.print "Music location = $" + toHexString(music.location)
.print "Music original location = $" + toHexString(musicData) + " - $" + toHexString(musicDataEnd - 1)
.print "Music size = " + music.size
.print "Intro tune (the Glitch) = $" + toHexString(intro.location) + ", size " + intro.size + ", init $" + toHexString(intro.init) + " play $" + toHexString(intro.play)
.print "Music init address = $" + toHexString(music.init)
.print "Music play address = $" + toHexString(music.play)

.print "--- movables ---"

.print formatRange("Movable music", musicData, musicDataEnd)
.print formatRange("Dashboard charset", dasboardCharset, dashboardCharsetEnd)
.print formatRange("Font", font, fontEnd)
.print formatRange("Game end", gameEnd, gameEndEnd)
.print formatRange("Second sprite bank", secondSpriteBank, secondSpriteBankEnd)
.print formatRange("Third sprite bank", thirdSpriteBank, thirdSpriteBankEnd)
.print formatRange("First sprite bank", firstSpriteBank, firstSpriteBankEnd)
