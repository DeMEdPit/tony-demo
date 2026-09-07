# The token thumbnails: the retro layout (design log)

Where the thumbnail design stands, what has been decided, and what is still open.
Everything here is mock-up work: the eight token SVGs in `deliverables/assets/tokens/`
are still the earlier idle-dance design, and nothing in this log touches the frozen
base PRG, the vectors or the freeze record. Mock files live in
`deliverables/assets/mock/` and `deliverables/screenshots/mock-retro-*`.

Dates are 2026-09-07 unless given.

## 1. The layout (decided)

A 48 x 48 card, black, in three parts, all on the C64's 48-pixel grid:

- **The tag.** The seven token colours as seven 2 x 2 squares straight across the top
  left, at y = 2, starting at x = 2, a half pixel apart (pitch 2.5). Drawn anti-aliased
  so the half-pixel gap stays even at any display size (crisp rendering snapped it to
  alternating 13 and 12 screen pixels at 240 px).
- **The buddy.** The idle dance from the earlier design, centred: 24 wide, 32 ink rows,
  at x = 12, y = 5, his feet on the floor's top row. The hat clears the tag by a pixel.
  Placement uses the ink height (32), not the 42-row frame.
- **The floor.** Eleven rows (y 37..47), a dithered gradient from the buddy's own colour
  down to black, dithered on a half-pixel grid (96 x 22 cells) with a 4 x 4 ordered
  matrix. Eleven rows is the most the card allows with the figure clear of the floor.

Ramps, top to bottom (palette indices): Shadow 6 0 · Dancer 3 14 6 0 · Echo 7 8 9 0 ·
Mirror 14 6 0 · Wanderer 5 11 0 · Shy 10 2 9 0 · Sleeper 4 6 0. The top row is always
the body colour, so the buddy stands on his own colour.

## 2. Motion (decided)

- **The dance** is the existing idle loop, 1.8 s, unchanged.
- **The own square breathes**: opacity 0.45 to 1 and back over 3.6 s (two dance loops),
  eased, with a blurred glow copy (0 to 0.9). The other six squares rest at 0.45 so the
  live one reads as a square waking up out of the row.
- **Resting level 0.45** for every token (chosen from 0.6, 0.45, 0.3).

## 3. The Glitch (decided, one choice open)

- **Body: white with static.** Once per breath, at 1.20 to 1.54 s, ten quick flips
  between light grey, white and grey, then white again. The blink from the earlier
  design stays.
- **Tag: the sweep.** Once per breath a wave of light runs straight across the row:
  square i peaks at 0.3 + 0.15 i seconds, rises in 0.05 s and fades over 0.45 s
  (the "comet", a 1.0 s tail, was mocked and not chosen).
- **Floor: grey.** White, light grey, grey, dark grey, black (1 15 12 11 0).
- **Open: white or dark.** The alternative is a dark grey body (11) on a dark grey to
  black floor, the room with the lights out, the bar the only real colour. At a true
  48 px on a dim screen he can vanish; the white version reads everywhere.
- Not chosen: the seven-colour cascade body (the earlier design), the spectrum,
  luminance and following floors, and the other start colours.

## 4. Open small items

- **The order of the seven squares.** Now round the colour wheel, warm to cool: light
  red, yellow, green, cyan, light blue, blue, purple. The alternatives are the token
  roster (Shadow blue, Dancer cyan, Echo yellow, Mirror light blue, Wanderer green,
  Shy light red, Sleeper purple), which makes the bar an index of the collection, or
  brightest first. Sheet: `mock-retro-tag-order-strip.png`.
- **The Shadow's floor** has only blue and black, so it is a single fade.
- **The Wanderer's floor** falls through dark grey before black; the others go
  straight to black.

## 5. Sizes

| SVG | Earlier design | Retro layout |
|---|---|---|
| The seven | 6,056 bytes each | about 17.7 KB each |
| The Glitch | 6,842 bytes | about 22.9 KB (white, static, sweep) |

The floor on the half-pixel grid is most of the growth (the whole-pixel floor is about
10 KB per card). The contracts session should hear the size before it decides how the
image is stored.

## 6. Taste notes from the owner

"Not packed tight, just a hair closer" (the gap). "More detailed dithering and more
gradient" (the floor). "White top, then grey, then dark" (the Glitch's floor). The
sweep "goes across kind of quick, then lingers and goes away, but not immediately".
The static and flicker: keep.

## 7. When the design is adopted

1. Generate the eight real token SVGs from `tools/buddy_retro_svg.py` with the chosen
   options (or port the layout into `tools/buddy_thumbnail.py`), into
   `deliverables/assets/tokens/`.
2. Verify: well-formed XML; in Chromium, seek the SVG clock and check the dance
   phases, the breath (peak at 1.8 s), the sweep, the static burst and the blink;
   render at 48, 96 and 240 px.
3. Update `HANDOFF-CONTRACTS.md` section 6 (shape and sizes) and tell the contracts
   session the image and its size changed. The PRG, the vectors and the freeze are
   unaffected.

## 8. Regenerating the mocks

```
python3 tools/buddy_retro_svg.py --floor deep-fine --tag-gap 0.5 --tag-dim 0.45 \
    --tokens the-shadow the-dancer the-echo the-mirror the-wanderer the-shy the-sleeper \
    --lineup deliverables/screenshots/mock-retro-fine-lineup-gap0.5.png
python3 tools/buddy_retro_svg.py --floor deep-fine --tag-gap 0.5 --tag-dim 0.45 --tokens the-glitch \
    --glitch-floor grey --glitch-body static --glitch-tag sweep --gif deliverables/screenshots/mock-retro-grey --fps 20 --seconds 7.2
```
Other sheets: `--tag-strip`, `--dim-strip`, `--order-strip`, `--glitch-sheet`.
