#!/usr/bin/env python3
"""
sidreloc.py - relocate a PSID tune to a new page-aligned load address.

The tune is run in a small 6502 interpreter that tags every byte of the
file with its offset and follows those tags through registers, memory and
arithmetic.  Whenever an address is formed - an absolute operand, an
indirect pointer, a jump, a return - the tag of its high byte is recorded
together with where the address points.  A file byte that only ever serves
as the high byte of an address inside the tune is relocated; a byte that is
also used as data, as an index, as a low byte, or as the high byte of an
address outside the tune (a SID register, zero page) is a conflict and is
reported.  Because the move is a whole number of pages, low bytes never
change.

The proof that a relocation is right is not this analysis but a replay:
tools/verify_reloc.py plays the original and the relocated tune on the
emulator and compares the SID register stream frame by frame.

Usage:
  sidreloc.py IN.sid OUT.sid --to A000 [--frames 12000] [--subtune 0]
"""
import argparse, struct, sys

# ---------------------------------------------------------------- opcode table
OPS = {}
def _t(mn, pairs):
    for op, mode in pairs: OPS[op] = (mn, mode)
_t('LDA', [(0xA9,'imm'),(0xA5,'zp'),(0xB5,'zpx'),(0xAD,'abs'),(0xBD,'abx'),(0xB9,'aby'),(0xA1,'izx'),(0xB1,'izy')])
_t('LDX', [(0xA2,'imm'),(0xA6,'zp'),(0xB6,'zpy'),(0xAE,'abs'),(0xBE,'aby')])
_t('LDY', [(0xA0,'imm'),(0xA4,'zp'),(0xB4,'zpx'),(0xAC,'abs'),(0xBC,'abx')])
_t('STA', [(0x85,'zp'),(0x95,'zpx'),(0x8D,'abs'),(0x9D,'abx'),(0x99,'aby'),(0x81,'izx'),(0x91,'izy')])
_t('STX', [(0x86,'zp'),(0x96,'zpy'),(0x8E,'abs')])
_t('STY', [(0x84,'zp'),(0x94,'zpx'),(0x8C,'abs')])
_t('ADC', [(0x69,'imm'),(0x65,'zp'),(0x75,'zpx'),(0x6D,'abs'),(0x7D,'abx'),(0x79,'aby'),(0x61,'izx'),(0x71,'izy')])
_t('SBC', [(0xE9,'imm'),(0xE5,'zp'),(0xF5,'zpx'),(0xED,'abs'),(0xFD,'abx'),(0xF9,'aby'),(0xE1,'izx'),(0xF1,'izy')])
_t('AND', [(0x29,'imm'),(0x25,'zp'),(0x35,'zpx'),(0x2D,'abs'),(0x3D,'abx'),(0x39,'aby'),(0x21,'izx'),(0x31,'izy')])
_t('ORA', [(0x09,'imm'),(0x05,'zp'),(0x15,'zpx'),(0x0D,'abs'),(0x1D,'abx'),(0x19,'aby'),(0x01,'izx'),(0x11,'izy')])
_t('EOR', [(0x49,'imm'),(0x45,'zp'),(0x55,'zpx'),(0x4D,'abs'),(0x5D,'abx'),(0x59,'aby'),(0x41,'izx'),(0x51,'izy')])
_t('CMP', [(0xC9,'imm'),(0xC5,'zp'),(0xD5,'zpx'),(0xCD,'abs'),(0xDD,'abx'),(0xD9,'aby'),(0xC1,'izx'),(0xD1,'izy')])
_t('CPX', [(0xE0,'imm'),(0xE4,'zp'),(0xEC,'abs')])
_t('CPY', [(0xC0,'imm'),(0xC4,'zp'),(0xCC,'abs')])
_t('INC', [(0xE6,'zp'),(0xF6,'zpx'),(0xEE,'abs'),(0xFE,'abx')])
_t('DEC', [(0xC6,'zp'),(0xD6,'zpx'),(0xCE,'abs'),(0xDE,'abx')])
_t('ASL', [(0x0A,'acc'),(0x06,'zp'),(0x16,'zpx'),(0x0E,'abs'),(0x1E,'abx')])
_t('LSR', [(0x4A,'acc'),(0x46,'zp'),(0x56,'zpx'),(0x4E,'abs'),(0x5E,'abx')])
_t('ROL', [(0x2A,'acc'),(0x26,'zp'),(0x36,'zpx'),(0x2E,'abs'),(0x3E,'abx')])
_t('ROR', [(0x6A,'acc'),(0x66,'zp'),(0x76,'zpx'),(0x6E,'abs'),(0x7E,'abx')])
_t('BIT', [(0x24,'zp'),(0x2C,'abs')])
_t('JMP', [(0x4C,'abs'),(0x6C,'ind')])
_t('JSR', [(0x20,'abs')])
for op, mn in ((0x60,'RTS'),(0x40,'RTI'),(0x00,'BRK'),(0xEA,'NOP'),(0x18,'CLC'),(0x38,'SEC'),(0x58,'CLI'),(0x78,'SEI'),
               (0xB8,'CLV'),(0xD8,'CLD'),(0xF8,'SED'),(0xAA,'TAX'),(0x8A,'TXA'),(0xA8,'TAY'),(0x98,'TYA'),(0xBA,'TSX'),
               (0x9A,'TXS'),(0x48,'PHA'),(0x68,'PLA'),(0x08,'PHP'),(0x28,'PLP'),(0xE8,'INX'),(0xC8,'INY'),(0xCA,'DEX'),(0x88,'DEY')):
    OPS[op] = (mn, 'imp')
for op, mn in ((0x10,'BPL'),(0x30,'BMI'),(0x50,'BVC'),(0x70,'BVS'),(0x90,'BCC'),(0xB0,'BCS'),(0xD0,'BNE'),(0xF0,'BEQ')):
    OPS[op] = (mn, 'rel')
SIZE = {'imm':2,'zp':2,'zpx':2,'zpy':2,'abs':3,'abx':3,'aby':3,'izx':2,'izy':2,'ind':3,'rel':2,'imp':1,'acc':1}

class Reloc6502:
    def __init__(self, data, load):
        self.mem = bytearray(65536)
        self.taint = [None] * 65536
        self.load, self.size = load, len(data)
        self.mem[load:load+len(data)] = data
        for i in range(len(data)):
            self.taint[load+i] = frozenset((i,))
        self.reloc, self.fixed, self.data = set(), set(), set()   # uses of file bytes
        self.a = self.x = self.y = 0; self.sp = 0xFF; self.pc = 0
        self.n = self.v = self.z = self.c = self.d = self.i = 0
        self.ta = self.tx = self.ty = None
        self.io_writes = []          # (frame, addr, value) for SID registers, for cross-checks
        self.frame = -1
        self.instructions = 0
        self.notes = []

    def inside(self, addr):
        return self.load <= addr < self.load + self.size

    # ---- address-use bookkeeping
    def use_hi(self, tset, base, eff):
        """A high byte with tags `tset` formed an address (base, indexed to eff)."""
        if not tset: return
        if self.inside(base) or self.inside(eff): self.reloc |= tset
        else: self.fixed |= tset
    def use_lo(self, tset):
        if tset: self.fixed |= tset
    def use_data(self, tset):
        if tset: self.data |= tset

    # ---- memory
    def rd(self, addr):
        if 0xD000 <= addr < 0xE000: return 0        # I/O reads: nothing meaningful for a player
        return self.mem[addr]
    def wr(self, addr, val, tset):
        if 0xD000 <= addr < 0xE000:
            if 0xD400 <= addr < 0xD420: self.io_writes.append((self.frame, addr, val))
            self.use_data(tset)                    # a value that reaches the chip is data
            return
        self.mem[addr] = val
        self.taint[addr] = tset

    def setnz(self, v):
        self.n = 1 if v & 0x80 else 0; self.z = 1 if v == 0 else 0

    def push(self, v, tset=None):
        self.mem[0x100 + self.sp] = v; self.taint[0x100 + self.sp] = tset; self.sp = (self.sp - 1) & 0xFF
    def pop(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.mem[0x100 + self.sp], self.taint[0x100 + self.sp]

    def flags_byte(self):
        return (self.n<<7)|(self.v<<6)|0x20|0x10|(self.d<<3)|(self.i<<2)|(self.z<<1)|self.c
    def set_flags(self, p):
        self.n=(p>>7)&1; self.v=(p>>6)&1; self.d=(p>>3)&1; self.i=(p>>2)&1; self.z=(p>>1)&1; self.c=p&1

    # ---- run one call (init or play) until it returns to the sentinel
    def call(self, entry, a=0, x=0, y=0, limit=2_000_000):
        sentinel = 0xFFF0
        self.a, self.x, self.y = a, x, y
        self.ta = self.tx = self.ty = None
        self.push((sentinel - 1) >> 8); self.push((sentinel - 1) & 0xFF)
        self.pc = entry
        n = 0
        while self.pc != sentinel:
            self.step(); n += 1
            if n > limit: raise RuntimeError("call from $%04X did not return after %d instructions (pc=$%04X)" % (entry, n, self.pc))
        self.instructions += n
        return n

    def step(self):
        mem, taint = self.mem, self.taint
        pc = self.pc
        op = mem[pc]
        if op not in OPS: raise RuntimeError("unsupported opcode $%02X at $%04X" % (op, pc))
        mn, mode = OPS[op]
        size = SIZE[mode]
        self.pc = pc + size
        # ---- effective address
        ea = None; tea = None      # tea: taint of the loaded operand (for imm) or of memory at ea
        if mode == 'imm':
            ea = pc + 1
        elif mode == 'zp':
            ea = mem[pc+1]; self.use_lo(taint[pc+1])
        elif mode == 'zpx':
            ea = (mem[pc+1] + self.x) & 0xFF; self.use_lo(taint[pc+1]); self.use_data(self.tx)
        elif mode == 'zpy':
            ea = (mem[pc+1] + self.y) & 0xFF; self.use_lo(taint[pc+1]); self.use_data(self.ty)
        elif mode in ('abs', 'abx', 'aby'):
            base = mem[pc+1] | (mem[pc+2] << 8)
            idx = self.x if mode == 'abx' else self.y if mode == 'aby' else 0
            ea = (base + idx) & 0xFFFF
            self.use_lo(taint[pc+1]); self.use_hi(taint[pc+2], base, ea)
            if mode == 'abx': self.use_data(self.tx)
            if mode == 'aby': self.use_data(self.ty)
        elif mode == 'izx':
            zp = (mem[pc+1] + self.x) & 0xFF; self.use_lo(taint[pc+1]); self.use_data(self.tx)
            ea = mem[zp] | (mem[(zp+1) & 0xFF] << 8)
            self.use_lo(taint[zp]); self.use_hi(taint[(zp+1) & 0xFF], ea, ea)
        elif mode == 'izy':
            zp = mem[pc+1]; self.use_lo(taint[pc+1]); self.use_data(self.ty)
            base = mem[zp] | (mem[(zp+1) & 0xFF] << 8)
            ea = (base + self.y) & 0xFFFF
            self.use_lo(taint[zp]); self.use_hi(taint[(zp+1) & 0xFF], base, ea)
        elif mode == 'ind':
            ptr = mem[pc+1] | (mem[pc+2] << 8)
            self.use_lo(taint[pc+1]); self.use_hi(taint[pc+2], ptr, ptr)
            lo = self.rd(ptr); hi = self.rd((ptr & 0xFF00) | ((ptr + 1) & 0xFF))
            ea = lo | (hi << 8)
            self.use_lo(taint[ptr]); self.use_hi(taint[(ptr & 0xFF00) | ((ptr + 1) & 0xFF)], ea, ea)
        elif mode == 'rel':
            off = mem[pc+1]; ea = (self.pc + (off - 256 if off & 0x80 else off)) & 0xFFFF

        # ---- execute
        if mn == 'LDA':
            self.a = self.rd(ea); self.ta = taint[ea]; self.setnz(self.a)
        elif mn == 'LDX':
            self.x = self.rd(ea); self.tx = taint[ea]; self.setnz(self.x)
        elif mn == 'LDY':
            self.y = self.rd(ea); self.ty = taint[ea]; self.setnz(self.y)
        elif mn == 'STA': self.wr(ea, self.a, self.ta)
        elif mn == 'STX': self.wr(ea, self.x, self.tx)
        elif mn == 'STY': self.wr(ea, self.y, self.ty)
        elif mn in ('ADC', 'SBC'):
            if self.d: raise RuntimeError("decimal mode arithmetic at $%04X" % pc)
            m = self.rd(ea); t = taint[ea]
            if mn == 'ADC':
                r = self.a + m + self.c
                self.v = 1 if (~(self.a ^ m) & (self.a ^ r) & 0x80) else 0
                self.c = 1 if r > 0xFF else 0
            else:
                r = self.a - m - (1 - self.c)
                self.v = 1 if ((self.a ^ m) & (self.a ^ r) & 0x80) else 0
                self.c = 0 if r < 0 else 1
            self.a = r & 0xFF; self.setnz(self.a)
            self.ta = (self.ta | t) if (self.ta and t) else (self.ta or t)
        elif mn in ('AND', 'ORA', 'EOR'):
            m = self.rd(ea); t = taint[ea]
            self.a = (self.a & m) if mn == 'AND' else (self.a | m) if mn == 'ORA' else (self.a ^ m)
            self.setnz(self.a)
            self.ta = (self.ta | t) if (self.ta and t) else (self.ta or t)
        elif mn in ('CMP', 'CPX', 'CPY'):
            r = {'CMP': self.a, 'CPX': self.x, 'CPY': self.y}[mn]; m = self.rd(ea)
            self.c = 1 if r >= m else 0; self.setnz((r - m) & 0xFF)
        elif mn == 'BIT':
            m = self.rd(ea); self.z = 1 if (self.a & m) == 0 else 0; self.n = (m >> 7) & 1; self.v = (m >> 6) & 1
        elif mn in ('INC', 'DEC'):
            m = (self.rd(ea) + (1 if mn == 'INC' else -1)) & 0xFF; self.wr(ea, m, taint[ea]); self.setnz(m)
        elif mn in ('ASL', 'LSR', 'ROL', 'ROR'):
            if mode == 'acc': m = self.a
            else: m = self.rd(ea)
            if mn == 'ASL': c = m >> 7; m = (m << 1) & 0xFF
            elif mn == 'LSR': c = m & 1; m >>= 1
            elif mn == 'ROL': c = m >> 7; m = ((m << 1) | self.c) & 0xFF
            else: c = m & 1; m = (m >> 1) | (self.c << 7)
            self.c = c; self.setnz(m)
            if mode == 'acc': self.a = m
            else: self.wr(ea, m, taint[ea])
        elif mn == 'JMP': self.pc = ea
        elif mn == 'JSR':
            ret = self.pc - 1
            self.push(ret >> 8); self.push(ret & 0xFF)
            self.pc = ea
        elif mn == 'RTS':
            lo, tlo = self.pop(); hi, thi = self.pop()
            target = ((lo | (hi << 8)) + 1) & 0xFFFF
            self.use_lo(tlo); self.use_hi(thi, target, target)
            self.pc = target
        elif mn == 'RTI':
            p, _ = self.pop(); self.set_flags(p)
            lo, tlo = self.pop(); hi, thi = self.pop()
            target = lo | (hi << 8); self.use_lo(tlo); self.use_hi(thi, target, target); self.pc = target
        elif mn == 'BRK': raise RuntimeError("BRK at $%04X" % pc)
        elif mn == 'NOP': pass
        elif mn == 'CLC': self.c = 0
        elif mn == 'SEC': self.c = 1
        elif mn == 'CLI': self.i = 0
        elif mn == 'SEI': self.i = 1
        elif mn == 'CLV': self.v = 0
        elif mn == 'CLD': self.d = 0
        elif mn == 'SED': self.d = 1
        elif mn == 'TAX': self.x = self.a; self.tx = self.ta; self.setnz(self.x)
        elif mn == 'TXA': self.a = self.x; self.ta = self.tx; self.setnz(self.a)
        elif mn == 'TAY': self.y = self.a; self.ty = self.ta; self.setnz(self.y)
        elif mn == 'TYA': self.a = self.y; self.ta = self.ty; self.setnz(self.a)
        elif mn == 'TSX': self.x = self.sp; self.tx = None; self.setnz(self.x)
        elif mn == 'TXS': self.sp = self.x
        elif mn == 'PHA': self.push(self.a, self.ta)
        elif mn == 'PLA': self.a, self.ta = self.pop(); self.setnz(self.a)
        elif mn == 'PHP': self.push(self.flags_byte())
        elif mn == 'PLP': p, _ = self.pop(); self.set_flags(p)
        elif mn == 'INX': self.x = (self.x + 1) & 0xFF; self.setnz(self.x)
        elif mn == 'INY': self.y = (self.y + 1) & 0xFF; self.setnz(self.y)
        elif mn == 'DEX': self.x = (self.x - 1) & 0xFF; self.setnz(self.x)
        elif mn == 'DEY': self.y = (self.y - 1) & 0xFF; self.setnz(self.y)
        elif mode == 'rel':
            take = {'BPL': not self.n, 'BMI': self.n, 'BVC': not self.v, 'BVS': self.v,
                    'BCC': not self.c, 'BCS': self.c, 'BNE': not self.z, 'BEQ': self.z}[mn]
            if take: self.pc = ea
        else:
            raise RuntimeError("unhandled %s at $%04X" % (mn, pc))

def read_psid(path):
    d = open(path, 'rb').read()
    if d[:4] != b'PSID': raise SystemExit("not a PSID file: " + path)
    ver = struct.unpack('>H', d[4:6])[0]; off = struct.unpack('>H', d[6:8])[0]
    load, init, play, songs, start = struct.unpack('>HHHHH', d[8:18])
    body = d[off:]
    if load == 0:
        load = body[0] | (body[1] << 8); body = body[2:]
    return d[:off], load, init, play, songs, body

def write_psid(header, load, init, play, body, path):
    h = bytearray(header)
    struct.pack_into('>HHH', h, 8, 0, init, play)          # load address kept in the data, as the original did
    open(path, 'wb').write(bytes(h) + bytes((load & 0xFF, load >> 8)) + body)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--to', required=True, help='new load address, hex (page aligned)')
    ap.add_argument('--frames', type=int, default=12000, help='play calls to trace (default 12000 = 4 min at 50 Hz)')
    ap.add_argument('--subtune', type=int, default=0)
    ap.add_argument('--report', help='write the per-byte use report here')
    a = ap.parse_args()
    to = int(a.to, 16)
    header, load, init, play, songs, body = read_psid(a.src)
    if (to - load) & 0xFF: raise SystemExit("the move must be a whole number of pages")
    dhi = ((to - load) >> 8) & 0xFF
    print("%s: load $%04X init $%04X play $%04X size %d -> $%04X (high bytes %+d pages)" % (a.src, load, init, play, len(body), to, (to - load) >> 8))
    cpu = Reloc6502(body, load)
    cpu.frame = -1
    n_init = cpu.call(init, a=a.subtune)
    for f in range(a.frames):
        cpu.frame = f
        cpu.call(play)
    print("traced: init %d instructions, %d play calls, %d instructions in all" % (n_init, a.frames, cpu.instructions))
    reloc = cpu.reloc
    conflicts = sorted(reloc & (cpu.fixed | cpu.data))
    print("bytes used as an address high byte inside the tune: %d; also used otherwise (conflicts): %d" % (len(reloc), len(conflicts)))
    out = bytearray(body)
    bad = []
    for o in sorted(reloc):
        v = body[o]
        if not (load >> 8) <= v <= ((load + len(body) - 1) >> 8): bad.append((o, v))
        out[o] = (v + dhi) & 0xFF
    if bad: print("WARNING: %d relocated bytes do not hold a page of the tune: %s" % (len(bad), ['+%04X=$%02X' % b for b in bad[:10]]))
    if conflicts: print("WARNING: conflicts at " + ', '.join('+%04X' % c for c in conflicts[:20]))
    write_psid(header, to, init + (to - load), play + (to - load), bytes(out), a.dst)
    print("wrote %s: %d bytes of tune at $%04X, init $%04X play $%04X" % (a.dst, len(out), to, init + (to - load), play + (to - load)))
    if a.report:
        with open(a.report, 'w') as r:
            r.write("offset value use\n")
            for o in range(len(body)):
                uses = []
                if o in reloc: uses.append('reloc')
                if o in cpu.fixed: uses.append('fixed')
                if o in cpu.data: uses.append('data')
                if uses: r.write("+%04X $%02X %s\n" % (o, body[o], ','.join(uses)))
    return 1 if (conflicts or bad) else 0

if __name__ == '__main__':
    sys.exit(main())
