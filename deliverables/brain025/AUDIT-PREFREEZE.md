# Perception Chamber: final pre-freeze audit

Diagnostic pass only. **No PRG bytes changed** - `tony-b025-a-vis3.prg` is still 52,098 bytes,
sha256 `a9efe9d00afd0cfc9453acbcb0fe6b0faa8fe6f7f83f43635c2bd4ee80ef12ec`. Every frozen and research
artifact is untouched. The only code changed is `tools/brain025_test.py`, which is host-side tooling:
the descriptor now publishes the world materials table, and the drain gate reports why a handshake was
refused. Raw data and the scripts that produced it are in `deliverables/brain025/audit/`.

---

## 1. The one-step education rollback

**No correctness violation. The whole transaction rolls back atomically.** The invariant holds in its
stronger form: a lesson is recorded and applied together, and it is un-recorded and un-applied together.

### What the mechanism is

`lessonAck` cannot decrement anything - it writes only `lessonStatus`, `lessonReadSeq`, `lessonCumRead`,
`lessonDrains` and `lessonAckRequest`, and the `badSum` branch writes only the status bit. The decrements
come from **`teachShadowRestore`**, and in Candidate A they are the chord toggle's designed behaviour:
down+fire held `TEACH_HOLD_FRAMES` (50) toggles TEACH, takes back the brick the press laid, and - in the
engine's own words - *"the lessons the press taught, if any, are forgotten"*. The press was a mode
command, so it is not allowed to leave teaching behind.

### What it reverts, measured on Candidate A

One chord hold, one lesson landing inside it, then the toggle:

| | education | writeSeq | cumWrite | kind | writeSlot | writePtr | weights sha256 | nonzero |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| before the hold | 0 | 0 | 0 | 0 | 0 | 37152 | `9e132485d5107211` | 0/640 |
| mid-hold | **1** | **1** | 327 | 1 | 1 | 37163 | `c7e08e0f3dcc6fce` | 38/640 |
| after the toggle | **0** | **0** | 0 | 0 | 0 | 37152 | `9e132485d5107211` | **0/640** |

Exactly the reported `education_count -= 1` and `write_seq -= 1`, and the weight block returns
**byte-identical**. `teachShadowRestore` rewinds weights, `brainKind`, `brainEducation`,
`lessonWriteSeq`, `lessonWriteSlot`, `lessonWritePtr` and `lessonCumWrite` together, clears the
ring-full bit, and zeroes `brainAction` so the next think decides with the restored weights.

* **The neural weight update is reverted.** 38 changed bytes, all of them back.
* **The lesson bytes are abandoned in place, not erased.** The 11 bytes stay in the ring slot, but
  `writeSeq`, `writeSlot` and `writePtr` all point back at that slot, so the next lesson overwrites it,
  and the readable range `readSeq..writeSeq` excludes it. Unreachable, reused, and `cumWrite` is
  consistent with the empty range.
* **There is no learned mood state to revert.** `brainMood` is 10 signed bytes read by `brainForward`
  and written by nothing in the learning path - measured `[0]*10` before teaching, after 7 lessons, and
  after a rollback. The shadow covers the 800 weight bytes, which is exactly the set learning changes.

### Why the host sees status 4

The rollback moves `cumWrite` and `writeSeq` underneath a host that has already read the range. Where
the host's acknowledgement lands decides which refusal it gets. Both were reproduced, and **both refuse
and reclaim nothing** - `readSeq` unchanged, `drains` unchanged, in every case:

| the host's acknowledgement | result |
|---|---|
| names a sequence number the machine no longer has | `status $02` **stale range** |
| names the current sequence number with the sum it took before the rollback | `status $04` **bad checksum** |

The status-4 case, measured: the host held sum `$0147`; after the rollback and one replacement lesson
the machine was back at `writeSeq 1` with its own sum `$013E`; the sequence numbers matched and the sums
did not. That is the handshake failing closed on a range that no longer adds up - it is the fail-closed
design working, not a fault.

### Throttling

**Not required.** The rollback is deterministic and was reproduced at full emulation speed. Throttling
only widens the host's read-to-acknowledge window, which makes the collision likely instead of rare, and
lets the intermediate `education - 1` state be observed at all.

### Does this exist in BRAIN02.5 / vis3

**Not reachable from play.** The chord is gone: `teachRoute` forces `teachHold` to 0 every frame and the
comment says so; TEACH is toggled by the T key. Every write to `shadowRequest` and
`shadowRestoreRequest` in the vis3 image writes **zero** - nothing sets either. Measured: a 120-frame
down+fire hold in TEACH leaves `teachMode` 1, `teachHold` 0, `shadowValid` 0, `shadowRestoreRequest` 0,
and the lesson kept.

Driven the way a **host** would drive it, the mechanism is intact and still exactly atomic in vis3:
education 4 → 10 → 4, writeSeq 4 → 10 → 4, cumWrite `$05F1` → `$0D82` → `$05F1`, weights byte-identical
to the snapshot.

### One host-facing hazard, reported and NOT fixed

`teachShadowRestore` does not consult `shadowValid`. Candidate A's caller checks it before setting the
request; a host that pokes `shadowRestoreRequest = 1` directly bypasses that check and restores an
**unwritten** shadow. At `$9200` the load image holds 781 of 800 nonzero bytes - relocated music data -
so the brain is replaced with that.

The safety net holds: `shadowKind` was never written, so `brainKind` becomes 0, `brainCheck` rejects the
slot (`brainKindNow` 0), and the clone idles rather than running garbage weights. Measured: `cloneX`
unchanged over 200 further frames, overruns 0. But `brainEducation` reads 0 while the weight block is
non-blank, so the slot is momentarily self-inconsistent, and a host exporting it would get a brain the
replay reference cannot reproduce from the lesson stream.

A guard is about five bytes (return unless `shadowValid` is 1). **Not implemented** - it changes
behaviour, and this pass is an audit.

---

## 2. The world materials table, published

`deliverables/brain025/workbench/tony-b025-a-vis3.json` gains a `world` block. **Nothing was moved or
renamed** - these are the addresses the engine already uses.

| what | address | length | index |
|---|---|---:|---|
| **`roomMaterialsBuffer`** - read this one | `$BE00` (48640) | 170 (`MAX_BG_CHARS`) | the **drawn** screen code, as it appears in the matrix after `translateRoom` |
| `materials` - the static source | `$583B` (22587) | 255 | the **original** character code, before `decodeRoom` remaps it |
| `roomCharsDecodingBuffer` | `$BF00` (48896) | 256 | original code → drawn code, rebuilt per room |
| `chamberLines` - the row table | `$5190` (20880) | 25 low then 25 high | the screen address of each character row |

Semantics: a bitfield per character. `$01` WALL (solid), `$02` LADDER (climbable), `$04` KILLING
(deadly), `$40` COLLECTIBLE (a pickup, not terrain), `$00` no material. The masks the engine itself
uses are published too: FLOOR `$01`, FAR `$03`, BOX `$46`, BOX_NK `$42`, OBJ `$40`.

**The live table cannot be derived by the host, and the descriptor says why.** `decodeRoom` keys it by
the room's used-character list, and the build demo then patches the codes it owns. On this build four
entries differ that way - **drawn codes `$50`-`$53`, the four cells of a brick the player or the clone
has laid**, which are WALL in the live table and which no original character code maps to at all. A host
deriving from the source file would treat every placed brick as empty air.

Hashes: the source table is part of the load image, so its hash is stable -
`1318fdeb246be49bbf46fa297db463d3f8ae45d85bbb859853e1309f340c09b6`. The live table is measured and
published per chamber; both chambers give
`b7200f562c6603f888fa639b8f0758abb0e16bf98c5a683a5c394221d661bef9`, because they share one
used-character list.

Measured facts the host should know about this level: only `$00`, `$01` and `$02` occur in the live
table. **No cell of this level is deadly** - KILLING is in the schema and in the source table, but none
of the characters carrying it are in this room's used-character list. COLLECTIBLE likewise does not
occur: the candle is drawn, but these rooms carry no static objects, so the object-materials pass has
nothing to patch. The seeded back wall's bricks are material `$00`, verified on the machine, so the
terrain probe, the senses and the brain cannot see any of them.

---

## 3. Far-field inactivity and proximity-dependent teaching

**I could not reproduce it. On the machine the clone is more mobile at long range, not less, and the
distance a curriculum was taught at made almost no difference.** Reported honestly, including the
things the data does support.

### Method

The player is walked to each distance with the joystick while the slot is still blank, so the clone
stands still during setup; the trained brain is loaded only then; teaching is off throughout; the terrain
is never touched. 50 think ticks per bin. Placement is read back before any row is trusted - three
earlier attempts at poking positions produced identical-looking rows across all six bins and were
discarded, because the physics block is swapped between the two bodies and a poked `physPlayerX` is
overwritten within one frame.

Three brains: the migrated `climbed-b02-a` (education 33), and a **matched pair** taught the same thing
- "step toward the player" - differing only in the distance bucket the lessons were recorded in. Both
reached **education 11**, with 56 and 58 nonzero weights.

### Results

| bin | gap | adx | thresholds set | climbed: IDLE / disp | near-trained: IDLE / disp | far-trained: IDLE / disp |
|---|---:|---:|---:|---|---|---|
| very near | −4 | 0 | 0/7 | 88.0% / +16 | 0.0% / −8 | 0.0% / −16 |
| near | +12 | 2 | 2/7 | 88.0% / +16 | 0.0% / +24 | 0.0% / +24 |
| middle | +44 | 5 | 5/7 | 88.0% / +60 | 0.0% / +32 | 0.0% / +44 |
| rest | +104 | 6 | 6/7 | 82.0% / +116 | 0.0% / +96 | 0.0% / +96 |
| far | +140 | 7 | **7/7** | 88.0% / +116 | 0.0% / +140 | 0.0% / +152 |
| max practical | +204 | 7 | **7/7** | 86.0% / +204 | 0.0% / +204 | 0.0% / +204 |

Every brain closes the distance in every bin. At maximum separation all three cross the whole room and
arrive at the player's X. Builds 0 and jumps flat (5-6 for the climbed brain, 0 for the trained pair) at
every distance. **Displacement rises with separation; IDLE does not.**

### Hypothesis by hypothesis

1. **Distance features saturating at long range - CONFIRMED, but it does not cause inactivity.**
   Sense 1 is a bucketed distance, and the buckets are the engine's own: `0: under 8px, 1: under 16,
   2: under 24, 3: under 32, 4: under 48, 5: under 64, 6: under 128, 7: 128 and more`. The interior is
   only 240 px wide, so bucket 7 covers **more than half the room**. Measured: at 140 px and at 204 px
   separation all seven `adx>=k` inputs are set and the climbed brain's accumulator vector is
   *identical* - `[16,0,0,-6,0,0,-10,0,0,0]`. Two separations 64 px apart are the same state. The clone
   therefore cannot modulate anything by distance beyond 128 px: he comes at you with the same
   commitment from across the room as from a body-length outside bucket 6. That is a real
   representational limit. It produces **uniform** behaviour, not absent behaviour.
2. **Training-distribution coverage - NOT SUPPORTED.** The matched pair is behaviourally near-identical
   across all six bins: IDLE 0.0% everywhere, raw output 1 winning everywhere, and the same
   displacement profile. The far-trained brain is no better in the far field and the near-trained brain
   is no worse.
3. **IDLE dominating far states through score ties - NOT OBSERVED.** Both trained brains show scores of
   the form `[-k, +k, 0, 0, …]` at every distance - never a tie - and IDLE is 0% at every distance. The
   climbed brain's high IDLE (82-88%) is **flat** across distance and is a property of its jump-based
   policy: the IDLE ticks are the airborne frames between jumps, which is why it displaces +204 px while
   idling 86% of ticks. **High IDLE is not inactivity.**
4. **still / lastAction hysteresis - no distance dependence found.** The `still` and `lastAction` inputs
   fire in near and far states alike; the active-input count *rises* with distance (14-17 near, 21-22
   far), so the far state is input-rich, not input-poor.
5. **Reference-relative action resolution - CONFIRMED, and it is the reason (2) failed.** The taught
   action is stored relative to the reference: raw output 1 means "toward", and `h` supplies the
   direction at decision time. One lesson therefore generalises across every separation for free. The
   action mix shows it directly - both brains run ~50/50 LEFT/RIGHT at very near, where `dx` oscillates
   through zero, and 100% RIGHT at maximum separation, where `dx` is firmly positive. **The relative
   vocabulary makes distance-bucket coverage nearly irrelevant for toward/away behaviour.**
6. **Terrain inputs changing with proximity - present but not causal here.** The terrain quantities are
   measured in the toward frame, so they do change as the player moves; the terrain was held constant
   and the behaviour still tracked separation monotonically.
7. **Other machine behaviour found:** the real near-field artefact is the opposite of the report. At
   gap −4 both trained brains **jitter** - LEFT 26 / RIGHT 24, net displacement −8 and −16 px - because
   `h` is always defined (it falls back to the facing bit when `dx` is 0), so "toward" never resolves to
   "stay". Near the player he oscillates; far from the player he walks decisively.

### Does human proximity make the learner easier to teach

**No measured advantage.** Both curricula reached education 11 and produced equivalent brains. What is
true is that near teaching is *self-limiting* in a way that feels more productive: the near bouts ended
early and often because the clone arrives and the state leaves the near band, so a human gets tighter,
faster feedback loops - 32 teaching ticks across 10 bouts, against 104 for the far curriculum to reach
the same 11 lessons. That is an ergonomics difference in the teaching loop, not a difference in what the
learner can absorb.

### So what would the tester's observation be

I did not reproduce it, so this is inference, labelled as such. The described sequence - *"after
teaching actions such as following, jumping or building, releasing the clone while the player remains
far away"* - mixes curricula, and interference is this architecture's documented standing negative:
retention falls **100% → 72%** on BRAIN02.5 after an unrelated later stream (98% → 54% on BRAIN02). A
follow response overwritten by later jump and build lessons would leave a clone with no toward-response,
and the near-field jitter above would still read as "he comes alive when I get close", because near
states activate a different, smaller input set (14-17 active against 21-22 far) and can survive when the
far response has been overwritten.

**That points at retention, not motivation.** Of the four categories asked about:

* **perception** owns the saturation: one extra band, or a second longer-range thermometer, would let
  separations beyond 128 px differ at all. Real, measured, and bounded.
* **retention** owns "he goes lifeless after I teach him other things". This is the standing negative
  and it is the best available explanation for the report.
* **memory** and **motivation/agency** are not implicated by anything measured here. **Nothing in this
  data supports adding intrinsic motivation**, and the clone is demonstrably *not* less behaviourally
  expressive at long player distance.

No wander, curiosity, random motion, exploration, reward, hidden state or scripted fallback was added,
and the old hand-authored follow rule was not restored. If the inactivity is real in play it is a
property of a learned policy that has lost its follow response, and the honest fix is retention, which
is architecture and out of scope here.

---

## 4. Provenance

| | |
|---|---|
| commit | `91def992d8a89b66fd7f8121846ce60157984061` (the audit's own commit is reported in the reply) |
| vis3 PRG | `tony-b025-a-vis3.prg`, 52,098 bytes |
| vis3 sha256 | `a9efe9d00afd0cfc9453acbcb0fe6b0faa8fe6f7f83f43635c2bd4ee80ef12ec` |
| PRG bytes changed | **none** |
| gates | descriptor, roomdata, transit, crouch, smoke re-run after the tooling change: all pass |
| reference | `brain025_ref verify` matches the pinned manifest; the canonical 244-lesson replay is byte-identical at 244/244 |

Nothing was implemented for retention, memory, reinforcement learning, intrinsic motivation, new room
navigation or Solidity.
