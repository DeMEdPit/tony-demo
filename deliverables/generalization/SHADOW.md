# The shadow holdout

Sixteen fresh scenarios for the curriculum experiment, written after the curriculum, the teacher and
the stopping rule were committed (7dff84e) and before any training pass, in their own commit. Nothing
in training reads them. They differ from the old corpus and from the curriculum in start, geometry or
timing: a middle brick with nothing to stop the last jump, a lone brick, a two-wide platform, the far
walls as starts, Tony below the clone, Tony climbing during the episode, Tony walking away or
ducking, an open column with Tony low on the ladder, the left-wall ladder with Tony high on it. The
strict rule applies: a near goal counts only in a grounded or ladder state. Same integrity checks as
the old corpus. The start state of every scenario was checked with no arm installed
(`python3 tools/generalization_test.py check-shadow`) before this commit.

| id | bucket | ladder | success | limit | what it is |
|---|---|---|---|---|---|
| H01_tony_on_third_brick_C29 | middle_brick | 29 | within 20/12 px of Tony, grounded or on a ladder | 480 | three bricks only at column 29, Tony standing on the third; the goal is beside him on it (the last jump has nothing to stop it) |
| H02_step2_facing_away | same_side_variant | 33 | on the ladder within 16/16 px of Tony | 480 | driven onto the second brick and turned away from the stairs before t0 |
| H03_far_left_150px | walk_required | 33 | on the ladder within 16/16 px of Tony | 700 | the clone parked at X 66 while Tony builds and climbs: a hundred and fifty pixels of floor first |
| H04_two_wide_platform | obstacle | 33 | within 24/12 px of Tony, grounded or on a ladder | 500 | two bricks side by side on the floor, a 32-px platform; Tony crossed it and stands beyond |
| H05_mirror_far_right_C9 | mirror | 9 | on the ladder within 16/16 px of Tony | 800 | the mirror ladder at column 9 with the clone parked at the far right wall: the long walk left, the climb left, the route |
| H06_restraint_left_wall | restraint | 33 | stays on the floor within 80 px of Tony, every poll | 300 | Tony walks to the left wall; the clone follows and must stand beside him there |
| H07_tony_below_clone_on_step3 | tony_below | 33 | within 24/12 px of Tony, grounded or on a ladder | 500 | four bricks; the clone driven onto the third, then Tony walks back down off the fourth to the floor: he must come down to him |
| H08_stack_from_right_far | obstacle | 33 | within 20/12 px of Tony, grounded or on a ladder | 500 | Tony on a two-brick stack, the clone far to its right facing back: walk, a step, and the jump onto the stack beside him |
| H09_ladder_C21_from_far_right | mirror | 21 | on the ladder within 16/16 px of Tony | 900 | the ladder at column 21, stairs rising rightward, the clone parked at the right wall: under the floating stairs, over the first brick, back up them, the route |
| H10_tony_climbs_while_mid_stairs | timing | 33 | on the ladder within 16/16 px of Tony | 600 | the clone driven onto the second brick; Tony waits on the fifth and climbs the ladder 60 frames after t0 |
| H11_tony_walks_away | restraint | 33 | stays on the floor within 80 px of Tony, every poll | 400 | nothing built, the two side by side; Tony walks 80 px right after 80 frames: the clone must follow to stay within 80 px |
| H12_tony_ducks | restraint | 33 | stays on the floor within 80 px of Tony, every poll | 300 | Tony ducks beside him for the whole window (a sense value never seen: playerDuck) |
| H13_tony_on_single_brick | middle_brick | 33 | within 20/12 px of Tony, grounded or on a ladder | 480 | Tony lays one brick and stands on it; the goal is beside him on the brick (a jump onto a lone brick has nothing to stop it) |
| H14_C5_far_start_tony_high | ladder_mirror | 5 | on the ladder within 16/16 px of Tony | 900 | the left-wall ladder with the clone parked at the far right and Tony ten frames higher on the ladder |
| H15_C27_tony_low | ladder_same_side | 27 | on the ladder within 16/16 px of Tony | 600 | an open column with Tony only twenty frames up the ladder (Y 102): the route's dy thresholds are shifted |
| H16_clone_on_top_tony_on_floor | tony_below | 33 | within 24/12 px of Tony, grounded or on a ladder | 600 | four bricks; the clone driven onto the top one, then Tony walks back down to the floor: he must come all the way down |
