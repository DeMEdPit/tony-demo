# The body (tony-body.prg): the clone on Tony's own physics

The building demo's next step, for the owner to play and for the brain session to build on: the
second Tony (the Shadow) no longer moves by a hand-written rule with a fixed floor. He is run through
the player's own physics, a second time each frame, from a record of his own, and fed a one-byte
joystick that a brain writes. The first brain is the Chamber's follow rule, as joystick bits; the
second is whatever you teach him, with the stick, while you play (TEACH, below). Nothing
here touches the frozen base (`tony-chamber.prg`, sha256 `67dc97bc1e306715...`) or the building demo
(`tony-build.prg`, sha256 `5c24a63e1c14e26c...`); both are byte for byte what they were.

| | |
|---|---|
| file | `deliverables/prg/minimal64/tony-body.prg` |
| size | 49,348 bytes |
| sha256 | `9976be313ca35a680ba70f75e137eff1b951a3bebeab15fcd2376f25333414e3` |
| boots on | minimal64 (the benches in `tools/verify_body.py`, `tools/verify_brain.py`, `tools/brain_golden.py check` and `tools/teach_demo.py`, all passing); a plain PRG for VICE, READY 64 or the browser launcher, joystick in port 2 |
| built from | the building demo's generator with one more option: `tools/make_chamber.py --variant tony-body --build-demo --body`, then `tools/build_demo.sh tony-body` |
| the builder file | `deliverables/prg/minimal64/tony-body-builder.prg`, the same program with the slot's kind byte assembled as 2 (`--brain-kind 2`), sha256 `4a0fdf34511132635c48fb8403e6507da2ed4878dc94dcb074be79c0c10531bc`, one byte different: the builder brain from the start, for play; teaching does not touch a kind 2 brain |
| diff | `deliverables/build-demo/tony-body.diff`, the body's source against the building demo's (the clone's code is the bulk of it) |
| bench output | `deliverables/build-demo/verify-body.txt` (the body), `verify-brain.txt` (the senses, the slot, the builder), `golden-check.txt` (the learning rule against the reference's golden vectors), `teach-demo.txt` (teaching end to end, with the number) |

## What you see

Everything the building demo does (two rooms, down + fire lays a brick, up + fire steps onto it, the
seeded ladder), and the green Tony now moves like you do:

- He **walks** two pixels a frame, **stops** in front of a brick you lay between you (by the physics, not
  by a rule: his walk state is blocked by the wall material and his position reset, exactly as yours),
  **falls** off an edge and lands, **jumps in the same frame you jump** (the same 26-frame arc, so you
  land together), **ducks when you duck**, and stands up again.
- He does not leave the room: while you are in the room above he waits where he stood, and he is
  there when you come back. He cannot die (there is nothing that kills in these rooms, and the death
  path is not run for him anyway).
- His brain boots as the follow rule, so at first he does not build or climb on his own. Hold down
  with fire for a second and the stick is his: while you drive him, what you do in each situation is a
  lesson, and when you let go he does what he was taught (TEACH, below). The bench drives him through
  a staircase and up the ladder with the joystick byte, and teaches him to climb to you in four short
  sessions.

Screenshots (minimal64): `deliverables/screenshots/body-start-m64.png` (the two at the start),
`body-follow-m64.png`, `body-jump-m64.png` (the same frame of the same jump), `body-wall-m64.png` (a brick
between them), `body-clone-stairs-m64.png` (his own three-brick staircase, built on the bench's byte),
`body-clone-north-stop-m64.png` (hanging at the top of the ladder), `body-blocked-m64.png` (his own stairs
in his way: the follow rule does not jump), `body-room-above-m64.png`.

## What the body is

The engine's physics (`physics-tall.asm`) keeps its state in one block of twenty bytes, `physPlayerX`
through `_phys_stateChange` (position, next position, the three collision flag bytes, state, allowed
state, animation, command, facing, the ladder adjustment, the jump phase, the proposal). The clone has a
copy of those twenty, `cloneRec`, laid out the same (its labels are derived from the physics block's
own, and asserted at assembly). Every frame, after the player's turn and the actors:

1. `cloneThink` writes his joystick byte (the follow rule).
2. `cloneSwap` exchanges the record with the physics block.
3. The same routines run on it: the build verb for bits 5 and 6, `dispatchPlayerCommand` with the byte
   in the port's sense, `phys_transitState`, `phys_executeState`, the collision check, `phys_blockMovement`,
   the collision check again when he was blocked or adjusted. State changes go to his own animation slot
   (`cloneOnStateChange`), not the player's.
4. `cloneSwap` again. The record is his; the physics block is the player's, untouched.

What is not run for him: the room-change check, the kill check, the collectible check, the sprite
collision handling. Two guards: he climbs no higher than Y 56 (`CLONE_NORTH_STOP`; the up bit is masked
from there, so he hangs on the ladder in view instead of leaving through the ceiling), and the joystick
debounce (`joyHandlingForBorg`, three frames of delay when fire is held) is the player's alone: the
clone's byte is taken as it is.

His sprites (5, 6, and 7 for the backdrop) are placed from the record where the player's are placed
from the physics block, and his frames come from the player's own animation tables through a small
animator that mirrors `ani_animatePlayer` (the engine's animator writes the player's sprite pointers
by fixed address, so it could not be reused by index). So he wears the walk, the jump, the duck, the
ladder and the idle exactly as the player does, in his colour.

The building demo's hand-moved buddy (`buddyUpdate`) is gone from this build; the Chamber's other
behaviours (Dance, Wanderer, Sleeper, Echo, Glitch) are still assembled but not called. The build verb's
"is the other Tony in the slot" test reads the record, which holds whoever is not having his turn.

## The joystick byte

`cloneJoy`, one byte a frame, a set bit is a pressed line:

| bit | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| | up | down | left | right | fire | lay or lift | step up | (unused) |

Bits 0 to 4 go through the game's own dispatch, so the combinations mean what they mean for the player
(fire with a direction is a jump that way, down on the floor is a duck, up at a ladder climbs). Bits 5
and 6 act on their rising edge, like the player's chords. A brain writes the byte in `cloneThink`;
**`cloneJoyOverride`** with bit 7 set replaces it with the override's low seven bits, every frame, until
cleared. That is the hook for a bench and for a trainer: poke a byte, he does it. The bench uses it to
walk him to a spot, build a staircase of three, walk him off it, jump him, build five under the ladder
and send him up it.

## The sense block

The contract the Python reference is built from. Twenty senses, one byte each at `cloneSenses`, the
value in the low nibble and the high nibble zero. Every value is a signed nibble in two's complement
(`-8` to `7`, so `F` is `-1`): a reader sign-extends the low four bits. Flags are `0` or `7`, buckets
run `-7` to `7`, the bias is `7`, so every sense has the same reach against a nibble weight. The block
carries the frame it describes in `cloneSensesFrame` (a 16-bit count of frames the physics have run
since the level started, `bodyFrames`). "Ahead" is the column just past his collision box the way he
faces; his box is columns `X/8 - 2` and `(X+8)/8 - 2`, rows `Y/8 - 6` (the top) to the top plus 3 (the
feet), the far row one below the feet, as the engine counts them.

| # | name | value |
|---|---|---|
| 0 | bias | always 7 |
| 1 | dx | the player's X minus his: the sign, and a bucket of the distance in pixels. 0 under 8, 1 under 16, 2 under 24, 3 under 32, 4 under 48, 5 under 64, 6 under 128, 7 from 128; negative when the player is to his left |
| 2 | dy | his Y minus the player's, in bricks: `min(7, (abs + 8) / 16)`, 7 from 120 pixels; positive when the player is above him |
| 3 | facingRight | 7 when his state's bit 7 is set |
| 4 | onGround | 7 in states 0, 1, 3 (standing, walking, ducking) |
| 5 | inAir | 7 in states 4, 5, 6 (jumping sideways, jumping up, falling) |
| 6 | onLadder | 7 in states 2, 7 (climbing, stopped on a ladder) |
| 7 | ducking | 7 in state 3 |
| 8 | floorBelow | 7 when the far row under him holds wall material (the engine's FLOOR_FAR flag) |
| 9 | wallAheadFoot | 7 when the cell ahead at his feet row holds wall material |
| 10 | wallAheadHead | 7 when the cell ahead at his top row holds wall material |
| 11 | brickAheadFoot | 7 when the cell ahead at his feet row is a placed brick (screen codes $50 to $53) |
| 12 | ladderHere | 7 when a ladder is in his box (the engine's LADDER flag) |
| 13 | ladderBelow | 7 when a ladder is in the far row or its top is at his feet (LADDER_FAR or LADDER_TOP) |
| 14 | buildable | 7 when the slot ahead can take a brick now by the verb's own rules: his feet on something (states 0, 1, 3), the level whole (`(19 - top)` even, 0 to 18), the slot's left column in 5 to 33 (past his right column made odd when facing right, before his left column made even less one when facing left), its four cells empty or a mural brick, and the player's box not touching it |
| 15 | playerAir | 7 when the player's state is 4, 5 or 6 |
| 16 | lastAction | the action applied to him this frame, read from the joystick byte: 0 idle, 1 left, 2 right, 3 up, 4 down, 5 jump, 6 jump left, 7 jump right, 8 build left, 9 build right (a lay or step-up bit, the way he faces); left before right, jump before the lines |
| 17 | still | frames since he last moved, a bucket: 0 moved this frame, 1 under 4, 2 under 8, 3 under 16, 4 under 32, 5 under 64, 6 under 128, 7 from 128 |
| 18 | playerDuck | 7 when the player's state is 3 |
| 19 | playerOnLadder | 7 when the player's state is 2 or 7 |

Cells off the screen (a row below 0 or above 24) read as empty. Rows and columns change only every
eight pixels, which is why the collision self-test sweeps in steps of eight.

**How it is produced, and what a reader may rely on.** At the end of his turn, while his record is
swapped in, the raw values of that frame are copied whole to `senseRaw`: his X, Y, state, the two
collision flag bytes, the player's X, Y, state, the joystick byte applied to him, his still counter, and
the frame. The main loop packs them into `sensePack` (`bodySensePack`, once per frame, a pure function
of the raw block and the map), and the next turn publishes `sensePack` as `cloneSenses` with the
frame stamp. So the interrupt pays only for the copies, and a reader that samples between turns (the
harness's `sync`, which stops in the top border) always sees a whole block, describing the frame stamped
in it, normally one or two frames behind the physics. The bench (`tools/verify_brain.py`) recomputes
every nibble in Python from `senseRaw`, the screen and the materials table at a dozen snapshots, and
they agree nibble for nibble; the reference should be written from the table above and checked the
same way.

## The brain slot

A page-aligned block found by its marker, the way the Chamber's `MURAL02` block is found: a hex
editor finds `BRAIN01` in every exported program, and the symbol file names it (`brainMarker`, at
$7400 in this build) until a freeze fixes it. A contract stamps the header, the weights and the mood at
render; `prg(id)` carries them to a real C64.

| offset | bytes | field |
|---|---|---|
| 0 | 8 | the marker, `BRAIN01` and a zero |
| 8 | 1 | kind: 0 no network, the follow rule drives and the weights are ignored (the page says "no brain yet"); 1 a perceptron over this layout; 2 the builder rule, hand-written, no weights. Live teaching turns 0 into 1 on the first lesson taken |
| 9 | 1 | layout: 1, the sense packing above and the action vocabulary below |
| 10 | 1 | inputs, 20 |
| 11 | 1 | hidden, 0 for the perceptron |
| 12 | 1 | outputs, 10 |
| 13 | 1 | period, frames between thinks, 4 |
| 14 | 1 | lineage bits, the contract's (the program does not read them) |
| 15 | 1 | rule version: 1, the learning rule below. The program treats 2 and up as malformed |
| 16 | 256 | the weights. Kind 1 uses the first 100: output `o`'s twenty weights are nibbles `o * 20` to `o * 20 + 19`, two per byte, the first of each pair in the low nibble, so `w[o][i]` is byte `16 + o * 10 + i / 2`, low nibble for even `i`, high for odd. Signed, two's complement |
| 272 | 8 | the mood: ten signed nibbles in the same packing (five bytes used), `m[o]`. A render's nudge, never part of a saved brain |

**A malformed slot is kind 0.** Every think starts with `brainCheck`: the marker, layout 1, a kind
under 3, twenty inputs, no hidden units, ten outputs and a rule version under 2, or the effective kind
(`brainKindNow`, the one the turn reads) is 0 and the follow rule drives. A page that writes a slot the
program does not understand gets the follow rule, never garbage.

**The forward pass, exactly.** For each output `o`, `acc[o]` is a 16-bit two's complement sum of
`w[o][i] * x[i]` over the twenty senses, each product a signed byte from the 256-entry table indexed by
the two nibbles, plus `m[o] * 16`. The bound is 20 × 64 + 128 = 1408 in magnitude, so 16 bits never
overflow; the bench's sweep includes the extremes. The action is the first output with the largest
accumulator (ties go to the lowest index). The accumulators are left in `brainAcc` (low byte, high
byte, per output) and the action in `brainAction`, which the decoder reads every frame. The Python
reference is three lines: `acc[o] = sum(w[o][i] * x[i]) + m[o] * 16`, `action = max(range(10), key=lambda
o: (acc[o], -o))`, with every nibble sign-extended. The bench (`verify_brain.py`, "forward sweep") pokes
random weights, moods and senses into the test hook and compares all ten accumulators and the action
over forty vectors, the all-zero and the two extreme cases among them.

**The think.** In the main loop, every `period` frames (counted in `bodyFrames`), for kinds 1 and 2:
the published sense block is copied whole with the interrupts off, the forward pass runs (about two
frames of main-loop time, interruptible, reading nothing the interrupt writes), and `brainThinks`
counts. Kind 0 thinks nowhere: the follow rule runs in his turn as before. The think runs whether or
not the override holds his joystick, so teaching sees what he would have done.

**The test hook.** Poke the twenty senses into `brainTestIn`, the weights and mood into the slot, and 1
into `brainTestRun`: the next main-loop pass runs the forward pass on them, leaves the accumulators in
`brainTestAcc` and the action in `brainTestAction`, restores the live action and clears the flag. Two
frames of waiting are enough.

**The action vocabulary and the decoder.** Ten actions, one output each:

| # | action | the joystick byte |
|---|---|---|
| 0 | idle | 0 |
| 1 | left | bit 2 |
| 2 | right | bit 3 |
| 3 | up | bit 0 |
| 4 | down | bit 1 (a duck on the floor, a climb down on a ladder) |
| 5 | jump | bit 4 |
| 6 | jump left | bits 4 and 2 |
| 7 | jump right | bits 4 and 3 |
| 8 | build left | the macro, leftward |
| 9 | build right | the macro, rightward |

The decoder (`cloneDecode`) runs in his turn every frame for kinds 1 and 2 and turns `brainAction`
into `cloneJoy`. It owns two things the network must not: the **build macro**, five frames at most
(a frame of the direction if he is not facing that way, the lay bit, a frame of nothing that checks the
brick count rose and abandons the macro if the lay was refused, the step-up bit, a frame of nothing),
during which the think's choices are ignored; and the **release frame**: a byte without down after
one with it is preceded by a frame of nothing, because the physics allow no walk out of the duck
state. What the decoder emitted last is `cloneJoyOut`; the override still wins after it.

**Two weights, as a proof.** With `w[right][dx] = 7`, `w[left][dx] = -7` and `w[idle][bias] = 2` he
walks to within sixteen pixels of Tony and stops (a bucket of one is outweighed by the bias), and
follows him across the room. With `w[build left][buildable] = 7` and the same bias he builds a
staircase of nine bricks in two hundred frames, turning left first because the macro faces the way it
was told. Both are in the bench.

## The learning rule, and what a lesson is

The rule is the interface's (`BRAIN-INTERFACE-V1.md`, section 6), on the 6502 as `brainLearn`: the
mood-free prediction `p` (the forward pass with the mood left out), nothing when `p` equals the taught
action `t`, otherwise `w[t][i] += sgn(x[i])` and `w[p][i] -= sgn(x[i])` for every non-zero sense, each
nibble saturating at -8 and 7. Behind a test hook like the forward pass: poke the senses into
`brainTestIn`, the taught action into `brainLearnTestT` and 1 into `brainLearnRun`; the weights change
in place, `brainLearnTestP` gets `p` and `brainLearnTestTook` whether a lesson was taken.
`tools/brain_golden.py` holds the Python reference (`forward`, `learn`, `replay`), writes the golden
vectors in `deliverables/golden/` (`forward.json` 46 cases, `lessons.json` 27, `mood.json` 22) and checks
them on the 6502 through both hooks: 95 of 95 agree (`deliverables/build-demo/golden-check.txt`).

**What a lesson pairs.** A lesson is `(x, t)`: `x` is the published block, the state of one frame, and
`t` is the action applied in the frame *after* it, the one taken from that state. Not the block's own
sense 16, which is the action that *made* the state: a jump's first frame is already in the air, so
pairing a block with its own action teaches "in the air: jump" and never "on the ground with a wall
ahead: jump". The main loop has the next frame's packed block (`sensePack`) before the turn publishes
it, so `t` is `sensePack + 16` and the lesson is taken only when the two frames are consecutive
(`brainInFrame + 1 == sensePackFrame`; a pack missed because the main loop ran long is no lesson).

**When lessons are taken.** At every think tick (every `period` frames), and at every **edge**: a frame
whose applied action differs from the last frame's, a press or a release. The tick alone would see the
frame that launched a jump one time in four; the edge sees every press, whatever the period's phase,
and so a human's stick teaches as well as a rig's. A lesson taken flashes him white for six frames
(`cloneFlash`; his sprites' colour, 1 while it runs).

## The builder, a brain anyone can read (kind 2)

Kind 2 is a hand-written rule over the same senses and the same ten actions, so the decoder, the
macro and the senses were exercised by something legible before any weights existed, and so the
owner's two observations have their answer: he jumps a brick on his own, and he climbs the ladder to
you. The rule, in order:

1. In the air: nothing. The physics finish the jump.
2. On a ladder: up when the player is above, down when below, hang on when level.
3. The player above and a ladder in his box: up.
4. Nearer than 48 pixels to the player and not two bricks or more below him: wait. This keeps him out
   of the slot the player is building in (a first version walked up to within sixteen pixels and stood
   in it, and the player's lays were refused).
5. His way is toward the player, or the way he faces when level with him. Facing his way, a wall at
   his feet with his head clear is a step: jump it, that way. A wall at his head too is a climb: build a
   brick that way if the slot is free, else nothing.
6. Forty-eight pixels or more from the player: walk his way (which turns him if he faced away).
7. Nearer, well below him, with nothing ahead: build, the way he faces.

What it does in the bench: with a brick laid between them he jumps it and comes to within 48 pixels
of Tony; with Tony's five-brick staircase under the ladder and Tony part way up it, he walks to the
stairs, jumps each step (the jump from against a brick rises past its top and lands on it), reaches
the top brick under the ladder, and climbs to Tony's height, where he hangs. With the builder on
while Tony builds, he waits beside the stairs, one step behind as Tony climbs, all five bricks get
laid, and he follows up the ladder. Nothing in the follow rule could do any of it; the builder does
it from the senses alone. The first thing a trained brain has to beat is this rule.

## TEACH: teaching him with the stick

Two ways in. The page pokes `teachMode` to 1, and to 0 to stop. Or, on any stick, hold the lay chord,
down with fire, for a second (`TEACH_HOLD_FRAMES`, fifty frames): the press lays or lifts a brick as
always, and when the hold reaches the second that brick is taken back, teaching toggles, and the chord
is spent, dead for the player and for the clone until it is let go. A hold that turns teaching off also
takes back what its press taught: on the chord's first frame, while teaching, the weights, the kind and
the lesson counters are copied to a shadow (`TEACH_SHADOW`, $8900, 256 bytes) and put back when the
hold toggles. So the hold has no side effect, whichever way it toggles; the brick that appears and
vanishes is the cue. A tap, let go before the second, is a lay, and the lessons it taught stay. The
shadow copy is 57 raster lines and lands in the frame where the clone lays (a turn ending at 191, the
worst under teaching); it is not made when teaching is off, where Tony's own lay makes the heaviest
frame (188) and no lesson can happen anyway.

While teaching is on: Tony stands (his path sees no lines pressed); the port's byte goes to the
clone's override with the chords translated, fire with down the lay bit, fire with up the step-up bit,
the rest as they are; the think runs and the lessons are taken as above; the first lesson turns a
kind 0 brain into kind 1; the builder (kind 2) is never taught. `teachHold` counts the chord's frames
(255 once spent), `teachWas` clears the override when teaching ends. When the stick is let go the brain
drives with what it learned: he does what he was taught, not what the follow rule did. A reload
forgets; nothing here survives the program, and saving is the page's, from the lesson block below and
the slot.

**The lesson block, `LESSON1`.** Every lesson taken is recorded in order in a marked block at $8a00, in
the memory the level tune vacates when it is copied to $A000 at startup (the shadow is below it, and the
assembler refuses a build whose code reaches either). Found by its marker at a page boundary like the
others; the symbol file names it (`lessonMarker`).

| offset | bytes | field |
|---|---|---|
| 0 | 8 | `LESSON1` and a zero |
| 8 | 2 | count: lessons recorded, low byte first |
| 10 | 2 | capacity, 500 |
| 12 | 1 | a lesson's size, 11 |
| 13 | 2 | total: lessons taken this session, recorded or not (the buffer may be full) |
| 15 | 1 | zero |
| 16 | 11 each | the lessons: the twenty sense nibbles packed two per byte (nibble `i` in byte `i / 2`, low nibble for even `i`), then one byte with the taught action in its low nibble |

The page replays them over the saved brain with the rule (the interface's section 7); a lesson whose
replay finds `p == t` is a no-op and still counted.

**The number (E5).** `tools/teach_demo.py` runs the milestone end to end on the harness (output in
`deliverables/build-demo/teach-demo.txt`): kind 0 boots and follows; teaching through the flag and
through the chord, the stick walking him; the weights change and the first lesson makes him kind 1;
let go, he keeps walking right on his own brain where the follow rule would have stopped beside Tony;
a lesson flashes him white within the frame; a reload boots kind 0 with zero weights. Then the number:
Tony builds five bricks under the ladder and climbs it; a teacher (the builder's rule as joystick
lines, decided from the published block once every think period, through the harness's interactive
mode) drives the clone up the stairs and the ladder to him in 212 frames; then the same start with the
taught weights and the brain alone for 480 frames. Sessions from zero until he climbs to Tony on his
own:

| session | lessons | alone afterwards |
|---|---|---|
| 1 | 11 | stands at the foot of the stairs |
| 2 | 11 | jumps two steps, stops on the third |
| 3 | 7 | stands at the foot |
| 4 | 7 | climbs the stairs and the ladder to Tony |

**Thirty-six lessons in four sessions, from zero weights.** The step of one argues over the features
the states share (on the ground, the floor below, a wall ahead) between "jump" at the steps and "up" at
the ladder's foot, which is the swing of sessions 1 to 3; by the fourth the features that separate them
(the brick ahead, the ladder in the box, dy) carry it. The weights that climbed are
`deliverables/brains/taught-climb.bin`. The teacher never walks in this task (every state has a wall
ahead), so walking to Tony is not in these weights; the two-weight follow brain shows what that part
costs.

## Time, measured

Two Tonys on the physics did not fit the frame as the game schedules it, and the way it failed is worth
knowing: the game's top handler (physics, actors, music) is a copper entry at raster line 40 and the
visual handler (sprites) one at line 255. With the clone's turn added, the top handler ran past line 255
on some frames; the copper then arms the visual entry too late, the visual handler runs a frame later,
and the top entry is skipped the frame after that: both Tonys froze one frame in eight, which the bench
saw as walks that came up short. Four things fixed it, all in the body's generator patches:

- The top handler starts at line 0 instead of 40 (the upper border; nothing is drawn there).
- A collision check is ~30 raster lines and the game's loop runs two a frame regardless. Both Tonys now
  skip the first when the proposed position is the current one and the map has not changed since their
  flags were computed (`bodyCheckProposal`, a stale bit per Tony set by every routine that writes the
  map), and the second when the movement was not blocked or adjusted (`bodyBlockMovement`). A Tony
  standing still costs no check; walking, one; landing or blocked, two. The results are the same: the
  check reads only the map and the position.
- The check itself is rewritten (`checkBGCollision` in the body's code): the same scan in the same
  order (left column then right, five rows, the ladder columns noted as the game notes them) with a
  row's address set once, a cell read once, in line, and the ladder noted only where one is. It is
  about a fifth cheaper than the game's, not the half first estimated: a check is about 24 raster
  lines, and the saving that mattered was skipping the ones that cannot say anything new. The game's own instance is kept
  as `checkBGCollisionRef`, and **`bodySelfTest`** runs both over every distinct position (X and Y in
  steps of 8, X to 511, Y to 255: the columns and rows change no finer) and counts the positions where
  any of the four outputs differ. The bench runs it in the room below with five bricks laid and in the
  room above: zero differ. Poke `bodySelfTestRun` to run it in any state.
- The two bats' actors are gone from the body's level data (`level/body/data.asm`); the demo never
  showed them, and their path logic cost a few lines a frame.

With that, in the bench's worst frame (the two landing from the same jump at once, which every mirrored
jump produces) the clone's turn ends on raster line 188, the top handler's part of the frame is 0 to
188, the visual handler runs from 255 for about 36 lines, and the main loop has the rest, about 80
lines a frame. `bodyRasterMax` keeps the latest line a turn has ended on, `bodyRasterFrame` the frame
it happened in (`bodyFrames` counts the frames the physics have run), and `bodyOverruns` counts turns
that ended on line 250 or later (the level's first two frames are not watched: the copper's first
interrupt fires off-schedule on a stale raster flag, once). The bench asserts zero overruns and a
maximum below 230. The swap is unrolled (320 cycles each way); the clone's whole turn is about 45
lines when he stands, 70 walking, 100 landing, including the senses' raw copy.

The senses cost the interrupt about six lines (the raw copy and the publish); the packing itself runs
in the main loop. A first version packed everything in the turn and cost twenty lines, which put the
worst frame at 244: the interrupt's budget is the scarce one, and nothing else should go into it.
Teaching keeps to that: the lessons, at ticks and edges, run in the main loop like the think (a forward
pass and two rows of nudges), the chord's routing is a few lines in the player's part of the handler,
and the shadow copy (57 lines, a second version of the same lesson: it first landed in the frame of
Tony's own lay and put the worst frame at 244 again) is made only while teaching, where the lay is
the clone's and the frame ends at 191.

For a brain: the main loop's time, about 80 lines a frame, is where a think step runs, spread over
frames, writing `cloneJoy` when it finishes; the body reads the byte at the start of every turn, so a
brain that thinks every fourth frame works without any change here.

## Bench (`tools/verify_body.py`, output in `deliverables/build-demo/verify-body.txt`)

Thirty-three checks, each snapshot taken after the harness's new `sync` command (it runs on until the
raster is in the top border, lines 8 to 30, so a peek never lands inside a turn, where the record and
the physics block have changed places). Follow: the clone walks from 120 to within 40 pixels of Tony,
his sprites where his record says, follows to the right pillar and back to the left, ducks and stands
with him. Jump: the same frame, the same Y, together in the air, both back on the floor. Wall: a brick
between them stops him at X 158 in the walking state. Drive (the override): a hundred pixels left in
fifty frames, two pixels for one frame, a brick laid, a step up (Y 190), three bricks high (Y 158), off
the top down the stairs to the floor, a jump, and the brain back: he walks towards Tony until his own
stairs stop him. Ladder: five bricks under the seeded ladder, the climb to the north stop (Y 56, the
ladder-stopped state, in his room, in view), the climb back down. Rooms: the collision sweep below with
bricks laid, Tony's climb above (the clone's sprites off, his record unchanged a hundred frames later),
the sweep above, the return. Time: no overruns, the latest turn end. `--verbose` prints every snapshot,
`--shots DIR` keeps the screenshots. `tools/verify_brain.py` covers the senses, the slot and the
builder; `tools/brain_golden.py check` the learning rule (95 golden cases through the two hooks);
`tools/teach_demo.py` the teaching story and the number (`teach_demo.py PRG SAVE` also keeps the
weights that climbed).

## Notes for the brain session

- The physics run for the clone are the player's, byte for byte, with the collision flags computed
  lazily as above. A Python twin of the body is a twin of `physics-tall.asm` plus the dispatch table in
  `dispatchPlayerCommand`, and `bodySelfTest` is the pattern for proving a twin's collision function:
  sweep, compare all four outputs.
- The clone's senses are all in the record and the map: `cloneX`, `cloneY`, `cloneState` (bit 7 is the
  facing), `cloneBGCollision` and `cloneBGCollisionExt` (the flags at his position: floor near and far,
  wall left and right, ladder in the box, far and top), and the screen cells around him through
  `buildReadCell`. The player's are the physics block, read outside the clone's turn.
- The follow rule's one lesson: a duck ends only with the stick released (the physics allow no walk out
  of the duck state), so a brain that pressed down must let go for a frame. `cloneThink` does.
- Left in for a later clean-up: the Chamber's behaviour routines and their variables (dead here), the
  old buddy's guard routines are removed, `buddyX`/`buddyY` are still declared but nothing moves them;
  the record is the clone.

## For a v2

- A builder brain: lay when blocked, step up, repeat towards Tony; the byte's bits 5 and 6 are ready.
  (Built: kind 2.)
- If the rig shows a scaled step or a lesson every frame converging faster than thirty-six lessons,
  either is a rule version 2 with its own golden vectors, not a change to version 1.
- If more frame time is needed: the second Tony's turn could skip `phys_transitState` and
  `phys_executeState` when his command and state are unchanged (they are a few lines), and the music
  could move to the visual handler if that handler is measured short enough (today it is 36 lines from
  255, and the music 22 at most: too close to the next top entry at 8).
- The clone's colour is the parameter block's, like the buddy's; the Glitch's colour cycle is not wired
  to him.
