#!/usr/bin/env python3
"""
teach_demo.py - the engine milestone (E5) on the harness, no contract needed:
  1. kind 0 boots and follows (the follow rule);
  2. TEACH from zero, through the page's flag and through the chord, the stick driving the clone;
  3. the weights change, the first lesson makes him kind 1, a lesson flashes him white;
  4. let go: he drives what he was taught, which is not what the follow rule did;
  5. a reload forgets: a fresh boot is kind 0 with zero weights;
  6. the number: teaching sessions of follow-and-climb from zero until he climbs Tony's stairs and the ladder
     to him on his own, and the lessons that took.
Prints the story and ALL OK; the number is the last line. Usage: teach_demo.py [PRG [SAVE]]; SAVE keeps the
weights that climbed (the first hundred bytes of the slot, loadable with the harness).
"""
import os, re, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "deliverables/prg/minimal64/tony-body.prg")
SAVE = sys.argv[2] if len(sys.argv) > 2 else None      # where to keep the weights that climbed (100 bytes)
SYM = {}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(os.path.join(ROOT, "src/kickass/tony-body.sym")).read()):
    SYM.setdefault(m.group(1), int(m.group(2), 16))
W, KIND, TEACH, LCOUNT, LTOTAL = SYM["brainWeights"], SYM["brainKind"], SYM["teachMode"], SYM["lessonCount"], SYM["lessonTotal"]
def pk(addr, n=1): return "".join(f"peek:{addr + i:X}," for i in range(n))
SNAP = "sync," + pk(SYM["physPlayerX"], 2) + pk(SYM["physPlayerY"]) + pk(SYM["physPlayerState"]) + pk(SYM["cloneX"], 2) + pk(SYM["cloneY"]) + pk(SYM["cloneState"]) + pk(KIND) + pk(TEACH) + pk(LCOUNT, 2) + pk(LTOTAL, 2) + pk(SYM["buildCount"]) + pk(SYM["cloneFlash"]) + pk(SYM["buddyColourNow"])
PER = 17
def run(script):
    with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
    r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), PRG, "@" + f.name], capture_output=True, text=True); os.unlink(f.name)
    return [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)], r.stdout
def row(v, k):
    d = v[k * PER:(k + 1) * PER]
    return dict(px=d[0] | d[1] << 8, py=d[2], ps=d[3], cx=d[4] | d[5] << 8, cy=d[6], cs=d[7], kind=d[8], teach=d[9], count=d[10] | d[11] << 8,
                total=d[12] | d[13] << 8, bricks=d[14], flash=d[15], colour=d[16])
ok = True
def check(cond, msg):
    global ok
    ok &= bool(cond); print(("  ok   " if cond else "  FAIL ") + msg)
print(f"{os.path.basename(PRG)}: {os.path.getsize(PRG)} bytes")

print("1. kind 0 boots and follows:")
v, _ = run("wait:300," + SNAP + "joy:8:60,wait:100," + SNAP)
a, b = row(v, 0), row(v, 1)
check(a["kind"] == 0 and a["teach"] == 0 and a["count"] == 0, f"a fresh boot: kind {a['kind']}, no lessons")
check(abs(b["px"] - b["cx"]) < 52 and b["px"] > 270, f"the follow rule: Tony at {b['px']}, the clone at {b['cx']}")

print("2. TEACH from zero, the page's way (the flag) and the stick's way (the lay chord held a second):")
# the flag: teach "right" for forty frames with the stick, then let go
v, _ = run("wait:300," + f"poke:{TEACH:X}:01,hold:8,wait:40,release:8,wait:2," + SNAP + f"poke:{TEACH:X}:00,wait:150," + SNAP + pk(W, 100) + "wait:1," + pk(W, 100))
a, b = row(v, 0), row(v, 1)
wts = v[2 * PER:2 * PER + 100]
check(a["teach"] == 1 and a["px"] == 184 and a["cx"] > 200, f"while teaching Tony stands at {a['px']} and the stick walks the clone to {a['cx']}")
check(a["count"] >= 1 and a["kind"] == 1, f"lessons taken: {a['total']} ({a['count']} recorded); the first made him kind {a['kind']}")
check(any(wts), f"the weights are no longer zero ({sum(1 for x in wts if x)} of 100 bytes set)")
print("3. let go: he drives what he was taught:")
check(b["teach"] == 0 and b["cx"] > a["cx"] + 40, f"taught 'right', he keeps walking right on his own brain: {a['cx']} -> {b['cx']} (the follow rule would have stopped beside Tony at {b['px']})")
# the chord
v, _ = run("wait:300,hold:18,wait:60,release:18,wait:10," + SNAP + "hold:18,wait:60,release:18,wait:10," + SNAP)
a, b = row(v, 0), row(v, 1)
check(a["teach"] == 1 and a["bricks"] == 0, f"the lay chord held a second turns teaching on, and the brick its press laid is taken back (bricks {a['bricks']})")
check(b["teach"] == 0 and b["bricks"] == 0, f"a second hold turns it off, the clone's brick taken back the same way (bricks {b['bricks']})")
print("4. a lesson flashes him white:")
v, out = run("wait:300," + f"poke:{TEACH:X}:01,hold:4,wait:3," + SNAP + "wait:1," + SNAP)
a, b = row(v, 0), row(v, 1)
check((a["flash"] > 0 and a["colour"] == 1) or (b["flash"] > 0 and b["colour"] == 1), f"the press is an edge, so its lesson is taken at once and flashes him white within the frame (flash frames left {a['flash']}, colour {a['colour']}, lessons {a['total']})")
print("5. a reload forgets:")
v, _ = run("wait:300," + SNAP + pk(W, 100))
a = row(v, 0); wts = v[PER:PER + 100]
check(a["kind"] == 0 and not any(wts), "a fresh boot is kind 0 with all-zero weights")

print("6. the number: sessions of follow-and-climb from zero until he does it alone:")
# The teacher is a policy over the clone's own senses, decided every think period from the published block
# and pressed on the port (the program routes the port to the clone while teaching), so every state gets
# one consistent label: the builder's rule, driven by hand. A scripted sequence with pauses teaches "stand
# still" in the very state where "jump" was just taught, and cancels itself.
class Machine:
    """the harness driven line by line"""
    def __init__(self):
        self.p = subprocess.Popen([os.path.join(ROOT, "tools/m64-harness/m64run"), PRG, "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    def do(self, line):
        self.p.stdin.write(line + "\n"); self.p.stdin.flush()
        out = []
        while True:
            l = self.p.stdout.readline()
            if not l or l.strip() == "ok": break
            out.append(l)
        return [int(m, 16) for l in out for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", l)]
    def close(self):
        try: self.p.stdin.close(); self.p.wait(timeout=5)
        except Exception: self.p.kill()
SENSES = SYM["cloneSenses"]
def sgn(x): return x - 16 if x >= 8 else x
def read(m):
    v = m.do("sync," + SNAP + pk(SENSES, 20))
    d = row(v, 0); d["senses"] = [sgn(x) for x in v[PER:PER + 20]]; return d
def teacher(sn):
    """the builder's rule as joystick lines: 1 up, 2 down, 4 left, 8 right, 16 fire, decided from the
    published block. In the air: nothing (the physics finish the jump; a jump held through the air
    would launch again on landing, before the next read). A lesson pairs a state with the action taken
    from it, at every edge as well as every tick, so the frame that launches a jump teaches "ground,
    wall ahead: jump" whatever the period's phase."""
    dx, dy, facing, ground, air, ladder, wallFoot, wallHead, ladderHere = sn[1], sn[2], sn[3], sn[4], sn[5], sn[6], sn[9], sn[10], sn[12]
    if air: return 0
    if ladder: return 1 if dy > 0 else 0
    if dy > 0 and ladderHere: return 1
    if abs(dx) >= 2 or dy >= 2:
        d = 8 if dx > 0 else 4 if dx < 0 else (8 if facing else 4)
        if wallFoot and not wallHead and ((d == 8) == bool(facing)): return d | 16
        return d
    return 0
C = 33
t = 8 * C - 60
setup = f"wait:300,joy:8:{(t - 184) // 2},wait:20," + "".join("joy:18:6,wait:20,joy:17:6,wait:30," for _ in range(5)) + "wait:10,hold:1,wait:50,release:1,wait:10"
wdir = tempfile.mkdtemp()
lessons_total = 0; reached = None; sessions = 10
for k in range(1, sessions + 1):
    m = Machine(); m.do(setup)
    if k > 1: m.do(f"load:{W:X}:{wdir}/w{k - 1}.bin,poke:{KIND:X}:01")
    m.do(f"poke:{TEACH:X}:01")
    held = 0; top = None
    for step in range(150):                      # up to 600 frames of teaching, a decision every think period
        d = read(m); lines = teacher(d["senses"])
        if lines != held:
            m.do((f"release:{held}," if held else "") + (f"hold:{lines}" if lines else "wait:0"))
            held = lines
        m.do("wait:4")
        if (d["cs"] & 0x7f) in (2, 7) and d["cy"] <= d["py"] + 8: top = step; break
    if held: m.do(f"release:{held}")
    m.do(f"poke:{TEACH:X}:00,wait:2")
    d = read(m); lessons_total += d["total"]
    m.do(f"dump:{W:X}:64:{wdir}/w{k}.bin"); m.close()
    # alone: the same start, his brain only
    m = Machine(); m.do(setup); m.do(f"load:{W:X}:{wdir}/w{k}.bin,poke:{KIND:X}:01,wait:480"); a = read(m); m.close()
    on_ladder = (a["cs"] & 0x7f) in (2, 7) and a["cy"] <= a["py"] + 16
    print(f"       session {k}: {d['total']} lessons, taught up to Y {d['cy']} in {(top + 1) * 4 if top is not None else 600} frames; alone after it: Y {a['cy']}, X {a['cx']}, state {a['cs']}" + ("  <- climbs to Tony" if on_ladder else ""))
    if on_ladder and reached is None: reached = (k, lessons_total); break
check(reached is not None, f"he climbs the stairs and the ladder to Tony on his own after {reached[0] if reached else '?'} session(s), {reached[1] if reached else lessons_total} lessons from zero")
print("ALL OK" if ok else "FAILURES")
if reached: print(f"LESSONS-TO-CLIMB {reached[1]} in {reached[0]} session(s)")
if reached and SAVE: shutil.copy(f"{wdir}/w{reached[0]}.bin", SAVE); print(f"the weights that climbed: {SAVE}")
sys.exit(0 if ok else 1)
