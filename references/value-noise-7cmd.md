# 7 命令值噪声核（视频样本拆解）

> 来源：用户提供的 7 条命令 + B 站视频  
> [只用7个命令方块做出柏林噪声生成地形](https://www.bilibili.com/video/BV1vfKJedEdA)  
> [MC指令教学：值噪声与柏林噪声](https://www.bilibili.com/video/BV1rrHpzuE1i)

## 1. 它是“核”，不是完整 16×16 地形机

7 条命令一次只生成 **一列**：

```text
1. 在 a 锚点 + nxs 方向上算出采样位置，summon o
2-5. 用 a/b/c/d 四个角把 o 搬到插值后的位置
6. 在 o 处 fill 一列
7. kill o
```

要生成整片地形，必须有外层循环移动 `nxs`（或玩家/锚点）；视频里“7 个命令方块”通常指**噪声核**，不是 64 列扫描器。

## 2. 实体角色

| 名字/标签 | 作用 |
|---|---|
| `a/b/c/d` | 四个晶格角锚点 |
| `nxs` | 方向/采样锚点（决定当前列） |
| `o` | 当前采样点（临时盔甲架） |
| `armor_stand` | 所有锚点/采样点的载体 |

## 3. 七条命令的职责

### 命令 1：建立采样点

```mcfunction
execute as @e[name=a] at @s positioned ~7.5 -60 ~7.5
  rotated as @e[tag=nxs] positioned ^^^4
  rotated as @e[tag=nxs] positioned ^^^2
  rotated as @e[tag=nxs] positioned ^^^1
  rotated as @e[tag=nxs] positioned ^^^0.5
  rotated as @e[tag=nxs] positioned ^4^^
  rotated as @e[tag=nxs] positioned ^2^^
  rotated as @e[tag=nxs] positioned ^1^^
  rotated as @e[tag=nxs] positioned ^0.5^^
  positioned ~-8 ~-4096 ~-8
  facing entity @s feet
  positioned ~8 ~4096 ~8
  run summon armor_stand ~ ~10 ~ ~ ~90 minecraft:entity_spawned o
```

作用：从 `a` 出发，用 `nxs` 的方向做多次 4/2/1/0.5 分叉，再经过大坐标折叠，生成当前采样点 `o`。

### 命令 2-5：四角插值

分别用 `a/b/c/d`：

```text
2 → a
3 → b
4 → c
5 → d
```

每条都做类似的嵌套 `rotated/positioned/facing`，把 `o` 往对应角的方向搬。  
四条合起来就是四角值噪声插值。

### 命令 6：落一列

文本里的：

```text
fill ~~0.5~~ -60~ grass
```

应整理为：

```mcfunction
fill ~ ~0.5 ~ ~ ~-60 ~ minecraft:grass
```

从 `o` 上方 0.5 格填到 y=-60，形成一列草/地表。

### 命令 7：清理

```mcfunction
kill @e[name=o]
```

`o` 是临时采样点，不清理会累积。

## 4. 与 385 条 calc 链的对比

| | 7 命令核 | scoreboard calc |
|---|---|---|
| 计算 | 实体坐标/旋转/精度 | 计分板整数 |
| 方块数 | 7（核） | 数百 |
| 可移植 | 依赖浮点/版本 | 定点稳定 |
| 网格 | 需外层循环 | 自身状态机 |
| 调试 | 实体位置直观 | 分数/状态复杂 |

## 5. 要变成完整地形还缺什么

1. **外层扫描器**：移动 `nxs` 走 16×16。
2. **四角初始化**：a/b/c/d 固定到晶格四角。
3. **列高限制**：`fill` 从 `~0.5` 到 `~-60` 会填很深，实际应限制高度。
4. **清理/重置**：每列 kill o，结束时清理锚点。
5. **区块加载**：所有采样点必须在 tickingarea 内。

## 6. 注意

- 样本里的 `【】` 必须换成 `[]`。
- `summon ... ~~10~~~90 minecraft:entity_spawned o` 这类写法要按实际版本核对参数顺序；不要直接照抄。
- `fill` 的 `~~0.5~~ -60~` 是压缩写法，实际要拆成 6 个坐标。
- 这套是**视觉噪声**，不是稳定服务端数据。

## 7. 一句话

> 7 条命令 = **采样点生成 + 四角插值 + 落一列 + 清理**；  
> 真正的地形机还需要一个移动 `nxs` 的扫描器。
