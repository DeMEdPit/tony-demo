#!/usr/bin/env python3
"""Headless VICE driver: boots a Tony PRG, plays it via the binary monitor
(joyport I/O simulation) and captures PNG screenshots of the VIC-II display.

Requires: x64sc (VICE 3.7) with C64 ROMs installed, xvfb-run, Pillow.
The game reads the joystick on control port 2 (CIA1 port A); we attach
VICE's "Joyport I/O simulation" device (id 37) and drive its lines from
the binary monitor (command 0xa2), which the game's direct CIA polling
sees as real joystick input.  KERNAL keyboard-buffer feeding would NOT
work here - the game never calls the KERNAL.

Usage: c64shot.py PRG OUTDIR PREFIX [script]
  script: comma list of steps, default
          "sleep8,shot-boot,fire,sleep5,shot-title,fire,sleep8,shot-game,left2.0,shot-walk"
  steps:  sleepN  wait N s | fire | leftN | rightN | upN | shot-NAME
"""

import os
import signal
import socket
import struct
import subprocess
import sys
import time

from PIL import Image

STX = 0x02
API = 0x02

CMD_MEM_GET = 0x01
CMD_JOYPORT_SET = 0xA2
CMD_DISPLAY_GET = 0x84
CMD_PALETTE_GET = 0x85
CMD_EXIT = 0xAA  # resume emulation - monitor commands leave the machine paused

# Joyport lines are active-low: enable initialises them to all-high (idle),
# a cleared bit is a closed switch (see vice joyport_io_sim.c).
JOY_IDLE = 0x1F
JOY_UP, JOY_DOWN, JOY_LEFT, JOY_RIGHT, JOY_FIRE = 1, 2, 4, 8, 16


class BinMon:
    def __init__(self, port, timeout=30):
        deadline = time.time() + timeout
        while True:
            try:
                self.sock = socket.create_connection(("127.0.0.1", port), 2)
                break
            except OSError:
                if time.time() > deadline:
                    raise
                time.sleep(0.5)
        self.req = 0
        self.buf = b""

    def _recv(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError("monitor closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def cmd(self, command, body=b""):
        self.req += 1
        hdr = struct.pack("<BBIIB", STX, API, len(body), self.req, command)
        self.sock.sendall(hdr + body)
        while True:
            rh = self._recv(12)
            stx, api, length, rtype, err, rid = struct.unpack("<BBIBBI", rh)
            assert stx == STX, "lost sync"
            rbody = self._recv(length)
            if rid == 0xFFFFFFFF:  # spontaneous event, ignore
                continue
            if rid == self.req:
                return rtype, err, rbody

    def mem(self, start, end):
        rtype, err, body = self.cmd(
            CMD_MEM_GET, struct.pack("<BHHBH", 0, start, end, 0, 0))
        assert err == 0, f"mem_get error {err}"
        self.cmd(CMD_EXIT)
        return body[2:]  # skip u16 length

    def player_pos(self):
        """Sprite 0 position = Tony (X including MSB, Y)."""
        d = self.mem(0xD000, 0xD010)
        return d[0] | (256 if d[0x10] & 1 else 0), d[1]

    def joy(self, pressed):
        # drive both control ports (ids 0 and 1); value = idle lines minus
        # the pressed bits; then resume emulation
        value = JOY_IDLE & ~pressed
        for port in (0, 1):
            self.cmd(CMD_JOYPORT_SET, struct.pack("<HH", port, value))
        self.cmd(CMD_EXIT)

    # Pepto PAL palette; display_get returns raw VIC-II color indices and the
    # 3.7.1 palette_get reply is unreliable early in boot, so use the classic
    # fixed palette instead.
    PALETTE = [(0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x68, 0x37, 0x2B),
               (0x70, 0xA4, 0xB2), (0x6F, 0x3D, 0x86), (0x58, 0x8D, 0x43),
               (0x35, 0x28, 0x79), (0xB8, 0xC7, 0x6F), (0x6F, 0x4F, 0x25),
               (0x43, 0x39, 0x00), (0x9A, 0x67, 0x59), (0x44, 0x44, 0x44),
               (0x6C, 0x6C, 0x6C), (0x9A, 0xD2, 0x84), (0x6C, 0x5E, 0xB5),
               (0x95, 0x95, 0x95)]

    def display(self, border=32):
        rtype, err, body = self.cmd(CMD_DISPLAY_GET, bytes([1, 0]))
        assert err == 0, f"display_get error {err}"
        (info_len,) = struct.unpack_from("<I", body, 0)
        dw, dh, ox, oy, iw, ih, bpp = struct.unpack_from("<HHHHHHB", body, 4)
        (buf_len,) = struct.unpack_from("<I", body, 4 + info_len)
        pixels = body[4 + info_len + 4:4 + info_len + 4 + buf_len]
        im = Image.new("RGB", (dw, dh))
        px = im.load()
        rows = min(dh, len(pixels) // dw) if dw else 0
        for y in range(rows):
            row = pixels[y * dw:(y + 1) * dw]
            for x in range(dw):
                px[x, y] = self.PALETTE[row[x] % 16]
        # crop to the visible screen plus a slice of border
        x0, y0 = max(0, ox - border), max(0, oy - border)
        return im.crop((x0, y0, min(dw, ox + iw + border), min(dh, oy + ih + border)))


def main():
    args = [a for a in sys.argv[1:] if a != "--nowarp"]
    warp = "--nowarp" not in sys.argv
    prg, outdir, prefix = args[0], args[1], args[2]
    script = (args[3] if len(args) > 3 else
              "sleep8,shot-boot,fire,sleep5,shot-title,fire,sleep8,shot-game,"
              "left2.0,shot-walk").split(",")
    port = 6502
    # a leftover emulator would still own the monitor port - refuse to run
    if subprocess.run(["pgrep", "-x", "x64sc"], capture_output=True).returncode == 0:
        raise SystemExit("another x64sc is running - kill it first (pkill -x x64sc)")
    proc = subprocess.Popen(
        ["xvfb-run", "-a", "x64sc",
         "-default", "-binarymonitor",
         "-binarymonitoraddress", f"ip4://127.0.0.1:{port}",
         "-controlport1device", "37", "-controlport2device", "37",
         "-sounddev", "dummy"] + (["-warp"] if warp else []) +
        ["-autostartprgmode", "1", "-autostart", prg],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True)
    try:
        mon = BinMon(port)
        print("monitor connected")
        for step in script:
            step = step.strip()
            if step.startswith("sleep"):
                time.sleep(float(step[5:]))
            elif step == "fire":
                mon.joy(JOY_FIRE); time.sleep(0.4); mon.joy(0)
            elif step.startswith("left"):
                mon.joy(JOY_LEFT); time.sleep(float(step[4:] or 1)); mon.joy(0)
            elif step.startswith("right"):
                mon.joy(JOY_RIGHT); time.sleep(float(step[5:] or 1)); mon.joy(0)
            elif step.startswith("up"):
                mon.joy(JOY_UP); time.sleep(float(step[2:] or 1)); mon.joy(0)
            elif step.startswith("fl"):  # jump left
                mon.joy(JOY_FIRE | JOY_LEFT); time.sleep(float(step[2:] or 0.4)); mon.joy(0)
            elif step.startswith("fr"):  # jump right
                mon.joy(JOY_FIRE | JOY_RIGHT); time.sleep(float(step[2:] or 0.4)); mon.joy(0)
            elif step.startswith("wsp"):  # wsp<N>lt<X>/gt<X>: wait for sprite N
                n, cond = int(step[3]), step[4:6]
                val = int(step[6:])
                for _ in range(400):
                    d = mon.mem(0xD000, 0xD010)
                    x = d[2 * n] | (256 if d[0x10] & (1 << n) else 0)
                    if (cond == "lt" and x < val) or (cond == "gt" and x > val):
                        break
                    time.sleep(0.05)
                print(f"  {step}: sprite {n} at x={x}")
            elif step.startswith("gox"):  # walk to sprite X with feedback
                target = int(step[3:])
                for _ in range(200):
                    x, y = mon.player_pos()
                    if abs(x - target) < 5:
                        break
                    mon.joy(JOY_LEFT if x > target else JOY_RIGHT)
                    time.sleep(0.06)
                mon.joy(0)
                print(f"  gox{target}: at {mon.player_pos()}")
            elif step.startswith("goy"):  # climb to sprite Y with feedback
                target = int(step[3:])
                for _ in range(200):
                    x, y = mon.player_pos()
                    if abs(y - target) < 5:
                        break
                    mon.joy(JOY_UP if y > target else JOY_DOWN)
                    time.sleep(0.06)
                mon.joy(0)
                print(f"  goy{target}: at {mon.player_pos()}")
            elif step.startswith("shot-"):
                name = f"{outdir}/{prefix}-{step[5:]}.png"
                im = mon.display()
                mon.cmd(CMD_EXIT)
                im.save(name)
                print("wrote", name)
            else:
                raise SystemExit(f"unknown step {step}")
    finally:
        # kill the whole session (xvfb-run + Xvfb + x64sc), not just the wrapper
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            time.sleep(1)
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        # x64sc occasionally escapes the session; sweep by exact name
        subprocess.run(["pkill", "-9", "-x", "x64sc"], capture_output=True)
        subprocess.run(["pkill", "-9", "-x", "Xvfb"], capture_output=True)


if __name__ == "__main__":
    main()
