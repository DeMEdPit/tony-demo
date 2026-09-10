#!/usr/bin/env python3
"""
generalization_test.py - the adversarial generalization test of the frozen taught brain, on the real
minimal64 harness (deliverables/generalization/PREREG.md is the pre-registration; read it first).

  prereg   write the corpus (scenarios.json: every scenario with its setup script, its goal and its
           frame limit), the stamped PRGs for the ladder-position holdout, the permuted brain, the
           materials table, and the hashes of all of them (hashes.json). Committed before any run.
  train    re-run the four teaching sessions of tools/teach_demo.py, deterministic, logging the sense
           vectors the clone was in during teaching and the lessons recorded (training-set.json): the
           seen/novel split, and the label-aliasing check on the lessons themselves.
  run      run every scenario against the five arms and write results.json (raw, per episode),
           encountered.json (every polled sense vector with the arm's action, the builder twin's, the
           oracle's, and the outcome), and RESULTS.md (the tables). Nothing in the corpus, the
           weights or the rules is read from the results.

The five arms: learned (the frozen taught-climb.bin, kind 1), follow (kind 0), zero (kind 1, all
weights zero), builder (kind 2, hand-written), permuted (taught-climb.bin with its ten output rows
permuted by a fixed seed, kind 1). Teaching is off in every episode; the weights are dumped after
each and compared byte for byte to what was installed, and the lesson counter must read zero.

Success is mechanical and fixed before the run: a "near" goal holds at the first poll (every eight
frames) where |cloneX - tonyX| <= dx and |cloneY - tonyY| <= dy, in one of the allowed states if given;
a "restraint" goal holds when every poll of the window keeps him on the floor (Y >= y_min) within dx of
Tony. Time-to-goal is the poll's offset from t0. The window ends at the limit or at success.
"""
import hashlib, json, os, random, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables/generalization")
PRG_DEFAULT = os.path.join(ROOT, "deliverables/prg/minimal64/tony-body.prg")
BRAIN = os.path.join(ROOT, "deliverables/brains/taught-climb.bin")
PERMUTED = os.path.join(OUT, "taught-climb-permuted.bin")
ZERO = os.path.join(OUT, "zero.bin")
HARNESS = os.path.join(ROOT, "tools/m64-harness/m64run")
STAMP = os.path.join(ROOT, "tools/stamp_mural.py")
PERMUTE_SEED = 20260910
POLL = 8                       # frames between polls
SYM = {}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(os.path.join(ROOT, "src/kickass/tony-body.sym")).read()):
    SYM.setdefault(m.group(1), int(m.group(2), 16))
OV, KIND, TEACH, W = SYM["cloneJoyOverride"], SYM["brainKind"], SYM["teachMode"], SYM["brainWeights"]
ACTIONS = ["idle", "left", "right", "up", "down", "jump", "jump left", "jump right", "build left", "build right"]
SENSE_NAMES = "bias dx dy facingRight onGround inAir onLadder ducking floorBelow wallAheadFoot wallAheadHead brickAheadFoot ladderHere ladderBelow buildable playerAir lastAction still playerDuck playerOnLadder".split()

def sha(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()
def sgn(x): return x - 16 if x >= 8 else x

# ----------------------------------------------------------------------------------------- the machine
class Machine:
    """the harness driven line by line (interactive mode): do(line) runs it and returns its peeks"""
    def __init__(self, prg):
        self.p = subprocess.Popen([HARNESS, prg, "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
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

def pk(name, n=1): return "".join(f"peek:{SYM[name] + i:X}," for i in range(n))
POLL_PEEKS = (pk("cloneSenses", 20) + pk("cloneX", 2) + pk("cloneY") + pk("cloneState") + pk("physPlayerX", 2) + pk("physPlayerY") + pk("physPlayerState")
              + pk("brainAction") + pk("lessonTotal", 2) + pk("bodyFrames", 2) + pk("buildCount") + pk("currentChamberNumber") + pk("brainKind") + pk("cloneJoy"))
def parse_poll(v):
    return dict(senses=[sgn(x) for x in v[0:20]], cx=v[20] | v[21] << 8, cy=v[22], cs=v[23], tx=v[24] | v[25] << 8, ty=v[26], ts=v[27],
                action=v[28], lessons=v[29] | v[30] << 8, frame=v[31] | v[32] << 8, bricks=v[33], room=v[34], kind=v[35], joy=v[36])

# ----------------------------------------------------------------------------------- setup primitives
# Tony: joy:MASK:N presses lines for N frames then releases and runs 5 more; hold/release/wait as they are.
# The clone: the override byte (bit 7 on) replaces his brain's byte every frame until cleared.
def clone_hold(bits, frames): return f"poke:{OV:X}:{0x80 | bits:02X},wait:{frames},"
def clone_idle(): return f"poke:{OV:X}:80,"
def clone_free(): return f"poke:{OV:X}:00,"
def clone_step(): return clone_hold(0x40, 3) + clone_idle() + "wait:20,"          # the step-up bit onto the brick ahead
LAY = "joy:18:6,wait:20,"                                                          # Tony's lay chord (six frames: never the teaching hold)
STEP = "joy:17:6,wait:30,"                                                         # Tony's step-up chord
def stairs(C, n=5):
    """Tony walks to the ladder's approach and builds n bricks, stepping up each: rightward when the
    ladder is at column 13 or more (the training side), leftward below."""
    if C >= 13:
        t = 8 * C - 60                                    # in the verb's window 8C-64 .. 8C-57, even like his start
        walk = f"joy:8:{(t - 184) // 2}," if t > 184 else f"joy:4:{(184 - t) // 2},joy:8:1,"
    else:
        t = 8 * C + 99
        walk = f"joy:4:{(184 - t) // 2},"
    return walk + "wait:20," + (LAY + STEP) * n + "wait:10,"
def tony_climb(frames=50): return f"hold:1,wait:{frames},release:1,wait:10,"
FOOT_RIGHT = clone_hold(0x08, 40) + clone_idle() + "wait:4,"       # walks right until the first brick stops him, facing it
FOOT_LEFT = clone_hold(0x04, 60) + clone_idle() + "wait:4,"

# ------------------------------------------------------------------------------------------ the corpus
SEEDS = {33: None, 31: 5, 29: 40, 27: 3, 25: 35, 21: 6, 9: 17, 5: 1}     # ladder column -> "holdout seed N" (None: the default PRG)
def near(dx, dy, states=None): return dict(kind="near", dx=dx, dy=dy, states=states)
LADDER = near(16, 16, [2, 7])                                            # on the ladder within a brick of Tony
def restraint(y_min=190, dx=80): return dict(kind="restraint", y_min=y_min, dx=dx)

def corpus():
    S = []
    def add(id, bucket, setup, goal, limit, note, C=33, during=(), held_out=True):
        S.append(dict(id=id, bucket=bucket, held_out=held_out, C=C, seed=SEEDS[C], setup=setup, during=list(during), goal=goal, limit=limit, note=note))
    # A. the training start itself
    add("A1_train_start", "in_distribution", stairs(33) + tony_climb(50), LADDER, 480,
        "the teaching demo's start: Tony's five bricks under the ladder at column 33 and his climb to Y 72; the clone followed to the foot (X 206)", held_out=False)
    # B. the same side, other starts and timings
    add("B1_foot_facing_left", "same_side_variant", stairs(33) + tony_climb(50) + clone_hold(0x04, 1) + clone_idle() + "wait:4,", LADDER, 480,
        "at the foot but turned away: one frame of left before t0")
    add("B2_tony_on_fourth_brick", "same_side_variant", stairs(33, 4), near(20, 12), 480,
        "four bricks only: Tony stands on the fourth, clear of the ladder (state 0, so playerOnLadder is 0 throughout), dy 4 at the foot; the goal is beside him on it")
    add("B3_tony_climbs_late", "same_side_variant", stairs(33), LADDER, 600, "Tony waits on the top brick 120 frames after t0, then climbs",
        during=[(120, "hold:1"), (170, "release:1")])
    add("B4_start_in_air", "same_side_variant", stairs(33) + tony_climb(50) + clone_hold(0x18, 4), LADDER, 480,
        "the override launches a jump right at the foot four frames before t0 and lets go in the air")
    add("B5_partial_step2", "same_side_variant", stairs(33) + tony_climb(50) + clone_step() * 2, LADDER, 480, "driven onto the second brick before t0")
    add("B6_partial_step4", "same_side_variant", stairs(33) + tony_climb(50) + clone_step() * 4, LADDER, 480, "driven onto the fourth brick before t0")
    add("B7_start_on_top", "same_side_variant", stairs(33) + tony_climb(50) + clone_step() * 5, LADDER, 480, "driven onto the fifth brick, under the ladder, before t0")
    add("B8_tony_higher", "same_side_variant", stairs(33) + tony_climb(60), LADDER, 480, "Tony ten frames higher on the ladder (Y 62): dy one bucket more at the top")
    add("B9_tony_lower", "same_side_variant", stairs(33) + tony_climb(20), LADDER, 480, "Tony only twenty frames up the ladder (Y 102): dy 2 at the top")
    # C. walking required: the first brick is out of reach of a wall check
    add("C1_far_left", "walk_required", clone_idle() + stairs(33) + tony_climb(50), LADDER, 600,
        "the clone held at his start (X 146) while Tony builds and climbs: sixty pixels of floor before the first brick")
    add("C2_mid_distance", "walk_required", clone_idle() + stairs(33) + tony_climb(50) + clone_hold(0x08, 16) + clone_idle() + "wait:4,", LADDER, 600,
        "driven to X 178: a jump's reach short of the first brick, nothing ahead in the senses")
    # D. obstacles
    add("D1_two_high_wall", "obstacle",
        clone_idle() + "joy:8:1," + LAY + "joy:4:8,joy:8:1," + LAY + STEP + LAY + STEP + clone_hold(0x08, 9) + clone_idle() + "wait:4," + clone_hold(0x20, 3) + clone_idle() + "wait:10,",
        near(20, 12), 600,
        "Tony stacks two bricks in one slot and stands on them; the clone lifts the step Tony used: a two-high wall two columns ahead, an empty slot between")
    add("D2_brick_between", "obstacle", clone_idle() + "joy:8:1," + LAY + STEP + "joy:8:20,wait:30,", near(24, 12), 500,
        "one brick on the floor between the clone (X 146) and Tony, who crossed it and stands beyond on the floor")
    # E. the other side and the other approach
    add("E1_mirror_with_walk", "mirror", clone_hold(0x08, 40) + clone_idle() + stairs(9) + tony_climb(50), LADDER, 600,
        "the ladder at column 9: Tony's stairs rise leftward; the clone parked to the right must walk left and jump left", C=9)
    add("E2_C21_from_right", "mirror", clone_hold(0x08, 60) + clone_idle() + stairs(21) + tony_climb(50), LADDER, 600,
        "the ladder at column 21, stairs rising rightward, the clone parked beyond them to the right: the floor under the floating stairs is open", C=21)
    # F. the ladder-position holdout: the training protocol at other seeded columns
    for C in (31, 29, 27):
        add(f"F_ladder_C{C}", "ladder_same_side", stairs(C) + tony_climb(50), LADDER, 480,
            f"the training protocol with the seeded ladder at column {C} (training: 33), the clone following to the foot", C=C)
    for C in (25, 21):
        add(f"F_ladder_C{C}", "ladder_same_side", clone_hold(0x04, 30) + clone_idle() + stairs(C) + tony_climb(50) + FOOT_RIGHT, LADDER, 480,
            f"the seeded ladder at column {C}: Tony's approach is left of the clone's start, so the clone is parked at the left first and driven to the foot after the climb", C=C)
    for C in (9, 5):
        add(f"F_ladder_C{C}_mirror", "ladder_mirror", clone_hold(0x08, 40) + clone_idle() + stairs(C) + tony_climb(50) + FOOT_LEFT, LADDER, 480,
            f"the ladder at column {C}: leftward stairs, the clone driven to their foot facing left before t0", C=C)
    # G. restraint: Tony is not above
    add("G1_beside_no_stairs", "restraint", "joy:8:20,wait:40,", restraint(), 300, "nothing built; Tony forty pixels right; success is staying on the floor near him")
    add("G2_tony_back_on_floor", "restraint", stairs(33, 4) + "joy:4:60,wait:40,", restraint(), 300,
        "four bricks stand but Tony walked back off them to the floor beside the clone; success is not climbing without him")
    return S

# ---------------------------------------------------------------------------------------------- arms
def arms():
    return dict(learned=dict(weights=BRAIN, kind=1), follow=dict(weights=None, kind=0), zero=dict(weights=ZERO, kind=1),
                builder=dict(weights=None, kind=2), permuted=dict(weights=PERMUTED, kind=1))
def install(arm):
    s = f"poke:{TEACH:X}:00,"
    if arm["weights"]: s += f"load:{W:X}:{arm['weights']},"
    s += f"poke:{KIND:X}:{arm['kind']:02X}," + clone_free()
    return s

# --------------------------------------------------------------------------- the twin and the oracle
def builder_twin(s):
    """builderThink, kind 2, from the assembly in tools/make_chamber.py: the senses -> an action"""
    dx, dy, facing, air, ladder, wallFoot, wallHead, ladderHere, buildable = s[1], s[2], s[3], s[5], s[6], s[9], s[10], s[12], s[14]
    if air: return 0
    if ladder: return 0 if dy == 0 else (3 if dy > 0 else 4)
    if dy > 0 and ladderHere: return 3
    if dx < 0: d, wantRight = 1, False
    elif dx > 0: d, wantRight = 2, True
    else: d, wantRight = (2, True) if facing else (1, False)
    adx = abs(dx)
    if adx < 5 and not (dy >= 2): return 0                     # near, not two bricks below him: wait
    if bool(facing) == wantRight:
        if wallFoot:
            if not wallHead: return d + 5
            return d + 7 if buildable else 0
    if adx >= 5: return d
    return (9 if facing else 8) if buildable else 0

def oracle(p, screen, mat):
    """a privileged reference: the same task read from the exact positions and the map, not the
    senses. What a competent agent who can see the room would do next to reach Tony."""
    cx, cy, cs, tx, ty, s = p["cx"], p["cy"], p["cs"], p["tx"], p["ty"], p["senses"]
    st, facing_right = cs & 0x7f, bool(cs & 0x80)
    if st in (4, 5, 6): return 0
    dy_px, dx_px = cy - ty, tx - cx
    if st in (2, 7): return 3 if dy_px > 8 else (4 if dy_px < -8 else 0)
    if s[12] and dy_px > 8: return 3
    if abs(dx_px) <= 12 and abs(dy_px) <= 8: return 0
    right = dx_px > 0 if abs(dx_px) > 8 else facing_right
    d = 2 if right else 1
    left, rightc, top = cx // 8 - 2, (cx + 8) // 8 - 2, cy // 8 - 6
    feet, ahead = top + 3, (rightc + 1 if right else left - 1)
    def solid(r, c): return 0 <= r < 25 and 0 <= c < 40 and bool(mat[screen[r * 40 + c]] & 1)
    wall_foot, wall_head = solid(feet, ahead), solid(top, ahead)
    if dy_px >= 24 or abs(dx_px) >= 48:                     # two bricks above him, or 48 px away: the builder's own distances
        if wall_foot and not wall_head: return 5 + d
        if wall_foot and wall_head: return (7 + d) if s[14] else 0
        if abs(dx_px) < 48: return (7 + d) if s[14] else d
        return d
    return 0

def forward(weights, x):
    """the reference forward pass (mood zero): weights as 100+ bytes, x the twenty signed senses"""
    def w(o, i):
        b = weights[o * 10 + i // 2]; n = b & 15 if i % 2 == 0 else b >> 4
        return n - 16 if n >= 8 else n
    acc = [sum(w(o, i) * x[i] for i in range(20)) for o in range(10)]
    return max(range(10), key=lambda o: (acc[o], -o))

# ------------------------------------------------------------------------------------------ prereg
def prereg():
    os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.join(OUT, "prg"), exist_ok=True)
    brain = open(BRAIN, "rb").read()
    rows = [brain[o * 10:o * 10 + 10] for o in range(10)]
    perm = list(range(10)); random.Random(PERMUTE_SEED).shuffle(perm)
    assert perm != list(range(10))
    open(PERMUTED, "wb").write(b"".join(rows[perm[o]] for o in range(10)))
    open(ZERO, "wb").write(bytes(100))
    hashes = dict(prg=dict(default=sha(PRG_DEFAULT)), brain=sha(BRAIN), permuted=sha(PERMUTED), permutation=perm, zero=sha(ZERO), commit=subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip())
    orig = open(PRG_DEFAULT, "rb").read()
    for C, n in SEEDS.items():
        if n is None: continue
        out = os.path.join(OUT, "prg", f"tony-body-ladder-C{C}.prg")
        subprocess.run([sys.executable, STAMP, PRG_DEFAULT, out, "--text", f"holdout seed {n}", "--block", "25850267"], check=True, capture_output=True)
        b = open(out, "rb").read(); diff = [i for i in range(len(b)) if b[i] != orig[i]]
        assert len(b) == len(orig) and 0x5009 <= min(diff) and max(diff) < 0x5009 + 32, "a stamp touched more than the seed"
        m = Machine(out); v = m.do("wait:300," + pk("buildLadderCol") + pk("muralDim")); m.close()
        assert v[0] == C, (C, v)
        hashes["prg"][f"C{C}"] = dict(sha256=sha(out), seed_text=f"holdout seed {n}", bytes_differing=len(diff), dim_room=v[1])
    m = Machine(PRG_DEFAULT); mat = os.path.join(OUT, "materials.bin"); m.do(f"wait:300,dump:BE00:100:{mat}"); m.close()
    hashes["materials"] = sha(mat)
    json.dump(corpus(), open(os.path.join(OUT, "scenarios.json"), "w"), indent=1)
    json.dump(hashes, open(os.path.join(OUT, "hashes.json"), "w"), indent=1)
    S = corpus()
    print(f"{len(S)} scenarios, {sum(1 for s in S if s['held_out'])} held out; brain {hashes['brain'][:16]}; permutation {perm}")
    print("| id | bucket | ladder | goal | limit | what is different |\n|---|---|---|---|---|---|")
    for s in S:
        g = s["goal"]; gs = f"on the ladder within {g['dx']}/{g['dy']} px of Tony" if g["kind"] == "near" and g["states"] else (f"within {g['dx']}/{g['dy']} px of Tony" if g["kind"] == "near" else f"stays on the floor (Y >= {g['y_min']}) within {g['dx']} px of Tony, every poll")
        print(f"| {s['id']} | {s['bucket']}{'' if s['held_out'] else ' (training)'} | {s['C']} | {gs} | {s['limit']} | {s['note']} |")

# ------------------------------------------------------------------------------------------- train
def train():
    """the four teaching sessions of the demo, re-run to log what teaching showed him"""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    src = open(os.path.join(ROOT, "tools/teach_demo.py")).read().replace("ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))", f"ROOT = {ROOT!r}")
    ns = {"__name__": "prereg"}; head = src.split('print("1. kind 0 boots and follows:")')[0]
    tail = src.split("class Machine:")[1].split("wdir = tempfile.mkdtemp()")[0]
    sys.argv = ["teach_demo.py", PRG_DEFAULT]; exec(head + "class Machine:" + tail, ns)
    setup, teacher, read, SNAP, SENSES = ns["setup"], ns["teacher"], ns["read"], ns["SNAP"], ns["SENSES"]
    LC, LD = SYM["lessonCount"], SYM["lessonData"]
    wdir = tempfile.mkdtemp(); seen = {}; lessons = []
    for k in range(1, 5):
        m = ns["Machine"](); m.do(setup)
        if k > 1: m.do(f"load:{W:X}:{wdir}/w{k - 1}.bin,poke:{KIND:X}:01")
        m.do(f"poke:{TEACH:X}:01"); held = 0
        for step in range(150):
            d = read(m); key = ",".join(map(str, d["senses"])); seen.setdefault(key, []).append(dict(session=k, step=step, cx=d["cx"], cy=d["cy"], cs=d["cs"]))
            lines = teacher(d["senses"])
            if lines != held:
                m.do((f"release:{held}," if held else "") + (f"hold:{lines}" if lines else "wait:0")); held = lines
            m.do("wait:4")
            if (d["cs"] & 0x7f) in (2, 7) and d["cy"] <= d["py"] + 8: break
        if held: m.do(f"release:{held}")
        m.do(f"poke:{TEACH:X}:00,wait:2")
        n = m.do(f"peek:{LC:X},peek:{LC + 1:X}"); n = n[0] | n[1] << 8
        raw = m.do("".join(f"peek:{LD + i:X}," for i in range(11 * n)))
        for j in range(n):
            b = raw[j * 11:(j + 1) * 11]
            x = [sgn(b[i // 2] & 15) if i % 2 == 0 else sgn(b[i // 2] >> 4) for i in range(20)]
            lessons.append(dict(session=k, index=j, x=x, t=b[10] & 15))
        m.do(f"dump:{W:X}:64:{wdir}/w{k}.bin"); m.close()
    final = open(f"{wdir}/w4.bin", "rb").read()
    json.dump(dict(seen=seen, lessons=lessons, final_weights_sha256=hashlib.sha256(final).hexdigest(), frozen_brain_sha256=sha(BRAIN),
                   reproduces_frozen_brain=hashlib.sha256(final).hexdigest() == sha(BRAIN)), open(os.path.join(OUT, "training-set.json"), "w"), indent=1)
    by_x = {}
    for l in lessons: by_x.setdefault(",".join(map(str, l["x"])), set()).add(l["t"])
    print(f"training: {len(seen)} distinct sense vectors seen, {len(lessons)} lessons recorded, {len(by_x)} distinct lesson states, "
          f"{sum(1 for v in by_x.values() if len(v) > 1)} with conflicting labels; the sessions reproduce the frozen brain: {hashlib.sha256(final).hexdigest() == sha(BRAIN)}")

# --------------------------------------------------------------------------------------------- run
def goal_met(g, p):
    if g["kind"] == "near":
        return abs(p["cx"] - p["tx"]) <= g["dx"] and abs(p["cy"] - p["ty"]) <= g["dy"] and (g["states"] is None or (p["cs"] & 0x7f) in g["states"])
    return p["cy"] >= g["y_min"] and abs(p["cx"] - p["tx"]) <= g["dx"]

def episode(scn, arm_name, arm, prg, mat, enc, screens):
    m = Machine(prg)
    m.do("wait:300," + scn["setup"] + install(arm) + "wait:1")
    installed = open(arm["weights"], "rb").read() if arm["weights"] else None
    log, success, t_goal, screen_id = [], None, None, None
    def snap():
        nonlocal screen_id
        f = tempfile.NamedTemporaryFile(suffix=".scr", delete=False).name
        m.do(f"dump:C000:3E8:{f}"); b = open(f, "rb").read(); os.unlink(f)
        h = hashlib.sha256(b).hexdigest()[:16]; screens[h] = b.hex(); screen_id = h
    v = m.do("sync," + POLL_PEEKS); p0 = parse_poll(v); snap(); p0["screen"] = screen_id; log.append(dict(off=0, **p0))
    bricks, during = p0["bricks"], sorted(scn["during"])
    restraint_ok = goal_met(scn["goal"], p0) if scn["goal"]["kind"] == "restraint" else None
    for off in range(POLL, scn["limit"] + 1, POLL):
        for at, cmd in during:
            if off - POLL <= at < off: m.do(cmd)
        p = parse_poll(m.do(f"wait:{POLL},sync," + POLL_PEEKS))
        if p["bricks"] != bricks: snap(); bricks = p["bricks"]
        p["screen"] = screen_id; p["off"] = off; log.append(p)
        key = ",".join(map(str, p["senses"]))
        enc.append(dict(scenario=scn["id"], arm=arm_name, off=off, key=key, action=p["action"], cx=p["cx"], cy=p["cy"], cs=p["cs"], tx=p["tx"], ty=p["ty"],
                        screen=screen_id, oracle=oracle(p, bytes.fromhex(screens[screen_id]), mat), twin=builder_twin(p["senses"])))
        if scn["goal"]["kind"] == "near":
            if goal_met(scn["goal"], p): success, t_goal = True, off; break
        else:
            if not goal_met(scn["goal"], p): restraint_ok = False
    if scn["goal"]["kind"] == "near" and success is None: success = False
    if scn["goal"]["kind"] == "restraint": success = bool(restraint_ok)
    f = tempfile.NamedTemporaryFile(suffix=".w", delete=False).name
    end = m.do(f"dump:{W:X}:64:{f}," + pk("lessonTotal", 2) + pk("brainKind") + pk("teachMode")); after = open(f, "rb").read(); os.unlink(f); m.close()
    last = log[-1]
    return dict(scenario=scn["id"], arm=arm_name, success=success, time_to_goal=t_goal, polls=len(log) - 1,
                start=dict(cx=p0["cx"], cy=p0["cy"], cs=p0["cs"], tx=p0["tx"], ty=p0["ty"], ts=p0["ts"], bricks=p0["bricks"]),
                final=dict(cx=last["cx"], cy=last["cy"], cs=last["cs"], tx=last["tx"], ty=last["ty"], ts=last["ts"], bricks=last["bricks"], frame=last["off"]),
                min_cy=min(r["cy"] for r in log), min_dist=min(abs(r["cx"] - r["tx"]) + abs(r["cy"] - r["ty"]) for r in log),
                bricks_laid=last["bricks"] - p0["bricks"], left_room=any(r["room"] != 0 for r in log),
                weights_unchanged=(installed is None or after[:100] == installed[:100]), weights_sha256_after=hashlib.sha256(after[:100]).hexdigest(),
                lessons_after=end[0] | end[1] << 8, kind_after=end[2], teach_after=end[3], trace=log)

def run():
    S = corpus(); A = arms(); H = json.load(open(os.path.join(OUT, "hashes.json")))
    assert sha(BRAIN) == H["brain"] and sha(PERMUTED) == H["permuted"] and sha(PRG_DEFAULT) == H["prg"]["default"], "the inputs are not the pre-registered ones"
    assert json.load(open(os.path.join(OUT, "scenarios.json"))) == json.loads(json.dumps(S)), "the corpus in the script differs from the pre-registered file"
    mat = open(os.path.join(OUT, "materials.bin"), "rb").read()
    results, enc, screens = [], [], {}
    for scn in S:
        prg = PRG_DEFAULT if scn["seed"] is None else os.path.join(OUT, "prg", f"tony-body-ladder-C{scn['C']}.prg")
        for name, arm in A.items():
            r = episode(scn, name, arm, prg, mat, enc, screens); results.append(r)
            print(f"{scn['id']:24s} {name:9s} {'ok  ' if r['success'] else 'FAIL'} t={r['time_to_goal']} final=({r['final']['cx']},{r['final']['cy']},s{r['final']['cs']}) minY={r['min_cy']} minDist={r['min_dist']} bricks+{r['bricks_laid']} unchanged={r['weights_unchanged']} lessons={r['lessons_after']}", flush=True)
    assert sha(BRAIN) == H["brain"], "the brain file changed during the run"
    H["prereg_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    json.dump(dict(inputs_commit=H["commit"], prereg_commit=H["prereg_commit"], brain_sha256_before=H["brain"], brain_sha256_after=sha(BRAIN), results=results), open(os.path.join(OUT, "results.json"), "w"))
    json.dump(dict(encountered=enc, screens=screens), open(os.path.join(OUT, "encountered.json"), "w"))
    report(S, A, results, enc, screens, mat, H)

def report(S, A, results, enc, screens, mat, H):
    by = {(r["scenario"], r["arm"]): r for r in results}
    buckets = []
    for s in S:
        if s["bucket"] not in buckets: buckets.append(s["bucket"])
    L = [f"# Generalization test: results\n", f"The inputs' commit: `{H['commit']}`; the pre-registration commit the run started from: `{H.get('prereg_commit', '?')}`. Brain `taught-climb.bin` sha256 `{H['brain']}` before, `{sha(BRAIN)}` after the run; "
         f"in memory after every episode: {sum(1 for r in results if r['weights_unchanged'])} of {len(results)} unchanged, lessons taken during evaluation: {sum(r['lessons_after'] for r in results)}.\n",
         "## Per scenario\n", "| scenario | bucket | " + " | ".join(A) + " |", "|---|---|" + "---|" * len(A)]
    for s in S:
        cells = []
        for a in A:
            r = by[(s["id"], a)]; cells.append((f"ok {r['time_to_goal']}" if r["time_to_goal"] else "ok") if r["success"] else f"FAIL (Y {r['final']['cy']}, d {r['min_dist']}{', +' + str(r['bricks_laid']) + ' bricks' if r['bricks_laid'] else ''})")
        L.append(f"| {s['id']} | {s['bucket']}{'' if s['held_out'] else ' (training)'} | " + " | ".join(cells) + " |")
    L += ["\n## Aggregate success\n", "| bucket | n | " + " | ".join(A) + " |", "|---|---|" + "---|" * len(A)]
    def rate(sel, a):
        n = sum(1 for s in sel); k = sum(1 for s in sel if by[(s["id"], a)]["success"]); return f"{k}/{n}"
    for b in buckets:
        sel = [s for s in S if s["bucket"] == b]; L.append(f"| {b} | {len(sel)} | " + " | ".join(rate(sel, a) for a in A) + " |")
    held = [s for s in S if s["held_out"]]; L.append(f"| **all held out** | {len(held)} | " + " | ".join(rate(held, a) for a in A) + " |")
    feas = [s for s in held if by[(s["id"], "builder")]["success"]]; L.append(f"| held out and builder-solvable | {len(feas)} | " + " | ".join(rate(feas, a) for a in A) + " |")
    # the encountered states
    tr = os.path.join(OUT, "training-set.json"); T = json.load(open(tr)) if os.path.exists(tr) else None
    seen = set(T["seen"]) if T else set()
    lesson_x = set(",".join(map(str, l["x"])) for l in T["lessons"]) if T else set()
    brain = open(BRAIN, "rb").read()
    keys = {}
    for e in enc:
        k = keys.setdefault(e["key"], dict(n=0, arms={}, oracle=set(), twin=e["twin"], machine_learned=set(), machine_builder=set()))
        k["n"] += 1; k["arms"][e["arm"]] = k["arms"].get(e["arm"], 0) + 1; k["oracle"].add(e["oracle"])
        if e["arm"] == "learned": k["machine_learned"].add(e["action"])
        if e["arm"] == "builder": k["machine_builder"].add(e["action"])
    learned_keys = [k for k, v in keys.items() if "learned" in v["arms"]]
    novel = [k for k in learned_keys if k not in seen]
    agree = lambda ks: (sum(1 for k in ks if forward(brain, list(map(int, k.split(",")))) == keys[k]["twin"]), len(ks))
    a_seen, a_novel = agree([k for k in learned_keys if k in seen]), agree(novel)
    aliased = [k for k, v in keys.items() if len(v["oracle"]) > 1]
    L += ["\n## Encountered sense vectors\n",
          f"{len(keys)} distinct 20-sense vectors over all arms; the learned arm met {len(learned_keys)}, of which {len(novel)} never appeared in the four teaching sessions "
          f"({'training-set.json' if T else 'no training-set.json: the seen/novel split is unavailable'}).",
          f"The frozen brain's action agrees with the builder twin's on {a_seen[0]}/{a_seen[1]} of the vectors seen in teaching and {a_novel[0]}/{a_novel[1]} of the novel ones.",
          f"Oracle aliasing (the same 20 senses, the privileged oracle wanting different actions): {len(aliased)} vectors.",
          f"Twin check: the builder arm's machine action matched the Python twin on the same block for {sum(1 for k, v in keys.items() if v['machine_builder'] and v['machine_builder'] <= {v['twin']})} of {sum(1 for v in keys.values() if v['machine_builder'])} vectors it met (the machine's action can lag one block behind the polled one)."]
    if aliased:
        L += ["\n| senses (dx dy facing ground air ladder duck floor wallF wallH brick ladderHere ladderBelow buildable pAir last still pDuck pLadder) | oracle actions | twin | learned |", "|---|---|---|---|"]
        for k in aliased[:40]:
            v = keys[k]; L.append(f"| {k} | {', '.join(ACTIONS[a] for a in sorted(v['oracle']))} | {ACTIONS[v['twin']]} | {ACTIONS[forward(brain, list(map(int, k.split(','))))]} |")
    if T:
        by_x = {}
        for l in T["lessons"]: by_x.setdefault(",".join(map(str, l["x"])), []).append(l["t"])
        conf = {k: v for k, v in by_x.items() if len(set(v)) > 1}
        L += [f"\n## The lessons' own labels\n", f"{len(T['lessons'])} lessons recorded over the four sessions (the sessions reproduce the frozen brain: {T['reproduces_frozen_brain']}); "
              f"{len(by_x)} distinct states among them; {len(conf)} states carry conflicting labels (the same senses taught different actions):"]
        for k, v in conf.items(): L.append(f"- `{k}`: " + ", ".join(f"{ACTIONS[t]} x{v.count(t)}" for t in sorted(set(v))))
    novel_dis = [k for k in novel if forward(brain, list(map(int, k.split(",")))) != keys[k]["twin"]]
    L += ["\n## Where the learned brain and the twin disagree on novel states\n", "| senses | learned | twin | oracle | met in |", "|---|---|---|---|---|"]
    for k in novel_dis[:60]:
        v = keys[k]; L.append(f"| {k} | {ACTIONS[forward(brain, list(map(int, k.split(','))))]} | {ACTIONS[v['twin']]} | {', '.join(ACTIONS[a] for a in sorted(v['oracle']))} | {v['arms'].get('learned', 0)} polls |")
    open(os.path.join(OUT, "RESULTS.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:len(S) + 12]))

def check():
    """the setups only, no arm installed: the state at t0 of every scenario, to see that each start is
    the one described (part of writing the corpus; run before the pre-registration commit)"""
    mat = open(os.path.join(OUT, "materials.bin"), "rb").read()
    for scn in corpus():
        prg = PRG_DEFAULT if scn["seed"] is None else os.path.join(OUT, "prg", f"tony-body-ladder-C{scn['C']}.prg")
        m = Machine(prg); m.do("wait:300," + scn["setup"] + f"poke:{TEACH:X}:00," + clone_idle() + "wait:1")
        p = parse_poll(m.do("sync," + POLL_PEEKS))
        f = tempfile.NamedTemporaryFile(suffix=".scr", delete=False).name; m.do(f"dump:C000:3E8:{f}"); scr = open(f, "rb").read(); os.unlink(f); m.close()
        top = p["cy"] // 8 - 6; left = p["cx"] // 8 - 2
        rows = []
        for r in range(max(0, top - 3), min(25, top + 6)):
            rows.append("".join(("#" if mat[scr[r * 40 + c]] & 1 else ("L" if mat[scr[r * 40 + c]] & 2 else ".")) if 0 <= c < 40 else " " for c in range(left - 6, left + 10)))
        print(f"{scn['id']:24s} clone ({p['cx']},{p['cy']}) s{p['cs']}  Tony ({p['tx']},{p['ty']}) s{p['ts']}  bricks {p['bricks']} room {p['room']}  senses {p['senses']}  oracle {ACTIONS[oracle(p, scr, mat)]}, twin {ACTIONS[builder_twin(p['senses'])]}")
        print("      map around him (columns %d..%d, rows %d..): " % (left - 6, left + 9, max(0, top - 3)) + " | ".join(rows))

if __name__ == "__main__":
    {"prereg": prereg, "train": train, "run": run, "check": check}[sys.argv[1]]()
