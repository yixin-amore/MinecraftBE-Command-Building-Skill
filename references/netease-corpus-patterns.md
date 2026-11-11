# 网易真实地图命令方块语料分析

> 样本：用户提供的 12 个 `.bdx` / `.mcworld` 导入文件，共 **18,945 条非空命令**、**19,501 个命令方块**（含空命令）。
> 解析工具：AuroraBuild 的 `AuroraStructure` 模块（`structure.StructureFromFile` + `GetChunks` + `GetChunksNBT`）。
> 版本目标：网易 1.21.130 / 协议 898。

## 1. 样本概览

| # | 格式 | 结构尺寸 | 命令方块 | 非空命令 |
|---|---|---|---:|---:|
| 01 | BDX | 42×13×61 | 742 | 738 |
| 02 | MCWorld | 77×61×52 | 489 | 489 |
| 03 | BDX | 166×11×103 | 858 | 858 |
| 04 | BDX | 101×80×101 | 1,557 | 1,557 |
| 05 | MCWorld | 101×382×101 | 1,531 | 1,531 |
| 06 | MCWorld | 68×39×68 | 2,898 | 2,898 |
| 07 | BDX | 163×26×90 | 6,492 | 6,492 |
| 08 | MCWorld | 71×32×110 | 2,562 | 2,562 |
| 09 | BDX | 5×6×3 | 34 | 34 |
| 10 | BDX | 160×58×128 | 1,317 | 1,317 |
| 11 | MCWorld | 29×4×4 | 89 | 89 |
| 12 | MCWorld | 110×72×89 | 932 | 932 |

## 2. 命令频率（前 30）

| 命令 | 次数 | 说明 |
|---|---:|---|
| `execute` | 11,696 | 绝对主力；多数已是新语法 |
| `scoreboard` | 3,829 | 状态、菜单、计分 |
| `tag` | 873 | 玩家/实体标记 |
| `title` | 513 | 标题/actionbar 菜单 |
| `setblock` | 430 | 机关、红石 |
| `clear` | 202 | 收物品/扣费 |
| `replaceitem` | 158 | 背包/槽位 |
| `clone` | 157 | 复制机关/模板 |
| `kill` | 120 | 清实体 |
| `tellraw` | 116 | 文本 |
| `testfor` | 108 | 旧式检测 |
| `tp` | 99 | 传送 |
| `effect` | 99 | 状态效果 |
| `titleraw` | 80 | JSON 菜单 |
| `playsound` | 79 | 音效 |
| `structure` | 65 | 结构保存/加载 |
| `fill` | 56 | 区域方块 |
| `summon` | 35 | 生成实体 |
| `give` | 34 | 给物品 |
| `say` | 33 | 调试/提示 |
| `playanimation` | 30 | 实体动画 |
| `enchant` | 29 | 附魔 |
| `spreadplayers` | 20 | 随机撒实体 |
| `gamerule` | 13 | 规则 |
| `tickingarea` | 13 | 常加载 |
| `particle` | 12 | 粒子 |
| `gamemode` | 8 | 模式 |
| `testforblocks` | 8 | 区域比较 |
| `camerashake` | 5 | 镜头震动 |
| `damage` | 2 | 伤害 |

> `schedule`、`function`、`fog`、`music`、`mobevent`、`ride`、`stopsound`、`toggledownfall` 在这批样本里为 0 次；其中 `schedule`/`function` 在网易官方命令列表内，`fog` 官方标注未实装。

## 3. 模式一：计分板菜单 + actionbar

样本里的“雪球菜单”几乎都是同一套：

```mcfunction
# 给玩家一个状态分
scoreboard players set @s 雪球菜单 1

# 每 tick 根据状态显示 actionbar
titleraw @a[scores={雪球菜单=1}] actionbar {"rawtext":[{"text":"§l§e--------Ф雪球菜单Ф-------"}]}

# 抬头确认 / 低头取消（rx 是最大 pitch，rxm 是最小）
execute as @a[scores={雪球菜单=1},rx=-86,rxm=-90] at @s run tp @s ~~~ facing ~1~0
```

要点：

- 菜单项编号存进一个 objective（`雪球菜单`、`MTC`、`uid`），用 `scores=` 选中。
- 抬头/低头用 `rx`/`rxm`（不是 Java 的 `x_rotation`）。
- 菜单渲染放在 `repeat` 或每秒时钟里；确认动作放在条件链里。
- `titleraw` 的 `rawtext` 只支持 `text/translate/selector/score` + `§`。

## 4. 模式二：常加载区域 + 结构模板

```mcfunction
tickingarea add ~~~ ~100~~100 §k指令区
structure save 红箱子 ~~1~ ~~1~ disk
structure load temp 15012 -57 15021
```

要点：

- `tickingarea` 用紧凑坐标 `~~~`、`~100~~100` 也能被旧解析器接受；新图建议写空格。
- `structure save` 的区域用 `~~1~` 这种相对坐标；`disk` 持久化。
- 结构加载常用于“复制一个小机关/房间”，比 `clone` 更适合带方块实体的结构。
- 远处机关没有 `tickingarea` 就会停。

## 5. 模式三：旧 execute 升级

样本里 677 条旧语法：

```mcfunction
execute @a[scores={MTC=41}] ~ ~ ~ tag @s add 互传机制
execute @a[tag=准备] ~ ~ ~ setblock ~ ~ ~ redstone_block
```

新语法：

```mcfunction
execute as @a[scores={MTC=41}] at @s run tag @s add 互传机制
execute as @a[tag=准备] at @s run setblock ~ ~ ~ redstone_block
```

要点：

- 旧 `execute <target> <pos> <command>` 在 1.19.50 后移除；网易 1.21.130 新图不要用。
- 旧图导入先用 AuroraBuild `utils/command_upgrader` 升级，再手工检查 `detect` → `if block`、`~~~` 坐标、旧 data 参数。
- 旧 `fill ... <block> <data> replace ...` 的 data 参数也要去掉或改方块状态。

## 6. 模式四：检测与区域

```mcfunction
testfor @a[tag=互传机制]
testforblocks ~-2 ~-2 ~-2 ~-2 ~-2 ~-2 ~~1~
execute if block ~ ~-1 ~ gold_block run say on_gold
```

要点：

- 网易地图仍大量用 `testfor`/`testforblocks`；新代码可用 `execute if entity`/`if blocks`。
- 条件链/命令方块里，`testfor` 的成功次数可以直接被 conditional chain 使用。
- 区域比较适合“机关是否被正确搭建”的自检。

## 7. 模式五：表现层

```mcfunction
playanimation @e[name=实体_鹿与管,type=armor_stand] animation.ghast.scale default 100
camerashake add @a[scores={镰刀=1}] 0.25 0.2 rotational
event entity @e[type=creeper] minecraft:stop_exploding
damage @e[type=ender_crystal] 0
spreadplayers -5025 -4985 3 5 @e[type=armor_stand,name=矿方包,r=100]
```

要点：

- `playanimation` 常用于 NPC/盔甲架模型；动画名来自实体定义/资源包。
- `camerashake` 是网易可用的镜头表现；不要用未验证的 `camera`。
- `event` 触发实体事件；`damage` 造成伤害；`spreadplayers` 随机撒实体。
- 这些命令都应在事件触发时执行，不要每 tick 刷。

## 8. 从语料得到的设计结论

1. **执行层几乎全是 `execute`**：把“谁/在哪/什么条件”写进一条 `execute`，比堆 `testfor` 更稳。
2. **状态全在计分板**：每个系统一个 objective（`MTC`、`uid`、`雪球菜单`、`攻击`），假玩家存全局状态。
3. **菜单是“状态 + actionbar + 视角”**：`scores=` 选菜单页，`rx/rxm` 选确认/取消。
4. **常加载是地图的生命线**：远处机关没有 `tickingarea` 就会停。
5. **结构/克隆是复用手段**：`structure save/load` 用于带方块实体的模板，`clone` 用于纯方块。
6. **旧图要升级**：不要把旧 `execute @a ~ ~ ~` 直接抄进 1.21.130 新图。
7. **表现层要克制**：`playanimation`/`camerashake`/`particle` 放在事件里，不要放每 tick 时钟。

## 9. 复现方式

解析工具在 `work/repo/cmd/mcbeextract`（AuroraStructure 模块），输出 JSON：

```bash
go run ./cmd/mcbeextract "/path/to/file.bdx" > out.json
```

字段：`format`、`size`、`command_blocks[]`（`pos`、`block`、`type`、`facing`、`conditional`、`auto`、`delay`、`command`、`nbt`）、`functions[]`。

> 语料只用于学习模式；具体命令是否可用仍以网易 1.21.130 的 `/help` 为准。
