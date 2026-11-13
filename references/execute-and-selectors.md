# execute 与目标选择器（基岩版）

> Bedrock 1.19.50+ 的新 execute 语法。旧语法 `execute <target> <pos> <command>` 已被移除，不要再用。
> 网易 1.21.130 同样使用新语法；导入的旧地图里若看到 `execute @a ~ ~ ~`，先手工升级。

## 1. execute 的 11 个子命令

```
execute
  align <axes>
  anchored <eyes|feet>
  as <target>
  at <target>
  facing <x y z>
  facing entity <target> <eyes|feet>
  in <overworld|nether|the_end>
  positioned <x y z>
  positioned as <target>
  rotated <yaw> <pitch>
  rotated as <target>
  if|unless block <x y z> <block> [blockStates]
  if|unless blocks <begin> <end> <destination> <all|masked>
  if|unless entity <target>
  if|unless score <target> <objective> <op> <source> <sourceObjective>
  if|unless score <target> <objective> matches <range>
  run <command>
```

- 子命令可以任意顺序串联，`run` 只能出现一次且在最后。
- 链可以以条件子命令结尾（不写 `run`），这时它本身就是一个“门”，成功次数 > 0 表示条件成立。
- **没有** `store`、`detect`、`runasync`、`if data/items/predicate/biome/dimension/loaded`。

## 2. 执行上下文

| 子命令 | 改变什么 | 不改变什么 |
|---|---|---|
| `as` | 执行者（`@s`） | 位置、旋转、维度 |
| `at` | 位置、旋转、维度 | 执行者 |
| `positioned` | 位置（并把 anchor 重置为 feet） | 执行者、旋转 |
| `rotated` | 旋转 | 执行者、位置 |
| `facing` | 旋转（朝向目标） | 执行者、位置 |
| `anchored` | 局部坐标原点（eyes/feet） | 执行者、位置、旋转 |
| `align` | 位置向下取整到方块 | 其他 |
| `in` | 维度（并按比例换算坐标） | 执行者、旋转 |

**最重要**：`as` 只换执行者，不换位置；`at` 只换位置/旋转，不换执行者。
所以“每个玩家在自己脚下放方块”必须 `execute as @a at @s run ...`。

### Bedrock 的 fork 是深度优先

```mcfunction
execute as @e[type=armor_stand] as @e[type=armor_stand] run summon armor_stand
```

基岩版会把后面的子命令作为一个整体，对每个外层实体依次执行；没有 Java 的广度优先写法。

## 3. 目标选择器变量

| 变量 | 选中 |
|---|---|
| `@a` | 所有在线玩家 |
| `@p` | 最近的玩家 |
| `@r` | 随机玩家（可用 `type=` 选非玩家） |
| `@e` | 所有已加载实体 |
| `@s` | 当前执行者（命令方块里通常不是玩家） |
| `@n` | 最近的实体（新版；用前先 `/help` 确认） |
| `@initiator` | 点击 NPC 对话按钮的玩家（Bedrock/教育版） |

> 命令方块里的 `@s` 是命令方块本身；要玩家必须 `execute as @a ...` 或直接用 `@a/@p`。

## 4. 基岩版选择器参数（完整）

```text
@e[
  type=zombie,                     # 实体 ID；type=!zombie 取反
  family=monster,                  # 实体家族；可多个，AND；family=!monster 取反
  name=Herobrine,                  # 名字精确匹配；name=!Bob 取反
  tag=ready,                       # tag；tag=!ready 取反；tag= 无 tag；tag=! 至少一个
  scores={coins=1..,deaths=..5},   # 分数范围；scores={x=!10} 取反
  x=0,y=64,z=0,                    # 位置
  dx=15,dy=5,dz=15,                # 体积
  r=10,rm=5,                       # 最大/最小距离
  rx=45,rxm=0,                     # pitch 最大/最小（向上为负）
  ry=90,rym=-90,                   # yaw 最大/最小
  m=!spectator,                    # 游戏模式：survival/creative/adventure/spectator/default，或 s/c/a/d
  l=30,lm=10,                      # 经验等级最大/最小
  c=1,                             # 数量；负数反向取最远
  hasitem={item=diamond,quantity=5..,location=slot.weapon.mainhand,slot=0},
  haspermission={movement=disabled},
  has_property={...}
]
```

### 关键差异（相对 Java）

| Java | 基岩版 |
|---|---|
| `distance=..5` | `r=5` |
| `distance=5..10` | `rm=5,r=10` |
| `limit=1` | `c=1` |
| `sort=nearest/furthest` | `c=1` / `c=-1` |
| `level=10` | `lm=10,l=10` |
| `gamemode=creative` | `m=creative` |
| `x_rotation` / `y_rotation` | `rx`/`rxm`、`ry`/`rym` |
| `team=red` | ❌ 无；用 `tag=red` |
| `nbt={...}` | ❌ 无；用 `tag`/`scores`/`hasitem` |
| `predicate=` | ❌ 无 |
| `advancements=` | ❌ 无 |

> `l` 是**最大**等级，`lm` 是**最小**；`rx`/`ry` 也是最大，`rxm`/`rym` 是最小。命名容易反，写完用 `/help` 或小范围测试。

### `hasitem` 细节

```mcfunction
# 主手有钻石剑
@a[hasitem={item=diamond_sword,location=slot.weapon.mainhand}]

# 背包至少 5 个钻石
@a[hasitem={item=diamond,quantity=5..}]

# 0 个（没有）某物品
@a[hasitem={item=bread,quantity=0}]

# 同时有 A 和 B（列表形式）
@a[hasitem=[{item=iron_ingot,quantity=3..},{item=stick,quantity=1..}]]

# 指定槽位
@a[hasitem={item=bread,location=slot.hotbar,slot=0}]
```

- 是 `quantity` 不是 `count`。
- `quantity` 支持范围 `..5`、`5..`、`0..5`，也支持 `!5` 取反。
- `slot` 必须和 `location` 一起用。
- `data` 仍可用于区分变种（如药水），但很多方块物品的 data 不可靠。

### `haspermission` / `has_property`

```mcfunction
@a[haspermission={movement=disabled}]
@a[haspermission={movement=disabled}]
@e[has_property={...}]
```

- `haspermission` 的值是 `enabled`/`disabled`；网易 1.21.130 未验证该选择器，先用 `/execute if entity` 小范围测试。
- `has_property` 匹配实体属性（行为包定义的 property）。

### 坐标小坑

- 基岩版选择器坐标支持 `~`，**不支持 `^`**。
- 只写 `x=0` 且没有 `r`/`dx` 时，整数坐标会被中心校正为 `0.5`；要精确对齐写 `x=0.0`。
- `dx/dy/dz` 是带符号差值，不是“另一角坐标”。

## 5. 条件子命令

### `if block`

```mcfunction
execute if block ~ ~-1 ~ gold_block run say gold
execute if block 10 64 10 chest ["minecraft:cardinal_direction"="east"] run say chest
execute unless block ~ ~ ~ air run say inside
```

- 方块状态是 `["state"="value",...]`，不是 `[facing=east]`。
- 位置未加载/越界时，`if` 失败、`unless` 成功。

### `if blocks`

```mcfunction
execute if blocks 0 64 0 3 66 3 100 64 0 all run say same
execute if blocks 0 64 0 3 66 3 100 64 0 masked run say same_ignoring_air
```

### `if entity`

```mcfunction
execute if entity @a[tag=ready] run say ready
execute unless entity @e[type=zombie,tag=wave] run say cleared
```

- 空选择器：`if entity` 失败，`unless entity` 成功。
- 这是“有没有人/有没有怪”的标准写法。

### `if score`

```mcfunction
# 范围
execute if score @s coins matches 10.. run say ten_plus
execute if score @s coins matches ..0 run say broke
execute if score @s coins matches 5 run say exactly_five
execute unless score @s coins matches 1.. run say zero_or_less

# 两个分数比较
execute if score @s coins >= @s cap run say capped
execute if score fb_a obj < fb_b obj run say less
execute if score fb_a obj = fb_b obj run say equal
```

- `matches` 后面是整数范围：`5`、`5..`、`..5`、`5..10`。
- 比较运算符：`<`、`<=`、`=`、`>=`、`>`。
- 两个分数比较时，两边都要写“目标 + 目标名”。
- 分数未跟踪时按 0 处理。

### 条件串联

```mcfunction
execute if score fb_state obj matches 1 if score fb_count obj matches 0 run say go
execute as @a at @s if block ~ ~-1 ~ stone run say on_stone
```

条件按顺序求值；任何一个失败，后面的子命令和 `run` 都不执行。

## 6. 常用配方

### 每个玩家在自己位置

```mcfunction
execute as @a at @s run particle flame ~ ~1 ~
```

### 每个玩家眼睛位置

```mcfunction
execute as @a at @s anchored eyes run particle end_rod ^ ^ ^1
```

- `^` 局部坐标需要 `at`/`rotated`/`facing` 提供旋转；`anchored eyes` 把原点移到眼睛。

### 玩家脚下的方块

```mcfunction
execute as @a at @s if block ~ ~-1 ~ gold_block run say standing_on_gold
```

### 玩家面前的方块（射线 1 格）

```mcfunction
execute as @a at @s run setblock ^ ^ ^1 glass
```

### 只对生存模式玩家

```mcfunction
execute as @a[m=!spectator,m=!creative] run ...
```

### 最近 5 格内的玩家

```mcfunction
execute as @a[r=5] run ...
```

### 方形区域内的玩家

```mcfunction
execute as @a[x=0,y=64,z=0,dx=9,dy=3,dz=9] run ...
```

### 给所有人计数（没有 execute store 的替代）

```mcfunction
# 每 tick 清零
scoreboard players set fb_online obj 0

# 每个玩家给全局假玩家 +1（Bedrock 没有 store，这是标准替代）
execute as @a run scoreboard players add fb_online obj 1

# 判断人数
execute if score fb_online obj matches 3.. run say 3+
```

### 统计实体数量

```mcfunction
scoreboard players set fb_zombies obj 0
execute as @e[type=zombie,tag=wave] run scoreboard players add fb_zombies obj 1
execute if score fb_zombies obj matches 1.. run say zombies_left
```

### 把玩家传送到各自的重生点

```mcfunction
execute as @a at @s run tp @s ~ ~ ~
```

（真要“各自的重生点”需要给每个玩家存坐标；计分板只有整数，通常用 tag + 固定点。）

### 条件传送

```mcfunction
execute as @a[scores={checkpoint=1}] at @s run tp @s 100 64 100
```

### 结构/区域比较

```mcfunction
execute if blocks 0 64 0 4 68 4 20 64 0 all run say gate_open
```

### 维度限制

```mcfunction
execute as @a in the_end run say in_end
```

- `in` 会切换执行维度；`~` 坐标会按比例换算（下界/主世界 8:1）。

## 7. 常见错误

| 写法 | 问题 | 改成 |
|---|---|---|
| `execute as @a run tp @s ~ ~ ~` | 没有 `at`，所有人传到命令方块位置 | `execute as @a at @s run tp @s ~ ~ ~` |
| `execute at @a run say @s` | 没有 `as`，`@s` 还是命令方块 | `execute as @a at @s run say @s` |
| `execute if score @s obj = 1` | 右边缺目标/目标名 | `execute if score @s obj matches 1` |
| `execute if score @s obj > 5` | 不能拿常数直接比 | `execute if score @s obj matches 6..` |
| `execute if block ~ ~ ~ stone[facing=east]` | Java 方块状态 | `execute if block ~ ~ ~ stone ["minecraft:cardinal_direction"="east"]` |
| `@e[distance=..5]` | 基岩版没有 `distance` | `@e[r=5]` |
| `@a[team=red]` | 基岩版没有 team | `@a[tag=red]` |
| `@a[limit=1]` | 基岩版用 `c` | `@a[c=1]` |
| `execute store result score ...` | 基岩版没有 store | 用 `execute as ... run scoreboard players add ...` 计数 |
| `execute as @e ... detect ...` | 旧/Java 子命令 | `execute if block ...` |
| `execute @a ~ ~ ~ say hi` | 旧 execute 语法已移除 | `execute as @a at @s run say hi` |

## 8. 速记

- `as` = 谁；`at` = 在哪/朝哪；`positioned` = 只改位置；`rotated` = 只改朝向。
- 条件优先用 `if`/`unless`，不要用 `testfor` 堆叠。
- 没有 `store`：用“执行副作用 + 成功次数”或“每个实体给全局分数 +1”来计数。
- 选择器能窄就窄：`type`、`family`、`tag`、`c` 先用上。
- 写完用 `execute if entity <selector>` 单独测试选择器，再放进链里。

## 9. 参考

- [Commands/execute — Minecraft Wiki](https://minecraft.wiki/w/Commands/execute)
- [Target selectors — Minecraft Wiki](https://minecraft.wiki/w/Target_selectors)
- [Minecraft Creator Docs — execute](https://learn.microsoft.com/en-us/minecraft/creator/commands/commands/execute)
