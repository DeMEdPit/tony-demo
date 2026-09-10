# Pre-registration: the architecture bake-off, phases 1 and 2

Written and committed before Phase 1 ran. Design input: the session of record's architecture review
of 2026-09-10 (`chamber-v2-architecture-review.md`), with the owner's two questions kept separate:
**A**, representation and learnability with the information Tony has today; **B**, goal observability,
specified and sealed in `GOAL-SENSES.md` and `goal-holdout.json` in this same commit and read by
nothing in A. The present result (the curriculum brain) is taken as evidence that a recoding can remove
the representability failure, not yet as evidence that the learning rule is sufficient; Phase 2 exists
to test the second claim, and no convergence theorem is assumed for the bounded -8..7 saturating rule.

Nothing in the PRG, the senses, the rule, the decoder or the frozen corpora and results changes here.
Phases 1 and 2 are offline. Phases 3 and 4 (the machine, the behaviour) are outlined at the end and
will be pre-registered separately once Phases 1 and 2 have named the survivors.

## Held fixed

The twenty raw senses as published, the ten actions, the curriculum teacher of
`../curriculum/PREREG-CURRICULUM.md` as the labelling policy and the imitation ceiling, the 4-bit
range, the step-of-one rule (mood-free prediction, lesson on error, the taught row up and the predicted
row down by the sign of each input, saturating), the first-largest tie rule, the strict scoring rule.
The frozen data: the 231 distinct teacher states and the 1,484-tick stream of one curriculum pass
(`../curriculum/decisions-*.json`), the 525 recorded lessons, and the 1,358 vectors encountered in the
curriculum evaluation (`../curriculum/encountered2.json`), which with the 231 make a union of 1,424
distinct vectors, every one labelled by the teacher.

## The features (the contract for Phase 3's bit-for-bit check)

Every added input is a fixed function of the twenty raw senses as the 6502 publishes them (signed
nibbles; flags 0 or 7). The reference below is the definition; the 6502 must derive the same bytes from
the same block, and Phase 3's acceptance test is a golden set over recorded blocks compared byte for
byte through the test hook.

```python
def therm_dy_up(x):   return [F if x[2] >= k else 0 for k in range(1, 8)]        # "Tony at least k bricks above me", k = 1..7
def therm_dy_down(x): return [F if x[2] <= -k else 0 for k in range(1, 8)]       # "Tony at least k bricks below me"
def onehot_dy(x):     return [F if x[2] == v else 0 for v in range(-7, 8)]       # 15 flags
def dx_sign(x):       return [F if x[1] > 0 else 0, F if x[1] < 0 else 0]        # "he is to my right", "to my left"
def therm_adx(x):     return [F if abs(x[1]) >= k else 0 for k in range(1, 8)]   # "at least k buckets away"
def onehot_adx(x):    return [F if abs(x[1]) == k else 0 for k in range(0, 8)]   # 8 flags
def onehot_last(x):
    """the last action as a category. Sense 16 holds the action index 0..9 in the low nibble; the
    reference sign-extends it, so 8 and 9 arrive as -8 and -7. The category is the raw nibble
    (value & 15): nibble k sets flag k for k in 0..9; nibbles 10..15 (never produced) set no flag."""
    r = x[16] & 15
    return [F if r == k else 0 for k in range(10)]
```

The last action: sense 16 holds the action index 0..9 in the low nibble; the reference sign-extends
every nibble, so 8 and 9 arrive as -8 and -7. The one-hot category is the raw nibble (`value & 15`):
nibble k sets flag k for k in 0..9, nibbles 10..15 (never produced) set no flag. The 6502 reads the
nibble directly.

The association units (C3), fixed at build time from a seed, never learned, their wiring the published
structure:

```python
class Assoc:
    """fixed random association units over the twenty raw senses, generated from a seed and never
    learned. Two kinds. 'sign': a unit reads four senses with fixed random signs and fires when the
    signed sum reaches its threshold. 'bucket': a unit reads two senses, each against a fixed random
    threshold in a fixed direction, and fires when both hold (a random conjunction of two detectors).
    The wiring is the published structure: units(seed) lists every unit's senses, signs/thresholds."""
    def __init__(self, K, seed, kind):
        self.K, self.seed, self.kind = K, seed, kind
        rng = random.Random(f"{kind}-{K}-{seed}")
        self.units = []
        for _ in range(K):
            if kind == "sign":
                idx = rng.sample(range(1, 20), 4); sg = [rng.choice((-1, 1)) for _ in idx]; th = rng.choice((0, 4, 8, 12))
                self.units.append(dict(senses=idx, signs=sg, threshold=th))
            else:
                idx = rng.sample(range(1, 20), 2); conds = []
                for i in idx:
                    lo, hi = (-7, 7) if i in (1, 2) else (0, 7)
                    k = rng.randint(lo + 1, hi); conds.append((i, rng.choice((">=", "<=")), k))
                self.units.append(dict(conds=conds))
    def __call__(self, x):
        out = []
        for u in self.units:
            if self.kind == "sign": out.append(F if sum(s * x[i] for i, s in zip(u["senses"], u["signs"])) >= u["threshold"] else 0)
            else: out.append(F if all((x[i] >= k) if op == ">=" else (x[i] <= k) for i, op, k in u["conds"]) else 0)
        return out

```

## The arms

Designed retinas (every subset of the thermometer parts over the raw senses, plus the review's A1 and
A2), and the association layer at K = 32, 48, 64 for both unit kinds over seeds 0..9 (60 arms). The
review's primary arm is `T_dyup+dxs+last` (T4: 39 inputs).

| arm | inputs | what it is |
|---|---|---|
| `A0_raw` | 20 | the twenty senses as published |
| `A1_raw+dy1h+last` | 45 | A0 plus one-hot dy (15) and one-hot last action (10) |
| `A2_A1+adx1h+dxs` | 55 | A1 plus one-hot |dx| (8) and the sign of dx (2) |
| `T_dyup` | 27 | raw plus dyup |
| `T_dydown` | 27 | raw plus dydown |
| `T_dyup+dydown` | 34 | raw plus dyup, dydown |
| `T_dxs` | 22 | raw plus dxs |
| `T_dyup+dxs` | 29 | raw plus dyup, dxs |
| `T_dydown+dxs` | 29 | raw plus dydown, dxs |
| `T_dyup+dydown+dxs` | 36 | raw plus dyup, dydown, dxs |
| `T_last` | 30 | raw plus last |
| `T_dyup+last` | 37 | raw plus dyup, last |
| `T_dydown+last` | 37 | raw plus dydown, last |
| `T_dyup+dydown+last` | 44 | raw plus dyup, dydown, last |
| `T_dxs+last` | 32 | raw plus dxs, last |
| `T_dyup+dxs+last` | 39 | raw plus dyup, dxs, last |
| `T_dydown+dxs+last` | 39 | raw plus dydown, dxs, last |
| `T_dyup+dydown+dxs+last` | 46 | raw plus dyup, dydown, dxs, last |
| `T_adxt` | 27 | raw plus adxt |
| `T_dyup+adxt` | 34 | raw plus dyup, adxt |
| `T_dydown+adxt` | 34 | raw plus dydown, adxt |
| `T_dyup+dydown+adxt` | 41 | raw plus dyup, dydown, adxt |
| `T_dxs+adxt` | 29 | raw plus dxs, adxt |
| `T_dyup+dxs+adxt` | 36 | raw plus dyup, dxs, adxt |
| `T_dydown+dxs+adxt` | 36 | raw plus dydown, dxs, adxt |
| `T_dyup+dydown+dxs+adxt` | 43 | raw plus dyup, dydown, dxs, adxt |
| `T_last+adxt` | 37 | raw plus last, adxt |
| `T_dyup+last+adxt` | 44 | raw plus dyup, last, adxt |
| `T_dydown+last+adxt` | 44 | raw plus dydown, last, adxt |
| `T_dyup+dydown+last+adxt` | 51 | raw plus dyup, dydown, last, adxt |
| `T_dxs+last+adxt` | 39 | raw plus dxs, last, adxt |
| `T_dyup+dxs+last+adxt` | 46 | raw plus dyup, dxs, last, adxt |
| `T_dydown+dxs+last+adxt` | 46 | raw plus dydown, dxs, last, adxt |
| `T_dyup+dydown+dxs+last+adxt` | 53 | raw plus dyup, dydown, dxs, last, adxt |
| `C3_sign_K{32,48,64}_s{0..9}` | 52, 68, 84 | raw plus K fixed sign units (four senses, random signs, a threshold), ten seeds |
| `C3_bucket_K{32,48,64}_s{0..9}` | 52, 68, 84 | raw plus K fixed bucket-conjunction units (two senses, each against a random threshold), ten seeds |

## Phase 1: exact feasibility and margin (CBC through pulp)

For every arm: (1) whether any legal 4-bit 10 x n matrix reproduces the teacher's labels on the 231
states under the program's tie rule, 120 s per solve, "Not Solved" reported as such and never as a
proof; (2) for feasible arms, the largest achievable minimum margin, an integer m maximised subject to
every gap being at least m plus the tie term, 120 s (the incumbent's m is reported as a lower bound if
the solver stops on time); (3) for the designed arms and the first two feasible seeds of each
association group, feasibility on the union of 1,424 labelled vectors, 300 s. The margin is in
accumulator units: one nudge of one weight moves an accumulator by at most 7, so a margin under 7 can
be undone by a single lesson on a shared input, which is what Phase 2 measures directly.

## Phase 2: learnability by the exact rule, from zero

For every arm feasible on the 231 (and A0 as the reference), the exact rule in Python (the same
`learn` the golden vectors check, generalised to n inputs) from zero weights, 300 passes, on:

- **S1, the tick stream**: the curriculum's 1,484 labelled states per pass in order, the rule deciding
  which become lessons (prediction differs from the teacher). This is the stream the machine would
  see, up to the edge lessons.
- **S2, the labels cycled**: the 231 unique states with their labels, in a fixed order.
- **S3, the tick stream with the idle tails subsampled**: an idle decision is kept if its neighbour is
  not idle, else with probability one in eight (seed 0).
- **S0, the 525 recorded lessons** replayed in order, for comparison with the review's proposal; these
  are the raw brain's lessons, so on a recoded arm they are a different stream from the one the
  machine would produce.

Recorded per arm and stream: lessons to the first pass that reproduces the teacher on all 231 states;
the number of passes at full agreement out of 300 (stability); the final and the best agreement; the
count of saturating clamps; the lessons per pass over the last ten passes.

**Survivor rule, fixed now.** An arm survives Phase 2 if, on S1, it first reproduces the teacher on
all 231 states within 400 lessons and then stays at full agreement for at least 80% of the remaining
passes. An arm that CBC fits but the rule cannot reach within 400 lessons on S1 is reported as
"representable, not learnable by this rule" and goes to the rule-v2 question, not to Phase 3. If S3
reaches within 400 where S1 does not, the imbalance was a cause and that is reported as a curriculum
finding, not a survival.

Among survivors, the ranking for Phase 3 is by inputs ascending; C2 (a designed retina) is preferred
over C3 at equal behaviour, and C3 is carried to Phase 3 if it survives on at least half its seeds at
some K, so that Phase 4 can show whether it wins on fresh behaviour or headroom, as the owner asked.

## Predictions, written before the run

- Phase 1: A0 infeasible; A1 infeasible; A2 feasible; T4 feasible with margin 2 on the 231 (a smoke
  test of the code reproduced the review's T4 feasibility and found the margin to be exactly 2, which
  the review had predicted "above 2"); the thermometer subsets without the dx sign infeasible; the
  union feasible for T4 and A2. C3 sign units feasible on fewer than half the seeds at K = 48; bucket
  units on more.
- Phase 2: with a margin of 2 against nudges of 7, I expect S1 to reach full agreement on T4 but not
  to hold it: the rule will oscillate on the states whose fits are tight, and stability under 80% is
  my guess for T4, better for the wider A2, worse for C3. If that is the outcome, the recoding removes
  the representability failure and the rule is what falls short, and the rule-v2 question (a margin,
  or a scaled step) is the next one.

## Phase 3 and 4, outlined, to be pre-registered after Phase 2

Phase 3: the survivors implemented as slot layouts behind the same test hooks, the recoding table or
the unit table in the program, golden vectors for the added features compared byte for byte against
this reference, cycles per think and per lesson on the harness at period 4 and 6, RAM, the raster
bench at zero overruns. Phase 4: each survivor trained from zero with the curriculum and the stopping
rule as pre-registered, evaluated with the seven arms of RESULTS2 on the old corpus and the shadow
holdout, and then, with the sealed goal senses built in, on the sealed goal holdout, against the
extended teacher. The decision rule of the review stands: the arm within two scenarios of the teacher
on the sealed holdout with the fewest inputs; C2 over C3 at a tie; if neither is within five, the
architecture question reopens.
