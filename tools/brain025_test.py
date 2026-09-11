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
        for x in sel: s += po(ob["brainTestIn"], xb(x)) + f"poke:{ob['brainTestRun']:X}:01,wait:2,sync," + pk(ob["brainTestAction"]) + pk(ob["brainTestOutput"])
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
        m.do(po(b["lessonAckSeq"], w16(st["write"])) + po(b["lessonAckSum"], w16(total)) + f"poke:{b['lessonAckRequest']:X}:01,wait:2")
        st2 = ring_state(m, b)
        accepted = (st2["status"] & 0x80) != 0 and st2["read"] == st["write"] and st2["drains"] == st["drains"] + 1 and (st2["status"] & 0x0e) == 0
        if accepted or not (st2["status"] & 0x02): break
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
