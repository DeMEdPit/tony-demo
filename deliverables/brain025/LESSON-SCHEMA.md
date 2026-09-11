# BRAIN02.5: the lesson record, version 2

Marker `LESSON25`, entry size **15 bytes**, ring capacity **180** at boot. Version 2 is declared in the
descriptor and is not BRAIN02's: a BRAIN02 lesson is eleven bytes and carries twenty nibbles.

## The entry

| bytes | what |
|---|---|
| 0 to 13 | the twenty-seven sense nibbles, nibble *i* in byte *i*/2, the low half for even *i*. The twenty-seventh nibble has no partner, so it sits alone in the low half of byte 13 and that byte's high half is zero. |
| 14 | the taught action, absolute, in the low nibble; the mood-free prediction the brain made in the high nibble. |

Nibbles 0 to 19 are BRAIN02's senses, unchanged. Nibbles 20 to 26 are the seven terrain quantities, in
the order `tSafeRun`, `tGapW`, `tFarRun`, `tObstH`, `tObstTop`, `tHead`, `tBackRoom`, each an unsigned
value 0 to 7.

The lesson with sequence *s* lives at `lessonData + (s mod capacity) * 15`. Unread lessons are the
half-open range `[read_seq, write_seq)`.

## What it lets an independent implementation do

Everything, without ever seeing the room. Given one entry alone a replayer can:

1. sign-extend nibbles 0 to 19 into the twenty senses;
2. derive the nine pseudo-senses from them, exactly as BRAIN02 does;
3. read the seven terrain quantities straight out of nibbles 20 to 26;
4. evaluate all eighty inputs through the published retina table;
5. resolve `h` from senses 1 and 3 and translate the taught absolute action into the relative index;
6. apply the rule.

The terrain quantities are **in the record** rather than recomputed, which is the point: a replayer does
not need the screen, the materials table, the brick layout, or any browser-side state, and there is
nothing it could get wrong about geometry. The cost is four bytes per lesson and a smaller ring.

## What is preserved from BRAIN02

* **Atomicity.** A lesson is recorded and applied together, or neither happens. A full ring pauses
  learning and flashes red; it never applies a lesson it did not record.
* **The hardened drain.** Monotonic `write_seq` and `read_seq`, a host acknowledgement that must name
  the exact range and carry a byte checksum over it, and reclamation only after the machine validates
  both. A wrong checksum sets status bit 2, a stale range sets bit 1, and neither reclaims anything.
* **Deterministic replay.** The machine's own lesson stream, drained in batches across ring reuse
  cycles, replayed uninterrupted by the machine and by the reference, gives the same weights, the same
  education count and the same behavioural hash. Measured: 126 lessons in 5 batches, byte for byte.

## Capacity

180, down from BRAIN02's 300. The ring lives in the memory the level tune vacates at startup, between
its own start and `$A000`; the entry grew from 11 bytes to 15 and the brain's shadow grew from 640
bytes to 800, so less room is left. This is reported, not defended: a teaching session longer than 180
lessons needs one drain, which the handshake already supports and the drain gate exercises eight times
over.
