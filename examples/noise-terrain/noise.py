#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""值噪声（value noise）整数模型 + 邻域平滑 —— 与 gen.py 的命令逐位一致。

新增（照 skill 的 gaussian-filter.md 思路，但用计分板而不是实体采样）：
  3×3 邻域加权平均（边界按"实际有几个邻居"归一化），跑两遍 ≈ 高斯。
"""
from __future__ import annotations

# ---------------------------------------------------------------- 可调参数
GRID_W = 16         # 每边 16 根柱子 → 32×32 格地形
OCTAVES = [
    dict(L=8, seed=11, amp=2, ox=2, oz=1),
    dict(L=4, seed=47, amp=2, ox=0, oz=0),
    dict(L=2, seed=83, amp=1, ox=0, oz=0),
]

K127, K311 = 127, 311
K251 = 251
K256 = 256
K65536 = 65536
OFFSETS = [0, 127, 311, 438]
BIAS = 125 * sum(o["amp"] for o in OCTAVES)   # 625
DIV = 30            # 高度缩放（越大越平）
MID_RAW = 38        # 模糊前的中间高度（保证正数、且不提前夹断）
OFF_RAW = 28        # 模糊后 -28 → 2..18
H_MIN, H_MAX = 2, 18
SALT_MAX = 20000
SMOOTH_PASSES = 2   # 3×3 均值跑几遍


def tdiv(a: int, b: int) -> int:
    """基岩版 /=：朝 0 截断。"""
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def tmod(a: int, b: int) -> int:
    return a - tdiv(a, b) * b


def wrap32(v: int) -> int:
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


def hash_value(ix: int, iz: int, seed: int, corner: int, salt: int = 0) -> int:
    a = wrap32(ix * K127 + iz * K311 + seed + salt + OFFSETS[corner])
    return tmod(wrap32(a * (a + 1)), K251)


def bilinear(px: int, pz: int, L: int, seed: int, ox: int = 0, oz: int = 0, salt: int = 0) -> int:
    rx, rz = px + ox, pz + oz
    kL = K256 // L
    ix, fx = tdiv(rx, L), tmod(rx, L) * kL
    iz, fz = tdiv(rz, L), tmod(rz, L) * kL
    fx2, fz2 = K256 - fx, K256 - fz
    v00 = hash_value(ix, iz, seed, 0, salt)
    v10 = hash_value(ix, iz, seed, 1, salt)
    v01 = hash_value(ix, iz, seed, 2, salt)
    v11 = hash_value(ix, iz, seed, 3, salt)
    num = v00 * fx2 * fz2 + v10 * fx * fz2 + v01 * fx2 * fz + v11 * fx * fz
    return tdiv(num, K65536)


def raw_height(px: int, pz: int, salt: int = 0) -> int:
    """模糊前的中间高度（不夹断，约 19..57）。"""
    acc = 0
    for oc in OCTAVES:
        acc += bilinear(px, pz, oc["L"], oc["seed"], oc["ox"], oc["oz"], salt) * oc["amp"]
    return MID_RAW + tdiv(acc - BIAS, DIV)


GRID = [2 * i + 1 for i in range(GRID_W)]      # 1,3,..,31


def heights(salt: int = 0) -> dict:
    """(px,pz) -> 未平滑的中间高度"""
    return {(px, pz): raw_height(px, pz, salt) for pz in GRID for px in GRID}


def blur_once(h: dict) -> dict:
    """3×3 均值，边界按实际邻居数归一化（与命令里的 cnt 一致）。"""
    out = {}
    for (px, pz), _ in h.items():
        s = c = 0
        for dx in (-2, 0, 2):          # 柱子间距 2 格
            for dz in (-2, 0, 2):
                v = h.get((px + dx, pz + dz))
                if v is not None:
                    s += v
                    c += 1
        out[(px, pz)] = tdiv(s, c)
    return out


def smoothed(salt: int = 0, passes: int = SMOOTH_PASSES) -> dict:
    """平滑后 → 最终高度 2..18"""
    h = heights(salt)
    for _ in range(passes):
        h = blur_once(h)
    return {k: max(H_MIN, min(H_MAX, v - OFF_RAW)) for k, v in h.items()}


def columns(salt: int = 0):
    """(px, pz, 平滑后高度)，行优先。"""
    h = smoothed(salt)
    return [(px, pz, h[(px, pz)]) for pz in GRID for px in GRID]


if __name__ == "__main__":
    import statistics
    for salt in (0, 530):
        raw = list(heights(salt).values())
        sm = list(smoothed(salt).values())
        diffs = []
        r = heights(salt)
        s = smoothed(salt)
        for pz in GRID:
            for px in GRID[:-1]:
                diffs.append(abs(s[(px, pz)] - s[(px + 2, pz)]))
                diffs.append(abs(r[(px, pz)] - r[(px + 2, pz)]))
        n = len(diffs) // 2
        print(f"salt={salt}: 高度 {min(raw)}..{max(raw)} → 平滑后 {min(sm)}..{max(sm)}")
        print(f"  相邻高差 平均 {statistics.mean(diffs[1::2]):.2f} → {statistics.mean(diffs[0::2]):.2f}")
