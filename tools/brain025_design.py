#!/usr/bin/env python3
"""
brain025_design.py - step D of PREREG-BRAIN025.md: the smallest terrain extension, chosen by the census.

The room's solidity is taken from the machine (the screen page as the build verb writes it, through the
room's own materials table), with a scenario's bricks laid on top. Eight terrain quantities are defined
over that solidity and Tony's own pose, in the frame the action vocabulary already uses; every one of
them is a fact about where things are, computable by anyone holding the room and the pose, and none of
them says what to do.

  values     the eight quantities on every census scenario
  score      every candidate input scored by the consequential alias classes it separates
  table      the chosen retina table (id 5), printed as the generator will embed it
"""
import json, os, sys, itertools
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
ref = _load("brain02_ref", os.path.join(ROOT, "tools/brain02_ref.py"))
CENSUS = os.path.join(ROOT, "deliverables/brain025/census.json")
ROOM = os.path.join(ROOT, "deliverables/brain025/room-solid.json")

WALL = 1
CAP = 7

def room_solid():
    """the empty room's solid map, 25 rows of 40 columns, read once from the machine and cached"""
    if os.path.exists(ROOM): return json.load(open(ROOM))["solid"]
    import subprocess, re, tempfile
    prg = os.path.join(ROOT, "deliverables/prg/minimal64/tony-b02-a.prg")
    d = tempfile.mkdtemp()
    scr, mat = os.path.join(d, "s.bin"), os.path.join(d, "m.bin")
    subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), prg, f"wait:300,sync,dump:C000:3E8:{scr},dump:BE00:100:{mat}"], capture_output=True, text=True)
    s = open(scr, "rb").read(); m = open(mat, "rb").read()
    solid = [[1 if (m[s[r * 40 + c]] & WALL) else 0 for c in range(40)] for r in range(25)]
    json.dump(dict(note="the empty Chamber room: 1 where the material carries the wall bit", solid=solid), open(ROOM, "w"))
    return solid

def solid_map(bricks):
    g = [row[:] for row in room_solid()]
    for (c, r) in bricks:
        for dr in (0, 1):
            for dc in (0, 1):
                if 0 <= r + dr < 25 and 0 <= c + dc < 40: g[r + dr][c + dc] = 1
    return g

def solid(g, c, r): return 1 if (0 <= c < 40 and 0 <= r < 25 and g[r][c]) else (1 if (c < 0 or c >= 40 or r >= 25) else 0)

# ------------------------------------------------------------------ the eight terrain quantities
TERRAIN = ["tSafeRun", "tGapW", "tDropH", "tFarH", "tFarRun", "tObstD", "tObstH", "tObstTop", "tHead", "tBackH", "tBackRoom"]

def terrain(g, col, row, u):
    """col is his left box column, row his top row, u the toward direction (+1 right, -1 left).
    Nine quantities, each a fact about where things are, in the frame the vocabulary already uses."""
    cl, cr = col, col + 1
    ce = cr if u > 0 else cl                      # the box edge on the toward side
    ca = cl if u > 0 else cr                      # the box edge on the away side
    rf = row + 3                                  # his foot row
    rs = row + 4                                  # the row his feet rest on
    def at(i): return ce + i * u
    def supported(c): return solid(g, c, rs)
    def blocked(c): return solid(g, c, rf)
    def stack(c):
        n = 0
        while n < CAP and solid(g, c, rf - n): n += 1
        return n
    def clear_above(c, frm):
        n = 0
        while n < CAP and not solid(g, c, frm - n): n += 1
        return n
    def surface(c):
        """the row of the topmost standing surface of column c within CAP rows of his own floor row,
        or None: the first row r, scanning from high on the screen downward, that is solid with air above"""
        for r in range(rs - CAP, rs + CAP + 1):
            if solid(g, c, r) and not solid(g, c, r - 1): return r
        return None
    # 1. how far his own floor reaches toward the reference
    run = 0
    while run < CAP and supported(at(run + 1)): run += 1
    # 2. the width of the gap past it, 3. what lies under that gap, 4. the height of the far side
    gapw = dropH = farH = farRun = 0
    if run < CAP:
        w = 0
        while run + 1 + w <= CAP and not supported(at(run + 1 + w)): w += 1
        gapw = min(CAP, w)
        s0 = surface(at(run + 1))
        if s0 is not None: dropH = max(-CAP, min(CAP, rs - s0))
        if run + 1 + w <= CAP and supported(at(run + 1 + w)):
            s1 = surface(at(run + 1 + w))
            if s1 is not None: farH = max(-CAP, min(CAP, rs - s1))
            while farRun < CAP and supported(at(run + 1 + w + farRun)): farRun += 1
    # 5. the first thing in his way, 6. its height, 7. the room to stand above it
    obstd = obsth = obsttop = 0
    for i in range(1, CAP + 1):
        if blocked(at(i)):
            obstd = i; obsth = stack(at(i)); obsttop = clear_above(at(i), rf - obsth); break
    # 8. the room above his own head, 9. what is at his back
    head = min(clear_above(cl, row - 1), clear_above(cr, row - 1))
    backh = stack(ca - u)
    backroom = 0
    while backroom < CAP and not blocked(ca - (backroom + 1) * u): backroom += 1
    return dict(tSafeRun=run, tGapW=gapw, tDropH=dropH, tFarH=farH, tFarRun=farRun, tObstD=obstd, tObstH=obsth,
                tObstTop=obsttop, tHead=head, tBackH=backh, tBackRoom=backroom)

def rows_with_terrain():
    d = json.load(open(CENSUS))
    out = []
    for r in d["rows"]:
        g = solid_map([tuple(b) for b in r["bricks"]])
        t = terrain(g, r["start"]["col"], r["start"]["row"], r["toward"])
        q = dict(r); q["terrain"] = t; out.append(q)
    return d, out

# --------------------------------------------------------------------------------- scoring the candidates
GE, LE = ref.GE, ref.LE
def bit_value(t, cand):
    v, op, k = cand
    return 1 if (t[v] >= k if op == GE else t[v] <= k) else 0
def cand_name(cand):
    v, op, k = cand
    return f"{v}{'>=' if op == GE else '<='}{k}"

def candidates(rows):
    """every threshold that actually cuts the observed range of a quantity in two"""
    out = []
    for v in TERRAIN:
        vals = sorted({r["terrain"][v] for r in rows})
        for k in range(min(vals) + 1, max(vals) + 1):
            if k > 0: out.append((v, GE, k))
        for k in range(min(vals), 0):
            out.append((v, LE, k))
    return [c for c in out if 0 < sum(bit_value(r["terrain"], c) for r in rows) < len(rows)]

GOOD, BAD = {"ADVANCE", "CLIMB"}, {"DROP", "BLOCKED", "AIRBORNE", "RETREAT"}
def splits(rows, bits):
    """the consequential splits that survive when the rows are grouped by the extended observation"""
    grp = {}
    for r in rows:
        key = r["z"] + "".join(str(bit_value(r["terrain"], b)) for b in bits)
        grp.setdefault(key, []).append(r)
    left = []
    for key, g in grp.items():
        for a in range(10):
            seen = {}
            for r in g: seen.setdefault(r["outcomes"][a], set()).add(r["geometry"])
            if any(o in GOOD for o in seen) and any(o in BAD for o in seen):
                left.append((key, a, {k: sorted(v) for k, v in seen.items()}))
    return left

def conflicts(rows, bits):
    """the finer objective: pairs of scenarios that share an observation but whose outcome for some action
    is good for one and bad for the other. Whole splits vanish only when every such pair is separated, so
    counting pairs gives the search a gradient where counting splits gives it a cliff."""
    grp = {}
    for r in rows:
        key = r["z"] + "".join(str(bit_value(r["terrain"], b)) for b in bits)
        grp.setdefault(key, []).append(r)
    n = 0
    for g in grp.values():
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                if g[i]["geometry"] == g[j]["geometry"]: continue
                for a in range(10):
                    oi, oj = g[i]["outcomes"][a], g[j]["outcomes"][a]
                    if (oi in GOOD and oj in BAD) or (oj in GOOD and oi in BAD): n += 1; break
    return n

def greedy(rows, cands, budget=24):
    chosen = []; base = len(splits(rows, chosen)); trace = [dict(bit=None, name="(none)", splits_left=base)]
    basec = conflicts(rows, chosen); trace[0]["conflicts_left"] = basec
    while len(chosen) < budget:
        best, bestc = None, basec
        for c in cands:
            if c in chosen: continue
            n = conflicts(rows, chosen + [c])
            if n < bestc: best, bestc = c, n
        if best is None: break
        chosen.append(best); basec = bestc
        trace.append(dict(bit=best, name=cand_name(best), splits_left=len(splits(rows, chosen)), conflicts_left=bestc))
        if bestc == 0: break
    return chosen, trace

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] in ("values", "score"):
    d, rows = rows_with_terrain()
    if sys.argv[1] == "values":
        seen = {}
        for r in rows: seen.setdefault(r["geometry"], r["terrain"])
        print(f"{'geometry':16s} " + " ".join(f"{k[1:]:>8s}" for k in TERRAIN))
        for g in sorted(seen): print(f"{g:16s} " + " ".join(f"{seen[g][k]:8d}" for k in TERRAIN))
        sys.exit(0)
    cands = candidates(rows)
    print(f"{len(cands)} candidate thresholds over {len(TERRAIN)} quantities; {len(splits(rows, []))} consequential splits, {conflicts(rows, [])} conflicting pairs with none of them")
    chosen, trace = greedy(rows, cands)
    for t in trace: print(f"   + {t['name']:18s} -> {t['splits_left']} splits, {t['conflicts_left']} conflicting pairs left")
    left = splits(rows, chosen)
    print(f"\nchosen {len(chosen)} inputs; {len(left)} consequential splits remain")
    for key, a, s in left[:8]:
        print(f"   '{ref.REL_ACTIONS[a]}' still splits: " + "; ".join(f"{k}: {','.join(v)}" for k, v in s.items()))
    json.dump(dict(quantities=TERRAIN, candidates=[cand_name(c) for c in cands], chosen=[list(c) for c in chosen],
                   chosen_names=[cand_name(c) for c in chosen], trace=[dict(name=t["name"], splits_left=t["splits_left"]) for t in trace],
                   splits_before=len(splits(rows, [])), splits_after=len(left),
                   remaining=[dict(action=ref.REL_ACTIONS[a], split={k: v for k, v in s.items()}) for key, a, s in left],
                   terrain_by_geometry={r["geometry"]: r["terrain"] for r in rows}), open(os.path.join(ROOT, "deliverables/brain025/design.json"), "w"), indent=1)

# ------------------------------------------------------------------- the published design (retina id 5)
# Seven of the eleven quantities earn inputs; each gets an ordinal thermometer whose rungs include every
# threshold the search chose, so the code stays ordinal instead of a scatter of tuned cuts.
DESIGN = [("tSafeRun", GE, 1), ("tSafeRun", GE, 3),
          ("tGapW", GE, 3), ("tGapW", GE, 4), ("tGapW", GE, 6),
          ("tFarRun", GE, 1), ("tFarRun", GE, 3),
          ("tObstH", GE, 1), ("tObstH", GE, 3), ("tObstH", GE, 5),
          ("tObstTop", GE, 1), ("tObstTop", GE, 3),
          ("tHead", GE, 1), ("tHead", GE, 4),
          ("tBackRoom", GE, 2), ("tBackRoom", GE, 4)]
PUBLISHED = ["tSafeRun", "tGapW", "tFarRun", "tObstH", "tObstTop", "tHead", "tBackRoom"]   # the sense block's extra nibbles, in this order
OMITTED = ["tDropH", "tFarH", "tObstD", "tBackH"]                                          # computed while designing, not published

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "final":
    d, rows = rows_with_terrain()
    cands = candidates(rows); chosen, trace = greedy(rows, cands)
    keys = {}
    for r in rows:
        k = r["z"] + "".join(str(bit_value(r["terrain"], b)) for b in DESIGN); keys.setdefault(k, set()).add(r["geometry"])
    act = [sum(bit_value(r["terrain"], b) for b in DESIGN) for r in rows]
    load = {cand_name(b): conflicts(rows, [x for j, x in enumerate(DESIGN) if j != i]) for i, b in enumerate(DESIGN)}
    out = dict(quantities=TERRAIN, published=PUBLISHED, omitted=OMITTED,
               design=[[v, "GE" if op == GE else "LE", k] for v, op, k in DESIGN], design_names=[cand_name(c) for c in DESIGN],
               greedy=[cand_name(c) for c in chosen], greedy_trace=[dict(name=t["name"], splits_left=t["splits_left"], conflicts_left=t["conflicts_left"]) for t in trace],
               candidates=[cand_name(c) for c in cands],
               before=dict(observations=d["observations"], consequential_classes=d["consequential_classes"], splits=len(splits(rows, [])), conflicts=conflicts(rows, [])),
               after=dict(observations=len(keys), splits=len(splits(rows, DESIGN)), conflicts=conflicts(rows, DESIGN),
                          still_shared=[sorted(v) for v in keys.values() if len(v) > 1]),
               active=dict(terrain_min=min(act), terrain_mean=sum(act) / len(act), terrain_max=max(act)),
               load_bearing=load, terrain_by_geometry={r["geometry"]: r["terrain"] for r in rows})
    json.dump(out, open(os.path.join(ROOT, "deliverables/brain025/design.json"), "w"), indent=1)
    print(f"design: {len(DESIGN)} appended inputs over {len(PUBLISHED)} published quantities")
    print(f"  before: {out['before']['observations']} observations, {out['before']['splits']} consequential splits, {out['before']['conflicts']} conflicting pairs")
    print(f"  after:  {out['after']['observations']} observations, {out['after']['splits']} consequential splits, {out['after']['conflicts']} conflicting pairs")
    print(f"  terrain inputs set at once: {out['active']['terrain_min']}..{out['active']['terrain_max']}, mean {out['active']['terrain_mean']:.1f}")
