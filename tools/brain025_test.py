#!/usr/bin/env python3
"""
brain025_test.py - the BRAIN02.5 gates (deliverables/brain025/PREREG-BRAIN025.md), through the harness.

  smoke PRG        boots, the markers, a blank brain that idles, the profiler
  blank PRG        the blank-Tony proof: zero weights, every accumulator equal, IDLE, and he never moves
  key PRG          the teaching key: the edge, the rows it ignores, and the joystick untouched by the scan
  parity PRG       the terrain probe against the model, the retina and h, the goldens, malformed slots
  migrate PRG      the migration gate: a BRAIN02 brain into BRAIN02.5, zero prediction mismatches
  resources PRG    sizes, addresses, cycles, raster
  teach PRG        teaching end to end through the key
  drain PRG        ring cycles with replay equality, and the split against the uninterrupted run
  descriptor PRG   the JSON descriptor for the workbench
"""
import hashlib, json, os, re, subprocess, sys, tempfile
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables/brain025")
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
ref = _load("brain025_ref", os.path.join(ROOT, "tools/brain025_ref.py"))
b02 = _load("brain02_ref", os.path.join(ROOT, "tools/brain02_ref.py"))
census = _load("brain025_census", os.path.join(ROOT, "tools/brain025_census.py"))
design = _load("brain025_design", os.path.join(ROOT, "tools/brain025_design.py"))

KEY_T = 21                                # minimal64's key code for T (matrix row 2, column bit 6)

class Build:
    def __init__(self, prg):
        self.prg = prg; self.name = os.path.basename(prg)[:-4]
        self.sym = {}
        for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(os.path.join(ROOT, f"src/kickass/{self.name}.sym")).read()):
            self.sym.setdefault(m.group(1), int(m.group(2), 16))
        self.n = self.sym["B02_N"]; self.senses = self.sym.get("B02_SENSES", 20); self.retina = self.sym["B02_RETINA"]; self.vocab = self.sym["B02_VOCAB"]
        self.size = os.path.getsize(prg); self.sha = hashlib.sha256(open(prg, "rb").read()).hexdigest()
    def __getitem__(self, k): return self.sym[k]
    def run(self, script):
        with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
        r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), self.prg, "@" + f.name], capture_output=True, text=True); os.unlink(f.name)
        return [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)], r.stdout

def pk(a, n=1): return "".join(f"peek:{a + i:X}," for i in range(n))
def po(a, d): return "".join(f"poke:{a + i:X}:{b & 255:02X}," for i, b in enumerate(d))
def w16(v): return [v & 255, (v >> 8) & 255]
def s16(lo, hi): v = lo | (hi << 8); return v - 65536 if v >= 32768 else v
def sg(x): return x - 16 if x >= 8 else x
def xb(x): return bytes(v & 15 for v in x)

ok = True
def check(cond, msg):
    global ok
    ok &= bool(cond); print(("  ok   " if cond else "  FAIL ") + msg)

def place(b, cx, cy, state, px, py, pstate=0x80):
    """both Tonys put where a scenario wants them, through THIS build's own symbols"""
    return (po(b["cloneX"], w16(cx)) + po(b["cloneNextX"], w16(cx)) +
            f"poke:{b['cloneY']:X}:{cy:02X},poke:{b['cloneNextY']:X}:{cy:02X},poke:{b['cloneState']:X}:{state:02X},poke:{b['cloneStateAllowed']:X}:{state:02X}," +
            po(b["physPlayerX"], w16(px)) + f"poke:{b['physPlayerY']:X}:{py:02X},poke:{b['physPlayerState']:X}:{pstate:02X},")

WEIGHTS_ZERO = bytes(10 * 80)
def weights_bytes(W): return bytes(v & 255 for row in W for v in row)

# ----------------------------------------------------------------------------------------- smoke
def smoke(b):
    print(f"{b.name}: {b.size} bytes, sha256 {b.sha[:16]}, n={b.n} senses={b.senses} retina {b.retina} vocab {b.vocab}")
    v, out = b.run("wait:300,sync," + pk(b["brainMarker"], 8) + pk(b["brainKind"]) + pk(b["brainLayout"]) + pk(b["brainInputCount"]) + pk(b["brainRetinaId"]) +
                   pk(b["lessonMarker"], 8) + pk(b["lessonCap"], 2) + pk(b["lessonSize"]) + pk(b["brainKindNow"]) + pk(b["cloneX"], 2) + pk(b["cloneY"]) + pk(b["cloneSenses"], 27) +
                   "joy:8:120,wait:200,sync," + pk(b["cloneX"], 2) + pk(b["brainThinks"], 2) + pk(b["brainActiveCount"]) + pk(b["brainAction"]) + pk(b["brainAcc"], 20) + pk(b["bodyRasterMax"]) + pk(b["bodyOverruns"]))
    check(bytes(v[0:8]) == b"BRAIN025", f"the slot's marker is BRAIN025, not BRAIN02")
    check(v[8] == 1 and v[9] == 3 and v[10] == b.n and v[11] == ref.RETINA_ID, f"kind {v[8]}, layout {v[9]}, {v[10]} inputs, retina {v[11]}")
    check(bytes(v[12:20]) == b"LESSON25" and v[22] == ref.LESSON_SIZE, f"the LESSON25 ring: capacity {v[20] | v[21] << 8}, entry {v[22]} bytes")
    check(v[23] == 1, "the slot passes its own check at boot: the blank brain runs the network, not a fallback")
    cx = v[24] | v[25] << 8
    check((cx >> 3) - 2 == 7, f"the study spawn: X {cx}, columns {(cx >> 3) - 2} to {((cx + 8) >> 3) - 2}, Y {v[26]}")
    i = 27 + 27
    cx1 = v[i] | v[i + 1] << 8; th = v[i + 2] | v[i + 3] << 8; acc = [s16(v[i + 6 + 2 * o], v[i + 7 + 2 * o]) for o in range(10)]
    check(cx1 == cx and th > 20 and v[i + 5] == 0 and acc == [0] * 10, f"after 320 frames with the player walking off: he has not moved, {th} thinks, {v[i + 4]} inputs set, action {v[i + 5]}, every accumulator 0")
    check(v[i + 26] <= 230 and v[i + 27] == 0, f"raster maximum {v[i + 26]}, overruns {v[i + 27]}")
    return ok

# --------------------------------------------------------------------------------- the terrain probe
def terrain_parity(b, quick=False):
    """the machine's own seven terrain nibbles against the offline model, on every census scenario"""
    SC = census.scenarios()
    if quick: SC = SC[::8]
    bad = 0; total = 0; first = []
    for c in range(0, len(SC), 12):
        chunk = SC[c:c + 12]
        s = f"wait:300,poke:{b['brainKind']:X}:01," + po(b["brainWeights"], WEIGHTS_ZERO) + "snapshot,"
        parts = []
        for sc in chunk:
            t = "".join(census.brick(col, row) for (col, row) in sc["bricks"])
            t += place(b, *sc["pose"], *sc["player"], sc.get("pstate", 0x80))
            t += f"wait:{census.SETTLE},sync," + pk(b["cloneSenses"], 27) + pk(b["cloneX"], 2) + pk(b["cloneY"])
            parts.append(t)
        v, out = b.run(s + "restore,".join(parts))
        for k, sc in enumerate(chunk):
            g = v[k * 30:(k + 1) * 30]
            if len(g) < 30: bad += 1; total += 1; continue
            x = [sg(t) for t in g[:27]]; cx = g[27] | g[28] << 8; cy = g[29]
            gmap = design.solid_map([tuple(bb) for bb in sc["bricks"]])
            want = design.terrain(gmap, (cx >> 3) - 2, (cy >> 3) - 6, 1 if sc["toward"] > 0 else -1)
            got = {nm: x[20 + i] for i, nm in enumerate(ref.TERRAIN)}
            total += 1
            if any(got[nm] != want[nm] for nm in ref.TERRAIN):
                bad += 1
                if len(first) < 4: first.append((sc["name"], {nm: (got[nm], want[nm]) for nm in ref.TERRAIN if got[nm] != want[nm]}))
    for nm, d in first: print(f"   differs: {nm}: " + ", ".join(f"{k} machine {a} model {w}" for k, (a, w) in d.items()))
    check(bad == 0, f"the terrain probe: {total - bad} of {total} scenarios equal to the model, quantity for quantity")
    return bad == 0

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "terrain":
    sys.exit(0 if terrain_parity(Build(sys.argv[2]), quick="--quick" in sys.argv) else 1)
if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "smoke":
    sys.exit(0 if smoke(Build(sys.argv[2])) else 1)

# ------------------------------------------------------------------------- the blank-Tony proof
def blank(b):
    """zero weights, a normal forward pass, every accumulator equal, IDLE by the existing tie, and he
    does not move. The follow rule is still in the image and is proved never to run."""
    print(f"{b.name}: the blank brain")
    S = b.sym
    s = "wait:300,sync," + pk(S["cloneX"], 2) + pk(S["cloneY"]) + pk(S["brainKindNow"])
    for k in range(12):                                                    # the player walks away and back
        s += ("joy:8:40," if k % 2 == 0 else "joy:4:40,") + "wait:10,sync," + pk(S["cloneX"], 2) + pk(S["cloneY"]) + pk(S["brainAction"]) + pk(S["brainOutput"]) + pk(S["brainAcc"], 20) + pk(S["cloneJoy"]) + pk(S["brainActiveCount"])
    s += "sync," + pk(S["brainThinks"], 2) + pk(S["bodyFrames"], 2)
    v, out = b.run(s)
    x0 = v[0] | v[1] << 8; y0 = v[2]
    check(v[3] == 1, "a blank slot is well formed: the network runs, there is no fallback kind")
    moved = 0; nonidle = 0; untied = 0; joy = 0; act = []
    for k in range(12):
        g = v[4 + k * 27:4 + (k + 1) * 27]
        if (g[0] | g[1] << 8) != x0 or g[2] != y0: moved += 1
        if g[3] != 0 or g[4] != 0: nonidle += 1
        acc = [s16(g[5 + 2 * o], g[6 + 2 * o]) for o in range(10)]
        if len(set(acc)) != 1: untied += 1
        if g[25] != 0: joy += 1
        act.append(g[26])
    i = 4 + 12 * 27
    check(moved == 0, f"over {v[i + 2] | v[i + 3] << 8} frames of the player walking to and fro, the clone never moved from X {x0} Y {y0}")
    check(untied == 0, "every accumulator equal to every other at every sample: nothing breaks the tie")
    check(nonidle == 0, "the chosen action and output were 0 (IDLE) at every sample")
    check(joy == 0, "the joystick byte the brain wrote was never anything but zero")
    check((v[i] | v[i + 1] << 8) > 100, f"and it was a real forward pass each time: {v[i] | v[i + 1] << 8} thinks, {min(act)}-{max(act)} inputs set")
    return ok

# ----------------------------------------------------------------------------- the teaching key
def key(b):
    """the toggle: the press edge, once per press; no other key in the row or the matrix; and a replayed
    joystick script identical with the scan running"""
    print(f"{b.name}: the teaching key")
    S = b.sym
    s = "wait:300,sync," + pk(S["teachMode"]) + pk(S["teachKeyEdges"])
    for k, frames in ((KEY_T, 10), (KEY_T, 10), (KEY_T, 60), (19, 20), (5, 20), (20, 20), (47, 20), (KEY_T, 10)):
        s += f"key:{k}:{frames},sync," + pk(S["teachMode"]) + pk(S["teachKeyEdges"]) + pk(S["brainAction"]) + pk(S["macroStep"]) + pk(S["lessonWriteSeq"], 2)
    v, out = b.run(s)
    names = ["T", "T again", "T held 60 frames", "E (row 1)", "5 (row 2, column 0)", "R (row 2, column 1)", "X (row 2, column 7)", "T once more"]
    want = [(1, 1), (0, 2), (1, 3), (1, 3), (1, 3), (1, 3), (1, 3), (0, 4)]
    good = True; lessons = 0
    for k, nm in enumerate(names):
        g = v[2 + k * 6:2 + (k + 1) * 6]
        got = (g[0], g[1]); lessons = g[4] | g[5] << 8
        if got != want[k]: good = False; print(f"   {nm}: teachMode {got[0]} edges {got[1]}, wanted {want[k]}")
    check(v[0] == 0 and v[1] == 0, "the build boots with teaching off and the key untouched")
    check(good, "T toggles once per press and no other key in its row or its matrix does anything")
    check(lessons == 0, f"and no press ever became a lesson: {lessons} recorded")
    # Does the scan disturb the joystick? The same drive, frame for frame, once with nothing pressed and
    # once with four keys pressed in turn (three of them in the scanned row) so the matrix is being pulled
    # while port A is driven. None of them is T, so teaching never toggles and only the scan differs.
    drive = "joy:8:60,wait:30,joy:4:40,wait:30,joy:24:20,wait:60,sync,"
    read = pk(S["physPlayerX"], 2) + pk(S["physPlayerY"]) + pk(S["physPlayerState"]) + pk(S["cloneX"], 2) + pk(S["cloneY"]) + pk(S["bodyFrames"], 2) + pk(S["teachMode"])
    quiet = "wait:300," + "wait:9,wait:10," * 4 + drive                      # key:K:4 is four frames pressed then five released
    keys = "wait:300," + "".join(f"key:{k}:4,wait:10," for k in (5, 20, 47, 19)) + drive
    a, _ = b.run(quiet + read); c, _ = b.run(keys + read)
    check(a == c, f"the same drive, frame for frame, is identical with four keys pressed and with none: player X {a[0] | a[1] << 8} Y {a[2]} state {a[3]}, clone X {a[4] | a[5] << 8} Y {a[6]}, frame {a[7] | a[8] << 8}, teaching {a[9]}")
    # and with T held right through the drive: it toggles once, on its edge, and the stick still works
    held = "wait:300," + "wait:9,wait:10," * 4 + "hold:0,"                     # nothing on the stick yet
    d, _ = b.run("wait:300,key:21:200,sync," + pk(S["teachKeyEdges"]) + pk(S["teachMode"]))
    check(d[0] == 1 and d[1] == 1, f"T held for 200 frames toggles exactly once: {d[0]} edge(s), teaching {d[1]}")
    return ok

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "blank": sys.exit(0 if blank(Build(sys.argv[2])) else 1)
if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "key": sys.exit(0 if key(Build(sys.argv[2])) else 1)

# --------------------------------------------------------------------------------------- parity
WAIT = 6                                   # frames for one hook pass at eighty inputs, all of them set
def blocks_all():
    b2 = _load("bakeoff2", os.path.join(ROOT, "tools/bakeoff2.py")); D = b2.sets()
    return sorted(D["s1424"]), D

def parity(b, quick=False):
    """the retina and h on the census blocks through the hook, the goldens at eighty inputs, the
    vocabulary, and a malformed slot on every header field"""
    print(f"{b.name}: n={b.n} senses={b.senses} retina {b.retina} vocab {b.vocab}")
    S = b.sym; n = b.n
    TI, TF, TR, TM, TA, TO, TAC, TH = S["brainTestIn"], S["brainTestFlags"], S["brainTestRun"], S["brainTestMode"], S["brainTestAction"], S["brainTestOutput"], S["brainTestAcc"], S["brainTestH"]
    W, MOOD, KIND = S["brainWeights"], S["brainMood"], S["brainKind"]
    entries = ref.table_T1()
    # 1. the retina on the census blocks, and on the recorded blocks with terrain appended
    G = json.load(open(os.path.join(OUT, "golden/retina-5.json")))["cases"]
    cases = [(c["senses"] + c["terrain"], c["flags"], c["h"]) for c in G]
    blocks, D = blocks_all()
    rnd = __import__("random").Random(4)
    extra = [list(x) + [rnd.randint(0, ref.CAP) for _ in ref.TERRAIN] for x in blocks[::(40 if quick else 4)]]
    cases += [(x, "".join(map(str, ref.flags(entries, x))), 1 if ref.h_of(x[:20]) == 1 else 0) for x in extra]
    if quick: cases = cases[::6]
    bad = 0
    for c0 in range(0, len(cases), 90):
        chunk = cases[c0:c0 + 90]; s = f"wait:300,poke:{TM:X}:00,"
        for x, want, h in chunk: s += po(TI, xb(x)) + f"poke:{TR:X}:01,wait:{WAIT},sync," + pk(TF, n) + pk(TH)
        v, out = b.run(s)
        for k, (x, want, h) in enumerate(chunk):
            g = v[k * (n + 1):(k + 1) * (n + 1)]
            if len(g) < n + 1 or "".join(map(str, g[:n])) != want or g[n] != h:
                bad += 1
                if bad < 4: print(f"   differs: {x}\n     machine {''.join(map(str, g[:n]))}\n     want    {want}")
    check(bad == 0, f"the retina and h: {len(cases) - bad} of {len(cases)} blocks byte for byte (the census scenarios and recorded blocks under random terrain)")
    # 2. the forward pass, at eighty inputs
    G = json.load(open(os.path.join(OUT, "golden/forward.json")))["cases"]
    s = f"wait:300,poke:{TM:X}:01,"
    for c in G: s += po(W, bytes.fromhex(c["weights"])) + po(MOOD, bytes.fromhex(c["mood"])) + po(TF, bytes(c["x"])) + f"poke:{TR:X}:01,wait:{WAIT},sync," + pk(TAC, 20) + pk(TO) + pk(TA)
    v, out = b.run(s); bad = 0
    for k, c in enumerate(G):
        g = v[k * 22:(k + 1) * 22]; acc = [s16(g[2 * o], g[2 * o + 1]) for o in range(10)]
        if len(g) < 22 or acc != c["acc"] or g[20] != c["action"]:
            bad += 1; print(f"   differs: forward '{c['name']}': machine {acc} out {g[20] if len(g) > 20 else '?'}")
    check(bad == 0, f"the golden forward pass at {n} inputs: {len(G) - bad} of {len(G)} cases (the accumulators and the first largest)")
    # 3. the rule, at eighty inputs
    G = json.load(open(os.path.join(OUT, "golden/lessons.json")))["cases"]
    LR, LT, LP, LK = S["brainLearnRun"], S["brainLearnTestT"], S["brainLearnTestP"], S["brainLearnTestTook"]
    bad = 0
    for c in G:
        s = f"wait:300,poke:{TM:X}:01," + po(MOOD, bytes(10)) + po(W, bytes.fromhex(c["weights_before"]))
        for les in c["lessons"]: s += po(TF, bytes(les["x"])) + f"poke:{LT:X}:{les['t']:02X},poke:{LR:X}:01,wait:{WAIT},sync," + pk(LP) + pk(LK)
        s += "sync," + "".join(pk(W + i, 1) for i in range(10 * n))
        v, out = b.run(s); m = len(c["lessons"])
        got = bytes(v[2 * m:2 * m + 10 * n])
        if got.hex() != c["weights_after"] or [v[2 * k] for k in range(m)] != c["predictions"] or [bool(v[2 * k + 1]) for k in range(m)] != c["taken"]:
            bad += 1; print(f"   differs: lessons '{c['name']}'")
    check(bad == 0, f"the golden lessons at {n} inputs, box -128..127: {len(G) - bad} of {len(G)} cases (the weights after, the predictions, and which were taken)")
    # 4. the vocabulary, unchanged from BRAIN02
    V = json.load(open(os.path.join(ROOT, "deliverables/bakeoff/golden-1b/vocabulary-v2.json")))["cases"]
    s = f"wait:300,poke:{TM:X}:00,"
    for c in V: s += po(TI, xb(list(c["block"]) + [0] * len(ref.TERRAIN))) + f"poke:{TR:X}:01,wait:{WAIT},sync," + pk(TH)
    v, out = b.run(s); bad = sum(1 for k, c in enumerate(V) if v[k] != (1 if c["h"] == 1 else 0))
    check(bad == 0, f"the vocabulary on {len(V)} golden cases: h resolved as BRAIN02 resolves it, {len(V) - bad} of {len(V)}")
    # 5. a malformed slot falls back, on every header field
    good = ref.slot_bytes(1, b.vocab, [[0] * n for _ in range(10)])
    fields = {"marker": (0, ord("X")), "layout": (9, 2), "inputs": (10, n - 1), "hidden": (11, 1), "outputs": (12, 9), "rule": (15, 3), "vocab": (16, 2), "retina": (17, 2), "kind": (8, 3)}
    s = "wait:300," + po(S["brainMarker"], good) + "wait:8,sync," + pk(S["brainKindNow"])
    for nm, (off, val) in fields.items():
        s += po(S["brainMarker"], good) + f"poke:{S['brainMarker'] + off:X}:{val:02X},wait:8,sync," + pk(S["brainKindNow"])
    s += po(S["brainMarker"], good) + "wait:8,sync," + pk(S["brainKindNow"])
    v, out = b.run(s)
    check(v[0] == 1 and all(x == 0 for x in v[1:1 + len(fields)]) and v[1 + len(fields)] == 1,
          f"malformed slots: a good one gives kind 1, each header field wrong in turn gives {list(v[1:1 + len(fields)])}, and a good one again gives {v[1 + len(fields)]}")
    return ok

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "parity": sys.exit(0 if parity(Build(sys.argv[2]), quick="--quick" in sys.argv) else 1)

# ------------------------------------------------------------------------------ the migration gate
def migrate_gate(b, old_prg=None, quick=False):
    """the same brain on both machines: the original on the BRAIN02 build and the migrated copy on the
    BRAIN02.5 build must choose the same action wherever the old observation interface applies"""
    old_prg = old_prg or os.path.join(ROOT, "deliverables/prg/minimal64/tony-b02-a.prg")
    ob = Build(old_prg)
    print(f"{b.name}: the migration gate against {ob.name} ({ob.n} inputs)")
    mig = _load("brain025_migrate", os.path.join(ROOT, "tools/brain025_migrate.py"))
    brains = []
    p3 = os.path.join(ROOT, "deliverables/bakeoff/phase3/climbed-tony-b02-a.bin")
    if os.path.exists(p3): brains.append(("the Phase 3 taught brain", open(p3, "rb").read()))
    b2t = _load("brain02_test", os.path.join(ROOT, "tools/brain02_test.py"))
    Wl = b2t.learned_weights(ob)
    brains.append(("Phase 2b's learned weights", b02.slot_bytes(1, ob.vocab, ob.retina, Wl, education=474)))
    rnd = __import__("random").Random(20260911)
    brains.append(("a random brain at the clamps", b02.slot_bytes(1, ob.vocab, ob.retina, [[rnd.choice((-128, 127, rnd.randint(-128, 127))) for _ in range(ob.n)] for _ in range(10)], education=7)))
    blocks, D = blocks_all()
    sel = sorted(D["s474"])[::(24 if quick else 6)]
    terrains = [[0] * len(ref.TERRAIN), [ref.CAP] * len(ref.TERRAIN), [3, 0, 2, 4, 7, 1, 5]]
    total = 0; bad = 0
    for nm, old in brains:
        new = ref.migrate(old)
        r = ref.migration_report(old, new)
        check(r["weights_copied"] and r["appended_zero"], f"{nm}: the 64 weights copied in order per row, {b.n - ob.n} zero weights appended, fields {', '.join(f'{k} {v[0]}->{v[1]}' for k, v in r['fields'].items() if k != 'mood')}")
        # the old machine's choice
        s = f"wait:300,poke:{ob['brainTestMode']:X}:00," + po(ob["brainMarker"], old)
        # the same generous wait on both builds: two frames is sometimes short of one hook pass even at
        # sixty-four inputs, and a short wait reads the previous block's answer rather than this one's
        for x in sel: s += po(ob["brainTestIn"], xb(x)) + f"poke:{ob['brainTestRun']:X}:01,wait:{WAIT},sync," + pk(ob["brainTestAction"]) + pk(ob["brainTestOutput"])
        va, _ = ob.run(s)
        # the new machine's, with the migrated brain, under each terrain
        for t in terrains:
            s = f"wait:300,poke:{b['brainTestMode']:X}:00," + po(b["brainMarker"], new)
            for x in sel: s += po(b["brainTestIn"], xb(list(x) + t)) + f"poke:{b['brainTestRun']:X}:01,wait:{WAIT},sync," + pk(b["brainTestAction"]) + pk(b["brainTestOutput"])
            vb, _ = b.run(s)
            for k in range(len(sel)):
                total += 1
                if va[2 * k:2 * k + 2] != vb[2 * k:2 * k + 2]:
                    bad += 1
                    if bad < 4: print(f"   differs: block {list(sel[k])} terrain {t}: BRAIN02 action {va[2 * k]} output {va[2 * k + 1]}, BRAIN02.5 action {vb[2 * k]} output {vb[2 * k + 1]}")
    check(bad == 0, f"on the machine: {total - bad} of {total} choices identical ({len(brains)} brains x {len(sel)} teacher-visited blocks x {len(terrains)} terrains)")
    # and the whole corpus, offline
    tot = badd = 0
    for nm, old in brains:
        n2, b2 = ref.predicts_same(old, ref.migrate(old), blocks, terrains); tot += n2; badd += b2
    check(badd == 0, f"off the machine, over the full 1,424-block corpus: {tot - badd} of {tot} choices identical, {badd} mismatches")
    return ok

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "migrate": sys.exit(0 if migrate_gate(Build(sys.argv[2]), quick="--quick" in sys.argv) else 1)

# ------------------------------------------------------------------------- a machine driven by line
class Machine:
    def __init__(self, b):
        self.b = b; self.p = subprocess.Popen([os.path.join(ROOT, "tools/m64-harness/m64run"), b.prg, "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    def do(self, line):
        self.p.stdin.write(line + "\n"); self.p.stdin.flush(); out = []
        while True:
            l = self.p.stdout.readline()
            if not l or l.strip() == "ok": break
            out.append(l)
        return [int(m, 16) for l in out for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", l)]
    def close(self):
        try: self.p.stdin.close(); self.p.wait(timeout=5)
        except Exception: self.p.kill()
cu = _load("curriculum", os.path.join(ROOT, "tools/curriculum.py"))

def senses(m, b):
    v = m.do("sync," + pk(b["cloneSenses"], b.senses) + pk(b["cloneX"], 2) + pk(b["cloneY"]) + pk(b["cloneState"]) + pk(b["physPlayerX"], 2) + pk(b["physPlayerY"]))
    n = b.senses
    return dict(senses=[sg(x) for x in v[:n]], cx=v[n] | v[n + 1] << 8, cy=v[n + 2], cs=v[n + 3], px=v[n + 4] | v[n + 5] << 8, py=v[n + 6])
def ring_state(m, b):
    v = m.do("sync," + pk(b["lessonWriteSeq"], 2) + pk(b["lessonReadSeq"], 2) + pk(b["lessonStatus"]) + pk(b["brainEducation"], 2) + pk(b["lessonCap"], 2) + pk(b["lessonDrains"]) +
             pk(b["lessonCumWrite"], 2) + pk(b["lessonCumRead"], 2) + pk(b["lessonNotPaired"], 2))
    return dict(write=v[0] | v[1] << 8, read=v[2] | v[3] << 8, status=v[4], education=v[5] | v[6] << 8, cap=v[7] | v[8] << 8, drains=v[9],
                cumWrite=v[10] | v[11] << 8, cumRead=v[12] | v[13] << 8, not_paired=v[14] | v[15] << 8)
def slot(m, b):
    n = b["BRAIN_BLOCK_SIZE"]; out = []
    for c in range(0, n, 200): out += m.do("".join(f"peek:{b['brainMarker'] + c + i:X}," for i in range(min(200, n - c))))
    return bytes(out)
def teach_on(m, b, on=True):
    st = m.do("sync," + pk(b["teachMode"]))[0]
    if st != int(on): m.do(f"key:{KEY_T}:6,wait:4")
    return m.do("sync," + pk(b["teachMode"]))[0] == int(on)
def teach_frames(m, b, drv, frames, on_tick=None):
    f = 0
    while f < frames:
        d = senses(m, b); a = cu.teacher(d["senses"][:20]); m.do(drv.emit(a)); f += 32 if a in (cu.BUILDL, cu.BUILDR) else cu.TICK
        if on_tick: on_tick(m, f)
    if drv.held: m.do(f"release:{drv.held}"); drv.held = 0
import random as _random
_CH = _random.Random(20260911); CHATTER = [_CH.choice((1, 2, 5, 3, 0, 4)) for _ in range(4000)]
def chatter_frames(m, b, drv, frames, on_tick=None):
    f = 0; t = 0
    while f < frames:
        m.do(drv.emit(CHATTER[t])); f += cu.TICK; t += 1
        if on_tick: on_tick(m, f)
    if drv.held: m.do(f"release:{drv.held}"); drv.held = 0

def drain(m, b, saved_slot, log, teaching=True, batches=None):
    """the hardened handshake, at the BRAIN02.5 entry size: read the unread lessons, acknowledge the exact
    range with its checksum, and replay them over the saved slot with the reference"""
    LS = ref.LESSON_SIZE
    if teaching: m.do(f"poke:{b['teachMode']:X}:00,wait:2")
    accepted = False; recs = []; total = 0; st = ring_state(m, b); attempt = 0
    for attempt in range(4):
        st = ring_state(m, b); cap = st["cap"]; recs = []
        for sq in range(st["read"], st["write"]):
            base = b["lessonData"] + (sq % cap) * LS
            recs.append(bytes(m.do("".join(f"peek:{base + i:X}," for i in range(LS)))))
        total = sum(sum(r) for r in recs) & 0xffff
        # The machine services lessonAckRequest from its main loop, so the request needs frames, not one
        # frame. This used to be wait:2 and that was too few: on a build where the clone can be crouched
        # when the session ends the main loop runs long enough that the request was still sitting there
        # unread, and the gate scored a refusal the machine had never made - status $80 with no error bit,
        # the sums in agreement, and read and drains simply untouched. Six frames, the same number the
        # golden and migration gates needed for the same reason, and a retry while it is still pending.
        m.do(po(b["lessonAckSeq"], w16(st["write"])) + po(b["lessonAckSum"], w16(total)) + f"poke:{b['lessonAckRequest']:X}:01,wait:6")
        st2 = ring_state(m, b)
        pending = m.do(pk(b["lessonAckRequest"]))[0]
        accepted = (st2["status"] & 0x80) != 0 and st2["read"] == st["write"] and st2["drains"] == st["drains"] + 1 and (st2["status"] & 0x0e) == 0
        if not accepted:
            print(f"       acknowledgement not accepted on attempt {attempt + 1}: asked {st['read']}..{st['write']} sum ${total:04X};"
                  f" status ${st2['status']:02X}, read {st2['read']} (wanted {st['write']}),"
                  f" drains {st2['drains']} (wanted {st['drains'] + 1}), machine's own sum"
                  f" ${(st['cumWrite'] - st['cumRead']) & 0xffff:04X}, request byte ${pending:02X}"
                  f" ({'still pending' if pending else 'consumed'})")
        # retry on a stale range, and on a request the machine has not got to yet
        if accepted or not ((st2["status"] & 0x02) or pending): break
    if teaching: m.do(f"poke:{b['teachMode']:X}:01")
    p = ref.parse_slot(saved_slot); W = [row[:] for row in p["weights"]]; edu = p["education"]; entries = ref.table_T1()
    divergent = 0
    for r in recs:
        x, t_abs, _pred = ref.unpack_lesson(r)
        z = ref.flags(entries, x); t = ref.to_relative(t_abs, ref.h_of(x[:20])) if b.vocab else t_abs
        _, took = ref.learn(W, z, t)
        if not took: divergent += 1
        edu += 1
    machine = slot(m, b); pm = ref.parse_slot(machine)
    same = pm["weights"] == W and pm["education"] == edu
    log.append(dict(drained=len(recs), seq_from=st["read"], seq_to=st["write"], sum=total, accepted=accepted, attempts=attempt + 1, replay_took_all=(divergent == 0),
                    weights_equal=(pm["weights"] == W), education_machine=pm["education"], education_replay=edu,
                    hash_machine=ref.brain_hash(machine), hash_replay=ref.brain_hash(ref.slot_bytes(pm["kind"], pm["vocabulary"], W, edu, retina_id=pm["retina_id"]))))
    good = accepted and same and divergent == 0
    if good and batches is not None: batches.append(recs)
    return (machine if good else saved_slot), good

# --------------------------------------------------------------------------------- the teach gate
STAIRS_C33 = "wait:300,joy:8:{},wait:20,".format((8 * 33 - 60 - 184) // 2) + "".join("joy:18:6,wait:20,joy:17:6,wait:30," for _ in range(5)) + "wait:10,hold:1,wait:50,release:1,wait:10,"

# The teach gate replays BRAIN02's own E5 episode so the two can be compared, and that episode's scripted
# teacher is a hand-written rule over the twenty senses that was written for the clone standing at X 120.
# From the BRAIN02.5 study spawn at X 72 it walks him into the staircase and then returns IDLE, because
# its "a two-high wall and nothing buildable" case has no answer there. That is a limit of the scripted
# teacher, not of the build: during teaching the brain does not drive at all, and the teacher sees only
# the twenty senses BRAIN02 also gave it. So this gate places the clone where that episode places him.
# The study spawn is exercised by the blank gate, the key gate and the gauntlet.
def at_b02_spawn(b): return po(b["cloneX"], w16(120)) + po(b["cloneNextX"], w16(120)) + "wait:2,"

def follow_teacher(s):
    """The simplest thing a person teaches a blank Tony first: come to me. A function of the twenty senses
    only, in absolute actions, so the machine does the relative translation itself. It is deliberately not
    the curriculum's builder rule: this gate is about the teaching machinery, not about any policy."""
    dx, dy, fac, grd, air, lad = s[1], s[2], s[3], s[4], s[5], s[6]
    wF, wH, lH = s[9], s[10], s[12]
    if air: return cu.IDLE
    if lad: return cu.UP if dy > 0 else (cu.DOWN if dy < 0 else cu.IDLE)
    if lH and dy > 0: return cu.UP
    toward = cu.RIGHT if dx > 0 else cu.LEFT if dx < 0 else (cu.RIGHT if fac else cu.LEFT)
    if abs(dx) <= 1: return cu.IDLE
    if wF and not wH: return cu.JUMPR if toward == cu.RIGHT else cu.JUMPL
    return toward

def follow_frames(m, b, drv, frames):
    f = 0
    while f < frames:
        d = senses(m, b); a = follow_teacher(d["senses"][:20]); m.do(drv.emit(a)); f += cu.TICK
    if drv.held: m.do(f"release:{drv.held}"); drv.held = 0

def gate_teach(b, outdir):
    """teaching end to end, with the key doing the toggling: a blank Tony, the mode on, lessons recorded
    and applied, the behaviour changed, the brain saved and reloaded byte for byte on a fresh boot, and an
    untouched build that has not learned it. The taught behaviour is 'come to me', because it depends on
    no particular terrain; what a person can teach about terrain is the gauntlet's question, not this
    gate's."""
    global ok
    os.makedirs(outdir, exist_ok=True)
    print(f"{b.name}: teaching end to end")
    ALONE = 700
    SETUP = "wait:300,joy:8:90,wait:40,"                      # the player walks to the right of the room
    m = Machine(b); m.do(SETUP + "wait:1")
    st0 = ring_state(m, b); s0 = slot(m, b); d0 = senses(m, b)
    check(st0["education"] == 0 and set(ref.parse_slot(s0)["weights"][0]) == {0}, f"he boots blank: education {st0['education']}, every weight zero")
    check(m.do("sync," + pk(b["teachMode"]))[0] == 0, "and teaching is off until the key says otherwise")
    check(teach_on(m, b, True), "the key turns teaching on, and only the key")
    story = []; reached = None; saved = None; drv = cu.PortDriver(m)
    for k in range(1, 6):
        follow_frames(m, b, drv, 240)
        st = ring_state(m, b); saved = slot(m, b)
        # try it alone, on a machine that has just booted, so the trial inherits no progress of the teacher's
        m2 = Machine(b); m2.do(SETUP + po(b["brainMarker"], saved) + f"wait:{ALONE}"); a = senses(m2, b); m2.close()
        came = a["cx"] > d0["cx"] + 120 and abs(a["px"] - a["cx"]) < 40
        story.append(dict(session=k, education=st["education"], recorded=st["write"], not_paired=st["not_paired"], alone_x=a["cx"], alone_y=a["cy"], player_x=a["px"], came=came))
        print(f"       session {k}: {st['education']} lessons in all; alone after it he ends at X {a['cx']} with Tony at X {a['px']}" + ("  <- he came" if came else ""))
        if came and reached is None: reached = (k, st["education"]); break
        m.do("joy:4:60,wait:20,joy:8:60,wait:20")              # the player moves, so there is something new to teach
    m.close()
    check(st["education"] > 0 and set(ref.parse_slot(saved)["weights"][0]) != {0}, f"lessons change the weights: education {st['education']}, {st['write']} recorded, {st['not_paired']} pairings dropped")
    check(reached is not None, (f"taught from nothing, he comes to Tony on his own after {reached[0]} session(s) and {reached[1]} lessons" if reached else "he did not come to Tony in five sessions"))
    if saved: open(os.path.join(outdir, f"taught-{b.name}.b025"), "wb").write(saved)
    m3 = Machine(b); m3.do(SETUP + po(b["brainMarker"], saved) + f"wait:{ALONE}")
    a3 = senses(m3, b); st3 = ring_state(m3, b); back = slot(m3, b); m3.close()
    check(back == saved and st3["education"] == ref.parse_slot(saved)["education"],
          f"the slot reads back byte for byte after the reload, hash {ref.brain_hash(saved)[:16]}, education {st3['education']}")
    check(a3["cx"] > d0["cx"] + 120, f"and the saved brain on a fresh boot does it again: X {d0['cx']} -> {a3['cx']}, Tony at {a3['px']}")
    m4 = Machine(b); m4.do(SETUP + f"wait:{ALONE}"); a4 = senses(m4, b); m4.close()
    check(a4["cx"] == d0["cx"], f"an untouched build has not learned it: he is still at X {a4['cx']}")
    json.dump(dict(name=b.name, taught="come to me", sessions=story, sessions_to_come=reached, alone_frames=ALONE,
                   hash=ref.brain_hash(saved) if saved else None, education=ref.parse_slot(saved)["education"] if saved else 0),
              open(os.path.join(outdir, f"teach-{b.name}.json"), "w"), indent=1)
    return ok

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "teach":
    sys.exit(0 if gate_teach(Build(sys.argv[2]), OUT) else 1)

# --------------------------------------------------------------------------------- the drain gate
SETUP_WALK = "wait:300,joy:8:60,wait:20,"

def gate_drain(b, outdir):
    """ring cycles at a lowered capacity, replay equality after every drain, the full-ring pause, refused
    acknowledgements, and the split run against the uninterrupted one"""
    global ok
    os.makedirs(outdir, exist_ok=True); n = b.n
    W, KIND, TEACH, CAP = b["brainWeights"], b["brainKind"], b["teachMode"], b["lessonCap"]
    print(f"{b.name}: save, drain and reuse")
    log = []; saved = None; wraps = 0; total = 0; all_ok = True; last_write = 0; st = None
    for k in range(2):
        m = Machine(b); m.do(SETUP_WALK)
        if saved: m.do(po(b["brainMarker"], saved))
        m.do(po(CAP, w16(40)) + f"poke:{KIND:X}:01,poke:{TEACH:X}:01,wait:1")
        if saved is None: saved = slot(m, b)
        drv = cu.PortDriver(m)
        def on_tick(mm, f):
            nonlocal saved, all_ok, wraps, last_write
            s2 = ring_state(mm, b)
            if s2["write"] // 40 > last_write // 40: wraps += 1
            last_write = s2["write"]
            if s2["write"] - s2["read"] >= 30:
                if drv.held: mm.do(f"release:{drv.held}"); drv.held = 0
                saved, good = drain(mm, b, saved, log); all_ok &= good
        chatter_frames(m, b, drv, 1200, on_tick)
        m.do(f"poke:{TEACH:X}:00,wait:1"); st = ring_state(m, b)
        if st["write"] > st["read"]: saved, good = drain(m, b, saved, log); all_ok &= good
        total += st["write"]; last_write = 0; m.close()
    check(all_ok and len(log) >= 6 and wraps >= 3, f"{len(log)} drains over 2 sessions, {total} lessons, {wraps} ring wraps at capacity 40: every acknowledgement accepted and every replay equal to the machine byte for byte ({st['not_paired']} pairings dropped)")
    check(all(l["hash_machine"] == l["hash_replay"] for l in log), "the behavioural hash of the machine's slot equals the replay's after every drain")
    edu = [l["education_machine"] for l in log]
    check(all(a <= c for a, c in zip(edu, edu[1:])) and edu[-1] == sum(l["drained"] for l in log), f"the education count runs across sessions and drains: {edu[-1]} applied, {sum(l['drained'] for l in log)} drained")
    # the full ring pauses learning, and a wrong or stale acknowledgement reclaims nothing
    m = Machine(b); m.do(SETUP_WALK + po(CAP, w16(12)) + f"poke:{KIND:X}:01,poke:{TEACH:X}:01,wait:1"); saved0 = slot(m, b)
    drv = cu.PortDriver(m); chatter_frames(m, b, drv, 140); st = ring_state(m, b)
    v = m.do("sync," + pk(b["cloneFlashColour"]))
    check(st["write"] == 12 and st["write"] - st["read"] == 12 and (st["status"] & 1) and st["education"] == 12,
          f"capacity 12 with no drain: {st['write']} recorded, the ring full (status ${st['status']:02x}), education {st['education']}: learning paused rather than applied unrecorded; last flash colour {v[0]} (2 is red)")
    m.do(po(b["lessonAckSeq"], w16(st["write"])) + po(b["lessonAckSum"], w16((st["cumWrite"] - st["cumRead"] + 1) & 0xffff)) + f"poke:{b['lessonAckRequest']:X}:01,wait:2"); bad1 = ring_state(m, b)
    m.do(po(b["lessonAckSeq"], w16(st["write"] - 1)) + po(b["lessonAckSum"], w16((st["cumWrite"] - st["cumRead"]) & 0xffff)) + f"poke:{b['lessonAckRequest']:X}:01,wait:2"); bad2 = ring_state(m, b)
    check(bad1["read"] == st["read"] and (bad1["status"] & 4) and bad2["read"] == st["read"] and (bad2["status"] & 2),
          f"a wrong checksum is refused (status ${bad1['status']:02x}) and a stale range is refused (status ${bad2['status']:02x}); nothing reclaimed")
    saved0, good = drain(m, b, saved0, log); chatter_frames(m, b, drv, 30); st2 = ring_state(m, b)
    check(good and st2["write"] > 12 and not (st2["status"] & 1), f"after the right acknowledgement learning resumes: {st2['write']} lessons, status ${st2['status']:02x}")
    m.close()
    # the equivalence: the split run's own recorded stream, replayed uninterrupted by the machine and by the reference
    m = Machine(b); m.do(SETUP_WALK + po(CAP, w16(40)) + f"poke:{KIND:X}:01,poke:{TEACH:X}:01,wait:1")
    drv = cu.PortDriver(m); saved_e = slot(m, b); dlog = []; batches = []
    def on_tick2(mm, f):
        nonlocal saved_e
        s2 = ring_state(mm, b)
        if s2["write"] >= on_tick2.threshold:
            on_tick2.threshold += 30
            if drv.held: mm.do(f"release:{drv.held}"); drv.held = 0
            saved_e, g = drain(mm, b, saved_e, dlog, batches=batches)
    on_tick2.threshold = 30
    chatter_frames(m, b, drv, 720, on_tick2); m.do(f"poke:{TEACH:X}:00,wait:1")
    saved_e, good = drain(m, b, saved_e, dlog, batches=batches); st_split = ring_state(m, b); final_split = slot(m, b); m.close()
    seq = [r for batch in batches for r in batch]
    m = Machine(b); m.do("wait:300," + f"poke:{KIND:X}:00,poke:{b['brainTestMode']:X}:00,")
    for r in seq:
        x, t_abs, _ = ref.unpack_lesson(r)
        m.do(po(b["brainTestIn"], bytes(v & 15 for v in x)) + f"poke:{b['brainLearnTestT']:X}:{t_abs:02X},poke:{b['brainLearnRun']:X}:01,wait:{WAIT}")
    m.do(f"poke:{KIND:X}:01,wait:1"); final_machine = slot(m, b); m.close()
    pm, ps = ref.parse_slot(final_machine), ref.parse_slot(final_split)
    entries = ref.table_T1(); Wr = [[0] * n for _ in range(10)]; took_all = True
    for r in seq:
        x, t_abs, _ = ref.unpack_lesson(r)
        t = ref.to_relative(t_abs, ref.h_of(x[:20])) if b.vocab else t_abs
        _, took = ref.learn(Wr, ref.flags(entries, x), t); took_all &= took
    same_m = pm["weights"] == ps["weights"] and pm["education"] == ps["education"]
    check(len(seq) == st_split["write"] and same_m and Wr == ps["weights"] and took_all and ref.brain_hash(final_machine) == ref.brain_hash(final_split),
          f"the split run's {len(seq)} recorded lessons in {len(batches)} drained batches, replayed uninterrupted by the machine itself and by the reference, give the split run's brain byte for byte: education {pm['education']} = {ps['education']}, hash {ref.brain_hash(final_split)[:16]}; {st_split['not_paired']} pairings dropped")
    json.dump(dict(cycles=log, equivalence=dict(split_lessons=st_split["write"], batches=len(batches), hash_split=ref.brain_hash(final_split),
                                                hash_machine_replay=ref.brain_hash(final_machine), reference_equal=(Wr == ps["weights"]),
                                                education=ps["education"], not_paired=st_split["not_paired"])),
              open(os.path.join(outdir, f"drain-{b.name}.json"), "w"), indent=1)
    return ok

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "drain": sys.exit(0 if gate_drain(Build(sys.argv[2]), OUT) else 1)

# ------------------------------------------------------------------------------ the resources gate
def gate_resources(b, outdir):
    """every number the pre-registration asks for, exactly: sizes, addresses, the RAM map, how many inputs
    are set at once, cycles for the think, the lesson, the terrain probe, the shadow and the drain, and the
    raster over a real teaching episode"""
    global ok
    os.makedirs(outdir, exist_ok=True); n = b.n; S = b.sym
    labels = sorted((a, nm) for nm, a in S.items() if 0x0800 <= a < 0xa000)
    def size_of(name):
        a = S[name]; nxt = [x for x, nm in labels if x > a]; return (nxt[0] - a) if nxt else None
    prg = open(b.prg, "rb").read(); load = prg[0] | prg[1] << 8; off = S["brainMarker"] - load + 2
    pad = 0
    while off - pad - 1 >= 0 and prg[off - pad - 1] == 0: pad += 1
    cap = 180
    r = dict(name=b.name, prg_size=b.size, sha256=b.sha, inputs=n, senses=b.senses, terrain_quantities=len(ref.TERRAIN),
             retina_id=b.retina, vocabulary=b.vocab, slot_bytes=S["BRAIN_BLOCK_SIZE"], header_bytes=24, weight_bytes=10 * n, mood_bytes=10,
             padding_before_marker_upper_bound=pad, retina_table_bytes=1 + 3 * n, flag_vector_ram=n, active_list_ram=n, value_ram=29 + len(ref.TERRAIN),
             lesson_entry_bytes=ref.LESSON_SIZE, lesson_ring_capacity=cap, lesson_ring_bytes=32 + ref.LESSON_SIZE * cap,
             shadow_ram=10 * n, shadow_at=S["TEACH_SHADOW"], ring_at=S["LESSON_BLOCK"], code_end=S["musicData"] - 1,
             headroom_below_shadow=S["TEACH_SHADOW"] - S["musicData"], headroom_above_ring=0xa000 - (S["LESSON_BLOCK"] + 32 + ref.LESSON_SIZE * cap),
             code_bytes={k: size_of(k) for k in ("brainRetina", "brainForward", "brainLearn", "bodyThink", "senseTerrain", "tRowSet", "tAt", "teachKey", "testInputs", "brainCheck", "teachLesson", "lessonAck", "copyWeights", "teachShadowSave", "teachShadowRestore", "lessonInit")},
             accumulator_bound=ref.bound(n))
    # a real episode: a taught brain, teaching on, chatter, a drain
    m = Machine(b); m.do(SETUP_WALK + f"poke:{S['brainKind']:X}:01,poke:{S['teachMode']:X}:01,wait:1")
    saved = slot(m, b); drv = cu.PortDriver(m); chatter_frames(m, b, drv, 600)
    m.do(f"poke:{S['shadowRequest']:X}:01,wait:6")
    for _ in range(30): m.do(f"poke:{S['terrainTestRun']:X}:01,wait:2")      # the probe alone, interrupts held off
    log = []; saved, good = drain(m, b, saved, log)
    v = m.do("sync," + pk(S["profThink"], 4) + pk(S["profLesson"], 4) + pk(S["profShadow"], 4) + pk(S["profDrain"], 4) + pk(S["profTerrain"], 4) + pk(S["profTerrainPure"], 4) +
             pk(S["bodyRasterMax"]) + pk(S["bodyOverruns"]) + pk(S["gapMin"], 2) + pk(S["gapMax"], 2) + pk(S["gapSum"], 4) + pk(S["gapCount"], 2) + pk(S["brainThinks"], 2) + pk(S["brainActiveCount"]))
    m.close()
    r.update(think_cycles_last=v[0] | v[1] << 8, think_cycles_max=v[2] | v[3] << 8, lesson_cycles_last=v[4] | v[5] << 8, lesson_cycles_max=v[6] | v[7] << 8,
             shadow_cycles_last=v[8] | v[9] << 8, shadow_cycles_max=v[10] | v[11] << 8, drain_cycles_last=v[12] | v[13] << 8, drain_cycles_max=v[14] | v[15] << 8,
             terrain_cycles_last=v[16] | v[17] << 8, terrain_cycles_max=v[18] | v[19] << 8,
             terrain_pure_last=v[20] | v[21] << 8, terrain_pure_max=v[22] | v[23] << 8, raster_max=v[24], overruns=v[25])
    gmin, gmax = s16(v[26], v[27]), s16(v[28], v[29]); gsum = v[30] | v[31] << 8 | v[32] << 16 | v[33] << 24; gcount = v[34] | v[35] << 8
    r.update(gap_min=gmin, gap_max=gmax, gap_mean=(gsum / gcount if gcount else None), gap_count=gcount, thinks=v[36] | v[37] << 8, drain_ok=good)
    # the work itself, interrupts held off, through the hooks on recorded blocks under real terrain
    blocks, D = blocks_all(); rnd = __import__("random").Random(3)
    test = [list(x) + [rnd.randint(0, ref.CAP) for _ in ref.TERRAIN] for x in sorted(D["s474"])[::12]]
    s = "wait:300," + f"poke:{S['brainTestMode']:X}:00," + po(S["brainWeights"], bytes(rnd.randint(0, 255) for _ in range(10 * n)))
    for x in test: s += po(S["brainTestIn"], xb(x)) + f"poke:{S['brainTestRun']:X}:01,wait:{WAIT},sync," + pk(S["profThinkPure"], 2) + pk(S["brainActiveCount"])
    for x in test[:20]: s += po(S["brainTestIn"], xb(x)) + f"poke:{S['brainLearnTestT']:X}:09,poke:{S['brainLearnRun']:X}:01,wait:{WAIT},sync," + pk(S["profLessonPure"], 2)
    v, out = b.run(s)
    tp = [v[3 * k] | v[3 * k + 1] << 8 for k in range(len(test))]; act = [v[3 * k + 2] for k in range(len(test))]
    lp = [v[3 * len(test) + 2 * k] | v[3 * len(test) + 2 * k + 1] << 8 for k in range(20)]
    r.update(think_pure_min=min(tp), think_pure_mean=sum(tp) / len(tp), think_pure_max=max(tp),
             lesson_pure_min=min(lp), lesson_pure_mean=sum(lp) / len(lp), lesson_pure_max=max(lp),
             active_min=min(act), active_mean=sum(act) / len(act), active_max=max(act), frame_cycles=19656)
    json.dump(r, open(os.path.join(outdir, f"resources-{b.name}.json"), "w"), indent=1)
    for k, v2 in r.items():
        if k != "code_bytes": print(f"  {k}: {v2}")
    print("  code bytes:", r["code_bytes"])
    check(r["headroom_below_shadow"] > 0 and r["headroom_above_ring"] >= 0, f"the code ends {r['headroom_below_shadow']} bytes below the shadow and the ring ends {r['headroom_above_ring']} bytes below $a000")
    check(r["raster_max"] <= 230 and r["overruns"] == 0, f"raster maximum {r['raster_max']} (limit 230), overruns {r['overruns']}")
    fits = r["think_pure_max"] < 19656 and r["lesson_pure_max"] < 19656
    r["fits_one_frame"] = fits
    print(f"  {'ok   ' if fits else 'NOTE '}BRAIN02's one-frame bound: the think {r['think_pure_max']} cycles at most, the lesson {r['lesson_pure_max']}, against 19656."
          + ("" if fits else " At eighty inputs neither fits inside one frame of main-loop time any longer. This is reported, not gated: the pre-registration asks for the exact numbers, and the bound that matters is the one below."))
    check(r["terrain_pure_max"] < 19656, f"the terrain probe's own work is at most {r['terrain_pure_max']} cycles a frame, {100 * r['terrain_pure_max'] / 19656:.1f}% of a frame; its wall-clock span on the live path, raster work included, reaches {r['terrain_cycles_max']}")
    check(r["think_cycles_max"] < 4 * 19656, f"the think finishes inside its own four-frame period: {r['think_cycles_max']} cycles of wall-clock at most against {4 * 19656}")
    check(good, "the drain in the episode accepted and replayed equal")
    return ok

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "resources": sys.exit(0 if gate_resources(Build(sys.argv[2]), OUT) else 1)

# --------------------------------------------------------- the world materials, for the descriptor
def _world_block(b, S):
    """Where the screen-code-to-semantics table is, what its bytes mean, and why the LIVE one is the
    only one a host may trust. The table is not moved for the descriptor's benefit; this only says
    where it already is. The live buffer is read from the machine so the numbers are measured."""
    MAXC = S["MAX_BG_CHARS"]
    src = os.path.join(ROOT, "src/level-custom/chamber-materials.bin")
    src_bytes = open(src, "rb").read() if os.path.exists(src) else b""
    live = {}
    with tempfile.TemporaryDirectory() as d:
        for chamber, direction in ((0, None), (1, 1)):
            pre = "" if direction is None else po(S["roomChangeDirection"], [direction]) + po(S["roomChange"], [chamber]) + "wait:40,"
            b.run(f"wait:400,{pre}sync,dump:{S['roomMaterialsBuffer']:X}:100:{d}/m{chamber}.bin,"
                  f"dump:{S['roomCharsDecodingBuffer']:X}:100:{d}/c{chamber}.bin,")
            raw = open(f"{d}/m{chamber}.bin", "rb").read()[:MAXC]
            live[chamber] = dict(sha256=hashlib.sha256(raw).hexdigest(),
                                 histogram={f"0x{k:02X}": sum(1 for x in raw if x == k) for k in sorted(set(raw))})
    return dict(
        note="the host captures the screen matrix; this says how to turn a drawn screen code into terrain"
             " semantics. Nothing here was moved or renamed for the descriptor - these are the addresses the"
             " engine already uses.",
        materials_live=dict(
            address=S["roomMaterialsBuffer"], length=MAXC, stride=1,
            index="the DRAWN screen code, exactly as it appears in the screen matrix after translateRoom",
            rebuilt="per room, by decodeRoom, and then patched at run time",
            read_this_one="yes - this is the table the engine's own collision code reads",
            measured=live,
            why_not_derivable="the source table cannot be remapped into this one by the host: decodeRoom keys"
                              " it by the room's used-character list, and the build demo then patches the"
                              " codes it owns. On this build four entries differ that way - drawn codes 0x50"
                              " to 0x53, the four cells of a brick the player or the clone has laid, which are"
                              " WALL in the live table and which no original character code maps to at all."),
        materials_source=dict(
            address=S["materials"], length=len(src_bytes),
            index="the ORIGINAL character code, before decodeRoom remaps it",
            file="src/level-custom/chamber-materials.bin",
            sha256=hashlib.sha256(src_bytes).hexdigest(),
            stable="yes - this one is part of the load image, so the hash is stable for the build"),
        char_decode=dict(address=S["roomCharsDecodingBuffer"], length=256,
                         meaning="original character code -> drawn screen code; rebuilt per room by decodeRoom"),
        row_table=dict(address=S["chamberLines"], rows=25,
                       layout="lohifill: 25 low bytes at the address, then 25 high bytes",
                       meaning="the screen address of the first cell of each character row"),
        semantics=dict(
            kind="a bitfield, one byte per character",
            bits={f"0x{S['BG_CLSN_WALL']:02X}": "WALL - solid; the box and the feet both collide",
                  f"0x{S['BG_CLSN_LADDER']:02X}": "LADDER - climbable",
                  f"0x{S['BG_CLSN_KILLING']:02X}": "KILLING - deadly on contact",
                  f"0x{S['BG_CLSN_COLLECTIBLE']:02X}": "COLLECTIBLE - a pickup, not terrain"},
            none=f"0x{S['BG_CLSN_NONE']:02X} - no material; decoration, and NOT terrain",
            masks={f"0x{S['BG_CLSN_FLOOR_MASK']:02X}": "FLOOR_MASK - what counts underfoot",
                   f"0x{S['BG_CLSN_FAR_MASK']:02X}": "FAR_MASK - wall or ladder, for the far column",
                   f"0x{S['BG_CLSN_BOX_MASK']:02X}": "BOX_MASK - what the body box reports",
                   f"0x{S['BG_CLSN_BOX_NK_MASK']:02X}": "BOX_NK_MASK - the same without the killing bit",
                   f"0x{S['BG_CLSN_OBJ_MASK']:02X}": "OBJ_MASK - object rather than terrain"}),
        in_this_level=dict(
            values_present="only 0x00, 0x01 and 0x02 occur in the live table on this build",
            deadly="KILLING (0x04) is in the schema and in the source table, but none of the characters"
                   " carrying it are in this room's used-character list, so no cell of this level is deadly",
            collectible="COLLECTIBLE (0x40) likewise does not occur: the candle is drawn but this build's"
                        " rooms carry no static objects, so the object-materials pass has nothing to patch",
            mural="the seeded back wall's bricks are material 0x00 - verified on the machine, not assumed -"
                  " so the terrain probe, the senses and the brain cannot see any of them",
            chambers="both chambers produce the same live table, because they share one used-character list"))

# --------------------------------------------------------------------------- the workbench descriptor
def descriptor(b, commit):
    """a machine-readable descriptor of the BRAIN02.5 study build, in the shape BRAIN02's descriptor has,
    with a schema identifier of its own so neither can be mistaken for the other"""
    S = b.sym; n = b.n; entries = ref.table_T1()
    d = dict(
        schema="tony-brain025-descriptor/1", filename=os.path.basename(b.prg), sha256=b.sha, prg_size=b.size, engine_commit=commit,
        study="BRAIN02.5: BRAIN02's learner with seven local terrain quantities added to the sensed state and sixteen inputs appended at 64..79",
        derived_from=dict(brain="BRAIN02 Candidate A", prg="tony-b02-a.prg", sha256="ae6ce5244478532c5ec581c9e24a30bea0743c68b2dd7cc7ff9f3017bc3e594d", engine_commit="3e12f0e19d69f9d37e1b95beafa9aa3368511cd0"),
        load_address=0x0801, machine="Commodore 64 PAL; Minimal64 and VICE; a plain PRG",
        brain=dict(marker="BRAIN025", marker_address=S["brainMarker"], slot_bytes=S["BRAIN_BLOCK_SIZE"], layout=3, rule_version=2, inputs=n, outputs=10, vocabulary=b.vocab, retina_id=b.retina,
                   note="layout 3 and the marker BRAIN025 make a BRAIN02 slot malformed here and a BRAIN02.5 slot malformed there; neither loads into the other",
                   header=dict(kind=S["brainKind"], layout=S["brainLayout"], inputs=S["brainInputCount"], hidden=S["brainHiddenCount"], outputs=S["brainOutputCount"], period=S["brainPeriod"],
                               lineage=S["brainLineage"], rule=S["brainRule"], vocabulary=S["brainVocab"], retina_id=S["brainRetinaId"], education_count=S["brainEducation"], education_bytes=2),
                   weights=S["brainWeights"], weight_bytes=10 * n, weight_layout="row o at weights + o * inputs, one signed byte per input (two's complement)", mood=S["brainMood"], mood_bytes=10,
                   default_kind=1, blank_behaviour="zero weights give every accumulator the same value; the existing first-largest tie picks output 0, IDLE. There is no follow rule behind the brain in this build.",
                   hash_domains=dict(behavioural="bytes 8..12, 16..17 and the weights, in slot order, SHA-256", provenance="lineage, rule version, education count", timing_render="period, mood")),
        retina=dict(id=b.retina, name="T1", table_address=S["retinaTable"], table_bytes=1 + 3 * n, table_layout="count, then ops[n], operands a[n], k-or-b[n]",
                    inputs_0_63="R1b's, entry for entry, unchanged in meaning and in order", inputs_64_79="the sixteen appended thresholds over the seven terrain quantities",
                    flag_names=ref.flag_names(entries), pseudo_senses={20 + i: nm for i, nm in enumerate(ref.PSEUDO)},
                    terrain_values={29 + i: nm for i, nm in enumerate(ref.TERRAIN)},
                    terrain_frame="the toward frame: h = sign(refDx), or the clone's facing when refDx is zero, from the same published block the retina reads",
                    flag_vector=S["brainFlags"], flag_vector_bytes=n, active_list=S["brainActive"], active_count=S["brainActiveCount"], values=S["brainVals"], values_bytes=29 + len(ref.TERRAIN)),
        senses=dict(address=S["cloneSenses"], count=b.senses, frame=S["cloneSensesFrame"],
                    layout="one byte per sense, the signed nibble in the low four bits (8..15 negative); senses 0..19 are BRAIN02's, unchanged",
                    terrain={20 + i: nm for i, nm in enumerate(ref.TERRAIN)},
                    terrain_meanings=dict(tSafeRun="columns toward the reference with support at his own floor row, before the first without",
                                          tGapW="from that first unsupported column, how many in a row lack support",
                                          tFarRun="how many supported columns in a row the far side of that gap offers",
                                          tObstH="the height in rows of the first column toward him blocked at his foot row",
                                          tObstTop="the clear rows above that block's top", tHead="the clear rows above his own head, over both his columns",
                                          tBackRoom="how many columns away from the reference are clear at his foot row"),
                    terrain_cap=ref.CAP, terrain_probe=S["senseTerrain"]),
        live=dict(predicted_output=S["brainOutput"], resolved_action=S["brainAction"], h_right=S["brainH"], taught_action=S["brainTaught"], taught_raw=S["brainTaughtRaw"],
                  predicted_at_lesson=S["brainPredicted"], lesson_taken=S["brainLearned"], kind_now=S["brainKindNow"], think_count=S["brainThinks"], accumulators=S["brainAcc"],
                  score_gap=S["brainGap"], think_input=S["brainIn"], clone_x=S["cloneX"], clone_y=S["cloneY"], clone_state=S["cloneState"],
                  player_x=S["physPlayerX"], player_y=S["physPlayerY"], player_state=S["physPlayerState"], bricks=S["buildCount"],
                  flash_frames=S["cloneFlash"], flash_colour=S["cloneFlashColour"],
                  flash_colours=({5: "green: a lesson was accepted", 2: "red: a lesson was refused, the ring is full"} if "COL_CLONE" in S
                                 else {1: "white: a lesson", 2: "red: a lesson refused, the ring is full"}),
                  teach_mode=S["teachMode"], teach_key="T (keyboard matrix row 2, column bit 6); the toggle acts on the press edge",
                  teach_key_edges=S["teachKeyEdges"], teach_key_state=S["teachKeyWas"],
                  shadow_request=S["shadowRequest"], shadow_restore_request=S["shadowRestoreRequest"], shadow_valid=S["shadowValid"], shadow_at=S["TEACH_SHADOW"], shadow_bytes=10 * n,
                  raster_max=S["bodyRasterMax"], overruns=S.get("bodyOverruns"), frames=S["bodyFrames"], spawn=dict(x=72, columns=[7, 8], note="the study spawn, by the far left pillar, clear of the ladder at columns 33-34")),
        visual=(dict(revision="vis1", scope="presentation only",
                     clone_sprites=[5, 6], clone_colour_registers=[0xD02C, 0xD02D], backdrop_sprite=7,
                     human_tony="untouched: sprites 0, 1, 3 and 4 stay light grey (15)",
                     palette=dict(identity=1, teaching=3, accepted=5, refused=2, dropout=0),
                     grammar=["a lesson event outranks everything: the six-frame flash is green when one was accepted and red when one was refused",
                              "teaching: a slow cyan pulse over white, six frames of every sixteen",
                              "otherwise: white, dropping out to black for one frame in thirty-two",
                              "leaving teaching returns to white and the dropout with nothing left over"],
                     determinism="a pure function of bodyFrames, teachMode and the existing flash counter; no new mutable state, no random draw, and only the clone's own two sprite colour registers are written, so nothing here reaches the senses, the brain, the body, the lesson record or a replay")
                if "COL_CLONE" in S else None),
        profiler=dict(think=S["profThink"], think_max=S["profThinkMax"], lesson=S["profLesson"], lesson_max=S["profLessonMax"], shadow=S["profShadow"], shadow_max=S["profShadowMax"],
                      drain=S["profDrain"], drain_max=S["profDrainMax"], think_pure=S["profThinkPure"], think_pure_max=S["profThinkPureMax"],
                      lesson_pure=S["profLessonPure"], lesson_pure_max=S["profLessonPureMax"], terrain=S["profTerrain"], terrain_max=S["profTerrainMax"],
                      terrain_pure=S["profTerrainPure"], terrain_pure_max=S["profTerrainPureMax"], terrain_test_run=S["terrainTestRun"],
                      unit="CPU cycles, 16-bit; the live counts include whatever interrupt work fell inside them, the pure ones (hooks, interrupts held off) do not",
                      gap_min=S["gapMin"], gap_max=S["gapMax"], gap_sum=S["gapSum"], gap_count=S["gapCount"]),
        lessons=dict(marker="LESSON25", marker_address=S["lessonMarker"], version=ref.LESSON_VERSION,
                     sense_nibbles=b.senses,          # published explicitly so a host never has to infer it from the entry size
                     write_seq=S["lessonWriteSeq"], read_seq=S["lessonReadSeq"],
                     capacity=S["lessonCap"], capacity_default=180, entry_size=S["lessonSize"], entry_bytes=ref.LESSON_SIZE, status=S["lessonStatus"],
                     status_bits={0: "full, learning paused", 1: "last ack rejected: stale range", 2: "last ack rejected: bad checksum", 3: "last ack rejected: a hold in progress", 7: "last ack accepted"},
                     ack_seq=S["lessonAckSeq"], ack_sum=S["lessonAckSum"], ack_request=S["lessonAckRequest"], drains=S["lessonDrains"], cum_write=S["lessonCumWrite"], cum_read=S["lessonCumRead"], data=S["lessonData"],
                     entry_layout=f"bytes 0..{ref.LESSON_SIZE - 2}: the {b.senses} sense nibbles, nibble i in byte i/2, the low nibble for even i, so the last nibble sits alone in byte {ref.LESSON_SIZE - 2} with a zero high half; byte {ref.LESSON_SIZE - 1}: the taught absolute action in the low nibble, the predicted raw output in the high nibble",
                     slot_rule=f"the lesson with sequence s is at data + (s mod capacity) * {ref.LESSON_SIZE}; unread lessons are [read_seq, write_seq)",
                     completeness="every input, old and new, is reconstructible from the entry alone: the terrain quantities are in the block, so a replay never needs the room",
                     drain_procedure=["read read_seq, write_seq", "read the entries [read_seq, write_seq)", "sum every byte of those entries modulo 65536",
                                      "write ack_seq = write_seq, ack_sum = the sum, then ack_request = 1", "wait one frame; read status: bit 7 accepted, else bits 1..3 say why"],
                     replay="per lesson: unpack the twenty-seven nibbles, derive the eighty inputs with the retina table, translate the taught absolute action with h of the block under the relative vocabulary, apply the rule",
                     reference_implementation=dict(canonical=["tools/brain025_ref.py", "tools/brain02_ref.py"],
                                                   invocation="python3 tools/brain025_ref.py replay START.slot LESSONS.bin --out FINAL.slot [--expect MACHINE.slot] [--check-predictions]",
                                                   manifest="deliverables/brain025/replay/MANIFEST.json", document="deliverables/brain025/REPLAY.md",
                                                   note="both files together: brain025_ref.py holds the retina table, the formats and the replay; brain02_ref.py holds the rule, the forward pass, the vocabulary and the first sixty-four retina entries",
                                                   prediction_nibble="the high nibble of the last byte is the machine's mood-free prediction as a RAW output index, which under the reference-relative vocabulary is the relative one, while the low nibble is the taught action in ABSOLUTE terms. replay --check-predictions recomputes it per lesson and fails on disagreement")),
        test_hooks=dict(test_in=S["brainTestIn"], test_mode=S["brainTestMode"], test_run=S["brainTestRun"], test_flags=S["brainTestFlags"], test_acc=S["brainTestAcc"],
                        test_output=S["brainTestOutput"], test_action=S["brainTestAction"], test_h=S["brainTestH"], learn_run=S["brainLearnRun"], learn_t=S["brainLearnTestT"],
                        learn_p=S["brainLearnTestP"], learn_took=S["brainLearnTestTook"], terrain_test_run=S["terrainTestRun"],
                        note="research only: the hooks run the machine's own retina, forward pass, rule and terrain probe on supplied inputs"),
        world=_world_block(b, S),
        access=dict(observation="everything above may be read at any time; read write_seq before and after a read of the weights to know no lesson intervened",
                    research_control=dict(teach_mode="0/1, the same as the key", ack_fields="ack_seq, ack_sum, ack_request", capacity="may be lowered at boot before any lesson",
                                          slot="the whole slot may be written at boot to load a saved brain", test_hooks="research only"),
                    cognition="the terrain probe, the retina, the forward pass, the resolution, the rule and the lesson recording all run in the machine; the host never computes an input, a prediction or an action for him"),
        session_trace=dict(observe_per_frame=["frames", "teach_mode", "teach_key_edges", "clone_x", "clone_y", "clone_state", "player_x", "player_y", "predicted_output", "resolved_action", "write_seq", "flash_colour", "the seven terrain quantities"],
                           observe_per_lesson=["the new ring entry", "education_count", "the two weight rows that changed"],
                           events=["teach on/off (the key or the flag)", "drain", "brain load", "brain reset", "capacity change"],
                           derived=["lessons to competence on a course", "corrections", "aliasing (the same eighty inputs taught two actions)", "competence after reload", "how often a terrain input was the only thing that changed between two decisions"]))
    return d

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "descriptor":
    b = Build(sys.argv[2]); commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    os.makedirs(os.path.join(OUT, "workbench"), exist_ok=True)
    d = descriptor(b, commit); json.dump(d, open(os.path.join(OUT, "workbench", f"{b.name}.json"), "w"), indent=1)
    print(f"wrote deliverables/brain025/workbench/{b.name}.json ({len(json.dumps(d))} bytes of JSON)")


def gate_shadow(b, outdir):
    """The teaching shadow's restore, both ways. A restore with a valid snapshot must put the whole
    canonical brain back exactly; a restore with NO snapshot must change nothing at all. The second half
    is the guard: teachShadowRestore used to copy TEACH_SHADOW over the brain whatever was in it, and at
    $9200 the load image holds relocated music data, so a host poking shadowRestoreRequest replaced a
    trained brain with 781 nonzero bytes of tune. Unreachable from play - nothing sets the request byte -
    but the host interface could reach it."""
    global ok
    os.makedirs(outdir, exist_ok=True)
    print(f"{b.name}: the teaching shadow's restore")
    SLOT = b["lessonMarker"] - b["brainMarker"] if b["lessonMarker"] > b["brainMarker"] else 834
    def slot_of(m, tag):
        m.do(f"sync,dump:{b['brainMarker']:X}:{ref.SLOT_BYTES if hasattr(ref,'SLOT_BYTES') else 834:X}:{outdir}/shadow-{b.name}-{tag}.bin")
        return open(f"{outdir}/shadow-{b.name}-{tag}.bin", "rb").read()
    def fields(m):
        v = m.do("sync," + pk(b["brainEducation"], 2) + pk(b["lessonWriteSeq"], 2) + pk(b["lessonCumWrite"], 2)
                 + pk(b["brainKind"]) + pk(b["brainKindNow"]) + pk(b["shadowValid"]) + pk(b["shadowRestoreRequest"])
                 + pk(b["brainMood"], 10))
        return dict(education=v[0] | v[1] << 8, write_seq=v[2] | v[3] << 8, cum_write=v[4] | v[5] << 8,
                    kind=v[6], kind_now=v[7], valid=v[8], request=v[9], mood=v[10:20])
    def teach(m, n):
        m.do(po(b["teachMode"], [1]))
        for _ in range(n): m.do("hold:8"); m.do("wait:4"); m.do("release:8"); m.do("wait:2")
        m.do(po(b["teachMode"], [0])); m.do("wait:4")
    rec = {}
    # --- 1. a valid snapshot: the restore must be exact
    m = Machine(b); m.do("wait:400"); m.do(po(b["brainKind"], [1]))
    teach(m, 6); m.do(po(b["shadowRequest"], [1])); m.do("wait:8")
    snap, fsnap = slot_of(m, "snap"), fields(m)
    teach(m, 6); grown, fgrown = slot_of(m, "grown"), fields(m)
    m.do(po(b["shadowRestoreRequest"], [1])); m.do("wait:8")
    back, fback = slot_of(m, "back"), fields(m)
    m.close()
    rec["valid"] = dict(snapshot=fsnap, grown=fgrown, restored=fback,
                        snap_sha=hashlib.sha256(snap).hexdigest(), back_sha=hashlib.sha256(back).hexdigest())
    check(fsnap["valid"] == 1, f"the snapshot request takes one: shadowValid {fsnap['valid']}")
    check(grown != snap and fgrown["education"] > fsnap["education"],
          f"teaching moves the brain on: education {fsnap['education']} -> {fgrown['education']}, slot differs")
    check(back == snap, f"a VALID restore puts the whole {len(snap)}-byte slot back byte for byte "
                        f"({hashlib.sha256(snap).hexdigest()[:16]})")
    check(fback["education"] == fsnap["education"] and fback["write_seq"] == fsnap["write_seq"]
          and fback["cum_write"] == fsnap["cum_write"] and fback["kind"] == fsnap["kind"],
          f"and the counters with it: education {fback['education']}, write_seq {fback['write_seq']}, "
          f"cum_write {fback['cum_write']}, kind {fback['kind']}")
    # --- 2. NO snapshot: the restore must be a no-op
    m = Machine(b); m.do("wait:400"); m.do(po(b["brainKind"], [1]))
    teach(m, 8); before, fbefore = slot_of(m, "before"), fields(m)
    m.do(po(b["shadowRestoreRequest"], [1])); m.do("wait:10")
    after = slot_of(m, "after")
    fafter = fields(m)
    v = m.do("sync," + pk(b["cloneX"], 2)); cx = v[0] | v[1] << 8
    m.do("wait:200"); v = m.do("sync," + pk(b["cloneX"], 2) + pk(b["bodyOverruns"]))
    m.close()
    rec["invalid"] = dict(before=fbefore, after=fafter, before_sha=hashlib.sha256(before).hexdigest(),
                          after_sha=hashlib.sha256(after).hexdigest(), moved_after=(v[0] | v[1] << 8) - cx)
    check(fbefore["valid"] == 0, "no snapshot was ever taken: shadowValid 0")
    diff = [i for i in range(min(len(before), len(after))) if before[i] != after[i]]
    check(not diff, f"an INVALID restore leaves all {len(before)} slot bytes untouched"
                    + (f"; {len(diff)} bytes changed, first at offset {diff[0]}" if diff else
                       f" ({hashlib.sha256(before).hexdigest()[:16]})"))
    for k in ("education", "write_seq", "cum_write", "kind", "kind_now"):
        check(fafter[k] == fbefore[k], f"  {k} untouched: {fbefore[k]}")
    check(fafter["mood"] == fbefore["mood"], f"  mood untouched: {list(fbefore['mood'])}")
    check(fafter["request"] == 0, "the request byte is still consumed, so a host cannot spin on it")
    check(fafter["kind_now"] != 0, f"and the brain still runs: brainKindNow {fafter['kind_now']}, overruns {v[2]}")
    json.dump(dict(name=b.name, sha256=b.sha, states=rec,
                   design="teachShadowRestore returns before its first write unless shadowValid is 1."),
              open(os.path.join(outdir, f"shadow-{b.name}.json"), "w"), indent=1)
    return ok

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "shadow": sys.exit(0 if gate_shadow(Build(sys.argv[2]), OUT) else 1)

# ------------------------------------------------------------- recording a session for the replay
def gate_session(b, outdir):
    """Record one real teaching session as three files, so the canonical replay can be proved against
    the machine rather than against another copy of the same Python. The ring capacity is lowered so the
    session wraps and has to be drained several times: the ordered stream then spans reuse cycles, which
    is the case a replay is most likely to get wrong."""
    global ok
    # session-1 is the canonical recorded session and REPLAY.md pins its hashes and the build it came
    # from. Running this gate on any other build used to overwrite it in place - it silently replaced a
    # hash-pinned artifact with a recording from a different PRG. Only the build session-1 was recorded
    # on may write there; every other build records under its own name, next to it.
    CANONICAL = "tony-b025-a"
    d = os.path.join(outdir, "replay", "session-1" if b.name == CANONICAL else f"session-{b.name}")
    os.makedirs(d, exist_ok=True)
    print(f"{b.name}: recording a session into {os.path.relpath(d, ROOT)}")
    CAP = 40
    m = Machine(b); m.do(SETUP_WALK + po(b["lessonCap"], w16(CAP)) + f"poke:{b['brainKind']:X}:01,poke:{b['teachMode']:X}:01,wait:1")
    start = slot(m, b)
    p0 = ref.parse_slot(start)
    check(p0["education"] == 0 and set(p0["weights"][0]) == {0}, f"the session starts from a blank brain: education {p0['education']}, every weight zero, {len(start)} bytes")
    stream = bytearray(); drains = 0
    def take(mm):
        """read the unread entries in sequence order, acknowledge the exact range, keep the bytes"""
        nonlocal drains
        mm.do(f"poke:{b['teachMode']:X}:00,wait:2")
        st = ring_state(mm, b); recs = []
        for sq in range(st["read"], st["write"]):
            base = b["lessonData"] + (sq % st["cap"]) * ref.LESSON_SIZE
            recs.append(bytes(mm.do("".join(f"peek:{base + i:X}," for i in range(ref.LESSON_SIZE)))))
        total = sum(sum(r) for r in recs) & 0xffff
        mm.do(po(b["lessonAckSeq"], w16(st["write"])) + po(b["lessonAckSum"], w16(total)) + f"poke:{b['lessonAckRequest']:X}:01,wait:2")
        st2 = ring_state(mm, b)
        accepted = (st2["status"] & 0x80) != 0 and st2["read"] == st["write"]
        mm.do(f"poke:{b['teachMode']:X}:01")
        if accepted and recs: stream.extend(b"".join(recs)); drains += 1
        return accepted
    drv = cu.PortDriver(m); every = [0]
    def on_tick(mm, f):
        st = ring_state(mm, b)
        if st["write"] - st["read"] >= CAP - 10:
            if drv.held: mm.do(f"release:{drv.held}"); drv.held = 0
            take(mm)
    chatter_frames(m, b, drv, 1400, on_tick)
    m.do(f"poke:{b['teachMode']:X}:00,wait:2")
    st = ring_state(m, b)
    if st["write"] > st["read"]: take(m)
    final = slot(m, b); fin = ring_state(m, b); m.close()
    n = len(stream) // ref.LESSON_SIZE
    pf = ref.parse_slot(final)
    check(n > CAP and drains >= 3, f"{n} lessons recorded over {drains} drains at capacity {CAP}: the stream spans {n / CAP:.1f} ring fills, so it crosses reuse cycles")
    check(pf["education"] == n and fin["not_paired"] == 0, f"the machine applied every recorded lesson and no others: education {pf['education']}, entries {n}, dropped pairings {fin['not_paired']}")
    open(os.path.join(d, "start.slot"), "wb").write(start)
    open(os.path.join(d, "lessons.bin"), "wb").write(bytes(stream))
    open(os.path.join(d, "final.slot"), "wb").write(final)
    meta = dict(build=os.path.basename(b.prg), prg_sha256=b.sha, inputs=b.n, sense_nibbles=b.senses, retina_id=b.retina,
                vocabulary=b.vocab, lesson_entry_bytes=ref.LESSON_SIZE, ring_capacity_during_recording=CAP, drains=drains,
                lessons=n, ring_fills=round(n / CAP, 2), education_final=pf["education"],
                start=dict(bytes=len(start), sha256=hashlib.sha256(start).hexdigest(), brain_hash=ref.brain_hash(start), education=p0["education"]),
                lessons_file=dict(bytes=len(stream), sha256=hashlib.sha256(bytes(stream)).hexdigest()),
                final=dict(bytes=len(final), sha256=hashlib.sha256(final).hexdigest(), brain_hash=ref.brain_hash(final)),
                note="recorded on the machine: a blank BRAIN025 slot, the ordered LESSON25 entries as drained in sequence order across ring reuse, and the machine's own exported final slot")
    json.dump(meta, open(os.path.join(d, "session.json"), "w"), indent=1)
    print(f"  start.slot   {len(start)} bytes, brain hash {ref.brain_hash(start)[:16]}")
    print(f"  lessons.bin  {len(stream)} bytes, {n} entries, sha256 {meta['lessons_file']['sha256'][:16]}")
    print(f"  final.slot   {len(final)} bytes, brain hash {ref.brain_hash(final)}")
    return ok

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "session": sys.exit(0 if gate_session(Build(sys.argv[2]), OUT) else 1)

# ------------------------------------------------------------------- the visual state language (vis1)
SPR5_COLOUR, SPR0_COLOUR = 0xD02C, 0xD027       # the clone's own sprite colour, and the human Tony's
COLNAME = {0: "black", 1: "white", 2: "red", 3: "cyan", 5: "green", 15: "light grey"}

def _frames_of_colour(b, prefix, frames):
    """the clone's sprite colour and the human's, one sample a frame"""
    s = prefix + "".join("wait:1,sync," + pk(SPR5_COLOUR) + pk(SPR0_COLOUR) for _ in range(frames))
    v, out = b.run(s)
    return [(v[2 * k] & 15, v[2 * k + 1] & 15) for k in range(min(frames, len(v) // 2))]

def _hist(samples): 
    h = {}
    for c, _ in samples: h[c] = h.get(c, 0) + 1
    return h
def _show(h, n): return ", ".join(f"{COLNAME.get(c, c)} {v}/{n}" for c, v in sorted(h.items(), key=lambda kv: -kv[1]))

def gate_visual(b, outdir):
    """what the clone actually wears, frame by frame, in each of the five states. Presentation only, so
    what is checked is the colour register and that nothing else moved."""
    global ok
    os.makedirs(outdir, exist_ok=True)
    print(f"{b.name}: the clone's visual state language")
    rec = {}
    # 1. idle: white, dropping out to black. vis3 made the dropout's PERIOD a function of brainEducation,
    # so an untaught clone (education 0, which is what a fresh boot has) drops out one frame in sixteen.
    # vis1 and vis2 had a fixed one in thirty-two and this gate asserted 2 or 3 of 64; the expectation
    # moved with the behaviour, deliberately, and sub-check 6 below is what pins the new rule.
    idle = _frames_of_colour(b, "wait:300,", 64); h = _hist(idle)
    human = {c for _, c in idle}
    rec["idle"] = h
    check(h.get(1, 0) >= 56 and h.get(0, 0) in (3, 4, 5) and set(h) <= {0, 1},
          f"idle, untaught: {_show(h, len(idle))} over 64 frames, and nothing else")
    check(human == {15}, f"and the human Tony stays light grey throughout: {sorted(human)}")
    # 2. TEACH on: a slow cyan pulse over white
    on = _frames_of_colour(b, f"wait:300,key:{KEY_T}:6,wait:6,", 48); h = _hist(on)
    rec["teach_on"] = h
    cyan = h.get(3, 0)
    check(0.04 * len(on) <= cyan <= 0.20 * len(on) and h.get(1, 0) > 0 and not (set(h) - {0, 1, 3}),
          f"TEACH on: {_show(h, len(on))}, so cyan is a sprinkle of roughly one frame in eleven, over white, with the dropout still running")
    check({c for _, c in on} == {15}, "and the human Tony is untouched while teaching")
    # 3. an accepted lesson: a brief green flash
    m = Machine(b); m.do(f"wait:300,key:{KEY_T}:6,wait:6,hold:8")
    seen = []
    for _ in range(30): seen.append(m.do("wait:1,sync," + pk(SPR5_COLOUR) + pk(b["brainEducation"], 2))[0] & 15)
    m.do("release:8"); edu = m.do("sync," + pk(b["brainEducation"], 2)); m.close()
    green = seen.count(5); rec["accepted"] = dict(green_frames=green, education=edu[0] | edu[1] << 8, seen=seen)
    check(green >= 4 and (edu[0] | edu[1] << 8) > 0, f"an accepted lesson flashes green for {green} frames (education {edu[0] | edu[1] << 8}); the flash is 6 frames long by design")
    # 4. a refused lesson: red, and never green
    m = Machine(b); m.do(SETUP_WALK + po(b["lessonCap"], w16(6)) + f"poke:{b['brainKind']:X}:01,poke:{b['teachMode']:X}:01,wait:1")
    drv = cu.PortDriver(m); chatter_frames(m, b, drv, 160)
    st = ring_state(m, b)
    reds = []
    for _ in range(40): reds.append(m.do("wait:1,sync," + pk(SPR5_COLOUR))[0] & 15)
    fc = m.do("sync," + pk(b["cloneFlashColour"]))[0]; m.close()
    rec["refused"] = dict(ring_full=bool(st["status"] & 1), flash_colour=fc, red_frames=reds.count(2), green_frames=reds.count(5), seen=reds)
    check((st["status"] & 1) and fc == 2 and reds.count(2) > 0 and reds.count(5) == 0,
          f"with the ring full (status ${st['status']:02x}) a refused lesson flashes red on {reds.count(2)} of 40 frames and never green")
    # 5. leaving TEACH: back to white and the dropout, with no cyan left over
    off = _frames_of_colour(b, f"wait:300,key:{KEY_T}:6,wait:30,key:{KEY_T}:6,wait:20,", 64); h = _hist(off)
    rec["teach_off"] = h
    check(h.get(3, 0) == 0 and h.get(1, 0) >= 58 and set(h) <= {0, 1},
          f"TEACH off: {_show(h, len(off))}, no cyan and no flash left behind")
    # 6. vis3, the trained state: education changes the dropout's FREQUENCY and nothing else, it gets
    # rarer as he learns, and it never reaches zero however much he is taught.
    cad = {}
    for edu in (0, 8, 33, 96, 300, 1000):
        poke = po(b["brainEducation"], w16(edu))
        s = "wait:300," + poke + "".join("wait:1,sync," + pk(SPR5_COLOUR) + pk(SPR0_COLOUR) + poke for _ in range(256))
        v, _ = b.run(s)
        seen = [v[2 * k] & 15 for k in range(min(256, len(v) // 2))]
        cad[edu] = dict(dropout=seen.count(0), white=seen.count(1), other=sorted(set(seen) - {0, 1}), frames=len(seen))
    rec["cadence"] = cad
    drops = [cad[e]["dropout"] for e in (0, 8, 33, 96, 300, 1000)]
    check(all(d > 0 for d in drops), f"the dropout survives every education: {drops} of 256 frames at 0, 8, 33, 96, 300, 1000 lessons")
    check(drops[0] > drops[1] > drops[2] > drops[3] and drops[3] == drops[4] == drops[5],
          f"and it gets rarer as he learns, down to a floor: one frame in {[cad[e]['frames'] // cad[e]['dropout'] for e in (0, 8, 33, 96, 300, 1000)]}")
    check(all(not cad[e]["other"] for e in cad), "with no colour but white and the dropout while he runs on his own")
    json.dump(dict(name=b.name, sha256=b.sha, states=rec,
                   palette={"white": 1, "cyan": 3, "green": 5, "red": 2, "dropout": 0, "human_tony": 15},
                   design="a pure function of bodyFrames, teachMode, brainEducation and the existing flash counter;"
                          " only sprites 5 and 6 are written. Education modulates the dropout's period only: 16, 32,"
                          " 64, 128 frames, and 128 is a floor - the dropout never goes away."),
              open(os.path.join(outdir, f"visual-{b.name}.json"), "w"), indent=1)
    return ok

# -------------------------------------------------------- the transition effect, and the two fixes (vis3)
def gate_transit(b, outdir):
    """THE GUARD FOR THE TRANSITION EFFECT. The redraw between rooms is meant to be seen: while a room
    change runs the background holds COL_TRANSIT and the fade cannot reach the screen. That works only
    because the roomChange override is the LAST write to A before "sta c64lib.BG_COL_0" in
    doEachFrameTop, and nothing in the assembler can enforce it. This gate can, and does."""
    global ok
    os.makedirs(outdir, exist_ok=True)
    print(f"{b.name}: the room-transition effect, both directions")
    rec = {}
    def bg_across(chamber, direction, pre=""):
        s = ("wait:400," + pre + po(b["roomChangeDirection"], [direction]) + po(b["roomChange"], [chamber]) +
             "".join("wait:1,sync," + pk(0xD021) + pk(b["roomChange"]) + pk(b["bodyOverruns"]) + pk(b["brainThinks"], 2) for _ in range(20)))
        v, _ = b.run(s)
        n = min(20, len(v) // 5)
        return ([v[5 * k] & 15 for k in range(n)], [v[5 * k + 1] for k in range(n)],
                [v[5 * k + 2] for k in range(n)], [v[5 * k + 3] | v[5 * k + 4] << 8 for k in range(n)])
    up, rc_up, ov_up, th_up = bg_across(1, 1)
    down, rc_dn, ov_dn, th_dn = bg_across(0, 2, po(b["roomChangeDirection"], [1]) + po(b["roomChange"], [1]) + "wait:60,")
    rec["up"] = dict(bg=up, overruns=ov_up, thinks=th_up)
    rec["down"] = dict(bg=down, overruns=ov_dn, thinks=th_dn)
    COL_TRANSIT = 11
    for way, bg, rc in (("up   (0 -> 1)", up, rc_up), ("down (1 -> 0)", down, rc_dn)):
        held = [c for c, r in zip(bg, rc) if r != 0xff]
        check(held and set(held) == {COL_TRANSIT},
              f"{way}: the background holds {COL_TRANSIT} for all {len(held)} frames of the change ({bg})")
        check(0 not in bg, f"{way}: and never dips to black, so the fade never hides the redraw")
    # the brain must stay blocked while the room is redrawn: changeRoomIfNeeded holds the main loop
    for way, th in (("up", th_up), ("down", th_dn)):
        spent = th[-1] - th[0]
        rec[f"thinks_{way}"] = spent
        check(spent <= 6, f"{way}: the brain thought {spent} times across the 20 frames of the change, not the ~5 a free main loop would manage each four frames")
    check(not any(ov_up) and not any(ov_dn), f"no raster overruns either way: {max(ov_up + ov_dn)}")
    # and the fades that are NOT room changes must be untouched
    s = "sync," + "".join("wait:4,sync," + pk(0xD021) + pk(b["roomChange"]) for _ in range(60))
    v, _ = b.run(s)
    boot = [v[2 * k] & 15 for k in range(min(60, len(v) // 2))]
    boot_rc = {v[2 * k + 1] for k in range(min(60, len(v) // 2))}
    rec["boot"] = boot
    check(boot_rc == {0xff}, f"level start is not a room change (roomChange stayed $ff), so its own fade is untouched")
    check(0 in boot and 15 in boot, f"and it still fades: the level-start background goes through black to the room's colour")
    json.dump(dict(name=b.name, sha256=b.sha, transit_colour=COL_TRANSIT, states=rec,
                   design="doEachFrameTop pins BG_COL_0 to COL_TRANSIT while roomChange != $ff. It must be the LAST"
                          " override before the store; this gate fails if a later write or a reordering takes it back."),
              open(os.path.join(outdir, f"transit-{b.name}.json"), "w"), indent=1)
    return ok

def gate_crouch(b, outdir):
    """human/clone parity around the build action. Down with fire lays a brick; the player keeps his
    crouch while down is held, and before --build-parity the routed clone stood straight back up because
    teachRoute replaced the whole stick with the verb bit. His published ducking sense read 0 where the
    same stick on the player's body reads non-zero, and that is what the lesson recorded. The taught
    action must NOT move: actionOf tests bits 5-6 before any direction, so a build frame is 8 or 9."""
    global ok
    os.makedirs(outdir, exist_ok=True)
    print(f"{b.name}: the build action, human against clone")
    DUCK = {0x03, 0x83}
    def hold(pre, addr, extra=()):
        s = ("wait:400," + pre + "sync,hold:18," +
             "".join("wait:2,sync," + pk(addr) + "".join(pk(a) for a in extra) for _ in range(24)) +
             "release:18,wait:6,sync," + pk(addr))
        v, _ = b.run(s)
        w = 1 + len(extra)
        n = (len(v) - 1) // w
        return [v[w * k] for k in range(n)], [[v[w * k + 1 + i] for k in range(n)] for i in range(len(extra))], v[-1]
    human, _, human_after = hold("", b["physPlayerState"])
    clone, extra, clone_after = hold(f"key:{KEY_T}:6,wait:20,", b["cloneState"],
                                     (b["cloneSenses"] + 7, b["cloneSenses"] + 16, b["cloneJoy"]))
    duck, last, joy = extra
    hd = sum(1 for s in human if s in DUCK); cd = sum(1 for s in clone if s in DUCK)
    check(hd >= 20, f"the player holds his crouch: {hd} of {len(human)} samples ducking while down is held")
    check(cd >= 20, f"and so does the routed clone: {cd} of {len(clone)} samples ducking (this is the fix)")
    check(human_after not in DUCK and clone_after not in DUCK, "both stand up when down is let go, and only then")
    settled = [d for d in duck[2:]]
    check(all(d > 0 for d in settled), f"his published ducking sense follows his body: nibble 7 = {sorted(set(settled))} while he is crouched")
    acts = {a for a in last[2:]}
    check(acts <= {8, 9} and acts, f"and the taught action of a build frame is unchanged: sense 16 = {sorted(acts)} (8 and 9 are build-left and build-right)")
    check({j for j in joy[2:]} and all(j & 0b100000 for j in joy[2:]) and all(j & 0b10 for j in joy[2:]),
          f"the clone's stick carries the verb AND the direction: cloneJoy = {sorted({j for j in joy[2:]})}")
    json.dump(dict(name=b.name, sha256=b.sha, human_states=[f"${s:02X}" for s in human], clone_states=[f"${s:02X}" for s in clone],
                   ducking_sense=duck, last_action_sense=last, clone_joy=joy,
                   design="teachRoute ORs the build verb onto the teaching stick instead of substituting for it,"
                          " matching buildVerb, which passes the player's stick through untouched."),
              open(os.path.join(outdir, f"crouch-{b.name}.json"), "w"), indent=1)
    return ok

def gate_roomdata(b, outdir):
    """the packed level data must survive play. muralBatsStamp patches its six parameter stores from the
    room's static-object array pointers and writes through them whether the room has objects or not; a
    room with none has ZERO-LENGTH arrays, and for chamber 0 of this two-room level every one of those
    pointers is the address of chamber 1's compressed map. Two map bytes were being overwritten at level
    start, which is the "75" that appeared in the room above's top-left corner."""
    global ok
    os.makedirs(outdir, exist_ok=True)
    print(f"{b.name}: the packed level data, after a round trip through both rooms")
    prg = open(b.prg, "rb").read(); load = prg[0] | prg[1] << 8
    v, _ = b.run("wait:400,sync," + pk(b["level_roomPtr"], 2) + pk(b["level_roomPtr"] + 2, 2) +
                 pk(b["level_objectControlPtr"], 2) + pk(b["level_objectControlPtr"] + 2, 2) + pk(b["level_objectSizes"], 2))
    rooms = [v[0] | v[2] << 8, v[1] | v[3] << 8]
    objs = [v[4] | v[6] << 8, v[5] | v[7] << 8]
    sizes = [v[8], v[9]]
    print(f"  rooms at ${rooms[0]:04X} ${rooms[1]:04X}; object arrays at ${objs[0]:04X} ${objs[1]:04X}; sizes {sizes}")
    check(sizes == [0, 0] and objs[0] == rooms[1],
          f"the shape that causes it is still here: chamber 0 has no static objects and its arrays alias chamber 1's map at ${rooms[1]:04X}")
    dump = os.path.join(outdir, f"roomdata-{b.name}.bin")
    b.run("wait:400," + po(b["roomChangeDirection"], [1]) + po(b["roomChange"], [1]) + "wait:40," +
          po(b["roomChangeDirection"], [2]) + po(b["roomChange"], [0]) + f"wait:40,sync,dump:{rooms[1]:X}:20:{dump},")
    now = open(dump, "rb").read(); want = prg[2 + rooms[1] - load:2 + rooms[1] - load + 32]
    bad = [i for i in range(min(len(now), len(want))) if now[i] != want[i]]
    check(not bad, f"chamber 1's packed map is byte-identical to the load image after both transitions"
                   + (f"; differs at {bad}: " + " ".join(f"${want[i]:02X}->${now[i]:02X}" for i in bad) if bad else ""))
    # both rooms pack the same build-room.bin and decode the same charset, so their ceiling must agree.
    # These are the DRAWN codes, after translateRoom, not the map bytes: before the guard the room above
    # showed $2A $28 here (the map's damaged $08 $06 translated) where the room below shows $06 $09.
    v, _ = b.run("wait:400,sync," + pk(0xC000, 2) + po(b["roomChangeDirection"], [1]) + po(b["roomChange"], [1]) +
                 "wait:40,sync," + pk(0xC000, 2))
    below, above = v[0:2], v[2:4]
    check(above == below,
          f"and the two rooms draw the same ceiling: below ${below[0]:02X} ${below[1]:02X}, above ${above[0]:02X} ${above[1]:02X}"
          f" (the map's ${want[0]:02X} ${want[1]:02X} through the room charset)")
    # THE CHECK THIS GATE WAS MISSING. Verifying the packed map and the freshly drawn ceiling is not
    # enough: the sink the stamp is redirected to is written at base+0 AND base+1, because the stores are
    # indexed by y (0 for the left bat, 1 for the right). A sink one byte short spills onto muralRowA,
    # whose low byte is the mural's first row base, and the back wall then stamps across row 0 of both
    # rooms from the first transition onward - which no check on the packed map or on a first draw can
    # see. So: draw the room, go up, come back, and require the whole top of the room to be unchanged.
    dmp = os.path.join(outdir, f"roomdata-ceiling-{b.name}")
    b.run("wait:400,sync," + f"dump:C000:80:{dmp}-a.bin," + po(b["roomChangeDirection"], [1]) + po(b["roomChange"], [1]) +
          f"wait:40,sync,dump:C000:80:{dmp}-up.bin," + po(b["roomChangeDirection"], [2]) + po(b["roomChange"], [0]) +
          f"wait:40,sync,dump:C000:80:{dmp}-b.bin,")
    ca, cu_, cb = (open(f"{dmp}-{t}.bin", "rb").read() for t in ("a", "up", "b"))
    moved = [i for i in range(128) if ca[i] != cb[i]]
    check(not moved,
          "the top of the room is the same after going up and coming back as it was at level start"
          + (f"; {len(moved)} cells moved, at rows/columns "
             + " ".join(f"r{i // 40}c{i % 40}(${ca[i]:02X}->${cb[i]:02X})" for i in moved[:16]) if moved else ""))
    print(f"       the room above's own ceiling, for the record: {' '.join(f'${x:02X}' for x in cu_[:8])} …")
    json.dump(dict(name=b.name, sha256=b.sha, room_ptrs=[f"${a:04X}" for a in rooms], object_ptrs=[f"${a:04X}" for a in objs],
                   object_sizes=sizes, intact=not bad, ceiling_stable=not moved,
                   design="muralBatsStamp sends its parameter stores to a two-byte sink when the room carries no static"
                          " objects. Two bytes because the stores are indexed by y: 0 for the left bat, 1 for the right."),
              open(os.path.join(outdir, f"roomdata-{b.name}.json"), "w"), indent=1)
    return ok

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "transit": sys.exit(0 if gate_transit(Build(sys.argv[2]), OUT) else 1)
if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "crouch": sys.exit(0 if gate_crouch(Build(sys.argv[2]), OUT) else 1)
if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "roomdata": sys.exit(0 if gate_roomdata(Build(sys.argv[2]), OUT) else 1)

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "visual": sys.exit(0 if gate_visual(Build(sys.argv[2]), OUT) else 1)
