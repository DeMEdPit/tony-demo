# Write-up: an agent as pixel artist in the Tony codebase

## What was easy

- **The build.** The pinned-deps recipe worked first try; `tony.prg` came out
  at exactly the expected 56,361 bytes. The retro-assembler plugin's build is
  fast (~30 s cold, ~7 s warm), which made "edit → build → diff the PRG" a
  tight loop. `build.gradle.kts` doubles as complete, accurate documentation
  of every asset conversion — the single most valuable file in the repo.
- **The palette edit.** The color-scheme system is clean table-driven data
  (`_constants.asm` + four tables in `tony.asm`). The only trap — four static
  initializers hardcoding scheme 0 (copper list entry, `currentColor`, the two
  fade ramps) — is easy to find by grepping `SCHEME_`.
- **Reading binary formats with the parser's own source.** Cloning the exact
  plugin version (1.7.6) and reading its Kotlin processors turned CTM/PNG
  conversion from guesswork into specification: CTM block layouts, the
  "alpha is ignored, RGB black = background" sprite rule, `extend` anchoring
  top-left, row-major `split` ordering. Every format assumption I later relied
  on was verified against code, then against bytes (my CTM parser had to parse
  all 11 shipped files to exact end-of-file before I trusted it).

## What was hard

- **Implicit art conventions.** The player sheets only work because of
  unwritten rules: art must stay in the left 24 px of each 32-px frame (the
  right sprite column is discarded); the artist stamps an identical head
  bitmap onto every frame (two pose variants); left-facing walk frames are
  build-generated mirrors with a 7-px realignment, but death-left is separate
  hand-mirrored art. None of this is documented — it fell out of diffing
  frames and reading the gradle image pipelines.
- **Redesigning 26 frames coherently.** Hand-pixeling every frame would be
  slow and inconsistent, so the redesign is a *program* (`restyle_tony.py`):
  flood-fill + template-match the head anchor + stamp the new head. Getting a
  transformation that survives duck crouches, the sinking death sequence and
  the rear-view ladder took several preview iterations. ASCII-art previews
  (1 char = 1 px) were essential — as an agent I can "see" those precisely.
- **Emulator automation.** The game never touches the KERNAL, so VICE's
  keyboard-buffer tricks don't reach it. The working path: attach the
  "Joyport I/O simulation" device and drive its lines over the binary monitor
  protocol. Three landmines cost real time: the joyport command id differs
  from older docs (0xa2 — read the source), the lines are active-low (idle =
  0x1F), and every monitor command leaves the machine paused until an
  explicit EXIT (0xaa) — which silently made all input no-ops. Plus a classic:
  `terminate()` on `xvfb-run` orphans the emulator, and the next session
  connects to the stale instance's monitor port — screenshots lie unless the
  process group is killed and the port guarded.
- **Small traps.** The plugin's PNG reader crashes on 3-channel RGB files
  (palette or RGBA only); running an art transform twice double-stamps
  (fixed with an idempotency guard); Ubuntu's VICE looks for revision-named
  ROMs (`kernal-901227-03.bin`) that the package doesn't ship.

## What tooling makes an agent effective here

Built during this project (all in `tools/`):

- `ctm_tool.py` — CharPad CTM v8/v9 inspect/export/patch (byte-in-place).
  This is the difference between "can't touch levels without CharPad on
  Windows" and one-line map edits.
- `sprite_tool.py` — PNG sheet ↔ ASCII ↔ C64 sprite bins, plus overlay
  generation by dilation. The ASCII round-trip is the agent's paintbrush.
- `restyle_tony.py` — the sprite redesign as a reviewable, idempotent program.
- `c64shot.py` — headless VICE driver (boot PRG, inject joystick, PNG
  screenshots). Closes the loop: the agent can *play-test* its own builds.

What I'd add next for a production workflow:

1. **A room compiler**: text/JSON room description → CTM map patch + object
   list in `data.asm`, with material-aware validation (is the platform
   reachable? does a killing char sit under a spawn?).
2. **A palette previewer** rendering any scheme over exported screens without
   a build (the negated-charset double inversion makes colors easy to reason
   about incorrectly).
3. **Frame-consistency lint** for sprite sheets: verify head-stamp alignment,
   bounding boxes within the visible 24 px, and bg-overlay coverage — the
   things the pipeline silently truncates.
4. **A scripted gameplay harness** on top of `c64shot.py` (assert "player can
   reach cell X,Y") — input recording plus memory peeks of `physPlayerX/Y`
   would make level edits regression-testable.

## Honest assessment

The codebase is exceptionally moddable for a C64 game: modern build, assets in
editable source formats, data-driven color/level/object systems. The friction
is entirely in *unwritten conventions* and *toolchain blind spots*, both of
which an agent can neutralize by reading the toolchain's source and building
small verifiers. Total: 3 modified PRGs, all booting and play-verified in VICE,
with pixel-exact evidence at every stage.
