#!/usr/bin/env python3
"""CharPad CTM v8/v9 inspector and patcher for the Tony demo assets.

Implements exactly the subset of the CTM format that the c64lib
gradle-retro-assembler-plugin 1.7.6 charpad processor reads
(see processors/charpad/usecase/post6/CTM8Processor.kt / CTM9Processor.kt):

  "CTM" <version:u8>
  header (v8: 10 bytes, v9: 15 bytes)
  blocks, each preceded by a $DA $Bn marker (n = running block index):
    0: charset       u16 numChars-1, then numChars*8 bytes of 8x8 bitmaps
    1: materials     numChars bytes (collision class per char)
    2: char colours  (only when colouringMethod == 1 "per char")
    tiles blocks     (only when flags bit 1 "TileSys" set)
    map              u16 width, u16 height, then w*h*2 bytes little-endian
                     (lo byte = char code as used by the game)

All patching is done in place (fixed-size records), so a patched file is
byte-identical outside the edited region.

Usage:
  ctm_tool.py info FILE.ctm
  ctm_tool.py map-txt FILE.ctm [x0 y0 x1 y1]      # dump map region as text
  ctm_tool.py map-png FILE.ctm OUT.png [x0 y0 x1 y1]
  ctm_tool.py charset-png FILE.ctm OUT.png
  ctm_tool.py char-txt FILE.ctm CODE              # dump one char 8x8
  ctm_tool.py set-cell FILE.ctm X Y CODE          # patch one map cell
  ctm_tool.py set-char FILE.ctm CODE B0..B7       # patch one char bitmap
"""

import struct
import sys


class CTM:
    def __init__(self, path):
        self.path = path
        self.data = bytearray(open(path, "rb").read())
        if self.data[0:3] != b"CTM":
            raise ValueError("not a CTM file")
        self.version = self.data[3]
        if self.version not in (8, 9):
            raise ValueError(f"unsupported CTM version {self.version}")
        self._parse()

    def _parse(self):
        d = self.data
        pos = 4
        if self.version == 8:
            (self.display_mode, self.colouring_method, self.flags,
             self.screen_color, self.mc1, self.mc2, self.bg4,
             self.cb0, self.cb1, self.cb2) = struct.unpack_from("<10B", d, pos)
            pos += 10
        else:  # v9
            self.display_mode = d[pos]; self.colouring_method = d[pos+1]
            self.flags = d[pos+2]
            self.flexi_w = d[pos+3] + 256*d[pos+4]
            self.flexi_h = d[pos+5] + 256*d[pos+6]
            # 1 ignored byte, then colours
            (self.screen_color, self.mc1, self.mc2, self.bg4,
             self.cb0, self.cb1, self.cb2) = struct.unpack_from("<7B", d, pos+8)
            pos += 15

        self.blocks = []

        def marker(p, expect_idx):
            if d[p] != 0xDA or (d[p+1] & 0xF0) != 0xB0:
                raise ValueError(f"bad block marker at {p:#x}: {d[p]:02x} {d[p+1]:02x}")
            if (d[p+1] & 0x0F) != expect_idx:
                raise ValueError(f"unexpected block index at {p:#x}")
            return p + 2

        bi = 0
        # block 0: charset
        pos = marker(pos, bi); bi += 1
        self.num_chars = struct.unpack_from("<H", d, pos)[0] + 1
        pos += 2
        self.charset_off = pos
        pos += self.num_chars * 8
        # block 1: materials
        pos = marker(pos, bi); bi += 1
        self.materials_off = pos
        pos += self.num_chars
        # optional per-char colours (colouring method: 0=Global 1=PerTile 2=PerChar)
        # colours entry size by screen mode: BitmapHires(3)=2, BitmapMulticolor(4)=3, else 1
        self.colours_size = {3: 2, 4: 3}.get(self.display_mode, 1)
        self.colours_off = None
        if self.colouring_method == 2:  # PerChar
            pos = marker(pos, bi); bi += 1
            self.colours_off = pos
            pos += self.num_chars * self.colours_size
        # optional tiles
        self.tiles = None
        if self.flags & 0x01:  # TileSys flag (CTM8Flags.TileSys = 0x01)
            pos = marker(pos, bi); bi += 1
            num_tiles = struct.unpack_from("<H", d, pos)[0] + 1
            tw, th = d[pos+2], d[pos+3]
            pos += 4
            tiles_off = pos
            pos += num_tiles * tw * th * 2
            if self.colouring_method == 1:  # PerTile
                pos = marker(pos, bi); bi += 1
                pos += num_tiles * self.colours_size
            pos = marker(pos, bi); bi += 1  # tile tags
            pos += num_tiles
            pos = marker(pos, bi); bi += 1  # tile names
            for _ in range(num_tiles):
                n = 0
                while n < 32 and d[pos] != 0:
                    pos += 1; n += 1
                pos += 1  # terminator
            self.tiles = (num_tiles, tw, th, tiles_off)
        # map block
        pos = marker(pos, bi); bi += 1
        self.map_w, self.map_h = struct.unpack_from("<HH", d, pos)
        pos += 4
        self.map_off = pos
        pos += self.map_w * self.map_h * 2
        self.end_off = pos

    # --- accessors -------------------------------------------------
    def cell(self, x, y):
        off = self.map_off + (y * self.map_w + x) * 2
        return struct.unpack_from("<H", self.data, off)[0]

    def set_cell(self, x, y, code):
        if not (0 <= x < self.map_w and 0 <= y < self.map_h):
            raise IndexError("cell out of range")
        off = self.map_off + (y * self.map_w + x) * 2
        struct.pack_into("<H", self.data, off, code)

    def char_bitmap(self, code):
        off = self.charset_off + code * 8
        return bytes(self.data[off:off + 8])

    def set_char_bitmap(self, code, eight_bytes):
        assert len(eight_bytes) == 8
        off = self.charset_off + code * 8
        self.data[off:off + 8] = bytes(eight_bytes)

    def material(self, code):
        return self.data[self.materials_off + code]

    def set_material(self, code, value):
        self.data[self.materials_off + code] = value & 0xFF

    def save(self, path=None):
        open(path or self.path, "wb").write(self.data)

    def info(self):
        print(f"{self.path}: CTM v{self.version}")
        print(f"  display_mode={self.display_mode} colouring_method={self.colouring_method} "
              f"flags={self.flags:#04x}")
        print(f"  colors: screen={self.screen_color} mc1={self.mc1} mc2={self.mc2} "
              f"base={self.cb0},{self.cb1},{self.cb2}")
        print(f"  charset: {self.num_chars} chars @ {self.charset_off:#x}")
        print(f"  materials @ {self.materials_off:#x}")
        if self.colours_off is not None:
            print(f"  per-char colours @ {self.colours_off:#x}")
        if self.tiles:
            n, tw, th, off = self.tiles
            print(f"  tiles: {n} of {tw}x{th} @ {off:#x}")
        print(f"  map: {self.map_w}x{self.map_h} @ {self.map_off:#x}")
        print(f"  file size {len(self.data)}, parsed end {self.end_off}"
              + ("" if self.end_off == len(self.data) else "  (trailing data!)"))


def char_rows(bitmap):
    return [[(b >> (7 - i)) & 1 for i in range(8)] for b in bitmap]


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    cmd = args[0]
    ctm = CTM(args[1])
    if cmd == "info":
        ctm.info()
    elif cmd == "map-txt":
        x0, y0, x1, y1 = (int(a) for a in args[2:6]) if len(args) > 2 else (0, 0, ctm.map_w, ctm.map_h)
        for y in range(y0, y1):
            print(" ".join(f"{ctm.cell(x, y) & 0xFF:02x}" for x in range(x0, x1)))
    elif cmd == "map-png":
        from PIL import Image
        out = args[2]
        x0, y0, x1, y1 = (int(a) for a in args[3:7]) if len(args) > 3 else (0, 0, ctm.map_w, ctm.map_h)
        w, h = (x1 - x0) * 8, (y1 - y0) * 8
        im = Image.new("L", (w, h), 0)
        px = im.load()
        for cy in range(y0, y1):
            for cx in range(x0, x1):
                rows = char_rows(ctm.char_bitmap(ctm.cell(cx, cy) & 0xFF))
                for ry in range(8):
                    for rx in range(8):
                        if rows[ry][rx]:
                            px[(cx - x0) * 8 + rx, (cy - y0) * 8 + ry] = 255
        im.save(out)
        print(f"wrote {out} ({w}x{h})")
    elif cmd == "charset-png":
        from PIL import Image
        out = args[2]
        cols = 16
        rows_n = (ctm.num_chars + cols - 1) // cols
        im = Image.new("L", (cols * 8, rows_n * 8), 0)
        px = im.load()
        for c in range(ctm.num_chars):
            rows = char_rows(ctm.char_bitmap(c))
            bx, by = (c % cols) * 8, (c // cols) * 8
            for ry in range(8):
                for rx in range(8):
                    if rows[ry][rx]:
                        px[bx + rx, by + ry] = 255
        im.save(out)
        print(f"wrote {out} ({ctm.num_chars} chars)")
    elif cmd == "char-txt":
        code = int(args[2], 0)
        print(f"char {code} material={ctm.material(code):#04x}")
        for row in char_rows(ctm.char_bitmap(code)):
            print("".join("#" if v else "." for v in row))
    elif cmd == "set-cell":
        x, y, code = int(args[2]), int(args[3]), int(args[4], 0)
        ctm.set_cell(x, y, code)
        ctm.save()
        print(f"set cell ({x},{y}) = {code:#x}")
    elif cmd == "set-char":
        code = int(args[2], 0)
        ctm.set_char_bitmap(code, bytes(int(b, 0) for b in args[3:11]))
        ctm.save()
        print(f"set char {code}")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
