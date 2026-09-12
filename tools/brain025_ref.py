#!/usr/bin/env python3
"""
brain025_ref.py - the reference for BRAIN02.5 (deliverables/brain025/PREREG-BRAIN025.md and DESIGN.md).

BRAIN02.5 is BRAIN02 with more eyes and nothing else. The learner is untouched: the ten reference-relative
outputs, the byte weights, the symmetric rule at the byte box, the first-largest tie, the accumulator
semantics, and inputs 0 to 63 with exactly the meanings and the order R1b gave them. What is new is seven
local terrain quantities in the published sense block and sixteen inputs appended at 64 to 79.

Every implementation (this one, the 6502, and any later one) must produce exactly these bytes on these
inputs.

  check     the table against BRAIN02's on the old inputs, the terrain quantities against the design
            tool, the rule against BRAIN02's, and the slot and lesson round trips
  golden    writes deliverables/brain025/golden/{forward,lessons,terrain,retina-5}.json
  table     prints the retina table as the generator embeds it
"""
import hashlib, json, os, random, sys
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables/brain025")
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
b02 = _load("brain02_ref", os.path.join(ROOT, "tools/brain02_ref.py"))

# ------------------------------------------------------------------ what BRAIN02.5 keeps, unchanged
GE, LE, EQN, AND, ANDNOT, OR, XNOR = b02.GE, b02.LE, b02.EQN, b02.AND, b02.ANDNOT, b02.OR, b02.XNOR
OPS, LO, HI = b02.OPS, b02.LO, b02.HI
SENSES = b02.SENSES                      # the twenty of BRAIN02, indices 0..19, unchanged
PSEUDO = b02.PSEUDO                      # the nine of BRAIN02, indices 20..28, unchanged
ABS_ACTIONS, REL_ACTIONS, HDIR = b02.ABS_ACTIONS, b02.REL_ACTIONS, b02.HDIR
reference, h_of, to_relative, to_absolute = b02.reference, b02.h_of, b02.to_relative, b02.to_absolute
pseudo = b02.pseudo
forward, learn, learn_signed, forward_signed = b02.forward, b02.learn, b02.learn_signed, b02.forward_signed

# --------------------------------------------------------------------------- what BRAIN02.5 adds
TERRAIN = ["tSafeRun", "tGapW", "tFarRun", "tObstH", "tObstTop", "tHead", "tBackRoom"]   # senses 20..26
SENSE_COUNT = 20 + len(TERRAIN)          # 27 nibbles in the published block
TERRAIN_BASE = 29                        # terrain quantities live at brainVals 29..35
CAP = 7                                  # every terrain count saturates here, so each fits one nibble

def values(x):
    """the 36 signed values of one block: the twenty senses, the nine pseudo-senses, the seven terrain"""
    assert len(x) == SENSE_COUNT, f"a BRAIN02.5 block is {SENSE_COUNT} nibbles, not {len(x)}"
    return list(x[:20]) + pseudo(list(x[:20])) + list(x[20:])

# the retina table, id 5: R1b's sixty-four entries untouched, then the sixteen of DESIGN.md
def terrain_entries():
    T = {n: TERRAIN_BASE + i for i, n in enumerate(TERRAIN)}
    return [(GE, T["tSafeRun"], 1), (GE, T["tSafeRun"], 3),
            (GE, T["tGapW"], 3), (GE, T["tGapW"], 4), (GE, T["tGapW"], 6),
            (GE, T["tFarRun"], 1), (GE, T["tFarRun"], 3),
            (GE, T["tObstH"], 1), (GE, T["tObstH"], 3), (GE, T["tObstH"], 5),
            (GE, T["tObstTop"], 1), (GE, T["tObstTop"], 3),
            (GE, T["tHead"], 1), (GE, T["tHead"], 4),
            (GE, T["tBackRoom"], 2), (GE, T["tBackRoom"], 4)]
def table_T1(): return b02.table_R1b() + terrain_entries()
TABLES = {5: ("T1", table_T1)}
RETINA_ID = 5
N = len(table_T1())                      # 80

def flag_names(entries):
    names = SENSES + PSEUDO + TERRAIN
    out = []
    for op, a, k in entries:
        nm = names[a]
        out.append(nm if (op == GE and k == 1 and a in range(3, 20)) else
                   (f"{nm}>={k}" if op == GE else f"{nm}<={k}" if op == LE else f"{nm}=={k}" if op == EQN else f"{OPS[op]}({nm},{names[k]})"))
    return out
def table_bytes(entries): return b02.table_bytes(entries)

def flags(entries, x):
    """the table interpreter over the 36 values of one BRAIN02.5 block"""
    v = values(x); out = []
    for op, a, k in entries:
        if op == GE: f = v[a] >= k
        elif op == LE: f = v[a] <= k
        elif op == EQN: f = (v[a] & 15) == k
        else:
            p, q = v[a] != 0, v[k] != 0
            f = (p and q) if op == AND else (p and not q) if op == ANDNOT else (p or q) if op == OR else (p == q)
        out.append(1 if f else 0)
    return out
def bound(n): return 128 * n + 128

# ------------------------------------------------------------------------------- the slot, layout 3
MARKER = b"BRAIN025"                     # eight bytes, and not BRAIN02's
LAYOUT = 3
def slot_bytes(kind, vocab, weights, education=0, mood=None, period=4, lineage=0, rule=2, retina_id=RETINA_ID):
    n = len(weights[0]); assert len(weights) == 10 and all(len(r) == n for r in weights)
    b = bytearray(MARKER) + bytes([kind, LAYOUT, n, 0, 10, period, lineage, rule, vocab, retina_id, education & 255, education >> 8, 0, 0, 0, 0])
    for o in range(10): b += bytes(v & 255 for v in weights[o])
    b += bytes((mood[o] if mood else 0) & 255 for o in range(10))
    return bytes(b)
def parse_slot(b):
    assert b[:8] == MARKER, "not a BRAIN025 slot"
    n = b[10]; sx = lambda v: v - 256 if v >= 128 else v
    return dict(kind=b[8], layout=b[9], inputs=n, hidden=b[11], outputs=b[12], period=b[13], lineage=b[14], rule=b[15], vocabulary=b[16], retina_id=b[17],
                education=b[18] | (b[19] << 8), weights=[[sx(b[24 + o * n + i]) for i in range(n)] for o in range(10)], mood=[sx(b[24 + 10 * n + o]) for o in range(10)])
def behavioural_bytes(b):
    """the same three domains BRAIN02 defines: behaviour is kind, layout, width, shape, vocabulary,
    retina and the weights; the mood is timing, the education and lineage are provenance"""
    n = b[10]; return bytes(b[8:13]) + bytes(b[16:18]) + bytes(b[24:24 + 10 * n])
def brain_hash(b): return hashlib.sha256(behavioural_bytes(b)).hexdigest()
def malformed(b, retina_id_of_build, n_of_build):
    return not (b[:8] == MARKER and b[9] == LAYOUT and b[8] < 3 and b[10] == n_of_build and b[11] == 0 and b[12] == 10 and b[15] == 2 and b[16] < 2 and b[17] == retina_id_of_build)

# ------------------------------------------------------------------------- the lesson record, version 2
# A BRAIN02 lesson was eleven bytes: twenty nibbles and the taught action. A BRAIN02.5 lesson is fifteen:
# the twenty-seven nibbles of the published block, low nibble of each pair first, and the taught action.
# Everything an independent implementation needs to rebuild every input, old and new, is in those bytes;
# it never has to see the room.
LESSON_VERSION = 2
LESSON_SIZE = (SENSE_COUNT + 1) // 2 + 1          # 15
def pack_lesson(x, t_abs, predicted=0):
    """the machine's own bytes: nibble i in byte i//2, low half first, so the twenty-seventh sits alone in
    byte 13; the last byte is the taught action with the mood-free prediction in its high half (telemetry
    the replay ignores, exactly as BRAIN02's eleventh byte carried it)"""
    assert len(x) == SENSE_COUNT
    b = bytearray(LESSON_SIZE)
    for i, v in enumerate(x): b[i // 2] |= (v & 15) << (0 if i % 2 == 0 else 4)
    b[LESSON_SIZE - 1] = (t_abs & 15) | ((predicted & 15) << 4)
    return bytes(b)
def unpack_lesson(b):
    assert len(b) == LESSON_SIZE
    sx = lambda v: v - 16 if v >= 8 else v
    x = [sx(b[i // 2] & 15) if i % 2 == 0 else sx(b[i // 2] >> 4) for i in range(SENSE_COUNT)]
    return x, b[LESSON_SIZE - 1] & 15, b[LESSON_SIZE - 1] >> 4

# --------------------------------------------------------------------------------------- migration
MIGRATION_FIELDS = ["kind", "period", "lineage", "rule", "vocabulary", "education", "mood"]
def migrate(b02_slot, retina_id=RETINA_ID, n_new=N):
    """a BRAIN02 brain to a BRAIN02.5 brain: per action row the original weights in order, unchanged, then
    a zero weight for every appended input. Every other behavioural or provenance field is copied by name,
    never inherited by accident; the width, the layout, the marker and the retina id are the only changes."""
    p = b02.parse_slot(b02_slot)
    assert p["layout"] == 2 and p["hidden"] == 0 and p["outputs"] == 10, "not a BRAIN02 layout-2 slot"
    old = p["inputs"]; assert n_new >= old, "BRAIN02.5 is never narrower than the brain it takes"
    W = [row[:] + [0] * (n_new - old) for row in p["weights"]]
    for o in range(10): assert W[o][:old] == p["weights"][o] and W[o][old:] == [0] * (n_new - old)
    return slot_bytes(p["kind"], p["vocabulary"], W, education=p["education"], mood=p["mood"],
                      period=p["period"], lineage=p["lineage"], rule=p["rule"], retina_id=retina_id)
def migration_report(b02_slot, new_slot):
    p, q = b02.parse_slot(b02_slot), parse_slot(new_slot)
    return dict(fields={k: (p[k], q[k]) for k in MIGRATION_FIELDS},
                inputs=(p["inputs"], q["inputs"]), layout=(p["layout"], q["layout"]), retina_id=(p["retina_id"], q["retina_id"]),
                weights_copied=all(q["weights"][o][:p["inputs"]] == p["weights"][o] for o in range(10)),
                appended_zero=all(set(q["weights"][o][p["inputs"]:]) <= {0} for o in range(10)),
                hash_before=b02.brain_hash(b02_slot), hash_after=brain_hash(new_slot))

def predicts_same(b02_slot, new_slot, blocks20, terrains=None):
    """the migration gate's measurement: on every block of the old interface, with any terrain at all
    appended, does the migrated brain choose the action the original chose? Returns (checked, mismatches)"""
    p, q = b02.parse_slot(b02_slot), parse_slot(new_slot)
    eo, en = b02.TABLES[p["retina_id"]][1](), TABLES[q["retina_id"]][1]()
    rnd = random.Random(20260911); bad = 0; n = 0
    for x in blocks20:
        x = list(x)
        z0 = b02.flags(eo, x); _, a0 = forward(p["weights"], z0, p["mood"])
        for t in (terrains if terrains is not None else [[rnd.randint(0, CAP) for _ in TERRAIN] for _ in range(2)]):
            z1 = flags(en, x + list(t)); _, a1 = forward(q["weights"], z1, q["mood"])
            n += 1
            if a0 != a1 or z1[:len(z0)] != z0: bad += 1
    return n, bad

# ------------------------------------------------------------------------------------------ checks
def check():
    design = _load("brain025_design", os.path.join(ROOT, "tools/brain025_design.py"))
    b2 = _load("bakeoff2", os.path.join(ROOT, "tools/bakeoff2.py"))
    ok = True
    e5, e2 = table_T1(), b02.table_R1b()
    ok &= (e5[:64] == e2); print(f"the first 64 entries of retina 5 are R1b's, entry for entry: {e5[:64] == e2}")
    print(f"retina 5 T1: {len(e5)} inputs, {len(table_bytes(e5))} table bytes; the appended sixteen use only GE over values {TERRAIN_BASE}..{TERRAIN_BASE + len(TERRAIN) - 1}")
    ok &= all(op == GE and TERRAIN_BASE <= a < TERRAIN_BASE + len(TERRAIN) for op, a, k in e5[64:])
    # the old inputs do not move, whatever the terrain is
    D = b2.sets(); blocks = sorted(D["s1424"]); rnd = random.Random(7); bad = 0
    for x in blocks:
        t = [rnd.randint(0, CAP) for _ in TERRAIN]
        if flags(e5, list(x) + t)[:64] != b02.flags(e2, list(x)): bad += 1
    print(f"inputs 0..63 identical to BRAIN02's on all {len(blocks)} recorded blocks under random terrain: {bad} differences"); ok &= bad == 0
    # the terrain quantities agree with the design tool on every census scenario
    d, rows = design.rows_with_terrain(); bad = 0
    for r in rows:
        t = [r["terrain"][k] for k in TERRAIN]
        want = [1 if t[TERRAIN.index(v)] >= k else 0 for v, op, k in design.DESIGN]
        got = flags(e5, r["senses"] + t)[64:]
        if got != want: bad += 1
    print(f"the appended inputs equal the design tool's thresholds on all {len(rows)} census scenarios: {bad} differences"); ok &= bad == 0
    # the rule is BRAIN02's, at the same box, on the wider vector
    w1 = [[0] * N for _ in range(10)]; w2 = [[0] * N for _ in range(10)]; rnd = random.Random(11); same = True
    for _ in range(400):
        z = [rnd.randint(0, 1) for _ in range(N)]; t = rnd.randint(0, 9)
        if learn(w1, z, t) != b02.learn(w2, z, t) or w1 != w2: same = False
    print(f"the rule on 80 inputs is BRAIN02's rule, lesson for lesson over 400 lessons: {same}"); ok &= same
    # the slot and the lesson round trip, and neither kind of slot loads into the other build
    W = [[rnd.randint(-128, 127) for _ in range(N)] for _ in range(10)]
    s = slot_bytes(1, 1, W, education=300, mood=[0] * 10)
    p = parse_slot(s)
    ok &= (len(s) == 24 + 10 * N + 10 and p["weights"] == W and p["education"] == 300 and not malformed(s, RETINA_ID, N))
    print(f"slot: {len(s)} bytes at {N} inputs, parse and malformed checks ok; hash domain bytes {len(behavioural_bytes(s))}")
    old = b02.slot_bytes(1, 1, 2, [[0] * 64 for _ in range(10)])
    ok &= malformed(old + bytes(300), RETINA_ID, N) and b02.malformed(s, 2, 64)
    print(f"a BRAIN02 slot is malformed to a BRAIN02.5 build and the reverse: True")
    for _ in range(200):
        x = [rnd.randint(-8, 7) for _ in range(20)] + [rnd.randint(0, CAP) for _ in TERRAIN]; t = rnd.randint(0, 9)
        pr = rnd.randint(0, 9)
        y, tt, pp = unpack_lesson(pack_lesson(x, t, pr))
        if y != x or tt != t or pp != pr: ok = False
    print(f"the lesson record v{LESSON_VERSION}, {LESSON_SIZE} bytes, round trips on 200 random blocks: {ok}")
    # migration: the appended weights are zero, so the argmax cannot move
    Wo = [[rnd.randint(-128, 127) for _ in range(64)] for _ in range(10)]
    so = b02.slot_bytes(1, 1, 2, Wo, education=123, mood=[0] * 10)
    sn = migrate(so); rep = migration_report(so, sn)
    ok &= rep["weights_copied"] and rep["appended_zero"] and rep["fields"]["education"] == (123, 123)
    n, bad = predicts_same(so, sn, blocks[::4])
    print(f"migration: weights copied {rep['weights_copied']}, appended all zero {rep['appended_zero']}, {bad} prediction mismatches over {n} block-and-terrain pairs"); ok &= bad == 0
    print("ALL OK" if ok else "DIFFERENCES FOUND"); return ok

def write_golden():
    os.makedirs(os.path.join(OUT, "golden"), exist_ok=True)
    design = _load("brain025_design", os.path.join(ROOT, "tools/brain025_design.py"))
    rnd = random.Random(20260911)
    def wpack(W): return bytes((v & 255) for row in W for v in row).hex()
    e5 = table_T1()
    # 1. the retina on every census scenario: the machine must match these flag vectors exactly
    d, rows = design.rows_with_terrain()
    ret = [dict(name=r["name"], senses=r["senses"], terrain=[r["terrain"][k] for k in TERRAIN],
                flags="".join(map(str, flags(e5, r["senses"] + [r["terrain"][k] for k in TERRAIN]))),
                h=1 if h_of(r["senses"]) == 1 else 0) for r in rows]
    json.dump(dict(retina=RETINA_ID, n=N, inputs=flag_names(e5), cases=ret), open(os.path.join(OUT, "golden/retina-5.json"), "w"), indent=1)
    # 2. the forward pass at 80 inputs, including both extremes of the accumulator
    fwd = []
    def addf(name, W, z, mood, expect=None):
        acc, a = forward(W, z, mood); assert max(abs(v) for v in acc) <= bound(len(z))
        if expect is not None: assert a == expect, (name, a, expect)
        fwd.append(dict(name=name, n=len(z), weights=wpack(W), mood=bytes(v & 255 for v in mood).hex(), x=z, acc=acc, action=a))
    Z1 = [1] * N
    addf("all zero, every input set: the tie goes to output 0, IDLE", [[0] * N for _ in range(10)], Z1, [0] * 10, 0)
    addf("127 everywhere, every input set, mood 127", [[127] * N for _ in range(10)], Z1, [127] * 10, 0)
    addf("-128 everywhere, every input set, mood -128", [[-128] * N for _ in range(10)], Z1, [-128] * 10, 0)
    W = [[0] * N for _ in range(10)]; W[6][79] = 100; addf("one weight on the last appended input decides", W, [0] * 79 + [1], [0] * 10, 6)
    W = [[0] * N for _ in range(10)]; W[4][64] = 7; W[9][64] = 7; addf("a tie between 4 and 9 on input 64 goes to 4", W, [0] * 64 + [1] + [0] * 15, [0] * 10, 4)
    for k in range(5):
        W = [[rnd.randint(-128, 127) for _ in range(N)] for _ in range(10)]; z = [rnd.randint(0, 1) for _ in range(N)]
        addf(f"random weights and inputs {k}", W, z, [rnd.randint(-128, 127) for _ in range(10)])
    json.dump(dict(n=N, cases=fwd), open(os.path.join(OUT, "golden/forward.json"), "w"), indent=1)
    # 3. lessons at 80 inputs
    les = []
    def addl(name, W, lessons):
        W = [row[:] for row in W]; before = wpack(W); preds, took = [], []
        for z, t in lessons:
            p, tk = learn(W, z, t, LO, HI); preds.append(p); took.append(tk)
        les.append(dict(name=name, n=N, box=[LO, HI], weights_before=before, lessons=[dict(x=z, t=t) for z, t in lessons], weights_after=wpack(W), predictions=preds, taken=took))
    addl("from zero, twelve lessons over random vectors", [[0] * N for _ in range(10)], [([rnd.randint(0, 1) for _ in range(N)], rnd.randint(0, 9)) for _ in range(12)])
    addl("at the clamps: every weight 127 then a lesson that cannot raise it", [[127] * N for _ in range(10)], [(Z1, 3), (Z1, 3), (Z1, 7)])
    addl("at the floor: every weight -128", [[-128] * N for _ in range(10)], [(Z1, 5), (Z1, 2)])
    json.dump(dict(n=N, cases=les), open(os.path.join(OUT, "golden/lessons.json"), "w"), indent=1)
    # 4. the terrain quantities themselves, so the 6502 probe can be checked against the model
    json.dump(dict(quantities=TERRAIN, cap=CAP, cases=[dict(name=r["name"], bricks=r["bricks"], col=r["start"]["col"], row=r["start"]["row"],
                                                            toward=r["toward"], terrain=[r["terrain"][k] for k in TERRAIN]) for r in rows]),
              open(os.path.join(OUT, "golden/terrain.json"), "w"), indent=1)
    print(f"golden written: retina-5 {len(ret)} cases, forward {len(fwd)}, lessons {len(les)}, terrain {len(rows)}")

# ------------------------------------------------------------------------------------ the replay
# The canonical replay: an explicit starting slot plus the ordered LESSON25 entries in, the final slot
# and its behavioural hash out. It reinterprets nothing. Every structural field of the slot and every
# length is checked first, and anything that does not match this reference's own shape is refused with
# the reason, rather than being read as if it were something else.
class Incompatible(Exception): pass

def check_slot(b, where="the starting slot"):
    """fail closed on a slot that is not a BRAIN02.5 slot of exactly this reference's shape"""
    if len(b) < 24: raise Incompatible(f"{where}: {len(b)} bytes, too short to hold a 24-byte header")
    if b[:8] != MARKER:
        if b[:8] == b02.MARKER: raise Incompatible(f"{where}: this is a BRAIN02 slot (marker {b[:8]!r}). Migrate it first with tools/brain025_migrate.py; replay will not reinterpret it")
        raise Incompatible(f"{where}: marker is {b[:8]!r}, not {MARKER!r}")
    if b[9] != LAYOUT: raise Incompatible(f"{where}: layout byte is {b[9]}, not {LAYOUT}")
    if b[17] not in TABLES: raise Incompatible(f"{where}: retina id {b[17]} is unknown to this reference (known: {sorted(TABLES)})")
    entries = TABLES[b[17]][1](); n = b[10]
    if n != len(entries): raise Incompatible(f"{where}: header says {n} inputs but retina {b[17]} has {len(entries)} entries")
    if b[11] != 0: raise Incompatible(f"{where}: hidden count is {b[11]}, not 0")
    if b[12] != 10: raise Incompatible(f"{where}: output count is {b[12]}, not 10")
    if b[15] != 2: raise Incompatible(f"{where}: rule version is {b[15]}, not 2")
    if b[16] > 1: raise Incompatible(f"{where}: vocabulary byte is {b[16]}, not 0 (absolute) or 1 (reference-relative)")
    if b[8] > 2: raise Incompatible(f"{where}: kind byte is {b[8]}, above the 0..2 the machine's own check allows")
    want = 24 + 10 * n + 10
    if len(b) != want: raise Incompatible(f"{where}: {len(b)} bytes, but {n} inputs need exactly {want} (24 header + 10 x {n} weights + 10 mood)")
    return entries

def check_lessons(raw):
    """fail closed on a lesson stream that is not a whole number of LESSON25 entries"""
    if len(raw) % LESSON_SIZE: raise Incompatible(f"the lesson stream is {len(raw)} bytes, not a multiple of the {LESSON_SIZE}-byte LESSON25 entry ({len(raw) // LESSON_SIZE} whole entries and {len(raw) % LESSON_SIZE} bytes over)")
    out = []
    for i in range(0, len(raw), LESSON_SIZE):
        e = raw[i:i + LESSON_SIZE]; x, t, pred = unpack_lesson(e)
        if t > 9: raise Incompatible(f"lesson {i // LESSON_SIZE}: taught action {t} is not one of the ten outputs")
        out.append((x, t, pred))
    return out

def replay(start_slot, lesson_bytes):
    """the whole of it: the rule applied to each entry in the order the machine recorded them.
    Returns (the final slot, a record of what happened)."""
    entries = check_slot(start_slot); lessons = check_lessons(lesson_bytes)
    p = parse_slot(start_slot); W = [row[:] for row in p["weights"]]; edu = p["education"]
    applied = 0; no_change = 0; predictions = []
    for x, t_abs, _pred in lessons:
        z = flags(entries, x)
        t = to_relative(t_abs, h_of(x[:20])) if p["vocabulary"] else t_abs
        pr, took = learn(W, z, t, LO, HI)
        predictions.append(pr)
        if took: applied += 1; edu += 1
        else: no_change += 1
    final = slot_bytes(p["kind"], p["vocabulary"], W, education=edu, mood=p["mood"], period=p["period"],
                       lineage=p["lineage"], rule=p["rule"], retina_id=p["retina_id"])
    return final, dict(inputs=p["inputs"], retina_id=p["retina_id"], vocabulary=p["vocabulary"], lessons=len(lessons),
                       applied=applied, no_change=no_change, education_before=p["education"], education_after=edu,
                       hash_before=brain_hash(start_slot), hash_after=brain_hash(final), predictions=predictions)

def _cmd_replay(argv):
    start_path, lessons_path = argv[0], argv[1]
    out_path = next((argv[i + 1] for i, a in enumerate(argv) if a == "--out"), None)
    expect_path = next((argv[i + 1] for i, a in enumerate(argv) if a == "--expect"), None)
    start = open(start_path, "rb").read(); raw = open(lessons_path, "rb").read()
    try:
        final, r = replay(start, raw)
    except Incompatible as e:
        print(f"REFUSED: {e}"); return 2
    print(f"  starting slot   {start_path}: {len(start)} bytes, {r['inputs']} inputs, retina {r['retina_id']}, vocabulary {'reference-relative' if r['vocabulary'] else 'absolute'}, education {r['education_before']}")
    print(f"  lesson stream   {lessons_path}: {len(raw)} bytes, {r['lessons']} entries of {LESSON_SIZE}")
    print(f"  applied         {r['applied']} lessons; {r['no_change']} left the weights alone")
    print(f"  education       {r['education_before']} -> {r['education_after']}")
    print(f"  brain hash      {r['hash_before'][:16]} -> {r['hash_after']}")
    if out_path: open(out_path, "wb").write(final); print(f"  written         {out_path}: {len(final)} bytes")
    if expect_path:
        want = open(expect_path, "rb").read()
        same = want == final
        print(f"  against {expect_path}: {'IDENTICAL byte for byte' if same else 'DIFFERENT'}"
              + ("" if same else f" (expected hash {brain_hash(want) if want[:8] == MARKER else 'unparseable'})"))
        if not same:
            for i in range(min(len(want), len(final))):
                if want[i] != final[i]: print(f"    first difference at byte {i}: expected ${want[i]:02x}, replay gave ${final[i]:02x}"); break
            if len(want) != len(final): print(f"    lengths differ: expected {len(want)}, replay gave {len(final)}")
            return 1
    if r["no_change"]:
        print(f"  NOTE: {r['no_change']} entries changed nothing. The machine records a lesson only when it takes one,"
              f" so a stream straight off the machine should show zero here.")
    return 0

# ---------------------------------------------------------------------- the provenance manifest
CANONICAL = ["tools/brain025_ref.py", "tools/brain02_ref.py"]
MANIFEST = "deliverables/brain025/replay/MANIFEST.json"

def _sha(path): return hashlib.sha256(open(os.path.join(ROOT, path), "rb").read()).hexdigest()
def _blob(path, commit):
    import subprocess
    r = subprocess.run(["git", "rev-parse", f"{commit}:{path}"], capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip() if r.returncode == 0 else None

def _cmd_manifest(argv):
    import subprocess
    commit = argv[0] if argv else subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    m = dict(schema="tony-brain025-replay-manifest/1", pinned_commit=commit,
             note="tools/ is canonical. These two files together are the BRAIN02.5 replay reference: brain025_ref.py "
                  "holds the retina table, the slot and lesson formats and the replay; brain02_ref.py holds the rule, "
                  "the forward pass, the vocabulary, the nine pseudo-senses and the first sixty-four retina entries.",
             files=[dict(path=p, sha256=_sha(p), git_blob=_blob(p, commit)) for p in CANONICAL])
    os.makedirs(os.path.dirname(os.path.join(ROOT, MANIFEST)), exist_ok=True)
    json.dump(m, open(os.path.join(ROOT, MANIFEST), "w"), indent=1)
    print(f"wrote {MANIFEST} pinned at {commit}")
    for f in m["files"]: print(f"  {f['path']}  sha256 {f['sha256']}  blob {f['git_blob']}")
    return 0

def _cmd_verify(argv):
    path = os.path.join(ROOT, MANIFEST)
    if not os.path.exists(path): print(f"REFUSED: no manifest at {MANIFEST}; run 'manifest' first"); return 2
    m = json.load(open(path)); bad = 0
    print(f"manifest {MANIFEST}, pinned at {m['pinned_commit']}")
    for f in m["files"]:
        now = _sha(f["path"]); ok = now == f["sha256"]
        print(f"  {'ok  ' if ok else 'DRIFT'} {f['path']}  {now}" + ("" if ok else f"  manifest says {f['sha256']}"))
        bad += not ok
    print("the canonical replay reference is byte for byte what the manifest pinned" if not bad else f"{bad} file(s) have changed since the manifest was written")
    return 0 if not bad else 1

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "replay":
        if len(sys.argv) < 4:
            print("usage: brain025_ref.py replay START.slot LESSONS.bin [--out FINAL.slot] [--expect MACHINE.slot]"); sys.exit(2)
        sys.exit(_cmd_replay(sys.argv[2:]))
    if cmd == "manifest": sys.exit(_cmd_manifest(sys.argv[2:]))
    if cmd == "verify": sys.exit(_cmd_verify(sys.argv[2:]))
    if cmd == "check": sys.exit(0 if check() else 1)
    if cmd == "golden": write_golden()
    if cmd == "table":
        e = table_T1(); print(len(e)); print(" ".join(str(op) for op, a, k in e)); print(" ".join(str(a) for op, a, k in e)); print(" ".join(str(k) for op, a, k in e))
