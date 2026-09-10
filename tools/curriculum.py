#!/usr/bin/env python3
"""
curriculum.py - the diverse-experience experiment (deliverables/curriculum/PREREG-CURRICULUM.md).

A sense-only teacher (a fixed decision list over the twenty senses, nothing else) drives the clone
through the port while teaching is on, over a fixed curriculum of episodes repeated in passes, until a
pre-registered stopping rule fires; the brain that results is frozen and evaluated by
tools/generalization_test.py run2 against the old corpus (a regression set now) and a shadow holdout.
The PRG, the senses, the slot, the decoder, the quantisation and the learning rule are the ones of
commit 5116a2d, untouched.

  check    the start state of every curriculum episode, no teaching (part of writing the curriculum)
  train    the passes; writes deliverables/curriculum/training-log.json, the weights after every pass,
           and freezes the final brain as deliverables/curriculum/taught-curriculum.bin with its hash
  teacher  print the teacher's action for a sense vector given as twenty comma-separated integers

Presses are one frame long for jumps and chords (the launch is an edge, the release is an edge, and no
air frame carries the jump's label); directions and the ladder's up are held for the tick.
"""
import hashlib, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
_spec = importlib.util.spec_from_file_location("gt", os.path.join(os.path.dirname(os.path.abspath(__file__)), "generalization_test.py"))
gt = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(gt)
ROOT = gt.ROOT
OUT = os.path.join(ROOT, "deliverables/curriculum")
BRAIN2 = os.path.join(OUT, "taught-curriculum.bin")
IDLE, LEFT, RIGHT, UP, DOWN, JUMP, JUMPL, JUMPR, BUILDL, BUILDR = range(10)
TICK = 4                                  # frames between the teacher's decisions: the brain's think period

# ------------------------------------------------------------------------------------------ the teacher
def teacher(s):
    """The curriculum's policy: a function of the twenty senses only (signed, as published), returning
    one of the ten actions. Written once, before training; see PREREG-CURRICULUM.md for the rules."""
    dx, dy, fac, grd, air, lad, duck, flr, wF, wH, brk, lH, lB, bld, pA, last, still, pD, pL = s[1:20]
    if air: return IDLE                                            # in the air nothing acts
    if lad: return UP if dy > 0 else (DOWN if dy < 0 else IDLE)    # on a ladder: after him
    if lH and dy > 0: return UP                                    # a ladder in the box and he is above: climb
    toward = RIGHT if dx > 0 else LEFT if dx < 0 else (RIGHT if fac else LEFT)
    away = LEFT if toward == RIGHT else RIGHT
    ft = (fac != 0) == (toward == RIGHT)                           # facing his way
    adx = abs(dx)
    if dy <= 1:                                                    # level with him, or he is below: follow
        if adx <= 1: return IDLE                                   # beside him: nothing (restraint)
        if ft and wF and not wH: return JUMP + toward              # a brick in the way: jump it
        if ft and wF and wH: return IDLE                           # a wall: nothing to do
        return toward                                              # walk his way (a turn first if needed)
    if not ft:                                                     # two or more bricks below him, facing away
        if dy == 3 and bld and not wF: return BUILDL + (away - 1)  # the route's second brick
        return toward                                              # turn his way
    if wF and not wH:                                              # a step ahead
        if dy >= 5: return JUMP + toward                           # a middle step: the next brick stops the jump
        return BUILDL + (away - 1)                                 # near the top: the route's first brick, away from him
    if wF and wH: return (BUILDL + (toward - 1)) if bld else IDLE  # a two-high wall: a step in front of it, or nothing
    if dy == 2 and adx >= 4 and last == toward: return JUMP + toward   # the route's end: onto the top brick
    if adx >= 5: return toward                                     # far: walk
    return (BUILDL + (toward - 1)) if bld else toward              # near and below with nothing ahead: build up his way

# ------------------------------------------------------------------------------------ the two drivers
JOY = {IDLE: 0, LEFT: 4, RIGHT: 8, UP: 1, DOWN: 2, JUMP: 16, JUMPL: 20, JUMPR: 24}
class PortDriver:
    """teaching: the teacher's actions as the port's lines (teachMode 1 routes them to the clone).
    One-frame presses for jumps and chords; directions and up/down held. Every emit consumes TICK
    frames, a build 32."""
    def __init__(self, m): self.m, self.held = m, 0
    def _set(self, mask):
        cmd = ""
        if self.held and self.held != mask: cmd += f"release:{self.held},"
        if mask and mask != self.held: cmd += f"hold:{mask},"
        self.held = mask; return cmd
    def emit(self, a):
        if a in (LEFT, RIGHT, UP, DOWN): return self._set(JOY[a]) + f"wait:{TICK}"
        if a in (JUMP, JUMPL, JUMPR): return self._set(0) + f"hold:{JOY[a]},wait:1,release:{JOY[a]},wait:{TICK - 1}"
        if a in (BUILDL, BUILDR):
            d = 4 if a == BUILDL else 8
            return self._set(0) + f"hold:{d},wait:1,release:{d},wait:3,hold:18,wait:1,release:18,wait:3,hold:17,wait:1,release:17,wait:23"
        return self._set(0) + f"wait:{TICK}"
class OverrideDriver:
    """evaluation: the same actions through the override byte, the bytes the decoder would emit (no
    teaching involved). Same frame budget as the port driver."""
    def __init__(self, m): self.m = m; self.ov = gt.OV
    def emit(self, a):
        o = lambda b: f"poke:{self.ov:X}:{0x80 | b:02X},"
        if a in (LEFT, RIGHT, UP, DOWN): return o(JOY[a]) + f"wait:{TICK}"
        if a in (JUMP, JUMPL, JUMPR): return o(JOY[a]) + "wait:1," + o(0) + f"wait:{TICK - 1}"
        if a in (BUILDL, BUILDR):
            d = 4 if a == BUILDL else 8
            return o(d) + "wait:1," + o(0) + "wait:3," + o(0x20) + "wait:1," + o(0) + "wait:3," + o(0x40) + "wait:1," + o(0) + "wait:23"
        return o(0) + f"wait:{TICK}"

# ---------------------------------------------------------------------------------------- the curriculum
g = gt
def C(id, prg_col, setup, frames, note, during=()):
    return dict(id=id, C=prg_col, setup=setup, frames=frames, note=note, during=list(during))
def curriculum():
    park_right = g.clone_hold(0x08, 40) + g.clone_idle()                  # the clone parked at X 226 while Tony builds leftward
    return [
        C("E01_follow_right", 33, "joy:8:30,wait:20,", 300, "nothing built; Tony walks 60 px right and stops; the clone walks after him and stops beside him"),
        C("E02_follow_left", 33, "joy:4:40,wait:20,", 300, "Tony walks 80 px left, past the clone; the clone turns, walks left and stops beside him"),
        C("E03_follow_far_right", 33, "joy:8:50,wait:20,", 400, "Tony walks 100 px right, to the pillar side; a long walk"),
        C("E04_follow_far_left", 33, "joy:4:55,wait:20,", 400, "Tony walks 110 px left; a long walk the other way"),
        C("E05_brick_right", 33, g.clone_idle() + "joy:8:1," + g.LAY + g.STEP + "joy:8:20,wait:30,", 400,
          "Tony lays a brick, crosses it and stands beyond; the clone (parked at 146) walks, jumps the brick, stops beside him"),
        C("E06_brick_left", 33, g.clone_hold(0x08, 50) + g.clone_idle() + "joy:4:1," + g.LAY + g.STEP + "joy:4:20,wait:30,", 400,
          "the mirror: the clone parked at 246; Tony lays a brick leftward, crosses it, stands beyond on the left"),
        C("E07_stairs_C33_ladder", 33, g.stairs(33) + g.tony_climb(50), 700,
          "the old training start: five bricks under the ladder at column 33, Tony on the ladder; the clone followed to the foot"),
        C("E08_stairs_C5_ladder", 5, park_right + g.stairs(5) + g.tony_climb(50), 800,
          "the mirror at the left wall: leftward stairs under the ladder at column 5; the clone walks from 226 and climbs"),
        C("E09_stairs_C27_ladder", 27, g.stairs(27) + g.tony_climb(50), 800,
          "an open column on the training side: the top step needs the two-brick route"),
        C("E10_stairs_C9_ladder", 9, park_right + g.stairs(9) + g.tony_climb(50), 900,
          "an open column on the mirror side: walk left, climb left, the route, the ladder"),
        C("E11_restraint_stairs", 33, g.stairs(33, 4) + "joy:4:60,wait:40,", 300,
          "four bricks stand; Tony walked back to the floor beside the clone: nothing to do"),
        C("E12_restraint_wall", 33, "joy:8:60,wait:20,", 400, "Tony walks to the right wall; the clone follows and stands beside him at the wall"),
        C("E13_stack_from_right", 33, g.clone_hold(0x08, 45) + g.clone_idle() + "joy:8:1," + g.LAY + "joy:4:8,joy:8:1," + g.LAY + g.STEP + g.LAY + g.STEP + g.clone_hold(0x04, 1) + g.clone_idle() + "wait:4,", 48,
          "Tony on a two-brick stack; the clone beyond it on the right, facing back at it with an empty slot before it: build a step toward him (the lesson), then the jump; the episode ends there, because a jump onto a two-high stack overshoots it and the teacher would loop"),
        C("E14_stack_from_left", 33, g.clone_hold(0x04, 20) + g.clone_idle() + "joy:4:1," + g.LAY + "joy:8:8,joy:4:1," + g.LAY + g.STEP + g.LAY + g.STEP + g.clone_hold(0x08, 9) + g.clone_idle() + "wait:4,", 48,
          "the mirror: Tony stacks two bricks leftward; the clone on the left with an empty slot before the stack: build a step toward him, then the jump; cut short the same way"),
        C("E15_two_high", 33, g.clone_idle() + "joy:8:1," + g.LAY + "joy:4:8,joy:8:1," + g.LAY + g.STEP + g.LAY + g.STEP + g.clone_hold(0x08, 9) + g.clone_idle() + "wait:4," + g.clone_hold(0x20, 3) + g.clone_idle() + "wait:10,", 48,
          "the old corpus's two-high wall: Tony on the stack, the clone facing the lifted slot before it: build a step toward him, then the jump; cut short the same way"),
    ]
def prg_for(col): return g.PRG_DEFAULT if g.SEEDS[col] is None else os.path.join(g.OUT, "prg", f"tony-body-ladder-C{col}.prg")

# ------------------------------------------------------------------------------------------ the loop
def run_episode(ep, weights_file, log_decisions=False):
    """one episode under teaching: boot, setup, install the current weights, teach for ep frames.
    Returns (lessons taken, the lessons recorded, decisions, the weights after)"""
    m = g.Machine(prg_for(ep["C"]))
    m.do("wait:300," + ep["setup"] + f"load:{g.W:X}:{weights_file},poke:{g.KIND:X}:01,poke:{g.TEACH:X}:01,poke:{g.OV:X}:00,wait:1")
    drv = PortDriver(m); frames = 0; decisions = []
    while frames < ep["frames"]:
        for at, cmd in ep["during"]:
            if frames - TICK < at <= frames: m.do(cmd)
        p = g.parse_poll(m.do("sync," + g.POLL_PEEKS))
        a = teacher(p["senses"])
        if log_decisions: decisions.append(dict(frame=frames, senses=p["senses"], action=a, cx=p["cx"], cy=p["cy"], cs=p["cs"], tx=p["tx"], ty=p["ty"], lessons=p["lessons"]))
        cmd = drv.emit(a); m.do(cmd)
        frames += 32 if a in (BUILDL, BUILDR) else TICK
    if drv.held: m.do(f"release:{drv.held}")
    m.do(f"poke:{g.TEACH:X}:00,wait:1")
    end = g.parse_poll(m.do("sync," + g.POLL_PEEKS))
    LC, LD = g.SYM["lessonCount"], g.SYM["lessonData"]
    n = m.do(f"peek:{LC:X},peek:{LC + 1:X}"); n = n[0] | n[1] << 8
    raw = m.do("".join(f"peek:{LD + i:X}," for i in range(11 * n))) if n else []
    lessons = []
    for j in range(n):
        b = raw[j * 11:(j + 1) * 11]
        lessons.append(dict(x=[g.sgn(b[i // 2] & 15) if i % 2 == 0 else g.sgn(b[i // 2] >> 4) for i in range(20)], t=b[10] & 15))
    f = tempfile.NamedTemporaryFile(suffix=".w", delete=False).name
    m.do(f"dump:{g.W:X}:64:{f}"); w = open(f, "rb").read(); os.unlink(f); m.close()
    return dict(taken=end["lessons"], recorded=lessons, decisions=decisions, final=dict(cx=end["cx"], cy=end["cy"], cs=end["cs"], tx=end["tx"], ty=end["ty"], bricks=end["bricks"]), frames=frames), w

def check():
    for ep in curriculum():
        m = g.Machine(prg_for(ep["C"])); m.do("wait:300," + ep["setup"] + f"poke:{g.TEACH:X}:00," + g.clone_idle() + "wait:1")
        p = g.parse_poll(m.do("sync," + g.POLL_PEEKS)); m.close()
        print(f"{ep['id']:24s} clone ({p['cx']},{p['cy']}) s{p['cs']}  Tony ({p['tx']},{p['ty']}) s{p['ts']}  bricks {p['bricks']}  senses {p['senses']}  teacher: {g.ACTIONS[teacher(p['senses'])]}")

def train(max_passes=25, stop_rate=0.02, patience=3):
    os.makedirs(OUT, exist_ok=True)
    eps = curriculum(); wfile = os.path.join(OUT, "w-current.bin"); open(wfile, "wb").write(bytes(100))
    log = dict(stopping=dict(max_passes=max_passes, stop_rate=stop_rate, patience=patience), passes=[])
    best, since_best = None, 0
    for k in range(1, max_passes + 1):
        rec = dict(n=k, episodes=[], lessons=0, ticks=0); all_lessons = []
        for ep in eps:
            r, w = run_episode(ep, wfile, log_decisions=(k == 1)); open(wfile, "wb").write(w[:100])
            rec["episodes"].append(dict(id=ep["id"], taken=r["taken"], final=r["final"], frames=r["frames"])); rec["lessons"] += r["taken"]; rec["ticks"] += r["frames"] // TICK
            all_lessons += [dict(episode=ep["id"], **l) for l in r["recorded"]]
            if k == 1: json.dump(r["decisions"], open(os.path.join(OUT, f"decisions-{ep['id']}.json"), "w"))
        rec["rate"] = rec["lessons"] / rec["ticks"]; rec["weights_sha256"] = hashlib.sha256(open(wfile, "rb").read()).hexdigest()
        open(os.path.join(OUT, f"w-pass{k:02d}.bin"), "wb").write(open(wfile, "rb").read())
        json.dump(all_lessons, open(os.path.join(OUT, f"lessons-pass{k:02d}.json"), "w"))
        log["passes"].append(rec); json.dump(log, open(os.path.join(OUT, "training-log.json"), "w"), indent=1)
        print(f"pass {k:2d}: {rec['lessons']:4d} lessons over {rec['ticks']} ticks ({100 * rec['rate']:.2f}%)  " + " ".join(f"{e['id'][:3]}:{e['taken']}" for e in rec["episodes"]), flush=True)
        if best is None or rec["lessons"] < best: best, since_best = rec["lessons"], 0
        else: since_best += 1
        if rec["rate"] <= stop_rate: log["stopped"] = f"pass {k}: the rate {rec['rate']:.4f} is at or under {stop_rate}"; break
        if since_best >= patience: log["stopped"] = f"pass {k}: no decrease for {patience} passes (best {best})"; break
    else: log["stopped"] = f"the cap of {max_passes} passes"
    w = open(wfile, "rb").read()[:100]; open(BRAIN2, "wb").write(w)
    import random
    rows = [w[o * 10:o * 10 + 10] for o in range(10)]; perm = list(range(10)); random.Random(g.PERMUTE_SEED).shuffle(perm)
    permuted = os.path.join(OUT, "taught-curriculum-permuted.bin"); open(permuted, "wb").write(b"".join(rows[perm[o]] for o in range(10)))
    log["frozen"] = dict(file=BRAIN2, sha256=hashlib.sha256(w).hexdigest(), passes=len(log["passes"]), lessons_total=sum(p["lessons"] for p in log["passes"]),
                         permuted=permuted, permuted_sha256=hashlib.sha256(open(permuted, "rb").read()).hexdigest(), permutation=perm)
    json.dump(log, open(os.path.join(OUT, "training-log.json"), "w"), indent=1)
    print("stopped:", log["stopped"], "| frozen", log["frozen"])

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "check": check()
    elif cmd == "train": train()
    elif cmd == "teacher": print(g.ACTIONS[teacher([int(x) for x in sys.argv[2].split(",")])])
