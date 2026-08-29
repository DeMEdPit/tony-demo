# The Idol Vault — a custom single-screen board

**`deliverables/prg/tony-vault.prg` — 37,732 bytes, load address `$0801`
(`SYS 2240`).** A standalone build containing exactly ONE sealed room and the
full game engine: original-look Tony, classic grey scheme, the regular music,
physics, animation, score/lives dashboard. There is no title screen and no
other rooms — the game boots straight into the vault, all four exits are
sealed, and game over loops back into the vault. The other 29 rooms are not
in the binary (hence ~19 KB smaller than the full game).

Run it: `x64sc tony-vault.prg` (or any C64 emulator / real hardware). At the
boot cheat menu press RETURN (or joystick fire) to skip. Joystick in port 2:
left/right walk, up climbs ladders, fire jumps, fire+direction jumps sideways.

## The room

A treasure vault built around a solid stone idol on a pillar-mounted dais.
The pillar splits the floor in two zones, and the idol splits the dais in two
wings — so the room plays as two mirrored challenges:

- **Right wing** (you spawn here): dodge the pacing deadman, climb the right
  ladder, jump left from the top onto the dais — landing between the dais
  flame and the idol — to take the **potion** (and the right platform jewel
  on the way).
- **Left wing**: the left ladder rises beside a pike trap, a snake guards the
  floor, and a skull bobs exactly in the drop lane to the dais — time it to
  reach the left jewel sitting a step away from the flame.
- A bat sweeps the upper vault on a gliding path; chains and vines hang from
  the ceiling; candelabra glow high on the walls. Two more jewels sit on the
  side platforms. Carrying the potion lets you survive one enemy touch.

## How it's made (all committed)

| piece | file |
|---|---|
| room map generator (layout as code, 105 tiles used) | `tools/build_custom_room.py` |
| generated 40×20 map | `src/level-custom/custom-room.bin` |
| one-room level data: sealed exits, object/enemy list, bat path | `src/kickass/level/custom/data.asm` |
| standalone game variant (boots straight into the room) | `src/kickass/tony-room.asm` |
| build wiring (new include + libDir) | `build.gradle.kts` |
| room preview render | `deliverables/assets/custom-room-preview.png` |
| play-test screenshots | `deliverables/screenshots/vault-*.png` |

`tony-room.asm` differs from `tony.asm` in exactly four ways: output file
name, the level import (`level/custom/data.asm`), both `jsr startTitle` call
sites replaced with `startRoomDirect` (startGame without the title font
exchange), and that new 12-line subroutine. The full game (`tony.prg`) still
builds unchanged alongside it.

The room was tuned by *playing it*: `tools/c64shot.py` drives VICE through
the binary monitor with joystick injection and now also reads the sprite
registers for position feedback (`gox`/`goy`/`wsp` script steps) — the
scripted run climbs the ladder, jumps onto the dais and collects the potion
(see `vault-6-potion.png`: potion in inventory, score 100). Play-testing
caught one real bug pre-ship: the deadman's patrol originally swept the spawn
point.
