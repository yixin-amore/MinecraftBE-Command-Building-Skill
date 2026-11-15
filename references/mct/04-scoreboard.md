# 计分板与系统骨架（11~26 章）

> 计分项、`operation` 与 clamp、三层分层、初始化链、主循环链、属性公式、UID、伤害、随机、经济、商店、背包、队伍、死亡、二分法。
**什么时候读**：搭一套新的数据化系统、需要某类系统的现成骨架。

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**（拆家前是第几章现在还是第几章）；跨文件的章号去主文件的
> 「章号 → 文件 对照表」查。这里的结论可能早于主文件的「⭐ 当前基线」——
> **冲突时以基线为准**。

---

## 11. 计分项

### 11.1 四种用法

| 用途           | 写法                                     | 例子                                                             |
| ------------ | -------------------------------------- | -------------------------------------------------------------- |
| **引擎准则**（免费） | `scoreboard objectives add <名> health` | `health` / `totalKillCount` / `deathCount` / `playerKillCount` |
| **自算数值**     | `... add <名> dummy`                    | `hp` `energy` `money`                                          |
| **布尔位**      | dummy + 显式置 0                          | `建档` `礼包` `已领取`                                                |
| **虚拟玩家常量**   | `scoreboard players set <名> #常量 10`    | `zero` `one` `five` `twenty` `hundred`                         |
| **计数器**      | 每刻 `add #tick sys 1`                   | 驱动定时器                                                          |

**能用引擎准则就别自己算。** 血量同步、击杀数、死亡数全部免费。

| 准则                | 范围   | 说明        |
| ----------------- | ---- | --------- |
| `health`          | 0–20 | 真实血量，引擎维护 |
| `playerKillCount` | 0–∞  | 玩家击杀数     |
| `totalKillCount`  | 0–∞  | 总击杀数（含生物） |
| `deathCount`      | 0–∞  | 死亡次数      |
| `dummy`           | 任意整数 | 自己算的一切    |

### 11.2 布尔位必须兜底

❗ `scores={x=0}` **匹配不到"从未赋值"的玩家**。建档时每个布尔位都要：

```
scoreboard players add @a 建档 0
scoreboard players add @a 礼包 0
```

这两条放主循环段首，每刻跑一次，成本极低，但少了它整套条件全失效。

### 11.3 命名约定

- 计分项用中文更直观：`金币` `等级` `经验` `已领取` `队伍`
- 内部临时值用 `_` 前缀：`_差值` `_临时`
- 系统常量用虚拟玩家：`zero` `one` `five` `ten` `twenty` `hundred`
- 一个功能一段链，段与段之间空一行位置

---

## 12. `operation` 与 clamp

```
scoreboard players operation <目标> <项> <运算符> <来源> <项>
```

| 运算符                      | 含义            |
| ------------------------ | ------------- |
| `=`                      | 赋值            |
| `+=` `-=` `*=` `/=` `%=` | 四则与取模         |
| `><`                     | 交换两边的值        |
| `<`                      | **取较小值**（min） |
| `>`                      | **取较大值**（max） |
|                          |               |

`<` 和 `>` 是 **MC 指令里唯一的 clamp 工具**：

```
scoreboard players operation @a energy < hundred sys    ← 能量封顶 100
scoreboard players operation @a atk_cd > zero sys       ← 冷却不落负
scoreboard players operation @a hp     > zero sys       ← 血量不落负
```

配套常量（初始化链里建）：

```
scoreboard players set zero sys 0
scoreboard players set one sys 1
scoreboard players set five sys 5
scoreboard players set ten sys 10
scoreboard players set twenty sys 20
scoreboard players set hundred sys 100
```

**除法是整除**，`/=` 会直接截断。要保留精度就先乘后除。

---

## 13. 三层分层与命名

```
数据层（只写分数） → 规则层（判定与结算） → 表现层（HUD / 音效 / 粒子）
```

**表现层绝不写数据。** 否则 HUD 一刷新就把逻辑改了。

具体分工：

| 层   | 内容                                    | 能不能碰分数 |
| --- | ------------------------------------- | ------ |
| 数据层 | 血量、能量、金币、等级                           | 只能写自己的 |
| 规则层 | 升级判定、伤害结算、扣费、发奖                       | 读写全部   |
| 表现层 | `titleraw` / `playsound` / `particle` | **只读** |

---

## 14. 初始化链

脉冲方块 + 按钮触发，只跑一次。**顺序很重要**：

```
1. 建计分项（scoreboard objectives add ...）
2. 建常量（scoreboard players set <常量> sys N）
3. 世界规则（gamerule ...，sendcommandfeedback 排第一）
4. 界面净化（hud @a hide ...）
5. 出生点与配装（setworldspawn / give）
6. 场景准备（time set / summon / gamerule doMobSpawning）
7. 开场提示（tellraw / titleraw）
```

完整样例：

```
scoreboard objectives add hp dummy "生命"
scoreboard objectives add energy dummy "能量"
scoreboard players set zero sys 0
scoreboard players set five sys 5
scoreboard players set hundred sys 100
gamerule commandblocksenabled true
gamerule sendcommandfeedback false
gamerule commandblockoutput false
gamerule showdeathmessages false
gamerule announceadvancements false
gamerule showrecipemessages false
gamerule showcoordinates false
gamerule dodaylightcycle false
gamerule doweathercycle false
gamerule keepinventory true
hud @a hide health
hud @a hide hunger
hud @a hide armor
hud @a hide status_effects
hud @a hide item_text
setworldspawn 8 -59 7
time set midnight
give @a iron_sword 1
tellraw @a {"rawtext":[{"text":"§b§l系统 §r§f已就绪"}]}
```

❗ `hud` 能隐藏的元素：`health` `hunger` `armor` `status_effects` `item_text` `crosshair` `hotbar` `paperdoll`。  
自定义 HUD 必须先把原生元素藏掉，否则两套叠在一起。

---

## 15. 主循环链

循环方块触发，**每刻 20 次**。顺序即正确性：

```
1. 时钟递增（#tick += 1）
2. 布尔位兜底（add @a 位 0）
3. 引擎同步（hp = health × 5）
4. 差值检测（受伤飘字）
5. 倒计时递减（冷却、受伤窗口）
—— 定时器闸门 ——
6. 属性重算（等级、经验条）
7. 结算（升级、击杀奖励）
8. 建档（新玩家）
9. 表现（HUD）
```

**前 5 步每刻跑，后 4 步每秒跑**（放在 `matches 20..` 闸门后面）。

实测：55 条全跑 → 2 段结构（11 条每刻 + 43 条每秒 + 2 条闸门），  
有玩家时每刻 13 条（降 76%），没人时 2 条。

---

## 16. 属性与升级公式

```
hp_max    = lv × 100 + 50
attack    = lv² + 10
crit      = lv % 100          ← 暴击率百分比
xp_max    = lv × 100
```

实现：

```
execute as @a if score @s xp >= @s xp_max run scoreboard players operation @s level_old = @s level
execute as @a if score @s xp >= @s xp_max run scoreboard players add @s level 1
execute as @a if score @s xp >= @s xp_max run scoreboard players operation @s xp -= @s xp_max
execute as @a unless score @s level = @s level_old run scoreboard players operation @s xp_max += hundred sys
execute as @a unless score @s level = @s level_old run scoreboard players operation @s attack = @s level
execute as @a unless score @s level = @s level_old run scoreboard players operation @s attack *= @s level
execute as @a unless score @s level = @s level_old run scoreboard players operation @s attack += ten sys
execute as @a unless score @s level = @s level_old run scoreboard players operation @s crit = @s level
execute as @a unless score @s level = @s level_old run scoreboard players operation @s crit %= hundred sys
execute as @a unless score @s level = @s level_old run scoreboard players operation @s level_old = @s level
```

❗ **最后一条 `level_old = level` 不能省**，它是"这次升级已处理"的标记。  
❗ 建档时 `level` 和 `level_old` 要**一起置 1**，否则下一秒 `unless level = level_old` 成立，  
新玩家白拿一次 LEVEL UP、`xp_max` 多 100。

---

## 17. UID 与归属

给每个玩家发一个唯一编号，用于击杀归属、队伍匹配。

```
scoreboard players add #uid sys 1
execute as @a[scores={uid=0}] run scoreboard players operation @s uid = #uid sys
```

- `uid=0` 表示"还没发号"
- `#uid` 是虚拟玩家计数器，永不自减
- 发号必须在**建档段**里，且排在 `建档=1` 之前

**击杀归属**：`totalKillCount` 涨了就说明有人击杀，但引擎不告诉你是谁杀谁。  
做法是用**伤害差值法**配合最近攻击者记录（见第 18 章）。

---

## 18. 伤害差值法

唯一不依赖伤害来源的掉血检测。

```
# 每刻把 health 抄成 hp（×5 放大到 0..100）
execute as @a run scoreboard players operation @s hp = @s health
execute as @a run scoreboard players operation @s hp *= five sys

# 和上一刻比，差值就是这一下掉了多少
execute as @a unless score @s hp_counta = @s hp run scoreboard players operation @s hp_hurt = @s hp
execute as @a unless score @s hp_counta = @s hp run scoreboard players operation @s hp_hurt -= @s hp_counta
execute as @a unless score @s hp_counta = @s hp run scoreboard players set @s hp_hurta 20

# 记账
execute as @a run scoreboard players operation @s hp_counta = @s hp

# 窗口递减
scoreboard players remove @a[scores={hp_hurta=1..}] hp_hurta 1
```

`hp_hurta` 是"受伤飘字还剩几刻"，配合 HUD 的 `%%N` 条件片段控制显隐。

❗ 这套逻辑**必须每刻跑**，放秒级会漏掉一整次伤害。

### 18.1 伤害：同分 + 二分法结算（U34 / U44）★ 推荐

**先记住一句话**：`damage` 只吃**字面数字**，吃不了分数；
而伤害是算出来的（攻击者的攻击力）。所以中间必须有一次"分数 → 固定 damage"的转换，
**二分法**就是干这个的。

```text
# ① 命中：只记分，不扣血 —— 目标的"受伤" = 攻击者的"攻击"
execute as @e[type=xp_orb,scores={子弹=1,命中格=11..13}] at @s \
        positioned ^^^1 positioned ~~-499.5~ \
        as @e[r=1.2,c=1,身体] \
        run scoreboard players operation @s tg_hurt = @e[type=xp_orb,scores={子弹=1},c=1] tg_damage

# ② 结算：二分法把分数拆成 2 的幂，逐档 damage + 减分（9 档 × 2 条 = 18 条）
execute as @e[scores={tg_hurt=256..}] at @s run damage @s 256 entity_attack
execute as @e[scores={tg_hurt=256..}] run scoreboard players remove @s tg_hurt 256
execute as @e[scores={tg_hurt=128..}] at @s run damage @s 128 entity_attack
execute as @e[scores={tg_hurt=128..}] run scoreboard players remove @s tg_hurt 128
...                                                    # 64 / 32 / 16 / 8 / 4 / 2 / 1

# ③ 计分板只做 HUD 镜像（每刻，放在无闸门的常驻链）
execute as @a run scoreboard players operation @s tg_health = @s health
scoreboard players operation @a tg_health *= sys_five tg_temp      # 0..20 → 0..100
```

**为什么这样比"每格写死 damage"好**：

| 写法 | 加一把枪 | 改一次伤害 | 命令数 |
|---|---|---|---|
| 每格写死 `damage @s 6` | 每条链加 N 格 | 全链重算 | 距离 × 8 |
| 同分 + 二分法结算 | **0 格** | **改表里一个数** | 18 条（固定） |

三条铁律：

1. **幂次从大到小**，且"扣血"与"减分"必须**成对**出现（第 26 章）。
2. 结算链的闸门是 `@e[scores={tg_hurt=1..}]` —— 没人欠血就一条都不跑。
3. `tg_hurt` 扣完必须归零，否则下一 tick 还会再结算一次（重复扣血）。

> ⚠️ **下面这一节是历史方案，默认不要用。**
> 自建血池意味着"判死"也要自己做，而 `damage` 动不了计分板、计分板也动不了原版血量 ——
> 两套血量并存必然打架。除非你**必须**接管血量（护甲减伤、更细的血条），否则按 18.1 做。
> 保留它是为了记住三个坑（A24）。

### 18.2 自建血池 + 赋分扣血（已废弃 · 仅作教训）

上面那套是「读原版血量」。要做**完全可控的血量**（能显示、能按数据扣、扣完即死），
用计分板自建血量，并且**扣血不穷举**：

```text
# ① 命中时只做一件事：给目标贴标
execute as @e[tag=子弹,scores={命中格=1..}] at @s positioned ^^^N ... 
        as @e[r=1.2,c=1,身体] run tag @s add tg_hit

# ② 扣血：一条命令，扣多少由**子弹身上带的伤害分**决定
execute as @e[tag=tg_hit] unless score @s tg_health matches 1..
        run scoreboard players set @s tg_health 100
scoreboard players operation @e[tag=tg_hit] tg_health -= @e[tag=子弹,scores={命中格=1..},c=1] tg_damage

# ③ 判死（放在无闸门的常驻链）
scoreboard players set @a tg_died 0                              # 每刻先清票
scoreboard players set @e[scores={tg_health=..0}] tg_died 1      # 见底发票
scoreboard players set @e[scores={tg_died=1}] tg_health 100      # 先回满，再杀
execute as @e[scores={tg_died=1}] at @s run kill @s
```

三条不能反的顺序：

1. **建档补满在扣血之前** —— `remove` / `-=` 遇到"这一项不存在"是从 0 往下扣，会一枪秒杀。
2. **回满在 kill 之前** —— kill 之后实体查不到，回血那条永远跑不到 → 复活即死循环。
3. **清票在每刻开头** —— 玩家死亡期间不在 `@a` 里，只有每刻无条件清一次才清得掉。

❗ 建档标记要用**永不为 0** 的项（`tg_health_max`），拿 `tg_health` 判会把"刚死"误判成"没建档"。

**为什么比穷举好**：加枪型 / 改射程 / 改伤害只动数据表，
`10 距离 × 3 枪型 × 4 条 = 120 格` 直接变成 `1 条`。

---

## 19. 随机与暴击

```
scoreboard players random @s _roll 1 200
```

含两端，`1..200` 共 200 个数。

暴击判定（暴击率 `crit` 是百分比）：

```
execute as @a if score @s _roll <= @s crit run scoreboard players set @s _crit 1
execute as @a unless score @s _roll <= @s crit run scoreboard players set @s _crit 0
```

伤害计算：

```
# 基础伤害
execute as @a run scoreboard players operation @s _dmg = @s attack
# 暴击 ×2
execute as @a[scores={_crit=1}] run scoreboard players operation @s _dmg *= two sys
```

❗ `random` 每刻都调用会不断变化，**只在出手那一帧调用一次**。

---

## 20. 经济与奖励

### 20.1 五种货币的奖励结算

奖励公式：`奖励 = 等级 × 2 + 10`，同时给经验和金币。


```
execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s award = @s level
execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s award *= two sys
execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s award += ten sys
execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s xp += @s award
execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s money += @s award
execute as @a unless score @s killtotal = @s killcount run tellraw @s {"rawtext":[{"text":"§6击杀奖励 §e+"},{"score":{"objective":"award","name":"@s"}},{"text":" §6经验/金币"}]}
execute as @a unless score @s killtotal = @s killcount run scoreboard players operation @s killcount = @s killtotal
```

`killtotal` 是引擎同步的总击杀，`killcount` 是"已结算到第几次"。  
两者不等就说明有新击杀。**最后一条必须同步**，否则会重复发奖。

❗ 重置数据时不能只 `reset killcount`，否则 `killtotal` 还在，立刻白送一次奖励。  
重置要写成 `operation killcount = killtotal`。

### 20.2 回收与折扣

```
tellraw @s {"rawtext":[{"text":" §l今日>§r§f回收汇率： 1.0/0."},{"score":{"name":"折扣","objective":"计算"}}]}
tellraw @s {"rawtext":[{"text":"\n§g Retrieve §l§f> 回收价格§r§f： "},{"score":{"name":"@s","objective":"回收"}}]}
```

折扣用 `计算` 这个共享目标存，回收价 = 原价 × 折扣。

---

## 21. 商店与开箱

### 21.1 方块探测式商店（免举）

踩在特定方块上就打开商店：

```
execute as @a at @s if block ~ ~-1 ~ gold_block run scoreboard players set @s 商店 1
execute as @a[scores={商店=1..}] run titleraw @s actionbar {...}
```

### 21.2 扣款 → 发货 → 提示（三段式）

```
# 第一段（脉冲）：扣款，条件不够就不扣
execute as @p[scores={money=30..}] run scoreboard players remove @s money 30
# 第二段（条件）：发货
give @p golden_apple 3
# 第三段（条件）：余额不足提示
execute as @p[scores={money=..29}] run tellraw @s {"rawtext":[{"text":"§c金币不足"}]}
```

❗ **扣款必须在发货之前**，且扣款用脉冲块——否则每刻扣一次，一秒扣光。

### 21.3 开箱：按方块类型定品质

```
execute as @a at @s if block ~ ~-1 ~ diamond_block run scoreboard players set @s 品质 4
execute as @a at @s if block ~ ~-1 ~ gold_block    run scoreboard players set @s 品质 3
execute as @a at @s if block ~ ~-1 ~ iron_block    run scoreboard players set @s 品质 2
execute as @a at @s if block ~ ~-1 ~ stone         run scoreboard players set @s 品质 1
```

然后用 `品质` 决定掉落表。判定顺序**从高到低**，用 `if` 而不是 `unless`。

---

## 22. 背包与装卸

槽位名（Bedrock）：

```
slot.weapon.mainhand      主手
slot.weapon.offhand       副手
slot.armor.head           头盔
slot.armor.chest          胸甲
slot.armor.legs           护腿
slot.armor.feet           靴子
slot.hotbar 0..8          快捷栏
slot.inventory 0..26      背包
```

装卸：

```
replaceitem entity @s slot.armor.head 0 iron_helmet 1
replaceitem entity @s slot.armor.head 0 air
```

判定"是否已装备"：

```
execute as @a[hasitem={item=iron_helmet,location=slot.armor.head}] run scoreboard players set @s 头盔 1
```

❗ 卸下用 `replaceitem ... air`，不要用 `clear`（`clear` 会清掉所有同名物品）。

---

## 23. 队伍

用 `队伍uid` 分数做分组，不用 tag：

```
# 队长发起组队：把自己的 uid 抄给队友
execute as @a[scores={组队申请=1..}] run scoreboard players operation @s 队伍uid = @a[c=1,scores={队长=1}] 队伍uid

# 判断是不是队友
execute as @a unless score @s 队伍uid = @s uid run ...
```

- `队伍uid = 0` 表示没组队
- 打自己人不掉血：`execute ... if score @s 队伍uid != @e[c=1] 队伍uid`

---

## 24. 死亡与复活

### 24.1 用引擎 `deathCount`

```
execute as @a[scores={deathCount=1..}] run scoreboard players set @s 死亡 1
```

`deathCount` 只增不减，所以要记一个 `_death_old` 做差值。

### 24.2 三态轮转（用布尔位，不用 tag）

```
# 每刻：把"刚死"标记推进一格
execute as @a[scores={死亡=1,刚死=0}] run scoreboard players set @s 刚死 1
execute as @a[scores={刚死=1}] run scoreboard players set @s 刚死 0
```


`刚死` 只存活 1 刻，用来触发"一次性"逻辑（掉落、播报、传送）。

### 24.3 完整死亡流程

```
# 头或身归零 → 标记死亡
execute as @a[scores={headhp=..0}] run scoreboard players set @s 死亡 1
execute as @a[scores={chesthp=..0}] run scoreboard players set @s 死亡 1

# 死亡表现
execute as @a[scores={死亡=1}] run camera @s fade time 0 2 0.5 color 0 0 0
execute as @a[scores={死亡=1}] run playsound block.end_portal.spawn @s

# 复位（必须放在表现之后）
execute as @a[scores={死亡=1}] run scoreboard players operation @s headhp = @s headhpmax
execute as @a[scores={死亡=1}] run scoreboard players operation @s chesthp = @s chesthpmax
execute as @a[scores={死亡=1}] run scoreboard players set @s 死亡 0
```

❗ 复位必须放在表现之后。先复位就再也匹配不到 `死亡=1`，表现不会播。

---

## 25. 小工具

### 25.1 测距仪 / 两点填充

**手持特定物品当开关**，配合 `setblock` 搭临时链、`clone` 搬运区域：

```
execute if entity @a[hasitem={item=compass,location=slot.weapon.mainhand}] run setblock ~1~~ chain_command_block 5
execute if entity @a[hasitem={item=bat_spawn_egg,location=slot.weapon.mainhand}] run setblock ~-1~~ chain_command_block 4
clone ~ ~-1 ~ ~ ~-1 ~ 1000 100 1000
```

- 蝙蝠刷怪蛋、命名牌这类"无实际用途"的物品最适合当选择器
- `setblock` 的 `facing_direction` 要跟链条流向一致（5 东 / 4 西）
- 这类逻辑**必须放在脉冲链或闸门后面**，否则每刻都在改方块

### 25.2 阈值播报（一次性）

```
execute as @a[scores={回收=20000..,播报过=0}] run tellraw @a {"rawtext":[{"text":"§e物资已回收"}]}
execute as @a[scores={回收=20000..,播报过=0}] run scoreboard players set @s 播报过 1
```

布尔位要 `add @a 播报过 0` 兜底。需要"每局重置"就在回合开始时统一置 0。

### 25.3 手持物品信息面板

```
execute @e[name=装备,type=armor_stand] ~ ~ ~ tellraw @p[tag=装备] {"rawtext":[
 {"text":"§a< §fEquipment§a > §f已装备物品: "},
 {"selector":"@e[r=3,name=!物品展示框,name=!木桶,type=item]"}]}
```

用 `@e[type=item]` 当"地面物品探测器"，配 `name=!` 黑名单排除干扰实体。

---

## 26. 二分法

任何整数都是 2 的幂次和。用"够不够减"的判断，20 步走完百万格。

```
# 分数 → X 轴坐标：1145 只需 6 步
execute as @a if score @s 坐标 >= pow512 sys run scoreboard players remove @s 坐标 512
execute as @a if score @s 坐标 >= pow512 sys run tp @s ~512 ~ ~
execute as @a if score @s 坐标 >= pow256 sys run scoreboard players remove @s 坐标 256
execute as @a if score @s 坐标 >= pow256 sys run tp @s ~256 ~ ~
...
```

**三条硬规则**：

1. 放进**脉冲链**（`impulse` + 按钮），不要放循环链——链上全是无条件块，放循环链就是每刻全跑
2. 幂次**必须从大到小**，动作与扣值**成对**出现
3. 取某一位必须 `%=` 取模，`matches 4..` 对 5、6、7 也成立，是错的

### 二进制存档

一个分数（int32）能存 32 个开关：`分数 = Σ (位值 × 2^n)`。

```
# 写第 3 位为 1
scoreboard players operation @s 存档 |= pow8 sys
# 读第 3 位
scoreboard players operation @s _tmp = @s 存档
scoreboard players operation @s _tmp %= pow16 sys
scoreboard players operation @s _tmp /= pow8 sys     ← 得到 0 或 1
```

### 分数 → 方块阵列

```
execute as @a if score @s 图案 >= pow32 sys run setblock 0 4 0 black_concrete
execute as @a if score @s 图案 >= pow32 sys run scoreboard players remove @s 图案 32
...
```

---

# 第五部分 · UI 设计

> 这一部分是整套系统的"脸面"。命令方块做 UI 的本质是：  
> **用一行 `titleraw` 的 JSON，靠"选择器命中与否"控制几十个片段的显隐。**  
> 一个 `%%N` 顶一个命令方块，这是 UI 的核心压缩手段。
