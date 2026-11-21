# 23 · NXS：递归坐标架 / 点阵光栅（NxsRaster）

> 作者：NeilGreentot。样本：`binaryTree2D.txt` / `binaryTree3D.txt`。
> **NXS 不是 FMBE**：FMBE 是实体部件模型；NXS 是**用 execute 的坐标架/旋转递归画几何**。

## 1. 它到底在做什么

核心不是“粒子命令”，而是**变换栈**：

```text
rotate -> move -> face -> rotate -> move -> emit
```

用的是 execute 子命令：

```text
rotated as @e[name=tree]   # 从锚点实体取一个坐标架
rotated ~ 45               # 在局部 yaw 上叠 45°
positioned ^^^1024         # 沿局部前方走 1024（把方向变成射线）
facing 0 0 0               # 重置到世界朝向
positioned ^^^2048         # 再走，形成镜像/另一侧
rotated ~180 45            # 反向
run particle ...
```

`@e[name=tree]` 是**坐标架寄存器**，通常是一只船/盔甲架；`rot0/rot1` 是初始朝向。
每多一层 `rotated~ angle`，角度减半：45 → 22.5 → 11.25 → 5.625 → 2.8125 → 1.40625。

所以 `binaryTree` 不是“画一棵树”，是**递归二分出 2D/3D 几何的坐标架**。

## 2. 样本目录

### 2D

| 形状 | 关键操作 |
|---|---|
| 圆(64) | 45° 起步，逐层减半，`facing` 重置后镜像 |
| 圆(精简版) | 去掉冗余层，保留 11.25→1.40625 |
| 同心圆 | 先 `positioned^^^4/.25/.125` 做半径，再画 |
| 椭圆 | 先沿一个轴 `positioned^^^2`，再画圆 |
| 八角星 | 先 `1.875` 反向对称，再二分 |
| 双八边形 | 两个 `4.5266` 反向点，再做 22.5/11.25/5.625 |
| 12 角星 | 30/15/7.5，三角形×4 |
| 跟随盔甲架 | `as@e[type=armor_stand] at@s` 把锚点换到盔甲架 |
| 球面投影 | `as@e[name=tree] rotated as@s` 交叉坐标架 |

### 3D

| 形状 | 关键操作 |
|---|---|
| 正方体 | `rotated 0~`/`180~` + `positioned^^^.5/4/2/1` |
| 正方体框架(3对称) | yaw 22.5 + pitch 55/30 |
| 正方体框架(2对称) | yaw 67.5 + pitch -37.5 |
| 同心正方体 | 先半径 2.6516/1/.5/.25/.125 |
| 正四面体 | pitch 35.264/72.3678 + yaw 30/60 |
| 同心正四面体 | 先半径，再四面体角 |
| 双正四面体 | 两套相反朝向的坐标架 |
| 跟随玩家 | `positioned as@p` + `facing entity@p feet` |

## 3. DSL / 编译器应该怎么建模

```python
NxsShape(
  anchor="tree",             # 坐标架实体
  plane="2d"|"3d",
  kind="circle"|"cube"|"tetra"|...,
  center=(x,y,z),
  radius=...,
  steps=[45,22.5,11.25,...],
  mirror=True,
  particle="minecraft:balloon_gas_particle",
  follow=None|"armor_stand"|"player",
)
```

编译期校验：

- `anchor` 实体存在且唯一
- `rot0/rot1` 初始朝向已设置
- 每层角度合法、不出现 0 次递归
- `positioned` 的 `^`/`~` 与 `facing` 顺序正确
- `particle` 名称走命令白名单
- 最终命令用 `command_syntax.py` / lint 过语法

**不在 DSL 里手写 1024/2048 魔法数**：它们是“把方向变成射线”的哨兵值，应该封装成 `NxsOp.ray(times)`。

## 4. 与 FMBE 的关系

| | NXS | FMBE |
|---|---|---|
| 本质 | execute 坐标架递归 | 实体部件 + playanimation |
| 产物 | 粒子/几何线框 | 模型/骨骼动画 |
| 锚点 | `tree` 船/盔甲架 | carrier 僵尸/狐狸 |
| 用途 | 法阵、符文、轨道、3D 线框 | Boss、武器、展示体 |

两者可以叠加：NXS 画法阵/轨道，FMBE 放主体。

## 5. 广义 NXS：点阵 + CSG 掩码

NXS 不只画圆/树。它的通用形式是：

```text
坐标架 → dyadic 点阵 → 选择器掩码 → 终端输出
```

### 5.1 dyadic 点阵

参考命令反复做：

```text
positioned ^^^1
positioned ^^^0.5
positioned ^^^0.25
positioned ^^^0.125
```

这是沿局部轴的**二分采样**。每轴 4 个采样点：

```text
1, 1/2, 1/4, 1/8
```

- 2D（forward × right）：`4 × 4 = 16` 点
- 3D（forward × right × up）：`4 × 4 × 4 = 64` 点
- 层数越多，分辨率越高；但点阵、掩码和命令长度都会增长

`rotated as @e[name=nx]` 只是取坐标架；把 `nx` 换成船/盔甲架/玩家，几何不变。

### 5.2 `if` / `unless` 是点集运算

```text
if entity @s[...]      → 保留落在该体积内的点（交集）
unless entity @s[...]  → 扣掉落在该体积内的点（差集）
```

多个 `unless` 连用 = 减去多个区域的并集。

所以苦力怕脸、圆、正方形、十字、圆环都可以由同一套点阵 + 不同掩码得到。

`@s` 在这里是**探针**：`positioned` 把命令源移到点阵格点，选择器的 `x/y/z/dx/dy/dz/r/rm` 相对命令源；`y=~-4.52` 是在补偿“眼睛 → 脚”的高度差。因此它判断的是“当前格点是否落在目标体积内”，不是“玩家在不在”。

选择器能表达的是**长方体、球、距离区间、实体类型/分数等**；不是任意位图查表。

任意 CSG 形状可以；任意高分辨率像素画需要大量掩码或更高层点阵，受命令长度限制。

### 5.3 每种材料 1 CB

一个命令方块一次只执行一条命令，一条 `execute` 链末尾只有一个 `run`：

```text
一个材料 CB
→ 一个 execute 链
→ 一个 run particle / setblock / fill
→ 一次只输出一个点
```

所以“每种材料 1 CB”成立，但它压缩的是 **CB 数量**，不是构建时间。

两种驱动方式：

| 方式 | 行为 |
|---|---|
| 共享 cell 计数器 | 所有材料 CB 看同一个格点；同一格通常只有一种材料命中，实际约 1 块/tick |
| 每材料独立 cell 计数器 | 每种材料遍历自己的点；最多 80 块/tick，但计数器和掩码复杂度高 |

如果允许 `function`，一个材料 CB 可以调用一个函数，函数内放多条 `setblock`；这时 CB 数仍是每材料 1 个，但函数命令数和 10,000 条/次上限会成为新约束。

### 5.4 80 CB 建筑比赛的边界

```text
材料数 ≤ 80
每种材料 1 CB
→ CB 预算刚好用满
```

但还要算：

- 一个 CB 一次一个 `run`；
- 32,500 字符/命令，掩码不能无限长；
- 共享计数器时约 20 格/秒，大模型要按 `cells / 20` 估时间；
- 每 tick 80 个 `setblock` 可能造成方块更新压力；
- 实心体用 `fill` 比 NXS 点阵更划算。

推荐混合：

```text
大块实心 → greedy fill
表面/镂空/曲线 → NXS 点阵 + 掩码
材料选择 → 每材料 1 CB 或 function
```

### 5.5 billboard：转到玩家视角

参考里的：

```text
rotated as @s rotated ~90 45
positioned ^^^10000
facing entity @s eyes
positioned ^^^20000
...
positioned ^^^28284.27124
```

是在构造**面向玩家视角的屏幕基座**：

- `10000` / `20000` 是用大距离构造方向向量，减少小角度舍入；
- `28284.27124 = 20000 × √2`，是对角线归一化；
- `facing entity @s eyes` 把方向重新指回玩家；
- 最终把点阵投到玩家面前的平面上。

因此：

- 世界固定建筑：可以删掉 billboard，直接用世界轴/建筑朝向；
- 粒子画 / 屏幕 UI / 玩家面前展示：保留，并封装成 `billboard=True`。

### 5.6 `NxsRaster` IR

```python
NxsRaster(
  frame="nx",                  # 坐标架实体
  origin="eyes+3",
  levels=4,                    # 1, 1/2, 1/4, 1/8
  axes=["forward", "right"],   # 2D；3D 再加 up
  masks=[                      # CSG 掩码
    Sphere(center, r),
    Box(x, y, z, dx, dy, dz),
    Ring(center, r_outer, r_inner),
  ],
  material="minecraft:...",
  emit="particle" | "setblock" | "fill",
  billboard=True,
)
```

编译器要做：

1. 生成 dyadic 点阵；
2. 把 `masks` 编译成 `if` / `unless` 链；
3. 每种材料生成一个 CB，或生成一个 function；
4. 校验命令长度、CB 数、每 tick 输出、掩码互斥；
5. `billboard` 单独生成，不污染几何。

`NxsRaster` 的产物不是“圆/树”，而是**任意 CSG 体素图**：粒子线框、法阵、角色脸、地形切片、建筑表面都能用同一套 IR。
