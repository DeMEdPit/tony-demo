#!/usr/bin/env python3
"""Mini-castle byte patches for the ON-CHAIN Tony PRG (token edition).

The deployed PRG (PoC721 `prg()`, keccak256 = PRG_HASH below) is the 30-room
Tony demo with the boot menu skipped and the GREEN scheme default.  A
"castle" is a tiny patch over those exact bytes: the title room's west exit
becomes the castle's entry room, the castle rooms' exit bytes are rewired,
the boot colour scheme byte is set, and a 10-byte stub clears (or sets) the
cheat-state byte the skipped menu used to initialise.  Nothing is
reassembled; rooms, objects, music and sprites are untouched.

    python3 tools/onchain_castle.py info    PRG            # offset map + self-checks
    python3 tools/onchain_castle.py census  PRG            # door sockets, compatible pairs
    python3 tools/onchain_castle.py samples PRG OUTDIR     # the three sample castles
    python3 tools/onchain_castle.py castle  PRG OUTDIR --spec castle.json

Every run first verifies keccak256(PRG) == PRG_HASH and refuses anything else:
patches are only meaningful against the deployed bytes.  Addresses come from a
KickAssembler symbol file of a byte-identical rebuild of upstream 75f62f5b
(deliverables/onchain/tony-token-edition.sym) and every table is re-checked
against the binary before use.

Patch record encoding (for a Solidity applier): repeated
    [offset: u16 big-endian][len: u16 big-endian][len bytes]
where offset is the byte index into the PRG (0 = first byte of the 2-byte
load address).  `hex` in the emitted JSON is exactly that byte string; a
room-map rewrite is one record carrying the whole (never larger) RLE3 block.
"""
import argparse
import json
import sys
from collections import Counter
from itertools import product
from pathlib import Path

try:
    from Crypto.Hash import keccak
except ImportError:  # pragma: no cover
    keccak = None

PRG_HASH = "5bcd208f63ac255ffc391c4abeb7b8f701061ac896008607ef414c24c880f34d"
LOAD = 0x0801
ROOMS = 30
TITLE = 29
NO = 255
W, H = 40, 20

# --- addresses (tony-token-edition.sym; code segment identical to upstream) --
A = dict(
    level_startRoom=0x449A, level_startPositionX=0x449B, level_startPositionY=0x449D,
    level_startState=0x449E,
    level_roomPtr=0x9446, level_usedCharsPtr=0x9482, level_usedCharsCount=0x94BE,
    level_roomExitsN=0x94DC, level_roomExitsE=0x94FA, level_roomExitsS=0x9518,
    level_roomExitsW=0x9536,
    level_objectControlPtr=0x9554, level_objectPositionXPtr=0x9590,
    level_objectPositionYPtr=0x95CC, level_movableObjectValue2Ptr=0x9608,
    level_objectSizes=0x9644, level_roomStates=0x9662,
    paths=0x9680, pathsPtrsLo=0x96C8, pathsPtrsHi=0x96D2, pathLengths=0x96DC,
    materials=0x8DC7,
    boot_jsr_blankScreen=0x08F8,   # token edition: 20 E1 2B right after `cli`
    blankScreen=0x2BE1,
    scheme_ldx=0x0964,             # token edition: A2 02  (ldx #GREEN)
    cheatMenu=0xB462,              # dead entry point of the skipped menu (in load image)
    gameCheatState=0x2D, currentChamberNumber=0x3E51,
    physPlayerX=0x39CC, physPlayerY=0x39CE, physPlayerState=0x39D3,
    musicData=0x9EDE, endOfTony=0xE428,
)
SCHEMES = ["CLASSIC", "AMBER", "GREEN", "BLUE", "C64", "C128"]
CHEAT = dict(STONE=0x02, LIVES=0x04, DOORS=0x08, SPRITE=0x10, PIKES=0x20)
SO = {0: "DEAD", 1: "FLAME1", 2: "FLAME2", 3: "PIKES", 4: "SNAKE_L", 5: "STONE", 6: "JEWEL",
      7: "KEY", 8: "DOOR", 9: "KEYCODE", 10: "DOORCODE", 11: "POTION", 12: "SNAKE_R",
      13: "BAT", 14: "BAT_V", 15: "SKULL"}
WALL, LADDER, KILL = 1, 2, 4
# room index -> castle-map grid slot (declaration order in level/demo/data.asm)
GRID = [(x, 0) for x in range(4)] + [(x, y) for y in range(1, 6) for x in range(5)] + [(4, 0)]


def off(addr):
    return addr - LOAD + 2


def keccak256(b):
    if keccak is None:
        raise SystemExit("pycryptodome needed: pip install pycryptodome")
    k = keccak.new(digest_bits=256)
    k.update(bytes(b))
    return k.hexdigest()


def load_prg(path):
    b = bytes(Path(path).read_bytes())
    h = keccak256(b)
    if h != PRG_HASH:
        raise SystemExit(f"{path}: keccak256 {h[:16]}... is not the on-chain prgHash - refusing")
    return b


# --- decoding --------------------------------------------------------------
def rd(prg, addr, n):
    return prg[off(addr):off(addr) + n]


def lohi(prg, addr, n=ROOMS):
    lo, hi = rd(prg, addr, n), rd(prg, addr + n, n)
    return [lo[i] | (hi[i] << 8) for i in range(n)]


def rle3_decode(prg, addr, magic=0xFF):
    out, p = [], off(addr)
    while True:
        v = prg[p]
        if v != magic:
            out.append(v); p += 1; continue
        val, rep = prg[p + 1], prg[p + 2]
        p += 3
        if rep == 0:
            break
        out.extend([val] * rep)
    return bytes(out), p - off(addr)


def rle3_encode(data, magic=0xFF):
    out, i = bytearray(), 0
    while i < len(data):
        v, n = data[i], 1
        while i + n < len(data) and data[i + n] == v and n < 0xFF:
            n += 1
        if n == 1 and v != magic:
            out.append(v)
        elif n == 2 and v != magic:
            out += bytes([v, v])
        else:
            out += bytes([magic, v, n])
        i += n
    out += bytes([magic, magic, 0])
    return bytes(out)


class Tony:
    def __init__(self, prg):
        self.prg = prg
        self.exits = {d: list(rd(prg, A["level_roomExits" + d], ROOMS)) for d in "NESW"}
        self.start = dict(room=rd(prg, A["level_startRoom"], 1)[0],
                          x=int.from_bytes(rd(prg, A["level_startPositionX"], 2), "little"),
                          y=rd(prg, A["level_startPositionY"], 1)[0],
                          state=rd(prg, A["level_startState"], 1)[0])
        self.room_ptr = lohi(prg, A["level_roomPtr"])
        self.obj_ctrl_ptr = lohi(prg, A["level_objectControlPtr"])
        self.obj_x_ptr = lohi(prg, A["level_objectPositionXPtr"])
        self.obj_y_ptr = lohi(prg, A["level_objectPositionYPtr"])
        self.obj_sizes = list(rd(prg, A["level_objectSizes"], ROOMS))
        self.materials = rd(prg, A["materials"], 255) + b"\x00"
        self.rooms, self.room_len = [], []
        for r in range(ROOMS):
            data, n = rle3_decode(prg, self.room_ptr[r])
            assert len(data) == W * H, f"room {r}: decoded {len(data)} bytes"
            self.rooms.append([list(data[i * W:(i + 1) * W]) for i in range(H)])
            self.room_len.append(n)
        self.objects = []
        for r in range(ROOMS):
            n = self.obj_sizes[r]
            ctrl = rd(prg, self.obj_ctrl_ptr[r], n)
            xs, ys = rd(prg, self.obj_x_ptr[r], n), rd(prg, self.obj_y_ptr[r], n)
            self.objects.append([dict(type=SO[c & 0x0F], value=c >> 4, x=xs[i], y=ys[i],
                                      ctrl_addr=self.obj_ctrl_ptr[r] + i)
                                 for i, c in enumerate(ctrl)])
        self.scheme = rd(prg, A["scheme_ldx"], 2)[1]
        # runtime collision classes (static map + drawn objects, through the engine's
        # own materials buffer), captured by tools/capture_runtime_rooms.py.  The
        # static map alone misses flame fire-chars, which are deadly at runtime.
        self.runtime = None
        rt = Path(__file__).parent.parent / "deliverables" / "onchain" / "runtime-collision.json"
        if rt.exists():
            self.runtime = {int(k): v for k, v in json.loads(rt.read_text())["rooms"].items()}
        self._sockets()

    # self-checks against what the source declares
    def selfcheck(self):
        e = self.exits
        checks = [
            ("start room is the title (29)", self.start["room"] == TITLE),
            ("title west exit -> room 18", e["W"][TITLE] == 18),
            ("room 0 exits E=1 S=4", e["E"][0] == 1 and e["S"][0] == 4),
            ("room 28 exits N=23 W=27", e["N"][28] == 23 and e["W"][28] == 27),
            ("boot: cli; jsr blankScreen", rd(self.prg, 0x08F7, 4) == bytes([0x58, 0x20, 0xE1, 0x2B])),
            ("scheme: ldx #GREEN", rd(self.prg, A["scheme_ldx"], 2) == bytes([0xA2, 0x02])),
            ("dead menu entry intact", rd(self.prg, A["cheatMenu"], 2) == bytes([0xA9, 0x9B])),
            ("30 rooms decode to 40x20", all(len(r) == H for r in self.rooms)),
            ("object counts sum to 214", sum(self.obj_sizes) == 214),
        ]
        bad = [n for n, ok in checks if not ok]
        if bad:
            raise SystemExit("self-check failed: " + "; ".join(bad))
        return checks

    # --- door sockets ------------------------------------------------------
    def mat(self, r, row, col):
        if self.runtime is not None:
            return self.runtime[r][row][col]
        return self.materials[self.rooms[r][row][col]]

    def _open(self, v):
        return not (v & WALL) and not (v & KILL)

    def _ew(self, r, col):
        rows = [self._open(self.mat(r, i, col)) for i in range(H)]
        return {i for i in range(H - 2) if rows[i] and rows[i + 1] and rows[i + 2]}

    def _ns(self, r, row, ladder=False):
        ok = []
        for c in range(W):
            v = self.mat(r, row, c)
            good = (self._open(v) or (v & LADDER and not v & WALL))
            if ladder:
                good = good and (v & LADDER)
            ok.append(bool(good))
        return {c for c in range(W - 1) if ok[c] and ok[c + 1]}

    def _sockets(self):
        self.east = [self._ew(r, W - 1) for r in range(ROOMS)]
        self.west = [self._ew(r, 0) for r in range(ROOMS)]
        self.top = [self._ns(r, 0) for r in range(ROOMS)]
        self.bottom = [self._ns(r, H - 1) for r in range(ROOMS)]
        self.top_ladder = [self._ns(r, 0, True) for r in range(ROOMS)]
        self.bottom_ladder = [self._ns(r, H - 1, True) for r in range(ROOMS)]

    def ew_fit(self, a, b):          # a on the left of b
        return bool(self.east[a] & self.west[b])

    def ns_fit(self, a, b):          # a above b (fall-through)
        return bool(self.bottom[a] & self.top[b])

    def ns_climb(self, a, b):        # ladder continues through the seam
        return bool(self.bottom_ladder[a] & self.top_ladder[b])

    # --- playable tier: floor-aligned doorways -------------------------------
    # Tony crosses a side door at his current height, so the far edge needs a
    # standable spot at the SAME floor row: a wall tile at row F under both of
    # his columns' worth of edge, with rows F-3..F-1 open and not deadly.  F=20
    # is the implicit floor at the bottom of the playfield (shipped behaviour
    # for rooms whose S exit is sealed).
    def edge_floors(self, r, side):
        cols = (0, 1) if side == "W" else (W - 2, W - 1)
        out = set()
        for F in range(3, H):
            above = all(self._open(self.mat(r, F - k, c)) for k in (1, 2, 3) for c in cols)
            floor = any(self.mat(r, F, c) & WALL for c in cols) and not any(self.mat(r, F, c) & KILL for c in cols)
            if above and floor:
                out.add(F)
        return out

    def arrive_ok(self, r, side, F):
        """Tony steps onto edge `side` of room r with his feet at row F (body rows F-3..F-1).
        Fine if the body zone is open and he either stands on a wall at F or drops through
        safe open tiles onto a wall further down; a deadly tile or falling off the bottom
        edge disqualifies (there is no floor below the playfield)."""
        cols = (0, 1) if side == "W" else (W - 2, W - 1)
        if F < 3 or not all(self._open(self.mat(r, F - k, c)) for k in (1, 2, 3) for c in cols):
            return False
        for row in range(F, H):
            v = [self.mat(r, row, c) for c in cols]
            if any(x & KILL for x in v):
                return False
            if any(x & WALL for x in v):
                return True
        return False

    def door_ok(self, a, b):           # walking east out of a, arriving safely in b
        return any(self.arrive_ok(b, "W", F) for F in self.edge_floors(a, "E"))

    def side_ok(self, a, b, d):
        """Every standable spot on a's side d arrives safely on b's opposite side -
        no invisible death doors on that edge."""
        opp = {"E": "W", "W": "E"}[d]
        floors = self.edge_floors(a, d)
        return bool(floors) and all(self.arrive_ok(b, opp, F) for F in floors)

    def pluggable(self, r):
        """Unwired vertical openings of r can be walled off without growing its RLE3 block."""
        cells = plug_cells(self, r, top=bool(self.top_ladder[r]), bottom=bool(self.bottom[r]))
        if not cells:
            return True
        grid = [row[:] for row in self.rooms[r]]
        for row, col, ch in cells:
            grid[row][col] = ch
        return len(rle3_encode(bytes(sum(grid, [])))) <= self.room_len[r]

    def ring_ok(self, a, b):           # a|b|a|b...: every standable edge spot arrives safely opposite
        ea, wa, eb, wb = (self.edge_floors(a, "E"), self.edge_floors(a, "W"),
                          self.edge_floors(b, "E"), self.edge_floors(b, "W"))
        return (bool(ea) and bool(eb) and bool(wa) and bool(wb)
                and all(self.arrive_ok(b, "W", F) for F in ea) and all(self.arrive_ok(a, "E", F) for F in wb)
                and all(self.arrive_ok(a, "W", F) for F in eb) and all(self.arrive_ok(b, "E", F) for F in wa))

    def loop_ok(self, r):              # room's east edge is its own west edge
        e, w = self.edge_floors(r, "E"), self.edge_floors(r, "W")
        return (bool(e) and bool(w) and all(self.arrive_ok(r, "W", F) for F in e)
                and all(self.arrive_ok(r, "E", F) for F in w))

    def safe_drop_cols(self, a, b):
        """Columns of a's bottom openings through which falling (or climbing) out of a
        lands safely in b: the 2-column shaft in b is open down to a wall tile, never a
        deadly one, never off the bottom."""
        cols = []
        for c in self.bottom[a]:
            for row in range(H):
                v = [self.mat(b, row, c), self.mat(b, row, c + 1)]
                if any(x & KILL for x in v):
                    break
                if any(x & WALL for x in v):
                    if row > 2:
                        cols.append(c)
                    break
        return cols

    def drop_ok(self, a, b):
        return bool(self.safe_drop_cols(a, b))

    TITLE_EXIT_FLOOR = 6    # Tony spawns on the title's upper platform and walks off it

    def entry_ok(self, r):
        return self.arrive_ok(r, "E", self.TITLE_EXIT_FLOOR)

    def summary(self, r):
        c = Counter(o["type"] for o in self.objects[r])
        return " ".join(f"{k}x{v}" if v > 1 else k for k, v in c.items()) or "-"


# --- castles ---------------------------------------------------------------
class Patch:
    def __init__(self, prg):
        self.base = prg
        self.out = bytearray(prg)
        self.records = []

    def set(self, addr, new, why):
        o = off(addr)
        old = bytes(self.base[o:o + len(new)])
        if bytes(self.out[o:o + len(new)]) != old:
            raise ValueError(f"overlapping patch at ${addr:04X}")
        if old == bytes(new):
            return
        self.out[o:o + len(new)] = new
        self.records.append(dict(addr=f"${addr:04X}", offset=o, old=old.hex(), new=bytes(new).hex(), why=why))

    def encoded(self):
        b = bytearray()
        for r in self.records:
            new = bytes.fromhex(r["new"])
            b += r["offset"].to_bytes(2, "big") + len(new).to_bytes(2, "big") + new
        return bytes(b)


def build_castle(t, spec):
    """spec: name, entry, exits {room: {N/E/S/W: target}}, scheme, cheat (int or None=clear)."""
    p = Patch(t.prg)
    p.set(A["level_roomExitsW"] + TITLE, bytes([spec["entry"]]), f"title gate -> room {spec['entry']}")
    exits = {int(r): dict(ex) for r, ex in spec["exits"].items()}
    # a castle is closed: every direction a spec leaves unmentioned is sealed,
    # otherwise an untouched original exit would leak into the rest of the demo
    for room in reachable_rooms(spec):
        for d in "NESW":
            exits.setdefault(room, {}).setdefault(d, NO)
    for room, ex in sorted(exits.items()):
        for d, target in ex.items():
            if target != NO and target not in exits and target != TITLE:
                raise SystemExit(f"room {room} {d} exit -> {target} leaves the castle")
            p.set(A["level_roomExits" + d] + room, bytes([target]),
                  f"room {room} {d} exit -> {'sealed' if target == NO else target}")
    # measured: a bottom opening with a sealed S exit drops Tony out of bounds onto the
    # dashboard rows, and a ladder into a sealed N exit is untested - wall them off
    walls = list(spec.get("walls", []))
    for room, ex in sorted(exits.items()):
        cells = plug_cells(t, room, top=ex["N"] == NO and bool(t.top_ladder[room]),
                           bottom=ex["S"] == NO and bool(t.bottom[room]))
        if cells:
            walls.append(dict(room=room, cells=cells, auto=True))
    if spec.get("scheme") is not None:
        s = spec["scheme"] if isinstance(spec["scheme"], int) else SCHEMES.index(spec["scheme"])
        p.set(A["scheme_ldx"] + 1, bytes([s]), f"boot colour scheme {SCHEMES[s]}")
    if spec.get("cheat", 0) is not None:
        c = spec.get("cheat", 0)
        stub = bytes([0xA9, c, 0x85, A["gameCheatState"], 0x4C]) + A["blankScreen"].to_bytes(2, "little")
        p.set(A["boot_jsr_blankScreen"], bytes([0x20]) + A["cheatMenu"].to_bytes(2, "little"),
              "boot: jsr stub (was jsr blankScreen)")
        p.set(A["cheatMenu"], stub, f"stub in dead menu: lda #${c:02X}; sta $2D; jmp blankScreen")
    for edit in spec.get("objects", []):
        addr = t.objects[edit["room"]][edit["index"]]["ctrl_addr"]
        new = (edit["value"] << 4) | [k for k, v in SO.items() if v == edit["type"]][0]
        p.set(addr, bytes([new]), f"room {edit['room']} object {edit['index']} -> {edit['type']} v{edit['value']}")
    for edit in walls:   # {room, cells: [[row, col, char], ...]}
        r = edit["room"]
        grid = [row[:] for row in t.rooms[r]]
        for row, col, ch in edit["cells"]:
            grid[row][col] = ch
        blob = rle3_encode(bytes(sum(grid, [])))
        if len(blob) > t.room_len[r]:
            raise SystemExit(f"room {r} wall edit grows compressed block {t.room_len[r]} -> {len(blob)} bytes")
        p.set(t.room_ptr[r], blob, f"room {r} map: {len(edit['cells'])} cells rewritten (block {t.room_len[r]}->{len(blob)}b)")
    p.walls = walls
    return p


def reachable_rooms(spec):
    seen, todo = set(), [spec["entry"]]
    while todo:
        r = todo.pop()
        if r in seen:
            continue
        seen.add(r)
        for target in spec["exits"].get(str(r), spec["exits"].get(r, {})).values():
            if target != NO:
                todo.append(target)
    return sorted(seen)


def emit(t, spec, outdir):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    p = build_castle(t, spec)
    slug = spec["name"].lower().replace(" ", "-")
    prg_path = outdir / f"castle-{slug}.prg"
    prg_path.write_bytes(bytes(p.out))
    enc = p.encoded()
    meta = dict(name=spec["name"], base_prgHash="0x" + PRG_HASH, patched_keccak256="0x" + keccak256(p.out),
                entry=spec["entry"], rooms=reachable_rooms(spec), scheme=SCHEMES[spec.get("scheme", 2)] if isinstance(spec.get("scheme", 2), int) else spec["scheme"],
                cheat_byte=spec.get("cheat", 0), spec=spec, walls=p.walls, patch_bytes=len(enc), records=p.records, hex=enc.hex(),
                credits=["Tony: Born for Adventure - code Maciej Malecki, graphics Rafal Dudek, music Sami Juntunen (MIT)",
                         "runtime: minimal64 by nopsta (GPL-2.0)"])
    (outdir / f"castle-{slug}.json").write_text(json.dumps(meta, indent=1))
    return prg_path, meta


# --- sample castles: chosen deterministically from the data --------------
def sample_specs(t):
    R = range(TITLE)
    entries = [r for r in R if t.entry_ok(r)]
    score = lambda r: t.obj_sizes[r]

    # 1. THE RING: walk east forever - a's east edge opens on b, b's east edge opens
    #    on a; every standable spot on those edges arrives safely.  West edges are
    #    sealed (invisible walls, shipped behaviour).  Unwired vertical openings get
    #    walled off automatically, so rooms only need to be pluggable.
    neighbours = lambda a, b: t.exits["E"][a] == b or t.exits["E"][b] == a
    flat = lambda r: not t.top_ladder[r] and not t.bottom[r]
    usable = lambda r: t.pluggable(r)
    rings = [(a, b) for a in entries for b in R
             if a != b and not neighbours(a, b) and usable(a) and usable(b)
             and t.side_ok(a, b, "E") and t.side_ok(b, a, "E")]
    a, b = max(rings, key=lambda ab: (flat(ab[0]) + flat(ab[1]), score(ab[0]) + score(ab[1])))
    ring = dict(name="The Ring", entry=a, scheme="AMBER", cheat=0,
                exits={str(a): {"E": b}, str(b): {"E": a}})

    # 2. THE WELL: descend.  Entry room whose floor hole drops safely into a
    #    non-neighbour; from there a floor-aligned door east into a third, final
    #    chamber (with the way back if that door works in both directions).
    orig_ns = {(r, t.exits["S"][r]) for r in R if t.exits["S"][r] != NO}
    best = None
    for a in entries:
        for b in R:
            if b == a or (a, b) in orig_ns or not t.drop_ok(a, b) or not usable(b):
                continue
            for c in R:
                if c in (a, b) or not usable(c) or neighbours(b, c) or not t.side_ok(b, c, "E"):
                    continue
                back = t.side_ok(c, b, "W")
                cand = (back, flat(b) + flat(c), score(a) + score(b) + score(c), a, b, c)
                if best is None or cand > best:
                    best = cand
    back, _, _, a, b, c = best
    well = dict(name="The Well", entry=a, scheme="BLUE", cheat=0,
                exits={str(a): {"S": b}, str(b): {"E": c}, str(c): {"W": b if back else NO}})

    # 3. THE ESCHER CORRIDOR: an antechamber, then a room whose east edge is its own
    #    west edge (both directions, every edge floor) - walk either way forever.
    #    Infinite lives baked as a trait.  Unwired vertical openings get walled off.
    best = None
    for L in R:
        if not t.loop_ok(L) or not usable(L):
            continue
        for a in entries:
            if a == L or neighbours(a, L) or not usable(a) or not t.side_ok(a, L, "E"):
                continue
            cand = (flat(L) + flat(a), score(L) + score(a), a, L)
            if best is None or cand > best:
                best = cand
    _, _, a, L = best
    escher = dict(name="The Escher Corridor", entry=a, scheme="C64", cheat=CHEAT["LIVES"],
                  exits={str(a): {"E": L}, str(L): {"E": L, "W": L}})
    return [ring, well, escher]


def plug_cells(t, r, top=False, bottom=False):
    """Wall cells that close the openings in the top two / bottom two rows of room r,
    using the room's most common wall char of that edge row (falls back to any wall
    char in the room)."""
    def wall_char(row):
        c = Counter(t.rooms[r][row][x] for x in range(W) if t.mat(r, row, x) & WALL)
        if not c:
            c = Counter(t.rooms[r][y][x] for y in range(H) for x in range(W) if t.mat(r, y, x) & WALL)
        return c.most_common(1)[0][0]
    cells = []
    if bottom:
        ch = wall_char(H - 1)
        cells += [[row, c, ch] for row in (H - 2, H - 1) for c in range(W)
                  if not (t.mat(r, row, c) & WALL) and any(c in (w, w + 1) for w in t.bottom[r])]
    if top:
        ch = wall_char(0)
        cells += [[row, c, ch] for row in (0, 1) for c in range(W)
                  if (t.mat(r, row, c) & LADDER) and any(c in (w, w + 1) for w in t.top_ladder[r])]
    return cells


# --- CLI -------------------------------------------------------------------
def cmd_info(t):
    print(f"on-chain PRG verified: keccak256 = 0x{PRG_HASH}  ({len(t.prg)} bytes, ${LOAD:04X}-${LOAD + len(t.prg) - 3:04X})")
    for n, ok in t.selfcheck():
        print(f"  [ok] {n}")
    print("\nPATCH TARGETS (address / file offset / size)")
    rows = [
        ("title gate = level_roomExitsW[29]", A["level_roomExitsW"] + TITLE, 1),
        ("level_roomExitsN[0..29]", A["level_roomExitsN"], 30), ("level_roomExitsE[0..29]", A["level_roomExitsE"], 30),
        ("level_roomExitsS[0..29]", A["level_roomExitsS"], 30), ("level_roomExitsW[0..29]", A["level_roomExitsW"], 30),
        ("level_startRoom / X(word) / Y / state", A["level_startRoom"], 5),
        ("boot colour scheme operand (ldx #n, 0-5)", A["scheme_ldx"] + 1, 1),
        ("boot jsr blankScreen (-> cheat stub)", A["boot_jsr_blankScreen"], 3),
        ("dead cheatMenu entry (stub home)", A["cheatMenu"], 7),
        ("materials (collision class per char)", A["materials"], 255),
        ("level_roomPtr lo[30] hi[30]", A["level_roomPtr"], 60),
        ("level_objectControlPtr lo/hi", A["level_objectControlPtr"], 60),
        ("level_objectPositionXPtr lo/hi", A["level_objectPositionXPtr"], 60),
        ("level_objectPositionYPtr lo/hi", A["level_objectPositionYPtr"], 60),
        ("level_objectSizes[30]", A["level_objectSizes"], 30),
        ("bat paths path0..9 (+ptrs, lengths)", A["paths"], 0x96E6 - A["paths"]),
    ]
    for name, addr, n in rows:
        print(f"  {name:44s} ${addr:04X}  +0x{off(addr):05X}  {n:3d} B")
    print("\nPER-ROOM DATA (compressed map block / object list)")
    for r in range(ROOMS):
        g = GRID[r]
        print(f"  room {r:2d} grid({g[0]},{g[1]})  map ${t.room_ptr[r]:04X} ({t.room_len[r]:3d}B RLE3)  "
              f"objects ${t.obj_ctrl_ptr[r]:04X} x{t.obj_sizes[r]:2d}  exits N/E/S/W="
              f"{'/'.join('-' if t.exits[d][r] == NO else str(t.exits[d][r]) for d in 'NESW'):11s} {t.summary(r)}")


def cmd_census(t):
    R = range(TITLE)
    print("door sockets per room (E/W: open 3-row windows at the edge column; N/S: open 2-col windows)")
    for r in range(ROOMS):
        print(f"  room {r:2d}: E{sorted(t.east[r])} W{sorted(t.west[r])} top{len(t.top[r])} bottom{len(t.bottom[r])}"
              f"{' ladder-top' if t.top_ladder[r] else ''}{' ENTRY' if r != TITLE and t.entry_ok(r) else ''}")
    ew = [(a, b) for a, b in product(R, R) if a != b and t.ew_fit(a, b)]
    ns = [(a, b) for a, b in product(R, R) if a != b and t.ns_fit(a, b)]
    print(f"\nside-by-side pairs: {len(ew)}   stacked pairs: {len(ns)}   "
          f"self-loops: {[r for r in R if t.ew_fit(r, r)]}   entry-capable: {[r for r in R if t.entry_ok(r)]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["info", "census", "samples", "castle"])
    ap.add_argument("prg")
    ap.add_argument("outdir", nargs="?")
    ap.add_argument("--spec", help="castle spec JSON (for `castle`)")
    args = ap.parse_args()
    t = Tony(load_prg(args.prg))
    t.selfcheck()
    if args.cmd == "info":
        cmd_info(t)
    elif args.cmd == "census":
        cmd_census(t)
    elif args.cmd == "samples":
        for spec in sample_specs(t):
            path, meta = emit(t, spec, args.outdir or ".")
            print(f"{meta['name']:22s} entry {meta['entry']:2d} rooms {meta['rooms']} scheme {meta['scheme']:7s} "
                  f"cheat ${meta['cheat_byte']:02X}  {meta['patch_bytes']:3d} patch bytes  -> {path.name}")
            for r in meta["records"]:
                print(f"     {r['addr']} +0x{r['offset']:05X}  {r['old']} -> {r['new']}   {r['why']}")
    elif args.cmd == "castle":
        spec = json.loads(Path(args.spec).read_text())
        path, meta = emit(t, spec, args.outdir or ".")
        print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
