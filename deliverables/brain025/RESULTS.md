# BRAIN02.5: the bounded terrain-observability experiment, result

Branch `claude/brain025-terrain-observability`. BRAIN02 is untouched: nothing of its was renamed, moved,
mutated or overwritten, and every BRAIN02.5 artifact is separately named.

## The answer

The question was how much more reliably the same learner can be taught when the smallest useful increase
in local terrain observability is added. On a fresh twenty-course gauntlet, judged against one
measurement of what the world actually does:

| | Candidate A, 64 inputs | BRAIN02.5, 80 inputs |
|---|---|---|
| **lessons to competence** | **never: 98% after 882 lessons** | **74 lessons, 9 passes, 100%** |
| distinct observations over 180 situations | 37 | 99 |
| observations whose courses need different actions | 1 | **0** |
| representable at all (CP-SAT, the byte box) | yes | yes |
| retention after unrelated later teaching | 98% → 54% | 100% → **72%** |
| taught far off, right with Tony on the ladder | 67% | **100%** |
| regressions | — | **0** |

Both brains can *express* the behaviour; only one can be *taught* it. That is the finding. Sixteen
appended inputs, over seven local terrain quantities, took the same learner from stuck at 98 percent to
competent in 74 lessons, and cost nothing anywhere in the gauntlet.

Two results do not flatter the design and are reported with the same weight. Teaching still interferes
with itself: an unrelated later stream costs BRAIN02.5 28 points of accuracy (BRAIN02 loses 44). And at
eighty inputs the think and the lesson no longer fit inside one frame of main-loop time, though both
finish well inside the four-frame think period with no overruns and a lower raster maximum than BRAIN02.

## The eighteen deliverables

| # | what | where |
|---|---|---|
| 1 | branch | `claude/brain025-terrain-observability` |
| 2 | exact commit | the tip of that branch; every checkpoint is its own commit |
| 3 | pre-registration | `PREREG-BRAIN025.md`, committed before any measurement, with one amendment made before any result existed and marked as such |
| 4 | schema and version | marker `BRAIN025`, layout 3, retina id 5; ring `LESSON25`, lesson format version 2; descriptor schema `tony-brain025-descriptor/1` |
| 5 | PRG and hash | `deliverables/prg/minimal64/tony-b025-a.prg`, 52,092 bytes, sha256 `2a547ebfe77bebb6b6174729af05a2ebb4dc2a8e558359f615cbdf34d6bfb423` |
| 6 | descriptor | `workbench/tony-b025-a.json` |
| 7 | the complete input list | `INPUTS.md`: 0 to 63 byte-identical to R1b, 64 to 79 appended |
| 8 | the lesson schema | `LESSON-SCHEMA.md` |
| 9 | the migration tool and spec | `tools/brain025_migrate.py`, `MIGRATION.md` |
| 10 | migration parity results | zero mismatches: 711 of 711 on the machine, 12,816 of 12,816 off it |
| 11 | the preserved human brain | **outstanding: not in this repository.** `MIGRATION.md` gives the one command and the expected result |
| 12 | deterministic replay | the drain gate: 126 lessons in 5 batches replaying byte for byte, across 13 drains and 8 ring wraps |
| 13 | the zero-brain idle proof | the blank gate: 912 frames, no movement, every accumulator equal, IDLE throughout |
| 14 | the keyboard teaching proof | the key gate: the press edge, no other key, no lesson, the joystick untouched |
| 15 | the resource report | `RESOURCES.md` |
| 16 | Candidate A against BRAIN02.5 | `GAUNTLET.md` |
| 17 | regressions and failed hypotheses | below |
| 18 | integration instructions | `WORKBENCH-INTEGRATION-025.md` |

## The work, in order

**A. Baseline verified and frozen** (`BASELINE-VERIFICATION.md`). Engine commit `3e12f0e`, Candidate A's
hash, and all four BRAIN02 gates re-run green before anything was written. The preserved 300-lesson
human brain was searched for three ways and is not here.

**B. Pre-registered** (`PREREG-BRAIN025.md`) before any measurement: the frozen learner, blank-Tony,
the key, the spawn, one room, a measured definition of an alias and of its consequence, the additive
rule, the zero-mismatch migration gate, the versioned lesson record, the resource gates, the gauntlet,
the non-goals, and seven falsifiable predictions.

**C. The alias census** (`CENSUS.md`). 192 scenarios over 32 local terrains produce **21 distinct
observations**, 17 of them consequential aliases. The largest single observation covers eleven
geometries in which walking toward Tony drops the clone off an edge in nine and is safe in two.

**D. The extension** (`DESIGN.md`). Eleven candidate quantities were defined and scored; a search that
removes the most conflicting scenario pairs per input reached zero after nine thresholds. The published
design is the smallest ordinal thermometers containing all nine: **sixteen inputs over seven
quantities**, appended at 64 to 79. Over the same scenarios, 21 observations become 93 and both the 34
consequential splits and the 636 conflicting pairs fall to zero.

**E. On the machine.** The reference, the generator, the four playable seams (a widened sense block, a
terrain probe inside the packer, a blank brain with no fallback, a keyboard toggle), and the gates.

**F. Migration.** Zero prediction mismatches, as pre-registered.

**G. Replay and resources.** Both in `RESOURCES.md` and the drain gate.

**H. The gauntlet** (`GAUNTLET.md`), on twenty fresh courses that had no part in choosing the design.

## Every prediction, scored

| | prediction | outcome |
|---|---|---|
| 1 | consequential aliases exist and concentrate in two families: a gap ahead, and obstacles distinguished only above the head row | **half right.** The gap and edge family is the largest, as predicted. Obstacle height above the head row was **not** consequential on its own; what mattered instead was the ceiling above, the wall behind, and how far the floor reaches |
| 2 | one gap-ahead input separates more per bit than any other single candidate | **wrong.** The search's first pick was `tObstTop >= 3`, the standing room above an obstacle, which removed 218 of 636 conflicting pairs. Gap width came second |
| 3 | eight to sixteen inputs resolve most classes; more than twenty-four not needed | **right**, at the generous end: nine thresholds sufficed, sixteen were published for ordinality |
| 4 | migration exactly clean, zero mismatches | **right**, after one false alarm traced to a stale test-hook read on the old build, not to the migration |
| 5 | the machine holds: the think inside one frame, raster unchanged, the ring falling roughly in proportion | **half wrong.** The ring fell as predicted (180) and the raster improved (141 against 174, no overruns), but **the think no longer fits inside one frame**: 24,129 cycles against 19,656 |
| 6 | teaching improves on gap and obstacle scenarios, is unchanged elsewhere, and is worse nowhere | **right.** 74 lessons to full competence against never; zero regressions |
| 7 | blank is blank and the key is clean | **right.** Both proved on the machine |

## Regressions, and everything that went wrong

* **No behavioural regressions.** On the 170 gauntlet scenarios that have a good action, every one
  Candidate A gets right BRAIN02.5 also gets right.
* **The one-frame bound is a regression in resources**, and the only one. It is set out in
  `RESOURCES.md` with the three measurements that say the machine keeps up regardless.
* **The ring holds 180 lessons instead of 300.** Pre-registered as acceptable; a longer session needs
  one drain, which the handshake already supports.
* **Retention is poor for both brains** and is not fixed by more eyes. This is the clearest open problem
  the experiment leaves behind, and it belongs to the rule and the single layer, not to the senses.
* **A false alarm in the migration gate**, three mismatches out of 711, chased to the end and found to
  be a two-frame wait on a hook that sometimes needs six. Recorded in `MIGRATION.md` rather than quietly
  fixed.
* **The scripted E5 teacher stalls from the study spawn**, so the teaching gate was rebuilt around a
  terrain-independent behaviour ("come to me") rather than the E5 staircase climb. The teacher is a
  BRAIN02-era hand-written rule and the brain does not drive during teaching, so this says nothing about
  BRAIN02.5; it is recorded because the gate changed.
* **The two builds' own rollouts disagree on 80 of 180 gauntlet scenarios**, 70 of those on the two
  build outputs, because BRAIN02.5's slower main loop completes fewer build macros inside a fixed
  rollout. The comparison uses one measurement of the world for both, and the disagreement is reported
  rather than hidden.
* **Deliverable 11 is outstanding** because the 300-lesson human brain is not in this repository.

## BRAIN02 is unchanged, and checked

The pre-registration requires the existing tests to keep passing. Re-run at the end of the experiment:

* `tools/brain02_ref.py check` — ALL OK.
* the four gates on `tony-b02-a.prg` — parity 6 checks, resources 4, teach 11, drain 7, **no failures**.
* the five BRAIN02 PRGs, `tony-chamber.prg` and `tony-build.prg` — every hash unchanged.
* Candidate A rebuilt from the modified generator — byte for byte
  `ae6ce5244478532c5ec581c9e24a30bea0743c68b2dd7cc7ff9f3017bc3e594d`, so the one change made to the
  generator (a default that BRAIN02.5 needs) alters nothing for BRAIN02.
* `git diff 3e12f0e..HEAD` over `deliverables/bakeoff/`, the three BRAIN02 tools and the five BRAIN02
  PRGs — empty.

## What was not done, deliberately

No hidden layer, no recurrence, no memory, no reward, no planner, no pathfinding, no second room, no
moving ladder, no procedural rooms, no browser-side inference or learning, no Solidity, no renderer, no
UI. The sealed goal senses and the sealed goal holdout were not opened and the sealed Phase 4 sweep was
not run. The learner is BRAIN02's, unchanged: same vocabulary, same byte weights, same rule, same tie,
same accumulator semantics, same inputs 0 to 63.

## Status

BRAIN02.5 is a research build for this study. It is **not** the final Chamber v2 architecture, nothing
is deployed, nothing is merged over BRAIN02, and the 300-lesson human brain is untouched. The work stops
here.
