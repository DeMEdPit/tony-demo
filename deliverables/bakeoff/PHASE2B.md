# Phase 2b: learnability by the exact rule at boxes of 4, 6 and 8 bits (results)

Run as pre-registered in `PREREG-1B.md` (commit bcba27f). The rule is the program's own (the mood-free
prediction, a lesson when the prediction differs from the taught action, the taught row up and the
predicted row down by the sign of each input, saturating at the box), generalised to n inputs and a
box; before any 6- or 8-bit number was read, the vectorised learner was checked weight for weight and
lesson for lesson against the generalised reference on six arm/box combinations, and that reference
against the golden reference itself at the 4-bit box (`parity-1b.json`: all identical). Zero initial
weights, 300 passes, both vocabularies, every arm, streams S1 (the 1,484-tick curriculum stream), S2
(the 231 labels cycled), S4 (S1 with 5% of the labels replaced by another action, fresh every pass)
and S5 (S1 with every label delayed one tick). Data: `phase2b.json` (every run's curves, clamps, weight
magnitudes and final weights). Agreement is always against the clean teacher labels of the 231, and
"474" is the agreement on the teacher-visited union after the same training.

One addition after the pre-registration, marked as such: **S2u, the 474 labels cycled**, because the
review's central 474-state claim was made on that stream (training on the union itself), not on the
231-state streams the pre-registration listed. It changes no pre-registered criterion.

## 1. The review's numbers, reproduced

The review's table (its section 2 and section 5), against the engine's runs of the same stream on the
same arm. Cells are "agreement at the end" for runs that never fit, and "lessons to the first full
pass, passes held" for runs that did.

| arm, box | stream | the review | the engine | same? |
|---|---|---|---|---|
| T36, 4-bit | S2 / S1 | 227 / 229, clamps 523 | 227 / 229, clamps 523 | identical |
| T36, 6-bit | S2 / S1 | 228 / 229, 0 clamps, max 25 | 228 / 229, 0 clamps, max 25 | identical |
| T36, 8-bit | S2 / S1 | 228 / 229, 0 clamps, max 25 | 228 / 229, 0 clamps, max 25 | identical |
| A2, 4-bit | S2 / S1 | 228 / 228, clamps 38 | 228 / 228, clamps 38 | identical |
| A2, 8-bit | S2 / S1 | 228 / 229, 0 clamps, max 16 | 228 / 229, 0 clamps, max 16 | identical |
| BIN (R0), 4-bit | S2 / S1 | 227 / 229, clamps 931 | 227 / 229, clamps 931 | identical |
| BIN (R0), 6-bit | S2 / S1 | 231 at 428, held 263 / 231 at 384, held 277, max 25 | 231 at 428, held 263 / 231 at 384, held 277, max 25 | identical |
| BIN (R0), 8-bit | S2 / S1 | as 6-bit | as 6-bit | identical |
| BIN under V, 8-bit, the 231 | S2 | 231 at 182, held 289 | 231 at 182, held 289 | identical |
| BIN under V, 4-bit, the 231 | S2 | 231 at 359, held 271 | 231 at 359, held 271 | identical |
| BIN under V, 8-bit, the 474 | S2u | 474 at 779, held 269 | 474 at 849, held 259 | the same claim; the lesson count depends on the cycle order, which the review did not publish |
| BIN under V, 4-bit, the 474 | S2u | 449, cycles | best 457, final 424, cycles | the same claim |
| BIN absolute, 8-bit, the 474, the rule as a bound | S2u | 472 of 474 | best 473 of 474 (final 470) | the engine's rule does one state better; the exact minimum is Phase 1b's |

Where the streams are the same, every number of the review reproduces to the lesson. The
implementation the review imported (`bakeoff.py`'s rule) and the engine's re-implementation for this
phase agree, and both agree with the golden reference. The falsifier "if R0 at 8 bits fails to converge
here, the harness or the reference differs" did not fire.

## 2. Every arm, both vocabularies, at 8 and at 4 bits

The 6-bit runs are identical to the 8-bit runs on S1 and S2 for every arm except `raw20` (whose
weights reach 32 there and clamp); they differ from 8 bits only in some S4 and S5 cells and are in
`phase2b.json`. "Held" is passes at full agreement out of 300. On S4 the cell gives the best agreement,
the mean agreement at the end of each of the last 100 passes, and the lessons per pass split into
clean ticks and corrupted ticks. On S5 the best and final agreement against the clean labels.

### Absolute vocabulary, 8 bits

| arm | n | S1 tick stream | S2 labels cycled | S4 noisy human | S5 lagging human | 474 agreement from S1 |
|---|---:|---|---|---|---|---|
| `R0` | 56 | full at 384, held 277/300, clamps 0, max\|w\| 23 | full at 428, held 263/300, clamps 0, max\|w\| 25 | best 230, mean of the last 100 passes 205, clean lessons/pass 76 beside 72 corrupted | best 179, final 178 | 425/474 (final 413) |
| `R1` | 62 | full at 374, held 271/300, clamps 0, max\|w\| 23 | full at 371, held 264/300, clamps 0, max\|w\| 22 | best 230, mean of the last 100 passes 203, clean lessons/pass 78 beside 72 corrupted | best 179, final 178 | 430/474 (final 413) |
| `R1b` | 64 | full at 379, held 270/300, clamps 0, max\|w\| 23 | full at 409, held 260/300, clamps 0, max\|w\| 24 | best 230, mean of the last 100 passes 204, clean lessons/pass 75 beside 72 corrupted | best 179, final 178 | 431/474 (final 421) |
| `R2` | 337 | full at 163, held 295/300, clamps 0, max\|w\| 14 | full at 193, held 285/300, clamps 0, max\|w\| 16 | best 231, mean of the last 100 passes 215, clean lessons/pass 71 beside 72 corrupted | best 178, final 178 | 425/474 (final 425) |
| `raw20` | 20 | never; best 222, final 221, clamps 0, max\|w\| 50 | never; best 219, final 219, clamps 0, max\|w\| 36 | best 211, mean of the last 100 passes 176, clean lessons/pass 103 beside 71 corrupted | best 165, final 158 | 402/474 (final 397) |
| `T36` | 36 | never; best 229, final 229, clamps 0, max\|w\| 25 | never; best 228, final 228, clamps 0, max\|w\| 25 | best 229, mean of the last 100 passes 206, clean lessons/pass 81 beside 72 corrupted | best 179, final 178 | 416/474 (final 415) |
| `A2` | 55 | never; best 229, final 229, clamps 0, max\|w\| 16 | never; best 228, final 228, clamps 0, max\|w\| 13 | best 230, mean of the last 100 passes 198, clean lessons/pass 79 beside 72 corrupted | best 180, final 178 | 413/474 (final 409) |

### Absolute vocabulary, 4 bits

| arm | n | S1 tick stream | S2 labels cycled | S4 noisy human | S5 lagging human | 474 agreement from S1 |
|---|---:|---|---|---|---|---|
| `R0` | 56 | never; best 229, final 229, clamps 931, max\|w\| 8 | never; best 227, final 227, clamps 759, max\|w\| 8 | best 228, mean of the last 100 passes 192, clean lessons/pass 90 beside 72 corrupted | best 181, final 172 | 399/474 (final 396) |
| `R1` | 62 | never; best 230, final 229, clamps 740, max\|w\| 8 | never; best 229, final 229, clamps 759, max\|w\| 8 | best 226, mean of the last 100 passes 191, clean lessons/pass 91 beside 72 corrupted | best 181, final 173 | 418/474 (final 413) |
| `R1b` | 64 | never; best 228, final 228, clamps 778, max\|w\| 8 | never; best 227, final 227, clamps 722, max\|w\| 8 | best 228, mean of the last 100 passes 186, clean lessons/pass 87 beside 71 corrupted | best 170, final 155 | 413/474 (final 413) |
| `R2` | 337 | never; best 230, final 230, clamps 1862, max\|w\| 8 | full at 236, held 288/300, clamps 125, max\|w\| 8 | best 231, mean of the last 100 passes 212, clean lessons/pass 76 beside 71 corrupted | best 169, final 162 | 422/474 (final 422) |
| `raw20` | 20 | never; best 202, final 192, clamps 8512, max\|w\| 8 | never; best 197, final 170, clamps 5969, max\|w\| 8 | best 190, mean of the last 100 passes 132, clean lessons/pass 122 beside 71 corrupted | best 155, final 136 | 370/474 (final 346) |
| `T36` | 36 | never; best 229, final 229, clamps 523, max\|w\| 8 | never; best 227, final 227, clamps 144, max\|w\| 8 | best 222, mean of the last 100 passes 194, clean lessons/pass 94 beside 72 corrupted | best 189, final 166 | 409/474 (final 398) |
| `A2` | 55 | never; best 228, final 228, clamps 38, max\|w\| 8 | never; best 228, final 228, clamps 32, max\|w\| 8 | best 228, mean of the last 100 passes 196, clean lessons/pass 81 beside 72 corrupted | best 181, final 168 | 408/474 (final 408) |

### Reference-relative vocabulary V, 8 bits

| arm | n | S1 tick stream | S2 labels cycled | S4 noisy human | S5 lagging human | 474 agreement from S1 |
|---|---:|---|---|---|---|---|
| `R0` | 56 | full at 194, held 294/300, clamps 0, max\|w\| 19 | full at 182, held 289/300, clamps 0, max\|w\| 17 | best 231, mean of the last 100 passes 206, clean lessons/pass 73 beside 72 corrupted | best 178, final 178 | 410/474 (final 410) |
| `R1` | 62 | full at 161, held 289/300, clamps 0, max\|w\| 17 | full at 144, held 291/300, clamps 0, max\|w\| 14 | best 231, mean of the last 100 passes 209, clean lessons/pass 71 beside 72 corrupted | best 184, final 178 | 436/474 (final 436) |
| `R1b` | 64 | full at 185, held 293/300, clamps 0, max\|w\| 20 | full at 154, held 292/300, clamps 0, max\|w\| 17 | best 231, mean of the last 100 passes 209, clean lessons/pass 72 beside 72 corrupted | best 178, final 178 | 433/474 (final 433) |
| `R2` | 337 | full at 158, held 295/300, clamps 0, max\|w\| 14 | full at 143, held 294/300, clamps 0, max\|w\| 15 | best 231, mean of the last 100 passes 215, clean lessons/pass 70 beside 71 corrupted | best 178, final 178 | 414/474 (final 414) |
| `raw20` | 20 | never; best 211, final 207, clamps 0, max\|w\| 68 | never; best 210, final 200, clamps 0, max\|w\| 60 | best 201, mean of the last 100 passes 173, clean lessons/pass 112 beside 71 corrupted | best 175, final 163 | 375/474 (final 362) |
| `T36` | 36 | full at 197, held 291/300, clamps 0, max\|w\| 19 | full at 197, held 289/300, clamps 0, max\|w\| 23 | best 231, mean of the last 100 passes 214, clean lessons/pass 73 beside 71 corrupted | best 181, final 178 | 419/474 (final 414) |
| `A2` | 55 | full at 154, held 295/300, clamps 0, max\|w\| 14 | full at 146, held 291/300, clamps 0, max\|w\| 13 | best 231, mean of the last 100 passes 206, clean lessons/pass 73 beside 71 corrupted | best 182, final 178 | 423/474 (final 423) |

### Reference-relative vocabulary V, 4 bits

| arm | n | S1 tick stream | S2 labels cycled | S4 noisy human | S5 lagging human | 474 agreement from S1 |
|---|---:|---|---|---|---|---|
| `R0` | 56 | full at 395, held 276/300, clamps 299, max\|w\| 8 | full at 359, held 271/300, clamps 257, max\|w\| 8 | best 230, mean of the last 100 passes 202, clean lessons/pass 86 beside 71 corrupted | best 184, final 167 | 414/474 (final 395) |
| `R1` | 62 | never; best 229, final 216, clamps 1305, max\|w\| 8 | full at 228, held 285/300, clamps 141, max\|w\| 8 | best 231, mean of the last 100 passes 199, clean lessons/pass 82 beside 71 corrupted | best 181, final 169 | 415/474 (final 388) |
| `R1b` | 64 | never; best 230, final 230, clamps 1869, max\|w\| 8 | never; best 215, final 215, clamps 1214, max\|w\| 8 | best 230, mean of the last 100 passes 201, clean lessons/pass 82 beside 71 corrupted | best 183, final 168 | 414/474 (final 414) |
| `R2` | 337 | never; best 229, final 229, clamps 1901, max\|w\| 8 | never; best 229, final 229, clamps 686, max\|w\| 8 | best 231, mean of the last 100 passes 213, clean lessons/pass 76 beside 72 corrupted | best 168, final 160 | 414/474 (final 414) |
| `raw20` | 20 | never; best 183, final 169, clamps 7879, max\|w\| 8 | never; best 183, final 155, clamps 5837, max\|w\| 8 | best 185, mean of the last 100 passes 131, clean lessons/pass 121 beside 71 corrupted | best 160, final 136 | 347/474 (final 314) |
| `T36` | 36 | full at 499, held 276/300, clamps 471, max\|w\| 8 | full at 470, held 263/300, clamps 405, max\|w\| 8 | best 229, mean of the last 100 passes 201, clean lessons/pass 90 beside 71 corrupted | best 176, final 156 | 410/474 (final 405) |
| `A2` | 55 | full at 161, held 294/300, clamps 19, max\|w\| 8 | full at 154, held 290/300, clamps 17, max\|w\| 8 | best 231, mean of the last 100 passes 207, clean lessons/pass 75 beside 71 corrupted | best 164, final 161 | 424/474 (final 424) |

### S2u, the 474 labels cycled (post-registration addition)

"the 231" is the agreement on the 231 subset at the end.

Absolute vocabulary:

| arm | 8 bits | 6 bits | 4 bits |
|---|---|---|---|
| `R0` | never; best 473, final 470, clamps 0, max\|w\| 56; the 231: 229/231 | never; best 473, final 469, clamps 78, max\|w\| 31; the 231: 229/231 | never; best 448, final 422, clamps 14707, max\|w\| 8; the 231: 206/231 |
| `R1` | never; best 472, final 468, clamps 0, max\|w\| 47; the 231: 227/231 | never; best 473, final 460, clamps 40, max\|w\| 32; the 231: 224/231 | never; best 456, final 431, clamps 14799, max\|w\| 8; the 231: 209/231 |
| `R1b` | never; best 473, final 467, clamps 0, max\|w\| 52; the 231: 228/231 | never; best 472, final 470, clamps 39, max\|w\| 32; the 231: 229/231 | never; best 453, final 446, clamps 15692, max\|w\| 8; the 231: 218/231 |
| `R2` | full at 680, held 257/300, clamps 0, max\|w\| 37; the 231: 231/231 | full at 711, held 246/300, clamps 19, max\|w\| 32; the 231: 231/231 | never; best 469, final 465, clamps 6601, max\|w\| 8; the 231: 226/231 |
| `raw20` | never; best 436, final 419, clamps 46, max\|w\| 128; the 231: 209/231 | never; best 429, final 414, clamps 2382, max\|w\| 32; the 231: 206/231 | never; best 411, final 328, clamps 7788, max\|w\| 8; the 231: 145/231 |
| `T36` | never; best 472, final 472, clamps 0, max\|w\| 63; the 231: 229/231 | never; best 472, final 472, clamps 157, max\|w\| 32; the 231: 229/231 | never; best 448, final 415, clamps 16813, max\|w\| 8; the 231: 207/231 |
| `A2` | never; best 472, final 472, clamps 0, max\|w\| 36; the 231: 229/231 | never; best 471, final 471, clamps 13, max\|w\| 31; the 231: 228/231 | never; best 460, final 443, clamps 7534, max\|w\| 8; the 231: 220/231 |

Reference-relative vocabulary V:

| arm | 8 bits | 6 bits | 4 bits |
|---|---|---|---|
| `R0` | full at 849, held 259/300, clamps 0, max\|w\| 39; the 231: 231/231 | full at 915, held 249/300, clamps 10, max\|w\| 31; the 231: 231/231 | never; best 457, final 424, clamps 14270, max\|w\| 8; the 231: 209/231 |
| `R1` | full at 579, held 276/300, clamps 0, max\|w\| 32; the 231: 231/231 | full at 581, held 276/300, clamps 2, max\|w\| 31; the 231: 231/231 | never; best 462, final 403, clamps 13552, max\|w\| 8; the 231: 197/231 |
| `R1b` | full at 538, held 279/300, clamps 0, max\|w\| 33; the 231: 231/231 | full at 538, held 279/300, clamps 2, max\|w\| 31; the 231: 231/231 | never; best 461, final 453, clamps 14389, max\|w\| 8; the 231: 223/231 |
| `R2` | full at 496, held 279/300, clamps 0, max\|w\| 28; the 231: 231/231 | full at 496, held 279/300, clamps 0, max\|w\| 28; the 231: 231/231 | never; best 468, final 459, clamps 8458, max\|w\| 8; the 231: 221/231 |
| `raw20` | never; best 402, final 384, clamps 0, max\|w\| 82; the 231: 193/231 | never; best 405, final 383, clamps 1446, max\|w\| 32; the 231: 185/231 | never; best 394, final 353, clamps 5805, max\|w\| 8; the 231: 158/231 |
| `T36` | never; best 470, final 465, clamps 0, max\|w\| 42; the 231: 228/231 | never; best 472, final 467, clamps 42, max\|w\| 32; the 231: 227/231 | never; best 449, final 389, clamps 18698, max\|w\| 8; the 231: 191/231 |
| `A2` | never; best 472, final 467, clamps 0, max\|w\| 30; the 231: 227/231 | never; best 472, final 467, clamps 0, max\|w\| 30; the 231: 227/231 | never; best 463, final 450, clamps 7023, max\|w\| 8; the 231: 218/231 |

## 3. The survivor rule, applied as pre-registered

"Full agreement on the 231 within 500 lessons on S1, held for 80% of the remaining passes; on S4 and
S5 the best agreement within five states of the clean run."

| arm | vocabulary | bits | S1: full within 500 lessons, held 80% | S4 best within 5 | S5 best within 5 | verdict |
|---|---|---:|---|---|---|---|
| `R0` | abs | 8 | yes (384, held 277) | yes (230) | no (179) | S1 and S4 only |
| `R0` | abs | 6 | yes (384, held 277) | yes (230) | no (179) | S1 and S4 only |
| `R0` | abs | 4 | no (None, held 0) | yes (228) | no (181) | no |
| `R0` | rel | 8 | yes (194, held 294) | yes (231) | no (178) | S1 and S4 only |
| `R0` | rel | 6 | yes (194, held 294) | yes (231) | no (178) | S1 and S4 only |
| `R0` | rel | 4 | yes (395, held 276) | yes (230) | no (184) | S1 and S4 only |
| `R1` | abs | 8 | yes (374, held 271) | yes (230) | no (179) | S1 and S4 only |
| `R1` | abs | 6 | yes (374, held 271) | yes (230) | no (179) | S1 and S4 only |
| `R1` | abs | 4 | no (None, held 0) | yes (226) | no (181) | no |
| `R1` | rel | 8 | yes (161, held 289) | yes (231) | no (184) | S1 and S4 only |
| `R1` | rel | 6 | yes (161, held 289) | yes (231) | no (184) | S1 and S4 only |
| `R1` | rel | 4 | no (None, held 0) | yes (231) | no (181) | no |
| `R1b` | abs | 8 | yes (379, held 270) | yes (230) | no (179) | S1 and S4 only |
| `R1b` | abs | 6 | yes (379, held 270) | yes (230) | no (179) | S1 and S4 only |
| `R1b` | abs | 4 | no (None, held 0) | yes (228) | no (170) | no |
| `R1b` | rel | 8 | yes (185, held 293) | yes (231) | no (178) | S1 and S4 only |
| `R1b` | rel | 6 | yes (185, held 293) | yes (231) | no (178) | S1 and S4 only |
| `R1b` | rel | 4 | no (None, held 0) | yes (230) | no (183) | no |
| `R2` | abs | 8 | yes (163, held 295) | yes (231) | no (178) | S1 and S4 only |
| `R2` | abs | 6 | yes (163, held 295) | yes (231) | no (173) | S1 and S4 only |
| `R2` | abs | 4 | no (None, held 0) | yes (231) | no (169) | no |
| `R2` | rel | 8 | yes (158, held 295) | yes (231) | no (178) | S1 and S4 only |
| `R2` | rel | 6 | yes (158, held 295) | yes (231) | no (172) | S1 and S4 only |
| `R2` | rel | 4 | no (None, held 0) | yes (231) | no (168) | no |
| `raw20` | abs | 8 | no (None, held 0) | no (211) | no (165) | no |
| `raw20` | abs | 6 | no (None, held 0) | no (203) | no (157) | no |
| `raw20` | abs | 4 | no (None, held 0) | no (190) | no (155) | no |
| `raw20` | rel | 8 | no (None, held 0) | no (201) | no (175) | no |
| `raw20` | rel | 6 | no (None, held 0) | yes (206) | no (161) | no |
| `raw20` | rel | 4 | no (None, held 0) | yes (185) | no (160) | no |
| `T36` | abs | 8 | no (None, held 0) | yes (229) | no (179) | no |
| `T36` | abs | 6 | no (None, held 0) | yes (230) | no (178) | no |
| `T36` | abs | 4 | no (None, held 0) | no (222) | no (189) | no |
| `T36` | rel | 8 | yes (197, held 291) | yes (231) | no (181) | S1 and S4 only |
| `T36` | rel | 6 | yes (197, held 291) | yes (231) | no (173) | S1 and S4 only |
| `T36` | rel | 4 | yes (499, held 276) | yes (229) | no (176) | S1 and S4 only |
| `A2` | abs | 8 | no (None, held 0) | yes (230) | no (180) | no |
| `A2` | abs | 6 | no (None, held 0) | yes (230) | no (178) | no |
| `A2` | abs | 4 | no (None, held 0) | yes (228) | no (181) | no |
| `A2` | rel | 8 | yes (154, held 295) | yes (231) | no (182) | S1 and S4 only |
| `A2` | rel | 6 | yes (154, held 295) | yes (231) | no (178) | S1 and S4 only |
| `A2` | rel | 4 | yes (161, held 294) | yes (231) | no (164) | S1 and S4 only |

**No arm survives the rule as written, and the reason is S5, not the arms.** The lagged stream pairs
every state with the label of the tick before it, so a deterministic policy that fits S5's labels
perfectly agrees with the clean labels on at most **178 of 231** states (the majority lagged label
against the clean one, per state; no state carries conflicting lagged labels, so this is exact and the
same under V: 178). Every arm's best S5 agreement is 178 to 189: at the ceiling, or a few above it
where the brain fails to fit some lagged labels and happens to match the clean ones. The 53 states the
lag relabels are precisely the decisive ones (the tick before a press is now taught the press, the
press's own tick is taught what came before). So S5 as pre-registered does not measure robustness to a
lagging teacher; it measures agreement with a different teacher, and the criterion "within five of the
clean run" is unreachable by any policy. That is a defect in the pre-registered stream, reported as
such; it is not evidence about any arm. What a lagging human costs is a behavioural question for Phase
4 (the brain would learn to act one tick late, which the machine may or may not tolerate), and a future
offline version of S5 should measure agreement with the lagged labels themselves.

Under the other three criteria (S1 within 500 lessons and held, S4 within five), the binary arms
`R0`, `R1`, `R1b` and `R2` pass at 6 and at 8 bits under both vocabularies; under V, `R0` also passes
at 4 bits, and so do the mixed controls `T36` (8, 6 and, at 499 lessons, 4 bits) and `A2` (8, 6, 4).
Under the absolute vocabulary nothing passes at 4 bits and no mixed control passes at any box.

## 4. What the streams say

- **S1 and S2 (clean).** With the box widened to 6 or 8 bits, every binary retina learns the 231 from
  zero in 371 to 428 lessons (absolute) or 144 to 194 lessons (V), and holds. The six named facts of
  `R1` and the two of `R1b` change the absolute-vocabulary lesson counts by a few lessons either way
  (374, 379 against 384) and under V bring them down (161, 185 against 194). `R2` learns **fastest**
  of all (163 absolute, 158 under V, held 295 of 300): the order-2 layer, predicted by the review to
  learn slower for its many active inputs, learns in under half the lessons. The reason is that its
  conjunctions give the build-direction states private inputs, so the corrections stop fighting over
  shared weights.
- **The 4-bit box.** Under the absolute vocabulary no binary arm fits the 231 at 4 bits on S1 (227 to
  230, hundreds of clamps, the four-lesson cycle): Phase 2's result, reproduced; `R2` alone fits it on
  the cycled labels (236 lessons, held 288). Under V, `R0` fits at 4 bits on S1 (395 lessons, held 276)
  and so do `T36` and `A2`; `R1`, `R1b` and `R2` do not on S1 (`R1` does on S2, at 228). The 4-bit box
  is enough for the easy target and not for the hard one.
- **S4, the noisy human.** The best agreement is within one of the clean run everywhere (the
  pre-registered criterion holds), but the fit does not hold: with 5% of the labels wrong the rule
  takes about 72 lessons a pass on the corrupted ticks and about 70 to 80 more on clean ticks to undo
  them, and the agreement at the end of a pass averages 200 to 215 over the last hundred passes. The
  review's prediction "under ten lessons per pass of flapping and no loss of the fit" is wrong on the
  first half and right only in the sense that the fit is revisited: a wrong lesson moves twenty to
  forty weights by one, and at these margins that is enough to flip states until the next clean pass
  through them. Wider weights do not damp this (the 8-bit and 4-bit S4 rows differ little), because
  the step is one whatever the box. This is the strongest argument in these results for a rule
  refinement at the *interactive* stage (a margin trigger, or a step that a wrong lesson cannot undo
  cheaply), and it is outside the pre-registered scope; it is reported, not acted on.
- **The 474 from the 231 stream.** Training on the curriculum stream alone leaves 60 to 64 of the 474
  teacher-visited states wrong for every binary arm under either vocabulary (`R0` 425 absolute, 410
  under V, `R2` 425 / 414). Replaying the final weights names them: two thirds are "teacher idle, brain
  acts" in evaluation scenarios the curriculum never showed (the two-high wall, Tony on the fourth
  brick, Tony on a single brick, the C21 ladder from the right). That is a coverage gap of the
  curriculum, not of the retina or the vocabulary, and V does not close it.
- **S2u, the 474 cycled.** Under the absolute vocabulary no arm but `R2` fits the 474 (best 472 to
  473, cycling); `R2` fits it at 680 lessons and holds 257. Under V, `R0` fits it at 849 lessons (held
  259), `R1` at 579, `R1b` at 538, `R2` at 496, all held 276 to 279; at 4 bits none.

## 5. The residual under the absolute vocabulary, named

The states the rule leaves wrong at the end of the absolute 8-bit runs, replayed from the recorded
weights (`phase2b.json`), are the same states in every arm and the same two kinds the review named:

| state (sense vector, non-zero senses) | where | teacher | the brain says |
|---|---|---|---|
| dx 1, dy 4, facing right, on ground, floor below, wall ahead at the foot, brick ahead at the foot, still 2, Tony on a ladder | E07 stairs C33, frame 128: the route's first brick, standing on the stairs facing him with a step ahead | build left (away) | build right |
| dx -3, dy 2, on ground, floor below, buildable, still 2 | E13 stack from the right, frame 0: the stack's foot, on the floor with a buildable slot ahead | build left (toward) | build right |

`T36` and `A2` at 8 bits cycle on exactly these two (four lessons a pass, no clamps). `R0` trained on the
474 ends with these two plus two more of the first kind met in the evaluation (B3 at offset 32: dx 5,
dy 4; B9 at offset 96: dx 3, dy 4). Both kinds are "build left" where the same senses with the sign of
dx flipped say "build right": the direction of a build is an exclusive-or of the sign of dx with the
situation, and under V both become one word, "build away" on the stairs, "build toward" at the foot.
Phase 1b (`PHASE1B.md`) says whether any weights in the box can hold these under the absolute
vocabulary at all, and names the minimum unfit set exactly.

## 6. Predictions, scored

The engine's (PREREG-1B.md section 8):

- `R0` absolute at 8 bits: the 231 within 500 lessons, held: **right** (384, 277 of 300). At 6 bits the same: **right**. At 4 bits fails: **right**.
- `R0` under V at 8 bits: the 231 within 300 lessons: **right** (194); "the 474 reached within 900 lessons on S1, held": **wrong** as written (from the 231 stream the 474 stays at 410); on the 474's own stream, 849 lessons, held 259: **right** in the review's sense.
- The mixed controls at 8 bits: `T36` and `A2` end at the four-lesson cycle with zero clamps: **right** under the absolute vocabulary, and **the diagnosis behind it is incomplete**: under V the same mixed arms fit and hold (T36 197 lessons, A2 154), and `A2` even at 4 bits. See section 7.
- `raw20` never fits: **right**.
- `R2` converges more slowly than `R0`: **wrong**, it converges fastest.
- S4 flapping under ten clean lessons a pass with no loss of the fit: **wrong** (about 75); S5 costs more than S4: **right**, for a reason that makes the criterion unusable.

The review's (its section 7): R0 at 8 bits reproduces the box result: **right**. At 4 bits fails: **right**. With V, R0 at 8 bits fits and learns the 474 within 900 lessons, held: **right** (849). R1's named facts add nothing to it: **partly wrong**: they add nothing to feasibility (Phase 1b) but cut the 474's lesson count from 849 to 579 (R1) and 538 (R1b). T36 and A2 cycle at 8 bits with zero clamps: **right** under the absolute vocabulary only. S4 under ten lessons of flapping: **wrong**. S5 costs more than S4: **right**. The order-2 layer learns slower: **wrong**.

## 7. Interpretation

1. **The review's box result is real and reproduces to the lesson.** The bounded symmetric rule
   learns the curriculum teacher from zero on a binary retina once the weights have six or more bits,
   with weights that never exceed 25 in magnitude, and holds. The 4-bit box was the obstacle for the
   binary retina; the reference and the engine's own implementation agree on every number.
2. **The review's "cause one" is not what the data says.** The claim was that a mixed encoding (graded
   dx, dy, still beside flags) cannot be learned by the sign-step rule in any box, because the step is
   not along the input. But the same mixed arms, at the same boxes, on the same streams, fit and hold
   under the relative vocabulary, and `A2` does so even at 4 bits. What the mixed arms could not learn
   under the absolute vocabulary was the build-direction exclusive-or, the same two states everything
   else stalls on; the binary retina learned it at 8 bits because its thermometer and sign flags give
   those states enough private inputs, not because its step is "the perceptron step". So there is one
   cause in these results, the hard target, plus one aggravating factor, the box; the graded step is
   not shown to be a cause on its own.
3. **The vocabulary is the larger lever.** Under V every binary arm learns the 231 in roughly half the
   lessons, the 474 becomes learnable from its own stream for every binary arm, the 4-bit box becomes
   sufficient for `R0` on the 231, and even the raw-plus-thermometer control fits. The decoder gains
   one deterministic rule and decides nothing about what the reference is.
4. **Neither lever closes the generalisation gap.** From the curriculum stream, 60 or more of the
   teacher-visited states stay wrong for every arm and vocabulary, in situations the curriculum never
   contained. Coverage is a curriculum matter and Phase 4's behavioural holdouts are where it counts.
5. **Noise is the open problem for interactive teaching.** A 5% noisy teacher keeps the rule at
   about 150 lessons a pass and the fit is never stable; the step of one is as large relative to
   the margins at 8 bits as it was at 4. The S5 stream as pre-registered measured the wrong thing and
   should be replaced by agreement with the lagged labels, or by behaviour.
6. **Exploratory, after the pre-registration** (`PHASE1B.md` section 6): a binary retina whose dx
   flags are a signed thermometer (61 inputs) learns the 231 in 276 lessons and the 474 from its own
   stream under the absolute vocabulary (1,502 lessons, held 238), so the residual that the vocabulary
   removes can also be removed by the retina; the vocabulary still halves the lessons.
