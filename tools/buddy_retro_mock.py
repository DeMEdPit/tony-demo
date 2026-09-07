#!/usr/bin/env python3
"""
buddy_retro_mock.py - PNG mock-ups of a token image in the old paint-program style: the buddy,
a dithered gradient in his colour, and the seven-colour strip. Not SVGs, not the token files.
Everything is drawn on a 48x48 grid (the token's real size) and shown at 5x, 2x and 1x.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buddy_thumbnail as bt
from PIL import Image, ImageDraw

PAL = {0: "#000000", 1: "#ffffff", 2: "#813338", 3: "#75cec8", 4: "#8e3c97", 5: "#56ac4d", 6: "#2e2c9b", 7: "#edf171",
       8: "#8e5029", 9: "#553800", 10: "#c46c71", 11: "#4a4a4a", 12: "#7b7b7b", 13: "#a9ff9f", 14: "#706deb", 15: "#b2b2b2"}
def rgb(i): h = PAL[i]; return tuple(int(h[k:k + 2], 16) for k in (1, 3, 5))
# the seven tokens: colour index, and a ramp (top to bottom) for the gradient, ending in black
TOKENS = {"the-shadow": (6, [14, 6, 0]), "the-dancer": (3, [1, 3, 14, 6, 0]), "the-echo": (7, [1, 7, 8, 9, 0]),
          "the-mirror": (14, [3, 14, 6, 0]), "the-wanderer": (5, [13, 5, 0]), "the-shy": (10, [1, 10, 2, 9, 0]),
          "the-sleeper": (4, [10, 4, 6, 0])}
STRIP = [10, 7, 5, 3, 14, 6, 4]           # warm to cool, the seven token colours
BAYER = [[0, 2], [3, 1]]                    # 2x2 ordered dither thresholds (0..3)

def dither_column(width, height, ramp):
    """A vertical gradient through the ramp's colours, mixed by 2x2 ordered dither: a list of rows of palette indices."""
    rows = []
    bands = len(ramp) - 1
    for y in range(height):
        t = y / max(1, height - 1) * bands           # position along the ramp
        i = min(int(t), bands - 1); f = t - i        # between ramp[i] and ramp[i+1], f in 0..1
        level = int(f * 4)                           # 0..3 : how much of the next colour
        row = []
        for x in range(width):
            row.append(ramp[i + 1] if BAYER[y % 2][x % 2] < level else ramp[i])
        rows.append(row)
    return rows

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]   # 4x4 ordered dither, 16 levels

def dither_column_fine(width, height, ramp):
    """As dither_column, with the 4x4 matrix: sixteen mixing levels between each pair of colours."""
    rows = []
    bands = len(ramp) - 1
    for y in range(height):
        t = y / max(1, height - 1) * bands
        i = min(int(t), bands - 1); f = t - i
        level = int(f * 16)
        rows.append([ramp[i + 1] if BAYER4[y % 4][x % 4] < level else ramp[i] for x in range(width)])
    return rows

def glow_mask(width, height, cx, cy, r):
    """A dithered halo: density falls off with distance; returns rows of 0/1."""
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            d = ((x - cx) ** 2 + ((y - cy) * 1.0) ** 2) ** 0.5
            level = 4 - int(min(4, max(0, (d / r) * 4)))       # 4 near the centre .. 0 outside
            row.append(1 if BAYER[y % 2][x % 2] < level and level > 0 else 0)
        rows.append(row)
    return rows

def draw(frames, token, variant, size=48):
    colour, ramp = TOKENS[token]
    im = Image.new("RGB", (size, size), rgb(0)); px = im.load()
    frame = frames[bt.PHASES[0]]
    fw = len(frame[0])
    fh = bt.ink_box(frames)[1] + 1                 # the figure's real height (32): the frame data carries ten blank rows below the feet
    strip_h = 7
    def put_strip(y0):
        for i, c in enumerate(STRIP):
            for x in range(size): px[x, y0 + i] = rgb(c)
    def put_column(x0, w, y0, h, ramp):
        col = dither_column(w, h, ramp)
        for y in range(h):
            for x in range(w): px[x0 + x, y0 + y] = rgb(col[y][x])
    def put_figure(fx, fy, c):
        for y, row in enumerate(frame):
            for x, v in enumerate(row):
                if v and 0 <= fx + x < size and 0 <= fy + y < size: px[fx + x, fy + y] = rgb(c)
    if variant == "left-bottom":       # gradient column left, strip along the bottom, the buddy standing on it
        put_strip(size - strip_h)
        put_column(0, 10, 0, size - strip_h - 1, ramp)
        put_figure(size - fw - 3, size - strip_h - 1 - fh, colour)
    elif variant == "left-top":        # strip at the top like a palette bar, gradient left, the buddy on the floor line
        put_strip(0)
        put_column(0, 10, strip_h + 1, size - strip_h - 1, ramp)
        put_figure(size - fw - 3, size - 1 - fh, colour)
    elif variant == "thin":            # thinner everything: a 4-wide gradient, 1-px stripes with a black line between
        for i, c in enumerate(STRIP):
            for x in range(size): px[x, size - 14 + i * 2] = rgb(c)
        put_column(0, 4, 0, size - 15, ramp)
        put_figure((size - fw) // 2 + 2, size - 15 - fh, colour)
    elif variant == "halo":            # the dithered sphere idea: a halo in the token's colour behind the buddy, strip at the bottom
        put_strip(size - strip_h)
        cx, cy = size // 2, (size - strip_h) // 2
        halo = glow_mask(size, size - strip_h - 1, cx, cy + 4, 22)
        dark = ramp[-2] if ramp[-2] != colour else 11      # the ramp's darkest colour above black (dark grey for the Shadow, whose ramp ends on himself)
        for y, row in enumerate(halo):
            for x, v in enumerate(row):
                if v: px[x, y] = rgb(dark)
        put_figure((size - fw) // 2, size - strip_h - 1 - fh, colour)
    elif variant == "gradient-back":   # the whole background a dithered gradient from the colour's dark end up to black, strip bottom
        put_strip(size - strip_h)
        put_column(0, size, 0, size - strip_h - 1, [0, ramp[-2] if ramp[-2] != colour else 11])
        put_figure((size - fw) // 2, size - strip_h - 1 - fh, colour)
    if variant.startswith("swatch"):    # seven colour squares down the left; the gradient is the floor he stands on
        floor_h = 8
        floor_ramp = [c for c in ramp if c != 1] or ramp          # the floor starts on his colour, not on white
        if "halo" in variant:
            cx, cy = 8 + (size - 8) // 2, (size - floor_h) // 2 + 2
            halo = glow_mask(size, size - floor_h, cx, cy, 20)
            dark = ramp[-2] if ramp[-2] != colour else 11
            for y, row in enumerate(halo):
                for x, v in enumerate(row):
                    if v and x >= 8: px[x, y] = rgb(dark)
        if "across" in variant:                                    # the floor's gradient runs left to right
            band = dither_column(floor_h, size, floor_ramp)         # built as a column, then turned on its side
            for y in range(floor_h):
                for x in range(size): px[x, size - floor_h + y] = rgb(band[x][y])
        else:                                                      # the floor's gradient runs down: his colour at his feet, black at the edge
            band = dither_column(size, floor_h, floor_ramp)
            for y in range(floor_h):
                for x in range(size): px[x, size - floor_h + y] = rgb(band[y][x])
        for i, c in enumerate(STRIP):                              # the swatches: 4x4, a pixel apart
            y0 = 2 + i * 5
            for y in range(4):
                for x in range(4): px[1 + x, y0 + y] = rgb(c)
            if "marked" in variant and c == colour:                # the token's own square framed in white
                for k in range(-1, 5):
                    for (xx, yy) in ((k, -1), (k, 4), (-1, k), (4, k)):
                        if 0 <= 1 + xx < size and 0 <= y0 + yy < size: px[1 + xx, y0 + yy] = rgb(1)
        put_figure(8 + (size - 8 - fw) // 2, size - floor_h - fh, colour)
    if variant.startswith("tag"):       # the buddy centred on a finer-dithered floor; the seven colours as a small tag top left
        floor_h = 8                      # eight rows of floor: his hat then clears the tag by a row even when he rises
        floor_ramp = ramp[ramp.index(colour):]                     # the floor starts on his own colour and falls to black
        if "deep" in variant: floor_h = 11                         # eleven rows: the most the grid allows under the tag and the hat
        if "lit" in variant:                                       # a lighter row at the top edge, the light catching the ground
            lighter = ramp[max(0, ramp.index(colour) - 1)]
            floor_ramp = ([lighter] if lighter != colour else []) + floor_ramp
        if "grey" in variant:                                      # a darker middle: the colour falls through dark grey before black
            floor_ramp = [c for c in floor_ramp if c != 0] + [11, 0]
        band = dither_column_fine(size, floor_h, floor_ramp)
        for y in range(floor_h):
            for x in range(size): px[x, size - floor_h + y] = rgb(band[y][x])
        put_figure((size - fw) // 2, size - floor_h - fh, colour)
        sq, gap = (3, 1) if variant == "tag-column" else (2, 1)     # the corner tags are two-pixel squares, clear of the hat
        if "big" in variant: sq = 3                                    # three-pixel squares: a bolder tag, still clear of the hat
        def square(x0, y0, c, w=sq, h=sq):
            for y in range(h):
                for x in range(w):
                    if 0 <= x0 + x < size and 0 <= y0 + y < size: px[x0 + x, y0 + y] = rgb(c)
        def frame(x0, y0, w=sq, h=sq):
            for k in range(-1, w + 1):
                for (xx, yy) in ((k, -1), (k, h)):
                    if 0 <= x0 + xx < size and 0 <= y0 + yy < size: px[x0 + xx, y0 + yy] = rgb(1)
            for k in range(-1, h + 1):
                for (xx, yy) in ((-1, k), (w, k)):
                    if 0 <= x0 + xx < size and 0 <= y0 + yy < size: px[x0 + xx, y0 + yy] = rgb(1)
        if variant.startswith("tag-row"):    # seven squares in a row, two pixels each
            for i, c in enumerate(STRIP): square(2 + i * (sq + gap), 2, c)
        elif variant == "tag-row-thin":      # seven flat rectangles, two pixels tall
            for i, c in enumerate(STRIP): square(2 + i * (sq + gap), 2, c, h=2)
        elif variant == "tag-block":         # four over three: 15 x 7, a tag
            for i, c in enumerate(STRIP):
                r_, k = (0, i) if i < 4 else (1, i - 4)
                square(2 + k * (sq + gap), 2 + r_ * (sq + gap), c)
        elif variant == "tag-block-marked":  # the same, the token's own square framed in white
            for i, c in enumerate(STRIP):
                r_, k = (0, i) if i < 4 else (1, i - 4)
                square(2 + k * (sq + gap), 2 + r_ * (sq + gap), c)
            for i, c in enumerate(STRIP):
                if c == colour:
                    r_, k = (0, i) if i < 4 else (1, i - 4)
                    frame(2 + k * (sq + gap), 2 + r_ * (sq + gap))
        elif variant == "tag-column":        # the earlier column, shrunk to the corner: seven squares down the left edge
            for i, c in enumerate(STRIP): square(2, 2 + i * (sq + gap), c)
    return im

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokens", nargs="*", default=["the-echo", "the-dancer", "the-shadow"])
    ap.add_argument("--variants", nargs="*", default=["tag-row", "tag-block", "tag-block-marked", "tag-column"])
    ap.add_argument("--out", default="deliverables/screenshots/mock-retro-sheet.png")
    a = ap.parse_args()
    frames = bt.load_frames()
    pad, th = 14, 18
    cols = len(a.variants); rows = len(a.tokens)
    cell_w = 240 + 8 + 96 + 8 + 48
    sheet = Image.new("RGB", (pad + cols * (cell_w + pad), pad + rows * (240 + th + pad)), (24, 24, 24)); d = ImageDraw.Draw(sheet)
    for r, t in enumerate(a.tokens):
        for c, v in enumerate(a.variants):
            im = draw(frames, t, v)
            x0 = pad + c * (cell_w + pad); y0 = pad + r * (240 + th + pad)
            d.text((x0, y0 + 2), f"{t} · {v}", fill=(230, 230, 230))
            x = x0
            for scale in (5, 2, 1):
                big = im.resize((48 * scale, 48 * scale), Image.NEAREST)
                sheet.paste(big, (x, y0 + th + (240 - 48 * scale))); x += 48 * scale + 8
    sheet.save(a.out); print(a.out, sheet.size)

def lineup(variant, out, tokens=("the-shadow", "the-dancer", "the-echo", "the-mirror", "the-wanderer", "the-shy", "the-sleeper")):
    """All the regulars in one variant, at 5x and 1x, side by side."""
    frames = bt.load_frames()
    pad, th = 12, 18
    sheet = Image.new("RGB", (pad + len(tokens) * (240 + pad), pad + th + 240 + pad + 48 + pad), (24, 24, 24)); d = ImageDraw.Draw(sheet)
    for i, t in enumerate(tokens):
        im = draw(frames, t, variant); x = pad + i * (240 + pad)
        d.text((x, pad), t, fill=(230, 230, 230))
        sheet.paste(im.resize((240, 240), Image.NEAREST), (x, pad + th))
        sheet.paste(im, (x, pad + th + 240 + pad))
    sheet.save(out); print(out, sheet.size)

if __name__ == "__main__":
    if "--lineup" in sys.argv:
        i = sys.argv.index("--lineup"); lineup(sys.argv[i + 1], sys.argv[i + 2])
    else:
        main()
