#!/usr/bin/env python3
"""PNG sprite-sheet <-> ASCII <-> C64 hardware sprite tooling for the Tony demo.

Replicates the conversion rule of the c64lib retro-assembler image processor
(C64SpriteWriter + ReadPngImageAdapter):
  - alpha is IGNORED when reading PNGs;
  - a pixel whose RGB is (0,0,0) is background (bit 0);
  - any other RGB is figure (bit 1);
  - a 24x21 cell packs into 63 bytes (3 bytes per row, MSB leftmost) + 1 pad.

The Tony player sheets are N frames of 32x32 laid out horizontally.  The build
splits each frame into 24x21 quadrants after extending to 48x42 and keeps only
the left column (quadrants 0 and 2) => usable art area is x 0..23, y 0..31 of
each 32x32 cell.  The ".bg" overlay sheets are sampled at every second row
(reduceY=2) and displayed as a single Y-expanded sprite behind the player.

Usage:
  sprite_tool.py sheet2txt SHEET.png [cellW cellH]       # ASCII dump
  sprite_tool.py txt2sheet ART.txt OUT.png W H           # compile ASCII art
  sprite_tool.py bin2txt SPRITE.bin                      # decode 63/64b bin
  sprite_tool.py bins2png OUT.png BIN [BIN...]           # decode bins to PNG
  sprite_tool.py genbg FG.png OUT.png [radius]           # overlay via dilation

ASCII art format for txt2sheet: frames separated by lines starting with
"== frame"; '.' or ' ' = background, anything else = figure pixel.
"""

import sys

from PIL import Image

BLACK = (0, 0, 0)


def load_mask(path):
    """PNG -> 2D list of 0/1 using the plugin's RGB-only rule."""
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    return [[0 if px[x, y][:3] == BLACK else 1 for x in range(w)] for y in range(h)], w, h


def save_mask(mask, path):
    # RGBA: the plugin's PNG reader handles palette or 4-channel PNGs only
    # (plain RGB rows crash its scanline indexing); alpha itself is ignored.
    h, w = len(mask), len(mask[0])
    im = Image.new("RGBA", (w, h), BLACK + (255,))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                px[x, y] = (255, 255, 255, 255)
    im.save(path)


def frames_of(mask, w, h, cw, ch):
    fr = []
    for fy in range(0, h, ch):
        for fx in range(0, w, cw):
            fr.append([row[fx:fx + cw] for row in mask[fy:fy + ch]])
    return fr


def txt_of_frame(fr):
    return "\n".join("".join("#" if v else "." for v in row) for row in fr)


def sheet2txt(path, cw=32, ch=32):
    mask, w, h = load_mask(path)
    for i, fr in enumerate(frames_of(mask, w, h, cw, ch)):
        print(f"== frame {i} ({cw}x{ch}) of {path}")
        print(txt_of_frame(fr))


def txt2sheet(txt_path, out_path, w, h):
    frames = []
    cur = None
    for line in open(txt_path):
        line = line.rstrip("\n")
        if line.startswith("== frame"):
            cur = []
            frames.append(cur)
        elif cur is not None and line.strip("=") != "":
            cur.append([0 if c in ". " else 1 for c in line])
    n = len(frames)
    cw, ch = w // n if False else None, None  # frames laid out horizontally
    # infer cell size from first frame
    ch = len(frames[0])
    cw = max(len(r) for r in frames[0])
    assert n * cw == w and ch == h, f"{n} frames of {cw}x{ch} != sheet {w}x{h}"
    mask = [[0] * w for _ in range(h)]
    for i, fr in enumerate(frames):
        for y, row in enumerate(fr):
            for x, v in enumerate(row):
                if v:
                    mask[y][i * cw + x] = 1
    save_mask(mask, out_path)
    print(f"wrote {out_path}: {n} frames of {cw}x{ch}")


def decode_bin(path):
    data = open(path, "rb").read()
    rows = []
    for y in range(21):
        row = []
        for bx in range(3):
            b = data[y * 3 + bx]
            row.extend((b >> (7 - i)) & 1 for i in range(8))
        rows.append(row)
    return rows


def bins2png(out, paths):
    n = len(paths)
    im = Image.new("RGB", (n * 24, 21), BLACK)
    px = im.load()
    for i, p in enumerate(paths):
        rows = decode_bin(p)
        for y in range(21):
            for x in range(24):
                if rows[y][x]:
                    px[i * 24 + x, y] = (255, 255, 255)
    im.save(out)
    print(f"wrote {out} ({n} sprites)")


def dilate(mask, radius):
    h, w = len(mask), len(mask[0])
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < h and 0 <= xx < w:
                            out[yy][xx] = 1
    return out


def genbg(fg_path, out_path, radius=2, cw=32, ch=32):
    """Overlay sheet = per-frame dilation of the fg silhouette.

    Dilation is done per frame cell so overlays never bleed into the
    neighbouring frame of the sheet.
    """
    mask, w, h = load_mask(fg_path)
    out = [[0] * w for _ in range(h)]
    for fy in range(0, h, ch):
        for fx in range(0, w, cw):
            cell = [row[fx:fx + cw] for row in mask[fy:fy + ch]]
            cell = dilate(cell, radius)
            for y in range(ch):
                for x in range(cw):
                    if cell[y][x]:
                        out[fy + y][fx + x] = 1
    save_mask(out, out_path)
    print(f"wrote {out_path} (dilation r={radius})")


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 1
    cmd = a[0]
    if cmd == "sheet2txt":
        cw, ch = (int(a[2]), int(a[3])) if len(a) > 2 else (32, 32)
        sheet2txt(a[1], cw, ch)
    elif cmd == "txt2sheet":
        txt2sheet(a[1], a[2], int(a[3]), int(a[4]))
    elif cmd == "bin2txt":
        print(txt_of_frame(decode_bin(a[1])))
    elif cmd == "bins2png":
        bins2png(a[1], a[2:])
    elif cmd == "genbg":
        genbg(a[1], a[2], int(a[3]) if len(a) > 3 else 2)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
