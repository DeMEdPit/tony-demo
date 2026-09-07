# The Glitch's tune: the record (for the agent writing the contracts)

Companion to `HANDOFF-CONTRACTS.md`, section 4a. This note records how the
demo's second tune got into the base and what was proved on the way, so
that nothing here has to be taken on trust.

## 1. The decision

The Glitch alone plays the intro tune, the music of the full game's intro
scroller, which no Chamber build had played before. The seven other tokens
keep the level tune. The Dancer was tried on the intro tune and dances worse
to it (7 ground steps in 18 s against 42; airborne 55% against 33%), so the
tune is the Glitch's and nobody else's. The owner chose this on 2026-09-07
after listening to both builds.

## 2. One base, both tunes

There is one base program for all 64 tokens, `tony-chamber.prg`, 46,876
bytes, sha256
`d45a129aab3ad60d79b3972f1d3047b99e425a3a8845fead9cf2d67401abd7ef`. It
carries the level tune at $A000 (as every Chamber build did) and the intro
tune at $8000–$9695, a region the engine never writes at run time
(measured over 3,000 frames of play: zero bytes changed in $6600–$9FFF).
At boot the engine starts the tune the behaviour byte asks for: 7 the
intro tune, anything else the level tune; the same choice routes the
once-a-frame play call. The parameter block is unchanged (42 bytes at
`marker + 8`, file offset 0x04EC9 in this build) and the contract does
nothing extra for the tune: writing behaviour 7 is enough.

The two-base alternative (a second program for the Glitch) was built and
tested first and then retired: one program, one hash, one `tokenURI` path,
and about 35 KB less to store on chain.

## 3. The relocation, and its proof

The intro tune was assembled for $E000, where the Chamber keeps its
sprites. `tools/sidreloc.py` runs the tune in a tag-tracking 6502 and
changes only the bytes that serve as the high byte of an address inside the
tune: 289 of 5,782, no byte also used as data, index, low byte or an outside
address. `tools/verify_reloc.py` then played the original at $E000 and the
copy at $8000 for 24,000 frames (eight minutes) on the emulator and compared
every SID register write: identical. No note, instrument or timing differs.
The file is `src/music/TonyIntro8000_reloc.sid`; the original stays beside
it; `src/music/RELOCATION.md` has the commands. Credit Sami Juntunen for
both tunes (MIT); if the metadata names the music, "the intro tune of Tony"
is accurate, and it is not new music.

## 4. The Glitch's Dance phase

The Dance mechanic steps on a voice's note changes and bounces on the third
voice's envelope rises. The intro tune's first voice is an arpeggio nearly
every frame and its third voice a fast lead whose every attack counts as a
hit, so the Dance mechanic as written for the level tune would keep the
Glitch in the air 99% of the time, never stepping. In the one base, when
behaviour is 7 the Dance mechanic reads the intro tune's second voice and
keeps the engine's twenty-frame pause after a landing. Measured in his
Dance phase: airborne 59%, about one bounce a second, shuffles and turns
between. The Dancer token's code path is untouched (measured after the
change: 42 steps, 17 turns, 13 hops, airborne 33% in 18 s, as before).

## 5. What was verified on the one base

- All eight mechanic tests pass (`tools/verify_buddy.py`), including new
  checks that the Glitch's build plays the intro tune and not the level
  tune, that the Dancer's plays the level tune and not the intro tune, and
  that the Glitch's Dance phase lands.
- The bats over sixteen seeds pass (`tools/verify_bats.py`).
- The register stream of the Glitch build on the emulator uses 23
  instrument settings and 80 notes, all of the intro tune's; the Dancer's
  uses 12 and 79, all of the level tune's. Forty seconds of each are in
  `deliverables/audio/`.

## 6. What the contract does about it

Nothing. Store the one base, write the 42 bytes, and The Glitch's token
writes behaviour 7 like any other token writes its mechanic.
