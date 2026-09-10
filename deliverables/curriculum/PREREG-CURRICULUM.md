# Pre-registration: the diverse-experience experiment

Written and committed before any training pass. The question, in the owner's words: how much of
the current failure disappears through better experience alone? The perceptron, the twenty senses,
the 4-bit weights, the learning rule, the decoder and the PRG are the ones of commit 5116a2d and are
not touched. Only the teaching changes: a diverse, fixed curriculum, a sense-only teacher, one-frame
presses, and a stopping rule fixed here.

## What was learned in the design phase (feasibility, no training involved)

All on the stamped column-31 and column-9 PRGs, through the override, no brain involved:

- A one-frame press through the port under teaching launches the jump on that frame (the lesson pairs
  the state before it with the jump, and the release pairs the first air frame with idle).
- A vertical jump from the fourth brick never brings the ladder's columns into his box (he is one slot
  left of them); "up" pressed in the air while the ladder is in the box during a jump right does not
  grab it (the physics ignore the stick in the air); the air cannot be steered.
- A running jump carries 48 px and rises 20; a brick is 16 px wide. A jump from the fourth brick, or
  from one brick built beside it, overshoots the fifth brick unless a wall stops it.
- Standing half over the edge of a built brick and jumping lands on the fifth brick by one pixel, and
  the senses do not distinguish the edge from the middle of the brick, so that route is not teachable.
- **The two-brick route works on both sides**: from the fourth brick, build a brick away from Tony
  and step onto it (one level up, one slot back), build again and step (two up, two back), turn, jump:
  the 48-px jump lands on the fifth brick, and "up" takes the ladder. So the top step at an open
  column is reachable within the vocabulary: a geometry and action-interface difficulty, not an
  impossibility. It is teachable only through Tony's height above him (dy), since nothing else in the
  senses says "this is the last step".
- A jump from a built step onto a two-brick stack overshoots the stack the same way; no route onto a
  stack was found short of three bricks, and the stack episodes below are cut to the build lesson.

## The teacher

A function of the twenty published senses and nothing else, returning one of the ten actions. It is
the file's `teacher` in `tools/curriculum.py`, reproduced here verbatim:

```python
def teacher(s):
    """The curriculum's policy: a function of the twenty senses only (signed, as published), returning
    one of the ten actions. Written once, before training; see PREREG-CURRICULUM.md for the rules."""
    dx, dy, fac, grd, air, lad, duck, flr, wF, wH, brk, lH, lB, bld, pA, last, still, pD, pL = s[1:20]
    if air: return IDLE                                            # in the air nothing acts
    if lad: return UP if dy > 0 else (DOWN if dy < 0 else IDLE)    # on a ladder: after him
    if lH and dy > 0: return UP                                    # a ladder in the box and he is above: climb
    toward = RIGHT if dx > 0 else LEFT if dx < 0 else (RIGHT if fac else LEFT)
    away = LEFT if toward == RIGHT else RIGHT
    ft = (fac != 0) == (toward == RIGHT)                           # facing his way
    adx = abs(dx)
    if dy <= 1:                                                    # level with him, or he is below: follow
        if adx <= 1: return IDLE                                   # beside him: nothing (restraint)
        if ft and wF and not wH: return JUMP + toward              # a brick in the way: jump it
        if ft and wF and wH: return IDLE                           # a wall: nothing to do
        return toward                                              # walk his way (a turn first if needed)
    if not ft:                                                     # two or more bricks below him, facing away
        if dy == 3 and bld and not wF: return BUILDL + (away - 1)  # the route's second brick
        return toward                                              # turn his way
    if wF and not wH:                                              # a step ahead
        if dy >= 5: return JUMP + toward                           # a middle step: the next brick stops the jump
        return BUILDL + (away - 1)                                 # near the top: the route's first brick, away from him
    if wF and wH: return (BUILDL + (toward - 1)) if bld else IDLE  # a two-high wall: a step in front of it, or nothing
    if dy == 2 and adx >= 4 and last == toward: return JUMP + toward   # the route's end: onto the top brick
    if adx >= 5: return toward                                     # far: walk
    return (BUILDL + (toward - 1)) if bld else toward              # near and below with nothing ahead: build up his way
```

Two admissions, recorded in advance. (1) The route's end (on the second built brick, turned toward
Tony, nothing ahead, two bricks below him, 32 to 48 px away) and the foot of a two-brick stack with an
empty slot before it look the same to the senses except for the last action; the teacher jumps in the
first and builds in the second on that one sense, and the perceptron may not follow. (2) The route's
trigger is dy, so Tony's height on the ladder changes where it fires; the old corpus's B8 and B9 will
show what that costs.

Presses: jumps and the lay and step-up chords are one frame; directions and up/down are held for the
tick (4 frames); a build is turn, lay, step, 32 frames in all. The teacher decides every 4 frames from
the published block, as the brain thinks.

## The curriculum

Fifteen episodes in this fixed order, each a scripted setup (Tony's stick and, to place the clone, the
override, as in the generalization corpus) followed by teaching for the frames given, the clone driven
by the teacher through the port with `teachMode` on. Every pass repeats the list unchanged. Because
the teacher drives, the trajectory of every episode is identical in every pass; only which lessons are
taken changes, so a pass's lesson count is the brain's disagreement with its teacher on a fixed
stream.

| episode | ladder column | frames | what it teaches |
|---|---|---|---|
| E01_follow_right | 33 | 300 | nothing built; Tony walks 60 px right and stops; the clone walks after him and stops beside him |
| E02_follow_left | 33 | 300 | Tony walks 80 px left, past the clone; the clone turns, walks left and stops beside him |
| E03_follow_far_right | 33 | 400 | Tony walks 100 px right, to the pillar side; a long walk |
| E04_follow_far_left | 33 | 400 | Tony walks 110 px left; a long walk the other way |
| E05_brick_right | 33 | 400 | Tony lays a brick, crosses it and stands beyond; the clone (parked at 146) walks, jumps the brick, stops beside him |
| E06_brick_left | 33 | 400 | the mirror: the clone parked at 246; Tony lays a brick leftward, crosses it, stands beyond on the left |
| E07_stairs_C33_ladder | 33 | 700 | the old training start: five bricks under the ladder at column 33, Tony on the ladder; the clone followed to the foot |
| E08_stairs_C5_ladder | 5 | 800 | the mirror at the left wall: leftward stairs under the ladder at column 5; the clone walks from 226 and climbs |
| E09_stairs_C27_ladder | 27 | 800 | an open column on the training side: the top step needs the two-brick route |
| E10_stairs_C9_ladder | 9 | 900 | an open column on the mirror side: walk left, climb left, the route, the ladder |
| E11_restraint_stairs | 33 | 300 | four bricks stand; Tony walked back to the floor beside the clone: nothing to do |
| E12_restraint_wall | 33 | 400 | Tony walks to the right wall; the clone follows and stands beside him at the wall |
| E13_stack_from_right | 33 | 48 | Tony on a two-brick stack; the clone beyond it on the right, facing back at it with an empty slot before it: build a step toward him (the lesson), then the jump; the episode ends there, because a jump onto a two-high stack overshoots it and the teacher would loop |
| E14_stack_from_left | 33 | 48 | the mirror: Tony stacks two bricks leftward; the clone on the left with an empty slot before the stack: build a step toward him, then the jump; cut short the same way |
| E15_two_high | 33 | 48 | the old corpus's two-high wall: Tony on the stack, the clone facing the lifted slot before it: build a step toward him, then the jump; cut short the same way |

The stack episodes (E13 to E15) are 48 frames on purpose: the build lesson and the jump, before the
overshoot loop that would follow.

## The stopping rule

Passes continue until the first of: a pass takes lessons on at most 2% of its ticks; three consecutive
passes without a decrease in lessons taken; twenty-five passes. The rule reads only the training
passes. The weights after every pass and every pass's recorded lessons are kept. The brain at the stop
is frozen as `deliverables/curriculum/taught-curriculum.bin` with its sha256, and a row-permuted copy
(the same seed as before) is made as the control. The old teaching (36 lessons, 4 sessions) is the
comparison point for lessons-to-stop.

## Evaluation

Two corpora, separately reported:

1. **The old corpus, as a regression set.** `deliverables/generalization/scenarios.json` unchanged,
   its results now known to have informed this curriculum. Strict rule for every arm: a near goal
   counts only in a grounded or ladder state.
2. **A shadow holdout**, twelve to twenty fresh valid scenarios written after this commit and before
   any training pass, in its own commit, not used by anything in training.

Seven arms on both: the curriculum brain; the old frozen brain (`taught-climb.bin`); the teacher
itself, driven through the override with the same bytes the decoder would emit, as the imitation
ceiling; the builder (kind 2); the follow rule (kind 0); the zero brain; the curriculum brain with its
rows permuted. Same integrity checks as before: the weights dumped after every episode and compared,
the lesson counter at zero, the brain files' hashes before and after.

## Aliasing and representability, reported separately

- **Label aliasing** in the curriculum's recorded lessons: the same senses taught different actions,
  over all passes.
- **Oracle aliasing** on the evaluation's encountered vectors, as before.
- **The residual**: the frozen brain's action against the teacher's on every distinct sense vector
  visited under teaching. Because the teacher is a function of the senses, a residual is not aliasing;
  it is either the rule not having found a solution or the model class not having one.
- **Exact representability** (`tools/representability.py`): with CBC, whether any legal 4-bit
  10 x 20 weight matrix reproduces the teacher's labels on the visited vectors under the program's own
  tie-breaking. "A solution exists but the rule did not find it" and "no representable solution" are
  reported as different findings. The checker was validated on the old teaching's lessons (17
  consistent states: representable, as the frozen brain's existence already implied).
- **The offline fit**: the Python reference rule over the recorded lessons with unlimited passes, as a
  third datum, not as proof of anything.

## Predictions

- Lessons to stop: more than the old 36, likely between 150 and 400, in six to fifteen passes.
- The residual against the teacher: not zero. The route's rules and the restraint rules share features
  with the walking rules, and a step-of-one perceptron will keep arguing on a few states; my guess is
  90 to 97% agreement on the visited vectors, with the disagreements around the route's end and the
  "near and below" build.
- Representability: feasible for the walking, jumping, restraint and ladder states together; whether
  the route's states fit with them is the open question, and I expect CBC to say infeasible once the
  route's end and the stack's foot are both in the set.
- The old corpus, strict: the curriculum brain above the old brain's 11 of 24, with the mirror bucket
  and the restraint bucket largely recovered and the same-side ladder columns depending entirely on
  whether the route survived learning; something like 15 to 19 of 24, the teacher itself around 18 to
  21 (it fails B2 and the two-high wall by its own rules).
- The shadow holdout: the curriculum brain below the teacher by a few scenarios, both well above the
  old brain.

## How to run

```
python3 tools/curriculum.py check                   # every episode's start, no teaching
python3 tools/curriculum.py train                   # the passes, the log, the frozen brain
python3 tools/generalization_test.py run2           # both corpora, seven arms, RESULTS2.md
python3 tools/representability.py deliverables/curriculum/decisions-*.json
```
