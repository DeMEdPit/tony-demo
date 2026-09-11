# BRAIN02.5, step A: the baseline verified and frozen

Run before any BRAIN02.5 implementation, on a clean tree, in the order the brief sets out.
Every check below had to pass for the work to continue; the brief says STOP otherwise.

## 1. The engine commit

    3e12f0e19d69f9d37e1b95beafa9aa3368511cd0
    Chamber v2 Phase 3, Checkpoint C: the four research PRGs, the gates passed, the integration contract
    Fri Sep 11 01:36:07 2026 +0000

`git status --short` empty: nothing modified, nothing staged, no untracked file. HEAD was already this
commit on `claude/tony-c64-demo-expert-wp40it`.

## 2. Candidate A's PRG

    deliverables/prg/minimal64/tony-b02-a.prg
    51,169 bytes
    sha256 ae6ce5244478532c5ec581c9e24a30bea0743c68b2dd7cc7ff9f3017bc3e594d

Equal to the hash the brief names. R1b, 64 inputs, reference-relative, 674-byte slot.

The other three research PRGs and the parity build, unchanged, for the record:

| PRG | bytes | sha256 |
|---|---:|---|
| tony-b02-a.prg | 51,169 | ae6ce5244478532c5ec581c9e24a30bea0743c68b2dd7cc7ff9f3017bc3e594d |
| tony-b02-b.prg | 51,121 | 4c62c1d2d788414562ca8307673b2074c7eeaa8650c609ca133b232ef36cd305 |
| tony-b02-drel.prg | 51,041 | 7ec874b6535618e8f02172ab0ab5cc4654b72c3d06757287076a24a37c31cfa4 |
| tony-b02-dabs.prg | 51,041 | 012d42d58e977a55116376b34c5072a100bf5aab28df8c7eb85f9eb659200fa1 |
| tony-b02-p128.prg | 52,193 | f99958e93528443e1516cab7ae2aa3ef2466ae99419263742c1c26746051d9d0 |

The two frozen earlier deliverables are also unchanged: `tony-chamber.prg` 46,877 bytes
sha256 67dc97bc1e3067151c8a1d24fe4bf18beabf83624c69cdb65182a34aa914ad61, and `tony-build.prg`
43,434 bytes sha256 5c24a63e1c14e26c2f966e7cc58cf4d484792b82bcd7c8e397ae96cd564bbf29.

## 3. The preserved human-trained brain: NOT PRESENT in this repository or session

The brief names a preserved Candidate A brain, behavioural hash
`b23df474f739e48dfa0b1dd9bf7dc0e892b76dd2eb3571cb6882228576b79cbb`, education count 300, whose 300
human lessons replay from zero to the exact exported brain byte for byte.

It is not here. The searches run, all negative:

* the literal hex string, over every tracked and untracked file outside `.git`;
* the sha256 of every file under 20 KB in the working tree, compared against that hash;
* `brain_hash` (the behavioural domain: header bytes 8-12 and 16-17 plus the ten weight rows) of every
  binary in `deliverables/` that parses as a BRAIN02 slot.

Four slot exports exist, all from the machine's own Phase 3 teaching runs, none of them the human brain:

| file | bytes | education | brainHash |
|---|---:|---:|---|
| climbed-tony-b02-a.bin | 674 | 33 | be9b0a98a6427eb63df4da1d65ce4bc8c479530eb4bdfeec9d63f770e3005547 |
| climbed-tony-b02-b.bin | 644 | 31 | 65d586625ab9f5a62fee4d0029ca8730ca5ac4220581ae7bf51d0daae1d8fa7e |
| climbed-tony-b02-drel.bin | 594 | 37 | 58d645d709c741069aa274ea057bc723b99d3bfc26b8d221554bfa88cf674f71 |
| climbed-tony-b02-dabs.bin | 594 | 34 | 4693091f418390b16b6c1505894b8204b39645418bd63564d5a7c02ff0d0025a |

The brief makes this check conditional ("if available in this repo/session"), so its absence is not a
STOP. It does leave deliverable 11, the migration result on the preserved human brain, outstanding.
The migration tool is written to take that brain the moment it is handed over, and
`MIGRATION.md` records the exact command and the exact expected result. What is needed from the
manager or workbench session is the 674-byte slot export itself, or the 300-lesson stream from which it
replays.

## 4. The BRAIN02 baseline gates, re-run on this tree

`python3 tools/brain02_ref.py check` - ALL OK:

* the four retina tables differ from the offline encoders on 0 of 1,424 recorded blocks;
* h against the offline reference: 0 differences;
* the vocabulary maps round trip and agree;
* `learn_signed` identical to the golden reference over 20 passes, 729 lessons;
* the flag rule equals the signed rule on 0/1 inputs over 300 random lessons;
* the slot is 674 bytes for R1b, 647 behavioural bytes, parse and malformed checks ok.

`python3 tools/brain02_test.py <gate> deliverables/prg/minimal64/tony-b02-a.prg`, all four exit 0 with
no FAIL line:

* **parity** - the retina and h byte for byte on 1,424 of 1,424 recorded blocks; golden forward 3 of 3;
  golden lessons 3 of 3; the 40 vocabulary cases; malformed slots falling back on every header field;
  Phase 2b's learned R1b weights replaying on 474 of 474 teacher-visited blocks.
* **resources** - think at most 17,464 cycles, lesson at most 18,999, each inside one frame of
  main-loop time; the episode's drain accepted and replayed equal. (The lesson figure was 18,971 at
  Checkpoint C; the profiler counts wall-clock work in the main loop and moves by a few tens of cycles
  between runs. The gate is "inside one frame", and it passes.)
* **teach** - blank boot, the chord, weights and education advancing, behaviour changing, the climb
  after 2 sessions and 33 lessons from zero, the saved brain reloading byte for byte on a fresh boot
  and climbing again, hash be9b0a98a6427eb6.
* **drain** - three ring cycles, validated acknowledgements, refused bad checksums and stale acks,
  and the split run's 163 lessons in 6 batches replaying to the uninterrupted brain byte for byte,
  0 dropped pairings.

## 5. The BRAIN02.5 branch

    claude/brain025-terrain-observability

branched from 3e12f0e. No BRAIN02 artifact is renamed, moved, mutated or overwritten on it.

## 6. Distinct names and schema identifiers

Everything BRAIN02.5 writes is separately named. The reservation, fixed here before any code:

| BRAIN02 (frozen) | BRAIN02.5 (new) |
|---|---|
| slot marker `BRAIN02\0` | slot marker `BRAIN025` |
| ring marker `LESSON2\0` | ring marker `LESSON25` |
| `tools/brain02_ref.py` | `tools/brain025_ref.py` |
| `tools/brain02_asm.py` | `tools/brain025_asm.py` |
| `tools/brain02_test.py` | `tools/brain025_test.py` |
| `tony-b02-*.prg` | `tony-b025-*.prg` |
| descriptor schema `tony-brain02-descriptor/1` | `tony-brain025-descriptor/1` |
| `deliverables/bakeoff/phase3/` | `deliverables/brain025/` |
| retina ids 1-4 (R0, R1b, R0s, R1s) | retina id 5 and up |
| lesson format (implicit, 11 bytes) | lesson format, explicitly versioned |

Slot layout byte 9 is 2 for every BRAIN02 slot; BRAIN02.5 uses 3, so a BRAIN02 slot cannot be loaded
into a BRAIN02.5 build or the reverse without the malformed check catching it.
