#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线解释器：真的按 spec.json 的命令跑一遍（不是查表）。

支持子集：scoreboard / summon / tag / tp / fill / setblock / kill / execute(if score,
as, at, positioned, run)。title/tellraw/titleraw/playsound/effect/particle 记日志。
"""
from __future__ import annotations

import json
import math
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import noise as N  # noqa: E402

SPEC = json.loads((HERE / "spec.json").read_text(encoding="utf-8"))
BASE_Y = int(SPEC["blocks"][0]["command"].split()[2])   # boot00: setblock 0 <BASE_Y> 0 air
BY_ID = {b["id"]: b for b in SPEC["blocks"]}
HEADS = [(b["id"], max(b["delay"], 1), b["type"]) for b in SPEC["blocks"]
         if b["type"] in ("impulse", "repeat")]


def w32(v: int) -> int:
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


class Ent:
    _n = 0

    def __init__(self, pos, tags=(), kind="armor_stand"):
        Ent._n += 1
        self.id = Ent._n
        self.pos = list(pos)
        self.tags = set(tags)
        self.kind = kind
        self.sc: dict[str, int] = {}

    def __repr__(self):
        return f"<{self.kind}#{self.id} {[round(v, 2) for v in self.pos]} {sorted(self.tags)}>"


class World:
    def __init__(self):
        self.ents: list[Ent] = []
        self.fake: dict[str, dict[str, int]] = {}
        self.blocks: dict[tuple[int, int, int], str] = {}
        self.chat: list[str] = []
        self.log: list[str] = []

    def get(self, holder, obj) -> int:
        if isinstance(holder, Ent):
            return holder.sc.get(obj, 0)
        return self.fake.get(holder, {}).get(obj, 0)

    def set(self, holder, obj, v):
        v = w32(v)
        if isinstance(holder, Ent):
            holder.sc[obj] = v
        else:
            self.fake.setdefault(holder, {})[obj] = v


# ---------------------------------------------------------------- 选择器
_SEL = re.compile(r"^@([a-z])(?:\[(.*)\])?$")


def split_args(s: str) -> list[str]:
    out, buf, depth = [], [], 0
    for ch in s:
        if ch in "[{(":
            depth += 1
        elif ch in "]})":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf))
    return [x.strip() for x in out if x.strip()]


def select(w: World, sel: str, s: Ent | None, pos) -> list[Ent]:
    m = _SEL.match(sel)
    assert m, sel
    var, inner = m.group(1), m.group(2)
    if var not in ("s", "e"):
        raise SystemExit(f"selector @{var}")
    cand = ([s] if s is not None else []) if var == "s" else list(w.ents)
    r_only = None
    c_limit = None
    for a in split_args(inner) if inner else []:
        k, v = a.split("=", 1)
        if k == "type":
            cand = [x for x in cand if x.kind == v]
        elif k == "tag":
            cand = [x for x in cand if (v[1:] not in x.tags if v.startswith("!") else v in x.tags)]
        elif k == "r":
            r_only = float(v)
        elif k == "c":
            c_limit = int(v)
        elif k == "scores":
            for item in split_args(v[1:-1]):
                m2 = re.match(r"^(\w+)\s*=\s*(-?\d+)(?:\.\.(-?\d+))?$", item)
                assert m2, (v, item)
                obj, lo = m2.group(1), int(m2.group(2))
                hi = int(m2.group(3)) if m2.group(3) is not None else lo
                cand = [x for x in cand if lo <= x.sc.get(obj, 0) <= hi]
        else:
            raise SystemExit(f"selector arg {k}")
    if r_only is not None:
        cand = [x for x in cand if math.dist(x.pos, pos) <= r_only]
    if c_limit is not None:
        cand = cand[:c_limit] if c_limit >= 0 else cand[c_limit:]
    return cand


# ---------------------------------------------------------------- 坐标
def coord(tok: str, base: float) -> float:
    if tok == "~":
        return base
    if tok.startswith("~"):
        return base + float(tok[1:])
    return float(tok)


def num(v: float) -> int:
    return math.floor(v + 1e-9)


# ---------------------------------------------------------------- 叶子命令
def do_leaf(toks, w: World, s, pos) -> bool:
    head = toks[0]
    if head == "scoreboard":
        return do_scoreboard(toks, w, s, pos)
    if head == "summon":
        p = [coord(toks[2 + i], pos[i]) for i in range(3)] if len(toks) >= 5 else list(pos)
        p[1] = float(math.floor(p[1] + 1e-9))     # 重力：落到方块顶
        w.ents.append(Ent(p))
        return True
    if head == "tag":
        tgt = select(w, toks[1], s, pos)
        for x in tgt:
            (x.tags.add if toks[2] == "add" else x.tags.discard)(toks[3])
        return bool(tgt)
    if head == "tp":
        tgt = select(w, toks[1], s, pos)
        p = [coord(toks[2 + i], pos[i]) for i in range(3)]
        for x in tgt:
            x.pos = list(p)
        return bool(tgt)
    if head in ("fill", "setblock"):
        if head == "fill":
            x1, y1, z1 = (num(coord(toks[1 + i], pos[i])) for i in range(3))
            x2, y2, z2 = (num(coord(toks[4 + i], pos[i])) for i in range(3))
            block = toks[7]
            lo = [min(x1, x2), min(y1, y2), min(z1, z2)]
            hi = [max(x1, x2), max(y1, y2), max(z1, z2)]
            for x in range(lo[0], hi[0] + 1):
                for y in range(lo[1], hi[1] + 1):
                    for z in range(lo[2], hi[2] + 1):
                        w.blocks[(x, y, z)] = block
            return True
        x, y, z = (num(coord(toks[1 + i], pos[i])) for i in range(3))
        w.blocks[(x, y, z)] = toks[4]
        return True
    if head == "kill":
        tgt = select(w, toks[1], s, pos)
        for x in tgt:
            w.ents.remove(x)
        return bool(tgt)
    if head in ("title", "titleraw", "tellraw"):
        w.chat.append(" ".join(toks[1:]))
        return True
    if head in ("playsound", "effect", "particle", "tickingarea"):
        return True
    raise SystemExit(f"unhandled leaf: {toks}")


RNG = random.Random(20261114)


def do_scoreboard(toks, w: World, s, pos) -> bool:
    if toks[1] == "objectives":
        return True
    verb = toks[2]
    if verb == "random":
        holders = select(w, toks[3], s, pos) if toks[3].startswith("@") else [toks[3]]
        lo, hi = int(toks[5]), int(toks[6])
        v = RNG.randint(lo, hi)
        for h in holders:
            w.set(h, toks[4], v)
        return True
    if verb in ("set", "add", "remove", "reset", "get"):
        if verb == "get":
            return False
        holders = select(w, toks[3], s, pos) if toks[3].startswith("@") else [toks[3]]
        if not holders:
            return False
        obj = toks[4]
        if verb == "reset":
            for h in holders:
                (h.sc if isinstance(h, Ent) else w.fake.setdefault(h, {})).pop(obj, None)
            return True
        val = int(toks[5])
        for h in holders:
            base = w.get(h, obj)
            w.set(h, obj, val if verb == "set" else base + val if verb == "add" else base - val)
        return True
    if verb == "operation":
        holders = select(w, toks[3], s, pos) if toks[3].startswith("@") else [toks[3]]
        if not holders:
            return False
        tobj, op = toks[4], toks[5]
        sh, sobj = toks[6], toks[7]
        src = select(w, sh, s, pos)[0] if sh.startswith("@") else sh
        b = w.get(src, sobj)
        for h in holders:
            a = w.get(h, tobj)
            if op == "=":
                r = b
            elif op == "+=":
                r = a + b
            elif op == "-=":
                r = a - b
            elif op == "*=":
                r = a * b
            elif op == "/=":
                r = N.tdiv(a, b) if b else a
            elif op == "%=":
                r = N.tmod(a, b) if b else a
            elif op == "<":
                r = 1 if b < a else 0
            elif op == ">":
                r = 1 if b > a else 0
            else:
                raise SystemExit(f"op {op}")
            w.set(h, tobj, r)
        return True
    raise SystemExit(f"scoreboard {verb}")


# ---------------------------------------------------------------- execute
def match_range(v: int, rng: str) -> bool:
    if ".." in rng:
        lo, hi = rng.split("..")
        return (not lo or v >= int(lo)) and (not hi or v <= int(hi))
    return v == int(rng)


def do_execute(toks, i, w: World, s, pos) -> bool:
    while i < len(toks):
        t = toks[i]
        if t in ("if", "unless"):
            kind = toks[i + 1]
            if kind == "score":
                a, obj = toks[i + 2], toks[i + 3]
                if toks[i + 4] == "matches":
                    rng = toks[i + 5]; i += 6
                else:
                    raise SystemExit(f"if score cmp {toks[i+4]}")
                holder = select(w, a, s, pos)[0] if a.startswith("@") else a
                val = w.get(holder, obj)
                ok = match_range(val, rng)
            elif kind == "entity":
                sel = toks[i + 2]; i += 3
                ok = bool(select(w, sel, s, pos))
            elif kind == "block":
                x, y, z = (num(coord(toks[i + 2 + k], pos[k])) for k in range(3))
                want = toks[i + 5]; i += 6
                ok = w.blocks.get((x, y, z), "minecraft:air") in (want, want.replace("minecraft:", ""))
            else:
                raise SystemExit(f"if {kind}")
            if (t == "if") != ok:
                return False
        elif t == "as":
            for e2 in select(w, toks[i + 1], s, pos):
                do_execute(toks, i + 2, w, e2, pos)
            return True
        elif t == "at":
            for e2 in select(w, toks[i + 1], s, pos):
                do_execute(toks, i + 2, w, s, e2.pos)
            return True
        elif t == "positioned":
            pos = [coord(toks[i + 1 + k], pos[k]) for k in range(3)]
            i += 4
        elif t == "run":
            return do_leaf(toks[i + 1:], w, s, pos)
        else:
            raise SystemExit(f"exec token {t}")
    return True


def run_cmd(cmd: str, w: World, s=None, pos=(0, 0, 0)) -> bool:
    toks = cmd.split()
    if toks[0] == "execute":
        return do_execute(toks, 1, w, s, pos)
    return do_leaf(toks, w, s, pos)


# ---------------------------------------------------------------- 主循环
def run_chain(w, head):
    bid = head
    while bid:
        bp = BY_ID[bid]["pos"]
        run_cmd(BY_ID[bid]["command"], w, None, (bp[0] + 0.5, bp[1] + 0.5, bp[2] + 0.5))
        bid = BY_ID[bid]["next"]


def main() -> None:
    ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    if len(sys.argv) > 2:
        global RNG
        RNG = random.Random(int(sys.argv[2]))
    w = World()
    total = 0
    for run_idx in range(2):                     # 跑两轮：第二轮验证"重触发不会秒完成"
        for tick in range(ticks):
            total += 1
            for head, delay, mode in HEADS:
                if mode == "impulse":
                    fire = tick == 0
                else:
                    fire = tick % delay == 0
                if fire:
                    run_chain(w, head)
            if w.fake.get("fb_state", {}).get("ctl") == 99:
                break
        else:
            raise SystemExit(f"run {run_idx} 没跑完（state={w.fake.get('fb_state')}）")
        print(f"--- run {run_idx + 1} 完成于第 {total} tick，种子 {w.fake['fb_seed']['nz']}")
        if run_idx == 0:
            run_chain(w, "boot00")               # 模拟"再放一次红石块"
    cols = [e for e in w.ents if "nt_col" in e.tags]
    g = lambda name: w.fake.get(name, {}).get("ctl")
    print(f"ticks={ticks} entities={len(w.ents)} cols={len(cols)} blocks={len(w.blocks)}")
    print("final state:", g("fb_state"), "scan:", g("fb_n"), "band:", g("fb_b"))

    got = {(e.sc.get("px"), e.sc.get("pz")): e for e in cols}
    exp = {(px, pz) for pz in N.GRID for px in N.GRID}
    missing, extra = exp - set(got), set(got) - exp
    assert not missing and not extra, (len(missing), len(extra))

    salt = w.fake.get("fb_seed", {}).get("nz", 0)
    print("seed:", salt)
    model = {(c[0], c[1]): c for c in N.columns(salt)}
    diff = [(k, got[k].sc.get("hgt"), model[k][2]) for k in sorted(exp)
            if got[k].sc.get("hgt") != model[k][2]]
    assert not diff, diff[:5]
    print(f"✓ {len(exp)} 根柱子的 hgt 与 noise.py 模型逐格相同")

    # 地形方块
    x0, z0 = 0, 24
    heights = {k: model[k][2] for k in exp}
    total_fill = sum(4 * h for h in heights.values())
    floor_blocks = 4 * len(exp)     # 每根柱子占 2×2
    print(f"地形方块 = 4×Σ高度 = {total_fill}，地板 {floor_blocks}")

    bad = []
    for (px, pz), h in heights.items():
        for dx in (0, 1):
            for dz in (0, 1):
                x, z = x0 + px - 1 + dx, z0 + pz - 1 + dz
                top = BASE_Y + 1 + h
                for y in range(BASE_Y + 2, top + 1):
                    if (x, y, z) not in w.blocks:
                        bad.append(("hole", x, y, z))
                if w.blocks.get((x, top, z)) not in ("minecraft:grass", "minecraft:snow"):
                    bad.append(("top", x, top, z, w.blocks.get((x, top, z))))
    assert not bad, bad[:8]
    print("✓ 每列从 y=2 到顶面连续，顶面是草/雪")
    snow = sum(1 for (px, pz), h in heights.items() if h >= 14)
    print(f"✓ 雪顶柱 {snow} 根（h≥14）")

    hist = {h: sum(1 for k in exp if model[k][2] == h) for h in range(2, 19) if any(model[k][2] == h for k in exp)}
    print("高度分布:", hist)
    print("最后一条 chat:", w.chat[-1][:160] if w.chat else None)


if __name__ == "__main__":
    main()
