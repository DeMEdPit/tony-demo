# The token thumbnails: the retro layout (design log)

**Frozen 2026-09-07 at commit `9880f03e5330605b1246acba63fc9671f5935d88`.** The eight
files in `deliverables/assets/tokens/` do not change after this commit, as the base
does not after `21b95e3`; a change would be a new named commit, declared by the owner.
Record: `deliverables/contract/tokens-record.json` (sizes, sha256, keccak256);
checker output at the freeze: `deliverables/contract/tokens-verify.txt`.

**Status: adopted 2026-09-07.** The eight token files in `deliverables/assets/tokens/`
are this design, written by `tools/buddy_retro_svg.py --final` and verified by
`tools/verify_tokens.py`. `deliverables/assets/tokens-sheet.png` shows all eight;
`deliverables/assets/tokens-preview-<name>.gif` are previews (the Glitch's steps
through his bursts at 20 ms). `HANDOFF-CONTRACTS.md` section 6 describes the files
for the contract. Nothing here touches the frozen base PRG, the vectors or the freeze.
The mock-ups that led here are in `deliverables/assets/mock/` and
`deliverables/screenshots/mock-retro-*`; the earlier buddy-alone design
(`tools/buddy_thumbnail.py`, `assets/buddy-idle-*.svg`) is superseded but kept.

## 1. The card

A 48 x 48 black canvas, everything on the C64's 48-pixel grid:

- **The tag.** The seven token colours as seven 2 x 2 squares straight across the top
  left, at y = 2, x = 2 + 2.5 i: a half-pixel gap, drawn anti-aliased so it stays even
  at any display size. Order, left to right: blue, yellow, purple, green, light red,
  cyan, light blue. That is three pairs of opposites side by side (blue and yellow,
  purple and green, light red and cyan) with green in the middle, ending on the
  lightest cool colour. Each buddy's own square therefore sits in a different place:
  Shadow first, Echo second, Sleeper third, Wanderer fourth, Shy fifth, Dancer sixth,
  Mirror seventh.
- **The buddy.** The game's idle dance, centred: 24 wide, 32 ink rows, at (12, 5), his
  feet on the floor's top row, his hat a pixel clear of the tag.
- **The floor.** Eleven rows (37 to 47), a dithered gradient from the buddy's own
  colour down to black, dithered on a half-pixel grid (96 x 22 cells, a 4 x 4 ordered
  matrix). The top row is always his colour, so he stands on his own colour.

Floor ramps, top to bottom: Shadow blue, black · Dancer cyan, light blue, blue, black ·
Echo yellow, orange, brown, black · Mirror light blue, blue, black · Wanderer green,
black · Shy light red, red, brown, black · Sleeper purple, black. The floors follow the
supply ladder (decided 2026-09-07): the three commons at 12 each, the Shadow, the
Wanderer and the Sleeper, have a single fade from their colour to black; the three at
8 each, the Echo, the Mirror and the Shy, have two or three steps; the Dancer and the
Glitch have three. The Wanderer's single fade was chosen from six mock-ups (the palette
has no darker green, so green dithered with black stays green all the way down); the
Sleeper's followed to complete the rule.

## 2. Motion

- **The dance** is the existing idle loop, 1.8 s, unchanged.
- **The tag rests at 0.3** and the buddy's own square breathes: 0.3 to 1 and back over
  3.6 s (two dance loops), eased, with a blurred glow copy beneath (0 to 0.9). At the
  peak the square is exactly its palette colour; its neighbours pick up a faint halo.

## 3. The Glitch

The room with the lights out: a dark grey body on a floor that runs light grey, grey,
dark grey, black. Three things happen to him, on periods that drift against each other:

- **The blink** (every 2.6 s): out for 80 ms, back for 40 ms, out again for 80 ms.
- **Static** (every 3.6 s, from 1.20 to 1.54 s): ten quick flips between grey, dark
  grey and a colour. The two colour flips (30 ms, then 20 ms) are dealt from a fixed
  sequence, each of the seven colours twice over seven bursts, never the same twice
  running, so the fill's period is 25.2 s and the sparks read as chance.
- **The sweep** (every 3.6 s): a wave of light across the seven squares, each peaking in
  turn at 0.3 + 0.15 i seconds, rising in 50 ms and fading over 450 ms, a glow under each.

## 4. Sizes

| file | bytes |
|---|---|
| the-dancer.svg, the-echo.svg, the-shy.svg | 17,727 to 17,729 |
| the-mirror.svg | 17,684 |
| the-shadow.svg, the-wanderer.svg, the-sleeper.svg | 13,958 to 13,960 |
| the-glitch.svg | 25,000 |

Base64, as a data URI: about 18.6 KB, 23.6 KB and 33.3 KB. The earlier files were
6,056 and 6,842 bytes; the half-pixel floor is most of the growth.

## 5. Verification

`tools/verify_tokens.py` opens each file in Chromium, pauses the SVG clock and seeks
it: body colour at rest, the floor's top row, the seven squares in order at 0.3, the
own square at full colour at 1.8 s with the others resting, the four dance frames; for
the Glitch the sparks at 1.28, 1.46, 4.88, 8.48 and 8.66 s, the blink out at 2.40 s and
back at 2.48 s, and the sweep on the middle square at 0.78 s and the last at 1.25 s.
68 checks, all passing on 2026-09-07.

## 6. How it was decided

Ten rounds of mock-ups, PNG then animated SVG, each a look-see that touched nothing
frozen. The owner's choices in order: the tag straight across, not stacked; the buddy
centred with his feet flush on the floor; "more detailed dithering and more gradient"
(the eleven-row, half-pixel floor); the squares "just a hair closer" (0.5 px), drawn
evenly; a dimmer resting row so the pulse shows (0.45, then 0.3); the Glitch grey
rather than cascading, then dark, "since he's in a blacked-out room", on a lighter
floor; the static with its flicker kept; the sweep ("goes across quick, then lingers
and goes away, but not immediately"); the lighter-grey flips of the static made into
colour sparks; and the bar order with green in the middle, ending on light blue.
Not chosen: badge, square and bar layouts, palette columns, a halo, the seven-colour
cascade body, the spectrum, luminance and following floors, the comet trail, other
start colours, the roster and luminance orders.

## 7. Regenerating

```
python3 tools/buddy_retro_svg.py --final --lineup deliverables/assets/tokens-sheet.png --still 1.8
python3 tools/buddy_retro_svg.py --final --gif deliverables/assets/tokens-preview --burst-gif
python3 tools/verify_tokens.py
```
The decisions are the `FINAL` and `FINAL_GLITCH` constants in `tools/buddy_retro_svg.py`;
every other option of the tool is for mock-ups.
