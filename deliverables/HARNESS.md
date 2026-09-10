# The harness as an API: minimal64, headless, scripted

`tools/m64-harness/m64run` runs a PRG on a natively compiled minimal64 (nopsta's emulator, the one
stored on Ethereum; GPL-2.0), with no Commodore ROMs, no display, about ten times real time, and a
script that drives the joystick, reads and writes memory, keeps and restores the machine, and takes
screenshots. The benches (`tools/verify_body.py`, `tools/verify_brain.py`, `tools/verify_build.py`)
are scripts of it; a training rig is the same thing with a loop around it. Everything is
deterministic: the same PRG and the same script give the same bytes.

## Running

```
tools/m64-harness/m64run PRG "cmd,cmd,cmd"        # commands separated by commas
tools/m64-harness/m64run PRG @FILE                # one command per line; a line starting with # is a comment
```

Output is text on stdout, one line per command that answers (`peek $6c34 = $1a`, `sync raster 0`,
`load $7410 +100 <- file`, `shot file (384x284)`). Build it once with `tools/m64-harness/build.sh
/path/to/minimal64` (it copies the emulator's sources beside the harness and compiles them).

## Commands

| command | what it does |
|---|---|
| `wait:N` | run exactly N PAL frames. Every frame ends at raster line 0, the frame boundary, where neither interrupt handler is running and the top handler is about to start: a peek there sees whole frames, a poke lands before the frame's handlers |
| `sync` | run on to the next raster line 0 unless already there. After `wait` it is free; use it before peeks that follow a `joy` or a `hold` |
| `joy:MASK:N` | press joystick lines MASK for N frames, release, and run 5 more frames. MASK: 1 up, 2 down, 4 left, 8 right, 16 fire, added |
| `hold:MASK` | press lines MASK and leave them pressed (no frames run) |
| `release:MASK` | release lines MASK (no frames run: pair with `wait`) |
| `key:CODE:N` | hold a key for N frames (the emulator's `keyboard.h` codes) |
| `peek:ADDRHEX` | print one byte |
| `poke:ADDRHEX:VALHEX` | write one byte |
| `load:ADDRHEX:FILE` | write a whole file into memory at the address (a weight set in one line) |
| `dump:ADDRHEX:LENHEX:FILE` | write LEN bytes of memory to a file |
| `snapshot` | keep the machine as it is now. The process forks: the commands up to the next `restore` run in a child; then the parent, still at the snapshot, goes on with the commands after that `restore`, forking again if another `restore` follows. So `snapshot, episode, restore, episode, restore, tail` runs each episode from the same state, and the tail from it too |
| `restore` | back to the snapshot: ends the current episode |
| `shot:FILE.ppm` | the last completed frame as a binary PPM, 384 x 284; the visible area is at (32, 40), 320 x 200 |
| `audio:FILE.wav`, `audio-stop` | record what the SID plays as a 16-bit mono WAV at 44.1 kHz |
| `pc` | print the program counter |

A command the harness does not know is ignored without a message, so check the output when a
script misbehaves. In a script file (`@FILE`) a line starting with `#` is a comment.

**Interactive mode.** `m64run PRG -` reads command lines from standard input and answers `ok` after
each one is done, its peeks printed before it. A rig that must decide as it goes (a teacher that reads
his senses and presses the stick every think period) writes a line, reads to the `ok`, decides, and
writes the next; the machine holds still between lines. `tools/teach_demo.py` wraps it in a dozen lines
(`Machine.do`).

## Addresses: the symbol file and the markers

Every build writes `src/kickass/NAME.sym` with a line per label, `.label name=$addr`. Read it and
address by name; the addresses move between builds. The benches do:

```python
import re
SYM = {}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open("src/kickass/tony-body.sym").read()):
    SYM.setdefault(m.group(1), int(m.group(2), 16))
```

Two blocks are also findable without the symbol file, by their marker at a page boundary in the PRG
and in memory: `MURAL02` (the Chamber's parameter block: seed, block digits, behaviour, colour) and
`BRAIN01` (the brain slot: header, weights, mood; `BODY.md`, "The brain slot"). The names the body
exposes for a rig, all in the symbol file:

| name | what |
|---|---|
| `physPlayerX` (word), `physPlayerY`, `physPlayerState` | Tony |
| `cloneX` (word), `cloneY`, `cloneState`, `cloneBGCollision`, `cloneBGCollisionExt` | the clone's record (his physics block while it is swapped out, which is any time a peek after `sync` sees it) |
| `cloneJoy`, `cloneJoyOverride` | the joystick byte the brain wrote this frame; the override (bit 7 set: bits 0 to 6 replace it every frame until cleared) |
| `cloneSenses` (20), `cloneSensesFrame` (word) | the published sense block and the frame it describes (`BODY.md`, "The sense block") |
| `senseRaw` (14), `sensePack` (20), `sensePackFrame` (word) | the raw values of the last turn and the packer's output for them, for a twin's check |
| `brainMarker`, `brainKind`, `brainLineage`, `brainRule`, `brainWeights` (256), `brainMood` (8) | the slot (`BODY.md`, "The brain slot"); `brainKindNow` is the kind the turn uses, 0 when the slot is malformed |
| `brainAction`, `brainThinks` (word), `brainAcc` (20) | the last think's choice, the count of thinks, the accumulators |
| `brainTestRun`, `brainTestIn` (20), `brainTestAcc` (20), `brainTestAction` | the network test hook |
| `brainLearnRun`, `brainLearnTestT`, `brainLearnTestP`, `brainLearnTestTook` | the learning hook: senses in `brainTestIn`, the taught action, out come the prediction and whether the lesson was taken; the weights change in place |
| `teachMode`, `teachHold`, `teachWas`, `cloneFlash` | teaching on or off (poke it, or the chord sets it); the chord's frame count (255 once it has toggled); the override's release flag; the flash's frames left |
| `lessonMarker` (`LESSON1`, page-aligned), `lessonCount` (word), `lessonTotal` (word), `lessonData` | the lesson block (`BODY.md`, "TEACH"): the lessons taken this session, 11 bytes each |
| `TEACH_SHADOW` (256), `shadowValid` | the weights as they were when the chord was pressed, put back if the hold toggles |
| `bodySelfTestRun`, `bodySelfTestBad` (word), `bodySelfTestDone` | the collision sweep |
| `bodyFrames` (word), `bodyRasterMax`, `bodyRasterFrame` (word), `bodyOverruns` | the frame counter and the raster watch |
| `buildCount`, `currentChamberNumber`, `buildLadderCol` | the room's brick count, the room, the seeded ladder's column |
| `$D015`, `$D00A`, `$D00B` | sprites enabled; sprite 5's position (the clone's) |
| `$C000` + row * 40 + column, `$BE00` + code | the screen, the materials table |

## The sweep pattern

The way this project proves a twin: a self-test inside the program runs two implementations over
every input and counts the differences, and the bench asserts zero. For the collision check
(`bodySelfTest`) the inputs are positions, swept in steps of eight over the whole room, and the outputs
are the four flag bytes. For the network (`brainTestRun`) the inputs are too many to enumerate, so the
bench pokes random weights, moods and senses (the all-zero and the extreme vectors among them), runs the
6502's forward pass through the hook, and compares all ten accumulators and the chosen action with the
Python reference; every recorded sense block is a vector too. Both are in `tools/verify_brain.py` and
`tools/verify_body.py`.

## One worked episode

`tools/harness-examples/episode.m64`, written against this build's symbol file (regenerate the
addresses for another build):

```
# One worked episode on tony-body.prg (addresses from src/kickass/tony-body.sym, this build). Boot and let the
# level settle, keep the machine, load a brain, teach him for twenty frames with the override, let the brain
# drive, read his senses; then the same start with another brain; then the start itself.
wait:300
snapshot
load:7510:deliverables/brains/follow-two-weights.bin
poke:7508:01
poke:6CC6:88
wait:20
poke:6CC6:00
wait:100
sync,peek:6CD1,peek:6CD2,peek:80AF,peek:80B0,peek:809B,peek:809C,peek:809D,peek:809E,peek:809F,peek:80A0,peek:80A1,peek:80A2,peek:80A3,peek:80A4,peek:80A5,peek:80A6,peek:80A7,peek:80A8,peek:80A9,peek:80AA,peek:80AB,peek:80AC,peek:80AD,peek:80AE,peek:7618,peek:761A,peek:761B,peek:6CB0,peek:6CB1,peek:4867,peek:4868
restore
load:7510:deliverables/brains/build-left.bin
poke:7508:01
wait:150
sync,peek:6CD1,peek:6CD2,peek:80AF,peek:80B0,peek:809B,peek:809C,peek:809D,peek:809E,peek:809F,peek:80A0,peek:80A1,peek:80A2,peek:80A3,peek:80A4,peek:80A5,peek:80A6,peek:80A7,peek:80A8,peek:80A9,peek:80AA,peek:80AB,peek:80AC,peek:80AD,peek:80AE,peek:7618,peek:761A,peek:761B,peek:6CB0,peek:6CB1,peek:4867,peek:4868
restore
sync,peek:6CD1,peek:6CD2,peek:80AF,peek:80B0,peek:809B,peek:809C,peek:809D,peek:809E,peek:809F,peek:80A0,peek:80A1,peek:80A2,peek:80A3,peek:80A4,peek:80A5,peek:80A6,peek:80A7,peek:80A8,peek:80A9,peek:80AA,peek:80AB,peek:80AC,peek:80AD,peek:80AE,peek:7618,peek:761A,peek:761B,peek:6CB0,peek:6CB1,peek:4867,peek:4868
```

Boot and let the level settle (`wait:300`); keep the machine (`snapshot`); load the two-weight follow
brain into the slot's weights and set its kind to 1; hold the clone's joystick byte to "right" for twenty
frames through the override (teaching: he walks right whatever the brain says, and the think keeps
running); let go; a hundred frames of the brain; then `sync` and the reads: the frame counter, the sense
block with the frame it describes, the last action, the count of thinks, both positions. `restore`
returns to the snapshot and the second episode loads the build-left brain instead; the last `restore`
returns once more and the final reads describe the snapshot itself.

The run's output, decoded (`tools/harness-examples/episode.out` has the raw lines):

```
prg src/kickass/tony-body.prg: 49348 bytes
load $7510 +100 <- deliverables/brains/follow-two-weights.bin
poke $7508 <- $01
poke $6cc6 <- $88
poke $6cc6 <- $00
sync raster 0
load $7510 +100 <- deliverables/brains/build-left.bin
poke $7508 <- $01
sync raster 0
sync raster 0
episode 1, taught right for 20 frames then the follow brain for 100: frame 372, the block describes frame 371
   senses: bias 7, dx 0, dy 0, facingRight 7, onGround 7, inAir 0, onLadder 0, ducking 0, floorBelow 7, wallAheadFoot 0, wallAheadHead 0, brickAheadFoot 0, ladderHere 0, ladderBelow 0, buildable 7, playerAir 0, lastAction 0, still 6, playerDuck 0, playerOnLadder 0
   action 0, thinks 30, the clone at X 186, Tony at X 184
episode 2, the build-left brain for 150 frames: frame 402, the block describes frame 400
   senses: bias 7, dx 6, dy -5, facingRight 0, onGround 7, inAir 0, onLadder 0, ducking 0, floorBelow 7, wallAheadFoot 7, wallAheadHead 7, brickAheadFoot 0, ladderHere 0, ladderBelow 0, buildable 0, playerAir 0, lastAction 0, still 6, playerDuck 0, playerOnLadder 0
   action 0, thinks 37, the clone at X 59, Tony at X 184
the snapshot itself: frame 252, the block describes frame 251
   senses: bias 7, dx 4, dy 0, facingRight 7, onGround 7, inAir 0, onLadder 0, ducking 0, floorBelow 7, wallAheadFoot 0, wallAheadHead 0, brickAheadFoot 0, ladderHere 0, ladderBelow 0, buildable 7, playerAir 0, lastAction 0, still 7, playerDuck 0, playerOnLadder 0
   action 0, thinks 0, the clone at X 146, Tony at X 184
```

The first episode: after the taught twenty frames of right the follow brain brought him back beside
Tony, within sixteen pixels, and the block published one frame behind the physics describes the frame
before. The second: the build-left brain climbed a staircase up to the left pillar, five bricks above
Tony, and stopped when the slot ahead was the pillar. The last reads are the snapshot itself, three
hundred frames in, before any brain: the clone at 146 beside Tony at 184, no thinks yet.

A teaching episode is the same shape with the port instead of the override: `poke teachMode 1`, then
`hold`, `wait` and `release` as a player would, and the reads add `lessonTotal`, `brainKind` and the
weights; `tools/teach_demo.py` is that, six times over, with the interactive mode for the sessions.
