# The building demo (tony-build.prg)

A standalone program for the owner to play: the Chamber's room with one verb added, **build**.
It is a branch of the frozen base, not a change to it: the base (`tony-chamber.prg`, sha256
`67dc97bc1e306715...`) is byte for byte what it was, and nothing here is on chain or in a token.

| | |
|---|---|
| file | `deliverables/prg/minimal64/tony-build.prg` |
| size | 42,303 bytes |
| sha256 | `05ef5e3b4b2c8f543e30a6d3e2c4a3707f3351c77d2eaa3821d4559ef76cecf3` |
| boots on | minimal64 (the bench in `tools/verify_build.py`, ten checks passing); a plain PRG for VICE, READY 64 or the browser launcher, joystick in port 2 |
| built from | the Chamber base at `21b95e3`, room and seed as the base's default block, by `tools/make_chamber.py --variant tony-build --build-demo` and `tools/build_demo.sh tony-build` |
| diff | `deliverables/build-demo/tony-build.diff`, the demo's source against the base's (595 lines changed, most of them the new code) |

## Controls

Left and right walk, fire jumps (fire with a direction jumps that way), down ducks.
**Down + fire** lays a brick in the slot in front of Tony at his feet, or lifts it again if he laid it there; **up + fire** steps him up onto a brick he laid in front.

## What is in the room

The Chamber's room exactly as the base draws it for its default block: the seeded wall, the candle, the
floor. Two changes for the demo: **the bats are gone**, and the block number carved in the floor is
replaced by a **count of the bricks on screen** (three carved digits, same font, same wall material).
The second Tony is **the Shadow** (behaviour 0, the base's default), green.

## The verb, exactly

- **The grid.** Bricks are the mural's own 2 x 2 dotted brick, laid on the wall's grid of 15 columns
  (screen columns 5 + 2i) and 10 levels (rows 21 to 22 on the floor, then two rows up per level). The
  lowest level sits on the floor at row 23.
- **Lay.** With his feet on something (standing, walking or ducking), the target is the slot past his
  collision box in the direction he faces, at the level his feet are on. It is laid if its four cells are
  empty or seeded mural bricks and the slot does not overlap the Shadow.
- **Lift.** The same chord on a slot that holds a brick he laid takes it away. What the mural had there
  comes back: the seeded bricks are remembered in a 19-byte bitmap of the 150 slots at start, and each
  cell is restored from it. Only placed bricks lift; the pillars, floor, ceiling, candle and seeded
  bricks are not touchable.
- **Step up.** Up + fire moves him onto the brick he laid in front when the four rows above it are clear:
  his collision box lands on the brick's two columns, one brick higher, on the ground, facing as before.
  Walking off an edge he falls, by the engine's own physics.

## Confirmations the spec asked for

- **Collision is a lookup, confirmed, with one detail.** The engine reads the screen character under
  Tony and looks its material up in a 256-entry table at $BE00, indexed by the character's *screen code*
  (the room's codes are translated at load, so the mural's brick is $39 $31 / $30 $2F on screen). A placed
  brick is therefore four screen codes of its own, $40 to $43, given the wall material and copies of the
  brick glyphs at start. The physics is untouched: standing on, bumping into and jumping onto a placed
  brick all come from the engine. The seeded mural bricks keep their codes and no material, so they stay
  decoration.
- **The second Tony did not obey the map.** His routine steps one pixel toward the player, clamped to
  the pillars, with a fixed floor and a scripted hop; it never read a material. The demo adds a guard on
  each step: the column ahead of him, from his top row down to the row above the floor, is checked
  against the same materials table, and a wall there cancels the step. So a placed brick stops him at
  any height, and he cannot climb. Bench: with a brick laid between them and Tony walking to X 286, the
  Shadow follows to X 159 and stays there; without the brick he follows to 247.
- **Bat contact in the base kills.** No cheat bits are set, so a bat runs the death sequence, respawns
  Tony at the entry point and costs a life; running out of lives restarts the room. The demo removes the
  bats (the seed's presence value forced to none), so there is no contact and no death.
- **The count** is the three carved digits in the floor at columns 27 to 29.

## Why there is a step-up chord

Tony's jump is long: about 48 pixels of travel and a 23-pixel apex. From beside a 16-pixel brick he sails
over it, and the take-off window that lands him on one is 24 pixels wide, which no one can find from the
top of a two-column brick. So a staircase of single bricks needed the step-up, one chord, no physics
change. If the second Tony ever gets real physics, the same problem applies to him.

## Bench (minimal64, `tools/verify_build.py`, output in `deliverables/build-demo/verify.txt`)

Lay one brick (four cells, count 1); step up (Y 206 to 190, X over the brick's columns); a second and a
third from up there (Y 174, 158; twelve cells); a fourth laid and lifted from the top with the wall
restored cell for cell; walking off the top drops him to the floor; a brick between Tony and the Shadow
stops the Shadow at X 159 while Tony walks to 286. Screenshot: `deliverables/screenshots/build-demo-stairs-m64.png`.

## For a v2

- The placed bricks are recognisable by their codes, so no separate map of them is kept; a room map for a
  token would be the 150-slot bitmap of placed bricks, 19 bytes, next to the seed. The lift rule already
  reads the mural from such a bitmap.
- The placed brick uses the mural's dotted glyph so it looks native. If a built brick should read as
  built, a solid glyph for the four codes is a 32-byte change.
- The Shadow's guard is the first piece of a second Tony that knows the map; the next is making him an
  actor on the player's physics, which is where any trained policy would have to sit.
