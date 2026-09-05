#!/usr/bin/env python3
"""Play-test a castle patch on minimal64 (the on-chain runtime), headless.

    python3 tools/verify_castle.py deliverables/onchain/castles/castle-the-ring.json [SHOTDIR]

Reads the castle's emitted JSON (spec + patched PRG next to it) and drives
tools/m64-harness/m64run through a plan derived from the spec:

  gate    boot, fire at the title, expect the entry room
  door    for every wired E/W exit: jump into the room, stand Tony at that edge
          on a standable floor row, walk out, expect the target room
  drop    for every wired S exit: stand Tony over a safe hole column, hold DOWN
  loop    for a self-wired room: walk out east, expect the same room with Tony
          re-entered at the west side (X wraps)
  cheat   read gameCheatState after boot

Room jumps use the engine's own transition (poke roomChange + direction), and
positions use the physics actor variables; the walks themselves are real
joystick input through the emulated CIA.  Exit code 0 only if every check
passes.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import onchain_castle as oc  # noqa: E402

M64RUN = Path(__file__).parent / "m64-harness" / "m64run"
CHAMBER, X_LO, X_HI, Y = 0x3E51, 0x39CC, 0x39CD, 0x39CE
ROOM_CHANGE, ROOM_DIR = 0x3E55, 0x3E59
ACT_X, ACT_Y = 0x39D6, 0x39D8
JOY = dict(UP=1, DOWN=2, LEFT=4, RIGHT=8, FIRE=16)
DIR_W = 4                               # "exiting west" => engine places Tony at the east edge


def x_of_col(col):                      # measured: physPlayerX 20 <-> column 0, 8 px per column
    return 20 + 8 * col


def y_of_floor(F):                      # measured: feet on row 6 <-> physPlayerY 70
    return 70 + 8 * (F - 6)


def run(prg, script):
    out = subprocess.run([str(M64RUN), str(prg), ",".join(script)], capture_output=True, text=True, timeout=600).stdout
    peeks = [int(l.split("=")[1].strip()[1:], 16) for l in out.splitlines() if l.startswith("peek")]
    return peeks, out


def jump(room):                         # engine-driven room change; Tony lands at the east edge
    # the arrival spot is arbitrary and may be deadly; wait out a death+respawn
    # (~100 frames) so a later place() is not undone by the respawn
    return [f"poke:{ROOM_DIR:x}:{DIR_W:02x}", f"poke:{ROOM_CHANGE:x}:{room:02x}", "wait:260"]


def place(x, y):
    # measured: after a teleport Tony spends ~50 frames landing (crouch state) and
    # ignores the stick, so give him time to settle before walking
    return [f"poke:{ACT_X:x}:{x & 0xff:02x}", f"poke:{ACT_X + 1:x}:{x >> 8:02x}", f"poke:{ACT_Y:x}:{y:02x}", "wait:90"]


def main():
    meta = json.loads(Path(sys.argv[1]).read_text())
    shots = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    prg = Path(sys.argv[1]).with_suffix(".prg")
    spec = meta["spec"]
    base = oc.Tony(oc.load_prg(Path(__file__).parent.parent / "deliverables" / "onchain" / "tony-token-edition.prg"))
    boot = ["wait:400", "joy:16:6", "wait:250"]
    # door/drop/loop checks measure geometry and wiring, not combat: an enemy
    # guarding an edge (room 8's skull) would otherwise kill the teleported Tony
    # mid-test.  Test-only RAM poke of the cheat byte: stone+sprite+pikes proof.
    invincible = ["poke:2d:32"]
    results = []

    def check(name, script, expect, shot=None):
        s = list(script)
        if shot and shots:
            s.append(f"shot:{shots}/{shot}.ppm")
        peeks, out = run(prg, s)
        ok = expect(peeks)
        results.append(ok)
        print(f"  [{'ok' if ok else 'FAIL'}] {name}: peeks {[hex(p) for p in peeks]}")
        return ok

    slug = meta["name"].lower().replace(" ", "-")
    print(f"== {meta['name']} ({prg.name}) ==")
    entry = spec["entry"]
    check(f"gate: fire at title -> room {entry}; cheat byte ${meta['cheat_byte']:02X}",
          boot + [f"peek:{CHAMBER:x}", "peek:2d"], lambda p: p[0] == entry and p[1] == meta["cheat_byte"],
          shot=f"{slug}-entry")

    for room, ex in spec["exits"].items():
        room = int(room)
        for d, target in ex.items():
            if target == oc.NO:
                continue
            if d in "EW":
                floors = sorted(base.edge_floors(room, d))
                if not floors:
                    print(f"  [skip] room {room} {d}: no standable edge floor to walk from"); continue
                F = floors[0]
                x = x_of_col(37) if d == "E" else x_of_col(1)
                joy = JOY["RIGHT"] if d == "E" else JOY["LEFT"]
                script = boot + invincible + jump(room) + place(x, y_of_floor(F)) + [
                    f"joy:{joy}:60", "wait:150", f"peek:{CHAMBER:x}", f"peek:{X_LO:x}", f"peek:{X_HI:x}"]
                if target == room:      # self-loop: same room, X wrapped to the other side
                    side_ok = (lambda p: p[1] | (p[2] << 8) < 160) if d == "E" else (lambda p: p[1] | (p[2] << 8) > 180)
                    check(f"loop: room {room} walk {d} -> re-enter {room} from the other side",
                          script, lambda p: p[0] == room and side_ok(p), shot=f"{slug}-loop-{d}")
                else:
                    check(f"door: room {room} walk {d} (floor row {F}) -> room {target}",
                          script, lambda p: p[0] == target, shot=f"{slug}-door-{room}{d}")
            elif d == "S":
                cols = base.safe_drop_cols(room, target)
                if not cols:
                    print(f"  [skip] room {room} S: no safe drop column"); continue
                c = cols[0]
                script = boot + invincible + jump(room) + place(x_of_col(c), y_of_floor(18)) + [
                    "joy:2:90", "wait:150", f"peek:{CHAMBER:x}", f"peek:{Y:x}"]
                check(f"drop: room {room} down through column {c} -> room {target}",
                      script, lambda p: p[0] == target, shot=f"{slug}-drop-{room}")
            elif d == "N":
                print(f"  [skip] room {room} N exit: no automated climb-out test")

    for edit in meta.get("walls", spec.get("walls", [])):
        r = edit["room"]
        rows = sorted({row for row, _, _ in edit["cells"]})
        c = edit["cells"][0][1]
        script = boot + invincible + jump(r) + place(x_of_col(c), y_of_floor(min(rows))) + [
            "joy:2:90", "wait:60", f"peek:{CHAMBER:x}", f"peek:{Y:x}"]
        check(f"wall plug: room {r} rows {rows} hold DOWN on the plugged hole -> stays in room at floor",
              script, lambda p: p[0] == r and p[1] <= y_of_floor(min(rows)) + 2, shot=f"{slug}-plug")

    print(f"== {sum(results)}/{len(results)} checks passed ==")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
