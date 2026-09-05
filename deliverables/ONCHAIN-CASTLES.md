# Mini castles as byte patches over the on-chain Tony PRG

The Tony demo that the Ethereum PoC721 token serves (`prg()`, keccak256
`0x5bcd208f63ac255ffc391c4abeb7b8f701061ac896008607ef414c24c880f34d`) is the
30-room game with two boot-time changes (menu skipped, GREEN scheme). Because
the level is data — exit bytes, object lists, RLE3 room blocks at fixed
addresses — a "castle" is a **48–58-byte patch** over those exact bytes: rewire
a handful of exits, set the scheme byte, and (optionally) rewrite one room
block. No reassembly. A collection contract can hold the base PRG once
(or read it from the token) and a few dozen bytes per token, apply them in
memory, and hand the result to the READY 64 Launcher's `dataURI(prg, 0)`.

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
of every room), `tools/m64-harness` (native build of the vendored, chain-proven
minimal64 source; now with `poke` and `dump`).

## Two findings about the deployed bytes (measured, not inferred)

**1. The cheat byte is uninitialised on ROM-equipped machines.** The skipped
menu was the only code that ever wrote `gameCheatState` (zero page `$2D`).
On minimal64 RAM starts zeroed, so the on-chain page is clean (`$2D = $00`,
measured at the title and in play). On a real C64 or VICE, after `LOAD`, `$2D`
holds BASIC's end-of-program pointer: measured **`$2D = $28`** with the exact
on-chain bytes autostarted in VICE — that is `CHEAT_PIKES_INVINCIBLE` (`$20`)
+ `CHEAT_PASS_THRU_DOORS` (`$08`) silently ON. The game runs, but it is not the
same game (pike-proof Tony who walks through locked doors). Fix, 10 bytes,
included in every castle patch: `$08F8: 20 62 B4` (`jsr $B462` instead of
`jsr blankScreen`) and `$B462: A9 nn 85 2D 4C E1 2B` (`lda #nn; sta $2D;
jmp blankScreen`) — the stub lives in the dead menu's own entry point, which
is still in the load image and runs before unpack. Verified: VICE `$2D = $00`,
minimal64 `$2D = $00`, game boots and plays identically
(`screenshots/onchain-cheatclear-vice-title.png`). The same byte doubles as a
trait: `nn = $04` bakes infinite lives (the Escher castle; measured `$04` on
both machines).

**2. Room 11 declares a south exit to room 16 that cannot fire** — its bottom
two rows are solid wall and no object opens them. Harmless vestigial data;
noted because a socket census must not count it as a door.

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
| dead `cheatMenu` entry (stub home) | `$B462` | `0x0AC63` | 7 |
| `materials` — collision class per char (bit0 wall, bit1 ladder, bit2 deadly, bit6 collectible) | `$8DC7` | `0x085C8` | 255 |
| `level_roomPtr` lo[30] hi[30] → each room's RLE3 map block | `$9446` | `0x08C47` | 60 |
| `level_objectControlPtr` / `PositionXPtr` / `PositionYPtr` lo/hi | `$9554` / `$9590` / `$95CC` | `0x08D55` … | 3×60 |
| `level_objectSizes[30]` | `$9644` | `0x08E45` | 30 |
| bat paths `path0..9`, `pathsPtrsLo/Hi`, `pathLengths` | `$9680` | `0x08E81` | 102 |

Per-room: each room's compressed map block (address + length) and object
list (address + count, control byte = type + value<<4, then X and Y arrays)
are printed by `python3 tools/onchain_castle.py info PRG`. Object records are
uncompressed and patchable in place (same count); the map blocks are RLE3
(`_compress.asm`: literal runs, `FF value count` for runs, `FF FF 00` end mark)
and the tool's encoder reproduces all 30 on-chain blocks byte-exactly, so a
room can be rewritten as long as the new block is **not larger** (the decoder
stops at the end mark; leftover bytes are inert). Walls usually compress
smaller. The four exit tables, the pointer tables and the start block are
plain bytes.

Runtime facts that shape the rules (all measured on minimal64 with pokes into
the running game): an exit set to `NO` (`$FF`) is an invisible wall for
sideways travel — Tony walks to X=327 and stops, exactly as the shipped room
18 east edge behaves; the title's fire handler simply walks Tony left off the
platform at floor row 6, so `exitsW[29]` is the whole gate; a **bottom
opening with a sealed south exit is not safe** — the collision scan has row
addresses only for rows 0–19 and Tony comes to rest at Y=214, out of bounds
under the dashboard, alive; the only room-number-specific engine logic is
`cmp #29` (title) and `cmp #22/#23` (stones charset), so remixing leaves them
intact because room numbers never change.

### No castle name string

The deployed game draws no text at runtime — the title is tile art, the
dashboard is glyphs — and the menu strings (`"tony born for adventure"`,
`"official trainer"`, …) are dead bytes now that the menu is skipped:
patchable, invisible. A castle's name belongs in the token metadata, not the
PRG. (A code patch could print one; that is a different project.)

## What a castle patch is

1. **Gate**: `exitsW[29] = entry room`. Tony leaves the title on floor row 6
   and arrives at the entry room's east edge, X=321, Y=70.
2. **Wiring**: exit bytes of the castle rooms. A castle is closed: every
   direction the spec does not wire is sealed (`$FF`); a wired target must be
   another castle room (the generator refuses leaks into the rest of the demo).
3. **Vertical rule**: a room's bottom opening is either wired to a safe drop or
   walled off; a top-edge ladder likewise (a ladder into a sealed sky is
   untested territory). The generator plugs unwired openings automatically by
   rewriting the room block (same-or-smaller RLE3, e.g. room 8: 532 → 529 B).
4. **Scheme byte** and the **cheat stub** (clear, or a trait value).
5. Optional object edits (type/value in place) and wall edits.

Sockets are computed from the engine's **runtime** collision map, not the
static tiles: `capture_runtime_rooms.py` forces each room transition in the
running game and reads `roomMaterialsBuffer` (`$BE00`) through the live screen
rows in `chamberLines` (`$4290`). The difference matters: flame objects are
marked deadly at runtime with no cheat exemption (room 8 gains exactly 8
deadly cells, one column two rows per flame pair; room 24 twelve), doors
become blocking, pikes deadly. A door is "safe" when Tony, stepping through
at his current floor row, finds his body zone open and either stands on a
wall or drops through safe cells onto one; an edge is "side-safe" when every
standable spot on it arrives safely opposite. Under those rules the 29 rooms
offer 15 entry-capable rooms, 234 safe one-way doors, 165 safe drops, 9
non-neighbour eastward rings and one perfect self-loop room (2). The original
author's own 23 doors pass the same test in 19 cases; the four exceptions are
shipped one-way quirks.

## The three sample castles (`deliverables/onchain/castles/`)

Each has its patched PRG (56,361 bytes), a JSON with the exact records and the
`hex` patch string, and was play-tested on minimal64 by `verify_castle.py`:
boot, fire at the title, then every wired door walked through (Tony placed on
the edge floor with the physics actor variables, joystick through the emulated
CIA), every drop taken, the cheat byte read. Screenshots:
`screenshots/onchain-castle-*.png`.

**The Ring** — AMBER, 48 bytes. Title → room 27 (the flame-lit hall with the
door); walk east into room 16 (snakes, potion, jewel); walk east again and you
are back in 27 — forever. Rooms 27 and 16 are not neighbours in the castle.
West edges sealed. `3/3` checks passed.

```
$9553 12→1b  gate → 27        $950A 11→1b  16.E → 27      $9546 0f→ff  16.W sealed
$9515 1c→10  27.E → 16        $9551 1a→ff  27.W sealed    $0965 02→01  AMBER
$08F8 20e12b→2062b4  jsr stub $B462 a99b8d11d0a908→a900852d4ce12b  stub, cheats clear
```

**The Well** — BLUE, 58 bytes. Title → room 8 (skull pillars); climb down the
centre ladder and fall into room 24 (the keycode hall, six flames) — a
non-neighbour, four grid rows away; walk east into room 9, and back. Room 8's
other exits sealed, 9's north and east sealed. `4/4` checks passed (drop
through column 25 lands on 24's floor at Y=102).

```
$9553 12→08  gate → 8         $9520 0d→18  8.S → 24       $953E 07→ff  8.W sealed
$953F ff→18  9.W → 24         $94E5 04→ff  9.N sealed     $9503 0a→ff  9.E sealed
$9512 19→09  24.E → 9         $0965 02→03  BLUE           $08F8 / $B462 stub, cheats clear
```

**The Escher Corridor** — C64 scheme, 48 bytes, **infinite lives** baked
(`$2D = $04`, measured on minimal64 and in VICE). Title → room 26 (four
vertical bats); walk east into room 2 — whose east edge is its own west edge.
Walk either way forever. `4/4` checks passed (east wrap lands Tony at X=104
after re-entry, west wrap at X=241).

```
$9553 12→1a  gate → 26        $9514 1b→02  26.E → 2       $9550 19→ff  26.W sealed
$94FC 03→02  2.E → 2          $9538 01→02  2.W → 2        $0965 02→04  C64
$08F8 20e12b→2062b4  jsr stub $B462 a99b8d11d0a908→a904852d4ce12b  stub, lives
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
today (~64M view gas including hex+base64), so per-castle cost is that plus a
few hundred byte writes. Per-token storage: 48–58 bytes for exits+scheme+stub,
plus ~530 bytes when a room block is rewritten.

## Not done / open

- Object-level traits (swap a snake for a skull, move a jewel) and
  hand-drawn wall edits are supported by the generator (`objects`, `walls` in a
  spec) but no sample uses them; a north-edge ladder into a sealed exit is
  walled off rather than tested.
- The census treats a standable edge spot as reachable; it does not path-find
  inside rooms, so a wired door can be behind an enemy or a locked door — the
  verifier teleports past that, a player would not. Curation still wants a
  human eye on each castle.
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
