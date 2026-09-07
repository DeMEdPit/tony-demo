#!/usr/bin/env python3
"""
chamber_vectors.py - test vectors for the contracts: what the Chamber draws from a block.

For each vector: the 42 bytes a contract writes (seed, digits, behaviour, colour),
the file offset they go to in the base PRG, and what the base then shows, from
the Python model in tools/stamp_mural.py (which mirrors the 6502 bit for bit and
was checked against the emulator over sixteen seeds for the bats and many more
for the wall). A contract test that writes the same 42 bytes can compare its
own expectations against these, and an integration test can render the PRG and
compare the screen against the wall rows.

Usage: chamber_vectors.py [--prg deliverables/prg/minimal64/tony-chamber.prg] [--out deliverables/contract/chamber-vectors.json]
"""
import argparse, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stamp_mural import predict, bats, BEHAVIOURS, PATH_NAMES, PATH_TRAVEL, MODETAB

NAMES = ["The Shadow", "The Dancer", "The Echo", "The Mirror", "The Wanderer", "The Shy One", "The Sleeper", "The Glitch"]
COLOURS = [6, 3, 7, 14, 5, 10, 4, 1]      # provisional token colours by behaviour (the Glitch's byte is ignored: he cycles)
DENSITY = ["quarter", "half", "three-quarter", "eighth"]

def vector(seed, block, behaviour, colour, note):
    digits = [int(ch) for ch in "%08d" % (block % 100000000)]
    mode, wall, candle = predict(seed)
    presence, a, b = bats(seed)
    blk = bytes(seed) + bytes(digits) + bytes([behaviour, colour])
    assert len(blk) == 42
    return {
        "note": note,
        "block_number": block,
        "bytes_hex": blk.hex(),
        "seed_hex": seed.hex(),
        "digits": digits,
        "behaviour": behaviour, "mechanic": BEHAVIOURS[behaviour], "token_name": NAMES[behaviour],
        "colour": colour,
        "tune": "intro" if behaviour == 7 else "level",
        "room": "blackout" if behaviour == 7 else "ordinary",
        "wall": None if behaviour == 7 else {
            "density_mode": mode, "density": DENSITY[mode],
            "rows": ["".join("#" if v else "." for v in row) for row in wall],
            "bricks": sum(sum(row) for row in wall),
        },
        "candle": None if behaviour == 7 or candle is None else {"column": candle[0] + 1, "top_row": candle[1]},
        "bats": None if behaviour == 7 else {
            "presence": presence,
            "left": {"path": a[0], "path_name": PATH_NAMES[a[0]], "travel_px": PATH_TRAVEL[a[0]], "column": a[1], "row": a[2]},
            "right": {"path": b[0], "path_name": PATH_NAMES[b[0]], "travel_px": PATH_TRAVEL[b[0]], "column": b[1], "row": b[2]},
        },
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prg", default="deliverables/prg/minimal64/tony-chamber.prg")
    ap.add_argument("--out", default="deliverables/contract/chamber-vectors.json")
    a = ap.parse_args()
    prg = open(a.prg, "rb").read()
    i = prg.find(b"MURAL02\x00")
    vectors = []
    # the seeds the deliverables use, then a spread of block hashes, then the edges
    for block in (25850267, 25850271, 25850251, 25850252, 25850254, 25850256):
        vectors.append(vector(hashlib.sha256(b"block %d" % block).digest(), block, 0, 5, "sha256('block N'), as the stamped deliverables"))
    for k in range(24):
        block = 26000000 + k * 7919
        seed = hashlib.sha256(b"vector %d" % k).digest()
        beh = k % 8
        vectors.append(vector(seed, block, beh, COLOURS[beh], "sha256('vector k'), one of each mechanic in turn"))
    vectors.append(vector(bytes(32), 0, 0, 5, "all-zero seed"))
    vectors.append(vector(bytes([0xFF] * 32), 99999999, 7, 1, "all-ones seed, the Glitch: the blackout ignores the wall bits"))
    # fix the all-zero note from the model itself
    z = vectors[-2]; z["note"] = "all-zero seed: %s wall, %s, bats %s" % (z["wall"]["density"], "no candle" if z["candle"] is None else "a candle", z["bats"]["presence"])
    out = {
        "base_prg": os.path.basename(a.prg),
        "base_size": len(prg),
        "base_sha256": hashlib.sha256(prg).hexdigest(),
        "marker": "MURAL02\\0",
        "marker_file_offset": i,
        "block_file_offset": i + 8,
        "block_bytes": 42,
        "layout": "seed[32] + digits[8] (0-9 each, most significant first) + behaviour[1] (0-7) + colour[1] (0-15)",
        "density_table": MODETAB,
        "mechanics": BEHAVIOURS, "token_names": NAMES, "provisional_colours": COLOURS,
        "vectors": vectors,
    }
    json.dump(out, open(a.out, "w"), indent=1)
    print("%s: %d vectors for %s (%d bytes, sha256 %s), block at file offset 0x%05X" % (a.out, len(vectors), out["base_prg"], out["base_size"], out["base_sha256"][:16], i + 8))

if __name__ == "__main__":
    main()
