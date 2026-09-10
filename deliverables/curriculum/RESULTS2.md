# Curriculum experiment: results

Strict rule for every arm: a near goal counts only in a grounded or ladder state.

## The old corpus (regression, 24 held out)

| scenario | bucket | learned2 | learned_old | teacher | builder | follow | zero | permuted2 |
|---|---|---|---|---|---|---|---|---|
| A1_train_start | in_distribution (training) | FAIL (d 55) | ok 200 | ok 272 | ok 200 | FAIL (d 212) | FAIL (d 212) | FAIL (d 48) |
| B1_foot_facing_left | same_side_variant | FAIL (d 55) | ok 200 | ok 276 | ok 200 | FAIL (d 212) | FAIL (d 212) | FAIL (d 48) |
| B2_tony_on_fourth_brick | same_side_variant | FAIL (d 5) | FAIL (d 11) | FAIL (d 54, +3) | FAIL (d 21) | FAIL (d 125) | FAIL (d 125) | FAIL (d 85) |
| B3_tony_climbs_late | same_side_variant | FAIL (d 53) | ok 200 | FAIL (d 66, +-5) | ok 200 | FAIL (d 161) | FAIL (d 161) | FAIL (d 46) |
| B4_start_in_air | same_side_variant | FAIL (d 55) | ok 192 | ok 264 | ok 192 | FAIL (d 172) | FAIL (d 172) | FAIL (d 48) |
| B5_partial_step2 | same_side_variant | FAIL (d 55) | ok 136 | ok 208 | ok 136 | FAIL (d 147) | FAIL (d 149) | FAIL (d 49) |
| B6_partial_step4 | same_side_variant | FAIL (d 55) | ok 72 | ok 144 | ok 72 | FAIL (d 87) | FAIL (d 87) | FAIL (d 49) |
| B7_start_on_top | same_side_variant | FAIL (d 55) | ok 48 | ok 40 | ok 48 | FAIL (d 55) | FAIL (d 55) | FAIL (d 55) |
| B8_tony_higher | same_side_variant | FAIL (d 31) | ok 216 | ok 208 | ok 216 | FAIL (d 222) | FAIL (d 222) | FAIL (d 58) |
| B9_tony_lower | same_side_variant | FAIL (d 25) | ok 168 | ok 200 | ok 168 | FAIL (d 182) | FAIL (d 182) | FAIL (d 18) |
| C1_far_left | walk_required | FAIL (d 103, +5) | ok 240 | ok 300 | ok 232 | FAIL (d 212) | FAIL (d 270) | FAIL (d 48) |
| C2_mid_distance | walk_required | FAIL (d 71, +5) | ok 200 | ok 284 | ok 216 | FAIL (d 212) | FAIL (d 238) | FAIL (d 48) |
| D1_two_high_wall | obstacle | FAIL (d 9, +1) | FAIL (d 21) | FAIL (d 8, +1) | FAIL (d 32, +1) | FAIL (d 71) | FAIL (d 71) | FAIL (d 21) |
| D2_brick_between | obstacle | FAIL (d 85) | ok 64 | ok 48 | FAIL (d 45) | FAIL (d 43) | FAIL (d 85) | FAIL (d 85) |
| E1_mirror_with_walk | mirror | FAIL (d 56) | FAIL (d 266) | ok 296 | FAIL (d 49) | FAIL (d 210) | FAIL (d 266) | FAIL (d 210) |
| E2_C21_from_right | mirror | FAIL (d 210, +1) | FAIL (d 210) | FAIL (d 103, +3) | FAIL (d 65, +3) | FAIL (d 172) | FAIL (d 210) | FAIL (d 205) |
| F_ladder_C31 | ladder_same_side | FAIL (d 53, +1) | FAIL (d 51) | ok 268 | FAIL (d 51) | FAIL (d 212) | FAIL (d 212) | FAIL (d 53) |
| F_ladder_C29 | ladder_same_side | FAIL (d 53, +1) | FAIL (d 56) | FAIL (d 76) | FAIL (d 56) | FAIL (d 212) | FAIL (d 212) | FAIL (d 50) |
| F_ladder_C27 | ladder_same_side | FAIL (d 53, +2) | FAIL (d 56) | ok 268 | FAIL (d 56, +1) | FAIL (d 212) | FAIL (d 212) | FAIL (d 56) |
| F_ladder_C25 | ladder_same_side | FAIL (d 53, +1) | FAIL (d 54) | ok 268 | FAIL (d 54, +4) | FAIL (d 212) | FAIL (d 212) | FAIL (d 51) |
| F_ladder_C21 | ladder_same_side | FAIL (d 53, +1) | FAIL (d 54) | ok 268 | FAIL (d 54, +4) | FAIL (d 212) | FAIL (d 212) | FAIL (d 51) |
| F_ladder_C9_mirror | ladder_mirror | FAIL (d 56) | FAIL (d 204) | ok 268 | FAIL (d 56) | FAIL (d 210) | FAIL (d 210) | FAIL (d 210) |
| F_ladder_C5_mirror | ladder_mirror | FAIL (d 50) | FAIL (d 204) | ok 272 | ok 200 | FAIL (d 210) | FAIL (d 210) | FAIL (d 210) |
| G1_beside_no_stairs | restraint | ok | FAIL (d 12) | ok | ok | ok | ok | ok |
| G2_tony_back_on_floor | restraint | FAIL (d 19) | FAIL (d 19) | ok | ok | ok | ok | FAIL (d 19) |

| bucket | n | learned2 | learned_old | teacher | builder | follow | zero | permuted2 |
|---|---|---|---|---|---|---|---|---|
| in_distribution | 1 | 0/1 | 1/1 | 1/1 | 1/1 | 0/1 | 0/1 | 0/1 |
| same_side_variant | 9 | 0/9 | 8/9 | 7/9 | 8/9 | 0/9 | 0/9 | 0/9 |
| walk_required | 2 | 0/2 | 2/2 | 2/2 | 2/2 | 0/2 | 0/2 | 0/2 |
| obstacle | 2 | 0/2 | 1/2 | 1/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| mirror | 2 | 0/2 | 0/2 | 1/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| ladder_same_side | 5 | 0/5 | 0/5 | 4/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| ladder_mirror | 2 | 0/2 | 0/2 | 2/2 | 1/2 | 0/2 | 0/2 | 0/2 |
| restraint | 2 | 1/2 | 0/2 | 2/2 | 2/2 | 2/2 | 2/2 | 1/2 |
| **all held out** | 24 | 1/24 | 11/24 | 19/24 | 13/24 | 2/24 | 2/24 | 1/24 |

## The shadow holdout (fresh)

| scenario | bucket | learned2 | learned_old | teacher | builder | follow | zero | permuted2 |
|---|---|---|---|---|---|---|---|---|
| H01_tony_on_third_brick_C29 | middle_brick | FAIL (d 9, +4) | FAIL (d 9) | FAIL (d 30, +1) | FAIL (d 21) | FAIL (d 93) | FAIL (d 93) | FAIL (d 88) |
| H02_step2_facing_away | same_side_variant | FAIL (d 55) | ok 144 | ok 212 | ok 144 | FAIL (d 147) | FAIL (d 151) | FAIL (d 49) |
| H03_far_left_150px | walk_required | FAIL (d 183, +5) | ok 272 | ok 340 | ok 272 | FAIL (d 212) | FAIL (d 350) | FAIL (d 48) |
| H04_two_wide_platform | obstacle | FAIL (d 89) | ok 64 | ok 52 | FAIL (d 45) | FAIL (d 63) | FAIL (d 89) | FAIL (d 89) |
| H05_mirror_far_right_C9 | mirror | FAIL (d 51) | FAIL (d 320) | ok 324 | FAIL (d 53) | FAIL (d 210) | FAIL (d 320) | FAIL (d 210) |
| H06_restraint_left_wall | restraint | ok | FAIL (d 38) | ok | ok | ok | ok | ok |
| H07_tony_below_clone_on_step3 | tony_below | FAIL (d 104) | FAIL (d 100) | ok 44 | FAIL (d 76) | FAIL (d 70) | FAIL (d 110) | FAIL (d 110, +1) |
| H08_stack_from_right_far | obstacle | FAIL (d 64, +1) | FAIL (d 89) | FAIL (d 29) | FAIL (d 32, +1) | FAIL (d 71) | FAIL (d 95) | FAIL (d 95) |
| H09_ladder_C21_from_far_right | mirror | FAIL (d 124, +1) | FAIL (d 230) | FAIL (d 103, +3) | FAIL (d 103, +3) | FAIL (d 172) | FAIL (d 230) | FAIL (d 138) |
| H10_tony_climbs_while_mid_stairs | timing | FAIL (d 53) | ok 136 | FAIL (d 34, +-5) | ok 136 | FAIL (d 96) | FAIL (d 98) | FAIL (d 47) |
| H11_tony_walks_away | restraint | FAIL (d 38) | FAIL (d 12) | ok | ok | ok | FAIL (d 38) | FAIL (d 38) |
| H12_tony_ducks | restraint | ok | FAIL (d 12) | ok | ok | ok | ok | ok |
| H13_tony_on_single_brick | middle_brick | FAIL (d 71) | FAIL (d 10) | FAIL (d 9) | FAIL (d 55) | FAIL (d 55) | FAIL (d 71) | FAIL (d 71) |
| H14_C5_far_start_tony_high | ladder_mirror | FAIL (d 60) | FAIL (d 362) | ok 280 | ok 288 | FAIL (d 220) | FAIL (d 362) | FAIL (d 220) |
| H15_C27_tony_low | ladder_same_side | FAIL (d 23, +1) | FAIL (d 24) | ok 200 | FAIL (d 24, +1) | FAIL (d 182) | FAIL (d 182) | FAIL (d 24) |
| H16_clone_on_top_tony_on_floor | tony_below | FAIL (d 142) | FAIL (d 100) | ok 60 | FAIL (d 76) | FAIL (d 70) | FAIL (d 142) | FAIL (d 142) |

| bucket | n | learned2 | learned_old | teacher | builder | follow | zero | permuted2 |
|---|---|---|---|---|---|---|---|---|
| middle_brick | 2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| same_side_variant | 1 | 0/1 | 1/1 | 1/1 | 1/1 | 0/1 | 0/1 | 0/1 |
| walk_required | 1 | 0/1 | 1/1 | 1/1 | 1/1 | 0/1 | 0/1 | 0/1 |
| obstacle | 2 | 0/2 | 1/2 | 1/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| mirror | 2 | 0/2 | 0/2 | 1/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| restraint | 3 | 2/3 | 0/3 | 3/3 | 3/3 | 3/3 | 2/3 | 2/3 |
| tony_below | 2 | 0/2 | 0/2 | 2/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| timing | 1 | 0/1 | 1/1 | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 |
| ladder_mirror | 1 | 0/1 | 0/1 | 1/1 | 1/1 | 0/1 | 0/1 | 0/1 |
| ladder_same_side | 1 | 0/1 | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| **all** | 16 | 2/16 | 4/16 | 11/16 | 7/16 | 3/16 | 2/16 | 2/16 |

## The residual against the teacher

231 distinct sense vectors were visited under teaching; the frozen brain reproduces the teacher's action on 184 of them (79.7%).
| senses | teacher | brain |
|---|---|---|
| 7,4,0,7,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,0 | right | idle |
| 7,4,0,7,7,0,0,0,7,0,0,0,0,0,0,0,2,0,0,0 | right | idle |
| 7,3,0,7,7,0,0,0,7,0,0,0,0,0,0,0,2,0,0,0 | right | idle |
| 7,2,0,7,7,0,0,0,7,0,0,0,0,0,0,0,2,0,0,0 | right | idle |
| 7,0,0,7,7,0,0,0,7,0,0,0,0,0,0,0,0,4,0,0 | idle | build right |
| 7,0,0,7,7,0,0,0,7,0,0,0,0,0,0,0,0,5,0,0 | idle | build right |
| 7,0,0,7,7,0,0,0,7,0,0,0,0,0,0,0,0,6,0,0 | idle | build right |
| 7,0,0,7,7,0,0,0,7,0,0,0,0,0,0,0,0,7,0,0 | idle | build right |
| 7,-4,0,0,7,0,0,0,7,0,0,0,0,0,7,0,1,0,0,0 | left | idle |
| 7,-3,0,0,7,0,0,0,7,0,0,0,0,0,0,0,1,0,0,0 | left | idle |
| 7,-2,0,0,7,0,0,0,7,0,0,0,0,0,0,0,1,0,0,0 | left | idle |
| 7,4,0,7,7,0,0,0,7,0,0,0,0,0,7,0,2,0,0,0 | right | idle |
| 7,-4,0,0,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,0 | left | idle |
| 7,6,0,7,7,0,0,0,7,0,0,0,0,0,7,0,0,7,0,0 | right | idle |
| 7,6,0,7,7,0,0,0,7,0,0,0,0,0,7,0,2,0,0,0 | right | idle |
| 7,5,0,7,7,0,0,0,7,0,0,0,0,0,0,0,2,0,0,0 | right | idle |
| 7,-6,0,0,7,0,0,0,7,0,0,0,0,0,7,0,1,0,0,0 | left | idle |
| 7,-5,0,0,7,0,0,0,7,0,0,0,0,0,7,0,1,0,0,0 | left | idle |
| 7,-5,0,0,7,0,0,0,7,0,0,0,0,0,0,0,1,0,0,0 | left | jump left |
| 7,6,7,7,7,0,0,0,7,7,0,7,0,0,0,0,2,7,0,7 | jump right | build right |
| 7,5,7,7,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7 | jump right | build right |
| 7,4,6,7,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7 | jump right | build right |
| 7,3,5,7,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7 | jump right | build right |
| 7,1,4,7,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7 | build left | idle |
| 7,4,3,0,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,7 | build left | idle |
| 7,5,2,0,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,7 | right | idle |
| 7,4,2,7,7,0,0,0,7,0,0,0,0,0,7,0,2,0,0,7 | jump right | idle |
| 7,0,3,7,7,0,0,0,7,7,7,0,7,0,0,0,0,1,0,7 | up | idle |
| 7,0,1,7,0,0,7,0,0,7,7,0,7,7,0,0,3,0,0,7 | up | idle |
| 7,-7,7,7,7,0,0,0,7,0,0,0,0,0,7,0,0,7,0,7 | left | build right |
| 7,-7,7,0,7,0,0,0,7,0,0,0,0,0,7,0,1,0,0,7 | left | jump left |
| 7,-6,7,0,7,0,0,0,7,0,0,0,0,0,7,0,1,0,0,7 | left | jump left |
| 7,-6,7,0,7,0,0,0,7,0,0,0,0,0,0,0,1,0,0,7 | left | jump left |
| 7,-1,4,0,7,0,0,0,7,7,0,7,0,0,0,0,0,1,0,7 | build right | jump left |
| 7,-3,3,7,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,7 | build right | idle |
| 7,-4,2,7,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,7 | left | idle |
| 7,-4,2,0,7,0,0,0,7,0,0,0,0,0,7,0,1,0,0,7 | jump left | idle |
| 7,0,3,0,7,0,0,0,7,7,7,0,7,0,0,0,0,1,0,7 | up | idle |
| 7,0,1,0,0,0,7,0,0,7,7,0,7,7,0,0,3,0,0,7 | up | idle |
| 7,0,1,7,0,0,7,0,0,0,0,0,7,7,0,0,3,0,0,7 | up | idle |
| 7,1,3,0,7,0,0,0,7,0,0,0,7,0,7,0,0,1,0,7 | up | idle |
| 7,0,1,0,0,0,7,0,0,0,0,0,7,7,0,0,3,0,0,7 | up | idle |
| 7,-2,0,7,7,0,0,0,7,7,0,7,0,0,0,0,0,7,0,0 | left | jump right |
| 7,-3,2,0,7,0,0,0,7,0,0,0,0,0,7,0,0,2,0,0 | build left | idle |
| 7,-2,1,0,7,0,0,0,7,7,0,7,0,0,0,0,0,4,0,0 | jump left | jump right |
| 7,3,2,7,7,0,0,0,7,0,0,0,0,0,7,0,0,2,0,0 | build right | idle |
| 7,4,2,7,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,0 | build right | idle |

## Aliasing in the curriculum's lessons

525 lessons over all passes, 137 distinct states, 17 states with conflicting labels:
- `7,4,0,7,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,0`: idle x1, right x13
- `7,1,4,7,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7`: idle x1, left x6
- `7,2,4,0,7,0,0,0,7,0,0,0,0,0,7,0,0,1,0,7`: idle x2, build left x7
- `7,4,3,0,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,7`: idle x2, left x4
- `7,4,3,0,7,0,0,0,7,0,0,0,0,0,7,0,0,1,0,7`: idle x2, build left x5
- `7,4,2,7,7,0,0,0,7,0,0,0,0,0,7,0,2,0,0,7`: right x1, jump right x2
- `7,0,3,7,7,0,0,0,7,7,7,0,7,0,0,0,0,1,0,7`: idle x1, up x3
- `7,-4,6,0,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7`: idle x1, jump left x5
- `7,-3,3,7,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,7`: idle x2, right x14
- `7,-4,2,7,7,0,0,0,7,0,0,0,0,0,7,0,0,4,0,7`: idle x1, left x12
- `7,-4,2,0,7,0,0,0,7,0,0,0,0,0,7,0,1,0,0,7`: left x1, jump left x10
- `7,3,5,7,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7`: idle x2, jump right x1
- `7,-1,3,7,7,0,0,0,7,0,0,0,7,0,7,0,0,1,0,7`: idle x1, up x4
- `7,4,6,7,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7`: idle x1, jump right x4
- `7,-4,3,7,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7`: idle x1, build right x2
- `7,1,3,0,7,0,0,0,7,0,0,0,7,0,7,0,0,1,0,7`: idle x1, up x1
- `7,5,7,7,7,0,0,0,7,7,0,7,0,0,0,0,0,2,0,7`: idle x2, jump right x1

Oracle aliasing over the evaluation's 1358 distinct vectors: 43 vectors where the privileged oracle wants different actions.

---

# Interpretation, written after the run

The tables above this line are the script's. The pre-registration is `PREREG-CURRICULUM.md`
(commit 7dff84e); the shadow holdout is `../generalization/SHADOW.md` (commit 9256a27); the frozen
brain is commit 756ca7c, sha256 `02c5dc1fbb6c256b13318a5195f7b72e25a05051e0cc70c43001a8565f88f589`,
unchanged after every one of the 287 episodes, with zero lessons taken in any of them.

## The answer to the question

None of the failure disappeared through better experience alone. It got worse. Under the strict
rule the curriculum brain passes 1 of the 24 held-out regression scenarios and 2 of the 16 fresh
ones, and those three are the restraint scenarios where doing nothing is the right answer. The old
narrow brain, on the same runs, passes 11 and 4. The curriculum's own teacher, driven through the
override with the bytes the decoder would emit, passes 19 and 11: the corpus is solvable on these
senses with this vocabulary, including four of the five same-side ladder columns and both mirror
ladders by the two-brick route, walking on both sides, the floor brick both ways and Tony below him.
The ceiling for imitation is high; the perceptron under this rule did not get near it.

My pre-registered predictions were wrong in direction: I expected 15 to 19 of 24 and the mirror and
restraint buckets recovered. Only restraint recovered, and for the wrong reason.

## Why: the policy is not representable, and the rule then keeps the frequent label

Three measurements, none of which involves the corpus:

1. **Exact representability.** On the 231 distinct sense vectors the clone was in under teaching
   (identical in every pass, since the teacher drives), CBC finds no legal 4-bit 10 x 20 weight
   matrix that reproduces the teacher's labels under the program's tie-breaking (infeasible, 0.1 s;
   `representability-pass1.json`). Every episode's states are representable on their own; the
   conflicts are between episodes, and the one pair the solver could not settle in thirty seconds is
   the two wall-column climbs, E07 at the right wall and E08 at the left. The greedy scan in
   curriculum order names the states that had to be dropped for the rest to fit. The old teaching's
   17 consistent states were representable, which is why that brain existed.
2. **The rule's behaviour on an unrepresentable target.** The disagreement per pass settled at 4.3 to
   5.5% of ticks and never approached the 2% stop; the stop came from three passes without a
   decrease. Offline, the reference rule replayed over the 525 recorded lessons for 300 epochs peaks
   at 200 of 231 states and oscillates; fed the teacher's labels directly it peaks at 197, still
   taking thirty to fifty lessons every epoch. The frozen brain reproduces the teacher on 184 of 231
   states (79.7%), the best of the seven passes.
3. **Which states it gets right.** The teacher's labels over a pass are 90% idle (1,338 of 1,484
   decisions: the follow and restraint episodes end with long stretches of standing beside Tony) and
   the decisive actions are 1 to 3% each. The frozen brain agrees on 160 of the 164 idle-labelled
   states and on 15 of 22 "up", 2 of 15 "left", 0 of 9 "right", 2 of 7 "jump right", 5 of 7 "jump
   left" and 0 of 7 "build". The old brain, taught on a stream with no idle tails, got 22 of 22 "up"
   and 7 of 7 "jump right" and nothing else. With a target it cannot fit, the step-of-one rule settles
   where the frequent label wins and the rare decisive labels lose; the "idle" row of the new brain
   carries the largest weights in the matrix (bias 5, air 7, ladderBelow 6, wallAheadHead 5), and on
   the corpus he climbs the training stairs to the top brick and stands there.

So this is a model and rule limitation on this policy, established without appeal to the senses:
the teacher is a function of the senses, its labels are consistent, and no weight matrix of the
class reproduces them. The senses are not the binding constraint here (the teacher solves 30 of 40
scenarios from the same twenty senses), and the quantisation is not either (the infeasibility is over
the full legal range, and the curriculum brain's weights reach 7 and -7 without saturating a
decision). Task construction contributed one thing: the label imbalance. A curriculum with the idle
tails cut would change which states the rule sacrifices, but not the infeasibility.

## Aliasing, reported separately

- **In the lessons**: 17 of the 137 distinct lesson states carry conflicting labels. Every one is
  "idle once or twice, the decisive action many times": the machine's tick and the teacher's press
  are one tick out of phase, so the state before a press is taught idle at the tick that precedes it
  and the action at the edge that follows. A timing effect of the teacher's reaction lag, as before,
  not the senses; the majority label wins but each recurrence costs a lesson.
- **Against the privileged oracle**: 43 of the 1,358 distinct vectors met in the evaluation. The
  larger corpus met more of the one-frame publish lag (in the air, just landed) and the states the
  oracle reads from the map beyond the one cell the senses see.
- **The residual**: not aliasing; see above. Among the 47 disagreements, 40 are the brain answering
  idle where the teacher acts.

## What the teacher's own failures say about the corpus

The teacher fails B2 and the two-high wall (a jump onto a lone top brick or a stack overshoots it;
the two middle-brick shadow scenarios fail for every arm for the same reason), B3 (it waits at the
top brick's height rather than on it), E2 and H09 (from the far side of a rightward staircase it
builds instead of walking under), F_ladder_C29 and H10, and H13. None of those is a learning
question; they are the vocabulary's missing step-up and the policy's fixed rules.

## Not done, as instructed

No change to the senses, the network, the rule, the quantisation, the decoder or the PRG. The result
argues for the architecture step the owner deferred: the two-brick route, the restraint conditions
and both directions together are more than a single linear layer over these senses can hold, and a
learning rule that does not weight rare decisive labels will lose them to the idle majority whatever
the curriculum. The teacher through the override is the useful artefact of this round: a policy on
these senses that solves most of both corpora, and the standard any later brain should be measured
against.
