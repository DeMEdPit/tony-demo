# BRAIN02.5, step D: the smallest terrain extension

Chosen from the census of step C by the rule the pre-registration set: score each candidate by the
consequential alias classes it separates per input added, and report the rejected alternatives and what
stays aliased. Raw data: `design.json`. Tool: `tools/brain025_design.py`.

## The result

**Sixteen appended inputs, over seven local terrain quantities, resolve every consequential alias the
census found.** The count of distinct observations over the same 192 scenarios rises from 21 to 93; the
34 consequential splits and the 636 conflicting scenario pairs both fall to zero. Inputs 0 to 63 keep
their meanings and their order exactly; the new inputs are 64 to 79. The brain is 80 inputs wide.

## The frame

Every quantity is measured in the **toward frame**: the direction `h` that the reference-relative
vocabulary already resolves, `+1` when the player is to the right of the clone, `-1` when to the left,
and the clone's own facing when the player is level with him. That is the same `h`, computed from the
same block, that decides whether output 1 means left or right.

The frame is a choice and the alternative was real. The existing senses 9, 10 and 11 look ahead in the
direction Tony **faces**, not the direction of the reference. Terrain in the facing frame was rejected
for two reasons: the action vocabulary is in the toward frame, so terrain in the same frame lets one
weight mean "there is a step in the direction I would move", which is the rule a person is actually
teaching; and mirrored courses then produce identical observations, which the census can check and does.
Facing is not lost: pseudo-sense 24, `facingRef`, already tells the brain whether its facing agrees with
`h`, and it is input 56.

A frame is not an answer. Each quantity says what is at a place. None of them says what to do, where to
go, whether to jump, or whether a route exists. Each is computable from the room and Tony's pose by
someone who does not know the task, which is the test the pre-registration set.

## The seven published quantities

His box covers two character columns and four rows. Write `rf` for his foot row, `rs` for the row his
feet rest on, `ce` for the box column on the toward side and `ca` for the box column on the away side.
Every count is capped at 7 so it fits one unsigned nibble.

| # | name | range | what it observes |
|---|---|---|---|
| 0 | `tSafeRun` | 0-7 | how many columns toward him, starting one past his box, have solid support at his own floor row, before the first that has none |
| 1 | `tGapW` | 0-7 | from that first unsupported column, how many columns in a row lack support |
| 2 | `tFarRun` | 0-7 | how many supported columns in a row the far side of that gap offers |
| 3 | `tObstH` | 0-7 | the height in rows of the first column toward him that is blocked at his foot row |
| 4 | `tObstTop` | 0-7 | the clear rows above that block's top |
| 5 | `tHead` | 0-7 | the clear rows above his own head, over both his columns |
| 6 | `tBackRoom` | 0-7 | how many columns away from the reference are clear at his foot row |

They are appended to the published sense block as seven more nibbles, so the block is 27 nibbles rather
than 20. Being in the block, they are in the lesson record, and an independent implementation replays a
lesson without ever seeing the room.

## The sixteen inputs

Each quantity gets an ordinal thermometer. Input 64 is the first appended input.

| input | test | input | test |
|---:|---|---:|---|
| 64 | `tSafeRun >= 1` | 72 | `tObstH >= 3` |
| 65 | `tSafeRun >= 3` | 73 | `tObstH >= 5` |
| 66 | `tGapW >= 3` | 74 | `tObstTop >= 1` |
| 67 | `tGapW >= 4` | 75 | `tObstTop >= 3` |
| 68 | `tGapW >= 6` | 76 | `tHead >= 1` |
| 69 | `tFarRun >= 1` | 77 | `tHead >= 4` |
| 70 | `tFarRun >= 3` | 78 | `tBackRoom >= 2` |
| 71 | `tObstH >= 1` | 79 | `tBackRoom >= 4` |

Between three and ten of the sixteen are set at once, six and a half on average. Across all eighty
inputs, between 19 and 36 are set at once, 26 on average, against about 18 for BRAIN02.

## How the sixteen were chosen

Eleven quantities were defined and computed for every census scenario. A search over all sixty
thresholds that actually cut an observed range added one input at a time, each time taking the one that
removed the most conflicting scenario pairs. It reached zero conflicts after nine:

| added | consequential splits left | conflicting pairs left |
|---|---:|---:|
| (none) | 34 | 636 |
| `tObstTop >= 3` | 34 | 418 |
| `tGapW >= 4` | 37 | 248 |
| `tBackRoom >= 2` | 21 | 152 |
| `tSafeRun >= 1` | 19 | 84 |
| `tGapW >= 6` | 15 | 48 |
| `tFarRun >= 3` | 12 | 28 |
| `tGapW >= 3` | 8 | 14 |
| `tHead >= 1` | 1 | 4 |
| `tObstH >= 3` | 0 | 0 |

Nine thresholds are enough for this corpus, and nine thresholds tuned to one corpus is exactly the
"scatter of special cases" the pre-registration warns against. The published sixteen are the smallest
ordinal thermometers that contain all nine, so each quantity is read as a magnitude rather than as the
single cut that happened to work here. Removing any one input and recounting shows which are
load-bearing on this corpus and which are there for ordinality:

    load-bearing:  tBackRoom>=2 (70 pairs), tObstTop>=3 (40), tSafeRun>=1 (20), tFarRun>=3 (20),
                   tGapW>=3 (8), tGapW>=6 (6), tObstH>=3 (4)
    for ordinality: tSafeRun>=3, tGapW>=4, tFarRun>=1, tObstH>=1, tObstH>=5, tObstTop>=1,
                    tHead>=1, tHead>=4, tBackRoom>=4

If the machine cannot afford sixteen, the nine load-bearing inputs are the fallback, and the cost of
that trade is that each quantity becomes a single threshold rather than a magnitude. The resource
measurements in step G decide it; nothing here is chosen to fit a budget that has not been measured.

## The four quantities computed and not published

| name | what it observes | why it is not published |
|---|---|---|
| `tDropH` | the drop from his floor row to the first surface under the gap | separated `gap_down` from `ledge` and `gap1`, but those are aliased without consequence |
| `tFarH` | the far side's height relative to his floor row | only `gap_up` used it, and `gap_up` is already separated by having an obstacle |
| `tObstD` | how many columns to the first blocked column | BRAIN02 already distinguishes an adjacent obstacle from a distant one through `wallAheadFoot`; the distance beyond that never changed an outcome |
| `tBackH` | the height of the block one column away from the reference | superseded by `tBackRoom`: the build verb works on a slot two columns wide, so what matters behind him is how much clear width there is, not how tall the first column is |

Each is a legitimate observation and each could be added later; none earned an input here.

## What stays aliased

Twenty-three of the ninety-three observations still cover more than one geometry, and none of them
consequentially: every action does the same thing to every member.

    obst1 / obst1_open / step_then_gap / step_then_wall     (identical within one column of his box)
    obst2 / obst2_open                                      (the same terrain by construction)
    gap_none / ledge / on_top_edge                          (all simply an edge with a drop)
    gap_down / ledge_high                                   (both an edge with a deeper drop)
    gap1 / gap_level                                        (the same terrain by construction)
    obst1_far2 / obst1_far3                                 (distance beyond two columns, never consequential here)

The honest reading is that the extension resolves everything the census could show it must, and that
terrains outside the census may well hide aliases this design does not touch. It is a bounded result on
a designed sweep, not a proof about all terrain.
