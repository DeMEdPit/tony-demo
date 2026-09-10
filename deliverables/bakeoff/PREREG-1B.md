# Pre-registration: the architecture bake-off, phases 1b and 2b

Written and committed before Phase 1b or Phase 2b ran. Design input: the session of record's second
architecture review of 2026-09-10 (`chamberv2architecturereview2.md`, written against this branch at
`2ae24ae`), with the owner's four requirements and the reference-relative refinement, all pinned
below. The review's probe scripts (its own `tools/chamber-v2/`) are not in this repository and are not
the reference: the review's numbers are claims to reproduce, and the engine's exact bounded
implementation (`tools/bakeoff2.py`, parity-checked against `tools/brain_golden.py`) is what decides.

Scope: offline only. Nothing in the PRG changes; BRAIN02 is not implemented; the sealed goal senses
and the goal holdout are untouched (`GOAL-SENSES.md` sha256 `54694f90…128a4`, `goal-holdout.json`
`45f61f78…ebe40`, read by nothing here). No convergence theorem and no historical framing is an
acceptance criterion: behaviour of the exact bounded multiclass rule is established first, and the
sealed behavioural holdouts (Phase 4, later) decide usefulness.

## Held fixed

The twenty raw senses as published; the curriculum teacher of `../curriculum/PREREG-CURRICULUM.md`
as the labeller; the strict scoring rule; the symmetric step-of-one rule (mood-free prediction, a
lesson when the prediction differs from the taught action, the taught row up and the predicted row
down by the sign of each input, saturating at the box), the first-largest tie rule (ties to the
lowest index), zero initial weights. The frozen data: the 231 distinct teacher states and the
1,484-tick stream of one curriculum pass (`../curriculum/decisions-*.json`, concatenated sha256
`d682345f…5793`), and the 1,358 vectors met in the curriculum evaluation
(`../curriculum/encountered2.json`, sha256 `dbc1f948…7050`), labelled by the teacher.

New against phases 1 and 2, as parameters: the weight box (4 bits: -8..7; 6 bits: -32..31; 8 bits:
-128..127), binary retinas (every input a flag, 0 or 1 in the readout), and the action vocabulary
(absolute as today, or reference-relative as defined next).

## 1. The reference-relative vocabulary V, pinned

**The reference vector.** The relative vocabulary is defined from an explicit signed reference vector
`r = (rx, ry)` supplied to the decoder and to the teaching translation by the sensed state. The decoder
never decides what the reference is (Tony, a ladder, an exit, another goal): target selection belongs
to the sensed state and the interface. For the present curriculum the reference is Tony's offset,
senses 1 and 2 of the same block (`dx`, `dy`), and nothing else is available; a future goal sense
(`routeDx`, `ladderDx` of `GOAL-SENSES.md`) would supply `r` without any change to the decoder.

**The horizontal sign h** resolves `toward` and `away`:

- `rx > 0`: `h = +1`, toward is right;
- `rx < 0`: `h = -1`, toward is left;
- `rx == 0` (the reference directly above or below): `h` is the clone's current facing in the same
  block, sense 3 `facingRight`: `+1` if set, else `-1`.

This is the deterministic fallback the review's probe used and the curriculum teacher's own `toward`
rule (`RIGHT if dx > 0 else LEFT if dx < 0 else (RIGHT if fac else LEFT)`). One concrete inconsistency
was looked for and not found: for each `h` the map between absolute and relative actions is a
bijection, so relabelling a state is invertible (`tools/bakeoff2.py check` verifies the round trip
for every action and both signs, and that every labelled state maps back to its absolute label). 88
of the 231 states, 129 of the 474 and 216 of the 1,424 have `dx == 0`, so the fallback is exercised.

**The actions.** Ten, indices kept:

| index | absolute (today) | relative (V) | translation, given h |
|---:|---|---|---|
| 0 | idle | idle | unchanged |
| 1 | left | toward | left is toward when h = -1, away when h = +1 |
| 2 | right | away | right is toward when h = +1, away when h = -1 |
| 3 | up | up | unchanged |
| 4 | down | down | unchanged |
| 5 | jump | jump | unchanged |
| 6 | jump left | jump toward | as 1 |
| 7 | jump right | jump away | as 2 |
| 8 | build left | build toward | as 1 |
| 9 | build right | build away | as 2 |

**The decoder's resolution** (relative to absolute): `toward` is right when `h = +1`, left when
`h = -1`; `away` the other way; the same for the jump and build pairs. **A human's press** (absolute
to relative, the taught action of a lesson): the applied action of the frame, as sense 16 computes it
today from the joystick byte (a lay or step-up bit is a build the way he faces; fire with left or
right a directional jump; else the direction, up, down, or idle), is translated with the `h` of the
block the lesson carries (senses 1 and 3 of that block), including when the reference is directly
above or below. Both sides use the same block and the same rule, so the eleven-byte lesson stays
reconstructible: it keeps the absolute applied action, and the relative taught action is derived
identically at replay. The `lastAction` input of the retina stays the absolute nibble (as the block
publishes it); R1b's two relative facts are derived from it and `h`.

In this phase V is applied as a relabelling of the teacher's labels (and of the evaluation vectors'
teacher labels) by exactly this rule, nothing else changed.

## 2. The retinas (the contract for Phase 3's byte-for-byte check)

Every flag is a fixed function of the twenty raw senses as the 6502 publishes them. In the readout a
flag is 1 (the block's 7 would scale every accumulator by 7 and change nothing in the rule, whose step
is the sign; the 6502 of Phase 3 adds weights, no multiply). The mixed controls keep the published
values, as in phases 1 and 2. The reference is `tools/bakeoff2.py`, reproduced here:

```python
RAW_FLAGS = (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19)      # the fifteen raw flags
def fl(v): return 1 if v else 0
def r_bias(x): return [1]
def r_rawflags(x): return [fl(x[i]) for i in RAW_FLAGS]
def r_dxs(x): return [fl(x[1] > 0), fl(x[1] < 0)]
def r_adxt(x): return [fl(abs(x[1]) >= k) for k in range(1, 8)]
def r_dyup(x): return [fl(x[2] >= k) for k in range(1, 8)]
def r_dydown(x): return [fl(x[2] <= -k) for k in range(1, 8)]
def r_stillt(x): return [fl(x[17] >= k) for k in range(1, 8)]
def r_last(x): r = x[16] & 15; return [fl(r == k) for k in range(10)]
def bin56(x): return r_bias(x) + r_rawflags(x) + r_dxs(x) + r_adxt(x) + r_dyup(x) + r_dydown(x) + r_stillt(x) + r_last(x)
def six(x):
    """the six named second-order facts of the review's section 5, as the engine reads the names"""
    h = href(x); facing = 1 if x[3] else -1
    facingPlayer = facing == h                                   # facing the reference's way (h itself when rx == 0)
    stepAhead = x[9] and not x[10]                               # a one-high step ahead
    wallAhead = x[9] and x[10]                                   # a two-high wall ahead
    ladderHereAndHeAbove = x[12] and x[2] > 0
    facingAStep = facingPlayer and stepAhead
    buildableAndClear = x[14] and not x[9]
    return [fl(v) for v in (facingPlayer, stepAhead, wallAhead, ladderHereAndHeAbove, facingAStep, buildableAndClear)]
def lastrel(x):
    """the last action's horizontal direction against h: toward the reference, away from it"""
    h = href(x); d = HDIR.get(x[16] & 15, 0)                     # HDIR: left/jump left/build left -1, right/jump right/build right +1
    return [fl(d == h), fl(d == -h)]
SIT_IDX = (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19)          # the raw flags without facing
def order2(x):
    """the order-2 layer: every conjunction of a direction flag (dx sign, facing, last one-hot: 13) with
    a situation flag (the fourteen raw flags other than facing, dy up thermometer: 21): 273 units"""
    d = r_dxs(x) + [fl(x[3])] + r_last(x)
    s = [fl(x[i]) for i in SIT_IDX] + r_dyup(x)
    return [a & b for a in d for b in s]
```

The last action: sense 16 holds the action index 0..9 in the low nibble and the reference sign-extends
it, so 8 and 9 arrive as -8 and -7; the category is the raw nibble (`value & 15`), nibbles 10..15
(never produced) set no flag. The six named facts are the engine's reading of the review's names
(the review's definitions are not in this repository); they are stated here so that a disagreement
with the review's numbers can be traced to a definition.

| arm | inputs | binary | what it is |
|---|---:|---|---|
| `raw20` | 20 | no | control: the twenty senses as published (mixed) |
| `T36` | 36 | no | control: raw plus dy-up thermometer, dx sign, \|dx\| thermometer (Phase 1's `T_dyup+dxs+adxt`) |
| `A2` | 55 | no | control: raw plus one-hot dy, one-hot last, one-hot \|dx\|, dx sign (Phase 1's `A2`) |
| `R0` | 56 | yes | BIN: bias 1, the fifteen raw flags, dx sign 2, \|dx\| thermometer 7, dy up 7, dy down 7, still 7, last one-hot 10 |
| `R1` | 62 | yes | R0 plus facingPlayer, stepAhead, wallAhead, ladderHereAndHeAbove, facingAStep, buildableAndClear |
| `R1b` | 64 | yes | R1 plus lastActionTowardPlayer, lastActionAwayFromPlayer |
| `R2` | 337 | yes | R1b plus the order-2 layer, 13 direction flags by 21 situation flags = 273 conjunctions |

Every arm runs under both vocabularies (absolute, V).

## 3. The sets, kept separate

- **the 231**: the distinct states visited under teaching in the curriculum's first pass, with the
  teacher's labels;
- **the teacher-visited union, 474**: the 231 plus the evaluation vectors met by the *teacher arm* of
  `RESULTS2` (arm `teacher` in `encountered2.json`), labelled by the teacher. The primary
  representability diagnostic: a policy must be right where the teacher itself goes;
- **the full union, 1,424**: the 231 plus every evaluation vector of every arm, labelled by the
  teacher. Adversarial coverage, reported but never the sole definition of intelligence: 950 of these
  states were reached only by failing policies.

Every state keeps its identity (episode and frame, or scenario, arm and offset, with both actors'
positions) so that an unfit state can be named. Under V each set is relabelled by section 1.

## 4. Phase 1b: exact representability as a maximum feasible subset (CP-SAT)

For each arm, vocabulary and set, the question "does any legal `10 x n` integer matrix in the box
reproduce every label under the tie rule" is solved as a **maximum feasible subset**: one Boolean per
state, that state's nine constraints (for every `o != t`: `sum_i (w[t][i] - w[o][i]) z_i >= 1` if
`o < t`, `>= 0` if `o > t`) enforced only when its Boolean holds, the count of fitted states
maximised. CP-SAT (OR-Tools 9.15), 300 s, four workers. The result is exact when the status is
OPTIMAL: an optimum equal to the set size is feasibility; anything less is the **minimum number of
unfit states**, and the unfit states are listed by name (identity and sense vector). On a time limit
the incumbent and the bound are reported as a range, never as a proof. Every solution is replayed
through the exact forward pass (`forward_ref`) as a check on the solver: the fitted states must all
be reproduced and the replay's misses must be the listed unfit states. A minimum unfit set need not
be unique; the set reported is the one found, and for the absolute-vocabulary teacher-visited union
of every binary arm the alternatives are probed by re-solving with each named state forced to fit.

Boxes: 8 bits for every arm, vocabulary and set; 4 bits as well for the binary arms on the 231 and
the 474 (the review reports 4-bit rows). For every feasible case at 8 bits, the **largest margin**: the
integer `m` maximised subject to every gap being at least `m` plus the tie term, 300 s, the incumbent
reported as a lower bound when the solver stops on time. Cross-check: the 231 at 8 bits also through
CBC (Phase 1's tool with the box as a parameter), 120 s, feasibility only. The three union cases Phase
1 left undecided at 4 bits (`T_dyup+dxs+last+adxt`, `T_dyup+dydown+dxs+last+adxt`, `A2`) are settled
the same way, at 4 and at 8 bits, absolute vocabulary.

**The comparison the owner asked for.** The review found, with the 8-bit rule as an upper bound, two
unfit teacher-visited states for BIN under the absolute vocabulary, both build-direction cases: "the
route's first brick (build away from Tony, standing on the stairs facing him with a step ahead)
against the stack's foot (build toward him, on the floor with a buildable slot ahead), on both
sides". The exact minimum here is compared with that: the same count and the same kinds of state
strengthen the diagnosis; a different count or different states is a result in itself, to be traced
(the flag scale, the `h` fallback, a fact's definition, the exact minimum against a rule-based bound)
before anything else proceeds.

## 5. Phase 2b: learnability by the exact rule, from zero

The rule of section 0 held fixed, the box a parameter, symmetric update only (the single-row update
is falsified by the review and not run), zero initial weights, 300 passes, every arm, both
vocabularies, boxes 4, 6 and 8 bits, on four streams:

- **S1, the tick stream**: the 1,484 labelled states of one curriculum pass, in order, the rule
  deciding which become lessons;
- **S2, the labels cycled**: the 231 unique states with their labels, in first-visit order;
- **S4, a noisy human**: S1 with each tick's label replaced, independently with probability 0.05, by
  one of the nine other actions drawn uniformly; the draw is fresh on every pass from one generator
  seeded 0 at the start of the run (a human's slips do not repeat on the same state);
- **S5, a lagging human**: S1 with every label delayed one tick within its episode, the state at tick
  k paired with the teacher's label for tick k-1 and the first tick of every episode paired with idle
  (the stick centred before the first press); this is the one-tick phase offset the curriculum
  experiment measured between the machine's tick and the teacher's press.

Agreement is always measured against the clean teacher labels of the 231 (relabelled under V), and,
after every pass, on the teacher-visited union of 474. Recorded per run: the lessons to the first
pass at full agreement on the 231, the passes held at full agreement out of 300, the final and best
agreement, the count of saturating clamps, the largest weight magnitude at the end and over the run,
the lessons per pass over the last ten passes (on S4 also the lessons taken on corrupted ticks), the
agreement curves on the 231 and the 474, and the final weights' hash.

**Survivor rule, fixed now.** An arm at a box survives if, on S1, it first reproduces the teacher on
all 231 states within 500 lessons and then holds full agreement for at least 80% of the remaining
passes; and on S4 and S5 its best agreement is within five states of its clean S1 run. Under V the
same rule applies to the 231, and the 474 agreement is reported beside it (the review's claim: 474
of 474 within 900 lessons, held).

## 6. Parity of the widened-box rule, before any 6- or 8-bit result is trusted

`tools/bakeoff2.py parity`, results in `parity-1b.json`:

1. the reference rule generalised to n inputs and a box (`learn_ref`) against the golden reference
   itself (`brain_golden.learn`, unchanged, box -8..7, twenty inputs), weight for weight and lesson for
   lesson over twenty passes of the labels (the check Phase 2 ran, repeated);
2. the vectorised learner (`learn_stream`, what Phase 2b runs) against `learn_ref` after **every
   lesson** over passes of S1, at 4, 6 and 8 bits, on binary and mixed arms (raw20/4, R0/8, R0 under
   V/6, R2 under V/8, A2/8, R1b/4): identical weights or the run is not trusted;
3. golden edge cases for a byte-weight implementation, written as vectors for Phase 3
   (`golden-1b/forward-v2.json`, `golden-1b/lessons-v2.json`): the all-zero tie, the most positive and
   most negative accumulators at the selected maximum input count, positive and negative exact ties
   between rows (the first largest wins), a weight of -128 against -127, saturation at 127 and at -128
   with the wrap cases (127 + 1 stays 127, -128 - 1 stays -128), the same at the 6-bit box, the mood
   term against a weight, no-op lessons, and seeded random cases at 56, 62, 64 and 128 inputs.

**The accumulator bound, recomputed and asserted.** With every input a flag of 1, byte weights and the
mood term as today (`m * 16`, `m` in -8..7): `|acc| <= n * 128 + 128`. The selected maximum input count
is **128** (the review's header limit): the bound is 16,512, inside 16 bits with room; the positive
extreme is 128 * 127 + 112 = 16,368 and the negative -16,512. The 16-bit limit would be reached at 255
inputs (bound 32,768, the negative extreme exactly -32,768) with no slack; the order-2 arm at 337
inputs exceeds it (bound 43,264) and the header's one-byte input count, so R2 can only be an offline
ceiling in this form. The assertion is in the code and its outcome in `parity-1b.json`.

## 7. The exact BRAIN02 byte budget (method; the table is a deliverable, nothing is built)

For each surviving architecture, exactly: the marker (8), the header (8: kind, layout, inputs,
hidden, outputs, period, lineage, rule), the weights (10 rows of n signed bytes), the mood if
retained (8 as today; its scale against unit flags is a Phase 3 question, noted, not decided), the
retina table if table-driven (3 bytes per threshold flag: sense, comparison, threshold; 4 per
conjunction of two flags; 2 per order-2 pair) or the retina as code, the page alignment (the slot is
found by its marker at a page boundary), the maximum input count the slot supports at that size, the
spare capacity, the teaching shadow (a full copy of the weights, today 256 bytes at `TEACH_SHADOW`),
the lesson block (500 lessons at 11 bytes plus 16, 5,516 bytes), and where all of it sits in this
build's map (code to `$863e`, the run-time free region `$863f`-`$9fff` that the level tune vacates,
6,593 bytes, holding the shadow and the lesson block). The slot's arithmetic is exact; the code the
retina needs is an estimate and labelled as one. No assumption is made that a slot of about 1 KB
holds 128 byte-weight inputs: 16 + 10 * 128 + 8 = 1,304 bytes before any table.

## 8. Predictions, written before the run

The engine's, beside the review's (section 7 of the review; scored afterwards):

- **Phase 1b, absolute vocabulary.** `raw20` infeasible on the 231 at 8 bits as at 4 (the failure is
  separability, not the box); `T36` and `A2` feasible at 8 bits with larger margins than at 4. `R0`
  feasible on the 231 at 8 and at 4 bits; on the 474 the exact minimum unfit count is 1 or 2 (the
  review's rule-based bound is 2) and the named states are build-direction states of the two kinds
  the review describes; on the 1,424 the minimum is at least 5. `R1` and `R1b` change the 474 count
  little or not at all (the named facts do not carry the sign of dx into the build rows), against the
  review's "fewer than fifteen", which both would also satisfy. `R2` fits the 474 (0 unfit): the
  direction-by-situation conjunctions carry exactly the exclusive-or the build direction needs; on the
  1,424 it is still infeasible.
- **Phase 1b, V.** `R0` feasible on the 231 and on the 474 at 8 bits, and on both at 4 bits; on the
  1,424 infeasible with a minimum unfit count under ten. The three undecided Phase 1 union cases:
  infeasible at 4 bits, and at 8 bits.
- **Phase 2b.** `R0` absolute at 8 bits on S1: full agreement on the 231 within 500 lessons, held for
  more than 80% of the remaining passes; at 6 bits the same; at 4 bits it fails as in Phase 2 (the
  review's box result reproduces, because the rule is the same rule). `R0` under V at 8 bits: the 231
  within 300 lessons and the 474 reached within 900 lessons on S1, held. The mixed controls at 8 bits:
  `T36` and `A2` end at the four-lesson cycle with zero clamps (the review's cause one); `raw20` never
  fits. `R2` converges at 8 bits on S1 more slowly than `R0` (more active inputs per lesson). S4 costs
  flapping of under ten clean-tick lessons per pass beyond the corrupted ticks themselves and no loss
  of the best fit; S5 costs more than S4 and may not reach the fit on the absolute vocabulary.

**Falsifiers.** If `R0` at 8 bits does not converge here where it converged in the review, the
implementation or the reference differs and that is the finding to run down first (the flag scale, the
tie rule, the stream). If the 474 residual under the absolute vocabulary is not the review's two
build-direction states, the disagreement is investigated before Phase 2b is read. If `R1b` is no better
than `R0` on the 474, the named facts are the wrong facts, and `R2` says whether any first-order-plus-
pairs retina can hold this teacher. If V's 474 fit does not learn, the review's strongest claim fails
on the engine's machine.

## What comes after, not here

Phase 3 and 4 are pre-registered separately, after these results are returned and read: BRAIN02
behind the same test hooks with the golden-1b vectors byte for byte, cycles, RAM, the raster bench,
then behaviour on the old corpus, the shadow holdout and, with the goal senses built as flags and
LESSON2, the sealed goal holdout. Decision rule as before: within two of the teacher on the sealed
holdouts with the fewest inputs; R1 over R2 at a tie.
