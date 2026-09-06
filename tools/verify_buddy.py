#!/usr/bin/env python3
"""Scripted tests of the buddy's seven mechanics on the minimal64 harness.

Finds the buddy's variables in the PRG by the hop-arc byte signature and the
player's by the code that reads them (no symbol file), stamps behaviour and
colour with tools/stamp_mural.py, runs the Chamber on the native minimal64
build and reads the machine back frame by frame with the harness's peek.

  0 Follow   (The Shadow)   walks after the player, hops when he jumps
  1 Dance    (The Dancer)   steps with the bass line, bounces on voice 3's hits,
                            his path independent of the player
  2 Echo     (The Echo)     replays the player ECHO_DELAY frames later, frame for
                            frame: position, height and pose (walk, duck, jump)
  3 Mirror   (The Mirror)   stands at the player's reflection about the centre
                            line, clamped to the pillars, hops with him
  4 Wander   (The Wanderer) strolls, pauses and sits on the chip's dice, turns at
                            the pillars, never leaves the room
  5 Shy      (The Shy One)  runs from a close player, cowers at the pillar, creeps
                            back when he is far
  6 Sleeper  (The Sleeper)  dozes crouched, wakes on an approach, follows a while,
                            dozes off again

Usage:  python3 tools/verify_buddy.py [deliverables/prg/minimal64/tony-chamber.prg] [names...]
"""
import os
import re
import subprocess
import sys
import tempfile

M64 = "tools/m64-harness/m64run"
HOP_ARC = bytes([252, 252, 252, 254, 254, 254, 255, 255, 255, 0, 255, 0, 255, 1, 0, 1, 0, 1, 1, 1, 2, 2, 2, 4, 4, 4])   # Tony's jump
HOP_LEN = len(HOP_ARC)
DANCE_RISE, ECHO_DELAY, MIRROR_SUM = 6, 200, 344
FLOOR_Y, MIN_X, MAX_X, AIR = 206, 64, 280, 206 - 8
BOOT = 150
LEFT, RIGHT, FIRE = 4, 8, 16
VARS = {"buddyX": -9, "buddyY": -7, "buddyFacing": -6, "buddyMoving": -5, "buddyHop": -4, "buddyCool": -3,
        "buddyPhase": -2, "buddyDelay": -1}
AFTER = {"wantHop": 0, "envPrev": 1, "stepCount": 2, "slideCount": 3, "buddyMode": 12, "buddyPoseMoving": 13,
         "buddyCrouch": 14, "distMag": 15, "distRight": 16, "echoHead": 17, "echoFill": 18, "wanderTimer": 21,
         "wanderState": 22, "sleepAwake": 24, "sleepFar": 25, "wanderRng": 32, "buddyJumpPose": 34}   # offsets past the arc
VARS.update({k: HOP_LEN + v for k, v in AFTER.items()})


def addresses(prg):
    data = open(prg, "rb").read()
    i = data.find(HOP_ARC)
    assert i > 0 and data.count(HOP_ARC) == 1, "hop arc signature not found once"
    a = 0x0801 + i - 2
    A = {k: a + v for k, v in VARS.items()}
    bx = A["buddyX"]
    m = re.search(rb"\x38\xAD(..)\xED" + bytes([bx & 0xFF, bx >> 8]), data, re.S)   # SEC / LDA physPlayerX / SBC buddyX
    A["playerX"] = m.group(1)[0] | (m.group(1)[1] << 8)
    A["playerY"] = A["playerX"] + 2
    A["playerAnim"] = A["playerX"] + 6
    m = re.search(rb"\xBD(..)\x9D\x00\xD4", data, re.S)                            # the tune's player: LDA image,X / STA $D400,X
    A["sidImage"] = m.group(1)[0] | (m.group(1)[1] << 8)
    return A


def stamp(prg, behaviour, colour):
    out = tempfile.NamedTemporaryFile(suffix=".prg", delete=False).name
    subprocess.run([sys.executable, "tools/stamp_mural.py", prg, out, "--behaviour", str(behaviour),
                    "--colour", str(colour)], check=True, capture_output=True)
    return out


def run(prg, script):
    r = subprocess.run([M64, prg, script], capture_output=True, text=True)
    return [int(m, 16) for m in re.findall(r"peek \$[0-9a-f]+ = \$([0-9a-f]+)", r.stdout)]


def peeks(A, names):
    return "".join(f"peek:{A[n]:X}," + (f"peek:{A[n] + 1:X}," if n in ("buddyX", "playerX") else "") for n in names)


def frames(prg, A, names, plan):
    """plan: list of (joystick mask or None, frames). Returns dict name -> per-frame values (16-bit for X)."""
    script = f"wait:{BOOT},"
    held = 0
    for mask, n in plan:
        if mask != held:
            if held:
                script += f"release:{held},"
            if mask:
                script += f"hold:{mask},"
            held = mask or 0
        script += (peeks(A, names) + "wait:1,") * n
    if held:
        script += f"release:{held},"
    v = run(prg, script)
    width = sum(2 if n in ("buddyX", "playerX") else 1 for n in names)
    total = sum(n for _, n in plan)
    assert len(v) == width * total, (len(v), width * total)
    out, k = {}, 0
    for n in names:
        if n in ("buddyX", "playerX"):
            out[n] = [v[f * width + k] | (v[f * width + k + 1] << 8) for f in range(total)]
            k += 2
        else:
            out[n] = [v[f * width + k] for f in range(total)]
            k += 1
    return out


def near(f, lst, w):
    return any(abs(f - g) <= w for g in lst)


def report(name, ok, detail):
    print(f"{name:8s} {detail} -> {'OK' if ok else 'FAIL'}")
    return ok


# ----------------------------------------------------------------------------- the seven
def follow(prg, A):
    p = stamp(prg, 0, 5)
    v = run(p, f"wait:{BOOT},peek:{A['buddyX']:X},joy:{RIGHT}:120,peek:{A['buddyX']:X},peek:D02C,joy:{FIRE}:4,wait:6,peek:{A['buddyHop']:X},"
                f"wait:40,hold:2,wait:20,peek:{A['playerAnim']:X},peek:{A['buddyCrouch']:X},release:2,wait:10,peek:{A['buddyCrouch']:X}")
    os.unlink(p)
    ok = v[1] != v[0] and (v[2] & 15) == 5 and v[3] != 0 and v[4] in (2, 3, 18, 19) and v[5] == 1 and v[6] == 0
    return report("FOLLOW", ok, f"player walks 120 frames: buddy X {v[0]} -> {v[1]} (must follow), colour {v[2] & 15}, hop after the player's jump {v[3]}, "
                  f"player ducks (anim {v[4]}): buddy crouch {v[5]}, after: {v[6]}")


def dance(prg, A):
    p = stamp(prg, 1, 3)
    n = 900
    S = A["sidImage"]
    per = (f"peek:D41C,peek:{A['buddyHop']:X},peek:{A['buddyFacing']:X},peek:{A['buddyX']:X},"
           f"peek:{A['buddyPhase']:X},peek:{S:X},peek:{S + 1:X},wait:1,")
    v = run(p, f"wait:{BOOT},peek:D02C,peek:D02D," + per * n)
    col5, col6, v = v[0] & 15, v[1] & 15, v[2:]
    env, hop, facing, bx, phase = v[0::7], v[1::7], v[2::7], v[3::7], v[4::7]
    freq = [lo | (hi << 8) for lo, hi in zip(v[5::7], v[6::7])]
    notes = [f for f in range(1, n) if abs(freq[f] - freq[f - 1]) >= freq[f - 1] // 32]
    steps = [f for f in range(1, n) if phase[f] != phase[f - 1] and hop[f] == 0 and hop[f - 1] == 0]
    turns = [f for f in range(1, n) if facing[f] != facing[f - 1]]
    hops = [f for f in range(1, n) if hop[f - 1] == 0 and hop[f] != 0]
    rises = [f for f in range(2, n) if env[f] - env[f - 1] >= DANCE_RISE or env[f] - env[f - 2] >= DANCE_RISE]
    steps_off = [f for f in steps if not near(f, notes, 1)]
    unanswered = [f for f in notes if not near(f, steps, 1) and not any(hop[g] for g in range(max(0, f - 1), f + 2))]
    gaps = [b - a for a, b in zip(turns, turns[1:])]
    # a hit while he is in the air is answered the moment he lands: a hop may follow its rise by a whole jump
    hops_unfounded = [f for f in hops if not any(f - HOP_LEN - 2 <= g <= f + 3 for g in rises)]
    rises_unanswered, last = [], -99
    for f in rises:
        if f - last <= 8:
            continue
        last = f
        if not any(hop[g] for g in range(f, min(n, f + 4))) and not any(hop[g] for g in range(max(0, f - HOP_LEN - 2), f)):
            rises_unanswered.append(f)
    ok = (len(steps) >= 30 and not steps_off and len(unanswered) <= len(notes) // 20 and len(turns) >= 8
          and all(g >= 30 for g in gaps) and len(hops) >= 6 and not hops_unfounded and not rises_unanswered
          and 16 <= max(bx) - min(bx) <= 48 and col5 == 3 and col6 == 3)
    # his path is the music's: the same trace whether the player stands or walks about
    still = frames(p, A, ["buddyX"], [(None, 400)])["buddyX"]
    walk = frames(p, A, ["buddyX"], [(RIGHT, 60), (LEFT, 60)] * 3 + [(RIGHT, 40)])["buddyX"]
    os.unlink(p)
    same = still == walk
    return report("DANCE", ok and same, f"{n / 50:.0f} s: notes {len(notes)}, steps {len(steps)} (off the beat {len(steps_off)}, unanswered {len(unanswered)}), "
                  f"turns {len(turns)}, ENV3 rises {len(rises)}, hops {len(hops)} (without a rise {len(hops_unfounded)}, rises unanswered {len(rises_unanswered)}), "
                  f"X {min(bx)}..{max(bx)}, colours {col5},{col6}; path with the player still vs walking {'identical' if same else 'DIFFERS'}")


def echo(prg, A):
    """A routine - run left, five jumps, a duck, run right - must come back exactly, ECHO_DELAY frames later."""
    p = stamp(prg, 2, 7)
    DOWN = 2
    plan = [(LEFT, 40)] + [(FIRE, 4), (None, 36)] * 5 + [(DOWN, 40), (RIGHT, 60), (None, ECHO_DELAY + 40)]
    t = frames(p, A, ["playerX", "playerY", "playerAnim", "buddyX", "buddyY", "buddyFacing",
                      "buddyPoseMoving", "buddyCrouch", "buddyJumpPose"], plan)
    col = run(p, f"wait:{BOOT},peek:D02C")[0] & 15
    os.unlink(p)
    px, py, pa = t["playerX"], t["playerY"], t["playerAnim"]
    bx, by, bf, walk, crouch, jump = t["buddyX"], t["buddyY"], t["buddyFacing"], t["buddyPoseMoving"], t["buddyCrouch"], t["buddyJumpPose"]
    n = len(px)
    # the recording is taken inside the frame; find the exact lag (ECHO_DELAY or one more) and demand it everywhere
    def misses(k):
        return [f for f in range(k, n) if bx[f] != px[f - k] or by[f] != py[f - k]]
    k, bad = min(((kk, misses(kk)) for kk in (ECHO_DELAY, ECHO_DELAY + 1, ECHO_DELAY - 1)), key=lambda x: len(x[1]))
    POSE = {0: "walk", 1: "walk", 2: "duck", 3: "duck", 18: "duck", 19: "duck", 7: "jump", 8: "jump"}
    WANT = {"walk": (1, 0, 0), "duck": (0, 1, 0), "jump": (0, 0, 1)}
    def want(f):
        return WANT.get(POSE.get(pa[f]), (0, 0, 0))
    # the game sets the duck's animation a little later in the frame than the others, so a pose may change one
    # frame late in the recording: allow that jitter at transitions, nothing else
    pose_bad = [f for f in range(k + 1, n) if (walk[f], crouch[f], jump[f]) not in (want(f - k), want(f - k - 1), want(f - k + 1))]
    FACING = {0: 0, 2: 0, 4: 0, 7: 0, 18: 0, 1: 1, 3: 1, 5: 1, 8: 1, 19: 1}
    face_bad = [f for f in range(k, n) if pa[f - k] in FACING and bf[f] != FACING[pa[f - k]]]
    # every jump and duck the player made in the recorded window comes back, and nothing extra
    JUMP, DUCK = (7, 8), (2, 3, 18, 19)
    player_jumps = sum(1 for f in range(1, n - k) if pa[f] in JUMP and pa[f - 1] not in JUMP)
    echoed_jumps = sum(1 for f in range(k + 1, n) if jump[f] and not jump[f - 1])
    player_ducks = sum(1 for f in range(1, n - k) if pa[f] in DUCK and pa[f - 1] not in DUCK)
    echoed_ducks = sum(1 for f in range(k + 1, n) if crouch[f] and not crouch[f - 1])
    ok = (not bad and not pose_bad and not face_bad and player_jumps >= 3 and echoed_jumps == player_jumps
          and player_ducks >= 1 and echoed_ducks == player_ducks and col == 7 and max(px) - min(px) >= 40)
    return report("ECHO", ok, f"{n} frames, lag {k}: position and height match the player {k} frames earlier at every frame ({len(bad)} misses), "
                  f"pose ({len(pose_bad)} misses) and facing ({len(face_bad)} misses) too; player jumped {player_jumps} times, "
                  f"echo {echoed_jumps}; ducked {player_ducks}, echo {echoed_ducks}; player X {min(px)}..{max(px)}, colour {col}")


def mirror(prg, A):
    p = stamp(prg, 3, 14)
    DOWN = 2
    plan = [(RIGHT, 80), (LEFT, 160), (None, 10), (FIRE, 4), (None, 40), (DOWN, 30), (None, 10)]
    t = frames(p, A, ["playerX", "playerY", "playerAnim", "buddyX", "buddyHop", "buddyFacing", "buddyCrouch"], plan)
    col = run(p, f"wait:{BOOT},peek:D02C")[0] & 15
    os.unlink(p)
    px, py, pa, bx, hop, fac, crouch = t["playerX"], t["playerY"], t["playerAnim"], t["buddyX"], t["buddyHop"], t["buddyFacing"], t["buddyCrouch"]
    n = len(px)
    DUCK = (2, 3, 18, 19)
    crouch_bad = [f for f in range(1, n) if crouch[f] != (1 if pa[f] in DUCK else 0) and crouch[f] != (1 if pa[f - 1] in DUCK else 0)]
    want = [min(MAX_X, max(MIN_X, MIRROR_SUM - x)) for x in px]
    bad = [f for f in range(1, n) if bx[f] not in (want[f - 1], want[f])]
    # while the player walks right (and the reflection is not pinned), the mirror faces left
    opposite = all(fac[f] == 0 for f in range(5, 80) if want[f] != want[f - 1])
    jump = next((f for f in range(n) if py[f] < AIR), None)
    hops = [f for f in range(1, n) if hop[f - 1] == 0 and hop[f] != 0]
    ducked = sum(1 for f in range(n) if pa[f] in DUCK)
    ok = not bad and opposite and jump is not None and any(abs(h - jump) <= 3 for h in hops) and ducked >= 20 and not crouch_bad and col == 14
    return report("MIRROR", ok, f"{n} frames: buddy X = {MIRROR_SUM} - player X, clamped {MIN_X}..{MAX_X}, at every frame ({len(bad)} misses), "
                  f"faces the other way {opposite}, player jumps at {jump}, buddy hops at {hops}, player ducks {ducked} frames, "
                  f"buddy crouches with him ({len(crouch_bad)} misses), colour {col}")


def wander(prg, A):
    p = stamp(prg, 4, 5)
    n = 2000
    t = frames(p, A, ["buddyX", "buddyCrouch", "buddyFacing", "wanderState"], [(None, n)])
    os.unlink(p)
    bx, crouch, fac, st = t["buddyX"], t["buddyCrouch"], t["buddyFacing"], t["wanderState"]
    turns = sum(1 for f in range(1, n) if fac[f] != fac[f - 1])
    sits = max((sum(1 for _ in g) for k, g in __import__("itertools").groupby(crouch) if k), default=0)
    still = 0
    best = 0
    for f in range(1, n):
        still = still + 1 if bx[f] == bx[f - 1] and not crouch[f] else 0
        best = max(best, still)
    plans = sum(1 for f in range(1, n) if st[f] != st[f - 1])
    ok = max(bx) - min(bx) >= 80 and turns >= 3 and sits >= 60 and best >= 20 and MIN_X <= min(bx) and max(bx) <= MAX_X and plans >= 8
    return report("WANDER", ok, f"{n / 50:.0f} s alone: X {min(bx)}..{max(bx)} (room {MIN_X}..{MAX_X}), turns {turns}, plan changes {plans}, "
                  f"longest sit {sits} frames, longest pause {best} frames")


def shy(prg, A):
    """The player comes at him from the right, then walks away to the far right and waits."""
    p = stamp(prg, 5, 10)
    plan = [(LEFT, 60), (RIGHT, 110), (None, 200)]
    t = frames(p, A, ["playerX", "buddyX", "buddyCrouch"], plan)
    col = run(p, f"wait:{BOOT},peek:D02C")[0] & 15
    os.unlink(p)
    px, bx, crouch = t["playerX"], t["buddyX"], t["buddyCrouch"]
    dist = [abs(a - b) for a, b in zip(px, bx)]
    fled = bx[0] - min(bx[:60])                            # he ran left as the player came
    pinned = next((f for f in range(60) if bx[f] <= MIN_X), None)
    closest_free = min(dist[f] for f in range(60) if bx[f] > MIN_X + 2)   # never caught while he could still run
    cowered = any(crouch[f] for f in range(60))
    crept = bx[-1] - bx[170]                               # he came back while the player was far
    far_dist = min(dist[170:])
    ok = fled >= 40 and pinned is not None and closest_free >= 44 and cowered and crept >= 30 and far_dist >= 100 and col == 10
    return report("SHY", ok, f"player approaches: buddy runs {fled} px, at the pillar by frame {pinned}, closest while free {closest_free} px, cowers {cowered}; "
                  f"player leaves: buddy creeps back {crept} px, nearest he comes {far_dist} px, colour {col}")


def sleeper(prg, A):
    p = stamp(prg, 6, 4)
    plan = [(None, 100), (LEFT, 30), (RIGHT, 100), (None, 250)]
    t = frames(p, A, ["playerX", "buddyX", "buddyCrouch", "sleepAwake"], plan)
    col = run(p, f"wait:{BOOT},peek:D02C")[0] & 15
    os.unlink(p)
    px, bx, crouch, awake = t["playerX"], t["buddyX"], t["buddyCrouch"], t["sleepAwake"]
    dozing_first = all(crouch[:100]) and len(set(bx[:100])) == 1
    woke = next((f for f in range(100, 130) if not crouch[f]), None)
    followed = bx[229] - bx[130]
    dozed_again = next((f for f in range(230, 480) if crouch[f]), None)
    settled = dozed_again is not None and len(set(bx[dozed_again + 20:])) == 1 and all(crouch[dozed_again + 20:])
    ok = dozing_first and woke is not None and followed >= 30 and settled and col == 4
    return report("SLEEPER", ok, f"dozes crouched and still for 100 frames {dozing_first}; player comes close: wakes at frame {woke}; "
                  f"follows {followed} px; dozes off again at frame {dozed_again} and stays put {settled}, colour {col}")


TESTS = {"follow": follow, "dance": dance, "echo": echo, "mirror": mirror, "wander": wander, "shy": shy, "sleeper": sleeper}

if __name__ == "__main__":
    args = sys.argv[1:]
    prg = args.pop(0) if args and args[0].endswith(".prg") else "deliverables/prg/minimal64/tony-chamber.prg"
    A = addresses(prg)
    print(f"{prg}: buddy variables at ${A['buddyX']:04X}.., player at ${A['playerX']:04X}, player's register image at ${A['sidImage']:04X}")
    names = args or list(TESTS)
    results = [TESTS[n](prg, A) for n in names]
    print("ALL OK" if all(results) else "FAILED")
    sys.exit(0 if all(results) else 1)
