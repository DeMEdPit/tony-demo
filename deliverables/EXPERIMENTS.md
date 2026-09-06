# Experiment ledger — Tony on the Permanent Machine

The running record of every experiment started in this line of work, so
nothing gets lost between sessions. One entry per experiment: what it was
for, what it produced, what it taught, what is still open. Newest thinking
at the bottom. Detailed write-ups live in the documents each entry points to.

Status: **done** · **in progress** · **proposed** (thought through, nothing
built) · **parked** (deliberately not now).

Window: 2026-08-29 → 2026-09-06. Repo: `DeMEdPit/tony-demo`, branch
`claude/tony-c64-demo-expert-wp40it`. Upstream: `maciejmalecki/tony-demo`
@ `75f62f5b`, MIT (code Maciej Małecki, graphics Rafał Dudek, music Sami
Juntunen). Runtime: minimal64 by nopsta, GPL-2.0.

| # | experiment | status | key output |
|---|---|---|---|
| E1 | Asset map & build pipeline | done | `ASSET-MAP.md`, `tools/ctm_tool.py`, `tools/sprite_tool.py` |
| E2 | Three escalating edits (palette, protagonist, level) | done | `CHANGELOG.md`, `prg/c64-roms-required/tony-edit*.prg` |
| E3 | Emulator harnesses (VICE driver, native minimal64) | done | `tools/c64shot.py`, `tools/m64-harness/` |
| E4 | Custom single-screen boards (Vault, Colonnade) | done | `VAULT.md`, `tony-vault.prg`, `tony-colonnade.prg` |
| E5 | Buddy Tony (green follower, tall room, no HUD, no menu) | done | `prg/minimal64/tony-buddy.prg`, `tools/make_buddy.py` |
| E6 | Trainer / ROM-free builds | done | `TRAINER.md`, `tony-trainer-romfree.prg`, `tony-trained-nomenu.prg` |
| E7 | Repo organisation by target machine | done | `README.md` |
| E8 | Room census: which rooms can join which | done | `tools/onchain_castle.py census` |
| E9 | Mini castles as byte patches over the mainnet PRG | in progress | `ONCHAIN-CASTLES.md`, `onchain/castles/` |
| E10 | Room builder (Workbench extension) | proposed | this file, §E10 |
| E11 | Buddy behaviours as instruments | proposed | this file, §E11 |
| E12 | Chain-reactive tokens (render-time / run-time) | proposed | this file, §E12 |
| E13 | Collection architecture (bases + patches, keyless) | proposed | this file, §E13 |
| E14 | The Chamber: a back wall drawn from a 32-byte seed | in progress | `prg/minimal64/tony-chamber.prg`, `tools/stamp_mural.py` |
| E15 | Token thumbnail: the buddy's idle dance as an animated SVG | in progress | `assets/buddy-idle-*.svg`, `tools/buddy_thumbnail.py` |

---

## E1 — Asset map & build pipeline · done

**For:** become able to change anything in the demo deliberately.
**Produced:** the map of every asset class (sprites, charsets, 30 room maps,
colour schemes, enemies, music) and how each flows through the Gradle /
KickAssembler build; byte-level CharPad (`.ctm`) patching validated against
all 11 files; PNG↔sprite conversion with the plugin's exact rules (alpha
ignored, black = bit 0).
**Taught:** the build is deterministic — a clean rebuild of upstream is
byte-identical to the token on mainnet (this is what makes E9 possible).
**Open:** nothing.

## E2 — Three escalating edits · done

EMBER, a seventh colour scheme as boot default; "Golem Tony", a full
protagonist redesign keeping every frame count and the 24×21 format; title
lettering and a new platform in room 18. Sizes reported; music untouched.
**Taught:** how a 4-byte table insertion relocates 35 KB of a PRG; that
sprite slots are fixed 64-byte records (art edits never change size).

## E3 — Emulator harnesses · done

VICE driven through its binary monitor (joystick injection, sprite-register
position feedback, screenshots) and a **native build of the vendored,
chain-proven minimal64** with scripted input, RAM peek/poke, PC probe and
framebuffer grabs. Every later claim of "verified" rests on these.
**Taught:** three stacked VICE monitor gotchas (command id, active-low
joystick lines, every command pauses the machine); minimal64's PRG injector
parses the BASIC `SYS` line itself. **Open:** a Playwright driver for the
browser Workbench would close the last gap (on-chain page ≠ native build).

## E4 — Custom single-screen boards · done

The Idol Vault (a designed puzzle room, tuned by scripted play) and The
Colonnade (empty room, two pillars, three bats). **Taught:** any sprite
touching another sprite counts as a hit on the player — overlapping bat
paths drained hearts; room maps are layout-as-code (`build_custom_room.py`).

## E5 — Buddy Tony · done · **candidate first token**

A second, green Tony the game controls: follows, faces you, hops when you
jump, idles with the real six-phase animation. Tall 25-row room, no
dashboard, no boot menu, boots straight into the chamber. 37,310 bytes,
ROM-free, verified on native minimal64 and VICE. **Taught:** sprite colours
are repainted in the top-of-frame interrupt (the buddy's green must be set
there); the physics clamps collision scanning to row 20 (needed a forked
`physics-tall.asm`; `_constants.asm` cannot be forked). **Open:** the
owner's own play-through in READY 64 — the one gate it has not passed.

## E6 — Trainer / ROM-free builds · done

The demo's own five-toggle boot menu makes zero KERNAL calls but draws with
the character ROM, invisible on minimal64; rebuilt with the game's own font
(`cheatmenu-romfree.asm`); a menu-less build with infinite lives baked.
Static ROM-reference sweep (`check_romfree.py`) plus on-target runs.
**Taught:** the Code segment has 171 bytes of headroom; boot-time code must
live in scratch RAM above the image; the Movable segment is overwritten by
the music copy at unpack (first attempt crashed with PC in zero page).

## E7 — Repo organisation · done

`prg/minimal64/` (plays on the bare machine, and everywhere) vs
`prg/c64-roms-required/` (boot menu needs a character ROM, for now).

## E8 — Room census · done

30 rooms (29 + the title, itself a walkable room). Exits are one byte per
side — the engine has no grid; the author himself wires the title (4,0)
west into room 18 at (4,3). Under the playable-tier rules: 15 entry-capable
rooms, 234 safe one-way doors, 165 safe drops, one perfect self-loop room;
~660 valid 2-room and ~19,000 valid 3-room layouts by geometry alone.
**Taught:** room 11 declares a south exit that cannot fire (solid floor).

## E9 — Mini castles as byte patches over the mainnet PRG · in progress

A castle is 167–192 bytes over the exact on-chain PRG (`prgHash` verified):
rewired exits, colour scheme, a 10-byte cheat-state fix, a 108-byte edge
guard. Three samples (Ring = infinite, Well = void, Escher = wall), each
play-tested on minimal64 by `verify_castle.py`. **Three owner play-test
rounds in READY 64 found three real defects**, each now a permanent check:

1. sealed exits are not walls (Tony walks off the playfield, X wraps) → the
   edge guard, in the BASIC-stub padding at `$080D`;
2. a wall cap on a ladder traps Tony at the top → guard only, no caps;
3. a void on the door you entered by is a death loop → respawn-side rule.

Also found: the deployed game boots with two cheats on when run from a real
C64 (uninitialised `$2D`); `$080A–$080C` are BASIC structure, never patch
them; snakes ignore every cheat (author's own `TODO`).
**Open:** owner play-through of the Well (does the void feel right?);
one clean round with no new finds before any castle is minted; a Solidity
applier exists only as a sketch. Full detail: `ONCHAIN-CASTLES.md`.

## E10 — Room builder · proposed

Start from a template (Colonnade / bare box / empty), paint tiles from named
brushes (floors, platforms, pillars, ladders, chains, vines, sconces,
masonry), place objects (flames and pikes are hazards; jewels, potion, keys,
doors, snakes), draw bat paths, set the buddy, see constraints live, play
instantly, export the patch. Architecture: one deployed **room base** (the
E5 engine with a blank room and a reserved parameter block) + a small patch
per room, edited live in the emulator the way the Workbench STUDIO panel
drives CHAINGRID (`m64_cpuWrite`, nothing restarts). Hard limits to show
live: **two flyers with a buddy, four without** (hardware sprites); bat
paths must stay above the buddy's plane; patch size against the reserved
block. Colours: sprites free (16 colours each); tiles need a per-cell colour
map added to the room base (one session, recommended). Effort: base +
patch tool ≈ 1 session; builder MVP in the Workbench ≈ 2–4; tile colours
+1; behaviour table +1. `pm-chamber` in akalabeth already extracted and
credited the tile groups.

## E11 — Buddy behaviours as instruments · proposed

Follow / mirror / lead / hide are cheap and teach nothing about the machine.
Behaviours chosen as **probes** do: a buddy driven by the SID's oscillator-3
noise readback (the chip's own dice; tests that read on the on-chain
emulator); a buddy whose movement code uses undocumented 6502 opcodes
(first attestation of illegal-opcode support on the permanent machine —
unknown today); a path-finding buddy (frame budget, measurable with the
engine's debug border); two buddies plus bats via sprite multiplexing (the
classic raster-timing accuracy test). **The music-reactive buddy** is the
purest: the SID player's own state (pattern step, voice notes) and the
chip's readback registers are all inside the machine — a buddy that dances
to the soundtrack needs no outside data at all.

**Decided (owner, 2026-09-06): seven mechanics, one per token.** Follow
(the E5 buddy: keeps his distance, faces you, hops when you jump), Dance
(bounces on the hits of the tune, read from the SID's envelope readback, no
timing table), Echo (replays your moves a second or two behind you), Mirror
(moves opposite to you, reflected about the room's centre line), Wander
(lives there and ignores you: rules plus dice, the dice from the SID noise
generator with the render's hash setting the mood), Shy (runs when you
approach, creeps back, hides behind a pillar), Sleeper (dozes crouched until
you come close, follows for a while, dozes off again). Behaviour is fixed per
token; the wall (E14) is the living part. The base look stays as it is now,
black and grey, and **each token's buddy has a dedicated colour**: one
behaviour byte and one colour byte join the seed block, so one build serves
all seven. The colour-from-base-fee idea (E12) is **parked**. The sixteen
candidates are on `assets/buddy-palette-16.png` on the Chamber's black;
readable on black: white, cyan, purple, green, yellow, orange, light red,
light green, light blue, grey, light grey (Tony's own, so avoid); too dark:
red, blue, brown, dark grey; black is invisible. **Colours chosen (owner,
2026-09-06):** cyan (3), green (5), yellow (7), light blue (14), blue (6),
light red (10), purple (4); blue is the dimmest of the seven on black and
was picked with that in view. Which colour goes with which mechanic is
still open. Build order: the two bytes, then Dance, then the rest, each
with a scripted test on minimal64.

## E12 — Chain-reactive tokens · proposed

The 6502 only ever reads a parameter block in RAM; two honest ways to fill
it from Ethereum. **Render time, fully on-chain:** `tokenURI` runs in the
EVM and may read any chain state (owner, holdings, block number/hash,
timestamp, an on-chain price feed) and patch it into the PRG bytes before
the launcher wraps the page. Keyless, serverless, deterministic and
provable; a snapshot per render. **Run time, in the page:** JavaScript
writes bytes into the running machine (the STUDIO pattern) from live chain
data — but the page must then reach a node, i.e. an RPC. Rule: bake no URL
into an immutable token; use the viewer's wallet provider or a viewer-
supplied endpoint, treat responses as bounded bytes only, and let the token
render completely without any of it. **Display:** the game already renders
text with its own font (E6), so a block number or a short address can be
drawn *inside* the C64 screen from the same block.

## E13 — Collection architecture · proposed

Tokens = (base program, patch). Base 1: the Tony token edition, on mainnet.
Base 2: the buddy room engine, to deploy once. Castles and chambers are
patches; five buddy tokens with different behaviours are five patches over
base 2 (or five artifacts under one series, per the series-zero memo:
publish once, reference many). Keyless and immutable per token means
fix-forward: bugs found later are fixed in new tokens. Gates before any
mint: the automated suite passes and the owner has played it in READY 64.
Decide up front whether shared parts (guard, launcher) can ever change.

## E14 — The Chamber: a back wall drawn from a seed · in progress

Chain state as *decoration* rather than a readout: carved into the room the
way stone gets inscribed. Mock-ups built from the game's own tiles, its title
font and its sprites (`assets/engraved-chamber-mock.png`), sample values:

- **lintel** — a brick band under the ceiling with the block number carved
  out (negative glyphs of the title font, `$BC20`);
- **pillar shafts** — the owner's short id (`48DD` / `AF5B`) carved into the
  niche rows;
- **mural** — the dotted background bricks (`$B0–$B3`, the ones behind the
  skull in room 11) laid as a 14×7 field where each brick is present iff a
  bit of the block hash is set: a fingerprint nobody reads as data;
- **sconces** (`$69 $6A / $6D $6E`) — one lit candle per token held;
- **weathering** — cracked-brick variants (`$50–$5E`) sprinkled into the
  floor, count growing with blocks since mint: the chamber ages with the chain;
- **the carved face block** (`$3D–$48`) and an engraved diamond in the mural.

Also the HUD kept as a panel (`assets/hud-instrument-mock.png`): the
six-digit score becomes the block number, hearts become tokens held, an
item slot shows a relic, labels redrawn (`HOLDS`, `BLOCK`, `GAS`). Both feed
from the same parameter block as E11/E12; render-time values from the
contract make every render a dated impression.

**Built (2026-09-06), after the owner cut it down to the one idea:** no HUD,
the full 25 rows, a brick ceiling, the same floor, the two pillars, Tony,
the green buddy, two bats — and the chain touches only what the seed block
says. `tony-chamber.prg` (37,942 B, ROM-free, boots straight in) carries a
**40-byte seed block** right after an 8-byte marker `MURAL01\0` (file offset
`0x042C9`, address `$4AC8`, 64-aligned): 32 seed bytes (the block hash) and
8 block-number digits. The shipped default seed is sha256 of "block 25850267",
a typical roll (quarter wall, one candle high on the left). The pillars are plain shafts (the two "niche" rows
with the diagonal crack are gone). At every room draw the game stamps, between the room
decompression and its character translation:

- **the wall** — 15 × 10 slots of 2×2 dotted bricks. Three bit streams run
  through the seed (A from byte 0, B from 19, C from 25, wrapping at 32) and a
  **density mode** picks how they combine per slot. Three seed bits
  (`seed[31] & 7`) index the table 3,3,3,0,0,1,1,2 — **fewer bricks is
  always more common**: an eighth filled (A&B&C) three rolls in eight, a
  quarter (A&B) two, half (A) two, and three-quarters (A|B) **one in eight,
  the rare roll**. Measured over 4,000 hashes: 39 / 24 / 25 / 12 %. "Dense"
  means more brick slots filled; the lattice spacing never changes. Same
  seed, same wall, forever;
- **the candle** — one at most. Present when `seed[30] & 3` is not zero
  (three rolls in four). Its place comes from `seed[29]`: the low four bits
  choose one of 14 slot columns through a 16-entry table (left column
  5 + 2k), the next three bits one of 5 slot rows through an 8-entry table
  (top row 4, 6, 8, 10 or 12) — 70 positions, all on the upper and middle
  wall, never within eight rows of the floor, and all 70 reachable (checked
  over 4,000 hashes). The candle is the glowing one from room 10 (beside its
  ladder): a 3×3 block `$BD–$C5`, a candle on its holder inside a halo of
  dots, all decorative material, drawn inside a cleared 4×4 niche (two wall
  slots by two) so no half bricks are left beside it. (Two earlier tries:
  `$69–$6E` is a carved skull block; `$70/$72` are the small flame candles
  of room 8's ledge, which the game marks deadly.)
- **the floor inscription** — the eight block digits carved into the top
  course of the floor, right-aligned against the right pillar (columns
  27–34), as ten new glyphs (`$01–$0A` in the chamber's own charset: a
  smooth stone cell with a small 4×6 numeral cut into it, dark on light; wall
  material, so Tony stands on them). Eight digits cover block numbers to
  99,999,999 — roughly the year 2054 at today's block rate; a ninth digit
  would take column 26.

Also fixed: the buddy showed the wall through his transparent pixels. Tony
never did because the engine gives him a third, Y-expanded, dark backdrop
sprite; the buddy now has the same on sprite 7 (free in this build), pointed
at the BG frame of whatever pose he wears and repainted in the top-of-frame
interrupt with the player's backdrop colour.

Verified on minimal64 for five seeds (all four density modes, 0–2 candles):
every one of the 150 wall slots, the candle's niche (all nine cells of the
motif and the seven cleared cells around it) and the eight floor digits match
`tools/stamp_mural.py`'s bit-exact prediction of the 6502 routine. Captures:
`assets/chamber-five-seeds-m64.png`, `assets/chamber-zoom-candles.png`,
`assets/chamber-zoom-floor.png`. Generated sources:
`tools/build_chamber_room.py` (map, `chamber-charset.bin`,
`chamber-materials.bin`), `tools/make_chamber.py` (`level/chamber/data.asm`,
`tony-chamber.asm`). A trap met on the way: characters the run-time routine
needs must be parked in the static map, and two parked groups overlapped —
three candle characters fell out of the room's character set and the
candle's bottom row went blank until the parking was fixed. The combination space is 2^150 walls × 4 densities ×
71 candle states — not a preset list.

**Decided (owner, 2026-09-06):** the wall is fed at **render time**. When a
marketplace or viewer calls the token, the contract writes the current
block's hash (`blockhash(block.number - 1)`, the newest hash a view call can
read) into the 32 seed bytes and the current block number into the 8 digit
bytes, so every fresh render is a different wall, a different candle roll and
a different number in the floor. Consequences to keep in mind: marketplaces
cache metadata and re-fetch on their own schedule, so "every render" means
every re-fetch, while READY 64 and a direct call are always fresh; and a
chain can only serve the last 256 block hashes, so a wall seen at block N
cannot be recomputed on-chain an hour later — the renders are impressions,
not a permanent series (if a permanent "birth wall" is ever wanted, the mint
block's hash can be stored at mint and rendered alongside). Colour: the
room keeps its black-and-grey scheme; only the buddy is coloured, one
dedicated colour per token (decided with the seven mechanics, E11).

**Open:** the owner's play-through in READY 64; the room base (the buddy
engine) is not yet deployed; the contract that performs the 40-byte write.

---

## E15 — Token thumbnail: the idle dance as an animated SVG · in progress

**For:** the image a marketplace shows for each of the seven tokens. The
owner's brief: the buddy alone, in his token colour, doing the little dance
he does when he stands still, on repeat, and entirely on chain.

**Built:** `tools/buddy_thumbnail.py` rebuilds the loop from the sprite
bytes the PRG itself carries (the four idle frames, the left 24-pixel column
of each 48×42 cell in `tony spoczynek 4klatki.png`) and emits one SVG per
colour: a square 56×56 canvas, black field, four `<path>` layers in
run-length pixel rows, switched by SMIL `<animate opacity>` in discrete
steps, A B A B C D at 0.3 s each (fifteen PAL frames, as in
`animations.asm`), 1.8 s a loop. Two layouts: **floor** (the Chamber's own
brick course from the level charset, in Tony's light grey, flush on the
bottom edge, the buddy standing on it: his lowest ink row is the row above
the bricks' top line; 8,205 bytes) and **plain** (no bricks, the buddy
centred; 6,060 bytes). The first cut had the buddy at a fixed sprite offset
and he floated 11 px above the bricks, because the idle sprites carry ten
empty rows under the feet; the owner spotted it and the layout now places
the feet from the measured ink box. Files: `assets/buddy-idle-<colour>.svg`
(floor) and `assets/buddy-idle-<colour>-plain.svg` for the seven colours,
`assets/buddy-thumbnail-seven.png` (all seven, floor layout),
`assets/buddy-thumbnail-layouts.png` (floor beside plain),
`assets/buddy-idle-phases.png` (the six phases as a strip). Verified in
Chromium, both layouts, by pausing the SVG clock at mid-phase times and
comparing the rendered pixels against the sprite frames: A B A B C D, A
again at the start of the second and third loops, the feet row carrying the
buddy's colour directly above the bricks' top line.

**On chain, the plan:** the SVG needs no image file. The contract's
`tokenURI` writes it from the sprite bytes (already public in the Tony blobs;
a copy of the four frames as run-length rows is a few hundred bytes of
contract data) and the token's colour byte, and returns it as a `data:` URI
in the metadata JSON, the standard fully on-chain pattern. A viewer that
hands the SVG to an `<img>` animates it (the major browsers run SMIL there);
one that rasterises to a cached still shows frame A, which is why A is drawn
first. `data:` inside `data:` needs base64 of the SVG (about 11 KB per render);
gas is paid only by the caller of a view, so the size costs nothing at mint.

**Taught:** the game's idle sequence is not four frames in a row; it is
A B A B C D. A fixed-per-token thumbnail (colour only) can be stored once
at deploy; if the thumbnail should ever carry the render-time wall as well,
the same seed logic as `tools/stamp_mural.py` would have to be repeated in
Solidity, which is a much larger contract than the buddy alone.

**Second round (owner's review):** the chunky course read as one big
block with a seam, so three more layouts were built, all on
`assets/buddy-thumbnail-options.png` at one tile size: **plain** at 48 and
40 px (the buddy alone, larger in the tile; `buddy-idle-cyan-plain-40.svg`,
6,014 bytes), **bricks** (a full-width course of the game's small
running-bond bricks, characters `$AD $AE $AF`, room 0,3's left wall, no
seam; `buddy-idle-cyan-bricks.svg`, 8,230 bytes), and an **arched
doorway**. The game's tiles hold no arch: the nearest things are the
rounded corners of the big cave blocks and the stone-framed grille in room
2,5. So the doorway is drawn in the level's own textures: **arch** (a ring
of seven voussoirs and jambs in the speckled stone of the blocks, small
bricks around, a 36 px opening with a semicircular top, 64 px canvas;
`buddy-idle-cyan-arch.svg`, 12,793 bytes) and **arch-brick** (the same
opening cut straight out of the small-brick wall;
`buddy-idle-cyan-arch-brick.svg`, 12,414 bytes). The arch SVG was verified
in Chromium like the others (phase order, feet on the floor row).

**Decided (owner, 2026-09-06): the buddy alone, the middle size** (plain,
48 px canvas; he fills half the tile). The seven files are
`assets/buddy-idle-<colour>.svg`, 6,014 bytes each;
`assets/buddy-thumbnail-seven.png` shows them together. The other layouts
stay available in the tool (`--layout`, `--size`) and on the options
sheet, but are no longer shipped as files.

**Open:** Solidity generator and its gas; how each marketplace of interest
treats SMIL in practice (measured, not assumed) before relying on the
animation.

---

## Road to seven tokens · plan (2026-09-06)

What stands between the Chamber as it is and seven minted tokens, in the
order it has to happen. Owner decisions are marked ◆.

1. **Engine.** Grow the parameter block from 40 to 42 bytes (behaviour,
   colour, 32 seed bytes, 8 block digits) and build the seven mechanics
   (E11) into one Chamber PRG, Dance first. Each mechanic gets a scripted
   minimal64 test the way the wall got one (drive the buddy, read his
   position and state back). ◆ Which colour goes with which mechanic;
   ◆ the seven token names.
2. **Owner play-through** of every mechanic in READY 64 (the E13 gate: no
   mint before the suite passes and the owner has played it).
3. **Freeze the base.** Hash the final PRG, record the block offset and
   every patchable byte (a patch map like `ONCHAIN-CASTLES.md`'s), and
   store the PRG in the deliverables with its size. From here the room
   engine never changes; later fixes are new tokens (fix-forward).
4. **Contracts.** (a) Store the Chamber PRG on chain as base 2 (the same
   blob pattern the Tony token uses for base 1). (b) The seven-token
   contract: per id two bytes (behaviour, colour); `prgFor(id)` = base 2
   with the 42-byte block written at the fixed offset at render time
   (`blockhash(block.number - 1)`, the block number as digits, the two
   bytes); `tokenURI(id)` = JSON with name, description, attributes
   (mechanic, colour, base hash), `image` = the idle-dance SVG built in
   Solidity from the sprite rows and the colour byte (E15),
   `animation_url` = the launcher's page over `prgFor(id)`. The
   description carries the credits (Maciej Małecki, Rafał Dudek, Sami
   Juntunen, MIT; nopsta, GPL-2.0) and the plain statement about nopsta
   in the project's wording. ◆ The description text.
5. **Prove the contract off chain.** A Python reference produces the
   exact bytes the contract must produce (base 2 + block) and the SVG;
   the Solidity is run in a local EVM against it, byte for byte, for all
   seven ids and several block values; the produced PRGs run on the
   minimal64 harness; the SVGs render in Chromium as in E15.
6. **Deploy and mint** (owner's keys, owner's gas): base 2 blobs, the
   token contract, seven mints. Then verify on READY 64 and on a
   marketplace: fresh metadata, the SVG animating or at least frame A,
   the wall changing between renders.
7. **Afterwards.** Anything found later is fixed in new tokens, never in
   these; the ledger keeps the findings.

Estimate: step 1 about one session, steps 3–5 one to two sessions, steps
2 and 6 are the owner's. Nothing in this plan touches the chain until
step 6.

---

## Findings register (measured facts, engine and hardware)

- Exit bytes are the whole castle topology; no grid in the engine (E8).
- Any sprite-to-sprite touch counts as a player hit (E4, E10).
- Sprite colours are repainted in the top-of-frame IRQ (E5).
- The idle animation plays its four frames as A B A B C D, fifteen PAL
  frames per phase, a 1.8 s loop (E15).
- The Movable segment is overwritten by the music copy at unpack; the
  dead menu at `$B462` can only run at boot (E6, E9).
- Sealed exits have no behaviour; X wraps through zero (E9).
- `$0801–$080C` is BASIC structure parsed by RUN and by minimal64 (E9).
- The token edition boots with cheats `$28` on a ROM-equipped C64 (E9).
- Snakes are static objects and ignore every cheat (E9).
- A wall cap on a ladder flips Tony to "standing" at the top (E9).
- Respawn is at the room entry point in the entry state (E9).
- Room 11's declared south exit is dead; room 25's ladder is an entrance
  only (E8, E9).
