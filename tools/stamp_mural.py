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
CANDLE_SLOT = [0, 1, 2, 3, 4, 1, 2, 3]
CANDLE_COL = [7, 13, 19, 25, 31]


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
    """-> (mode, wall rows of 15 bools, sconce columns, sconce count asked)"""
    A, B, C = Stream(seed, 0), Stream(seed, 19), Stream(seed, 25)
    mode = seed[31] & 3
    wall = []
    for r in range(10):
        row = []
        for c in range(15):
            a, b, cc = A.bit(), B.bit(), C.bit()
            row.append(bool([a & b, a, a | b, a & b & cc][mode]))
        wall.append(row)
    n = seed[30] & 3
    picks = [seed[29] & 7, (seed[29] >> 3) & 7, seed[28] & 7][:n]
    lit = []
    for k in picks:
        slot = CANDLE_SLOT[k]
        if slot not in lit:
            lit.append(slot)
    return mode, wall, [CANDLE_COL[s] for s in lit], n


def show(seed, digits):
    mode, wall, cols, n = predict(seed)
    names = ["quarter (A&B)", "half (A)", "three-quarter (A|B)", "eighth (A&B&C)"]
    print(f"   density mode {mode}: {names[mode]}; sconces asked {n}, lit at columns {cols or 'none'}; "
          f"floor reads {''.join(str(d) for d in digits)}")
    for r, row in enumerate(wall):
        line = "".join("#" if v else "." for v in row)
        if r == 3:
            marks = "".join("C" if (5 + 2 * c) in cols else " " for c in range(15))
            line += "   sconces: " + marks
        print("   " + line)


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
