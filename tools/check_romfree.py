#!/usr/bin/env python3
"""Static ROM-reference scan for Tony PRG builds.

Disassembles the PRG (linear sweep) and reports every instruction whose
control flow or vector could reach ROM address space:

  - JSR/JMP absolute with a target in $A000-$BFFF (BASIC) or
    $E000-$FFFF (KERNAL)
  - JMP (indirect) anywhere (reported for manual review)
  - writes (STA/STX/STY abs) to the hardware vectors $FFFA-$FFFF
    (reported: RAM vectors are the correct ROM-free technique)

The whole file is swept; hits inside pure data regions are possible in
principle, so each hit is listed with its file/memory offset for vetting.

Usage: check_romfree.py GAME.PRG [code_end_hex]
"""

import sys

# opcode -> length for the documented 6502 set (undocumented -> 1)
LEN = {}
for op in range(256):
    LEN[op] = 1
def setlen(ops, n):
    for o in ops: LEN[o] = n
setlen([0xA9,0xA2,0xA0,0x69,0x29,0xC9,0xE0,0xC0,0x49,0x09,0xE9,0x0B,0x2B], 2)  # imm
setlen([0xA5,0xB5,0xA6,0xB6,0xA4,0xB4,0x85,0x95,0x86,0x96,0x84,0x94,
        0x65,0x75,0x25,0x35,0x06,0x16,0xC5,0xD5,0xE4,0xC4,0xC6,0xD6,
        0x45,0x55,0xE6,0xF6,0x46,0x56,0x05,0x15,0x26,0x36,0x66,0x76,
        0xE5,0xF5,0x24,0xA1,0xB1,0x81,0x91,0x61,0x71,0x21,0x31,0xC1,
        0xD1,0x41,0x51,0x01,0x11,0xE1,0xF1], 2)                                 # zp/(zp)
setlen([0x10,0x30,0x50,0x70,0x90,0xB0,0xD0,0xF0], 2)                            # branches
setlen([0xAD,0xBD,0xB9,0xAE,0xBE,0xAC,0xBC,0x8D,0x9D,0x99,0x8E,0x8C,
        0x6D,0x7D,0x79,0x2D,0x3D,0x39,0x0E,0x1E,0xCD,0xDD,0xD9,0xEC,
        0xCC,0xCE,0xDE,0x4D,0x5D,0x59,0xEE,0xFE,0x4E,0x5E,0x0D,0x1D,
        0x2E,0x3E,0x6E,0x7E,0xED,0xFD,0xF9,0x2C,0x20,0x4C,0x6C], 3)             # abs

def main():
    path = sys.argv[1]
    data = open(path, "rb").read()
    load = data[0] | (data[1] << 8)
    mem = data[2:]
    code_end = int(sys.argv[2], 16) if len(sys.argv) > 2 else load + len(mem)
    print(f"{path}: load ${load:04x}, {len(data)} bytes, image ${load:04x}-${load+len(mem)-1:04x}")
    print(f"sweeping ${load:04x}-${code_end:04x}")

    hits = []
    pc = 0
    while pc < len(mem) and load + pc < code_end:
        op = mem[pc]
        ln = LEN[op]
        if ln == 3 and pc + 2 < len(mem):
            tgt = mem[pc+1] | (mem[pc+2] << 8)
            addr = load + pc
            if op in (0x20, 0x4C):  # JSR / JMP abs
                if 0xA000 <= tgt <= 0xBFFF or 0xE000 <= tgt <= 0xFFFF:
                    hits.append((addr, f"{'JSR' if op==0x20 else 'JMP'} ${tgt:04x}"))
            elif op == 0x6C:        # JMP (indirect)
                hits.append((addr, f"JMP (${tgt:04x}) [indirect - review vector]"))
            elif op in (0x8D, 0x8E, 0x8C) and 0xFFFA <= tgt <= 0xFFFF:
                hits.append((addr, f"write to hardware vector ${tgt:04x} (RAM vector setup)"))
        pc += ln

    if not hits:
        print("no control flow into ROM ranges found")
    for addr, desc in hits:
        print(f"  ${addr:04x}: {desc}")
    print(f"{len(hits)} finding(s) - vet each against the symbol map")

if __name__ == "__main__":
    main()
