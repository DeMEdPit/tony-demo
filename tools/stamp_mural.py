#!/usr/bin/env python3
"""Write a seed block into a Chamber PRG (or read the one it has), and predict
exactly what the game will draw from it.

    python3 tools/stamp_mural.py IN.prg OUT.prg --hex 0x5bcd... [--block 25850250]
    python3 tools/stamp_mural.py IN.prg OUT.prg --text "block 25990001" --block 25990001
    python3 tools/stamp_mural.py IN.prg --show

The block sits right after the 8-byte marker "MURAL01\\0": 32 seed bytes
(the block hash), then 8 block-number digits (0-9 each, most significant
first). A contract writes the same 40 bytes at render time. The prediction
below mirrors the 6502 routine in tony-chamber.asm bit for bit.
"""
import argparse
import hashlib
from pathlib import Path

MARKER = b"MURAL01\x00"
MODETAB = [0, 0, 1, 1, 1, 3, 3, 2]                          # quarter x2, half x3, eighth x2, dense x1
KTAB = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 4, 9]   # slot column 0..13 (left column 5 + 2k)
JTAB = [1, 2, 3, 4, 5, 2, 3, 4]                             # slot row 1..5 (top row 2 + 2j)


class Stream:
    def __init__(self, seed, start):
        self.seed, self.idx, self.cur, self.left = seed, start, 0, 0

    def bit(self):
        if self.left == 0:
            self.cur = self.seed[self.idx]
            self.idx = (self.idx + 1) & 31
            self.left = 8
        self.left -= 1
        b = (self.cur >> 7) & 1
        self.cur = (self.cur << 1) & 0xFF
        return b


def predict(seed):
    """-> (mode, wall rows of 15 bools, candle or None)
    candle = (left, top): the niche is rows top..top+3, columns left..left+3
    (wall slots (j,k),(j,k+1),(j+1,k),(j+1,k+1) cleared, j=(top-2)//2,
    k=(left-5)//2); the 3x3 block $BD-$C5 sits at rows top..top+2, columns
    left+1..left+3."""
    A, B, C = Stream(seed, 0), Stream(seed, 19), Stream(seed, 25)
    mode = MODETAB[seed[31] & 7]
    wall = []
    for r in range(10):
        row = []
        for c in range(15):
            a, b, cc = A.bit(), B.bit(), C.bit()
            row.append(bool([a & b, a, a | b, a & b & cc][mode]))
        wall.append(row)
    candle = None
    if seed[30] & 3:
        k = KTAB[seed[29] & 15]
        j = JTAB[(seed[29] >> 4) & 7]
        candle = (5 + 2 * k, 2 + 2 * j)
    return mode, wall, candle


def show(seed, digits):
    mode, wall, candle = predict(seed)
    names = ["quarter (A&B)", "half (A)", "three-quarter (A|B, rare)", "eighth (A&B&C)"]
    where = f"candle at column {candle[0] + 1}, rows {candle[1]}-{candle[1] + 2}" if candle else "no candle"
    print(f"   density mode {mode}: {names[mode]}; {where}; floor reads {''.join(str(d) for d in digits)}")
    lit = set()
    if candle:
        k, j = (candle[0] - 5) // 2, (candle[1] - 2) // 2
        lit = {(j, k), (j, k + 1), (j + 1, k), (j + 1, k + 1)}
    for r, row in enumerate(wall):
        print("   " + "".join("i" if (r, c) in lit else ("#" if v else ".") for c, v in enumerate(row)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prg")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--hex", help="32-byte seed, e.g. a block hash")
    ap.add_argument("--text", help="seed = sha256 of this text")
    ap.add_argument("--block", type=int, help="block number carved into the floor (8 digits)")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    data = bytearray(Path(a.prg).read_bytes())
    i = data.find(MARKER)
    if i < 0 or data.count(MARKER) != 1:
        raise SystemExit("no (or more than one) MURAL01 marker in this PRG")
    off = i + len(MARKER)
    addr = 0x0801 + off - 2
    cur_seed, cur_digits = bytes(data[off:off + 32]), list(data[off + 32:off + 40])
    print(f"seed block at file offset 0x{off:05X} (address ${addr:04X}): 32 seed bytes + 8 digits")
    print(f"current seed {cur_seed.hex()} block {''.join(str(d) for d in cur_digits)}")
    if a.show or not a.out:
        show(cur_seed, cur_digits)
        return
    seed = cur_seed
    if a.hex:
        seed = bytes.fromhex(a.hex[2:] if a.hex.startswith("0x") else a.hex)
    elif a.text:
        seed = hashlib.sha256(a.text.encode()).digest()
    if len(seed) != 32:
        raise SystemExit(f"seed must be 32 bytes, got {len(seed)}")
    digits = cur_digits if a.block is None else [int(ch) for ch in f"{a.block:08d}"[-8:]]
    data[off:off + 32] = seed
    data[off + 32:off + 40] = bytes(digits)
    Path(a.out).write_bytes(bytes(data))
    print(f"wrote {a.out}: seed {seed.hex()} block {''.join(str(d) for d in digits)}")
    show(seed, digits)


if __name__ == "__main__":
    main()
