# Handoff note: The Glitch's tune (for the agent writing the contracts)

Companion to `HANDOFF-CONTRACTS.md`. Everything in that document still
holds; this note covers one change the owner is trying: **The Glitch plays
the demo's other tune.** Nothing about the parameter block, its offset, the
SVGs or the metadata changes. What changes is *which base program the Glitch
token points at*, or, if the second shape below is chosen, the base itself.

## 1. What the change is

Tony's demo has two pieces of music, both by Sami Juntunen (MIT, credit
required): the level tune, which every Chamber build plays, and the intro
tune, which the full game plays over its intro scroller and which no
Chamber build had ever played. The intro tune was assembled for memory the
Chamber uses for its sprites, so it was **relocated** into the Chamber's
music slot: `tools/sidreloc.py` runs the tune in a tag-tracking 6502 and
changes only the 289 bytes (of 5,782) that serve as the high byte of an
address inside the tune. `tools/verify_reloc.py` then played the original
and the copy for 24,000 frames (eight minutes) and every write to the sound
chip matched. No note, instrument or timing differs. The relocated file is
`src/music/TonyIntroA000_reloc.sid`, its provenance in
`src/music/RELOCATION.md`.

A second base program carries it: the same engine, the other tune. Because
the intro tune is faster and its lead voice would keep the Dancer in the
air, the Dance mechanic in that base steps to the tune's second voice and
keeps a short pause after each landing (about one bounce a second). The
Glitch cycles through the seven mechanics, so this is what his Dance phase
does under the new tune. The blackout, teleports, colour cycling and bursts
are unchanged; the Glitch test passes on the new base.

## 2. The two bases

| | base 2 (seven tokens) | base 2-intro (the Glitch) |
|---|---|---|
| file | `deliverables/prg/minimal64/tony-chamber.prg` | `deliverables/prg/minimal64/tony-chamber-intro.prg` |
| size | 41,094 bytes | 41,368 bytes |
| sha256 | `f9f7225f507c954f50c43f557643039d6f7bd59b2520ecc4dde82c845ad1e262` | `170789a970c7b30a6b4283c3fdf5fa092a703eb907cab39db7d6cb74237c24b9` |
| tune | level tune | intro tune, relocated |
| marker `"MURAL02\0"` at file offset | `0x04EC1` | `0x04EC1` |
| the 42 bytes the contract writes | file offset `0x04EC9` | file offset `0x04EC9` |
| rebuild | `python3 tools/make_chamber.py` | `python3 tools/make_chamber.py --music src/music/TonyIntroA000_reloc.sid --variant tony-chamber-intro --dance-voice 2 --dance-cool` |

Both carry the blackout's block number in black (the owner's choice of 2026-09-07; the same byte in both bases, so the hashes above are the current ones). Both come out of `./gradlew build -x downloadDeps` (ignore the exomizer
failure at the end) at `src/kickass/<name>.prg`, byte for byte. The block
is at the same offset in both because it lives in the code segment, before
the music data; still find it by its marker, never by a fixed offset, until
the freeze.

Neither base is frozen. The seven-token base has been feature complete for
a while; the intro base is days old and the owner is still listening.

## 3. What you would do with it

Two shapes are possible. **The owner has not chosen**; this note exists so
the choice is an informed one.

**Shape A, two bases.** The seven tokens render from base 2; the Glitch
renders from base 2-intro. The contract stores both PRGs and the Glitch's
`tokenURI` writes the same 42 bytes at the same offset into the second one.
Simplest to write and to prove. Costs one more stored program (41,368
bytes) and gives the collection two base hashes instead of one.

**Shape B, one base carrying both tunes.** The engine has 14,847 bytes free
at run time below the music slot, enough for the second tune. Behaviour 7
would start the intro tune, the other seven the level tune, and the Dance
mechanic would pick its voice and pause by behaviour at run time. One
program of about 46,900 bytes, one hash, one `tokenURI` path; roughly
35 KB less to store on chain than Shape A. Not built; a few hours of engine
work plus re-running every mechanic test, and it changes the seven-token
base's hash once (it is not frozen, so that is allowed).

Recommendation from this side: Shape B if the tune is confirmed, because
the whole collection then stays "one immutable program, one block per
token". Shape A is the fallback if the contracts need to move before the
engine work is done: nothing in Shape A is wasted, the Glitch base simply
becomes the second stored program.

## 4. What does not change

- The parameter block: 42 bytes at `marker + 8`, seed then digits then
  behaviour then colour, exactly as in `HANDOFF-CONTRACTS.md` section 4.
- The Glitch's behaviour byte (7), colour handling, blackout and thumbnail.
- The SVG images and the metadata fields.
- The proof plan in section 7 of the main handoff: a test that writes a
  known block into either base and checks the wall against
  `tools/stamp_mural.py --show` works unchanged on the intro base.

## 5. Public text

Credit Sami Juntunen for both tunes (MIT). If the metadata names the music,
"the intro tune of Tony" is accurate; do not describe it as new music. The
rest of the public-text rules in section 1 of the main handoff apply as
written.

## 6. To hear it

`deliverables/audio/the-glitch-intro-tune-40s.wav` and
`the-glitch-level-tune-40s.wav` are forty seconds of each Glitch build,
rendered by the emulator's own SID (22 kHz mono). The playable files are
`deliverables/prg/minimal64/tony-chamber-intro-the-glitch.prg` (intro tune)
and `tony-chamber-the-glitch.prg` (level tune).
