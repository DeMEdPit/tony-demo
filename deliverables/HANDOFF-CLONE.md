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
   the stairs you built.
2. A hand-written builder brain: lay when blocked, step up, repeat toward you. Watch him build.
3. Record your play; train the first network in the emulator; run it on the 6502.
4. The save-to-token piece with the contracts session.
