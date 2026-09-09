# The building demo (tony-build.prg)

A standalone program for the owner to play: the Chamber's room with one verb added, **build**, and
since 2026-09-09 a second room above it, reached by a ladder that hangs from the ceiling.
It is a branch of the frozen base, not a change to it: the base (`tony-chamber.prg`, sha256
`67dc97bc1e306715...`) is byte for byte what it was, and nothing here is on chain or in a token.
Its next step, the second Tony on the player's own physics, is a further PRG (`tony-body.prg`), written
up in `BODY.md`; this file describes the building demo as it is.

| | |
|---|---|
| file | `deliverables/prg/minimal64/tony-build.prg` |
| size | 43,434 bytes |
| sha256 | `5c24a63e1c14e26c2f966e7cc58cf4d484792b82bcd7c8e397ae96cd564bbf29` |
| boots on | minimal64 (the bench in `tools/verify_build.py`, seventeen checks passing); a plain PRG for VICE, READY 64 or the browser launcher, joystick in port 2 |
| built from | the Chamber base at `21b95e3`, room and seed as the base's default block, by `tools/make_chamber.py --variant tony-build --build-demo` and `tools/build_demo.sh tony-build` |
| diff | `deliverables/build-demo/tony-build.diff`, the demo's source against the base's (810 lines changed, most of them the new code) |

## Controls

Left and right walk, fire jumps (fire with a direction jumps that way), down ducks.
**Down + fire** lays a brick in the slot in front of Tony at his feet, or lifts it again if he laid it there; **up + fire** steps him up onto a brick he laid in front.

## What is in the rooms

Two rooms, exactly alike: the Chamber's room as the base draws it for its default block, the seeded
wall, the candle, the floor. Changes for the demo: **the bats are gone**; the block number carved in the
floor is replaced by plain floor, and a **count of this room's bricks** is carved under the left pillar
(three digits, the room's own font, wall material). The second Tony is **the Shadow** (behaviour 0, the
base's default), green, and he **stays in the room below**: he cannot climb, so when you go up he waits,
and he is there when you come back.

**The ladder.** In the room below a ladder hangs from the ceiling and stops at row 9, well above the
floor: five bricks stacked under it bring its bottom rung within reach, and holding up on the top brick
starts the climb. Its column is seeded (byte 30 of the seed, bits 2 to 5, mirrored away from the
candle's niche), so a different block hangs it elsewhere. Climb off the top and you are in the room
above, arriving on the same ladder where it comes up through the floor. To come back, stand over the
hole and hold down: you climb through the floor, arrive at the top of the hanging ladder, climb to its
end and drop, onto your bricks if you built them under it. Each room keeps its own bricks (a 19-byte
record per room, re-laid when you enter), so the staircase is still there. The ladder in the room above
runs through the floor rows only, as the game's own maps do it: Tony stands in its top cell and steps
sideways onto the floor.

## The verb, exactly

- **The grid.** A brick is 2 x 2 cells drawn as a small stone block, the two ends of a floor brick, so it
  reads as built next to the dotted mural (changed 2026-09-09 at the owner's request). It is laid on the wall's grid of 15 columns
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
- **The count** is the three carved digits in the floor at columns 1 to 3, this room's bricks.

## Why there is a step-up chord

Tony's jump is long: about 48 pixels of travel and a 23-pixel apex. From beside a 16-pixel brick he sails
over it, and the take-off window that lands him on one is 24 pixels wide, which no one can find from the
top of a two-column brick. So a staircase of single bricks needed the step-up, one chord, no physics
change. If the second Tony ever gets real physics, the same problem applies to him.

## Bench (minimal64, `tools/verify_build.py`, output in `deliverables/build-demo/verify.txt`)

Lay one brick (four cells, count 1); step up (Y 206 to 190, X over the brick's columns); a second and a
third from up there (Y 174, 158; twelve cells); a fourth laid and lifted from the top with the wall
restored cell for cell; walking off the top drops him to the floor; a brick between Tony and the Shadow
stops the Shadow at X 159 while Tony walks to 286. The two rooms: five bricks up to the ladder, the climb into
the room above (the Shadow's sprites off there, no bricks there), the climb back down onto the bricks (the
count still five, the Shadow back). Screenshots: `deliverables/screenshots/build-demo-stairs-m64.png` and
`build-demo-two-rooms-m64.png`.

## Two rooms: what the engine needed

- The tall room's floor lies below the game's south limit, so with a south exit Tony would leave the
  moment he stood on the floor. The demo moves that limit to Y 224, which only a ladder through the
  floor reaches, and lands an arrival from below at Y 216, on that ladder.
- The four ladder characters have to be in the room's character set, so the demo's map carries them in
  four empty cells of the mural area (`src/level-custom/build-room.bin`); the mural overwrites them and
  the ladder is drawn with the mural, in map codes, before the room's characters are translated.
- The extra characters push the room's screen codes past $40, so the placed bricks live at $50 to $53.

## For a v2

- The placed bricks are recognisable by their codes, so no separate map of them is kept; a room map for a
  token would be the 150-slot bitmap of placed bricks, 19 bytes, next to the seed. The lift rule already
  reads the mural from such a bitmap.
- The placed brick's look is four glyphs copied at start (the floor brick's ends, map codes $31 $36 /
  $37 $3C); any other 2 x 2 look is a change to that list.
- The Shadow's guard is the first piece of a second Tony that knows the map; the next is making him an
  actor on the player's physics, which is where any trained policy would have to sit. Done, 2026-09-09,
  as `tony-body.prg`: see `BODY.md`.
