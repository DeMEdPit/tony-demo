#!/usr/bin/env python3
"""
freeze_record.py - the numbers that identify the Chamber base, for the handoff.

Prints size, sha256, keccak256, the marker's and the block's file offsets and
the git commit of the working tree for the base PRG, then the same digests for
every stamped deliverable. Run at the freeze and paste the output into
HANDOFF-CONTRACTS.md section 4.

Usage: freeze_record.py [--prg deliverables/prg/minimal64/tony-chamber.prg] [--json OUT]
"""
import argparse, glob, hashlib, json, os, subprocess
from Crypto.Hash import keccak      # pip install pycryptodome

def digests(path):
    d = open(path, "rb").read()
    i = d.find(b"MURAL02\x00")
    blk = d[i + 8:i + 50]
    return {"file": os.path.basename(path), "size": len(d), "sha256": hashlib.sha256(d).hexdigest(),
            "keccak256": keccak.new(digest_bits=256, data=d).hexdigest(), "marker_offset": i, "block_offset": i + 8,
            "behaviour": blk[40], "colour": blk[41], "block_number": "".join(str(b) for b in blk[32:40])}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prg", default="deliverables/prg/minimal64/tony-chamber.prg")
    ap.add_argument("--json")
    ap.add_argument("--frozen", help="record the freeze: the date, e.g. 2026-09-07 (the commit is the working tree's)")
    a = ap.parse_args()
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "tools", "deliverables/prg"], capture_output=True, text=True).stdout.strip() != ""
    except Exception:
        commit, dirty = None, None
    base = digests(a.prg)
    base["commit"] = commit
    base["working_tree_clean"] = not dirty
    if a.frozen:
        base["frozen"] = {"date": a.frozen, "commit": commit, "note": "the base does not change after this; anything found later is fix-forward in new tokens"}
    print("base %s: %d bytes" % (base["file"], base["size"]))
    print("  sha256    %s" % base["sha256"])
    print("  keccak256 %s" % base["keccak256"])
    print("  marker at file offset 0x%05X, the 42 bytes at 0x%05X" % (base["marker_offset"], base["block_offset"]))
    print("  commit %s%s" % (commit, "" if not dirty else "  (WORKING TREE NOT CLEAN)"))
    if a.frozen: print("  FROZEN %s at this commit" % a.frozen)
    stamped = []
    for f in sorted(glob.glob(os.path.join(os.path.dirname(a.prg), "tony-chamber-the-*.prg"))):
        s = digests(f); stamped.append(s)
        print("  %-34s behaviour %d colour %2d  sha256 %s" % (s["file"], s["behaviour"], s["colour"], s["sha256"]))
    if a.json:
        json.dump({"base": base, "stamped": stamped}, open(a.json, "w"), indent=1)
        print("wrote", a.json)

if __name__ == "__main__":
    main()
