#!/usr/bin/env python3
"""Write a seed block into a Chamber PRG (or read the one it has), and predict
exactly what the game will draw from it.

    python3 tools/stamp_mural.py IN.prg OUT.prg --hex 0x5bcd... [--block 25850250]
    python3 tools/stamp_mural.py IN.prg OUT.prg --text "block 25990001" --block 25990001
    python3 tools/stamp_mural.py IN.prg --show

The block sits right after the 8-byte marker "MURAL02\\0": 32 seed bytes
(the block hash), 8 block-number digits, the behaviour byte (0 Follow,
1 Dance, 2-6 reserved) and the colour byte (a C64 colour index); older
"MURAL01" builds carry only the first 40 bytes. Digits are 0-9 each, most significant
first). A contract writes the same 40 bytes at render time. The prediction
below mirrors the 6502 routine in tony-chamber.asm bit for bit.
"""
import argparse
import hashlib
from pathlib import Path

MARKERS = {b"MURAL02\x00": 42, b"MURAL01\x00": 40}   # marker -> bytes the contract writes
BEHAVIOURS = ["Follow", "Dance", "Echo", "Mirror", "Wander", "Shy", "Sleeper", "Glitch"]
MODETAB = [3, 3, 3, 0, 0, 1, 1, 2]                          # eighth x3, quarter x2, half x2, dense x1: fewer bricks = more common
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


PATH_TRAVEL = [64, 48, 32, 48, 56, 48, 64, 24]        # pixels, per path
PATH_NAMES = ["long glide", "shorter glide", "short flutter", "wave", "glide with two hops", "bobbing",
              "long glide with a dip", "tight flutter"]
COL_B = [24, 25, 26, 27, 28, 29, 26, 28]


def bats(seed):
    """What the seed does to the bats (mirrors muralBatsStamp): presence, and (path, column, row) per bat."""
    pres = seed[27] & 15
    presence = "none" if pres == 0 else "left only" if pres <= 2 else "right only" if pres <= 4 else "both"
    a = (seed[24] & 7, 2 + ((seed[24] >> 3) & 7), 2 + (seed[25] & 7))
    b = ((seed[25] >> 3) & 7, COL_B[seed[26] & 7], 2 + ((seed[26] >> 3) & 7))
    return presence, a, b


def dice_seed(seed):
    """The buddy's dice at boot (mirrors buddyInit): a 16-bit register from seed bytes the contract leaves to the hash."""
    lo, hi = seed[28] ^ seed[15], seed[3] ^ seed[20]
    if lo == 0 and hi == 0:
        lo, hi = 0x5A, 0xA5
    return lo | (hi << 8)


def dice_step(state):
    """One frame of rollDice: eight steps of the Galois register x^16 + x^14 + x^13 + x^11 + 1 (mask $B400)."""
    for _ in range(8):
        bit = state & 1
        state >>= 1
        if bit:
            state ^= 0xB400
    return state


def show(seed, digits):
    mode, wall, candle = predict(seed)
    names = ["quarter (A&B)", "half (A)", "three-quarter (A|B, rare)", "eighth (A&B&C)"]
    where = f"candle at column {candle[0] + 1}, rows {candle[1]}-{candle[1] + 2}" if candle else "no candle"
    print(f"   density mode {mode}: {names[mode]}; {where}; floor reads {''.join(str(d) for d in digits)}")
    presence, a, b = bats(seed)
    def bat(t):
        return f"path {t[0]} ({PATH_NAMES[t[0]]}, {PATH_TRAVEL[t[0]]} px), column {t[1]}, row {t[2]}"
    print(f"   bats: {presence}; left {bat(a)}; right {bat(b)}")
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
    ap.add_argument("--behaviour", type=int, help="0 Follow, 1 Dance, 2-6 Echo/Mirror/Wander/Shy/Sleeper, 7 Glitch (the blackout room) (MURAL02 builds)")
    ap.add_argument("--colour", type=int, help="the buddy's C64 colour index 0-15 (MURAL02 builds)")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    data = bytearray(Path(a.prg).read_bytes())
    found = [(m, n) for m, n in MARKERS.items() if data.count(m) == 1]
    if len(found) != 1:
        raise SystemExit("no (or more than one) MURAL marker in this PRG")
    marker, nbytes = found[0]
    off = data.find(marker) + len(marker)
    addr = 0x0801 + off - 2
    cur_seed, cur_digits = bytes(data[off:off + 32]), list(data[off + 32:off + 40])
    cur_beh, cur_col = (data[off + 40], data[off + 41]) if nbytes == 42 else (None, None)
    print(f"{marker[:7].decode()} block at file offset 0x{off:05X} (address ${addr:04X}): {nbytes} bytes"
          + (" = 32 seed + 8 digits + behaviour + colour" if nbytes == 42 else " = 32 seed + 8 digits"))
    print(f"current seed {cur_seed.hex()} block {''.join(str(d) for d in cur_digits)}"
          + (f" behaviour {cur_beh} ({BEHAVIOURS[cur_beh] if cur_beh < len(BEHAVIOURS) else '?'}) colour {cur_col}"
             f" tune {'intro (the Glitch)' if cur_beh == 7 else 'level'}" if nbytes == 42 else ""))
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
    if nbytes == 42:
        if a.behaviour is not None:
            if not 0 <= a.behaviour <= 7:
                raise SystemExit("behaviour must be 0-7")
            data[off + 40] = a.behaviour
        if a.colour is not None:
            if not 0 <= a.colour <= 15:
                raise SystemExit("colour must be 0-15")
            data[off + 41] = a.colour
    elif a.behaviour is not None or a.colour is not None:
        raise SystemExit("this is a MURAL01 build: no behaviour or colour bytes")
    Path(a.out).write_bytes(bytes(data))
    extra = f" behaviour {data[off + 40]} colour {data[off + 41]}" if nbytes == 42 else ""
    print(f"wrote {a.out}: seed {seed.hex()} block {''.join(str(d) for d in digits)}{extra}")
    show(seed, digits)


if __name__ == "__main__":
    main()
