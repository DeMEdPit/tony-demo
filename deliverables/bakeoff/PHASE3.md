# Phase 3: BRAIN02 on the machine (Checkpoint B and C results)

Run as pre-registered in `PREREG-PHASE3.md` (commit c09465a). Engine commit for the PRGs and this report:
`a04968d337d9dd5b030462a644e2a9e81b07a866`. Nothing here freezes an architecture; the sealed Phase 4 sweep was not run; the sealed goal
senses and holdout are untouched. Raw data: `phase3/` (per build: `resources-*.json`, `teach-*.json`,
`drain-*.json`, `climbed-*.bin`, cached learned weights), the gate logs summarised below, the
descriptors in `workbench/`, and `WORKBENCH-INTEGRATION.md`.

## 1. The pre-step (section 1 of the pre-registration)

R1s (R0s plus R1b's eight facts, 69 inputs) fits every set in both vocabularies (margins 127 on the 231,
88/122 on the 474, 51/63 on the 1,424) and learns the 474 cycled under V in **610** lessons against
R1b's 538 and R0s's 974 (`prestep-R1s.json`). The rule required at least 20% fewer than the better
candidate: it does not dominate, so A and B stand and R1s is recorded. One extra number from the same
run: R0s's margin on the full union under V is 20 against R1b's 63.

## 2. The gates, per build

| PRG | candidate | gate 1 parity | gate 2 resources | gate 3 TEACH | gate 4 drain |
|---|---|---|---|---|---|
| `tony-b02-a` | A (R1b, relative) | pass (6 checks) | pass | pass | pass |
| `tony-b02-b` | B (R0s, relative) | pass (6 checks) | pass | pass | pass |
| `tony-b02-drel` | D-rel (R0, relative) | pass (6 checks) | pass | pass | pass |
| `tony-b02-dabs` | D-abs (R0, absolute) | pass (6 checks) | pass | pass | pass |

The parity build `tony-b02-p128` (128 inputs) passes its golden sets (15 of 15 forward cases, the lesson case at 128 inputs).

Gate 1 on each candidate: the retina and `h` byte for byte against the reference on all 1,424 recorded
blocks; `golden-1b/forward-v2` and `lessons-v2` at the build's width through the flag-vector hook
(accumulators, the first largest, saturation at 127 and −128, the wrap cases, exact ties, the mood add);
the 40 vocabulary cases (the resolution, the translation, `h` from the block, the identity under the
absolute vocabulary); every header field wrong in turn gives kind 0 while kinds 0 and 2 still drive;
and Phase 2b's learned weights for the build's retina and vocabulary give the reference's output and
resolved action on all 474 teacher-visited blocks. The 128-input build covers the 16-bit extremes
(16,383 and −16,512 on every row at 128 set flags) and the largest lesson cases.

## 3. The resource ledger (gate 2)

Cycle counts are the machine's own (CIA 2 timer A). "Pure" is through the test hook with the
interrupts held off (the work itself); the live counts in `resources-*.json` include the frame
interrupt. Headroom: below the shadow (the code region's spare) and above the ring (the vacated
region's spare).

| PRG | bytes | sha256 | n | slot | weights | table | flag RAM | shadow | ring | headroom | think cycles (pure) | lesson cycles (pure) | snapshot (live max) | drain (max) | raster max / overruns | score gap min / mean / max |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|---|---|
| `tony-b02-a` | 51169 | `ae6ce5244478532c…` | 64 | 674 | 640 | 193 | 157 | 640 | 3332 | 164 / 508 | 11704–17464 (mean 14466) | 11467–18999 (mean 14559) | 27802 | 347 | 174 / 0 | 1 / 27 / 56 |
| `tony-b02-b` | 51121 | `4c62c1d2d7884145…` | 61 | 644 | 610 | 184 | 151 | 610 | 3332 | 212 / 508 | 10723–16096 (mean 13312) | 10680–17060 (mean 13422) | 21698 | 375 | 174 / 0 | 1 / 19 / 51 |
| `tony-b02-drel` | 51041 | `7ec874b6535618e8…` | 56 | 594 | 560 | 169 | 141 | 560 | 3332 | 292 / 508 | 10485–15754 (mean 13028) | 10361–16742 (mean 13144) | 20417 | 333 | 174 / 0 | 3 / 20 / 32 |
| `tony-b02-dabs` | 51041 | `012d42d58e977a55…` | 56 | 594 | 560 | 169 | 141 | 560 | 3332 | 292 / 508 | 10554–16008 (mean 13138) | 10194–16874 (mean 13143) | 20435 | 330 | 174 / 0 | 2 / 31 / 61 |

Code: candidate A's code region ends at `$8d5b` against `tony-body.prg`'s `$863e`, a net growth of 1,821
bytes of which the slot's growth (394), the retina table (193), the flag, active and pseudo-sense RAM
(157) and the pairing ring (26) are data and 276 bytes of multiply table and nibble expansions are
retired, leaving about 1,330 bytes of BRAIN02 code, hooks and profiler in place of BRAIN01's. The 128-input hook
with every flag set takes 50,563 cycles (2.6 frames): the cost is the active-flag count times ten rows,
so the candidates' 20 to 30 active flags cost 11,000 to 19,000 and 128 would not fit a frame.

## 4. TEACH end to end (gate 3)

Every candidate: boots kind 0 and follows; TEACH by the flag and by the chord; the stick drives him;
lessons change BRAIN02's weights and the education count and the first makes him kind 1; let go, he
drives on what he was taught (taught "left" with Tony to his right he walks left to the wall where the
follow rule walks right to Tony, under either vocabulary); the chord held a second toggles teaching on
and off with the brick taken back each time; a press is an edge and flashes him white within the frame;
the untouched PRG forgets. Then the number, E5's: sessions of follow-and-climb from zero with the
builder's rule as the teacher until he climbs the stairs and the ladder to Tony on his own, and the
brain that climbed, exported and loaded on a fresh boot, climbs again with the slot read back byte for
byte and the hash unchanged.

| PRG | candidate | lessons to climb | lessons per session |
|---|---|---|---|
| `tony-b02-a` | A (R1b, relative) | 33 in 2 session(s) | 16, 17 |
| `tony-b02-b` | B (R0s, relative) | 31 in 2 session(s) | 17, 14 |
| `tony-b02-drel` | D-rel (R0, relative) | 37 in 2 session(s) | 18, 19 |
| `tony-b02-dabs` | D-abs (R0, absolute) | 34 in 2 session(s) | 19, 15 |

BRAIN01 took 36 lessons in 4 sessions (E25).

## 5. Save, drain and reuse (gate 4)

At capacity 40 with a pseudo-random chattering teacher (a lesson on most ticks), drains whenever thirty
lessons are unread, over two sessions with the brain carried between them; after every drain the
drained records replayed by the reference over the brain as exported before them equal the machine's
weights and education count byte for byte, with equal behavioural hashes. Then at capacity 12 with no
drain: the ring fills, learning pauses (status bit 0, the red flash), a wrong checksum and a stale range
are refused with nothing reclaimed, the right acknowledgement resumes learning. Then the equivalence:
the split run's recorded lesson sequence, replayed once more uninterrupted by the machine's own rule
through the learn hook on a fresh boot and by the reference, gives the split run's brain byte for byte.

| PRG | drains | lessons drained | every ack accepted and replay equal | the split run | machine replay equal (education and hash) | reference replay equal |
|---|---:|---:|---|---|---|---|
| `tony-b02-a` | 16 | 451 | True | 163 lessons, 6 drains, 0 dropped | True | True |
| `tony-b02-b` | 16 | 458 | True | 172 lessons, 6 drains, 0 dropped | True | True |
| `tony-b02-drel` | 18 | 500 | True | 156 lessons, 6 drains, 0 dropped | True | True |
| `tony-b02-dabs` | 16 | 442 | True | 155 lessons, 6 drains, 0 dropped | True | True |

The equivalence is stated on the recorded lesson sequence, not on two stick scripts: a live teacher's
sequence shifts when a drain's frames land near a tick, so two runs of the same script are not the
same sequence; the pre-registration's intent (the identical sequence, uninterrupted or split, gives the
identical brain) is what the test checks.

## 6. Unexpected findings, and what was done about each

1. **Lessons were lost to the main loop's pace.** The pairing rule required the main loop to pack the
   block's next frame and attempt the lesson inside the same frame; a BRAIN02 lesson costs most of a
   frame, so under a chattering teacher 58 of 99 ticks lost their lesson (245 dropped pairings in one
   session, counted by a new `lessonNotPaired` field). Fixed: the frame interrupt records each frame's
   applied joystick byte and the clone's state in an eight-entry ring and the lesson looks the block's
   next frame up there; the taught action is derived from those bytes by sense 16's own rule. After the
   fix, zero dropped pairings and 79 lessons in the same 99 ticks. This is a change to the teaching
   pipeline's mechanics, not to the lesson's content (the same block, the same applied action).
2. **A teaching tick ran the forward pass twice.** The lesson evaluates the block (the retina, the
   mood-free forward pass, the resolution) and the think then did it again on the same block; the
   second is skipped now (`brainLessonRan`), which keeps a teaching pass inside a frame. The
   pre-lesson output is what "he thought X" reports.
3. **The deferred restore opened a window.** With the shadow restore moved to the main loop, a think in
   flight at the chord's toggle could hand the hold's choice (a build) to the decoder before the weights
   were put back; the second chord hold left a brick. Closed: the toggle idles the decoder and drops a
   macro in progress, and the clone's turn does nothing while a restore is pending.
4. **The 128-input hook needs three frames**, and the harness gate reads it accordingly; the CIA
   measurement includes the interrupt, so the pure numbers come from the hook with interrupts off.
5. **`$C000` is the screen**, not a free kilobyte (recorded at Checkpoint A); the 300-lesson ring fits
   the vacated region with 508 bytes above it in candidate A.
6. **The retina table is stored as three parallel arrays** (count, ops, operands, k) rather than
   interleaved triples, for X-indexed access without a zero-page pointer (none is safely free); the
   published content is the same and the descriptor states the layout.
7. **The ring's capacity is a header field** the machine reads, so a research control may lower it at
   boot (the gates use 40 and 12); the default stays 300.

## 7. What is delivered at Checkpoint C

`deliverables/prg/minimal64/tony-b02-{a,b,drel,dabs}.prg` (the sizes and hashes above), one JSON
descriptor per PRG in `workbench/`, `WORKBENCH-INTEGRATION.md`, this report, the raw data, and the E27
entry in `EXPERIMENTS.md`. Not done, by instruction: no Akalabeth change, no freeze, no interface
update as final, no Solidity, no hidden layer or recurrence, no rule change for noise, no holdout
exposed, no sealed Phase 4 sweep. The next step is the owner's first non-holdout human session on the
existing workbench (the five steps in `WORKBENCH-INTEGRATION.md`); Phase 4 follows its trace.
