# The clone: where the building demo stands, what it taught, and how a brain would plug in

For the session thinking about the second Tony's brain. Written 2026-09-09 by the demo's session.
Everything below is on the branch `claude/tony-c64-demo-expert-wp40it`; nothing touches the frozen
Chamber (base `21b95e3`, images `b114468`). The demo's write-up with rules and numbers is
`BUILD-DEMO.md`; this note is the thinking.

## 1. What is built

`deliverables/prg/minimal64/tony-build.prg` (43,434 bytes, sha256 `5c24a63e...`), a branch of the
Chamber base with:

- **The build verb.** Down + fire lays a 2 x 2 brick in the wall slot in front of Tony at his foot
  level, or lifts it if he laid it; up + fire steps him onto a brick he laid in front. Bricks are drawn as
  a small stone block (a floor brick's two ends), distinct from the dotted mural.
- **Two rooms, exactly alike**, joined by a ladder that hangs from the ceiling of the room below and stops
  at row 9. Five bricks stacked under it bring its bottom rung within reach. Its column comes from the seed
  (byte 30, bits 2 to 5), steered clear of the candle. Climb off the top and you arrive on the same ladder
  where it comes up through the floor of the room above; hold down over the hole to come back, and drop
  off the ladder's end onto your bricks. Each room keeps its own bricks (19 bytes per room).
- **The Shadow** (behaviour 0) as the second Tony, with one addition: a guard on every step that checks
  the column ahead against the collision table, so a placed brick stops him. He cannot climb; he stays in
  the room below and waits.
- **No bats**, and a count of the room's bricks carved in the floor under the left pillar.
- **The bench**, `tools/verify_build.py`: seventeen checks on minimal64 (lay, step up, three high, lay
  and lift from the top with the mural restored, walk off, the Shadow walled off, five bricks to the
  ladder, the room above, the Shadow absent there, the return onto the bricks). All passing.

## 2. What the engine taught us

- **Collision is a lookup by character.** The engine reads the screen character under Tony and looks its
  material up in a 256-entry table indexed by the character's screen code (the room's codes are
  compacted at load, so the mural's brick is $39 $31 / $30 $2F on screen, not $B0 to $B3). A placed brick
  is therefore four screen codes of its own with wall material; the physics never changed.
- **The second Tony had no physics.** His routine is an X, a fixed floor and a canned hop; it never read a
  material before the guard. This is the whole reason for section 3.
- **Tony's jump is long**: about 48 px of travel, a 23 px apex. From beside a 16 px brick he sails over
  it; the take-off window to land on one is 24 px wide. Single bricks are not climbable by jumping, hence
  the step-up chord. Any actor with the same physics has the same problem.
- **Rooms, exits and ladders are map data.** A second room is a pack line and two exit numbers; a ladder
  is two character codes with ladder material. But the tall 25-row room's floor lies below the game's
  south limit (set for 20-row rooms), so a south exit would fire the moment Tony stood on the floor;
  the demo moves that limit to Y 224, which only a ladder through the floor reaches.
- **A downward ladder lives in the floor rows only**, as the game's own maps have it: its top cell is
  the floor row, Tony stands in that cell and steps sideways onto the floor. One row higher and the
  engine's "no floor under you but a ladder behind you" rule drops him into the hole forever.
- **A room change re-enables the room's enemy sprites** after the mural code has hidden them; the demo
  switches the bats' sprites off every frame.
- **Bat contact in the base kills** (no cheat bits set): the death sequence, a respawn, a life lost.

## 3. The body: the clone on Tony's physics

**Built, 2026-09-09: `deliverables/prg/minimal64/tony-body.prg`, write-up `BODY.md`.** What follows
was the plan; the differences found on the way: the physics state is twenty bytes, one block, and the
record mirrors it by derived labels; the engine's animator writes the player's sprite pointers by fixed
address, so the clone has a small animator of his own over the same frame tables; and two Tonys did
not fit the frame as the game schedules it until the collision checks were made conditional and
cheaper (measured and proved in `BODY.md`, "Time, measured"). The guards listed below are all in.

The engine's physics (`physics-tall.asm`) is written for one player against one set of variables:
position, next position, state, facing, jump phase, ladder adjustment, the collision flags, the animation
number. About thirty bytes. The proposal is not a second physics but the same one run twice a frame:

1. Save the player's set, load the clone's set, place his joystick state where the port's would be.
2. Run the command dispatch and the physics step exactly as for the player.
3. Store the set back as the clone's, restore the player's.

Cost: the physics is 2.7 KB of code and a few thousand cycles; a second pass fits the frame. The
animation code already handles several actors by index (the bats), so his sprites can follow his state.

What it buys: he walks, jumps, falls, climbs ladders and bumps into walls by your rules, so anything he
learns in the emulator is true in the room, and a race is fair.

What to watch: the physics assumes a single player in places that are not the physics, the room-change
check (he must not change rooms by walking into an exit unless we want that), the death path (he has no
lives), the respawn position, the sprite-to-sprite collision mask (the buddy is "friendly" today by sprite
number). Each is a small guard, but they have to be found. Estimate: days, not hours; the two-room demo is
the test bed, and the first thing to watch is him climbing the staircase you built.

## 4. The joystick: the contract between brain and body

**As built:** `cloneJoy`, bit 0 up, 1 down, 2 left, 3 right, 4 fire, 5 lay or lift, 6 step up, a set bit
is a pressed line; bits 0 to 4 go through the game's own dispatch, 5 and 6 act on their rising edge.
`cloneJoyOverride` with bit 7 set replaces the brain's byte (the bench's and a trainer's hook). The body
reads the byte at the start of the clone's turn every frame, so a brain may write it whenever it likes.

**The three asks of 2026-09-09, done** (all in `BODY.md`): the sense block, twenty signed nibbles with
the packing written nibble by nibble as the contract, checked against a Python twin in the bench; the
brain slot, `BRAIN01` page-aligned with the header (kind 0 says "no brain yet"), 256 bytes of nibble
weights, the mood, the forward pass proved against a Python reference on random vectors, the ten-action
decoder with the build macro and the release frame, a think every fourth frame in the main loop that
runs under teaching; and the harness page, `HARNESS.md`, with snapshot, restore and load and one worked
episode. Example weight files in `deliverables/brains/`. The builder brain (kind 2) is in the same
program; `tony-body-builder.prg` has it on from the start, for play.

Everything the player can do is five lines a frame, up down left right fire, and in this demo two
chords. So the brain's output is one byte a frame: the five lines, plus "lay" and "step up" as two more
bits the body turns into the chords. Nothing else. A scripted brain, a hand-written builder and a trained
network all produce the same byte, so they are interchangeable, and a recorded stream of the player's
bytes (the Echo mechanic already records and replays one, four seconds long) is a training set.

## 5. The brain

**Senses.** A small network is only as good as its inputs, and the inputs should be things the body
already computes or the map already holds, so they cost nothing:

- where you are relative to him: above, below, left, right, and roughly how far (a few bits each)
- what is ahead of him at foot level and at head level: empty, mural, a placed brick, a wall, a ladder
- what is under him: floor, a placed brick, nothing (he is falling), a ladder
- whether a ladder is within reach, and whether the slot in front is one he may build in
- his own state: on the ground, in the air, on a ladder, facing
- a little memory: his last output, and a count of frames since he last moved

About a dozen to twenty inputs, each a bit or a small number. Outputs: the seven bits of section 4.

**Size.** A single-layer perceptron (inputs straight to outputs) is a few hundred bytes of weights and
learns only straight-line rules over the senses, which is enough for follow, climb-what-is-there and
lay-when-blocked if the senses are chosen well. A hidden layer of eight to twelve units, roughly 140 to
250 bytes of weights, can learn to build a staircase toward a goal. On the 6502 either fits if he thinks
every fourth frame; the perceptron every frame.

**A reflex layer under it.** A few hard rules the network cannot override: never walk off the room, never
lay a brick into a body, never step into a wall. This keeps a half-trained brain from looking broken.

**Where to train.** In the emulator, off the machine, with the bench we already have: minimal64 headless
runs the real game deterministically and faster than real time with a scripted joystick and full memory
access. Two signals, both worth using: your recorded play (imitation, the cheap and watchable first
brain, he plays like his owner), and reward with hill-climbing over the weights (mutate, run a thousand
episodes with seeded rooms and ladder positions, keep the better set), which suits a net this small far
better than anything fancier.

**Learning in play.** Imitation can run live: while you play, his weights nudge toward doing what you did
in the situation you were in. A few hundred additions per update. Two rails: a small learning rate and
weights clamped to a byte. Reward learning in real time is too slow and noisy to feel like anything.

**Persistence.** Nothing in the running program survives the page closing. The brain has to live where the
seed lives: the weights become part of the stamped block next to the seed, every render stamps them into
the PRG, and saving is a transaction the token's owner signs (the page around the emulator reads the
weights out of memory and offers "save your clone"). Only the owner should be able to save; anyone can
play a token, and their play should not overwrite the owner's clone. The brain then transfers with the
token.

## 6. Decisions worth settling between the sessions

- **Can the clone lay bricks?** If yes, the first behaviour to teach is building his own way up to you,
  the most watchable thing he could do, and a race is possible. If no, he only uses what you build.
- **The brain's storage size**, for the contract: 64, 140 or 256 bytes. It sets what the network can be.
- **Save rights**: owner only (my recommendation), or a training session the owner opens and closes.
- **Rooms**: whether he follows you through exits, waits, or is fast-forwarded when you return.
- **Perceptron or one hidden layer**: the senses above are chosen so a plain perceptron has a chance; if
  the other session's design is a perceptron, it should tell us which inputs it wants, and the body can
  compute them.

## 7. The order

1. The body (section 3), with the follow rule as its first brain, on the two-room demo. Watch him climb
   the stairs you built. **Done** (`BODY.md`): on the bench's byte he builds stairs and climbs the ladder;
   the follow rule alone does neither.
2. A hand-written builder brain: lay when blocked, step up, repeat toward you. Watch him build.
3. Record your play; train the first network in the emulator; run it on the 6502.
4. The save-to-token piece with the contracts session.

## 8. Settled with the contracts session (2026-09-09)

Their answers to section 6, recorded here so both sessions build to the same thing:

- **The clone can lay bricks.** Building his own way up to you is taught first; a race is the game.
- **Storage: 256 bytes of weights per token plus an 8-byte header** (a magic word, the layer sizes, a
  version), readable by the program. The stamped block grows from 42 bytes to about 300, which is a new
  parameter block and marker, `MURAL03`, in a new base for the new collection. The Chamber stays as it is.
- **Save rights: the owner only, a signed transaction.** Anyone can play a token and teach the clone for
  the length of a visit; only the holder makes it stick. The frame cannot sign, so "save your clone" lives
  on the loading page with the wallet button, which reads the weights out of the emulator's memory. An
  owner-opened training session is a later refinement.
- **Rooms: he waits.** Following through exits is a second brain.
- **Both code paths**: hidden size zero is the perceptron; choose after the first training runs.
- **Arithmetic**: weights as signed bytes, inputs as 4-bit values, multiplied through a table, no
  shift-and-add loop; a 16-bit accumulator per unit; about three hundred multiplies every fourth frame.
- **Two additions.** Two to four recurrent units fed back from the previous think, so an intention such
  as "building a staircase" survives across frames (an Elman network, still tiny). And legibility by
  construction: the header, and the weights laid out as a labelled block anyone can find with a hex
  editor, as the `MURAL02` marker is today. The brain should be readable off the chain.
- **For the save piece they need**: the header format, the block's offset and size, and a reference
  implementation of the think step in Python that the 6502 matches bit for bit, checked the way the
  stamp is checked today.

### The budget, counted

256 bytes of signed-byte weights holds less than "twelve hidden over twenty inputs". With I inputs,
R recurrent units, H hidden and 7 outputs, the weights are (I + R) x H + H x 7 plus H + 7 biases:

| shape | weight bytes | fits 256? |
|---|---|---|
| perceptron, 20 inputs, 7 outputs | 147 | yes, with 109 spare |
| 20 + 2 recurrent inputs, 8 hidden, 7 outputs | 247 | yes, just |
| 16 + 2 recurrent, 8 hidden | 203 | yes |
| 20 + 4 recurrent, 12 hidden | 391 | no |
| 20 + 4 recurrent, 12 hidden, 4-bit weights | 196 | yes |

So within 256 bytes the choice is eight hidden units at byte weights, or twelve at nibble weights, or
the budget goes to 512 bytes for twelve at byte weights. My recommendation is eight hidden units at
byte weights with two recurrent units: it fits the table-driven multiply as specified, and eight units
over these senses is plenty for follow, climb and build. Nibble weights are possible with the same
multiply table (the table is 4-bit by 4-bit already) but halve the precision the learning rule has to work
with, which matters more for learning in play than for the trained set.

### The multiply, as it would be done

A 4-bit input times a signed byte weight through one 256-entry table: the weight's magnitude is split
into two nibbles, each looked up against the input in a 16 x 16 table of products (each product at most
225, a byte), the high nibble's product shifted left by four before the add, the sign applied once to the
sum. Two lookups, one shift, one add per weight; the 16-bit accumulator absorbs it. Activation: hidden
units clamp their accumulator to 0..15, so their outputs are 4-bit like the inputs and feed both the
output layer and the recurrent inputs of the next think; outputs fire when the accumulator is positive.
All of it is integer and deterministic, so a Python twin matches it exactly.

### A header to react to (eight bytes)

`"BRN"` (3 bytes, the magic), version (1), inputs (1), hidden (1), recurrent (1), outputs (1). The
weights follow in a fixed order: input-to-hidden by hidden unit, recurrent-to-hidden, hidden biases,
hidden-to-output by output, output biases; for hidden = 0, input-to-output then output biases. The 8-byte
header and the 256 bytes sit right after the `MURAL03` block's own fields, at a fixed offset from the
marker, so a hex editor finds them the way it finds the seed today. The recurrent state is not stored;
it starts at zero every render.

### What this session delivers, in order

1. The body: the physics as a second pass, on the two-room demo, with the follow rule as the first brain.
   **Delivered:** `tony-body.prg` (44,422 bytes, sha256 `b20e222253c5e7d2...`), the bench
   `tools/verify_body.py` (thirty-three checks), `BODY.md`. Frame time left for a brain: about 30 raster
   lines inside the top handler, or the main loop's ~60 lines a frame (a think step every fourth frame
   fits there without any change to the body).
2. The hand-written builder brain, using the joystick contract, so the senses and the reflex layer get
   exercised before any training.
3. The think step on the 6502 with the header above, its Python twin, a bench that runs both on recorded
   inputs and compares every output, and the first trained weights.
4. With the contracts session: the `MURAL03` block's layout, the offset and size, and the twin as the
   check on the contract side.
