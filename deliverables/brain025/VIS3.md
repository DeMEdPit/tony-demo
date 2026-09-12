# BRAIN02.5 vis3: the crouch, the transition, the "75", and the trained state

**vis3 is the current revision.** It keeps everything vis1 and vis2 did and adds four changes: two
genuine fixes with causes established on the machine before anything was touched, and two presentation
changes the owner asked for.

| revision | PRG | bytes | sha256 |
|---|---|---:|---|
| research, no visual pass | `tony-b025-a.prg` | 52,092 | `2a547ebfe77bebb6b6174729af05a2ebb4dc2a8e558359f615cbdf34d6bfb423` |
| vis1 | `tony-b025-a-vis1.prg` | 52,092 | `4e22961ef55a5e29a80bdf65f8773301ced5e68904fc5417108bb543f1a7a708` |
| vis2 | `tony-b025-a-vis2.prg` | 52,092 | `117559716a3f529d35a887bac8f7e620adf250bbd3841d58edf10f837a614958` |
| **vis3** | `tony-b025-a-vis3.prg` | **52,098** | `41af4d661d3019cb7582f5f2072f5f40abe37599009fc8331ff4294335e66717` |

All three earlier PRGs are untouched, and the generator still reproduces the two frozen ones exactly:
regenerating `tony-b025-a` and `tony-build` from `tools/make_chamber.py` gives sources identical to what
is on disk, modulo the output filename. The two fixes are behind their own flags for that reason - the
research artifact is hash-pinned on the old code paths and has to stay reproducible.

    python3 tools/make_chamber.py --build-demo --body --brain025-visual \
        --build-parity --bat-stamp-guard --vocab rel --variant tony-b025-a-vis3
    bash tools/build_demo.sh tony-b025-a-vis3

---

## 1. The crouch: human and clone now obey the same rule around the build action

### The cause, established before anything changed

Down with fire lays a brick. For the **player** the verb is **additive**: `buildVerb` acts on the chord
and hands the joystick on to `dispatchPlayerCommand` untouched, so down is still pressed and he holds
the crouch he took. For the **routed clone** it was **substitutive**: in `teachRoute`, the lay branch
replaced the whole byte with the verb bit -

    lda #%00100000
    sta byte

so bits 0-4 reached `dispatchPlayerCommand` empty and he stood straight back up while down was still
held. Measured on vis2, down+fire held, sampled every second frame:

| | states while the stick is held | `cloneJoy` | `cloneJoyOverride` |
|---|---|---|---|
| player | `DUCK_L` on 23 of 24 samples | - | - |
| clone (vis2) | `ON_GROUND_R` on **24 of 24** | `$20` (lay only) | `$A0` |
| clone (vis3) | `DUCK_R` on **24 of 24** | `$32` (lay + fire + down) | `$B2` |

Both stand up when down is let go, and only then.

### It did reach the recorded lesson

`ducking` is **input 5** of the network, reading sense nibble 7, and the lesson records all 27 nibbles.
On vis2 nibble 7 read **0** through the whole crouch - the observation the lesson stored disagreed with
the pose the same stick produces on the player's body. On vis3 it reads non-zero and follows the body.
So this was a teaching-fidelity defect, not cosmetics.

### What provably did not move

The **taught action**. `actionOf` tests bits 5 and 6 *before* it looks at any direction:

    lda joyByte
    and #%01100000
    beq notBuild
        ldx #8              // 8 and 9: build-left and build-right
        lda stateByte
        bpl !+
            inx

so a build frame is action 8 or 9 whatever the direction bits say, and `stateByte`'s bit 7 (facing) is
the same crouched or standing. Measured: sense 16 (`lastAction`) is **9 on both builds**, every sample.
Byte 14 of the lesson, the action vocabulary and the replay reference are all untouched.

The brick also lands in the same place. Both `buildVerb` and `cloneVerb` fire on the rising edge
*before* `dispatchPlayerCommand` runs, so the target is computed while he is still standing in both
builds. Measured: same slot (`placedBits` bit 2 of byte 0), the same four screen cells at rows 21-22
columns 9-10, the same count digit, on vis2 and vis3 alike.

### The consequence to be aware of

Lessons **already recorded replay unchanged** - the reference tool reconstructs from the stored nibbles
and does not simulate a body. But a *new* session taught on vis3 records the corrected observation, so
for the same human input it will not produce the same lesson bytes vis2 would have. That is the fix
working, and it is the reason the flag exists.

---

## 2. The room transition is now an effect, on purpose, in both directions

### What it always was

A room change is: write the new chamber number, fade out, redraw, reposition Tony, fade in. The redraw
(`drawPlayfieldFading`) writes straight into the live screen at `$C000` with the display never blanked
(`$D011` bit 4 stays set) and no raster sync. It takes **eight frames** of a twenty-frame, 0.4 s
transition, in three visible passes: `_draw_playfield` lays the room down in raw untranslated map codes,
`muralStamp` puts the wall on top, `translateRoom` converts the codes into real characters. At its peak
**418 of 1000 cells** differ from either room.

What hid it was the fade: `playboardFadeOut` walks `currentColor` down to black and `doEachFrameTop`
copies `currentColor` into `BG_COL_0` every frame, so the screen went dark for exactly those frames.

vis1's dark room above outranked the fade by accident - it pinned `BG_COL_0` to 11 whenever
`currentChamberNumber` was non-zero, and the chamber number is written *before* the fade starts - so the
redraw was in plain sight going up and hidden coming down. **It was reachable before vis1 too**: the
Glitch's blackout (`muralBehaviour == 7` → 11) and a candle-less room (`muralDim` → 12) override the same
register. Measured on the frozen research build: hold `muralDim` and the background stays 12 across the
whole transition; hold `muralBehaviour` at 7 and it stays 11; it never reaches 0 either way.

### What vis3 does

While a room change is running the background holds `COL_TRANSIT` (11, dark grey - flavour (a)), so the
fade cannot reach the screen and the redraw is watched rather than hidden, **both ways**:

    ldy roomChange              // vis3: THE TRANSITION EFFECT, and it must stay last in this chain.
    iny                         // roomChange is $ff unless a room change is running: $ff + 1 sets Z.
    beq !+
        lda #COL_TRANSIT
    !:
    sta c64lib.BG_COL_0

Measured, `BG_COL_0` frame by frame across the twenty frames of a change:

| | up, 0 → 1 | down, 1 → 0 |
|---|---|---|
| vis2 | `15 11 11 11 …` pinned | `11 15 12 12 11 11 0 0 0 0 0 0 0 0 0 0 11 11 12 12` |
| vis3 | `11 11 11 …` pinned | `11 11 11 …` pinned |

### What it deliberately does not touch

* **The death, game-over and level-start fades.** `roomChange` is `$ff` for all of them - `initRoom`
  sets it and `checkForRoomChange` is the only routine that ever writes a real room number. Measured:
  the boot/level-start `BG_COL_0` trace and the death trace are **identical** to vis2, sample for sample.
* **The brain.** `changeRoomIfNeeded` blocks the main loop and `bodyThink` is called from it, so the
  brain cannot think on a half-drawn room. Measured: `brainThinks` advances **0** times across the
  twenty frames of a change, where a free main loop would manage about five.
* **Timing.** `bodyOverruns` **0** and `bodyRasterMax` **138**, both unchanged.

### It is load-bearing and silently breakable, so a gate holds it

The effect exists only because that override is the **last** write to A before `sta c64lib.BG_COL_0`.
Anything inserted after it, or any reordering of the colour chain above it, removes the effect with no
error and no visible difference outside a room change. No assembler check can express that. The
`transit` gate can: it measures `BG_COL_0` across a change in both directions and fails if the
background dips instead of holding. It passes on vis3 and **fails on vis2** at exactly the down
transition, so it is a real guard rather than a tautology.

---

## 3. The "75" in the room above: it was a write over the level data

### It was not the glitch, and not the level file

The upper room's top-left two cells read as "75". They appear at frame 12 of the transition, *after*
`translateRoom` finishes, so they are part of the finished picture, not an intermediate. They are static
over 240+ frames, unchanged by every seed byte that drives the wall, the candle and the block digits,
and the two rooms' character decoding tables are **identical** (0 of 256 entries differ). The packed room
says `$31 $32` at those cells. In RAM after boot it said `$08 $06`.

Localised by build layer: `tony-build.prg` (the frozen build demo) is **clean**; every `--body` build has
it. That is the whole clue.

### The mechanism

`muralBatsStamp` patches six parameter stores from the room's static-object array pointers and writes
through them whether the room has any objects or not. `_level_pack` emits those arrays with
`.fill <size>, …`, so a room with **no** static objects gets a **zero-length** array - and its pointer is
simply the address of whatever label follows. The `--body` builds carry no bats, so both rooms have empty
lists, and for chamber 0 that address is **chamber 1's compressed map**:

    level_roomPtr        room0 $53AD   room1 $55BF
    objectControlPtr     room0 $55BF   room1 $57D1      <- room 0's arrays ARE room 1's map
    objectPositionXPtr   room0 $55BF   room1 $57D1
    objectPositionYPtr   room0 $55BF   room1 $57D1
    movableValue2Ptr     room0 $55BF   room1 $57D1
    objectSizes          room0 0       room1 0

At level start the stamp writes the bats' parameters there. The last write at each index wins:
`muralBats+3 = $08` lands on offset 0 and `muralBats+6 = $06` on offset 1 - exactly the two bytes that
were wrong. Every later draw of the room above then decompresses the damaged stream, and `$08 $06`
translate through the room charset to `$2A $28`, which read as "7" and "5".

So it was a live write over level data. Two bytes, in a ceiling row that carries no material, which is
why nothing else ever went wrong - but the same shape would have put those bytes anywhere the layout
happened to put the next label.

### The fix

With no objects there is no bat to carry the parameters, so the stores have no reader. `--bat-stamp-guard`
sends them to a sink byte instead, and leaves `muralBats` and the `level_roomStates` presence masking
exactly as they were. Measured on vis3: chamber 1's packed map is **byte-identical to the load image**
after a full round trip through both rooms, and the two rooms draw the same ceiling (`$06 $09` both).
The `roomdata` gate pins this and **fails on vis2**, naming the two bytes.

---

## 4. The trained state: education changes how often the dropout comes, and nothing else

The clone's base identity stays **white**, and the dropout stays - he is still a copy. What education
changes is the dropout's **period**, as a mask patched into an immediate (`decodeRoom`'s own `comparePrt`
idiom, so the state language costs no extra byte):

| `brainEducation` | dropout |
|---|---|
| 0, nothing taught | one frame in **16** - the least steady he gets |
| 1 to 31 | one frame in 32 |
| 32 to 95 | one frame in 64 |
| 96 and up | one frame in **128**, and this is a floor |

Measured over 512 frames at 0, 8, 33, 96, 300 and 1000 lessons: 32, 16, 8, 4, 4, 4 dropout frames -
one in 16, 32, 64, 128, 128, 128. **It never reaches zero**, however much he is taught.

Everything else in the state language is unchanged from vis2: cyan is reserved for TEACH being active
(three frames in thirty-two, measured 3 of 48, and the dropout keeps running underneath at its education
cadence), an accepted lesson is six green frames, a refused one red. **No blue tick** - cyan alone
signals the TEACH state. The human Tony is untouched and stays light grey, verified in every state.

All of it is a pure function of `bodyFrames`, `teachMode`, `brainEducation` and the existing flash
counter, and only sprites 5 and 6 are written.

---

## What this pass did not change

No change to the neural inputs' definitions, the retina table, the learning rule, the weights, the
lesson format or its bytes, the physics, the action semantics, the replay reference, or any
cross-runtime state. `brain025_ref verify` still matches the pinned manifest and the canonical
244-lesson session still replays to a **byte-identical** final slot with **244 of 244** predictions
matching.

A fresh session recorded on vis3 itself replays the same way end to end: 235 lessons over 8 drains at
capacity 40, spanning 5.9 ring fills, blank start hash `f88f9b61ba509825`, final
`79fd85b9f3a49f646e2f42c59beb2e036e04bb706fb180a717cbcc138f15b48f`, **235 of 235** predictions matching
and the final slot byte-identical to the machine's. It is stored as
`replay/session-tony-b025-a-vis3/` - see the note under Gates about why it is not `session-1`.

Measured field by field, vis2 against vis3, 40 samples four frames apart over both Tonys' positions and
states, all 27 senses, the chosen action, education, the ring's write sequence, the think count, the
brick count, the frame counter, the raster maximum and the overrun count:

* an episode that never touches the build verb: **every field identical on every sample**;
* an episode holding down+fire while teaching: `cloneState` differs on every sample (`$80` → `$83`,
  standing → crouched) and sense nibble 7 with it. That is the fix, and it is the only intended
  behavioural difference in the build.

Nearest-N brick selection and a guaranteed candle were **not** implemented in this pass and remain a
future option; `litRadius` is still the single byte that tunes the current light gate.

## Resources

| | research | vis1 | vis2 | **vis3** |
|---|---:|---:|---:|---:|
| PRG bytes | 52,092 | 52,092 | 52,092 | **52,098** |
| code end | $90F6 | $90F6 | $90F6 | **$90FC** |
| think, cycles max | 42,288 | 42,297 | 40,753 | **40,843** |
| lesson, cycles max | 38,347 | 39,012 | 40,711 | **40,024** |
| terrain probe, pure | 4,361 | 4,399 | 4,427 | **4,416** |
| raster max | 141 | 141 | 138 | **138** |
| overruns | 0 | 0 | 0 | **0** |
| headroom below the shadow | 265 | 265 | 265 | **259** |
| slot bytes | 834 | 834 | 834 | **834** |

Six more bytes, all of them the crouch fix's two `ora` forms. The think still finishes inside its
four-frame period (78,624 cycles) and the raster maximum is unchanged against a limit of 230.

## Gates

Fifteen gates on vis3: `smoke`, `blank`, `key`, `terrain`, `parity`, `migrate`, `resources`, `visual`,
`session`, `teach`, `drain`, `descriptor`, and the three new ones - `transit`, `crouch`, `roomdata`.

Two existing gates had to change, and both changes are recorded here rather than quietly made:

* **`visual`, sub-check 1.** It asserted a fixed dropout of 2 or 3 frames in 64. The dropout's period is
  now a function of education and a fresh boot has none, so an untaught clone drops out one frame in
  sixteen. The expectation moved with the behaviour, deliberately, and three new sub-checks pin the new
  rule: the dropout survives every education, gets rarer monotonically down to a floor, and no colour
  but white and the dropout appears while he runs on his own.
* **`drain`, the acknowledgement handshake.** It gave `lessonAckRequest` **two frames** and scored a
  refusal if nothing had happened. On vis3 that produced one apparent refusal out of fourteen - with
  `status $80`, no error bit, the machine's own checksum in agreement, and `read` and `drains` simply
  untouched, which is not a refusal at all but a request the main loop had not got to yet. The machine
  was never at fault: the same acknowledgement, reproduced in isolation, is accepted. The handshake now
  gets **six frames**, the same number the golden and migration gates needed for the same reason, and
  retries while the request byte is still pending. The corrected gate passes on vis2 as well as vis3 -
  392 applied of 392 drained on vis3, 353 of 353 on vis2, zero pairings dropped on both.

One more hazard was found and closed while running them. `gate_session` wrote into
`replay/session-1/` whatever build it was given, so running it on vis3 **silently overwrote the
canonical recorded session** that REPLAY.md pins by hash and attributes to `tony-b025-a.prg`. It was
caught by reading `git status` rather than by any check. `session-1` is restored and verified, and the
gate now writes there only for the build that session came from; every other build records under its own
name beside it.
