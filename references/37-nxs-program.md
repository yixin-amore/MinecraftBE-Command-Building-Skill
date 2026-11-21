# 37 · NXS Program：空间程序，不只是光栅器

`NxsRaster` 只是 NXS 的一个后端。  
NXS 更一般的形态是：

```text
NxsProgram
→ Frame / Path / Spiral / Radial / Array / Orbit
→ Instance
→ commands / templates
```

## IR

```python
NxsFrame(origin, yaw, pitch, roll, scale)
NxsInstance(frame, material, kind, label)
NxsProgram(name, ops)
```

`NxsFrame` 提供：

```text
basis()          # right / up / forward
point(local)     # 局部 → 世界
moved(local)
rotated(dyaw, dpitch, droll)
```

## 已实现 Op

| Op | 用途 |
|---|---|
| `EmitOp` | 单点输出 |
| `SpiralOp` | 螺旋楼梯/螺旋灯带 |
| `RadialOp` | 玫瑰窗环/法阵环/柱列 |
| `PathOp` | 折线/梁/拱线/激光 |
| `OrbitOp` | 环绕轨道/弹幕/灯环 |
| `ArrayOp` | 阵列/垛口/柱网 |

## 三个非图像 demo

```bash
python3 examples/nxs-program/demo.py
```

| demo | instances | 说明 |
|---|---:|---|
| spiral-stair | 24 | 半径 4、1 圈、上升 6 |
| rose-tracery | 112 | 双环 + 8 根辐条 |
| orbiting-laser | 72 | 24 轨道点 + 2 条穿过圆心的光束 |

产物：

```text
examples/nxs-program/out/spiral.json
examples/nxs-program/out/rose.json
examples/nxs-program/out/orbit.json
examples/nxs-program/out/report.json
```

## 输出

- `commands()`：绝对坐标命令
- `templates()`：`execute positioned/rotated` 模板
- `to_dict()`：instances + commands + templates + budget

示例：

```text
particle minecraft:end_rod 5.0 20.0 0.0
```

模板：

```text
execute positioned 5 20 0 rotated 90 0 run particle minecraft:end_rod ^ ^ ^
```

## 预算

`NxsProgram.to_dict()['budget']` 给出：

```text
instances
commands
chars
```

它不替代 raster 的 80 CB 求解；Program 的预算更粗。

## 边界

- 目前是 IR + 绝对命令/模板，不是完整 `execute` 递归 lowering。
- `PathOp` 是线性采样，还没有 Bezier/arc 专用采样器。
- `OrbitOp` 是离散环绕，不是连续运动。
- 还没有 Branch/Query op；递归树/射线命中仍在 `NxsRaster` 之外。
- 建筑用法（螺旋楼梯、玫瑰窗、飞扶壁弧线）已有 demo，但还没有和 `ArchBuilder` 自动拼装。

## 和 NxsRaster 的分工

| | NxsRaster | NxsProgram |
|---|---|---|
| 输入 | Shape/CSG | Frame/Op |
| 采样 | 自适应 octree/quadtree | 显式 count/samples |
| 适合 | 图像、法阵、体素场 | 楼梯、窗棂、轨道、梁、阵列 |
| 输出 | particle/setblock/fill | particle/setblock/entity |
| 预算 | 80 CB/字符 | instances/chars |
