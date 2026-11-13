# 基岩版命令参考（命令方块常用）

> 只列命令方块/地图逻辑最常用的命令。签名以 **网易 1.21.130（Bedrock 1.21.130）** 为准；`<...>` 必填，`[...]` 可选，`(a|b)` 多选一。
> 命令方块里不需要写开头的 `/`。
>
> **目标：网易我的世界 1.21.130（协议 898）**。`schedule`/`function` 有网易官方命令列表依据；`camera`/`inputpermission`/`dialogue`/`loot`/`place`/`recipe`/`scriptevent`/`fog` 未验证/未实装，见 `netease-1.21.130.md`。

## 0. 先记住这些“不存在”

| Java 有 | 基岩版 |
|---|---|
| `data get/modify/remove` | ❌ 没有；状态写进计分板/tag |
| `execute store ...` | ❌ 没有 |
| `execute ... detect` | ❌ 没有；用 `execute if block` |
| `execute ... runasync` | ❌ 没有 |
| `item replace` | `replaceitem` |
| `attribute` | ❌ 没有；用 `effect` 或行为包 |
| `bossbar` | ❌ 没有；用 `titleraw actionbar` / sidebar |
| `team` | ❌ 没有；用 tag + 计分板 |
| `forceload` | `tickingarea` |
| `advancement` / `predicate` / `loot table`（数据包） | ❌ 命令侧不支持 |
| `nbt=` 选择器 / `summon ... {}` | ❌ 没有 NBT |
| `[facing=east]` 方块状态 | `["minecraft:cardinal_direction"="east"]` |
| `give @s diamond_sword[enchantments={...}]` | `give` + `enchant`，或 components JSON（版本相关） |
| `title @a title {"text":"..."}` | `title` 纯文本 + `§`，或 `titleraw` + `rawtext` |
| `@e[distance=..5]` / `limit=` / `sort=` | `@e[r=5]` / `c=` |
| `@a[team=red]` | 无 team 参数；用 tag |
| `scoreboard objectives add deaths deathCount` | 只有 `dummy`；死亡要外部事件 |
| `scoreboard objectives modify` | ❌ 没有 |
| `scoreboard players get/enable` | ❌ 没有；用 `test` / `execute if score` |

---

## 1. 方块与世界

### `setblock`

```mcfunction
setblock <x y z> <block> [blockStates] [destroy|keep|replace]
```

```mcfunction
setblock 10 64 10 stone
setblock 10 64 10 chest ["minecraft:cardinal_direction"="east"]
setblock 10 64 10 air destroy
```

- `blockStates` 是 `["state"="value",...]`，键值都要引号。
- 默认 `replace`。
- 不能用来配置命令方块（没有 NBT）。

### `fill`

```mcfunction
fill <from x y z> <to x y z> <block> [blockStates] [destroy|hollow|keep|outline|replace]
fill <from> <to> <block> [blockStates] replace [replaceBlock] [replaceBlockStates]
```

```mcfunction
fill 0 64 0 9 64 9 stone
fill 0 64 0 9 64 9 glass hollow
fill 0 64 0 9 64 9 stone replace dirt
```

- 范围太大会卡；建议单次 ≤32,768 方块并分块。
- `hollow`/`outline` 只作用于外壳。
- 方块状态写法同 `setblock`。

### `clone`

```mcfunction
clone <begin x y z> <end x y z> <destination x y z> [replace|masked] [force|move|normal]
clone <begin> <end> <destination> filtered <force|move|normal> <block> [blockStates]
```

```mcfunction
clone 0 64 0 9 70 9 100 64 0
clone 0 64 0 9 64 9 100 64 0 masked
```

- 上限 655,360 方块。
- `normal` 模式下源和目标重叠会失败；用 `force`。
- 可复制方块实体数据（包括命令方块设置），可用来做模板；先在目标版本验证。

### `structure`

```mcfunction
structure save <name> <from x y z> <to x y z> [includeEntities] [disk|memory] [includeBlocks]
structure load <name> <to x y z> [rotation] [mirror] [includeEntities] [includeBlocks] [waterlogged] [integrity] [seed]
structure delete <name>
```

```mcfunction
structure save arena 0 64 0 20 80 20 true disk true
structure load arena 100 64 0 0_degrees none true true false 100
```

- 单次 ≤ 64×384×64。
- `memory` 模式重进世界会丢；要持久化用 `disk`。
- 旋转：`0_degrees/90_degrees/180_degrees/270_degrees`；镜像：`none/x/z/xz`。

### `testforblock` / `testforblocks`

```mcfunction
testforblock <x y z> <block> [blockStates]
testforblocks <begin x y z> <end x y z> <destination x y z> [all|masked]
```

```mcfunction
testforblock 10 64 10 gold_block
testforblocks 0 64 0 3 66 3 100 64 0 masked
```

- 新代码优先用 `execute if block` / `execute if blocks`，可组合、可嵌套。

### `tickingarea`

```mcfunction
tickingarea add <from x y z> <to x y z> [name] [preload]
tickingarea add circle <center x y z> <radius> [name] [preload]
tickingarea remove <name|x y z>
tickingarea remove_all
tickingarea list [all-dimensions]
tickingarea preload <name|x y z> [true|false]
```

```mcfunction
tickingarea add 0 0 0 31 0 31 arena_area true
tickingarea add circle 100 64 100 2 spawn_area
```

- 最多 10 个；矩形总计 ≤100 区块；圆半径 0..4 区块。
- 远处机关必须加，否则链不跑。
- `preload` 让区域在世界加载时优先加载。

---

## 2. 实体与玩家

### `summon`

```mcfunction
summon <entity> [spawnPos x y z] [yRot] [xRot] [spawnEvent] [nameTag]
summon <entity> <nameTag> [spawnPos x y z]
summon <entity> [spawnPos] facing <x y z|entity> [spawnEvent] [nameTag]
```

```mcfunction
summon zombie 10 64 10
summon zombie wave_mob 10 64 10
summon armor_stand marker 10 64 10
```

- 不能带 NBT；需要 tag 就在生成后 `tag ... add`。
- `nameTag` 是显示名，不是 tag；选择器 `name=` 匹配它。

### `teleport` / `tp`

```mcfunction
teleport <destination x y z> [checkForBlocks]
teleport <victim> <destination x y z> [yRot] [xRot] [checkForBlocks]
teleport <victim> <destination x y z> facing <x y z|entity> [checkForBlocks]
teleport <victim> <destination entity> [checkForBlocks]
```

```mcfunction
tp @a 0 64 0
tp @s 0 64 0 90 0
tp @a ~ ~ ~ facing entity @e[type=armor_stand,c=1]
```

- `checkForBlocks true` 会在目标位置有方块时拒绝传送。
- 基岩版 `tp` 支持 `facing`，做镜头/朝向很方便。

### `spreadplayers`

```mcfunction
spreadplayers <x> <z> <spreadDistance> <maxRange> <targets>
```

```mcfunction
spreadplayers -5025 -4985 3 5 @e[type=armor_stand,name=矿方包,r=100]
```

- 把实体随机撒到以 `(x,z)` 为中心、最大半径 `maxRange` 的区域内；`spreadDistance` 是实体间最小间距。
- 网易样本常用它摆放随机矿点/物资。

### `kill`

```mcfunction
kill [target]
```

```mcfunction
kill @e[type=zombie,tag=wave_mob]
kill @s
```

### `effect`

```mcfunction
effect <player> clear [effect]
effect <player> <effect> [seconds] [amplifier] [hideParticles]
effect <player> <effect> infinite [amplifier] [hideParticles]
```

```mcfunction
effect @s speed 10 2 true
effect @a regeneration infinite 0 true
effect @s clear
```

- 效果名不带 `minecraft:`；基岩版用 `village_hero` 而不是 `hero_of_the_village`。
- `seconds` 是秒，不是 tick；`infinite` 表示永久。

### `damage`

```mcfunction
damage <target> <amount> <cause> [entity <damager>]
```

```mcfunction
damage @s 4 entity_attack
damage @e[type=zombie] 6 fire
damage @s 2 entity_attack entity @p
```

- `amount` 是整数。
- 常用 `cause`：`entity_attack`, `projectile`, `fire`, `fire_tick`, `lava`, `fall`, `drowning`, `suffocation`, `magic`, `void`, `block_explosion`, `entity_explosion`, `lightning`, `anvil`, `contact`, `starve`, `freezing`, `sonic_boom`, `self_destruct`。
- 伤害会被护甲/抗性/创造模式等修正，不等于最终扣血。
- 已移除 `suicide`，改用 `self_destruct`。

### `tag`

```mcfunction
tag <entity> add <name>
tag <entity> remove <name>
tag <entity> list
```

```mcfunction
tag @s add ready
tag @a remove in_zone
tag @e[type=zombie] add wave_mob
```

- tag 是字符串，区分大小写；每实体最多 1024 个。
- 选择器 `tag=name` / `tag=!name` / `tag=`（无 tag）。

### `testfor`

```mcfunction
testfor <target>
```

```mcfunction
testfor @a[tag=ready]
testfor @e[type=zombie,r=10]
```

- 旧命令；新代码用 `execute if entity @a[tag=ready]`。

### `gamemode`

```mcfunction
gamemode <survival|creative|adventure|spectator|default|s|c|a|d> [player]
```

```mcfunction
gamemode adventure @a
gamemode s @s
```

### `xp`

```mcfunction
xp <amount> [player]
xp <amount>L [player]
```

```mcfunction
xp 10 @s
xp -5 @s
xp 3L @s
```

- 负数是扣经验。

### `clear`

```mcfunction
clear <player> [item] [data] [maxCount]
```

```mcfunction
clear @s
clear @s emerald
clear @s emerald 0 1
```

- 不带 item 清空整个背包。
- 只清除成功才返回成功；适合做“扣费成功才发货”的门。

### `give`

```mcfunction
give <player> <item> [amount] [data] [components]
```

```mcfunction
give @s bread 3
give @s diamond_sword
give @s fireworks 1 1
```

- 附魔优先用 `enchant`，避免 components 版本差异。
- `components` 是 JSON，形状随版本变化；先在目标版本用 `/give` 试。

### `replaceitem`

```mcfunction
replaceitem entity <target> <slotType> <slotId> <item> [amount] [data] [components]
replaceitem entity <target> <slotType> <slotId> <destroy|keep> <item> [amount] [data] [components]
replaceitem block <x y z> slot.container <slotId> <item> [amount] [data] [components]
```

```mcfunction
replaceitem entity @s slot.weapon.mainhand 0 diamond_sword
replaceitem entity @s slot.armor.head 0 iron_helmet
replaceitem entity @s slot.hotbar 0 bread 16
replaceitem block 10 64 10 slot.container 0 diamond 1
```

- 槽位：`slot.weapon.mainhand`, `slot.weapon.offhand`, `slot.armor.head/chest/legs/feet`, `slot.hotbar`, `slot.inventory`, `slot.enderchest`。
- 槽位类型 + 槽位编号（如 `slot.weapon.mainhand 0`）；不同版本的参数顺序以 `/help replaceitem` 为准。

### `enchant`

```mcfunction
enchant <player> <enchantment> [level]
```

```mcfunction
enchant @s sharpness 5
enchant @s protection 4
```

- 作用于主手物品；附魔名不带 `minecraft:`。

---

## 3. 逻辑与状态

- `execute` → 见 `execute-and-selectors.md`
- `scoreboard` → 见 `scoreboard-memory.md`
- `tag` / `testfor` → 见上

---

## 4. 文本、声音、镜头

### `tellraw`

```mcfunction
tellraw <player> <rawtext JSON>
```

```mcfunction
tellraw @a {"rawtext":[{"text":"§aHello"}]}
tellraw @a {"rawtext":[{"selector":"@p"},{"text":" §7joined"}]}
tellraw @a {"rawtext":[{"text":"Score: "},{"score":{"name":"@s","objective":"coins"}}]}
```

- 基岩版用 `rawtext` 数组；颜色用 `§` 代码。
- Java 的 `"color"`、`"clickEvent"`、`"hoverEvent"` 不要依赖。
- `"selector"` 会插入玩家名；`"score"` 在支持的版本可插入分数（先用 `/tellraw` 验证）。

### `title` / `titleraw`

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
title @a subtitle §7Get ready
title @a actionbar §e3
title @a times 10 60 20
titleraw @a title {"rawtext":[{"text":"§lChapter I"}]}
```

- `title` 是纯文本（可带 `§`）；`titleraw` 是 JSON。
- `times` 单位是 tick：10/70/20 是默认值。
- `actionbar` 可当 bossbar 用（只有一行）。
- 清屏用 `title @a clear`。
- 纯文本 `title` 的文本参数超过约 **512 字节**会静默失败；大面板用 `titleraw`，或拆成多条。

### `hud`

```mcfunction
hud <target> <hide|reset> [element]
```

元素：`health` `hunger` `armor` `status_effects` `item_text` `hotbar` `crosshair` `paperdoll` `air_bubbles` `horse_health` `progress_bar` `tooltips` `touch_controls` `all`。

```mcfunction
hud @a hide health
hud @a hide hunger
hud @a hide armor
hud @a hide status_effects
hud @a hide item_text
hud @s reset health
```

- 用于数据化 RPG 隐藏原版血条/饥饿/护甲，避免和自定义 T显/血条打架。
- 需要 cheats/游戏主管权限；隐藏后必须在重生/退出/关闭界面时 `reset`，否则玩家看不到原版 HUD。
- **网易 1.21.130 边界**：Bedrock 1.21 稳定版有文档，但网易官方命令列表未列；样本 `数据化四` 用了它。先在网易 `/help hud` 验证，不支持就不要隐藏原版血条。

### `playsound`

```mcfunction
playsound <sound> [player] [x y z] [volume] [pitch] [minimumVolume]
```

```mcfunction
playsound random.orb @s
playsound random.levelup @a 0 64 0 1 1
playsound mob.wither.spawn @a ~ ~ ~ 0.5 1
```

- 不给坐标时在玩家处播放。
- `volume` 0..1；`pitch` 0..256；`minimumVolume` 0..1。
- 音效名不带 `minecraft:`。

### `particle`

```mcfunction
particle <effect> [x y z]
```

```mcfunction
particle flame ~ ~1 ~
particle heart ~ ~1 ~
particle end_rod ~ ~ ~
```

- **基岩版只有效果名和位置**；没有 Java 的 `delta/speed/count`。
- 要多个粒子就多条命令，或用 `execute as @e ...` fork。
- 粒子名可用 `minecraft:` 前缀；具体列表用 `/particle` 补全。

### `camerashake`

```mcfunction
camerashake add <player> <intensity> <seconds> [positional|rotational]
camerashake stop [player]
```

```mcfunction
camerashake add @a[scores={镰刀=1}] 0.25 0.2 rotational
```

- 网易 1.21.130 可用；`camera` 命令未验证，不要混用。
- 过场用 `tp ... facing` + `title` + `camerashake`；结束 `camerashake stop @a`。

### `playanimation`

```mcfunction
playanimation <entity> <animation> [nextState] [blendOutTime] [stopExpression] [controller]
```

```mcfunction
playanimation @e[name=实体_鹿与管,type=armor_stand] animation.ghast.scale default 100
```

- 动画名来自实体定义/资源包；先用 `/playanimation` 补全。
- 常用于 NPC/盔甲架模型。

### `event`

```mcfunction
event entity <target> <eventName>
```

```mcfunction
event entity @e[type=creeper] minecraft:stop_exploding
```

- 触发实体定义中的事件；事件名以行为包为准。

---

## 5. 世界规则

### `time`

```mcfunction
time set <day|noon|night|midnight|sunrise|sunset|int>
time add <int>
time query <daytime|gametime|day>
```

```mcfunction
time set day
time set 0
time add 1000
time query daytime
```

### `weather`

```mcfunction
weather <clear|rain|thunder> [duration]
```

```mcfunction
weather clear 6000
weather rain 12000
toggledownfall
```

- `toggledownfall` 是网易官方列表内的旧式天气切换；新代码优先 `weather`。

### `gamerule`

```mcfunction
gamerule <rule> [value]
```

```mcfunction
gamerule commandblockoutput false
gamerule sendcommandfeedback false
gamerule dodaylightcycle false
gamerule domobspawning false
gamerule keepinventory true
gamerule showcoordinates true
gamerule maxcommandchainlength 65536
gamerule playerssleepingpercentage 0
```

常用规则（大小写敏感，以 `/gamerule` 补全为准）：

`commandblockoutput`, `commandblocksenabled`, `sendcommandfeedback`, `dodaylightcycle`, `domobspawning`, `dofiretick`, `doweathercycle`, `doentitydrops`, `domobloot`, `dotiledrops`, `doinsomnia`, `keepinventory`, `mobgriefing`, `naturalregeneration`, `showcoordinates`, `tntexplodes`, `randomtickspeed`, `maxcommandchainlength`, `spawnRadius`, `playerssleepingpercentage`, `doimmediaterespawn`, `showdeathmessages`, `pvp`, `drowningdamage`, `falldamage`, `firedamage`, `freezedamage`。

### `difficulty`

```mcfunction
difficulty <peaceful|easy|normal|hard>
```

### `setworldspawn` / `spawnpoint`

```mcfunction
setworldspawn [x y z] [rotation]
spawnpoint [player] [x y z]
```

```mcfunction
setworldspawn 0 64 0
spawnpoint @s 10 64 10
clearspawnpoint @a
```

- `clearspawnpoint @a` 清除玩家个人重生点，让玩家回到世界出生点。

---

## 6. 函数与调度

### `function`

```mcfunction
function <filepath>
```

```mcfunction
function arena/start
function shop/buy
```

- 路径相对行为包 `functions/`，**不带命名空间**：`functions/arena/start.mcfunction` → `function arena/start`。
- 函数里的命令按行顺序执行，同一 tick 内跑完；单次调用最多 10,000 条。
- 函数用执行者/执行位置：命令方块调用时继承命令方块的位置与执行者（`@s` 可能是方块，不是玩家）。

### `schedule`

```mcfunction
schedule delay add <function> <delayTicks> [append|replace]
schedule delay clear <function>
schedule clear <function>
schedule on_area_loaded add <from> <to> <function>
schedule on_area_loaded add circle <center> <radius> <function>
schedule on_area_loaded add tickingarea <name> <function>
schedule on_area_loaded clear function <function>
schedule on_area_loaded clear tickingarea <name> [function]
```

```mcfunction
schedule delay add arena/tick 20 append
schedule clear arena/tick
schedule on_area_loaded add 0 0 0 31 0 31 arena/on_load
```

- 基岩版没有 `schedule function <fn> 1t` 的 Java 写法。
- **网易 1.21.130 官方命令列表明确列出 `/schedule`**（“安排函数在特定的游戏刻后运行”），可以用；它调度的是 Add-on 函数。
- 延迟单位是 tick；`append` 可叠加多次，`replace` 替换。
- 常加载区域加载时触发函数，适合做区域初始化。

### `reload`

```mcfunction
reload
```

- 重载行为包函数；**新加的函数文件通常要重启世界**才可见，改已有文件可用 `reload`。

---

## 7. 网易 1.21.130 可用/不可用清单

**官方列表内、本文未展开**：`mobevent`、`music`、`ride`、`stopsound`、`toggledownfall`。语法用 `/help <命令>` 确认。

**未验证/未实装，不要用**：`camera`、`inputpermission`、`dialogue`、`loot`、`place`、`recipe`、`scriptevent`、`fog`。

**Java 有、基岩版没有**：`data`、`item`、`attribute`、`bossbar`、`team`、`forceload`、`advancement`、`worldborder`、`spectate`、`datapack`、`fillbiome`。

**`schedule` 与 `function`**：网易官方命令列表内有；`schedule` 调度的是 Add-on 函数，服务器未启用函数时不要依赖。详见 `netease-1.21.130.md`。

## 8. 参考

- [Minecraft Creator Docs — Commands](https://learn.microsoft.com/en-us/minecraft/creator/commands/)
- [Commands — Minecraft Wiki](https://minecraft.wiki/w/Commands)
- 各命令的 Wiki 页面（`Commands/setblock`、`Commands/fill`、`Commands/clone`、`Commands/structure`、`Commands/tickingarea`、`Commands/damage`、`Commands/title`、`Commands/scoreboard` 等）
