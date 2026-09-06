# Deliverables index

Playable builds of Tony: Born for Adventure (demo) and custom boards made
from its engine, organized by target.

## `prg/minimal64/` — plays on minimal64 (and everywhere else)

Verified on a natively-compiled [minimal64](https://github.com/DeMEdPit/minimal64)
(no Commodore ROMs present) via `tools/m64-harness/`. **Backwards
compatible**: these also run on a full-firmware C64 — real hardware, VICE,
any emulator (verified in VICE as well).

| file | bytes | what it is |
|---|---|---|
| `tony-buddy.prg` | 37,310 | the tall pillar chamber: no menu, no dashboard, loads straight in — your Tony plus the green mimic Tony (follows, faces you, hops when you jump, idles like the real one), two bats up high |
| `tony-chamber.prg` | 41,094 | the Chamber: the tall pillar room with a brick ceiling and plain pillars, Tony, the buddy and two bats; its back wall (bricks and density — fewer bricks common, the near-full wall the rare roll), one candle that appears three times in four somewhere on the upper or middle wall, the block number carved into the floor's right end, and the two bats (which of eight flight paths each flies, where it starts, whether it is there: no bats one render in sixteen, one bat one in four) are drawn from the 42-byte parameter block in the file (`tools/stamp_mural.py`: 32 seed bytes, 8 block digits, the buddy's behaviour byte and colour byte; a contract writes them at render time). Default block: block 25850267, behaviour 0 Follow, colour 5 green |
| `tony-chamber-block-25850271.prg` | 41,094 | same build, seed "block 25850271": eighth wall (the most common roll), no candle |
| `tony-chamber-block-25850251.prg` | 41,094 | same build, seed "block 25850251": eighth wall, candle low right |
| `tony-chamber-block-25850252.prg` | 41,094 | same build, seed "block 25850252": quarter wall, candle upper middle |
| `tony-chamber-block-25850254.prg` | 41,094 | same build, seed "block 25850254": half wall, candle low middle |
| `tony-chamber-block-25850256.prg` | 41,094 | same build, seed "block 25850256": the rare three-quarter wall, candle |
| `tony-chamber-the-shadow.prg` | 41,094 | the same build with the token's behaviour and a provisional colour stamped: The Shadow (Follow, blue): keeps his distance, faces Tony, jumps when Tony jumps (Tony's own arc, measured) and crouches when he crouches. `tools/verify_buddy.py` is the scripted test of all seven |
| `tony-chamber-the-dancer.prg` | 41,094 | the same build with the token's behaviour and a provisional colour stamped: The Dancer (Dance, cyan): side-steps and turns with the bass line, bounces on voice 3's hits read from the chip; his path is the music's, not Tony's. `tools/verify_buddy.py` is the scripted test of all seven |
| `tony-chamber-the-echo.prg` | 41,094 | the same build with the token's behaviour and a provisional colour stamped: The Echo (Echo, yellow): replays Tony exactly four seconds behind, every step, jump and duck, wherever he was and whatever he looked like. `tools/verify_buddy.py` is the scripted test of all seven |
| `tony-chamber-the-mirror.prg` | 41,094 | the same build with the token's behaviour and a provisional colour stamped: The Mirror (Mirror, light blue): Tony's reflection about the room's centre line, facing the way the reflection would; crouches while Tony is in the air, bounces while Tony is crouched. `tools/verify_buddy.py` is the scripted test of all seven |
| `tony-chamber-the-wanderer.prg` | 41,094 | the same build with the token's behaviour and a provisional colour stamped: The Wanderer (Wander, green): strolls, pauses, sits and jumps now and then on the chip's dice, turns at the pillars, ignores Tony. `tools/verify_buddy.py` is the scripted test of all seven |
| `tony-chamber-the-shy-one.prg` | 41,094 | the same build with the token's behaviour and a provisional colour stamped: The Shy One (Shy, light red): runs when Tony comes close, cowers at the pillar, bolts straight past Tony when he is almost on him, creeps back when he leaves. `tools/verify_buddy.py` is the scripted test of all seven |
| `tony-chamber-the-sleeper.prg` | 41,094 | the same build with the token's behaviour and a provisional colour stamped: The Sleeper (Sleeper, purple): dozes crouched until Tony comes close, follows a while, dozes off. `tools/verify_buddy.py` is the scripted test of all seven |
| `tony-chamber-the-glitch.prg` | 41,094 | the same build with behaviour 7: The Glitch, the eighth mechanic, wears one of the seven at a time and teleports into the next every few seconds, cycles the seven colours, blinks and jitters in bursts; his room is the blackout, no wall, no candle, no bats, the stone dark grey and Tony grey, only the block number in the floor, in light grey |
| `tony-trainer-romfree.prg` | 56,520 | the full game with the five-toggle "official trainer" boot menu rendered in the game's own font (no character ROM needed) |
| `tony-trained-nomenu.prg` | 55,770 | the full game, no menu, infinite lives baked in at build time |

## `prg/c64-roms-required/` — needs full firmware for now

These builds are fine games, but their boot cheat menu draws its text
through the **character ROM** — on minimal64 (whose char ROM is zeros) they
boot to an invisible menu on a black screen. They still start if you blindly
press fire/RETURN, and the games themselves are ROM-free — so each of these
can be promoted to `minimal64/` later by applying the same treatment as the
romfree trainer (own-font menu, or menu removed).

| file | bytes | what it is |
|---|---|---|
| `tony-trainer-kernal.prg` | 56,480 | the stock current build, untouched — the readable-menu build for full-firmware machines |
| `tony-baseline.prg` | 56,361 | unmodified upstream reference build |
| `tony-edit1-palette.prg` | 56,365 | + EMBER color scheme as boot default (Phase-2 edit 1) |
| `tony-edit2-sprites.prg` | 56,365 | + "Golem Tony" protagonist redesign (Phase-2 edit 2) |
| `tony-edit3-level.prg` | 56,480 | + title-screen lettering and new room-18 platform (Phase-2 edit 3) |
| `tony-vault.prg` | 37,732 | "The Idol Vault" custom single-screen board |
| `tony-colonnade.prg` | 37,448 | "The Colonnade" empty pillar chamber with three bats |

## `onchain/` — patches over the mainnet PRG

`tony-token-edition.prg` is the exact PRG the Ethereum PoC721 token serves
(`prg()`, keccak256 `0x5bcd208f…`), with its byte-exact symbol file and the
engine's runtime collision map of all 30 rooms (`runtime-collision.json`).
`castles/` holds three sample "mini castles" — patch sets over those bytes
(167–192 bytes each: rewired exits, colour scheme, the cheat-state fix and a
108-byte edge guard with a per-castle "wall" or "void" mode; a room block is
rewritten only when a floor hole must be filled), each with its patched PRG
and a JSON of the exact records, all play-tested on minimal64 including the
scenarios the first player hit: walking out of the entry room, climbing a
ladder that used to lead to another room and back down, and walking back
into the door you came in by. Generator
`tools/onchain_castle.py`, play-tester `tools/verify_castle.py`, capture
`tools/capture_runtime_rooms.py`, diagram `tools/castle_diagram.py`.
Everything is documented in **`ONCHAIN-CASTLES.md`**, including the
field report on the first play-test and what it changed.

## Documents

- **`THE-GLITCH.md`** — the eighth token: what the Glitch does, the blackout
  room, how the idea arrived and why it was built the simple way, the
  decisions made on evidence, and what it means for the contract.
- **`HANDOFF-CONTRACTS.md`** — for the agent writing and deploying the
  Chamber contracts: what is on mainnet, the base program and its 42-byte
  parameter block, what `tokenURI` must do, the SVG image exactly, how to
  prove it before deploying, the deployment order, open decisions.
- **`ONCHAIN-CASTLES.md`** — the on-chain PRG's patch map (offsets of every
  table), the castle patch scheme, the three verified samples, and two
  measured findings about the deployed bytes.
- **`EXPERIMENTS.md`** — the experiment ledger: every experiment started,
  its status, what it produced and taught, what is open.
- **`TRAINER.md`** — the trainer builds and the full ROM-free verification
  (on-target runs + static scan).
- **`VAULT.md`** — the Idol Vault board: design, route, how it's made.
- **`ASSET-MAP.md`** — where every asset class lives and how it flows
  through the build (sprites, charsets, level maps, color schemes, enemies,
  music).
- **`CHANGELOG.md`** — the three Phase-2 edits in detail.
- **`WRITEUP.md`** — honest notes on modding this codebase as an agent.

Boards recap (details in the docs): "The Colonnade + Buddy" sources are
`tools/build_tall_room.py` + `tools/make_buddy.py` (green buddy AI, tall
25-row room, physics fork); the Vault is `tools/build_custom_room.py` +
`src/kickass/level/custom/`; the trainers come from `tools/make_trainers.py`
+ `src/kickass/cheatmenu-romfree.asm`. The token thumbnail (the buddy's idle dance
as an animated SVG, one file per colour, the buddy alone at 48 px) is
`tools/buddy_thumbnail.py` → `assets/tokens/the-<name>.svg`, the eight by token name (`--tokens`; the Glitch's cycles the seven colours), and `assets/buddy-idle-<colour>.svg` by colour;
`assets/buddy-thumbnail-seven.png` shows the seven chosen colours,
`assets/buddy-thumbnail-options.png` the layouts that were considered, and
`assets/buddy-palette-16.png` all sixteen C64 colours on the Chamber's black. `screenshots/` holds before/after and
on-target captures (`*-m64-*.png` are minimal64 framebuffer grabs;
`buddy-m64-*.png` show the buddy build booting straight into the chamber).

Note on the working tree: it carries the regular look (original Tony art,
classic scheme default; EMBER remains selectable). The Phase-2 edit builds
are archived here and their sources live in git history.

## Build everything

    git clone https://github.com/c64lib/common.git .ra/deps/c64lib/common -b 0.5.0
    git clone https://github.com/c64lib/chipset.git .ra/deps/c64lib/chipset -b 0.5.0
    git clone https://github.com/c64lib/copper64.git .ra/deps/c64lib/copper64 -b 0.5.0
    git clone https://github.com/c64lib/text.git .ra/deps/c64lib/text -b 0.5.0
    ./gradlew build -x downloadDeps   # exomizer-task failures are expected

Outputs land in `src/kickass/`: `tony.prg` (full game), `tony-room.prg`
(vault), `tony-pillars.prg` (colonnade), `tony-buddy.prg`,
`tony-trained.prg`, `tony-trainer-romfree.prg`, plus the splash/intro bins.
