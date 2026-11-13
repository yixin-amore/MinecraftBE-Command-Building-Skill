# 文本、标题、音效与实体表现（网易 1.21.130）

> 网易版可用：`title`、`titleraw`、`tellraw`、`playsound`、`particle`、`camerashake`、`playanimation`、`event`、`damage`、`spreadplayers`。
> 不要用：`camera`、`inputpermission`、`fog`（网易官方标注尚未实装）。

## 1. 基岩版文本模型

基岩版的 JSON 文本是一个 `rawtext` 数组：

```json
{"rawtext":[
  {"text":"§aHello "},
  {"selector":"@p"},
  {"text":"!"}
]}
```

规则：

- 根对象必须有 `rawtext`，值是数组。
- 每个对象一个内容标签：`text`、`translate`、`selector`、`score`（同时出现时按 `translate` → `text` → `selector` → `score` 取第一个）。
- 数组按顺序拼接；换行用 `\n`。
- **格式只用 `§` 代码**；Java 的 `color`、`bold`、`clickEvent`、`hoverEvent` 在基岩版文本里不可用。
- `translate` 用 `with` 传参，占位符是 `%%s` / `%%1`（两个百分号）。
- `score` 可以显示分数：`{"score":{"name":"fb_count","objective":"arena"}}`；`"*"` 表示读消息的玩家自己。
- `selector` 显示被选中实体的名字。

### `§` 格式代码

| 代码 | 颜色/样式 | 代码 | 颜色/样式 |
|---|---|---|---|
| `§0` | 黑 | `§a` | 绿 |
| `§1` | 深蓝 | `§b` | 青 |
| `§2` | 深绿 | `§c` | 红 |
| `§3` | 深青 | `§d` | 浅紫 |
| `§4` | 深红 | `§e` | 黄 |
| `§5` | 深紫 | `§f` | 白 |
| `§6` | 金 | `§k` | 随机 |
| `§7` | 灰 | `§l` | 粗体 |
| `§8` | 深灰 | `§m` | 删除线 |
| `§9` | 蓝 | `§n` | 下划线 |
| `§o` | 斜体 | `§r` | 重置 |

## 2. tellraw

```mcfunction
tellraw <player> <rawtext JSON>
```

```mcfunction
tellraw @a {"rawtext":[{"text":"§aWelcome!"}]}

tellraw @a {"rawtext":[
  {"text":"§7"},
  {"selector":"@p"},
  {"text":" §fjoined the game"}
]}

tellraw @a {"rawtext":[{"text":"§eWave: "},{"score":{"name":"fb_wave","objective":"arena"}}]}
```

**坑**：

- 必须用 `{"rawtext":[...]}`；`{"text":"..."}` 直接作为根在基岩版不可靠。
- 颜色写进文本：`§c红字`，不要写 `"color":"red"`。
- 双引号要转义；先用 `/tellraw` 在聊天栏测试，再放进命令方块。
- 很长的 JSON 注意 32,500 字符上限。

## 3. title / titleraw

```mcfunction
title <player> <clear|reset>
title <player> <title|subtitle|actionbar> <plain text>
title <player> times <fadeIn> <stay> <fadeOut>

titleraw <player> <clear|reset>
titleraw <player> <title|subtitle|actionbar> <rawtext JSON>
titleraw <player> times <fadeIn> <stay> <fadeOut>
```

```mcfunction
title @a title §6Round 1
title @a subtitle §7Survive 60 seconds
title @a actionbar §e3
title @a times 10 60 20

titleraw @a title {"rawtext":[{"text":"§lCHAPTER I"}]}
titleraw @a actionbar {"rawtext":[{"text":"§e"},{"score":{"name":"fb_count","objective":"arena"}}]}
```

- `title` 是纯文本 + `§`；`titleraw` 是 JSON。
- `times` 单位 tick：`10 70 20` 是默认（淡入 0.5s / 停留 3.5s / 淡出 1s）。
- `actionbar` 只有一行，适合持续状态；`title` 会盖住屏幕中央，不要每 tick 刷。
- 同一玩家同时只能有一个 title；新 title 会替换旧的。
- 网易地图大量用 `titleraw actionbar` 做菜单（见 `netease-corpus-patterns.md`）。

### 用 title 做倒计时

```mcfunction
titleraw @a actionbar {"rawtext":[{"text":"§eTime: "},{"score":{"name":"fb_count","objective":"arena"}},{"text":"s"}]}
```

每秒执行一次即可；不要每 tick 执行（会闪）。

### 用 title 做 Boss 血条（替身）

没有 `bossbar`（网易也没有），用 actionbar 或 sidebar：

```mcfunction
titleraw @a actionbar {"rawtext":[{"text":"§cBoss "},{"score":{"name":"fb_bosshp","objective":"boss"}},{"text":" / 100"}]}
```

或：

```mcfunction
scoreboard objectives setdisplay sidebar boss
```

## 4. 音效

```mcfunction
playsound <sound> [player] [x y z] [volume] [pitch] [minimumVolume]
stopsound <player> [sound]
```

```mcfunction
playsound random.orb @s
playsound random.levelup @a 0 64 0 1 1
playsound mob.wither.spawn @a ~ ~ ~ 0.5 1
stopsound @a music.game
```

- 不给坐标时在玩家处播放；给坐标时所有目标听到同一位置的声音。
- `volume` 0..1；`pitch` 0..256；`minimumVolume` 0..1。
- 音效名不带 `minecraft:`；高频音效要加冷却。

## 5. 粒子

```mcfunction
particle <effect> [x y z]
```

```mcfunction
particle flame ~ ~1 ~
particle heart ~ ~1 ~
particle end_rod ~ ~1 ~
```

- 基岩版**没有** `xd yd zd speed count`；只有效果名和位置。
- 要“爆发”多个粒子：多条命令、`execute as @e[...]` fork、或每 tick 少量发射。

## 6. 镜头震动 camerashake

```mcfunction
camerashake add <player> <intensity> <seconds> [positional|rotational]
camerashake stop [player]
```

```mcfunction
camerashake add @a[scores={镰刀=1}] 0.25 0.2 rotational
camerashake stop @a
```

- 这是网易 1.21.130 **可用**的镜头表现；`camera` 命令本身未验证，不要混用。
- 持续过场用 `tp ... facing` + `title` + `camerashake`，不要用 `camera set`。

## 7. 实体动画 playanimation

```mcfunction
playanimation <entity> <animation> [nextState] [blendOutTime] [stopExpression] [controller]
```

```mcfunction
playanimation @e[name=实体_鹿与管,type=armor_stand] animation.ghast.scale default 100
playanimation @e[type=npc] animation.creeper.swelling move 100000
```

- 网易地图常用 NPC/盔甲架做模型，`playanimation` 播放原版动画。
- 动画名、控制器名以资源包/实体定义为准；先用 `/playanimation` 补全测试。

### FMBE / MBE 显示实体

`playanimation` 更高级的用法是用 Molang 改变原版动画的骨骼变量，把狐狸主手物品/盔甲架副手物品伪装成方块：

- FMBE：狐狸 + 主手物品 + 8 条 `playanimation`（1 条初始化 + 7 条变量/姿态；第一条控制器 `controller.animation.fox.move`）。
- MBE：盔甲架 + 副手物品 + `animation.armor_stand.entertain_pose`。
- 前置：成年狐狸/盔甲架、`replaceitem`、`tag`、隐身/抗性/消音、`tickingarea`、`structure save/load`。
- 变量：`v.xpos/ypos/zpos` 是 1/16 格，`v.xrot/yrot/zrot` 是角度，`v.scale/xzscale/yscale` 是缩放。
- 一实体一显示；不能当方块检测；注意性能与狐狸 AI/声音。

完整命令链、变量表、MBE 尺寸/旋转、社区变体与例子见 `references/fmbe-mbe.md`。

## 8. 实体事件 event / 伤害 damage

```mcfunction
event entity <target> <eventName>
damage <target> <amount> <cause> [entity <damager>]
```

```mcfunction
event entity @e[type=creeper] minecraft:stop_exploding
damage @s 4 entity_attack
damage @e[type=ender_crystal] 0
```

- `event` 触发实体定义里的事件；事件名以行为包为准。
- `damage` 在样本中已使用；`amount` 是整数，实际伤害受护甲/抗性修正。

## 9. spreadplayers

```mcfunction
spreadplayers <x> <z> <spreadDistance> <maxRange> <targets>
```

```mcfunction
spreadplayers -5025 -4985 3 5 @e[type=armor_stand,name=矿方包,r=100]
```

- 常用于把实体随机撒到区域内；`maxRange` 是相对中心的最大半径。

## 10. 设计建议

- **文本**：颜色/前缀集中在一个函数里，避免每条命令重复 `§`。
- **actionbar** 适合持续状态；**title** 适合大事件；不要每 tick 发 title。
- **音效**：关键事件给独特音效，普通反馈低音量；多人时 `@a` 会同时播。
- **粒子**：每 tick 全玩家大量粒子会掉帧；用低频 + 小范围。
- **镜头**：网易没有可靠 `camera`；用 `camerashake` + `tp ... facing` + 字幕。
- **过场结束**：恢复玩家状态、清 title、停 camerashake。

## 11. 常见错误

| 写法 | 问题 | 改成 |
|---|---|---|
| `tellraw @a {"text":"Hi"}` | 基岩版根不是 `text` | `{"rawtext":[{"text":"Hi"}]}` |
| `tellraw @a {"rawtext":[{"text":"Hi","color":"red"}]}` | 基岩版不认 `color` | `{"text":"§cHi"}` |
| `title @a title {"text":"Hi"}` | `title` 是纯文本 | `title @a title Hi` 或 `titleraw` |
| `particle flame ~ ~ ~ 0.5 0.5 0.5 0.1 20` | 基岩版没有这些参数 | `particle flame ~ ~ ~` |
| `camera @a set ...` | 网易未验证 | `camerashake` + `tp ... facing` |
| `fog @a ...` | 网易官方标注未实装 | 用资源包/行为包或忽略 |
| `playanimation ...` 动画名错 | 实体没有该动画 | 用 `/playanimation` 补全或查实体定义 |

## 12. 参考

- [Text component format — Minecraft Wiki](https://minecraft.wiki/w/Text_component_format)（Bedrock 的 `rawtext`、`score`、`selector`、`%%s`）
- [Commands/title — Minecraft Wiki](https://minecraft.wiki/w/Commands/title)
- [Commands/tellraw — Minecraft Wiki](https://minecraft.wiki/w/Commands/tellraw)
- [网易开发者官网 — 命令列表及概述](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/10-addon教程/第04章：指令系统，你的创作管家/课程04.命令列表及概述.html)
