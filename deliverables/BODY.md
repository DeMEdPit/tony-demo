# The body (tony-body.prg): the clone on Tony's own physics

The building demo's next step, for the owner to play and for the brain session to build on: the
second Tony (the Shadow) no longer moves by a hand-written rule with a fixed floor. He is run through
the player's own physics, a second time each frame, from a record of his own, and fed a one-byte
joystick that a brain writes. The first brain is the Chamber's follow rule, as joystick bits. Nothing
here touches the frozen base (`tony-chamber.prg`, sha256 `67dc97bc1e306715...`) or the building demo
(`tony-build.prg`, sha256 `5c24a63e1c14e26c...`); both are byte for byte what they were.

| | |
|---|---|
| file | `deliverables/prg/minimal64/tony-body.prg` |
| size | 44,422 bytes |
| sha256 | `b20e222253c5e7d2c71c9b0df1904924907e5e051a7b1dc6038ec3caf3d2a972` |
| boots on | minimal64 (the bench in `tools/verify_body.py`, thirty-three checks passing); a plain PRG for VICE, READY 64 or the browser launcher, joystick in port 2 |
| built from | the building demo's generator with one more option: `tools/make_chamber.py --variant tony-body --build-demo --body`, then `tools/build_demo.sh tony-body` |
| diff | `deliverables/build-demo/tony-body.diff`, the body's source against the building demo's (1,348 lines; the clone's code is the bulk of it) |
| bench output | `deliverables/build-demo/verify-body.txt` |

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
- His brain is still only the follow rule, so he does not build or climb on his own. The body can do
  both: the bench drives him through a staircase and up the ladder with the joystick byte (below).

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

## Time, measured

Two Tonys on the physics did not fit the frame as the game schedules it, and the way it failed is worth
knowing: the game's top handler (physics, actors, music) is a copper entry at raster line 40 and the
visual handler (sprites) one at line 255. With the clone's turn added, the top handler ran past line 255
on some frames; the copper then arms the visual entry too late, the visual handler runs a frame later,
and the top entry is skipped the frame after that: both Tonys froze one frame in eight, which the bench
saw as walks that came up short. Four things fixed it, all in the body's generator patches:

- The top handler starts at line 8 instead of 40 (the upper border; nothing is drawn there).
- A collision check is ~30 raster lines and the game's loop runs two a frame regardless. Both Tonys now
  skip the first when the proposed position is the current one and the map has not changed since their
  flags were computed (`bodyCheckProposal`, a stale bit per Tony set by every routine that writes the
  map), and the second when the movement was not blocked or adjusted (`bodyBlockMovement`). A Tony
  standing still costs no check; walking, one; landing or blocked, two. The results are the same: the
  check reads only the map and the position.
- The check itself is rewritten (`checkBGCollision` in the body's code): the same scan in the same
  order (left column then right, five rows, the ladder columns noted as the game notes them) with a
  row's address set once and a cell read once, at about half the cost. The game's own instance is kept
  as `checkBGCollisionRef`, and **`bodySelfTest`** runs both over every distinct position (X and Y in
  steps of 8, X to 511, Y to 255: the columns and rows change no finer) and counts the positions where
  any of the four outputs differ. The bench runs it in the room below with five bricks laid and in the
  room above: zero differ. Poke `bodySelfTestRun` to run it in any state.
- The two bats' actors are gone from the body's level data (`level/body/data.asm`); the demo never
  showed them, and their path logic cost a few lines a frame.

With that, in the bench's worst frame (the two landing from the same jump at once) the clone's turn
ends on raster line 218, the top handler's part of the frame is 8 to 218, the visual handler runs from
255 for about 36 lines, and the main loop has the rest. `bodyRasterMax` keeps the latest line a turn
has ended on and `bodyOverruns` counts turns that ended on line 250 or later (the level's first two
frames are not watched: the copper's first interrupt fires off-schedule on a stale raster flag, once).
The bench asserts zero overruns and a maximum below 230. The swap is unrolled (320 cycles each way);
the clone's whole turn is about 60 lines when he stands, 75 walking, 100 landing.

For a brain: what is left in the frame for thinking is about 30 raster lines inside the top handler
(the space to 250 in the worst frame), or the main loop's time, about 60 lines a frame, where a slow
think step can be spread over frames and just write `cloneJoy`; the body reads the byte at the start of
every turn, so a brain that thinks every fourth frame works without any change here.

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
`--shots DIR` keeps the screenshots.

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
- If more frame time is needed: the second Tony's turn could skip `phys_transitState` and
  `phys_executeState` when his command and state are unchanged (they are a few lines), and the music
  could move to the visual handler if that handler is measured short enough (today it is 36 lines from
  255, and the music 22 at most: too close to the next top entry at 8).
- The clone's colour is the parameter block's, like the buddy's; the Glitch's colour cycle is not wired
  to him.
