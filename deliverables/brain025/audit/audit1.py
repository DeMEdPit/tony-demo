#!/usr/bin/env python3
"""AUDIT 1. The chord toggle in Candidate A fires teachShadowRestore. Is the rollback atomic?
Snapshot the whole learned state before the hold, after lessons land, and after the toggle."""
import hashlib, os, re, subprocess, sys, tempfile
ROOT="/home/user/tony-demo"; G="/tmp/claude-0/-home-user-tony-demo/c7c8bdb1-08b2-5026-9106-bb75e5d7e5a0/scratchpad/a1"
os.makedirs(G, exist_ok=True)
name = sys.argv[1] if len(sys.argv)>1 else "tony-b02-a"
S={}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(f"{ROOT}/src/kickass/{name}.sym").read()): S.setdefault(m.group(1),int(m.group(2),16))
WB=S["B02_WEIGHT_BYTES"]
def pk(a,n=1): return "".join(f"peek:{a+i:X}," for i in range(n))
def po(a,d): return "".join(f"poke:{a+i:X}:{b&255:02X}," for i,b in enumerate(d))
# the whole learned + ring state, in one readable block
FIELDS=[("education",S["brainEducation"],2),("kind",S["brainKind"],1),("writeSeq",S["lessonWriteSeq"],2),
        ("readSeq",S["lessonReadSeq"],2),("cumWrite",S["lessonCumWrite"],2),("cumRead",S["lessonCumRead"],2),
        ("status",S["lessonStatus"],1),("drains",S["lessonDrains"],1),("writeSlot",S["lessonWriteSlot"],2),
        ("writePtr",S["lessonWritePtr"],2),("teachMode",S["teachMode"],1),("shadowValid",S["shadowValid"],1),
        ("notPaired",S["lessonNotPaired"],2)]
SNAP="".join(pk(a,n) for _,a,n in FIELDS)
def snap(tag): return f"sync,{SNAP}dump:{S['brainWeights']:X}:{WB:X}:{G}/{tag}-w.bin,dump:{S['lessonData']:X}:100:{G}/{tag}-l.bin,"
def parse(v,k):
    o=k*sum(n for _,_,n in FIELDS); out={}
    for nm,_,n in FIELDS:
        out[nm]=v[o] if n==1 else v[o]|v[o+1]<<8; o+=n
    return out
def run(script):
    with tempfile.NamedTemporaryFile("w",suffix=".m64",delete=False) as f: f.write(script)
    r=subprocess.run([f"{ROOT}/tools/m64-harness/m64run",f"{ROOT}/src/kickass/{name}.prg","@"+f.name],capture_output=True,text=True)
    os.unlink(f.name); return [int(m,16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)",r.stdout)]
CHORD=18  # down + fire
HOLD=60   # TEACH_HOLD_FRAMES is 50
script=("wait:400,"
        # 1. into TEACH by the chord, then let go
        f"hold:{CHORD},wait:{HOLD},release:{CHORD},wait:20," + snap("A")
        # 2. teach: a second chord hold. Its first frame snapshots; lessons land during it; frame 50 toggles out
        + f"hold:{CHORD},wait:20," + snap("B")
        + f"wait:{HOLD},release:{CHORD},wait:20," + snap("C"))
v=run(script)
rows=[parse(v,k) for k in range(3)]
labels=["A  teaching, before the hold","B  mid-hold, lessons landing","C  after the toggle-out"]
print(f"{name}: the chord toggle's rollback\n")
keys=[nm for nm,_,_ in FIELDS]
print(f"{'':30}" + "".join(f"{k:>11}" for k in keys))
for lab,r in zip(labels,rows): print(f"{lab:30}" + "".join(f"{r[k]:>11}" for k in keys))
print()
for tag in ("A","B","C"):
    w=open(f"{G}/{tag}-w.bin","rb").read(); l=open(f"{G}/{tag}-l.bin","rb").read()
    print(f"  {tag}: weights sha256 {hashlib.sha256(w).hexdigest()[:16]}   nonzero {sum(1 for x in w if x)}/{len(w)}"
          f"   first 256 lesson bytes sha256 {hashlib.sha256(l).hexdigest()[:16]}")
wa,wb,wc=(open(f"{G}/{t}-w.bin","rb").read() for t in ("A","B","C"))
la,lb,lc=(open(f"{G}/{t}-l.bin","rb").read() for t in ("A","B","C"))
print()
print(f"  weights  B vs A: {sum(1 for x,y in zip(wa,wb) if x!=y)} bytes differ    C vs A: {sum(1 for x,y in zip(wa,wc) if x!=y)} bytes differ")
print(f"  lessons  B vs A: {sum(1 for x,y in zip(la,lb) if x!=y)} bytes differ    C vs A: {sum(1 for x,y in zip(la,lc) if x!=y)} bytes differ")
print()
print("  VERDICT: " + ("weights and counters BOTH returned to A - the rollback is atomic"
      if wc==wa and rows[2]["education"]==rows[0]["education"] and rows[2]["writeSeq"]==rows[0]["writeSeq"]
      else "MISMATCH - weights and counters did NOT return together"))
