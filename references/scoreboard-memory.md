# 用 dummy 计分板做内存（基岩版）

> 基岩版计分板**只有 `dummy` 一种准则**：分数不会自动变化，全部由命令读写。
> 这既是限制，也是优势：状态完全可控、可预测、可测试。

## 1. 建目标与显示

```mcfunction
scoreboard objectives add arena dummy
scoreboard objectives add coins dummy "Coins"
scoreboard objectives add shop dummy

scoreboard objectives setdisplay sidebar arena
scoreboard objectives setdisplay sidebar coins descending
scoreboard objectives setdisplay belowname coins
scoreboard objectives list
scoreboard objectives remove arena
```

- `add <name> dummy [displayName]`；显示名有空格要加引号。
- `setdisplay <list|sidebar|belowname> [objective] [ascending|descending]`。
- `belowname` 是基岩版拼写（没有下划线）。
- `list` 槽在基岩版目前不可靠，重要信息放 `sidebar` / `belowname`。
- 侧边栏最多显示 15 行；以 `#` 开头的假玩家不会显示。

## 2. 读写分数

```mcfunction
scoreboard players set @s coins 0
scoreboard players add @s coins 10
scoreboard players remove @s coins 3
scoreboard players reset @s coins       # 删除该目标的分数（不是置 0）
scoreboard players reset @s             # 删除该玩家所有目标
scoreboard players list @s
```

- `add` 负数等于减；`remove` 负数等于加。
- `reset` 是“移除记录”，之后选择器 `scores={coins=0}` 不会匹配未跟踪的分数；要“归零但保留”用 `set 0`。
- 分数是 32 位整数：-2,147,483,648 .. 2,147,483,647；溢出会回绕。

## 3. 假玩家（全局变量）

```mcfunction
scoreboard players set fb_state arena 1
scoreboard players add fb_tick arena 1
scoreboard players set fb_max arena 100
scoreboard players set fb_two arena 2
```

- 名字以 `#` 开头，不会出现在侧边栏。
- 适合全局状态、常量、计数器、计时器。
- 约定：`fb_state`、`fb_tick`、`fb_count`、`fb_cd`、`fb_flag`、`fb_two`、`fb_max`。
- **不要用 `#state` 这类假玩家名**：网易 1.21.130 解析 `scoreboard ... #name` / `if score #name ...` 会报“意外的 #”。统一用 `fb_` 前缀。
- 常量要显式初始化，不要依赖“未跟踪=0”的隐含行为（可读性差）。

## 4. 每玩家状态

```mcfunction
# 初始化
execute as @a unless score @s initialized matches 1 run scoreboard players set @s initialized 1

# 每人加 1 分
execute as @a run scoreboard players add @s kills 1

# 只对满足条件的玩家
execute as @a[scores={kills=10..}] run title @s actionbar §610 kills!
```

- `execute as @a ...` 为每个玩家 fork；`@s` 是当前玩家。
- 选择器里 `scores={...}` 只匹配已跟踪的分数；玩家第一次被 `set/add` 时自动创建。
- 玩家退出后分数保留；重新加入要先判断是否初始化。

## 5. 运算

```mcfunction
scoreboard players operation @s result = @s value      # 赋值
scoreboard players operation @s result += @s bonus     # 加
scoreboard players operation @s result -= @s penalty   # 减
scoreboard players operation @s result *= @s factor    # 乘
scoreboard players operation @s result /= @s divisor   # 整除（向下取整）
scoreboard players operation @s result %= @s modulus   # 取模（正余数）
scoreboard players operation @s result >< @s other     # 交换
scoreboard players operation @s result < @s other      # 取较小
scoreboard players operation @s result > @s other      # 取较大
```

- 运算符：`=`、`+=`、`-=`、`*=`、`/=`、`%=`、`><`、`<`、`>`。
- 右边是“目标 + 目标名”，可以是 `@s`、`fb_fake`、玩家名。
- 除数为 0：基岩版“成功但不改变目标值”，不会报错；要自己防 0。
- 负数除法向下取整（不是向 0 取整），做“每 20 tick 一次”时通常没问题，做负数坐标要小心。
- `%=` 用正余数；`-1 % 2 = 1`。

### 常用数学

```mcfunction
# 钳制到 0..100
execute if score fb_n obj matches 101.. run scoreboard players set fb_n obj 100
execute if score fb_n obj matches ..-1 run scoreboard players set fb_n obj 0

# 取绝对值（先复制，再判断负号）
scoreboard players operation fb_abs obj = fb_n obj
execute if score fb_abs obj matches ..-1 run scoreboard players operation fb_abs obj *= fb_neg obj

# 求符号（-1/0/1）
scoreboard players set fb_sign obj 0
execute if score fb_n obj matches 1.. run scoreboard players set fb_sign obj 1
execute if score fb_n obj matches ..-1 run scoreboard players set fb_sign obj -1

# 乘以 1.5（先乘 3 再除 2）
scoreboard players operation fb_r obj = fb_n obj
scoreboard players operation fb_r obj *= fb_three obj
scoreboard players operation fb_r obj /= fb_two obj

# 百分比：hp * 100 / max
scoreboard players operation fb_pct obj = fb_hp obj
scoreboard players operation fb_pct obj *= fb_hundred obj
scoreboard players operation fb_pct obj /= fb_maxhp obj
```

## 6. 范围比较

```mcfunction
execute if score @s coins matches 10.. run ...        # >= 10
execute if score @s coins matches ..0 run ...         # <= 0
execute if score @s coins matches 5..10 run ...       # 5..10
execute if score @s coins matches 5 run ...           # 恰好 5
```

- 选择器里也能写范围：`@a[scores={coins=10..}]`。
- 取反：`@a[scores={coins=!10}]`、`@a[scores={coins=!10..20}]`。
- 需要“不等于”时，用 `unless score ... matches ...` 或选择器 `!`。

## 7. 随机与测试

```mcfunction
scoreboard players random @s rng 1 6
scoreboard players test @s rng 1 3
```

- `random <min> <max>` 闭区间；`min` 必须小于 `max`。
- `test <min> [max]` 是旧式测试；新代码优先 `execute if score ... matches ...`。
- `test` 的 `*` 表示极值：`scoreboard players test @s obj * 5`。

## 8. 显示名与顺序

```mcfunction
scoreboard objectives add coins dummy "金币"
scoreboard objectives setdisplay sidebar coins descending
```

- 显示名在 `add` 时给；基岩版**没有** `objectives modify`，之后不能改显示名（只能删了重建）。
- `ascending`/`descending` 只对 `sidebar`/`list` 有意义；`belowname` 不接受排序参数。
- 侧边栏只显示前 15 名；假玩家不显示。

## 9. 命名与状态编码

推荐：

| 类型 | 命名 | 例子 |
|---|---|---|
| 全局状态 | `fb_state` | 0=idle 1=count 2=run 3=end |
| 计时 | `fb_tick` / `fb_cd` / `fb_hold` | 每 tick +1 或 -1 |
| 计数 | `fb_count` / `fb_wave` / `fb_score` | 整数 |
| 常量 | `fb_two` / `fb_max` / `fb_hundred` | 显式初始化 |
| 临时标记 | `fb_flag` / `fb_done` | 用完清零 |
| 每玩家 | `@s.<name>` | `coins`, `kills`, `cd`, `job` |

状态编码：

- 0..N 的枚举最直观；不要用“多个布尔分数”表达互斥状态。
- 布尔用 0/1，方便 `matches 1` 和取模。
- 需要“阶段 + 子阶段”时用两个分数（`fb_phase`, `fb_step`），不要硬编码成 10、11、12。
- 坐标存整数（计分板没有小数）；需要小数时放大 100 倍存。

## 10. 没有自动统计怎么办

基岩版没有 `deathCount`、`playerKillCount`、`health`、`xp` 等准则。常见替代：

| 需求 | 替代 |
|---|---|
| 死亡计数 | 行为包/脚本的死亡事件，或自定义“重生检测”；命令方块单独做不到可靠检测 |
| 击杀计数 | 击杀后由掉落物/区域/tag 触发，或行为包事件 |
| 生命值 | `effect` 施加/移除，或用 `damage` 控制；读不到当前血量 |
| 经验 | 读不到；用 `xp` 给/扣，自己记账 |
| 队伍 | tag：`tag @s add red`；选择器 `tag=red` |
| Boss 血条 | `titleraw actionbar` / sidebar / 多次 `title` |

> 如果需求强依赖死亡/击杀/血量，建议直接上行为包脚本（Script API）或实体事件，不要硬用命令方块模拟。

## 11. 初始化与清理

```mcfunction
# 初始化（世界加载/重置时跑一次）
scoreboard objectives add arena dummy
scoreboard players set fb_state arena 0
scoreboard players set fb_tick arena 0
scoreboard players set fb_count arena 0
scoreboard players set fb_two arena 2

# 清理（每轮结束）
scoreboard players set @a temp 0
tag @a remove ready
title @a clear
```

- 目标已存在时 `add` 会失败；初始化函数要么先 `remove` 再 `add`（会清分），要么忽略失败。
- 用 `scoreboard objectives list` 检查是否已存在。
- 临时分数每轮清零，避免“上一轮的状态”污染下一轮。

## 12. 参考

- [Scoreboard — Minecraft Wiki](https://minecraft.wiki/w/Scoreboard)
- [Commands/scoreboard — Minecraft Wiki](https://minecraft.wiki/w/Commands/scoreboard)
- [Minecraft Creator Docs — scoreboard](https://learn.microsoft.com/en-us/minecraft/creator/commands/commands/scoreboard)
