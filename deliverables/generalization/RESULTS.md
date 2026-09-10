# Generalization test: results

The inputs' commit: `5116a2dda0f855eb8d1caf52d5b2afd572676138`; the pre-registration commit the run started from: `8000dc032a3590465e0e7428d6e245faba2f6337`. Brain `taught-climb.bin` sha256 `fbf9bb1332be256503205faf3958b778b3dc96193c9e359c9c01d51905b0fb40` before, `fbf9bb1332be256503205faf3958b778b3dc96193c9e359c9c01d51905b0fb40` after the run; in memory after every episode: 125 of 125 unchanged, lessons taken during evaluation: 0.

## Per scenario

| scenario | bucket | learned | follow | zero | builder | permuted |
|---|---|---|---|---|---|---|
| A1_train_start | in_distribution (training) | ok 200 | FAIL (Y 206, d 212) | FAIL (Y 206, d 212) | ok 200 | FAIL (Y 206, d 206) |
| B1_foot_facing_left | same_side_variant | ok 200 | FAIL (Y 206, d 212) | FAIL (Y 206, d 212) | ok 200 | FAIL (Y 206, d 207) |
| B2_tony_on_fourth_brick | same_side_variant | ok 80 | FAIL (Y 206, d 125) | FAIL (Y 206, d 125) | ok 80 | FAIL (Y 206, d 119) |
| B3_tony_climbs_late | same_side_variant | ok 200 | FAIL (Y 206, d 161) | FAIL (Y 206, d 161) | ok 200 | FAIL (Y 206, d 155) |
| B4_start_in_air | same_side_variant | ok 192 | FAIL (Y 190, d 172) | FAIL (Y 190, d 172) | ok 192 | FAIL (Y 206, d 172) |
| B5_partial_step2 | same_side_variant | ok 136 | FAIL (Y 174, d 147) | FAIL (Y 174, d 149) | ok 136 | FAIL (Y 174, d 147) |
| B6_partial_step4 | same_side_variant | ok 72 | FAIL (Y 142, d 87) | FAIL (Y 142, d 87) | ok 72 | FAIL (Y 190, d 81) |
| B7_start_on_top | same_side_variant | ok 48 | FAIL (Y 126, d 55) | FAIL (Y 126, d 55) | ok 48 | FAIL (Y 126, d 55) |
| B8_tony_higher | same_side_variant | ok 216 | FAIL (Y 206, d 222) | FAIL (Y 206, d 222) | ok 216 | FAIL (Y 206, d 216) |
| B9_tony_lower | same_side_variant | ok 168 | FAIL (Y 206, d 182) | FAIL (Y 206, d 182) | ok 168 | FAIL (Y 206, d 177) |
| C1_far_left | walk_required | ok 240 | FAIL (Y 206, d 212) | FAIL (Y 206, d 270) | ok 232 | FAIL (Y 206, d 212) |
| C2_mid_distance | walk_required | ok 200 | FAIL (Y 206, d 212) | FAIL (Y 206, d 238) | ok 216 | FAIL (Y 206, d 212) |
| D1_two_high_wall | obstacle | ok 16 | FAIL (Y 206, d 71) | FAIL (Y 206, d 71) | FAIL (Y 190, d 32, +1 bricks) | FAIL (Y 206, d 45) |
| D2_brick_between | obstacle | ok 64 | FAIL (Y 206, d 43) | FAIL (Y 206, d 85) | FAIL (Y 206, d 45) | FAIL (Y 206, d 43) |
| E1_mirror_with_walk | mirror | FAIL (Y 206, d 266) | FAIL (Y 206, d 210) | FAIL (Y 206, d 266) | FAIL (Y 206, d 49) | FAIL (Y 206, d 266) |
| E2_C21_from_right | mirror | FAIL (Y 206, d 210) | FAIL (Y 206, d 172) | FAIL (Y 206, d 210) | FAIL (Y 134, d 65, +3 bricks) | FAIL (Y 206, d 210) |
| F_ladder_C31 | ladder_same_side | FAIL (Y 206, d 51) | FAIL (Y 206, d 212) | FAIL (Y 206, d 212) | FAIL (Y 206, d 51) | FAIL (Y 206, d 206) |
| F_ladder_C29 | ladder_same_side | FAIL (Y 206, d 56) | FAIL (Y 206, d 212) | FAIL (Y 206, d 212) | FAIL (Y 206, d 56) | FAIL (Y 206, d 207) |
| F_ladder_C27 | ladder_same_side | FAIL (Y 206, d 56) | FAIL (Y 206, d 212) | FAIL (Y 206, d 212) | FAIL (Y 190, d 56, +1 bricks) | FAIL (Y 206, d 207) |
| F_ladder_C25 | ladder_same_side | FAIL (Y 206, d 54) | FAIL (Y 206, d 212) | FAIL (Y 206, d 212) | FAIL (Y 134, d 54, +4 bricks) | FAIL (Y 206, d 206) |
| F_ladder_C21 | ladder_same_side | FAIL (Y 206, d 54) | FAIL (Y 206, d 212) | FAIL (Y 206, d 212) | FAIL (Y 134, d 54, +4 bricks) | FAIL (Y 206, d 206) |
| F_ladder_C9_mirror | ladder_mirror | FAIL (Y 206, d 204) | FAIL (Y 206, d 210) | FAIL (Y 206, d 210) | FAIL (Y 206, d 56) | FAIL (Y 206, d 170) |
| F_ladder_C5_mirror | ladder_mirror | FAIL (Y 206, d 204) | FAIL (Y 206, d 210) | FAIL (Y 206, d 210) | ok 200 | FAIL (Y 206, d 170) |
| G1_beside_no_stairs | restraint | FAIL (Y 206, d 12) | ok | ok | ok | FAIL (Y 206, d 4) |
| G2_tony_back_on_floor | restraint | FAIL (Y 206, d 19) | ok | ok | ok | FAIL (Y 206, d 3) |

## Aggregate success

| bucket | n | learned | follow | zero | builder | permuted |
|---|---|---|---|---|---|---|
| in_distribution | 1 | 1/1 | 0/1 | 0/1 | 1/1 | 0/1 |
| same_side_variant | 9 | 9/9 | 0/9 | 0/9 | 9/9 | 0/9 |
| walk_required | 2 | 2/2 | 0/2 | 0/2 | 2/2 | 0/2 |
| obstacle | 2 | 2/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| mirror | 2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| ladder_same_side | 5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| ladder_mirror | 2 | 0/2 | 0/2 | 0/2 | 1/2 | 0/2 |
| restraint | 2 | 0/2 | 2/2 | 2/2 | 2/2 | 0/2 |
| **all held out** | 24 | 13/24 | 2/24 | 2/24 | 14/24 | 0/24 |
| held out and builder-solvable | 14 | 11/14 | 2/14 | 2/14 | 14/14 | 0/14 |

## Encountered sense vectors

629 distinct 20-sense vectors over all arms; the learned arm met 219, of which 174 never appeared in the four teaching sessions (training-set.json).
The frozen brain's action agrees with the builder twin's on 45/45 of the vectors seen in teaching and 119/174 of the novel ones.
Oracle aliasing (the same 20 senses, the privileged oracle wanting different actions): 8 vectors.
Twin check: the builder arm's machine action matched the Python twin on the same block for 223 of 253 vectors it met (the machine's action can lag one block behind the polled one).

| senses (dx dy facing ground air ladder duck floor wallF wallH brick ladderHere ladderBelow buildable pAir last still pDuck pLadder) | oracle actions | twin | learned |
|---|---|---|---|
| 7,5,7,7,0,7,0,0,7,7,0,7,0,0,0,0,0,0,0,7 | idle, jump right | idle | idle |
| 7,1,4,7,0,7,0,0,7,7,0,7,0,0,0,0,0,0,0,7 | idle, jump right | idle | idle |
| 7,0,3,7,0,7,0,0,7,7,7,0,7,0,0,0,0,0,0,7 | idle, up | idle | idle |
| 7,6,7,7,7,0,0,0,7,0,0,0,0,0,0,0,2,0,0,7 | right, jump right | right | up |
| 7,0,4,7,0,7,0,0,7,7,7,0,7,0,0,0,0,0,0,7 | idle, up | idle | idle |
| 7,7,7,0,7,0,0,0,7,0,0,0,0,0,7,0,0,1,0,7 | idle, right | right | jump right |
| 7,0,5,0,0,7,0,0,7,7,0,7,0,0,0,0,0,0,0,7 | idle, jump left | idle | idle |
| 7,-6,7,7,7,0,0,0,7,0,0,0,0,0,7,0,0,1,0,7 | left, jump left | left | up |

## The lessons' own labels

36 lessons recorded over the four sessions (the sessions reproduce the frozen brain: True); 21 distinct states among them; 4 states carry conflicting labels (the same senses taught different actions):
- `7,6,7,7,0,7,0,0,0,7,0,7,0,0,0,0,7,0,0,7`: idle x3, jump right x1
- `7,5,7,7,0,7,0,0,0,7,0,7,0,0,0,0,7,0,0,7`: idle x1, jump right x2
- `7,3,5,7,0,7,0,0,0,7,0,7,0,0,0,0,7,0,0,7`: idle x1, jump right x2
- `7,1,4,7,0,7,0,0,0,7,0,7,0,0,0,0,7,0,0,7`: idle x2, jump right x1

## Where the learned brain and the twin disagree on novel states

| senses | learned | twin | oracle | met in |
|---|---|---|---|---|
| 7,6,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,2,0,7 | jump right | right | idle | 1 polls |
| 7,0,0,7,7,0,0,0,7,0,0,0,0,0,7,0,0,1,0,0 | up | idle | idle | 1 polls |
| 7,-7,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,2,0,7 | up | left | left | 1 polls |
| 7,-7,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,3,0,7 | up | left | left | 1 polls |
| 7,-7,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,4,0,7 | up | left | left | 2 polls |
| 7,-7,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,5,0,7 | up | left | left | 4 polls |
| 7,-7,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,6,0,7 | up | left | left | 8 polls |
| 7,-7,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,7,0,7 | up | left | left | 59 polls |
| 7,-6,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,2,0,7 | up | left | left | 1 polls |
| 7,-6,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,3,0,7 | up | left | left | 1 polls |
| 7,-6,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,4,0,7 | up | left | left | 2 polls |
| 7,-6,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,5,0,7 | up | left | left | 4 polls |
| 7,-6,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,6,0,7 | up | left | left | 8 polls |
| 7,-6,7,0,7,0,0,0,7,0,0,0,0,0,7,0,3,7,0,7 | up | left | left | 59 polls |
| 7,-2,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,2,0,7 | up | idle | left | 1 polls |
| 7,-2,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,3,0,7 | up | idle | left | 1 polls |
| 7,-2,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,4,0,7 | up | idle | left | 2 polls |
| 7,-2,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,5,0,7 | up | idle | left | 4 polls |
| 7,-2,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,6,0,7 | up | idle | left | 8 polls |
| 7,-2,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,7,0,7 | up | idle | left | 22 polls |
| 7,-3,7,7,7,0,0,0,7,7,7,0,0,0,0,0,0,2,0,7 | up | idle | left | 1 polls |
| 7,-3,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,3,0,7 | up | idle | left | 1 polls |
| 7,-3,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,4,0,7 | up | idle | left | 2 polls |
| 7,-3,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,5,0,7 | up | idle | left | 4 polls |
| 7,-3,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,6,0,7 | up | idle | left | 8 polls |
| 7,-3,7,7,7,0,0,0,7,7,7,0,0,0,0,0,3,7,0,7 | up | idle | left | 23 polls |
| 7,-3,7,7,7,0,0,0,7,0,0,0,0,0,7,0,0,2,0,7 | up | build right | build left | 1 polls |
| 7,-3,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,3,0,7 | up | build right | build left | 3 polls |
| 7,-3,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,4,0,7 | up | build right | build left | 6 polls |
| 7,-3,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,5,0,7 | up | build right | build left | 12 polls |
| 7,-3,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,6,0,7 | up | build right | build left | 24 polls |
| 7,-3,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,7,0,7 | up | build right | build left | 69 polls |
| 7,-3,7,7,7,0,0,0,7,0,0,0,0,0,7,0,0,1,0,7 | up | build right | build left | 2 polls |
| 7,-6,7,7,7,0,0,0,7,0,0,0,0,0,7,0,0,1,0,7 | up | left | left, jump left | 2 polls |
| 7,-6,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,3,0,7 | up | left | left | 2 polls |
| 7,-6,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,4,0,7 | up | left | left | 4 polls |
| 7,-6,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,5,0,7 | up | left | left | 8 polls |
| 7,-6,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,6,0,7 | up | left | left | 16 polls |
| 7,-6,7,7,7,0,0,0,7,0,0,0,0,0,7,0,3,7,0,7 | up | left | left | 82 polls |
| 7,-1,0,7,7,0,0,0,7,0,0,0,0,0,7,0,3,1,0,0 | jump right | idle | idle | 1 polls |
| 7,-5,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,1,0,0 | up | left | left | 1 polls |
| 7,-5,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,3,0,0 | up | left | left | 1 polls |
| 7,-5,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,4,0,0 | up | left | left | 2 polls |
| 7,-5,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,5,0,0 | up | left | left | 4 polls |
| 7,-5,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,6,0,0 | up | left | left | 8 polls |
| 7,-5,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,7,0,0 | up | left | left | 14 polls |
| 7,-4,-1,7,7,0,0,0,7,7,0,7,0,0,0,0,0,1,0,0 | jump right | idle | idle | 1 polls |
| 7,-5,-2,7,7,0,0,0,7,7,0,7,0,0,0,0,0,1,0,0 | jump right | left | left | 1 polls |
| 7,-6,-3,7,7,0,0,0,7,7,0,7,0,0,0,0,0,1,0,0 | jump right | left | left | 1 polls |
| 7,-6,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,2,0,0 | up | left | left | 1 polls |
| 7,-6,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,3,0,0 | up | left | left | 1 polls |
| 7,-6,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,4,0,0 | up | left | left | 2 polls |
| 7,-6,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,5,0,0 | up | left | left | 4 polls |
| 7,-6,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,6,0,0 | up | left | left | 8 polls |
| 7,-6,0,7,7,0,0,0,7,7,7,0,0,0,0,0,3,7,0,0 | up | left | left | 4 polls |

---

# Interpretation, written after the run

Everything above this line was written by the script. The numbers stand as pre-registered; what
follows reads them, with the post-hoc probes in `probes.txt` (run afterwards, on the same frozen
inputs, changing nothing in `results.json`).

## Integrity

125 episodes, five arms on the same 25 setups. The weights were unchanged after every episode, the
lesson counter read zero in every episode, the brain file's hash is the same before and after, and
the corpus the script ran is the committed one. The four teaching sessions, re-run, reproduce the
frozen brain byte for byte, so the "seen in teaching" set is the real one.

## Two mechanical successes that are not real ones

The **near** goal for scenarios where Tony stands on a brick (B2, D1) had no state requirement, and
the learned arm met it in mid-air, passing through the goal box during a jump. Run to the end of
their windows (`probes.txt`, section 1), B2 ends with him overshooting the fourth brick, falling past
the room's wall to the floor and standing there pressing up; D1 ends in a loop of jumping at the
two-high wall from the same spot. The builder's B2 is a mid-air pass too, and it then stands one brick
below Tony, 13 px away, by its own "stay beside him" rule. So, counting only successes that hold in a
grounded or ladder state (a stricter reading than the one registered, applied to every arm alike):

| held out, 24 | learned | follow | zero | builder | permuted |
|---|---|---|---|---|---|
| as registered | 13 | 2 | 2 | 14 | 0 |
| substantive (B2 and D1 not counted for anyone) | 11 | 2 | 2 | 13 | 0 |

The goal definition was the mistake, and it is recorded here rather than repaired.

## What the brain learned, and what it did not

The frozen weights have three non-zero rows: idle, up and jump right (`probes.txt`, section 3). Every
other action's row is zero, because the teacher never used it: the taught policy is a three-way
choice. Read off the weights and confirmed by the episodes:

1. **On the ground with Tony to the right: jump right.** Taught as "a step is ahead: jump it", it
   fires with nothing ahead too (the wall senses carry little weight; the ground, the still count and
   the last action carry it), which is why the two walk-required starts succeeded: he hopped across
   sixty pixels of floor to the stairs (C1, 240 frames) and up them. The same rule, with Tony beside
   him on the floor and no stairs, hops him past Tony to the far wall (G1), and with the stairs
   standing and Tony back on the floor it climbs them without him (G2): the "wall ahead" and "Tony
   above" conditions were never contrasted in teaching, since Tony was always above, so the rule has
   no restraint. Every restraint scenario failed.
2. **In the air: nothing.** Clean; the air flag outweighs everything.
3. **A ladder in the box, Tony above: up.** Attributed to the ladder sense, not to the wall that
   happened to stand beside the training ladder: driven onto the top brick at column 31, away from the
   wall, he climbs to Tony (`probes.txt`, section 2), and the two ladder heights and the partial
   climbs all passed.

What it did not learn is exactly what the trajectory did not contain: no left, no walk, no build,
no restraint. Mirror scenarios 0 of 4, obstacles 0 of 2 in the substantive count. And one thing it
learned wrongly by extrapolation: **"up" whenever Tony is to his left.** Every lesson had Tony to the
right or straight above, so the up row's dx weight was only ever pushed down (each "jump right" lesson
that the brain had mispredicted as "up" subtracted the sign of dx), and a linear unit turns "not when he
is to the right" into "yes when he is to the left". In every mirror start he stands pressing up at
nothing, or hops right, away from the stairs. This is the one clear artefact of the model class in the
results: a perceptron over a signed distance has no way to say "dx does not matter here" once one sign
has argued with it.

Agreement with the builder twin: 45 of 45 on the vectors seen in teaching (the brain reproduces its
teacher on everything it saw) and 119 of 174 on vectors it had never seen (68%). The 55 disagreements
are the dx < 0 states (up instead of left) and the states whose right answer is an action with a zero
row (left, build, right).

## The ladder-position bucket is a finding about the teacher, not the learner

All five same-side ladder columns failed, for the learned arm and the builder alike, in the same way:
the jump from the fourth brick overshoots the fifth. A running jump carries about thirty pixels and a
brick is sixteen wide; at the training column the fifth brick stands against the room's wall, which
stopped every jump and put him on the brick, and nobody noticed the crutch. At any other column he
flies over the top brick and falls to the floor on the far side (`F_ladder_C31` in `probes.txt`,
section 4), then stands at the wall pressing up. On the mirror side the same physics explain the one
builder success (column 5, against the left wall) and its failure at column 9. The learned brain
matched the builder step for step in this bucket. The cause is the teacher's stepping method (jump at
a wall) and the training geometry, not the learner; the game's own step-up verb (bit 6) moves exactly
one brick and would not overshoot.

## Aliasing

- **In the lessons' labels**: 4 of 21 lesson states carry both "idle" and "jump right", all of them
  in-air states just after a launch. The teacher held the jump lines for a whole think period, so the
  second, third and fourth frames of each hold paired air states with "jump right", and later air
  frames, after the release, with "idle". That is the teacher's granularity, not the senses. Harmless
  in effect (a jump held in the air does nothing) but it spent lessons.
- **Against the privileged oracle**: 8 of 629 vectors, all in-air blocks. The block describes the
  frame before the poll, so the same block covers "still in the air" and "just landed", and the
  oracle, reading the newer record, wants idle for one and a jump or a climb for the other. This is
  the one-frame publish lag of the sense pipeline; the period-4 think mostly hides it. No aliasing was
  found in grounded states: nothing in the corpus needed two actions from one grounded observation.
- **Twin check**: the builder arm's machine action matched the Python twin on 223 of 253 vectors on
  the same block; the rest are the one-block lag between the polled block and the last think.

## Diagnosis, by cause

- **Task construction: the dominant cause.** One trajectory, one direction, Tony always above and to
  the right, no walking or building in the lessons, a wall behind the training ladder that the
  teacher's method depended on, and a teacher whose holds outlast the launch. Everything the brain
  failed at outside the mirror artefact traces here.
- **Linear-model capacity: one clear artefact.** The dx sign extrapolation ("up when Tony is to the
  left"). Also structural: no mirror, so left needs its own lessons; and restraint needs the
  conjunction "wall ahead and Tony above", which a perceptron can represent but was never shown the
  negative of.
- **Senses: no failure found.** The ladder rule sits on the ladder sense; the training-side variants
  (facing away, mid-air, partial climbs, other heights, late Tony, both walk starts) all passed; the
  overshoot is invisible to the senses but is not caused by them (the rule-based builder falls the same
  way). The only representational gap seen is the one-frame lag in the air.
- **Quantisation: no evidence.** The decisive margins are large (35 against -12 at the foot, 27
  against -9 at the top), no weight reached saturation (the largest magnitude is 6).
- **Learning rule: no evidence.** The rule reproduced the teacher on every state it saw and converged in
  four sessions; every artefact traces to the data it was given.

## The answer

A reusable policy, but a small one: three rules that carry to starts, heights, timings and distances
the teaching never showed, on the side and in the direction it was taught, and nothing beyond that.
The learned brain's substantive held-out rate (11 of 24) is close to the hand-written builder's (13 of
24) on the same corpus, and their failures overlap because most of them belong to the teacher's method
and the training geometry, not to the learner. Not fixed here, as asked: the candidates are a teacher
that steps with the step-up verb, lessons on both sides, a restraint lesson (Tony beside him at a wall:
idle), and a look at whether dx should be split into two one-sided senses before more capacity is
considered.
