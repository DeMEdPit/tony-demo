#!/usr/bin/env python3
"""Scripted test of the buddy's mechanics on the minimal64 harness.

Locates the buddy's variables in the PRG by the hop-arc byte signature (no
symbol file needed), stamps behaviour and colour with tools/stamp_mural.py,
runs the Chamber on the native minimal64 build and reads the machine back
frame by frame.

DANCE (behaviour 1): the pose must advance on the notes of voice 1 (read from
the player's register image, a jump of half a semitone or more) and never
otherwise; he must turn round every fourth note; every hop must sit on a rise
of voice 3's envelope (ENV3, $D41C, a hit while airborne answered on landing)
and every clear rise must produce a hop;
he must not follow the player; the sprite colour registers must carry the
colour byte. FOLLOW (behaviour 0) is the regression: he still walks after the
player and hops when the player jumps, in his original green.

Usage:  python3 tools/verify_dance.py [deliverables/prg/minimal64/tony-chamber.prg]
"""
import os
import re
import subprocess
import sys
import tempfile

PRG = sys.argv[1] if len(sys.argv) > 1 else "deliverables/prg/minimal64/tony-chamber.prg"
M64 = "tools/m64-harness/m64run"
HOP_ARC = bytes([253, 253, 254, 254, 255, 255, 0, 0, 1, 1, 2, 2, 3, 3])
DANCE_RISE = 6                           # as in the build (tools/make_chamber.py)
BOOT = 150                               # frames until the room is up and the tune plays
FRAMES = 900                             # 18 s of listening
RIGHT, FIRE = 8, 16


def addresses(prg):
    data = open(prg, "rb").read()
    i = data.find(HOP_ARC)
    assert i > 0 and data.count(HOP_ARC) == 1, "hop arc signature not found once"
    a = 0x0801 + i - 2                   # file offset -> address
    m = re.search(rb"\xBD(..)\x9D\x00\xD4", data, re.S)   # the tune's player: LDA image,X / STA $D400,X
    return {"buddyX": a - 9, "buddyY": a - 7, "buddyFacing": a - 6, "buddyMoving": a - 5,
            "buddyHop": a - 4, "buddyCool": a - 3, "buddyPhase": a - 2, "buddyDelay": a - 1,
            "wantHop": a + 14, "envPrev": a + 15, "stepCount": a + 16,
            "sidImage": m.group(1)[0] | (m.group(1)[1] << 8)}


def stamp(prg, behaviour, colour):
    out = tempfile.NamedTemporaryFile(suffix=".prg", delete=False).name
    subprocess.run([sys.executable, "tools/stamp_mural.py", prg, out, "--behaviour", str(behaviour),
                    "--colour", str(colour)], check=True, capture_output=True)
    return out


def run(prg, script):
    r = subprocess.run([M64, prg, script], capture_output=True, text=True)
    return [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)]


def near(f, frames, w):
    return any(abs(f - g) <= w for g in frames)


def dance(prg, A):
    prg1 = stamp(prg, 1, 3)              # Dance, cyan
    S = A["sidImage"]
    per = (f"peek:D41C,peek:{A['buddyHop']:X},peek:{A['buddyFacing']:X},peek:{A['buddyX']:X},"
           f"peek:{A['buddyPhase']:X},peek:{S:X},peek:{S + 1:X},wait:1,")
    v = run(prg1, f"wait:{BOOT},peek:D02C,peek:D02D," + per * FRAMES)
    col5, col6, v = v[0] & 15, v[1] & 15, v[2:]
    env, hop, facing, bx, phase = v[0::7], v[1::7], v[2::7], v[3::7], v[4::7]
    freq = [lo | (hi << 8) for lo, hi in zip(v[5::7], v[6::7])]
    assert len(freq) == FRAMES, len(freq)
    notes = [f for f in range(1, FRAMES) if abs(freq[f] - freq[f - 1]) >= freq[f - 1] // 32]
    steps = [f for f in range(1, FRAMES) if phase[f] != phase[f - 1] and hop[f] == 0 and hop[f - 1] == 0]
    turns = [f for f in range(1, FRAMES) if facing[f] != facing[f - 1]]
    hops = [f for f in range(1, FRAMES) if hop[f - 1] == 0 and hop[f] != 0]
    # the sampler and the machine read the chip at different moments: a rise over one or two frames counts
    rises = [f for f in range(2, FRAMES) if env[f] - env[f - 1] >= DANCE_RISE or env[f] - env[f - 2] >= DANCE_RISE]
    # the machine and the sampler read the tune at different moments in the frame: allow 1 frame
    steps_off_beat = [f for f in steps if not near(f, notes, 1)]
    notes_unanswered = [f for f in notes if not near(f, steps, 1) and not any(hop[g] for g in range(max(0, f - 1), f + 2))]
    turn_gaps = [b - a for a, b in zip(turns, turns[1:])]
    hops_unfounded = [f for f in hops if not any(f - 16 <= g <= f + 3 for g in rises)]   # a hit while airborne is answered on landing
    rises_unanswered = []
    last = -99
    for f in rises:
        if f - last <= 8:
            continue
        last = f
        if not any(hop[g] for g in range(f, min(FRAMES, f + 4))) and not any(hop[g] for g in range(max(0, f - 16), f)):
            rises_unanswered.append(f)                    # (a hit while he is in the air is queued for the landing)
    ok = (len(steps) >= 40 and not steps_off_beat and len(notes_unanswered) <= len(notes) // 20
          and len(turns) >= 8 and all(g >= 30 for g in turn_gaps)
          and len(hops) >= 6 and not hops_unfounded and not rises_unanswered
          and min(bx) == max(bx) and col5 == 3 and col6 == 3)
    print(f"DANCE  {FRAMES / 50:.0f} s: notes on voice 1 {len(notes)}, pose steps {len(steps)} (off the beat {len(steps_off_beat)}, "
          f"notes unanswered {len(notes_unanswered)}), turns {len(turns)} (every {min(turn_gaps) if turn_gaps else 0}..{max(turn_gaps) if turn_gaps else 0} frames), "
          f"ENV3 rises {len(rises)}, hops {len(hops)} (without a rise {len(hops_unfounded)}, rises without a hop {len(rises_unanswered)}), "
          f"buddy X {min(bx)}..{max(bx)}, sprite colours {col5},{col6} -> {'OK' if ok else 'FAIL'}")
    os.unlink(prg1)
    return ok


def dance_ignores_player(prg, A):
    prg1 = stamp(prg, 1, 3)
    v = run(prg1, f"wait:{BOOT},peek:{A['buddyX']:X},joy:{RIGHT}:120,peek:{A['buddyX']:X}")
    os.unlink(prg1)
    ok = v[0] == v[1]
    print(f"DANCE  the player walks 120 frames: buddy X {v[0]} -> {v[1]} (must not follow) -> {'OK' if ok else 'FAIL'}")
    return ok


def follow(prg, A):
    prg0 = stamp(prg, 0, 5)              # Follow, green: the original buddy
    v = run(prg0, f"wait:{BOOT},peek:{A['buddyX']:X},joy:{RIGHT}:120,peek:{A['buddyX']:X},peek:D02C,"
                  f"joy:{FIRE}:4,wait:6,peek:{A['buddyHop']:X}")
    os.unlink(prg0)
    ok = v[1] != v[0] and (v[2] & 15) == 5 and v[3] != 0
    print(f"FOLLOW the player walks 120 frames: buddy X {v[0]} -> {v[1]} (must follow), colour {v[2] & 15}, "
          f"hop after the player's jump {v[3]} -> {'OK' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    A = addresses(PRG)
    print(f"{PRG}: buddy variables at ${A['buddyX']:04X}.. (hop arc signature), player's register image at ${A['sidImage']:04X}")
    results = [follow(PRG, A), dance(PRG, A), dance_ignores_player(PRG, A)]
    print("ALL OK" if all(results) else "FAILED")
    sys.exit(0 if all(results) else 1)
