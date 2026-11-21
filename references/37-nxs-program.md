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
| `BezierOp` | 三次/二次 Bezier 曲线 |
| `ArcOp` | 平面圆弧/拱线 |
| `RayOp` | 射线采样/激光 |
| `BranchOp` | 递归分叉树 |
| `QueryOp` | 体积命中过滤 |

## 三个非图像 demo

```bash
python3 examples/nxs-program/demo.py
```

| demo | instances | 说明 |
|---|---:|---|
| spiral-stair | 24 | 半径 4、1 圈、上升 6 |
| rose-tracery | 112 | 双环 + 8 根辐条 |
| orbiting-laser | 72 | 24 轨道点 + 2 条穿过圆心的光束 |
| branch-tree | 7 | 深度 3、二分支递归树 |
| curve-query | 53 | 半圆弧 + Bezier + 射线 + 体积过滤 |

产物：

```text
examples/nxs-program/out/spiral.json
examples/nxs-program/out/rose.json
examples/nxs-program/out/orbit.json
examples/nxs-program/out/branch.json
examples/nxs-program/out/curve.json
examples/nxs-program/out/report.json
```

## 输出

- `commands()`：默认相对坐标
- `absolute_commands()`：显式绝对坐标
- `templates()`：`execute positioned/rotated` 模板
- `relative_commands()`：相对坐标源
- `lower_tree()`：Branch 的递归树 + 其他 op 的展开子节点
- `timeline()`：按 `tick` 分组，给 Orbit 等运动用
- `to_dict()`：instances + commands + templates + relative + tree + timeline + budget

示例：

```mcfunction
execute positioned ~5 ~20 ~0 rotated 90 0 run particle minecraft:end_rod ^ ^ ^
```

绝对模式显式调用：

```python
program.absolute_commands()
```

## 递归 execute lowering

`relative_commands()` 输出：

```mcfunction
execute positioned ~4 ~2 ~0 rotated 90 0 run particle ... ^ ^ ^
```

`BranchOp.tree()` / `lower_tree()` 保留：

```text
root frame
→ emit
→ child frame
   → emit
   → child frame ...
```

这不是把整棵树压成一条命令；每个执行体仍然一个 `run`，但坐标架层级是递归的。

## ArchBuilder 拼装

```python
from nxs_arch import apply_program
apply_program(program, builder)
```

`examples/nxs-program/arch_demo.py` 把螺旋楼梯写进 ArchBuilder：

```text
NXS spiral 40 点
→ ArchBuilder 体素
→ BDX
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

- `relative_commands()` 是嵌套 execute，但每个实例仍是一个执行体。
- `lower_tree()` 已经是递归结构，但还没有自动降成多个 CB/函数调度。
- `QueryOp` / `RayOp` 用 Python 几何求值；还没有转成 `execute if entity` 的真机查询链。
- `OrbitOp.tick_step` 只生成 tick 元数据，没有自动 loop/调度器。
- `ArchBuilder` 拼装是单向写入；还没有把 ArchBuilder 反编译成 NxsProgram。
- Bezier/Arc 是采样器，不是解析曲线；预算仍按采样点算。

## 和 NxsRaster 的分工

| | NxsRaster | NxsProgram |
|---|---|---|
| 输入 | Shape/CSG | Frame/Op |
| 采样 | 自适应 octree/quadtree | 显式 count/samples |
| 适合 | 图像、法阵、体素场 | 楼梯、窗棂、轨道、梁、阵列 |
| 输出 | particle/setblock/fill | particle/setblock/entity |
| 预算 | 80 CB/字符 | instances/chars |
