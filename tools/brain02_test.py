#!/usr/bin/env python3
"""
brain02_test.py - the Phase 3 gates on a BRAIN02 build (PREREG-PHASE3.md), through the harness.

  smoke PRG        boots, the markers, kind 0 follows, kind 1 thinks and the profiler counts
  parity PRG       gate 1: the retina on every recorded block, golden-1b forward/lessons/vocabulary, malformed slots
  resources PRG    gate 2: sizes, addresses, cycles, raster
  teach PRG        gate 3: TEACH end to end (the E5 story on BRAIN02)
  drain PRG        gate 4: three ring cycles with replay equality, and the split-vs-uninterrupted equivalence
  descriptor PRG   the JSON descriptor for the workbench
"""
import hashlib, json, os, re, subprocess, sys, tempfile
import importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
ref = _load("brain02_ref", os.path.join(ROOT, "tools/brain02_ref.py"))

class Build:
    """a BRAIN02 PRG with its symbols"""
    def __init__(self, prg):
        self.prg = prg; self.name = os.path.basename(prg)[:-4]
        self.sym = {}
        for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(os.path.join(ROOT, f"src/kickass/{self.name}.sym")).read()):
            self.sym.setdefault(m.group(1), int(m.group(2), 16))
        self.n = self.sym["B02_N"]; self.retina = self.sym["B02_RETINA"]; self.vocab = self.sym["B02_VOCAB"]
        self.size = os.path.getsize(prg); self.sha = hashlib.sha256(open(prg, "rb").read()).hexdigest()
    def __getitem__(self, k): return self.sym[k]
    def run(self, script):
        with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
        r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), self.prg, "@" + f.name], capture_output=True, text=True); os.unlink(f.name)
        return [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)], r.stdout
def pk(addr, n=1): return "".join(f"peek:{addr + i:X}," for i in range(n))
def po(addr, data): return "".join(f"poke:{addr + i:X}:{b & 255:02X}," for i, b in enumerate(data))
def w16(v): return [v & 255, (v >> 8) & 255]
def s16(lo, hi): v = lo | (hi << 8); return v - 65536 if v >= 32768 else v
def s8(v): return v - 256 if v >= 128 else v

ok = True
def check(cond, msg):
    global ok
    ok &= bool(cond); print(("  ok   " if cond else "  FAIL ") + msg)

def smoke(b):
    print(f"{b.name}: {b.size} bytes, sha256 {b.sha[:16]}, n={b.n} retina {b.retina} vocab {b.vocab}")
    M, L = b["brainMarker"], b["lessonMarker"]
    v, out = b.run("wait:300," + pk(M, 8) + pk(b["brainKind"]) + pk(L, 8) + pk(b["lessonCap"], 2) + pk(b["lessonSize"]) + "sync," + pk(b["physPlayerX"], 2) + pk(b["cloneX"], 2) + pk(b["brainThinks"], 2) +
                   "joy:8:60,wait:100,sync," + pk(b["physPlayerX"], 2) + pk(b["cloneX"], 2) + pk(b["brainThinks"], 2) +
                   f"poke:{b['brainKind']:X}:01,wait:40,sync," + pk(b["brainThinks"], 2) + pk(b["profThink"], 4) + pk(b["brainOutput"]) + pk(b["brainAction"]) + pk(b["brainH"]) + pk(b["brainActiveCount"]) + pk(b["brainAcc"], 20) + pk(b["cloneX"], 2))
    check(bytes(v[0:8]) == b"BRAIN02\0" and v[8] == 0, f"the slot's marker and kind 0 at boot")
    check(bytes(v[9:17]) == b"LESSON2\0" and v[17] | v[18] << 8 == 300 and v[19] == 11, f"the LESSON2 ring: capacity {v[17] | v[18] << 8}, entry size {v[19]}")
    px0, cx0, th0 = v[20] | v[21] << 8, v[22] | v[23] << 8, v[24] | v[25] << 8
    px1, cx1, th1 = v[26] | v[27] << 8, v[28] | v[29] << 8, v[30] | v[31] << 8
    check(abs(px1 - cx1) < 52 and px1 > 270 and th1 == 0, f"kind 0 follows: Tony {px0}->{px1}, the clone {cx0}->{cx1}, no thinks")
    th2 = v[32] | v[33] << 8; prof = v[34] | v[35] << 8; profmax = v[36] | v[37] << 8
    acc = [s16(v[42 + 2 * o], v[43 + 2 * o]) for o in range(10)]
    check(th2 >= 8 and 2000 < prof < 40000 and profmax >= prof, f"kind 1 thinks: {th2} thinks in 40 frames, the last think {prof} cycles wall-clock, interrupts included (max {profmax})")
    check(acc == [0] * 10 and v[38] == 0 and v[39] == 0, f"zero weights: every accumulator 0, output {v[38]}, action {v[39]}; h {v[40]}, {v[41]} flags active")
    return ok

if __name__ == "__main__":
    cmd, prg = sys.argv[1], sys.argv[2]
    b = Build(prg)
    if cmd == "smoke": sys.exit(0 if smoke(b) else 1)

# ------------------------------------------------------------------------------------ gate 1: parity
def blocks_all():
    b2 = _load("bakeoff2", os.path.join(ROOT, "tools/bakeoff2.py")); D = b2.sets()
    return sorted(D["s1424"]), D
def xb(x): return bytes(v & 15 for v in x)
def parity(b, quick=False):
    WAIT = 2 if b.n <= 72 else 6                                     # the hook runs inside one main-loop pass; 128 fully set inputs take 2.6 frames
    """gate 1 on one build: the retina on every recorded block, the golden sets at this build's width (and the
    128-input sets on the parity build), the vocabulary, malformed slots, and a learned brain replayed"""
    global ok
    print(f"{b.name}: n={b.n} retina {b.retina} vocab {b.vocab}")
    TI, TF, TR, TM, TA, TO, TAC, TH = b["brainTestIn"], b["brainTestFlags"], b["brainTestRun"], b["brainTestMode"], b["brainTestAction"], b["brainTestOutput"], b["brainTestAcc"], b["brainTestH"]
    W, MOOD, KIND = b["brainWeights"], b["brainMood"], b["brainKind"]
    LR, LT, LP, LK, LREL = b["brainLearnRun"], b["brainLearnTestT"], b["brainLearnTestP"], b["brainLearnTestTook"], b["brainLearnTestTrel"]
    entries = ref.TABLES[b.retina][1]() if b.retina else None
    n = b.n
    # 1. the retina on every recorded block
    if entries:
        blocks, D = blocks_all()
        if quick: blocks = blocks[::10]
        bad = 0; total = 0
        for c in range(0, len(blocks), 150):
            chunk = blocks[c:c + 150]; script = "wait:300," + f"poke:{TM:X}:00,"
            for x in chunk: script += po(TI, xb(x)) + f"poke:{TR:X}:01,wait:{WAIT},sync," + pk(TF, n) + pk(TH) + pk(TO) + pk(TA)
            v, out = b.run(script); per = n + 3
            for k, x in enumerate(chunk):
                got = v[k * per:(k + 1) * per]; total += 1
                want = ref.flags(entries, list(x)); h = 1 if ref.h_of(list(x)) == 1 else 0
                if got[:n] != want or got[n] != h: bad += 1
                if bad and bad < 4 and (got[:n] != want or got[n] != h): print("   differs:", list(x), "flags", "".join(map(str, got[:n])), "want", "".join(map(str, want)), "h", got[n], want and h)
        check(bad == 0, f"the retina and h: {total - bad} of {total} recorded blocks byte for byte")
    # 2. golden forward-v2 at this width (mode 1)
    G = json.load(open(os.path.join(ROOT, "deliverables/bakeoff/golden-1b/forward-v2.json")))["cases"]
    cases = [c for c in G if c["n"] == n]
    if cases:
        script = "wait:300," + f"poke:{TM:X}:01,"
        for c in cases: script += po(W, bytes.fromhex(c["weights"])) + po(MOOD, bytes.fromhex(c["mood"])) + po(TF, bytes(c["x"])) + f"poke:{TR:X}:01,wait:{WAIT},sync," + pk(TAC, 20) + pk(TO) + pk(TA)
        v, out = b.run(script); bad = 0
        for k, c in enumerate(cases):
            got = v[k * 22:(k + 1) * 22]; acc = [s16(got[2 * o], got[2 * o + 1]) for o in range(10)]
            if acc != c["acc"] or got[20] != c["action"] or got[21] != c["action"]:
                bad += 1; print(f"   differs: forward '{c['name']}': machine {acc} out {got[20]} act {got[21]}")
        check(bad == 0, f"golden forward-v2 at {n} inputs: {len(cases) - bad} of {len(cases)} cases (accumulators, the first largest, the identity resolution with h left)")
    # 3. golden lessons-v2 at this width (mode 1, raw taught index)
    G = json.load(open(os.path.join(ROOT, "deliverables/bakeoff/golden-1b/lessons-v2.json")))["cases"]
    cases = [c for c in G if c["n"] == n and c["box"] == [-128, 127]]
    if cases:
        script = "wait:300," + f"poke:{TM:X}:01," + po(MOOD, bytes(10))
        for c in cases:
            script += po(W, bytes.fromhex(c["weights_before"]))
            for l in c["lessons"]: script += po(TF, bytes(l["x"])) + f"poke:{LT:X}:{l['t']:02X},poke:{LR:X}:01,wait:{WAIT},sync," + pk(LP) + pk(LK)
            script += "sync," + pk(W, 10 * n)
        v, out = b.run(script); i = 0; bad = 0
        for c in cases:
            preds, took = [], []
            for l in c["lessons"]: preds.append(v[i]); took.append(bool(v[i + 1])); i += 2
            after = bytes(v[i:i + 10 * n]).hex(); i += 10 * n
            if after != c["weights_after"] or preds != c["predictions"] or took != c["taken"]:
                bad += 1; print(f"   differs: lessons '{c['name']}': predictions {preds} taken {took}")
        check(bad == 0, f"golden lessons-v2 at {n} inputs, box -128..127: {len(cases) - bad} of {len(cases)} cases (weights after, predictions, taken)")
    if entries is None: return ok
    # 4. the vocabulary: the resolution and the translation on the forty golden cases
    G = json.load(open(os.path.join(ROOT, "deliverables/bakeoff/golden-1b/vocabulary-v2.json")))["cases"]
    script = "wait:300," + f"poke:{TM:X}:00," + po(MOOD, bytes(10))
    for c in G:
        Wm = [[0] * n for _ in range(10)]; Wm[c["output"]][0] = 100               # the bias flag alone chooses the output
        script += po(W, bytes(v & 255 for row in Wm for v in row)) + po(TI, xb(c["block"])) + f"poke:{TR:X}:01,wait:{WAIT},sync," + pk(TO) + pk(TA) + pk(TH)
        script += f"poke:{LT:X}:{c['pressed_absolute']:02X},poke:{LR:X}:01,wait:{WAIT},sync," + pk(LREL) + pk(LP)
    v, out = b.run(script); bad = 0
    for k, c in enumerate(G):
        got = v[k * 5:(k + 1) * 5]; h = 1 if c["h"] == 1 else 0
        want_abs = c["resolved_absolute"] if b.vocab else c["output"]; want_rel = c["taught_relative"] if b.vocab else c["pressed_absolute"]
        if got[0] != c["output"] or got[1] != want_abs or got[2] != h or got[3] != want_rel:
            bad += 1; print(f"   differs: vocabulary {c['case']} output {c['output']}: machine out {got[0]} act {got[1]} h {got[2]} trel {got[3]}; want act {want_abs} trel {want_rel}")
    check(bad == 0, f"the vocabulary on {len(G)} golden cases: the resolution, the translation and h ({'reference-relative' if b.vocab else 'absolute, the identity'})")
    # 5. malformed slots -> kind 0; a valid kind 2 stays 2
    KN = b["brainKindNow"]; fields = [("marker", b["brainMarker"] + 2, ord("X")), ("layout", b["brainLayout"], 1), ("kind", KIND, 3), ("inputs", b["brainInputCount"], n + 1), ("hidden", b["brainHiddenCount"], 1),
                                      ("outputs", b["brainOutputCount"], 9), ("rule", b["brainRule"], 1), ("vocabulary", b["brainVocab"], 2), ("retina", b["brainRetinaId"], b.retina + 1)]
    script = "wait:300," + f"poke:{KIND:X}:01,wait:{WAIT},sync," + pk(KN)
    for name, addr, badv in fields:
        script += f"peek:{addr:X}," + f"poke:{addr:X}:{badv:02X},wait:{WAIT},sync," + pk(KN)
        script += f"poke:{addr:X}:{{{name}}},"     # restored below
    # build with the restore values by reading them first
    v0, _ = b.run("wait:300," + "".join(f"peek:{addr:X}," for name, addr, badv in fields))
    for (name, addr, badv), orig in zip(fields, v0): script = script.replace(f"poke:{addr:X}:{{{name}}},", f"poke:{addr:X}:{orig:02X},")
    script += f"poke:{KIND:X}:02,wait:{WAIT},sync," + pk(KN) + f"poke:{KIND:X}:00,wait:{WAIT},sync," + pk(KN)
    v, out = b.run(script)
    k2, k0 = 1 + 2 * len(fields), 2 + 2 * len(fields)
    checks = [v[0] == 1] + [v[2 + 2 * k] == 0 for k in range(len(fields))] + [v[k2] == 2, v[k0] == 0]
    check(all(checks), f"malformed slots: kind 1 valid -> {v[0]}; each header field wrong in turn -> {[v[2 + 2 * k] for k in range(len(fields))]}; kind 2 -> {v[k2]}, kind 0 -> {v[k0]}")
    # 6. a learned brain replayed: Phase 2b's weights for this retina and vocabulary on the 231 and the 474
    P2 = json.load(open(os.path.join(ROOT, "deliverables/bakeoff/phase2b.json")))
    arm = {1: "R0", 2: "R1b", 3: "R0s"}.get(b.retina); key = f"{arm}|{'rel' if b.vocab else 'abs'}|8|S2u"
    if arm and key in P2:
        Wl = P2[key]["weights"]; blocks, D = blocks_all(); test = sorted(D["s474"])
        if quick: test = test[::5]
        script = "wait:300," + f"poke:{TM:X}:00," + po(MOOD, bytes(10)) + po(W, bytes(v & 255 for row in Wl for v in row))
        for x in test: script += po(TI, xb(x)) + f"poke:{TR:X}:01,wait:{WAIT},sync," + pk(TO) + pk(TA)
        v, out = b.run(script); bad = 0
        for k, x in enumerate(test):
            z = ref.flags(entries, list(x)); acc, o = ref.forward(Wl, z); a = ref.to_absolute(o, ref.h_of(list(x))) if b.vocab else o
            if v[2 * k] != o or v[2 * k + 1] != a: bad += 1
        check(bad == 0, f"Phase 2b's learned {arm} weights on {len(test)} teacher-visited blocks: the machine's output and resolved action equal the reference's on {len(test) - bad}")
    return ok
if __name__ == "__main__" and sys.argv[1] == "parity": sys.exit(0 if parity(Build(sys.argv[2]), quick="--quick" in sys.argv) else 1)

# ------------------------------------------------------------------------- a machine driven line by line
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
def sgn(x): return x - 16 if x >= 8 else x
def senses(m, b):
    v = m.do("sync," + pk(b["cloneSenses"], 20) + pk(b["cloneX"], 2) + pk(b["cloneY"]) + pk(b["cloneState"]) + pk(b["physPlayerX"], 2) + pk(b["physPlayerY"]) + pk(b["physPlayerState"]))
    return dict(senses=[sgn(x) for x in v[:20]], cx=v[20] | v[21] << 8, cy=v[22], cs=v[23], px=v[24] | v[25] << 8, py=v[26], ps=v[27])
def ring_state(m, b):
    v = m.do("sync," + pk(b["lessonWriteSeq"], 2) + pk(b["lessonReadSeq"], 2) + pk(b["lessonStatus"]) + pk(b["brainEducation"], 2) + pk(b["lessonCap"], 2) + pk(b["lessonDrains"]) + pk(b["lessonCumWrite"], 2) + pk(b["lessonCumRead"], 2) + pk(b["lessonNotPaired"], 2))
    return dict(write=v[0] | v[1] << 8, read=v[2] | v[3] << 8, status=v[4], education=v[5] | v[6] << 8, cap=v[7] | v[8] << 8, drains=v[9], cumWrite=v[10] | v[11] << 8, cumRead=v[12] | v[13] << 8, not_paired=v[14] | v[15] << 8)
def slot(m, b):
    """the whole slot as bytes"""
    n = b["BRAIN_BLOCK_SIZE"]; out = []
    for c in range(0, n, 200): out += m.do("".join(f"peek:{b['brainMarker'] + c + i:X}," for i in range(min(200, n - c))))
    return bytes(out)
def teach_frames(m, b, drv, frames, on_tick=None):
    """the scripted teacher (curriculum.py) through the port for so many frames; on_tick(m) after each decision"""
    f = 0
    while f < frames:
        d = senses(m, b); a = cu.teacher(d["senses"]); m.do(drv.emit(a)); f += 32 if a in (cu.BUILDL, cu.BUILDR) else cu.TICK
        if on_tick: on_tick(m, f)
    if drv.held: m.do(f"release:{drv.held}"); drv.held = 0
STAIRS_C33 = "wait:300,joy:8:{},wait:20,".format((8 * 33 - 60 - 184) // 2) + "".join("joy:18:6,wait:20,joy:17:6,wait:30," for _ in range(5)) + "wait:10,hold:1,wait:50,release:1,wait:10,"   # every setup ends with a comma: commands are appended
EPISODES = [("E01_follow_right", "wait:300,joy:8:30,wait:20,", 300), ("E02_follow_left", "wait:300,joy:4:40,wait:20,", 300), ("E07_stairs_C33", STAIRS_C33, 700), ("E03_follow_far_right", "wait:300,joy:8:50,wait:20,", 400), ("E12_restraint_wall", "wait:300,joy:8:60,wait:20,", 400)]

def drain(m, b, saved_slot, log, teaching=True):
    """with teaching held off for the frames the handshake needs (no lesson can be recorded meanwhile; the
    workbench pauses the emulator instead), read the unread lessons, acknowledge with the checksum (retrying
    if a lesson landed between the read and the request), replay the accepted range over the saved slot with
    the reference and compare with the machine's slot byte for byte. Returns (the new saved slot, ok)."""
    TEACH = b["teachMode"]; n = b.n
    if teaching: m.do(f"poke:{TEACH:X}:00,wait:2")
    accepted = False; recs = []
    for attempt in range(4):
        st = ring_state(m, b); cap = st["cap"]
        recs = []
        for sq in range(st["read"], st["write"]):
            base = b["lessonData"] + (sq % cap) * 11
            recs.append(bytes(m.do("".join(f"peek:{base + i:X}," for i in range(11)))))
        total = sum(sum(r) for r in recs) & 0xffff
        m.do(po(b["lessonAckSeq"], w16(st["write"])) + po(b["lessonAckSum"], w16(total)) + f"poke:{b['lessonAckRequest']:X}:01,wait:2")
        st2 = ring_state(m, b)
        accepted = (st2["status"] & 0x80) != 0 and st2["read"] == st["write"] and st2["drains"] == st["drains"] + 1 and (st2["status"] & 0x0e) == 0
        if accepted or not (st2["status"] & 0x02): break                  # accepted, or refused for a reason a retry cannot mend
    if teaching: m.do(f"poke:{TEACH:X}:01")
    p = ref.parse_slot(saved_slot); W = [row[:] for row in p["weights"]]; edu = p["education"]; entries = ref.TABLES[b.retina][1]()
    divergent = 0
    for r in recs:
        x = [sgn(r[i // 2] & 15) if i % 2 == 0 else sgn(r[i // 2] >> 4) for i in range(20)]
        t_abs = r[10] & 15; z = ref.flags(entries, x); t = ref.to_relative(t_abs, ref.h_of(x)) if b.vocab else t_abs
        pr, took = ref.learn(W, z, t)
        if not took: divergent += 1
        edu += 1
    machine = slot(m, b); pm = ref.parse_slot(machine)
    same = pm["weights"] == W and pm["education"] == edu
    log.append(dict(drained=len(recs), seq_from=st["read"], seq_to=st["write"], sum=total, accepted=accepted, attempts=attempt + 1, replay_took_all=(divergent == 0), weights_equal=(pm["weights"] == W),
                    education_machine=pm["education"], education_replay=edu, hash_machine=ref.brain_hash(machine), hash_replay=ref.brain_hash(ref.slot_bytes(pm["kind"], pm["vocabulary"], pm["retina_id"], W, edu))))
    good = accepted and same and divergent == 0
    return (machine if good else saved_slot), good
def dummy_drain(m, b):
    """the same frames as a drain, no acknowledgement (the uninterrupted run of the equivalence test)"""
    m.do(f"poke:{b['teachMode']:X}:00,wait:2,wait:2,poke:{b['teachMode']:X}:01")

import random as _random
_CHATTER = _random.Random(20260911); CHATTER = [_CHATTER.choice((1, 2, 5, 3, 0, 4)) for _ in range(2000)]
def chatter(tick):
    """a teacher whose next action the senses cannot predict (a fixed pseudo-random sequence of toward, away,
    jump, up, idle, down), so the brain disagrees on most ticks and the ring fills quickly; the sense of the
    lessons is beside the point in the ring tests. A cycling sequence was learned in a few lessons through
    the last-action flags."""
    return CHATTER[tick]
def chatter_frames(m, b, drv, frames, on_tick=None):
    f = 0; tick = 0
    while f < frames:
        a = chatter(tick); m.do(drv.emit(a)); f += cu.TICK; tick += 1
        if on_tick: on_tick(m, f)
    if drv.held: m.do(f"release:{drv.held}"); drv.held = 0

def gate_drain(b, outdir):
    """gate 4: three ring cycles at a lowered capacity (a research control at boot), the replay equality after
    every drain, the full-ring pause, refused acknowledgements, and the split-versus-uninterrupted equivalence"""
    global ok
    os.makedirs(outdir, exist_ok=True); n = b.n; W, KIND, TEACH, CAP = b["brainWeights"], b["brainKind"], b["teachMode"], b["lessonCap"]
    print(f"{b.name}: gate 4, save, drain and reuse")
    log = []; saved = None; wraps = 0; total_lessons = 0; all_ok = True; last_write = 0
    for k in range(2):
        m = Machine(b); m.do(EPISODES[2][1] if k == 0 else EPISODES[0][1])
        if saved: m.do(po(b["brainMarker"], saved))
        m.do(po(CAP, w16(40)) + f"poke:{KIND:X}:01,poke:{TEACH:X}:01,wait:1")
        if saved is None: saved = slot(m, b)
        drv = cu.PortDriver(m)
        def on_tick(m, f):
            nonlocal saved, all_ok, wraps, last_write
            st = ring_state(m, b)
            if st["write"] // 40 > last_write // 40: wraps += 1
            last_write = st["write"]
            if st["write"] - st["read"] >= 30:
                if drv.held: m.do(f"release:{drv.held}"); drv.held = 0
                saved, good = drain(m, b, saved, log); all_ok &= good
        chatter_frames(m, b, drv, 640, on_tick)
        m.do(f"poke:{TEACH:X}:00,wait:1"); st = ring_state(m, b)
        if st["write"] > st["read"]: saved, good = drain(m, b, saved, log); all_ok &= good
        total_lessons += st["write"]; last_write = 0; m.close()
    check(all_ok and len(log) >= 6 and wraps >= 3, f"{len(log)} drains over 2 sessions, {total_lessons} lessons, {wraps} ring wraps at capacity 40: every acknowledgement accepted and every replay equal to the machine byte for byte")
    check(all(l["hash_machine"] == l["hash_replay"] for l in log), "the behavioural hash of the machine's slot equals the replay's after every drain")
    edu = [l["education_machine"] for l in log]
    check(all(a <= c for a, c in zip(edu, edu[1:])) and edu[-1] == sum(l["drained"] for l in log), f"the education count runs across sessions and drains: {edu[-1]} lessons applied over the whole run, {sum(l['drained'] for l in log)} drained")
    m = Machine(b); m.do(EPISODES[2][1] + po(CAP, w16(12)) + f"poke:{KIND:X}:01,poke:{TEACH:X}:01,wait:1"); saved0 = slot(m, b)
    drv = cu.PortDriver(m); chatter_frames(m, b, drv, 120); st = ring_state(m, b)
    v = m.do("sync," + pk(b["cloneFlashColour"]))
    check(st["write"] == 12 and st["write"] - st["read"] == 12 and (st["status"] & 1) and st["education"] == 12, f"capacity 12 with no drain after 30 chattering ticks: {st['write']} lessons recorded, the ring full (status ${st['status']:02x}), education {st['education']}: learning paused; the last flash colour {v[0]} (2 is red)")
    m.do(po(b["lessonAckSeq"], w16(st["write"])) + po(b["lessonAckSum"], w16((st["cumWrite"] - st["cumRead"] + 1) & 0xffff)) + f"poke:{b['lessonAckRequest']:X}:01,wait:2"); bad1 = ring_state(m, b)
    m.do(po(b["lessonAckSeq"], w16(st["write"] - 1)) + po(b["lessonAckSum"], w16((st["cumWrite"] - st["cumRead"]) & 0xffff)) + f"poke:{b['lessonAckRequest']:X}:01,wait:2"); bad2 = ring_state(m, b)
    check(bad1["read"] == st["read"] and (bad1["status"] & 4) and bad2["read"] == st["read"] and (bad2["status"] & 2), f"a wrong checksum is refused (status ${bad1['status']:02x}) and a stale range is refused (status ${bad2['status']:02x}); nothing reclaimed")
    saved0, good = drain(m, b, saved0, log); chatter_frames(m, b, drv, 60); st2 = ring_state(m, b)
    check(good and st2["write"] > 12 and not (st2["status"] & 1), f"after the right acknowledgement learning resumes: {st2['write']} lessons, status ${st2['status']:02x}")
    m.close()
    results = []
    for cap in (300, 40):
        m = Machine(b); m.do(EPISODES[2][1] + po(CAP, w16(cap)) + f"poke:{KIND:X}:01,poke:{TEACH:X}:01,wait:1")
        drv = cu.PortDriver(m); saved_e = slot(m, b); dlog = []
        def on_tick(m, f):
            nonlocal saved_e
            st = ring_state(m, b)
            if st["write"] - st["read"] >= 30 or (cap == 300 and st["write"] % 30 == 0 and st["write"] > 0 and f % 4 == 0 and st["write"] != on_tick.last):
                on_tick.last = st["write"]
                if drv.held: m.do(f"release:{drv.held}"); drv.held = 0
                if cap == 40: saved_e, good = drain(m, b, saved_e, dlog)
                else: dummy_drain(m, b)
        on_tick.last = -1
        chatter_frames(m, b, drv, 720, on_tick); m.do(f"poke:{TEACH:X}:00,wait:1")
        st = ring_state(m, b); final = slot(m, b); m.close()
        results.append(dict(cap=cap, lessons=st["write"], drains=len(dlog), hash=ref.brain_hash(final), education=ref.parse_slot(final)["education"], weights=ref.parse_slot(final)["weights"]))
    a, c = results
    diff = sum(1 for ra, rc in zip(a["weights"], c["weights"]) for x, y in zip(ra, rc) if x != y)
    check(a["weights"] == c["weights"] and a["education"] == c["education"] and a["hash"] == c["hash"], f"the identical script uninterrupted ({a['lessons']} lessons, no drain) and split ({c['lessons']} lessons, {c['drains']} drains): the same weights ({diff} bytes differ), education {a['education']} = {c['education']}, hashes {a['hash'][:16]} = {c['hash'][:16]}")
    json.dump(dict(cycles=log, equivalence=[{k: v for k, v in r.items() if k != "weights"} for r in results]), open(os.path.join(outdir, f"drain-{b.name}.json"), "w"), indent=1)
    return ok

def gate_teach(b, outdir):
    """gate 3: the E5 story on BRAIN02 through the real control path, then save/reload, then the number"""
    global ok
    os.makedirs(outdir, exist_ok=True); n = b.n; W, KIND, TEACH, WS, EDU = b["brainWeights"], b["brainKind"], b["teachMode"], b["lessonWriteSeq"], b["brainEducation"]
    SNAP = "sync," + pk(b["physPlayerX"], 2) + pk(b["cloneX"], 2) + pk(KIND) + pk(TEACH) + pk(WS, 2) + pk(EDU, 2) + pk(b["buildCount"]) + pk(b["cloneFlash"]) + pk(b["cloneFlashColour"]) + pk(b["buddyColourNow"])
    PER = 14
    def row(v, k):
        d = v[k * PER:(k + 1) * PER]
        return dict(px=d[0] | d[1] << 8, cx=d[2] | d[3] << 8, kind=d[4], teach=d[5], lessons=d[6] | d[7] << 8, edu=d[8] | d[9] << 8, bricks=d[10], flash=d[11], colour=d[12], bcol=d[13])
    print(f"{b.name}: gate 3, TEACH end to end")
    v, _ = b.run("wait:300," + SNAP + "joy:8:60,wait:100," + SNAP)
    a, c = row(v, 0), row(v, 1)
    check(a["kind"] == 0 and a["teach"] == 0 and a["lessons"] == 0 and a["edu"] == 0, "a fresh boot: kind 0, no lessons, education 0")
    check(abs(c["px"] - c["cx"]) < 52 and c["px"] > 270, f"kind 0 follows: Tony at {c['px']}, the clone at {c['cx']}")
    v, _ = b.run("wait:300," + f"poke:{TEACH:X}:01,hold:4,wait:30,release:4,wait:2," + SNAP + f"poke:{TEACH:X}:00,wait:150," + SNAP + pk(W, 10 * n))
    a, c = row(v, 0), row(v, 1); wts = v[2 * PER:2 * PER + 10 * n]
    check(a["teach"] == 1 and a["px"] == 184 and a["cx"] < 130, f"TEACH by the flag: Tony stands at {a['px']}, the stick walks the clone left to {a['cx']} (Tony stays to his right)")
    check(a["lessons"] >= 1 and a["kind"] == 1 and a["edu"] == a["lessons"], f"lessons taken: {a['lessons']} (education {a['edu']}); the first made him kind {a['kind']}")
    check(any(wts), f"BRAIN02's weights changed ({sum(1 for x in wts if x)} of {10 * n} bytes set)")
    check(c["teach"] == 0 and c["cx"] < a["cx"] - 30, f"let go: taught 'left' (away from Tony) he keeps walking left on his own brain, {a['cx']} -> {c['cx']}, where the follow rule would have walked right to Tony at {c['px']}")
    v, _ = b.run("wait:300,hold:18,wait:60,release:18,wait:10," + SNAP + "hold:18,wait:60,release:18,wait:10," + SNAP)
    a, c = row(v, 0), row(v, 1)
    check(a["teach"] == 1 and a["bricks"] == 0 and c["teach"] == 0 and c["bricks"] == 0, f"the chord held a second toggles teaching on and off, the brick taken back each time (bricks {a['bricks']}, {c['bricks']})")
    v, _ = b.run("wait:300," + f"poke:{TEACH:X}:01,hold:4,wait:3," + SNAP + "wait:1," + SNAP)
    a, c = row(v, 0), row(v, 1)
    check((a["flash"] > 0 and a["colour"] == 1) or (c["flash"] > 0 and c["colour"] == 1), f"a press is an edge: its lesson is taken at once and flashes him white (flash {a['flash']}, colour {a['colour']}, lessons {a['lessons']})")
    v, _ = b.run("wait:300," + SNAP + pk(W, 10 * n))
    a = row(v, 0); wts = v[PER:PER + 10 * n]
    check(a["kind"] == 0 and not any(wts) and a["edu"] == 0, "the untouched PRG forgets: a fresh boot is kind 0 with zero weights and education 0")
    # the number: sessions of follow-and-climb from zero with the builder's rule as the teacher (E5's step 6)
    def teacher_lines(sn):
        dx, dy, facing, ground, air, ladder, wallFoot, wallHead, ladderHere = sn[1], sn[2], sn[3], sn[4], sn[5], sn[6], sn[9], sn[10], sn[12]
        if air: return 0
        if ladder: return 1 if dy > 0 else 0
        if dy > 0 and ladderHere: return 1
        if abs(dx) >= 2 or dy >= 2:
            d = 8 if dx > 0 else 4 if dx < 0 else (8 if facing else 4)
            if wallFoot and not wallHead and ((d == 8) == bool(facing)): return d | 16
            return d
        return 0
    lessons_total = 0; reached = None; saved = None; story = []
    for k in range(1, 11):
        m = Machine(b); m.do(STAIRS_C33)
        if saved: m.do(po(b["brainMarker"], saved))
        m.do(f"poke:{KIND:X}:01,poke:{TEACH:X}:01"); held = 0; top = None
        for step in range(150):
            d = senses(m, b); lines = teacher_lines(d["senses"])
            if lines != held:
                m.do((f"release:{held}," if held else "") + (f"hold:{lines}" if lines else "wait:0")); held = lines
            m.do("wait:4")
            if (d["cs"] & 0x7f) in (2, 7) and d["cy"] <= d["py"] + 8: top = step; break
        if held: m.do(f"release:{held}")
        m.do(f"poke:{TEACH:X}:00,wait:2"); st = ring_state(m, b); lessons_total += st["write"]; saved = slot(m, b); m.close()
        m = Machine(b); m.do(STAIRS_C33 + po(b["brainMarker"], saved) + "wait:480"); a2 = senses(m, b); m.close()
        on_ladder = (a2["cs"] & 0x7f) in (2, 7) and a2["cy"] <= a2["py"] + 16
        story.append(dict(session=k, lessons=st["write"], taught_to_y=None, alone_y=a2["cy"], alone_x=a2["cx"], climbs=on_ladder)); print(f"       session {k}: {st['write']} lessons; alone after it: Y {a2['cy']}, X {a2['cx']}, state {a2['cs']}" + ("  <- climbs to Tony" if on_ladder else ""))
        if on_ladder: reached = (k, lessons_total); break
    check(reached is not None, f"he climbs the stairs and the ladder to Tony on his own after {reached[0] if reached else '?'} session(s), {reached[1] if reached else lessons_total} lessons from zero")
    if reached:
        open(os.path.join(outdir, f"climbed-{b.name}.bin"), "wb").write(saved)
        m = Machine(b); m.do(STAIRS_C33 + po(b["brainMarker"], saved) + "wait:480"); a3 = senses(m, b); st = ring_state(m, b); back = slot(m, b); m.close()
        on_ladder = (a3["cs"] & 0x7f) in (2, 7) and a3["cy"] <= a3["py"] + 16
        check(on_ladder and back == saved and ref.brain_hash(back) == ref.brain_hash(saved) and st["education"] == ref.parse_slot(saved)["education"], f"the saved brain reloaded on a fresh boot climbs to Tony again (Y {a3['cy']}, X {a3['cx']}); the slot reads back byte for byte, hash {ref.brain_hash(saved)[:16]}, education {st['education']}")
    json.dump(dict(sessions=story, lessons_to_climb=reached), open(os.path.join(outdir, f"teach-{b.name}.json"), "w"), indent=1)
    return ok

def gate_resources(b, outdir):
    """gate 2: sizes and addresses from the build, cycles and the raster over a teaching episode with a learned brain"""
    global ok
    os.makedirs(outdir, exist_ok=True); n = b.n; S = b.sym
    labels = sorted((a, nm) for nm, a in S.items() if 0x0800 <= a < 0xa000)
    def size_of(name):
        a = S[name]; nxt = [x for x, nm in labels if x > a]; return (nxt[0] - a) if nxt else None
    prg = open(b.prg, "rb").read(); load = prg[0] | prg[1] << 8; off = S["brainMarker"] - load + 2
    pad = 0
    while off - pad - 1 >= 0 and prg[off - pad - 1] == 0: pad += 1
    r = dict(name=b.name, prg_size=b.size, sha256=b.sha, inputs=n, retina_id=b.retina, vocabulary=b.vocab, slot_bytes=S["BRAIN_BLOCK_SIZE"], header_bytes=24, weight_bytes=10 * n, mood_bytes=10,
             padding_before_marker_upper_bound=pad, retina_table_bytes=1 + 3 * n, flag_vector_ram=n, active_list_ram=n, pseudo_sense_ram=29, shadow_ram=10 * n, shadow_at=S["TEACH_SHADOW"],
             ring_at=S["LESSON_BLOCK"], ring_bytes=32 + 11 * 300, capacity=300, code_end=S["musicData"] - 1, headroom_below_shadow=S["TEACH_SHADOW"] - S["musicData"], headroom_above_ring=0xa000 - (S["LESSON_BLOCK"] + 32 + 11 * 300),
             code_bytes={k: size_of(k) for k in ("brainRetina", "brainForward", "brainLearn", "bodyThink", "testInputs", "gapStats", "brainCheck", "teachLesson", "lessonAck", "copyWeights", "teachShadowSave", "teachShadowRestore", "lessonInit", "profInit", "profRead", "profBegin", "profEnd")},
             accumulator_bound=128 * n + 128)
    # the dynamic numbers: the stairs episode with Phase 2b's learned weights, teaching on, a chord hold (the snapshot and the restore), one drain
    P2 = json.load(open(os.path.join(ROOT, "deliverables/bakeoff/phase2b.json"))); arm = {1: "R0", 2: "R1b", 3: "R0s"}.get(b.retina)
    Wl = P2[f"{arm}|{'rel' if b.vocab else 'abs'}|8|S2u"]["weights"] if arm else [[0] * n for _ in range(10)]
    m = Machine(b); m.do(STAIRS_C33 + po(b["brainWeights"], bytes(v & 255 for row in Wl for v in row)) + f"poke:{b['brainKind']:X}:01,poke:{b['teachMode']:X}:01,wait:1")
    saved = slot(m, b)                                                  # the brain before any lesson: the replay starts here
    drv = cu.PortDriver(m); teach_frames(m, b, drv, 400)
    m.do("hold:18,wait:60,release:18,wait:10")                          # the chord: a snapshot, then the restore at the toggle (teaching goes off)
    m.do(f"poke:{b['teachMode']:X}:01,wait:1"); teach_frames(m, b, drv, 200)
    st = ring_state(m, b); log = []; saved, good = drain(m, b, saved, log)
    v = m.do("sync," + pk(S["profThink"], 4) + pk(S["profLesson"], 4) + pk(S["profShadow"], 4) + pk(S["profDrain"], 4) + pk(S["profThinkPure"], 4) + pk(S["profLessonPure"], 4) +
             pk(S["bodyRasterMax"]) + (pk(S["bodyOverruns"]) if "bodyOverruns" in S else "") + pk(S["gapMin"], 2) + pk(S["gapMax"], 2) + pk(S["gapSum"], 4) + pk(S["gapCount"], 2) + pk(S["brainThinks"], 2))
    m.close()
    r.update(think_cycles_last=v[0] | v[1] << 8, think_cycles_max=v[2] | v[3] << 8, lesson_cycles_last=v[4] | v[5] << 8, lesson_cycles_max=v[6] | v[7] << 8, shadow_cycles_last=v[8] | v[9] << 8, shadow_cycles_max=v[10] | v[11] << 8,
             drain_cycles_last=v[12] | v[13] << 8, drain_cycles_max=v[14] | v[15] << 8, think_pure_last=v[16] | v[17] << 8, think_pure_max=v[18] | v[19] << 8, lesson_pure_last=v[20] | v[21] << 8, lesson_pure_max=v[22] | v[23] << 8)
    i = 24; r["raster_max"] = v[i]; i += 1
    if "bodyOverruns" in S: r["overruns"] = v[i]; i += 1
    gmin, gmax = s16(v[i], v[i + 1]), s16(v[i + 2], v[i + 3]); gsum = v[i + 4] | v[i + 5] << 8 | v[i + 6] << 16 | v[i + 7] << 24; gcount = v[i + 8] | v[i + 9] << 8; thinks = v[i + 10] | v[i + 11] << 8
    r.update(gap_min=gmin, gap_max=gmax, gap_mean=(gsum / gcount if gcount else None), gap_count=gcount, thinks=thinks, lessons_in_episode=st["write"], drain_ok=good)
    # the pure think and lesson through the hooks on recorded blocks (the interrupts held off): the work itself
    blocks, D = blocks_all(); test = sorted(D["s474"])[::12]
    script = "wait:300," + f"poke:{b['brainTestMode']:X}:00," + po(b["brainWeights"], bytes(v & 255 for row in Wl for v in row))
    for x in test: script += po(b["brainTestIn"], xb(x)) + f"poke:{b['brainTestRun']:X}:01,wait:2,sync," + pk(S["profThinkPure"], 2)
    for x in test[:20]: script += po(b["brainTestIn"], xb(x)) + f"poke:{b['brainLearnTestT']:X}:09,poke:{b['brainLearnRun']:X}:01,wait:2,sync," + pk(S["profLessonPure"], 2)
    v, out = b.run(script); tp = [v[2 * k] | v[2 * k + 1] << 8 for k in range(len(test))]; lp = [v[2 * len(test) + 2 * k] | v[2 * len(test) + 2 * k + 1] << 8 for k in range(20)]
    r.update(think_pure_hook_min=min(tp), think_pure_hook_mean=sum(tp) / len(tp), think_pure_hook_max=max(tp), lesson_pure_hook_min=min(lp), lesson_pure_hook_mean=sum(lp) / len(lp), lesson_pure_hook_max=max(lp))
    json.dump(r, open(os.path.join(outdir, f"resources-{b.name}.json"), "w"), indent=1)
    for k, v2 in r.items():
        if k != "code_bytes": print(f"  {k}: {v2}")
    print("  code bytes:", r["code_bytes"])
    check(r["headroom_below_shadow"] > 0 and r["headroom_above_ring"] >= 0, "the code ends below the shadow and the ring ends below $a000")
    check(r["raster_max"] <= 230 and r.get("overruns", 0) == 0, f"raster maximum {r['raster_max']} (limit 230), overruns {r.get('overruns', 'n/a')}")
    check(r["think_pure_hook_max"] < 19656 and r["lesson_pure_hook_max"] < 19656, f"the think ({r['think_pure_hook_max']} cycles at most) and the lesson ({r['lesson_pure_hook_max']}) each inside one frame of main-loop time")
    check(good, "the drain in the episode accepted and replayed equal")
    return ok

if __name__ == "__main__" and sys.argv[1] in ("resources", "teach", "drain"):
    b = Build(sys.argv[2]); outdir = os.path.join(ROOT, "deliverables/bakeoff/phase3")
    f = {"resources": gate_resources, "teach": gate_teach, "drain": gate_drain}[sys.argv[1]]
    sys.exit(0 if f(b, outdir) else 1)

# --------------------------------------------------------------------------- the workbench descriptor
def descriptor(b, commit):
    """a machine-readable descriptor of one research PRG for the Akalabeth workbench (WORKBENGH-INTEGRATION.md):
    identities, every address the contract names, the block layouts, and the three access lists"""
    S = b.sym; n = b.n
    entries = ref.TABLES[b.retina][1]() if b.retina else []
    d = dict(
        schema="tony-brain02-descriptor/1", filename=os.path.basename(b.prg), sha256=b.sha, prg_size=b.size, engine_commit=commit,
        candidate={"tony-b02-a": "A: R1b, reference-relative", "tony-b02-b": "B: R0s, reference-relative", "tony-b02-drel": "diagnostic: R0, reference-relative", "tony-b02-dabs": "diagnostic: R0, absolute", "tony-b02-p128": "parity build, 128 inputs, not a candidate"}.get(b.name, b.name),
        load_address=0x0801, machine="Commodore 64 PAL; Minimal64 and VICE; a plain PRG",
        brain=dict(marker="BRAIN02\\0", marker_address=S["brainMarker"], slot_bytes=S["BRAIN_BLOCK_SIZE"], layout=2, rule_version=2, inputs=n, outputs=10, vocabulary=b.vocab, retina_id=b.retina,
                   header=dict(kind=S["brainKind"], layout=S["brainLayout"], inputs=S["brainInputCount"], hidden=S["brainHiddenCount"], outputs=S["brainOutputCount"], period=S["brainPeriod"], lineage=S["brainLineage"], rule=S["brainRule"],
                               vocabulary=S["brainVocab"], retina_id=S["brainRetinaId"], education_count=S["brainEducation"], education_bytes=2, reserved=S["brainEducation"] + 2),
                   weights=S["brainWeights"], weight_bytes=10 * n, weight_layout="row o at weights + o * inputs, one signed byte per flag (two's complement)", mood=S["brainMood"], mood_bytes=10,
                   hash_domains=dict(behavioural="bytes 8..12, 16..17 and the weights, in slot order, SHA-256 (brain_hash)", provenance="lineage, rule version, education count", timing_render="period, mood")),
        retina=dict(id=b.retina, name=ref.TABLES[b.retina][0] if b.retina else "none", table_address=S["retinaTable"], table_bytes=1 + 3 * n, table_layout="count, then ops[n], operands a[n], k-or-b[n] (the published triples stored as three arrays)",
                    ops=["GE: sense[a] >= k (signed)", "LE: sense[a] <= k (signed)", "EQN: (sense[a] & 15) == k", "AND(a,b)", "ANDNOT(a,b)", "OR(a,b)", "XNOR(a,b)"], flag_names=ref.flag_names(entries),
                    pseudo_senses={20 + i: nm for i, nm in enumerate(ref.PSEUDO)}, reference_vector="refDx, refDy = senses 1 and 2 (the player's offset) in this build; h = sign(refDx), or the facing when zero",
                    flag_vector=S["brainFlags"], flag_vector_bytes=n, active_list=S["brainActive"], active_count=S["brainActiveCount"], values=S["brainVals"], values_bytes=29),
        live=dict(predicted_output=S["brainOutput"], resolved_action=S["brainAction"], h_right=S["brainH"], applied_action="sensePack+16 (the applied action of the frame being packed)", applied_action_address=S["sensePack"] + 16,
                  taught_action=S["brainTaught"], taught_raw=S["brainTaughtRaw"], predicted_at_lesson=S["brainPredicted"], lesson_taken=S["brainLearned"], kind_now=S["brainKindNow"],
                  think_count=S["brainThinks"], think_count_bytes=2, accumulators=S["brainAcc"], accumulators_layout="ten signed 16-bit little-endian, acc[o] at 2o", score_gap=S["brainGap"],
                  senses=S["cloneSenses"], senses_bytes=20, senses_frame=S["cloneSensesFrame"], senses_layout="one byte per sense, the signed nibble in the low four bits (8..15 negative)", think_input=S["brainIn"],
                  clone_x=S["cloneX"], clone_y=S["cloneY"], clone_state=S["cloneState"], player_x=S["physPlayerX"], player_y=S["physPlayerY"], player_state=S["physPlayerState"], bricks=S["buildCount"],
                  flash_frames=S["cloneFlash"], flash_colour=S["cloneFlashColour"], flash_colours={1: "white: a lesson", 2: "red: a lesson refused, the ring is full"}, teach_mode=S["teachMode"], teach_hold=S["teachHold"],
                  shadow_request=S["shadowRequest"], shadow_restore_request=S["shadowRestoreRequest"], shadow_valid=S["shadowValid"], shadow_at=S["TEACH_SHADOW"], shadow_bytes=10 * n,
                  raster_max=S["bodyRasterMax"], overruns=S.get("bodyOverruns"), frames=S["bodyFrames"], seed_bytes="the parameter block: 32 seed bytes after the MURAL02 marker (tools/stamp_mural.py)", mural_marker=S.get("muralMarker")),
        profiler=dict(think=S["profThink"], think_max=S["profThinkMax"], lesson=S["profLesson"], lesson_max=S["profLessonMax"], shadow=S["profShadow"], shadow_max=S["profShadowMax"], drain=S["profDrain"], drain_max=S["profDrainMax"],
                      think_pure=S["profThinkPure"], think_pure_max=S["profThinkPureMax"], lesson_pure=S["profLessonPure"], lesson_pure_max=S["profLessonPureMax"], unit="CPU cycles, 16-bit; the live counts include interrupts, the pure ones (test hooks) do not",
                      gap_min=S["gapMin"], gap_max=S["gapMax"], gap_sum=S["gapSum"], gap_count=S["gapCount"]),
        lessons=dict(marker="LESSON2\\0", marker_address=S["lessonMarker"], block_bytes=32 + 11 * 300, write_seq=S["lessonWriteSeq"], read_seq=S["lessonReadSeq"], capacity=S["lessonCap"], capacity_default=300, entry_size=S["lessonSize"], entry_bytes=11,
                     status=S["lessonStatus"], status_bits={0: "full, learning paused", 1: "last ack rejected: stale range", 2: "last ack rejected: bad checksum", 3: "last ack rejected: a chord hold in progress", 7: "last ack accepted"},
                     ack_seq=S["lessonAckSeq"], ack_sum=S["lessonAckSum"], ack_request=S["lessonAckRequest"], drains=S["lessonDrains"], cum_write=S["lessonCumWrite"], cum_read=S["lessonCumRead"], data=S["lessonData"],
                     entry_layout="bytes 0..9: the twenty sense nibbles, nibble i in byte i/2, the low nibble for even i; byte 10: the taught absolute action in the low nibble, the predicted raw output in the high nibble",
                     slot_rule="the lesson with sequence s is at data + (s mod capacity) * 11; unread lessons are [read_seq, write_seq)",
                     drain_procedure=["read read_seq, write_seq", "read the entries [read_seq, write_seq)", "sum every byte of those entries modulo 65536", "write ack_seq = write_seq, ack_sum = the sum, then ack_request = 1", "wait one frame; read status: bit 7 accepted (read_seq == write_seq), else bits 1..3 say why; re-read and retry on a stale range"],
                     replay="per lesson: unpack the senses, derive the flags with the retina table, the taught raw index (translate the absolute action with h of the block under the relative vocabulary), apply the rule; the result must equal the machine's weights and education count"),
        test_hooks=dict(test_in=S["brainTestIn"], test_mode=S["brainTestMode"], test_run=S["brainTestRun"], test_flags=S["brainTestFlags"], test_acc=S["brainTestAcc"], test_output=S["brainTestOutput"], test_action=S["brainTestAction"], test_h=S["brainTestH"],
                        learn_run=S["brainLearnRun"], learn_t=S["brainLearnTestT"], learn_p=S["brainLearnTestP"], learn_took=S["brainLearnTestTook"], learn_trel=S["brainLearnTestTrel"], note="research only: the hooks run the machine's own retina, forward pass and rule on supplied inputs; they change the slot's weights and education count when a lesson is taken"),
        access=dict(
            observation="everything above may be read at any time; read write_seq before and after a read of the weights to know no lesson intervened",
            research_control=dict(teach_mode="0/1: the same as the chord", ack_fields="ack_seq, ack_sum, ack_request: the drain handshake", capacity="may be lowered at boot before any lesson (research only)",
                                  slot="the whole slot may be written at boot to load a saved brain (marker, header, weights, mood); zeroing the weights and the education count and kind 0 is a reset", seed_bytes="the parameter block, at boot",
                                  test_hooks="research only, absent from production semantics"),
            cognition="the retina, the forward pass, the resolution, the rule and the lesson recording run only in the machine; the host never computes a prediction, chooses an action, derives a flag for him or writes a weight outside a load or reset"),
        session_trace=dict(observe_per_frame=["frames", "teach_mode", "clone_x", "clone_y", "clone_state", "player_x", "player_y", "player_state", "applied_action", "predicted_output", "resolved_action", "write_seq", "flash_colour"],
                           observe_per_lesson=["the new ring entry (senses, taught, predicted)", "education_count", "the weights that changed (a diff of the two rows)"],
                           events=["teach on/off (by the chord or the flag)", "drain (ack accepted, the batch and its replay result)", "brain load", "brain reset", "capacity change"],
                           derived=["wall-clock to first visible improvement", "active teaching time", "lessons per minute", "deliberate edges (applied action changes)", "corrections (lessons whose predicted output differed from the taught index)", "aliasing (the same senses taught two actions)", "lag (press against state change)", "competence on release", "competence after reload"]))
    return d
if __name__ == "__main__" and sys.argv[1] == "descriptor":
    b = Build(sys.argv[2]); commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    outdir = os.path.join(ROOT, "deliverables/bakeoff/workbench"); os.makedirs(outdir, exist_ok=True)
    d = descriptor(b, commit); json.dump(d, open(os.path.join(outdir, f"{b.name}.json"), "w"), indent=1); print(f"wrote {outdir}/{b.name}.json")
