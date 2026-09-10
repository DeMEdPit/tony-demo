# Goal observability: the senses and the holdout, sealed

Written and committed before Phase 1 of the bake-off ran. Nothing in Phase 1 or Phase 2 reads this
file; the representation is selected without it. After Phase 1 and 2 name the surviving encodings,
each survivor is built with exactly these senses and tested against exactly these scenarios in
Phase 4. The holdout is sealed by this commit.

## The question these senses answer

Everything the clone senses today is relative to Tony or within one cell of his own box. He cannot
seek what he cannot sense: a ladder across the room, or the way to a Tony who is not in the room.
The five senses below are facts about his room, none a decision. They append at index 20 and up
under every candidate encoding, packed like the others (signed nibbles, flags 0 or 7, buckets as dx
and dy are bucketed today), so the sense contract's first twenty entries do not change.

| index | name | value | derived from |
|---|---|---|---|
| 20 | `playerAway` | 7 when Tony is in another room, else 0 | currentChamberNumber against the clone's room; not in the twenty raw senses |
| 21 | `routeDx` | while playerAway: the sign and bucket (as dx, 0 under 8 px ... 7 from 128) of the distance from the clone to the route point, the foot of the ladder that leads to Tony's room (its columns' centre); 0 when not away | the clone's X and the ladder column of the room (from the seed); not in the raw senses |
| 22 | `routeDy` | while playerAway: the height of the route point above his feet in bricks, as dy is bucketed (the ladder's bottom rung row against his feet row); 0 when not away | the clone's Y and the ladder's bottom row |
| 23 | `ladderDx` | the sign and bucket of the distance to the nearest ladder in his room (its columns' centre), whether or not Tony is away; 0 when he is within the ladder's columns | the clone's X and the room's ladder columns |
| 24 | `ladderDy` | bricks between his feet and the nearest ladder's bottom rung, positive when the rung is above him, bucketed as dy; 0 when he is on or beside it | the clone's Y and the ladder's bottom row |

## Can Solidity reconstruct them from committed state?

No, not from what a lesson commits today. A lesson records the twenty raw senses, and the twenty are
relative quantities: none of them carries the clone's absolute X or Y, the room he is in, or the ladder
column. The ladder column is reconstructible from the seed (the parameter block's stream, as the
stamp tool predicts it), but the clone's own position is not in the lesson, so `routeDx`, `routeDy`,
`ladderDx` and `ladderDy` cannot be recomputed on the chain from an 11-byte lesson, and `playerAway`
cannot either. Two options, decided later by the session of record; the recommendation is the first:

1. **A versioned lesson, `LESSON2`**: the raw senses packed two per byte (25 nibbles, 13 bytes) and
   the action byte, 14 bytes, with the size byte of the block header saying 14 and a layout number
   in the brain header saying which senses the lesson carries. The replay is unchanged in kind: the
   recoding table applies to the first twenty as before, and the five new senses enter the readout
   as published (or as flags, if the survivor's retina recodes them too).
2. Commit the clone's position and room with each lesson instead (X, Y, room: 4 bytes) and let the
   chain derive the five from them and the seed. Cheaper per lesson by a byte, but it moves the sense
   definitions into Solidity, which then has to reproduce the engine's bucketing of a room geometry;
   the first option keeps the engine the only place senses are computed.

Either way the 11-byte format stays valid for brains without these senses, and a brain header's
layout number says which format its lessons use.

## The sealed goal holdout

Eight scenarios, four with their mirrors, to be run in Phase 4 under the strict rule against every
survivor, the teacher extended with the same senses, and the controls. Two of them need a two-ladder
variant of the body's level data (the level is data, the program is not changed); the rest run on the
seeded PRGs already in `../generalization/prg/`. Setups are described here and scripted verbatim in
Phase 4; the goal rules are fixed now.

| id | needs | ladder | setup | goal | mirror |
|---|---|---|---|---|---|
| G01_find_ladder_tony_above | playerAway, routeDx, routeDy | 33 | stairs(33) built by Tony who then climbs through the ceiling into the room above (hold up 200 frames) and waits there; the clone parked at X 146 during the setup | on the ladder (states 2, 7) at Y <= 88 within 900 frames, strict | G02 |
| G02_find_ladder_tony_above_mirror | playerAway, routeDx, routeDy | 5 | the mirror: leftward stairs under the ladder at column 5, Tony through the ceiling, the clone parked at X 226 | as G01 | G01 |
| G03_choose_route_two_ladders | ladderDx, ladderDy, playerAway | two-ladder level (needs the two-ladder variant of the body's level data: seeded ladder plus a second ladder at the mirror column) | stairs under both ladders built by the scenario (the override drives Tony's verb through the setup); Tony climbs the RIGHT ladder into the room above; the clone starts between the two stairs | the right ladder within 900 frames; taking the left one is a failure | G04 |
| G04_choose_route_two_ladders_mirror | ladderDx, ladderDy, playerAway | two-ladder level | as G03 with Tony up the LEFT ladder | the left ladder | G03 |
| G05_come_back_down | playerAway, routeDx, routeDy | 33 | the clone driven up the ladder into the room above (the north stop is masked for this scenario's build only if needed; otherwise Tony climbs first and the clone follows under the follow rule), then Tony climbs back down to the room below and walks away from the ladder | beside Tony on the floor of the room below within 900 frames, strict | G06 |
| G06_come_back_down_mirror | playerAway, routeDx, routeDy | 5 | the mirror at column 5 | as G05 | G05 |
| G07_seek_ladder_no_stairs | ladderDx, ladderDy | 33 | no stairs; Tony stands under the ladder on the floor; the clone at the far left | within 24 px of Tony on the floor within 600 frames (a walk guided by the ladder senses is not required, but the scenario measures whether the ladder senses disturb a plain walk) | G08 |
| G08_seek_ladder_no_stairs_mirror | ladderDx, ladderDy | 5 | the mirror | as G07 | G07 |

The extended teacher for these (written in Phase 4, before any survivor is trained on them): while
`playerAway`, the route point replaces Tony in the follow rules (walk toward it, climb the stairs
toward it, take the ladder); with two ladders, the route point is the ladder Tony used, which the
program records when Tony leaves the room; `ladderDx`/`ladderDy` are available to the readout but the
teacher's rules do not use them for the first four scenarios, so that G07/G08 measure whether their
presence disturbs the plain follow.
