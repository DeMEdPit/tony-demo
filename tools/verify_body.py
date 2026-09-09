#!/usr/bin/env python3
"""
verify_body.py - runs the body demo (deliverables/prg/minimal64/tony-body.prg) on minimal64 and checks the
clone's body: he follows the player on the player's own physics (walks, stops, ducks, jumps in the same frame
as the player), a brick laid between them stops him, and, with the bench holding his joystick byte
(cloneJoyOverride), he lays bricks, steps up them, walks off the top, jumps, climbs the dangling ladder and
stops at the north stop without changing room; and he waits in his room while the player is above.
Prints one line per check and ALL OK; --shots DIR keeps screenshots.
Every snapshot is taken after the harness's sync (the raster in the top border), so a peek never lands
inside the clone's turn, where his record and the player's physics block have changed places.
"""
import os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRG = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.join(ROOT, "deliverables/prg/minimal64/tony-body.prg")
SYMFILE = os.path.join(ROOT, "src/kickass/tony-body.sym")
SYM = {}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(SYMFILE).read()):
    SYM.setdefault(m.group(1), int(m.group(2), 16))
A = [SYM[k] for k in ("physPlayerX", "physPlayerY", "physPlayerState", "cloneX", "cloneY", "cloneState", "buildCount", "currentChamberNumber", "buildLadderCol", "bodyRasterMax", "bodyOverruns", "bodySelfTestBad", "bodySelfTestDone")]
OV = SYM["cloneJoyOverride"]; NORTH = SYM["CLONE_NORTH_STOP"]; RUN = SYM["bodySelfTestRun"]
SHOTS = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None
VERBOSE = "--verbose" in sys.argv        # print every snapshot's fields
ROWS, COLS = range(13, 24), range(3, 37)
def snap(): return "sync," + "".join(f"peek:{a:X}," for a in (A[0], A[0] + 1, A[1], A[2], A[3], A[3] + 1, A[4], A[5], A[6], A[7], A[8], 0xD015, 0xD00A, 0xD00B, A[9], A[10], A[11], A[11] + 1, A[12]))
def wall(): return "".join(f"peek:{0xC000 + r * 40 + c:X}," for r in ROWS for c in COLS)
def stick(bits, frames, rest=10): return f"poke:{OV:X}:{0x80 | bits:02X},wait:{frames},poke:{OV:X}:80,wait:{rest},"
LAY, STEP = stick(0x20, 3), stick(0x40, 3, 20)
ok = True
RASTER, OVERRUNS = [], []      # the clone's turn: the latest raster line it ended on, and the turns that ended too late
def check(cond, msg):
    global ok
    ok &= bool(cond); print(("  ok   " if cond else "  FAIL ") + msg)
def run(steps):
    script = "".join(act + snap() + wall() for _, act in steps)
    with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
    r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), PRG, "@" + f.name], capture_output=True, text=True); os.unlink(f.name)
    vals = [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)]
    per = 19 + len(ROWS) * len(COLS); assert len(vals) == per * len(steps), f"the harness did not answer every peek ({len(vals)} of {per * len(steps)})"
    out = []
    for k in range(len(steps)):
        v = vals[k * per:(k + 1) * per]
        out.append(dict(x=v[0] | (v[1] << 8), y=v[2], state=v[3], cx=v[4] | (v[5] << 8), cy=v[6], cs=v[7], count=v[8], room=v[9], ladder=v[10],
                        sprites=v[11], sx=v[12], sy=v[13], raster=v[14], overruns=v[15], bad=v[16] | (v[17] << 8), sweeps=v[18], cells=v[19:]))
        RASTER.append(v[14]); OVERRUNS.append(v[15])
        if VERBOSE: print("       ", steps[k][0] + ":", {a: b for a, b in out[-1].items() if a != "cells"}, "placed", placed(out[-1]))
    return out
def placed(s): return sum(1 for c in s["cells"] if 0x50 <= c <= 0x53)
def near(s): return abs(s["x"] - s["cx"]) < 52
def shot(name): return f"shot:{SHOTS}/{name}.ppm," if SHOTS else ""
ON_GROUND, WALKING, LADDER, DUCK, JUMPING_UP, LADDER_STOP = 0, 1, 2, 3, 5, 7
def pose(s): return s["cs"] & 0x7f
print(f"{os.path.basename(PRG)}: {os.path.getsize(PRG)} bytes")

print("follow:")
s = run([("start", "wait:300," + shot("body-start")), ("Tony walks right 60", "joy:8:60,wait:100," + shot("body-follow")),
         ("Tony walks left 120", "joy:4:120,wait:150,"), ("Tony ducks", "hold:2,wait:30," + shot("body-duck")), ("Tony stands", "release:2,wait:30,")])
check(s[0]["y"] == 206 and s[0]["cy"] == 206 and pose(s[0]) == ON_GROUND and 120 < s[0]["cx"] < s[0]["x"] and near(s[0]),
      f"boots into the room: the clone walked from 120 to {s[0]['cx']}, on the floor, near Tony at {s[0]['x']}")
check(s[0]["sx"] == s[0]["cx"] and s[0]["sy"] == s[0]["cy"] and (s[0]["sprites"] & 0xE0) == 0xE0, "his sprites are where his record says")
check(s[1]["x"] >= 270 and near(s[1]) and s[1]["cy"] == 206, f"Tony at the right pillar ({s[1]['x']}), the clone followed to {s[1]['cx']}")
check(s[2]["x"] < 120 and near(s[2]) and s[2]["cy"] == 206, f"Tony back left ({s[2]['x']}), the clone followed to {s[2]['cx']}")
check(pose(s[3]) == DUCK and (s[3]["state"] & 0x7f) == DUCK, "Tony ducks, the clone ducks")
check(pose(s[4]) == ON_GROUND, "and stands again")

print("jump:")
j = run([("start", "wait:300,"), ("Tony jumps", "joy:16:6,wait:2," + shot("body-jump")), ("mid-air", "wait:6,"), ("landed", "wait:60,")])
check(pose(j[1]) == JUMPING_UP and (j[1]["state"] & 0x7f) == JUMPING_UP and j[1]["cy"] == j[1]["y"] < 206,
      f"the clone jumps in the same frame as Tony: both at Y {j[1]['y']}")
check(j[2]["cy"] == j[2]["y"] < 195, f"still together in the air at Y {j[2]['y']}")
check(j[3]["cy"] == 206 and j[3]["y"] == 206 and pose(j[3]) == ON_GROUND, "both back on the floor")

print("wall:")
w = run([("start", "wait:300,"), ("Tony lays a brick between us", "joy:18:6,wait:20,"), ("Tony walks right 150", "joy:8:150,wait:200," + shot("body-wall"))])
check(w[1]["count"] == 1 and placed(w[1]) == 4 and w[1]["cx"] < w[1]["x"], "a brick laid between Tony and the clone")
check(w[2]["x"] >= 270 and w[1]["cx"] <= w[2]["cx"] <= 162 and w[2]["cy"] == 206 and pose(w[2]) == WALKING,
      f"Tony walks to {w[2]['x']}; the clone walks into the brick and stays at X {w[2]['cx']} (his physics, not a rule)")

print("drive (the bench holds his joystick byte):")
d = run([("start", "wait:300,"), ("Tony walks right 60, the clone follows", "joy:8:60,wait:80,"),
         ("walk left 50 frames", stick(0x08 >> 1, 50)), ("face right", stick(0x08, 1)), ("lay", LAY), ("step up", STEP),
         ("lay, step up", LAY + STEP), ("lay, step up", LAY + STEP + shot("body-stairs")),
         ("walk left, off the top", stick(0x04, 60, 40)), ("jump", stick(0x10, 3)), ("landed", "wait:40,"),
         ("the byte back to the brain", f"poke:{OV:X}:00,wait:150," + shot("body-blocked"))])
check(d[1]["x"] >= 270 and near(d[1]), f"Tony at {d[1]['x']}, the clone at {d[1]['cx']}")
check(d[2]["cx"] == d[1]["cx"] - 100 and d[2]["cs"] == ON_GROUND, f"bit 2 for fifty frames: a hundred pixels left, to {d[2]['cx']}, two a frame")
check(d[3]["cx"] == d[2]["cx"] + 2 and d[3]["cs"] == 0x80 | ON_GROUND, "bit 3 for one frame: two pixels right, facing right")
check(d[4]["count"] == 1 and placed(d[4]) == 4 and d[4]["cy"] == 206 and d[4]["cx"] == d[3]["cx"], "bit 5 lays a brick in front of him")
check(d[5]["cy"] == 190 and d[5]["cx"] > d[4]["cx"] and d[5]["cs"] == 0x80 | ON_GROUND, f"bit 6 steps him onto it (Y 190, X {d[5]['cx']})")
check(d[6]["cy"] == 174 and d[6]["count"] == 2, "a second brick and step")
check(d[7]["cy"] == 158 and d[7]["count"] == 3 and placed(d[7]) == 12, "three bricks high")
check(d[8]["cy"] == 206 and d[8]["cx"] < d[4]["cx"], f"walking left off the top drops him down the stairs to the floor (X {d[8]['cx']})")
check(pose(d[9]) == JUMPING_UP and d[9]["cy"] < 200, f"bit 4 makes him jump (Y {d[9]['cy']})")
check(d[10]["cy"] == 206 and pose(d[10]) == ON_GROUND, "and he lands")
check(d[11]["x"] >= 270 and pose(d[11]) == WALKING and d[4]["cx"] - 4 <= d[11]["cx"] <= d[4]["cx"] + 12 and d[11]["cy"] == 206,
      f"the brain again: he walks towards Tony until his own stairs stop him (X {d[11]['cx']}); the follow rule does not jump")

print("ladder (the bench builds him up to it):")
probe = run([("start", "wait:300,")])
C, cx = probe[0]["ladder"], probe[0]["cx"]
print(f"  the ladder hangs at columns {C}-{C + 1} (seeded); the clone starts from X {cx}")
if C >= 13:   # build rightward: brick 1 at C - 8, his right column C - 9 -> X in 8C - 64 .. 8C - 57
    lo, hi, face = 8 * C - 64, 8 * C - 57, 0x08
else:         # build leftward: brick 1 at C + 8, his left column C + 10 -> X in 8C + 96 .. 8C + 103
    lo, hi, face = 8 * C + 96, 8 * C + 103, 0x04
target = next(t for t in range(lo + 1, hi) if (t - cx) % 2 == 0)       # two pixels a frame keep his parity; a frame of turning fits inside
walk = stick(0x08, (target - cx) // 2) if target > cx else stick(0x04, (cx - target) // 2)
L = run([("start", "wait:300,"), ("walk under the ladder's approach", walk + stick(face, 1)),
         ("five bricks up", (LAY + STEP) * 5 + shot("body-ladder-foot")),
         ("up for 200 frames", stick(0x01, 200, 30) + shot("body-ladder-top")),
         ("down for 160 frames", stick(0x02, 160, 60))])
check(L[2]["count"] == 5 and 118 <= L[2]["cy"] <= 126 and L[2]["room"] == 0, f"five bricks laid and climbed, the ladder in reach (Y {L[2]['cy']}, count {L[2]['count']})")
check(L[3]["cy"] == NORTH and pose(L[3]) == LADDER_STOP and L[3]["room"] == 0 and (L[3]["sprites"] & 0x60) == 0x60,
      f"he climbs the ladder and hangs at the north stop (Y {L[3]['cy']}, state {L[3]['cs']}), in his room, in view")
check(118 <= L[4]["cy"] <= 126 and pose(L[4]) == ON_GROUND and L[4]["room"] == 0, f"and climbs down onto the bricks (Y {L[4]['cy']})")

print("rooms (Tony climbs into the room above):")
if C >= 13:
    t = 8 * C - 60
    walk = f"joy:8:{(t - 184) // 2}," if t > 184 else f"joy:4:{(246 - 8 * C) // 2},joy:8:1,"
else:
    t = 8 * C + 99
    walk = f"joy:4:{(184 - t) // 2}," if t < 184 else f"joy:8:{(t - 184) // 2},joy:4:1,"
stair = "".join("joy:18:6,wait:20,joy:17:6,wait:30," for _ in range(5))
SWEEP = f"poke:{RUN:X}:01,wait:400,"
R = run([("start", "wait:300,"), ("Tony walks under the ladder's approach", walk + "wait:20,"), ("five bricks up", stair + "wait:10,"),
         ("the collision sweep, below", SWEEP),
         ("climb: hold up 200 frames", "hold:1,wait:200,release:1,wait:30," + shot("body-room-above")), ("a hundred frames above", "wait:100,"),
         ("the collision sweep, above", SWEEP),
         ("climb down: hold down 160 frames", "hold:2,wait:160,release:2,wait:60," + shot("body-room-below-again"))])
check(R[2]["count"] == 5 and R[2]["room"] == 0, f"Tony builds five bricks under the ladder (count {R[2]['count']})")
check(R[3]["sweeps"] == 1 and R[3]["bad"] == 0, f"the faster collision check agrees with the game's own at every position of the room below, bricks laid ({R[3]['bad']} differ)")
R = R[:3] + R[4:6] + R[7:]     # the sweeps out of the way of the numbering below
check(R[3]["room"] == 1 and (R[3]["sprites"] & 0x60) == 0, f"Tony in the room above (room {R[3]['room']}); the clone's sprites off")
check(R[4]["room"] == 1 and (R[4]["cx"], R[4]["cy"], R[4]["cs"]) == (R[3]["cx"], R[3]["cy"], R[3]["cs"]), f"the clone waits: his record unchanged a hundred frames later (X {R[4]['cx']}, Y {R[4]['cy']})")
check(R[5]["room"] == 0 and (R[5]["sprites"] & 0x60) == 0x60 and R[5]["cy"] == 206 and pose(R[5]) in (ON_GROUND, WALKING),
      f"Tony back below: the clone is there, on the floor, following again (X {R[5]['cx']}, state {R[5]['cs']})")
check(R[5]["sweeps"] == 2 and R[5]["bad"] == 0, f"and the check agrees with the game's own in the room above too ({R[5]['bad']} differ)")
print("time:")
check(max(OVERRUNS) == 0, f"no turn of the clone ended on raster line 250 or later ({len(OVERRUNS)} snapshots)")
check(max(RASTER) < 230, f"the latest a turn ended: raster line {max(RASTER)} (the visual handler's line is 255)")
print("ALL OK" if ok else "FAILURES"); sys.exit(0 if ok else 1)
