#!/usr/bin/env python3
"""
brain025_census.py - step C of PREREG-BRAIN025.md: the BRAIN02 terrain-observation alias census.

Two things are measured on the machine, never modelled:

  * what BRAIN02 sees   - the published twenty-nibble sense block of the frozen Candidate A build, put
                          through that build's own R1b retina (proved byte for byte equal to the
                          reference on all 1,424 recorded blocks by the parity gate), giving the exact
                          64-bit observation vector;
  * what the world does - for each of the ten reference-relative outputs, a bounded rollout in which the
                          brain is made to choose that output, then to idle, and the outcome is
                          classified from Tony's own position and state.

A scenario is a terrain built the way a person builds it: 2x2 bricks written as the four screen codes
the build verb writes, which the room's own materials table already makes wall.

  geometry     the column/row calibration and the rollout calibration
  census       the full sweep -> deliverables/brain025/census.json
"""
import json, os, re, subprocess, sys, hashlib
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
ref = _load("brain02_ref", os.path.join(ROOT, "tools/brain02_ref.py"))

PRG = os.path.join(ROOT, "deliverables/prg/minimal64/tony-b02-a.prg")
SYM = os.path.join(ROOT, "src/kickass/tony-b02-a.sym")
S = {}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(SYM).read()): S.setdefault(m.group(1), int(m.group(2), 16))

# ------------------------------------------------------------------ the room's geometry, calibrated on the machine
# a character column c is the cells at X in [8(c+2), 8(c+2)+7]:  leftCol = X/8 - 2, rightCol = (X+8)/8 - 2
# a character row r is the cells at Y in [8(r+6), 8(r+6)+7]:     top     = Y/8 - 6, feet = top + 3
def x_of_col(c): return 8 * (c + 2)
def y_on_row(r): return 8 * (r + 2) + 6      # the resting Y of a Tony standing on the surface at row r (BUDDY_FLOOR_Y for the floor)
FLOOR_ROW = 23                               # the room's floor; interior columns 5..34, rows 2..22
LADDER_COLS = (33, 34)
BRICK = (0x50, 0x51, 0x52, 0x53)             # top left, top right, bottom left, bottom right

def pk(a, n=1): return "".join(f"peek:{a + i:X}," for i in range(n))
def po(a, d): return "".join(f"poke:{a + i:X}:{b & 255:02X}," for i, b in enumerate(d))
def brick(col, row):
    """a 2x2 brick with its top left at (col, row), exactly the four cells buildLayCells writes"""
    base = 0xC000 + 40 * row + col
    return po(base, BRICK[:2]) + po(base + 40, BRICK[2:])
def clear(col, row):
    base = 0xC000 + 40 * row + col
    return po(base, [0x20, 0x20]) + po(base + 40, [0x20, 0x20])
def sg(x): return x - 16 if x >= 8 else x

import tempfile
def run(script):
    with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
    r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), PRG, "@" + f.name], capture_output=True, text=True)
    os.unlink(f.name)
    return [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)], r.stdout

# ------------------------------------------------------------------------------- forcing one output
def weights_for(action):
    """ten rows of 64 bytes: every weight zero but the bias of one row, so the forward pass always picks
    that output, the decoder resolves and drives it exactly as in play"""
    w = bytearray(640)
    if action is not None: w[action * 64] = 1
    return bytes(w)
ZERO_W = bytes(640)

def place(cx, cy, state, px, py, pstate=0x80):
    return (po(S["cloneX"], [cx & 255, cx >> 8]) + po(S["cloneNextX"], [cx & 255, cx >> 8]) +
            f"poke:{S['cloneY']:X}:{cy:02X},poke:{S['cloneNextY']:X}:{cy:02X},poke:{S['cloneState']:X}:{state:02X},poke:{S['cloneStateAllowed']:X}:{state:02X}," +
            po(S["physPlayerX"], [px & 255, px >> 8]) + f"poke:{S['physPlayerY']:X}:{py:02X},poke:{S['physPlayerState']:X}:{pstate:02X},")

SETTLE = 8          # frames after placing, so the senses are packed and published for the placed pose
HOLD  = 8           # the forced output held: two think periods at the default period of 4 frames
COAST = 52          # the neutral continuation: idle, long enough for a jump arc and its landing

def scenario_script(sc, action, read_senses):
    """one scenario at one action: build the terrain, place both Tonys, settle, read, roll out, read"""
    s = f"poke:{S['brainKind']:X}:01," + po(S["brainWeights"], ZERO_W) + po(S["brainMood"], bytes(10))
    for (c, r) in sc["bricks"]: s += brick(c, r)
    s += place(*sc["pose"], *sc["player"], sc.get("pstate", 0x80))
    s += f"wait:{SETTLE},sync,"
    if read_senses: s += pk(S["cloneSenses"], 20) + pk(S["cloneX"], 2) + pk(S["cloneY"]) + pk(S["cloneState"])
    if action is None: return s
    s += po(S["brainWeights"], weights_for(action)) + f"wait:{HOLD},"
    s += po(S["brainWeights"], ZERO_W) + f"wait:{COAST},sync," + pk(S["cloneX"], 2) + pk(S["cloneY"]) + pk(S["cloneState"]) + pk(S["cloneSenses"] + 8) + pk(S["cloneSenses"] + 6)
    return s

def classify(sc, cx0, cy0, cx1, cy1, floor, ladder):
    """the outcome rules fixed in the pre-registration, in character columns and rows"""
    col0, col1 = (cx0 >> 3) - 2, (cx1 >> 3) - 2
    row0, row1 = (cy0 >> 3) - 6, (cy1 >> 3) - 6      # the top row; smaller is higher on the screen
    d = (col1 - col0) * sc["toward"]                  # toward the reference is positive
    supported = bool(floor) or bool(ladder)
    if row1 > row0: return "DROP"
    if row1 < row0 and supported: return "CLIMB"
    if d >= 1 and supported: return "ADVANCE"
    if d <= -1 and supported: return "RETREAT"
    return "BLOCKED" if supported else "AIRBORNE"

# ------------------------------------------------------------------------------ the scenario family
def plat(cols, level):
    """bricks at the given slot columns on a level: level 0 is rows 21-22, sitting on the floor"""
    return [(c, 21 - 2 * level) for c in cols]

def families():
    """the local geometries of PREREG-BRAIN025.md section 8, each at a pose the geometry is about.
    'toward' is +1 when the reference (the player) is to the right of the clone."""
    F = []
    def add(name, family, bricks, col, row, facing, pcol, prow, note):
        # row is the character row whose top the clone's feet rest on (he stands supported by that row)
        F.append(dict(name=name, family=family, bricks=bricks, col=col, row=row, facing=facing,
                      pose=(x_of_col(col), y_on_row(row), 0x80 if facing > 0 else 0x00),
                      player=(x_of_col(pcol), y_on_row(prow)), toward=1 if pcol > col else -1, note=note))
    # 1. flat ground, nothing ahead
    add("flat", "flat", [], 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "open floor, nothing within sight")
    add("flat_near_wall", "flat", [], 5, FLOOR_ROW, -1, 20, FLOOR_ROW, "against the left pillar, facing away")
    # 2. obstacles of several heights, directly ahead
    for h, nm in ((1, "obst1"), (2, "obst2"), (3, "obst3"), (5, "obst5")):
        add(nm, "obstacle", plat([9], 0) + [(9, 21 - 2 * k) for k in range(1, h)], 7, FLOOR_ROW, +1, 20, FLOOR_ROW, f"{h} bricks high, ahead")
    # 3. an obstacle with a standing surface on top, and the same obstacle under a ceiling
    add("obst1_open", "obstacle_top", plat([9], 0), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "one high, its top free to stand on")
    add("obst1_covered", "obstacle_top", plat([9], 0) + plat([9], 2), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "one high with a ceiling two above: no standing on it")
    add("obst2_open", "obstacle_top", plat([9], 0) + plat([9], 1), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "two high, its top free")
    add("obst2_covered", "obstacle_top", plat([9], 0) + plat([9], 1) + plat([9], 3), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "two high under a ceiling")
    # 4. a ledge: standing on a platform with its edge ahead and the floor far below
    add("ledge", "ledge", plat([5, 7], 0), 7, 21, +1, 20, FLOOR_ROW, "on a platform, its edge one column ahead")
    add("ledge_high", "ledge", plat([5, 7], 0) + plat([5, 7], 1), 7, 19, +1, 20, FLOOR_ROW, "on a platform two levels up, its edge ahead")
    # 5. gaps of one, two and three slot columns between platforms
    add("gap1", "gap", plat([5, 7], 0) + plat([11], 0), 7, 21, +1, 20, FLOOR_ROW, "one slot of gap, the far side level")
    add("gap2", "gap", plat([5, 7], 0) + plat([13], 0), 7, 21, +1, 20, FLOOR_ROW, "two slots of gap")
    add("gap3", "gap", plat([5, 7], 0) + plat([15], 0), 7, 21, +1, 20, FLOOR_ROW, "three slots of gap")
    # 6. a gap whose far side is level, higher, lower
    add("gap_level", "gap_land", plat([5, 7], 0) + plat([11], 0), 7, 21, +1, 20, FLOOR_ROW, "far side level with him")
    add("gap_up", "gap_land", plat([5, 7], 0) + plat([11], 0) + plat([11], 1), 7, 21, +1, 20, FLOOR_ROW, "far side one level higher")
    add("gap_down", "gap_land", plat([5, 7], 0) + plat([5, 7], 1) + plat([11], 0), 7, 19, +1, 20, FLOOR_ROW, "far side one level lower")
    add("gap_none", "gap_land", plat([5, 7], 0), 7, 21, +1, 20, FLOOR_ROW, "no far side at all: the floor below")
    # 7. pockets and traps
    add("pocket", "pocket", plat([5], 0) + plat([9], 0), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "one slot wide between two one-high walls")
    add("pocket_deep", "pocket", plat([5], 0) + plat([5], 1) + plat([9], 0) + plat([9], 1), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "two high on both sides")
    add("pocket_covered", "pocket", plat([5], 0) + plat([9], 0) + plat([5, 7, 9], 2), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "walled and roofed")
    add("corridor", "pocket", plat([5, 7, 9], 2), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "roofed, both sides open")
    # 8. a step up then immediately a gap: the jump has to change direction in the air
    add("step_then_gap", "combo", plat([9], 0) + plat([13], 0), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "a one-high step, then a gap beyond it")
    add("step_then_wall", "combo", plat([9], 0) + plat([11], 0) + plat([11], 1), 7, FLOOR_ROW, +1, 20, FLOOR_ROW, "a step, then a two-high wall beyond")
    # 8b. the same obstacles further away: two and three slots ahead, where nothing reaches
    add("obst1_far2", "distance", plat([11], 0), 7, FLOOR_ROW, +1, 26, FLOOR_ROW, "a one-high step two slots ahead")
    add("obst1_far3", "distance", plat([13], 0), 7, FLOOR_ROW, +1, 26, FLOOR_ROW, "a one-high step three slots ahead")
    add("obst2_far2", "distance", plat([11], 0) + plat([11], 1), 7, FLOOR_ROW, +1, 26, FLOOR_ROW, "a two-high wall two slots ahead")
    add("hole_far2", "distance", plat([5, 7], 0) + plat([11, 13], 0), 7, 21, +1, 26, FLOOR_ROW, "a platform, a one-slot hole two slots ahead")
    add("hole_far3", "distance", plat([5, 7, 9], 0) + plat([13], 0), 7, 21, +1, 26, FLOOR_ROW, "a platform, the hole three slots ahead")
    # 9. standing on top of an obstacle, looking down
    add("on_top_edge", "on_top", plat([7], 0), 7, 21, +1, 20, FLOOR_ROW, "on a single brick, the drop ahead")
    add("on_top_flat", "on_top", plat([7, 9, 11], 0), 7, 21, +1, 20, FLOOR_ROW, "on a run of bricks, more ahead")
    return F

# the player's placements. The ladder hangs at columns 33-34 from the ceiling to row 9, so a Tony put
# on it needs a ladder state and a Y inside those rows or he simply falls; "ladder_low" and "ladder_high"
# are real ladder poses, and are not mirrored (there is no ladder on the left of the room).
LADDER_STATE = 2          # STATE_ON_LADDER_FACING_LEFT
PLAYERS = [("floor_far", 26, FLOOR_ROW, 0x80, False), ("floor_near", 13, FLOOR_ROW, 0x80, False),
           ("ladder_low", 33, 9, LADDER_STATE, True), ("ladder_high", 33, 4, LADDER_STATE, True)]

def mirror_col(c): return 39 - c                   # the room is symmetric about its middle; slots stay on the 5+2i grid
def scenarios():
    """every geometry at every player placement, and the whole set mirrored left-for-right"""
    out = []
    for g in families():
        for pname, pcol, prow, pstate, on_ladder in PLAYERS:
            for mir in (0, 1):
                if mir and on_ladder: continue            # the ladder is only on the right of the room
                if mir:
                    bricks = [(mirror_col(c) - 1, r) for (c, r) in g["bricks"]]
                    col = mirror_col(g["col"]) - 1; facing = -g["facing"]; pc = mirror_col(pcol) - 1
                else:
                    bricks = list(g["bricks"]); col = g["col"]; facing = g["facing"]; pc = pcol
                sc = dict(g); sc["bricks"] = bricks; sc["col"] = col; sc["facing"] = facing
                sc["pose"] = (x_of_col(col), y_on_row(g["row"]), 0x80 if facing > 0 else 0x00)
                py = y_on_row(prow) if not on_ladder else 8 * (prow + 6)     # on a ladder he hangs in the rows, not on a surface
                sc["player"] = (x_of_col(pc), py); sc["pstate"] = pstate; sc["toward"] = 1 if pc > col else -1
                sc["name"] = f"{g['name']}|{pname}{'|m' if mir else ''}"; sc["player_at"] = pname; sc["mirrored"] = bool(mir)
                out.append(sc)
    return out

# ------------------------------------------------------------------------------------- the calibration
def geometry():
    """the column and row mapping, and that the rollout can tell the outcomes apart at all"""
    print("column mapping: a brick at column c registers as the wall ahead when c is the column past his box")
    s = f"wait:300,poke:{S['brainKind']:X}:01," + po(S["brainWeights"], ZERO_W)
    s += "snapshot," + "restore,".join(brick(c, 21) + place(x_of_col(7), y_on_row(FLOOR_ROW), 0x80, x_of_col(26), y_on_row(FLOOR_ROW)) + f"wait:{SETTLE},sync," + pk(S["cloneSenses"], 20) + pk(S["cloneX"], 2) for c in range(6, 14))
    v, _ = run(s)
    for i, c in enumerate(range(6, 14)):
        g = v[i * 22:(i + 1) * 22]; x = g[20] | g[21] << 8
        print(f"   brick at column {c:2d}: X {x}, box columns {(x >> 3) - 2}-{((x + 8) >> 3) - 2}, wallAheadFoot {sg(g[9])}, wallAheadHead {sg(g[10])}, buildable {sg(g[14])}")
    print(f"\nrollout: the forced output held {HOLD} frames, then idle for {COAST}")
    for nm, bricks, col, row in (("flat floor", [], 7, FLOOR_ROW), ("a one-high step ahead", plat([9], 0), 7, FLOOR_ROW), ("a two-high wall ahead", plat([9], 0) + plat([9], 1), 7, FLOOR_ROW)):
        s = f"wait:300,poke:{S['brainKind']:X}:01," + po(S["brainMood"], bytes(10))
        for (c, r) in bricks: s += brick(c, r)
        s += place(x_of_col(col), y_on_row(row), 0x80, x_of_col(26), y_on_row(FLOOR_ROW))
        s += po(S["brainWeights"], ZERO_W) + f"wait:{SETTLE},sync," + pk(S["cloneX"], 2) + pk(S["cloneY"]) + "snapshot,"
        s += "restore,".join(po(S["brainWeights"], weights_for(a)) + f"wait:{HOLD}," + po(S["brainWeights"], ZERO_W) + f"wait:{COAST},sync," + pk(S["cloneX"], 2) + pk(S["cloneY"]) + pk(S["cloneSenses"] + 8) for a in range(10))
        v, _ = run(s)
        x0 = v[0] | v[1] << 8; y0 = v[2]
        print(f"   {nm}: from column {(x0 >> 3) - 2}, row {(y0 >> 3) - 6}")
        for a in range(10):
            g = v[3 + a * 4:7 + a * 4]
            if len(g) < 4: print(f"      {ref.REL_ACTIONS[a]:12s} (no reading)"); continue
            x1 = g[0] | g[1] << 8; y1 = g[2]
            print(f"      {ref.REL_ACTIONS[a]:12s} X {x0}->{x1} (col {(x0 >> 3) - 2}->{(x1 >> 3) - 2})  Y {y0}->{y1} (row {(y0 >> 3) - 6}->{(y1 >> 3) - 6})  floorBelow {sg(g[3])}")

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "geometry": geometry()

# ------------------------------------------------------------------------------------- the census
def census():
    """every scenario: the machine's published senses, the 64-bit R1b observation, and the ten rollouts"""
    SC = scenarios(); out = []
    for i, sc in enumerate(SC):
        s = "wait:300," + scenario_script(sc, None, True) + "snapshot,"
        s += "restore,".join(po(S["brainWeights"], weights_for(a)) + f"wait:{HOLD}," + po(S["brainWeights"], ZERO_W) +
                             f"wait:{COAST},sync," + pk(S["cloneX"], 2) + pk(S["cloneY"]) + pk(S["cloneSenses"] + 8) + pk(S["cloneSenses"] + 6) + pk(S["cloneSenses"] + 5) for a in range(10))
        v, raw = run(s)
        if len(v) < 24 + 60: print(f"   {sc['name']}: short read ({len(v)}), skipped"); continue
        x = [sg(t) for t in v[:20]]; cx0 = v[20] | v[21] << 8; cy0 = v[22]; st0 = v[23]
        z = ref.flags(ref.table_R1b(), x)
        acts = []
        for a in range(10):
            g = v[24 + a * 6:30 + a * 6]
            cx1 = g[0] | g[1] << 8; cy1 = g[2]
            acts.append(dict(action=a, name=ref.REL_ACTIONS[a], dcol=((cx1 >> 3) - 2) - ((cx0 >> 3) - 2), drow=((cy1 >> 3) - 6) - ((cy0 >> 3) - 6),
                             outcome=classify(sc, cx0, cy0, cx1, cy1, sg(g[3]), sg(g[4])), inair=sg(g[5])))
        out.append(dict(name=sc["name"], family=sc["family"], geometry=sc["name"].split("|")[0], player_at=sc["player_at"], mirrored=sc["mirrored"],
                        note=sc["note"], bricks=sc["bricks"], col=sc["col"], facing=sc["facing"], toward=sc["toward"],
                        senses=x, z="".join(map(str, z)), start=dict(x=cx0, y=cy0, state=st0, col=(cx0 >> 3) - 2, row=(cy0 >> 3) - 6),
                        outcomes=[a["outcome"] for a in acts], actions=acts))
        if (i + 1) % 20 == 0: print(f"   {i + 1}/{len(SC)} scenarios")
    return out

def analyse(rows):
    """group by the 64-bit observation, then ask whether the grouped scenarios behave differently"""
    byz = {}
    for r in rows: byz.setdefault(r["z"], []).append(r)
    classes = []
    for z, g in byz.items():
        geos = sorted({r["geometry"] for r in g})
        outs = {r["name"]: r["outcomes"] for r in g}
        distinct = sorted({tuple(v) for v in outs.values()})
        conseq = []
        if len(distinct) > 1:
            for a in range(10):
                seen = {}
                for r in g: seen.setdefault(r["outcomes"][a], []).append(r["geometry"])
                good = {"ADVANCE", "CLIMB"}; bad = {"DROP", "BLOCKED", "AIRBORNE", "RETREAT"}
                if any(o in good for o in seen) and any(o in bad for o in seen):
                    conseq.append(dict(action=a, name=ref.REL_ACTIONS[a], split={k: sorted(set(v)) for k, v in seen.items()}))
        classes.append(dict(z=z, members=[r["name"] for r in g], geometries=geos, distinct_outcome_rows=len(distinct),
                            consequential=bool(conseq), consequential_actions=conseq, active=sum(int(c) for c in z)))
    return classes

def bit_names():
    return ref.flag_names(ref.table_R1b())

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "census":
    rows = census(); classes = analyse(rows)
    multi = [c for c in classes if len(set(c["geometries"])) > 1]
    cons = [c for c in classes if c["consequential"]]
    outp = os.path.join(ROOT, "deliverables/brain025/census.json")
    json.dump(dict(prg=os.path.basename(PRG), prg_sha=hashlib.sha256(open(PRG, "rb").read()).hexdigest(),
                   hold=HOLD, coast=COAST, settle=SETTLE, scenarios=len(rows), observations=len(classes),
                   aliased_classes=len(multi), consequential_classes=len(cons), rows=rows, classes=classes), open(outp, "w"), indent=1)
    print(f"\n{len(rows)} scenarios -> {len(classes)} distinct 64-bit observations")
    print(f"{len(multi)} observations cover more than one geometry; {len(cons)} of those are consequential")
    print(f"written {outp}")
