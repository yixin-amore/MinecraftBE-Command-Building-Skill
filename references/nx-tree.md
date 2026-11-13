# N 叉树 / NX 树：用执行分叉做空间与分支

> 社区常写作“n叉树 / nx树 / N 叉树”。它不是新方块，也不是行为包；  
> 本质是**一条命令通过嵌套 `execute` 产生 N 个执行上下文**，每个上下文跑同一个叶子动作。

## 1. 模型

```text
根上下文（玩家/鱼钩/坐标）
  ├─ execute positioned/rotated → 分支 1 → 叶子
  ├─ execute positioned/rotated → 分支 2 → 叶子
  └─ ... N 个分支
```

- **节点**：一个执行上下文（谁、在哪、朝哪、什么条件）。
- **边**：`as/at/positioned/rotated/anchored/facing` 的变换。
- **分支因子 N**：一次分叉产生的上下文数。
- **叶子**：`particle`、`damage`、`summon`、`setblock`、`tag` 等实际动作。
- `2cb/5cb` 这类说法指**命令方块数量**，不是树的深度；一个方块里可以嵌套很多上下文。

Bedrock 的 `execute` 本身会按目标分叉；N 叉树只是把这个特性**显式组织成树**：

```mcfunction
execute as @e[type=fishing_hook] at @s run tag @e[c=2] add nx_root
execute as @e[tag=nx_root] at @s rotated as @p run tp @s ^^^40 facing ^^^-10
execute as @a[tag=nx_root] at @s anchored eyes positioned ^^^8 rotated as @e[tag=nx_root] positioned ^^^4 rotated as @e[tag=nx_root] positioned ^^^2 run particle minecraft:end_rod
tag @e remove nx_root
```

（这是结构示意，不是完整武器系统；实际项目要加冷却、命中、清理。）

## 2. 三种用法

### 2.1 射线 / 穿透

沿视线反复 `positioned ^^^distance`，每个分支只做一次检测或粒子：

- 近处分支：`^^^1`、`^^^2`、`^^^4`；
- 远处分支：`^^^8`、`^^^16`；
- 每个分支的叶子做 `if block`/`if entity`/`particle`。

### 2.2 圆 / 椭圆

命令里不现场算 `sin/cos`，而是预计算偏移表：

```text
θ: 0°, 15°, 30°, ... 345°
x = round(r * cosθ), z = round(r * sinθ)
```

然后用 N 个 `positioned ^x^y^z` 分支遍历这些偏移，叶子放粒子/实体。

**对称优化**：只算第一象限，镜像四个象限：

```text
(+x,+z) (+x,-z) (-x,+z) (-x,-z)
```

圆周采样从 4N 降到 N 个分支。

### 2.3 体积 / 传送门 / 区域扫描

用两层/三层 N 叉树枚举平面/体积：

```text
外层：x 偏移
内层：z 偏移
叶子：if block / particle / teleport
```

适合传送门、检测区、圆形判定；但分支数 = 点数，必须限制。

## 3. 复杂度与限制

- 一条命令最多 32,500 字符；嵌套 `execute` 太长要拆成多条命令/多个方块。
- 每个分支的叶子都执行一次；**成本 = 分支数 × 叶子成本**，按 20 Hz 计。
- 选择器分叉（`execute as @e[...]`）会随实体数增长；不要用裸 `@e`。
- 递归/无限分叉不允许；深度和分支数都要有上限。
- 远处执行需要区块加载；关键机关加 `tickingarea`。

## 4. 设计步骤

```text
1. 定根：谁/哪个实体/哪个坐标
2. 定坐标系：世界坐标还是 ^ 局部坐标
3. 定分支表：射线距离 / 圆偏移 / 体积点
4. 定叶子：只做一件最小动作
5. 定清理：tag/临时实体/分数
6. 估算：分支数 × 叶子命令数 × 20 Hz
7. 进服验证：先 1 个分支，再 N 个，再全量
```

## 5. 与普通 chain 的取舍

| 场景 | 用 chain | 用 N 叉树 |
|---|---|---|
| 顺序步骤 | ✅ | ❌ |
| 同一动作打多个点 | ❌ 方块太多 | ✅ |
| 空间形状 | 难 | ✅ |
| 可读性 | 高 | 需要表/注释 |
| 调试 | 逐块 | 先单分支再全量 |

## 6. 来源

- [Bedrock Wiki — Execution Forking](https://github.com/bedrock-oss/bedrock-wiki/blob/0930b394916fad2275d600f3bf77eed8f2783d02/docs/commands/execution-forking.md)
- [MCBE n叉树 圆/椭圆 对称原理（Bilibili）](https://www.bilibili.com/video/BV1fe3rz8EX7/)
- [MCBE nx树 作品与指令讨论（233乐园）](https://www.233leyuan.com/post-detail/1951414174883661672)
