# BRAIN02.5 and the workbench: what the manager session needs

This is the BRAIN02.5 contract. It does **not** replace `deliverables/bakeoff/WORKBENCH-INTEGRATION.md`;
BRAIN02 is frozen and its contract stands unchanged. Everything here is additive and separately named.

## The build

| | |
|---|---|
| PRG | `deliverables/prg/minimal64/tony-b025-a.prg` |
| size | 52,092 bytes |
| sha256 | `2a547ebfe77bebb6b6174729af05a2ebb4dc2a8e558359f615cbdf34d6bfb423` |
| descriptor | `deliverables/brain025/workbench/tony-b025-a.json`, schema `tony-brain025-descriptor/1` |
| machine | Commodore 64 PAL, a plain PRG; Minimal64 and VICE |

The descriptor carries every address, layout and procedure below in machine-readable form. Read it
rather than hard-coding anything from this document.

## What changed from BRAIN02, in the order it will bite

1. **The slot is not interchangeable.** Marker `BRAIN025`, layout byte 3, 80 inputs, retina id 5, 834
   bytes. A BRAIN02 slot loaded here fails the machine's own header check and the clone falls back;
   a BRAIN02.5 slot loaded into a BRAIN02 build does the same. This is deliberate. To carry a brain
   across, use `tools/brain025_migrate.py` and `MIGRATION.md`.
2. **The sense block is twenty-seven nibbles, not twenty.** Nibbles 0 to 19 are unchanged. Nibbles 20 to
   26 are the seven terrain quantities; `INPUTS.md` and the descriptor name them and say what each
   observes.
3. **The lesson entry is fifteen bytes, not eleven, and the ring holds 180, not 300.** Marker `LESSON25`,
   format version 2. `LESSON-SCHEMA.md` gives the layout and the drain procedure, which is otherwise
   BRAIN02's unchanged: name the exact range, carry the byte checksum, and only then is anything
   reclaimed.
4. **Teaching is toggled by the T key, not by a joystick chord.** Down with fire is the lay verb again
   and nothing else; up with fire is still the step up. The workbench may still write `teach_mode`
   directly, and that is the recommended way to drive it from a UI. The key exists so a person at a
   real machine can teach without a chord that collides with the verbs they are teaching.
5. **A blank Tony does nothing.** There is no follow rule behind the brain in this build. Zero weights
   give ten equal accumulators and the existing first-largest tie picks output 0, IDLE. Do not expect
   the clone to move before he is taught; that is the study's whole point. Cosmetic idle animation is
   the only thing that runs.
6. **The clone spawns at X 72, columns 7 and 8**, by the far left pillar, clear of the ladder at columns
   33 and 34, leaving the room for courses.

## What did not change

The learner. Ten reference-relative outputs, byte weights, the symmetric rule at the byte box, the
first-largest tie, the accumulator semantics, and inputs 0 to 63 with R1b's meanings and order. The
atomic weight shadow, driven by `shadow_request` and `shadow_restore_request`, is exactly BRAIN02's and
the main loop still honours it before any lesson. The behavioural, provenance and timing hash domains
are defined the same way, over the new widths.

## Reading a session

Per frame: `frames`, `teach_mode`, `teach_key_edges`, the clone's and the player's position and state,
`predicted_output`, `resolved_action`, `write_seq`, `flash_colour`, and the seven terrain quantities out
of the sense block. Per lesson: the new ring entry, the education count, and the two weight rows that
changed. The descriptor's `session_trace` section lists these and the derived quantities worth keeping.

## What the host must never do

Compute an input, a prediction or an action for him. The terrain probe, the retina, the forward pass,
the vocabulary resolution, the rule and the lesson recording all run on the C64. The host may observe
everything, toggle teaching, run the drain handshake, load or reset a brain at boot, and lower the ring
capacity before any lesson. That is the whole of it.

## Two numbers to plan around

* At eighty inputs the think takes up to 24,129 cycles and a lesson up to 26,747, so neither fits inside
  one frame of main-loop time any more, though both finish comfortably inside the four-frame think
  period and the raster maximum is 141 with no overruns. If the workbench single-steps frames, do not
  expect a decision every frame.
* Teaching interferes with itself. An unrelated later stream cost 28 points of gauntlet accuracy on
  BRAIN02.5 and 44 on BRAIN02. Long sessions are not short sessions repeated, and a session plan should
  either revisit earlier material or accept the loss.

## Status

This is a research build for the terrain-observability study. It is **not** a production architecture,
nothing here is deployed, and BRAIN02 remains the frozen baseline.

## Canonical state, and the two hashes (added at the pre-Solidity freeze)

**A valid canonical brain has all ten mood bytes zero**, at slot offsets 824 to 833. Each is a signed
per-output bias written straight into that output's accumulator, so a nonzero one changes the action.
No contract or runtime should inject or stamp a nonzero mood. `canonical_violations()` in
`tools/brain025_ref.py` names the violation and its offset; `check_slot()` fails closed on a nonzero-mood
starting slot.

* **canonical state hash** - sha256 over all 834 slot bytes. Byte identity. **Commit this one.**
* **learned-policy hash** - sha256 over the header's shape bytes, the vocabulary, the retina id and the
  800 weights. A policy-equivalence check in the weight domain. It is a behavioural statement only for
  slots that satisfy the zero-mood invariant. Previously called "the behavioural hash"; that name is
  retired as overstating the domain.

**Replay authority is the ordered lesson stream against a named starting slot, not the education
count.** The counter is not inherently monotonic under every historical control path - the teaching
shadow's restore rewinds it together with the weights and the ring's write side.

**Everything the Workbench draws is a rendering of bytes the machine published.** The material-bits grid
is a host-derived visualisation of the live `roomMaterialsBuffer` and the screen matrix that the
descriptor points at: the semantics are the machine's, the picture is the host's. It is not a second
world model and not browser-side cognition.

Full statement: `PERCEPTION-CHAMBER-SCOPE.md`, section 5.
