# BRAIN02: the exact byte budget (analysis only; nothing is built)

Computed by `tools/bakeoff2.py budget` against the map of this build (`src/kickass/tony-body.sym`,
`BODY.md`): the body's code and data end at `$863e`; the Movable segment follows in the file and is
copied out at startup, so `$863f`–`$9fff` (6,593 bytes) is free at run time and holds the teaching
shadow (`TEACH_SHADOW`, 256 bytes at `$8900`) and the lesson block (`LESSON1` at `$8a00`, 500 lessons
of 11 bytes plus 16 = 5,516 bytes, ending at `$9f8b`; the generator's comment says `$9D8C`, a slip
for `$9F8C`, left as is because nothing in the PRG changes in this phase); the level tune lives at
`$a000` from then on. A byte-weight, flag-input brain retires the `BRAIN01` slot (280 bytes), the
nibble multiply table (`brainMul`, 256) and the two nibble-expansion buffers (`evenHi`, `oddLo`, 20).

The owner's requirement: do not assume at once that the slot is about 1 KB and that it holds 128
byte-weight inputs. It does not: 128 inputs need 16 + 1,280 + 8 = **1,304 bytes** before any table.

## 1. The slot, exactly

Marker 8 (`BRAIN02` and a zero), header 8 (kind, layout, inputs, hidden, outputs, period, lineage,
rule version 2), weights 10 rows of n signed bytes, mood 8 as today (ten signed nibbles, five bytes
used; its scale against unit flags is a Phase 3 question, not decided here). The slot starts at a page
boundary (found by its marker, as `BRAIN01` is) and its length need not be a multiple of 256; the
padding before the marker is whatever the code before it leaves, up to 255 bytes, as today.

| architecture | inputs n | header | weights | mood | **slot, exact** | whole pages | spare in those pages | inputs those pages could hold | retina as a table | flag vector (RAM) | teaching shadow |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R0 (BIN) | 56 | 16 | 560 | 8 | **584** | 3 (768) | 184 | 74 | 168 | 56 | 560 |
| R0s (BIN with a signed dx thermometer, exploratory, `PHASE1B.md` section 6) | 61 | 16 | 610 | 8 | **634** | 3 (768) | 134 | 74 | 183 | 61 | 610 |
| R1 (BIN + 6 facts) | 62 | 16 | 620 | 8 | **644** | 3 (768) | 124 | 74 | 192 | 62 | 620 |
| R1b (R1 + 2 facts) | 64 | 16 | 640 | 8 | **664** | 3 (768) | 104 | 74 | 200 | 64 | 640 |
| R1b + the goal senses as 33 flags | 97 | 16 | 970 | 8 | **994** | 4 (1,024) | 30 | 100 | 299 | 97 | 970 |
| R2 (R1b + order-2, offline ceiling) | 337 | 16 | 3,370 | 8 | **3,394** | 14 (3,584) | 190 | 356 | 746 | 337 | 3,370 |

The retina as a table: 3 bytes per threshold flag (sense, comparison, threshold; the 56 of BIN), 4
per conjunction of two flags (the six and the two named facts), 2 per order-2 pair over base flags,
3 per goal flag. As code instead of a table the retina is an estimate of 150 to 400 bytes (a
compare-and-store per flag, or a small interpreter over the table); the estimate is labelled as one
everywhere below and is the only number here that is not exact.

## 2. The accumulator, recomputed

Every input is a flag of 1, weights are bytes, the mood term is `m * 16` with `m` in -8..7:
`|acc| <= n * 128 + 128`. Selected maximum input count **128**: bound 16,512, positive extreme 16,368,
negative -16,512, inside 16 bits with room (asserted in `parity-1b.json`). The header's input byte
allows 255; at 255 the bound is 32,768 with the negative extreme exactly -32,768 and no slack, so 128
is the number to publish. R2 at 337 inputs: bound 43,264, **outside 16 bits** and outside the header;
it cannot be a BRAIN02 in this form (it would need a 24-bit accumulator or a two-byte input count and
a different slot), which is one more reason it stays an offline ceiling.

## 3. The code region

The slot replaces `BRAIN01`; the multiply table and the expansions go; the retina table and the flag
vector come; the retina's code is the estimate.

| architecture | slot − 280 − 256 − 20 + table + flag vector | with the code estimate (150..400) |
|---|---:|---|
| R0 | +252 | +402 to +652 |
| R0s | +322 | +472 to +722 |
| R1 | +342 | +492 to +742 |
| R1b | +372 | +522 to +772 |
| R1b + goal | +834 | +984 to +1,234 |
| R2 | +3,921 | +4,071 to +4,321 |

## 4. The run-time region: the shadow and the lesson block must still fit

The shadow is a full copy of the weights (10 n bytes, against 256 today) and the lesson block keeps
its size (the lesson stays 11 bytes: the raw senses and the applied action, the retina applied on both
sides; 14 bytes as `LESSON2` once the goal senses exist). Both must sit between the new end of the code
and `$a000`. The largest code growth the map allows, by lesson cap:

| architecture | cap 500 | cap 400 | cap 300 | the cap that fits at the high code estimate |
|---|---:|---:|---:|---:|
| R0 | 517 | 1,617 | 2,717 | **487** (500 at the low estimate) |
| R0s | 467 | 1,567 | 2,667 | **476** |
| R1 | 457 | 1,557 | 2,657 | **474** |
| R1b | 437 | 1,537 | 2,637 | **469** |
| R1b + goal (`LESSON2`, 14 bytes a lesson) | −1,393 | 7 | 1,407 | **312** |
| R2 | −2,293 | −1,193 | −93 | never |

Read against section 3: **R0 fits the present map at the 500-lesson cap only if its retina code stays
under about 265 bytes**; R1 and R1b do not fit at 500 (they need about 115 and 65 bytes of code, which
is not realistic) and fit at a cap of about 470; with the goal senses and `LESSON2` the cap must come
down to about 310. Every lesson of cap costs 11 (or 14) bytes. The alternatives are a Phase 3 decision,
not made here: a lower cap (the E5 demo used 36 lessons; the curriculum's longest pass took 525 over
15 episodes, so 300 to 470 is not obviously too few for one session, and the page can drain the block);
or relocating the block to memory the map has not claimed (the kilobyte under the screen at `$c000`
is a candidate the generator's copies do not name, to be verified before it is counted).

Two more costs that are not bytes: the shadow copy that today takes 57 raster lines for 256 bytes
becomes 560 to 970 bytes (about 125 to 215 lines), which cannot stay inside the frame path that
already reaches 188 of the 230-line bench (it must move to the main loop or spread over frames); and
the think, which becomes n adds per row instead of 20 nibble multiplies, cheaper than today for every
architecture but R2.

## 5. The zero-byte option, for the record

Under the relative vocabulary the mixed control `T36` (raw plus dy-up thermometer, dx sign, |dx|
thermometer, 36 inputs) fits the 231 at the 4-bit box on the curriculum stream (499 lessons, held
276 of 300, `PHASE2B.md`), and 36 nibble inputs are within the present `BRAIN01` weight area (360
nibbles of 512), so V alone, with no slot change, would buy the curriculum fit. It is not a
recommendation: it keeps the multiply table, it does not fit the 474 (best 449, cycles), and it is
the box the pre-registration set out to leave. It is the cheapest thing that works and is listed so
the comparison is honest.

## 6. Survivors, as the pre-registered rule scored them

No arm survived the rule as written, because the S5 stream cannot be passed by any policy
(`PHASE2B.md` section 3). On the remaining criteria the binary arms R0, R1 and R1b survive at 6 and 8
bits under both vocabularies (R0 also at 4 bits under V), which is why they are the rows above; R0s is
the exploratory arm of `PHASE1B.md` section 6, added for the comparison and not a survivor of anything
pre-registered; R2 is
kept as the offline ceiling and does not fit the machine; the goal-sense row is the planned extension
of `GOAL-SENSES.md`, whose senses stay sealed and untouched in this phase.
