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

---

## Findings register (measured facts, engine and hardware)

- Exit bytes are the whole castle topology; no grid in the engine (E8).
- Any sprite-to-sprite touch counts as a player hit (E4, E10).
- Sprite colours are repainted in the top-of-frame IRQ (E5).
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
