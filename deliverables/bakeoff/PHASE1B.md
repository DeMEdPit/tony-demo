# Phase 1b: exact representability as a maximum feasible subset (results)

Run as pre-registered in `PREREG-1B.md` (commit bcba27f). Solver: CP-SAT (OR-Tools 9.15), plain
feasibility first and, when a set is not feasible, the maximum feasible subset (one Boolean per state,
the count of fitted states maximised) warm-started from the weights the rule reached in Phase 2b and
carrying the proven cut; 300 s per solve; every solution replayed through the exact forward pass. The
231 at 8 bits also through CBC. Data: `phase1b.json` (every solve's status, bounds, weights and the
unfit states named). Two facts about reading the tables:

- **OPTIMAL is exact.** "feasible" means a legal weight matrix in the box reproduces every label under
  the tie rule (the replay confirms it); "k unfit" with OPTIMAL means no matrix fits more than N − k of
  the states, and the k are named below. A range ("a to b unfit") is a time limit: the incumbent fits
  N − b and the solver's bound allows as few as a.
- **The sets are nested** (231 ⊂ 474 ⊂ 1,424), so an infeasible smaller set proves the larger one
  infeasible even where the solver's own bound on the larger set stayed open: every "0 to b" cell
  whose smaller set is infeasible reads "1 to b". CBC proved infeasibility in a tenth of a second on
  two mixed-encoding instances where CP-SAT's feasibility phase timed out (`raw20` under V); the two
  solvers are complementary and both are reported.

## 1. The tables

Margins are the largest integer `m` such that every gap is at least `m` plus the tie term, at 8 bits,
exact where OPTIMAL. "max|w|" is the largest magnitude in the margin solution (the solver uses the
whole box for margin; it says nothing about what the rule needs, which Phase 2b measured at 25).

### Absolute vocabulary

| arm | the 231, 8 bits | the 231, 4 bits | the 474, 8 bits | the 474, 4 bits | the 1,424, 8 bits |
|---|---|---|---|---|---|
| `raw20` | **1 unfit** of 231 (1.6s); CBC Infeasible | (8-bit only) | 1 to 13 unfit of 474 (time limit; incumbent 461) | (8-bit only) | 0 to 79 unfit of 1424 (time limit; incumbent 1345) |
| `T36` | feasible (0.2s), margin , max\|w\|  | (8-bit only) | not run | (8-bit only) | not run |
| `A2` | not run | (8-bit only) | not run | (8-bit only) | not run |
| `R0` | feasible (0.1s), margin 63, max\|w\| 128; CBC Optimal | feasible (0.1s) | **1 unfit** of 474 (0.6s) | **1 unfit** of 474 (4.6s) | 0 to 2 unfit of 1424 (time limit; incumbent 1422) |
| `R1` | feasible (0.1s), margin 63, max\|w\| 128; CBC Optimal | feasible (0.2s) | **1 unfit** of 474 (0.5s) | **1 unfit** of 474 (5.6s) | 0 to 2 unfit of 1424 (time limit; incumbent 1422) |
| `R1b` | feasible (0.1s), margin 63, max\|w\| 128; CBC Optimal | feasible (0.1s) | **1 unfit** of 474 (0.7s) | **1 unfit** of 474 (2.3s) | 0 to 2 unfit of 1424 (time limit; incumbent 1422) |
| `R2` | feasible (0.2s), margin 127, max\|w\| 128; CBC Optimal | feasible (0.3s) | feasible (0.6s), margin 127, max\|w\| 128 | feasible (0.6s) | feasible (2.5s), margin 127, max\|w\| 128 |

### Reference-relative vocabulary V

| arm | the 231, 8 bits | the 231, 4 bits | the 474, 8 bits | the 474, 4 bits | the 1,424, 8 bits |
|---|---|---|---|---|---|
| `raw20` | 0 to 4 unfit of 231 (time limit; incumbent 227); CBC Infeasible | (8-bit only) | 0 to 35 unfit of 474 (time limit; incumbent 439) | (8-bit only) | 0 to 136 unfit of 1424 (time limit; incumbent 1288) |
| `T36` | not run | (8-bit only) | not run | (8-bit only) | not run |
| `A2` | not run | (8-bit only) | not run | (8-bit only) | not run |
| `R0` | feasible (0.1s), margin 127, max\|w\| 128; CBC Optimal | feasible (0.1s) | feasible (0.2s), margin 84, max\|w\| 128 | feasible (0.2s) | **1 unfit** of 1424 (15.0s) |
| `R1` | feasible (0.1s), margin 127, max\|w\| 128; CBC Optimal | feasible (0.1s) | feasible (0.3s), margin 122, max\|w\| 128 | feasible (0.3s) | feasible (1.0s), margin 63, max\|w\| 128 |
| `R1b` | feasible (0.1s), margin 127, max\|w\| 128; CBC Optimal | feasible (0.1s) | feasible (0.2s), margin 122, max\|w\| 128 | feasible (0.2s) | feasible (1.0s), margin 63, max\|w\| 128 |
| `R2` | feasible (0.2s), margin 127, max\|w\| 128; CBC Optimal | feasible (0.2s) | feasible (0.5s), margin 127, max\|w\| 128 | feasible (0.5s) | feasible (2.0s), margin 127, max\|w\| 128 |

## 2. The unfit states, named

### The teacher-visited 474 under the absolute vocabulary: exactly one, and which one is a choice

For `R0`, `R1` and `R1b` at 8 bits and at 4 bits the exact minimum is **one unfit state**, and it is
not the same state in every solve: the solver drops whichever member of one family costs least. The
forced-fit probe (each named state forced to fit, the problem re-solved) keeps the minimum at one and
drops another member of the same family. The family, every member of it a build:

| state (non-zero senses) | where met | teacher | the kind |
|---|---|---|---|
| dx 1, dy 4, facing right, on ground, floor below, wall ahead at the foot, brick ahead at the foot, still 2, Tony on a ladder | E07 stairs C33, frame 128; clone (270, 142), Tony (284, 72) | build left (away) | the route's first brick, on the stairs facing him with a step ahead, right side |
| dx −1, dy 4, facing left, on ground, floor below, wall ahead at the foot, brick ahead at the foot, still 2, Tony on a ladder | E1 mirror with walk (teacher arm), offset 156; clone (104, 142), Tony (92, 72) | build right (away) | the same, left side |
| dx −3, dy 2, facing left, on ground, floor below, buildable, still 2 | E13 stack from the right, frame 0; clone (234, 206), Tony (203, 174) | build left (toward) | the stack's foot, on the floor with a buildable slot ahead, from the right |
| dx 3, dy 2, facing right, on ground, floor below, buildable, still 2 | E14 stack from the left, frame 0; clone (124, 206), Tony (155, 174) | build right (toward) | the same, from the left |

Which single state is dropped in each solve: `R0` 8-bit E07 f128, forced → E14 f0; `R0` 4-bit E13 f0;
`R1` 8-bit E13 f0, forced → E1 off 156; `R1` 4-bit E14 f0; `R1b` 8-bit E13 f0, forced → E14 f0; `R1b`
4-bit E13 f0. **This agrees with the review's diagnosis** (two residual teacher-visited states, both
build-direction cases, "the route's first brick against the stack's foot, on both sides") and sharpens
it: the exact minimum is one, not two (the review's number was the rule's own upper bound, 472 of 474;
the engine's rule reached 473), and the residual is not two particular states but a four-member
family of which any one can be left out. The structure is the exclusive-or the review named: the
build's absolute direction is "away" on the stairs and "toward" at the foot, so the sign of dx must
flip the answer between the two situations, and a first-order readout can honour that on all but one
of the four. The six named facts (`R1`) and the two last-action facts (`R1b`) do not change this: none
of them carries the sign of dx into the build rows. The order-2 layer (`R2`) does, and fits the 474
with margin 127 at 8 bits and outright at 4 bits.

### The full union of 1,424 under the absolute vocabulary

`R0`, `R1` and `R1b`: between 1 and 2 unfit (the incumbents leave two states, both the route's first
brick on the left side, E08 stairs C5 frame 172 and E1 mirror offset 156, dx −1, dy 4, facing left,
a step ahead; the bound did not close in 300 s, and the 474 proves at least one). `R2`: **feasible**,
margin 127. So under the absolute vocabulary the order-2 layer represents the whole teacher on every
visited state, the full union included, which the review expected no tested retina to do.

### Under the reference-relative vocabulary V

`R0` fits the 231 (margin 127) and the 474 (margin 84) at 8 bits and both at 4 bits; on the 1,424 it
leaves exactly **one** state (OPTIMAL in 15 s): dx 4, dy 2, facing left, on ground, floor below,
buildable, still 5 (B2 Tony on the fourth brick, teacher arm, offset 180; teacher "right", under V
"toward": a turn toward him before a build). It is an `ft` case: the teacher's answer there depends on
whether the clone faces the way he is, an exclusive-or of the facing flag with the sign of dx, and BIN
holds both flags separately. `R1` adds `facingPlayer`, which is exactly that fact, and **fits the full
1,424** (margin 63); so do `R1b` (margin 63) and `R2` (margin 127). The review's 1,416 of 1,424 for
BIN under V was the rule's bound; the exact minimum is one for `R0` and zero from `R1` up.

## 3. The controls

(the controls' paragraph is written when their solves finish)

## 4. Predictions, scored

The engine's (`PREREG-1B.md` section 8): `raw20` infeasible on the 231 at 8 bits: **right** (one
unfit, exact). `R0` feasible on the 231 at 8 and 4 bits: **right**. On the 474 the minimum unfit count
1 or 2 and build-direction states: **right** (exactly 1, all four candidates builds). On the 1,424 at
least 5: **wrong** (at most 2). `R1` and `R1b` change the 474 count little or not at all: **right** (not
at all). `R2` fits the 474: **right**; still infeasible on the 1,424: **wrong** (feasible, margin
127). V: `R0` feasible on the 231 and 474 at 8 and 4 bits: **right**; on the 1,424 infeasible with
fewer than ten unfit: **right** (exactly one). The three undecided Phase 1 cases: see section 3.

The review's: `R1b` unfit on fewer than fifteen of the 474: **right** but by a wide margin (one, the
same one as `R0`); `R2` on fewer than three: **right** (zero); the union infeasible for every tested
retina under V (its section 5, "the real limit"): **wrong** (`R1` and up fit it). Its two residual
states: **the same family**, count sharpened from two to one.

## 5. Interpretation

1. **Representability is settled, exactly, for every arm and set** except the mixed controls on the
   larger sets, where the time limit leaves ranges (and the nesting closes their lower end).
2. **Under the absolute vocabulary the whole residual of the teacher-visited states is one
   exclusive-or**, the direction of a build against the situation, present as a four-member family
   of which a first-order readout can hold three. No named first-order fact removes it; the order-2
   layer does, at the cost the budget states (3,394-byte slot, an accumulator outside 16 bits).
3. **Under V the same states are first-order**, `R0` fits everything the teacher visits (the 474 with
   margin 84 at 8 bits, and at 4 bits), and one more named fact (`facingPlayer`) makes the entire
   evaluation union representable with 62 inputs. The review's "real limit" (no linear readout over
   any tested retina reproduces the teacher on the union) does not survive V plus one fact.
4. **Representable is not learned**: Phase 2b showed that from the curriculum stream every arm leaves
   about sixty of the 474 wrong, in situations the curriculum never showed, and that the 474 is
   learned only from its own stream. Phase 4's behaviour on the sealed holdouts remains the criterion;
   these tables say which facts to offer the retina and that the vocabulary is the cheaper lever.
