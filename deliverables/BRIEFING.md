# The Chamber: a briefing for an advisor

Written 2026-09-06 by the AI collaborator that did the engineering on this
project, at the owner's request, for someone who may advise on it. It
says what we are making, how we think about it, what is decided, what is
open, and where an outside view would help most. Everything technical in
it was measured on the machine the tokens will run on; where I am
guessing, I say so. The owner directs; the other design session and the
contracts agent are named where they own a piece.

## 1. The short version

A Commodore 64 emulator has been on Ethereum since 2022, stored by its
author, nopsta, who has since passed away. A complete C64 game, Tony: Born
for Adventure (MIT, 2023, by Maciej Małecki, Rafał Dudek and Sami
Juntunen), was put on Ethereum in August 2026 as a single token whose page
runs the game on that emulator with no server, no file fetched, and no
Commodore firmware. This project builds on that: one new room made from
the game's own engine, the Chamber, in which Tony has a second Tony beside
him, a buddy with a character. Eight characters exist. The room's back
wall, candle and bats are drawn from a 32-byte seed, and the block number
is carved into the floor. The plan now taking shape is a collection of 64
tokens: seven characters times nine rooms, plus one token, the Glitch,
whose room is a blackout. The program is feature complete and tested; the
freeze, the contract and the deployment are ahead.

## 2. What already exists on mainnet, and what we add

Already there (deployed by others, or by the owner before this project):

| what | note |
|---|---|
| minimal64, nopsta's C64 emulator in JavaScript, as four data contracts | anyone can read the bytes; GPL-2.0; source on GitHub |
| Tony: Born for Adventure, one token | the 56 KB program in three data blobs; `tokenURI` builds a complete playable page at read time; image and animation are `data:` URIs |
| READY 64, a token and a Launcher | the Launcher's `page(bytes prg, uint256 modes)` returns a self-contained player page for ANY program; `dataURI(...)` wraps it. This is the permissionless publishing layer we use |
| OpenROMs firmware | free KERNAL, BASIC and character set on chain; not needed here, the programs drive the hardware directly |

The owner tested the marketplace sandbox: the pages play inside the
OpenSea frame with `allow-scripts` alone.

What we add: one program (the Chamber, 41,094 bytes, a fresh build of the
game's engine, not a patch over the deployed game), stored on chain once;
a contract that assembles each token's page from that program, 42 bytes
written per render, and an image built in the contract; and the tokens.

## 3. The piece

### The room

The tall pillar room from the game: brick ceiling, brick floor, two plain
pillars, a black back wall. No dashboard, no menu, no other rooms, no
hazards. Tony is yours, with the joystick. The buddy is the token's.

### What the seed draws

Thirty-two bytes drive the room, and the contract writes them at render
time:

- **The wall**: 150 slots of dotted bricks, filled or not by three bit
  streams through the seed. Three seed bits pick the density: fewer bricks
  is common, a nearly full wall is the rare roll.
- **The candle**: present three times in four, placed by the seed among
  seventy positions on the upper and middle wall. It is the game's own
  glowing candle from another room.
- **The bats**: two bats near the ceiling. The seed picks each one's
  flight path from eight authored ones (glides, flutters, a wave, hops,
  bobbing, a dip), its start column and row, and whether it is there: no
  bats one render in sixteen, a single bat one in four. Checked
  exhaustively: on every path, row and column pair, the lowest bat stays
  30 pixels above the top of Tony's jump and the two bats never come
  within 32 pixels of each other. They are scenery, never a danger.
- **The block number**: eight digits carved into the floor's right end.

### The eight characters

One build serves all eight; a mechanic byte selects the character.

| # | name | what the buddy does | listens to |
|---|---|---|---|
| 1 | The Shadow | keeps his distance, faces you, jumps and crouches when you do | you |
| 2 | The Dancer | side-steps and turns with the bass line, bounces on the hits, ignores you | the tune, read from the sound chip |
| 3 | The Echo | replays you exactly, four seconds later: position, height, pose, every jump and duck | you, recorded |
| 4 | The Mirror | your reflection about the room's centre line, facing the way a reflection would; crouches while you jump, bounces while you crouch | you, inverted |
| 5 | The Wanderer | strolls, pauses, sits, jumps now and then; turns at the pillars; ignores you | the chip's dice and the seed's mood |
| 6 | The Shy One | runs at your speed when you come close, cowers at the pillar, bolts past you if you press in, creeps back when you leave | you |
| 7 | The Sleeper | dozes crouched, wakes when you approach, follows six seconds, dozes off | you |
| 8 | The Glitch | wears one of the seven at a time and teleports into the next; cycles the colours; blinks and jitters in bursts | the chip's dice |

Each has a dedicated colour, chosen by the owner from the machine's
palette: Shadow blue, Dancer cyan, Echo yellow, Mirror light blue,
Wanderer green, Shy One light red, Sleeper purple; the Glitch cycles the
seven. Every one jumps with Tony's measured arc and crouches with the
game's own crouch.

Two of them are instruments as much as characters. The Dancer reads the
tune from inside the machine: the beat from the notes the player sends to
the sound chip, the accents from the chip's own envelope readback
register. The Wanderer's dice are a shift register stirred by the chip's
third oscillator every frame, so nobody can say where he will be. Both
quietly demonstrated that the on-chain emulator implements those parts of
the chip faithfully.

### The Glitch and the blackout

The eighth token's room is unlike any other's and gated on his mechanic
byte, so no seed can produce it elsewhere: no bricks at all (a density the
seed never rolls), no candle, no bats, the stone in dark grey and Tony in
grey, only the block number left in the floor, in black, a carving in the dark stone.
His own document, `THE-GLITCH.md`, has the full story.

### The image

Each token's image is the buddy alone, in his colour, doing the little
dance the game plays when a character stands still: an animated SVG built
from the game's sprite bytes, four frames switched in discrete steps, 1.8
seconds a loop, about 6 KB. The Glitch's cycles through the seven colours
on top. All eight exist by name in the repository and were verified frame
by frame in a browser. The contract will build the same file from a few
constants.

## 4. The collection, and the decision underneath it

The other design session is shaping a collection of 64: seven characters
times nine rooms, plus the Glitch. Nine rooms falls out naturally as three
wall densities by three bat states, with the candle present in all
sixty-three and positioned differently in each; rarity comes from how
many of each are cut.

This forces one decision that I want an advisor to see clearly, because it
is the hinge of the whole design. Today every variable except the
character is drawn from the block hash at render time: the wall, the
candle and the bats change at every fresh render, for every token. That is
lovely, and it means a token has no fixed traits. A 64-token collection
with rarities only makes sense if each token's room is its own, forever,
which means the contract stores a seed per token instead of reading the
block hash. My recommendation is a hybrid: the wall, candle and bats fixed
per token from a stored seed, and the block number in the floor still
written at render time, so each token keeps its own room and every render
remains a photograph of a moment. The program does not care either way; it
reads 32 bytes. Nothing in the engine changes with this decision.

## 5. How we think and work

- **Measure first.** Before designing the Dancer, I measured what the tune
  actually does frame by frame. Before placing the bats, I measured Tony's
  jump. Before choosing digit colours, I rendered the candidates on the
  floor. The ledger records every such number.
- **A scripted test per behaviour**, on the same emulator source that is on
  chain. The buddy's variables are found in the program by a byte
  signature, the joystick is driven, and the machine is read back every
  frame: the Echo's position must equal Tony's 200 frames earlier at every
  frame; the Dancer's path must be identical whether Tony stands or walks;
  the Shy One must never be caught while he can still run. There are
  scripted tests for all eight characters and for the bats over sixteen
  seeds. A program is shipped only when they pass.
- **Play-testing by the owner closes the loop.** Play found what tests did
  not think to ask: the Echo collapsing five quick jumps into two, the
  buddy jumping half as high as Tony, the crouch that was really Tony
  halfway up, the Wanderer never jumping, the Shy One's corner escape
  (found in play, kept on purpose, now asserted). Each became a test.
- **Keyless, immutable, fix-forward.** Once the base is on chain it never
  changes. Anything found later is fixed in new tokens. So the gates before
  any mint are: the automated suite passes on the frozen base, and the
  owner has played every character.
- **An experiment ledger** (`EXPERIMENTS.md`, sixteen entries) records what
  each experiment was for, what it produced, what it taught, and what is
  open, with a register of measured facts about the engine and the machine.
- **Rules for public text.** Credit the game's authors (MIT) and nopsta
  (GPL-2.0) in metadata; state plainly that nopsta stored the machine on
  Ethereum in 2022 and has since passed away and that this work was made
  after he was gone and independently of him; never describe the work as
  done on a dead man's machine or any wording of that shape; no year of
  death anywhere. The music is never modified. Nothing is pushed to or
  opened against the game's upstream repository.

## 6. The engineering, for those who need it

- **The base program** is a plain C64 PRG, 41,094 bytes, reproducible byte
  for byte from the repository. It carries a 64-byte-aligned parameter
  block with a marker; the contract writes 42 bytes after the marker: 32
  seed bytes, 8 block digits, the mechanic byte, the colour byte. Its
  current hash and offset are in the handoff; until the freeze, find the
  block by the marker.
- **The contract's job** at render time: take the base, write the 42
  bytes, hand the result to the READY 64 Launcher's `dataURI`, and build
  the JSON with name, description, attributes and the SVG image, all as
  `data:` URIs. It is a view; readers pay the gas. The handoff
  (`HANDOFF-CONTRACTS.md`) gives the contracts agent the exact bytes, the
  SVG, a Python reference to prove the output against, the deployment
  order, and the open decisions.
- **Storage.** The Tony token's three-blob pattern fits; 41 KB is two
  chunks. Per-token storage is a few bytes plus names and descriptions.
- **Verification before deployment.** For all tokens and several block
  values, the contract's bytes must equal the Python reference's; every
  produced program must run on the emulator harness; the SVG for each
  token must equal the reference file.

## 7. Where the other lines stand

- **Castles** (`ONCHAIN-CASTLES.md`): small castles as byte patches over
  the deployed game's bytes, with a room census and an engine-level edge
  guard, three verified samples. Paused in favour of the Chamber; it is the
  foundation for a later series where the room, not the buddy, is the
  subject, and the place where real danger and ladders belong.
- **Room builder**: proposed, not built.
- **Tony's original** stays untouched; everything here is a new program or
  a patch that never modifies the deployed bytes.

## 8. Risks and open questions, honestly

1. **Living rooms or fixed rooms** (section 4). Decides what a token is.
2. **Marketplace behaviour.** Metadata is cached and re-fetched on their
   schedule, so "every render" means every re-fetch; the image is an
   animated SVG, and a viewer that rasterises to a still shows the first
   frame (chosen to be the best one). Both should be measured on the
   marketplaces that matter, not assumed.
3. **The hash window.** A chain serves only the last 256 block hashes, so
   a living wall seen at block N cannot be recomputed on chain an hour
   later; renders are impressions, not a series. The fixed-seed design
   removes this for the rooms; the block number is fine either way.
4. **The launcher's `modes` value** is not known here and must be read
   from the deployed contract and confirmed on READY 64.
5. **Licences.** The game is MIT and credited. The emulator is GPL-2.0,
   was put on chain by its author, and the token page uses it in place
   rather than redistributing it, exactly as the existing Tony token does;
   a legal read on that arrangement would be prudent before a larger
   collection.
6. **The mint itself** (who, how, price, allowlist) is not designed here
   and is outside my remit.
7. **Fix-forward is unforgiving.** The play-through gate exists because a
   bug in a frozen base is permanent. The Echo's first cut was half wrong
   and only play found it.
8. **The freeze has been "one word away" for a while.** Each good idea
   since has been worth taking, and each moved the hash. At some point the
   owner names the build that ships.

## 9. Where I would want an advisor's view

- Living or fixed rooms, and whether the hybrid loses anything.
- The 64 grid: are three densities by three bat states the right axes,
  and how rare should heavy walls and empty nights be?
- Whether the Glitch should be the sixty-fourth or held back for a later
  moment.
- Sequencing: mint the Dancer first, or all at once.
- The licence arrangement in item 5 above.
- Anything about how a collector reads a token whose room is a photograph
  of a block: is the render-time number in the floor a feature to lead
  with or a footnote?

## 10. Where everything is

Repository `DeMEdPit/tony-demo`, branch `claude/tony-c64-demo-expert-wp40it`,
folder `deliverables/`:

| file | what |
|---|---|
| `README.md` | the map of every program and document |
| `EXPERIMENTS.md` | the ledger: sixteen experiments, decisions, measured facts, the plan |
| `HANDOFF-CONTRACTS.md` | for the contracts agent |
| `THE-GLITCH.md` | the eighth token and the thinking behind it |
| `ONCHAIN-CASTLES.md` | the castles line |
| `prg/minimal64/tony-chamber.prg` | the base program; `tony-chamber-the-<name>.prg`, one stamped program per token |
| `assets/tokens/the-<name>.svg` | the eight token images; sheets and screenshots alongside |
| `../tools/` | the generators, the stamp tool, the tests, the emulator harness built from nopsta's source |

## Credits

Tony: Born for Adventure, code Maciej Małecki, graphics Rafał Dudek, music
Sami Juntunen, all MIT. Runtime: minimal64 by nopsta, GPL-2.0. nopsta
stored the machine on Ethereum in 2022 and has since passed away; this
work was made after he was gone and independently of him.
