# Mini castles as byte patches over the on-chain Tony PRG

The Tony demo that the Ethereum PoC721 token serves (`prg()`, keccak256
`0x5bcd208f63ac255ffc391c4abeb7b8f701061ac896008607ef414c24c880f34d`) is the
30-room game with two boot-time changes (menu skipped, GREEN scheme). Because
the level is data — exit bytes, object lists, RLE3 room blocks at fixed
addresses — a "castle" is a small patch over those exact bytes: rewire a
handful of exits, set the scheme byte, fix the cheat-state byte, install a
108-byte **edge guard** (see the field report: the engine has no behaviour for
a sealed exit), and only where a floor hole would lead nowhere in "wall" mode,
rewrite one room block. **167–192 bytes for the three samples**, no
reassembly. A
collection contract can hold the base PRG once (or read it from the token),
apply the bytes in memory, and hand the result to the READY 64 Launcher's
`dataURI(prg, 0)`.

Everything below is derived from and verified against the deployed bytes:
`deliverables/onchain/tony-token-edition.prg` here is byte-identical to the
mainnet `prg()` (its keccak256 equals the token's `prgHash`), and every
address comes from a KickAssembler symbol file of a **byte-identical**
rebuild of upstream `75f62f5b` (`tony-token-edition.sym`; the plugin's
`:version=`/`:variant=e` command-line values are needed to reproduce the
hash — without them the menu text differs by 9 bytes). The two deployed
patches live at `$08F8` (3-byte `jsr cheatMenu` deleted) and `$0964`
(`ldx #0` → `ldx #2` plus a 3-byte `sta fadeIn`); everything after `$0971`
equals upstream, so all table offsets are shared with the pristine build.

Tools: `tools/onchain_castle.py` (offset map, census, patch generator — it
refuses any input whose keccak256 is not the on-chain `prgHash`),
`tools/verify_castle.py` (play-tests a castle on minimal64),
`tools/capture_runtime_rooms.py` (dumps the engine's runtime collision map
of every room), `tools/castle_diagram.py` (renders
`assets/onchain-castles-diagram.png` from the castle JSONs), `tools/m64-harness`
(native build of the vendored, chain-proven minimal64 source; with `poke` and
`dump`).

## Field report — what the first play-test found, and what it changed

The first three sample castles (superseded; their files are replaced) were
played by the owner through READY 64 in OpenSea. Report: after fire at the
title you can walk left, then "when I try and leave either room … you die",
and "if I go forward and hop over the door and keep going, I also lose a
life". Reproduced on minimal64 with the exact v1 Ring PRG: holding LEFT from
the entry, lives went 5 → 4 → 3 → 1 in about 500 frames while the room number
never changed (`screenshots/onchain-castle-v1-bug-room27-spikes.png`). Two
independent causes:

**1. A sealed exit is not a wall — the engine has no behaviour for it.**
`changeRoomIfNeeded` skips a room change when `roomChange == $FF`, and that
is all. `checkForRoomChange` keeps firing every frame, Tony keeps walking, his
16-bit X runs past the playfield and through zero, the collision scan indexes
columns that do not exist and reads whatever bytes lie there, and the east
test (`physPlayerX+1 != 0`) can even fire a phantom transition through the
*opposite* exit. Depending on the room this is a death, a teleport or a walk
into nothing. My earlier note that a sealed exit "is an invisible wall" was
measured **eastward only** (room 18, where the garbage column past the right
edge happens to read as wall) and generalised wrongly — westward is where it
breaks. Fix: the **edge guard** below, so a sealed exit has one defined,
selectable behaviour.

**2. Room 27 is a spike bed with a platform, not a front door.** Tony arrives
at a castle's entry room on its east edge, facing west (that is how the title
gate works in the shipped game). Room 27 offers eleven columns of platform in
that direction and then a fall onto a floor-wide spike bed. Fix: entries are
now chosen by a **front-door rule** (below); the on-chain demo's own first
room, 18, is the model.

**3. (second play-test) A wall cap on a ladder traps Tony at the top.** My
first fix also "capped" ladders that used to lead into a now-sealed room by
turning their top two cells into wall. The owner climbed room 11's ladder,
was stopped at the top and could then only crouch — not climb down. Measured
with the same probe on three PRGs (stand at the ladder foot, hold UP, hold
DOWN): capped ladder — Tony reaches Y=38 and his state flips from *on ladder*
(`$07`) to *standing* (`$00`); DOWN then does nothing. Guard only, no cap —
he is held at Y=36–37 still in the climbing state and DOWN brings him back to
the platform (Y=86). Shipped game — he climbs into room 6. So the cap is
gone: sky ladders are left to the guard, whose top-edge case is now always a
wall (never void — a ladder that kills at its last rung is a hazard nobody can
see). Room 25's ladder hangs from the top edge over open space; it was only
ever an entrance from the room above and cannot be grabbed from below
(measured), so there is nothing to get stuck on.

**4. (second play-test) A void on the door you came through is a death
loop.** The Escher's entry room had its east edge — the edge the title gate
delivers Tony to — sealed in void mode. Walking back into it: the void takes a
life, the engine respawns Tony *where he entered the room* (that same edge),
in the *state* he entered with (walking — the shipped respawn behaviour, which
is why "he keeps walking when I'm not"), the death hop plays, and any
rightward input kills him again. Fix, in the guard: **never void into the
edge Tony would respawn on** — the side is read from the high byte of
`playerRespawnPositionX` (east half when X ≥ 256), so a room entered from the
east has a wall on its east edge and a void on its west, and vice versa; a
drop-in room takes its landing spot as the reference. In void mode open floor
holes are now left open — a pit *is* the void (fall, lose a life, respawn) —
while wall mode still fills them. Verified both ways on every sealed edge
(respawn far side → one life lost; respawn same side → wall).

Two more facts surfaced while fixing it:

- `$0801–$080C` is the BASIC program (`0B 08 | 0A 00 | 9E "2240" | 00 | 00 00`):
  line link, line number, SYS token, argument, end-of-line, end-of-program
  link. Every byte is parsed by `RUN` on a real C64 and by minimal64's PRG
  injector. My first guard started at `$080A` and none of the castles booted;
  the free padding starts at **`$080D`** (179 zero bytes to `$08BF`, and a
  linear disassembly of `$08C0–$449A` finds no instruction that references
  the area).
- Snakes ignore every cheat. They are *static* objects (`handleSnake`, which
  carries the author's own comment `// TODO add cheat mode here!`) and kill
  through the object-collision path, so the deployed game's "resistant to
  nasties" bit (`$10`) does not cover them. Relevant to any trainer semantics
  and to automated testing.

## Findings about the deployed bytes (measured, not inferred)

**1. The cheat byte is uninitialised on ROM-equipped machines.** The skipped
menu was the only code that ever wrote `gameCheatState` (zero page `$2D`).
On minimal64 RAM starts zeroed, so the on-chain page is clean (`$2D = $00`,
measured at the title and in play). On a real C64 or VICE, after `LOAD`, `$2D`
holds BASIC's end-of-program pointer: measured **`$2D = $28`** with the exact
on-chain bytes autostarted in VICE — that is `CHEAT_PIKES_INVINCIBLE` (`$20`)
+ `CHEAT_PASS_THRU_DOORS` (`$08`) silently ON. The game runs, but it is not the
same game. Fix, 10 bytes, included in every castle patch: `$08F8: 20 62 B4`
(`jsr $B462` instead of `jsr blankScreen`) and `$B462: A9 nn 85 2D 4C E1 2B`
(`lda #nn; sta $2D; jmp blankScreen`) — the stub lives in the dead menu's own
entry point, which is still in the load image and runs before unpack.
Verified: VICE `$2D = $00`, minimal64 `$2D = $00`
(`screenshots/onchain-cheatclear-vice-title.png`). The same byte doubles as a
trait: `nn = $04` bakes infinite lives (the Escher castle).

**2. Room 11 declares a south exit to room 16 that cannot fire** — its bottom
two rows are solid wall and no object opens them. Harmless vestigial data;
noted because a socket census must not count it as a door.

**3. Sealed exits have no behaviour** (field report above).

## The patch map

`file offset = address − $0801 + 2` (PRG starts with the 2-byte load address).

| target | address | file offset | size |
|---|---|---|---|
| **title gate** = `level_roomExitsW[29]` (the room fire-at-title walks into) | `$9553` | `0x08D54` | 1 |
| `level_roomExitsN[0..29]` | `$94DC` | `0x08CDD` | 30 |
| `level_roomExitsE[0..29]` | `$94FA` | `0x08CFB` | 30 |
| `level_roomExitsS[0..29]` | `$9518` | `0x08D19` | 30 |
| `level_roomExitsW[0..29]` | `$9536` | `0x08D37` | 30 |
| `level_startRoom` (29), `startPositionX` (word 170), `startPositionY` (70), `startState` | `$449A` | `0x03C9B` | 5 |
| boot colour scheme operand (`ldx #n`, 0 CLASSIC 1 AMBER 2 GREEN 3 BLUE 4 C64 5 C128) | `$0965` | `0x00166` | 1 |
| boot `jsr blankScreen` (→ cheat stub) | `$08F8` | `0x000F9` | 3 |
| dead `cheatMenu` entry (cheat stub home, runs pre-unpack only) | `$B462` | `0x0AC63` | 7 |
| **edge guard home**: zero padding after the BASIC program (`$080D–$08BF`, 179 B free) | `$080D` | `0x0000E` | 108 |
| `checkForRoomChange` tail `sta roomChange; rts` → `jmp $080D` | `$14E8` | `0x00CE9` | 3 |
| `materials` — collision class per char (bit0 wall, bit1 ladder, bit2 deadly, bit6 collectible) | `$8DC7` | `0x085C8` | 255 |
| `level_roomPtr` lo[30] hi[30] → each room's RLE3 map block | `$9446` | `0x08C47` | 60 |
| `level_objectControlPtr` / `PositionXPtr` / `PositionYPtr` lo/hi | `$9554` / `$9590` / `$95CC` | `0x08D55` … | 3×60 |
| `level_objectSizes[30]` | `$9644` | `0x08E45` | 30 |
| bat paths `path0..9`, `pathsPtrsLo/Hi`, `pathLengths` | `$9680` | `0x08E81` | 102 |

Do not touch `$0801–$080C` (the BASIC line, see the field report). Runtime
variables the guard uses (RAM, not in the file): `roomChange $3E55`,
`roomChangeDirection $3E59`, `physPlayerX $39CC/CD`, `physPlayerY $39CE`,
`playerDying $42C9`, `playerRespawnPositionX $42C5/C6`, `gameLivesLeft $42CA`,
`currentChamberNumber $3E51`;
routines `physResetActorPosition $3662`, `updatePlayerPosition $2A0D`,
`killPlayer $0E64`.

Per-room: each room's compressed map block (address + length) and object
list (address + count, control byte = type + value<<4, then X and Y arrays)
are printed by `python3 tools/onchain_castle.py info PRG`. Object records are
uncompressed and patchable in place (same count); the map blocks are RLE3
(`_compress.asm`: literal runs, `FF value count` for runs, `FF FF 00` end mark)
and the tool's encoder reproduces all 30 on-chain blocks byte-exactly, so a
room can be rewritten as long as the new block is **not larger** (the decoder
stops at the end mark; leftover bytes are inert). The four exit tables, the
pointer tables and the start block are plain bytes.

Runtime facts that shape the rules (measured on minimal64): the title's fire
handler simply walks Tony left off the platform at floor row 6, so
`exitsW[29]` is the whole gate and Tony arrives at the entry room's **east**
edge at X=321, Y=70, facing west; a **bottom opening with a sealed south
exit** drops Tony out of bounds under the dashboard (the collision scan has
row addresses only for rows 0–19) — so it is walled off; the only
room-number-specific engine logic is `cmp #29` (title) and `cmp #22/#23`
(stones charset), so remixing leaves them intact because room numbers never
change.

### No castle name string

The deployed game draws no text at runtime — the title is tile art, the
dashboard is glyphs — and the menu strings are dead bytes now that the menu is
skipped: patchable, invisible. A castle's name belongs in the token metadata,
not the PRG.

## What a castle patch is

1. **Gate**: `exitsW[29] = entry room`.
2. **Wiring**: exit bytes of the castle rooms. A castle is closed: every
   direction the spec does not wire is sealed (`$FF`); a wired target must be
   another castle room (the generator refuses leaks into the rest of the demo).
3. **Vertical rule**: a room's bottom opening is either wired to a safe drop,
   or — in wall mode — filled with wall (the generator rewrites the room
   block, same-or-smaller RLE3; the guard would otherwise hold Tony falling in
   the hole forever), or — in void mode — left open as a pit that costs a
   life. A ladder into a sealed sky is **not** touched: the guard holds Tony
   at its top in the climbing state and he can climb back down (a wall cap
   traps him — field report, item 3).
4. **Scheme byte** and the **cheat stub** (clear, or a trait value).
5. **Edge guard** with its **mode byte** (next section) — installed in every
   castle, 108 B at `$080D` plus the 3-byte re-route at `$14E8`.
6. Optional object edits (type/value in place) and wall edits.

Sockets are computed from the engine's **runtime** collision map, not the
static tiles: `capture_runtime_rooms.py` forces each room transition in the
running game and reads `roomMaterialsBuffer` (`$BE00`) through the live screen
rows in `chamberLines` (`$4290`). Flame objects are deadly at runtime with no
cheat exemption, doors block, pikes kill. A door is "safe" when Tony, stepping
through at his current floor row, finds his body zone open and either stands
on a wall or drops through safe cells onto one; an edge is "side-safe" when
every standable spot on it arrives safely opposite. Under those rules the 29
rooms offer 15 entry-capable rooms, 234 safe one-way doors, 165 safe drops and
one perfect self-loop room (2). The original author's own 23 doors pass the
same test in 19 cases; the four exceptions are shipped one-way quirks.

## Edge modes — the guard, and the "infinite / wall / void" variable

The guard replaces the tail of `checkForRoomChange`. Entered with the exit
byte in A and `roomChangeDirection` set, it stores the byte like the original
did and returns if the exit is real. If the exit is sealed (`$FF`) it pushes
Tony back inside on the side he tried to leave (X to 21 or 320, Y to 37 or
195 — two pixels inside the transit limits), re-syncs the actor position the
way `changeRoomIfNeeded` does, and then — for the west, east and south edges —
consults its **mode byte** (`$0855` = guard + 72). Two cases are a wall in
every mode: the **top edge** (the only way up there is a ladder, and Tony is
simply held on its top rung) and **the side edge Tony would respawn on**
(field report, item 4).

| mode | byte | what a sealed edge does | verified |
|---|---|---|---|
| **wall** | `$00` | invisible wall: Tony stays in the room, in bounds, alive (walks in place against it); floor holes are filled | Escher: sealed entry edge `same room, in bounds, 5 lives`; ladder top: held, climbs back down |
| **void** | `$01` | the far edges and open pits cost one life — `killPlayer` once, never while already dying — and Tony respawns where he entered the room; the top edge and the edge he would respawn on stay walls | Well: rooms 5 (west) and 24 (east): respawn far side → `exactly one life lost, same room`; respawn same side → `in bounds, 5 lives`; entry room's own edge → wall |
| **infinite** | (either) | not a byte but a topology: every open side edge is wired somewhere, so the guard only ever fires at the top of a sky ladder | Ring: six doors, no sealed side edge; ladder top: held, climbs back down |

108 bytes, assembled by `edge_stub()` in the generator (a two-pass mini
assembler, so branch offsets are never hand-counted); listing generated from
the assembled bytes:

```
080D 8d 55 3e     sta roomChange
0810 c9 ff        cmp #$FF (sealed)
0812 d0 64        bne $0878
0814 ad 59 3e     lda roomChangeDirection
0817 c9 04        cmp #$04 (WEST)
0819 d0 0d        bne $0828
081B a9 15        lda #$15 (WEST_LIMIT+2)
081D 8d cc 39     sta physPlayerX
0820 a9 00        lda #$00 (0)
0822 8d cd 39     sta physPlayerX+1
0825 4c 4e 08     jmp $084E
0828 c9 03     <- cmp #$03 (EAST)
082A d0 0d        bne $0839
082C a9 40        lda #$40 (<(EAST_LIMIT-2))
082E 8d cc 39     sta physPlayerX
0831 a9 01        lda #$01 (>(EAST_LIMIT-2))
0833 8d cd 39     sta physPlayerX+1
0836 4c 4e 08     jmp $084E
0839 c9 01     <- cmp #$01 (NORTH)
083B d0 0c        bne $0849
083D a9 25        lda #$25 (NORTH_LIMIT+2)
083F 8d ce 39     sta physPlayerY
0842 20 62 36     jsr physResetActorPosition
0845 20 0d 2a     jsr updatePlayerPosition
0848 60           rts            ; top edge: wall in every mode
0849 a9 c3     <- lda #$C3 (SOUTH_LIMIT-2)
084B 8d ce 39     sta physPlayerY
084E 20 62 36  <- jsr physResetActorPosition
0851 20 0d 2a     jsr updatePlayerPosition
0854 a9 00        lda #MODE  ($00 wall / $01 void)
0856 f0 20        beq $0878
0858 ad c9 42     lda playerDying
085B d0 1b        bne $0878
085D ad 59 3e     lda roomChangeDirection
0860 c9 03        cmp #$03 (EAST)
0862 d0 08        bne $086C
0864 ad c6 42     lda playerRespawnPositionX+1
0867 d0 0f        bne $0878
0869 4c 75 08     jmp $0875
086C c9 04     <- cmp #$04 (WEST)
086E d0 05        bne $0875
0870 ad c6 42     lda playerRespawnPositionX+1
0873 f0 03        beq $0878
0875 20 64 0e  <- jsr killPlayer
0878 60        <- rts
```

Why `$080D` is safe: the game never references `$0800–$08BF` (linear sweep of
the code segment), nothing is copied over it at unpack (music goes to
`$A000+`, screens to `$C000+`), and the bytes sit inside the PRG so a contract
can patch them like any other. The dead menu at `$B462` is **not** usable for
runtime code — `unpack` copies the music over it — which is why the cheat stub
there may only run at boot. The `guard` check in the play-tester re-reads the
guard bytes and the re-routed tail after a played session.

## Front doors — the gentle-entry rule

`entry_walk(room)` simulates what a new player does: arrive at the east edge
on floor row 6, drop to the first floor, hold LEFT. It returns how many
columns of continuous safe floor that walk covers and how it ends — `wall`
(he stops), `drop` (a fall onto safe floor), `door` (floor to the west edge),
`deadly` (a fall onto spikes) or `pit` (off the bottom). A room is a valid
**front door** when Tony can stand where he arrives, the run is at least six
columns, it does not end `deadly`/`pit`, and the room has no rolling boulders
(STONE objects hunt the whole floor). Of the 15 entry-capable rooms only
**11** (10 columns, then wall), **18** (8, then drop — the shipped first room)
and **19** (12, then drop, but six enemies) qualify; 27 is 11 columns then
`deadly`, 22 is 26 columns then `deadly` with boulders. The generator ranks
front doors by run length minus hazards parked on the run, and gives each
sample castle its own door when the data allows.

The play-tester turns the rule into a measurement (`entry` check): from the
gate it holds LEFT and samples X and lives every 8 frames until Tony has
covered the promised run; every sample must show all five lives and the entry
room. Sprite enemies are disabled for that one check (`$2D = $12`, pikes
stay live) so it measures the floor, not the fight — a snake on the run would
still fail it, legitimately, since snakes ignore cheats.

## The three sample castles (`deliverables/onchain/castles/`)

Each has its patched PRG (56,361 bytes), a JSON with the exact records and the
`hex` patch string, and was play-tested on minimal64 by `verify_castle.py`:
gate, entry walk, every wired door walked through (Tony placed on the edge
floor with the physics actor variables, joystick through the emulated CIA),
every drop taken, every sealed side edge walked into, every reachable sky
ladder climbed up and back down, guard bytes re-read. Screenshots: `screenshots/onchain-castle-*.png`;
map: `assets/onchain-castles-diagram.png`.

**The Ring** — AMBER, **infinite** topology, 192 B.
Title → room 11 (the jewel gallery; skull, bat, two pikes up high). West door
→ room 16 (two snakes, potion, jewel), west again → room 25 (vertical bats,
pikes), west again → 11. Eastward the same cycle in reverse: 11 → 25 → 16 →
11. Six doors, all six side-safe both ways; no room pair is neighbours in the
castle. Room 11's ladder into the sealed sky is held by the guard (climb up,
held, climb down — measured); room 25's hangs over open space and cannot be
reached. **10/10 checks passed** (one skipped: the unreachable ladder).

```
$9553 12→0b  gate → 11        $9541 0a→10  11.W → 16      $9505 0c→19  11.E → 25
$9546 0f→19  16.W → 25        $950A 11→0b  16.E → 11      $954F 18→0b  25.W → 11
$9513 1a→10  25.E → 16        $94E7/$9523  11.N, 11.S sealed   $94F5  25.N sealed
$0965 02→01  AMBER            $08F8/$B462  cheat stub, clear   $080D/$14E8  guard (wall)
```

**The Well** — BLUE, **void** mode, 167 B. Title → room 18, the shipped
game's own first room (snake on the stairs, bat, pikes far left). Its west door
→ room 5 (the deadman's hall); fall through the floor hole at column 2 into
room 24 (the keycode hall, six flames), a non-neighbour four grid rows away;
room 5's east door leads back to 18. The far edges are the void: step off
room 5's west edge or room 24's east edge and you lose a life and wake where
you entered that room. The edges you enter by (18's east, 5's east, 24's
landing side) are walls. **13/13 checks passed** (each void edge tested from
both respawn sides).

```
$9548 11→05  18.W → 5         $951D 0a→18  5.S → 24       $94FF 06→ff  5.E sealed
$953B 04→ff  5.W sealed       $9512 19→ff  24.E sealed    $0965 02→03  BLUE
$08F8/$B462  cheat stub, clear                            $080D/$14E8  guard (void)
```

**The Escher Corridor** — C64 scheme, **wall** mode, **infinite lives** baked
(`$2D = $04`), 177 B. Title → room 11; west door → room 2, whose east edge is
its own west edge: walk either way forever. Room 11's east edge — the door you
came in by — is an invisible wall; its sky ladder holds you at the top and
lets you climb down. **8/8 checks passed** (both wraps re-enter room 2 from
the far side).

```
$9553 12→0b  gate → 11        $9541 0a→02  11.W → 2       $94FC 03→02  2.E → 2
$9538 01→02  2.W → 2          $94E7/$9505/$9523  11.N, 11.E, 11.S sealed
$0965 02→04  C64              $08F8/$B462  cheat stub, lives  $080D/$14E8  guard (wall)
```

## Applying a patch in Solidity

Record encoding (the JSON `hex`): repeated `[offset u16 BE][len u16 BE][len
bytes]`, offset into the PRG counting the 2-byte load address. A castle
contract needs no copy of the game:

```solidity
bytes32 constant PRG_HASH = 0x5bcd208f63ac255ffc391c4abeb7b8f701061ac896008607ef414c24c880f34d;

function prgFor(uint256 id) public view returns (bytes memory prg) {
    prg = TONY.prg();                       // PoC721: 56,361 bytes from its 3 data blobs
    require(keccak256(prg) == PRG_HASH);    // patches are only meaningful over these bytes
    bytes memory p = patches[id];
    for (uint256 i; i < p.length; ) {
        uint256 off = (uint256(uint8(p[i])) << 8) | uint8(p[i + 1]);
        uint256 len = (uint256(uint8(p[i + 2])) << 8) | uint8(p[i + 3]);
        for (uint256 k; k < len; ++k) prg[off + k] = p[i + 4 + k];
        i += 4 + len;
    }
}
// tokenURI: animation_url = LAUNCHER.dataURI(prgFor(id), 0)
```

`TONY.prg()` is already the first half of what the token's own `tokenURI` does
today, so per-castle cost is that plus a few hundred byte writes. Storage: the
guard (108 B) and its tail re-route are identical for every castle except the
mode byte, so they can be one shared constant applied by the contract; the
per-token part is then exits + scheme + cheat + mode (a few dozen bytes) plus
~400–600 B only when a floor hole had to be filled in wall mode (none of the
three samples needs one).

## Not done / open

- Object-level traits (swap a snake for a skull, move a jewel) and hand-drawn
  wall edits are supported by the generator (`objects`, `walls` in a spec) but
  no sample uses them.
- The census treats a standable edge spot as reachable; it does not path-find
  inside rooms, so a wired door can be behind an enemy or a locked door — the
  verifier teleports past that, a player would not. The front-door rule covers
  the first steps only. Curation still wants a human eye on each castle.
- The earlier castles were replaced, not versioned: their PRGs and JSONs no
  longer exist here; the field report records what they were and what broke.
- Nothing here touches the chain: no contract was written or deployed, and the
  akalabeth repository was read only. These files live in `tony-demo`.

## Credits

Tony: Born for Adventure — code © 2023 Maciej Małecki, graphics © 2023 Rafał
Dudek, music © 2023 Sami Juntunen, all MIT (the four LICENSE files travel with
every PRG here). Runtime: minimal64 by nopsta, GPL-2.0
(github.com/nopsta/minimal64); nopsta stored the machine on Ethereum in 2022
and has since passed away — this work was made after he was gone and
independently of him. The harness in `tools/m64-harness` is built from the
vendored, chain-proven copy of his source.

## Reproduce

    python3 tools/onchain_castle.py info    deliverables/onchain/tony-token-edition.prg
    python3 tools/onchain_castle.py census  deliverables/onchain/tony-token-edition.prg
    python3 tools/onchain_castle.py samples deliverables/onchain/tony-token-edition.prg out/
    sh tools/m64-harness/build.sh /path/to/minimal64      # native harness
    python3 tools/capture_runtime_rooms.py                # runtime-collision.json
    python3 tools/verify_castle.py out/castle-the-ring.json shots/
    python3 tools/castle_diagram.py out/castle-the-ring.json out/castle-the-well.json out/castle-the-escher-corridor.json
