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
(a few hundred bytes to ~1.2 KB each: rewired exits, colour scheme, the
cheat-state fix, a 75-byte edge guard, and a rewritten room block where a
ladder or floor hole had to be capped), each with its patched PRG and a JSON
of the exact records, all play-tested on minimal64 including the "walk out of
the entry room" scenario the first player hit. Generator
`tools/onchain_castle.py`, play-tester `tools/verify_castle.py`, capture
`tools/capture_runtime_rooms.py`, diagram `tools/castle_diagram.py`.
Everything is documented in **`ONCHAIN-CASTLES.md`**, including the
field report on the first play-test and what it changed.

## Documents

- **`ONCHAIN-CASTLES.md`** — the on-chain PRG's patch map (offsets of every
  table), the castle patch scheme, the three verified samples, and two
  measured findings about the deployed bytes.
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
+ `src/kickass/cheatmenu-romfree.asm`. `screenshots/` holds before/after and
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
