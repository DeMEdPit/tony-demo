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
        self.n = self.sym["B02_N"]; self.senses = self.sym["B02_SENSES"]; self.retina = self.sym["B02_RETINA"]; self.vocab = self.sym["B02_VOCAB"]
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
