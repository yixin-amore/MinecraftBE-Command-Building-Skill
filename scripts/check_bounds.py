#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""指令区包围盒断言：≤64×64×100，并打印单个矩形常加载区命令。

为什么需要它：
  基岩版 `tickingarea` 必须是单个矩形才能稳定驱动指令区。指令区一旦超出
  64×64×100，或常加载区没罩住整个盒子，上层链就不 tick —— 表现就是
  "常加载覆盖不全 / 部分特效不跑"。本脚本在导出前兜底拦下这类越界。

  出自寒冰拔刀实战：旧版 B.W=128、单层展开 Z 深 ~300、常加载区只盖 Y -4~4，
  上层粒子链永远不跑；压进 64×64 + 单矩形常加载区后根治。详见
  references/19-constraints-64x64x100.md。

用法：
  python check_bounds.py 世界.mcworld
  python check_bounds.py 世界.mcworld --max-x 64 --max-z 64 --max-y 100 --name yy
  python check_bounds.py 世界.mcworld --origin 0 4 2   # 打印相对初始化块的偏移
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from mcworld_to_structure import read_world, bounds  # noqa: E402


def main():
    ap = argparse.ArgumentParser(
        description="断言指令区包围盒 ≤ max-x×max-y×max-z，并打印常加载区命令")
    ap.add_argument("world", help=".mcworld 路径（已构建世界）")
    ap.add_argument("--max-x", type=int, default=64)
    ap.add_argument("--max-z", type=int, default=64)
    ap.add_argument("--max-y", type=int, default=100)
    ap.add_argument("--name", default="yy", help="tickingarea 名字")
    ap.add_argument("--origin", nargs=3, type=int, default=None,
                    metavar=("OX", "OY", "OZ"),
                    help="常加载区相对偏移的原点（初始化块世界坐标）；"
                         "不传则打印绝对坐标的 tickingarea 命令")
    a = ap.parse_args()

    if not a.world.endswith(".mcworld"):
        sys.exit("[错误] 只支持 .mcworld（已构建世界）；spec / mcstructure 暂不支持")

    blocks, _ = read_world(a.world)
    if not blocks:
        sys.exit("[错误] 世界里没有方块（可能是纯空气或解析失败）")

    (x0, y0, z0), (sx, sy, sz) = bounds(blocks)
    x1, y1, z1 = x0 + sx - 1, y0 + sy - 1, z0 + sz - 1

    print("方块 %d 个" % len(blocks))
    print("包围盒 起点 (%d,%d,%d)  尺寸 X=%d Y=%d Z=%d" % (x0, y0, z0, sx, sy, sz))
    print("        终点 (%d,%d,%d)" % (x1, y1, z1))

    bad = []
    if sx > a.max_x:
        bad.append("X 宽 %d > %d" % (sx, a.max_x))
    if sy > a.max_y:
        bad.append("Y 高 %d > %d" % (sy, a.max_y))
    if sz > a.max_z:
        bad.append("Z 深 %d > %d" % (sz, a.max_z))

    if a.origin:
        ox, oy, oz = a.origin
        ax, bx = x0 - ox, x1 - ox
        ay, by = y0 - oy, y1 - oy
        az, bz = z0 - oz, z1 - oz
        rel = "（相对原点 %s）" % (tuple(a.origin),)
    else:
        ax, ay, az, bx, by, bz = x0, y0, z0, x1, y1, z1
        rel = "（绝对坐标）"

    print("\ntickingarea add ~%d ~%d ~%d ~%d ~%d ~%d %s%s"
          % (ax, ay, az, bx, by, bz, a.name, rel))

    if bad:
        print("\n❌ 越界：" + "；".join(bad))
        sys.exit(1)
    print("\n✓ 全在 %d×%d×%d 内" % (a.max_x, a.max_y, a.max_z))


if __name__ == "__main__":
    main()
