# Phase 1: exact feasibility and margin (results)

Run as pre-registered in `PREREG-BAKEOFF.md` (commit 241f6cf). CBC through pulp; "Not Solved" is a
time limit, never a proof. Data: `phase1.json`. The 231 teacher states are the states visited under
teaching; the union adds the 1,358 vectors met in the curriculum evaluation, labelled by the teacher
(1,424 distinct).

## The designed retinas

| arm | inputs | the 231 | the union |
|---|---|---|---|
| `A0_raw` | 20 | Infeasible (0.2s) | not run |
| `A1_raw+dy1h+last` | 45 | Infeasible (0.2s) | not run |
| `T_dyup` | 27 | Infeasible (0.2s) | not run |
| `T_dydown` | 27 | Infeasible (0.2s) | not run |
| `T_dyup+dydown` | 34 | Infeasible (0.2s) | not run |
| `T_dxs` | 22 | Optimal (6.0s), margin 3 | Infeasible (1.3s) |
| `T_dyup+dxs` | 29 | Optimal (5.3s), margin 3 | Infeasible (2.2s) |
| `T_dydown+dxs` | 29 | Not Solved (120.1s) | not run |
| `T_last` | 30 | Infeasible (0.1s) | not run |
| `T_dyup+last` | 37 | Infeasible (0.1s) | not run |
| `T_dydown+last` | 37 | Infeasible (0.1s) | not run |
| `T_dyup+dydown+last` | 44 | Infeasible (0.1s) | not run |
| `T_dyup+dydown+dxs` | 36 | Optimal (2.5s), margin 1 | Infeasible (1.7s) |
| `T_dxs+last` | 32 | Optimal (6.7s), margin 3 | Infeasible (1.9s) |
| `A2_A1+adx1h+dxs` | 55 | Optimal (6.1s), margin 16 | Not Solved (300.6s) |
| `T_dyup+dxs+last` | 39 | Optimal (60.3s), margin 2 | Infeasible (5.6s) |
| `T_dydown+dxs+last` | 39 | Optimal (6.8s), margin 0 | Infeasible (1.9s) |
| `T_dyup+dydown+dxs+last` | 46 | Optimal (6.7s), margin 1 | Infeasible (6.2s) |
| `T_adxt` | 27 | Not Solved (120.1s) | not run |
| `T_dyup+adxt` | 34 | Not Solved (120.1s) | not run |
| `T_dydown+adxt` | 34 | Not Solved (120.1s) | not run |
| `T_dyup+dydown+adxt` | 41 | Not Solved (120.1s) | not run |
| `T_dxs+adxt` | 29 | Optimal (2.3s), margin 7 | Infeasible (2.6s) |
| `T_dydown+dxs+adxt` | 36 | Optimal (4.2s), margin 3 | Infeasible (2.4s) |
| `T_dyup+dxs+adxt` | 36 | Optimal (14.5s), margin 8 | Infeasible (2.3s) |
| `T_dyup+dydown+dxs+adxt` | 43 | Optimal (4.9s), margin 7 | Infeasible (2.4s) |
| `T_last+adxt` | 37 | Not Solved (120.1s) | not run |
| `T_dyup+last+adxt` | 44 | Not Solved (120.1s) | not run |
| `T_dydown+last+adxt` | 44 | Not Solved (120.1s) | not run |
| `T_dyup+dydown+last+adxt` | 51 | Not Solved (120.1s) | not run |
| `T_dxs+last+adxt` | 39 | Optimal (5.2s), margin 4 | Infeasible (3.0s) |
| `T_dydown+dxs+last+adxt` | 46 | Optimal (4.2s), margin 2 | Infeasible (3.0s) |
| `T_dyup+dxs+last+adxt` | 46 | Optimal (3.1s), margin 11 | Not Solved (300.9s) |
| `T_dyup+dydown+dxs+last+adxt` | 53 | Optimal (7.3s), margin 16 | Not Solved (301.0s) |

## The association layer (C3), ten seeds per group

| units | K | inputs | the 231 over ten seeds | margins of the feasible seeds | the union (first two feasible seeds) |
|---|---|---|---|---|---|
| sign | 32 | 52 | 7 feasible, 0 infeasible, 3 unsolved | [0, 0, 0, 1, 2, 3, 3] | Infeasible, Infeasible |
| sign | 48 | 68 | 9 feasible, 0 infeasible, 1 unsolved | [0, 1, 2, 3, 3, 3, 3, 6, 7] | Infeasible, Infeasible |
| sign | 64 | 84 | 8 feasible, 0 infeasible, 2 unsolved | [0, 0, 2, 3, 3, 3, 5, 7] | Infeasible, Infeasible |
| bucket | 32 | 52 | 6 feasible, 1 infeasible, 3 unsolved | [0, 0, 0, 1, 3, 3] | Infeasible, Infeasible |
| bucket | 48 | 68 | 10 feasible, 0 infeasible, 0 unsolved | [0, 0, 1, 2, 3, 3, 3, 5, 6, 7] | Infeasible, Infeasible |
| bucket | 64 | 84 | 8 feasible, 0 infeasible, 2 unsolved | [0, 3, 3, 3, 3, 3, 3, 6] | Infeasible, Infeasible |

## Reading

- **The 231 teacher states.** The two dx-sign flags are what unlocks them: raw senses plus the two
  flags (22 inputs) are representable with margin 3, and every arm without the sign flags is either
  infeasible or unsolved, the one-hot dy and last-action flags included (A1). The review's T4 (39
  inputs) is feasible with margin 2; adding the |dx| thermometer raises the margin to 8 at 36 inputs
  and 11 at 46; A2 and the full thermometer set reach margin 16. The association units fit on most
  seeds (8 of 10 at K = 48 for both kinds) with margins 0 to 7, seed-dependent, and a few seeds per
  group unsolved.
- **The union.** No arm was found to fit it. Every designed arm the solver could decide is infeasible,
  T4 in 5.6 s; the three widest (A2 at 55, the 46- and 53-input thermometer sets) ran out their limit
  undecided; all twelve association seeds tried are infeasible. Over the states the corpus actually
  visits, the teacher's policy is not representable by any decided encoding, so a fit to the 231 is a
  fit to the curriculum's own states, not to the policy in general.
- The margin is in accumulator units and one lesson moves an accumulator by up to 7 per shared input,
  which is why Phase 2 is the test that matters.
