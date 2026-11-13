#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""值噪声 fBm + 3×3 邻域平滑 地形发生器（MCBE 命令方块）。

流程：
  1. GRID_W×GRID_W 个隐形盔甲架（默认 16×16=256）= (2·GRID_W)² 地形的 2×2 柱子。
  2. 每根柱子并行算 3 层值噪声（晶格哈希 + 1/256 定点双线性 + fBm），得到"中间高度"。
  3. 用 3×3 邻域均值（边界按实际邻居数归一化）平滑两遍 —— 照 skill 的 gaussian-filter.md，
     但把邻域采样从实体搬到计分板，一条 execute 就够。
  4. 减偏移 → 夹到 2..18 → 按 17 档铺方块。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# 本地工作区：scripts 在 .dsh 技能目录；提交到技能仓库后：scripts 在仓库根。
_SCRIPTS = [ROOT / "scripts", ROOT / ".dsh/skills/mcbe-command-blocks/scripts"]
for _p in _SCRIPTS:
    if (_p / "bdxgen.py").exists():
        sys.path.insert(0, str(_p))
        break
else:
    raise SystemExit(f"找不到 bdxgen.py，试过: {_SCRIPTS}")
sys.path.insert(0, str(HERE))

from bdxgen import Block as BdxBlock, BuildBlock, write_build_bdx  # noqa: E402
import noise as N  # noqa: E402

# ---------------------------------------------------------------- 布局
WIDTH = 16
BASE_Y = 64
Y = dict(boot=0, prep=1, grid=2, calc1=4, draw=26)
PREP_Y = BASE_Y + Y["prep"]
TX, TZ = 0, 24              # 地形西南角
SPAN = N.GRID_W * 2         # 32 格
COLS_PER_ROW = N.GRID_W // 2  # 每 tick 2 根，16 根/行 → 8 tick/行
assert N.GRID_W % 2 == 0, "GRID_W 必须是偶数（每 tick 两根柱子）"
ROW_ADVANCE = 4             # 每 tick 游标前进 4 格
ROW_WRAP = -ROW_ADVANCE * (COLS_PER_ROW - 1)   # 行尾回到列首
FLOOR_Y = BASE_Y

CTL, NZ = "ctl", "nz"
COL, CUR = "nt_col", "nt_cursor"
R_COL = 0.6          # 柱子/游标的局部选择半径

# 每个实体变量一个 objective；u 既做坐标暂存，也做角哈希的临时寄存器。
OBJS = ["px", "pz", "hgt", "u", "ix", "fx", "fx2", "iz", "fz", "fz2",
        "base", "hh", "bi", "acc", "cnt"]

CONST = {
    "k1": 1, "k2": 2, "k4": 4, "k65536": 65536, "k251": 251,
    "k127": 127, "k311": 311,
    "kbias": N.BIAS, "kdiv": N.DIV, "kmidraw": N.MID_RAW, "koffraw": N.OFF_RAW,
    "ksalty": N.SALT_MAX,
    "ko1": 127, "ko2": 311, "ko3": 438,   # 角 0 的偏移是 0，不占常量
}
for _i, _oc in enumerate(N.OCTAVES, start=1):
    CONST[f"kd{_i}"] = _oc["L"]
    CONST[f"kl{_i}"] = 256 // _oc["L"]
    CONST[f"ks{_i}"] = _oc["seed"]
    if _oc["amp"] != 1:
        CONST[f"ka{_i}"] = _oc["amp"]
    if _oc.get("ox"):
        CONST[f"kox{_i}"] = _oc["ox"]
    if _oc.get("oz"):
        CONST[f"koz{_i}"] = _oc["oz"]


def e(*subs: str, run: str) -> str:
    return "execute " + " ".join(subs) + " run " + run


def gate(raw: str, state: int) -> str:
    """raw 形如 "execute as @e[...] run ..."：把状态门插到最前面。"""
    assert raw.startswith("execute ")
    return f"execute if score fb_cur {CTL} matches {state} " + raw[len("execute "):]


class Chain:
    def __init__(self, name: str, mode: str, delay: int, y: int, redstone: str = "always_active"):
        self.name, self.mode, self.delay, self.y, self.redstone = name, mode, delay, y, redstone
        self.cmds: list[str] = []
        self.notes: list[str] = []

    def add(self, cmd: str, note: str = "") -> None:
        assert cmd, note
        self.cmds.append(cmd)
        self.notes.append(note)

    def layout(self, z0: int = 1):
        cells, x, z, d = [], 0, z0, 1
        for i in range(len(self.cmds)):
            if i:
                nx = x + d
                if 0 <= nx < WIDTH:
                    x = nx
                else:
                    z += 1
                    d = -d
            cells.append((x, self.y, z))
        out = []
        for i, (x, y, z) in enumerate(cells):
            if i + 1 < len(cells):
                nx, _, nz = cells[i + 1]
                face = "east" if nx > x else "west" if nx < x else "south" if nz > z else "north"
            else:
                face = "east"
            out.append((x, y, z, face))
        return out


# ---------------------------------------------------------------- boot
def build_boot() -> Chain:
    ch = Chain("boot", "impulse", 0, BASE_Y + Y["boot"], redstone="needs_redstone")
    ch.add(f"setblock 0 {BASE_Y} 0 air", "自清理触发脉冲")
    for o in [CTL, NZ] + OBJS:
        ch.add(f"scoreboard objectives add {o} dummy", f"objective {o}")
    for k, v in CONST.items():
        ch.add(f"scoreboard players set {k} {NZ} {v}", f"常量 {k}={v}")
    ch.add(f"kill @e[tag={COL}]", "清旧柱子")
    ch.add(f"kill @e[tag={CUR}]", "清旧游标")
    ch.add("tickingarea remove noise", "清旧常加载")
    ch.add(f"tickingarea add 0 {FLOOR_Y-4} 0 {SPAN-1} {FLOOR_Y+40} {TZ+SPAN+3} noise", "圈常加载：墙+地形")
    ch.add(f"scoreboard players add fb_seed {NZ} 1", "兜底种子 +1")
    ch.add(f"scoreboard players operation fb_seed {NZ} %= ksalty {NZ}", "兜底种子夹回范围")
    ch.add(f"scoreboard players random fb_seed {NZ} 0 {N.SALT_MAX}", "抽随机种子")
    for h in range(N.H_MIN, N.H_MAX + 1):
        ch.add(f"scoreboard players set bn{h} {CTL} 0", f"清零 bn{h}")
    for k in ("fb_cx", "fb_cz", "fb_n", "fb_b", "fb_t", "fb_cur"):
        ch.add(f"scoreboard players set {k} {CTL} 0", f"清零 {k}（重跑必须）")
    ch.add(f"scoreboard players set fb_state {CTL} 10", "状态=10 等区块加载")
    ch.add('tellraw @a {"rawtext":[{"text":"§e值噪声 fBm 启动 §7| 种子 "},{"score":{"name":"fb_seed","objective":"nz"}},'
            f'{{"text":" §7| {SPAN}×{SPAN} 扫描"}}]}}', "提示")
    return ch


# ---------------------------------------------------------------- prep
def build_prep() -> Chain:
    ch = Chain("prep", "repeat", 2, PREP_Y)
    g = f"if score fb_cur {CTL} matches 10"
    ch.add(f"scoreboard players operation fb_cur {CTL} = fb_state {CTL}", "状态快照")
    ch.add(e(g, run=f"fill {TX} {FLOOR_Y} {TZ} {TX+SPAN-1} {FLOOR_Y} {TZ+SPAN-1} minecraft:stone"), "地形底板")
    ch.add(e(g, run=f"fill {TX} {FLOOR_Y+1} {TZ} {TX+SPAN-1} {FLOOR_Y+20} {TZ+SPAN-1} air"), "清空地形体")
    ch.add(e(g, run=f"kill @e[tag={COL}]"), "再清柱子")
    ch.add(e(g, run=f"kill @e[tag={CUR}]"), "再清游标")
    ch.add(e(g, run=f"summon armor_stand 1 {FLOOR_Y+1} {TZ+1}"), "召唤扫描游标")
    ch.add(e(g, f"positioned 1 {FLOOR_Y+1} {TZ+1}",
             run=f"tag @e[type=armor_stand,r=0.6] add {CUR}"), "标记游标")
    ch.add(e(g, run=f"effect @e[tag={CUR}] invisibility 999999 0 true"), "游标隐身")
    for k in ("fb_cx", "fb_cz", "fb_n", "fb_b"):
        ch.add(e(g, run=f"scoreboard players set {k} {CTL} 0"), f"再清 {k}")
    ch.add(e(g, run=f"scoreboard players set fb_state {CTL} 1"), "状态=1 进入扫描")
    ch.add(e(g, run=f'titleraw @a actionbar {{"rawtext":[{{"text":"§b值噪声 fBm §7· 扫描 {N.GRID_W*N.GRID_W} 格"}}]}}'), "提示")
    return ch


# ---------------------------------------------------------------- grid（每 pass 2 根柱子）
def build_grid() -> Chain:
    ch = Chain("grid", "repeat", 1, BASE_Y + Y["grid"])
    g = f"if score fb_cur {CTL} matches 1"
    ch.add(f"scoreboard players operation fb_cur {CTL} = fb_state {CTL}", "状态快照")

    def at_cursor(dx: int = 0):
        subs = [f"as @e[tag={CUR}]", "at @s"]
        if dx:
            subs.append(f"positioned ~{dx} ~ ~")
        return subs

    # 两根柱子都先召唤、立刻用 r=0.6 的局部选择器转正。
    # 不再用 `@e[type=armor_stand] unless ...` 全表扫描（256 根柱子时很贵）。
    for dx in (0, 2):
        ch.add(e(g, *at_cursor(dx), run="summon armor_stand ~ ~ ~"), f"召唤柱子 x+{dx}")
        ch.add(e(g, *at_cursor(dx),
                 run=f"tag @e[type=armor_stand,r={R_COL},tag=!{CUR}] add {COL}"), f"柱子 x+{dx} 转正")

    # px 只算一次基准，两根柱子共享；A=4cx+1，B=A+2。
    ch.add(e(g, run=f"scoreboard players operation fb_t {CTL} = fb_cx {CTL}"), "px 基准")
    ch.add(e(g, run=f"scoreboard players operation fb_t {CTL} *= k4 {NZ}"), "px ×4")
    ch.add(e(g, run=f"scoreboard players operation fb_t {CTL} += k1 {NZ}"), "px +1")
    ch.add(e(g, *at_cursor(0),
             run=f"scoreboard players operation @e[tag={COL},r={R_COL},c=1] px = fb_t {CTL}"), "写 A.px")
    ch.add(e(g, run=f"scoreboard players operation fb_t {CTL} += k2 {NZ}"), "px +2")
    ch.add(e(g, *at_cursor(2),
             run=f"scoreboard players operation @e[tag={COL},r={R_COL},c=1] px = fb_t {CTL}"), "写 B.px")

    # pz 两根柱子相同。
    ch.add(e(g, run=f"scoreboard players operation fb_t {CTL} = fb_cz {CTL}"), "pz 基准")
    ch.add(e(g, run=f"scoreboard players operation fb_t {CTL} *= k2 {NZ}"), "pz ×2")
    ch.add(e(g, run=f"scoreboard players operation fb_t {CTL} += k1 {NZ}"), "pz +1")
    for dx in (0, 2):
        ch.add(e(g, *at_cursor(dx),
                 run=f"scoreboard players operation @e[tag={COL},r={R_COL},c=1] pz = fb_t {CTL}"),
               f"写 {'A' if dx == 0 else 'B'}.pz")

    ch.add(e(g, run=f"scoreboard players add fb_n {CTL} 2"), "计数 +2")
    ch.add(e(g, run=f"scoreboard players add fb_cx {CTL} 1"), "列 +1")
    ch.add(e(g, f"if score fb_cx {CTL} matches {COLS_PER_ROW}..", run=f"scoreboard players set fb_cx {CTL} 0"), "列回绕")
    ch.add(e(g, f"if score fb_cx {CTL} matches 0", f"as @e[tag={CUR}]", "at @s",
             run=f"tp @s ~{ROW_WRAP} ~ ~2"), "换行：回列首 z+2")
    ch.add(e(g, f"if score fb_cx {CTL} matches 0", run=f"scoreboard players add fb_cz {CTL} 1"), "行 +1")
    ch.add(e(g, f"if score fb_cx {CTL} matches 1..", f"as @e[tag={CUR}]", "at @s",
             run=f"tp @s ~{ROW_ADVANCE} ~ ~"), "列前进 4 格")
    ch.add(e(g, f"if score fb_n {CTL} matches {N.GRID_W * N.GRID_W}..",
             run=f"scoreboard players set fb_state {CTL} 2"), "扫描完成 → 计算")
    ch.add(e(g, f"if score fb_n {CTL} matches {N.GRID_W * N.GRID_W}..",
             run='titleraw @a actionbar {"rawtext":[{"text":"§b值噪声 fBm §7· 计算高度"}]}'), "提示")
    return ch


# ---------------------------------------------------------------- calc（按层拆成若干 stage）
def octave_raw(i: int) -> list[tuple[str, str]]:
    """一层值噪声的原始命令（无状态门），返回 (cmd, note)。"""
    oc = N.OCTAVES[i]
    n = i + 1
    out: list[tuple[str, str]] = []

    def cg(run: str, note: str):
        out.append((e(f"as @e[tag={COL}]", run=run), f"L{n} {note}"))

    for axis in ("x", "z"):
        src = "@s px" if axis == "x" else "@s pz"
        idx = "@s ix" if axis == "x" else "@s iz"
        fr = "@s fx" if axis == "x" else "@s fz"
        fr2 = "@s fx2" if axis == "x" else "@s fz2"
        koff = oc.get("ox" if axis == "x" else "oz", 0)
        cst = f"k{'ox' if axis == 'x' else 'oz'}{n}"
        cg(f"scoreboard players operation {idx} = {src}", f"{axis} 下标源")
        if koff:
            cg(f"scoreboard players operation {idx} += {cst} nz", f"{axis} 相位+{koff}")
        cg(f"scoreboard players operation {idx} /= kd{n} nz", f"{axis} 晶格下标")
        cg(f"scoreboard players operation {fr} = {src}", f"{axis} 小数源")
        if koff:
            cg(f"scoreboard players operation {fr} += {cst} nz", f"{axis} 相位+{koff}")
        cg(f"scoreboard players operation {fr} %= kd{n} nz", f"{axis} 取余")
        cg(f"scoreboard players operation {fr} *= kl{n} nz", f"{axis} →1/256")
        cg(f"scoreboard players set {fr2} 256", f"{axis} 补数")
        cg(f"scoreboard players operation {fr2} -= {fr}", f"{axis} 补数完成")
    cg("scoreboard players operation @s base = @s ix", "base=ix")
    cg("scoreboard players operation @s base *= k127 nz", "×127")
    cg("scoreboard players operation @s u = @s iz", "u=iz")
    cg("scoreboard players operation @s u *= k311 nz", "×311")
    cg("scoreboard players operation @s base += @s u", "合并")
    cg(f"scoreboard players operation @s base += ks{n} nz", "+层种子")
    cg("scoreboard players operation @s base += fb_seed nz", "+随机种子")
    for c, (wx, wz) in enumerate([("fx2", "fz2"), ("fx", "fz2"), ("fx2", "fz"), ("fx", "fz")]):
        cg("scoreboard players operation @s hh = @s base", f"角{c} base")
        if c:
            cg(f"scoreboard players operation @s hh += ko{c} nz", f"角{c} 角偏移")
        cg("scoreboard players operation @s u = @s hh", f"角{c} u=h")
        cg("scoreboard players add @s u 1", f"角{c} u=h+1")
        cg("scoreboard players operation @s hh *= @s u", f"角{c} h(h+1)")
        cg("scoreboard players operation @s hh %= k251 nz", f"角{c} %251")
        cg(f"scoreboard players operation @s hh *= @s {wx}", f"角{c} 权重x")
        cg(f"scoreboard players operation @s hh *= @s {wz}", f"角{c} 权重z")
        if c == 0:
            cg("scoreboard players operation @s bi = @s hh", f"角{c} 初始化")
        else:
            cg("scoreboard players operation @s bi += @s hh", f"角{c} 累加")
    cg("scoreboard players operation @s bi /= k65536 nz", "归一化 0..250")
    if oc["amp"] != 1:
        cg(f"scoreboard players operation @s bi *= ka{n} nz", f"振幅×{oc['amp']}")
    cg("scoreboard players operation @s acc += @s bi", "累加 acc")
    return out


def build_map_raw() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []

    def cg(*subs, run: str, note: str):
        out.append((e(f"as @e[tag={COL}]", *subs, run=run), note))

    cg(run="scoreboard players operation @s acc -= kbias nz", note="去偏置")
    cg(run="scoreboard players operation @s acc /= kdiv nz", note=f"÷{N.DIV}")
    cg(run="scoreboard players operation @s acc += kmidraw nz", note=f"+{N.MID_RAW} 中间高度")
    cg(run="scoreboard players operation @s hgt = @s acc", note="hgt=中间高度")
    return out


def smooth_raw(pass_no: int) -> list[tuple[str, str]]:
    """一遍 3×3 邻域均值（边界按实际邻居数归一化）。"""
    out: list[tuple[str, str]] = []

    def cg(*subs, run: str, note: str):
        out.append((e(f"as @e[tag={COL}]", "at @s", *subs, run=run), note))

    # acc 在 map 之后已经空闲，这里复用它做邻域和，省一个 objective。
    cg(run="scoreboard players operation @s acc = @s hgt", note=f"第{pass_no}遍 中心值")
    cg(run="scoreboard players set @s cnt 1", note=f"第{pass_no}遍 cnt=1")
    for dx in (-2, 0, 2):
        for dz in (-2, 0, 2):
            if dx == 0 and dz == 0:
                continue
            pos = f"positioned ~{dx} ~ ~{dz}"
            cg(pos, f"if entity @e[tag={COL},r={R_COL}]",
               run=f"scoreboard players operation @s acc += @e[tag={COL},r={R_COL},c=1] hgt",
               note=f"第{pass_no}遍 邻居({dx:+d},{dz:+d}) 累加")
            cg(pos, f"if entity @e[tag={COL},r={R_COL}]",
               run="scoreboard players add @s cnt 1",
               note=f"第{pass_no}遍 邻居({dx:+d},{dz:+d}) 计数")
    cg(run="scoreboard players operation @s acc /= @s cnt", note=f"第{pass_no}遍 求平均")
    cg(run="scoreboard players operation @s hgt = @s acc", note=f"第{pass_no}遍 写回 hgt")
    return out


def build_finalize_raw() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []

    def cg(*subs, run: str, note: str):
        out.append((e(f"as @e[tag={COL}]", *subs, run=run), note))

    cg(run="scoreboard players operation @s hgt -= koffraw nz", note=f"-{N.OFF_RAW} → 2..18")
    cg("if score @s hgt matches ..1", run="scoreboard players set @s hgt 2", note="夹下界 2")
    cg("if score @s hgt matches 19..", run="scoreboard players set @s hgt 18", note="夹上界 18")
    return out


# ---------------------------------------------------------------- draw（17 档）
def build_draw(state: int) -> Chain:
    ch = Chain("draw", "repeat", 4, BASE_Y + Y["draw"])
    g = f"if score fb_cur {CTL} matches {state}"
    ch.add(f"scoreboard players operation fb_cur {CTL} = fb_state {CTL}", "状态快照")
    for h in range(N.H_MIN, N.H_MAX + 1):
        b = h - N.H_MIN
        base = f"{g} if score fb_b {CTL} matches {b} as @e[tag={COL}] if score @s hgt matches {h} at @s"
        if h >= 3:
            ch.add(e(base, run=f"fill ~-1 ~1 ~-1 ~0 ~{h-2} ~0 minecraft:stone"), f"档{b}(h{h}) 石头")
        ch.add(e(base, run=f"fill ~-1 ~{h-1} ~-1 ~0 ~{h-1} ~0 minecraft:dirt"), f"档{b}(h{h}) 土")
        top = "minecraft:snow" if h >= 14 else "minecraft:grass"
        ch.add(e(base, run=f"fill ~-1 ~{h} ~-1 ~0 ~{h} ~0 {top}"), f"档{b}(h{h}) 表层")
        ch.add(e(base, run=f"scoreboard players add bn{h} {CTL} 1"), f"档{b}(h{h}) 计数")
    ch.add(e(g, run=f"scoreboard players add fb_b {CTL} 1"), "下一档")
    ch.add(e(g, f"if score fb_b {CTL} matches {N.H_MAX - N.H_MIN + 1}..",
             run=f"scoreboard players set fb_state {CTL} 99"), "铺设完成")
    dist = ",".join('{"text":"§7%d:"},{"score":{"name":"bn%d","objective":"ctl"}}' % (h, h)
                    for h in range(N.H_MIN, N.H_MAX + 1))
    ch.add(e(g, f"if score fb_b {CTL} matches {N.H_MAX - N.H_MIN + 1}..",
             run='tellraw @a {"rawtext":[{"text":"§a地形完成 §7| 高度分布 "},%s]}' % dist), "高度分布")
    ch.add(e(g, f"if score fb_b {CTL} matches {N.H_MAX - N.H_MIN + 1}..", run="title @a title §a地形生成完成"), "标题")
    ch.add(e(g, f"if score fb_b {CTL} matches {N.H_MAX - N.H_MIN + 1}..", run="playsound random.levelup @a"), "音效")
    return ch


# ---------------------------------------------------------------- 组装
def build_spec():
    boot, prep, grid = build_boot(), build_prep(), build_grid()

    octs = [octave_raw(i) for i in range(len(N.OCTAVES))]
    octs[0] = [("execute as @e[tag=nt_col] run scoreboard players set @s acc 0", "acc=0")] + octs[0]
    base_stage = [c for st in octs for c in st] + build_map_raw()

    stages = [base_stage]
    for p in range(N.SMOOTH_PASSES):
        stages.append(smooth_raw(p + 1))
    stages.append(build_finalize_raw())

    chunks: list[list[tuple[str, str]]] = []
    for st in stages:
        for i in range(0, len(st), 80):
            chunks.append(st[i:i + 80])

    chains = [boot, prep, grid]
    for idx, chunk in enumerate(chunks):
        state = 2 + idx
        ch = Chain(f"calc{idx + 1}", "repeat", 0, BASE_Y + Y["calc1"] + idx)
        ch.add(f"scoreboard players operation fb_cur {CTL} = fb_state {CTL}", "状态快照")
        for cmd, note in chunk:
            ch.add(gate(cmd, state), note)
        ch.add(e(f"if score fb_cur {CTL} matches {state}",
                 run=f"scoreboard players set fb_state {CTL} {state + 1}"), f"stage 完成 → {state + 1}")
        chains.append(ch)

    draw_state = 2 + len(chunks)
    chains.append(build_draw(draw_state))

    blocks = []
    for ch in chains:
        pos = ch.layout()
        n = len(ch.cmds)
        for i, (x, y, z, face) in enumerate(pos):
            entry = {
                "id": f"{ch.name}{i:02d}",
                "type": ch.mode if i == 0 else "chain",
                "condition": "unconditional",
                "redstone": ch.redstone if i == 0 else "always_active",
                "delay": ch.delay if i == 0 else 0,
                "command": ch.cmds[i],
                "pos": [x, y, z],
                "facing": face,
                "next": f"{ch.name}{i+1:02d}" if i + 1 < n else None,
            }
            if ch.notes[i]:
                entry["note"] = f"{ch.name}.{i:02d} {ch.notes[i]}"
            blocks.append(entry)
    spec = {
        "name": "value-noise-terrain",
        "description": ("256 根柱子 + 32 位整数值噪声 fBm（3 层）+ 2 遍 3×3 邻域均值平滑 → 2..18 高度 "
                        "→ 32×32 地形。boot impulse 抽种子；grid 每 tick 两根柱子；calc 分 stage 并行算；"
                        "draw 每 4 tick 一档。"),
        "target_version": "1.21.130",
        "setup": ["gamerule commandblocksenabled true",
                  "导入后 setblock 0 64 0 redstone_block 触发"],
        "tests": ["导入后 15 秒内地形长出来", "chat 的高度分布与 design.md 一致",
                  "再触发一次换种子、换地形"],
        "notes": ["值噪声 + 邻域平滑；除法朝 0 截断；中间量 < 2^31"],
        "blocks": blocks,
    }
    return spec, chains, len(chunks)


def write_bdx(spec, path):
    items = [BdxBlock(b["pos"][0], b["pos"][1], b["pos"][2], b["type"], b["command"],
                      facing=b["facing"], delay=b["delay"], conditional=False,
                      needs_redstone=(b["redstone"] == "needs_redstone"),
                      custom_name=b["id"], track_output=True) for b in spec["blocks"]]
    items.append(BuildBlock(0, BASE_Y, 0, "redstone_block"))
    write_build_bdx(items, str(path))
    return len(items)


def main():
    spec, chains, nstages = build_spec()
    (HERE / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    n = write_bdx(spec, HERE / "terrain.bdx")
    cols = N.columns()
    hs = [c[2] for c in cols]
    print(f"command blocks={len(spec['blocks'])}  bdx items={n}  calc stages={nstages}")
    for ch in chains:
        pos = ch.layout()
        print(f"  {ch.name:6s} {ch.mode:8s} d{ch.delay:<2d} {len(ch.cmds):3d} 条  y={ch.y}  z1..{max(p[2] for p in pos)}")
    print("columns:", len(cols), " 高度:", min(hs), "..", max(hs),
          " 分布:", {h: hs.count(h) for h in range(N.H_MIN, N.H_MAX + 1) if hs.count(h)})


if __name__ == "__main__":
    main()
