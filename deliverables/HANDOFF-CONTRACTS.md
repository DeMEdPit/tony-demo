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
- **The music is never modified.** The Chamber reads the tune's state; it
  does not change a byte of it.
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
  | 4 | The Mirror | 3 Mirror | your reflection about the room's centre line; crouches while you jump, bounces while you crouch | built, tested |
  | 5 | The Wanderer | 4 Wander | lives there and ignores you: strolls, pauses, sits, jumps now and then, on the chip's dice | built, tested |
  | 6 | The Shy One | 5 Shy | runs when you come close, cowers at the pillar, bolts past you when you are almost on him, creeps back when you leave | built, tested |
  | 7 | The Sleeper | 6 Sleeper | dozes crouched until you come close, follows a while, dozes off | built, tested |

  One build serves all seven: the byte selects the mechanic at run time.
  All seven exist and pass their scripted tests; the base is feature
  complete and waits only on the owner's play-through and the colour
  mapping before the freeze. Provisional colours in the shipped files:
  Shadow blue (6), Dancer cyan (3), Echo yellow (7), Mirror light blue
  (14), Wanderer green (5), Shy One light red (10), Sleeper purple (4).
- **Colours (colour byte, a C64 colour index):** the owner's seven: cyan 3,
  green 5, yellow 7, light blue 14, blue 6, light red 10, purple 4. Which
  colour goes with which mechanic is **not decided yet**.
- **The wall (seed bytes):** drawn from 32 bytes: the block hash written at
  render time, so every fresh render is a different wall. The **block
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
candles is lit and where. Every fresh render is a different wall, and no
one, including the contract, can say in advance what it will be.

**The number in the floor is the block number.** Eight digits carved into
the floor's right end say which block the render was made at. So a render
is a photograph of the chain at one moment: the wall is what that block's
hash looked like, the floor says which block. A chain can only read the
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

Current file: `deliverables/prg/minimal64/tony-chamber.prg`, 40,248 bytes,
a plain C64 PRG (2-byte load address `$0801`, BASIC stub, then the program),
sha256 `5a479b7ae8a24a14a2ee6e26f8bc4cc3eda524f6e7a136e54b979c0cd2300948`.
Byte-for-byte reproducible from the repository (section 9). **Feature
complete, not frozen**: the freeze follows the owner's play-through and any
change it asks for; a rebuild moves the block. Find the block by its
marker, never by a fixed offset, until the freeze.

The **parameter block** is 50 bytes, 64-byte aligned in memory:

| offset from marker | bytes | field | the contract writes |
|---|---|---|---|
| 0 | 8 | marker `4D 55 52 41 4C 30 32 00` (`"MURAL02\0"`) | no (use it as a guard: require the bytes at the offset) |
| 8 | 32 | seed | yes: `blockhash(block.number - 1)`, the newest hash a view can read |
| 40 | 8 | block digits, one byte each, values 0–9, most significant first | yes: the low eight decimal digits of `block.number`, zero-padded |
| 48 | 1 | behaviour, 0–6 | yes: the token's mechanic |
| 49 | 1 | colour, 0–15 | yes: the token's colour |

So the contract writes **42 bytes** at `marker + 8`. In the current build the
marker is at file offset `0x04BC1` and the 42 bytes start at file offset
`0x04BC9` (address `$53C8`); file offsets count the 2-byte load address. The
digits are bytes 0–9, not ASCII. Bytes never written keep the file's
defaults (block 25850267, Follow, green).

How the seed is used (so a test can predict a wall; the Python model is
`tools/stamp_mural.py --show`): three bit streams run through the 32 bytes
(from byte 0, byte 19 and byte 25, each wrapping at 32); `seed[31] & 7` picks
the wall density through the table `3,3,3,0,0,1,1,2` (fewer bricks common,
the near-full wall rare); `seed[30] & 3 != 0` means a candle (three in
four); `seed[29]` places it (low 4 bits column, next 3 bits row). Any 32
bytes are valid. A wall seen at block N cannot be recomputed on chain more
than 256 blocks later; the renders are impressions, not a series. If a
permanent "birth wall" is wanted, store the mint block's hash at mint and
render it alongside (owner's decision, not made).

## 5. What `tokenURI(id)` must do

1. `prg = base2()` — the frozen program, from the collection's own data
   blobs (the Tony token's three-blob pattern; 38,200 bytes fits in two
   SSTORE2-style chunks).
2. Guard: `require(prg[MARKER..MARKER+8] == "MURAL02\0")`.
3. Write the 42 bytes at `MARKER + 8`: seed, digits, `behaviour[id]`,
   `colour[id]` (section 4). Sketch, over a `bytes memory prg`:

    ```solidity
    bytes32 h = blockhash(block.number - 1);
    for (uint256 i; i < 32; ++i) prg[OFF + i] = h[i];
    uint256 n = block.number;
    for (uint256 i; i < 8; ++i) { prg[OFF + 47 - i] = bytes1(uint8(n % 10)); n /= 10; }
    prg[OFF + 40] = bytes1(behaviour[id]);
    prg[OFF + 41] = bytes1(colour[id]);
    ```

    (`OFF` = the seed's file offset, `0x04BC9` in the current build; write it
    as a constant only at the freeze.)
4. `animation_url = READY64_LAUNCHER.dataURI(prg, modes)`. **The `modes`
   value is not known here**: read the deployed Launcher's ABI and source and
   use the same joystick-game setting the Tony token uses (joystick in port
   2, autostart). Confirm on READY 64 before relying on it.
5. `image` = the idle-dance SVG for `colour[id]` as a `data:image/svg+xml;base64` URI (section 6).
6. JSON: `name` (owner's names, not decided), `description` (owner's text,
   must carry the credits and the nopsta statement of section 1),
   `attributes`: Mechanic (name), Colour (name), Base hash (keccak256 of
   base 2 at the freeze), Block (the render's block number), Wall (density
   name, from `seed[31] & 7` and the table above), Candle (yes/no from
   `seed[30] & 3`). All of it `data:application/json;base64`.

Everything is a view; gas is the reader's. Marketplaces cache metadata and
re-fetch on their own schedule, so "every render" means every re-fetch;
READY 64 and a direct call are always fresh.

## 6. The image: the SVG, exactly

Reference implementation: `tools/buddy_thumbnail.py` (default layout); the
seven expected outputs are `deliverables/assets/buddy-idle-<colour>.svg`,
6,056 bytes each. The contract's output should match them byte for byte,
which makes the test trivial. Shape of the file:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" shape-rendering="crispEdges">
<rect width="48" height="48" fill="#000"/>
<path fill="#75cec8" d="M... (frame A, run-length pixel rows)">
<animate attributeName="opacity" values="1;0;1;0;0;0;1" keyTimes="0.0000;0.1667;0.3333;0.5000;0.6667;0.8333;1" calcMode="discrete" dur="1.8s" repeatCount="indefinite"/>
</path>
<path fill="#75cec8" d="... frame B"> <animate ... values="0;1;0;1;0;0;0" .../> </path>
<path fill="#75cec8" d="... frame C"> <animate ... values="0;0;0;0;1;0;0" .../> </path>
<path fill="#75cec8" d="... frame D"> <animate ... values="0;0;0;0;0;1;0" .../> </path>
</svg>
```

- Four frames, the game's own idle sprites (24×42 pixels each, the top and
  bottom halves of a two-sprite character), drawn at (12, 8) on a 48×48
  canvas; the loop is A B A B C D at 0.3 s a phase (fifteen PAL frames), as in
  the game. Frame A is first in the file so a still render shows it.
- The four `d` strings are constants (about 1.4 KB each, 5.6 KB in all);
  copy them from the reference files. Only the fill colour changes per
  token. Colour hex values (the Colodore palette the emulator uses): cyan
  `#75cec8`, green `#56ac4d`, yellow `#edf171`, light blue `#706deb`, blue
  `#2e2c9b`, light red `#c46c71`, purple `#8e3c97`.
- Base64 of the SVG is about 8.1 KB per render.
- Viewers that hand the SVG to an `<img>` animate it (the major browsers
  run SMIL there); viewers that rasterise to a cached still show frame A.
  Measure the marketplaces you care about before promising the animation.

## 7. How to prove the contract before it is deployed

- **Bytes.** For several block values and all seven ids, `prgFor(id)` in a
  local EVM must equal `tools/stamp_mural.py BASE OUT --hex <blockhash>
  --block <number> --behaviour b --colour c` applied to the frozen base,
  byte for byte. The Python side is the reference; it is what the tests in
  this repository already run.
- **Runs.** Every produced PRG must boot and behave on the native minimal64
  harness (`tools/m64-harness/m64run`, built from nopsta's source):
  `tools/verify_buddy.py PRG` drives all seven mechanics and checks each
  against what it must do. `tools/stamp_mural.py PRG --show` predicts the
  wall for the seed you wrote.
- **Image.** The SVG for each colour equals the reference file.
- **Page.** `dataURI(prg, modes)` opens and plays in READY 64 and in the
  OpenSea frame; the owner plays each mechanic there (the gate).

## 8. Deployment order (owner's keys)

1. Freeze base 2 in this repository: final build, keccak256 recorded,
   offsets recorded, this document updated with the constants.
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

1. `deliverables/prg/minimal64/tony-chamber.prg`, the base (take it again
   at the freeze; the hash and offsets in this document are updated then).
2. `deliverables/assets/buddy-idle-*.svg`, the seven image files; the four
   `d` path strings inside them are the constants the contract needs.
3. The seven (behaviour, colour) pairs and names (section 3), the
   description text (section 3a, once the owner has edited it).
4. To verify rather than trust: `tools/stamp_mural.py` (the byte
   reference), `tools/buddy_thumbnail.py` (the image reference),
   `tools/verify_dance.py`, and `tools/m64-harness/` with nopsta's source
   (github.com/nopsta/minimal64) to run any produced PRG headless.
5. This document and `deliverables/EXPERIMENTS.md`.

## 9. Where things are in this repository

| path | what |
|---|---|
| `deliverables/prg/minimal64/tony-chamber.prg` | base 2, current build (40,248 bytes; default block: Follow, green, block 25850267) |
| `deliverables/prg/minimal64/tony-chamber-the-<name>.prg` | the same build stamped for each of the seven (provisional colours) |
| `tools/make_chamber.py` | generates the Chamber sources from the buddy build (block, mural, mechanics) |
| `tools/build_chamber_room.py` | the room map, charset and materials |
| `tools/stamp_mural.py` | writes seed, digits, behaviour, colour into a PRG; `--show` predicts the wall |
| `tools/verify_buddy.py` | scripted tests of all seven mechanics on minimal64 |
| `tools/buddy_thumbnail.py` | the SVG reference; `deliverables/assets/buddy-idle-*.svg` its outputs |
| `tools/m64-harness/` | the native minimal64 test runner (`build.sh` builds it from nopsta's source) |
| `deliverables/EXPERIMENTS.md` | the ledger: every decision, measurement and open item |
| `deliverables/ONCHAIN-CASTLES.md` | the other line: patches over the Tony token's bytes (not this collection) |

Rebuild: `python3 tools/build_chamber_room.py && python3 tools/make_chamber.py && ./gradlew build -x downloadDeps`
(the exomizer step fails at the end; ignore it, the PRG is at
`src/kickass/tony-chamber.prg`). Then `python3 tools/verify_buddy.py src/kickass/tony-chamber.prg`.

## 10. Things not to do

- Do not patch the Tony token's PRG to make the Chamber; it is a different
  program. Do not modify the music. Do not change the base after the freeze.
- Do not bake an RPC URL or any fetch into the token; everything is `data:`.
- Do not write a fixed block offset before the freeze; use the marker.
- Do not push to, fork publicly, or open pull requests against the upstream
  `maciejmalecki/tony-demo`; the owner's fork is the workspace.
