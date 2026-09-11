#!/usr/bin/env python3
"""
brain025_gauntlet.py - step H of PREREG-BRAIN025.md: Candidate A against BRAIN02.5 on a small,
non-sealed gauntlet inspired by the free-play courses. It is not the sealed Phase 4 holdout and does
not touch it, and its geometries are deliberately not the census's: the census chose the design, so
reusing it would only show the design fitting its own training set.

What is measured on the machine, for each scenario and each build:
  * the observation the build actually publishes (BRAIN02's 64 inputs, BRAIN02.5's 80);
  * which of the ten outputs are good, by the same bounded rollout the census used, classified by
    Tony's own position. ADVANCE and CLIMB are good; DROP, BLOCKED, RETREAT and AIRBORNE are not.

What is measured off it, from those two things and nothing else:
  1. aliases: observations covering scenarios whose good-action sets differ;
  2. representability: whether any weight setting can choose a good action everywhere (CP-SAT);
  3. lessons to competence: the machine's own rule, run on a demonstration stream until it is right
     everywhere, or until it is clear that it will not be;
  4. retention: the same brain after an unrelated later stream;
  5. shepherding: whether being right depends on Tony standing nearby;
  6. regressions: anything BRAIN02.5 does worse than BRAIN02.

  measure     run the gauntlet on both builds -> deliverables/brain025/gauntlet.json
  compare     the six measurements from that file -> GAUNTLET.md's numbers
"""
import hashlib, json, os, re, subprocess, sys, tempfile
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables/brain025")
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
census = _load("brain025_census", os.path.join(ROOT, "tools/brain025_census.py"))
design = _load("brain025_design", os.path.join(ROOT, "tools/brain025_design.py"))
ref = _load("brain025_ref", os.path.join(ROOT, "tools/brain025_ref.py"))
b02 = _load("brain02_ref", os.path.join(ROOT, "tools/brain02_ref.py"))

FLOOR = census.FLOOR_ROW
GOOD = {"ADVANCE", "CLIMB"}

def plat(cols, level): return [(c, 21 - 2 * level) for c in cols]
def col_stack(c, h): return [(c, 21 - 2 * k) for k in range(h)]

def geometries():
    """twenty local courses of the kind a person builds in free play, none of them a census geometry"""
    G = []
    def add(name, bricks, col, row, facing, note):
        G.append(dict(name=name, bricks=bricks, col=col, row=row, facing=facing, note=note))
    # steps of several heights, two columns off rather than one
    add("step1_near", col_stack(11, 1), 7, FLOOR, +1, "one brick high, two slots off")
    add("step2_near", col_stack(11, 2), 7, FLOOR, +1, "two bricks high, two slots off")
    add("step4_near", col_stack(11, 4), 7, FLOOR, +1, "four bricks high, two slots off")
    add("stair2", col_stack(11, 1) + col_stack(13, 2), 7, FLOOR, +1, "two ascending steps")
    add("stair_down", col_stack(9, 3) + col_stack(11, 2) + col_stack(13, 1), 7, 15, +1, "standing on top of a descending stair")
    # edges and drops
    add("edge_here", plat([5, 7], 0), 7, 21, +1, "on a platform whose edge is the next column")
    add("edge_two", plat([5, 7, 9], 0), 7, 21, +1, "the edge two columns off")
    add("edge_high", plat([5, 7], 0) + plat([5, 7], 1) + plat([5, 7], 2), 7, 17, +1, "three levels up, the edge ahead")
    # gaps with landings of several widths and heights
    add("gap_small_wide_landing", plat([5, 7], 0) + plat([11, 13, 15], 0), 7, 21, +1, "one slot of gap, a wide landing")
    add("gap_small_thin_landing", plat([5, 7], 0) + plat([11], 0), 7, 21, +1, "one slot of gap, a one-slot landing")
    add("gap_wide", plat([5, 7], 0) + plat([17], 0), 7, 21, +1, "four slots of gap")
    add("gap_land_up", plat([5, 7], 0) + plat([11], 0) + plat([11], 1) + plat([13], 0) + plat([13], 1), 7, 21, +1, "a gap, the landing a level higher")
    add("gap_land_down", plat([5, 7], 0) + plat([5, 7], 1) + plat([11, 13], 0), 7, 19, +1, "a gap, the landing a level lower")
    add("notch", plat([5, 7], 0) + plat([11, 13, 15], 0), 7, 21, +1, "a one-slot notch in a long platform")
    # pockets, roofs and traps
    add("pocket1", col_stack(5, 1) + col_stack(9, 1), 7, FLOOR, +1, "one brick high on both sides")
    add("pocket3", col_stack(5, 3) + col_stack(9, 3), 7, FLOOR, +1, "three bricks high on both sides: a trap")
    add("roof_low", plat([5, 7, 9, 11], 1), 7, FLOOR, +1, "a ceiling one level above him")
    add("roof_and_step", plat([5, 7, 9, 11], 2) + col_stack(11, 1), 7, FLOOR, +1, "a step under a ceiling")
    # the ones that need a jump and a change of direction
    add("step_then_gap", col_stack(11, 1) + plat([17], 0), 7, FLOOR, +1, "a step, then a gap beyond it")
    add("gap_then_step", plat([5, 7], 0) + plat([11, 13], 0) + col_stack(15, 2), 7, 21, +1, "a gap, then a wall past the landing")
    return G

LADDER_STATE = 2
PLAYERS = [("floor_far", 26, FLOOR, 0x80, False), ("floor_near", 13, FLOOR, 0x80, False), ("ladder", 33, 6, LADDER_STATE, True)]
SPAWN_OFFSETS = [0, -2, -1, 1, 2]                       # in character columns, for the brittleness check

def scenarios():
    out = []
    for g in geometries():
        for pname, pcol, prow, pstate, on_ladder in PLAYERS:
            for mir in (0, 1):
                if mir and on_ladder: continue
                for dx in (SPAWN_OFFSETS if (pname == "floor_far" and not mir) else [0]):
                    if mir:
                        bricks = [(census.mirror_col(c) - 1, r) for (c, r) in g["bricks"]]
                        col = census.mirror_col(g["col"]) - 1 - dx; facing = -g["facing"]; pc = census.mirror_col(pcol) - 1
                    else:
                        bricks = list(g["bricks"]); col = g["col"] + dx; facing = g["facing"]; pc = pcol
                    py = census.y_on_row(prow) if not on_ladder else 8 * (prow + 6)
                    out.append(dict(name=f"{g['name']}|{pname}{'|m' if mir else ''}{f'|{dx:+d}' if dx else ''}", geometry=g["name"], note=g["note"],
                                    bricks=bricks, col=col, row=g["row"], facing=facing, player_at=pname, mirrored=bool(mir), spawn_offset=dx,
                                    pose=(census.x_of_col(col), census.y_on_row(g["row"]), 0x80 if facing > 0 else 0x00),
                                    player=(census.x_of_col(pc), py), pstate=pstate, toward=1 if pc > col else -1))
    return out

# --------------------------------------------------------------------------- measuring on a machine
def pk(a, n=1): return "".join(f"peek:{a + i:X}," for i in range(n))
def po(a, d): return "".join(f"poke:{a + i:X}:{b & 255:02X}," for i, b in enumerate(d))
def sg(x): return x - 16 if x >= 8 else x

class Rig:
    def __init__(self, prg, sym):
        self.prg = prg; self.S = {}
        for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(sym).read()): self.S.setdefault(m.group(1), int(m.group(2), 16))
        self.n = self.S["B02_N"]; self.senses = self.S.get("B02_SENSES", 20); self.retina = self.S["B02_RETINA"]
        self.sha = hashlib.sha256(open(prg, "rb").read()).hexdigest()
    def run(self, script):
        with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
        r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), self.prg, "@" + f.name], capture_output=True, text=True); os.unlink(f.name)
        return [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)]

def weights_for(rig, action):
    w = bytearray(10 * rig.n)
    if action is not None: w[action * rig.n] = 1
    return bytes(w)

def place(rig, cx, cy, state, px, py, pstate):
    S = rig.S
    return (po(S["cloneX"], [cx & 255, cx >> 8]) + po(S["cloneNextX"], [cx & 255, cx >> 8]) +
            f"poke:{S['cloneY']:X}:{cy:02X},poke:{S['cloneNextY']:X}:{cy:02X},poke:{S['cloneState']:X}:{state:02X},poke:{S['cloneStateAllowed']:X}:{state:02X}," +
            po(S["physPlayerX"], [px & 255, px >> 8]) + f"poke:{S['physPlayerY']:X}:{py:02X},poke:{S['physPlayerState']:X}:{pstate:02X},")

def measure(rig, SC):
    """the published observation and the ten outcomes, on one build, for every scenario"""
    S = rig.S; ZERO = bytes(10 * rig.n); out = []
    for i, sc in enumerate(SC):
        s = f"wait:300,poke:{S['brainKind']:X}:01," + po(S["brainWeights"], ZERO) + po(S["brainMood"], bytes(10))
        for (c, r) in sc["bricks"]: s += census.brick(c, r)
        s += place(rig, *sc["pose"], *sc["player"], sc["pstate"])
        s += f"wait:{census.SETTLE},sync," + pk(S["cloneSenses"], rig.senses) + pk(S["cloneX"], 2) + pk(S["cloneY"]) + "snapshot,"
        s += "restore,".join(po(S["brainWeights"], weights_for(rig, a)) + f"wait:{census.HOLD}," + po(S["brainWeights"], ZERO) +
                             f"wait:{census.COAST},sync," + pk(S["cloneX"], 2) + pk(S["cloneY"]) + pk(S["cloneSenses"] + 8) + pk(S["cloneSenses"] + 6) for a in range(10))
        v = rig.run(s); head = rig.senses + 3
        if len(v) < head + 50: print(f"   {sc['name']}: short read ({len(v)}), skipped"); continue
        x = [sg(t) for t in v[:rig.senses]]; cx0 = v[rig.senses] | v[rig.senses + 1] << 8; cy0 = v[rig.senses + 2]
        outcomes = []
        for a in range(10):
            g = v[head + a * 5:head + (a + 1) * 5]
            cx1 = g[0] | g[1] << 8; cy1 = g[2]
            outcomes.append(census.classify(sc, cx0, cy0, cx1, cy1, sg(g[3]), sg(g[4])))
        out.append(dict(name=sc["name"], geometry=sc["geometry"], player_at=sc["player_at"], mirrored=sc["mirrored"], spawn_offset=sc["spawn_offset"],
                        note=sc["note"], senses=x, start=dict(col=(cx0 >> 3) - 2, row=(cy0 >> 3) - 6), toward=sc["toward"], outcomes=outcomes,
                        good=[a for a in range(10) if outcomes[a] in GOOD]))
        if (i + 1) % 30 == 0: print(f"   {rig.prg.split('/')[-1]}: {i + 1}/{len(SC)}")
    return out

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "measure":
    SC = scenarios()
    a = Rig(os.path.join(ROOT, "deliverables/prg/minimal64/tony-b02-a.prg"), os.path.join(ROOT, "src/kickass/tony-b02-a.sym"))
    n = Rig(os.path.join(ROOT, "src/kickass/b025-a.prg"), os.path.join(ROOT, "src/kickass/b025-a.sym"))
    rows_a = measure(a, SC); rows_n = measure(n, SC)
    json.dump(dict(scenarios=len(SC), geometries=len(geometries()),
                   builds=dict(candidate_a=dict(prg="tony-b02-a.prg", sha256=a.sha, inputs=a.n, senses=a.senses, retina=a.retina),
                               brain025=dict(prg="b025-a.prg", sha256=n.sha, inputs=n.n, senses=n.senses, retina=n.retina)),
                   hold=census.HOLD, coast=census.COAST, settle=census.SETTLE, rows=dict(candidate_a=rows_a, brain025=rows_n)),
              open(os.path.join(OUT, "gauntlet.json"), "w"), indent=1)
    print(f"measured {len(rows_a)} on Candidate A and {len(rows_n)} on BRAIN02.5 -> deliverables/brain025/gauntlet.json")

# ------------------------------------------------------------------------------- the six measurements
def vectors(rows, build):
    """each scenario's input vector for that build: BRAIN02's retina on twenty senses, BRAIN02.5's on
    twenty-seven. Both come from the machine's own published block."""
    if build == "candidate_a":
        e = b02.table_R1b(); return [b02.flags(e, r["senses"][:20]) for r in rows]
    e = ref.table_T1(); return [ref.flags(e, r["senses"]) for r in rows]

def alias_report(rows, Z):
    by = {}
    for r, z in zip(rows, Z): by.setdefault("".join(map(str, z)), []).append(r)
    classes = []
    for key, g in by.items():
        sets = {tuple(r["good"]) for r in g}
        conflict = any(not (set(a) & set(b)) for a in sets for b in sets if a != b)
        classes.append(dict(members=[r["name"] for r in g], geometries=sorted({r["geometry"] for r in g}), good_sets=[list(s) for s in sets], conflicting=conflict))
    return dict(observations=len(by), classes_over_one_geometry=sum(1 for c in classes if len(c["geometries"]) > 1),
                conflicting=sum(1 for c in classes if c["conflicting"]),
                conflicting_detail=[c for c in classes if c["conflicting"]][:12])

def representable(Z, goods, box=(-128, 127), seconds=120):
    """is there any weight setting whose argmax lands in the good set everywhere? CP-SAT, over the same
    integer box the machine uses. Scenarios with no good action at all are left out and counted."""
    from ortools.sat.python import cp_model
    idx = [i for i, g in enumerate(goods) if g]
    n = len(Z[0]); M = cp_model.CpModel()
    W = [[M.NewIntVar(box[0], box[1], f"w{o}_{i}") for i in range(n)] for o in range(10)]
    acc = {}
    for s in idx:
        on = [i for i in range(n) if Z[s][i]]
        for o in range(10):
            a = M.NewIntVar(-128 * n, 127 * n, f"a{s}_{o}")
            M.Add(a == sum(W[o][i] for i in on)); acc[(s, o)] = a
    for s in idx:
        good = goods[s]; bad = [o for o in range(10) if o not in good]
        picks = []
        for o in good:
            p = M.NewBoolVar(f"p{s}_{o}"); picks.append(p)
            for b in bad: M.Add(acc[(s, o)] >= acc[(s, b)] + 1).OnlyEnforceIf(p)
        M.AddExactlyOne(picks)
    sol = cp_model.CpSolver(); sol.parameters.max_time_in_seconds = seconds; sol.parameters.num_search_workers = 8
    st = sol.Solve(M)
    name = {cp_model.OPTIMAL: "feasible", cp_model.FEASIBLE: "feasible", cp_model.INFEASIBLE: "infeasible", cp_model.UNKNOWN: "undecided"}[st]
    W0 = [[sol.Value(W[o][i]) for i in range(n)] for o in range(10)] if name == "feasible" else None
    return dict(status=name, scenarios=len(idx), no_good_action=len(goods) - len(idx)), W0

def argmax(W, z):
    acc = [sum(W[o][i] for i in range(len(z)) if z[i]) for o in range(10)]
    return max(range(10), key=lambda o: (acc[o], -o))

def teach_to_competence(Z, goods, passes=400):
    """the machine's own rule, on a demonstration stream that shows the preferred good action. Returns the
    lessons spent and whether every scenario ends choosing something good."""
    n = len(Z[0]); W = [[0] * n for _ in range(10)]
    idx = [i for i, g in enumerate(goods) if g]
    lessons = 0; first_ok = None
    for p in range(passes):
        for s in idx:
            t = min(goods[s]); a = argmax(W, Z[s])
            if a in goods[s]: continue
            for i in range(n):
                if Z[s][i]:
                    W[t][i] = min(127, W[t][i] + 1); W[a][i] = max(-128, W[a][i] - 1)
            lessons += 1
        right = sum(1 for s in idx for _ in [0] if argmax(W, Z[s]) in goods[s])
        if right == len(idx) and first_ok is None: first_ok = (p + 1, lessons); break
    right = [s for s in idx if argmax(W, Z[s]) in goods[s]]
    return dict(lessons=lessons, passes_to_competence=(first_ok[0] if first_ok else None), lessons_to_competence=(first_ok[1] if first_ok else None),
                right=len(right), of=len(idx), accuracy=len(right) / len(idx) if idx else None), W

def accuracy(W, Z, goods, sel=None):
    idx = [i for i, g in enumerate(goods) if g and (sel is None or sel(i))]
    if not idx: return None, 0
    return sum(1 for s in idx if argmax(W, Z[s]) in goods[s]) / len(idx), len(idx)

def unrelated_stream(build, passes=3):
    """an unrelated later teaching stream: the teacher-visited union of the bake-off, relabelled to the
    relative vocabulary, with flat terrain appended for the wider build. Nothing to do with the gauntlet."""
    b2 = _load("bakeoff2", os.path.join(ROOT, "tools/bakeoff2.py")); D = b2.sets()
    union = b2.relabel(D["s474"])
    out = []
    for _ in range(passes):
        for x, t in union.items():
            if build == "candidate_a": z = b02.flags(b02.table_R1b(), list(x))
            else: z = ref.flags(ref.table_T1(), list(x) + [7, 0, 0, 0, 0, 7, 7])
            out.append((z, t))
    return out

def apply_stream(W, stream):
    n = len(W[0]); applied = 0
    for z, t in stream:
        a = argmax(W, z)
        if a == t: continue
        for i in range(n):
            if z[i]:
                W[t][i] = min(127, W[t][i] + 1); W[a][i] = max(-128, W[a][i] - 1)
        applied += 1
    return applied

def compare():
    d = json.load(open(os.path.join(OUT, "gauntlet.json")))
    res = dict(builds=d["builds"], scenarios=d["scenarios"], geometries=d["geometries"], per_build={})
    # Which actions are good is a fact about the room and the physics, not about the brain: both builds run
    # the same clone through the same world and the action is forced by the weights either way. The two
    # machines' own rollouts nonetheless disagree on some scenarios, because BRAIN02.5's main loop is
    # slower and a forced output is therefore applied over a slightly different number of decisions. So the
    # ground truth is measured once, on the frozen Candidate A build, and both learners are judged against
    # it; the disagreement is reported rather than hidden.
    ra_, rn_ = d["rows"]["candidate_a"], d["rows"]["brain025"]
    by_name = {r["name"]: r for r in rn_}
    agree = sum(1 for r in ra_ if set(r["good"]) == set(by_name.get(r["name"], {}).get("good", [])))
    res["ground_truth"] = dict(measured_on="candidate_a", scenarios=len(ra_), own_measurements_agree=agree,
                               own_measurements_differ=len(ra_) - agree,
                               note="the good-action sets are taken from Candidate A's rollouts for both builds; BRAIN02.5's own rollouts agreed on {} of {}".format(agree, len(ra_)))
    print(f"ground truth: measured once on Candidate A; BRAIN02.5's own rollouts agreed on {agree} of {len(ra_)} scenarios (the rest differ by rollout pacing, not by terrain)")
    TRUTH = {r["name"]: r["good"] for r in ra_}
    Zs = {}; G = {}
    for build in ("candidate_a", "brain025"):
        rows = d["rows"][build]; Z = vectors(rows, build); goods = [TRUTH.get(r["name"], []) for r in rows]
        Zs[build] = (rows, Z, goods)
        print(f"\n=== {build}: {len(rows)} scenarios, {len(Z[0])} inputs")
        al = alias_report(rows, Z); print(f"  1. aliases: {al['observations']} distinct observations, {al['classes_over_one_geometry']} covering more than one geometry, {al['conflicting']} with conflicting good-action sets")
        rep, W0 = representable(Z, goods); print(f"  2. representability: {rep['status']} over {rep['scenarios']} scenarios ({rep['no_good_action']} had no good action at all)")
        tc, W = teach_to_competence(Z, goods); print(f"  3. lessons to competence: {tc['lessons_to_competence']} in {tc['passes_to_competence']} passes" if tc["lessons_to_competence"] else f"  3. never competent: {tc['right']} of {tc['of']} right after {tc['lessons']} lessons ({tc['accuracy']:.0%})")
        Wr = [r[:] for r in W]; applied = apply_stream(Wr, unrelated_stream(build))
        acc_after, _ = accuracy(Wr, Z, goods); print(f"  4. retention: after an unrelated stream of {applied} applied lessons, {acc_after:.0%} of the gauntlet still right (was {tc['accuracy']:.0%})")
        far = lambda i: rows[i]["player_at"] == "floor_far"
        Zf = [Z[i] for i in range(len(Z)) if far(i)]; Gf = [goods[i] for i in range(len(Z)) if far(i)]
        repf, _ = representable(Zf, Gf)
        tcf, Wf = teach_to_competence(Zf, Gf)
        near_acc, near_n = accuracy(Wf, Z, goods, lambda i: rows[i]["player_at"] == "floor_near")
        lad_acc, lad_n = accuracy(Wf, Z, goods, lambda i: rows[i]["player_at"] == "ladder")
        own_acc, _ = accuracy(Wf, Zf, Gf)
        print(f"  5. shepherding: taught only with Tony far off ({tcf['lessons_to_competence'] or tcf['lessons']} lessons, {own_acc:.0%} right there, that subset {repf['status']}), it is {near_acc:.0%} right with him near ({near_n}) and {lad_acc:.0%} with him on the ladder ({lad_n})")
        byg = {}
        for i, r in enumerate(rows):
            if not goods[i]: continue
            byg.setdefault(r["geometry"], []).append(argmax(W, Z[i]) in goods[i])
        spawn = {}
        for i, r in enumerate(rows):
            if r["spawn_offset"] == 0 or not goods[i]: continue
            spawn.setdefault(r["geometry"], []).append(argmax(W, Z[i]) in goods[i])
        res["per_build"][build] = dict(aliases=al, representability=rep, competence=tc, retention=dict(applied=applied, accuracy_after=acc_after),
                                       shepherding=dict(taught_far_lessons=tcf["lessons_to_competence"] or tcf["lessons"], far_subset_representable=repf["status"], accuracy_far=own_acc, accuracy_near=near_acc, accuracy_ladder=lad_acc),
                                       still_wrong=[rows[i]["name"] for i in range(len(rows)) if goods[i] and argmax(W, Z[i]) not in goods[i]],
                                       by_geometry={k: sum(v) / len(v) for k, v in byg.items()},
                                       spawn_variation={k: sum(v) / len(v) for k, v in spawn.items()})
        G[build] = (W, goods, Z, rows)
    # 6. regressions, scenario by scenario
    (Wa, ga, Za, ra) = G["candidate_a"]; (Wn, gn, Zn, rn) = G["brain025"]
    regress = []; gain = []; common = 0; a_right = 0; n_right = 0; differed = []
    for i in range(min(len(ra), len(rn))):
        if not ga[i] or not gn[i]: continue
        common += 1
        a_ok = argmax(Wa, Za[i]) in ga[i]; n_ok = argmax(Wn, Zn[i]) in gn[i]
        a_right += a_ok; n_right += n_ok
        if a_ok and not n_ok: regress.append(ra[i]["name"])
        if n_ok and not a_ok: gain.append(ra[i]["name"])
    res["regressions"] = regress; res["gains"] = gain
    res["like_for_like"] = dict(comparable=common, not_comparable=len(differed), not_comparable_names=differed[:12], candidate_a_right=a_right, brain025_right=n_right)
    print(f"\n6. like for like, on the {common} scenarios where both machines measured the same good actions:")
    print(f"     Candidate A right on {a_right} ({a_right / common:.0%}), BRAIN02.5 on {n_right} ({n_right / common:.0%}); {len(gain)} gained, {len(regress)} regressed" + (f" ({', '.join(regress[:6])})" if regress else ""))
    print(f"     both judged against the same ground truth, so every scenario with a good action is comparable")
    json.dump(res, open(os.path.join(OUT, "gauntlet-results.json"), "w"), indent=1)
    return res

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "compare": compare()
