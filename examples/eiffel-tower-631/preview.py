#!/usr/bin/env python3
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_eiffel as G

COL = {
    "deepslate_tiles": "#454550", "polished_deepslate": "#33333a",
    "iron_bars": "#aab0b8", "polished_blackstone": "#1b1a20",
    "chiseled_deepslate": "#5a5a64", "gold_block": "#e7bd45",
    "sea_lantern": "#a8f0d0", "glass": "#a9d7e6", "smooth_stone": "#a9a9a2",
    "grass_block": "#5d8a4b", "oak_leaves": "#3e7441", "oak_log": "#6b5134",
    "water": "#3f78c8", "redstone_lamp": "#d85445",
    "blue_wool": "#3558b8", "white_wool": "#e8e8e2", "red_wool": "#b83c46",
}
pts = list(G.V.items())

def render(a, b, depth, title, ax):
    pr = []
    for (x, y, z), blk in pts:
        pr.append((a(x, y, z), b(x, y, z), depth(x, y, z), blk))
    lo_a = min(p[0] for p in pr); hi_a = max(p[0] for p in pr)
    lo_b = min(p[1] for p in pr); hi_b = max(p[1] for p in pr)
    img = np.zeros((hi_b-lo_b+1, hi_a-lo_a+1, 3))
    dep = np.full((hi_b-lo_b+1, hi_a-lo_a+1), -1e9)
    for u, v, d, blk in pr:
        if d >= dep[hi_b-v, u-lo_a]:
            dep[hi_b-v, u-lo_a] = d
            img[hi_b-v, u-lo_a] = matplotlib.colors.to_rgb(COL.get(blk, "#ff00ff"))
    ax.imshow(img, interpolation="nearest")
    ax.set_title(title, fontsize=11)
    ax.set_xticks([]); ax.set_yticks([])

fig, axes = plt.subplots(1, 3, figsize=(12, 8), dpi=130,
                         gridspec_kw={"width_ratios": [1, 1, 1.25]})
render(lambda x,y,z:x, lambda x,y,z:y, lambda x,y,z:z, "正立面 · 631 / 黄金分割", axes[0])
render(lambda x,y,z:z, lambda x,y,z:y, lambda x,y,z:x, "侧立面", axes[1])
render(lambda x,y,z:x, lambda x,y,z:z, lambda x,y,z:y, "总平面 · 中轴/双拱/塔冠", axes[2])
fig.suptitle("埃菲尔铁塔 · 64×64×192（中心 300,300）", fontsize=13)
fig.tight_layout()
fig.savefig(HERE / "preview.png", bbox_inches="tight")
print("wrote preview.png")
