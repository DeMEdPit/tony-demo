# The Glitch: the eighth token, and how it came to be

Written 2026-09-06, from the `DeMEdPit/tony-demo` repository. A summary of
the Glitch mechanic and token and of the thinking around it, for sharing.
Everything here was built and measured on the emulator that lives on
Ethereum; the numbers are from those runs.

## What it is, in one paragraph

The Chamber is one room of Tony: Born for Adventure with two Tonys in it:
Tony, whom you play, and a buddy who behaves according to his token. Seven
tokens give the buddy seven characters: the Shadow, the Dancer, the Echo,
the Mirror, the Wanderer, the Shy One, the Sleeper. The Glitch is the
eighth. He is the same buddy, in the same slot, but nothing about him holds
still: he wears one of the seven characters at a time and teleports into
the next every few seconds, he cycles through the seven tokens' colours,
and in bursts he blinks out, jitters and flashes random colours. His room
is the blackout, which no other token can produce: no bricks on the wall,
no candle, no bats, the stone in dark grey, Tony in grey, and only the
block number left carved in the floor.

## How the idea arrived

It started as a question about scenery. The bats had just become part of
the render: each render draws from the block hash which of eight flight
paths each bat flies, where it starts, how high, and whether it is there at
all, with a quiet night of no bats one render in sixteen. The owner noticed
that a night with no bats leaves two sprites idle, and a Tony is exactly
two sprites tall. So: a third Tony on the bat sprites, in the rarest
renders. A glitch Tony, cycling colours, picking a character at random.

The first assessment said yes, possible, and costly: the buddy code runs
one buddy, so a second needs its state saved and restored around a second
update every frame, the sprite registers made selectable, the collision
rule taught that the bat sprites are no longer enemies, and a second memory
for the Echo. One to two sessions, and it had to be decided before the base
program was frozen, because after the freeze these tokens never change.

Then the collection took shape in another session: sixty-four tokens,
seven characters times nine rooms, plus one. That changed the answer. If
the Glitch is a token of his own, he does not need to be a third character
at all. He is that token's buddy, in the ordinary slot, wearing the seven
characters in turn. No second buddy, no bat sprites, none of the plumbing.
He was built that way in an afternoon, with a scripted test, and every
later refinement was a small change on top.

## What he does

- **Wears the seven.** Every 150 to 405 frames (three to eight seconds) he
  rolls a new character on the same dice the Wanderer uses, a shift
  register stirred every frame by the sound chip's third oscillator. The
  characters that keep state start afresh at each change. An Echo turn
  replays whatever his memory holds, which may be you from minutes ago.
- **Teleports.** Every change of character is a teleport: he blinks out for
  twelve frames and is somewhere else between the pillars when he comes
  back, the spot from the dice. One burst in eight is a teleport too, so he
  sometimes vanishes mid-character and reappears across the room still
  doing the same thing. He never lands outside the pillars.
- **Cycles the colours.** One of the seven token colours every eight
  frames: blue, cyan, yellow, light blue, green, light red, purple.
- **Bursts.** About once every 85 frames, a burst of 8 to 15 frames: his
  colour goes random, he blinks out one frame in four, and he jitters a
  pixel sideways, short of the pillars.

Measured over thirty seconds: six changes of character, five of them
teleporting, thirteen teleports in all, every non-black colour seen, 183
frames blinked out of 1,500, and he ranged from one pillar to the other.

## The blackout

The room is gated on his mechanic byte, not on the seed, so no ordinary
token's room can ever look like it. The wall gets a fifth density that the
seed never rolls, none at all; the candle is skipped; both bats are hidden;
the block number is still carved.

Two choices were made on evidence. Bare rather than full density: the
densities run from sparse to heavy and never to zero, so a bare wall is
exclusively his, while a full wall remains the rare ordinary room. And the
colours: the stone went from light grey to dark grey and Tony from light
grey to grey, one step lighter than the stone so he still reads against the
pillars. The block number is carved as dark strokes into the stone, and
dark strokes on dark grey would nearly vanish, so its eight cells keep light
grey ink, which flips them to bright numerals on dark stone. Rendered side
by side, black digits on the dark floor were readable but murky; the light
ones are clear. The number briefly wore the Glitch's colour, cycling with
him, and the owner chose to leave it alone: light grey throughout.

A related question was answered the same way for the other seven. Should
their block numbers take the buddy's colour? Rendered on the light grey
floor, black digits are crisp, purple readable, yellow and cyan poor. A
coloured number would work for half the palette and break the room's rule
that the buddy is the only colour in it. The seven keep black digits.

## The thumbnail

Each token's image is the buddy alone, doing the little dance the game
plays when a character stands still, as an animated SVG built from the
game's own sprite bytes. The Glitch's is the same file with one addition:
the fill cycles through the seven token colours, one every 0.4 seconds, a
full rainbow in 2.8 seconds against the 1.8 second dance, so the two drift
against each other rather than repeating in step. Verified in a browser
colour by colour. All eight thumbnails now exist by token name, in the
repository under `deliverables/assets/tokens/`.

## What it means for the contract

Nothing in the block format changes. The Glitch is mechanic byte 7 in the
same 42 bytes the contract writes; his colour byte is ignored, since he
cycles the seven. The blackout follows from the mechanic byte inside the
program. His image is one more animation line per path in the same SVG.
The base program grew to 41,094 bytes, and the handoff carries the current
hash and block offset. One decision does remain open and is not his: with
a 64-token collection, the rooms' seeds are stored per token rather than
read from the block hash, and the recommendation is a hybrid in which the
wall, candle and bats are fixed per token and the block number in the
floor still ticks with the chain.

## Also in this stretch

- The bats joined the render, as above, with a safety rule measured
  exhaustively: on every path, every row and every column pair the lowest
  bat stays 30 pixels above the top of Tony's jump, and the two bats never
  come within 32 pixels of each other. They are scenery, never a danger,
  so the game's death, lives and game-over screen stay out of the token.
- The Mirror became contrary in every axis: he crouches while you jump,
  bounces while you crouch, and faces the way your reflection would at
  every frame, so a turn in place while crouched flips him too.
- The Shy One bolts straight past you when you are almost on him in the
  corner, rather than only once you have squeezed past.
- The Wanderer jumps now and then, on the same dice as everything else he
  does.
- Every buddy jumps with Tony's exact measured arc, and crouches all the
  way down.

## Credits

Tony: Born for Adventure, code Maciej Małecki, graphics Rafał Dudek, music
Sami Juntunen, all MIT. Runtime: minimal64 by nopsta, GPL-2.0. nopsta
stored the machine on Ethereum in 2022 and has since passed away; this
work was made after he was gone and independently of him.

## An open question: his own tune

The demo has one other piece of music, the tune of the intro scroller,
which no Chamber build has ever played. It is faster and denser than the
level tune, about 107 beats a minute against a slow 75, with runs and
arpeggios on two voices and a filter sweeping under the third. It was
written for a different part of memory, so it has been moved into the
Chamber's music slot with a tool that changes only the addresses inside
the player, and the move was proved by playing both copies for eight
minutes and comparing every write to the sound chip. Under it the Glitch
is the same Glitch in the same blackout, but when he blinks in as the
Dancer the faster music changes him: the lead line's attacks would keep
him in the air nearly all the time, so the build for this tune has him
step to the steadier second voice and rest a moment after each landing,
about one bounce a second. Whether he takes the tune at all, and whether
moving a tune counts as changing the music, are the owner's calls; the
builds exist to listen to (`tony-chamber-intro-the-glitch.prg`).
