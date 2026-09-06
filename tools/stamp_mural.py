#!/usr/bin/env python3
"""Write a mural seed into a Chamber PRG (or read the one it has).

    python3 tools/stamp_mural.py IN.prg OUT.prg --hex 0x5bcd...          # 32 bytes, e.g. a block hash
    python3 tools/stamp_mural.py IN.prg OUT.prg --text "block 25850250"  # sha256 of the text
    python3 tools/stamp_mural.py IN.prg --show                            # print the seed and the wall

The seed sits right after the 8-byte marker "MURAL01\\0" (the generator
aligns it so it never crosses a page). The tool prints the file offset a
contract would patch, and the wall the seed draws (15 x 10 slots, # = brick).
"""
import argparse
import hashlib
from pathlib import Path

MARKER = b"MURAL01\x00"


def wall(seed):
    bits = "".join(f"{b:08b}" for b in seed)
    return ["".join("#" if bits[r * 15 + c] == "1" else "." for c in range(15)) for r in range(10)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prg")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--hex")
    ap.add_argument("--text")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    data = bytearray(Path(a.prg).read_bytes())
    i = data.find(MARKER)
    if i < 0 or data.count(MARKER) != 1:
        raise SystemExit("no (or more than one) MURAL01 marker in this PRG")
    off = i + len(MARKER)
    addr = 0x0801 + off - 2
    print(f"seed at file offset 0x{off:05X} (address ${addr:04X}), 32 bytes; current: {bytes(data[off:off + 32]).hex()}")
    if a.show or not a.out:
        print("\n".join("   " + row for row in wall(data[off:off + 32])))
        return
    if a.hex:
        seed = bytes.fromhex(a.hex[2:] if a.hex.startswith("0x") else a.hex)
    elif a.text:
        seed = hashlib.sha256(a.text.encode()).digest()
    else:
        raise SystemExit("give --hex or --text")
    if len(seed) != 32:
        raise SystemExit(f"seed must be 32 bytes, got {len(seed)}")
    data[off:off + 32] = seed
    Path(a.out).write_bytes(bytes(data))
    print(f"wrote {a.out}: seed {seed.hex()}")
    print("\n".join("   " + row for row in wall(seed)))


if __name__ == "__main__":
    main()
