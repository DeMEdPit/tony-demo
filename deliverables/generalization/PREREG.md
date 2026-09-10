# Pre-registration: does the taught brain generalize?

Written and committed before any arm was run. The question: has the perceptron taught in
`tools/teach_demo.py` (36 lessons, 4 sessions, from zero) learned a reusable policy, or a solution
specific to the teaching trajectory? Nothing below is changed after the results are in; the results
go in a second commit, and RESULTS.md carries the tables the script writes plus an interpretation
marked as written afterwards.

## What is frozen

| what | value |
|---|---|
| the brain | `deliverables/brains/taught-climb.bin`, 100 bytes, sha256 `fbf9bb1332be256503205faf3958b778b3dc96193c9e359c9c01d51905b0fb40` |
| the program | `deliverables/prg/minimal64/tony-body.prg`, sha256 `9976be313ca35a680ba70f75e137eff1b951a3bebeab15fcd2376f25333414e3` (49,348 bytes; the learning rule, the senses and the decoder are not touched) |
| the commit the inputs come from | `5116a2dda0f855eb8d1caf52d5b2afd572676138` |
| the permuted control | `taught-climb-permuted.bin`, the ten output rows of the brain reordered by the permutation [0, 6, 3, 8, 2, 5, 7, 9, 4, 1] (Python's `random.Random(20260910).shuffle`), sha256 `2b601297a9999fde61b5c4cdaa3e116ef017dc03825a228dd0f69707f3b93b0d` |
| the zero control | `zero.bin`, 100 zero bytes, sha256 `cd00e292c5970d3c5e2f0ffa5171e555bc46bfc4faddfb4a418b6840b86e79a3` |
| the materials table | `materials.bin`, the program's own ($BE00, 256 bytes), sha256 `a4b0a8929596eee913c9cbd1a5102418c64861afca15bfcdbbaf272c98643c2f`; bit 0 is wall, bit 1 ladder |

Teaching is off in every episode (`teachMode` 0). After each episode the weights are dumped and
compared byte for byte with what was installed, and `lessonTotal` must read 0; the brain file's hash
is checked before and after the whole run. The script asserts that the corpus it runs equals
`scenarios.json` and that every input's hash equals `hashes.json`.

## The five arms

| arm | slot | what it is |
|---|---|---|
| learned | kind 1, the frozen weights | the brain under test |
| follow | kind 0 | the Chamber's follow rule: walks to Tony, jumps and ducks with him, never climbs on its own |
| zero | kind 1, all weights zero | always action 0, idle: the trivial floor |
| builder | kind 2 | the hand-written rule over the same senses (`BODY.md`, "The builder"): the reference for what these senses allow, and the feasibility check on every scenario |
| permuted | kind 1, the rows permuted | the learned weights with the output rows scrambled: the same numbers, the mapping broken |

The arm is installed at t0, after an identical setup for all five (Tony's stick and, where the clone
must be placed, the override byte through the game's own physics; no position is poked). The clone's
kind during every setup is 0, as it was in teaching.

## Success, fixed in advance

A **near** goal succeeds at the first poll (every 8 frames from t0) where `|cloneX - tonyX| <= dx` and
`|cloneY - tonyY| <= dy`, in one of the listed states if any (2 and 7: on the ladder). Tony's position
is the one at that poll, so a moving Tony is followed. Time-to-goal is the poll's offset. A
**restraint** goal succeeds when every poll of the window has the clone on the floor (`Y >= 190`) and
within 80 px of Tony. The window ends at the limit or at success. Recorded per episode: success,
time-to-goal, the start and the final positions and states, the highest point reached, the closest
approach to Tony, bricks laid, whether he left the room, the weights' hash after, the lesson count.

Aggregates: per bucket and per arm, the number of successes over the bucket; for all held-out
scenarios; and over the held-out scenarios the builder solves (a scenario the builder cannot solve on
these senses is reported as such, and counts in the raw rate but not in that one).

## The corpus

Twenty-five scenarios, one the training start and twenty-four held out, in eight buckets. The ladder
column is the seeded one (the training's is 33); other columns come from the parameter block's seed
through `tools/stamp_mural.py`, which changes only the 32 seed bytes of the file (checked, below).
The stairs are always five bricks built by Tony with the game's own verb (four where the scenario
says so), rising rightward for a ladder at column 13 or more and leftward below.

| id | bucket | ladder | success | limit (frames) | what is different |
|---|---|---|---|---|---|
| A1_train_start | in_distribution **(training)** | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | the teaching demo's start: Tony's five bricks under the ladder at column 33 and his climb to Y 72; the clone followed to the foot (X 206) |
| B1_foot_facing_left | same_side_variant | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | at the foot but turned away: one frame of left before t0 |
| B2_tony_on_fourth_brick | same_side_variant | 33 | within 20 px of Tony's X and 12 of his Y | 480 | four bricks only: Tony stands on the fourth, clear of the ladder (state 0, so playerOnLadder is 0 throughout), dy 4 at the foot; the goal is beside him on it |
| B3_tony_climbs_late | same_side_variant | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 600 | Tony waits on the top brick 120 frames after t0, then climbs |
| B4_start_in_air | same_side_variant | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | the override launches a jump right at the foot four frames before t0 and lets go in the air |
| B5_partial_step2 | same_side_variant | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | driven onto the second brick before t0 |
| B6_partial_step4 | same_side_variant | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | driven onto the fourth brick before t0 |
| B7_start_on_top | same_side_variant | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | driven onto the fifth brick, under the ladder, before t0 |
| B8_tony_higher | same_side_variant | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | Tony ten frames higher on the ladder (Y 62): dy one bucket more at the top |
| B9_tony_lower | same_side_variant | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | Tony only twenty frames up the ladder (Y 102): dy 2 at the top |
| C1_far_left | walk_required | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 600 | the clone held at his start (X 146) while Tony builds and climbs: sixty pixels of floor before the first brick |
| C2_mid_distance | walk_required | 33 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 600 | driven to X 178: a jump's reach short of the first brick, nothing ahead in the senses |
| D1_two_high_wall | obstacle | 33 | within 20 px of Tony's X and 12 of his Y | 600 | Tony stacks two bricks in one slot and stands on them; the clone lifts the step Tony used: a two-high wall two columns ahead, an empty slot between |
| D2_brick_between | obstacle | 33 | within 24 px of Tony's X and 12 of his Y | 500 | one brick on the floor between the clone (X 146) and Tony, who crossed it and stands beyond on the floor |
| E1_mirror_with_walk | mirror | 9 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 600 | the ladder at column 9: Tony's stairs rise leftward; the clone parked to the right must walk left and jump left |
| E2_C21_from_right | mirror | 21 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 600 | the ladder at column 21, stairs rising rightward, the clone parked beyond them to the right: the floor under the floating stairs is open |
| F_ladder_C31 | ladder_same_side | 31 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | the training protocol with the seeded ladder at column 31 (training: 33), the clone following to the foot |
| F_ladder_C29 | ladder_same_side | 29 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | the training protocol with the seeded ladder at column 29 (training: 33), the clone following to the foot |
| F_ladder_C27 | ladder_same_side | 27 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | the training protocol with the seeded ladder at column 27 (training: 33), the clone following to the foot |
| F_ladder_C25 | ladder_same_side | 25 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | the seeded ladder at column 25: Tony's approach is left of the clone's start, so the clone is parked at the left first and driven to the foot after the climb |
| F_ladder_C21 | ladder_same_side | 21 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | the seeded ladder at column 21: Tony's approach is left of the clone's start, so the clone is parked at the left first and driven to the foot after the climb |
| F_ladder_C9_mirror | ladder_mirror | 9 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | the ladder at column 9: leftward stairs, the clone driven to their foot facing left before t0 |
| F_ladder_C5_mirror | ladder_mirror | 5 | on the ladder (states 2 or 7) within 16 px of Tony's X and 16 of his Y | 480 | the ladder at column 5: leftward stairs, the clone driven to their foot facing left before t0 |
| G1_beside_no_stairs | restraint | 33 | every poll on the floor (Y >= 190) and within 80 px of Tony | 300 | nothing built; Tony forty pixels right; success is staying on the floor near him |
| G2_tony_back_on_floor | restraint | 33 | every poll on the floor (Y >= 190) and within 80 px of Tony | 300 | four bricks stand but Tony walked back off them to the floor beside the clone; success is not climbing without him |

Buckets: **in_distribution** the teaching start itself; **same_side_variant** the training geometry
with a different clone start, height or timing; **walk_required** the first brick beyond the reach of
a wall check (the teacher never walked, so walking was never taught); **obstacle** something the
training never had (a two-high wall, a brick on the floor); **mirror** the stairs the other way round
or approached from the other side (no left-direction lesson exists; a perceptron has no mirror);
**ladder_same_side** the training protocol at other seeded ladder columns on the training side;
**ladder_mirror** at mirror columns, the clone driven to the foot; **restraint** Tony not above him:
success is staying put.

## The ladder-position PRGs

Stamped from the frozen program with `--text "holdout seed N" --block 25850267`; every file is the
same length and differs from the frozen program in exactly the 32 seed bytes at offset 0x5009. Each was
booted and its `buildLadderCol` read to confirm the column. Columns 5, 9, 21, 25, 27, 29 and 31 have a
candle (a lit room, as in training).

| file | ladder | seed text | bytes differing | sha256 |
|---|---|---|---|---|
| `prg/tony-body-ladder-C31.prg` | column 31 | `holdout seed 5` | 32 | `f7ea14a417d8a3edccffef8d4ebb7ac292e0ed78de27de0d993ad61c6e882471` |
| `prg/tony-body-ladder-C29.prg` | column 29 | `holdout seed 40` | 32 | `ca38b00b09e050827fe15a222461670d6e35d0af45e1802df099ecb81fb27a54` |
| `prg/tony-body-ladder-C27.prg` | column 27 | `holdout seed 3` | 32 | `2f1f0fd7ec976c9166219c95579b740639c99d20c0efb4bfe0dc85feb7c5e7a7` |
| `prg/tony-body-ladder-C25.prg` | column 25 | `holdout seed 35` | 32 | `45a7af15151c52f56dcd702b979cb72cf9ba1996c9899074e312cf8ba012783a` |
| `prg/tony-body-ladder-C21.prg` | column 21 | `holdout seed 6` | 32 | `415d0245fccca5ece2c58d17588172b88d0a26e772d9bc3b2e9c4611adb7d84f` |
| `prg/tony-body-ladder-C9.prg` | column 9 | `holdout seed 17` | 32 | `73044d7091627109a8c0a4ff690007da38acec29cf75f6bfe295e06cf08e7afc` |
| `prg/tony-body-ladder-C5.prg` | column 5 | `holdout seed 1` | 32 | `d0bf34856124e28cbf66b339e96d08da9180f6b361ca9227cc1b39e5f3b7dee6` |

## What is logged for the aliasing question

Every poll of every episode records the 20-sense vector with the arm's action, the builder twin's
action (a Python copy of `builderThink`, checked against the builder arm's own actions in the log), the
privileged oracle's action, and the positions and the map. The oracle reads what the senses cannot:
the exact positions and heights, and the screen cells, with the builder's own distances (48 px, two
bricks) so that a disagreement comes from the map or the exact geometry, not from another policy.

`train` re-runs the four teaching sessions (deterministic; the script checks they reproduce the frozen
brain byte for byte) and records every sense vector the clone was in, polled every think period, and
the 36 lessons as recorded in the `LESSON1` block. Reported: the distinct vectors met by the learned arm
that never appeared in teaching (novel), the frozen brain's agreement with the twin on seen and on
novel vectors, **oracle aliasing** (the same 20 senses, the oracle wanting different actions), and
**label aliasing** in the lessons themselves (the same senses taught different actions).

## Predictions, written before the run

- **in_distribution**: learned succeeds; follow, zero and permuted fail; builder succeeds.
- **same_side_variant**: learned succeeds on the partial climbs, the in-air start and the two ladder
  heights, because those states were in the trajectory. Uncertain on B1 (facing left: no such state
  was taught), on B2 (Tony off the ladder: every lesson had `playerOnLadder` 7, and that sense may be
  carrying weight it should not) and on B3 (he may climb to the top and wait, or not). Builder
  succeeds on all.
- **walk_required**: learned fails, unless the taught jump right serves as locomotion from a standing
  state with nothing ahead, which I cannot rule out. Builder succeeds. Follow fails (it walks to the
  first brick and stops).
- **obstacle**: learned fails both (it never built and never walked). Builder succeeds on D2; D1
  depends on whether the verb lets him lay in the slot next to the stack while Tony stands on it.
- **mirror**: learned fails both; builder succeeds on E1, uncertain on E2.
- **ladder_same_side**: learned succeeds on all five (the states are the training's up to the dx
  bucket); builder succeeds.
- **ladder_mirror**: learned fails both; builder succeeds.
- **restraint**: follow, zero and builder succeed on both. Learned fails G2 (it jumps at the wall in
  front of it whatever Tony is doing) and is uncertain on G1. Permuted: unknown.
- Overall for the learned arm on the held-out set: roughly a third to a half; near zero for follow,
  zero and permuted; high for the builder. If that is the shape, the reading is "a small reusable
  policy over the states it saw, nothing outside them", which is task construction (one trajectory,
  one direction, no walking) and the linear model's lack of symmetry, not the senses or the rule. If
  the same-side variants fail too, the diagnosis moves to the senses or the quantised weights.
- Aliasing: I expect label aliasing in the lessons from the teacher's reaction lag (the same standing
  state taught idle at one tick and jump at the next), and little oracle aliasing on the training side.

## How to run

```
python3 tools/generalization_test.py prereg     # already done: the files in this directory
python3 tools/generalization_test.py check      # the start state of every scenario, no arm
python3 tools/generalization_test.py train      # training-set.json
python3 tools/generalization_test.py run        # results.json, encountered.json, RESULTS.md
```
