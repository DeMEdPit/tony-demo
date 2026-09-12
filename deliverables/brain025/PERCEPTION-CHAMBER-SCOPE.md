# Perception Chamber: technical scope and limitations

Canonical statement of what this generation is and is not. Every claim below is implemented and tested
on the machine; nothing here is aspirational, and no PRG byte was changed to satisfy this document.

| | |
|---|---|
| engine commit | `ad4bd1501fc61db2fde35c8f75fc5af3a29c3f1e` |
| PRG | `tony-b025-a-vis4.prg`, 52,104 bytes |
| sha256 | `355645a687dc244257a6e53be2a652b19a9f81a8ad9d6abc4e042a9e5ca4ea62` |
| gates | 16 gates, 95 checks, no failures |

Every earlier research and visual artifact is preserved unchanged, including the frozen
`tony-chamber.prg` and `tony-build.prg`, the hash-pinned research build `tony-b025-a.prg`, and the
visual candidates vis1, vis2 and vis3.

---

## 1. Research framing

Perception Chamber is **intentionally minimal and deliberately isolated**. It is not an attempt to build
the most capable agent a C64 can host in one release. The working principle is:

> add a mechanism only after a measured failure demonstrates why it is needed.

The question this generation isolates is narrow:

> What changes when a small learned C64 agent is given enough **local perception** to distinguish the
> situations a human is actually trying to teach it?

Every mechanism absent from Section 3 is absent **on purpose**, and stays absent until evidence names it.
On the evidence gathered here, the next architectural question is **retention and interference** - not
more perception, not memory, and not motivation.

---

## 2. What Perception Chamber contains

**A single-layer, linear, feed-forward learned policy.** 80 inputs by 10 outputs, evaluated as ten
integer dot products. The only nonlinearity in the whole model is the argmax that picks the winning
output; ties go to the lowest index. There are no hidden units and no activation function.

**80 binary input features**, computed on the machine each decision by a "retina" table (id 5, name T1,
241 table bytes) from **36 signed values**: the 27 published sense nibbles plus 9 derived pseudo-senses.
Each input is one threshold or comparison over one value - `still>=4`, `adx>=2`, `lastAction==0`,
`AND(ladderHere, refAbove)` and so on. Inputs 0-63 are BRAIN02's, entry for entry; 64-79 are the terrain
extension.

**10 outputs, decoded through a reference-relative action vocabulary.** The ten scores are action
candidates; the winning index is interpreted relative to `h`, the horizontal sign of the player's
offset (falling back to the clone's facing when that offset is zero). So a single taught lesson such as
"step toward him" applies on either side without being taught twice. The absolute actions are IDLE,
LEFT, RIGHT, UP, DOWN, JUMP, JUMP-LEFT, JUMP-RIGHT, BUILD-LEFT, BUILD-RIGHT.

**800 signed learned weights in an 834-byte BRAIN025 slot.** Layout: a 24-byte header (marker
`BRAIN025`, kind, layout version 3, input count 80, retina id 5, education count, vocabulary byte) at
offsets 0-23, then 10x80 = **800 signed weight bytes** at 24-823, then **10 mood bytes** at 824-833. Only
the 800 weight bytes and the education count change with teaching.

**The mood is frozen to zero and is outside this generation's cognitive design.** Each of the ten mood
bytes is a **signed per-output bias**: `brainForward` writes it straight into that output's accumulator
as the starting value, sign-extended - it is *not* a nibble scaled by sixteen, and it is *not* timing.
(The name was carried over from the Chamber's mural, where the render's mood lengthens the rests. In a
brain slot it means something else entirely.) Because it is added to the accumulator it shifts the
argmax, so it changes the action. See Section 5 for the invariant, why it is required, and the hash
semantics that follow from it.

**Online human-supervised learning, on the machine.** TEACH mode (the T key, or the host's flag) routes
the joystick to the clone; each lesson pairs the 27-nibble observation of one frame with the action
actually applied on the next. The rule is a perceptron correction: if the model already predicts the
taught action, nothing changes; otherwise the taught output's weight rises by one and the predicted
output's falls by one, **on every input flag that is set**, saturating at the byte bounds. There is no
learning rate, no momentum, no batching and no reward.

**Deterministic education and replay (LESSON25).** Lessons are 15-byte records in a 180-entry ring:
27 nibbles in bytes 0-13, then the taught action absolute in the low nibble of byte 14 and the
prediction as a raw relative output index in the high nibble. **Given a starting slot and an ordered
lesson stream, the resulting brain is exactly reproducible.** Proven end to end: the canonical
244-lesson session replays to a **byte-identical** 834-byte final slot with **244 of 244** recomputed
predictions matching the recorded nibble, against a hash-pinned reference
(`tools/brain025_ref.py` + `tools/brain02_ref.py`, pinned in `replay/MANIFEST.json`). The drain
handshake is checksummed and fails closed: a stale range or a wrong sum is refused and reclaims nothing.

**Local terrain perception (the BRAIN02.5 extension).** Seven terrain quantities - `tSafeRun`, `tGapW`,
`tFarRun`, `tObstH`, `tObstTop`, `tHead`, `tBackRoom` - are measured on the machine each decision by
reading the live screen through the room's materials table, in the **toward frame** (the direction the
reference lies in), each capped at 7 and published as sense nibbles 20-26. Sixteen ordinal thermometer
inputs are derived from them. The probe costs 4,416 cycles. This is **instantaneous local sensing**, not
a stored map: nothing survives the decision it was computed for.

**Short-context features, not recurrence.** Two engine-maintained counters are presented to the network
as ordinary inputs: `lastAction`, the action applied on the previous frame (inputs 46-55, one per
action), and `still`, a saturating count of how long the clone has been motionless (inputs 39-45,
`still>=1` through `still>=7`). They give a one-step action context and a bounded stillness duration.
**The network itself has no feedback path and no hidden state** - these are observations computed outside
it, exactly like the terrain quantities.

**Autonomous execution of the learned policy after release.** With TEACH off the clone is driven
entirely by the slot: the terrain probe, the retina, the forward pass, the action resolution and the
body all run without any human input. What he does is whatever was taught, including taught initiative
(Section 4). He acts in the lower chamber only; while the player is in the room above, the clone's turn
returns immediately.

**Cognition and learning run natively on the Commodore 64.** The terrain probe, the sense packing, the
retina, the forward pass, the action resolution, the learning rule and the lesson recording are all
6502 code in the PRG. **The host never computes an input, a prediction, or an action.**

**Browser instrumentation is observation plus a research control plane - never inference.** The host can
read everything (the slot, the ring, the senses, the scores, the chosen action, the screen, colour RAM,
the charset, VIC state, the row table and the materials table, all published in the workbench
descriptor) and can write a bounded set of research controls: the TEACH flag, the drain
acknowledgement fields, the ring capacity at boot, a whole saved brain into the slot, and the research
test hooks. It performs **no** inference and **no** learning of its own. "Observational only" would be
imprecise; "no browser-side cognition" is exact.

Everything the Workbench draws is a **rendering of bytes the machine published**. Its material-bits
grid, for example, is a host-derived visualisation of the live `roomMaterialsBuffer` and the screen
matrix that the descriptor points it at - the semantics are the machine's, the picture is the host's.
It is not a second world model and it is not browser-side cognition.

**A four-frame cognition period.** `brainPeriod` is 4: the clone decides once every four frames, about
12.5 decisions a second on PAL. The think costs up to 40,836 cycles and a lesson up to 40,066 - each
more than a single frame's 19,656 cycles of main-loop time, and both comfortably inside the four-frame
period's 78,624. Measured raster maximum 138 against a limit of 230, with **zero** overruns.

---

## 3. What Perception Chamber does not contain

Each of these is genuinely absent from the implemented model. None is stubbed, disabled or hidden behind
a flag.

* **No hidden neural layer.** One linear layer, inputs straight to output scores.
* **No recurrent neural state.** No output, accumulator or activation is fed back as an input. The
  `still` and `lastAction` features above are counters the engine computes and presents as observations;
  the network has no memory of its own.
* **No persistent episodic memory.** Nothing records that a particular thing happened at a particular
  place or time. The lesson ring is a transport buffer for the host, not a memory the clone consults.
* **No internal room map or world model.** Terrain is re-read from the live screen every decision and
  discarded. He holds no representation of the room beyond the current 80 inputs.
* **No path planning.** No search, no waypoints, no route. Movement is one local decision at a time.
* **No explicit multi-step goals or intentions.** There is no variable anywhere that means "I am trying
  to reach the ladder".
* **No intrinsic motivation.** This is the distinction that matters most for description:
  **autonomous execution exists; intrinsic drive does not.** He can independently execute behaviours
  that were taught to him - including a taught initiative that fires from a stationary state - but
  there is no separate mechanism telling him to explore, to build, to seek novelty, or to pick
  something to do merely because nothing else is happening. Everything he initiates, he was taught to
  initiate.
* **No reward or reinforcement learning.** There is no reward signal, no value estimate, no return, no
  policy gradient. The only learning signal is a human's demonstrated action.
* **No curiosity or exploration drive.**
* **No scripted wander or follow fallback in operation.** An untaught brain does nothing: every
  accumulator is equal, the argmax picks index 0, and IDLE is the result - verified as a gate. *Honest
  detail for anyone reading the bytes:* the original hand-authored follow rule (`cloneFollow`) is still
  present in the image but is **unreachable** - no code path reaches it, and the comment in the source
  says so. It never executes, and no behaviour in this generation comes from it.
* **No autonomous self-training.** Weights change only while TEACH is on and a human is driving. He
  never modifies himself unattended.
* **No robust skill consolidation or anti-interference.** There is no rehearsal, no consolidation, no
  weight protection, no per-context gating. This is the measured boundary of Section 4.
* **No cross-room navigation intelligence.** The clone's autonomy is confined to the lower chamber.

---

## 4. Measured limitations

### Retention and interference - the strongest identified boundary

**Later education can overwrite earlier learned behaviour.** This is the clearest limit of the
generation and the next architectural question.

* **Measured study result: BRAIN02.5 retention after unrelated later teaching falls from 100% to 72%**
  (BRAIN02, without the terrain extension, falls from 98% to 54%). More perception reduced the damage
  but did not remove it.
* **Human session observation:** the first human teaching sessions showed strong follow/build
  interference. Recorded as a qualitative report from play, not as a measured rate.
* **Initiative experiment (measured):** a JUMP initiative was successfully taught from stationary
  states - autonomous IDLE fell from 66% to **0.0%**, jumping on 100 of 100 autonomous ticks with the
  human completely still - and the same six lessons **destroyed the previously learned follow
  behaviour**, cutting displacement across the room from +100px to **+0px**. A TOWARD arm preserved
  follow (+112px) but installed no initiative; a BUILD arm lost both.

**Why it is structural, not a tuning problem.** The perceptron update moves the weight of *every* input
flag that is set. At the initiative lessons only 6 to 8 of the 20 to 22 active inputs were
`still`/`lastAction` features; the other 14 were shared with the follow behaviour's state (`bias`,
`onGround`, `floorBelow`, `facingRef`, `dx>=1`, `adx>=1`, `adx>=2` and five terrain inputs). A single
linear layer has no way to make a lesson apply *only when still*: the update is necessarily spread
across all co-active inputs, so two behaviours that share inputs cannot be separated.

### Initiative

**Do not describe the current model as incapable of autonomous activity.** BRAIN02.5 **can** be taught
to initiate behaviour from a still state, using only the existing `still>=N` and `lastAction==0`
features, and this was demonstrated. The limit is not capability but coexistence: initiative lessons
interfere with other learned skills under the current update rule.

Two honest caveats. The demonstration is one arm of one experiment - six lessons, one base curriculum,
one room, one seed - so "initiative is learnable" is proven while "Tony has initiative" is not a
property of any shipped brain. And `still` rarely exceeds 3 in autonomous play (mean 1.2), because the
clone's own residual drift resets the counter, so a high-`still` policy seldom reaches the state it was
taught in without deliberate teaching.

### Proximity

**Human proximity is not required for learning, and should not be described as such.** Matched near and
far curricula, taught the same action and reaching the same lesson count, produced behaviourally
near-identical brains across every distance bin tested. No capability advantage for close teaching was
demonstrated.

It is fair to say that close, incremental teaching may give a **better human teaching experience** -
near bouts end sooner and more often, so the human gets tighter feedback loops. That is an **ergonomic
observation about the teaching loop, not a demonstrated neural requirement.**

### Distance perception

Horizontal relative distance is bucketed and **saturates at the far bucket, 128 px and above**. The room
interior is 240 px wide, so more than half of it collapses into one observation: two separations 64 px
apart produce an identical input vector and identical scores. Tony distinguishes "far" but nothing finer
beyond that threshold, and cannot modulate anything by distance past it. Vertical offset is likewise
bucketed and saturates.

**This did not prevent the tested follow behaviour from crossing the room.** Every brain tested closed
the distance from maximum separation, and measured displacement rose with separation rather than falling.

### Sequence and planning

Long behaviours - climbing, building a step and going up it, crossing the room - **emerge from chained
local decisions**, one every four frames. There is no explicit representation anywhere of the form "I am
currently executing the skill climb-the-ladder", no step counter and no plan. What looks like a sequence
is a series of independent decisions whose inputs happen to lead into one another.

### Memory

Tony **does not accumulate a remembered spatial map, and does not remember previous attempts**, except
insofar as those facts are represented indirectly in the current inputs or in the weights that teaching
has already shaped. The weights are the only thing that persists, and they encode a policy, not a
history.

### Determinism, scoped precisely

The learning rule and the replay are deterministic: **the same starting slot and the same ordered lesson
stream always produce the same brain**, byte for byte. This is not the same as saying the same human
play produces the same brain - whether a given frame yields a lesson at all depends on the main loop's
timing, and a missed pairing is counted rather than guessed at (`lessonNotPaired`). Provenance rests on
the recorded lesson stream, not on reproducing a human's hands.

**The education count is not an authority.** It is a counter, and it is **not inherently monotonic under
every historical control path**: the teaching shadow's restore rewinds it along with the weights and the
ring's write side, which is exactly what a chord toggle in the older Candidate A build did by design
(measured: education 1, then 0, with the weight block byte-identical to before). **Replay authority is
the ordered lesson stream**, against a named starting slot - never the counter alone. Read the education
count as a label on a brain, not as a proof of how it got there.

---

## 5. Canonical state and hash semantics

The Workbench found, and this was reproduced on the machine, that two slots can report the **same
learned-policy hash while producing different actions** if their mood bytes differ. One byte at slot
offset 833 turned a resolved IDLE into BUILD-LEFT with the policy hash unchanged. The resolution for
Perception Chamber:

### The zero-mood invariant

**A valid Perception Chamber canonical brain has `brainMood[0..9] == 0`** - all ten bytes, at slot
offsets 824-833. **No Perception Chamber contract or runtime should inject or stamp a nonzero mood.**

Two independent reasons, both verified:

1. **The learner and the actor must be the same function.** `brainLearn` raises `brainNoMood` around its
   own forward pass, so the prediction a lesson corrects is computed **mood-free**, while the live think
   is not. With a nonzero mood the machine learns against a prediction it never acts on. Measured with
   `mood[9] = 127`: the mood-free prediction was output 1 while the live output was 9.
2. **Without it the policy hash is not a behavioural statement.** Same measurement: identical policy
   hash, different action.

Freezing the mood to zero **conflicts with nothing implemented.** Learning never writes it (verified:
zero after teaching, after a drain and across a room change). The load image ships it zero. Every
existing artifact - the canonical replay session's start and final slots, the preserved brains - has it
zero. The only thing deferred is a *designed-but-unused hook*: the slot's original comment reserved the
mood for a per-block "nudge" a contract could stamp at render. Nothing has ever stamped one. **It may be
reconsidered in a future generation; in this one it is deliberately inactive.**

### The two hashes, and which one Solidity should use

| | domain | answers |
|---|---|---|
| **canonical state hash** | sha256 over **all 834 slot bytes** | *Is this the same artifact?* **Use this for byte identity and provenance.** |
| **learned-policy hash** | sha256 over header shape, vocabulary, retina and the 800 weights (807 bytes) | *Do these two brains implement the same learned policy?* |

**Recommendation for Solidity: commit the canonical state hash.** It is the only one that is a complete
commitment to what the machine will do. Two slots with the same canonical hash are the same artifact and
behave identically. Two slots with the same **policy** hash need not - they may differ in mood (which
changes behaviour), in education count, or in lineage.

The learned-policy hash remains useful, and is what the replay reports, but it must be described
honestly: it is a **policy-equivalence check, in the weight domain**, and it is a statement about
behaviour **only for slots that satisfy the zero-mood invariant**. It was previously described as "the
behavioural hash", and that wording is retired: it overstated the domain. The reference tool now exposes
it as `policy_hash` (with `brain_hash` kept as an alias so pinned callers still work) and adds
`canonical_hash`.

### Where the invariant is enforced

* **`canonical_violations()`** in `tools/brain025_ref.py` lists every reason a slot is not admissible,
  including a nonzero mood by name and offset. This is the **admission** predicate for a host or a
  contract.
* **`check_slot()`**, which gates replay, now **fails closed** on a nonzero-mood starting slot rather
  than reinterpreting it.
* **`malformed()` deliberately does NOT consult the mood.** That predicate exists to mirror the
  machine's own `brainCheck`, and the machine **does** accept a nonzero-mood slot and run it
  (`brainKindNow` 1, measured). Keeping the two in step is what the parity gate checks; the canonical
  rule belongs at the boundary where slots are admitted, not inside a machine-parity mirror.
* **The `mood` gate** proves the machine keeps the mood zero through teaching, a drain and a room
  change, that one mood byte changes the decision, that the policy hash cannot see it, and that the
  canonical hash can.

**No PRG change was made for this, and none is needed.** The invariant is already satisfied by the
engine: nothing in play or in the learner can produce a nonzero mood. Only a host deliberately writing
those ten bytes can - and a host able to write the mood can equally write the 800 weights, so an
on-machine guard would not create a trust boundary that does not already exist. It would cost bytes and
a new PRG hash to defend against something outside the contract. If a future generation wants the
machine itself to refuse such a slot, that is a `brainCheck` extension and a new freeze.

---

## 6. Status

Perception Chamber engine development is **stopped** at the commit and hash above, pending Workbench
integration and human QA. The next architectural research question is **retention and interference**.
Additional perception, memory, planning or motivation are not indicated by anything measured here, and
each stays out until evidence names it.
