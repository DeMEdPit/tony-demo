#!/usr/bin/env python3
"""Can BRAIN02.5 be taught "when I have been inactive, initiate something"?
Matched arms from one identical base brain. Nothing is added to the machine."""
import hashlib, importlib.util, json, os, re, sys
_A=sys.argv[1:]; sys.argv=["x"]; ROOT="/home/user/tony-demo"
G="/tmp/claude-0/-home-user-tony-demo/c7c8bdb1-08b2-5026-9106-bb75e5d7e5a0/scratchpad/init"
os.makedirs(G, exist_ok=True)
s=importlib.util.spec_from_file_location("t", f"{ROOT}/tools/brain025_test.py"); t=importlib.util.module_from_spec(s); s.loader.exec_module(t)
ref=t.ref
PRG=_A[0] if _A else "tony-b025-a-vis4"
S={}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(f"{ROOT}/src/kickass/{PRG}.sym").read()): S.setdefault(m.group(1),int(m.group(2),16))
b=t.Build(f"{ROOT}/src/kickass/{PRG}.prg")
ENTRIES=ref.table_T1(); NAMES=ref.flag_names(ENTRIES)
def pk(a,n=1): return "".join(f"peek:{a+i:X}," for i in range(n))
def po(a,d): return "".join(f"poke:{a+i:X}:{x&255:02X}," for i,x in enumerate(d))
def s16(lo,hi):
    v=lo|hi<<8; return v-65536 if v>=32768 else v
ACT={0:"IDLE",1:"LEFT",2:"RIGHT",3:"UP",4:"DOWN",5:"JUMP",6:"JUMP-L",7:"JUMP-R",8:"BUILD-L",9:"BUILD-R"}
GROUND={0x00,0x80,0x01,0x81,0x03,0x83}
FLOOR=206; REST=184
def sense(m): return m.do("sync,"+pk(S["cloneSenses"],27))
def obs(m):
    v=m.do("sync,"+pk(S["brainAction"])+pk(S["brainOutput"])+pk(S["cloneState"])+pk(S["brainActiveCount"])
           +pk(S["brainAcc"],20)+pk(S["cloneSenses"],27)+pk(S["cloneX"],2)+pk(S["buildCount"])+pk(S["brainEducation"],2))
    return dict(action=v[0],out=v[1],state=v[2],active=v[3],accs=[s16(v[4+2*i],v[5+2*i]) for i in range(10)],
                sn=v[24:51],cx=v[51]|v[52]<<8,builds=v[53],edu=v[54]|v[55]<<8)
def teach_burst(m, mask, ticks):
    m.do(po(S["teachMode"],[1]))
    for _ in range(ticks):
        if mask: m.do(f"hold:{mask}"); m.do("wait:4"); m.do(f"release:{mask}"); m.do("wait:2")
        else: m.do("wait:6")
    m.do(po(S["teachMode"],[0])); m.do("wait:4")

# ---------------------------------------------------------------- the base curriculum, taught once
def base():
    m=t.Machine(b); m.do("wait:400"); m.do(po(S["brainKind"],[1]))
    for bout in range(8):
        m.do(t.place(b,72,FLOOR,0x80,REST,FLOOR,0x80)+"wait:6")
        teach_burst(m, 8, 8)                                  # walk toward the player, who is to the right
    o=obs(m); m.do(f"sync,dump:{S['brainMarker']:X}:342:{G}/base.b025"); m.close()
    p=ref.parse_slot(open(f"{G}/base.b025","rb").read())
    print(f"base curriculum: education {p['education']}, {sum(1 for r in p['weights'] for v in r if v)} nonzero weights, "
          f"hash {ref.brain_hash(open(f'{G}/base.b025','rb').read())[:16]}")
    return p["education"]
base_edu=base()

# ---------------------------------------------------------------- the autonomous window, player frozen
def window(brain, label, ticks=100, start_near=True):
    m=t.Machine(b); m.do("wait:400")
    m.do(f"load:{S['brainMarker']:X}:{brain}"); m.do(po(S["teachMode"],[0]))
    cx = REST-16 if start_near else 72
    m.do(t.place(b,cx,FLOOR,0x80,REST,FLOOR,0x80)+"wait:10")
    o0=obs(m); stills=[]; acts=[]; states=[]; sample=None
    for k in range(ticks):
        o=obs(m); acts.append(o["action"]); states.append(o["state"]); stills.append(o["sn"][17])
        if k==ticks//2: sample=o
        m.do("wait:4")
    o1=obs(m); m.close()
    jumps=sum(1 for i in range(1,len(states)) if states[i] not in GROUND and states[i-1] in GROUND)
    idle=100.0*acts.count(0)/len(acts)
    return dict(label=label,idle_pct=idle,actions={ACT[a]:acts.count(a) for a in sorted(set(acts))},
                displacement=o1["cx"]-o0["cx"],builds=o1["builds"]-o0["builds"],jumps=jumps,
                still_max=max(stills),still_mean=sum(stills)/len(stills),
                accs=sample["accs"],active=sample["active"],out=sample["out"],
                still_at_sample=sample["sn"][17],last_at_sample=sample["sn"][16])

# ---------------------------------------------------------------- the initiative curriculum
def initiative(target_mask, target_name, bursts=6, settle=10):
    """the player never moves. Let the clone sit until still saturates, then teach ONE non-IDLE action."""
    m=t.Machine(b); m.do("wait:400")
    m.do(f"load:{S['brainMarker']:X}:{G}/base.b025"); m.do(po(S["brainKind"],[1]))
    m.do(t.place(b,REST-16,FLOOR,0x80,REST,FLOOR,0x80)+"wait:10")
    lessons=[]
    e0=obs(m)["edu"]
    for burst in range(bursts):
        m.do(po(S["teachMode"],[1]))
        for _ in range(settle): m.do("wait:6")            # teaching, stick idle: still climbs
        pre=sense(m)
        m.do(f"hold:{target_mask}"); m.do("wait:4"); m.do(f"release:{target_mask}"); m.do("wait:4")
        post=obs(m)
        lessons.append(dict(burst=burst, still=pre[17], last=pre[16], dx=pre[1],
                            active=[NAMES[i] for i,f in enumerate(ref.flags(ENTRIES, list(pre))) if f],
                            education=post["edu"]))
        m.do(po(S["teachMode"],[0])); m.do("wait:4")
        m.do(t.place(b,REST-16,FLOOR,0x80,REST,FLOOR,0x80)+"wait:8")
    o=obs(m); path=f"{G}/init-{target_name}.b025"
    m.do(f"sync,dump:{S['brainMarker']:X}:342:{path}"); m.close()
    p=ref.parse_slot(open(path,"rb").read())
    print(f"\ninitiative [{target_name}]: education {e0} -> {p['education']}, "
          f"{sum(1 for r in p['weights'] for v in r if v)} nonzero weights")
    print(f"  still at the taught moments: {[l['still'] for l in lessons]}   lastAction: {[l['last'] for l in lessons]}")
    print(f"  inputs active at the last such lesson ({len(lessons[-1]['active'])}): {', '.join(lessons[-1]['active'])}")
    return path, lessons, p["education"]

print("\n=== ARM A: base brain, player completely stationary ===")
A=window(f"{G}/base.b025","A base")
print(f"  IDLE {A['idle_pct']:5.1f}%  disp {A['displacement']:+5d}px  jumps {A['jumps']}  builds {A['builds']}  "
      f"still max {A['still_max']} mean {A['still_mean']:.1f}")
print(f"  actions {A['actions']}")
print(f"  scores at mid-window (still {A['still_at_sample']}, lastAction {A['last_at_sample']}, active {A['active']}, raw out {A['out']}): {A['accs']}")
res={"base_education":base_edu,"armA":A,"arms":{}}
for mask,name in ((8,"TOWARD"),(16,"JUMP"),(18,"BUILD")):
    path,lessons,edu=initiative(mask,name)
    W=window(path,f"B {name}")
    far=window(path,f"B {name} far",ticks=50,start_near=False)
    print(f"  ARM B [{name}] stationary window: IDLE {W['idle_pct']:5.1f}%  disp {W['displacement']:+5d}px  "
          f"jumps {W['jumps']}  builds {W['builds']}  still max {W['still_max']}")
    print(f"    actions {W['actions']}")
    print(f"    scores at mid-window (still {W['still_at_sample']}, raw out {W['out']}): {W['accs']}")
    print(f"  follow still intact? from far: disp {far['displacement']:+5d}px  IDLE {far['idle_pct']:5.1f}%  actions {far['actions']}")
    res["arms"][name]=dict(education=edu,lessons=lessons,window=W,follow=far)
A_far=window(f"{G}/base.b025","A base far",ticks=50,start_near=False)
res["armA_far"]=A_far
print(f"\nbaseline follow from far (arm A): disp {A_far['displacement']:+5d}px  IDLE {A_far['idle_pct']:5.1f}%  actions {A_far['actions']}")
json.dump(res, open(f"{G}/initiative.json","w"), indent=1)
