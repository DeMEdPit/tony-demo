#!/usr/bin/env python3
"""
verify_brain.py - the brain side of the body demo (tony-body.prg) on minimal64.
senses: a twin of the sense packing in Python recomputes every nibble of the clone's sense block from raw
state (both Tonys' records, the screen, the materials) at snapshots in a dozen situations, and every
nibble must agree with what the 6502 packed. Prints one line per snapshot and ALL OK; --verbose prints
the nibbles. Every snapshot is taken after the harness's sync.
"""
import os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRG = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.join(ROOT, "deliverables/prg/minimal64/tony-body.prg")
SYM = {}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(os.path.join(ROOT, "src/kickass/tony-body.sym")).read()):
    SYM.setdefault(m.group(1), int(m.group(2), 16))
VERBOSE = "--verbose" in sys.argv
N = SYM["SENSE_COUNT"]
OV = SYM["cloneJoyOverride"]
NAMES = ["bias", "dx", "dy", "facingRight", "onGround", "inAir", "onLadder", "ducking", "floorBelow", "wallAheadFoot", "wallAheadHead",
         "brickAheadFoot", "ladderHere", "ladderBelow", "buildable", "playerAir", "lastAction", "still", "playerDuck", "playerOnLadder"]
assert len(NAMES) == N
# the raw values the block is packed from (senseRaw, copied in the clone's turn) and the packer's output for that frame
RAW = SYM["senseRaw"]
SCALARS = [("cx", RAW + 0, 2), ("cy", RAW + 2, 1), ("cs", RAW + 3, 1), ("cbg", RAW + 4, 1), ("cext", RAW + 5, 1), ("px", RAW + 6, 2), ("py", RAW + 8, 1),
           ("ps", RAW + 9, 1), ("joy", RAW + 10, 1), ("still", RAW + 11, 1), ("rawFrame", RAW + 12, 2), ("packFrame", SYM["sensePackFrame"], 2),
           ("pubFrame", SYM["cloneSensesFrame"], 2), ("count", SYM["buildCount"], 1), ("room", SYM["currentChamberNumber"], 1)]
BRICKS = SYM["brickCodes"]
def stick(bits, frames, rest=10): return f"poke:{OV:X}:{0x80 | bits:02X},wait:{frames},poke:{OV:X}:80,wait:{rest},"
def snap():
    s = "sync," + "".join(f"peek:{SYM['sensePack'] + i:X}," for i in range(N))
    for _, addr, size in SCALARS:
        s += "".join(f"peek:{addr + k:X}," for k in range(size))
    s += "".join(f"peek:{BRICKS + k:X}," for k in range(4))
    s += "".join(f"peek:{0xC000 + i:X}," for i in range(1000))
    s += "".join(f"peek:{0xBE00 + i:X}," for i in range(256))
    return s
PER = N + sum(sz for _, _, sz in SCALARS) + 4 + 1000 + 256
def run(steps):
    script = "".join(act + snap() for _, act in steps)
    with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
    r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), PRG, "@" + f.name], capture_output=True, text=True); os.unlink(f.name)
    vals = [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)]
    assert len(vals) == PER * len(steps), f"the harness did not answer every peek ({len(vals)} of {PER * len(steps)})"
    out = []
    for k in range(len(steps)):
        v = vals[k * PER:(k + 1) * PER]; d = {"name": steps[k][0], "senses": v[:N]}; i = N
        for key, _, size in SCALARS:
            d[key] = v[i] | (v[i + 1] << 8) if size == 2 else v[i]; i += size
        d["bricks"] = v[i:i + 4]; i += 4
        d["screen"] = v[i:i + 1000]; i += 1000
        d["materials"] = v[i:i + 256]
        out.append(d)
    return out
def nib(v): return v & 0x0F
def sgn(v): return v - 16 if v >= 8 else v
WALL, LADDER, FLOOR_FAR, LADDER_FAR, LADDER_TOP, BUILD_CODE = 1, 2, 8, 16, 64, SYM["BUILD_CODE"]
def twin(d):
    """The sense packing, from the raw state the block was packed from (BODY.md, 'The sense block')."""
    px, py, ps, cx, cy, cs = d["px"], d["py"], d["ps"], d["cx"], d["cy"], d["cs"]
    scr, mat = d["screen"], d["materials"]
    def cell(row, col):
        if row < 0 or row > 24: return 0, 0
        code = scr[row * 40 + ((col + 256) & 0xFF)] if 0 <= col < 40 else scr[(row * 40 + ((col + 256) & 0xFF)) % 1000]
        return code, mat[code]
    s = [0] * N
    s[0] = 7
    dx = px - cx
    m = abs(dx); b = 7 if m >= 256 else sum(1 for t in (8, 16, 24, 32, 48, 64, 128) if m >= t)
    s[1] = nib(-b if dx < 0 else b)
    dy = cy - py
    m = abs(dy); b = 7 if m >= 120 else min(7, (m + 8) >> 4)
    s[2] = nib(-b if dy < 0 else b)
    facingRight = bool(cs & 0x80); st = cs & 0x0F
    s[3] = 7 if facingRight else 0
    s[4] = 7 if st in (0, 1, 3) else 0
    s[5] = 7 if st in (4, 5, 6) else 0
    s[6] = 7 if st in (2, 7) else 0
    s[7] = 7 if st == 3 else 0
    s[8] = 7 if d["cext"] & FLOOR_FAR else 0
    top = (cy >> 3) - 6
    left, right = (cx >> 3) - 2, ((cx + 8) >> 3) - 2
    ahead = right + 1 if facingRight else left - 1
    code, mt = cell(top + 3, ahead)
    s[9] = 7 if mt & WALL else 0
    s[11] = 7 if BUILD_CODE <= code < BUILD_CODE + 4 else 0
    code, mt = cell(top, ahead)
    s[10] = 7 if mt & WALL else 0
    s[12] = 7 if d["cbg"] & LADDER else 0
    s[13] = 7 if d["cext"] & (LADDER_FAR | LADDER_TOP) else 0
    # buildable: the verb's target, four free cells, the player not in the slot
    buildable = False
    if st in (0, 1, 3):
        k2 = 19 - top
        if 0 <= k2 < 19 and k2 % 2 == 0:
            k = k2 // 2; row = 21 - 2 * k
            col = ((right + 1) | 1) if facingRight else (((left - 1) & ~1) - 1)
            if 5 <= col < 34:
                cells = [scr[r * 40 + c] for r in (row, row + 1) for c in (col, col + 1)]
                if all(c == 0 or c in d["bricks"] for c in cells):
                    bTop, bLeft, bRight = (d["py"] >> 3) - 6, (px >> 3) - 2, ((px + 8) >> 3) - 2
                    if col + 1 < bLeft or bRight < col or row + 1 < bTop or bTop + 3 < row: buildable = True
    s[14] = 7 if buildable else 0
    pst = d["ps"] & 0x0F
    s[15] = 7 if pst in (4, 5, 6) else 0
    s[18] = 7 if pst == 3 else 0
    s[19] = 7 if pst in (2, 7) else 0
    j = d["joy"]
    if j & 0x60: a = 9 if facingRight else 8
    elif j & 0x10: a = 6 if j & 4 else 7 if j & 8 else 5
    else: a = 1 if j & 4 else 2 if j & 8 else 3 if j & 1 else 4 if j & 2 else 0
    s[16] = a
    n = d["still"]; s[17] = sum(1 for t in (1, 4, 8, 16, 32, 64, 128) if n >= t)
    return s
ok = True
def check(cond, msg):
    global ok
    ok &= bool(cond); print(("  ok   " if cond else "  FAIL ") + msg)
print(f"{os.path.basename(PRG)}: {os.path.getsize(PRG)} bytes")
print("senses (every nibble of the packed block against the twin, from the raw values of the same frame):")
LAY, STEP = stick(0x20, 3), stick(0x40, 3, 20)
steps = [("start: the clone near Tony", "wait:300,"),
         ("Tony walks right, the clone walking after him", "hold:8,wait:20,"),
         ("Tony at the pillar, the clone standing", "wait:120,release:8,wait:40,"),
         ("Tony ducks", "hold:2,wait:20,"),
         ("Tony jumps, both in the air", "release:2,wait:20,joy:16:6,wait:1,"),
         ("Tony walks left past him", "wait:60,joy:4:80,wait:20,"),
         ("the clone held still; Tony walks on, turns to face him and lays a brick between them", f"poke:{OV:X}:80,joy:4:10,wait:5,joy:8:1,wait:5,joy:18:6,wait:20,joy:4:20,wait:10,"),
         ("the clone let go: he walks into the brick", f"poke:{OV:X}:00,wait:120,"),
         ("the byte: the clone turns right, a slot free ahead", stick(0x08, 1)),
         ("the frame of the lay", f"poke:{OV:X}:A0,wait:1,"),
         ("the clone steps up", f"poke:{OV:X}:80,wait:10," + STEP),
         ("the clone walks right off it", stick(0x08, 30, 40)),
         ("the clone jumps", stick(0x10, 3, 2)),
         ("the byte back", f"poke:{OV:X}:00,wait:60,")]
S = run(steps)
for d in S:
    t = twin(d); got = d["senses"]
    bad = [f"{NAMES[i]} got {sgn(got[i])} twin {sgn(t[i])}" for i in range(N) if got[i] != t[i]]
    if d["packFrame"] != d["rawFrame"]: bad.append(f"the packer is behind: raw frame {d['rawFrame']}, packed {d['packFrame']}")
    if not (d["rawFrame"] - 2 <= d["pubFrame"] <= d["rawFrame"]): bad.append(f"the published block is stale: frame {d['pubFrame']} of {d['rawFrame']}")
    if VERBOSE: print("       ", {NAMES[i]: sgn(got[i]) for i in range(N)}, f"| Tony {d['px']},{d['py']} s{d['ps']} clone {d['cx']},{d['cy']} s{d['cs']} joy {d['joy']:02x}")
    check(not bad, f"{d['name']}: {N - len(bad)} of {N} nibbles agree" + ("; " + "; ".join(bad) if bad else ""))
# the situations the run was built to reach, so the twin was not idle
by = {d["name"]: d["senses"] for d in S}
check(by["Tony walks right, the clone walking after him"][NAMES.index("still")] == 0 and by["Tony walks right, the clone walking after him"][NAMES.index("lastAction")] == 2, "walking after Tony: still 0, last action right")
check(by["Tony ducks"][NAMES.index("playerDuck")] == 7 and by["Tony ducks"][NAMES.index("ducking")] == 7, "Tony ducking: playerDuck and ducking set")
check(by["Tony jumps, both in the air"][NAMES.index("playerAir")] == 7 and by["Tony jumps, both in the air"][NAMES.index("inAir")] == 7, "the jump: playerAir and inAir set")
check(by["the clone let go: he walks into the brick"][NAMES.index("wallAheadFoot")] == 7 and by["the clone let go: he walks into the brick"][NAMES.index("brickAheadFoot")] == 7, "blocked by a placed brick: wallAheadFoot and brickAheadFoot set")
check(by["the byte: the clone turns right, a slot free ahead"][NAMES.index("buildable")] == 7 and by["the byte: the clone turns right, a slot free ahead"][NAMES.index("wallAheadFoot")] == 0, "turned away from it: a free slot ahead, buildable set")
check(by["the frame of the lay"][NAMES.index("lastAction")] == 9, "the frame of the lay: last action build right")
check(by["the clone steps up"][NAMES.index("floorBelow")] == 7 and by["the clone steps up"][NAMES.index("onGround")] == 7, "after the step up: on the ground, floor below")

# ---------------------------------------------------------------- the brain slot
import random
print("slot:")
MARK, KIND, W, MOOD = SYM["brainMarker"], SYM["brainKind"], SYM["brainWeights"], SYM["brainMood"]
TRUN, TIN, TACC, TACT = SYM["brainTestRun"], SYM["brainTestIn"], SYM["brainTestAcc"], SYM["brainTestAction"]
THINKS, ACTION, COUNT = SYM["brainThinks"], SYM["brainAction"], SYM["buildCount"]
def peeks(addr, n): return "".join(f"peek:{addr + i:X}," for i in range(n))
def pokes(addr, data): return "".join(f"poke:{addr + i:X}:{b & 0xFF:02X}," for i, b in enumerate(data))
def harness(script):
    with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
    r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), PRG, "@" + f.name], capture_output=True, text=True); os.unlink(f.name)
    return [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)]
v = harness("wait:300,sync," + peeks(MARK, 16))
check(MARK % 256 == 0, f"the block is page-aligned (at ${MARK:04X})")
check(bytes(v[:8]) == b"BRAIN01\0", f"the marker reads BRAIN01: {bytes(v[:7])!r}")
check(v[8:14] == [0, 1, N, 0, 10, 4], f"the header: kind {v[8]}, layout {v[9]}, inputs {v[10]}, hidden {v[11]}, outputs {v[12]}, period {v[13]}")
check(W == MARK + 16 and MOOD == MARK + 16 + 256, "the weights at +16, the mood at +272")

print("forward sweep (the 6502 against a Python forward on random weights, moods and senses):")
def forward(w, mood, x):
    """The reference: w[o][i] signed nibbles, x[i] signed nibbles, mood[o] signed nibbles; acc[o] = sum w x + mood * 16; the first largest."""
    acc = [sum(w[o][i] * x[i] for i in range(N)) + mood[o] * 16 for o in range(10)]
    return acc, max(range(10), key=lambda o: (acc[o], -o))
random.seed(1)
script = "wait:300,"; cases = []
for k in range(40):
    w = [[random.randint(-8, 7) for _ in range(N)] for _ in range(10)]
    mood = [random.randint(-8, 7) for _ in range(10)]
    x = [random.randint(-8, 7) for _ in range(N)]
    if k == 0: w = [[0] * N for _ in range(10)]; mood = [0] * 10          # all zero: the first output wins the tie
    if k == 1: w = [[7] * N for _ in range(10)]; x = [-8] * N; mood = [-8] * 10   # the most negative accumulator
    if k == 2: w = [[-8] * N for _ in range(10)]; x = [-8] * N; mood = [7] * 10   # the most positive
    wb = bytes((w[o][i] & 15) | ((w[o][i + 1] & 15) << 4) for o in range(10) for i in range(0, N, 2))
    mb = bytes((mood[o] & 15) | ((mood[o + 1] & 15) << 4) for o in range(0, 10, 2))
    xb = bytes(xi & 15 for xi in x)
    cases.append(forward(w, mood, x))
    script += pokes(W, wb) + pokes(MOOD, mb) + pokes(TIN, xb) + f"poke:{TRUN:X}:01,wait:2,sync," + peeks(TACC, 20) + peeks(TACT, 1) + peeks(TRUN, 1)
v = harness(script)
bad = 0
for k, (acc, act) in enumerate(cases):
    got = v[k * 22:(k + 1) * 22]
    gacc = [((got[2 * o] | (got[2 * o + 1] << 8)) ^ 0x8000) - 0x8000 for o in range(10)]
    if gacc != acc or got[20] != act or got[21] != 0:
        bad += 1
        if bad <= 3: print(f"       case {k}: 6502 acc {gacc} action {got[20]} run {got[21]}; reference acc {acc} action {act}")
check(bad == 0, f"{len(cases)} vectors, accumulators and the chosen action: {len(cases) - bad} agree")

print("two weights (kind 1):")
follow = [[0] * N for _ in range(10)]; follow[2][1] = 7; follow[1][1] = -7; follow[0][0] = 1
def wbytes(w): return bytes((w[o][i] & 15) | ((w[o][i + 1] & 15) << 4) for o in range(10) for i in range(0, N, 2))
snapB = "sync," + peeks(SYM["physPlayerX"], 2) + peeks(SYM["cloneX"], 2) + peeks(SYM["cloneY"], 1) + peeks(THINKS, 2) + peeks(ACTION, 1) + peeks(COUNT, 1) + peeks(SYM["bodyFrames"], 2)
v = harness("wait:300," + pokes(W, wbytes(follow)) + f"poke:{KIND:X}:01,wait:150," + snapB + "joy:8:60,wait:150," + snapB)
def rowB(v, k):
    d = v[k * 11:(k + 1) * 11]
    return dict(px=d[0] | d[1] << 8, cx=d[2] | d[3] << 8, cy=d[4], thinks=d[5] | d[6] << 8, action=d[7], count=d[8], frames=d[9] | d[10] << 8)
a, b = rowB(v, 0), rowB(v, 1)
check(abs(a["px"] - a["cx"]) < 16 and a["cy"] == 206, f"right when dx is positive, left when negative, idle within 16 px (a bucket of one ties the bias, and the first output wins a tie): he came to {a['cx']} beside Tony at {a['px']}")
check(abs(b["px"] - b["cx"]) < 16 and b["px"] > 270, f"and followed Tony to the pillar (Tony {b['px']}, the clone {b['cx']})")
check(b["thinks"] - a["thinks"] >= (b["frames"] - a["frames"]) // 4 - 2, f"a think every four frames: {b['thinks'] - a['thinks']} thinks in {b['frames'] - a['frames']} frames")
build = [[0] * N for _ in range(10)]; build[8][14] = 7; build[0][0] = 2
v = harness("wait:300,joy:8:60,wait:100," + pokes(W, wbytes(build)) + f"poke:{KIND:X}:01,wait:200," + snapB + "wait:100," + snapB)
a, b = rowB(v, 0), rowB(v, 1)
check(a["count"] >= 3 and a["cy"] <= 158, f"build left whenever a slot is free: a staircase of {a['count']} in 200 frames, up at Y {a['cy']}")
check(b["count"] >= a["count"] and b["cy"] <= a["cy"], f"and on: {b['count']} bricks, Y {b['cy']}")

print("the builder (kind 2):")
snapC = "sync," + peeks(SYM["physPlayerX"], 2) + peeks(SYM["physPlayerY"], 1) + peeks(SYM["physPlayerState"], 1) + peeks(SYM["cloneX"], 2) + peeks(SYM["cloneY"], 1) + peeks(SYM["cloneState"], 1) + peeks(COUNT, 1) + peeks(SYM["currentChamberNumber"], 1) + peeks(SYM["buildLadderCol"], 1)
def rowC(v, k):
    d = v[k * 11:(k + 1) * 11]
    return dict(px=d[0] | d[1] << 8, py=d[2], ps=d[3], cx=d[4] | d[5] << 8, cy=d[6], cs=d[7], count=d[8], room=d[9], ladder=d[10])
# a brick between them: he jumps it and comes to Tony
v = harness("wait:300,joy:18:6,wait:20,joy:8:150,wait:100," + snapC + f"poke:{KIND:X}:02,wait:100," + snapC + "wait:100," + snapC)
a, b, c = rowC(v, 0), rowC(v, 1), rowC(v, 2)
check(a["count"] == 1 and a["cx"] <= 162 and a["px"] >= 270, f"Tony lays a brick between them and walks to {a['px']}; the follow rule leaves the clone at the brick, X {a['cx']}")
check(c["cx"] > a["cx"] + 40 and abs(c["px"] - c["cx"]) < 48 and c["cy"] == 206, f"kind 2: he jumps the brick and comes to within 48 px of Tony (X {b['cx']} after 100 frames, {c['cx']} after 200)")
# Tony builds five bricks under the ladder and climbs part of it; the clone climbs the stairs and the ladder to him
C = a["ladder"]
if C >= 13:
    t = 8 * C - 60
    walk = f"joy:8:{(t - 184) // 2}," if t > 184 else f"joy:4:{(246 - 8 * C) // 2},joy:8:1,"
else:
    t = 8 * C + 99
    walk = f"joy:4:{(184 - t) // 2}," if t < 184 else f"joy:8:{(t - 184) // 2},joy:4:1,"
stair = "".join("joy:18:6,wait:20,joy:17:6,wait:30," for _ in range(5))
v = harness("wait:300," + walk + "wait:20," + stair + "wait:10,hold:1,wait:50,release:1,wait:10," + snapC + f"poke:{KIND:X}:02,wait:120," + snapC + "wait:120," + snapC + "wait:120," + snapC)
a, b, c, d = rowC(v, 0), rowC(v, 1), rowC(v, 2), rowC(v, 3)
check(a["count"] == 5 and (a["ps"] & 0x7f) in (2, 7) and a["py"] < 100 and a["room"] == 0, f"Tony builds five bricks under the ladder and climbs part of it (Y {a['py']}); the clone waits below at X {a['cx']}, Y {a['cy']}")
check(b["cy"] < 206, f"kind 2: after 120 frames he is on the stairs (Y {b['cy']}, X {b['cx']})")
check(d["cy"] <= a["py"] + 16 and (d["cs"] & 0x7f) in (2, 7) and abs(d["cx"] - d["px"]) < 16 and d["room"] == 0,
      f"after 360 frames he is on the ladder beside Tony (Y {d['cy']} to Tony's {d['py']}, state {d['cs']}), unaided")
# the builder on from the start: he keeps out of Tony's way while Tony builds, then follows him up
v = harness(f"wait:300,poke:{KIND:X}:02,wait:60," + walk + "wait:20," + stair + "wait:10," + snapC + "hold:1,wait:50,release:1,wait:300," + snapC)
a, b = rowC(v, 0), rowC(v, 1)
check(a["count"] == 5, f"the builder on while Tony builds: he stays out of the slots, all five bricks laid (count {a['count']}); he is at X {a['cx']}, Y {a['cy']}")
check(b["cy"] <= b["py"] + 16 and (b["cs"] & 0x7f) in (2, 7) and abs(b["cx"] - b["px"]) < 16, f"and when Tony climbs he follows up the stairs and the ladder to him (Y {b['cy']} to Tony's {b['py']})")
print("ALL OK" if ok else "FAILURES"); sys.exit(0 if ok else 1)
