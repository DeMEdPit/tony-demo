#!/usr/bin/env python3
"""
verify_reloc.py - prove a SID relocation by replay.

Builds a bare player PRG for each tune (BASIC stub, RAM banked in at $01=$35,
init with the subtune, play once per frame on raster 0), runs both on the
minimal64 harness for N frames, dumps the player's own SID register image
(found by its copy loop LDA image,X / STA $D400,X) after every frame, and
compares the two streams byte for byte.

Usage: verify_reloc.py ORIGINAL.sid RELOCATED.sid [--frames 24000] [--subtune 0] [--work DIR]
"""
import argparse, os, re, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.join(HERE, 'm64-harness', 'm64run')

def read_psid(path):
    d = open(path, 'rb').read()
    off = struct.unpack('>H', d[6:8])[0]
    load, init, play = struct.unpack('>HHH', d[8:14])
    body = d[off:]
    if load == 0: load = body[0] | (body[1] << 8); body = body[2:]
    return load, init, play, body

def image_address(body, load):
    m = re.search(rb'\xBD(..)\x9D\x00\xD4', body, re.S)
    if not m: raise SystemExit("no LDA image,X / STA $D400,X copy loop found")
    return m.group(1)[0] | (m.group(1)[1] << 8)

def bare_player(load, init, play, body, subtune, path):
    stub = bytes([0x0B, 0x08, 0x0A, 0x00, 0x9E]) + b'2061' + bytes([0, 0, 0])      # 10 SYS 2061
    code = bytes([0x78,                               # sei
                  0xA9, 0x35, 0x85, 0x01,             # lda #$35 ; sta $01   (RAM everywhere but I/O)
                  0xA9, subtune, 0x20, init & 0xFF, init >> 8,   # lda #subtune ; jsr init
                  0xAD, 0x12, 0xD0, 0xD0, 0xFB,       # loop: lda $D012 ; bne loop   (raster 0)
                  0x20, play & 0xFF, play >> 8,       # jsr play
                  0xAD, 0x12, 0xD0, 0xF0, 0xFB,       # wait: lda $D012 ; beq wait
                  0x4C, 0x17, 0x08])                  # jmp loop
    img = stub + code
    if load < 0x0801 + len(img): raise SystemExit("tune too low for the bare player")
    img += bytes(load - 0x0801 - len(img)) + body
    open(path, 'wb').write(bytes([0x01, 0x08]) + img)

def capture(prg, image, frames, outdir):
    os.makedirs(outdir, exist_ok=True)
    script = os.path.join(outdir, 'script.m64')
    with open(script, 'w') as f:
        f.write('wait:5\n')
        for i in range(frames):
            f.write('wait:1\ndump:%04X:19:%s/f%05d\n' % (image, outdir, i))
    subprocess.run([HARNESS, prg, '@' + script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return [open(os.path.join(outdir, 'f%05d' % i), 'rb').read() for i in range(frames)]

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('original'); ap.add_argument('relocated')
    ap.add_argument('--frames', type=int, default=24000)
    ap.add_argument('--subtune', type=int, default=0)
    ap.add_argument('--work', help='working directory (default: a temporary one)')
    a = ap.parse_args()
    work = a.work or tempfile.mkdtemp(prefix='reloc-')
    os.makedirs(work, exist_ok=True)
    streams = []
    for tag, path in (('original', a.original), ('relocated', a.relocated)):
        load, init, play, body = read_psid(path)
        image = image_address(body, load)
        prg = os.path.join(work, tag + '.prg')
        bare_player(load, init, play, body, a.subtune, prg)
        print("%s: %s at $%04X (%d bytes), init $%04X play $%04X, register image $%04X" % (tag, os.path.basename(path), load, len(body), init, play, image))
        streams.append(capture(prg, image, a.frames, os.path.join(work, tag)))
    o, r = streams
    silent = all(not any(b) for b in o)
    if silent: print("FAIL: the original produced no register activity"); return 1
    for i in range(a.frames):
        if o[i] != r[i]:
            print("FAIL: streams differ at frame %d (%.1f s): %s vs %s" % (i, i / 50, o[i].hex(), r[i].hex())); return 1
    print("PASS: %d frames (%.1f s) of SID register writes are identical" % (a.frames, a.frames / 50))
    return 0

if __name__ == '__main__':
    sys.exit(main())
