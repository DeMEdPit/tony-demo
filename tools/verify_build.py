#!/usr/bin/env python3
"""
verify_build.py - runs the building demo (deliverables/prg/minimal64/tony-build.prg) on minimal64 and checks
the verb: a brick laid in front at foot level, the count, stepping up a staircase of three, a fourth laid and
lifted from the top with the mural brick under it restored, walking off the top; and the Shadow walled off.
Prints one line per check and ALL OK.
"""
import os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "deliverables/prg/minimal64/tony-build.prg")
SYM = {}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(os.path.join(ROOT, "src/kickass/tony-build.sym")).read()):
    SYM.setdefault(m.group(1), int(m.group(2), 16))
A = [SYM[k] for k in ("physPlayerX", "physPlayerY", "physPlayerState", "buddyX", "buddyY", "buildCount")]
ROWS, COLS = range(13, 24), range(3, 37)
def snap(): return "".join(f"peek:{a:X}," for a in (A[0], A[0] + 1, A[1], A[2], A[3], A[3] + 1, A[4], A[5]))
def wall(): return "".join(f"peek:{0xC000 + r * 40 + c:X}," for r in ROWS for c in COLS)
SCENARIOS = {
  "stairs": [("start", "wait:300,"), ("turn right", "joy:8:2,wait:10,"), ("lay", "joy:18:6,wait:20,"), ("step up", "joy:17:6,wait:30,"),
             ("lay", "joy:18:6,wait:20,"), ("step up", "joy:17:6,wait:30,"), ("lay", "joy:18:6,wait:20,"), ("step up", "joy:17:6,wait:30,"),
             ("lay a fourth", "joy:18:6,wait:20,"), ("lift it", "joy:18:6,wait:20,"), ("walk left off", "joy:4:60,wait:90,")],
  "wall": [("start", "wait:300,"), ("lay between us", "joy:18:6,wait:20,"), ("walk right 150", "joy:8:150,wait:60,"), ("wait 200", "wait:200,")],
}
ok = True
def check(cond, msg):
    global ok
    ok &= bool(cond); print(("  ok   " if cond else "  FAIL ") + msg)
def run(steps):
    script = "".join(act + snap() + wall() for _, act in steps)
    with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
    r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), PRG, "@" + f.name], capture_output=True, text=True); os.unlink(f.name)
    vals = [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)]
    per = 8 + len(ROWS) * len(COLS); assert len(vals) == per * len(steps), "the harness did not answer every peek"
    out = []
    for k in range(len(steps)):
        v = vals[k * per:(k + 1) * per]
        out.append(dict(x=v[0] | (v[1] << 8), y=v[2], state=v[3], bx=v[4] | (v[5] << 8), by=v[6], count=v[7], cells=v[8:]))
    return out
def placed(s): return sum(1 for c in s["cells"] if 0x40 <= c <= 0x43)
print(f"{os.path.basename(PRG)}: {os.path.getsize(PRG)} bytes")
print("stairs:")
s = run(SCENARIOS["stairs"])
check(s[0]["y"] == 206 and s[0]["count"] == 0 and placed(s[0]) == 0, "boots into the room, Tony on the floor, no bricks")
check(s[2]["count"] == 1 and placed(s[2]) == 4, "down + fire lays one brick (four cells)")
check(s[3]["y"] == 190 and s[3]["x"] == s[2]["x"] + 15, "up + fire steps him onto it, one brick higher, over its columns")
check(s[5]["y"] == 174 and s[5]["count"] == 2, "a second brick from up there and a second step up")
check(s[7]["y"] == 158 and s[7]["count"] == 3 and placed(s[7]) == 12, "three bricks high")
check(s[8]["count"] == 4 and placed(s[8]) == 16, "a fourth laid from the top")
check(s[9]["count"] == 3 and s[9]["cells"] == s[7]["cells"], "lifted again: the wall exactly as before it, mural bricks restored")
check(s[10]["y"] == 206 and s[10]["x"] < s[9]["x"], "walking off the top drops him to the floor")
print("wall:")
w = run(SCENARIOS["wall"])
check(w[1]["count"] == 1 and w[1]["bx"] < w[1]["x"], "a brick laid between Tony and the Shadow")
check(w[2]["x"] >= 280 and w[3]["bx"] <= 160, f"Tony walks to {w[2]['x']}, the Shadow stops at the brick (X {w[3]['bx']})")
print("ALL OK" if ok else "SOMETHING FAILED")
sys.exit(0 if ok else 1)
