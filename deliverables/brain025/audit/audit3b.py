#!/usr/bin/env python3
"""AUDIT 3 phase B. Two matched curricula, same lesson content ("step toward the player"), differing
only in the distance bucket the lessons were recorded in. Then both brains across the same bins."""
import importlib.util, json, os, re, sys
sys.argv=["x"]; ROOT="/home/user/tony-demo"; G="/tmp/claude-0/-home-user-tony-demo/c7c8bdb1-08b2-5026-9106-bb75e5d7e5a0/scratchpad"
s=importlib.util.spec_from_file_location("t", f"{ROOT}/tools/brain025_test.py"); t=importlib.util.module_from_spec(s); s.loader.exec_module(t)
ref=t.ref
S={}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(f"{ROOT}/src/kickass/tony-b025-a-vis3.sym").read()): S.setdefault(m.group(1),int(m.group(2),16))
b=t.Build(f"{ROOT}/src/kickass/tony-b025-a-vis3.prg")
def pk(a,n=1): return "".join(f"peek:{a+i:X}," for i in range(n))
def po(a,d): return "".join(f"poke:{a+i:X}:{x&255:02X}," for i,x in enumerate(d))
def sx(n): return n-16 if n>=8 else n
FLOOR=206
def read(m):
    v=m.do("sync,"+pk(S["cloneX"],2)+pk(S["physPlayerX"],2)+pk(S["cloneSenses"],27)+pk(S["brainEducation"],2))
    return dict(cx=v[0]|v[1]<<8, px=v[2]|v[3]<<8, dx=sx(v[4+1]), edu=v[31]|v[32]<<8)

def curriculum(player_x, want, bouts, label):
    """teach 'walk toward the player' only while the separation sits in want_bucket"""
    m=t.Machine(b); m.do("wait:400")
    # park the player
    d=player_x-184
    if d: m.do(f"hold:{8 if d>0 else 4}"); m.do(f"wait:{abs(d)//2}"); m.do(f"release:{8 if d>0 else 4}"); m.do("wait:6")
    m.do(po(S["brainKind"],[1]))
    kept=0; skipped=0
    for bout in range(bouts):
        m.do(t.place(b, 72, FLOOR, 0x80, player_x, FLOOR, 0x80)+"wait:6")
        m.do(po(S["teachMode"],[1])); m.do("wait:1")
        for tick in range(40):
            r=read(m)
            if abs(r["dx"]) not in want:            # out of the bucket: stop teaching this bout
                skipped+=1; break
            m.do("hold:8"); m.do("wait:4")             # toward the player, who is to the right
            kept+=1
        m.do("release:8"); m.do(po(S["teachMode"],[0])); m.do("wait:4")
    r=read(m)
    m.do(f"sync,dump:{S['brainMarker']:X}:342:{G}/brain-{label}.b025")
    m.close()
    p=ref.parse_slot(open(f"{G}/brain-{label}.b025","rb").read())
    nz=sum(1 for row in p["weights"] for v in row if v)
    print(f"  {label:5} taught at buckets {sorted(want)}: {kept} teaching ticks over {bouts} bouts, "
          f"education {p['education']}, {nz} nonzero weights, hash {ref.brain_hash(open(f'{G}/brain-{label}.b025','rb').read())[:16]}")
    return f"{G}/brain-{label}.b025", p["education"]

print("teaching two brains the same thing at two different separations\n")
near_brain, near_edu = curriculum(112, {1,2,3,4}, 10, "near")   # gap ~40px and closing -> the near buckets
far_brain,  far_edu  = curriculum(286, {7}, 10, "far")          # gap ~200px -> bucket 7, saturated
json.dump(dict(near=dict(path=near_brain,education=near_edu), far=dict(path=far_brain,education=far_edu)),
          open(f"{G}/a3-curricula.json","w"), indent=1)
