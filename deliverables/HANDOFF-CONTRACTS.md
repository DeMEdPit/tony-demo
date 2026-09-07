# Handoff: the Chamber collection, for the agent writing and deploying the contracts

Written 2026-09-06 from the `DeMEdPit/tony-demo` repository, branch
`claude/tony-c64-demo-expert-wp40it`. Everything below is either measured
in this repository (the tools named here reproduce it) or taken from the
owner's brief on what is already on mainnet. Where something is not yet
decided or not yet known, it says so. Read `EXPERIMENTS.md` for the history
and the reasons; this document is the operational summary.

## 1. Rules that apply to everything public

- **Wording about nopsta.** State plainly that nopsta stored the machine on
  Ethereum in 2022 and has since passed away, and that this work was made
  after he was gone and independently of him. Never describe the work as
  done on a dead man's machine or any wording of that shape. Put no year of
  death anywhere.
- **Credits in metadata.** Tony: Born for Adventure — code Maciej Małecki,
  graphics Rafał Dudek, music Sami Juntunen, all MIT (the four LICENSE files
  in this repository travel with every PRG). Runtime: minimal64 by nopsta,
  GPL-2.0 (github.com/nopsta/minimal64).
- **The music is the demo's own, unchanged in every note.** The level tune
  is the file the game ships; the intro tune was relocated to $8000 and is
  identical by an eight-minute register replay (section 4a). The Chamber
  reads the tune's state; it does not alter what either tune plays.
- **Keyless and immutable per token; fix-forward.** Once the base program
  is on chain it never changes. Anything found later is fixed in new tokens.
- **Gates before any mint.** The automated suite in this repository passes
  on the frozen base, and the owner has played every mechanic in READY 64.
- **Nothing here touches the chain** until the owner says so, with the
  owner's keys and gas.

## 2. What is already on mainnet (from the owner's brief)

| what | address | notes |
|---|---|---|
| minimal64 emulator, four data contracts (gunzip helper + three parts), on chain since 2022 | `0x1Cc49e603B4b205Be0E74f8833971Bea5beccEC9`, `0xEF13021d5302c3fCe437A3C281A286479ba60008`, `0x9A463234988C0F77ca1252Fc974DfD6b50AAA6Ba`, `0xf6Fb8cefFff7239d9689acDF1FBF5376C9996dA5` | anyone can EXTCODECOPY them |
| Tony: Born for Adventure token (PoC721, one token, keyless), deployed 2026-08-28 | `0xeBa8B68d17cAEaC99044aC9b8C9D44C0bBC8376C` | `prg()` returns the 56,361-byte PRG from three data blobs; keccak256 = `0x5bcd208f63ac255ffc391c4abeb7b8f701061ac896008607ef414c24c880f34d` |
| its Launcher (renderer) | `0xe6B82e3fFe31E66ccF445bE7F49916b1c0A1DE84` | `tokenURI` builds the whole page at read time; image and animation_url are `data:` URIs |
| READY 64 token | `0x0444C08150D830b3056926119DBEaB791669fF53` | bare C64 to READY, keyboard handed to the viewer |
| READY 64 Launcher | `0x08E13a8c04C98da88cD918900dC76D9C740AC28D` | `page(bytes prg, uint256 modes)` returns a complete player page for ANY PRG; `dataURI(prg, modes)` wraps it as `data:text/html;base64`. This is the publishing layer the Chamber tokens use |
| OpenROMs firmware | `0xE0a71d57FB514C8f5793e26937559935350b3406` | not needed: Tony and the Chamber drive the hardware directly |

Marketplace sandbox: the owner tested four iframe modes, six checks each;
`allow-scripts` alone suffices. The pages play inside the OpenSea frame.

## 3. What is being built

**The Chamber**: seven tokens over ONE program ("base 2"), the tall pillar
room from Tony with Tony himself, two bats, and a second Tony, "the buddy".
Each token is the buddy with one **mechanic** and one **colour**; the
room's back wall, one candle and a number carved in the floor are drawn at
every render from the current block. The room itself stays black and grey.

- **Mechanics and names (behaviour byte).** The owner's names, decided
  2026-09-06; the mechanic stays an attribute:

  | id | name | behaviour byte | what he does | status |
  |---|---|---|---|---|
  | 1 | The Shadow | 0 Follow | keeps his distance, faces you, jumps and crouches when you do | built, tested |
  | 2 | The Dancer | 1 Dance | steps and turns with the bass line, bounces on the hits, read from the chip | built, tested |
  | 3 | The Echo | 2 Echo | replays you exactly, four seconds behind: every step, jump and duck | built, tested |
  | 4 | The Mirror | 3 Mirror | your reflection about the room's centre line, facing the way your reflection would; crouches while you jump, bounces while you crouch | built, tested |
  | 5 | The Wanderer | 4 Wander | lives there and ignores you: strolls, pauses, sits, jumps now and then, on dice seeded from the block | built, tested |
  | 6 | The Shy | 5 Shy | runs when you come close, cowers at the pillar, bolts past you when you are almost on him, creeps back when you leave | built, tested |
  | 7 | The Sleeper | 6 Sleeper | dozes crouched until you come close, follows a while, dozes off | built, tested |
  | 8 | The Glitch | 7 Glitch | wears one of the seven at a time and teleports into the next, cycles the colours, blinks and jitters; his room is the blackout: no wall, no candle, no bats, dark grey stone, a grey Tony, the block number in black | built, tested |

  One build serves all eight: the byte selects the mechanic at run time.
  The Glitch's blackout is gated on his mechanic byte, not on the seed, so
  no other token's room can ever look like his; the colour byte is ignored
  for him (he cycles the seven).
  All seven exist and pass their scripted tests; the base is feature
  complete and waits only on the owner's play-through and the colour
  mapping before the freeze. Provisional colours in the shipped files:
  Shadow blue (6), Dancer cyan (3), Echo yellow (7), Mirror light blue
  (14), Wanderer green (5), Shy light red (10), Sleeper purple (4).
- **Colours (colour byte, a C64 colour index):** the owner's seven: cyan 3,
  green 5, yellow 7, light blue 14, blue 6, light red 10, purple 4. Which
  colour goes with which mechanic is **not decided yet**.
- **The wall, the candle and the bats (seed bytes):** drawn from 32 bytes:
  the block hash written at render time, so every fresh render is a
  different wall, a different candle, and different bats (which of eight
  flight paths each flies, where it starts, and whether it is there: no
  bats one render in sixteen, a single bat one in four). The **block
  number** is carved into the floor from 8 digit bytes.
- **The image:** the buddy alone in his colour, doing the idle dance the
  game plays when he stands still, as an animated SVG built in the contract.

The base program is a fresh build of Tony's engine (`tony-chamber.prg`, in
this repository), **not a patch over the Tony token's bytes**, so it needs
its own on-chain storage, the way the Tony token stores its PRG in data
blobs. The castles work (`ONCHAIN-CASTLES.md`) is the other line, patches
over base 1, and is not part of this collection.

## 3a. What a viewer is looking at, and why

Plain-language context, for the description text and for anyone reading
the contract.

**The machine.** nopsta wrote minimal64, a Commodore 64 emulator in
JavaScript, and stored it on Ethereum in 2022 as data contracts. He has
since passed away. This work was made after he was gone and independently
of him. A token's page runs that emulator in the viewer's browser with no
server, no file fetched from anywhere, and no Commodore firmware: the
program drives the hardware directly.

**The program.** Tony: Born for Adventure is a 2023 Commodore 64 demo by
Maciej Małecki (code), Rafał Dudek (graphics) and Sami Juntunen (music),
published MIT. The Chamber is one room built from its engine: the tall
pillar room, Tony, two bats, and the buddy, a second Tony in the token's
colour who behaves according to the token's mechanic. Tony is yours to
walk, jump and climb with the joystick; the buddy is the token's.

**The wall is the block.** The back wall is bricks drawn from 32 bytes.
When a marketplace or a viewer asks the token for its page, the contract
writes the hash of the newest block into those 32 bytes, so the bricks a
viewer sees are, literally, that block's hash: three bit streams run
through the bytes and decide which of 150 brick slots are filled. Three
seed bits pick how full the wall is (fewer bricks is common, a nearly full
wall is the rare roll) and two more decide whether one of the room's
candles is lit and where; four more bytes choose the bats. Every fresh
render is a different wall, and no
one, including the contract, can say in advance what it will be.

**The bats are the block too.** The two bats near the ceiling fly paths
the game already knows how to fly; the same 32 bytes choose which path
each flies, where it starts and how high, and whether it is there at all.
One render in sixteen is a quiet night with no bats; one in four has a
single bat. They stay well above Tony's reach: they are scenery, never a
danger.

**The number in the floor is the block whose hash drew the wall.** Eight
digits carved into the floor's right end name it: `block.number - 1`, the
newest block whose hash a view can read, the same one the seed comes from.
So a render is a photograph of the chain at one moment: the wall is what
that block's hash looked like, the floor says which block. A chain can only read the
last 256 block hashes, so a wall seen at block N cannot be recomputed on
chain an hour later. The renders are impressions, not a series. (If the
owner wants a permanent "birth wall", the mint block's hash can be stored
at mint and rendered alongside.)

**The buddy listens.** Each token's buddy has one mechanic. The Dancer, for
instance, reads the tune as the game plays it: the player keeps an image
of the sound-chip registers in memory, and the buddy steps and turns when
the bass line moves, and bounces when voice 3's envelope, read back from
the chip itself, jumps. No timing table and no data from outside the
machine: he is dancing to what the chip is actually doing.

**The picture.** The token image is the buddy alone in his colour, doing
the little dance the game plays when a character stands still, built in
the contract from the game's own sprite bytes as an animated SVG.

**Why nothing is stored per render and nothing is fetched.** The tokens
are keyless: no admin, no server, no URL. Everything a viewer receives is a
`data:` URI assembled in a view call from bytes already on chain. A render
costs the reader gas and the owner nothing. Bugs found later are fixed in
new tokens, never by changing these.

**A draft description, for the owner to edit** (it follows the wording
rules of section 1):

> The Dancer. One room of Tony: Born for Adventure, running on a Commodore
> 64 emulator kept on Ethereum, with no server and no firmware. Tony's cyan
> double dances to the tune: he steps with the bass line and bounces on the
> hits, read from the sound chip. The bricks of the back wall are the hash of
> the block this was rendered at, and the number in the floor is that block.
> Every fresh render is a new wall. Code Maciej Małecki, graphics Rafał
> Dudek, music Sami Juntunen (MIT). Emulator: minimal64 by nopsta (GPL-2.0),
> who stored the machine on Ethereum in 2022 and has since passed away; this
> work was made after he was gone and independently of him.

## 4. The base program and its parameter block

Current file: `deliverables/prg/minimal64/tony-chamber.prg`, 46,877 bytes,
a plain C64 PRG (2-byte load address `$0801`, BASIC stub, then the program,
ending at `$BF1A`), sha256
`67dc97bc1e3067151c8a1d24fe4bf18beabf83624c69cdb65182a34aa914ad61`.
One base for all eight tokens: it carries both of the demo's tunes, the
level tune for the seven and the intro tune for The Glitch (section 4a).

**RE-FROZEN 2026-09-07, later the same day.** The first freeze (commit
`c0b350a`) was reopened before anything left the repository, for one
change: a room without a candle is dim (section 4b). The base is now the
file in the commit named in section 8c and in
`deliverables/contract/base-record.json`. From here the program does not
change; anything found later is fix-forward in new tokens. **Record of the base:** size 46,877 bytes;
sha256 `67dc97bc1e3067151c8a1d24fe4bf18beabf83624c69cdb65182a34aa914ad61`; keccak256 `7677e3e91210588a9ecf781e493646836fbcde6e218173a304eb8253eeadb1ab`; marker at file offset `0x04EC1`, the 42 bytes
at `0x04EC9`. `tools/freeze_record.py`
prints these for the working tree, and `deliverables/contract/base-record.json`
holds the last run, with the eight stamped files' digests.
Byte-for-byte reproducible from the repository (section 9). The offsets
above are now constants; the marker is still the guard.

The **parameter block** is 50 bytes, 64-byte aligned in memory:

| offset from marker | bytes | field | the contract writes |
|---|---|---|---|
| 0 | 8 | marker `4D 55 52 41 4C 30 32 00` (`"MURAL02\0"`) | no (use it as a guard: require the bytes at the offset) |
| 8 | 32 | seed | yes: `blockhash(block.number - 1)`, the newest hash a view can read |
| 40 | 8 | block digits, one byte each, values 0–9, most significant first | yes: the low eight decimal digits of `block.number - 1` (the block whose hash is the seed), zero-padded |
| 48 | 1 | behaviour, 0–7 | yes: the token's mechanic (7 = the Glitch) |
| 49 | 1 | colour, 0–15 | yes: the token's colour |

So the contract writes **42 bytes** at `marker + 8`. In the current build the
marker is at file offset `0x04EC1` and the 42 bytes start at file offset
`0x04EC9` (address `$56C8`); file offsets count the 2-byte load address. The
digits are bytes 0–9, not ASCII. Bytes never written keep the file's
defaults (block 25850267, Follow, green).

## 4a. The Glitch's tune (decided 2026-09-07)

The demo has two tunes, both by Sami Juntunen (MIT): the level tune, which
the seven play, and the intro scroller's tune, which The Glitch alone plays.
The intro tune was relocated from $E000 to $8000 (`tools/sidreloc.py`,
proved note-for-note identical by an eight-minute replay with
`tools/verify_reloc.py`; `src/music/RELOCATION.md`) and lives inside the
one base at $8000–$9695, a region the engine never touches at run time
(measured). Behaviour 7 starts and plays the intro tune, anything else the
level tune; nothing in the block format changes and the contract does
nothing extra. The Glitch's Dance phase steps to the intro tune's second
voice and keeps a short pause after each landing (measured: airborne 59%,
about one bounce a second; the Dancer token, on the level tune, airborne
33%). `HANDOFF-GLITCH-TUNE.md` is the record of how this was decided and
verified. **The intro tune is The Glitch's alone**: the Dancer keeps the
level tune (he dances better to it: 42 steps against 7 in the same time).

**The dice (2026-09-07, at the contracts session's request):** the
Wanderer's and the Glitch's dice used to be stirred every frame by the
chip's oscillator 3, a musical waveform. They are now a 16-bit shift
register seeded at boot from the block (`seed[28] ^ seed[15]` low,
`seed[3] ^ seed[20]` high, a zero start replaced by $A55A) and stepped
eight bits a frame by the mechanic that rolls, with nothing from the chip,
the raster or the player stirred in: a render's dice are a pure function of
its seed and the frame count. `dice_seed` and `dice_step` in
`tools/stamp_mural.py` are the model; the `dice` test in
`tools/verify_buddy.py` reads the register off the machine and finds it on
the model's trajectory, before and after the player walks. Bytes 3, 15, 20
and 28 of the seed are therefore best left to the hash, not forced.

How the seed is used (so a test can predict a wall; the Python model is
`tools/stamp_mural.py --show`): three bit streams run through the 32 bytes
(from byte 0, byte 19 and byte 25, each wrapping at 32); `seed[31] & 7` picks
the wall density through the table `3,3,3,0,0,1,1,2` (fewer bricks common,
the near-full wall rare); `seed[30] & 3 != 0` means a candle (three in
four); `seed[29]` places it (low 4 bits column, next 3 bits row). **A room
without a candle is dim**: the stone (pillars, floor, ceiling, bricks) and
Tony drop from light grey (15) to medium grey (12), keyed on that same bit;
a lit room is unchanged, and The Glitch's blackout (dark grey 11, Tony 12)
takes precedence (section 4b). Any 32
bytes are valid; bytes 24–27 choose the bats (paths, start columns and
rows, presence; the model is `bats()` in `tools/stamp_mural.py`). A wall
seen at block N cannot be recomputed on chain more
than 256 blocks later; the renders are impressions, not a series. If a
permanent "birth wall" is wanted, store the mint block's hash at mint and
render it alongside (owner's decision, not made).

## 4b. The dim room (decided 2026-09-07)

Three rooms, by their colours, all from the same base and the same block:

| room | when | stone | Tony | the rest |
|---|---|---|---|---|
| lit | a candle (`seed[30] & 3 != 0`, three in four) | light grey 15 | light grey 15 | wall, candle, bats, number as before |
| dim | no candle (`seed[30] & 3 == 0`) | medium grey 12 | medium grey 12 | wall, bats, number as before; the buddy keeps his colour |
| blackout | behaviour 7, The Glitch | dark grey 11 | grey 12 | no wall, no candle, no bats, number in black |

The candle class is a stored trait per token in the contracts session's
table, so a candle-less token is a dim room for life, and the description
can say so ("a dim room" or the owner's words). The engine keeps one byte,
`muralDim`, at `marker + 58`, set at room entry; a contract never writes it.
The `rooms` test in `tools/verify_buddy.py` reads the three rooms' colours
off the machine; `tools/stamp_mural.py --show` names the room.

## 5. What `tokenURI(id)` must do

1. `prg = base2()` — the frozen program, from the collection's own data
   blobs (the Tony token's three-blob pattern). The base is 46,877 bytes;
   two SSTORE2-style blobs hold 49,150, so it fits in two with 2,274 bytes
   of headroom. Anything further means a third blob.
2. Guard: `require(prg[MARKER..MARKER+8] == "MURAL02\0")`.
3. Write the 42 bytes at `MARKER + 8`: seed, digits, `behaviour[id]`,
   `colour[id]` (section 4). Sketch, over a `bytes memory prg`:

    ```solidity
    bytes32 h = blockhash(block.number - 1);
    for (uint256 i; i < 32; ++i) prg[OFF + i] = h[i];
    uint256 n = block.number - 1;                       // the block whose hash is h: the floor names it
    for (uint256 i; i < 8; ++i) { prg[OFF + 39 - i] = bytes1(uint8(n % 10)); n /= 10; }   // digits at seed + 32..39
    prg[OFF + 40] = bytes1(behaviour[id]);
    prg[OFF + 41] = bytes1(colour[id]);
    ```

    (`OFF` = the seed's file offset, `0x04EC9`, a constant since the freeze;
    keep the marker guard.)
4. `animation_url = READY64_LAUNCHER.dataURI(prg, 0)`. `modes = 0`: checked
   by the contracts session against the deployed Launcher's templates, the
   argument is accepted and unused.
5. `image` = the idle-dance SVG for `colour[id]` as a `data:image/svg+xml;base64` URI (section 6).
6. JSON: `name` (owner's names), `description` (owner's text, must carry
   the credits and the nopsta statement of section 1, and it is where the
   render's block number, wall and candle go, since they change every
   render), `attributes`: the stored traits only, Character, Wall class,
   Bats class, Candle class, Colour, Base hash (keccak256 of the base at
   the freeze). Nothing that moves goes in `attributes`: marketplaces index
   them and a moving trait cannot be corrected once cached. All of it
   `data:application/json;base64`.

Everything is a view; gas is the reader's. Marketplaces cache metadata and
re-fetch on their own schedule, so "every render" means every re-fetch;
READY 64 and a direct call are always fresh.

## 6. The image: the SVG, exactly (redesigned 2026-09-07)

**FROZEN 2026-09-07, the way the base is frozen at `21b95e3`.** The first image
freeze, `9880f03`, was reopened by the owner later the same day for one fix and
re-frozen: dance frames B, C and D now rest hidden (a static `opacity="0"`, 36
bytes per file), so a viewer that does not run the animation, a file browser's
preview or a marketplace's still, shows frame A alone instead of all four frames
at once; where the animation runs the files draw pixel for pixel as before. The
commit holding the frozen files is the one named in
`deliverables/contract/tokens-record.json`, with each file's size, sha256 and
keccak256; `deliverables/contract/tokens-verify.txt` is the checker's full output
at the freeze (76 checks, all passing, eight of them the still). The files do not
change after that commit; a change would be a new named commit, declared by the
owner.

The image was redesigned and adopted on 2026-09-07; the earlier "buddy alone"
files (`deliverables/assets/buddy-idle-<colour>.svg`, 6,056 bytes) are
superseded. Reference implementation: `tools/buddy_retro_svg.py --final`;
the eight outputs, by token name, are `deliverables/assets/tokens/the-<name>.svg`.
`deliverables/THUMBNAILS.md` is the design log. **Store the eight files as they
are** (constants or SSTORE2 blobs) rather than generating them: the files now
differ per token in more than the fill colour (the floor's geometry and colours,
the position of the live square, and the Glitch's own animations), so the test is
equality with the repository files.

| file | bytes | base64 |
|---|---|---|
| the-shadow.svg | 13,994 | 18.2 KB |
| the-dancer.svg | 17,765 | 23.1 KB |
| the-echo.svg | 17,764 | 23.1 KB |
| the-mirror.svg | 17,720 | 23.1 KB |
| the-wanderer.svg | 13,996 | 18.2 KB |
| the-shy.svg | 17,763 | 23.1 KB |
| the-sleeper.svg | 13,994 | 18.2 KB |
| the-glitch.svg | 25,036 | 32.6 KB |

What the card is: a 48 x 48 black canvas with three parts.

- **The tag**: the seven token colours as seven 2 x 2 squares straight across
  the top left, at y = 2, x = 2 + 2.5 i (a half-pixel gap), in the order blue,
  yellow, purple, green, light red, cyan, light blue (opposite pairs side by
  side, green in the middle). They rest at opacity 0.3. The token's own square
  breathes: opacity 0.3 to 1 and back over 3.6 s (two dance loops, eased), with a
  blurred glow copy beneath it (Gaussian blur 1.1, opacity 0 to 0.9). The tag is
  drawn anti-aliased (`shape-rendering="geometricPrecision"` on its group) so the
  half-pixel gap stays even at any display size.
- **The buddy**: the game's own idle dance, unchanged from before: four frames,
  24 x 42 pixels, drawn at (12, 5), the loop A B A B C D at 0.3 s a phase
  (1.8 s), frame A first and frames B, C and D resting hidden, so a still shows
  frame A alone. His feet stand on the floor's top row.
- **The floor**: rows 37 to 47, a dithered gradient from the token's colour down
  to black (Shadow: blue, black; Dancer: cyan, light blue, blue, black; Echo:
  yellow, orange, brown, black; Mirror: light blue, blue, black; Wanderer: green,
  black; Shy: light red, red, brown, black; Sleeper: purple, black), dithered on a half-pixel grid (96 x 22 cells, a 4 x 4 ordered matrix),
  drawn as one path per colour inside `<g transform="scale(0.5)">`. The floors
  follow the supply ladder: the three at 12 (Shadow, Wanderer, Sleeper) have a
  single fade, the three at 8 have two or three steps, the Dancer and the
  Glitch three.

The Glitch's file differs throughout:

- His body is dark grey (`#4a4a4a`) on a floor that runs light grey, grey, dark
  grey, black; the room with the lights out.
- **Static**: once per 3.6 s, from 1.20 to 1.54 s, ten quick flips of his fill
  between grey, dark grey and a colour; the two colour flips (30 ms and 20 ms)
  are dealt from a fixed sequence so each of the seven colours appears twice
  over seven bursts, never the same twice running; the fill animation's period
  is therefore 25.2 s.
- **The blink** from the earlier design stays: every 2.6 s he drops out for
  80 ms, is back for 40 ms, out again for 80 ms.
- **The sweep**: once per 3.6 s a wave of light runs across the seven squares,
  each peaking in turn at 0.3 + 0.15 i seconds, rising in 50 ms and fading over
  450 ms, with the same glow copy under each.

All timing is SMIL `<animate>` on opacity and fill; no scripts, no external
references, no fonts. Every file was verified in Chromium by seeking the SVG
clock: body colour, floor, the seven squares and their order and resting level,
the own square at the peak, the four dance frames, the Glitch's sparks, blink
and sweep. Viewers that hand the SVG to an `<img>` animate it (the major
browsers run SMIL there); viewers that rasterise to a still without running the
animation show the resting card with frame A alone, which the checker proves by
rendering each file with every animation element removed. Measure the
marketplaces you care about before promising the animation.

Credits stay where section 5 puts them, in the token metadata: the sprite art
is Rafał Dudek's and the file carries no text of its own.

## 7. How to prove the contract before it is deployed

- **Bytes.** For several block values and all seven ids, `prgFor(id)` in a
  local EVM must equal `tools/stamp_mural.py BASE OUT --hex <blockhash>
  --block <number> --behaviour b --colour c` applied to the frozen base,
  byte for byte. The Python side is the reference; it is what the tests in
  this repository already run.
- **Runs.** Every produced PRG must boot and behave on the native minimal64
  harness (`tools/m64-harness/m64run`, built from nopsta's source):
  `tools/verify_buddy.py PRG` drives all seven mechanics and checks each
  against what it must do; `tools/verify_bats.py PRG` checks the seeded
  bats over sixteen seeds. `tools/stamp_mural.py PRG --show` predicts the
  wall, the candle and the bats for the seed you wrote.
- **Image.** The SVG for each colour equals the reference file.
- **Page.** `dataURI(prg, modes)` opens and plays in READY 64 and in the
  OpenSea frame; the owner plays each mechanic there (the gate).

## 8. Deployment order (owner's keys)

1. Freeze base 2 in this repository: final build, keccak256 recorded,
   offsets recorded, this document updated with the constants. (Done,
   2026-09-07.)
2. Deploy the base blobs; read them back and check the hash.
3. Deploy the token contract with the seven (behaviour, colour) pairs, the
   SVG constants, the Launcher address and `modes`.
4. Mint the seven to the owner.
5. Verify: fresh metadata on a marketplace, the SVG animating or at least
   frame A, the wall changing between renders, each mechanic playable.

Decisions the owner still has to make: colour ↔ mechanic mapping; the seven
names; the description text; whether a "birth wall" is stored at mint.

## 8a. Releasing The Dancer first

Nothing forces all seven out at once. A collection contract can define
the seven and mint them one at a time, whenever the owner sends the
transaction. The only constraint is the base program: it is frozen when it
is deployed. Since all seven mechanics now exist in one build, the natural
order is: the owner plays the seven, the base is frozen, the base and the
contract are deployed once, and The Dancer (or any of them) is minted
first, the rest whenever the owner likes. The alternative, a first base
with only Follow and Dance and a second base later, is no longer needed;
keep it in mind only if the owner wants The Dancer out before playing the
other six, in which case the contract keeps a base per token id.

## 8b. What the contracts agent needs, and how to get it

Nothing for the Chamber is on chain yet, so there is nothing to read from
Etherscan: the agent deploys the base. Everything needed is in this
repository, and read access to the fork (`DeMEdPit/tony-demo`, branch
`claude/tony-c64-demo-expert-wp40it`) is the simplest way to hand it over.
The PRG files are committed (they are force-added, since `*.prg` is
ignored by default). If a file bundle is preferred instead, it is:

1. `deliverables/prg/minimal64/tony-chamber.prg`, the base, frozen; the
   hash and offsets in this document are its.
2. `deliverables/assets/buddy-idle-*.svg`, the seven image files; the four
   `d` path strings inside them are the constants the contract needs.
3. The seven (behaviour, colour) pairs and names (section 3), the
   description text (section 3a, once the owner has edited it).
4. To verify rather than trust: `tools/stamp_mural.py` (the byte
   reference), `tools/buddy_retro_svg.py` (the image reference),
   `tools/verify_dance.py`, and `tools/m64-harness/` with nopsta's source
   (github.com/nopsta/minimal64) to run any produced PRG headless.
5. This document and `deliverables/EXPERIMENTS.md`.

## 8c. Ready for contract writing and a testnet: what is fixed, what is yours

Fixed on this side, and frozen by the owner's word on 2026-09-07:

- **The images**: the eight SVGs, frozen (section 6) at the commit named in
  `deliverables/contract/tokens-record.json` with their hashes;
  `deliverables/contract/tokens-verify.txt` is the checker's output.

- **The base**: one PRG, 46,877 bytes, sha256 above, byte-for-byte
  reproducible from the repository; both tunes inside; the eight mechanics,
  the seeded wall, candle and bats, the dim room without a candle, the
  blackout with a black number.
  The commit holding the frozen file is the one named in
  `deliverables/contract/base-record.json` (tags cannot be pushed from this
  session, so the commit is the reference); the first freeze's `c0b350a`
  was reopened the same day for the dim room, section 4b.
- **The block**: 42 bytes at `marker + 8` (file offset `0x04EC9` in this
  build; find the marker), seed, digits, behaviour, colour. Behaviour 7 is
  the only value that changes the room and the tune.
- **The model**: `tools/stamp_mural.py --show` predicts wall, candle and
  bats from any 32 bytes, and `deliverables/contract/chamber-vectors.json`
  holds 32 worked examples with the exact bytes to write.
- **The images**: `deliverables/assets/tokens/the-<name>.svg`, eight files,
  redesigned 2026-09-07 (the retro layout: the seven colours as a tag, the
  buddy, a dithered floor; the Glitch dark with static, sparks, a blink and a
  sweep), frozen at the commit named in `deliverables/contract/tokens-record.json`
  with their hashes, to be stored as they are (section 6).
- **The names and provisional colours**: section 3; the colours are the
  owner's to confirm before the metadata is written.

Yours (the contracts agent's), from the main sections: the seed rule
(section 5, seed = the newest block hash the view can read, with the
token id mixed in if the synthesis's per-token arrangement is kept), the
`tokenURI` assembly (section 5), the storage of the base and the write of
the 42 bytes into a copy of it at render time, the proof plan (section 7:
write a vector's bytes, render through the launcher, compare with the
vector's wall rows), and the testnet deployment order (section 8). The
owner still holds the colour table and the description text (section 3a
has the draft); the freeze is done. The supply is a ladder, set in the contracts
session: The Shadow, The Wanderer and The Sleeper 12 each; The Echo, The
Mirror and The Shy 8 each; The Dancer 3; The Glitch 1 (64). The rooms
are three stored traits per token (wall class, bats class, candle class)
with their own counts. The 64-row table lives in the contracts repository,
not here.

## 9. Where things are in this repository

| path | what |
|---|---|
| `deliverables/prg/minimal64/tony-chamber.prg` | base 2, current build (46,877 bytes, both tunes; default block: Follow, green, block 25850267) |
| `deliverables/prg/minimal64/tony-chamber-the-<name>.prg` | the same build stamped for each of the eight (provisional colours) |
| `tools/make_chamber.py` | generates the Chamber sources from the buddy build (block, mural, mechanics) |
| `tools/build_chamber_room.py` | the room map, charset and materials |
| `tools/stamp_mural.py` | writes seed, digits, behaviour, colour into a PRG; `--show` predicts the wall |
| `tools/verify_buddy.py` | scripted tests of all seven mechanics on minimal64 |
| `tools/verify_bats.py` | the seeded bats checked over sixteen seeds on minimal64 |
| `tools/sidreloc.py`, `tools/verify_reloc.py` | move a tune to another address and prove it by replay; `src/music/TonyIntro8000_reloc.sid` is the intro tune at $8000 (E17) |
| `tools/chamber_vectors.py` → `deliverables/contract/chamber-vectors.json` | 32 test vectors: the 42 bytes to write and what the base draws from them (wall rows, candle, bats, tune, room) |
| `deliverables/audio/` | forty seconds of the Glitch (intro tune) and the Dancer (level tune), rendered by the emulator's own SID |
| `tools/buddy_retro_svg.py --final` | the image reference; `deliverables/assets/tokens/the-<name>.svg` its outputs (`tools/buddy_thumbnail.py` is the earlier, superseded design) |
| `tools/m64-harness/` | the native minimal64 test runner (`build.sh` builds it from nopsta's source) |
| `deliverables/EXPERIMENTS.md` | the ledger: every decision, measurement and open item |
| `deliverables/ONCHAIN-CASTLES.md` | the other line: patches over the Tony token's bytes (not this collection) |

Rebuild: `./gradlew build -x downloadDeps` once (on a fresh clone it extracts the charset the room builder needs), then
`python3 tools/build_chamber_room.py && python3 tools/make_chamber.py && ./gradlew build -x downloadDeps`
(the exomizer step fails at the end; ignore it, the PRG is at
`src/kickass/tony-chamber.prg`). Then `python3 tools/verify_buddy.py src/kickass/tony-chamber.prg`.

## 10. Things not to do

- Do not patch the Tony token's PRG to make the Chamber; it is a different
  program. Do not modify the music. Do not change the base after the freeze.
- Do not bake an RPC URL or any fetch into the token; everything is `data:`.
- The block offset is fixed now (`0x04EC9`); keep the marker as the guard.
- Do not push to, fork publicly, or open pull requests against the upstream
  `maciejmalecki/tony-demo`; the owner's fork is the workspace.
