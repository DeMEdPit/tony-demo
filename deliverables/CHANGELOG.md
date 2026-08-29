# Modified builds — changelog

Base: `maciejmalecki/tony-demo` @ `75f62f5b`, MIT (code © 2023 Maciej Małecki,
graphics © 2023 Rafał Dudek, music © 2023 Sami Juntunen — all LICENSE files
retained unmodified; these changes are MIT-licensed derivative work and the
music is untouched). The edits are **cumulative** — each PRG contains the
previous edits too. All PRGs are `src/kickass/tony.prg` outputs: load address
`$0801`, BASIC `SYS 2240` stub, directly runnable in VICE (`x64sc tony-*.prg`).

| PRG (`deliverables/prg/`) | bytes | contains |
|---|---|---|
| `tony-baseline.prg` | **56,361** | unmodified build (matches expected size exactly) |
| `tony-edit1-palette.prg` | **56,365** | + EMBER color scheme as default |
| `tony-edit2-sprites.prg` | **56,365** | + Golem Tony sprite redesign |
| `tony-edit3-level.prg` | **56,480** | + title-screen text & new room-18 platform |

## Edit 1 — EMBER, a 7th color scheme, set as default

My own palette: playfield paper **ORANGE (8)**, ink/border/sprite-plate
**BLUE (6)** (complementary contrast), dashboard highlights **YELLOW (7)**,
dimmed **LIGHT_RED (10)**. Joystick-UP on the title still cycles all 7 schemes
(EMBER → CLASSIC → AMBER → … → C128 → EMBER).

Files touched:
- `src/kickass/_constants.asm` — 4 new `SCHEME_EMBER_*` labels;
  `MAX_COLOR_SCHEME` 6→7; new `DEFAULT_COLOR_SCHEME = 6`.
- `src/kickass/tony.asm` — appended EMBER to the four 6→7-entry tables
  (`colorLights/Darks/Bright/Dimmed`, tony.asm:3568); boot default `ldx #0` →
  `ldx #DEFAULT_COLOR_SCHEME` (init, :92); static scheme-0 references switched
  to EMBER: copper-list dashboard entry (:55), `currentColor` (:3531),
  `fadeOut`/`fadeIn` ramps (:3542).

PRG effect: +4 bytes (table entries). 35,809 bytes differ vs baseline, almost
all from the 4-byte insertion relocating subsequent code/data addresses; the
functional changes are the operand at file offset 0xCB and the 4×1 new table
bytes.

## Edit 2 — protagonist redesign: "Golem Tony"

Same animation frame counts (walk 4, duck 4, idle 4, jump 2, ladder 2,
death 5+5), same 24×21 hardware sprite format, same 3-sprite player assembly
(top + bottom + Y-expanded backdrop). Visual redesign applied uniformly to all
26 frames: line-art hollows flood-filled into a solid body, the beret head
replaced by a **solid golem head with a battlement crown and a carved 2×2 eye**
(dark backdrop shows through the eye). The head is placed per frame by
template-matching the artist's original beret stamp (two pose variants +
mirrored variant for the left-facing death sheet; rear-view ladder frames get
a crowned rear head). All 7 `.bg.png` backdrop sheets regenerated as r=2
dilations of the new silhouettes.

Files touched (art sources; conversion to sprites happens in the build):
- `src/spritepad/tony chodzenie 4 klatki.png` + `.bg.png` (walk)
- `src/spritepad/tony kucanie 4 klatki.png` + `.bg.png` (duck)
- `src/spritepad/tony spoczynek 4klatki.png` + `.bg.png` (idle)
- `src/spritepad/tony skok 2 klatki.png` + `.bg.png` (jump)
- `src/spritepad/tony_drabina.png` + `.bg.png` (ladder)
- `src/spritepad/tony smierc lewo 5klatek.png` + `.bg.png` (death left)
- `src/spritepad/tony smierc prawo 5klatek.png` + `.bg.png` (death right)
- generator: `tools/restyle_tony.py` (idempotent, refuses already-restyled art)

PRG effect: size unchanged (sprite slots are fixed 64-byte records). 2,665
bytes differ vs edit 1, all inside the player sprite banks in the Movable
segment (file 0xBCF1–0xDADC region), i.e. pure art data.

## Edit 3 — background/level alterations (CTM patching)

Two changes, patched byte-in-place into the CharPad sources with
`tools/ctm_tool.py` (driver: `tools/edit3_level.py`):

- **Title screen** (`src/charpad/demo-level.ctm`, map block cells
  x161-184 / y2-5): "CLAUDE" written into the empty sky in 3×4-cell letters
  of char `$F1` (solid block → renders as bright solid letters on the
  negated playfield). 54 map cells changed.
- **Room 18, the first gameplay room** (`src/charpad/castle_map.ctm`, cells
  176-181 / y73 + chains at 177-178 / y74-75): a new **standable floating
  platform** (chars `$60 $61×4 $62`, material 1 = wall — real collision) with
  decorative hanging chain links, in the previously empty middle of the room.
  10 map cells changed.

PRG effect: +115 bytes (RLE-compressed room data for the two rooms grew, and
their per-room used-chars decode lists gained entries). 3 diff regions:
room-data area near file 0x0000FA (room 18 + title room are stored early),
the used-chars tables, and everything after shifted by the insertion.

## Screenshots (`deliverables/screenshots/`)

Captured with `tools/c64shot.py` (headless VICE x64sc, driven through the
binary monitor with joystick I/O simulation):

- `baseline-title.png` vs `modded-title.png` — grey CLASSIC scheme + plain sky
  vs EMBER orange/blue + "CLAUDE" lettering (golem stands on the U).
- `baseline-game.png` vs `modded-game.png` — room 18: original capped Tony &
  empty middle vs crowned golem + new chained platform.
- `*-game2.png` — same scene a few seconds later (enemy/effect animation).

Reproduce: `python3 tools/c64shot.py deliverables/prg/c64-roms-required/tony-edit3-level.prg out modded`
(defaults need `x64sc`, C64 ROMs, `xvfb-run`; see tools/c64shot.py docstring).
