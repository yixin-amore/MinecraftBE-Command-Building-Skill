#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预览：32×32 地形，平滑前/后对比 + 不同种子。"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import noise as N  # noqa: E402

cmap = LinearSegmentedColormap.from_list("terrain", [
    "#1b3a5c", "#2a5a7a", "#3d7a5e", "#6ba368", "#9dbf6a",
    "#c9c05e", "#b58a4e", "#8a6a52", "#f2f2f2"])

W = N.GRID_W * 2


def to_grid(h: dict) -> np.ndarray:
    g = np.zeros((W, W), dtype=int)
    for pz in N.GRID:
        for px in N.GRID:
            g[pz - 1:pz + 1, px - 1:px + 1] = h[(px, pz)]
    return g


fig, axes = plt.subplots(1, 4, figsize=(15, 4.4), dpi=140)
raw = to_grid(N.heights(0))
raw = np.clip(raw - N.OFF_RAW, N.H_MIN, N.H_MAX)   # 平滑前也映射到 2..18 便于对比
smo = to_grid(N.smoothed(0))
for ax, data, title in (
    (axes[0], raw, "平滑前（尖刺、跳变）"),
    (axes[1], smo, "平滑后（3×3 ×2）"),
    (axes[2], to_grid(N.smoothed(530)), "换种子 530"),
    (axes[3], to_grid(N.smoothed(4242)), "换种子 4242"),
):
    im = ax.imshow(data, origin="upper", cmap=cmap, vmin=2, vmax=18)
    ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
fig.colorbar(im, ax=axes, shrink=0.75, label="高度（格）")
fig.suptitle(f"值噪声 fBm（{W}×{W}）+ 3×3 邻域平滑：尖刺被压平，山体保留", fontsize=13)
fig.savefig(HERE / "preview.png", bbox_inches="tight")

# 相邻高差统计
raw_d = np.abs(np.diff(raw[::2, ::2], axis=1)).mean()
smo_d = np.abs(np.diff(smo[::2, ::2], axis=1)).mean()
print(f"wrote preview.png  相邻高差 平均: 平滑前 {raw_d:.2f} → 平滑后 {smo_d:.2f} 格")
print("高度分布(平滑后):", {h: int((smo == h).sum() // 4) for h in range(2, 19) if (smo == h).sum()})
