# Workbench Integration Contract: the BRAIN02 research PRGs and the Akalabeth workbench

Engine commit `a04968d337d9dd5b030462a644e2a9e81b07a866`. This contract says what the existing Akalabeth workbench (`workbench/` in
`DeMEdPit/akalabeth`, owned by the program-manager session) may read and write in each research PRG,
and what must stay inside the machine. It replaces nothing there and builds no frontend: the
workbench loads a PRG like any other, drives the joystick, and reads and writes memory through
Minimal64's `m64_cpuRead` and `m64_cpuWrite`. Every address below is also in the machine-readable
descriptor beside this file (`workbench/<name>.json`, schema `tony-brain02-descriptor/1`), generated
from the build's symbol file, so the workbench need not hard-code candidate addresses.

## 1. The PRGs

Ordinary C64 programs (load address $0801, PAL), the same game as `tony-body.prg` with BRAIN02 in
place of BRAIN01; separate builds from the same generator, the retina table, the input count and the
vocabulary byte as data (the diagnostic pair differs by the vocabulary byte alone).

| file | candidate | bytes | sha256 | inputs | slot | think cycles (max) | lesson cycles (max) | raster max / overruns |
|---|---|---:|---|---:|---:|---:|---:|---|
| `tony-b02-a.prg` | A: R1b, reference-relative | 51169 | `ae6ce5244478532c…` | 64 | 674 | 17464 | 18999 | 174 / 0 |
| `tony-b02-b.prg` | B: R0s, reference-relative | 51121 | `4c62c1d2d7884145…` | 61 | 644 | 16096 | 17060 | 174 / 0 |
| `tony-b02-drel.prg` | diagnostic: R0, reference-relative | 51041 | `7ec874b6535618e8…` | 56 | 594 | 15754 | 16742 | 174 / 0 |
| `tony-b02-dabs.prg` | diagnostic: R0, absolute | 51041 | `012d42d58e977a55…` | 56 | 594 | 16008 | 16874 | 174 / 0 |

The parity build `tony-b02-p128.prg` (128 inputs, no retina of its own) exists for the golden vectors
and is not a candidate. Cycle counts are the machine's own (CIA 2 timer A) through the test hooks with
the interrupts held off: the work itself; the live counts include the frame interrupt.

## 2. Three kinds of access

**Observation** (read at any time): everything in the descriptor's `brain`, `retina`, `live`,
`profiler` and `lessons` sections. To read the weights consistently while the machine runs, read
`lessons.write_seq` before and after; equal means no lesson intervened (the workbench pauses the
emulator during a read in any case).

**Research control** (explicit writes, research-only, absent from production semantics):

- `live.teach_mode` (0/1): the same as the lay chord held a second; the machine's own path.
- the drain handshake: `lessons.ack_seq`, `lessons.ack_sum`, `lessons.ack_request` (section 4).
- `lessons.capacity`: may be lowered at boot before any lesson (the ring tests use 40 and 12).
- the whole slot, at boot: writing marker, header, weights and mood loads a saved brain; zero weights,
  education 0 and kind 0 is a reset. Never mid-session except through the drain-and-reload path.
- the seed bytes of the parameter block (the ladder's column and the wall), at boot.
- the test hooks (`test_hooks`): they run the machine's own retina, forward pass and rule on supplied
  inputs and change the slot when a lesson is taken; for parity work only.

**Cognition** (never the host's): the retina, the forward pass, the resolution of a relative action,
the learning rule and the recording of a lesson run only in the machine. The browser never computes a
prediction, chooses an action, derives a flag for him, or writes a weight outside a load or a reset.

## 3. The brain slot

`BRAIN02` at `0x7500` in candidate A (see each descriptor): marker 8, header 16 (kind, layout 2,
inputs, hidden 0, outputs 10, period, lineage, rule 2, vocabulary, retina id, education count as a
16-bit little-endian word, four reserved), then 10 rows of n signed bytes (row o at weights + o·n),
then ten signed mood bytes (zero in this phase). **Export** is a read of `slot_bytes` bytes from the
marker; **import** is the same bytes written back at boot. The behavioural hash (`brainHash`) is
SHA-256 over bytes 8..12, 16..17 and the weights, in slot order; two brains with equal hashes behave
identically. The education count and the lineage and rule bytes are provenance and travel with the
export but are not hashed. `tools/brain02_ref.py` (`parse_slot`, `brain_hash`) is the reference.

## 4. The lesson ring and the drain

`LESSON2` (32-byte header, then 300 entries of 11 bytes; the layout in the descriptor). A lesson is
applied and recorded together or not at all: when the ring is full learning pauses (status bit 0, the
clone flashes red instead of white on a refused lesson) until the host drains. The drain:

1. read `read_seq` and `write_seq`; the unread lessons are the sequences in [read_seq, write_seq);
2. read entry `s` at `data + (s mod capacity) · 11` for each; keep them (they are the education);
3. sum every byte of those entries modulo 65536;
4. write `ack_seq = write_seq`, `ack_sum` = the sum, then `ack_request = 1`;
5. after a frame, read `status`: bit 7 accepted (and `read_seq` now equals `write_seq`); bit 1 a lesson
   was recorded since your read (re-read and retry); bit 2 the sum did not match (nothing reclaimed);
   bit 3 a chord hold is in progress (retry later).

The machine reclaims only the exact range the host names with the exact content, so no education can
be discarded silently. Replay of a drained batch over the brain as exported before it (per lesson:
unpack the senses, derive the flags with the retina table, translate the taught absolute action with
the block's own `h` under the relative vocabulary, apply the rule) must equal the machine's weights
and education count byte for byte; the machine gate (`phase3/drain-*.json`) shows it does.

## 5. The owner's five-step test on the existing workbench

1. Load `tony-b02-a.prg` (or `-b`); he boots as kind 0 and follows Tony.
2. Enter TEACH through the machine's own path: hold the lay chord (down with fire) for a second
   (or write 1 to `teach_mode`). Tony stands; the stick now drives the clone.
3. Teach something simple and non-holdout in the training room: walk him toward Tony and back, jump
   him over a brick Tony laid, or lead him up the stairs Tony builds under the ladder at column 33
   (the E5 scenario: five bricks, then the ladder). Every lesson flashes him white; `write_seq` and the
   education count in the header advance; "he thought X, you said Y" is the high and low nibble of each
   new ring entry's byte 10.
4. Hold the chord again (or write 0): the stick returns to Tony and the learned brain drives. Compare
   with what the follow rule did.
5. Export the slot (`slot_bytes` from the marker) as the saved brain, and drain the ring (section 4) as
   the lesson batch; reload the PRG, write the slot back at boot, and see the behaviour persist.

Recommended first scenario: the training room as it boots (the ladder at column 33), Tony on the
floor: **follow right, follow left, then one brick to jump.** None of the holdout scenarios is built
into any PRG or named here.

## 6. The session trace the workbench can construct

By observation each frame: `frames`, `teach_mode`, both actors' positions and states, the applied
action, the predicted output and the resolved action, `write_seq`, the flash colour. Per lesson: the
new ring entry (senses, taught, predicted), the education count, and which weights changed (a diff of
the two rows). Events from research control: teach on/off, a drain (the batch and its replay result),
a brain load, a reset, a capacity change. From these: wall-clock to the first visible improvement,
active teaching time, lessons per minute, deliberate edges (applied-action changes), corrections
(lessons whose prediction differed from the taught action), aliasing (the same senses taught two
actions), the lag between a press and the state change it answered, competence when the teacher
releases control, and competence after save and reload. The descriptor's `session_trace` lists the
fields; the schema is JSON, one object per session, arrays per frame and per lesson.

## 7. What the machine tells about itself

`profiler.*`: the last and the largest cycle counts of a think, a lesson, a snapshot and a drain (live,
interrupts included) and of the hook's think and lesson (pure); `profiler.gap_*`: the score gap of
every think (the winner's accumulator minus the runner-up's), its minimum, maximum, sum and count,
for the mood-scale question. `lessons.not_paired` (the descriptor's `live` section in later
descriptors): lessons lost because the block's next frame was not packed in time.
