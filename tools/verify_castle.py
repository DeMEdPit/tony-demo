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
  entry   the first player's scenario: from the gate, hold LEFT and sample X and
          lives every 8 frames until Tony has covered the whole safe run the
          static analysis promises - no life may be lost on the way.  Sprite
          enemies are made harmless for this one check (cheat byte $12: sprite +
          stone immunity, NOT pike immunity) so it measures the floor, not the
          fight: a spike bed or the void on that run fails it.  (Snakes are static
          objects and ignore every cheat - handleSnake carries the author's "TODO
          add cheat mode here!" - so a snake parked on the run would fail it too,
          legitimately.)
  seal    for every sealed E/W exit with a standable edge floor: walk into it;
          "wall" mode keeps Tony in the room, in bounds, alive; "void" mode
          costs exactly one life and keeps him in the room
  sky     for every ladder that reaches the top edge under a sealed N exit: stand at
          its foot, hold UP (Tony must stay in the room, inside the playfield, still
          on the ladder), then hold DOWN (he must come back down) - the first
          player's "stuck at the top of the ladder" scenario
  guard   the edge-guard bytes are intact after play (nothing overwrote the padding after the BASIC line)

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
LIVES, INITIAL_LIVES = 0x42CA, 5
GUARD = oc.A["edge_stub"]
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
    mode = meta.get("edge_mode", "wall")
    stub, mode_off = oc.edge_stub(mode)
    rooms = set(meta["rooms"])
    print(f"== {meta['name']} ({prg.name}) edges={mode} ==")
    entry = spec["entry"]
    check(f"gate: fire at title -> room {entry}; cheat byte ${meta['cheat_byte']:02X}",
          boot + [f"peek:{CHAMBER:x}", "peek:2d"], lambda p: p[0] == entry and p[1] == meta["cheat_byte"],
          shot=f"{slug}-entry")
    walk_cols, walk_end = base.entry_walk(entry)
    x_end = x_of_col(oc.W - 2 - walk_cols)  # Tony's X once the run is fully walked
    samples = 40                            # 320 frames of LEFT, sampled every 8

    def walked_safely(p):
        # p = [chamber, x_lo, x_hi, lives] * samples: find the first sample past the
        # run's end; every sample up to it must still show all lives and the entry room
        for i in range(samples):
            ch, x, lives = p[4 * i], p[4 * i + 1] | (p[4 * i + 2] << 8), p[4 * i + 3]
            if ch != entry or lives != INITIAL_LIVES:
                return False
            if x <= x_end:
                return True
        return False                        # never got there: blocked, or stuck

    check(f"entry: hold LEFT from the gate over the {walk_cols}-column safe run (then {walk_end}), "
          f"enemies harmless, spikes live -> {INITIAL_LIVES} lives all the way",
          boot + ["poke:2d:12"] + ["joy:4:8", f"peek:{CHAMBER:x}", f"peek:{X_LO:x}", f"peek:{X_HI:x}", f"peek:{LIVES:x}"] * samples,
          walked_safely, shot=f"{slug}-entry-walk")

    # every direction the spec leaves unmentioned is sealed by the generator
    sealed = {r: {d: True for d in "EW"} for r in rooms}
    for r, ex in spec["exits"].items():
        for d, target in ex.items():
            if d in "EW" and target != oc.NO:
                sealed[int(r)][d] = False
    for r in sorted(rooms):
        for d in "EW":
            if not sealed[r][d]:
                continue
            floors = sorted(base.edge_floors(r, d))
            if not floors:
                continue                     # the map already walls that edge
            F = floors[0]
            x = x_of_col(37) if d == "E" else x_of_col(1)
            joy = JOY["RIGHT"] if d == "E" else JOY["LEFT"]
            script = boot + invincible + jump(r) + place(x, y_of_floor(F)) + [
                f"joy:{joy}:90", "wait:200", f"peek:{CHAMBER:x}", f"peek:{LIVES:x}", f"peek:{X_LO:x}", f"peek:{X_HI:x}"]
            inb = (lambda p: (p[2] | (p[3] << 8)) >= oc.LIMITS["WEST"] - 2) if d == "W" else \
                  (lambda p: (p[2] | (p[3] << 8)) <= oc.LIMITS["EAST"] + 2)
            if mode == "wall":
                check(f"seal/wall: room {r} walk into sealed {d} edge (floor row {F}) -> same room, in bounds, {INITIAL_LIVES} lives",
                      script, lambda p: p[0] == r and p[1] == INITIAL_LIVES and inb(p), shot=f"{slug}-seal-{r}{d}")
            else:
                check(f"seal/void: room {r} walk into sealed {d} edge (floor row {F}) -> same room, exactly one life lost",
                      script, lambda p: p[0] == r and p[1] == INITIAL_LIVES - 1, shot=f"{slug}-seal-{r}{d}")

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

    STATE, ON_LADDER = 0x39D3, 0x07            # physPlayerState; measured: 7 while climbing
    for r in sorted(rooms):
        n_exit = spec["exits"].get(str(r), {}).get("N", oc.NO)
        if n_exit != oc.NO or not base.top_ladder[r]:
            continue
        c = sorted(base.top_ladder[r])[0]
        L = 0
        while L + 1 < oc.H and base.mat(r, L + 1, c) & oc.LADDER:
            L += 1                              # last ladder row from the top
        if L + 1 >= oc.H or not (base.mat(r, L + 1, c) & oc.WALL):
            # measured (room 25): a ladder hanging from the top edge with nothing under
            # its last rung cannot be grabbed from below - it was only ever an entrance
            # from the room above.  Nothing to climb, nothing to get stuck on.
            print(f"  [skip] sky: room {r} ladder at column {c} (rows 0-{L}) hangs over open space - unreachable from below")
            continue
        script = boot + invincible + jump(r) + place(x_of_col(c), y_of_floor(L + 1)) + [
            "joy:1:200", f"peek:{CHAMBER:x}", f"peek:{Y:x}", f"peek:{STATE:x}",
            "joy:2:150", f"peek:{CHAMBER:x}", f"peek:{Y:x}", f"peek:{LIVES:x}"]
        check(f"sky: room {r} ladder at column {c} (rows 0-{L}) hold UP -> held at the top, still climbing; "
              f"hold DOWN -> comes back down",
              script, lambda p: (p[0] == r and p[1] >= oc.LIMITS["NORTH"] and p[2] == ON_LADDER
                                 and p[3] == r and p[4] >= p[1] + 16 and p[5] == INITIAL_LIVES),
              shot=f"{slug}-sky-{r}")

    for edit in meta.get("walls", spec.get("walls", [])):
        r = edit["room"]
        rows = sorted({row for row, _, _ in edit["cells"]})
        c = edit["cells"][0][1]
        if min(rows) == 0:      # a ladder into the sealed sky was capped: climb it, stay in the room
            script = boot + invincible + jump(r) + place(x_of_col(c), y_of_floor(4)) + [
                "joy:1:90", "wait:60", f"peek:{CHAMBER:x}", f"peek:{Y:x}"]
            check(f"wall plug: room {r} top rows {rows} hold UP under the capped ladder -> stays in room, inside the playfield",
                  script, lambda p: p[0] == r and p[1] >= oc.LIMITS["NORTH"], shot=f"{slug}-plug-{r}")
        else:                   # a floor hole over a sealed exit was filled: stand on it
            script = boot + invincible + jump(r) + place(x_of_col(c), y_of_floor(min(rows))) + [
                "joy:2:90", "wait:60", f"peek:{CHAMBER:x}", f"peek:{Y:x}"]
            check(f"wall plug: room {r} rows {rows} hold DOWN on the plugged hole -> stays in room at floor",
                  script, lambda p: p[0] == r and p[1] <= y_of_floor(min(rows)) + 2, shot=f"{slug}-plug-{r}")

    peeks_wanted = [f"peek:{GUARD + i:x}" for i in (0, 1, 2, mode_off)] + [f"peek:{oc.A['roomChange_tail'] + i:x}" for i in range(3)]
    check("guard: edge-guard bytes and the re-routed tail intact after a played session",
          boot + ["joy:4:120", "joy:8:120"] + peeks_wanted,
          lambda p: p[:4] == [stub[0], stub[1], stub[2], stub[mode_off]] and p[4:] == [0x4C, GUARD & 0xFF, GUARD >> 8])
    print(f"== {sum(results)}/{len(results)} checks passed ==")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
