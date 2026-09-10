#!/usr/bin/env python3
"""
brain_golden.py - the golden vectors for BRAIN-INTERFACE-V1 and the Python reference they are made with.

  python3 tools/brain_golden.py write        writes deliverables/golden/{forward,lessons,mood}.json
  python3 tools/brain_golden.py check PRG    drives the 6502 through its test hooks on every case and counts the differences

The reference (forward, learn) is the whole rule: three functions anyone can read. Every implementation
(this one, the 6502, the Solidity) must produce exactly these outputs on these inputs.

Encodings in the files: weights and moods are hex strings of the packed nibbles (two per byte, the first of
each pair in the low nibble; a row's twenty weights are ten bytes, output o at bytes o*10..o*10+9; the
mood's ten nibbles are five bytes); senses and actions are plain integers (senses -8..7).
"""
import json, os, random, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N, O = 20, 10

def sx(n): return n - 16 if n >= 8 else n                       # a nibble as a signed value
def pack(nibbles): return bytes((nibbles[i] & 15) | ((nibbles[i + 1] & 15) << 4) for i in range(0, len(nibbles), 2))
def unpack(data, count): return [sx((data[i // 2] >> (4 * (i & 1))) & 15) for i in range(count)]
def w_pack(w): return pack([w[o][i] for o in range(O) for i in range(N)]).hex()
def w_unpack(h): flat = unpack(bytes.fromhex(h), O * N); return [flat[o * N:(o + 1) * N] for o in range(O)]
def m_pack(m): return pack(m).hex()
def m_unpack(h): return unpack(bytes.fromhex(h), O)

def forward(w, x, mood):
    """acc[o] = sum w[o][i] * x[i] + mood[o] * 16; the action is the first largest."""
    acc = [sum(w[o][i] * x[i] for i in range(N)) + mood[o] * 16 for o in range(O)]
    return acc, max(range(O), key=lambda o: (acc[o], -o))

def clamp(v): return max(-8, min(7, v))

def learn(w, x, t):
    """One lesson: the mood-free prediction p; if p != t, w[t][i] += sgn(x[i]) and w[p][i] -= sgn(x[i]) for x[i] != 0,
    saturating. Returns (p, taken); w is changed in place."""
    _, p = forward(w, x, [0] * O)
    if p == t: return p, False
    for i in range(N):
        if x[i] == 0: continue
        s = 1 if x[i] > 0 else -1
        w[t][i] = clamp(w[t][i] + s)
        w[p][i] = clamp(w[p][i] - s)
    return p, True

def replay(w, lessons):
    out = []
    for x, t in lessons: out.append(learn(w, x, t))
    return out

def write():
    rnd = random.Random(20260910)
    def rw(): return [[rnd.randint(-8, 7) for _ in range(N)] for _ in range(O)]
    def rx(): return [rnd.randint(-8, 7) for _ in range(N)]
    def rm(): return [rnd.randint(-8, 7) for _ in range(O)]
    # set 1: forward
    cases = []
    def add1(name, w, x, m):
        acc, a = forward(w, x, m)
        cases.append(dict(name=name, weights=w_pack(w), mood=m_pack(m), x=x, acc=acc, action=a))
    add1("all zero: the first output wins the tie", [[0] * N for _ in range(O)], [0] * N, [0] * O)
    add1("the most negative accumulators: 7 * -8 twenty times, mood -8", [[7] * N for _ in range(O)], [-8] * N, [-8] * O)
    add1("the most positive: -8 * -8 twenty times, mood 7", [[-8] * N for _ in range(O)], [-8] * N, [7] * O)
    w = [[0] * N for _ in range(O)]; w[3][0] = 5; w[7][0] = 5
    add1("a tie between outputs 3 and 7 goes to 3", w, [7] + [0] * (N - 1), [0] * O)
    w = [[0] * N for _ in range(O)]; w[9][1] = 1
    add1("one weight, one sense: output 9 by a single product", w, [7, 3] + [0] * (N - 2), [0] * O)
    w = [[0] * N for _ in range(O)]; w[2][0] = 1
    add1("the mood alone decides: mood 1 on output 5 (16) beats a product of 7", w, [7] + [0] * (N - 1), [0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
    for k in range(40): add1(f"random {k}", rw(), rx(), rm())
    json.dump(dict(set="forward", interface="BRAIN-INTERFACE-V1", inputs=N, outputs=O, cases=cases), open(os.path.join(ROOT, "deliverables/golden/forward.json"), "w"), indent=1)
    # set 2: lessons
    cases = []
    def add2(name, w, lessons):
        w0 = w_pack(w); res = replay(w, lessons)
        cases.append(dict(name=name, weights_before=w0, lessons=[dict(x=x, t=t) for x, t in lessons], weights_after=w_pack(w),
                          predictions=[p for p, _ in res], taken=[tk for _, tk in res]))
    add2("an empty batch", rw(), [])
    w = [[0] * N for _ in range(O)]
    add2("from zero, taught right with the player to the right: bias and dx rows move", w, [([7, 3] + [0] * (N - 2), 2)])
    w = [[0] * N for _ in range(O)]; w[2] = [7] * N
    add2("saturation at 7: the taught row stays at 7, the predicted row falls", w, [([7] * N, 2), ([7] * N, 2), ([7] * N, 1)])
    w = [[0] * N for _ in range(O)]; w[0] = [-8] * N; w[1] = [7] * N
    add2("saturation at -8: the predicted row 0 cannot fall below -8", w, [([7] * N, 3)])
    w = [[0] * N for _ in range(O)]; w[4][0] = 3
    add2("a no-op: the taught action is already predicted", w, [([7] + [0] * (N - 1), 4)])
    w = [[0] * N for _ in range(O)]
    add2("negative senses step the other way", w, [([-7, -3, 0, 5] + [0] * (N - 4), 6)])
    w = [[0] * N for _ in range(O)]; w[1][0] = 2
    m = [0] * O
    add2("a batch of six that flips a decision and then no-ops", w, [([7, 5] + [0] * (N - 2), 2)] * 6)
    for k in range(20):
        add2(f"random {k}", rw(), [(rx(), rnd.randint(0, O - 1)) for _ in range(rnd.randint(1, 8))])
    json.dump(dict(set="lessons", interface="BRAIN-INTERFACE-V1", inputs=N, outputs=O, cases=cases), open(os.path.join(ROOT, "deliverables/golden/lessons.json"), "w"), indent=1)
    # set 3: mood
    cases = []
    def add3(name, w, x, m, t):
        _, with_mood = forward(w, x, m); _, without = forward(w, x, [0] * O)
        cases.append(dict(name=name, weights=w_pack(w), mood=m_pack(m), x=x, action_with_mood=with_mood, action_without_mood=without,
                          taught=t, lesson_taken=(without != t)))
    w = [[0] * N for _ in range(O)]; w[2][0] = 2
    add3("mood flips the action (idle by mood 2 on output 0) while the mood-free prediction is the taught one: no lesson", w, [7] + [0] * (N - 1), [2] + [0] * (O - 1), 2)
    w = [[0] * N for _ in range(O)]; w[2][0] = 1
    add3("mood does not save a wrong prediction: the lesson is taken on the mood-free one", w, [7] + [0] * (N - 1), [0, 0, 7, 0, 0, 0, 0, 0, 0, 0], 5)
    for k in range(20):
        w, x, m = rw(), rx(), rm(); add3(f"random {k}", w, x, m, rnd.randint(0, O - 1))
    json.dump(dict(set="mood", interface="BRAIN-INTERFACE-V1", inputs=N, outputs=O, cases=cases), open(os.path.join(ROOT, "deliverables/golden/mood.json"), "w"), indent=1)
    print("wrote deliverables/golden/forward.json, lessons.json, mood.json")

def check(prg):
    SYM = {}
    for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(os.path.join(ROOT, "src/kickass/tony-body.sym")).read()):
        SYM.setdefault(m.group(1), int(m.group(2), 16))
    W, MOOD, TIN, TRUN, TACC, TACT = SYM["brainWeights"], SYM["brainMood"], SYM["brainTestIn"], SYM["brainTestRun"], SYM["brainTestAcc"], SYM["brainTestAction"]
    LRUN, LT, LP, LTOOK = SYM["brainLearnRun"], SYM["brainLearnTestT"], SYM["brainLearnTestP"], SYM["brainLearnTestTook"]
    def pk(addr, n): return "".join(f"peek:{addr + i:X}," for i in range(n))
    def po(addr, data): return "".join(f"poke:{addr + i:X}:{b:02X}," for i, b in enumerate(data))
    def run(script):
        with tempfile.NamedTemporaryFile("w", suffix=".m64", delete=False) as f: f.write(script)
        r = subprocess.run([os.path.join(ROOT, "tools/m64-harness/m64run"), prg, "@" + f.name], capture_output=True, text=True); os.unlink(f.name)
        return [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)]
    def xb(x): return bytes(v & 15 for v in x)
    bad = 0; total = 0
    # forward and mood: the forward hook
    for name in ("forward", "mood"):
        cases = json.load(open(os.path.join(ROOT, f"deliverables/golden/{name}.json")))["cases"]
        script = "wait:300,"
        for c in cases:
            script += po(W, bytes.fromhex(c["weights"])) + po(MOOD, bytes.fromhex(c["mood"])) + po(TIN, xb(c["x"])) + f"poke:{TRUN:X}:01,wait:2,sync," + pk(TACC, 20) + pk(TACT, 1)
            if name == "mood":      # and the mood-free prediction, through the learning hook with t = the taught action
                script += po(TIN, xb(c["x"])) + f"poke:{LT:X}:{c['taught']:02X},poke:{LRUN:X}:01,wait:2,sync," + pk(LP, 1) + pk(LTOOK, 1) + po(W, bytes.fromhex(c["weights"]))
        v = run(script); per = 21 if name == "forward" else 23
        for k, c in enumerate(cases):
            got = v[k * per:(k + 1) * per]; total += 1
            acc = [((got[2 * o] | (got[2 * o + 1] << 8)) ^ 0x8000) - 0x8000 for o in range(O)]
            if name == "forward":
                if acc != c["acc"] or got[20] != c["action"]: bad += 1; print(f"  differs: forward '{c['name']}': 6502 {acc} {got[20]}")
            else:
                if got[20] != c["action_with_mood"] or got[21] != c["action_without_mood"] or bool(got[22]) != c["lesson_taken"]:
                    bad += 1; print(f"  differs: mood '{c['name']}': 6502 with {got[20]} without {got[21]} taken {got[22]}")
    # lessons: the learning hook, one lesson at a time, the weights read back at the end
    cases = json.load(open(os.path.join(ROOT, "deliverables/golden/lessons.json")))["cases"]
    script = "wait:300,"
    for c in cases:
        script += po(W, bytes.fromhex(c["weights_before"]))
        for l in c["lessons"]:
            script += po(TIN, xb(l["x"])) + f"poke:{LT:X}:{l['t']:02X},poke:{LRUN:X}:01,wait:2,sync," + pk(LP, 1) + pk(LTOOK, 1)
        script += "sync," + pk(W, 100)
    v = run(script); i = 0
    for c in cases:
        total += 1; preds = []; took = []
        for l in c["lessons"]:
            preds.append(v[i]); took.append(bool(v[i + 1])); i += 2
        after = bytes(v[i:i + 100]).hex(); i += 100
        if after != c["weights_after"] or preds != c["predictions"] or took != c["taken"]:
            bad += 1; print(f"  differs: lessons '{c['name']}': predictions {preds} taken {took}")
    print(f"golden vectors: {total} cases, {total - bad} agree between the 6502 and the reference")
    return bad == 0

if __name__ == "__main__":
    if sys.argv[1:2] == ["write"]: write()
    elif sys.argv[1:2] == ["check"]: sys.exit(0 if check(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "deliverables/prg/minimal64/tony-body.prg")) else 1)
    else: print(__doc__)
