#!/usr/bin/env python3
"""Capture every room's RUNTIME collision map from the on-chain PRG running on
minimal64: the screen chars with static objects drawn in (flames, pikes, doors,
stones, keys...) looked up through the engine's runtime materials buffer.  The
static map alone misses e.g. flame fire-chars, which the engine marks deadly
at runtime with no cheat exemption.

    python3 tools/capture_runtime_rooms.py [OUT.json]

Boots the token edition, presses fire, then for each room forces the engine's
own room transition (poke roomChange/direction), waits for the fade, and dumps
both screen buffers plus MATERIALS_MEM.  The active buffer is the one matching
the room's static map best.  Output: {room: [[material bits]*40]*20}.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import onchain_castle as oc  # noqa: E402

HERE = Path(__file__).parent
M64RUN = HERE / "m64-harness" / "m64run"
PRG = HERE.parent / "deliverables" / "onchain" / "tony-token-edition.prg"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "deliverables" / "onchain" / "runtime-collision.json"
# the physics reads roomMaterialsBuffer (per-room, indexed by the REMAPPED screen
# codes of the room's used-chars charset) through chamberLines (row addresses
# into whichever screen buffer is live) - tony.asm: checkBGCollision
ROOM_MATERIALS, CHAMBER_LINES = 0xBE00, 0x4290


def main():
    t = oc.Tony(oc.load_prg(PRG))
    out, report = {}, []
    with tempfile.TemporaryDirectory() as tmp:
        for r in range(oc.ROOMS):
            scr, m, cl = (Path(tmp) / f"scr-{r}.bin", Path(tmp) / f"m-{r}.bin", Path(tmp) / f"cl-{r}.bin")
            script = ["wait:400", "joy:16:6", "wait:250", "poke:2d:00"]
            if r != 18:
                script += [f"poke:{0x3E59:x}:04", f"poke:{0x3E55:x}:{r:02x}", "wait:250"]
            script += [f"dump:{CHAMBER_LINES:x}:40:{cl}", f"dump:{ROOM_MATERIALS:x}:100:{m}",
                       f"dump:c000:800:{scr}", f"peek:{0x3E51:x}"]
            res = subprocess.run([str(M64RUN), str(PRG), ",".join(script)], capture_output=True, text=True, timeout=600)
            chamber = [l for l in res.stdout.splitlines() if l.startswith("peek")][-1]
            assert chamber.endswith(f"${r:02x}"), f"room {r}: {chamber}"
            lines = cl.read_bytes()
            rows = None
            for n in (20, 25):                                          # .lohifill: n lo bytes, then n hi bytes
                cand = [lines[i] | (lines[n + i] << 8) for i in range(20)]
                if all(cand[i] == cand[0] + 40 * i for i in range(20)) and 0xC000 <= cand[0] <= 0xC400:
                    rows = cand
                    break
            assert rows, f"room {r}: unexpected chamberLines layout {lines[:50].hex()}"
            both = scr.read_bytes()                                     # $C000-$C7FF: both screen buffers
            mats = m.read_bytes()
            grid = [[mats[both[rows[row] - 0xC000 + col]] & 0x07 for col in range(40)] for row in range(20)]
            out[str(r)] = grid
            changed = sum(1 for row in range(20) for col in range(40)
                          if (t.materials[t.rooms[r][row][col]] & 0x07) != grid[row][col])
            kill_added = sum(1 for row in range(20) for col in range(40)
                             if grid[row][col] & 4 and not t.materials[t.rooms[r][row][col]] & 4)
            report.append((r, changed, kill_added))
            print(f"room {r:2d}: {changed:3d} cells differ from the static map, {kill_added:3d} newly deadly  ({t.summary(r)})")
    OUT.write_text(json.dumps(dict(source="tony-token-edition.prg on minimal64, cheats off; roomMaterialsBuffer[$BE00] "
                                          "indexed by the live screen through chamberLines[$4290]", rooms=out)))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
