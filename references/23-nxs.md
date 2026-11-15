# 23 · NXS：递归坐标架几何（binaryTree 2D/3D）

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
- `particle` 名称走 CHelper 白名单
- 最终命令用 CHelper 过语法

**不在 DSL 里手写 1024/2048 魔法数**：它们是“把方向变成射线”的哨兵值，应该封装成 `NxsOp.ray(times)`。

## 4. 与 FMBE 的关系

| | NXS | FMBE |
|---|---|---|
| 本质 | execute 坐标架递归 | 实体部件 + playanimation |
| 产物 | 粒子/几何线框 | 模型/骨骼动画 |
| 锚点 | `tree` 船/盔甲架 | carrier 僵尸/狐狸 |
| 用途 | 法阵、符文、轨道、3D 线框 | Boss、武器、展示体 |

两者可以叠加：NXS 画法阵/轨道，FMBE 放主体。

## 5. 当前状态

- 这两份已归入语料 `nxs` 类，不再当普通 math。
- 还没有 `nxs_ir.py` 编译器；先把模式和 IR 固定。
- 下一步：实现 2D circle / 3D cube 两个最小 shape，生成命令后用 CHelper 校验。
