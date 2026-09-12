#!/usr/bin/env python3
"""AUDIT 2. The live materials table, measured, so the descriptor publishes facts and not guesses."""
import hashlib, importlib.util, os, re, sys
from collections import Counter
sys.argv=["x"]; ROOT="/home/user/tony-demo"; G="/tmp/claude-0/-home-user-tony-demo/c7c8bdb1-08b2-5026-9106-bb75e5d7e5a0/scratchpad/a2"
os.makedirs(G,exist_ok=True)
s=importlib.util.spec_from_file_location("t", f"{ROOT}/tools/brain025_test.py"); t=importlib.util.module_from_spec(s); s.loader.exec_module(t)
S={}
for m in re.finditer(r"\.label (\w+)=\$([0-9a-f]+)", open(f"{ROOT}/src/kickass/tony-b025-a-vis3.sym").read()): S.setdefault(m.group(1),int(m.group(2),16))
b=t.Build(f"{ROOT}/src/kickass/tony-b025-a-vis3.prg")
MAXC=S["MAX_BG_CHARS"]
NAMES={0:"non-solid",1:"WALL",2:"LADDER",4:"KILLING",0x40:"COLLECTIBLE"}
def po(a,d): return "".join(f"poke:{a+i:X}:{x&255:02X}," for i,x in enumerate(d))
m=t.Machine(b); m.do("wait:400")
m.do(f"sync,dump:{S['roomMaterialsBuffer']:X}:100:{G}/mat0.bin,dump:{S['roomCharsDecodingBuffer']:X}:100:{G}/dec0.bin,dump:C000:3E8:{G}/scr0.bin")
m.do(po(S["roomChangeDirection"],[1])+po(S["roomChange"],[1])); m.do("wait:40")
m.do(f"sync,dump:{S['roomMaterialsBuffer']:X}:100:{G}/mat1.bin,dump:C000:3E8:{G}/scr1.bin")
m.close()
m0=open(f"{G}/mat0.bin","rb").read(); m1=open(f"{G}/mat1.bin","rb").read()
dec=open(f"{G}/dec0.bin","rb").read(); scr0=open(f"{G}/scr0.bin","rb").read()
static=open(f"{ROOT}/src/level-custom/chamber-materials.bin","rb").read()
print(f"roomMaterialsBuffer ${S['roomMaterialsBuffer']:04X}, MAX_BG_CHARS = {MAXC} entries in use (256 dumped)")
for tag, mm in (("chamber 0", m0), ("chamber 1", m1)):
    used = mm[:MAXC]
    h = Counter(used)
    print(f"  {tag}: sha256(first {MAXC}) {hashlib.sha256(used).hexdigest()[:16]}   "
          + ", ".join(f"{NAMES.get(k,hex(k))} {v}" for k,v in sorted(h.items())))
print(f"  the two chambers' live tables are {'IDENTICAL' if m0[:MAXC]==m1[:MAXC] else 'DIFFERENT'}")
print(f"\nstatic source, materials ${S['materials']:04X}: {len(static)} bytes, sha256 {hashlib.sha256(static).hexdigest()}")
print("  " + ", ".join(f"{NAMES.get(k,hex(k))} {v}" for k,v in sorted(Counter(static).items())))
# the live table is NOT a copy of the source: decodeRoom remaps it and the demo patches it
remapped = bytearray(256)
for orig in range(len(static)):
    new = dec[orig]
    if new < MAXC: remapped[new] = static[orig]
diff = [i for i in range(MAXC) if remapped[i] != m0[i]]
print(f"\nthe live table vs the source remapped through roomCharsDecodingBuffer: {len(diff)} entries differ")
print("  -> the host must read the LIVE buffer: decodeRoom remaps by used-char list and the demo patches it")
# what the clone actually walks on, by drawn code
codes = Counter(scr0[40*2:40*23])
print("\nwhat is on screen in chamber 0, by drawn code -> material:")
for c,n in sorted(codes.items(), key=lambda kv:-kv[1])[:10]:
    mat = m0[c] if c < 256 else None
    print(f"  code ${c:02X} x{n:4d}  material ${mat:02X} ({NAMES.get(mat,'combination')})")
