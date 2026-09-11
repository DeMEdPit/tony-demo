# BRAIN02.5, step H: Candidate A against BRAIN02.5 on the gauntlet

A small **non-sealed** diagnostic, pre-registered in `PREREG-BRAIN025.md` section 13. It is not the
sealed Phase 4 holdout, does not touch it, and its twenty courses are deliberately **not** the census's:
the census chose the design, so reusing it would show only a design fitting its own training set.
Raw data: `gauntlet.json`, `gauntlet-results.json`. Tool: `tools/brain025_gauntlet.py`.

## The courses

Twenty local courses of the kind a person builds in free play: steps one, two and four bricks high two
slots off; two ascending steps and a descending stair; a platform edge under his feet, two columns off,
and three levels up; gaps of one and four slots, with landings wide, thin, a level up and a level down;
a one-slot notch in a long platform; pockets one and three bricks high; a low ceiling and a step under a
ceiling; a step followed by a gap; and a gap followed by a wall. Each is placed with Tony on the floor
far off, on the floor near, and on the ladder; each floor case is also mirrored left for right; and the
far cases are repeated at five clone starting columns, the canonical one and two on each side. **180
scenarios.**

## Ground truth, measured once

Which of the ten outputs is good is a fact about the room and the physics, not about the brain: the same
clone runs through the same world and the output is forced by the weights either way. So the good-action
sets were measured once, on the frozen Candidate A build, and both learners are judged against them.

BRAIN02.5's own rollouts agreed on 100 of the 180. The disagreement is not terrain and is worth stating
exactly, because it is a limitation of the measurement rather than of either build: **70 of the 80
differences are on the two build outputs**, and the outcome mix shifts from CLIMB (337 to 289) toward
RETREAT (254 to 340). Building is a multi-frame macro, and BRAIN02.5's main loop is slower, so within
the fixed rollout fewer build macros complete. Judging both against one measurement removes that
artefact from the comparison.

## The six measurements

| | Candidate A, 64 inputs | BRAIN02.5, 80 inputs |
|---|---|---|
| distinct observations over 180 scenarios | 37 | **99** |
| observations covering more than one course | 12 | 22 |
| **observations whose courses need different actions** | **1** | **0** |
| representable (CP-SAT, the byte box) | feasible, 170 scenarios | feasible, 170 scenarios |
| **lessons to competence** | **never: 98% after 882 lessons** | **74 lessons, 9 passes** |
| right, like for like, on the 170 | 167 (98%) | **170 (100%)** |
| retention after an unrelated later stream | 98% → **54%** | 100% → **72%** |
| taught only with Tony far off, right with him near | 100% | 100% |
| taught only with Tony far off, right with him **on the ladder** | **67%** | **100%** |
| regressions against Candidate A | — | **0** |

Ten of the 180 scenarios have no good action at all: nothing Tony can choose from that pose advances or
climbs. They are excluded from every learning number and counted here instead.

### 1. Aliases resolved

Candidate A sees 37 distinct observations where the world offers 180 situations. BRAIN02.5 sees 99. One
of Candidate A's observations covers courses that need different actions; none of BRAIN02.5's do. On
this fresh set the extension did what the census said it would, which is the first evidence that the
design generalises past the courses it was chosen on.

### 2. Representability

Both are representable. A weight setting exists, inside the same byte box the machine uses, whose argmax
lands on a good action in all 170 scenarios, for **both** builds. This matters: the difference between
the two is **not** that Candidate A cannot express the behaviour. It is that the learner cannot find it.

### 3. Lessons to competence

BRAIN02.5 reaches every scenario right after **74 lessons in 9 passes**. Candidate A does not reach it
at all: after 882 lessons and 400 passes it is right on 167 of 170 and stops improving. Its three
remaining failures are the price of that one conflicting observation, which no weight assignment
reachable by this rule can satisfy in both directions at once.

This is the experiment's central number, and it answers the question that was asked. The same learner,
taught the same way, goes from stuck at 98% to competent in 74 lessons when the terrain it is failing on
becomes visible.

### 4. Retention after unrelated later teaching

Both lose ground when an unrelated stream is taught afterwards: the bake-off's 474 teacher-visited
states, three passes, nothing to do with the gauntlet. Candidate A falls from 98% to **54%**. BRAIN02.5
falls from 100% to **72%**.

More eyes help and do not cure. Interference between what Tony was taught before and what he is taught
later remains a real property of a single layer of byte weights under this rule, and nothing in this
experiment addresses it. Anyone planning long teaching sessions should expect it.

### 5. Shepherding

Taught **only** on scenarios with Tony far off, and then tested on the same courses with him near and on
the ladder: Candidate A is 100% right with him near and **67%** with him on the ladder. BRAIN02.5 is
100% in both. Candidate A needs Tony's position to carry information the terrain should have carried;
BRAIN02.5 does not, so less shepherding is needed.

### 6. Regressions

**None.** On the 170 scenarios, every one Candidate A gets right BRAIN02.5 also gets right, and three
more besides. Nothing in the gauntlet got worse.

### Starting position

The far-off cases were run at five clone starting columns, the canonical one and two columns each side.
BRAIN02.5 is right at every offset on every course where it is right at the canonical one. The result is
not a property of one coordinate.

## What this does not show

The gauntlet is a designed sweep, not a sample of what a person actually builds, and the teacher is an
oracle that demonstrates a good action rather than a human with a joystick. Lessons to competence here
counts lessons the rule takes on a clean stream; a person teaching live will need more, because some of
their presses will be late, ambiguous, or mutually inconsistent. The retention result says plainly that
a long session is not the same as a short one repeated.
