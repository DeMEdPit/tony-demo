#!/usr/bin/env python3
"""
brain02_ref.py - the reference for BRAIN02 (deliverables/bakeoff/PREREG-PHASE3.md): the nine pseudo-senses,
the retina table format and the four published tables, the table interpreter, the forward pass with byte
weights and a byte mood added directly, the symmetric rule at the byte box, the two vocabulary maps, the
slot layout and the three hash domains. Every implementation (this one, the 6502, later the chain) must
produce exactly these bytes on these inputs.

  check     the tables against bakeoff2.py's encoders flag for flag on the 1,424 recorded blocks, and the
            rule against the golden reference at the 4-bit box
  golden    writes deliverables/bakeoff/golden-1b/{forward,lessons,vocabulary,retina-<id>}-v2.json
  tables    prints the four tables as bytes (what the generator embeds)
"""
import hashlib, json, os, random, sys
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables/bakeoff")
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

SENSES = ["bias", "dx", "dy", "facingRight", "onGround", "inAir", "onLadder", "ducking", "floorBelow", "wallAheadFoot", "wallAheadHead",
          "brickAheadFoot", "ladderHere", "ladderBelow", "buildable", "playerAir", "lastAction", "still", "playerDuck", "playerOnLadder"]
PSEUDO = ["hRight", "lastTowardRef", "lastAwayRef", "refAbove", "facingRef", "stepAhead", "wallAhead", "buildableAndClear", "adx"]   # indices 20..28
ABS_ACTIONS = ["idle", "left", "right", "up", "down", "jump", "jump left", "jump right", "build left", "build right"]
REL_ACTIONS = ["idle", "toward", "away", "up", "down", "jump", "jump toward", "jump away", "build toward", "build away"]
HDIR = {1: -1, 2: 1, 6: -1, 7: 1, 8: -1, 9: 1}
GE, LE, EQN, AND, ANDNOT, OR, XNOR = range(7)
OPS = ["GE", "LE", "EQN", "AND", "ANDNOT", "OR", "XNOR"]
LO, HI = -128, 127

# ------------------------------------------------------------------ the reference vector and the vocabulary
def reference(x):
    """the interface's reference vector: today the player's offset, senses 1 and 2"""
    return x[1], x[2]
def h_of(x):
    rx, ry = reference(x)
    if rx > 0: return 1
    if rx < 0: return -1
    return 1 if x[3] else -1
def to_relative(a, h):
    if a not in HDIR: return a
    base = {1: 1, 2: 1, 6: 6, 7: 6, 8: 8, 9: 8}[a]
    return base if HDIR[a] == h else base + 1
def to_absolute(a, h):
    if a not in (1, 2, 6, 7, 8, 9): return a
    base = {1: 1, 2: 1, 6: 6, 7: 6, 8: 8, 9: 8}[a]; toward = (a == base)
    return base + (1 if ((h == 1) == toward) else 0)

# ------------------------------------------------------------------------------------ the pseudo-senses
def pseudo(x):
    """the nine values at indices 20..28, from the twenty senses of one block"""
    rx, ry = reference(x); h = h_of(x); hRight = 1 if h == 1 else 0
    d = HDIR.get(x[16] & 15, 0)
    facing = 1 if x[3] else 0
    return [hRight, 1 if d == h else 0, 1 if d == -h else 0, 1 if ry > 0 else 0, 1 if facing == hRight else 0,
            1 if (x[9] and not x[10]) else 0, 1 if (x[9] and x[10]) else 0, 1 if (x[14] and not x[9]) else 0, abs(rx)]
def values(x): return list(x) + pseudo(x)                    # 29 signed values

# ------------------------------------------------------------------------------------- the tables
RAW_FLAGS = (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19)
def _common_head(): return [(GE, 0, 1)] + [(GE, s, 1) for s in RAW_FLAGS]
def _common_tail(): return [(GE, 2, k) for k in range(1, 8)] + [(LE, 2, -k) for k in range(1, 8)] + [(GE, 17, k) for k in range(1, 8)] + [(EQN, 16, k) for k in range(10)]
def _facts(): return [(GE, 24, 1), (GE, 25, 1), (GE, 26, 1), (AND, 12, 23), (AND, 24, 25), (GE, 27, 1), (GE, 21, 1), (GE, 22, 1)]
def table_R0(): return _common_head() + [(GE, 1, 1), (LE, 1, -1)] + [(GE, 28, k) for k in range(1, 8)] + _common_tail()
def table_R1b(): return table_R0() + _facts()
def table_R0s(): return _common_head() + [(GE, 1, k) for k in range(1, 8)] + [(LE, 1, -k) for k in range(1, 8)] + _common_tail()
def table_R1s(): return table_R0s() + _facts()
TABLES = {1: ("R0", table_R0), 2: ("R1b", table_R1b), 3: ("R0s", table_R0s), 4: ("R1s", table_R1s)}
def flag_names(entries):
    out = []
    for op, a, k in entries:
        nm = (SENSES + PSEUDO)[a]
        if op == GE: out.append(nm if k == 1 and a not in (1, 2, 17, 28) else (f"{nm}>={k}" if a in (1, 2, 17, 28) else f"{nm}>={k}"))
        elif op == LE: out.append(f"{nm}<={k}")
        elif op == EQN: out.append(f"{nm}=={k}")
        else: out.append(f"{OPS[op]}({nm},{(SENSES + PSEUDO)[k]})")
    return out
def table_bytes(entries):
    b = bytearray([len(entries)])
    for op, a, k in entries: b += bytes([op, a, k & 255])
    return bytes(b)
def flags(entries, x):
    """the table interpreter: the flag vector (0/1) of one block"""
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

# ----------------------------------------------------------------------------- the forward pass, the rule
def forward(w, z, mood=None):
    """acc[o] = mood[o] + sum of w[o][i] over the set flags; the first largest wins"""
    n = len(z); acc = [(mood[o] if mood else 0) + sum(w[o][i] for i in range(n) if z[i]) for o in range(10)]
    return acc, max(range(10), key=lambda o: (acc[o], -o))
def learn(w, z, t, lo=LO, hi=HI):
    """the mood-free prediction p; no lesson if p == t; else w[t][i] += 1, w[p][i] -= 1 on every set flag, saturating"""
    _, p = forward(w, z)
    if p == t: return p, False
    for i in range(len(z)):
        if not z[i]: continue
        w[t][i] = min(hi, w[t][i] + 1); w[p][i] = max(lo, w[p][i] - 1)
    return p, True
def learn_signed(w, z, t, lo, hi):
    """the same rule on signed inputs (the golden reference's form, generalised): the step is the sign"""
    _, p = forward_signed(w, z)
    if p == t: return p, False
    for i in range(len(z)):
        if z[i] == 0: continue
        s = 1 if z[i] > 0 else -1
        w[t][i] = max(lo, min(hi, w[t][i] + s)); w[p][i] = max(lo, min(hi, w[p][i] - s))
    return p, True
def forward_signed(w, z):
    acc = [sum(w[o][i] * z[i] for i in range(len(z))) for o in range(10)]
    return acc, max(range(10), key=lambda o: (acc[o], -o))
def bound(n): return 128 * n + 128

# --------------------------------------------------------------------------------- the slot and the hash
MARKER = b"BRAIN02\0"
def slot_bytes(kind, vocab, retina_id, weights, education=0, mood=None, period=4, lineage=0, rule=2):
    n = len(weights[0]); assert len(weights) == 10 and all(len(r) == n for r in weights)
    b = bytearray(MARKER) + bytes([kind, 2, n, 0, 10, period, lineage, rule, vocab, retina_id, education & 255, education >> 8, 0, 0, 0, 0])
    for o in range(10): b += bytes(v & 255 for v in weights[o])
    b += bytes((mood[o] if mood else 0) & 255 for o in range(10))
    return bytes(b)
def parse_slot(b):
    assert b[:8] == MARKER, "not a BRAIN02 slot"
    n = b[10]; sx = lambda v: v - 256 if v >= 128 else v
    return dict(kind=b[8], layout=b[9], inputs=n, hidden=b[11], outputs=b[12], period=b[13], lineage=b[14], rule=b[15], vocabulary=b[16], retina_id=b[17],
                education=b[18] | (b[19] << 8), weights=[[sx(b[24 + o * n + i]) for i in range(n)] for o in range(10)], mood=[sx(b[24 + 10 * n + o]) for o in range(10)])
def behavioural_bytes(b):
    n = b[10]; return bytes(b[8:13]) + bytes(b[16:18]) + bytes(b[24:24 + 10 * n])
def brain_hash(b): return hashlib.sha256(behavioural_bytes(b)).hexdigest()
def malformed(b, retina_id_of_build, n_of_build):
    """True when the program must fall back to kind 0"""
    return not (b[:8] == MARKER and b[9] == 2 and b[8] < 3 and b[10] == n_of_build and b[11] == 0 and b[12] == 10 and b[15] == 2 and b[16] < 2 and b[17] == retina_id_of_build)

# ------------------------------------------------------------------------------------------- checks
def check():
    b2 = _load("bakeoff2", os.path.join(ROOT, "tools/bakeoff2.py")); golden = _load("brain_golden", os.path.join(ROOT, "tools/brain_golden.py"))
    D = b2.sets(); blocks = list(D["s1424"])
    encs = {1: b2.bin56, 2: lambda x: b2.bin56(x) + b2.six(x) + b2.lastrel(x), 3: b2.bin61, 4: lambda x: b2.bin61(x) + b2.six(x) + b2.lastrel(x)}
    ok = True
    for rid, (name, tab) in TABLES.items():
        entries = tab(); bad = sum(1 for x in blocks if flags(entries, list(x)) != encs[rid](list(x)))
        print(f"retina {rid} {name}: {len(entries)} flags, {len(table_bytes(entries))} table bytes, differs from the offline encoder on {bad} of {len(blocks)} blocks")
        ok = ok and bad == 0
    hs = sum(1 for x in blocks if h_of(list(x)) != b2.href(list(x))); print(f"h against bakeoff2.href: {hs} differences"); ok = ok and hs == 0
    for h in (1, -1):
        for a in range(10):
            assert to_relative(to_absolute(a, h), h) == a and to_absolute(to_relative(a, h), h) == a and to_relative(a, h) == b2.to_relative(a, h) and to_absolute(a, h) == b2.to_absolute(a, h)
    print("vocabulary maps: round trips and agreement with bakeoff2: ok")
    # the rule at the 4-bit box on the raw senses against the golden reference, lesson for lesson
    w1 = [[0] * 20 for _ in range(10)]; w2 = [[0] * 20 for _ in range(10)]; same = True; lessons = 0
    for p in range(20):
        for x, t in D["s231"].items():
            a = golden.learn(w1, list(x), t); b = learn_signed(w2, list(x), t, -8, 7); lessons += a[1]
            if a != b or w1 != w2: same = False
    print(f"learn_signed at the 4-bit box against brain_golden.learn over 20 passes: {lessons} lessons, identical {same}"); ok = ok and same
    # the flag rule is the signed rule on 0/1 inputs
    rnd = random.Random(1); same = True
    for _ in range(300):
        n = rnd.choice((56, 61, 64, 69)); w1 = [[rnd.randint(-128, 127) for _ in range(n)] for _ in range(10)]; w2 = [r[:] for r in w1]
        z = [rnd.randint(0, 1) for _ in range(n)]; t = rnd.randint(0, 9)
        if learn(w1, z, t) != learn_signed(w2, z, t, LO, HI) or w1 != w2: same = False
    print(f"learn (flags) equals learn_signed on 0/1 inputs at the byte box over 300 random lessons: {same}"); ok = ok and same
    for rid, (name, tab) in TABLES.items(): assert bound(len(tab())) <= 32767, name
    b = slot_bytes(1, 1, 2, [[0] * 64 for _ in range(10)], education=7); p = parse_slot(b)
    assert len(b) == 674 and p["inputs"] == 64 and p["education"] == 7 and not malformed(b, 2, 64) and malformed(b, 3, 61)
    print("slot: 674 bytes for R1b, parse and malformed checks ok;", "hash domain bytes", len(behavioural_bytes(b)))
    print("ALL OK" if ok else "DIFFERENCES FOUND"); return ok

def write_golden():
    os.makedirs(os.path.join(OUT, "golden-1b"), exist_ok=True)
    rnd = random.Random(20260911)
    def wpack(W): return bytes((v & 255) for row in W for v in row).hex()
    def mpack(m): return bytes(v & 255 for v in m).hex()
    NMAX = 128; fwd, les = [], []
    def addf(name, W, z, mood, expect=None):
        acc, a = forward(W, z, mood); assert max(abs(v) for v in acc) <= bound(len(z))
        if expect is not None: assert a == expect, (name, a, expect)
        fwd.append(dict(name=name, n=len(z), weights=wpack(W), mood=mpack(mood), x=z, acc=acc, action=a))
    def addl(name, W, lessons, lo, hi):
        W = [row[:] for row in W]; before = wpack(W); preds, took = [], []
        for z, t in lessons:
            p, tk = learn(W, z, t, lo, hi); preds.append(p); took.append(tk)
        les.append(dict(name=name, n=len(W[0]), box=[lo, hi], weights_before=before, lessons=[dict(x=z, t=t) for z, t in lessons], weights_after=wpack(W), predictions=preds, taken=took))
    Z1 = [1] * NMAX; z5 = [0] * 5 + [1] + [0] * (NMAX - 6)
    addf("all zero, 128 inputs: the first output wins the tie", [[0] * NMAX for _ in range(10)], Z1, [0] * 10, 0)
    addf("the most positive: 127 on every weight, every flag set, mood 127: 16383 on every row, output 0", [[127] * NMAX for _ in range(10)], Z1, [127] * 10, 0)
    addf("the most negative: -128 everywhere, every flag set, mood -128: -16512 on every row, output 0", [[-128] * NMAX for _ in range(10)], Z1, [-128] * 10, 0)
    W = [[0] * NMAX for _ in range(10)]; W[3][5] = 100; W[7][5] = 100; addf("a positive tie between outputs 3 and 7 goes to 3", W, z5, [0] * 10, 3)
    W = [[-100] * NMAX for _ in range(10)]; W[3][5] = -3; W[7][5] = -3; addf("a negative tie between outputs 3 and 7 goes to 3", W, z5, [0] * 10, 3)
    W = [[-1] * NMAX for _ in range(10)]; W[3][5] = -3; W[7][5] = -3; addf("rows 3 and 7 tie at -3 below the rest at -1: the first of the largest, 0", W, z5, [0] * 10, 0)
    W = [[0] * NMAX for _ in range(10)]; W[9][0] = 1; addf("one weight of 1 on one flag: output 9", W, [1] + [0] * (NMAX - 1), [0] * 10, 9)
    W = [[0] * NMAX for _ in range(10)]; W[2][0] = 15; addf("the mood alone decides: mood 16 on output 5 beats a weight of 15 on output 2", W, [1] + [0] * (NMAX - 1), [0, 0, 0, 0, 0, 16, 0, 0, 0, 0], 5)
    W = [[0] * NMAX for _ in range(10)]; W[2][0] = 16; addf("a weight of 16 ties mood 16 on output 5: the lower index, 2", W, [1] + [0] * (NMAX - 1), [0, 0, 0, 0, 0, 16, 0, 0, 0, 0], 2)
    W = [[0] * NMAX for _ in range(10)]; addf("mood -128 on output 0 and 127 on output 9 with no flags: 9", W, [0] * NMAX, [-128, 0, 0, 0, 0, 0, 0, 0, 0, 127], 9)
    W = [[127] * 56 for _ in range(10)]; W[4] = [-128] * 56; addf("56 inputs, the sign-extension check: a row of -128 against rows of 127", W, [1] * 56, [0] * 10, 0)
    W = [[0] * 56 for _ in range(10)]; W[6][10] = -128; W[8][10] = -127; addf("56 inputs: -127 beats -128; the rest zero: 0 wins", W, [0] * 10 + [1] + [0] * 45, [0] * 10, 0)
    W = [[-128] * 56 for _ in range(10)]; W[8][10] = -127; addf("56 inputs, all rows -128 on the active flag but row 8 at -127: 8", W, [0] * 10 + [1] + [0] * 45, [0] * 10, 8)
    for k in range(20):
        n = rnd.choice((56, 61, 64, 69, 128)); W = [[rnd.randint(-128, 127) for _ in range(n)] for _ in range(10)]
        addf(f"random {k}", W, [rnd.randint(0, 1) for _ in range(n)], [rnd.randint(-128, 127) if k % 2 else 0 for _ in range(10)])
    json.dump(dict(set="forward-v2", interface="BRAIN02", note="byte weights two's complement, inputs 0/1 flags, mood one signed byte per output added directly, 16-bit accumulators, first largest wins", cases=fwd),
              open(os.path.join(OUT, "golden-1b/forward-v2.json"), "w"), indent=1)
    for bits, (lo, hi) in ((8, (-128, 127)), (6, (-32, 31))):
        W = [[0] * 56 for _ in range(10)]; addl(f"box {bits}: from zero, taught 2 with flags 0 and 5 set: row 2 up, row 0 down", W, [([1] + [0] * 4 + [1] + [0] * 50, 2)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[2] = [hi] * 56; addl(f"box {bits}: row 2 at {hi} predicted, taught 1 twice: row 1 rises to 2, row 2 falls to {hi - 2}", W, [([1] * 56, 1), ([1] * 56, 1)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[0] = [lo] * 56; W[1] = [hi] * 56; addl(f"box {bits}: the predicted row 1 at {hi} falls to {hi - 1}; taught row 3 rises; row 0 at {lo} untouched", W, [([1] * 56, 3)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[5] = [hi] * 56; W[0] = [hi] * 56; addl(f"box {bits}: a tie at {hi} between rows 0 and 5 predicts 0; taught 5: row 5 cannot rise past {hi}, row 0 falls to {hi - 1}", W, [([1] * 56, 5)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[7] = [lo] * 56; W[0] = [lo + 1] * 56; W[1] = [lo] * 56; addl(f"box {bits}: the predicted row 0 at {lo + 1} falls to {lo} and no further on a second lesson", W, [([1] * 56, 7), ([1] * 56, 7), ([1] * 56, 7)], lo, hi)
        W = [[0] * 56 for _ in range(10)]; W[4][0] = 3; addl(f"box {bits}: a no-op: the taught action is already predicted", W, [([1] + [0] * 55, 4)], lo, hi)
        W = [[0] * 128 for _ in range(10)]; addl(f"box {bits}: 128 inputs all set, taught 9 six times from zero: one lesson, then no-ops", W, [([1] * 128, 9)] * 6, lo, hi)
        for k in range(12):
            n = rnd.choice((56, 61, 64, 69, 128)); W = [[rnd.randint(lo, hi) for _ in range(n)] for _ in range(10)]
            addl(f"box {bits}: random {k}", W, [([rnd.randint(0, 1) for _ in range(n)], rnd.randint(0, 9)) for _ in range(rnd.randint(1, 8))], lo, hi)
    json.dump(dict(set="lessons-v2", interface="BRAIN02", note="the rule of BRAIN-INTERFACE-V1 section 6 on flags with the clamp at the box; weights as bytes; inputs 0/1; the mood plays no part", cases=les),
              open(os.path.join(OUT, "golden-1b/lessons-v2.json"), "w"), indent=1)
    # the vocabulary: forty cases per direction, from blocks that set h each way
    voc = []
    for hname, x in (("dx>0", [7, 3, 0, 0] + [0] * 16), ("dx<0", [7, -3, 0, 7] + [0] * 16), ("dx==0 facing right", [7, 0, 2, 7] + [0] * 16), ("dx==0 facing left", [7, 0, 2, 0] + [0] * 16)):
        h = h_of(x)
        for a in range(10):
            voc.append(dict(block=x, h=h, case=hname, output=a, resolved_absolute=to_absolute(a, h), pressed_absolute=a, taught_relative=to_relative(a, h)))
    json.dump(dict(set="vocabulary-v2", interface="BRAIN02", note="the resolution (output index -> absolute action) and the translation (pressed absolute -> taught relative) under h of the block; identity under the absolute vocabulary", cases=voc),
              open(os.path.join(OUT, "golden-1b/vocabulary-v2.json"), "w"), indent=1)
    # the retinas: every recorded block's flag vector per table, as hex bit strings
    b2 = _load("bakeoff2", os.path.join(ROOT, "tools/bakeoff2.py")); D = b2.sets(); blocks = sorted(D["s1424"])
    for rid, (name, tab) in TABLES.items():
        entries = tab()
        cases = [dict(x=list(x), flags="".join(str(f) for f in flags(entries, list(x))), h=h_of(list(x)), pseudo=pseudo(list(x))) for x in blocks]
        json.dump(dict(set=f"retina-{rid}", retina=name, retina_id=rid, inputs=len(entries), table=table_bytes(entries).hex(), names=flag_names(entries), cases=cases),
                  open(os.path.join(OUT, f"golden-1b/retina-{rid}-v2.json"), "w"))
    print(f"wrote forward-v2 ({len(fwd)}), lessons-v2 ({len(les)}), vocabulary-v2 ({len(voc)}), retina-1..4 ({len(blocks)} blocks each)")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "check": sys.exit(0 if check() else 1)
    elif cmd == "golden": write_golden()
    elif cmd == "tables":
        for rid, (name, tab) in TABLES.items(): e = tab(); print(rid, name, len(e), table_bytes(e).hex())
    else: print(__doc__)
