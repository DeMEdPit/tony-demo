# Can BRAIN02.5 be taught to self-start? A diagnostic, and the shadow guard

Two bounded tasks. vis3 and every earlier artifact are untouched; `tony-b025-a-vis4.prg` exists only to
carry the `shadowValid` correctness guard. **Nothing was implemented from the diagnostic's result.**

| PRG | bytes | sha256 |
|---|---:|---|
| `tony-b025-a-vis3.prg` (unchanged) | 52,098 | `a9efe9d00afd0cfc9453acbcb0fe6b0faa8fe6f7f83f43635c2bd4ee80ef12ec` |
| **`tony-b025-a-vis4.prg`** (the guard) | **52,104** | `355645a687dc244257a6e53be2a652b19a9f81a8ad9d6abc4e042a9e5ca4ea62` |

Build line:

    python3 tools/make_chamber.py --build-demo --body --brain025-visual \
        --build-parity --bat-stamp-guard --shadow-guard --vocab rel --variant tony-b025-a-vis4
    bash tools/build_demo.sh tony-b025-a-vis4

Sixteen gates on vis4, **95 checks, no failures**: the fifteen from vis3 plus the new `shadow` gate.
Timing is unmoved - think 40,836 cycles max against a 78,624-cycle period (vis3: 40,843), lesson 40,066
(40,024), raster max **138** unchanged, overruns **0**, headroom below the shadow 253 bytes (259). Six
bytes of code, and the shadow profile drops because the guarded no-op returns immediately.

---

## 1. The `shadowValid` restore guard

`teachShadowRestore` copies `TEACH_SHADOW` over the canonical brain - weights, kind, education,
`lessonWriteSeq`, `lessonWriteSlot`, `lessonWritePtr` and `lessonCumWrite` - and it never asked whether a
snapshot had been taken. The chord that used to request it checked `shadowValid` first, so play was
safe. A host poking `shadowRestoreRequest` directly was not: at `$9200` the load image holds relocated
music data.

Six bytes, at the top of the routine, before its first write:

    teachShadowRestore: {
        lda shadowValid                     // --shadow-guard: no snapshot, no restore.
        bne haveShadow
            rts
        haveShadow:
        lda #0
        sta shadowValid
        ...

Behind `--shadow-guard`, off by default, so the hash-pinned research PRGs still regenerate byte for
byte (verified: `--brain025` without the flag reproduces `tony-b025-a.asm` exactly). The generated diff
between vis3 and vis4 is those four lines and nothing else.

### Proof, from the new `shadow` gate

**A valid snapshot restores exactly.** Teach to education 3, snapshot, teach on to education 11,
restore: the **whole 834-byte slot comes back byte for byte** (`2fb4aa9ffbe81906`), and education,
`write_seq`, `cum_write` and kind with it. Valid-snapshot semantics are unchanged.

**No snapshot is a no-op.** With `shadowValid` 0, a restore request leaves **all 834 slot bytes
untouched**, and each field is checked individually: education, `write_seq`, `cum_write`, `brainKind`,
`brainKindNow` and all ten `brainMood` bytes. The request byte is still consumed by the caller, so a
host cannot spin on it, and the brain keeps running (`brainKindNow` 1, overruns 0).

**The gate is adversarial, not a tautology.** On vis3 it fails exactly where it should: **783 of 834
bytes changed, first at offset 8** - `brainKind`, immediately after the marker - with education,
`write_seq`, `cum_write` and kind all clobbered and `brainKindNow` dropping to 0. The mood check passes
on vis3 too, which independently confirms the shadow never covered the mood.

15 of 15 checks pass on vis4.

---

## 2. Diagnostic: can the existing architecture be taught initiative?

No motivation, wander, randomness, reward, RL, planning, hidden state or fallback was added. The
question was only whether the **existing** `still` / `still>=N` and `lastAction` features can carry an
explicitly taught idle-state policy.

### Method

One base curriculum taught once - walk toward the player, 8 bouts, **education 48**, 18 nonzero weights,
hash `2eeeb8eff5ce0850` - then saved and loaded identically into every arm, so the arms differ only in
what came after. In each initiative arm the player **never moves**: teaching is switched on with the
stick idle until `still` climbs, then one non-IDLE action is pressed, and that repeats six times. Three
targets tested **separately**: TOWARD, JUMP, BUILD. Autonomous windows are 100 think ticks with the
player completely stationary and the clone adjacent to him; the follow check is a separate 50-tick
window from across the room.

### Results

| arm | education | autonomous IDLE | displacement | jumps | builds | `still` max | follow disp | follow IDLE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **A** base | 48 | **66.0%** | +12px | 0 | 0 | 3 | +100px | 70.0% |
| **B** TOWARD | 66 | 70.0% | +12px | 0 | 0 | 5 | +112px | 54.0% |
| **B** JUMP | 66 | **0.0%** | +0px | **4** | 0 | 1 | **+0px** | 52.0% |
| **B** BUILD | 59 | **100.0%** | +0px | 0 | 0 | 7 | **+0px** | 100.0% |

Arm A action mix: IDLE 66, LEFT 16, RIGHT 18, scores `[1, -1, 0, …]`.
Arm B JUMP action mix: **JUMP 100 of 100**, scores `[4, -10, 0, 0, 0, 6, 0, 0, 0, 0]` - output 5 at 6
beats IDLE at 4.
Arm B BUILD action mix: IDLE 100 of 100, scores `[15, -11, 0, 0, 0, 0, 0, 0, -4, 0]`.

**Arm A reproduces the report.** With the human completely stationary and the clone beside him, the base
brain is 66% IDLE, drifts ±12px, never jumps and never builds. That is the "knows behaviours but has no
reason to start one" feeling, measured.

### The features at the initiative lessons

Recorded at `still` 5, 5, 5, 5, 5, 6 (TOWARD), 5, 6, 5, 5, 5, 5 (JUMP) and 5, 6, 7, 7, 7, 7 (BUILD),
with `lastAction==0` set every time. The exact active input set at a JUMP initiative lesson, 20 inputs:

    bias>=1, facingRight, onGround, floorBelow, dx>=1, adx>=1, adx>=2,
    still, still>=2, still>=3, still>=4, still>=5, lastAction==0,
    facingRef>=1, tSafeRun>=1, tSafeRun>=3, tHead>=1, tHead>=4, tBackRoom>=2, tBackRoom>=4

### The two answers

**Can the existing linear BRAIN02.5 learn "when I have been inactive, initiate something"? YES, and it
was demonstrated.** The JUMP arm went from 66% IDLE to **0.0%**, jumping on 100 of 100 autonomous ticks
with the human completely stationary, with the taught output winning on score (6 against IDLE's 4).
`still>=N` and `lastAction==0` are sufficient to key an initiative policy. This is not an architectural
impossibility, and it needs no new mechanism.

**Is it compatible with what was already learned? NO - interference makes it unusable as taught.** The
only arm that installed initiative is the only arm that destroyed follow: displacement from across the
room fell from **+100px to +0px**, and he jumps in place instead of walking over. The arm that preserved
follow (TOWARD, +112px, intact) installed no initiative at all. BUILD lost both - 100% IDLE and +0px.

### Why the interference is structural, not incidental

The learning rule is a perceptron update over **every set flag**:

    if p == t: return p, False
    for i in range(len(z)):
        if not z[i]: continue
        w[t][i] += 1;  w[p][i] -= 1

So a lesson moves the weight of every co-active input. At the initiative lessons only **6 to 8 of the
20 to 22 active inputs are `still`/`lastAction` features**; the other **14 are shared with the follow
state** - `bias`, `onGround`, `floorBelow`, `facingRef`, `dx>=1`, `adx>=1`, `adx>=2` and five terrain
inputs. In a single layer with no hidden units there is no way to make a lesson apply *only when still*:
the update is spread across all co-active inputs, so initiative and follow necessarily share weights and
cannot be separated. The measured trade-off across the three arms is that fact showing up as behaviour.

A second, independent obstacle: **`still` never exceeds 3 autonomously** (arm A, mean 1.2), because the
clone's own residual ±12px jitter resets the counter. The initiative lessons had to be taught with the
stick held idle to reach `still` 5 to 7. Even a perfectly installed high-`still` policy would rarely
reach the state it was taught in during ordinary play.

### Classification

**A retention/interference issue with an architectural cause. NOT evidence that a motivation or agency
mechanism is required.**

Initiative is representable and teachable in what exists - the JUMP arm proves a learned policy can
generate activity with no human input, no randomness and no drive. What fails is holding it *alongside*
an earlier behaviour, and the cause is the single layer's inability to condition one behaviour on a
feature subset without disturbing another. That is capacity, not motivation. Separately, the `still`
counter not saturating in natural play is a perception and curriculum matter.

### Limits of this result

Three arms, six initiative lessons each, one base curriculum, one room, one seed, a deterministic
emulator. The TOWARD arm may have installed nothing simply because "toward" at zero separation is the
action the residual jitter already produces, so there was nothing new to learn. This is a diagnostic on
one machine, not a sweep, and the interference figure should not be read as a measured rate.

Raw data, the three initiative brains and the base brain are in `deliverables/brain025/audit/`.
