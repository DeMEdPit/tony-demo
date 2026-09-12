# BRAIN02.5: the canonical replay reference

What an independent implementation needs in order to take a recorded LESSON25 session and reproduce the
final BRAIN025 weights byte for byte. Nothing here changes the PRG, the architecture, the terrain
inputs, the learning rule, the lesson format, the timing, the controls or any behaviour.

## The canonical files: two, not one

`tools/` is canonical. There is no second copy to drift from it; the manifest below pins these by hash
and a check fails if either moves.

| path | sha256 | git blob |
|---|---|---|
| `tools/brain025_ref.py` | `5a94e05ccf7886d0d1b97282d1eec8e5f1e79b0ffd7b239b689b11f51b4434ae` | `dba2ad2b04939aac03ad30598e1490a8245a95ce` |
| `tools/brain02_ref.py` | `625e27296851ec4f55a2b610b0162879560d823d08a2dcf7d25560002c8ad59d` | `ee2e42e071ff0ca830634a6ea01a4f42c29c69fc` |

Both are required. `brain025_ref.py` holds the retina table, the slot and lesson formats and the replay
itself; it delegates to `brain02_ref.py` for the **learning rule and forward pass**, the **vocabulary
resolution** (`h_of`, `to_relative`), the **nine pseudo-senses**, and the **first sixty-four retina
entries**. Neither file is a replay implementation on its own. They import nothing else at module level,
so the two together are the whole dependency.

## Pinned to

| | |
|---|---|
| reference pinned at commit | `210fa005daf7462a786e68ca9d3a1f88a8ad42e5` |
| build the session was recorded on | `tony-b025-a.prg`, 52,092 bytes, sha256 `2a547ebfe77bebb6b6174729af05a2ebb4dc2a8e558359f615cbdf34d6bfb423` |
| that PRG first committed at | `348798f` |
| manifest | `deliverables/brain025/replay/MANIFEST.json`, schema `tony-brain025-replay-manifest/1` |

Check the pinning before trusting a replay:

    python3 tools/brain025_ref.py verify

It re-hashes both canonical files against the manifest and exits non-zero on any drift, naming the file
and both hashes.

## The hash the replay reports, named honestly

The hash printed as `brain hash` is the **learned-policy hash**: sha256 over the header's shape bytes,
the vocabulary, the retina id and the 800 weights - 807 bytes in all. It answers "do these two brains
implement the same learned policy". It **excludes** the mood, the education count and the lineage, and
it was previously called "the behavioural hash", which overstated its domain: two slots can share it
and still act differently if their mood bytes differ.

For byte identity and provenance use the **canonical state hash**, `canonical_hash()`: sha256 over all
834 slot bytes. That is the commitment to make on-chain.

Both are only meaningful for slots that satisfy the **zero-mood invariant** - all ten mood bytes zero,
at slot offsets 824 to 833. `check_slot()` fails closed on a nonzero-mood starting slot, and
`canonical_violations()` lists it by name. See `PERCEPTION-CHAMBER-SCOPE.md` section 5.

Replay authority is the **ordered lesson stream against a named starting slot**, never the education
count: the counter is not inherently monotonic under every historical control path, because the
teaching shadow's restore rewinds it together with the weights.

## The invocation

    python3 tools/brain025_ref.py replay START.slot LESSONS.bin --out FINAL.slot [--expect MACHINE.slot] [--check-predictions]

* `START.slot` — the 834-byte BRAIN025 slot the session began from. **Required and explicit.**
* `LESSONS.bin` — the ordered LESSON25 entries, 15 bytes each, concatenated in sequence order.
* `--out` — where to write the resulting 834-byte slot. Optional.
* `--expect` — an exported machine slot to compare against. Exits non-zero on any difference and names
  the first differing byte.
* `--check-predictions` — also verify the prediction the machine recorded at each lesson against the
  reference's own recomputation, and fail on disagreement. See below.

It prints the input count, the retina id, the vocabulary, the lessons applied, the education count
before and after, and the behavioural hash before and after.

## Starting-slot semantics, which are not optional

**A replay is only meaningful against the slot the session actually started from.** The lesson stream
carries no weights: it is a sequence of corrections, and applying it to a different starting brain gives
a different and silently wrong answer.

* For a session taught from nothing, the starting slot is the **blank** one: marker `BRAIN025`, layout
  3, 80 inputs, retina 5, all 800 weights zero, all 10 mood bytes zero, education 0. That is what the
  machine holds at boot, and `session-1/start.slot` is a copy of it.
* For a session that continued from a saved brain, the starting slot is **that** brain as it stood
  before the first lesson of the stream, education included. Capture it before teaching, not after.
* The education count in the result is the starting count plus the lessons applied. If your starting
  slot has the wrong education, the weights can still match while the slot bytes do not.
* The mood, period, lineage, kind and vocabulary are carried through from the starting slot untouched.
  The mood is held at zero throughout this work.

## The ordered stream

Entries must be in **sequence order**, the order the machine wrote them, concatenated with no padding
and no separators. The drain hands them over in that order within each batch: read the range
`[read_seq, write_seq)` ascending, and concatenate successive batches. The stream may span ring reuse
cycles, and the proof below deliberately does.

## The prediction cross-check

The weights are not the whole record. Each entry's last byte also carries the prediction the machine
made at lesson time, and a replay that only reproduces the weights leaves that field unverified. Ask for
it explicitly:

    python3 tools/brain025_ref.py replay START.slot LESSONS.bin --check-predictions

The count is always reported. It **fails**, exit 1, when verification was requested, meaning
`--check-predictions` or `--expect` was given. A bare replay reports the count and still exits 0.

**Mind the asymmetry inside that last byte.** The low nibble is the taught action in **absolute** terms.
The high nibble is the machine's mood-free prediction as a **raw output index**, which under the
reference-relative vocabulary is the *relative* one. Comparing it against the resolved absolute action is
wrong, and quietly so: on the 244-lesson session below, the raw relative reading matches 244 of 244
while the absolute reading matches only 171.

Why it is worth asking for: on that same session, stripping every prediction nibble out of the stream
leaves the final slot **byte-for-byte identical** and the brain hash unchanged, while 178 of 244
predictions no longer agree. The weights passing does not verify the record. The check names that case
specifically rather than reporting 178 ordinary disagreements:

    predictions  66 of 244 recomputed predictions match the recorded nibble; 178 disagree
      every recorded nibble is zero while the recomputed ones are not: this stream looks repacked
      without the high nibble of the last byte, rather than genuinely disagreeing
    against final.slot: IDENTICAL byte for byte
    FAILED: verification was requested and 178 recorded prediction(s) do not match

A single corrupted nibble is reported with its lesson index and both values:

    lesson 3: recorded 9, recomputed 3 (taught 1 absolute, 2 raw)

## It fails closed

The replay refuses rather than reinterpreting. Each of these is rejected by name, with the reason:

    a BRAIN02 slot                 this is a BRAIN02 slot (marker b'BRAIN02\x00'). Migrate it first
    layout byte 2, not 3           layout byte is 2, not 3
    header says 64 inputs          header says 64 inputs but retina 5 has 80 entries
    retina id 2                    retina id 2 is unknown to this reference (known: [5])
    output count 9                 output count is 9, not 10
    rule version 3                 rule version is 3, not 2
    marker BRAIN99                 marker is b'BRAIN99\x00', not b'BRAIN025'
    slot truncated by one byte     833 bytes, but 80 inputs need exactly 834
    lesson stream 7 bytes over     3667 bytes, not a multiple of the 15-byte LESSON25 entry
    a taught action of 11          lesson 0: taught action 11 is not one of the ten outputs

It also reports, without refusing, any entry that changed no weights. The machine records a lesson only
when it takes one, so a stream straight off the machine should show zero of those. Anything above zero
means the stream and the starting slot do not belong together.

## The proof

A real session, not another copy of the same Python checked against itself. Recorded by
`python3 tools/brain025_test.py session src/kickass/tony-b025-a.prg`, with the ring capacity lowered to
40 so the stream crosses reuse cycles rather than sitting inside one fill.

    deliverables/brain025/replay/session-1/
      start.slot    834 bytes   a blank brain, education 0
      lessons.bin  3660 bytes   244 entries of 15, drained 9 times, 6.1 ring fills
      final.slot    834 bytes   the machine's own exported brain, education 244
      session.json              the hashes and the recording conditions

Replayed:

    $ python3 tools/brain025_ref.py replay \
        deliverables/brain025/replay/session-1/start.slot \
        deliverables/brain025/replay/session-1/lessons.bin \
        --expect deliverables/brain025/replay/session-1/final.slot

      starting slot   834 bytes, 80 inputs, retina 5, vocabulary reference-relative, education 0
      lesson stream   3660 bytes, 244 entries of 15
      applied         244 lessons; 0 left the weights alone
      education       0 -> 244
      brain hash      f88f9b61ba509825 -> 5a6ce11734830cc76f091615576528dfb499c4e4e11beb402e85c35c8a95202e
      predictions     244 of 244 recomputed predictions match the recorded nibble
      against final.slot: IDENTICAL byte for byte

Exit 0. All 244 applied, none inert, every recorded prediction independently reproduced, and the
behavioural hash equal to the machine's.

## Independently confirmed

The manager session pulled this reference from the pushed tree and replayed the owner's own first human
BRAIN02.5 session, which is a different session from the one recorded here. Their second machine epoch
began from the same blank behavioural hash as the reference's, `f88f9b61ba509825`, and its 56 recorded
entries, repacked from the workbench JSON, replayed to
`523193cf6ea1fb41c8bec67d15ae4a520ad997343eece7ded38e287cf91b3d74` with all 834 bytes identical to the
brain the C64 exported. They also recomputed the prediction at every lesson across both machine lives,
163 of 163 matching, which is the check this tool now performs on request.

## What this does not cover

The replay reconstructs weights from lessons. It does not verify that the lessons themselves were
recorded correctly, which is the drain gate's job and is proved separately: acknowledgements validated
against an exact range and a checksum, a full ring pausing learning rather than applying an unrecorded
lesson, and a split run replaying to the uninterrupted one byte for byte.
