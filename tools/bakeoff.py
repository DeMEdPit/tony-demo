#!/usr/bin/env python3
"""
bakeoff.py - the architecture bake-off, phases 1 and 2, offline (deliverables/bakeoff/PREREG-BAKEOFF.md).

Held fixed: the twenty raw senses as published, the ten actions, the curriculum teacher of
PREREG-CURRICULUM.md, the 4-bit range -8..7, the step-of-one rule with the mood-free prediction and
the first-largest tie rule. What varies is the ENCODING the readout sees: the raw senses, or the raw
senses plus flags derived from them by a fixed table (a designed retina), or the raw senses plus fixed
random association units (the Mark I layout). Flags are 0 or 7, like the sense block's own flags.

  prereg   print the arms table (for the pre-registration document)
  phase1   exact representability and margin per arm, CBC through pulp, on the frozen 231 teacher
           states and on their union with the evaluation-encountered vectors labelled by the teacher
  phase2   learnability by the exact rule from zero, per arm, on three streams

Nothing here touches the PRG.
"""
import glob, hashlib, json, os, random, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables/bakeoff")
CUR = os.path.join(ROOT, "deliverables/curriculum")
_s = importlib.util.spec_from_file_location("cu", os.path.join(ROOT, "tools/curriculum.py")); cu = importlib.util.module_from_spec(_s); _s.loader.exec_module(cu)
teacher = cu.teacher
ACTIONS = ["idle", "left", "right", "up", "down", "jump", "jump left", "jump right", "build left", "build right"]
F = 7                                        # a flag that holds

# ------------------------------------------------------------------------------------- the features
# Every feature is a fixed function of the twenty raw senses as published (signed nibbles). The 6502
# and the reference must derive them identically; the definitions here are the contract for Phase 3.
def raw(x): return list(x)
def therm_dy_up(x):   return [F if x[2] >= k else 0 for k in range(1, 8)]        # "Tony at least k bricks above me", k = 1..7
def therm_dy_down(x): return [F if x[2] <= -k else 0 for k in range(1, 8)]       # "Tony at least k bricks below me"
def onehot_dy(x):     return [F if x[2] == v else 0 for v in range(-7, 8)]       # 15 flags
def dx_sign(x):       return [F if x[1] > 0 else 0, F if x[1] < 0 else 0]        # "he is to my right", "to my left"
def therm_adx(x):     return [F if abs(x[1]) >= k else 0 for k in range(1, 8)]   # "at least k buckets away"
def onehot_adx(x):    return [F if abs(x[1]) == k else 0 for k in range(0, 8)]   # 8 flags
def onehot_last(x):
    """the last action as a category. Sense 16 holds the action index 0..9 in the low nibble; the
    reference sign-extends it, so 8 and 9 arrive as -8 and -7. The category is the raw nibble
    (value & 15): nibble k sets flag k for k in 0..9; nibbles 10..15 (never produced) set no flag."""
    r = x[16] & 15
    return [F if r == k else 0 for k in range(10)]
PARTS = dict(dyup=(therm_dy_up, 7), dydown=(therm_dy_down, 7), dy1h=(onehot_dy, 15), dxs=(dx_sign, 2), adxt=(therm_adx, 7), adx1h=(onehot_adx, 8), last=(onehot_last, 10))

class Assoc:
    """fixed random association units over the twenty raw senses, generated from a seed and never
    learned. Two kinds. 'sign': a unit reads four senses with fixed random signs and fires when the
    signed sum reaches its threshold. 'bucket': a unit reads two senses, each against a fixed random
    threshold in a fixed direction, and fires when both hold (a random conjunction of two detectors).
    The wiring is the published structure: units(seed) lists every unit's senses, signs/thresholds."""
    def __init__(self, K, seed, kind):
        self.K, self.seed, self.kind = K, seed, kind
        rng = random.Random(f"{kind}-{K}-{seed}")
        self.units = []
        for _ in range(K):
            if kind == "sign":
                idx = rng.sample(range(1, 20), 4); sg = [rng.choice((-1, 1)) for _ in idx]; th = rng.choice((0, 4, 8, 12))
                self.units.append(dict(senses=idx, signs=sg, threshold=th))
            else:
                idx = rng.sample(range(1, 20), 2); conds = []
                for i in idx:
                    lo, hi = (-7, 7) if i in (1, 2) else (0, 7)
                    k = rng.randint(lo + 1, hi); conds.append((i, rng.choice((">=", "<=")), k))
                self.units.append(dict(conds=conds))
    def __call__(self, x):
        out = []
        for u in self.units:
            if self.kind == "sign": out.append(F if sum(s * x[i] for i, s in zip(u["senses"], u["signs"])) >= u["threshold"] else 0)
            else: out.append(F if all((x[i] >= k) if op == ">=" else (x[i] <= k) for i, op, k in u["conds"]) else 0)
        return out

def arms():
    """name -> (encoder, width, description)"""
    A = {}
    A["A0_raw"] = (lambda x: raw(x), 20, "the twenty senses as published")
    A["A1_raw+dy1h+last"] = (lambda x: raw(x) + onehot_dy(x) + onehot_last(x), 45, "A0 plus one-hot dy (15) and one-hot last action (10)")
    A["A2_A1+adx1h+dxs"] = (lambda x: raw(x) + onehot_dy(x) + onehot_last(x) + onehot_adx(x) + dx_sign(x), 55, "A1 plus one-hot |dx| (8) and the sign of dx (2)")
    # the thermometer family: every subset of {dy up, dy down, dx sign, last one-hot, |dx| thermometer} over the raw senses
    names = ["dyup", "dydown", "dxs", "last", "adxt"]
    for mask in range(1, 32):
        parts = [n for b, n in enumerate(names) if mask >> b & 1]
        fs = [PARTS[n][0] for n in parts]; w = 20 + sum(PARTS[n][1] for n in parts)
        A["T_" + "+".join(parts)] = ((lambda fs: lambda x: raw(x) + [v for f in fs for v in f(x)])(fs), w, "raw plus " + ", ".join(parts))
    for kind in ("sign", "bucket"):
        for K in (32, 48, 64):
            for seed in range(10):
                u = Assoc(K, seed, kind)
                A[f"C3_{kind}_K{K}_s{seed}"] = ((lambda u: lambda x: raw(x) + u(x))(u), 20 + K, f"raw plus {K} fixed {kind} units, seed {seed}")
    return A
T4 = "T_dyup+dxs+last"                        # the review's primary arm: raw + thermometer dy up + dx sign + last one-hot, 39 inputs

# --------------------------------------------------------------------------------------- the data
def visited():
    """the 231 teacher states with their labels, and the tick stream in curriculum order"""
    stream, labels = [], {}
    for f in sorted(glob.glob(os.path.join(CUR, "decisions-*.json"))):
        for d in json.load(open(f)):
            x = tuple(d["senses"]); stream.append((x, d["action"])); labels.setdefault(x, d["action"])
    return labels, stream
def union_states(labels):
    E = json.load(open(os.path.join(CUR, "encountered2.json")))
    U = dict(labels)
    for e in E["encountered"]:
        x = tuple(int(v) for v in e["key"].split(","))
        if x not in U: U[x] = teacher(list(x))
    return U

# ---------------------------------------------------------------------------- phase 1: CBC exact
def check(labels, enc, n, margin=False, time_limit=300):
    import pulp
    prob = pulp.LpProblem("rep", pulp.LpMaximize if margin else pulp.LpMinimize)
    w = [[pulp.LpVariable(f"w_{o}_{i}", -8, 7, cat="Integer") for i in range(n)] for o in range(10)]
    m = pulp.LpVariable("m", 0, 64 * n, cat="Integer") if margin else None
    prob += (m if margin else 0)
    X = {x: enc(list(x)) for x in labels}
    for x, t in labels.items():
        z = X[x]
        for o in range(10):
            if o == t: continue
            gap = pulp.lpSum((w[t][i] - w[o][i]) * z[i] for i in range(n) if z[i] != 0)
            prob += gap >= (1 if o < t else 0) + (m if margin else 0)
    t0 = time.time(); prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)); dt = time.time() - t0
    status = pulp.LpStatus[prob.status]
    W = [[int(round(w[o][i].value() or 0)) for i in range(n)] for o in range(10)] if status in ("Optimal",) or (margin and prob.status != -1 and w[0][0].value() is not None) else None
    mv = int(round(m.value())) if (margin and m.value() is not None) else None
    bad = None
    if W is not None:
        bad = 0
        for x, t in labels.items():
            z = X[x]; acc = [sum(W[o][i] * z[i] for i in range(n)) for o in range(10)]
            if max(range(10), key=lambda o: (acc[o], -o)) != t: bad += 1
    return dict(status=status, seconds=round(dt, 1), margin=mv, mislabelled=bad, weights=W)

def _phase1_one(args):
    name, n, desc, labels, U, do_union = args
    enc = arms()[name][0]
    r = dict(width=n, description=desc)
    f = check(labels, enc, n, margin=False, time_limit=120); r["frozen231"] = dict(status=f["status"], seconds=f["seconds"], mislabelled=f["mislabelled"])
    if f["status"] == "Optimal":
        mg = check(labels, enc, n, margin=True, time_limit=120); r["frozen231"]["margin"] = mg["margin"]; r["frozen231"]["margin_status"] = mg["status"]
        if mg["weights"] is not None and mg["mislabelled"] == 0: r["frozen231"]["max_abs_w"] = max(abs(v) for row in mg["weights"] for v in row)
        if do_union:
            u = check(U, enc, n, margin=False, time_limit=300); r["union"] = dict(status=u["status"], seconds=u["seconds"], mislabelled=u["mislabelled"])
    return name, r

def phase1(workers=None):
    """every arm's exact representability on the 231 (feasibility, then the largest margin), and the
    union with the encountered vectors for the designed arms and the first two feasible seeds of each
    association group (the union is the expensive solve). Arms run in parallel processes."""
    import multiprocessing as mp
    os.makedirs(OUT, exist_ok=True)
    labels, stream = visited(); U = union_states(labels); A = arms()
    print(f"{len(labels)} teacher states, {len(U)} in the union with the encountered vectors; {len(A)} arms", flush=True)
    jobs = [(name, n, desc, labels, U, not name.startswith("C3_")) for name, (enc, n, desc) in A.items()]
    res = {}
    with mp.Pool(workers or max(1, os.cpu_count() - 1)) as pool:
        for name, r in pool.imap_unordered(_phase1_one, jobs):
            res[name] = r
            print(f"{name:26s} n={r['width']:3d}  231: {r['frozen231']['status']:11s} {r['frozen231']['seconds']:6.1f}s margin {r['frozen231'].get('margin')}   union: {r.get('union', {}).get('status', '-'):11s} {r.get('union', {}).get('seconds', '')}", flush=True)
            json.dump(res, open(os.path.join(OUT, "phase1.json"), "w"), indent=1)
    # the union for the first two feasible seeds of each association group, after the rest
    extra = []
    for kind in ("sign", "bucket"):
        for K in (32, 48, 64):
            ok = [f"C3_{kind}_K{K}_s{s}" for s in range(10) if res.get(f"C3_{kind}_K{K}_s{s}", {}).get("frozen231", {}).get("status") == "Optimal"][:2]
            extra += [(name, A[name][1], A[name][2], labels, U, True) for name in ok]
    if extra:
        with mp.Pool(workers or max(1, os.cpu_count() - 1)) as pool:
            for name, r in pool.imap_unordered(_phase1_one, extra):
                res[name]["union"] = r.get("union"); print(f"{name:26s} union: {r.get('union', {}).get('status', '-')} {r.get('union', {}).get('seconds', '')}", flush=True)
                json.dump(res, open(os.path.join(OUT, "phase1.json"), "w"), indent=1)
    return res

# ------------------------------------------------------------------------ phase 2: the exact rule
def learn_stream(enc, n, stream, labels, passes=300, subsample_idle=None, seed=0):
    """the rule from zero over a stream of (x, t) repeated for passes; returns the curve"""
    Z = {x: np.array(enc(list(x)), dtype=np.int64) for x in labels}
    for x, t in stream:
        if x not in Z: Z[x] = np.array(enc(list(x)), dtype=np.int64)
    S = np.array([Z[x] for x, t in stream]); T = np.array([t for x, t in stream]); N = len(stream)
    if subsample_idle:
        rng = random.Random(seed); keep = []
        for k in range(N):
            if T[k] != 0 or (k and T[k - 1] != 0) or (k + 1 < N and T[k + 1] != 0) or rng.random() < subsample_idle: keep.append(k)
        S, T, N = S[keep], T[keep], len(keep)
    L = np.array([Z[x] for x in labels]); LT = np.array([labels[x] for x in labels])
    w = np.zeros((10, n), dtype=np.int64); lessons = 0; first_full = None; full_passes = 0; curve = []; clamps = 0
    for p in range(1, passes + 1):
        taken = 0
        for k in range(N):
            z = S[k]; acc = w @ z; pred = int(np.argmax(acc))
            if pred != T[k]:
                sg = np.sign(z); w[T[k]] += sg; w[pred] -= sg
                over = (w > 7).sum() + (w < -8).sum(); clamps += int(over)
                np.clip(w, -8, 7, out=w); taken += 1
        lessons += taken
        agree = int((np.argmax(L @ w.T, axis=1) == LT).sum())
        curve.append((p, taken, agree))
        if agree == len(labels):
            full_passes += 1
            if first_full is None: first_full = lessons
    never = int((np.argmax(L @ w.T, axis=1) != LT).sum())
    final_agree = curve[-1][2]
    return dict(lessons_total=lessons, first_full_at_lessons=first_full, passes_at_full=full_passes, passes=passes, final_agree=final_agree, states=len(labels),
                best_agree=max(c[2] for c in curve), clamps=clamps, lessons_per_pass_last10=[c[1] for c in curve[-10:]], agree_curve=[c[2] for c in curve])

def phase2(only=None):
    os.makedirs(OUT, exist_ok=True)
    labels, stream = visited(); A = arms()
    p1 = json.load(open(os.path.join(OUT, "phase1.json"))) if os.path.exists(os.path.join(OUT, "phase1.json")) else {}
    recorded = []
    for k in range(1, 8): recorded += [(tuple(l["x"]), l["t"]) for l in json.load(open(os.path.join(CUR, f"lessons-pass{k:02d}.json")))]
    uniq = list(labels.items())
    res = {}
    names = only or [n for n in A if n in p1 and p1[n]["frozen231"]["status"] == "Optimal"] or list(A)
    for name in names:
        enc, n, desc = A[name]; r = dict(width=n)
        r["S1_tick_stream"] = learn_stream(enc, n, stream, labels)
        r["S2_labels_cycled"] = learn_stream(enc, n, uniq, labels)
        r["S3_idle_subsampled"] = learn_stream(enc, n, stream, labels, subsample_idle=0.125)
        r["S0_recorded_lessons"] = learn_stream(enc, n, recorded, labels)
        res[name] = r
        print(f"{name:26s} n={n:3d} " + "  ".join(f"{k[:2]}: first {v['first_full_at_lessons']} full {v['passes_at_full']}/{v['passes']} final {v['final_agree']}/{v['states']} best {v['best_agree']}" for k, v in r.items() if k != "width"), flush=True)
        json.dump(res, open(os.path.join(OUT, "phase2.json"), "w"))
    return res

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prereg":
        for name, (enc, n, desc) in arms().items(): print(f"| {name} | {n} | {desc} |")
    elif cmd == "phase1": phase1()
    elif cmd == "phase2": phase2(sys.argv[2:] or None)
