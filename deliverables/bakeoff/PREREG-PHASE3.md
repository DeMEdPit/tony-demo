# Pre-registration: Chamber v2 Phase 3 (BRAIN02 on the machine) and Phase 4 (behaviour)

Written and committed before any change to the PRG generator. Baseline: the engine at `b5aed53`
(`PHASE1B.md`, `PHASE2B.md`, `BRAIN02-BUDGET.md`, E26). Design input: the session of record's Phase 3
synthesis and the owner's Phase 3 instructions of 2026-09-11, with the seven refinements the engine
proposed and the owner's four additions, all pinned below. BRAIN02 is a research platform, not a
production brain: nothing here freezes an architecture, updates the standing interface as final,
begins Solidity, adds a hidden layer or recurrence, redesigns the rule for noise, touches the
Akalabeth repository, or runs the sealed Phase 4 sweep. The sealed goal senses and holdout stay
sealed (`GOAL-SENSES.md` sha256 `54694f90…`, `goal-holdout.json` `45f61f78…`).

Stop conditions, as instructed: **A** this pre-registration (a material contradiction stops here;
one non-material finding is recorded in section 13); **B** a failed hard gate stops with the evidence,
no redesign around it; **C** the playable PRGs and the integration contract, then stop and report.

## 1. Candidates, diagnostics, and the pre-step

All BRAIN02: byte weights, the unchanged symmetric rule at the 8-bit box, mood zero, the same slot
format, the same rule of resolution. Only the retina table and the vocabulary byte differ.

| | inputs | slot bytes (section 4) | vocabulary | role |
|---|---:|---:|---|---|
| **A: R1b** | 64 | 674 | reference-relative | the fastest learner of the 474 that fits the machine (538 lessons), fits the full union (margin 63) |
| **B: R0s** | 61 | 644 | reference-relative | one uniform retina (signed thermometers for dx and dy, no teacher-chosen facts); represents every set under both vocabularies; the insurance arm |
| **D-rel: R0** | 56 | 594 | reference-relative | diagnostic pair with D-abs: identical retina, weights, rule, scenarios; only the vocabulary differs |
| **D-abs: R0** | 56 | 594 | absolute | the other half of the pair |

Kind 0 (follow), kind 2 (builder) and the scripted teacher through the override remain the free
controls in every PRG. Eight bits, not six: identical results, native width, no packing.

**Pre-step, offline, before the generator is touched: R1s**, the R0s retina plus R1b's eight named
facts (69 inputs), through Phase 1b (feasibility and margin on the 231, the 474 and the 1,424 in
both vocabularies at 8 bits) and Phase 2b (the rule at 8 bits on S1, S2 and the 474 cycled, both
vocabularies). Decision rule, fixed now: R1s *clearly dominates* both A and B if its lesson count to
full agreement on the 474 cycled under V is at least 20% below the better of A (538) and B (974) and
its margin on the 1,424 under V is at least as large as both; then it is **reported before machine
implementation**, not substituted. Otherwise A and B stand and R1s is recorded.

## 2. The reference-relative vocabulary, and where it is resolved

Indices 0 idle, 1 toward, 2 away, 3 up, 4 down, 5 jump, 6 jump-toward, 7 jump-away, 8 build-toward,
9 build-away; the absolute vocabulary keeps today's indices (1 left, 2 right, 6 jump left, 7 jump
right, 8 build left, 9 build right). The horizontal sign `h` comes from the **reference vector**, two
derived bytes the interface publishes, `refDx` and `refDy`: today copies of senses 1 and 2 (the
player's offset), later (goal senses) computed by the interface's published rule and never chosen by
the decoder. `h = +1` if `refDx > 0`, `-1` if `refDx < 0`, and if `refDx == 0` the clone's facing in
the **same block** (sense 3: `+1` if set, else `-1`).

**Resolution happens once per think, from the block the brain thought on.** The think computes the
raw output index (`brainOutput`); under the relative vocabulary it resolves it to an absolute action
with the `h` of that block (toward is right when `h = +1`, else left; the jump and build pairs the
same way) and stores the absolute action in `brainAction`, which the decoder and the build macro
consume exactly as today. Sense 16 (the applied action) stays absolute. The decoder is unchanged and
chooses nothing. **A human's press** becomes a taught action by the same rule in the other direction:
the applied absolute action of frame N (sense 16 of the frame after the block, as today) is
translated with the `h` of the lesson's own block (frame N − 1), including when the reference is
directly above or below; a lesson therefore stays reconstructible from its own bytes. Under the
absolute vocabulary both maps are the identity. The round trip is verified by golden cases (section
9): every action index, both signs, dx positive, negative and zero with either facing.

## 3. The retina: a published table over the senses and nine named world facts

The forward pass reads a **flag vector** of n bytes (0 or 1), computed once per think from the
twenty published senses and nine **pseudo-senses** computed by the program from the same block
(indices 20 to 28, published definitions, reference in `tools/brain02_ref.py`):

| index | name | definition |
|---:|---|---|
| 20 | `hRight` | 1 if `refDx > 0`, or `refDx == 0` and `facingRight`; else 0 |
| 21 | `lastTowardRef` | the last action's horizontal direction (left, jump left, build left: −1; right, jump right, build right: +1; else 0) equals `h` |
| 22 | `lastAwayRef` | that direction equals `−h` |
| 23 | `refAbove` | `refDy > 0` |
| 24 | `facingRef` | `facingRight ≠ 0` equals `hRight == 1` (the teacher's `ft`) |
| 25 | `stepAhead` | `wallAheadFoot` and not `wallAheadHead` |
| 26 | `wallAhead` | `wallAheadFoot` and `wallAheadHead` |
| 27 | `buildableAndClear` | `buildable` and not `wallAheadFoot` |
| 28 | `adx` | `|refDx|` (0..7) |

The table: one count byte, then n entries of three bytes `(op, a, k)`, evaluated in order into the
flag vector. Ops: 0 `GE`: flag = signed sense[a] ≥ k; 1 `LE`: sense[a] ≤ k (k signed); 2 `EQN`:
(sense[a] & 15) == k; 3 `AND`, 4 `ANDNOT` (a and not b), 5 `OR`, 6 `XNOR` (a equals b): two operands
a and b (byte 3 is b) taken as booleans (non-zero) over senses and pseudo-senses. The table lives in
the program (it belongs to the retina id, not to a brain), is published with its id and hashed into
the interface later.

The four retinas, in flag order:

- **R0** (id 1, 56): bias (`GE 0 1`); the fifteen raw flags (`GE s 1` for s in 3,4,5,6,7,8,9,10,11,
  12,13,14,15,18,19); `dxRight` (`GE 1 1`), `dxLeft` (`LE 1 −1`); `adx ≥ k` (`GE 28 k`, k = 1..7);
  `dy ≥ k` (`GE 2 k`); `dy ≤ −k` (`LE 2 −k`); `still ≥ k` (`GE 17 k`); `last == k` (`EQN 16 k`,
  k = 0..9).
- **R1b** (id 2, 64): R0 then `facingRef` (`GE 24 1`), `stepAhead` (`GE 25 1`), `wallAhead`
  (`GE 26 1`), `ladderHereAndRefAbove` (`AND 12 23`), `facingAStep` (`AND 24 25`),
  `buildableAndClear` (`GE 27 1`), `lastTowardRef` (`GE 21 1`), `lastAwayRef` (`GE 22 1`).
- **R0s** (id 3, 61): bias; the fifteen raw flags; `dx ≥ k` (`GE 1 k`, k = 1..7); `dx ≤ −k`
  (`LE 1 −k`); `dy ≥ k`; `dy ≤ −k`; `still ≥ k`; `last == k`.
- **R1s** (id 4, 69): R0s then R1b's eight facts in the same order.

Table bytes: R0 169, R1b 193, R0s 184, R1s 208. These definitions reproduce `bakeoff2.py`'s `bin56`,
`six`, `lastrel` and the exploratory `bin61` flag for flag (checked in the pre-step), so the offline
results carry over to the machine's retina exactly.

## 4. The BRAIN02 slot, and the hash domains

Page-aligned, found by its marker like `BRAIN01`; length 34 + 10 n.

| offset | bytes | field | domain |
|---:|---:|---|---|
| 0 | 8 | marker `BRAIN02` and a zero | structural |
| 8 | 1 | kind: 0 follow (weights ignored), 1 perceptron over this layout, 2 builder | behavioural |
| 9 | 1 | layout, 2: byte weights over a retina table, ten outputs | behavioural |
| 10 | 1 | inputs n (must equal the program's retina count) | behavioural |
| 11 | 1 | hidden, 0 | behavioural |
| 12 | 1 | outputs, 10 | behavioural |
| 13 | 1 | period, frames between thinks, 4 | timing |
| 14 | 1 | lineage bits | provenance |
| 15 | 1 | rule version, 2: the symmetric rule, clamp −128..127 | provenance |
| 16 | 1 | vocabulary: 0 absolute, 1 reference-relative | behavioural |
| 17 | 1 | retina id (section 3; must equal the program's) | behavioural |
| 18 | 2 | education count: lessons applied to these weights over their life, low byte first | provenance |
| 20 | 4 | reserved, zero | structural |
| 24 | 10 n | weights: row o at 24 + o·n, one signed byte per input | behavioural |
| 24 + 10 n | 10 | mood: one signed byte per output, added to the row's score directly; **zero throughout Phase 3** | render |

**Three named domains.** The *behavioural domain* is what makes two minds the same mind: bytes 8 to 12,
16 and 17, and the weights; `brainHash` is SHA-256 over exactly these bytes in slot order, and a saved
brain is identified by it. The *provenance domain* (lineage, rule version, education count) records
how the mind came to be and how it will change; it travels with the saved brain, is reported by the
workbench, and never enters `brainHash`. The *timing and render domains* (period, mood) say how the
mind is run and nudged and are never part of a saved brain's identity. The reserved bytes and the
marker are structural. Two brains with equal `brainHash` behave identically on the same blocks
whatever their provenance bytes say.

**Malformed slot.** Every think checks: the marker, layout 2, kind under 3, inputs equal to the
program's retina count, hidden 0, outputs 10, rule version 2, vocabulary under 2, retina id equal to
the program's. Anything else: the effective kind is 0 and the follow rule drives, as today.

## 5. The forward pass, the rule, the accumulator

For each output o: `acc[o] = mood[o] + Σ_i flag[i] · w[o][i]`, a 16-bit two's complement sum of the
weights whose flag is set (no multiply, no table); the action is the first largest (ties to the lowest
index), exactly today's compare. The learning rule is BRAIN-INTERFACE-V1 section 6 with the clamp
constants changed: the mood-free prediction p; no lesson if p equals the taught index; else for every
set flag `w[t][i] += 1` and `w[p][i] −= 1`, each saturating at −128 and 127 (the sign of a flag is
always positive, so the step is +1 and −1). The education count and the session count advance on
every applied lesson.

**Accumulator bound, recomputed per width:** `|acc| ≤ 128 n + 128`. R0 7,296; R0s 7,936; R1b 8,320;
R1s 8,960; the parity build at 128 inputs 16,512; all inside 16 bits, asserted by the reference and
checked by the extreme golden cases on the machine. **Mood is zero in every Phase 3 parity, TEACH,
comparison and behavioural gate** so it cannot confound selection; the mood add is still verified as
code by golden cases with non-zero mood; the typical score gaps are measured (section 10) and mood's
scale is a separate later experiment.

## 6. The lesson ring `LESSON2`, and the drain handshake

A marked page-aligned block in the vacated region, replacing `LESSON1` in these builds:

| offset | bytes | field | who writes |
|---:|---:|---|---|
| 0 | 8 | marker `LESSON2` and a zero | program |
| 8 | 2 | `writeSeq`: the sequence number of the next lesson to record; equals the lessons applied this session | program |
| 10 | 2 | `readSeq`: acknowledged and reclaimed up to here (exclusive) | program |
| 12 | 2 | capacity C, 300 | program |
| 14 | 1 | entry size, 11 (14 with the goal senses, later) | program |
| 15 | 1 | status: bit 0 full (learning paused), bit 1 last ack rejected: stale range, bit 2 rejected: bad checksum, bit 3 rejected: a chord hold in progress, bit 4 shadow copy pending (learning paused), bit 7 last ack accepted | program |
| 16 | 2 | `ackSeq`: the host's acknowledgement, must equal `writeSeq` | host |
| 18 | 2 | `ackSum`: the host's 16-bit sum of every byte of the entries in [`readSeq`, `ackSeq`) | host |
| 20 | 1 | `ackRequest`: the host writes 1; the program clears it when processed | host, program |
| 21 | 1 | `drains`: accepted acknowledgements this session | program |
| 22 | 2 | `cumWrite`: the running 16-bit sum of every byte ever recorded this session | program |
| 24 | 2 | `cumRead`: the same sum up to `readSeq` | program |
| 26 | 6 | reserved | |
| 32 | 11 C | entries; the lesson with sequence s lives at slot s mod C: the twenty sense nibbles packed as today, then one byte with the taught absolute action in the low nibble and the raw output the brain predicted in the high nibble ("he thought X, you said Y") | program |

Block size 32 + 3,300 = 3,332 bytes. **A full ring pauses learning**: when `writeSeq − readSeq == C`
no lesson is applied (the think continues, TEACH stays on, the clone flashes red instead of white
where a lesson would have been taken, bit 0 is set); an applied-but-unrecorded lesson can never
happen, so the replay of the records over the saved brain always equals the machine's weights.

**The handshake, hardened.** The host reads `readSeq`, `writeSeq` and the entries between them,
computes `ackSum`, writes `ackSeq = writeSeq`, `ackSum`, then `ackRequest = 1`. The program processes
a request in the main loop before any lesson: rejected if a chord hold is in progress (bit 3), if
`ackSeq ≠ writeSeq` (a lesson was recorded since the host read: bit 1, the host re-reads and retries),
or if `ackSum ≠ cumWrite − cumRead` (bit 2); otherwise `readSeq := writeSeq`, `cumRead := cumWrite`,
`drains += 1`, bit 7 set, bit 0 cleared. The host can therefore acknowledge only the exact unread
range with the exact content, never advance a pointer past lessons it has not read, and never skip. A
rejected request changes nothing. Every field is a plain byte the workbench can read and, for the
three host fields, write.

## 7. The teaching shadow, atomic

The chord's first frame (in the frame path) no longer copies; it sets `shadowRequest` (when teaching
is on, as today). The main loop, **before the think and before any lesson**, performs the whole
snapshot in one call (the weights, kind, education count, `writeSeq`, `cumWrite`) and clears the
request; the toggle at fifty frames sets `shadowRestoreRequest`, which the main loop honours the same
way. Lessons are applied only in the main loop and never while either request is pending, and the
interrupt never writes a weight, so a snapshot or a restore can never interleave with a lesson: a
saved brain is one learning state. Drain requests are rejected while a hold is in progress (section
6), so a restore can always rewind `writeSeq` and `cumWrite` to the snapshot without touching an
acknowledged range. A host reading the weights while the machine runs checks `writeSeq` before and
after the read; equal means no lesson intervened (the workbench pauses the emulator anyway).

## 8. The machine measures itself

CIA 2 timer A is unused by the game; it runs free (continuous, latch $FFFF) and the program reads it
around every think, every lesson, every snapshot or restore and every accepted drain: `profThink`,
`profLesson`, `profShadow`, `profDrain` (16-bit cycles, the latest) and their running maxima. The
raster bench (`bodyRasterMax`, `bodyOverruns`) stays. RAM comes from the symbol file. The score gaps
(`acc` of the winning row minus the runner-up) are recorded per think in a running minimum, mean and
maximum for the mood-scale question.

## 9. Hard gate 1: exact parity

The reference `tools/brain02_ref.py`: the pseudo-senses, the table interpreter, the forward pass, the
rule at the byte box, the two vocabulary maps, `brainHash`. It is checked against `bakeoff2.py`'s
encoders flag for flag on all 1,424 recorded blocks, and against `brain_golden.learn` at the 4-bit
box as `learn_ref` was. Then, on each candidate PRG through the test hooks (`brainTestIn`,
`brainTestMode` 0 senses / 1 a flag vector supplied directly, `brainTestRun`, `brainTestFlags`,
`brainTestH`, `brainTestAcc`, `brainTestOutput`, `brainTestAction`, `brainLearnRun`,
`brainLearnTestT`, `brainLearnTestP`, `brainLearnTestTook`, `brainLearnTestTrel`):

1. **Retina**: the flag vector byte for byte against the reference on every recorded block (the 231
   and the 1,424), on every candidate.
2. **Golden-1b**, regenerated for the byte mood (`golden-1b/forward-v2.json`, `lessons-v2.json`, the
   same cases, mood added directly): every case at its own width through mode 1, including the
   all-zero tie, the most positive and most negative accumulators at 128 inputs, positive and negative
   exact ties (first largest), −128 against −127, saturation at 127 and at −128 with the wrap cases,
   the no-op lesson, the mood add. The 128-input cases run on a parity build whose slot holds 128
   inputs (`tony-b02-p128`, not a deliverable).
3. **Vocabulary**: 40 golden cases (ten indices, `h` from dx > 0, dx < 0, dx == 0 facing right, dx == 0
   facing left) for the resolution (`brainTestOutput` to `brainTestAction`) and the translation
   (`brainLearnTestT` absolute to `brainLearnTestTrel`), and the round trip.
4. **Malformed slot**: each header field wrong in turn gives `brainKindNow` 0; kind 0 and kind 2
   still drive.
5. **A learned brain replayed**: the weights of Phase 2b's R1b and R0s runs loaded, the 231 and the
   474 blocks through mode 0, the machine's action equal to the reference's on every block.

Any mismatch stops the milestone with the evidence.

## 10. Hard gate 2: production-representative PRGs and their costs

Separate PRGs `tony-b02-a` (R1b, V), `tony-b02-b` (R0s, V), `tony-b02-drel` (R0, V), `tony-b02-dabs`
(R0, absolute), built by the same generator from the same code with the retina table, the input
count and the vocabulary byte as data; the diagnostic pair differs by the vocabulary byte alone and
the report says so. For each: exact PRG size and sha256; the header bytes; n; weight bytes; mood
bytes; slot bytes; padding before the marker; retina table bytes and interpreter code bytes; the
flag vector's RAM; the shadow's RAM; the ring's RAM; the remaining headroom in the vacated region and
in the code region; cycles per think, per lesson, per snapshot, per drain (latest and maximum over a
curriculum episode); raster maximum and overruns over the bench; the score-gap statistics; capacity.
Pass: zero overruns, raster maximum at or under 230, the think and the lesson inside one frame of
main-loop time, the snapshot out of the frame path. Memory claims are verified against the symbol
file and the constants (section 13).

## 11. Hard gate 3: TEACH end to end on BRAIN02

`tools/teach_demo.py` repeated on each candidate, the real control path (the port, the chord): boots
kind 0 and follows; TEACH entered by the flag and by the chord; the stick drives him through the
real physics; lessons change BRAIN02 weights and the education count; the first lesson makes him
kind 1; behaviour visibly changes (he keeps walking on his own brain where the follow rule would
stop); TEACH exits and the learned brain drives; the slot is dumped (the saved brain) and, on a fresh
boot, loaded back: behaviour persists; a fresh boot of the untouched PRG forgets. Inference and
learning are the machine's; the harness only pokes the stick and reads memory.

## 12. Hard gate 4: save, drain and reuse, and the equivalence

The scripted teacher (`curriculum.py`'s port driver, deterministic on a deterministic emulator)
teaches from zero on a candidate PRG for at least 3 C lessons with the harness draining whenever the
ring holds at least 200: after every drain the drained records are replayed by the reference over the
brain as saved at the previous drain, and the result must equal the machine's weights byte for byte
(hashes compared); the machine continues from those weights; the education count runs across cycles.
Then the equivalence: the identical teaching script, once with no drain (fewer than C lessons) and
once split across at least three drains, must end in byte-identical weights, education count and
`brainHash`. Failure is a hard stop.

## 13. The memory map, checked

`$C000`–`$C3FF` is the game's screen page 0 (screen data to `$C31F`, sprite pointers at `$C3F7`; two
free sprite slots of 64 bytes at `$C320`), so **the "kilobyte under the screen" is not available** and
is not counted. Not a plan-changing contradiction: the vacated region `$863f`–`$9fff` (6,593 bytes)
must hold the ring (3,332), the shadow (10 n + 8: R1b 648, R0s 618, R0 568) and the code's growth
(the slot's 34 + 10 n replacing 280, minus the 276 bytes of multiply table and expansions retired,
plus the table, the flag vector, the pseudo-senses and the new code, estimated at 1,300 to 1,800 in
all); the estimate leaves about 800 to 1,300 bytes, and the actual figures are gate 2's.

## 14. Gate 5, mirror pairs, with attribution

Under the relative vocabulary a scenario and its mirror should both pass or both fail. A split is
counted, and attributed: it is a decoder defect (a fail) only if the builder and the scripted teacher
do not split on the same pair; a split shared with them is the room's asymmetry (the training column's
wall, the ladder columns, a one-pixel landing) and is reported as such.

## 15. Checkpoint C: the playable deliverables and the integration contract

The four PRGs in `deliverables/prg/minimal64/`, each an ordinary loadable C64 program; per PRG a JSON
descriptor (`deliverables/bakeoff/workbench/<name>.json`) generated from the symbol file: filename,
sha256, engine commit, marker, layout, version, every address the contract names (weights and their
length, `brainOutput`, `brainAction`, the applied action, `brainTaught`, `teachMode`, `teachHold`,
`brainThinks`, the ring's fields, the shadow status, the flag vector and its length, the accumulators
and their representation, the raw sense block and its frame stamp, the room and seed bytes, the
flash and status bytes, the profiler fields), and the three lists the contract requires: what the host
may read (observation), the exact research-only writes (the ack fields, teachMode, the slot for load
and reset, the seed bytes) and what must stay inside the machine (the think, the flags, the weights).
`WORKBENCH-INTEGRATION.md` states the same in prose with the export and drain procedures, the owner's
five-step test on the existing Akalabeth workbench, the session-trace schema (what can be derived by
observation plus explicit research events), the recommended first non-holdout scenario, and the
resource ledger. No holdout scenario is built into any PRG or named as a preset.

## 16. Phase 4, written now, not run in this milestone

After the owner's first non-holdout human session: the old 24, the shadow 16 and the sealed goal 8
under the strict rule, per bucket, with time to goal, for A, B, the pair, the extended teacher, the
builder, follow and zero; lessons to competence from zero with the scripted teacher and the same after
a save and reload; the generalisation gap on the 474 split into coverage misses (states never shown)
and representation misses (shown, still wrong); mirror-pair consistency as a count with attribution;
the goal senses as flags with `LESSON2` at 14 bytes and the reference vector switched by the
interface's published rule (`playerAway` selects the route vector), verified by a scenario with Tony
away and the ladder behind the clone; the budgets at both layouts. Behaviour is the primary outcome;
a valid solution unlike the teacher's earns credit; "within two of the teacher" is a comparative
target, not a freeze condition. Human sessions score from zero weights, with candidate order
counterbalanced, and record wall-clock time, corrections, time to visible improvement and
persistence after release and reload; the measured noise model comes from them, and any rule
refinement is pre-registered against it afterwards.

## 17. Predictions, written now

The pre-step: R1s fits everything with margins between R0s's and R1b's and learns the 474 under V in
500 to 700 lessons; it will not clearly dominate both. Gate 1 passes on the first build or fails on a
sign-extension or tie detail that the golden extremes catch. Gate 2: think under 12,000 cycles for
R1b (about 0.6 frame) and under 9,000 for R0; lesson under 3,500; snapshot under 8,000; drain under
500; raster maximum unchanged at 188 on the bench; PRG sizes within 1,800 bytes of today's 49,348.
Gate 3 passes with a lessons-to-climb number near the 36 of E5 for the pair and lower for A and B.
Gate 4 passes byte for byte, because the ring pauses rather than drops.
