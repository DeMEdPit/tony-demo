#!/usr/bin/env python3
"""AUDIT 1b. Why the host sees status 4. It reads the range, the rollback rewinds cumWrite under it,
and its acknowledgement then names a range that no longer adds up. Both refusals demonstrated."""
import os, re, subprocess, sys, tempfile
ROOT="/home/user/tony-demo"; name="tony-b02-a"
S={}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(f"{ROOT}/src/kickass/{name}.sym").read()): S.setdefault(m.group(1),int(m.group(2),16))
def pk(a,n=1): return "".join(f"peek:{a+i:X}," for i in range(n))
def po(a,d): return "".join(f"poke:{a+i:X}:{b&255:02X}," for i,b in enumerate(d))
def w16(v): return [v&255,(v>>8)&255]
RING=[("writeSeq",S["lessonWriteSeq"],2),("readSeq",S["lessonReadSeq"],2),("cumWrite",S["lessonCumWrite"],2),
      ("cumRead",S["lessonCumRead"],2),("status",S["lessonStatus"],1),("drains",S["lessonDrains"],1),
      ("education",S["brainEducation"],2),("teachMode",S["teachMode"],1)]
R="".join(pk(a,n) for _,a,n in RING)
def parse(v,k):
    o=k*sum(n for _,_,n in RING); out={}
    for nm,_,n in RING: out[nm]=v[o] if n==1 else v[o]|v[o+1]<<8; o+=n
    return out
def run(script):
    with tempfile.NamedTemporaryFile("w",suffix=".m64",delete=False) as f: f.write(script)
    r=subprocess.run([f"{ROOT}/tools/m64-harness/m64run",f"{ROOT}/src/kickass/{name}.prg","@"+f.name],capture_output=True,text=True)
    os.unlink(f.name); return [int(m,16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)",r.stdout)]
C=18; HOLD=60
BITS={1:"ring full",2:"stale range",4:"bad checksum",8:"busy",0x80:"accepted"}
def why(s): return ", ".join(v for k,v in BITS.items() if s & k) or "no outcome bit"
enter=f"wait:400,hold:{C},wait:{HOLD},release:{C},wait:20,"
teach=f"hold:{C},wait:20,"                                     # one lesson lands, shadow taken
rollback=f"wait:{HOLD},release:{C},wait:20,"                    # frame 50: toggle out + restore

# --- case 1: the host's range is gone entirely
s1=(enter+teach+"sync,"+R+rollback+"sync,"+R)
v=run(s1); a,b=parse(v,0),parse(v,1)
ack=po(S["lessonAckSeq"],w16(a["writeSeq"]))+po(S["lessonAckSum"],w16(a["cumWrite"]-a["cumRead"]))+f"poke:{S['lessonAckRequest']:X}:01,wait:8,"
v=run(s1+ack+"sync,"+R); c=parse(v,2)
print("CASE 1  the host read the range, then the rollback rewound it, then it acknowledged")
print(f"  read at       writeSeq {a['writeSeq']} cumWrite {a['cumWrite']} education {a['education']}  -> host will ack seq {a['writeSeq']} sum {a['cumWrite']-a['cumRead']}")
print(f"  after rollback writeSeq {b['writeSeq']} cumWrite {b['cumWrite']} education {b['education']} teachMode {b['teachMode']}")
print(f"  after the ack  status ${c['status']:02X} ({why(c['status'])}), readSeq {c['readSeq']}, drains {c['drains']}  -> nothing reclaimed")

# --- case 2: the range is back at the same sequence number with different bytes
s2=(enter+teach+"sync,"+R+rollback
    +f"hold:{C},wait:14,release:{C},wait:6,"    # teach again: a short press, a new lesson into the reused slot
    +f"poke:{S['teachMode']:X}:01,wait:1,hold:8,wait:30,release:8,wait:10,"
    +"sync,"+R)
v=run(s2); a2,b2=parse(v,0),parse(v,1)
ack2=po(S["lessonAckSeq"],w16(a2["writeSeq"]))+po(S["lessonAckSum"],w16(a2["cumWrite"]-a2["cumRead"]))+f"poke:{S['lessonAckRequest']:X}:01,wait:8,"
v=run(s2+ack2+"sync,"+R); c2=parse(v,2)
print("\nCASE 2  the rollback rewound it and fresh teaching refilled the same slot with other bytes")
print(f"  read at        writeSeq {a2['writeSeq']} cumWrite {a2['cumWrite']}  -> host will ack seq {a2['writeSeq']} sum {a2['cumWrite']-a2['cumRead']}")
print(f"  at the ack     writeSeq {b2['writeSeq']} cumWrite {b2['cumWrite']} education {b2['education']}")
print(f"  after the ack  status ${c2['status']:02X} ({why(c2['status'])}), readSeq {c2['readSeq']}, drains {c2['drains']}  -> nothing reclaimed")
