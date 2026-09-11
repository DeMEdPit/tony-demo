# BRAIN02.5: pre-registration of the bounded terrain-observability experiment

Written and committed before any BRAIN02.5 alias census, any design choice among the candidate terrain
concepts, any line of BRAIN02.5 machine code, and any measurement. It fixes the question, what is
frozen, how each claim will be tested, what would count as a failure, and what is predicted. Results go
in separate documents; this one is not edited once results exist.

Baseline verified first, in `BASELINE-VERIFICATION.md`: engine commit
`3e12f0e19d69f9d37e1b95beafa9aa3368511cd0`, Candidate A
`ae6ce5244478532c5ec581c9e24a30bea0743c68b2dd7cc7ff9f3017bc3e594d`, the four BRAIN02 gates green, the
preserved human brain absent from this repository. Branch
`claude/brain025-terrain-observability`.

---

## 1. The question

A person played freely and built arbitrary obstacle courses for a blank Tony: stacked bricks, gaps,
pockets, obstacles one and several bricks high, jumps that need a change of direction, traps, routes
toward the player, routes onto the ladder. The reading that came back is that the limit is not the size
of the brain but how little of the terrain Tony can see. He needs more eyes before he needs more brain.

The question this experiment asks, and the only one it asks:

> **How much more reliably can the same learner be taught, when the smallest useful increase in local
> terrain observability is added to the sensed state?**

The learner is held fixed so that any difference is attributable to observability alone. Anything that
would answer the question by making Tony cleverer rather than better-sighted is out of scope, listed
in §14.

## 2. What is frozen

None of the following may change. If a machine-level bug forces one to, the experiment stops and the
bug is reported rather than worked around.

* The **ten-action reference-relative vocabulary**: idle, toward, away, up, down, jump, jump toward,
  jump away, build toward, build away; `h = +1` when `refDx > 0`, `-1` when `refDx < 0`, else the
  clone's facing from the same block; resolved once per think from the block thought on; the same map
  translating a human's absolute press into the taught relative action.
* **Byte weights**, ten rows, the box -128..127, saturating.
* **The rule**: the mood-free prediction `p`; no lesson when `p == t`; otherwise `+1` on row `t` and
  `-1` on row `p` at every set input, saturating.
* **Tie-breaking**: the first largest accumulator wins, outputs scanned 0 to 9.
* **Accumulator semantics**: `acc[o] = mood[o] + sum of w[o][i] over the set inputs`, 16-bit signed.
* **The meanings and the order of the existing 64 R1b inputs**, exactly as Candidate A defines them.
* **Machine-side inference and learning**: both stay on the C64. No cognition moves off the machine to
  meet a timing or memory budget. If it will not fit, that is the result.
* **No hidden layer, no recurrence, no persistent memory beyond the weights.**

The existing BRAIN02 tests must keep passing unchanged. `tools/brain02_ref.py check` and all four
`tools/brain02_test.py` gates on the four BRAIN02 PRGs are re-run at the end of the experiment and
reported. Any change in them is a failure of the experiment, not a new baseline.

## 3. What BRAIN02.5 may change

* **Additional inputs appended after input 63**, and only observations of the world (§6).
* The slot's marker, its layout byte, its retina id, its width, and the lesson record's format, all
  under new names and an explicit version (§10, and the table in `BASELINE-VERIFICATION.md` §6).
* The study build's **blank behaviour** (§4), **teaching control** (§5) and **clone spawn** (§7).

## 4. Blank Tony must be blank

Candidate A inherits kind 0, a hand-written follow rule that drives the clone whenever the brain is
absent or malformed. For a study of what a person can teach from nothing, that rule is a confound: a
blank Tony that already walks toward the player is not blank.

**Pre-registered requirement.** In the BRAIN02.5 study build, a slot of all zero weights produces a
normal forward pass, every accumulator equal, and the existing deterministic tie rule picks output 0,
IDLE. There is no fallback rule and no replacement hand-written behaviour. Cosmetic idle animation is
allowed because it is not an action: it must not move him, must not change his sensed state beyond the
animation frame, and must never be a taught or recorded action.

**Proof, on the machine, not by reading the source.** Boot the study build with a zero brain; over at
least 600 frames with the player moving, record: every accumulator equal to every other on every think;
`brainAction` 0 on every think; the clone's X and Y never changing; the joystick byte the brain writes
never non-zero. The historical fallback stays untouched in the frozen BRAIN02 builds.

## 5. The teaching control: a dedicated key, not a chord

The joystick chord must not carry teaching in this build. Down+Fire is the lay/build verb, Up+Fire is
the step-up verb used constantly while teaching, and an Up long-hold toggle misfires near the ladder.
All existing joystick and body controls are preserved exactly: nothing is removed, nothing is
repurposed, step-up stays.

**Pre-registered choice.** A dedicated C64 keyboard toggle, provisionally **T** (keyboard matrix row 2,
column bit 6). Scanned in the main loop, with interrupts held off for the scan, by driving CIA 1 port A
as output with the row mask, reading port B, then restoring the port to input before releasing
interrupts. Its rules:

* it changes teaching mode only, on the key's rising edge;
* it is never a gameplay action and never reaches the physics;
* it never becomes a lesson, and the frame it toggles on produces no lesson;
* mode transitions leak no stale decision: the action in flight is discarded on both edges, as the
  BRAIN02 chord already does through the shadow and the decoder guard;
* the workbench may still drive the published `teach_mode` directly.

If literal T proves unusable, another unused key is chosen and the reason is stated in the results. The
brief asks explicitly whether keyboard polling disturbs the joystick; this is tested rather than
argued, in both directions:

1. with the key scan running every frame, replay a fixed joystick script and compare the clone's and
   the player's frame-by-frame positions against the same script on a build whose scan is compiled out:
   they must be identical;
2. hold each of the five joystick directions and fire in turn while pressing keys in the scanned row,
   and confirm no phantom toggle and no phantom direction.

Verified in Minimal64 through the harness, and in VICE.

## 6. What a new input may be

Every appended input is an **observation of the world**. A feature that encodes an answer is
disqualified, whatever it would do for the numbers. Concretely, an input may report what is at a place
relative to Tony; it may not report what to do, where to go, whether to jump, whether to climb, which
way the player is, or whether a route exists. The reference vector stays what it already is: the
player's offset, senses 1 and 2, which BRAIN02 already publishes.

The test applied to each proposed input, and recorded for each: *could this be computed from the room
and Tony's pose alone, by someone who did not know the task?* If not, it is out.

## 7. The canonical study spawn, and one room

**Spawn.** The clone starts in a stable lower-left region near the far-left pillar, on the floor,
clearly separated from the ladder, with room for idle animation and most of the room left free for
courses. The room's interior is columns 5 to 34 with the floor at row 23; the ladder hangs at columns
33 to 34. The canonical spawn is chosen in columns 6 to 9 and reported exactly. Player Tony keeps his
normal starting and falling behaviour.

The result must not depend on one coordinate. A small set of nearby left-side starts is tested and
reported separately: the canonical X and at least four neighbours within a few pixels each side,
through the same gauntlet, reporting any scenario whose outcome changes with the start.

**One room.** No second room, no clone room transition, no cross-room reference semantics, no
multi-room navigation or memory, no room identity, no world map. The study target is whether a person
can teach a blank Tony to negotiate arbitrary local obstacles and reach the player at varied positions
inside this room, including when the player is on the ladder. The ladder is one useful visible
destination among others and is not the task. "Reach the player" is never hard-coded, sensed, or
rewarded. The sealed goal senses (`GOAL-SENSES.md`) and the sealed goal holdout
(`goal-holdout.json`) are not opened, read, or used, and the sealed Phase 4 sweep is not run.

## 8. Step C: the alias census

An alias claim has to be measured, not asserted. Both halves are measured on the machine.

**Definition 1 (observation alias).** Two machine states are *R1b-aliased* when the published BRAIN02
64-input flag vectors are identical bit for bit. The vectors come from the machine's own published
sense block through the build's own retina, not from a model of it.

**Definition 2 (consequence).** For a state and each of the ten actions, the machine is run forward a
bounded horizon with that action applied for one think period and a fixed neutral continuation after
it. The outcome is classified from Tony's own position and state, by rules fixed here:

* `ADVANCE` - net horizontal displacement of at least one character column in the direction of the
  reference, ending supported (on ground or on a ladder);
* `CLIMB` - ends at a strictly higher character row, supported;
* `DROP` - ends at a strictly lower character row than it began;
* `BLOCKED` - supported, no net column change, no row change.

**Definition 3 (consequential alias).** An observation alias is *consequential* when the outcome
classification differs between the two states for at least one action: an action that ADVANCEs or
CLIMBs in one and DROPs or is BLOCKED in the other. This is the operational form of "competent
behaviour would require different actions", and it is decided by the machine, not by a policy anyone
wrote.

**The state set.** Courses are built the way a person builds them, on the game's own grid: 2x2 bricks
at columns 5+2i and rows 21-2k, written as the four screen codes the build verb writes ($50 top left,
$51 top right, $52 bottom left, $53 bottom right), which the existing materials table already makes
wall. The census sweeps a family of local geometries at a fixed set of poses: flat ground; a gap of
one, two and three columns; a gap with the far side level, higher, and lower; obstacles one, two,
three and five bricks high; an obstacle with and without a standing surface on top; a one-column
pocket; a covered pocket; a ledge with a drop beyond; each mirrored left and right; each with the
player placed at several positions including on the ladder.

**What is reported.** The number of distinct 64-bit observation vectors; the alias classes with more
than one distinct terrain; for each, how many are consequential by Definition 3; and the census
broken down by geometry family, so that the extension in step D can be judged against named classes
rather than a single total.

**Falsification.** If few or no consequential aliases are found, the reading that started this
experiment is wrong, and that is the result. It will be reported as such, without redesigning the
architecture to rescue the hypothesis.

## 9. Step D: the extension

The smallest practical local terrain extension that resolves a meaningful share of the consequential
aliases found in step C. Concepts named in the brief as candidates to investigate, not as
requirements: a gap immediately ahead; safe floor or landing beyond a gap; terrain two columns ahead;
terrain three columns ahead; obstacle height; the local vertical profile; pocket and trap geometry;
landing height relative to Tony. A compact C64-native local terrain retina is preferred over a scatter
of special cases.

The design is chosen by the census, on the record: each candidate is scored by how many consequential
alias classes it separates per input added, and the choice and the rejected alternatives are both
reported. What remains aliased after the extension is reported too.

## 10. Additive compatibility, the slot and the lesson record

* Inputs 0 to 63 keep their meanings and their order exactly. Nothing is renumbered. New terrain
  inputs are appended from index 64 upward.
* The slot carries a new marker `BRAIN025` and layout byte 3, so neither kind of slot can be loaded
  into the other build; the malformed check rejects it and the build falls back as it already does.
* The lesson record is explicitly versioned. It must record everything an independent implementation
  needs to reconstruct **every** input, old and new, deterministically, with no hidden browser state and
  nothing that has to be recomputed from a room the replayer cannot see. Whether that means recording
  the new terrain observations in the entry, or the raw cells they come from, is decided in step E and
  reported with the reason.
* The existing atomicity is preserved: a lesson is recorded and applied together, or neither. A full
  ring pauses learning; it never applies an unrecorded lesson. The drain handshake keeps its monotonic
  sequence and validated acknowledgement of a specific range.
* Ring capacity may fall below 300. It will be reported, not defended.

## 11. Step F: the migration gate

A deterministic migration tool takes a BRAIN02 brain to a BRAIN02.5 brain: per action row, the
original 64 weights copied unchanged in order, then a zero weight appended for every new input; every
other compatible behavioural field copied explicitly and named in the tool, not inherited by accident.

**Acceptance: zero prediction mismatches caused by migration.** The migrated brain must choose the
same action as the original wherever the old observation interface applies, on

* every golden forward and lesson case;
* the full 1,424-block recorded corpus and the 474-block teacher-visited union;
* Phase 2b's learned weights;
* representative machine scenarios run on both builds;
* the preserved human brain `b23df474…`, education 300, if it is handed over.

The exact mismatch count is reported whatever it is. If zero is not reached, the experiment STOPS at
step F and explains precisely why. The original brain is not weakened, reinterpreted, retrained or
"upgraded" to make the gate pass, and the 300-lesson brain is never overwritten or replaced: a
migrated copy is a new, separately named file beside it.

## 12. Step G: replay and resources

**Replay.** A machine lesson stream, drained through several ring reuse cycles, replayed by an
independent reference implementation, must give the same brain bytes as the machine's own, including
the behavioural hash and the education count, exactly as BRAIN02's drain gate already requires.

**Resources, reported exactly, not approximately:** input count; brain slot bytes; weight bytes; PRG
size; lesson entry size; lesson ring capacity; the RAM map and the code headroom; the distribution of
how many inputs are active at once; think cycles minimum, mean and maximum; lesson and update cycles;
the accumulator bound; raster and frame behaviour with overruns counted; snapshot and shadow cost.
Cognition does not move off the C64 to satisfy any of these.

## 13. Step H: the gauntlet diagnostic

A small **non-sealed** diagnostic set inspired by the free-play gauntlet. It is not the sealed Phase 4
holdout and does not touch it. Candidate A and BRAIN02.5 are compared on: a one-high obstacle; a taller
local obstruction; a gap with a landing; a pocket or trap; an obstacle needing a jump and a change of
direction; mirrored variants of each; the player on and near the ladder; and small variations in the
clone's starting position.

Measured separately, not merged into one score:

1. consequential aliases resolved, by class;
2. representability: whether a weight setting exists that fits each scenario's required actions;
3. lessons to competence;
4. behaviour after later, unrelated teaching;
5. how much player proximity or shepherding is needed;
6. regressions against BRAIN02.

Every architecture change made during the experiment is recorded with the measurement that prompted
it. Repeated quiet tuning against the gauntlet is not allowed; the record must show each change.

## 14. Non-goals

Out of scope, and not to be introduced to rescue any result: a hidden neural layer; recurrent state;
persistent memory; the sealed goal senses; an explicit reward function; a route planner; pathfinding;
a second room; a moving ladder; block-derived world variation; procedural room generation;
browser-side inference; browser-side learning; Solidity; the NFT renderer; Brain Scope styling; mobile
UI; final Commons logic. The experiment ends at step I and declares nothing final.

## 15. Predictions

Recorded now so they can be wrong.

1. **Consequential aliases exist and are concentrated.** More than half the consequential alias classes
   will come from two families: a gap ahead that is invisible until Tony is over it, and obstacles
   distinguished only above the head row. Failure: aliases spread evenly across all families, or too
   few to matter.
2. **Gap-ahead is the single most valuable input.** One input reporting that the cell ahead has no
   floor below it will separate more consequential classes per bit than any other single candidate.
3. **The extension is small.** Eight to sixteen appended inputs will resolve most consequential
   classes; more than twenty-four will not be needed. Prediction fails if fewer than half the classes
   are resolved at twenty-four.
4. **Migration is exactly clean.** Zero mismatches. There is no reason for any: appended zero weights
   contribute nothing to any accumulator, so the argmax is untouched. If this fails, the cause is an
   implementation defect and the experiment stops at step F.
5. **The machine holds.** Think stays inside one frame of main-loop time at the new width, and the
   raster behaviour is unchanged with zero overruns. The slot grows by ten bytes per appended input;
   the ring capacity falls roughly in proportion to the lesson entry's growth.
6. **Teaching improves, and not uniformly.** Lessons to competence fall on gap and obstacle-height
   scenarios and are roughly unchanged on the flat-ground and ladder scenarios that BRAIN02 already
   handles. Prediction fails if BRAIN02.5 needs more lessons anywhere it did not before.
7. **Blank is blank and the key is clean.** Zero weights give IDLE on every think with no movement, and
   the key scan changes no frame of a replayed joystick script.

## 16. Order of work, and where this stops

A. baseline verified and frozen - done before this document.
B. this pre-registration, committed before anything else.
C. the alias census.
D. the extension designed from it.
E. implementation on the machine.
F. the migration gate.
G. replay and resource gates.
H. the gauntlet diagnostic.
I. the deliverables packaged.
J. STOP.

Checkpoints are committed after each stage that succeeds. If a major hypothesis fails it is reported
as a failure; the architecture is not redesigned around it. At J: no Solidity, nothing merged over
BRAIN02, nothing deployed, and no claim that BRAIN02.5 is the final Chamber v2 architecture.

---

## Amendment 1, before any census result exists

Made after the rollout calibration on the frozen Candidate A build and before a single scenario of the
census was measured or recorded. Nothing here is chosen with knowledge of a result; the calibration
measured only how far Tony travels per decision, on flat floor, a one-high step and a two-high wall.

1. **The rollout holds the chosen output for two think periods, not one.** The think period is four
   frames, and one period displaces Tony by four to eight pixels, less than the eight-pixel character
   column the outcome rules are stated in. Two periods (eight frames) put the displacement above the
   resolution of the measurement. The neutral continuation is fifty-two frames of idle, enough for a
   jump arc and its landing. Every scenario and every action gets exactly the same rollout.
2. **Two outcome classes are added** to the four of section 8, for completeness rather than as new
   ideas: `RETREAT`, supported and at least one column away from the reference, and `AIRBORNE`, ending
   neither on ground nor on a ladder. `DROP` keeps priority over both.
3. **The pose is placed at the surface's natural resting Y** (the floor's is 206, a brick top's is
   sixteen pixels above it), so that no scenario begins with a settling transient that the rollout
   would then measure.

The calibration output that motivated 1 and 3 is in `census-calibration.txt`.
