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
| E11 | Buddy behaviours as instruments | done (engine) | `tony-chamber-the-*.prg`, `tools/verify_buddy.py` |
| E12 | Chain-reactive tokens (render-time / run-time) | proposed | this file, §E12 |
| E13 | Collection architecture (bases + patches, keyless) | proposed | this file, §E13 |
| E14 | The Chamber: a back wall drawn from a 32-byte seed | in progress | `prg/minimal64/tony-chamber.prg`, `tools/stamp_mural.py` |
| E15 | Token thumbnail: the buddy's idle dance as an animated SVG | superseded by E21 | `assets/buddy-idle-*.svg`, `tools/buddy_thumbnail.py` |
| E21 | Token thumbnails: the retro layout (tag, buddy, dithered floor; the dark Glitch) | done, frozen 2026-09-07 (re-frozen the same day for the still fix; commit in `contract/tokens-record.json`) | `assets/tokens/the-<name>.svg`, `tools/buddy_retro_svg.py`, `THUMBNAILS.md` |
| E16 | The Glitch: the eighth mechanic, in the blackout room | built | `tony-chamber-the-glitch.prg`, `tools/verify_buddy.py glitch` |

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

## E11 — Buddy behaviours as instruments · done (engine)

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

**Names (owner, 2026-09-06):** The Shadow (Follow), The Dancer (Dance),
The Echo, The Mirror, The Wanderer, The Shy, The Sleeper; the mechanic
stays an attribute.

**Built (2026-09-06): the two bytes, and Dance.** The Chamber's parameter
block is now 42 bytes after the marker `MURAL02\0`: 32 seed bytes, 8
block digits, the behaviour byte, the colour byte (`tools/make_chamber.py`,
`tools/stamp_mural.py --behaviour --colour`). `buddyUpdate` is split into a
*decide* part (what he wants this frame: moving, facing, a hop) and an
*act* part (step, hop, sprite, pose); Follow is the original decide code
and the other mechanics dispatch through `buddyDecide` on the behaviour
byte, so one build serves all seven. Dance listens to two things, both
inside the machine, and nothing outside it:

- *the beat*: voice 1's note, read from the image of the sound-chip
  registers that the tune's player keeps in RAM and copies to the chip every
  frame (`$A474`, found in the player by its copy loop `LDA image,X / STA
  $D400,X`). A move of half a semitone or more (|new − old| ≥ old/32) is a
  step: the pose advances one phase of the idle cycle and he side-steps six
  pixels the way he faces, and every fourth step he turns round, so he
  shuffles a body-width each way around his spot (the owner's ask after the
  first cut, where he stood still). Between steps the pose holds: he moves
  only when the music moves;
- *the hits*: voice 3's envelope read back from the chip itself (`$D41C`).
  A rise of 6 or more in a frame is a note hit and queues a hop, answered
  the moment he is on the ground, so the tune's double hits become double
  bounces.

Measured on the tune before designing it: gate-ons are rare (a hard
restart every 160 frames, all three voices together); the notes move by
frequency, legato, voice 1 and voice 3 every 10 frames, voice 2 an arpeggio
every 3 frames; voice 3's envelope holds at $55 with a double attack (10
frames apart) every 150 frames. So the beat had to come from the note
changes, not the gates or the envelope, and the envelope gives the accents.
`tools/verify_dance.py` (18 s on minimal64): 68 notes on voice 1, 56 pose
steps, none off the beat, none unanswered; 17 turns, never closer than 39
frames; 79 envelope rises, 14 hops, every one on a rise, no rise without a
hop; his path is the music's alone: the X trace over 400 frames is
identical whether the player stands or walks to and fro; the sprite colour
registers carry the colour byte. Follow regression passes (walks after the player, hops at the
player's jump, green). **Taught:** minimal64 implements both readback
registers of the SID (`$D41B` oscillator 3, `$D41C` envelope 3) in its
`sid_read`, and the values behave like the chip's: the on-chain machine can
be listened to.

**Built (2026-09-06, later): the other five.** All in `buddyDecide`, each
leaving what he wants this frame (moving, facing, a hop, the walking pose,
the crouch) for the act part; the crouch and walking-pose flags are
committed once per frame by the act part, because the Sleeper's test caught
two samples in a hundred between the flag's reset and its set (a sampling
race, not a behaviour). `tools/verify_buddy.py` drives all seven on
minimal64 (`tools/verify_dance.py` is retired into it):

- **Echo** (2): a 256-entry ring of the player's X, Y and animation
  number, written every frame, played back 200 frames (4 s) later, frame
  for frame: he stands where the player stood, at the height the player
  was, wearing the pose the player wore (walk, duck, jump, idle, and the
  way he faced), so every step, jump and duck comes back in order and the
  playback runs on for four seconds after the player stops. The first cut
  replayed only X and turned each recorded jump into one of the buddy's
  own fixed hops, which collapsed five quick jumps into two and dropped
  the ducks; the owner saw it and asked for the whole routine. Test: a
  routine of running, four jumps and a duck comes back with position and
  height equal to the player's 200 frames earlier at every one of 580
  frames (0 misses), pose and facing too; four jumps echoed, one duck
  echoed, nothing extra (the ghost also replays Tony's fall into the room
  at boot, which is faithful). Measured on the way: the game sets the
  duck's animation number a little later in the frame than the walk and
  jump ones, so a recorded pose can change one frame late at that one
  transition.
- **Mirror** (3): x′ = 344 − x, the reflection about the centre line between
  the pillars, clamped to 64..280; he jumps with the player. Test: 0 misses
  over 294 frames of walking both ways, faces the other way while the
  player walks, hops on the player's jump frame.
- **Wander** (4): one plan at a time — stroll (40–103 px, direction from the
  dice), pause, sit (the crouch) — rolled from an 8-bit shift register
  stirred every frame by the chip's oscillator 3 (`$D41B`); the render's
  mood (two bits of seed byte 28) lengthens the rests; he turns at the
  pillars and never looks at the player. The first cut rolled the raw
  oscillator byte and hugged the left pillar (range 42 px in 40 s: the
  sawtooth's samples were correlated). Test: 40 s alone covers the whole
  room 64..280, 12 turns, 16 plans, a sit of 137 frames, a pause of 305.
- **Shy** (5): closer than 56 px he runs the other way at two pixels a
  frame (the player's own speed, measured: Tony walks 2 px/frame; at one he
  was simply caught) and cowers in the crouch when the pillar stops him;
  between 56 and 110 he stands and watches; beyond 110 he creeps back at
  half speed with the walking pose. Test: runs 56 px to the pillar by frame
  33, never closer than 54 px while he could still run, cowers; when the
  player walks off he creeps back 83 px and stops at 109 px.
- **Sleeper** (6): dozes in the crouch; wakes when the player *approaches*
  (inside 48 px, having been farther a moment before), is the Follow buddy
  for 300 frames, then dozes off wherever he is. Test: crouched and still
  for 100 frames; wakes 9 frames into the approach; follows 76 px; dozes
  off at frame 409 and stays put.

**From the owner's play-through (2026-09-06):** the crouch was frame 3 of
the duck sequence, which is Tony halfway back up (the four frames are
standing, bending, down, rising); it is frame 2 now, the one fully down,
for the Echo, the Wanderer's sit, the Shy's cower and the Sleeper's
doze. And the buddy's hop was the first Follow build's 14-frame, 12-pixel
arc; the owner noticed he never jumped as high as Tony. Tony's jump was
measured on the emulator (26 frames, apex 23 pixels, the deltas −4 −4 −4
−2 −2 −2 −1 −1 −1 0 −1 0 −1 +1 0 +1 0 +1 +1 +1 +2 +2 +2 +4 +4 +4) and is
now the buddy's arc in every mechanic that hops; the Echo replays Tony's
height directly and was already exact. Tests re-run: all seven pass (the
Dance test now allows a hop to answer a hit made during the previous
jump, since a jump lasts 26 frames). Then: the Shadow did not crouch when
Tony did; Follow and Mirror now crouch with him (the Mirror because a
mirror that ignores a crouch would be wrong), once he stands still; the
tests check the crouch appears with Tony's duck animation and goes when
it goes.
The Wanderer never jumped (measured: 0 jumps in 120 s alone; none of his
plans asked for one). He now has a fourth plan, a jump on the spot (one
roll in eight), and one stroll in eight starts with a running jump:
measured 10 jumps in 120 s, plan changes 40. The long measurements needed
the harness to take its script from a file (`m64run PRG @script`), since
a two-minute frame-by-frame script exceeds the command line.

The base is now **feature complete**: one build, 41,094 bytes, serves all
seven and the Glitch. Provisional colours for the shipped programs (the owner's mapping is
still open): Shadow blue (the owner's ask: the darkest of the seven for
the Shadow; the C64's blue, which reads as a dark purple on a black
screen), Dancer cyan, Echo yellow, Mirror light blue, Wanderer green, Shy
One light red, Sleeper purple.

**The Shy's corner escape (found by the owner in play, kept on
purpose).** Cornered at a pillar and crouching, he bolts the other way at
full speed the moment Tony squeezes past him: Tony's floor runs eight
pixels beyond the buddy's at each pillar, so Tony can get to the far side
of him, and "away from the player" flips. Nothing was written for it; the
flee rule produced it, the trace showed it before the owner did, and the
test now asserts it (cornered, passed, bolted, in that order) so it stays.
Then the owner asked for it a little more sensitive: he should bolt when
Tony is almost on him, not only once Tony is past. Cornered and crouching,
he now bolts straight at Tony and through him when Tony comes within 16
pixels, and keeps going until Tony is behind him, where the ordinary flee
carries him on the same way. Measured: cornered at frame 34, bolts at 55
with Tony 6 pixels off, clear of the corner by 71.

**The Mirror contradicts him up and down too (owner's idea, 2026-09-06).**
The literal mirror copied the jump and the crouch; nobody watching thinks
"reflection", they see a second Tony doing the opposite, and a crouch
answered with a crouch broke that. Now: while Tony is in the air the
Mirror crouches (shown once he is on the ground; he cannot crouch
mid-bounce), and while Tony is crouched the Mirror bounces without pause
until Tony stands. Left-right unchanged. Measured: Tony in the air 21
frames, the Mirror crouched throughout; Tony down 120 frames, the Mirror
bounced five times with four frames on the ground between. Then, from
play: a crouched Tony turning in place got no answer, since the Mirror's
facing came only from his own movement. His facing is now the opposite
of Tony's at every frame, read from Tony's animation (the Echo's pose
table gives the side), so a turn in place, crouched or standing, flips
him the other way; measured: two turns while crouched, answered, and the
opposite facing at every frame of the run. Open: the owner's
play-through of the seven in READY 64, the colour mapping, then the freeze.

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

**Block format since E11's build (2026-09-06):** the marker is
`MURAL02\0` and the contract writes 42 bytes after it: 32 seed, 8 digits,
behaviour, colour. In the current build (`tony-chamber.prg`, 41,094 bytes,
all seven mechanics) the block sits at file offset `0x04EC9` (address
`$56C8`); find it by the marker, never by a fixed offset, until the base is
frozen.

**The bats join the render (owner's ask, 2026-09-06).** The engine flies
each bat along an authored path chosen by one byte, so the seed now picks,
at every render, each bat's path (eight authored: glides, flutters, a wave,
hops, bobbing, a dip; travel 24–64 px, every path netting to zero and
straying at most 8 px), its start column (left bat 2–9, right bat 24–29,
so with the travel they never meet: their sprites must not touch), its row
(2–9), and whether it is there: seed byte 27's low four bits give a quiet
night with no bats one render in sixteen, a single bat one in four, both
otherwise. Seed bytes 24–27; written into the room's object tables by
`muralBatsStamp` before `initObjects` reads them, presence through the
room-state bits, and the choices reported in eight bytes after the block
for the tests. Safety was the design constraint: the bats stay a band
above Tony's reach (a bat's lowest point at least 30 px above the top of
his jump), because a bat within reach would bring the game's death, five
lives and game-over screen into an art token. `tools/verify_bats.py` (16
seeds on minimal64): every report byte as the Python model predicts, the
sprites present or hidden as the seed says, each bat starting at its
column and row (the engine places a bat 4 px below its row's top, a
measured fact), travelling its path's distance, keeping within 8 px of its
row, never within 30 px of the jump line, the two never meeting; one torn
sprite-register read in 300 frames at the 256 crossing is a sampling
artefact and is dropped. `assets`: `screenshots/chamber-bats-m64.png`
(four seeds: both bats, left only, right only, none).

**Open:** the owner's play-through in READY 64; the room base (the buddy
engine) is not yet deployed; the contract that performs the 42-byte write.

---

## E15 — Token thumbnail: the idle dance as an animated SVG · superseded by E21 (2026-09-07)

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
`assets/buddy-idle-<colour>.svg`, 6,056 bytes each;
`assets/buddy-thumbnail-seven.png` shows them together. The other layouts
stay available in the tool (`--layout`, `--size`) and on the options
sheet, but are no longer shipped as files.

**Open:** Solidity generator and its gas; how each marketplace of interest
treats SMIL in practice (measured, not assumed) before relying on the
animation.

---

**The Glitch's thumbnail blinks (2026-09-07, the owner's choice):** the
owner asked to see a blink and kept it. The generator wraps his figure in a
group whose opacity drops twice, briefly, every 2.6 s (out 0.08 s, back
0.04 s, out 0.08 s), a period that drifts against both the 1.8 s idle loop
and the 2.8 s colour cycle so the drops land on different poses and colours
each time. It is the default for `--glitch` and for the Glitch in
`--tokens` (`--no-blink` for the plain cycle): `assets/tokens/the-glitch.svg`
and `assets/buddy-idle-glitch.svg`, 6,842 bytes (was 6,668); `--gif` writes
a preview of the timeline from the same data (`assets/buddy-idle-glitch.gif`).
Verified in Chromium by seeking the SVG's clock: the figure is gone at
2.43 s and 2.55 s, back at 2.49 s and 2.62 s, gone again at 4.99 s, the
colours cycling throughout. The seven other thumbnails are byte-identical
to before.

---

## E16 — The Glitch: the eighth mechanic, in the blackout room · built

The owner's idea (2026-09-06): one render in sixteen has no bats, which
leaves the two bat sprites idle, and a Tony is exactly two sprites tall.
So the no-bat renders could carry a third Tony, "the Glitch": cycling
through the colours, flickering in and out, jittering, and switching
mechanic every few seconds (a Wanderer one moment, a Dancer the next). No
backdrop sprite is free for him (the eighth is the buddy's), so the wall
would show through him, which suits a glitch. Feasible: the buddy code
runs one buddy today, so a second needs its state saved and restored
around a second update each frame and the sprite registers made
selectable (5, 6 and 7 are hard-wired); sprites 3 and 4 count as enemies
in the collision rule, so touching him must be masked out while he is
active; his Echo would need its own ring (1 KB; there is room). Colour
cycling, flicker and jitter are cheap. Estimate: one to two sessions with
tests. It is engine-only: the same seed bytes drive him (no bats), so the
block format and the handoff stay valid; only the base hash changes.
Rarity per render: one in sixteen; with no candle as well, one in
sixty-four (the dark room).

**Built (2026-09-06), the simpler way.** With the owner and another session
shaping a 64-token collection (seven mechanics × nine rooms + one), the
Glitch became the sixty-fourth token rather than a per-render rarity, and
a token's buddy is the ordinary buddy slot: no second character, no bat
sprites, no two-buddy plumbing. Mechanic byte 7 = the Glitch: he wears one
of the seven mechanics at a time and changes it every 150–405 frames on the
Wanderer's dice (a 7 rolls to the Wanderer); the stateful mechanics start
afresh at each change, and an Echo stint replays whatever the ring holds,
which may be minutes old (a feature, for a glitch); he cycles the seven
token colours one every eight frames; and about once in 85 frames a burst
of 8–15 frames sets his colour at random, blinks him out (black) one
frame in four, and jitters him a pixel sideways (short of the pillars).
The colour the sprites wear now passes through `buddyColourNow` (the
block's colour for everyone else). His room is the **blackout**, gated on
the mechanic byte, not the seed, so no ordinary room can produce it: the
mural routine draws no bricks (a fifth density, bare), no candle, and
hides both bats; the block number is still carved. Test (30 s on
minimal64): wore four mechanics with four changes, all fifteen non-black
colours seen, 67 blink frames of 1,500, moved 96 px; the 600 wall cells
empty, the digits identical to an ordinary room's, both bat sprites off.
The seven buddy tests and the bat test still pass (the Sleeper's doze is
internal mode 8 now). Then, the owner's ask: teleports. Every change of
mechanic is now a teleport (he blinks out for twelve frames and is
somewhere else between the pillars when he comes back, the spot from the
dice), and one burst in eight is a teleport instead of a jitter. Test (30
s): six changes, five of them teleporting, seventeen teleports in all, 227
blink frames of 1,500, X 66..254, never past the pillars. And the owner's
last ask for him: everything darker. In the blackout the interrupt paints
the room's light (the screen background, which is what the negated
charset shows as stone) dark grey (11) instead of light grey and Tony's
sprites grey (12), and the mural routine gives the block number's eight
cells light-grey ink (colour RAM) so the digits read bright on the dark
floor. Measured: background 11, Tony 12, digit ink 15; an ordinary room
15 and 15. `screenshots/chamber-glitch-dark-m64.png` shows the two side
by side. Then the owner asked whether the digits should be black in the
blackout, or the buddy's colour everywhere, and rainbow for the Glitch.
Measured on the floor (`screenshots/chamber-digit-colours-m64.png`):
black digits on the dark-grey stone are readable but murky, the light-grey
ones clear; on the ordinary light-grey stone black digits are crisp,
yellow and cyan poor, purple readable, so a buddy-coloured number would
only work for the dark colours. Recommended and built: the seven keep
black digits, and the Glitch's number wears his colour, frame by frame,
light grey while he is blinked out (measured: the digits' ink cycles
through all seven colours and 15, never 0). The owner then chose to leave
the number alone even for him: it is light grey throughout the blackout
again, as before (measured: ink 15 for 20 s). (Superseded on 2026-09-07:
black, see E17.) His thumbnail (E15) is the
same idle dance with the fill cycling through the seven token colours,
0.4 s each: `assets/buddy-idle-glitch.svg` (6,668 bytes), verified in
Chromium colour by colour; `assets/buddy-idle-glitch-phases.png`. The
eight token thumbnails now exist by token name as well
(`tools/buddy_thumbnail.py --tokens` → `assets/tokens/the-<name>.svg`,
the seven at 6,056 bytes in their colours, the Glitch at 6,668), with
`assets/buddy-thumbnail-eight.png` showing all eight.

**Bats, exhaustively (2026-09-06):** on paper, all 8 paths × 8 rows × 64
column pairs: the lowest bat bottom is 153 (Tony's jump top is 183), the
narrowest gap between the bats 32 px; on the emulator, each of the eight
paths on the lowest row with the two bats at their closest starting
columns: lowest bottom 153, narrowest gap 32 px, all enabled, all within
their bands.

---

## E17 — The Glitch's tune: the intro tune relocated into the Chamber · built (2026-09-06)

**Question (owner):** are there other soundtracks in the demo, and could
the Glitch have his own?

**Census:** two tunes exist, ever: the level tune
(`src/music/TonyLevelA000_V2.sid`, $A000, 5,508 bytes, the game and every
Chamber build) and the intro tune (`src/music/tonyintroe000_1.sid`, $E000,
5,782 bytes, heard only in the full loader build's intro scroller, never in
the Chamber). Both are GoatTracker exports with one song each (init with 0,
1 or 2 gives the same register stream); no sound effects anywhere, no song
sources, nothing else in git history; the commented "funktest" tune in
intro.asm never existed in the repo.

**Measured character** (bare player on minimal64, PAL 50 Hz, 8-minute
captures of each player's register image): the level tune has a ~75 BPM
feel with 100 ms steps, is sparse (4.4 / 2.2 / 1.9 note-ons per second on
voices 1–3), opens quietly for 30 s, pulse-heavy, filter on voices 1–2, its
phrase structure recurring about every 3:08. The intro tune is ~107 BPM and
dense (7.4 / 7.1 / 10.4 note-ons per second), 70 ms runs and arpeggios on
voices 1 and 3, a constant low-pass sweep on voice 2, phrase structure
recurring about every 2:50 with an inner repeat near 1:24. Neither register
stream repeats exactly within 8 minutes (a free-running counter in the
player), so the periods come from autocorrelation of the note onsets.

**The obstacle:** the intro tune is bound to $E000, where the Chamber keeps
its 125 sprite shapes. No relocator on the machine (sidreloc unreachable
under the network policy); the two exported players share only 370 bytes in
fragments, so no diff-based move either.

**Relocation:** `tools/sidreloc.py`, a tag-tracking 6502 in Python: every
file byte carries its offset through registers, memory and arithmetic; when
an address is formed (an operand, an indirect pointer, a jump, a return) the
tag of its high byte is recorded together with where the address points.
12,000 play calls traced (3.8 M instructions, 6 s): 289 bytes serve as
address high bytes inside the tune, none of them also as data, index, low
byte or an outside address. **Proof by replay** (`tools/verify_reloc.py`):
bare players for the original at $E000 and the copy at $A000, 24,000 frames
each (8 minutes), every SID register write identical. Cross-check: the level
tune moved $A000 → $E000 the same way, 6,000 frames identical. The result is
`src/music/TonyIntroA000_reloc.sid` (provenance in `src/music/RELOCATION.md`);
no note, instrument or timing changed, the header is the original's.

**The variant:** `tools/make_chamber.py --music src/music/TonyIntroA000_reloc.sid
--variant tony-chamber-intro` generates `src/kickass/tony-chamber-intro.asm`,
the same engine carrying the other tune in the same slot ($A000–$B695, under
the charset at $B800; the materials area at $B400 is unused by the Chamber).
The default generation is unchanged (`tony-chamber.prg` still `81468c5a…`).
Build: `tony-chamber-intro.prg`, 41,368 bytes (274 more, the tune's extra
bytes), the parameter block at the same file offset 0x04EC9. The Glitch test
passes on it unchanged (7 changes, 17 teleports, blackout intact).

**The Dance phase under the intro tune (measured):** as built for the level
tune, the Dancer steps on voice 1's note changes and bounces on voice 3's
envelope rises (ENV3 ≥ 6). The intro tune's voice 1 is an arpeggio nearly
every frame (39 changes/s against 16 for the level tune's) and its voice 3 a
fast lead whose every attack is a big rise (8.8 rises/s, 495 of 532 ≥ $28):
he never lands — 34 hops in 18 s, airborne 99% by the hop model (ENV3
captured; no threshold up to 96 changes it), no visible step, 149 turns in
18 s. Two generator knobs, variant-only (the standard base's bytes do not
change): `--dance-voice 2` (he steps to voice 2, the steadier line: 41 notes
in the first 18 s) and `--dance-cool` (keep the engine's 20-frame pause after
a landing instead of zeroing it). With both: 19 hops in 18 s (about one a
second), airborne 55%, 7 steps, 10 turns — a bounce every other beat with
shuffles between. Reference, the standard base with the level tune: 68
notes, 41 steps, 17 turns, 13 hops, airborne 34%. `tools/verify_buddy.py`
now reads the voice the Dancer was built for and reports the airborne share;
its pass criteria remain the level tune's, so the variant reports FAIL on
the Dance test by design (7 steps against the 30 it expects) and OK on the
Glitch test.

**Deliverables:** `prg/minimal64/tony-chamber-intro.prg` (41,368 bytes,
unstamped), `tony-chamber-intro-the-glitch.prg` (behaviour 7, colour 1),
`tony-chamber-intro-the-dancer.prg` (behaviour 1, cyan; to hear the Dancer
alone with the intro tune). All three are the voice-2, landing-pause build.

**Heard (2026-09-07):** the owner played the build and likes the sound.
Before that, the doubt "it still sounds like the regular track" was settled
by measurement, not argument: the Glitch build's register stream on the
emulator uses 23 instrument settings and 80 notes, all of the intro tune's
(the old build: all of the level tune's), and the harness gained
`audio:FILE`, which renders the emulator's own SID output to a WAV; forty
seconds of each Glitch build are in `deliverables/audio/` (22 kHz). The
two tunes share a composer and 17 instrument settings, so the family
resemblance is real; the tell is the pace.

**The block number in black (2026-09-07, a look-see):** the owner asked to
see the blackout's number in black instead of light grey. The digit cells'
ink is now a generator option, `--glitch-ink N` (default 15; the default
build is unchanged). `tony-chamber-intro-the-glitch-black-number.prg`
(41,368 bytes, sha256 `2c338808…`) is the intro-tune Glitch with ink 0;
`screenshots/chamber-glitch-number-grey-vs-black-m64.png` shows the two
side by side (pixel-checked: strokes light grey 178,178,178 against the
dark grey stone 74,74,74 above, black 0,0,0 below). The owner then chose the
black. **Decision (2026-09-07):** `--glitch-ink` defaults to 0; both bases
rebuilt with the one byte changed (standard base 41,094 bytes, sha256
`f9f7225f507c954f50c43f557643039d6f7bd59b2520ecc4dde82c845ad1e262`; intro
base 41,368 bytes, sha256
`170789a970c7b30a6b4283c3fdf5fa092a703eb907cab39db7d6cb74237c24b9`; the
block at file offset 0x04EC9 in both, unchanged); all sixteen deliverable
PRGs re-stamped with their own blocks carried over byte for byte; the
look-see file dropped (it was the Glitch build itself). All eight mechanic
tests pass on the standard base, the bats over sixteen seeds pass, the
Glitch test passes on the intro base (the test now reads the blackout's
ink from the build).

**Open (owner's decisions):** (1) whether a relocation counts as modifying
the music — no note changes, 289 address bytes do; (2) the shipping shape:
a second base for the Glitch (this variant, a second hash) or both tunes
resident in one base (the 14,847 bytes free at run time below $A000 hold
the second tune; behaviour 7 would start it; one hash, the handoff's
assumption) — not built; `HANDOFF-GLITCH-TUNE.md` puts both to the
contracts agent; (3) the Dance knobs: the plain pogo (no knobs) or the
one-a-second bounce (voice 2 + landing pause). The number's ink is decided: black.

**Decided and built (2026-09-07):** the owner keeps the tune for the Glitch
alone (the Dancer dances worse to it: 7 steps against 42), takes the tamed
bounce, and asked for the one-base shape. Engineering: the intro tune
relocated a second time, to $8000 (289 bytes, replay-identical over 24,000
frames), and carried in the base's Movable segment ahead of the level tune,
copied out last into $8000–$9695, a region measured untouched by the engine
over 3,000 frames of play; `initSound` and `doPlay` route on behaviour 7;
the Dance mechanic rereads the intro player's voice 2 and skips the
cooldown reset when behaviour is 7. The load image now ends at $BF1A, 229
bytes under the screen at $C000 (the ceiling for growth). **Base:**
`tony-chamber.prg`, 46,876 bytes, sha256
`044f1f714e3e68cc94d79ac6dc16cf8a963cf6ad3d08cab8b900898aa79f6bcf`
(superseded by the dice change, E18), the block at file offset 0x04EC9,
unchanged. Measured on it: all eight tests
pass (the Glitch's build plays the intro tune and not the level tune, the
Dancer's the level tune and not the intro tune); the Glitch's Dance phase
over 90 s: airborne 59%, 0.97 hops/s; the Dancer unchanged (42 steps, 33%
airborne); bats over sixteen seeds pass; the register fingerprints match
the right tune for each. The second-base files and variant are retired.
For the contracts: `tools/chamber_vectors.py` writes 32 test vectors
(`deliverables/contract/chamber-vectors.json`) and `HANDOFF-CONTRACTS.md`
gained section 4a (the tune) and 8c (what is fixed and what is theirs).

---

## E18 — The dice off the chip · done (2026-09-07)

**Ask (the contracts session, via the owner):** the Wanderer's and the
Glitch's shift register was XORed with oscillator 3 (`$D41B`) every frame;
voice 3 plays the tune, so that byte is a musical waveform sampled once a
frame: the dice were correlated with the music and could not be recomputed
from the seed. Seed the register from the block instead and stir nothing
else in.

**Done, and one step further:** the register is 16 bits, not 8. An 8-bit
register alone has a period of 255 frames, and the Glitch tests it every
frame for a burst (three chances in 256), so his bursts would have come at
the same three phases of every five-second cycle — a visible beat. The
16-bit Galois register (x^16 + x^14 + x^13 + x^11 + 1, mask $B400) has a
period of 65,535 frames, 22 minutes, and is stepped eight times a frame so
consecutive frames' bytes are not shifted copies of each other. Seeded in
`buddyInit` from `seed[28] ^ seed[15]` (low) and `seed[3] ^ seed[20]`
(high), $A55A if that is zero; bytes the contract leaves to the hash.
Both stir sites replaced by `jsr rollDice`; `$D41B` is no longer read
anywhere (the Dancer's `$D41C` stays). Model: `dice_seed`, `dice_step` in
`tools/stamp_mural.py`. **Measured:** the new `dice` test reads the
register off the machine at boot + 150, finds it on the model's trajectory
(92 rolls from the seed), and again 100 waits later (100 rolls) and 100
more with the player walking (101 rolls: the harness frame and the engine
roll are not phase-locked, hence the ±3 tolerance); all eight mechanic
tests and the bats pass on the build. Base: 46,876 bytes (unchanged: the
code fits before the level data's alignment), sha256 `d45a129aab3ad60d79b3972f1d3047b99e425a3a8845fead9cf2d67401abd7ef`, keccak256
`cedeb14bf1a39b763c696ab3d7c8fe1b43ffd24edc881efb394783fbb0c72361`, block at file offset 0x04EC9.

**Handoff corrected on the contracts session's review:** the digit loop
(`OFF + 39 - i`, not `+ 47`), the carved number (`block.number - 1`, the
block whose hash is the seed), `modes = 0`, stored-only attributes with
the moving facts in the description, the blob arithmetic (two blobs hold
49,150, headroom 2,274), the supply ladder in place of "nine per class",
and the music sentence ("relocated to $8000, identical by an eight-minute
register replay"). The rename: the owner chose **The Shy** (2026-09-07), to keep the one-word
convention of the other seven; files, code, documents, the SVG and the
vectors carry it now.

---

## E19 — Pre-freeze audit · done (2026-09-07)

The owner asked whether everything had been checked before the freeze.
Beyond the test suite (nine mechanic tests including the dice, and the bats
over sixteen seeds, all passing on the deliverable base), these were run on
`deliverables/prg/minimal64/tony-chamber.prg` (46,876 bytes, sha256
`d45a129a…`):

- **Reproducible from the committed tree.** A clean `git archive` of HEAD,
  the generators, `./gradlew build`: the generated source is identical to the
  committed one and the PRG's sha256 is the deliverable's. One nit found and
  fixed in the rebuild instructions: on a fresh clone Gradle must run once
  before `tools/build_chamber_room.py`, which needs the charset Gradle
  extracts.
- **Wall, candle and digits against the model** for the default seed, the
  all-zero and all-ones seeds and eight random seeds: 0 brick mismatches in
  1,500 slots, every candle drawn where predicted, the digits the same chars
  for the same block. (The all-ones seed is the whole wall bricked, as the
  model says.)
- **Out-of-range block bytes** (the contract never writes them, but the
  program must not die): behaviour 8 and 255, colour 16 and 255, digits 10
  and 255, all 42 bytes 0 and all 255. Alive in every case; digits above 9
  draw as blanks; the Glitch ignores his colour byte.
- **Soak**: every mechanic for 12,000 frames (four minutes) with the player
  walking, jumping and ducking: alive throughout, the buddy inside
  64..280 and on or above the floor, the Glitch wearing all seven, the dice
  moving for the Wanderer and the Glitch and still for the six that do not
  roll. The Echo alone reaches X 286: he replays the player exactly, and
  286 is where the player himself stands at the right pillar. By design.
- **No ROM ever banked in after boot**: `$01` sampled through four minutes
  of the Glitch and of the Shadow is `$35` throughout (RAM with I/O), so no
  KERNAL or BASIC code can run. The static ROM-reference scan's 97 findings
  are all data misread as code (74 in the Movable data, 23 in the level
  data and tables of the code region) or the game's own IRQ vectors in RAM.
- **Both tunes intact after four minutes of play**: the Glitch's player is
  playing instruments all of which belong to the intro tune; the Shadow's
  all belong to the level tune (the one pair outside the three-minute
  reference is one of eight the level tune first uses after its third
  minute).
- **The players' entry points read no registers** they are not given: both
  `init` routines are a store and a return; `initSound` leaves Y holding the
  behaviour, harmlessly.
- **The marker is unique** in the file (one `MURAL02`, no `MURAL01`); all
  fourteen deliverables equal the base outside their 42 bytes; the vectors
  and the record carry the base's hash.
- **The new code read line by line** in the generated source: the dice
  register, its seeding and zero guard, the tune routing at init and per
  frame, the Dance mechanic's two rereads and its cooldown rule.

Not measured directly: the raster budget of the busiest frame (the Glitch
in a burst while the intro tune plays); by the tracer the intro tune's
player costs about 320 instructions a frame against the level tune's 303,
and no per-frame test ever dropped a frame. Nothing found that needs a
change to the base.

**FROZEN (2026-09-07, the owner's word):** the base is the file in commit
`c0b350a` (46,876 bytes, sha256 `d45a129a…`, keccak256 `cedeb14b…`, the
42 bytes at file offset 0x04EC9). It does not change from here; anything
found later is fix-forward in new tokens. The sources, tools and history
stay in the repository, so a later base can be built and frozen the same
way, with a new hash.

---

## E20 — The dim room: no candle, medium grey · done, re-frozen (2026-09-07)

**Ask (owner):** rooms without a candle (one in four by the seed, a stored
class per token) could look a little darker, between the lit room and the
Glitch's blackout: the pillars, floor, ceiling and Tony. Is it possible?

**The palette allows exactly one step:** black 0, dark grey 11, medium grey
12, light grey 15, white 1. The lit stone is 15, the blackout's 11, so the
dim room is 12. It is one register: the screen's background colour, the
same one the blackout sets, so the stone, pillars, floor, ceiling and the
wall's bricks darken together. A flag byte `muralDim` (marker + 58) is set
at room entry when `seed[30] & 3 == 0`; the frame interrupt reads it and
writes 12 to the background and to Tony's sprite colour ("make the user
controlled Tony match", the owner, mid-build). The Glitch's blackout takes
precedence (his flag stays 0). The buddy keeps his colour and stands in
front of the black wall, so his legibility does not change (checked for
blue and purple, the two dark ones). Shown as a look-see first, then made
the default; `--lit-no-candle` turns it off.

**Measured on the new base** (46,877 bytes, one byte more, the flag; the
block at file offset 0x04EC9 unchanged; sha256 `67dc97bc1e3067151c8a1d24fe4bf18beabf83624c69cdb65182a34aa914ad61`, keccak256 `7677e3e91210588a9ecf781e493646836fbcde6e218173a304eb8253eeadb1ab`): the
new `rooms` test reads the three rooms off the machine, lit 15/15, dim
12/12, blackout 11/12, with the number's characters equal in lit and dim;
all ten mechanic tests and the bats pass; wall, candle, digits and room
colours match the model for eleven seeds including the extremes (0
mismatches); a clean-checkout rebuild reproduces the hash. The deliverables
were re-stamped, the vectors regenerated (their `room` field is now lit,
dim or blackout; 7 of the 32 are dim), and the screenshots redrawn from the
final build: `screenshots/chamber-dim-no-candle-m64.png` and the crop.

**Freeze:** the morning's freeze (`c0b350a`) was reopened for this before
anything had left the repository; the base is re-frozen at the commit named
in `deliverables/contract/base-record.json`.

---

## E21 — Token thumbnails: the retro layout · done, adopted (2026-09-07)

The thumbnail redesigned through ten rounds of mock-ups and adopted: the seven
colours as a row of 2 x 2 squares top left (blue, yellow, purple, green, light red,
cyan, light blue; a half-pixel gap; resting at 0.3, the token's own square breathing
to full with a glow every 3.6 s), the buddy's idle dance centred with his feet on an
eleven-row floor dithered on a half-pixel grid from his colour to black. The Glitch
is dark grey on a light-grey-to-black floor, with bursts of static whose two
brightest flips are colour sparks, the blink from E15, and a sweep of light across
his squares once per burst. `tools/buddy_retro_svg.py --final` writes the eight
files to `assets/tokens/`; all eight verified in Chromium by seeking the SVG clock
(body, floor, tag order and level, the peak, the dance frames, sparks, blink,
sweep). Sizes 13,958 to 17,729 bytes, the Glitch 25,000. `THUMBNAILS.md` is the
design log; `HANDOFF-CONTRACTS.md` section 6 describes the files for the
contract. **Frozen 2026-09-07**: first at `9880f03`, reopened the same day for one fix
(frames B, C and D rest hidden, so a still made without running the animation shows
frame A alone rather than the four frames stacked, as the Finder's preview had shown)
and re-frozen at the commit named in `contract/tokens-record.json`; the checker's
output at the freeze is `contract/tokens-verify.txt` (76 checks, eight of them the still).
Measured 2026-09-08 on the live collection page: OpenSea runs the animation in the item
grid and in the profile picture, on the desktop and on the phone.
The PRG, the vectors and the base's freeze are untouched.

## E22 — The building demo: down + fire lays a brick · built (2026-09-09)

A separate PRG (`prg/minimal64/tony-build.prg`, 43,434 bytes, sha256 `5c24a63e1c14e26c...`) from the
frozen base: no bats, the Shadow as the second Tony, down + fire lays or lifts a 2 x 2 brick in the wall
slot in front of Tony at his feet, up + fire steps him onto it. Placed bricks are four new screen codes
with wall material, drawn as a small stone block (a floor brick's two ends) so they read as built, so the engine's own collision makes them floor and wall; the Shadow got a guard on
his step so a brick stops him. Measured on the way: Tony's jump carries 48 px, too far to land on a
single brick, hence the step-up. Later the same day a second room above, reached by a seeded ladder that
hangs from the ceiling and needs five bricks to reach; each room keeps its own bricks, the Shadow stays
below. Bench of seventeen checks on minimal64 in `tools/verify_build.py`. Write-up:
`BUILD-DEMO.md`. The base, the tokens and the freeze are untouched.

## E23 — The body: the clone on Tony's own physics · built (2026-09-09)

A PRG from the building demo (`prg/minimal64/tony-body.prg`, 44,422 bytes, sha256 `b20e222253c5e7d2...`):
the second Tony runs the player's physics a second time each frame from a twenty-byte record of his own
(the physics block's layout, swapped in and out), fed a one-byte joystick a brain writes (five lines, lay,
step up; an override byte for a bench or a trainer). The first brain is the follow rule as bits. He walks,
stops at a laid brick by the physics, falls, jumps in the same frame as the player, ducks, climbs the
ladder (to a north stop, never out of the room), lays bricks and steps up them on the bench's byte, waits
in his room while the player is above. Measured on the way: two Tonys did not fit the game's frame (the
top handler ran past the visual handler's raster line and the copper skipped a physics frame one in
eight); fixed by starting the top handler at line 8, running each collision check only when it can say
something new, rewriting the check at half the cost (proved equal to the game's own over every position
by a sweep in the build, `bodySelfTest`), and dropping the bats' actors. Worst frame now ends on line 218
of 255. Bench of thirty-three checks in `tools/verify_body.py`; the harness got a `sync` command so a
peek never lands mid-swap. Write-up: `BODY.md`. The base, the building demo, the tokens and the freeze
are untouched.

## E24 — The senses, the brain slot and the builder · built (2026-09-09)

On the body: the sense block (twenty signed nibbles from a raw snapshot of his turn, packed in the main
loop, published with its frame; the packing written as the contract in `BODY.md` and checked against a
Python twin at a dozen snapshots), the brain slot (`BRAIN01`, page-aligned: an 8-byte header whose kind
says "no brain yet", 256 bytes of nibble weights, the mood; a forward pass with 16-bit accumulators
and the first-largest rule, proved equal to a Python reference on forty random vectors; a ten-action
decoder that owns the build macro and the crouch's release frame; a think every fourth frame in the
main loop, running under teaching), and the builder, a hand-written brain over the same senses and
actions that jumps a brick and climbs the player's stairs and the ladder to him. Two-weight brains as
proofs: one follows, one builds a staircase of nine. The harness got exact frames (stopping at raster
0), snapshot and restore by forking, load from a file, comments in scripts, and a page, `HARNESS.md`,
with one worked episode. Frame time: a first packing in the interrupt put the worst frame at 244,
measured against the real cost of a collision check (~24 lines); the fix was to keep the interrupt for
copies only. Write-ups: `BODY.md`, `HARNESS.md`; brains in `deliverables/brains/`.

## E25 — Learning on the machine: the rule, the golden vectors, TEACH · built (2026-09-10)

The learning rule of the brain interface on the 6502 (`brainLearn`: the mood-free prediction, a step
of one on the taught and the predicted rows, nibbles saturating at 8) behind a test hook like the
forward pass; the slot's bytes 14 and 15 (lineage, rule version) and a check that makes a malformed
slot kind 0; the Python reference and the golden vectors (`tools/brain_golden.py`,
`deliverables/golden/`: 95 cases, all agreeing on the 6502); the interface returned with every proposed
row settled (`BRAIN-INTERFACE-V1.md`). Then TEACH: the page's flag or the lay chord held a second, the
port routed to the clone with the chords translated, Tony standing, a lesson at every think tick and at
every press or release, recorded in a marked block (`LESSON1`) the page reads, a white flash per
lesson, kind 0 made kind 1 by the first. Three things had to be learned on the way. The chord that
toggled teaching off left a brick behind: not a latch bug but the brain doing what the hold had taught
it, so the hold now takes back its lessons too (the weights and counters shadowed on the chord's first
frame), and the spent chord is dead until let go. The shadow's 256-byte copy is 57 raster lines and
first landed in the frame of Tony's own lay, the heaviest, at 244 again; it is made only while teaching,
where the lay is the clone's. And the lesson's pairing: a block's own sense 16 is the action that made
the state, so pairing them teaches "in the air: jump" and never "a wall ahead: jump"; a lesson now
pairs a state with the action applied in the frame after it, and is taken at every edge as well as
every tick, since a tick alone sees the launching frame one time in four. The number, on the harness
(`tools/teach_demo.py`): from zero weights, a teacher driving the builder's rule through the port,
four sessions and thirty-six lessons until he climbs Tony's stairs and the ladder to him on his own;
the weights are `deliverables/brains/taught-climb.bin`. The harness gained an interactive mode for it.
Write-ups: `BODY.md` ("The learning rule", "TEACH"), `HARNESS.md`, `BRAIN-INTERFACE-V1.md`.

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
- The SID's readback registers ($D41B oscillator 3, $D41C envelope 3) are
  implemented in minimal64 and behave like the chip's (E11).
- Tony walks two pixels a frame; the room between the pillars is X 64..280
  for the buddy and 56..286 for Tony (E11).
- The player's X and Y are settled before the buddy's update runs in a
  frame; the duck's animation number is written after it (E11).
- The room's light colour is the screen background: the level charset is
  loaded negated, so the stone is the background register and the char
  pixels (colour RAM) are the dark; the interrupt repaints both, and the
  player's sprites, from `currentColor` every frame (E16).
- A bat's sprite starts 4 px below the top of its row (Y = 54 + 8·row),
  X = 24 + 8·column; a bat's path is replayed with the same signs after
  the turn, so a path must net to zero to hold its height (E14).
- Tony's jump: 26 frames, apex 23 pixels, three frames each of −4, −2 and
  −1 with a hover at the top, then the mirror image down; the duck's four
  frames are standing, bending, down, rising (E11).
- The tune's player keeps a 25-byte image of the SID registers at $A474
  and copies it to the chip every frame; the tune moves its notes legato,
  by frequency, with a hard restart only every 160 frames (E11).
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
- The demo has exactly two tunes, both GoatTracker exports with one song
  each, and no sound effects (E17).
- Both players touch only $FE/$FF in zero page at run time (E17).
- A page-aligned move of a tune changes only address high bytes: 289 of the
  intro tune's 5,782; replay-identical for 8 minutes (E17).
- The intro tune's voice 3 raises ENV3 by ≥ $28 on 495 of its 532 attacks;
  under the Dancer's hit rule he is airborne 99% of the time with it (E17).

## E26 — The architecture bake-off, phases 1b and 2b: binary retinas, wider weights, a reference-relative vocabulary · offline (2026-09-10)

The second architecture review's claims reproduced independently on the engine's own exact bounded
implementation, pre-registered first (`deliverables/bakeoff/PREREG-1B.md`, commit bcba27f), nothing in
the PRG touched, the sealed goal senses untouched. The pre-registration pins the reference-relative
vocabulary from an explicit signed reference vector (the horizontal sign decides toward and away; a
zero horizontal falls back to the clone's facing in the same block; the same rule translates a human's
press), the binary retinas R0/R1/R1b/R2 and the mixed controls, the three sets kept apart (the 231
teacher states, the teacher-visited 474, the full 1,424), the survivor rule and the predictions. Before
any 6- or 8-bit number was read, the rule generalised to n inputs and a box was checked against the
golden reference (identical over 729 lessons) and the vectorised learner against it after every lesson
at 4, 6 and 8 bits (`parity-1b.json`), with byte-boundary, tie and wrap vectors written for a later
6502 (`golden-1b/`) and the 16-bit accumulator bound asserted for 128 unit-flag inputs (16,512).

Phase 2b (`PHASE2B.md`, `phase2b.json`): the review's box result reproduces to the lesson (the binary
retina at 6 or 8 bits: 384 lessons on the tick stream held 277 of 300, 428 on the cycled labels held
263, weights never above 25; the four-lesson cycle at 4 bits with 931 clamps; the mixed controls at
their cycle with zero clamps). Under the relative vocabulary every binary arm learns the 231 in about
half the lessons, learns the 474 from its own stream (849 lessons for R0, 538 for R1b), and R0 fits
at 4 bits; the mixed controls learn too, A2 even at 4 bits, so the review's "graded step" cause is not
supported. The order-2 arm learns fastest, not slowest. Five percent label noise costs about 75
corrective lessons a pass at any box and the fit never holds; the lagged stream as pre-registered has
a ceiling of 178 of 231 for any policy, so no arm survives the rule as written and the defect is the
stream's. From the curriculum stream alone every arm leaves about sixty of the 474 wrong, in
situations the curriculum never showed.

Phase 1b (`PHASE1B.md`, `phase1b.json`): CP-SAT, plain feasibility first and then a maximum feasible
subset warm-started from the Phase 2b weights, every unfit state named, CBC and LP relaxations as
cross-checks. Under the absolute vocabulary the teacher-visited residual of every binary first-order
retina is exactly one state, drawn from a four-member family of builds whose direction flips with the
side (the review's two kinds, count sharpened from two to one, the same family under the forced-fit
probe); the named facts do not remove it, the order-2 layer fits everything, and so do the mixed
encodings (A2 the whole 1,424 with 4-bit weights, T36 the 474), which the rule cannot learn. Under the
relative vocabulary R0 fits the 231 and the 474 exactly and misses the 1,424 by one state; R1 (one
more fact, facing the reference's way) fits the whole union with 62 inputs. Two of Phase 1's three
undecided union cases settle as feasible. `BRAIN02-BUDGET.md` gives the exact slot, accumulator and
memory arithmetic per architecture: R0 fits the present map at the 500-lesson cap only with a small
retina, R1 and R1b at a cap near 470, the goal senses at about 310 with the 14-byte lesson, and R2
not at all (337 inputs overflow the 16-bit accumulator). One exploratory arm after the
pre-registration, outside the selection: a binary retina whose dx flags are a signed thermometer (61
inputs) represents every set in both vocabularies at 4-bit weights and learns the 231 in 276 lessons
and the 474 from its own stream under the absolute vocabulary, so the residual was the dx encoding;
it goes to the next pre-registration. No BRAIN02 was built and no PRG changed.

## E27 — BRAIN02 on the machine: byte weights, a published retina, the relative vocabulary, the lesson ring · built (2026-09-11)

Phase 3 of Chamber v2 (`deliverables/bakeoff/PREREG-PHASE3.md`, `PHASE3.md`, `WORKBENCH-INTEGRATION.md`):
the research brain in the generator (`make_chamber.py --brain02 RETINA --vocab rel|abs`,
`tools/brain02_asm.py`), four playable PRGs (A: R1b, B: R0s, the R0 vocabulary pair) and a 128-input
parity build. The slot has a 24-byte header with the vocabulary, the retina id and a lifetime education
count; the retina is a published table interpreted on the 6502 over the twenty senses and nine named
pseudo-senses; the forward pass adds the weights of the set flags into 16-bit accumulators; the rule is
the symmetric step at the byte box; a relative action is resolved once per think from the block's own
reference vector and facing; the LESSON2 ring records every applied lesson, pauses learning when full,
and reclaims only a range the host acknowledges with the right checksum; the teaching shadow is taken
and put back by the main loop, never interleaved with a lesson; CIA 2 timer A measures the machine's
own cycles. Every gate passes on every candidate: the retina byte for byte on all 1,424 recorded blocks,
the golden sets at every width (the 16-bit extremes at 128 inputs), the vocabulary's 40 cases, the
malformed-slot fallback, Phase 2b's learned brains reproduced on all 474 teacher-visited blocks; think
and lesson inside a frame (about 11,000 to 19,000 cycles), raster maximum 174 with no overruns; TEACH
end to end with 33 lessons to climb on A and the climbed brain
climbing again after export and reload; three and more ring cycles with byte-exact replays, the
full-ring pause, refused acknowledgements, and the recorded sequence replayed uninterrupted giving the
same brain. Two mechanics were found and fixed on the way: lessons were being lost whenever the main
loop fell behind a frame (a per-frame ring of applied actions now makes the pairing independent of the
main loop's pace: 79 lessons in 99 chattering ticks against 33 before), and the deferred restore
had a one-frame window (closed in the clone's turn). Stopped at Checkpoint C for the owner's first
human session; the sealed Phase 4 sweep is not run.

## E28 — BRAIN02.5: more eyes, not more brain · built (2026-09-11)

A person played freely, built arbitrary obstacle courses for a blank Tony, and came back with a reading:
the limit is not the size of the brain but how little of the terrain he can see. This experiment asks
the one question that follows. **How much more reliably can the same learner be taught, when the
smallest useful increase in local terrain observability is added to the sensed state?** Nothing about
the learner changes: the ten reference-relative outputs, the byte weights, the symmetric rule at the
byte box, the first-largest tie, and inputs 0 to 63 with the meanings and the order R1b gave them.

Branch `claude/brain025-terrain-observability`, beside BRAIN02, which is frozen and untouched: its PRGs
still hash the same, its four gates still pass, and Candidate A rebuilds byte for byte from the modified
generator.

**The census (step C).** 192 scenarios over 32 local terrains, measured on the frozen Candidate A build,
collapse to **21 distinct observations**, and 17 of those are consequential aliases: the world acts
differently inside them and BRAIN02 cannot tell which world it is in. The largest single observation
covers eleven geometries in which walking toward Tony drops the clone off an edge in nine of them and is
safe in two. Consequence was measured, not asserted: the brain was made to choose each output in turn by
its bias weight, so the decoder, the macros and the vocabulary all ran as in play, and the outcome was
read from Tony's own position.

**The design (step D).** Eleven candidate terrain quantities were defined and scored; a search that
removes the most conflicting scenario pairs per input reached zero after nine thresholds. The published
design is the smallest ordinal thermometers containing all nine: **sixteen inputs over seven quantities**
(`tSafeRun`, `tGapW`, `tFarRun`, `tObstH`, `tObstTop`, `tHead`, `tBackRoom`), appended at 64 to 79 and
measured in the toward frame the vocabulary already uses. Over the same scenarios the distinct
observations rise from 21 to 93, and both the 34 consequential splits and the 636 conflicting pairs fall
to zero.

**On the machine.** `tony-b025-a.prg`, 52,092 bytes, sha256 `2a547ebf...`: marker `BRAIN025`, layout 3,
80 inputs, a 27-nibble sense block, a 15-byte lesson record in a ring of 180, a terrain probe inside the
sense packer that equals its offline model on all 192 census scenarios, a blank Tony with no follow rule
behind him, and a teaching toggle on the T key so the joystick keeps every verb it had.

**The gauntlet (step H),** on twenty fresh courses that had no part in choosing the design, both builds
judged against one measurement of what the world does:

| | Candidate A, 64 | BRAIN02.5, 80 |
|---|---|---|
| lessons to competence | never: 98% after 882 | **74 lessons, 9 passes, 100%** |
| distinct observations over 180 situations | 37 | 99 |
| representable at all | yes | yes |
| retention after unrelated teaching | 98% → 54% | 100% → 72% |
| taught far off, right on the ladder | 67% | 100% |
| regressions | — | 0 |

Both brains can express the behaviour; only one can be taught it. Migration is exactly clean: zero
prediction mismatches, 711 on the machine and 12,816 off it.

Two findings do not flatter the design and are reported with the same weight. **Teaching still
interferes with itself**: an unrelated later stream costs BRAIN02.5 28 points of accuracy and BRAIN02
44, and more eyes do not cure it. And **at eighty inputs the think and the lesson no longer fit inside
one frame** of main-loop time (24,129 and 26,747 against 19,656), though both finish inside the
four-frame think period with no overruns and a raster maximum of 141 against BRAIN02's 174.

Three of the seven pre-registered predictions were wrong, and are scored as such in `RESULTS.md`: the
most valuable single input was the standing room above an obstacle, not the gap ahead; obstacle height
above the head row was not consequential on its own; and the machine did not hold the one-frame bound.

Everything is in `deliverables/brain025/`. The 300-lesson human brain is not in this repository, so the
one deliverable that needs it stays outstanding with the command and the expected result written down.
This is a research build: not a production architecture, nothing deployed, nothing merged over BRAIN02.

## E29: vis3 - the transition effect, the trained state, and two defects found on the way

Four changes to the BRAIN02.5 playable candidate, in the order the owner asked for them. Written up in
`deliverables/brain025/VIS3.md`; the PRG is `tony-b025-a-vis3.prg`, 52,098 bytes, sha256
`a9efe9d00afd0cfc9453acbcb0fe6b0faa8fe6f7f83f43635c2bd4ee80ef12ec`. The frozen research artifact and
both earlier visual candidates are untouched and still regenerate from the generator byte for byte.

**The room transition is now an effect on purpose.** The redraw between rooms was always visible for
eight frames - the room being rebuilt in raw map codes, stamped over, then translated - and what hid it
was the fade dipping the background to black. vis1's dark room above outranked that fade by accident,
one way only. It is now deliberate in both directions, gated on `roomChange` so the death, game-over and
level-start fades are provably untouched, and held by a `transit` gate that fails on vis2.

**Two defects were found by measuring rather than by looking.** The routed clone stood back up out of
his crouch while down was still held, because `teachRoute` substituted the build verb for the whole
stick where the player's own `buildVerb` adds it - and his published `ducking` sense, input 5 of the
network, recorded 0 for a pose the player's body reports. The taught action was provably unaffected
(`actionOf` reads bits 5-6 first, so a build frame is 8 or 9 either way), so this was a fidelity defect
in the observation only. Separately, the "75" in the upper room's corner turned out not to be level data
at all: `muralBatsStamp` writes its parameters through the room's static-object array pointers, and a
room with no objects has zero-length arrays whose pointer is simply the next label - which for chamber 0
is chamber 1's compressed map. Two bytes of level data were being overwritten at every level start.

**The clone's trained state is legible without a new signal.** `brainEducation` modulates one thing: how
often the white dropout comes - one frame in 16 untaught, then 32, 64, and 128 as a floor it never
passes. An untaught copy flickers, a taught one is steady, and it never stops flickering entirely.

The first build of vis3 got the bat guard's sink one byte too small, and the owner found it in a
minute of play: the stores are indexed by y, so the right bat spilled onto `muralRowA` and the back wall
stamped itself across the ceiling of both rooms. The same bug shape as the one being fixed, one label
further along. It is two bytes now, and the gate that missed it - it checked the packed map and a fresh
draw, never the ceiling after a round trip - checks that too.

Fifteen gates pass, 81 checks, no failures. Two existing gates had to change and both changes are
recorded rather than quietly made: `visual`'s dropout expectation moved with the behaviour, and
`drain`'s acknowledgement handshake was given six frames instead of two after it scored a refusal the
machine had never made. A third hazard was closed: `gate_session` was overwriting the hash-pinned
canonical replay session with a recording from whatever build it was handed.
