# 20 · 语料蒸馏：这批资料里真正反复出现的模式
> 由 `scripts/analyze_corpus.py` 从本地语料自动生成；只统计模式，不复制整篇原文。
## 规模
| 类别 | 记录 |
|---|---:|
| `data` | 534 |
| `weapon` | 299 |
| `ui` | 233 |
| `teleport` | 184 |
| `economy` | 124 |
| `other` | 94 |
| `minigame` | 40 |
| `reference` | 40 |
| `math` | 36 |
| `protection` | 26 |
| `fmbe` | 18 |
| `building` | 16 |
| `nxs` | 2 |

## 高频命令头
| 命令 | 次数 |
|---|---:|
| `execute` | 37344 |
| `fill` | 32851 |
| `setblock` | 20390 |
| `scoreboard` | 13559 |
| `tag` | 2939 |
| `minecraft` | 2301 |
| `command` | 1203 |
| `give` | 1075 |
| `animation` | 1035 |
| `mob` | 994 |
| `title` | 992 |
| `replaceitem` | 897 |
| `rotated` | 720 |
| `effect` | 683 |
| `kill` | 593 |
| `tp` | 529 |
| `tellraw` | 403 |
| `bundle_dye_` | 392 |
| `structure` | 368 |
| `clear` | 360 |

## 语料里的语法断层
这些资料横跨多个版本，**不能直接照抄**：
- **新 `execute as/at/... run` 语法**：32258 行；DSL 里必须显式建模，不直接拼字符串。
- **`scoreboard`**：27106 行；DSL 里必须显式建模，不直接拼字符串。
- **`tag=` 选择器**：25225 行；DSL 里必须显式建模，不直接拼字符串。
- **旧半径/坐标选择器**：11186 行；DSL 里必须显式建模，不直接拼字符串。
- **旧 `execute @a ~ ~ ~` 语法**：6917 行；DSL 里必须显式建模，不直接拼字符串。
- **`hasitem=` 选择器**：6863 行；DSL 里必须显式建模，不直接拼字符串。
- **`particle`**：5602 行；DSL 里必须显式建模，不直接拼字符串。
- **`titleraw/tellraw`**：5055 行；DSL 里必须显式建模，不直接拼字符串。
- **`replaceitem`**：1427 行；DSL 里必须显式建模，不直接拼字符串。
- **`structure`**：1371 行；DSL 里必须显式建模，不直接拼字符串。
- **`summon`**：1221 行；DSL 里必须显式建模，不直接拼字符串。
- **FMBE/展示体**：510 行；DSL 里必须显式建模，不直接拼字符串。
- **`playanimation`**：418 行；DSL 里必须显式建模，不直接拼字符串。
- **`testfor`**：240 行；DSL 里必须显式建模，不直接拼字符串。

## 按任务的检索入口
| 任务 | 先检索 | 再用 |
|---|---|---|
| 武器/拔刀剑/鱼竿枪 | `weapon` | `dsl.py` + `build_cbworld.py` + CHelper |
| 数据化/属性/T显 | `data` | `cbc.py` + score actions |
| 菜单/公告/进度条 | `ui` | `dsl` Context + `titleraw/tellraw` |
| 商店/开箱/经济 | `economy` | `inventory` / `scoreboard` / `structure` |
| 传送/圆规/二分 | `teleport` / `math` | `positioned/rotated/facing` |
| FMBE/展示体 | `fmbe` | `auxiliary/fmbe-nxs.md` + `build_fmbe.py` |
| 防护/管理 | `protection` | `scoreboard`/`tag` 审计 + 回读 |

## 各类代表命令片段
### `building`
- `setblock ~37 ~14 ~51 yellow_glazed_terracotta 0`
- `setblock ~39 ~14 ~9 yellow_glazed_terracotta 0`
- `setblock ~38 ~14 ~9 lime_glazed_terracotta 0`
### `data`
- `scoreboard objectives add 雪球菜单 dummy "菜单"`
- `scoreboard objectives add menu_bak dummy "菜单备份"`
- `scoreboard objectives add act dummy "动画效果"`
### `economy`
- `scoreboard objectives remove 信息栏`
- `scoreboard objectives add 信息栏 dummy "§l§4ᴍ§cɪ§6ɴ§eᴇ§aᴄ§bʀ§3ᴀ§dғ§uᴛ"`
- `scoreboard objectives setdisplay sidebar 信息栏 ascending`
### `fmbe`
- `replaceitem entity @e[name=线] slot.weapon.mainhand 0 lime_concrete 1 0`
- `execute as @e[tag=连线1] at @s run playanimation @s animation.player.attack.positions none 0 "t.xpos1=q.position(0);t.ypos1=q.position(1);t.zpos1=q.position(2);" Urnalong`
- `execute as @e[name=连线2] at @s run playanimation @s animation.player.attack.positions none 0 "t.xpos2=q.position(0);t.ypos2=q.position(1);t.zpos2=q.position(2);" Urnalong`
### `math`
- `execute as @e[name=下] at @s positioned ~~-500~ run clone ~~~~~~~~-1~`
- `execute as @e[name=下] at @s positioned ~~-500~ run setblock ~~~ air`
- `execute as @e[name=下] at @s positioned ~~-500~ run kill`
### `minigame`
- `scoreboard objectives add 金币 dummy`
- `scoreboard objectives add 一键回收 dummy`
- `scoreboard objectives add 号码 dummy`
### `nxs`
- `execute`
- `execute as@e[type=ender_crystal]at@s run tp~~~~.5~.5`
- `execute as@e[type=ender_crystal,rxm=89]at@s run tp~~~~ -90`
### `other`
- `execute as @a at @s anchored eyes positioned ~ ~-1.2 ~ if entity @s[r=0.2] at @e[type=item,rx=0,rxm=0,rym=0,name="钻石"] align xyz if block ~1~~ diamond_ore run setblock ~1~~ air destroy`
- `execute as @a at @s anchored eyes positioned ~ ~-1.2 ~ if entity @s[r=0.2] at @e[type=item,rx=0,rxm=0,rym=0,name="钻石"] align xyz if block ~-1~~ diamond_ore run setblock ~-1~~ air destroy`
- `execute as @a at @s anchored eyes positioned ~ ~-1.2 ~ if entity @s[r=0.2] at @e[type=item,rx=0,rxm=0,rym=0,name="钻石"] align xyz if block ~~1~ diamond_ore run setblock ~~1~ air destroy`
### `protection`
- `scoreboard objectives add 开箱 dummy`
- `scoreboard objectives add 箱子种类 dummy`
- `scoreboard objectives add 摸索次数 dummy`
### `reference`
- `execute as @a[tag=!sz,hasitem={item=iron_block,location=slot.weapon.mainhand},rxm=88] at @s if entity @e[r=2] run tag @s add sz`
- `execute as @a[tag=sz,hasitem={item=gold_block,location=slot.weapon.mainhand}] at @s run execute as @e[name=世界] at @s positioned ^^1.4^6 run damage @e[r=5,name=!世界,tag=!sz] 8 entity_attack`
- `execute as @a[tag=sz,hasitem={item=gold_block,location=slot.weapon.mainhand}] at @s run execute as @e[name=世界] at @s if entity @e[r=5,tag=!sz,name=世界] positioned ^^1.4^2 run particle minecraft:dragon_destroy_block ^^^4`
### `teleport`
- `playsound <sound> <source> <targets> [x] [y] [z] [volume] [pitch] [minVolume]`
- `playsound <sound: string> <source: string> [player: target] [x: float] [y: float] [z: float] [volume: float] [pitch: float]`
- `playsound minecraft:entity.cow.ambient master @a ~ ~ ~ 2.0 1.2`
### `ui`
- `scoreboard objectives remove 信息栏`
- `scoreboard objectives add 信息栏 dummy "§l§42§c0§62§e6§a年§b祝§3大§d家§u新年快乐"`
- `scoreboard objectives setdisplay sidebar 信息栏 ascending`
### `weapon`
- `scoreboard objectives add 愤怒 dummy`
- `scoreboard objectives add 跳跃 dummy`
- `replaceitem entity @a[tag=重锤] slot.hotbar 0 keep mace 1 5000 {"item_lock":{"mode":"lock_in_slot"}}`

## 结论
- 这里不是“让模型背 1,600 篇”；是让 DSL 提供结构，语料提供**模式与命名**。
- 旧语法资料只能作为意图参考；生成前用 CHelper 复核，再进 `cbc.py`。
- FMBE/NXS 仍缺类型层：模型部件、绑定、动画、命中核心，见 `auxiliary/fmbe-nxs.md`。
