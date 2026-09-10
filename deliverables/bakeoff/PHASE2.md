# Phase 2: learnability by the exact rule, from zero (results)

Run as pre-registered. The rule is the program's own (the mood-free prediction, a lesson when the
prediction differs from the teacher, the taught row up and the predicted row down by the sign of each
input, saturating at -8 and 7), generalised to n inputs; it was checked against the golden-vector
reference on the raw arm over 20 passes of the labels: identical weights throughout, 729 lessons each.
CBC's margin-16 solution for A2, replayed through the same forward pass, agrees on 231 of 231, so the
encodings and the evaluation are the solver's. Data: `phase2.json`. Cells are best/final agreement
over 300 passes out of 231 states. **No arm on any stream ever reached full agreement**, so
"lessons to first full agreement" is undefined everywhere and the survivor rule (full agreement within
400 lessons, held for 80% of the remaining passes) is met by no arm.

## The designed retinas

| arm | inputs | S1 tick stream | S2 labels cycled | S3 idle subsampled | S0 recorded lessons | clamps (S1) | lessons in the last pass (S1) |
|---|---|---|---|---|---|---|---|
| `A2_A1+adx1h+dxs` | 55 | 228/228 | 228/228 | 227/227 | 210/189 | 38 | 4 |
| `T_dxs` | 22 | 199/181 | 201/156 | 200/164 | 198/184 | 8032 | 54 |
| `T_dyup+dxs` | 29 | 220/203 | 218/212 | 224/205 | 199/195 | 443 | 18 |
| `T_dyup+dydown+dxs` | 36 | 220/203 | 218/212 | 224/205 | 196/182 | 443 | 18 |
| `T_dxs+last` | 32 | 197/150 | 198/176 | 198/158 | 205/197 | 6271 | 47 |
| `T_dyup+dxs+last` | 39 | 217/215 | 216/212 | 216/216 | 209/195 | 1487 | 22 |
| `T_dydown+dxs+last` | 39 | 200/198 | 198/176 | 200/170 | 208/184 | 6081 | 43 |
| `T_dyup+dydown+dxs+last` | 46 | 217/215 | 216/212 | 219/196 | 208/184 | 1487 | 22 |
| `T_dxs+adxt` | 29 | 211/202 | 200/200 | 212/197 | 198/158 | 4695 | 16 |
| `T_dyup+dxs+adxt` | 36 | 229/229 | 227/227 | 228/227 | 199/130 | 523 | 4 |
| `T_dydown+dxs+adxt` | 36 | 213/195 | 188/177 | 212/197 | 199/158 | 4144 | 16 |
| `T_dyup+dydown+dxs+adxt` | 43 | 228/228 | 228/228 | 227/227 | 206/191 | 283 | 4 |
| `T_dxs+last+adxt` | 39 | 216/212 | 210/210 | 216/205 | 199/166 | 4040 | 16 |
| `T_dyup+dxs+last+adxt` | 46 | 228/228 | 228/228 | 227/227 | 209/186 | 364 | 4 |
| `T_dydown+dxs+last+adxt` | 46 | 201/195 | 212/193 | 220/195 | 200/187 | 3798 | 16 |
| `T_dyup+dydown+dxs+last+adxt` | 53 | 230/228 | 228/228 | 227/227 | 207/197 | 204 | 4 |

## The association layer, S1 over the feasible seeds

| units | K | seeds run | best agreement | final agreement |
|---|---|---|---|---|
| sign | 32 | 7 | 192 to 217 | 162 to 217 |
| sign | 48 | 9 | 194 to 224 | 155 to 221 |
| sign | 64 | 8 | 202 to 215 | 143 to 211 |
| bucket | 32 | 6 | 192 to 213 | 172 to 206 |
| bucket | 48 | 10 | 175 to 215 | 167 to 211 |
| bucket | 64 | 8 | 186 to 212 | 144 to 208 |

## The residual, and what it is

For the strongest arms (A2, the 36-input arm with the |dx| thermometer, the 53-input full set) the
run ends at a fixed cycle: exactly four lessons every pass, on the same two or three states, forever.
They are the same states in every arm: the teacher's **build left** where the brain says **build
right**, the route's first brick on the training side (`dx 1, dy 4, facing right, a step ahead`), the
route's second brick (`dx 4, dy 3, facing away`), and the stack's foot from the right (`dx -3, dy 2,
facing left`). The build's direction is "away from Tony" in the route and "toward him" at the stack,
so the same two rows must answer opposite ways on the sign of dx, decided by other senses. CBC shows
that is representable, at margin 16 for A2. The rule never gets there: each pass nudges the two build
rows against each other on the shared inputs, the clamps at -8 and 7 are active (38 to 523 clamps in
S1), and the bounded update cannot grow the weights that the classical argument grows. T4 is worse:
it settles at 215 with 22 lessons a pass, its residual the walking states as well as the builds. The
idle subsampling (S3) changes none of this, so the imbalance was not the cause once the target is
representable. The recorded-lesson replay (S0) is uniformly lower, as expected for a stream another
brain chose.

**Exploratory, not pre-registered, not used for selection:** the same rule with a margin trigger (a
lesson also when the taught row leads by less than M, with the runner-up row pushed down) at M = 8 and
16 on A2 and the 36-input arm ends at the same four-lesson cycle, 228 to 230 of 231. A margin alone
does not break the cycle within the 4-bit box.

## Verdict under the pre-registered rules

- Every recoded arm that fits the 231 is **representable, not learnable by this rule**: none reaches
  the fit from zero in 300 passes (over 440,000 tick decisions), on any stream. Under the survivor
  rule nothing proceeds to Phase 3, and the question goes to the rule.
- The review's central claim holds in its first half and fails in its second: recoding removes the
  representability failure on the curriculum's states (and the dx sign is the part that does it), but
  the bounded ±1 saturating rule does not find those solutions, and no perceptron convergence theorem
  applies to it. The present result is evidence that a recoding *can* remove the representability
  failure and evidence that the learning rule is *not* sufficient, exactly the two things the owner
  asked to keep apart.
- Separately, Phase 1 says the union of visited states is not representable by any decided arm, so
  even a rule that reached the 231 fit would be fitting the curriculum, not the policy.

## What this points to, without implementing anything

The residual is a two-row conflict on the build rows inside a saturating box. The candidates for a
rule version 2 are about the update, not the encoding: a wider weight range (5 or 6 bits, which
changes the slot and the replay), an update that nudges only the row that must move rather than both,
or a step that respects saturation (no nudge on an input whose weight is pinned, so that the other
row carries the correction). Each is a rule change with its own golden vectors, to be pre-registered
as such. The recoding question is answered: the dx-sign flags are necessary on this teacher, the |dx|
thermometer buys margin cheaply, and the last-action one-hot is not what separates the 231.
