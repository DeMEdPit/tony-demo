# Deliverables index

Mission: become the resident expert on the Tony C64 demo codebase and prove
control by shipping modified, playable PRG builds.

- **`ASSET-MAP.md`** — Phase 1: where every asset class lives, its format, and
  how it flows through the build (sprites, charsets, level maps, color
  schemes, enemy data, music).
- **`CHANGELOG.md`** — Phase 2: the three escalating edits, files touched,
  bytes/regions changed, PRG sizes.
- **`WRITEUP.md`** — honest assessment: easy/hard/tooling for an agent as
  pixel artist.
- **`prg/`** — the builds (each cumulative, all boot in VICE):
  - `tony-baseline.prg` (56,361 B) — unmodified reference
  - `tony-edit1-palette.prg` (56,365 B) — EMBER scheme default
  - `tony-edit2-sprites.prg` (56,365 B) — Golem Tony redesign
  - `tony-edit3-level.prg` (56,480 B) — title text + new room-18 platform
- **`screenshots/`** — VICE captures, `baseline-*` vs `modded-*` (title,
  first gameplay room, and a second gameplay frame).
- **`assets/`** — renders: full 30-room castle map, title screen before/after,
  room 18 after, sprite sheet before/after, golem walk frames from the built
  binaries.

Tooling lives in `/tools`: `ctm_tool.py` (CharPad CTM inspect/patch),
`sprite_tool.py` (PNG ↔ ASCII ↔ C64 sprites), `restyle_tony.py` (the sprite
redesign as a program), `edit3_level.py` (level patches), `c64shot.py`
(headless VICE driver for play-testing and screenshots).

Build (from repo root, needs Java 15+; exomizer-task failures are expected):

    git clone https://github.com/c64lib/common.git .ra/deps/c64lib/common -b 0.5.0
    git clone https://github.com/c64lib/chipset.git .ra/deps/c64lib/chipset -b 0.5.0
    git clone https://github.com/c64lib/copper64.git .ra/deps/c64lib/copper64 -b 0.5.0
    git clone https://github.com/c64lib/text.git .ra/deps/c64lib/text -b 0.5.0
    ./gradlew build -x downloadDeps        # -> src/kickass/tony.prg
