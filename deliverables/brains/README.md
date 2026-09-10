# Brains

Weight files for the brain slot of `tony-body.prg` (`BODY.md`, "The brain slot"): 100 bytes each, the
first hundred of the slot's 256, `w[o][i]` as signed nibbles, output `o`'s twenty at bytes `o * 10` to
`o * 10 + 9`, the first of each pair in the low nibble. Load one with the harness (`load:ADDR:FILE` at
`brainWeights`) and poke `brainKind` to 1.

- `follow-two-weights.bin`: `w[right][dx] = 7`, `w[left][dx] = -7`, `w[idle][bias] = 1`. He walks to
  within sixteen pixels of Tony and stops, and follows him about the room.
- `build-left.bin`: `w[build left][buildable] = 7`, `w[idle][bias] = 2`. He lays a brick to his left and
  steps onto it whenever the slot there is free: a staircase.

Both are the bench's (`tools/verify_brain.py`, "two weights"). Written by hand, not trained.

- `taught-climb.bin`: the first taught weights. Thirty-six lessons from zero in four teaching sessions
  on the harness (`tools/teach_demo.py`, `BODY.md`, "TEACH"): the builder's rule driven through the
  port as a teacher while Tony waits on the ladder above his five-brick stairs. Loaded alone from the
  same start he jumps the stairs and climbs the ladder to Tony. He was never taught to walk in that
  task (every state had a wall ahead), so these weights do not follow across a room.
