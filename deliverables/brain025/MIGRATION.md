# BRAIN02.5: migrating a BRAIN02 brain

Tool: `tools/brain025_migrate.py`. Results: `deliverables/brain025/brains/*.report.json`.

## What it does

Per action row, the original sixty-four weights are copied in order, unchanged, and sixteen zero weights
are appended. Every other compatible field is copied **by name**, so nothing is inherited by accident:

    kind, period, lineage, rule, vocabulary, education, mood      copied
    marker, layout, inputs, retina id                             the migration's only changes

    BRAIN02\0 -> BRAIN025      layout 2 -> 3      64 inputs -> 80      retina 2 -> 5

    python3 tools/brain025_migrate.py migrate IN.bin OUT.b025

The original file is never written to. The migrated brain is a new file with a new name, and the
verification report is written beside it.

## Why the prediction cannot move

Every appended weight is zero, so no appended input contributes to any accumulator. The ten accumulators
are therefore exactly what they were, and the argmax over them, with the same first-largest tie, is
exactly what it was. That is an argument. The gate measures it.

## The gate: zero prediction mismatches

Pre-registered acceptance was zero, and zero is what it is.

| what was checked | checks | mismatches |
|---|---:|---:|
| on the machine: three brains on the BRAIN02 build against their migrated copies on the BRAIN02.5 build, over 79 teacher-visited blocks under three terrains | 711 | **0** |
| off the machine: the same three brains over the full 1,424-block recorded corpus under three terrains | 12,816 | **0** |
| the Phase 3 taught brain alone, over the corpus under eight terrains | 11,392 | **0** |
| golden forward and lesson cases at eighty inputs | 13 | **0** |

The three brains are the Phase 3 machine-taught brain (`climbed-tony-b02-a.bin`, education 33), Phase
2b's learned weights at the byte box (education 474), and a random brain whose weights sit at the clamps.

### The one false alarm, and what it was

The first full run of the machine half reported **three mismatches out of 711**, all on the same block
with Phase 2b's weights, under all three terrains. It was worth chasing, because the pre-registered
acceptance is zero and a real migration defect would look exactly like this.

It was not the migration. Run in isolation, both machines and the reference all chose the same action
for that block. The gate had been giving the **BRAIN02** build's test hook two frames to finish, a
constant copied from BRAIN02's own parity gate, and on that block two frames is not enough: the peek
read the previous block's answer. Nine of seventy-nine blocks read stale at two frames and none at six.
Giving both builds the same generous wait, the count is 711 of 711.

The lesson is about the measurement, not the brain: a hook whose duration depends on how many inputs are
set needs a wait sized for the worst case, not the typical one.

## The preserved human-trained brain

**Not available in this repository or session.** The brief names a Candidate A brain with behavioural
hash `b23df474f739e48dfa0b1dd9bf7dc0e892b76dd2eb3571cb6882228576b79cbb` and education count 300, whose
300 human lessons replay from zero to the exact exported brain. It was searched for by that hex string
across every file, by SHA-256 over every small file in the tree, and by behavioural hash over every
binary that parses as a BRAIN02 slot. Every search was negative; `BASELINE-VERIFICATION.md` section 3
lists what is there instead.

Deliverable 11 is therefore outstanding, and it is one command away. Given the 674-byte slot export:

    python3 tools/brain025_migrate.py migrate b23df474.bin deliverables/brain025/brains/human-300-migrated.b025

The expected result, stated in advance: 834 bytes out, weights copied, sixteen zeros appended, education
300 carried, and **zero** prediction mismatches over the corpus. If it is anything else, the experiment
stops there, because the argument above would then be wrong about a real brain.

Given instead the 300-lesson stream, the same claim can be checked the harder way: replay it into a
BRAIN02 brain, migrate that, and confirm both the brain and the mismatch count.

## What is never done

The 300-lesson brain is not overwritten, not upgraded and not replaced. A migrated brain is a new file
beside the original, with a different extension and a different hash. BRAIN02.5 sits next to BRAIN02;
nothing is merged over it.
