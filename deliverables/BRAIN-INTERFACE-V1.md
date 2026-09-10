# BRAIN-INTERFACE-V1 (returned by the engine session, 2026-09-10)

Status: **RETURNED.** This is the session of record's draft of 2026-09-10 with every PROPOSED row
settled by the engine session and the golden vectors produced. Rows marked BUILT are unchanged and
are the engine's word; rows marked SETTLED were PROPOSED and are now the engine's word too, with the
correction stated where the draft misread the build; rows marked OPEN still need a measurement, and
the owner of that measurement is named. The code this describes is `tony-body.prg` at the commit that
carries this file; the benches (`tools/verify_brain.py`, `tools/brain_golden.py check`) are the proof.

Neither session invents its own interpretation. Where this file and the running code disagree, one
of them is wrong, and the answer is a correction here, not a private reading.

## 1. Identity

| Field | Value | Status |
|---|---|---|
| Marker | 8 bytes at slot offset 0: the ASCII bytes `BRAIN01` and a zero | BUILT |
| Schema version | the layout byte, 1: this sense packing and this action vocabulary | BUILT |
| Learning-rule version | byte 15, value 1 for the rule in section 6; 0 reads as 1 (an unset slot) | SETTLED |
| Brain kind | byte 8: 0 no network (the follow rule drives, weights ignored, brain-present false); 1 a perceptron over this layout; 2 the hand-written builder rule, weights ignored | BUILT |
| Malformed state | any of: the marker not `BRAIN01`, layout not 1, kind above 2, inputs not 20, hidden not 0, outputs not 10, rule byte above 1: the program behaves as kind 0 and the page says "no brain". Checked every think (`brainCheck`, the result in `brainKindNow`). Correction to the draft: the 6502 forward pass reads exactly twenty inputs and ten outputs whatever the header says; the counts are description today and become control when the capacity benchmark makes the input count variable, so a count other than the build's is malformed, not "above 51" | SETTLED |

## 2. Slot layout (page aligned, 280 bytes)

| Offset | Bytes | Content | Status |
|---:|---:|---|---|
| 0 | 8 | marker | BUILT |
| 8 | 1 | kind | BUILT |
| 9 | 1 | layout, 1 | BUILT |
| 10 | 1 | inputs, 20 | BUILT |
| 11 | 1 | hidden, 0 | BUILT |
| 12 | 1 | outputs, 10 | BUILT |
| 13 | 1 | period, frames between thinks, 4 | BUILT |
| 14 | 1 | lineage context bits, stamped at render: bit 0 PETARP, bit 1 ORAAND; read by nothing in the program today, shown on the ledger page when it exists | SETTLED |
| 15 | 1 | learning-rule version, 1 | SETTLED |
| 16 | 256 | weights, 512 nibbles; kind 1 with 20 inputs uses the first 100 bytes | BUILT |
| 272 | 8 | mood, ten signed nibbles in the same packing, five bytes used; a render's nudge, never part of a saved brain | BUILT |

A property worth stating: `brainHash` (section 8) covers the weights and header bytes 8 to 12 only, so a
render stamps bytes 13 to 15 and the mood without ever changing a saved hash.

The room's mutation layer lives outside this slot. Correction to the draft's size: it is 19 bytes per
room today (150 slots of the wall grid, one bit each, `placedBits`), 38 for both rooms, re-laid at
room entry; a marked block of that size injected the way the brain is, `ROOM01`, is the plan for the
room stage. Its layout is OPEN (engine), after the learning milestone.

## 3. Senses (inputs), ordered, 20

Unchanged from the draft: BUILT, parity-checked nibble for nibble at fourteen snapshots
(`tools/verify_brain.py`, "senses"). The exact definitions are in `BODY.md`, "The sense block", which
is the reference. Any sense added by the capacity benchmark appends at index 20 and up and raises the
inputs byte; nothing reorders these.

## 4. Actions (outputs), ordered, 10

Unchanged from the draft: BUILT. The decoder owns the build macro and the release frame after a duck;
the network never emits joystick bits directly (`BODY.md`, "The action vocabulary and the decoder").

## 5. Forward pass

Unchanged from the draft: BUILT. `acc[o] = sum(w[o][i] * x[i]) + m[o] * 16`, sign-extended, 16-bit; the
first largest wins, ties to the lowest index; `w[o][i]` at byte `16 + o*10 + i/2`, low nibble for even
`i`. The golden set `forward.json` (46 cases: the all-zero tie, both extremes, a tie between two
outputs, one product, the mood alone deciding, forty random) passes on the 6502 through the test hook.

## 6. Learning rule

SETTLED as proposed, with the open question answered and two details added, and one correction made
by the teaching build (item 1).

1. During teaching a lesson is taken at every think tick and at every **edge**, a frame whose applied
   action differs from the last frame's (a press or a release). `x` is the published sense block at
   that frame (the same bytes the scope shows, the state of one frame) and `t` is the action applied in
   the frame *after* it, the one taken from that state, decoded from the joystick byte by the mapping of
   sense 16. Not the block's own sense 16: that is the action that made the state, and pairing them
   teaches "in the air: jump" and never "a wall ahead: jump" (the frame that launches a jump is
   already in the air). The edge is there because a tick alone sees the launching frame one time in
   four. Replay is unaffected: a recorded lesson carries its `t`.
2. Compute the mood-free prediction `p`: the forward pass with the mood left out, ties to the lowest
   index (`brainNoMood`).
3. If `p == t`: no lesson. Nothing is recorded, nothing changes.
4. If `p != t`: record the lesson `(x, t)` and, for every input `i` with `x[i] != 0`: `w[t][i] += sgn(x[i])`,
   `w[p][i] -= sgn(x[i])`, each saturating at -8 and 7. The rows are updated in that order; since `t`
   and `p` differ, the order does not matter to the result.
5. The next think uses the new weights.

**The step is `sgn(x)`, a step of one.** The reason: weights saturate at 8, so a step scaled by a
flag's 7 saturates a weight in one lesson and every lesson becomes an overwrite of the last, while a
step of one leaves eight lessons of headroom for a weight to be argued over. The rig may still show a
scaled step converging faster on the follow-and-climb task; if it does, that is a rule version 2 and a
new golden set, not a change to this one.

Cost on the 6502: two rows of twenty saturating nibble steps, under two thousand cycles, in the main
loop. Implementation: `brainLearn`, behind the test hook `brainLearnRun` (inputs `brainTestIn` and
`brainLearnTestT`, outputs `brainLearnTestP` and `brainLearnTestTook`, the weights changed in place).

## 7. Lesson encoding

SETTLED as proposed: 11 bytes, the 20 sense nibbles packed two per byte (nibble `i` in byte `i/2`, low
nibble for even `i`), then one byte whose low nibble is the taught action and high nibble zero. The
taught action is derived from the joystick byte by the mapping of sense 16 (`BODY.md`, the sense
table). The program keeps a session's lessons in order in a marked block, `LESSON1`, that the page
reads: at $8a00 in this build, page-aligned, found by its marker or the symbol file; the marker and a
zero, the count (word), the capacity (word, 500), the size (11), the total taken (word, the buffer may
be full), a zero, then the lessons (`BODY.md`, "TEACH"). The buffer holds 500 lessons in the memory the
level tune vacates after it is copied out; the cap per session is the contract's gas, not the
machine's (OPEN, contracts). Replay on the chain: section 6 over the saved brain, in order; a
lesson whose replay finds `p == t` is a no-op and still counted.

## 8. Hashes and counters

Contract-side, unchanged from the draft. One engine note: `brain(id)` returns header bytes 8 to 12 as
the program stamps them; the program never changes them itself except the kind, which live teaching
sets from 0 to 1 on the first lesson taken, so that a taught clone drives his own brain after the
stick is released and a reload forgets.

## 9. Golden vectors

Produced. `deliverables/golden/`, JSON, one file per set, made by `tools/brain_golden.py write` from
the Python reference in the same file (`forward`, `learn`, `replay`: the whole rule in three functions),
and checked on the 6502 by `tools/brain_golden.py check`: 95 cases, 95 agree.

1. `forward.json`: brain + mood + senses → ten accumulators + action. 46 cases, the extremes and ties
   included.
2. `lessons.json`: brain + ordered lessons → new brain, with the prediction and whether the lesson was
   taken for each. 27 cases: an empty batch, from zero, saturation at 7 and at -8, a no-op, negative
   senses, a batch that flips a decision then no-ops, twenty random batches of one to eight.
3. `mood.json`: brain + mood + senses → the action with the mood and without it, the taught action and
   whether a lesson is taken. 22 cases, including the mood flipping the action while the mood-free
   prediction is the taught one (no lesson), and the mood not saving a wrong prediction.
4. brain → colour and traits: waits for the mapping (session of record).
5. population → commons: the contract's.

Encodings in the files: weights and moods as hex strings of the packed nibbles, senses and actions as
integers. A Solidity implementation passes when it reproduces every `acc`, `action`, `weights_after`,
`predictions` and `taken`.

## 10. Open items, by owner of the answer

- Engine: none of the PROPOSED rows; the `LESSON1` and `ROOM01` block layouts follow with their builds.
- Rig: lessons-from-zero to follow-and-climb: the engine's teaching demo reports **36 lessons in 4
  sessions** from zero weights, with the builder's rule as the teacher through the port and the stairs
  and ladder of the bench (`BODY.md`, "TEACH"; the weights in `deliverables/brains/taught-climb.bin`).
  Still the rig's: capacity at 200, about 320, about 400; whether a scaled step or a lesson every frame
  beats the step of one at period 4.
- Contracts: gas per save at 10, 25, 50 lessons against each brain size; `commons()` read cost; the
  batch cap.
- Owner: nothing.

## Two design notes from the engine, for the session of record

**The TEACH chord.** Hold the lay chord, down with fire, for a second (fifty frames). The press lays or
lifts a brick as always; when the hold reaches a second that brick is taken back and the mode
switches, so the hold has no side effect, and the brick that appears and vanishes is the cue. Any
stick can make it, a phone's on-screen one included, so the page needs no second button for it,
though it may have one (the flag `teachMode`). A first version used "up held a second"; it toggled by
accident whenever a player kept pushing up after arriving at the top of a ladder, and was dropped.
While teaching is on, Tony stands, the port drives the clone with fire-and-down and fire-and-up
translated to the lay and step-up bits, and a lesson flashes him white. Holding the chord a second
again turns it off, taking back the clone's brick the same way, and also the lessons the hold taught
(a routed lay is a "build" lesson, and without this he laid the brick again the moment the stick was
his): the weights and the lesson counters are shadowed on the chord's first frame and put back when
the hold toggles; the spent chord is then dead until let go. A tap is a lay and its lessons stay.
Decision 5 says the chord is engine work and cheap to revise; this is the first proposal, built.

**A taught clone following through the ceiling.** Not built, raised as an option because it reverses
"he waits". The engine's shape allows it cheaply: the clone gets a room number of his own, moves only
when his room is the one on screen, and crossing an exit sets his room and his arrival place, so he is
at the ladder hole when Tony arrives and comes back down after him. It makes "he can come up with you"
the first visible payoff of teaching, and it changes what the away-senses of E9 should read (dx and dy
to the ladder's foot only while the two are apart). To decide after the learning milestone.
