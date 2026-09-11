# BRAIN02.5: the complete input list

Eighty inputs. Inputs 0 to 63 are R1b's, **entry for entry**, with the meanings and the order
Candidate A gave them; nothing is renumbered. Inputs 64 to 79 are appended. The tables below are
generated from the two implementations rather than transcribed.

Every one of the first sixty-four table entries is byte-identical to Candidate A's: **True**.
(The name column is this tool's rendering of the entry, and differs in wording from BRAIN02's
renderer for a few entries; the entries themselves, the operator and the two operands, are equal.)

Retina id 5, name T1, 241 table bytes, stored as a count then three parallel
arrays, ops, operand a and operand k, exactly as BRAIN02 stores its own.

## Inputs 0 to 63: unchanged

| input | operator | value | k | test | identical to R1b |
|---:|---|---:|---:|---|---|
| 0 | GE | 0 | 1 | `bias>=1` | yes |
| 1 | GE | 3 | 1 | `facingRight` | yes |
| 2 | GE | 4 | 1 | `onGround` | yes |
| 3 | GE | 5 | 1 | `inAir` | yes |
| 4 | GE | 6 | 1 | `onLadder` | yes |
| 5 | GE | 7 | 1 | `ducking` | yes |
| 6 | GE | 8 | 1 | `floorBelow` | yes |
| 7 | GE | 9 | 1 | `wallAheadFoot` | yes |
| 8 | GE | 10 | 1 | `wallAheadHead` | yes |
| 9 | GE | 11 | 1 | `brickAheadFoot` | yes |
| 10 | GE | 12 | 1 | `ladderHere` | yes |
| 11 | GE | 13 | 1 | `ladderBelow` | yes |
| 12 | GE | 14 | 1 | `buildable` | yes |
| 13 | GE | 15 | 1 | `playerAir` | yes |
| 14 | GE | 18 | 1 | `playerDuck` | yes |
| 15 | GE | 19 | 1 | `playerOnLadder` | yes |
| 16 | GE | 1 | 1 | `dx>=1` | yes |
| 17 | LE | 1 | -1 | `dx<=-1` | yes |
| 18 | GE | 28 | 1 | `adx>=1` | yes |
| 19 | GE | 28 | 2 | `adx>=2` | yes |
| 20 | GE | 28 | 3 | `adx>=3` | yes |
| 21 | GE | 28 | 4 | `adx>=4` | yes |
| 22 | GE | 28 | 5 | `adx>=5` | yes |
| 23 | GE | 28 | 6 | `adx>=6` | yes |
| 24 | GE | 28 | 7 | `adx>=7` | yes |
| 25 | GE | 2 | 1 | `dy>=1` | yes |
| 26 | GE | 2 | 2 | `dy>=2` | yes |
| 27 | GE | 2 | 3 | `dy>=3` | yes |
| 28 | GE | 2 | 4 | `dy>=4` | yes |
| 29 | GE | 2 | 5 | `dy>=5` | yes |
| 30 | GE | 2 | 6 | `dy>=6` | yes |
| 31 | GE | 2 | 7 | `dy>=7` | yes |
| 32 | LE | 2 | -1 | `dy<=-1` | yes |
| 33 | LE | 2 | -2 | `dy<=-2` | yes |
| 34 | LE | 2 | -3 | `dy<=-3` | yes |
| 35 | LE | 2 | -4 | `dy<=-4` | yes |
| 36 | LE | 2 | -5 | `dy<=-5` | yes |
| 37 | LE | 2 | -6 | `dy<=-6` | yes |
| 38 | LE | 2 | -7 | `dy<=-7` | yes |
| 39 | GE | 17 | 1 | `still` | yes |
| 40 | GE | 17 | 2 | `still>=2` | yes |
| 41 | GE | 17 | 3 | `still>=3` | yes |
| 42 | GE | 17 | 4 | `still>=4` | yes |
| 43 | GE | 17 | 5 | `still>=5` | yes |
| 44 | GE | 17 | 6 | `still>=6` | yes |
| 45 | GE | 17 | 7 | `still>=7` | yes |
| 46 | EQN | 16 | 0 | `lastAction==0` | yes |
| 47 | EQN | 16 | 1 | `lastAction==1` | yes |
| 48 | EQN | 16 | 2 | `lastAction==2` | yes |
| 49 | EQN | 16 | 3 | `lastAction==3` | yes |
| 50 | EQN | 16 | 4 | `lastAction==4` | yes |
| 51 | EQN | 16 | 5 | `lastAction==5` | yes |
| 52 | EQN | 16 | 6 | `lastAction==6` | yes |
| 53 | EQN | 16 | 7 | `lastAction==7` | yes |
| 54 | EQN | 16 | 8 | `lastAction==8` | yes |
| 55 | EQN | 16 | 9 | `lastAction==9` | yes |
| 56 | GE | 24 | 1 | `facingRef>=1` | yes |
| 57 | GE | 25 | 1 | `stepAhead>=1` | yes |
| 58 | GE | 26 | 1 | `wallAhead>=1` | yes |
| 59 | AND | 12 | 23 | `AND(ladderHere,refAbove)` | yes |
| 60 | AND | 24 | 25 | `AND(facingRef,stepAhead)` | yes |
| 61 | GE | 27 | 1 | `buildableAndClear>=1` | yes |
| 62 | GE | 21 | 1 | `lastTowardRef>=1` | yes |
| 63 | GE | 22 | 1 | `lastAwayRef>=1` | yes |

## Inputs 64 to 79: appended

| input | operator | value | k | terrain quantity | test |
|---:|---|---:|---:|---|---|
| 64 | GE | 29 | 1 | tSafeRun | `tSafeRun>=1` |
| 65 | GE | 29 | 3 | tSafeRun | `tSafeRun>=3` |
| 66 | GE | 30 | 3 | tGapW | `tGapW>=3` |
| 67 | GE | 30 | 4 | tGapW | `tGapW>=4` |
| 68 | GE | 30 | 6 | tGapW | `tGapW>=6` |
| 69 | GE | 31 | 1 | tFarRun | `tFarRun>=1` |
| 70 | GE | 31 | 3 | tFarRun | `tFarRun>=3` |
| 71 | GE | 32 | 1 | tObstH | `tObstH>=1` |
| 72 | GE | 32 | 3 | tObstH | `tObstH>=3` |
| 73 | GE | 32 | 5 | tObstH | `tObstH>=5` |
| 74 | GE | 33 | 1 | tObstTop | `tObstTop>=1` |
| 75 | GE | 33 | 3 | tObstTop | `tObstTop>=3` |
| 76 | GE | 34 | 1 | tHead | `tHead>=1` |
| 77 | GE | 34 | 4 | tHead | `tHead>=4` |
| 78 | GE | 35 | 2 | tBackRoom | `tBackRoom>=2` |
| 79 | GE | 35 | 4 | tBackRoom | `tBackRoom>=4` |

## The values the inputs are tests over

| index | name | where it comes from |
|---:|---|---|
| 0 | bias | the published sense block, BRAIN02's, unchanged |
| 1 | dx | the published sense block, BRAIN02's, unchanged |
| 2 | dy | the published sense block, BRAIN02's, unchanged |
| 3 | facingRight | the published sense block, BRAIN02's, unchanged |
| 4 | onGround | the published sense block, BRAIN02's, unchanged |
| 5 | inAir | the published sense block, BRAIN02's, unchanged |
| 6 | onLadder | the published sense block, BRAIN02's, unchanged |
| 7 | ducking | the published sense block, BRAIN02's, unchanged |
| 8 | floorBelow | the published sense block, BRAIN02's, unchanged |
| 9 | wallAheadFoot | the published sense block, BRAIN02's, unchanged |
| 10 | wallAheadHead | the published sense block, BRAIN02's, unchanged |
| 11 | brickAheadFoot | the published sense block, BRAIN02's, unchanged |
| 12 | ladderHere | the published sense block, BRAIN02's, unchanged |
| 13 | ladderBelow | the published sense block, BRAIN02's, unchanged |
| 14 | buildable | the published sense block, BRAIN02's, unchanged |
| 15 | playerAir | the published sense block, BRAIN02's, unchanged |
| 16 | lastAction | the published sense block, BRAIN02's, unchanged |
| 17 | still | the published sense block, BRAIN02's, unchanged |
| 18 | playerDuck | the published sense block, BRAIN02's, unchanged |
| 19 | playerOnLadder | the published sense block, BRAIN02's, unchanged |
| 20 | hRight | derived in the retina from senses 0 to 19, BRAIN02's, unchanged |
| 21 | lastTowardRef | derived in the retina from senses 0 to 19, BRAIN02's, unchanged |
| 22 | lastAwayRef | derived in the retina from senses 0 to 19, BRAIN02's, unchanged |
| 23 | refAbove | derived in the retina from senses 0 to 19, BRAIN02's, unchanged |
| 24 | facingRef | derived in the retina from senses 0 to 19, BRAIN02's, unchanged |
| 25 | stepAhead | derived in the retina from senses 0 to 19, BRAIN02's, unchanged |
| 26 | wallAhead | derived in the retina from senses 0 to 19, BRAIN02's, unchanged |
| 27 | buildableAndClear | derived in the retina from senses 0 to 19, BRAIN02's, unchanged |
| 28 | adx | derived in the retina from senses 0 to 19, BRAIN02's, unchanged |
| 29 | tSafeRun | the published sense block, nibble 20: **new** |
| 30 | tGapW | the published sense block, nibble 21: **new** |
| 31 | tFarRun | the published sense block, nibble 22: **new** |
| 32 | tObstH | the published sense block, nibble 23: **new** |
| 33 | tObstTop | the published sense block, nibble 24: **new** |
| 34 | tHead | the published sense block, nibble 25: **new** |
| 35 | tBackRoom | the published sense block, nibble 26: **new** |

Every appended input uses the GE operator only. Every terrain quantity is an unsigned count capped
at 7, so each fits one nibble; the accumulator bound at eighty inputs is 10368, inside a
signed sixteen-bit accumulator with room to spare.

## The sense block

Twenty-seven nibbles, published one frame behind as BRAIN02's twenty were. Nibbles 0 to 19 are
BRAIN02's senses, unchanged in meaning, order and packing. Nibbles 20 to 26 are the terrain
quantities, in the order of the table above, each an unsigned value 0 to 7.

* nibble 20, `tSafeRun`
* nibble 21, `tGapW`
* nibble 22, `tFarRun`
* nibble 23, `tObstH`
* nibble 24, `tObstTop`
* nibble 25, `tHead`
* nibble 26, `tBackRoom`
