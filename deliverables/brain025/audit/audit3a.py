#!/usr/bin/env python3
"""AUDIT 3 phase A. The player is walked to each distance with the joystick while the slot is still
blank (so the clone stands still); the trained brain is loaded only then. Terrain untouched."""
import importlib.util, json, os, re, sys
_ARGV=sys.argv[1:]; sys.argv=["x"]; ROOT="/home/user/tony-demo"
s=importlib.util.spec_from_file_location("t", f"{ROOT}/tools/brain025_test.py"); t=importlib.util.module_from_spec(s); s.loader.exec_module(t)
S={}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(f"{ROOT}/src/kickass/tony-b025-a-vis3.sym").read()): S.setdefault(m.group(1),int(m.group(2),16))
b=t.Build(f"{ROOT}/src/kickass/tony-b025-a-vis3.prg")
BRAIN=_ARGV[0] if len(_ARGV)>0 else f"{ROOT}/deliverables/brain025/brains/climbed-b02-a-migrated.b025"
TAG=_ARGV[1] if len(_ARGV)>1 else "phaseA"
def pk(a,n=1): return "".join(f"peek:{a+i:X}," for i in range(n))
def po(a,d): return "".join(f"poke:{a+i:X}:{x&255:02X}," for i,x in enumerate(d))
def s16(lo,hi):
    v=lo|hi<<8; return v-65536 if v>=32768 else v
def sx(n): return n-16 if n>=8 else n
ACT={0:"IDLE",1:"LEFT",2:"RIGHT",3:"UP",4:"DOWN",5:"JUMP",6:"JUMP-L",7:"JUMP-R",8:"BUILD-L",9:"BUILD-R"}
GROUND={0x00,0x80,0x01,0x81,0x03,0x83}
REST=184
# (label, target player X, the dx bucket that separation should land in)
BINS=[("very near",80,1),("near",96,3),("middle",128,5),("rest",184,6),("far",224,7),("max practical",286,7)]
print(f"brain: {os.path.basename(BRAIN)}   clone parked at X 72; the player is walked to each X; nothing taught\n")
rows=[]
for label,target,want in BINS:
    d=target-REST
    move = "" if d==0 else (f"hold:8,wait:{abs(d)//2},release:8,wait:6," if d>0 else f"hold:4,wait:{abs(d)//2},release:4,wait:6,")
    m=t.Machine(b); m.do("wait:400")
    m.do(move) if move else None
    pre=m.do("sync,"+pk(S["physPlayerX"],2)+pk(S["cloneX"],2))
    m.do(f"load:{S['brainMarker']:X}:{BRAIN}"); m.do(po(S["teachMode"],[0])); m.do("wait:8")
    start=m.do("sync,"+pk(S["cloneX"],2)+pk(S["buildCount"])+pk(S["cloneSenses"],27)+pk(S["brainEducation"],2))
    cx0=start[0]|start[1]<<8; dx0=sx(start[3+1]); edu=start[30]|start[31]<<8
    acts=[];states=[];sample=None
    for k in range(50):
        r=m.do("wait:4,sync,"+pk(S["brainAction"])+pk(S["brainOutput"])+pk(S["cloneState"])+pk(S["brainActiveCount"])+pk(S["brainAcc"],20)+pk(S["cloneSenses"],27)+pk(S["physPlayerX"],2)+pk(S["cloneX"],2))
        acts.append(r[0]); states.append(r[2])
        if k==10: sample=dict(out=r[1],active=r[3],accs=[s16(r[4+2*i],r[5+2*i]) for i in range(10)],sn=r[24:51],px=r[51]|r[52]<<8,cx=r[53]|r[54]<<8)
    end=m.do("sync,"+pk(S["cloneX"],2)+pk(S["buildCount"])+pk(S["physPlayerX"],2)); m.close()
    cx1=end[0]|end[1]<<8
    disp=cx1-cx0; builds=end[2]-start[2]
    jumps=sum(1 for i in range(1,len(states)) if states[i] not in GROUND and states[i-1] in GROUND)
    idle=100.0*acts.count(0)/len(acts)
    adx=abs(dx0); sat=sum(1 for k in range(1,8) if adx>=k)
    rows.append(dict(label=label,player_x=pre[0]|pre[1]<<8,clone_x0=cx0,clone_x1=cx1,gap=(pre[0]|pre[1]<<8)-cx0,
                     dx_bucket=dx0,adx=adx,adx_thresholds_set=sat,education=edu,
                     active=sample["active"],raw_out=sample["out"],resolved=acts[10],accs=sample["accs"],
                     idle_pct=idle,displacement=disp,builds=builds,jumps=jumps,
                     actions={ACT[a]:acts.count(a) for a in sorted(set(acts))},
                     player_x_end=end[3]|end[4]<<8,senses=list(sample["sn"])))
    r=rows[-1]
    print(f"{label:14} player X {r['player_x']:3d}  clone X {cx0:3d} -> {cx1:3d}   gap {r['gap']:+4d}px  "
          f"dx bucket {dx0:+d} (adx {adx}, {sat}/7 thresholds set)")
    print(f"{'':14} active {r['active']:2d}  raw out {r['raw_out']}  resolved {ACT[r['resolved']]:7}  "
          f"IDLE {idle:5.1f}%  displacement {disp:+4d}px  builds {builds}  jumps {jumps}")
    print(f"{'':14} scores {r['accs']}")
    print(f"{'':14} {r['actions']}\n")
json.dump(rows, open(f"/tmp/claude-0/-home-user-tony-demo/c7c8bdb1-08b2-5026-9106-bb75e5d7e5a0/scratchpad/a3-{TAG}.json","w"), indent=1)
