# BRAIN02.5: the resource report

Every number the pre-registration asks for, measured on `tony-b025-a.prg` rather than estimated. Raw
data: `resources-tony-b025-a.json`. Candidate A's column is BRAIN02's own Phase 3 measurement,
`deliverables/bakeoff/phase3/resources-tony-b02-a.json`, unchanged.

## Sizes

| | Candidate A | BRAIN02.5 | |
|---|---:|---:|---|
| inputs | 64 | **80** | +16 appended |
| published sense nibbles | 20 | **27** | +7 terrain quantities |
| brain slot | 674 bytes | **834** | 24 header + 10·n weights + 10 mood |
| weight bytes | 640 | **800** | |
| retina table | 193 bytes | **241** | count plus three arrays of n |
| weight shadow | 640 | **800** | at `$9200` |
| lesson entry | 11 bytes | **15** | 27 nibbles + the taught and predicted byte |
| lesson ring capacity | 300 | **180** | 2,732 bytes at `$9540` |
| PRG | 51,169 bytes | **52,092** | |
| accumulator bound | 8,320 | **10,368** | inside a signed 16-bit accumulator |

## The RAM map, and what is left

    code           ... $90F5      (ends 265 bytes below the shadow)
    weight shadow  $9200 .. $951F (800 bytes)
    lesson ring    $9540 .. $9FEB (32 + 15 x 180 = 2,732 bytes; 20 bytes to $A000)

The shadow and the ring live in the memory the level tune vacates when it is copied to `$A000` at
startup, exactly as BRAIN02 places its own. Headroom is thin at both ends and is the reason the ring
holds 180 rather than 300; the ring is what gives way when the brain and the code grow.

## How many inputs are set at once

Over the same forty teacher-visited blocks, put through each build's own retina (the BRAIN02.5 column
with random terrain appended):

| | min | mean | max |
|---|---:|---:|---:|
| Candidate A, 64 inputs | 9 | 16.9 | 25 |
| BRAIN02.5, 80 inputs | 16 | **27.1** | 38 |

Over a live teaching episode on the machine, BRAIN02.5 reads 13 / 26.1 / 33. Of the sixteen appended
inputs, 3 to 10 are set at once over the census scenarios, 6.6 on average.

## Cycles

Measured with the machine's own CIA 2 timer. The *pure* figures are taken through the test hooks with
interrupts held off, so they are the work itself; the live figures are wall-clock spans in the main loop
and carry whatever raster work fell inside them.

| | Candidate A | BRAIN02.5 |
|---|---:|---:|
| think, pure, min / mean / max | 11,704 / 14,466 / **17,464** | 15,193 / 20,064 / **24,129** |
| lesson, pure, max | **18,999** | **26,747** |
| terrain probe, pure, max | n/a | **4,361** |
| think, wall-clock, max | 41,612 | 42,288 |
| lesson, wall-clock, max | — | 38,347 |
| shadow snapshot, max | 22,435 | 29,131 |
| drain, max | 222 | 265 |
| raster maximum (limit 230) | 174 | **141** |
| overruns | 0 | **0** |
| score gap, min / mean / max | 0 / 29.6 / 67 | 0 / 6.6 / 44 |

## The one bound that is no longer met

BRAIN02's resource gate required the think and the lesson each to fit inside one PAL frame of main-loop
time, 19,656 cycles. **At eighty inputs neither does.** The think reaches 24,129 and the lesson 26,747.

This is reported rather than engineered around, which is what the pre-registration asks for. Three things
say the machine nonetheless keeps up, and they are the bounds that matter:

* the think has four frames, not one: its period is four frames, and its wall-clock span, interrupts and
  all, reaches 42,288 against the 78,624 cycles those four frames contain;
* the raster maximum is **141**, comfortably under the 230 limit and better than BRAIN02's own 174,
  because the extra work is in the main loop and not in the interrupt;
* **no overruns**, over a full teaching episode with chatter, a shadow snapshot and a drain.

What it does mean in practice is that a workbench single-stepping frames should not expect a decision
every frame, and that a further widening of the brain would want the forward pass reworked rather than
simply extended. The terrain probe itself is not the problem: its own work is 4,361 cycles, 22 percent
of a frame, and the optimisation it already carries (setting a row once per fixed-row scan, and stepping
the column inline) bought little, because the cost is spread evenly over sixty-odd cell reads rather
than concentrated anywhere.

## Code

    brainRetina 29    brainForward 15   brainLearn 8      bodyThink 72
    senseTerrain 13   tRowSet 25        tAt 12            teachKey 71
    testInputs 17     brainCheck 80     teachLesson 25    lessonAck 28
    copyWeights 12    teachShadowSave 95  teachShadowRestore 74   lessonInit 98

(These are the distances to the next label, so they measure each routine's own body and not the tables
and buffers between them.)

## Cognition stayed on the machine

The terrain probe, the retina, the forward pass, the vocabulary resolution, the rule and the lesson
recording all run on the C64. Nothing was moved off it to meet any of these numbers, and the one number
that does not meet its old bound is reported as such.
