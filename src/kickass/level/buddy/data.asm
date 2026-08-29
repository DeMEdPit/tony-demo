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

// "The Colonnade + Buddy" - the TALL pillar chamber (full 25 rows, no
// dashboard) with two bats up high (sprites 3+4). Sprites 5+6 carry the
// green buddy Tony, which is engine code in tony-buddy.asm, not a level
// object. Map: tools/build_tall_room.py.

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
    _level_pack("pillar-room-tall.bin", NO, NO, NO, NO, List().add(
        objectExt(SO_BAT, 0, 5, 3, 0),      // two bats, each in its own air
        objectExt(SO_BAT, 0, 27, 4, 1)      // territory (sprites must not touch)
    ))

materials:
    .import binary "demo-level-materials.bin"

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

// bat flight paths: long glides with slight rises and dips, all up high
path0:          .byte   16, 0, 4, 1, 4, -1, 4, -1, 4, 1    // left third, X 64-128
path1:          .byte   12, 0, 3, -1, 3, 1, 3, 1, 3, -1     // right, X 240-288

pathsPtrsLo:    .byte <path0, <path1
pathsPtrsHi:    .byte >path0, >path1
pathLengths:    .byte 10, 10

demoLevelCharset: {
    loadNegated("demo-level-charset.bin")
}
demoLevelCharsetEnd:
