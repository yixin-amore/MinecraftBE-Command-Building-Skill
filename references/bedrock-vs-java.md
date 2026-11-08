# 基岩版 vs Java 版：命令与命令方块差异

> 用途：用户给的是 Java 语法时快速翻译；或判断某个需求在基岩版是否可行。
> 结论先行：**基岩版没有 NBT、没有 data、没有 execute store、计分板只有 dummy、没有 team/bossbar/attribute/item/forceload。**

## 1. 命令存在性

### Java 有、基岩版没有

| 命令 | 基岩版替代 |
|---|---|
| `data` | 无；状态写进计分板/tag/方块 |
| `execute store ...` | 无；用“每个实体给全局分数 +1”计数，或命令副作用 |
| `execute ... detect` | `execute if block` |
| `attribute` | `effect` 或行为包 |
| `bossbar` | `titleraw actionbar` / sidebar |
| `team` / `teammsg` | tag + 计分板 |
| `item` | `replaceitem` |
| `forceload` | `tickingarea` |
| `advancement` | 无（行为包脚本可做） |
| `fillbiome` | 无 |
| `worldborder` | 无 |
| `spectate` | 无 |
| `datapack` | 行为包（behavior pack） |
| `placefeature` / `place jigsaw` | 无 |
| `return` | 无 |
| `random` | `scoreboard players random` |
| `tick` | 无（用 `tick.json`） |
| `rotate` | 无（用 `tp ... facing`） |
| `waypoint` | 无 |
| `dialog`（Java 新命令） | `dialogue`（Bedrock 的 NPC 对话；网易未验证，别用） |

### 基岩版有、Java 没有（含网易可用性）

| 命令 | 用途 | 网易 1.21.130 |
|---|---|---|
| `tickingarea` | 常加载区域 | ✅ |
| `structure` | 保存/加载结构 | ✅ |
| `camerashake` | 镜头震动 | ✅ 官方列表 + 样本 |
| `camera` | 镜头控制 | ❌ 未验证，默认不用 |
| `inputpermission` | 输入权限 | ❌ 未验证 |
| `fog` | 雾效 | ❌ 官方标注未实装 |
| `dialogue` | NPC 对话 | ❌ 未验证 |
| `playanimation` | 实体动画 | ✅ 样本已用 |
| `mobevent` / `event` | 实体事件 | ✅ 官方列表 + 样本 |
| `scriptevent` | 脚本事件 | ❌ 未验证 |
| `testfor` / `testforblock` / `testforblocks` | 旧式测试（仍可用） | ✅ |
| `schedule`（不同语法） | 延迟/区域加载调度 | ✅ 官方列表 |
| `damage`（不同语法） | 造成伤害 | ✅ 样本已用 |

## 2. 语法差异速查

| 功能 | Java | 基岩版 |
|---|---|---|
| 方块状态 | `stone[facing=east]` | `stone ["minecraft:cardinal_direction"="east"]` |
| 文本 | `{"text":"Hi","color":"red"}` | `{"rawtext":[{"text":"§cHi"}]}` |
| 标题 | `title @a title {"text":"Hi"}` | `title @a title Hi` 或 `titleraw` |
| 选择器距离 | `distance=..5` | `r=5` |
| 选择器数量 | `limit=1,sort=nearest` | `c=1` / `c=-1` |
| 经验等级 | `level=10` | `lm=10,l=10` |
| 游戏模式 | `gamemode=creative` | `m=creative` |
| 队伍 | `team=red` | `tag=red` |
| 实体家族 | 无 | `family=monster` |
| 物品检测 | `if items` | `hasitem={item=diamond,quantity=5..}` |
| 权限检测 | 无 | `haspermission={movement=disabled}` |
| 分数比较 | `if score @s obj matches 1..` | 相同（Bedrock 也支持 `matches`） |
| 分数与常数比较 | `matches 6..` | 同样用 `matches 6..` |
| 执行条件 | `if data` / `if predicate` / `if biome` | `if block` / `if blocks` / `if entity` / `if score` |
| 存储结果 | `execute store result score ...` | 无 |
| 粒子 | `particle flame x y z dx dy dz speed count` | `particle flame x y z` |
| 函数调用 | `function ns:path` | `function path`（无命名空间） |
| 函数调度 | `schedule function ns:fn 1t` | `schedule delay add path 1` |
| 循环命令 | `return run` / 宏 | 无；用计分板状态机 |
| 数据包 | datapack | behavior pack |
| 命令方块延迟 | 无（只有 tick 链） | Delay in Ticks |
| 命令方块首 tick | 无 | Execute on First Tick |
| 红石时钟 | 20 Hz | 10 Hz（C-tick） |
| 命令方块条件 | 看身后方块成功次数 | 同样，但 Bedrock 成功次数可 >1 |

## 3. 计分板差异

| 项目 | Java | 基岩版 |
|---|---|---|
| 准则 | dummy、deathCount、health、xp、stat.* 等 | **只有 dummy** |
| 自动统计 | 有 | 无 |
| teams | 有 | 无 |
| `objectives modify` | 有 | 无（显示名只能在 add 时给） |
| `players get` | 有 | 无（用 `test` 或 `execute if score`） |
| `players enable` / trigger | 有 | 无（没有 trigger 准则） |
| `players random` | 无 | 有 |
| `players test` | 有（旧版） | 有 |
| 侧边栏 | 有 | 有（最多 15 行，`#` 假玩家不显示） |
| `belowname` | `below_name` | `belowname` |

## 4. execute 差异

Java：

```
execute as @a at @s if data entity @s {...} store result score @s obj run ...
```

基岩版：

```mcfunction
# 没有 data / store / predicate / items / biome / dimension / loaded
execute as @a at @s if block ~ ~-1 ~ stone run say on_stone
execute if score @s obj matches 1.. run say ok
```

子命令数量：Java 14 个，Bedrock 11 个（`align`, `anchored`, `as`, `at`, `facing`, `in`, `positioned`, `rotated`, `if/unless block/blocks/entity/score`, `run`）。

## 5. 物品与 NBT

| 需求 | Java | 基岩版 |
|---|---|---|
| 改背包物品 | `item replace` | `replaceitem` |
| 附魔 | `give ...[enchantments=...]` | `give` + `enchant` |
| 读箱子内容 | `data get block` | ❌ 读不到；用 hopper/比较器/计分板间接 |
| 改实体 NBT | `data merge entity` | ❌ 无 |
| 生成带 NBT 实体 | `summon ... {...}` | ❌ 无；生成后用命令/tag 补 |
| 自定义名称 | `CustomName` | `summon ... <nameTag>` / 命名牌 |
| 方块实体数据 | `data merge block` | ❌ 无；用方块状态或替换方块 |

## 6. 命令方块差异

| 项目 | Java | 基岩版 |
|---|---|---|
| 类型 | Impulse/Chain/Repeat | 同 |
| 条件 | Conditional 看身后成功次数 | 同，但成功次数可为任意整数 |
| 红石 | 每 tick 可响应 | 仅偶数 tick（C-tick），10 Hz |
| 延迟 | 无 UI；靠链 | **Delay in Ticks** |
| 首 tick | 无 | **Execute on First Tick** |
| 命名 | 铁砧命名 | Hover Note |
| 文本上限 | 32,500 | 32,500 |
| 配置复制 | 结构/克隆带 NBT | `clone` 可复制方块实体（先验证） |

## 7. 函数/包差异

| 项目 | Java | 基岩版 |
|---|---|---|
| 载体 | datapack | behavior pack |
| 目录 | `data/<ns>/functions/` | `functions/` |
| 调用 | `function ns:path` | `function path` |
| 每 tick | `#minecraft:tick` 标签 | `tick.json` |
| 单次上限 | 无硬性 10k（有命令限制） | **10,000 条** |
| 新函数加载 | `/reload` | 通常要重启世界 |
| 宏 | 支持 | 不支持 |
| 返回值 | `return` | 无 |

## 8. Java → Bedrock 翻译表

| Java | 基岩版 |
|---|---|
| `give @s diamond_sword[enchantments={levels:{sharpness:5}}]` | `give @s diamond_sword` + `enchant @s sharpness 5` |
| `execute if entity @a[distance=..5]` | `execute if entity @a[r=5]` |
| `execute as @a at @s run particle flame ~ ~1 ~ 0 0 0 0 1` | `execute as @a at @s run particle flame ~ ~1 ~` |
| `tellraw @a {"text":"Hi","color":"red"}` | `tellraw @a {"rawtext":[{"text":"§cHi"}]}` |
| `title @a title {"text":"Hi"}` | `title @a title Hi` |
| `scoreboard objectives add deaths deathCount` | ❌ 只有 `dummy`；用外部事件 |
| `team add red` | ❌ 用 `tag @s add red` |
| `bossbar add boss "Boss"` | ❌ 用 `titleraw actionbar` / sidebar |
| `forceload add 0 0 31 31` | `tickingarea add 0 0 0 31 0 31 area` |
| `data get entity @s SelectedItem` | ❌ 读不到；用 `hasitem` 选择器 |
| `execute store result score @s obj run ...` | ❌ 无；用计数/副作用 |
| `summon zombie ~ ~ ~ {IsBaby:1}` | `summon zombie ~ ~ ~`（无 NBT；用行为包变体/事件） |
| `setblock ~ ~ ~ stone[facing=east]` | `setblock ~ ~ ~ stone ["minecraft:cardinal_direction"="east"]` |

## 9. 判断需求是否可行

- 需要**读任意 NBT/容器内容** → 基岩版命令方块做不到，改用行为包脚本或间接检测。
- 需要**自动死亡/击杀/血量统计** → 命令方块做不到，改用行为包事件/脚本。
- 需要**每 tick 精确 20 次红石** → 用 Repeat + Always Active，不要用红石钟。
- 需要**复杂数组/字符串处理** → 用函数 + 计分板编码，或行为包脚本。
- 需要**自定义 UI/对话** → `titleraw`/`title`/`playanimation`；`dialogue`/`camera` 网易未验证，不要依赖。

## 10. 参考

- [Commands — Minecraft Wiki](https://minecraft.wiki/w/Commands)（Java/Bedrock 命令表）
- [Command Block — Minecraft Wiki](https://minecraft.wiki/w/Command_Block)
- [Target selectors — Minecraft Wiki](https://minecraft.wiki/w/Target_selectors)
- [Scoreboard — Minecraft Wiki](https://minecraft.wiki/w/Scoreboard)
- [Function (Bedrock Edition) — Minecraft Wiki](https://minecraft.wiki/w/Function_(Bedrock_Edition))
