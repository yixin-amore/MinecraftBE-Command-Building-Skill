#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""埃菲尔铁塔 · 631 / 黄金比例版。

设计不是“把铁塔堆出来”，而是先定 3 个体块关系：
  60% 基座（四腿 + 拱 + 第一平台）
  30% 塔身（收分格构 + 第二平台）
  10% 塔冠（观景舱 + 尖顶 + 天线/旗）
再定视觉焦点：塔冠最亮/最密，基座大拱作为入口的第二焦点；
四腿、拱、格构、中轴、尖顶共同把视线拉向塔冠。
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SKILL = ROOT / "scripts"
if not (SKILL / "bdxgen.py").exists():
    SKILL = ROOT / ".dsh/skills/mcbe-command-blocks/scripts"
sys.path.insert(0, str(SKILL))
from bdxgen import BuildBlock, write_build_bdx  # noqa: E402

CX = CZ = 0
SITE = 44
BASE_HALF = 32
H = 192
Y1 = 73          # 0.382 * 192，黄金分割
Y2 = 119         # 0.618 * 192
Y3 = 173         # 90% 高度，塔冠起点

MAIN = "deepslate_tiles"
FRAME = "polished_deepslate"
BARS = "iron_bars"
PLAT = "polished_blackstone"
ACC = "chiseled_deepslate"
GOLD = "gold_block"
GLOW = "sea_lantern"
GLASS = "glass"
STONE = "smooth_stone"
GRASS = "grass_block"
LEAVES = "oak_leaves"
LOG = "oak_log"
WATER = "water"
RED = "redstone_lamp"
BLUE = "blue_wool"
WHITE = "white_wool"
REDW = "red_wool"

V: dict[tuple[int, int, int], str] = {}


def put(x, y, z, b):
    V[(int(x), int(y), int(z))] = b


def box(x0, x1, y0, y1, z0, z1, b):
    x0, x1 = sorted((int(x0), int(x1)))
    y0, y1 = sorted((int(y0), int(y1)))
    z0, z1 = sorted((int(z0), int(z1)))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                put(x, y, z, b)


def ring(x0, x1, y0, y1, z0, z1, b, t=1):
    x0, x1 = sorted((int(x0), int(x1)))
    z0, z1 = sorted((int(z0), int(z1)))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if min(x - x0, x1 - x, z - z0, z1 - z) < t:
                for y in range(int(y0), int(y1) + 1):
                    put(x, y, z, b)


def diag3(a, b, steps, block):
    for k in range(steps + 1):
        t = k / steps
        put(round(a[0] + (b[0] - a[0]) * t),
            round(a[1] + (b[1] - a[1]) * t),
            round(a[2] + (b[2] - a[2]) * t), block)


# ---------------------------------------------------------------- 场地
# 60/30/10 色重：60% 深色石/铁，30% 黑石/栏杆，10% 金/灯/玻璃
box(-SITE, SITE, 0, 0, -SITE, SITE, MAIN)
box(-36, 36, 0, 0, -36, 36, STONE)
box(-32, 32, 0, 0, -32, 32, PLAT)
# 中轴：从南入口到塔心
box(-2, 2, 0, 0, -42, 42, ACC)
box(-42, 42, 0, 0, -2, 2, ACC)
for i in range(-40, 41, 8):
    put(0, 0, i, GOLD)
    put(i, 0, 0, GOLD)
# 四角花园
for sx in (-1, 1):
    for sz in (-1, 1):
        x0, x1 = sx * 42, sx * 34
        z0, z1 = sz * 42, sz * 34
        box(x0, x1, 1, 1, z0, z1, GRASS)
        # 树
        tx, tz = sx * 38, sz * 38
        for y in range(2, 6):
            put(tx, y, tz, LOG)
        box(tx - 2, tx + 2, 6, 6, tz - 2, tz + 2, LEAVES)
        box(tx - 1, tx + 1, 7, 8, tz - 1, tz + 1, LEAVES)
# 南入口喷泉（中轴端景，第二视觉焦点）
for x in range(-7, 8):
    for z in range(31, 45):
        d2 = x * x + (z - 38) ** 2
        if d2 <= 36:
            put(x, 0, z, WATER)
            if d2 >= 26:
                put(x, 1, z, FRAME)
put(0, 2, 38, GLOW)
for dx, dz in ((-6, 0), (6, 0), (0, -6), (0, 6)):
    put(dx, 1, 38 + dz, GOLD)
# 入口门柱
for sx in (-1, 1):
    box(sx * 6, sx * 6, 1, 5, 42, 42, FRAME)
    put(sx * 6, 6, 42, GLOW)
# 路灯 / 长椅
for z in (-28, -16, 16, 28):
    for sx in (-1, 1):
        x = sx * 5
        for y in range(1, 4):
            put(x, y, z, BARS)
        put(x, 4, z, GLOW)
for sx in (-1, 1):
    box(sx * 32, sx * 34, 1, 1, -28, -24, FRAME)
    box(sx * 32, sx * 34, 1, 1, 24, 28, FRAME)
# 场地边缘矮栏
for x in range(-SITE, SITE + 1, 4):
    put(x, 1, -SITE, BARS)
for z in range(-SITE, SITE + 1, 4):
    put(-SITE, 1, z, BARS)

# ---------------------------------------------------------------- 基座（60%）
# 四条腿的方形柱础：最重、最实，压住重心
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * 26, sz * 26
        box(cx - 4, cx + 4, 1, 4, cz - 4, cz + 4, FRAME)
        box(cx - 3, cx + 3, 5, 5, cz - 3, cz + 3, ACC)

# 四条向内收的格构腿（1..73）
for y in range(1, Y1 + 1):
    t = (y - 1) / (Y1 - 1)
    d_raw = 8 + 18 * (1 - t) ** 1.25
    d = round(d_raw / 2) * 2   # 2 格一档，避免每层一格的锯齿
    half = 3 if y <= 16 else 2
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = round(sx * d), round(sz * d)
            # 四角主柱
            for ax in (-half, half):
                for az in (-half, half):
                    put(cx + ax, y, cz + az, FRAME)
            # 底部 12 格全实，13–22 壳实：形成“重腿”，这是 60% 基座的视觉重量
            if y <= 12:
                box(cx - half, cx + half, y, y, cz - half, cz + half, MAIN)
            elif y <= 22:
                for i in range(-half, half + 1):
                    put(cx + i, y, cz - half, MAIN)
                    put(cx + i, y, cz + half, MAIN)
                    put(cx - half, y, cz + i, MAIN)
                    put(cx + half, y, cz + i, MAIN)
            # 每 3 格一道水平箍
            if y % 3 == 0:
                for i in range(-half, half + 1):
                    put(cx + i, y, cz - half, BARS)
                    put(cx + i, y, cz + half, BARS)
                    put(cx - half, y, cz + i, BARS)
                    put(cx + half, y, cz + i, BARS)
            # 每 8 格一道 X 斜撑
            if y % 8 == 0 and y + 8 <= Y1:
                for k in range(9):
                    put(cx - half + round(2 * half * k / 8), y + k, cz - half, BARS)
                    put(cx + half - round(2 * half * k / 8), y + k, cz - half, BARS)
                    put(cx - half + round(2 * half * k / 8), y + k, cz + half, BARS)
                    put(cx + half - round(2 * half * k / 8), y + k, cz + half, BARS)

# 四面大拱：入口/框景，第二视觉焦点
def arch_side(axis: str, sign: int):
    span = 18
    height = 29
    base_y = 8
    for i in range(-span, span + 1):
        h = round(height * math.sqrt(max(0.0, 1 - (i / span) ** 2)))
        for off in (0, 1):
            y = base_y + h
            if axis == "x":
                put(i, y, sign * 24 + off, MAIN)
                put(i, y + 1, sign * 24 + off, FRAME)
            else:
                put(sign * 24 + off, y, i, MAIN)
                put(sign * 24 + off, y + 1, i, FRAME)
    # 拱心石 + 灯
    if axis == "x":
        box(0, 0, base_y + height, base_y + height + 2, sign * 24, sign * 24 + 1, GOLD)
        put(0, base_y + height + 1, sign * 24 + 2, GLOW)
    else:
        box(sign * 24, sign * 24 + 1, base_y + height, base_y + height + 2, 0, 0, GOLD)
        put(sign * 24 + 2, base_y + height + 1, 0, GLOW)


for sz in (-1, 1):
    arch_side("x", sz)
for sx in (-1, 1):
    arch_side("z", sx)

# 拱脚小柱
for sx in (-1, 1):
    for sz in (-1, 1):
        box(sx * 17, sx * 19, 1, 7, sz * 23, sz * 25, FRAME)
        put(sx * 18, 8, sz * 24, GOLD)

# ---------------------------------------------------------------- 第一平台（黄金 0.382）
# 平台下弦/斜撑
ring(-20, 20, 70, 72, -20, 20, BARS, t=1)
for sx in (-1, 1):
    for sz in (-1, 1):
        diag3((sx * 20, 70, sz * 20), (0, 73, 0), 35, BARS)
box(-20, 20, 73, 73, -20, 20, PLAT)
ring(-20, 20, 74, 76, -20, 20, BARS, t=1)
ring(-20, 20, 76, 76, -20, 20, FRAME, t=1)
# 边缘灯带（节奏，不是铺满）
for i in range(-20, 21, 5):
    put(i, 76, -20, GLOW)
    put(i, 76, 20, GLOW)
    put(-20, 76, i, GLOW)
    put(20, 76, i, GLOW)
# 四个观景小亭（不压住塔身）
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = sx * 16, sz * 16
        box(cx - 2, cx + 2, 74, 76, cz - 2, cz + 2, GLASS)
        for ax in (-2, 2):
            for az in (-2, 2):
                put(cx + ax, 76, cz + az, FRAME)
        box(cx - 3, cx + 3, 77, 77, cz - 3, cz + 3, FRAME)
        box(cx - 2, cx + 2, 78, 78, cz - 2, cz + 2, GOLD)
        put(cx, 76, cz, GLOW)

# ---------------------------------------------------------------- 塔身（30%）
for y in range(Y1 + 1, Y3):
    t = (y - (Y1 + 1)) / (Y3 - Y1 - 1)
    w = max(3, round(16 * (1 - t) ** 0.85 + 2))
    # 四角主柱
    for sx in (-1, 1):
        for sz in (-1, 1):
            put(sx * w, y, sz * w, FRAME)
    # 每 4 格一道箍
    if y % 4 == 0:
        ring(-w, w, y, y, -w, w, BARS, t=1)
    # 每 12 格一道深色结构带
    if y % 12 == 0:
        ring(-w, w, y, y, -w, w, FRAME, t=1)
    # 每 8 格 X 斜撑（四个面）
    if y % 8 == 0 and y + 8 < Y3:
        w2 = max(3, round(16 * (1 - ((y + 8) - (Y1 + 1)) / (Y3 - Y1 - 1)) ** 0.85 + 2))
        diag3((-w, y, -w), (w2, y + 8, -w), 12, BARS)
        diag3((w, y, -w), (-w2, y + 8, -w), 12, BARS)
        diag3((-w, y, w), (w2, y + 8, w), 12, BARS)
        diag3((w, y, w), (-w2, y + 8, w), 12, BARS)
        diag3((-w, y, -w), (-w, y + 8, w2), 12, BARS)
        diag3((-w, y, w), (-w, y + 8, -w2), 12, BARS)
        diag3((w, y, -w), (w, y + 8, w2), 12, BARS)
        diag3((w, y, w), (w, y + 8, -w2), 12, BARS)

# 第二平台（黄金 0.618）；略外挑，形成可读的水平带
box(-14, 14, Y2, Y2, -14, 14, PLAT)
ring(-14, 14, Y2 + 1, Y2 + 3, -14, 14, BARS, t=1)
ring(-14, 14, Y2 + 3, Y2 + 3, -14, 14, FRAME, t=1)
for i in range(-14, 15, 7):
    put(i, Y2 + 3, -14, GLOW)
    put(i, Y2 + 3, 14, GLOW)
    put(-14, Y2 + 3, i, GLOW)
    put(14, Y2 + 3, i, GLOW)

# ---------------------------------------------------------------- 塔冠（10%）
box(-7, 7, Y3, Y3, -7, 7, PLAT)
ring(-7, 7, Y3 + 1, Y3 + 4, -7, 7, GLASS, t=1)
ring(-7, 7, Y3 + 4, Y3 + 4, -7, 7, FRAME, t=1)
# 塔冠金环：把视线最终焊在顶部
ring(-7, 7, Y3 + 5, Y3 + 5, -7, 7, GOLD, t=1)
# 四个金色角饰 / 观景台栏杆
for sx in (-1, 1):
    for sz in (-1, 1):
        put(sx * 7, Y3 + 5, sz * 7, GOLD)
        box(sx * 7, sx * 7, Y3 + 1, Y3 + 4, sz * 7, sz * 7, FRAME)
# 顶部金冠
box(-4, 4, Y3 + 5, Y3 + 5, -4, 4, GOLD)
box(-3, 3, Y3 + 6, Y3 + 6, -3, 3, FRAME)
box(-2, 2, Y3 + 7, Y3 + 7, -2, 2, GOLD)
# 尖顶（收成 1×1）
for y in range(Y3 + 8, 189):
    t = (y - (Y3 + 8)) / (188 - (Y3 + 8))
    w = max(0, round(4 * (1 - t) ** 0.9))
    if w == 0:
        put(0, y, 0, GOLD if y > 181 else FRAME)
    else:
        ring(-w, w, y, y, -w, w, MAIN if not y % 2 else FRAME, t=1)
        for sx in (-1, 1):
            for sz in (-1, 1):
                put(sx * w, y, sz * w, GOLD if y > 181 else FRAME)
# 天线
for y in range(189, 193):
    put(0, y, 0, GOLD)
    if y in (190, 192):
        for d in range(-1, 2):
            put(d, y, 0, FRAME)
            put(0, y, d, FRAME)
put(0, 193, 0, GLOW)
put(0, 194, 0, GLOW)
# 法国旗（三色）
for y in range(194, 200):
    put(0, y, 0, BARS)
for x, b in ((-1, BLUE), (0, WHITE), (1, REDW)):
    for y in range(196, 199):
        put(x, y, 0, b)

# 基座/平台的重点灯（把视线从拱引到塔冠）
for y in (8, 20, 38, 54, 73, 119, 173):
    for sx in (-1, 1):
        for sz in (-1, 1):
            put(sx * 7 if y in (73, 119, 173) else sx * 1, y, sz * 7, GLOW)
# 大拱前的轴线端景
for x in (-2, 0, 2):
    for z in (-2, 0, 2):
        put(x, 1, z, GLOW)

# ---------------------------------------------------------------- 输出
voxels = len(V)
counts = Counter(V.values())
print("voxels", voxels)
print("palette", counts.most_common())

# 压缩成 fills（只做参考/批量 fill 用）
rows: dict[tuple[str, int, int], list[int]] = {}
for (x, y, z), b in V.items():
    rows.setdefault((b, y, z), []).append(x)
segs: dict[tuple[str, int, int, int], list[int]] = {}
for (b, y, z), xs in rows.items():
    xs.sort()
    start = prev = xs[0]
    spans = []
    for x in xs[1:]:
        if x <= prev + 1:
            prev = x
        else:
            spans.append((start, prev))
            start = prev = x
    spans.append((start, prev))
    for x0, x1 in spans:
        segs.setdefault((b, y, x0, x1), []).append(z)
fills = []
for (b, y, x0, x1), zs in segs.items():
    zs.sort()
    start = prev = zs[0]
    spans = []
    for z in zs[1:]:
        if z <= prev + 1:
            prev = z
        else:
            spans.append((start, prev))
            start = prev = z
    spans.append((start, prev))
    for z0, z1 in spans:
        fills.append({"from": [x0, y, z0], "to": [x1, y, z1], "block": b})
(HERE / "fills.json").write_text(json.dumps(fills, ensure_ascii=False), encoding="utf-8")
(HERE / "plan.json").write_text(json.dumps({
    "name": "eiffel-631",
    "voxels": voxels,
    "fills": len(fills),
    "height": H,
    "base": BASE_HALF * 2,
    "golden": {"y1": Y1, "y2": Y2, "y3": Y3,
               "ratio_1": round(Y1 / H, 4), "ratio_2": round(Y2 / H, 4)},
    "palette": dict(counts),
}, ensure_ascii=False, indent=2), encoding="utf-8")

# BDX：本地坐标 0..88，StartPos 256 0 256
items = [BuildBlock(x + SITE, y, z + SITE, b) for (x, y, z), b in V.items()]
write_build_bdx(items, str(HERE / "eiffel-631.bdx"))
print("bdx blocks", len(items), "fills", len(fills))
print("height", H, "base", BASE_HALF * 2)
