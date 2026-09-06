#!/usr/bin/env python3
"""The bats from the seed, checked on the minimal64 harness.

For a set of seeds: stamp the Chamber, boot it, and read back what the game
decided (the report bytes after the parameter block) against the Python
model in tools/stamp_mural.py; then watch the two bat sprites for 300 frames
and check that each starts where its column and row say, travels its path's
distance, keeps within 8 px of its row, is present or hidden as the seed
says, never comes within 30 px of Tony's highest jump, and that the two
never meet.

Usage:  python3 tools/verify_bats.py [PRG] [seeds=12]
"""
import hashlib
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stamp_mural as sm            # noqa: E402
import verify_buddy as vb           # noqa: E402

PRG = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith(".prg") else "deliverables/prg/minimal64/tony-chamber.prg"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 12
REACH = 183                          # the top of Tony's highest jump (sprite Y at the apex)
MARGIN = 30


def main():
    data = open(PRG, "rb").read()
    off = data.find(b"MURAL02\x00") + 8
    rep = 0x0801 + off - 2 + 42      # muralBats: presence, pathA, colA, rowA, pathB, colB, rowB
    ok_all = True
    presences = set()
    for k in range(N):
        seed = hashlib.sha256(f"bats {k}".encode()).digest()
        presence, a, b = sm.bats(seed)
        presences.add(presence)
        out = tempfile.NamedTemporaryFile(suffix=".prg", delete=False).name
        subprocess.run([sys.executable, "tools/stamp_mural.py", PRG, out, "--hex", seed.hex()], check=True, capture_output=True)
        v = vb.run(out, "wait:150," + "".join(f"peek:{rep + i:X}," for i in range(7)) + "peek:D015,"
                        + "peek:D006,peek:D007,peek:D008,peek:D009,peek:D010,wait:1," * 300)
        os.unlink(out)
        r, en, t = v[:7], v[7], v[8:]
        want = [seed[27] & 15, a[0], a[1], a[2], b[0], b[1], b[2]]
        report_ok = r == want
        left_on, right_on = bool(en & 8), bool(en & 16)
        presence_ok = (left_on, right_on) == {"none": (False, False), "left only": (True, False),
                                              "right only": (False, True), "both": (True, True)}[presence]
        def track(xi, yi, msb):
            # a sample can catch the engine between writing a sprite's low X byte and its high bit (one frame in
            # three hundred at the 256 crossing): a position left of the room is such a torn read, drop it
            xs = [t[i + xi] + (256 if t[i + 4] & msb else 0) for i in range(0, len(t), 5)]
            ys = [t[i + yi] for i in range(0, len(t), 5)]
            keep = [i for i, x in enumerate(xs) if x >= 24]
            assert len(xs) - len(keep) <= 2, "too many torn reads"
            return [xs[i] for i in keep], [ys[i] for i in keep]
        checks = []
        for name, bat, on, (xi, yi, msb) in (("left", a, left_on, (0, 1, 8)), ("right", b, right_on, (2, 3, 16))):
            if not on:
                continue
            xs, ys = track(xi, yi, msb)
            x0, y0 = 24 + 8 * bat[1], 54 + 8 * bat[2]          # the engine puts a bat 4 px below the top of its row
            travel = sm.PATH_TRAVEL[bat[0]]
            c = (abs(min(xs) - x0) <= 2 and abs(max(xs) - (x0 + travel)) <= 4
                 and y0 - 8 <= min(ys) and max(ys) <= y0 + 8 and max(ys) + 21 <= REACH - MARGIN)
            checks.append((name, c, f"X {min(xs)}..{max(xs)} (want {x0}..{x0 + travel}), Y {min(ys)}..{max(ys)} (row {bat[2]} = {y0})"))
        apart = True
        if left_on and right_on:
            lx, _ = track(0, 1, 8); rx, _ = track(2, 3, 16)
            apart = max(lx) + 24 < min(rx)
        ok = report_ok and presence_ok and all(c for _, c, _ in checks) and apart
        ok_all &= ok
        print(f"seed {k:2d}: {presence:10s} report {'OK' if report_ok else 'WRONG ' + str(r)}, sprites {'OK' if presence_ok else 'WRONG'}, "
              + "; ".join(f"{n} path {bat[0]} {'OK' if c else 'FAIL'} [{d}]" for (n, c, d), bat in zip(checks, [x for x, on in ((a, left_on), (b, right_on)) if on]))
              + (f"; apart {apart}" if left_on and right_on else "") + f" -> {'OK' if ok else 'FAIL'}")
    print(f"presences seen: {sorted(presences)}")
    print("ALL OK" if ok_all else "FAILED")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
