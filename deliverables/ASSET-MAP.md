# Tony: Born for Adventure (C64 demo) — Asset Map

Repository: `maciejmalecki/tony-demo` @ `75f62f5b` (MIT, © 2023 Maciej Małecki).
Toolchain: Gradle + [c64lib retro-assembler plugin 1.7.6](https://github.com/c64lib/gradle-retro-assembler-plugin)
(KickAssembler 5.25 dialect) + c64lib 0.5.0 libraries (`common`, `chipset`, `copper64`, `text`).

## Build pipeline in one paragraph

`./gradlew build -x downloadDeps` runs three stages. (1) **Preprocess** (declared in
`build.gradle.kts` `preprocess {}` block): CharPad `.ctm` files are cut into raw
charset/map/materials binaries under `build/charpad/`; SpritePad `.spd` and plain
PNG sprite sheets are converted into 64-byte hardware sprite binaries under
`build/spritepad/` and `build/sprites/`. (2) **Assemble**: KickAssembler builds the three
program parts — `src/kickass/tony.asm` → **`src/kickass/tony.prg`** (the complete, directly
runnable game, load address `$0801`, `SYS 2240`, 56,361 bytes), plus `splash-zzap.bin` and
`intro.bin`. The `libDirs` setting makes `build/charpad`, `build/sprites`, `build/spritepad` and
`src/music` visible to `.import binary` / `LoadSid` directives. (3) **Pack/link** (optional,
needs the external `exomizer` binary): compresses the three parts and links them via
`tony-loader.asm` into the distribution `tony-e.prg`/`tony-e.d64`. Without exomizer these
finalizer tasks fail — expected and harmless; `tony.prg` is already complete.

Memory layout (from `src/kickass/_constants.asm:26-67`): code from `$08C0`, music at
`$A000`, level charset workspace `$C800`, screens at `$C000`/`$C400`, dashboard charset
`$D000`, sprite shapes `$E000-$FFFF`. Assets are stored once in the PRG ("Movable" segment)
and copied to their VIC-visible homes by `unpack:` (`tony.asm:131-171`) at boot.

---

## (a) Sprites — the protagonist

**Source art:** PNG sheets in `src/spritepad/` (32×32 px per frame, laid out horizontally).
Conversion rule (plugin `C64SpriteWriter` + `ReadPngImageAdapter`): *alpha is ignored;
RGB (0,0,0) = background bit 0; any other RGB = figure bit 1*. Each 24×21 cell packs to
63 bytes (3 bytes/row, MSB = leftmost pixel) padded to 64.

| Animation | Sheet (frames) | Output bins (`build/sprites/`) |
|---|---|---|
| walk | `tony chodzenie 4 klatki.png` (4) | `tony-walk-right_*.bin`, mirrored → `tony-walk-left_*.bin` |
| duck | `tony kucanie 4 klatki.png` (4) | `tony-duck-{left,right}_*.bin` |
| idle | `tony spoczynek 4klatki.png` (4) | `tony-idling-{left,right}_*.bin` |
| jump | `tony skok 2 klatki.png` (2) | `tony-jump-{left,right}_*.bin` |
| ladder | `tony_drabina.png` (2) | `tony-ladder_*.bin` |
| death | `tony smierc lewo 5klatek.png`, `... prawo 5klatek.png` (5 each) | `tony-death-{left,right}_*.bin` |

Each sheet has a **`.bg.png` twin**: the dark "backdrop plate" drawn behind Tony so the
light playfield doesn't shine through the line art. It is converted with `reduceResolution
reduceY=2` (every 2nd row) into **one** 24×21 sprite per frame and displayed **Y-expanded**
(`SPRITE_EXPAND_Y = %100`, `animations.asm:57`).

**How a frame reaches the screen:** the 32×32 frame is extended to 48×42 (top-left anchored,
black fill) and split into 24×21 quadrants; only the *left column* (quadrants 0, 2) is
imported ⇒ usable art area is x 0..23 of each frame. The player is drawn with hardware
sprites 0 (top half), 1 (bottom half), 2 (bg plate); enemies use sprites 3–6; sprite 7 is
the dashboard "eyes". Left-facing frames are generated in `build.gradle.kts` by
`cut(width=4*32−7) → flip(Y) → extend`, i.e. mirror plus a 7 px re-alignment shift.

**Frame → VIC slot wiring:** `src/kickass/sprites/player.asm` imports the bins in bank
order; `_constants.asm:239-263` names the slot bases (`PLAYER_BANK_WALK_LEFT` = slot 128,
…, `ENEMY_SKULL` = +120, `DASHBOARD_EYES` = +124); `animations.asm:210-278` builds the
per-phase sprite-pointer tables, and the engine animates by rewriting the three sprite
pointers at `SCREEN_MEM_0+1016..1018`. All player sprite data is copied to `$E000`
(`SPRITES_MEM`) by `unpack:`. Frame *counts* are fixed by `animationLength`
(`animations.asm:152`) and the `.fill` tables — changing art must keep counts.

Other sprites: skull enemy `czaszka pionowa.png` → `level/demo/bitmaps/skull.asm`
(4 frames, bank 1); vertical bat `nietoperek pionowy.png` and deadman `trupek zamek.png`
→ bank 2 (stored over the spare half of screen 1 RAM); horizontal bat
`nietoperz new 4 klatki 16x16b.png` → bank 3 (top of dashboard charset RAM);
dashboard eyes `eyes.spd` (SpritePad v5 format, the only .spd actually used).

## (b) Character sets / background tiles

All in CharPad CTM format, `src/charpad/` (v8 files start `43 54 4d 08`, castle is v9).
Format details: header (10 bytes v8 / 15 bytes v9 after `CTM<ver>`), then `$DA $Bn`-marked
blocks: charset (8 bytes/char), per-char **materials** (collision class), optional colours,
map (16-bit cells, little-endian; low byte = char code). `tools/ctm_tool.py` in this repo
parses and patches all 11 files byte-exactly.

| File | Chars | Map | Used for |
|---|---|---|---|
| `castle_map.ctm` (v9) | 255 | 200×120 | **the whole game level** — charset + materials + 30 room maps |
| `demo-level.ctm` (v8) | 255 | 200×120 | only region x160-199,y0-19 → **title screen room** (overrides map-4-0) |
| `belka-nowa-20023-v5.ctm` (v8) | 159 | 40×4 | dashboard (bottom 4 rows) charset + map |
| `font.ctm` | 37 | – | in-game text font (swapped into dashboard charset on demand) |
| `game-end.ctm` | 84 | – | game-over/end screen art (loaded negated) |
| `historia3.ctm`, `intro-font.ctm` | – | – | intro part only |
| `splash-screen-e.ctm`, `splash-screen-zzap.ctm` | – | – | splash part only |
| `dashboard.ctm`, `game-paused.ctm` | – | – | **unused leftovers** (not referenced by build) |

The level charset is imported **negated** (`loadNegated`, XOR $FF — the game renders dark
art on a light background): `level/demo/data.asm:543`. Materials byte per char (from the
CTM materials block, `build/charpad/demo-level-materials.bin`) carries collision classes
(`_constants.asm:146-155`): bit0 wall, bit1 ladder, bit2 killing, bit6 collectible.

## (c) Level maps and screen composition

`build.gradle.kts:157-205` slices `castle_map.ctm`'s 200×120 map into a 5×6 grid of
**30 rooms** (40×20 chars), `build/charpad/demo-level-map-<x>-<y>.bin` (800 bytes each,
1 byte/cell). Room index = `x + 5*y`. Room 29 (grid 4,0) is the **title screen** and its
map bin is overwritten from `demo-level.ctm` by a second charpad block.

`src/kickass/level/demo/data.asm` is the level master file. For each room the
`_level_pack` macro (line 56): RLE-compresses the map at assembly time
(`compressRLE3`, escape byte $FF), records N/E/S/W exit room numbers, computes the room's
"used chars" list (the engine decodes only those chars into `$C800` per room —
`decodeRoom`, `tony.asm:2093`), and emits the static-object tables. Start state:
`level_startRoom = 29`, start position, `STATE_ON_GROUND_LEFT` (`data.asm:32-39`).
Screens are drawn by `drawPlayfield` → RLE-decode → char-code translation → static
objects overdrawn (`initObjects`).

## (d) Color tables — the 6 selectable schemes

A **scheme** is 4 C64 colors: LIGHT (playfield paper), DARK (border/ink/sprite plate),
BRIGHT (dashboard highlights), DIMMED (dashboard disabled).

* **Definitions:** `src/kickass/_constants.asm:365-397` — `SCHEME_<NAME>_<ROLE>` labels
  for CLASSIC (grey/black/white), AMBER, GREEN, BLUE (monitor styles), C64 (blue/lt-blue),
  C128 (green/dk-grey); `MAX_COLOR_SCHEME = 6`.
* **Lookup tables:** `src/kickass/tony.asm:3567-3571` — `colorScheme` (current index,
  initial 0), `colorLights`, `colorDarks`, `colorBright`, `colorDimmed` (6 bytes each,
  indexed by scheme).
* **Static defaults referencing scheme 0** that must be kept in sync: copper-list dashboard
  split `dashboardColor` entry (`tony.asm:55`, `IRQH_DASHBOARD_CUTOFF` arg =
  `SCHEME_CLASSIC_DARK`), `currentColor` (`:3531`), fade ramps `fadeOut`/`fadeIn`
  (`:3542-3543`), and `init` writes `ldx #0; stx colorScheme` (`:92-93`).
* **Runtime:** joystick UP on the title screen cycles schemes (`handleTitleScreenCommand`
  → `nextColorScheme`, `tony.asm:1772`), which rewrites the copper entry + fade ramps and
  calls `setColors` (`:286`) to repaint color RAM and sprite colors.

## (e) Enemy placement / behaviour data

All placement lives in `src/kickass/level/demo/data.asm` room declarations:
`object(TYPE, value, colX, rowY)` / `objectExt(..., value2)` (types `SO_*` in
`_constants.asm:283-298`). Control byte = `type | value<<4` where `value` = animation
phase shift or mode; `value2` = movement period/amplitude (skull, deadman, vertical bat)
or **path id** (horizontal bat). Bat flight paths `path0..path9` (`data.asm:528-541`) are
`(count, deltaY)` pair lists replayed forward/backward. Behaviour code: `runActors`
(`tony.asm:1228` — skull, bat, vertical bat, deadman movement), snakes/pikes/stones are
char-based "static object" mechanics in `initObjects`/`playEffects`, with the shared
sprite/char art in `src/kickass/level/demo/bitmaps/*.asm` (each imports bins from
`build/sprites/`, mostly negated for char-based objects). Static-object charset slots
`SOC_*` sit at the top of the level charset (`_constants.asm:310-323`).

## (f) Music & sound effects (identify only)

* `src/music/TonyLevelA000_V2.sid` — main game tune, loaded via KickAssembler
  `LoadSid` (`tony.asm:42`), relocated to `$A000`, driven from the raster interrupt
  (`playMusic`, with a 6th-frame skip on NTSC). Music by Sami Juntunen (title credits).
* `src/music/tonyintroe000_1.sid` — intro tune (`intro.asm:96`).
* No separate SFX engine in the demo; "sound effects" are part of the SID tunes.
* `initSound`/`playMusic` in `tony.asm:3445-3467`. **Not modified in this project.**

---

## Where the game logic lives (for orientation)

`tony.asm` (main loop, raster copper list via c64lib copper64, room drawing, objects,
scoring), `physics.asm` (player state machine), `animations.asm` (sprite pointer
animation), `actors.asm` + `static-objects.asm` (enemy/object plumbing), `io.asm`
(joystick), `sequencer.asm` (timed callbacks), `aux-screens.asm` (game-over/end),
`cheatmenu.asm` (boot-time Y/N menu — press RETURN or joystick fire to skip),
`graph-text.asm`/`graph-bitmap.asm` (screen drawing macros), `exodecrunch.asm`
(third-party Exomizer decruncher, license header intact), `intro.asm`/`splash-zzap.asm`
(other program parts), `tony-loader.asm` + `_loader.asm` (final linking, d64 building).
