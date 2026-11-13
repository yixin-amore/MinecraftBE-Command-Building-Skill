# 网易我的世界 1.21.130 命令边界

> 目标环境：**网易中国版 · 基岩版 1.21.130 / 协议 898**。
> 证据：网易开发者官网《命令列表及概述》 + 12 个真实网易地图导入文件（18,945 条命令方块命令）的静态解析。

## 1. 先回答：`schedule` 有没有？

**有。**

网易开发者官网的命令列表明确列出：

> `/schedule` 安排函数在特定的游戏刻后运行。

所以 **不要删除 `schedule`**。它调度的是 Add-on 里的函数文件（`function`），不是命令方块本身；如果服务器没有启用行为包/函数，`schedule` 实际不可用，但命令本身存在。

基岩版 1.16.100+ 的语法（网易 1.21.130 以游戏内 `/help schedule` 为准）：

```mcfunction
schedule delay add <function> <delayTicks> [append|replace]
schedule delay clear <function>
schedule clear <function>
schedule on_area_loaded add <from> <to> <function>
schedule on_area_loaded add circle <center> <radius> <function>
schedule on_area_loaded add tickingarea <name> <function>
```

## 2. 网易官方命令列表（文档版）

以下是网易开发者官网列出的命令（按用途分组）。这些命令在网易版里有明确文档依据。

| 类别 | 命令 |
|---|---|
| 实体/玩家 | `clear` `clearspawnpoint` `clone` `effect` `enchant` `event` `execute` `gamemode` `give` `kill` `me` `msg`/`tell`/`w` `replaceitem` `ride` `say` `spawnpoint` `spreadplayers` `summon` `tag` `teleport`/`tp` `tellraw` `testfor` `xp` |
| 方块/世界 | `difficulty` `fill` `gamerule` `locate` `setblock` `setworldspawn` `structure` `tickingarea` `time` `toggledownfall` `weather` |
| 逻辑/计分板 | `execute` `function` `reload` `schedule` `scoreboard` `testforblock` `testforblocks` |
| 表现 | `camerashake` `music` `particle` `playanimation` `playsound` `stopsound` `title` |
| 服务器 | `help` `kick` `list` `mobevent` |
| 明确未实装 | `fog`（文档标注“1.16.100 加入，当前中国版版本尚未实装”） |

> `msg`/`tell`/`w` 是同一命令的别名；`teleport`/`tp` 同理。

## 3. 样本中实际出现、但文档未列的命令

对 12 个文件、18,945 条非空命令的统计中，以下命令被真实地图使用：

| 命令 | 次数 | 结论 |
|---|---:|---|
| `titleraw` | 80 | 可用（JSON 标题） |
| `camerashake` | 5 | 可用（文档也列了） |
| `damage` | 2 | 可用（1.19.80+ 的 Bedrock 命令，样本已用） |
| `execute`（旧语法） | 677 | **不应用于 1.21.130 新图**；见第 5 节 |
| `execute`（新语法） | 11,019 | 可用 |
| `hud` | 数据化合集少量使用 | Bedrock 1.21 稳定版有文档，但网易官方列表未列；先 `/help hud` 验证，见 `dataization-rpg.md` |

## 4. 不要在网易 1.21.130 中使用的命令

以下命令**未出现在网易官方列表**，也未在 18,945 条真实命令中出现。除 `fog` 有“未实装”明确说明外，其余属于“未验证”，默认不要用于网易地图：

| 命令 | 说明/替代 |
|---|---|
| `camera` | 未验证；用 `camerashake` + `tp ... facing` + `title` 做镜头表现 |
| `inputpermission` | 未验证；用 `tp`/`effect`/`title` 做过场，或行为包 |
| `dialogue` | 未验证；网易 NPC 对话走编辑器/NPC 组件，不用该命令 |
| `loot` | 未验证；用 `give`/`replaceitem`/`clear` |
| `place` | 未验证；用 `structure load` |
| `recipe` | 未验证；用 `give` 或行为包配方 |
| `scriptevent` | 未验证；网易用 ModSDK/行为包事件 |
| `fog` | 官方文档标注“当前中国版尚未实装” |

以及基岩版本身就没有的 Java 命令：`data`、`item`、`attribute`、`bossbar`、`team`、`forceload`、`advancement`、`worldborder`、`spectate`、`datapack`、`fillbiome`。

> 结论：**`schedule` 保留；`camera`/`inputpermission`/`dialogue`/`loot`/`place`/`recipe`/`scriptevent`/`fog` 从技能主文档移除，只在“未验证”表里保留替代方案。**

## 5. 旧语法：导入图的重灾区

样本里仍有 677 条旧 `execute`：

```mcfunction
# 旧语法（1.19.50 前；网易 1.21.130 新图不要用）
execute @a[scores={MTC=41}] ~ ~ ~ tag @s add 互传机制
execute @a[tag=准备] ~ ~ ~ setblock ~ ~ ~ redstone_block

# 新语法
execute as @a[scores={MTC=41}] at @s run tag @s add 互传机制
execute as @a[tag=准备] at @s run setblock ~ ~ ~ redstone_block
```

还有旧式方块 data 参数：

```mcfunction
# 旧：fill ... <block> <data> replace ...
fill 0 -59 0 9 -59 9 air 0 replace redstone_block

# 新：用方块状态；空气不需要 data
fill 0 -59 0 9 -59 9 air replace redstone_block
```

处理导入图时：

- 旧 `execute`、`setblock`、`fill` 先手工升级，再导入新图。
- 手写新图一律用新语法；技能 linter 会把旧 `execute` 标为 error。
- 旧图的 `~~~`、`~19~~` 紧凑坐标在旧解析器里可接受；新写法建议保留空格，避免歧义。

## 6. 样本中的网易地图惯用法

这些是 12 个真实地图里反复出现的模式，已写进 `chain-patterns.md` 和 `netease-corpus-patterns.md`：

- **菜单**：`title`/`titleraw actionbar` + 计分板状态（`雪球菜单`、`MTC`、`uid`）+ `hasitem`/`rx` 视角选择。
- **常加载**：`tickingarea add ~~~ ~100~~100 §k指令区`（名字里带 `§k` 混淆）。
- **结构**：`structure save <name> ~~1~ ~~1~ disk` / `structure load <name> <pos>`。
- **检测**：`testfor`、`testforblocks`、`execute if block` 混用。
- **表现**：`playanimation`、`camerashake`、`event`、`damage`、`spreadplayers`。
- **状态**：每个系统一个计分板目标（`MTC`、`uid`、`雪球菜单`、`攻击`、`经验计算`），假玩家做全局状态。

## 7. 版本边界的使用方式

- 写新命令前先问：**网易官方列表里有吗？** 没有就查样本/实测，仍没有就换替代方案。
- 不要把国际版 1.21.x 的新命令默认当成网易可用；`camera`、`inputpermission` 就是典型。
- `schedule`、`function` 有官方依据，可以用；但依赖行为包函数，服务器没开函数时不要用。
- `fog` 官方明确“尚未实装”，不要用。
- 版本继续升级后，以游戏内 `/help` 和网易开发者文档为准，本表只是 1.21.130 的快照。

## 8. 来源

- [网易开发者官网 — 命令列表及概述](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/10-addon教程/第04章：指令系统，你的创作管家/课程04.命令列表及概述.html)
- [Minecraft Wiki — Commands/schedule](https://minecraft.wiki/w/Commands/schedule)（Bedrock 语法）
