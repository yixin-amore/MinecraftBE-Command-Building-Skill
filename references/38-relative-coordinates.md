# 38 · 坐标策略：默认相对坐标

## 硬规则

> **所有新生成命令默认使用相对坐标。**  
> 绝对坐标只用于世界锚点、固定结构原点、地标/传送点，并显式标注 `ANCHOR`。

默认顺序：

```text
先建立执行者/坐标源
→ 再用 ~ 或 ^
→ 需要固定世界点时，只设置一次 anchor
```

## `~` 和 `^` 的分工

| 写法 | 含义 | 依赖 |
|---|---|---|
| `~ ~ ~` | 世界轴相对偏移 | 执行位置 |
| `~5 ~1 ~-2` | 世界轴偏移 | 执行位置 |
| `^ ^ ^` | 局部坐标：左 / 上 / 前 | 执行位置 + 朝向 |
| `^1 ^ ^3` | 左 1、前 3 | 朝向 |

```mcfunction
# 执行者上方 2 格
setblock ~ ~2 ~ minecraft:stone

# 执行者面向方向前 3 格
setblock ^ ^ ^3 minecraft:stone
```

`^` 只有在 `rotated` / 实体朝向存在时才有意义。

## 三种常用上下文

### 1. 跟随执行者

```mcfunction
execute as @p at @s run setblock ~ ~-1 ~ minecraft:gold_block
```

### 2. 跟随任意实体

```mcfunction
execute as @e[tag=torch] at @s run particle minecraft:flame ^ ^ ^0.5 0 0 0 0 1
```

### 3. 固定锚点，内部相对

```mcfunction
# ANCHOR: 舞台中心 100 64 100
execute positioned 100 64 100 rotated 0 0 run function stage/center
```

进入 `function` 后继续用 `~` / `^`，不要在每个命令里重复 `100 64 100`。

## 选择器里的相对坐标

```mcfunction
# 以执行位置为中心，1×1×1 的盒子
@e[x=~,y=~,z=~,dx=1,dy=1,dz=1]

# 半径 6 内
@e[distance=..6]

# 执行者前方 3 格附近
@e[x=^,y=^,z=^,distance=..1]
```

注意：

- `x=~,dx=1` 的盒子从 `~` 到 `~+1`；
- `r`/`rm` 是球形距离；
- `dx/dy/dz` 是轴对齐盒子，不随朝向旋转；
- 需要随朝向时，用 `^` + `distance` 或先 `execute rotated ...`。

## 命令方块链

命令方块没有 `execute` 源时，`~` 默认相对**该命令方块自身**。

```mcfunction
# 错误：链里每个 CB 的 ~ 都不同，会漂
setblock ~ ~1 ~ minecraft:stone

# 正确：固定一次源
execute positioned 100 64 100 run setblock ~ ~1 ~ minecraft:stone
```

链式 CB 要特别小心：

```text
CB1 at (100,64,100): execute positioned 100 64 100 run ...
CB2 at (101,64,100): ~ 仍然相对 CB2
```

多块链统一使用：

```mcfunction
execute positioned <anchor> rotated <yaw> <pitch> run ...
```

## 生成指令的默认检查

写命令前问：

1. **这是世界锚点吗？**
   - 是：写绝对坐标，并标 `ANCHOR`。
   - 否：用 `~` / `^`。
2. **执行者是谁？**
   - 玩家 / 实体 / 命令方块 / `execute` 源。
3. **需要世界轴还是局部朝向？**
   - 世界轴：`~`
   - 局部：`^` + `rotated`
4. **选择器是否也相对？**
   - 不要混用绝对 `x=100` 和相对 `~`。
5. **多命令是否共享同一个源？**
   - 用 `execute positioned` 固定一次。
6. **BDX/命令方块里的绝对坐标是否只是放置点？**
   - 是：保留；命令内容仍用相对。

## 反例

```mcfunction
# 错：硬编码世界坐标
setblock 100 64 100 minecraft:stone
particle minecraft:flame 100 65 100 0 0 0 0 1

# 对：跟随执行者
execute as @p at @s run setblock ~ ~-1 ~ minecraft:stone
execute as @p at @s run particle minecraft:flame ^ ^1 ^ 0 0 0 0 1

# 对：固定锚点
execute positioned 100 64 100 run setblock ~ ~1 ~ minecraft:stone
```

## 例外

只有这些情况允许绝对坐标：

- 世界锚点 / 舞台中心 / 传送点 / 结构原点；
- `execute positioned <anchor>` 的锚点本身；
- BDX / 命令方块的放置坐标；
- 结构文件里的绝对方块坐标；
- 日志/回读报告中的世界坐标。

例外必须显式写：

```text
ANCHOR: x y z
```

或：

```text
# absolute-anchor: 世界坐标，命令内部仍相对
```
