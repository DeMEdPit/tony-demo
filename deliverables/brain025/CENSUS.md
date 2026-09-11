# BRAIN02.5, step C: the terrain-observation alias census

Pre-registered in `PREREG-BRAIN025.md` section 8, and run before any BRAIN02.5 code existed. Everything
below is measured on the frozen Candidate A build
(`tony-b02-a.prg`, sha256 `ae6ce5244478532c5ec581c9e24a30bea0743c68b2dd7cc7ff9f3017bc3e594d`);
nothing is modelled. Raw data: `census.json`. Tool: `tools/brain025_census.py`.

## The result in one line

**192 scenarios, spanning 32 distinct local terrains, produce 21 distinct observations. Seventeen of
those observations are consequential aliases: the world behaves differently inside them and BRAIN02
cannot tell which world it is in.**

## How it was measured

Courses were built the way a person builds them, on the game's own grid: 2x2 bricks written as the four
screen codes the build verb writes, which the room's materials table already makes wall. The room is the
Chamber: interior columns 5 to 34, floor at row 23, the ladder hanging at columns 33 to 34 down to row 9.
The calibration that fixed the column and row mapping is in `census-calibration.txt`; a character column
is the pixels at `X/8 - 2`, a character row the pixels at `Y/8 - 6`.

The observation is the machine's published twenty-nibble sense block put through Candidate A's own R1b
retina, which the Phase 3 parity gate proves equal to the reference on all 1,424 recorded blocks.

The consequence is measured, not asserted. For each of the ten reference-relative outputs, the brain is
made to choose that output by setting its bias weight and zeroing every other weight, so the decoder,
the macros and the vocabulary resolution all run exactly as in play. The output is held two think
periods, then the weights are zeroed so the brain idles, and the machine runs on for fifty-two frames.
The outcome is read from Tony's own position and state: ADVANCE, CLIMB, DROP, RETREAT, BLOCKED or
AIRBORNE, by the rules fixed in the pre-registration.

An observation is a **consequential alias** when two scenarios that share it have outcomes for the same
action that are good for one and bad for the other.

## What is aliased

Five families account for all of it.

**1. Standing on anything with an edge (the largest class: 11 geometries in one observation).**
`gap1`, `gap2`, `gap3`, `gap_level`, `gap_none`, `gap_up`, `hole_far2`, `hole_far3`, `ledge`,
`on_top_edge` and `on_top_flat` are one observation. Walking toward the reference DROPs him off the
edge in nine of them and ADVANCEs safely in two. Jumping toward DROPs, ADVANCEs or CLIMBs depending on
how wide the gap is and what is on the far side. BRAIN02 sees the cell one column ahead at his feet and
at his head, and whether there is floor directly under *him*; it has no way to see that the next column
is empty underneath.

**2. A one-high step, a pocket, and a covered pocket (7 geometries).**
`obst1`, `obst1_open`, `obst1_covered`, `pocket`, `pocket_covered`, `step_then_gap`, `step_then_wall`.
Jumping away RETREATs in the open cases and CLIMBs in the pockets, because a pocket has a wall behind
him he cannot see. Building toward or away CLIMBs in the open cases and is BLOCKED under a ceiling he
cannot see.

**3. Tall obstructions (6 geometries).** `obst2`, `obst2_open`, `obst2_covered`, `obst3`, `obst5`,
`pocket_deep` are one observation. Worth recording precisely: in this rollout the heights two, three and
five bricks did **not** differ in outcome from one another. What split the class was what is behind him.
The height mattered only through `build toward` on an obstacle two columns away, family 5.

**4. Flat ground, a corridor, and an obstacle or an edge a little further off (8 geometries).**
`flat`, `flat_near_wall`, `corridor`, `gap_down`, `ledge_high`, `obst1_far2`, `obst1_far3`,
`obst2_far2`. Walking toward ADVANCEs on flat ground and DROPs off the two edges, which are two columns
away rather than one. Jumping toward CLIMBs onto the obstacles that stand two or three columns off.
Building is BLOCKED by the corridor's ceiling and by the pillar behind him.

**5. The height of something two columns away.** `obst1_far2` and `obst2_far2` share an observation and
`build toward` CLIMBs on one and is BLOCKED on the other.

## The aliases that are not consequential

`gap_down` with `ledge_high`: both are an edge with a drop, and every action does the same thing in
both. They are aliased and it does not matter.

## What this does and does not show

It shows that the bottleneck named at the start of this experiment is real and that it is concentrated:
one column of vision at two heights, plus the floor directly underfoot, collapses thirty-two terrains
into twenty-one observations, and seventeen of those hide a difference the world acts on.

It does not show that more eyes will make Tony easier to teach. That is what steps E to H test. It also
does not show anything about terrains outside this set; the census is a designed sweep, not a sample of
what a person actually builds.

Prediction 1 of the pre-registration said more than half the consequential classes would come from two
families, a gap ahead and obstacles distinguished only above the head row. The gap family is the
largest single class and the edge cases reach into family 4 as well, so the first half holds. The second
half does not: obstacle height above the head row turned out **not** to be consequential on its own in
this rollout. What mattered instead was the ceiling above, the wall behind, and how far the floor
reaches. That correction is carried into the design.
