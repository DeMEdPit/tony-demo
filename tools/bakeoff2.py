#!/usr/bin/env python3
"""
bakeoff2.py - the architecture bake-off, phases 1b and 2b, offline (deliverables/bakeoff/PREREG-1B.md).

Held fixed: the twenty raw senses as published, the curriculum teacher as the labeller, the symmetric
step-of-one rule with the mood-free prediction and the first-largest tie rule, the frozen corpora. New
against phases 1 and 2: the weight box is a parameter of the rule (4, 6 or 8 bits); the retinas are
binary (every input a flag, 0 or 1 in the readout); and the ten actions may be expressed relative to
an explicit reference vector (the vocabulary V), pinned in PREREG-1B.md and implemented here.

  check     the definitions checked: arm widths, set sizes, no label conflicts under V
  parity    the widened-box rule against the golden reference; writes golden-1b/ and parity-1b.json
  phase1b   representability by CP-SAT as a maximum feasible subset, every unfit state named
  phase2b   learnability by the exact rule from zero at boxes 4, 6 and 8 on S1, S2, S4 and S5
  budget    the exact BRAIN02 byte budget per architecture (a table, nothing built)

Nothing here touches the PRG.
"""
import glob, hashlib, json, os, random, sys, time
import numpy as np
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables/bakeoff")
CUR = os.path.join(ROOT, "deliverables/curriculum")
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
b1 = _load("bakeoff", os.path.join(ROOT, "tools/bakeoff.py"))
golden = _load("brain_golden", os.path.join(ROOT, "tools/brain_golden.py"))
teacher = b1.teacher
ABS_ACTIONS = ["idle", "left", "right", "up", "down", "jump", "jump left", "jump right", "build left", "build right"]
REL_ACTIONS = ["idle", "toward", "away", "up", "down", "jump", "jump toward", "jump away", "build toward", "build away"]
SENSES = ["bias", "dx", "dy", "facingRight", "onGround", "inAir", "onLadder", "ducking", "floorBelow", "wallAheadFoot", "wallAheadHead",
          "brickAheadFoot", "ladderHere", "ladderBelow", "buildable", "playerAir", "lastAction", "still", "playerDuck", "playerOnLadder"]
BOXES = {4: (-8, 7), 6: (-32, 31), 8: (-128, 127)}

# ------------------------------------------------------------- the reference vector and the vocabulary V
# The relative vocabulary is defined from an explicit signed reference vector r = (rx, ry). Nothing here
# decides what the reference is: the caller supplies it (for the curriculum it is Tony's offset, senses
# 1 and 2 of the same block). The horizontal sign h resolves toward and away:
#   rx > 0: h = +1 (toward is right);  rx < 0: h = -1 (toward is left);
#   rx == 0: h = the clone's current facing in the same block (sense 3: right if set, else left).
# The same h translates a human's absolute press into a relative taught action, from the lesson's own
# block, so a lesson stays reconstructible from its eleven bytes.
HDIR = {1: -1, 2: 1, 6: -1, 7: 1, 8: -1, 9: 1}                # the horizontal direction of an absolute action
def href(x, r=None):
    rx = x[1] if r is None else r[0]
    if rx > 0: return 1
    if rx < 0: return -1
    return 1 if x[3] else -1
def to_relative(a, h):
    """an absolute action index -> the relative index under h (a bijection for each h)"""
    if a not in HDIR: return a
    base = {1: 1, 2: 1, 6: 6, 7: 6, 8: 8, 9: 8}[a]
    return base if HDIR[a] == h else base + 1
def to_absolute(a, h):
    """the decoder's resolution: a relative index -> the absolute index under h"""
    if a not in (1, 2, 6, 7, 8, 9): return a
    base = {1: 1, 2: 1, 6: 6, 7: 6, 8: 8, 9: 8}[a]; toward = (a == base)
    right = (h == 1) == toward
    return base + (1 if right else 0)
def relabel(labels):
    return {x: to_relative(t, href(x)) for x, t in labels.items()}

# ------------------------------------------------------------------------------------ the retinas
# Every flag is a fixed function of the twenty raw senses as published. Binary retinas return 0/1 (the
# readout treats a flag as 1; the block's 7 would scale every accumulator by 7 and change nothing in
# the rule, whose step is the sign). The mixed controls return the published values, as in phases 1-2.
RAW_FLAGS = (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19)      # the fifteen raw flags
def fl(v): return 1 if v else 0
def r_bias(x): return [1]
def r_rawflags(x): return [fl(x[i]) for i in RAW_FLAGS]
def r_dxs(x): return [fl(x[1] > 0), fl(x[1] < 0)]
def r_adxt(x): return [fl(abs(x[1]) >= k) for k in range(1, 8)]
def r_dyup(x): return [fl(x[2] >= k) for k in range(1, 8)]
def r_dydown(x): return [fl(x[2] <= -k) for k in range(1, 8)]
def r_stillt(x): return [fl(x[17] >= k) for k in range(1, 8)]
def r_last(x): r = x[16] & 15; return [fl(r == k) for k in range(10)]
def bin56(x): return r_bias(x) + r_rawflags(x) + r_dxs(x) + r_adxt(x) + r_dyup(x) + r_dydown(x) + r_stillt(x) + r_last(x)
BIN56_NAMES = (["bias"] + [SENSES[i] for i in RAW_FLAGS] + ["dxRight", "dxLeft"] + [f"adx>={k}" for k in range(1, 8)] +
               [f"dy>={k}" for k in range(1, 8)] + [f"dy<=-{k}" for k in range(1, 8)] + [f"still>={k}" for k in range(1, 8)] + [f"last={ABS_ACTIONS[k]}" for k in range(10)])
def six(x):
    """the six named second-order facts of the review's section 5, as the engine reads the names"""
    h = href(x); facing = 1 if x[3] else -1
    facingPlayer = facing == h                                   # facing the reference's way (h itself when rx == 0)
    stepAhead = x[9] and not x[10]                               # a one-high step ahead
    wallAhead = x[9] and x[10]                                   # a two-high wall ahead
    ladderHereAndHeAbove = x[12] and x[2] > 0
    facingAStep = facingPlayer and stepAhead
    buildableAndClear = x[14] and not x[9]
    return [fl(v) for v in (facingPlayer, stepAhead, wallAhead, ladderHereAndHeAbove, facingAStep, buildableAndClear)]
SIX_NAMES = ["facingPlayer", "stepAhead", "wallAhead", "ladderHereAndHeAbove", "facingAStep", "buildableAndClear"]
def lastrel(x):
    """the last action's horizontal direction against h: toward the reference, away from it"""
    h = href(x); d = HDIR.get(x[16] & 15, 0)
    return [fl(d == h), fl(d == -h)]
LASTREL_NAMES = ["lastActionTowardPlayer", "lastActionAwayFromPlayer"]
DIR_NAMES = ["dxRight", "dxLeft", "facingRight"] + [f"last={ABS_ACTIONS[k]}" for k in range(10)]
SIT_IDX = (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19)          # the raw flags without facing
SIT_NAMES = [SENSES[i] for i in SIT_IDX] + [f"dy>={k}" for k in range(1, 8)]
def order2(x):
    """the order-2 layer: every conjunction of a direction flag (dx sign, facing, last one-hot: 13) with
    a situation flag (the fourteen raw flags other than facing, dy up thermometer: 21): 273 units"""
    d = r_dxs(x) + [fl(x[3])] + r_last(x)
    s = [fl(x[i]) for i in SIT_IDX] + r_dyup(x)
    return [a & b for a in d for b in s]
ORDER2_NAMES = [f"{a}&{b}" for a in DIR_NAMES for b in SIT_NAMES]

def arms():
    """name -> (encoder, width, binary, description, input names or None)"""
    A1 = b1.arms()
    A = {}
    A["raw20"] = (b1.raw, 20, False, "control: the twenty senses as published (mixed)", SENSES)
    A["T36"] = (A1["T_dyup+dxs+adxt"][0], 36, False, "control: raw plus dy-up thermometer, dx sign, |dx| thermometer (mixed)", None)
    A["A2"] = (A1["A2_A1+adx1h+dxs"][0], 55, False, "control: raw plus one-hot dy, one-hot last, one-hot |dx|, dx sign (mixed)", None)
    A["R0"] = (bin56, 56, True, "BIN: bias, 15 raw flags, dx sign, |dx| therm, dy up therm, dy down therm, still therm, last one-hot", BIN56_NAMES)
    A["R1"] = (lambda x: bin56(x) + six(x), 62, True, "R0 plus the six named second-order facts", BIN56_NAMES + SIX_NAMES)
    A["R1b"] = (lambda x: bin56(x) + six(x) + lastrel(x), 64, True, "R1 plus lastActionTowardPlayer, lastActionAwayFromPlayer", BIN56_NAMES + SIX_NAMES + LASTREL_NAMES)
    A["R2"] = (lambda x: bin56(x) + six(x) + lastrel(x) + order2(x), 337, True, "R1b plus the order-2 layer (13 direction x 21 situation = 273)", BIN56_NAMES + SIX_NAMES + LASTREL_NAMES + ORDER2_NAMES)
    return A
UNDECIDED = ["T_dyup+dxs+last+adxt", "T_dyup+dydown+dxs+last+adxt", "A2_A1+adx1h+dxs"]   # Phase 1's three unsolved union cases

# --------------------------------------------------------------------------------------- the data
def episodes():
    """the tick stream of one curriculum pass, per episode in curriculum order, with identities"""
    eps = []
    for f in sorted(glob.glob(os.path.join(CUR, "decisions-*.json"))):
        eid = os.path.basename(f)[len("decisions-"):-5]
        eps.append((eid, [(tuple(d["senses"]), d["action"], d) for d in json.load(open(f))]))
    return eps
def sets():
    """the 231 (labels, identities), the teacher-visited union (474), the full union (1,424); the tick
    stream; identities per state: where it was first met"""
    eps = episodes(); labels, ident, stream = {}, {}, []
    for eid, ticks in eps:
        for x, t, d in ticks:
            stream.append((x, t))
            if x not in labels: labels[x] = t; ident[x] = dict(source="curriculum", episode=eid, frame=d["frame"], clone=(d["cx"], d["cy"]), tony=(d["tx"], d["ty"]))
    E = json.load(open(os.path.join(CUR, "encountered2.json")))["encountered"]
    T, U = dict(labels), dict(labels)
    for e in E:
        x = tuple(int(v) for v in e["key"].split(","))
        if x not in U:
            U[x] = teacher(list(x)); ident[x] = dict(source="evaluation", scenario=e["scenario"], arm=e["arm"], off=e["off"], clone=(e["cx"], e["cy"]), tony=(e["tx"], e["ty"]), screen=e["screen"])
        if e["arm"] == "teacher" and x not in T:
            T[x] = U[x]
            if ident[x]["source"] == "evaluation" and ident[x]["arm"] != "teacher": ident[x] = dict(source="evaluation", scenario=e["scenario"], arm="teacher", off=e["off"], clone=(e["cx"], e["cy"]), tony=(e["tx"], e["ty"]), screen=e["screen"])
    return dict(s231=labels, s474=T, s1424=U, ident=ident, stream=stream, episodes=eps)
def describe(x):
    return ", ".join(f"{SENSES[i]} {x[i]}" for i in range(20) if x[i] != 0 and i != 0)

# ------------------------------------------------------------------------------ the exact rule
def forward_ref(w, z, mood=None):
    """the reference forward pass for n inputs: acc[o] = sum w[o][i] z[i] (+ mood[o] * 16); the first largest"""
    n = len(z); acc = [sum(w[o][i] * z[i] for i in range(n)) + (mood[o] * 16 if mood else 0) for o in range(10)]
    return acc, max(range(10), key=lambda o: (acc[o], -o))
def learn_ref(w, z, t, lo, hi):
    """the golden rule, generalised to n inputs and a box: the mood-free prediction p; no lesson if p == t;
    else w[t][i] += sgn(z[i]), w[p][i] -= sgn(z[i]) for z[i] != 0, each saturating in [lo, hi]"""
    _, p = forward_ref(w, z)
    if p == t: return p, False
    for i in range(len(z)):
        if z[i] == 0: continue
        s = 1 if z[i] > 0 else -1
        w[t][i] = max(lo, min(hi, w[t][i] + s)); w[p][i] = max(lo, min(hi, w[p][i] - s))
    return p, True

def learn_stream(Z, stream, labels, box, passes=300, noise=None, seed=0, union=None, trace=None):
    """the vectorised rule from zero over a stream of (x, t) for passes; Z: x -> np vector. noise: the
    probability that a tick's label is replaced by a uniformly random other action, drawn afresh every
    pass (seed). union: (labels) whose agreement is recorded after each pass. trace: a list that receives
    (pass, k, w.copy()) after every lesson (the parity check). Returns the record."""
    lo, hi = box
    S = np.array([Z[x] for x, t in stream]); T0 = np.array([t for x, t in stream]); N = len(stream); n = S.shape[1]
    L = np.array([Z[x] for x in labels]); LT = np.array([labels[x] for x in labels])
    if union: UL = np.array([Z[x] for x in union]); UT = np.array([union[x] for x in union])
    rng = np.random.default_rng(seed)
    w = np.zeros((10, n), dtype=np.int64); lessons = 0; first_full = None; full_passes = 0; clamps = 0
    curve = []; noisy_lessons = 0; maxabs_curve = []; union_curve = []; agree_before_full = None
    for p in range(1, passes + 1):
        T = T0
        if noise:
            flip = rng.random(N) < noise; other = (T0 + rng.integers(1, 10, N)) % 10
            T = np.where(flip, other, T0)
        taken = 0; taken_noisy = 0
        for k in range(N):
            z = S[k]; acc = w @ z; pred = int(np.argmax(acc))
            if pred != T[k]:
                sg = np.sign(z); w[T[k]] += sg; w[pred] -= sg
                clamps += int((w > hi).sum() + (w < lo).sum()); np.clip(w, lo, hi, out=w); taken += 1
                if noise and T[k] != T0[k]: taken_noisy += 1
                if trace is not None: trace.append((p, k, w.copy()))
        lessons += taken; noisy_lessons += taken_noisy
        agree = int((np.argmax(L @ w.T, axis=1) == LT).sum()); curve.append((p, taken, agree, taken_noisy))
        maxabs_curve.append(int(np.abs(w).max()))
        if union: union_curve.append(int((np.argmax(UL @ w.T, axis=1) == UT).sum()))
        if agree == len(labels):
            full_passes += 1
            if first_full is None: first_full = lessons
    rec = dict(lessons_total=lessons, first_full_at_lessons=first_full, passes_at_full=full_passes, passes=passes, states=len(labels),
               final_agree=curve[-1][2], best_agree=max(c[2] for c in curve), clamps=clamps, max_abs_w=int(np.abs(w).max()), max_abs_w_curve_max=max(maxabs_curve),
               lessons_per_pass_last10=[c[1] for c in curve[-10:]], agree_curve=[c[2] for c in curve], lessons_curve=[c[1] for c in curve], maxabs_curve=maxabs_curve)
    if noise: rec["noisy_lessons_total"] = noisy_lessons; rec["noisy_lessons_last10"] = [c[3] for c in curve[-10:]]
    if union: rec["union_states"] = len(union); rec["union_agree_curve"] = union_curve; rec["union_final_agree"] = union_curve[-1]; rec["union_best_agree"] = max(union_curve)
    rec["weights_sha256"] = hashlib.sha256(w.astype(np.int16).tobytes()).hexdigest()
    rec["weights"] = w.tolist()
    return rec

def streams(D, vocab):
    """S1 the tick stream; S2 the labels cycled; S5 the tick stream with every label delayed one tick
    within its episode (the first tick of an episode idle). S4 is S1 with noise drawn inside learn_stream."""
    lab = D["s231"] if vocab == "abs" else relabel(D["s231"])
    conv = (lambda x, t: t) if vocab == "abs" else (lambda x, t: to_relative(t, href(x)))
    S1 = [(x, conv(x, t)) for x, t in D["stream"]]
    S2 = list(lab.items())
    S5 = []
    for eid, ticks in D["episodes"]:
        prev = 0
        for x, t, d in ticks:
            S5.append((x, prev)); prev = conv(x, t)
    return lab, dict(S1=S1, S2=S2, S5=S5)

# ------------------------------------------------------------------------- phase 1b: CP-SAT exact
def cpsat_feasible(items, Z, n, box, time_limit=300, workers=4, hint=None):
    """plain feasibility: every state's constraints unconditional, no objective. OPTIMAL/FEASIBLE with a
    clean replay is a representable solution; INFEASIBLE is a proof that none exists in the box."""
    from ortools.sat.python import cp_model
    lo, hi = box
    model = cp_model.CpModel()
    w = [[model.NewIntVar(lo, hi, f"w{o}_{i}") for i in range(n)] for o in range(10)]
    for x, t in items:
        z = Z[x]; act = [(i, int(z[i])) for i in range(n) if z[i] != 0]
        for o in range(10):
            if o == t: continue
            model.Add(sum((w[t][i] - w[o][i]) * zi for i, zi in act) >= (1 if o < t else 0))
    if hint is not None:
        for o in range(10):
            for i in range(n): model.AddHint(w[o][i], max(lo, min(hi, int(hint[o][i]))))
    solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = time_limit; solver.parameters.num_workers = workers
    t0 = time.time(); st = solver.Solve(model); dt = time.time() - t0
    r = dict(status=solver.StatusName(st), seconds=round(dt, 1), states=len(items))
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        W = [[int(solver.Value(w[o][i])) for i in range(n)] for o in range(10)]
        bad = sum(1 for x, t in items if forward_ref(W, Z[x])[1] != t)
        r.update(feasible=(bad == 0), replay_mislabelled=bad, weights=W, max_abs_w=max(abs(v) for row in W for v in row))
    elif st == cp_model.INFEASIBLE: r["feasible"] = False
    else: r["feasible"] = None
    return r

def cpsat(items, Z, n, box, time_limit=300, margin=False, workers=4, forced=(), hint=None, cut=None):
    """maximum feasible subset (margin False): one Bool per state, every constraint of that state
    enforced only when its Bool holds, maximise the count. margin True: every state enforced, maximise the
    integer m added to every gap. Returns the status, the objective and its bound, the unfit states, the
    weights, replayed through the exact forward pass as a check on the solver."""
    from ortools.sat.python import cp_model
    lo, hi = box
    model = cp_model.CpModel()
    w = [[model.NewIntVar(lo, hi, f"w{o}_{i}") for i in range(n)] for o in range(10)]
    zmax = max(abs(v) for x, t in items for v in Z[x]) or 1
    m = model.NewIntVar(0, (hi - lo) * n * zmax, "m") if margin else None
    fit = [] if margin else [model.NewBoolVar(f"f{k}") for k in range(len(items))]
    for k, (x, t) in enumerate(items):
        z = Z[x]; act = [(i, int(z[i])) for i in range(n) if z[i] != 0]
        if not margin and x in forced: model.Add(fit[k] == 1)
        for o in range(10):
            if o == t: continue
            gap = sum((w[t][i] - w[o][i]) * zi for i, zi in act)
            need = 1 if o < t else 0
            if margin: model.Add(gap >= need + m)
            else: model.Add(gap >= need).OnlyEnforceIf(fit[k])
    if margin: model.Maximize(m)
    else:
        model.Maximize(sum(fit))
        if cut is not None: model.Add(sum(fit) <= cut)          # a proven bound from the plain feasibility solve
    if hint is not None:
        for o in range(10):
            for i in range(n): model.AddHint(w[o][i], max(lo, min(hi, int(hint[o][i]))))
        if not margin:
            for k, (x, t) in enumerate(items): model.AddHint(fit[k], 1 if forward_ref(hint, Z[x])[1] == t else 0)
    solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = time_limit; solver.parameters.num_workers = workers
    t0 = time.time(); st = solver.Solve(model); dt = time.time() - t0
    status = solver.StatusName(st)
    r = dict(status=status, seconds=round(dt, 1), states=len(items))
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        W = [[int(solver.Value(w[o][i])) for i in range(n)] for o in range(10)]
        bad = [x for x, t in items if forward_ref(W, Z[x])[1] != t]
        r["objective"] = int(round(solver.ObjectiveValue())); r["bound"] = int(round(solver.BestObjectiveBound()))
        r["max_abs_w"] = max(abs(v) for row in W for v in row); r["weights"] = W
        if margin: r["margin"] = r["objective"]; r["margin_bound"] = r["bound"]; r["replay_mislabelled"] = len(bad)
        else:
            unfit = [x for x, k in zip((x for x, t in items), fit) if not solver.Value(k)]
            r["fitted"] = r["objective"]; r["unfit"] = [list(x) for x in unfit]; r["replay_mislabelled"] = len(bad)
            r["replay_unfit_equal"] = (set(unfit) == set(bad)) or (len(bad) <= len(unfit) and set(bad) <= set(unfit))
            r["feasible"] = (r["objective"] == len(items)) and len(bad) == 0
            if status == "OPTIMAL": r["min_unfit"] = len(items) - r["objective"]
            else: r["min_unfit_between"] = [len(items) - r["bound"], len(items) - r["objective"]]
    elif st == cp_model.INFEASIBLE: r["feasible"] = False
    return r

def cbc_check(items, Z, n, box, time_limit=120):
    """the independent solver on the same feasibility question (phase 1's tool, the box a parameter)"""
    import pulp
    lo, hi = box
    prob = pulp.LpProblem("rep", pulp.LpMinimize)
    w = [[pulp.LpVariable(f"w_{o}_{i}", lo, hi, cat="Integer") for i in range(n)] for o in range(10)]
    prob += 0
    for x, t in items:
        z = Z[x]
        for o in range(10):
            if o == t: continue
            prob += pulp.lpSum((w[t][i] - w[o][i]) * int(z[i]) for i in range(n) if z[i] != 0) >= (1 if o < t else 0)
    t0 = time.time(); prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)); dt = time.time() - t0
    status = pulp.LpStatus[prob.status]; bad = None
    if status == "Optimal":
        W = [[int(round(w[o][i].value() or 0)) for i in range(n)] for o in range(10)]
        bad = sum(1 for x, t in items if forward_ref(W, Z[x])[1] != t)
    return dict(status=status, seconds=round(dt, 1), replay_mislabelled=bad)

def name_states(xs, D, vocab):
    out = []
    for x in xs:
        x = tuple(x); t = D["s1424"][x]; i = D["ident"][x]
        out.append(dict(x=list(x), senses=describe(x), teacher=ABS_ACTIONS[t], taught=(ABS_ACTIONS[t] if vocab == "abs" else REL_ACTIONS[to_relative(t, href(x))]), h=href(x), where=i))
    return out

def hint_for(name, vocab, bits, setname, D=None, enc=None, n=None):
    """a warm start for the solver: the weights the rule reached in Phase 2b (S2u for the unions, S1 for
    the 231) at the same box, else a short run of the rule on the set itself"""
    p2 = os.path.join(OUT, "phase2b.json"); res = json.load(open(p2)) if os.path.exists(p2) else {}
    if setname != "s1424":
        for s in (("S1",) if setname == "s231" else ("S2u", "S1")):
            r = res.get(f"{name}|{vocab}|{bits}|{s}")
            if r and "weights" in r: return r["weights"]
    if D is None: return None
    Z = {x: np.array(enc(list(x)), dtype=np.int64) for x in D["s1424"]}
    lab = D[setname] if vocab == "abs" else relabel(D[setname])
    return learn_stream(Z, list(lab.items()), lab, BOXES[bits], passes=100 if setname == "s1424" else 60)["weights"]

def phase1b(only=None, time_limit=300, workers=4):
    os.makedirs(OUT, exist_ok=True)
    D = sets(); A = arms(); A1 = b1.arms()
    path = os.path.join(OUT, os.environ.get("P1_OUT", "phase1b.json"))      # a second process writes its own file, merged after
    res = json.load(open(path)) if os.path.exists(path) else {}
    def enc_cache(enc):
        Z = {}
        for x in D["s1424"]: Z[x] = np.array(enc(list(x)), dtype=np.int64)
        return Z
    def run(key, items, Z, n, box, margin=False, hint=None):
        """plain feasibility first (fast either way); the maximum feasible subset only when the set is
        not feasible, warm-started and with the proven cut"""
        if key in res and res[key].get("status") not in (None, "UNKNOWN"): return res[key]
        if margin:
            r = cpsat(items, Z, n, box, time_limit=time_limit, margin=True, workers=workers, hint=hint)
        else:
            f = cpsat_feasible(items, Z, n, box, time_limit=time_limit, workers=workers, hint=hint)
            if f.get("feasible"):
                r = dict(status="OPTIMAL", seconds=f["seconds"], states=len(items), objective=len(items), bound=len(items), fitted=len(items), unfit=[], min_unfit=0,
                         feasible=True, replay_mislabelled=0, max_abs_w=f["max_abs_w"], weights=f["weights"], via="feasibility")
            else:
                cut = len(items) - 1 if f["feasible"] is False else None
                r = cpsat(items, Z, n, box, time_limit=time_limit, workers=workers, hint=hint, cut=cut)
                r["via"] = "max-subset"; r["feasibility_status"] = f["status"]; r["feasibility_seconds"] = f["seconds"]
                if f["feasible"] is False: r["feasible"] = False
        res[key] = r; json.dump(res, open(path, "w"))
        return r
    plan = only or ["raw20", "T36", "A2", "R0", "R1", "R1b", "R2"]
    for name in plan:
        enc, n, binary, desc, names = A[name]; Z = enc_cache(enc)
        for vocab in ("abs", "rel"):
            for setname in ("s231", "s474", "s1424"):
                lab = D[setname] if vocab == "abs" else relabel(D[setname]); items = list(lab.items())
                for bits in ((8, 4) if name.startswith("R") else (8,)):
                    if bits == 4 and setname == "s1424": continue
                    key = f"{name}|{vocab}|{setname}|{bits}"
                    hint = hint_for(name, vocab, bits, setname, D, enc, n)
                    r = run(key, items, Z, n, BOXES[bits], hint=hint)
                    unfit = r.get("unfit", [])
                    print(f"{key:24s} {r['status']:10s} {r['seconds']:6.1f}s fitted {r.get('fitted')}/{len(items)} bound {r.get('bound')} unfit {len(unfit)} max|w| {r.get('max_abs_w')}", flush=True)
                    if unfit:
                        res[key]["unfit_named"] = name_states(unfit, D, vocab); json.dump(res, open(path, "w"))
                    if bits == 8 and r.get("feasible"):
                        mk = key + "|margin"; mr = run(mk, items, Z, n, BOXES[8], margin=True, hint=r.get("weights"))
                        print(f"{mk:24s} {mr['status']:10s} {mr['seconds']:6.1f}s margin {mr.get('margin')} bound {mr.get('margin_bound')} max|w| {mr.get('max_abs_w')}", flush=True)
                    if bits == 8 and setname == "s231":
                        ck = key + "|cbc"
                        if ck not in res:
                            res[ck] = cbc_check(items, Z, n, BOXES[8]); json.dump(res, open(path, "w"))
                        print(f"{ck:24s} {res[ck]['status']:10s} {res[ck]['seconds']:6.1f}s replay mislabelled {res[ck]['replay_mislabelled']}", flush=True)
    if not only: phase1b_undecided(time_limit, workers, D, res, path)
    return res

def phase1b_undecided(time_limit=300, workers=4, D=None, res=None, path=None):
    """the three undecided union cases of phase 1, at their own box (4 bits) and at 8, absolute vocabulary"""
    D = D or sets(); A1 = b1.arms()
    path = path or os.path.join(OUT, os.environ.get("P1_OUT", "phase1b.json"))
    if res is None: res = json.load(open(path)) if os.path.exists(path) else {}
    for name in UNDECIDED:
        enc, n, desc = A1[name]; Z = {x: np.array(enc(list(x)), dtype=np.int64) for x in D["s1424"]}; items = list(D["s1424"].items())
        for bits in (4, 8):
            key = f"P1:{name}|abs|s1424|{bits}"
            if key in res and res[key].get("status") not in (None, "UNKNOWN"): continue
            hint = learn_stream(Z, items, D["s1424"], BOXES[bits], passes=100)["weights"]
            f = cpsat_feasible(items, Z, n, BOXES[bits], time_limit=time_limit, workers=workers, hint=hint)
            if f.get("feasible"):
                r = dict(status="OPTIMAL", seconds=f["seconds"], states=len(items), objective=len(items), bound=len(items), fitted=len(items), unfit=[], min_unfit=0, feasible=True, replay_mislabelled=0, max_abs_w=f["max_abs_w"], weights=f["weights"], via="feasibility")
            else:
                r = cpsat(items, Z, n, BOXES[bits], time_limit=time_limit, workers=workers, hint=hint, cut=(len(items) - 1 if f["feasible"] is False else None))
                r["via"] = "max-subset"; r["feasibility_status"] = f["status"]; r["feasibility_seconds"] = f["seconds"]
                if f["feasible"] is False: r["feasible"] = False
            if r.get("unfit"): r["unfit_named"] = name_states(r["unfit"], D, "abs")
            res[key] = r; json.dump(res, open(path, "w"))
            print(f"{key:44s} {r['status']:10s} {r['seconds']:6.1f}s fitted {r.get('fitted')}/{len(items)} bound {r.get('bound')} unfit {len(r.get('unfit', []))}", flush=True)
    return res

def alternatives(keys=None, time_limit=300, workers=4):
    """the minimum unfit set is not unique in general: for the named cases (default: every binary arm's
    absolute-vocabulary teacher-visited union at 8 bits), re-solve with each named unfit state forced to
    fit and report the minimum and the unfit set that results"""
    D = sets(); A = arms(); path = os.path.join(OUT, os.environ.get("P1_OUT", "phase1b.json")); res = json.load(open(path))
    keys = keys or [f"{a}|abs|s474|8" for a in ("R0", "R1", "R1b", "R2")]
    for key in keys:
        r = res.get(key, {})
        if not r.get("unfit"): print(key, "nothing unfit"); continue
        name, vocab, setname, bits = key.split("|"); enc, n, binary, desc, names = A[name]
        Z = {x: np.array(enc(list(x)), dtype=np.int64) for x in D["s1424"]}
        lab = D[setname] if vocab == "abs" else relabel(D[setname]); items = list(lab.items())
        for j, u in enumerate(r["unfit"]):
            fk = f"{key}|force{j}"
            if fk in res and res[fk].get("status") != "UNKNOWN": continue
            fr = cpsat(items, Z, n, BOXES[int(bits)], time_limit=time_limit, workers=workers, forced={tuple(u)}, hint=r.get("weights"), cut=len(items) - r.get("min_unfit", 1))
            fr["forced"] = u
            if fr.get("unfit"): fr["unfit_named"] = name_states(fr["unfit"], D, vocab)
            res[fk] = fr; json.dump(res, open(path, "w"))
            print(f"{fk:30s} {fr['status']:10s} {fr['seconds']:6.1f}s fitted {fr.get('fitted')}/{len(items)} min unfit {fr.get('min_unfit', fr.get('min_unfit_between'))} unfit {fr.get('unfit')}", flush=True)
    return res

# ---------------------------------------------------------------------------- phase 2b: the rule
def _p2_one(args):
    name, vocab, bits, sname = args
    D = sets(); A = arms(); enc, n, binary, desc, names = A[name]
    Z = {x: np.array(enc(list(x)), dtype=np.int64) for x in D["s1424"]}
    lab, S = streams(D, vocab); union = D["s474"] if vocab == "abs" else relabel(D["s474"])
    if sname == "S4": r = learn_stream(Z, S["S1"], lab, BOXES[bits], noise=0.05, seed=0, union=union)
    elif sname == "S2u":
        # post-registration addition (PHASE2B.md says so): the 474 labels cycled, the review's own 474
        # experiment; "states" is then the 474 and the "union" fields report the 231 subset
        r = learn_stream(Z, list(union.items()), union, BOXES[bits], union=lab)
    else: r = learn_stream(Z, S[sname], lab, BOXES[bits], union=union)
    r["width"] = n
    return f"{name}|{vocab}|{bits}|{sname}", r

def phase2b(only=None, workers=None, streams_=("S1", "S2", "S4", "S5")):
    import multiprocessing as mp
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "phase2b.json")
    res = json.load(open(path)) if os.path.exists(path) else {}
    plan = only or ["R0", "R1", "R1b", "R2", "raw20", "T36", "A2"]
    jobs = [(name, vocab, bits, s) for name in plan for vocab in ("abs", "rel") for bits in (8, 6, 4) for s in streams_ if f"{name}|{vocab}|{bits}|{s}" not in res]
    with mp.Pool(workers or 2) as pool:
        for key, r in pool.imap_unordered(_p2_one, jobs):
            res[key] = r; json.dump(res, open(path, "w"))
            print(f"{key:18s} n={r['width']:3d} first {str(r['first_full_at_lessons']):5s} held {r['passes_at_full']:3d}/300 best {r['best_agree']}/{r['states']} final {r['final_agree']} clamps {r['clamps']:6d} max|w| {r['max_abs_w']:3d} union {r['union_best_agree']}/{r['union_states']} (final {r['union_final_agree']})" + (f" noisy lessons/pass {r['noisy_lessons_last10'][-1]}" if 'noisy_lessons_last10' in r else ""), flush=True)
    return res

# ------------------------------------------------------------------------------------- parity
def parity():
    """the widened-box rule checked three ways: (1) the generalised reference at box 4, n = 20, against
    the golden reference itself (brain_golden.learn, unchanged) weight for weight; (2) the vectorised
    learner against the generalised reference weight for weight after every lesson at boxes 4, 6, 8 on
    binary and mixed arms; (3) golden edge cases at the byte boundaries, exact ties and the
    accumulator bound, written as vectors for the 6502 of Phase 3 (golden-1b/)."""
    os.makedirs(os.path.join(OUT, "golden-1b"), exist_ok=True)
    D = sets(); A = arms(); out = {}
    # (1) box 4, n = 20: the generalised reference is the golden reference
    lab = D["s231"]; w1 = [[0] * 20 for _ in range(10)]; w2 = [[0] * 20 for _ in range(10)]; lessons = 0; same = True
    for p in range(20):
        for x, t in lab.items():
            a = golden.learn(w1, list(x), t); b = learn_ref(w2, list(x), t, -8, 7)
            lessons += a[1]
            if a != b or w1 != w2: same = False
    out["ref_vs_golden_box4_n20"] = dict(passes=20, lessons=lessons, identical=same)
    # (2) the vectorised learner against the generalised reference, every lesson, several boxes and arms
    checks = []
    for name, vocab, bits, passes in (("raw20", "abs", 4, 3), ("R0", "abs", 8, 3), ("R0", "rel", 6, 3), ("R2", "rel", 8, 2), ("A2", "abs", 8, 2), ("R1b", "abs", 4, 3)):
        enc, n, binary, desc, names = A[name]; lo, hi = BOXES[bits]
        Z = {x: np.array(enc(list(x)), dtype=np.int64) for x in D["s1424"]}
        labs, S = streams(D, vocab); stream = S["S1"]
        trace = []; r = learn_stream(Z, stream, labs, (lo, hi), passes=passes, trace=trace)
        w = [[0] * n for _ in range(10)]; k = 0; ok = True; nl = 0; maxacc = 0
        for p in range(1, passes + 1):
            for idx, (x, t) in enumerate(stream):
                z = [int(v) for v in Z[x]]; acc, _ = forward_ref(w, z); maxacc = max(maxacc, max(abs(a) for a in acc))
                pr, took = learn_ref(w, z, t, lo, hi)
                if took:
                    nl += 1
                    if k >= len(trace) or trace[k][0] != p or trace[k][1] != idx or trace[k][2].tolist() != w: ok = False; break
                    k += 1
            if not ok: break
        checks.append(dict(arm=name, vocab=vocab, bits=bits, passes=passes, lessons=nl, identical=(ok and k == len(trace) and nl == r["lessons_total"]), max_abs_acc=maxacc))
        print("parity", checks[-1], flush=True)
    out["vectorised_vs_reference"] = checks
    # (3) golden edge cases: byte weights, unit flags, n up to 128, boxes 6 and 8; the accumulator bound
    NMAX = 128
    bound = NMAX * 128 + 8 * 16
    assert bound <= 32768, bound
    out["accumulator_bound"] = dict(n_max=NMAX, weight_min=-128, weight_max=127, mood_term_max=128, bound_abs=bound, int16_ok=bound <= 32768,
                                    positive_extreme=NMAX * 127 + 7 * 16, negative_extreme=-NMAX * 128 - 8 * 16, note="every input a flag of 1; |acc| <= n*128 + 128")
    rnd = random.Random(20260910)
    def wpack(W): return bytes((v & 255) for row in W for v in row).hex()
    fwd, les = [], []
    def addf(name, W, z, mood, expect=None):
        acc, a = forward_ref(W, z, mood)
        assert max(abs(v) for v in acc) <= bound
        if expect is not None: assert a == expect, (name, a, expect)
        fwd.append(dict(name=name, n=len(z), weights=wpack(W), mood=golden.m_pack(mood), x=z, acc=acc, action=a))
    def addl(name, W, lessons, lo, hi):
        W = [row[:] for row in W]; before = wpack(W); preds, took = [], []
        for z, t in lessons:
            p, tk = learn_ref(W, z, t, lo, hi); preds.append(p); took.append(tk)
        les.append(dict(name=name, n=len(W[0]), box=[lo, hi], weights_before=before, lessons=[dict(x=z, t=t) for z, t in lessons], weights_after=wpack(W), predictions=preds, taken=took))
        return W
    Z0 = [0] * NMAX; Z1 = [1] * NMAX
    addf("all zero, 128 inputs: the first output wins the tie", [[0] * NMAX for _ in range(10)], Z1, [0] * 10, 0)
    addf("the most positive: 127 on every weight, every flag set, mood 7: 16368 on every row, output 0", [[127] * NMAX for _ in range(10)], Z1, [7] * 10, 0)
    addf("the most negative: -128 everywhere, every flag set, mood -8: -16512 on every row, output 0", [[-128] * NMAX for _ in range(10)], Z1, [-8] * 10, 0)
    W = [[0] * NMAX for _ in range(10)]; W[3][5] = 100; W[7][5] = 100; addf("a positive tie between outputs 3 and 7 goes to 3", W, [0] * 5 + [1] + [0] * (NMAX - 6), [0] * 10, 3)
    W = [[-1] * NMAX for _ in range(10)]; W[3][5] = -3; W[7][5] = -3; addf("rows 3 and 7 tie at -3 below the rest at -1: the first of the largest, 0", W, [0] * 5 + [1] + [0] * (NMAX - 6), [0] * 10, 0)
    W = [[-100] * NMAX for _ in range(10)]; W[3][5] = -3; W[7][5] = -3; addf("a negative tie between outputs 3 and 7 goes to 3", W, [0] * 5 + [1] + [0] * (NMAX - 6), [0] * 10, 3)
    W = [[0] * NMAX for _ in range(10)]; W[9][0] = 1; addf("one weight of 1 on one flag: output 9", W, [1] + [0] * (NMAX - 1), [0] * 10, 9)
    W = [[0] * NMAX for _ in range(10)]; W[2][0] = 15; addf("the mood alone decides: mood 1 on output 5 (16) beats a weight of 15", W, [1] + [0] * (NMAX - 1), [0, 0, 0, 0, 0, 1, 0, 0, 0, 0], 5)
    W = [[0] * NMAX for _ in range(10)]; W[2][0] = 16; addf("a weight of 16 ties mood 16 on output 5: the lower index, 2", W, [1] + [0] * (NMAX - 1), [0, 0, 0, 0, 0, 1, 0, 0, 0, 0], 2)
    W = [[127] * 56 for _ in range(10)]; W[4] = [-128] * 56; addf("56 inputs, the sign-extension check: a row of -128 against rows of 127", W, [1] * 56, [0] * 10, 0)
    W = [[0] * 56 for _ in range(10)]; W[6][10] = -128; W[8][10] = -127; addf("56 inputs: -127 beats -128; the rest zero: 0 wins", W, [0] * 10 + [1] + [0] * 45, [0] * 10, 0)
    W = [[-128] * 56 for _ in range(10)]; W[8][10] = -127; addf("56 inputs, all rows -128 on the active flag but row 8 at -127: 8", W, [0] * 10 + [1] + [0] * 45, [0] * 10, 8)
    for k in range(20):
        n = rnd.choice((56, 62, 64, 128)); W = [[rnd.randint(-128, 127) for _ in range(n)] for _ in range(10)]
        z = [rnd.randint(0, 1) for _ in range(n)]; addf(f"random {k}", W, z, [rnd.randint(-8, 7) for _ in range(10)])
    json.dump(dict(set="forward-v2", interface="BRAIN02 candidate", note="byte weights two's complement, inputs 0/1 flags, mood ten signed nibbles as today (m*16), 16-bit accumulators, first largest wins",
                   cases=fwd), open(os.path.join(OUT, "golden-1b/forward-v2.json"), "w"), indent=1)
    for bits in (8, 6):
        lo, hi = BOXES[bits]
        W = [[0] * 56 for _ in range(10)]; addl(f"box {bits}: from zero, taught 2 with flags 0 and 5 set: rows 2 up, 0 down", W, [([1] + [0] * 4 + [1] + [0] * 50, 2)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[2] = [hi] * 56; addl(f"box {bits}: row 2 at {hi} predicted, taught 1 twice: row 1 rises to 2, row 2 falls to {hi - 2}", W, [([1] * 56, 1), ([1] * 56, 1)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[0] = [lo] * 56; W[1] = [hi] * 56; addl(f"box {bits}: the predicted row 1 at {hi} falls to {hi - 1}; taught row 3 rises; row 0 at {lo} untouched", W, [([1] * 56, 3)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[5] = [hi] * 56; W[0] = [hi] * 56; addl(f"box {bits}: a tie at {hi} between rows 0 and 5 predicts 0; taught 5: row 5 cannot rise past {hi}, row 0 falls to {hi - 1}", W, [([1] * 56, 5)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[7] = [lo] * 56; W[0] = [lo + 1] * 56; W[1] = [lo] * 56; addl(f"box {bits}: the predicted row 0 at {lo + 1} falls to {lo} and no further on a second lesson", W, [([1] * 56, 7), ([1] * 56, 7), ([1] * 56, 7)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[4][0] = 3; addl(f"box {bits}: a no-op: the taught action is already predicted", W, [([1] + [0] * 55, 4)], lo, hi)
        W = [[0] * 128 for _ in range(10)]; addl(f"box {bits}: 128 inputs all set, taught 9 six times from zero: one lesson, then no-ops", W, [([1] * 128, 9)] * 6, lo, hi)
        for k in range(12):
            n = rnd.choice((56, 64, 128)); W = [[rnd.randint(lo, hi) for _ in range(n)] for _ in range(10)]
            addl(f"box {bits}: random {k}", W, [([rnd.randint(0, 1) for _ in range(n)], rnd.randint(0, 9)) for _ in range(rnd.randint(1, 8))], lo, hi)
    json.dump(dict(set="lessons-v2", interface="BRAIN02 candidate", note="the rule of BRAIN-INTERFACE-V1 section 6 with the clamp at the box; weights as bytes; inputs 0/1", cases=les),
              open(os.path.join(OUT, "golden-1b/lessons-v2.json"), "w"), indent=1)
    out["golden_written"] = dict(forward=len(fwd), lessons=len(les))
    json.dump(out, open(os.path.join(OUT, "parity-1b.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "vectorised_vs_reference"}, indent=1))
    return out

# ------------------------------------------------------------------------------------- budget
# the map of this build (src/kickass/tony-body.sym, BODY.md): the code and its data end at CODE_END; the
# Movable segment follows in the file and is copied out at startup, so CODE_END+1..$9fff is free at run
# time and holds the teaching shadow and the lesson block; the level tune lives at $a000 from then on.
CODE_END = 0x863e; CEIL = 0xa000; SHADOW_NOW = 0x8900; LESSON_NOW = 0x8a00; LESSON_CAP = 500; LESSON1 = 11; LESSON2 = 14
BRAIN01_SLOT = 280; MUL_TABLE = 256; EXPANSION = 20          # retired by a byte-weight, flag-input brain
def budget():
    """the exact BRAIN02 byte budget: nothing built, a table. The slot: marker 8, header 8 (kind, layout,
    inputs, hidden, outputs, period, lineage, rule), weights 10 * n bytes, mood 8 as today; the retina as
    a table (3 bytes per threshold flag, 4 per conjunction of two flags, 2 per order-2 pair over base
    flags) or as code (an estimate, labelled); the flag vector n bytes of RAM; the teaching shadow a copy
    of the weights; the lesson block at its cap. The fit against the run-time map of this build."""
    def retina_bytes(name):
        return {"R0": 56 * 3, "R1": 56 * 3 + 6 * 4, "R1b": 56 * 3 + 8 * 4, "R2": 56 * 3 + 8 * 4 + 273 * 2}[name]
    rows = []
    for name, n in (("R0", 56), ("R1", 62), ("R1b", 64), ("R1b+goal", 97), ("R2", 337)):
        base = name.split("+")[0]; goal = "goal" in name
        rt = retina_bytes(base) + (33 * 3 if goal else 0)
        weights = 10 * n; header = 16; mood = 8
        slot = header + weights + mood; pages = (slot + 255) // 256
        r = dict(arch=name, inputs=n, header=header, weights=weights, mood=mood, slot=slot, slot_pages=pages, spare_in_pages=pages * 256 - slot,
                 max_inputs_in_pages=(pages * 256 - header - mood) // 10, retina_table=rt, flag_vector=n, teach_shadow=weights,
                 acc_bound=n * 128 + 128, int16_ok=(n * 128 + 128) <= 32768, header_max_inputs=255, int16_max_inputs=(32768 - 128) // 128)
        # the code region: the slot replaces BRAIN01, the multiply table and the nibble expansions go; the
        # table and the flag vector come; the retina's code is an estimate (150..400 bytes)
        data_delta = slot - BRAIN01_SLOT - MUL_TABLE - EXPANSION + rt + n
        r["code_region_delta_data"] = data_delta; r["code_region_delta_with_code_estimate"] = [data_delta + 150, data_delta + 400]
        # the run-time fit: shadow + lesson block must sit between the new code end and the ceiling
        lesson_size = LESSON2 if goal else LESSON1
        for cap in (500, 400, 300, 200):
            block = cap * lesson_size + 16
            max_growth = CEIL - block - weights - (CODE_END + 1)
            r[f"max_code_growth_at_cap_{cap}"] = max_growth
        r["fits_now_at_cap_500_estimate_high"] = (data_delta + 400) <= r["max_code_growth_at_cap_500"]
        r["lesson_cap_that_fits_estimate_high"] = (CEIL - weights - (CODE_END + 1 + data_delta + 400) - 16) // lesson_size
        rows.append(r)
    return rows

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "check":
        D = sets(); A = arms()
        print(f"the 231: {len(D['s231'])}  teacher-visited union: {len(D['s474'])}  full union: {len(D['s1424'])}  ticks: {len(D['stream'])}")
        for name, (enc, n, binary, desc, names) in A.items():
            widths = {len(enc(list(x))) for x in D["s1424"]}; vals = {v for x in D["s1424"] for v in enc(list(x))}
            assert widths == {n}, (name, widths); assert (names is None) or len(names) == n, name
            print(f"{name:6s} n={n:3d} binary={binary} values={sorted(vals)[:4]}{'...' if len(vals) > 4 else ''}  {desc}")
        for setname in ("s231", "s474", "s1424"):
            lab = D[setname]; rel = relabel(lab)
            back = {x: to_absolute(t, href(x)) for x, t in rel.items()}
            assert back == lab, setname
            from collections import Counter
            print(f"{setname}: abs labels {dict(Counter(ABS_ACTIONS[t] for t in lab.values()))}")
            print(f"{setname}: rel labels {dict(Counter(REL_ACTIONS[t] for t in rel.values()))}; zero-dx states {sum(1 for x in lab if x[1] == 0)} (h from facing)")
        labs, S = streams(D, "rel"); print(f"streams: S1 {len(S['S1'])} S2 {len(S['S2'])} S5 {len(S['S5'])}")
        for h in (1, -1):
            for a in range(10): assert to_relative(to_absolute(a, h), h) == a and to_absolute(to_relative(a, h), h) == a
        print("vocabulary round trips: ok")
    elif cmd == "parity": parity()
    elif cmd in ("phase1b", "phase1b-undecided", "alternatives", "phase2b", "phase2b-u"):
        args = sys.argv[2:]; workers = None
        if args[:1] == ["--workers"]: workers = int(args[1]); args = args[2:]
        if cmd == "phase1b": phase1b(args or None, workers=workers or 4)
        elif cmd == "phase1b-undecided": phase1b_undecided(workers=workers or 4)
        elif cmd == "alternatives": alternatives(args or None, workers=workers or 4)
        elif cmd == "phase2b-u": phase2b(args or None, workers=workers or 2, streams_=("S2u",))
        else: phase2b(args or None, workers=workers or 2)
    elif cmd == "budget":
        for r in budget(): print(r)
    else: print(__doc__)
