# 36 · NXS 编译器：点阵 + CSG + 预算 + 回读

## 链路

```text
NxsRaster
→ 自适应点阵
→ Shape 求值
→ 命令生成
→ Budget
→ JSON 回读
```

## 入口

```bash
python3 scripts/nxs_compile.py \
  --shape ring --size 16 --levels 3 \
  --emit particle \
  --out examples/nxs-compiler/ring.json

python3 scripts/nxs_read.py examples/nxs-compiler/ring.json
```

## Shape

已实现：

```text
Sphere / Box / Cylinder / Cone / Capsule / Torus
Plane / PolygonPrism / ExtrudedCurve / Sweep(alias)
Union / Intersect / Subtract
Transform / Mirror / Array / Repeat
```

`Shape.contains(point)` 是唯一求值接口；DSL 不直接拼命令。

## 自适应点阵

`NxsRaster.sample()`：

- 以 `shape.bounds()` 为根；
- 2D 采样四角、边中点、中心；
- 3D 采样 8 角、6 面心、12 边中点、中心；
- 全部在内部 → 合并为大 cell；
- 全在外部 → 跳过；
- 边界 → 递归细分到 `levels`；
- `max_cells` 防爆。

薄圆环/十字这类形状需要边中点探测，否则根节点会全部漏掉。

## 命令

```text
particle <material> <x> <y> <z>
setblock <x> <y> <z> <block>
fill <x0> <y0> <z0> <x1> <y1> <z1> <block>
```

当前是**绝对坐标命令表**，不是单条 NXS 模板。  
这样可以先验证几何、预算、回读，再把同一 cell 表降成 `execute` 链。

## if / unless

`if_unless_clauses()` 对简单形状生成选择器 clauses：

```json
{"if":["x=-2","dx=4","y=-0.25","dy=0.5","z=-2","dz=4"],"unless":[]}
```

`Subtract` 会变成 `if A` + `unless B`。  
复杂 `Union`、任意 CSG 仍返回 `None`，不假装一条选择器能表达所有并集。

## 预算

```text
points      cell 数
commands    命令数
chars       字符数
cb          按绝对命令估的命令方块数
ticks       cells / 20
max_chars   32,500
max_cb      80
issues      > 上限则拒绝
```

`cb` 是**当前绝对命令模式**的估计，不是“每材料 1 CB”的压缩值；  
压缩调度仍需要单独的 scheduler。

示例：

```text
ring 16×16, levels=3
points   36
commands 36
chars    2,124
cb       36
ticks    2
ok       true
```

## 回读

`nxs_read.py` 检查：

```text
commands 数 = points 数
particle/setblock/fill 可解析
materials / kinds
budget.issues
```

## 当前边界

- 尚未把 cell 表降成**单条 NXS execute 模板**；
- 尚未实现“1 材料 1 CB + 共享 cell 计数器”的调度；
- 自适应只在根 bounds 内；超薄/极细形状可能需要提高 levels；
- `Union` 的 `if/unless` 选择器尚未完整编译；
- `fill` 模式按 cell 输出，不是 greedy 合并。

## 下一步

1. `cell table → NXS execute 模板`；
2. `1 材料 1 CB + cell 调度`；
3. 预算求解器：给定 80 CB 反推 levels/采样；
4. PNG/SVG → Shape 导入；
5. 2D circle / 3D cube / creeper 三个 benchmark。
