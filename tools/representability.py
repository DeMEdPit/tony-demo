#!/usr/bin/env python3
"""
representability.py - the exact check the curriculum experiment's pre-registration asks for: given a
set of labelled sense vectors (x -> t), does ANY legal weight matrix (10 x 20 signed nibbles, -8..7)
reproduce every label under the program's own rule (the first largest accumulator wins, ties to the
lowest index, mood zero)? An integer feasibility problem solved exactly with CBC (through pulp):

    for every labelled x and every output o != t:
        sum_i w[t][i] x_i  -  sum_i w[o][i] x_i  >=  1  if o < t   (o would win a tie)
                                                  >=  0  if o > t   (t wins a tie)

"feasible" means a representable solution exists (the learning rule may or may not find it);
"infeasible" means no 4-bit perceptron over these senses can reproduce the labels: a capacity limit
of the model class on these vectors, independent of any learning rule.

  python3 tools/representability.py LABELS.json [more.json ...]
     LABELS.json: a list of {"x": [20 ints], "t": int} (a lessons file, or a decisions file with
     "senses"/"action" keys). Duplicate vectors with the same label are merged; a vector with two
     labels is reported as a conflict and excluded (nothing can reproduce both).
"""
import json, sys, time
import pulp

def load(paths):
    labels, conflicts = {}, {}
    for p in paths:
        for r in json.load(open(p)):
            x = tuple(r["x"] if "x" in r else r["senses"]); t = r["t"] if "t" in r else r["action"]
            if x in labels and labels[x] != t: conflicts.setdefault(x, set()).update({labels[x], t})
            labels.setdefault(x, t)
    for x in conflicts: labels.pop(x, None)
    return labels, conflicts

def check(labels, time_limit=600):
    prob = pulp.LpProblem("representable", pulp.LpMinimize)
    w = [[pulp.LpVariable(f"w_{o}_{i}", -8, 7, cat="Integer") for i in range(20)] for o in range(10)]
    prob += 0
    n = 0
    for x, t in labels.items():
        for o in range(10):
            if o == t: continue
            prob += pulp.lpSum((w[t][i] - w[o][i]) * x[i] for i in range(20) if x[i] != 0) >= (1 if o < t else 0)
            n += 1
    t0 = time.time(); prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit))
    status = pulp.LpStatus[prob.status]
    W = [[int(round(w[o][i].value() or 0)) for i in range(20)] for o in range(10)] if status == "Optimal" else None   # a variable in no constraint is unset: zero
    return status, n, time.time() - t0, W

def verify(W, labels):
    """the solution replayed with the rule, as a check on the solver"""
    bad = 0
    for x, t in labels.items():
        acc = [sum(W[o][i] * x[i] for i in range(20)) for o in range(10)]
        if max(range(10), key=lambda o: (acc[o], -o)) != t: bad += 1
    return bad

def pack(W):
    out = bytearray(100)
    for o in range(10):
        for i in range(20):
            n = W[o][i] & 15
            out[o * 10 + i // 2] |= n if i % 2 == 0 else n << 4
    return bytes(out)

if __name__ == "__main__":
    labels, conflicts = load(sys.argv[1:])
    print(f"{len(labels)} labelled vectors ({len(conflicts)} conflicting vectors excluded: {[(list(x), sorted(v)) for x, v in list(conflicts.items())[:5]]})")
    status, n, dt, W = check(labels)
    print(f"{n} constraints, CBC says {status} in {dt:.1f} s")
    if W is not None: print(f"a representable weight matrix exists; replayed with the rule it mislabels {verify(W, labels)} vectors; max |w| {max(abs(v) for r in W for v in r)}")
    elif status == "Infeasible": print("no legal 4-bit weight matrix reproduces these labels under the rule")
    else: print("undecided within the time limit")
