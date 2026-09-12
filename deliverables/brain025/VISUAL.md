# BRAIN02.5 vis1 and vis2: the clone's visual state language, and the rooms

**vis2 is the current revision.** It keeps everything vis1 did, makes the cyan of teaching a sprinkle
rather than a pulse, thins the lower room's back wall to the bricks the candle lights, and makes the
room above bare and darker.

| revision | PRG | sha256 |
|---|---|---|
| research, no visual pass | `tony-b025-a.prg` | `2a547ebfe77bebb6b6174729af05a2ebb4dc2a8e558359f615cbdf34d6bfb423` |
| vis1 | `tony-b025-a-vis1.prg` | `4e22961ef55a5e29a80bdf65f8773301ced5e68904fc5417108bb543f1a7a708` |
| **vis2** | `tony-b025-a-vis2.prg` | `117559716a3f529d35a887bac8f7e620adf250bbd3841d58edf10f837a614958` |

## vis2, what changed from vis1

**Teaching is a sprinkle, not a pulse.** Cyan was six frames of every sixteen, about 37 percent of the
time. It is now three frames of every thirty-two, about 9 percent, measured at 3 of 48 frames. The
dropout now runs in both states rather than being replaced while teaching, so teaching reads as white
with an occasional cyan tick. The green of an accepted lesson is unchanged and is now the loudest thing
on the clone by a wide margin, which was the point.

**A lesson still outranks the pulse.** The flash is tested first, so an accepted lesson gets its full
six green frames even if a cyan tick was due. Making cyan rarer does not weaken green; it makes green
stand out more.

**The lower room's back wall is thinned to what the candle lights.** A slot keeps its seeded brick only
if it lies within three slots of the candle's niche, measured Manhattan in slot coordinates. On the
default seed that takes the wall from 34 bricks to a small cluster hugging the candle, and leaves the
rest of the room bare. A room whose seed gives no candle gets no bricks at all.

This is a **gate in front of** the seeded density modes, not a replacement for them. `litRadius` is a
labelled byte; at zero the gate is off and the wall renders exactly as the seed always said. So the
Chamber's generative rule is untouched and this look is opt-in per build, which matters because
`muralStamp` is the art a block number renders as.

**The room above is bare and darker.** No bricks, no candle, and the stone in dark grey. All three reuse
paths the game already had: mode 4 for a bare wall and colour 11 for dark stone are what the Glitch's
blackout uses, and the candle already had a skip. They now also trigger on `currentChamberNumber` being
non-zero. Only the background colour is darkened; the human Tony's own colour is set further down from
`currentColor` and is deliberately left alone.

## vis2, measured

**Behaviour: identical.** The same script on the research build and vis2, 40 samples four frames apart:
the behavioural fields, meaning both Tonys' positions and states, all 27 senses, the chosen action and
raw output, the education count, the ring's write sequence, the think count and the brick count, are
**identical on all 40 samples**. Two things do differ and neither is behaviour:

* the frame counter is offset by exactly **one frame**, constant across every sample, because the room
  draw is slightly longer at boot;
* the raster maximum is **+3 lines**, 136 against 139 on that script and 138 against 141 on the
  resources episode. The limit is 230 and overruns stay at **0**.

The mural's bricks carry material 0, verified on the machine rather than assumed, so none of the room
work is terrain: the probe, the senses and the brain cannot see any of it. The terrain gate agrees,
192 of 192 scenarios equal to the model.

**Gates:** smoke, blank, key, terrain, parity, migrate, teach, drain, resources and visual all pass on
vis2 with no failures. PRG size is unchanged at 52,092 bytes.

---

# vis1: the clone's visual state language

A presentation-only revision, in its own PRG. The research build `tony-b025-a.prg` is untouched and
still hashes `2a547ebfe77bebb6b6174729af05a2ebb4dc2a8e558359f615cbdf34d6bfb423`; the replay and
provenance work continues to pin it.

| | |
|---|---|
| new PRG | `deliverables/prg/minimal64/tony-b025-a-vis1.prg`, 52,092 bytes |
| sha256 | `4e22961ef55a5e29a80bdf65f8773301ced5e68904fc5417108bb543f1a7a708` |
| descriptor | `workbench/tony-b025-a-vis1.json` |
| built by | `--brain025-visual` instead of `--brain025` |

## The grammar

The clone wears one colour a frame, decided in this order.

| state | what he wears |
|---|---|
| a lesson was **accepted** | **green** (5) for six frames |
| a lesson was **refused**, the ring is full | **red** (2), and it re-arms every tick the ring stays full, so it reads as a held condition rather than a blink |
| **teaching** is on | **cyan** (3) for six frames of every sixteen, over white: a slow pulse, about 3 Hz |
| otherwise | **white** (1), dropping out to **black** for one frame in thirty-two |

Leaving teaching returns to white and the dropout with nothing left over. The flash always wins, so an
accepted lesson reads clearly even mid-pulse.

## Two collisions worth knowing about

**The human Tony is light grey (15), not a strong colour.** White against light grey, on two
identically shaped sprites, is a close pair. The base colour is therefore *not* what distinguishes them
on screen: the **dropout** is. One black frame every thirty-two makes the clone visibly flicker while
the human stays perfectly steady, which is the "synthetic" read the design is after. If the two still
feel too close in practice, the dropout is the dial to turn, not the white.

**Green (5) is the V1 buddy's own base colour**, the default `muralColour`. It is used here only as a
six-frame success event, never as an identity, and no V1 behaviour colour is cycled. The clone also no
longer wears the seeded `muralColour` at all in this revision, which is the point: he is not a Chamber
V1 behaviour variant.

## How it is implemented, and why it cannot reach cognition

The colour is a **pure function of three things that already existed**: `bodyFrames`, which the main
loop increments anyway; `teachMode`; and the six-frame flash counter BRAIN02 already kept. There is no
new mutable state, no random draw, and nothing is written but `$D02C` and `$D02D`, the clone's own two
sprite colour registers. Sprites have individual colour registers, so the human Tony's cannot be
touched, and the shared multicolour registers are not written.

The existing flash mechanism was reused rather than replaced: only the accepted-lesson value changed,
from white to green.

## Measured

**Behaviour: identical.** The same deterministic script on both builds, walking, jumping, laying a
brick, stepping up, teaching and walking back, sampled every four frames over 40 samples of 48 bytes:
both Tonys' positions and states, all 27 senses, the chosen action and raw output, the education count,
the ring's write sequence, the think count, the frame counter, the raster maximum, the overrun count and
the brick count were **identical on every sampled byte**. End state on both: clone at X 203 Y 190
standing on the brick he laid, education 7, seven lessons recorded, 200 thinks, raster max 141, no
overruns, one brick.

**Resources: nil.** PRG size, slot bytes, ring capacity, both headroom figures, the raster maximum and
the overrun count are all identical. The colour block itself is about ten cycles a frame more than the
one it replaced, a bound from its instruction sequence; that is far below the profiler's run-to-run
variation, so it is not separately measurable. The think and lesson figures move by a couple of hundred
cycles between runs because the resources gate weights the brain randomly, and that is noise, not a cost
of this pass.

| | research | vis1 |
|---|---:|---:|
| PRG size | 52,092 | 52,092 |
| slot / ring / headroom | 834 / 180 / 265 and 20 | identical |
| raster maximum | 141 | 141 |
| overruns | 0 | 0 |

**The visual gate**, sampling the sprite register once a frame:

| state | measured |
|---|---|
| idle, 64 frames | white 62, black 2, nothing else |
| teaching on, 48 frames | white 30, cyan 18 |
| accepted lesson | green on 6 frames, education advancing |
| refused lesson, ring full | red on 40 of 40 frames, never green |
| teaching off, 64 frames | white 62, black 2, no cyan and no flash left behind |
| the human Tony, throughout | light grey (15), never anything else |

**Gates:** smoke, blank, key, terrain, parity, migrate, teach, drain, resources and visual all pass on
the new build with no failures. The one NOTE is the pre-existing one, that at eighty inputs the think
and the lesson no longer fit inside a single frame of main-loop time; it is unchanged by this pass and
is documented in `RESOURCES.md`.

## Scope

Presentation only. The architecture, the inputs and retina, the weights and learning rule, the lesson
format, the timing semantics, the controls, the build, movement, collision and physics, the replay
behaviour and the human Tony's behaviour are all untouched.
