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

// "The Chamber" - the tall Colonnade with a brick ceiling (full 25 rows, no
// dashboard), two bats up high (sprites 3+4), the green buddy Tony (sprites
// 5+6, engine code in tony-chamber.asm) and a back wall drawn at run time
// from the seed block below. Map: tools/build_chamber_room.py; generator:
// tools/make_chamber.py; seed: tools/stamp_mural.py.

#import "../../_constants.asm"
#import "../../_load-util.asm"
#import "../../_objects.asm"
#import "../../_compress.asm"

.label NO = 255

level_startRoom:        .byte 0
level_startPositionX:   .word 184   // centre of the room
level_startPositionY:   .byte 180   // drops to the floor at row 23
level_startState:       .byte STATE_ON_GROUND_LEFT

.var _level_roomPtrs = List()
.var _level_roomExitsN = List()
.var _level_roomExitsE = List()
.var _level_roomExitsS = List()
.var _level_roomExitsW = List()
.var _level_usedCharsPtrs = List()
.var _level_usedCharsSize = List()
.var _level_objectsControlPtrs = List()
.var _level_objectsPositionXPtrs = List()
.var _level_objectsPositionYPtrs = List()
.var _level_movableObjectsValue2Ptrs = List()
.var _level_objectSizes = List()

.macro _level_pack(name, exitN, exitE, exitS, exitW, staticObjects) {
    .var data = LoadBinary(name)

    roomStartAddress: compressRLE3(data, $ff)

    // define exit lists
    .eval _level_roomPtrs.add(roomStartAddress)
    .eval _level_roomExitsN.add(exitN)
    .eval _level_roomExitsE.add(exitE)
    .eval _level_roomExitsS.add(exitS)
    .eval _level_roomExitsW.add(exitW)

    // calculate used chars
    .var usedChars = Hashtable()
    .for (var i = 0; i < data.getSize(); i++) {
        .var charCode = data.get(i)
        .if (charCode != 0) {
            .eval usedChars.put(charCode, charCode)
        }
    }
    .var keys = usedChars.keys()
    .eval _level_usedCharsSize.add(keys.size() + 1)

    .print "Used chars for " + name + " = " + (keys.size() + 1)
    .assert "Room chars fits assumed buffer", (keys.size() + 1) <= MAX_BG_CHARS,  true

    usedCharsStartAddress:
        .byte 0
        .fill keys.size(), usedChars.get(keys.get(i))

    .eval _level_usedCharsPtrs.add(usedCharsStartAddress)

    .var soControl = List()
    .var soPositionX = List()
    .var soPositionY = List()
    .var moValue2 = List()

    .for (var i = 0; i < staticObjects.size(); i++) {
        .var staticObject = staticObjects.get(i)
        .var control = staticObject.type + (staticObject.value << 4)
        .eval soControl.add(control)
        .eval soPositionX.add(staticObject.positionX)
        .eval soPositionY.add(staticObject.positionY)
        .if (isMovable(staticObject)) {
            .eval moValue2.add(staticObject.value2)
        }
    }

    _soControl: .fill soControl.size(), soControl.get(i)
    _soPositionX: .fill soPositionX.size(), soPositionX.get(i)
    _soPositionY: .fill soPositionY.size(), soPositionY.get(i)
    _soValue2: .fill moValue2.size(), moValue2.get(i)

    .eval _level_objectsControlPtrs.add(_soControl)
    .eval _level_objectsPositionXPtrs.add(_soPositionX)
    .eval _level_objectsPositionYPtrs.add(_soPositionY)
    .eval _level_movableObjectsValue2Ptrs.add(_soValue2)
    .eval _level_objectSizes.add(soControl.size())
}

// THE COLONNADE - the one and only chamber; all exits sealed.
chamberColonnade: // 0
    _level_pack("chamber-room.bin", NO, NO, NO, NO, List().add(
        objectExt(SO_BAT, 0, 5, 3, 0),      // two bats, each in its own air
        objectExt(SO_BAT, 0, 27, 4, 1)      // territory (sprites must not touch)
    ))

// The parameter block. A contract (or tools/stamp_mural.py) overwrites the 42
// bytes after the marker: 32 seed bytes (the block hash), 8 block-number
// digits, the behaviour byte and the colour byte. The marker makes the block
// findable in any build; 64-aligned so it never crosses a page.
.align 64
muralMarker:     .byte $4D, $55, $52, $41, $4C, $30, $32, $00   // "MURAL02\0"
muralSeed:       .byte $C8, $3F, $A3, $8F, $73, $CA, $43, $B5, $26, $1D, $05, $9C, $B8, $3A, $8A, $B7, $17, $D2, $64, $39, $36, $49, $34, $68, $4C, $5E, $21, $83, $12, $84, $BE, $8C
muralBlock:      .byte 2, 5, 8, 5, 0, 2, 6, 7                   // block 25850267
muralBehaviour:  .byte 0                                        // 0 Follow, 1 Dance
muralColour:     .byte 5                                        // green, the buddy's original colour
muralBats:       .byte 0, 0, 0, 0, 0, 0, 0, 0                   // written by the game at room entry, for the tests:
                                                                // presence, pathA, colA, rowA, pathB, colB, rowB, 0

materials:
    .import binary "chamber-materials.bin"

level_fire:
    #import "../demo/bitmaps/fire.asm"
level_door:
    #import "../demo/bitmaps/door.asm"
level_doorcode:
    #import "../demo/bitmaps/doorcode.asm"
level_key:
    #import "../demo/bitmaps/key.asm"
level_keycode:
    #import "../demo/bitmaps/keycode.asm"
level_potion:
    #import "../demo/bitmaps/potion.asm"
level_jewel:
    #import "../demo/bitmaps/jewel.asm"
level_snakeLeft:
    #import "../demo/bitmaps/snake-left.asm"
level_snakeRight:
    #import "../demo/bitmaps/snake-right.asm"
level_pikes:
    #import "../demo/bitmaps/pikes.asm"
level_stones:
    #import "../demo/bitmaps/stones.asm"


level_roomPtr:              .lohifill   _level_roomPtrs.size(),         _level_roomPtrs.get(i)
level_usedCharsPtr:         .lohifill   _level_usedCharsPtrs.size(),    _level_usedCharsPtrs.get(i)
level_usedCharsCount:       .fill       _level_usedCharsSize.size(),    _level_usedCharsSize.get(i)
level_roomExitsN:           .fill       _level_roomExitsN.size(),       _level_roomExitsN.get(i)
level_roomExitsE:           .fill       _level_roomExitsE.size(),       _level_roomExitsE.get(i)
level_roomExitsS:           .fill       _level_roomExitsS.size(),       _level_roomExitsS.get(i)
level_roomExitsW:           .fill       _level_roomExitsW.size(),       _level_roomExitsW.get(i)

level_objectControlPtr:     .lohifill   _level_objectsControlPtrs.size(),   _level_objectsControlPtrs.get(i)
level_objectPositionXPtr:   .lohifill   _level_objectsPositionXPtrs.size(), _level_objectsPositionXPtrs.get(i)
level_objectPositionYPtr:   .lohifill   _level_objectsPositionYPtrs.size(), _level_objectsPositionYPtrs.get(i)
level_movableObjectValue2Ptr:
                            .lohifill   _level_movableObjectsValue2Ptrs.size(), _level_movableObjectsValue2Ptrs.get(i)

level_objectSizes:          .fill       _level_objectSizes.size(),          _level_objectSizes.get(i)

level_roomStates:           .fill       30, 0

// bat flight paths, eight of them, chosen per bat from the seed at every
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

demoLevelCharset: {
    loadNegated("chamber-charset.bin")
}
demoLevelCharsetEnd:
