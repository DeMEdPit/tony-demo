#!/usr/bin/env python3
"""bakeoff2_report.py - tables from phase2b.json / phase1b.json for PHASE2B.md and PHASE1B.md"""
import json, os, sys, glob
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import importlib.util
_s = importlib.util.spec_from_file_location("b2", os.path.join(ROOT, "tools/bakeoff2.py")); b2 = importlib.util.module_from_spec(_s); _s.loader.exec_module(b2)
OUT = os.path.join(ROOT, "deliverables/bakeoff")

def first_pass(r):
    """the pass at which full agreement was first reached (1-based), or None"""
    for p, a in enumerate(r["agree_curve"], 1):
        if a == r["states"]: return p
    return None
def survives_s1(r):
    p = first_pass(r)
    if p is None or r["first_full_at_lessons"] > 500: return False
    remaining = 300 - p
    return r["passes_at_full"] - 1 >= 0.8 * remaining if remaining else True
def p2_table(res, arms, vocab, bits):
    rows = []
    for a in arms:
        cells = []
        for s in ("S1", "S2", "S4", "S5"):
            r = res.get(f"{a}|{vocab}|{bits}|{s}")
            if not r: cells.append("-"); continue
            ff = r["first_full_at_lessons"]; held = r["passes_at_full"]
            if s == "S4":
                clean = [t - n for t, n in zip(r["lessons_per_pass_last10"], r["noisy_lessons_last10"])]
                mean100 = np.mean(r["agree_curve"][-100:])
                cells.append(f"best {r['best_agree']}, mean of the last 100 passes {mean100:.0f}, clean lessons/pass {np.mean(clean):.0f} beside {np.mean(r['noisy_lessons_last10']):.0f} corrupted")
            elif s == "S5":
                cells.append(f"best {r['best_agree']}, final {r['final_agree']}")
            else:
                cells.append((f"full at {ff}, held {held}/300" if ff is not None else f"never; best {r['best_agree']}, final {r['final_agree']}") + f", clamps {r['clamps']}, max\\|w\\| {r['max_abs_w_curve_max']}")
        r1 = res.get(f"{a}|{vocab}|{bits}|S1"); u = f"{r1['union_best_agree']}/{r1['union_states']} (final {r1['union_final_agree']})" if r1 else "-"
        rows.append(f"| `{a}` | {r1['width'] if r1 else ''} | " + " | ".join(cells) + f" | {u} |")
    return "| arm | n | S1 tick stream | S2 labels cycled | S4 noisy human | S5 lagging human | 474 agreement from S1 |\n|---|---:|---|---|---|---|---|\n" + "\n".join(rows)
def s2u_table(res, arms, vocab):
    rows = []
    for a in arms:
        cells = []
        for bits in (8, 6, 4):
            r = res.get(f"{a}|{vocab}|{bits}|S2u")
            if not r: cells.append("-"); continue
            ff = r["first_full_at_lessons"]
            cells.append((f"full at {ff}, held {r['passes_at_full']}/300" if ff is not None else f"never; best {r['best_agree']}, final {r['final_agree']}") + f", clamps {r['clamps']}, max\\|w\\| {r['max_abs_w_curve_max']}; the 231: {r['union_final_agree']}/231")
        rows.append(f"| `{a}` | " + " | ".join(cells) + " |")
    return "| arm | 8 bits | 6 bits | 4 bits |\n|---|---|---|---|\n" + "\n".join(rows)
def survivors(res, arms):
    rows = []
    for a in arms:
        for vocab in ("abs", "rel"):
            for bits in (8, 6, 4):
                r1 = res.get(f"{a}|{vocab}|{bits}|S1"); r4 = res.get(f"{a}|{vocab}|{bits}|S4"); r5 = res.get(f"{a}|{vocab}|{bits}|S5")
                if not (r1 and r4 and r5): continue
                s1 = survives_s1(r1); s4 = r4["best_agree"] >= r1["best_agree"] - 5; s5 = r5["best_agree"] >= r1["best_agree"] - 5
                rows.append(f"| `{a}` | {vocab} | {bits} | {'yes' if s1 else 'no'} ({r1['first_full_at_lessons']}, held {r1['passes_at_full']}) | {'yes' if s4 else 'no'} ({r4['best_agree']}) | {'yes' if s5 else 'no'} ({r5['best_agree']}) | {'**survives**' if s1 and s4 and s5 else ('S1 and S4 only' if s1 and s4 else 'no')} |")
    return "| arm | vocabulary | bits | S1: full within 500 lessons, held 80% | S4 best within 5 | S5 best within 5 | verdict |\n|---|---|---:|---|---|---|---|\n" + "\n".join(rows)
def s5_ceiling():
    """the best agreement with the clean 231 labels any deterministic policy could reach on S5's labels:
    per state, the majority label under the lag against the clean label"""
    D = b2.sets(); out = {}
    for vocab in ("abs", "rel"):
        lab, S = b2.streams(D, vocab)
        from collections import Counter, defaultdict
        votes = defaultdict(Counter)
        for x, t in S["S5"]: votes[x][t] += 1
        agree = sum(1 for x in lab if votes[x].most_common(1)[0][0] == lab[x])
        conflicting = sum(1 for x in lab if len(votes[x]) > 1)
        out[vocab] = dict(ceiling=agree, states=len(lab), states_with_conflicting_lag_labels=conflicting)
    return out

if __name__ == "__main__":
    what = sys.argv[1]
    if what == "p2":
        res = json.load(open(os.path.join(OUT, "phase2b.json")))
        arms = ["R0", "R1", "R1b", "R2", "raw20", "T36", "A2"]
        for vocab in ("abs", "rel"):
            for bits in (8, 6, 4):
                print(f"\n### {vocab}, {bits} bits\n"); print(p2_table(res, arms, vocab, bits))
        print("\n### S2u\n")
        for vocab in ("abs", "rel"): print(f"\n{vocab}\n"); print(s2u_table(res, arms, vocab))
        print("\n### survivors\n"); print(survivors(res, arms))
        print("\n### S5 ceiling\n"); print(s5_ceiling())

# ------------------------------------------------------------------------------------- phase 1b
def p1_load():
    res = {}
    for f in ("phase1b.json", "phase1b-B.json"):
        p = os.path.join(OUT, f)
        if os.path.exists(p): res.update(json.load(open(p)))
    return res
def p1_cell(r):
    if not r: return "not run"
    st = r.get("status"); fitted = r.get("fitted"); N = r.get("states")
    if r.get("feasible") and r.get("min_unfit") == 0: return f"feasible ({r['seconds']}s)"
    if st == "OPTIMAL": return f"**{r['min_unfit']} unfit** of {N} ({r['seconds']}s)"
    if st == "FEASIBLE":
        lo, hi = r["min_unfit_between"]; return f"{lo} to {hi} unfit of {N} (time limit; incumbent {fitted})"
    if st == "INFEASIBLE": return f"infeasible, no incumbent ({r['seconds']}s)"
    return f"{st} ({r.get('seconds')}s)"
def p1_margin(r):
    if not r: return ""
    if r.get("status") == "OPTIMAL": return f"{r['margin']}"
    if r.get("status") == "FEASIBLE": return f"at least {r['margin']} (bound {r['margin_bound']})"
    return r.get("status", "")
def p1_table(res, arms, vocab):
    rows = []
    for a in arms:
        c = []
        for setname in ("s231", "s474", "s1424"):
            for bits in (8, 4):
                if bits == 4 and setname == "s1424": continue
                if bits == 4 and not a.startswith("R"): c.append("(8-bit only)"); continue
                r = res.get(f"{a}|{vocab}|{setname}|{bits}")
                cell = p1_cell(r)
                if bits == 8 and r and r.get("feasible"):
                    m = res.get(f"{a}|{vocab}|{setname}|8|margin"); cell += f", margin {p1_margin(m)}, max\\|w\\| {m.get('max_abs_w') if m else ''}"
                if bits == 8 and setname == "s231":
                    cb = res.get(f"{a}|{vocab}|{setname}|8|cbc"); cell += f"; CBC {cb['status']}" if cb else ""
                c.append(cell)
        rows.append(f"| `{a}` | " + " | ".join(c) + " |")
    return "| arm | the 231, 8 bits | the 231, 4 bits | the 474, 8 bits | the 474, 4 bits | the 1,424, 8 bits |\n|---|---|---|---|---|---|\n" + "\n".join(rows)
def p1_unfit(res, key):
    r = res.get(key)
    if not r or not r.get("unfit_named"): return "none"
    out = []
    for u in r["unfit_named"]:
        w = u["where"]; where = (f"{w['episode']} frame {w['frame']}" if w["source"] == "curriculum" else f"{w['scenario']} ({w['arm']} arm) offset {w['off']}") + f", clone {tuple(w['clone'])}, Tony {tuple(w['tony'])}"
        out.append(f"| {u['senses']} | {where} | {u['teacher']} | {u['taught']} | {u['h']:+d} |")
    return "| sense vector (non-zero senses) | where met | teacher (absolute) | label in this vocabulary | h |\n|---|---|---|---|---|\n" + "\n".join(out)
if __name__ == "__main__" and sys.argv[1] == "p1":
    res = p1_load(); arms = ["raw20", "T36", "A2", "R0", "R1", "R1b", "R2"]
    for vocab in ("abs", "rel"): print(f"\n### {vocab}\n"); print(p1_table(res, arms, vocab))
    for key in sorted(k for k in res if res[k].get("unfit_named")):
        print(f"\n#### {key}: {len(res[key]['unfit'])} unfit\n"); print(p1_unfit(res, key))
    for k in sorted(k for k in res if k.startswith("P1:")): print(k, p1_cell(res[k]))
