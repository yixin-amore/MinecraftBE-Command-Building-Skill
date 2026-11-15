# 技巧集（67~73 / 75 / 78~81 / 脚本清单）

> 方块当变量、物品 `data` 当参数、哨兵实体、查表法、`structure save/load`、锚点摆点、`setdisplay`、镜头体感、六个坏习惯、26 条静默失败清单、指令确认表。
**什么时候读**：需要某个具体技巧的完整写法，或怀疑踩了静默失败的坑。

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**（拆家前是第几章现在还是第几章）；跨文件的章号去主文件的
> 「章号 → 文件 对照表」查。这里的结论可能早于主文件的「⭐ 当前基线」——
> **冲突时以基线为准**。

---

## 67. 方块当变量（`if block` 分支）

Bedrock 没有 NBT 存储，真实地图大量&#x7528;**"某个位置的方块类型"当变量**：

```mcfunction
# 玩家脚下踩什么方块 → 加载哪套建筑（指令区 2）
execute as @a[scores={进度=100}] at @s if block ~ ~-0.1 ~ gold_block [] run structure load "金块" ~~-1~ 0_degrees none layer_by_layer 300
execute as @a[scores={进度=100}] at @s if block ~ ~-0.1 ~ diamond_block [] run structure load "钻石块" ~~-1~ 0_degrees none layer_by_layer 600
execute as @a[scores={进度=100}] at @s if block ~ ~-0.1 ~ netherite_block [] run structure load "合金块" ~~-1~ 0_degrees none layer_by_layer 2000
```

```mcfunction
# 箱子开箱：脚下羊毛颜色决定开哪个箱子（指令区 999）
execute as @a[scores={开箱=100..}] at @s anchored eyes positioned ^^^1 if block ~~~ red_wool run structure load 红 ~~~ 0_degrees none block_by_block 120
execute as @a[scores={开箱=100..}] at @s anchored eyes positioned ^^^1 if block ~~~ light_blue_wool run structure load 蓝 ~~~ 0_degrees none block_by_block 120
```

**用法要点：**

| 写法                         | 含义                                |
| -------------------------- | --------------------------------- |
| `if block ~ ~-0.1 ~ <方块>`  | 玩家**脚下**那块（−0.1 而不是 −1，避开半砖/台阶误差） |
| `if block ~ ~-2 ~ <方块>`    | 再往下一层                             |
| `if block ^ ^0.5 ^1.3 air` | 眼前 1.3 格是空气（用于"能不能往前挪"）           |
| `if block ~ ~-1 ~ <方块> []` | 末尾 `[]` = 空状态表，明确"任意状态都算"         |

**适用场景**：地图上的"选择器"（踩不同颜色地毯进不同关）、开关（金块=开/煤块=关）、  
剧情触发（站在特定方块上）。**不适合高频读写**——每次 `if block` 都是一条命令。

---

## 68. 物品 `data` 值当参数 ★

**一种物品当 N 种道具用**，靠 `data` 区分。这是真实地图省物品栏的核心手法：

```mcfunction
# 雪球：data=1 闪光弹 / data=4 烟雾弹（GKM）
execute as @a[hasitem={item=snowball,location=slot.weapon.mainhand,data=1}] at @s positioned ~~~ run tag @e[r=3,type=snowball,tag=!闪光弹,tag=!燃烧瓶,tag=!烟雾弹] add 手雷1
execute as @a[hasitem={item=snowball,location=slot.weapon.mainhand,data=4}] at @s positioned ~~~ run tag @e[r=3,type=snowball,tag=!手雷,tag=!燃烧瓶,tag=!闪光弹] add 烟雾弹1

# 鹦鹉螺壳：data=60 吸血刀 / data=99 武魂 / data=300 弗拉迪尾刺
execute as @a[hasitem={item=nautilus_shell,location=slot.weapon.offhand,data=99},tag=!保护] at @s run …
```

**给物品打上 `data`：**

```mcfunction
replaceitem entity @a slot.weapon.offhand 0 nautilus_shell 1 300
#                                                       ↑数量 ↑data
```

**读"玩家有没有"：**

```mcfunction
hasitem={item=fishing_rod,quantity=0}     # quantity=0 = 没有
hasitem={item=fishing_rod,data=1..}       # data 也能用区间
```

**配套的排除法**：投掷物刚生成时先打上**所有**互斥标签的取反，再精确打标——

```mcfunction
tag @e[r=3,type=snowball,tag=!手雷,tag=!燃烧瓶,tag=!闪光弹] add 烟雾弹1
```

`tag=!A,tag=!B,tag=!C` 是 Bedrock 选择器**唯一的多重排除写法**（没有 OR，只有 AND + 取反）。

---

## 69. 哨兵实体做「只执行一次」★

真实地图的初始化**不用计分板布尔位**，用一个藏起来的盔甲架当哨兵：

```mcfunction
# 弗拉迪，原样：哨兵不存在 → 才执行初始化
execute unless entity @e[type=armor_stand,tag=vladi_v10] run gamerule commandblockoutput false
execute unless entity @e[type=armor_stand,tag=vladi_v10] run gamerule sendcommandfeedback false
execute unless entity @e[type=armor_stand,tag=vladi_v10] run scoreboard objectives add vladi_eq dummy
execute unless entity @e[type=armor_stand,tag=vladi_v10] run scoreboard objectives add vladi_cd dummy
…
# 最后一条：造出哨兵，从此上面全部不再执行
execute unless entity @e[type=armor_stand,tag=vladi_v10] run tag @e[type=armor_stand,r=35,c=1,tag=!vladi_s] add vladi_v10
```

**为什么比布尔位好：**

| 方案                     | 每刻成本                            | 重置方式                            |
| ---------------------- | ------------------------------- | ------------------------------- |
| 计分板布尔位 `add @a 位 0` 兜底 | 每刻 1 条（兜底那条）                    | `scoreboard players set @a 位 0` |
| **哨兵实体**               | 每刻 N 条 `unless entity`（N=初始化条数） | `kill @e[tag=哨兵]`               |

哨兵方案**不需要兜底**（实体不会被"清空"，只会被 kill），代价是每条初始化都要带一次 `unless entity`。  
初始化条数 ≤ 10 时用哨兵；> 20 条时改用"一条 `execute if score` 包住整个初始化链"更省。

**哨兵必须是玩家碰不到的实体**：盔甲架 + `invisibility` + `resistance 255` + 埋在方块里。

```mcfunction
summon minecraft:armor_stand ~-5 ~4 ~-2
effect @e[type=armor_stand,r=35] invisibility 999999 1 true
effect @e[type=armor_stand,r=35] resistance 999999 255 true
```

---

## 70. 查表法：累加选择器 + `%%N` 索引前移 ★★

**这是本次拆解最有价值的一条。** 真实地图用**一个 `translate` 组件**实现任意长的 switch 表。

```json
{"translate":"%%7","with":{"rawtext":[
  {"selector":"@s[scores={境界=1}]"},
  {"selector":"@s[scores={境界=1..2}]"},
  {"selector":"@s[scores={境界=1..3}]"},
  {"selector":"@s[scores={境界=1..4}]"},
  {"selector":"@s[scores={境界=1..5}]"},
  {"selector":"@s[scores={境界=1..}]"},
  {"text":"§a炼气期"},{"text":"§a筑基境"},{"text":"§b灵台境"},
  {"text":"§d化神境"},{"text":"§e登仙境"},{"text":"§c轮回者"}
]}}
```

### 70.1 机制

**解析失败的组件会被整个剔除，后面的索引自动前移。**  
`%%N` 的 N 是**剔除之后**的位置（1 起）。

设选择器 S 个、文本 M 个，命中 k 个选择器（N = S + 1）：

```
存活列表 = [k 个选择器] + [M 个文本]
%%N 取第 N 个 → 文本序号 = N − k
```

验证（境界表：6 选择器、6 文本、`%%7`）：

| `境界` | 命中 k  | `%%7` 取到        | 正确？    |
| ---- | ----- | --------------- | ------ |
| 1    | 6（全中） | 文本 1 = 炼气期      | ✅      |
| 2    | 5     | 文本 2 = 筑基境      | ✅      |
| 3    | 4     | 文本 3 = 灵台境      | ✅      |
| 6    | 1     | 文本 6 = 轮回者      | ✅      |
| 0    | 0     | 文本 7 —— **越界** | ❌ 实测**显示 `%7`**，不是空白（务必看 70.2 的兜底） |

### 70.2 通用模板

```python
def table(obj, items, colors):
    """obj 的分数 1..N 对应 items[0..N-1]；0 或越界输出空白。

    ❗ 末尾那个 {"text":""} 是**兜底，不能省**：
       选择器全失败时数组只剩 N 个文本，%%(N+1) 越界，
       游戏**不是输出空白，而是把 "%7" 原样打上屏**（用户实测）。
    """
    n = len(items)
    sels = "".join('{"selector":"@s[scores={%s=1..%d}]"},' % (obj, i) for i in range(1, n + 1))
    txts = "".join('{"text":"%s%s"},' % (colors[i], items[i]) for i in range(n))
    return '{"translate":"%%%%%d","with":{"rawtext":[%s%s{"text":""}]}}' % (n + 1, sels, txts)
```

**要点：**

- 选择器必须是**累加区间** `1..1, 1..2, … 1..N`，命中数才会随数值**递减**
- `%%` 后面那个数字 = **选择器个数 + 1**
- **末尾必须挂 `{"text":""}` 兜底** —— 越界时落在空串上。不挂就是满屏 `%N`
- 末尾多余的逗号要清掉（`.replace(",]}", "]}")`）
- 一个组件顶 N 个方块：6 档只要 1 个方块，20 档也只要 1 个

### 70.3 带占位的条状图

尖刺条（8 档 + 空位）：

```json
{"translate":"%%9","with":{"rawtext":[
  {"selector":"@s[scores={尖刺3=-10..}]"},   ← 永远成立，占住第 1 位
  {"selector":"@s[scores={尖刺3=1..}]"},
  {"selector":"@s[scores={尖刺3=2..}]"},
  … 到 7..
  {"text":"§f"},
  {"text":"     ▷     "},{"text":"    ▷      "},… 共 7 个
]}}
```

第一项 `-10..` 是**永远成立**的填充位，让"值为 0"时 `%%9` 正好落到最后的空白格。

---

## 71. `structure save/load` 的六种用法 ★

真实地图把结构方块当**素材库 + 动画引擎**用，共 90 处。

### 71.1 渐进加载 = 建造动画

```mcfunction
structure load "金块" ~~-1~ 0_degrees none layer_by_layer 300
#                     ↑位置   ↑旋转    ↑镜像  ↑动画模式      ↑秒数
```

| 动画模式             | 效果        |
| ---------------- | --------- |
| `layer_by_layer` | 一层一层往上长   |
| `block_by_block` | 一块一块随机冒出来 |
| `none`           | 瞬间出现      |

`300` = 300 秒放完（不是 3 秒）。**数字越大越慢**。

### 71.2 渐进清空 = 拆解动画

```mcfunction
structure load air ~ ~ ~ 0_degrees none layer_by_layer 60
```

`air` 是空结构，加载它 = 逐层挖掉。

### 71.3 素材库换装

```mcfunction
# 抽奖：先摆好 3×1 的奖品牌，按随机数 clone 到展示位（指令区 2）
execute as @a[tag=抽奖,scores={random=1..60}]   run clone 15013 -58 15002 15015 -58 15004 15009 -58 15002
execute as @a[tag=抽奖,scores={random=61..85}]  run clone 15018 -58 15002 15020 -58 15004 15009 -58 15002
execute as @a[tag=抽奖,scores={random=86..100}] run clone 15023 -58 15002 15025 -58 15004 15009 -58 15002
```

`clone <起点> <终点> <目标>` —— 比 `structure load` 快，且不需要预先存盘。

### 71.4 天气 / 场景切换

```mcfunction
execute as @e[scores={天气=80..200},name="天气"] at @s run structure load "晴天" 1012 -57 1036
execute as @e[scores={天气=40..79},name="天气"] at @s run structure load "阴天" 1012 -57 1036
execute as @e[scores={天气=20..39},name="天气"] at @s run structure load "小雨" 1012 -57 1036
```

### 71.5 动态生成地形（矿区 / 地皮）

```mcfunction
structure load "地皮" ~-2 ~-5 ~-2
structure load 矿区 6781 1 5578 0_degrees none false true true 70
```

### 71.6 保存（运行时把玩家造的东西存下来）

```mcfunction
structure save 仓库 ~ ~1 ~ ~10 ~6 ~10 disk
structure save 实体_四周检测 15016 -57 15017 15016 -55 15017 true memory false
```

| 参数       | 含义               |
| -------- | ---------------- |
| `disk`   | 存到世界存档（永久）       |
| `memory` | 存到内存（关世界就丢，适合临时） |

> ❗ **`structure load` 的名子带空格要加引号**：`structure load "金块"`。  
> 不带引号会当成"名子 然后 位置"，报语法错。

---

## 72. 锚点盔甲架 + 局部坐标摆点

真实地图的刀光/特效不是"逐点算坐标"，而是**先召唤锚点，再在锚点周围用 `^` 摆点**：

```mcfunction
# 召唤锚点
execute unless entity @e[type=armor_stand,tag=vladi_s1] run summon minecraft:armor_stand ~-5 ~4 ~-2
# 就近认领（r=35 内最近的一个，且没被别的链认领）
execute unless entity @e[type=armor_stand,tag=vladi_s1] run tag @e[type=armor_stand,r=35,c=1,tag=!vladi_s,tag=!vladi_v10] add vladi_s1
# 摆点：先站到锚点，转成锚点朝向，再往前 0.85
execute as @a[tag=vladi_hold] at @s positioned ~ ~2.55 ~ as @e[type=armor_stand,tag=vladi_v10,c=1] rotated as @s positioned ^0.0 ^ ^0.85 run particle …
```

**核心是 `rotated as @s` + `positioned ^x ^y ^z`**：  
`rotated as` 把执行朝向改成锚点的朝向，之后的 `^` 就是**锚点局部坐标系**。  
八个方向只需要改 `^0.85 ^ ^0` → `^0 ^ ^0.85` → `^-0.85 ^ ^0` …

```mcfunction
# 环形 8 点（弗拉迪，原样，四对）
positioned ^0.0  ^ ^0.85   /  positioned ^0.0  ^ ^-0.85
positioned ^0.85 ^ ^0.0    /  positioned ^-0.85 ^ ^0.0
```

---

## 73. 原生 HUD：`setdisplay`

**不用 `titleraw` 也能显示数值**，且零每刻成本：

```mcfunction
scoreboard objectives setdisplay sidebar 公告 ascending     # 右侧记分板
scoreboard objectives setdisplay list 金币榜 descending      # Tab 列表
scoreboard objectives setdisplay belowname vip               # 玩家头顶（准星下方）
```

| 位置          | 能显示              | 刷新成本        |
| ----------- | ---------------- | ----------- |
| `belowname` | 1 个数值（头顶）        | **0**（引擎自动） |
| `sidebar`   | 最多 15 行（名字 + 数值） | **0**       |
| `list`      | Tab 列表排序         | **0**       |

**用中文当计分项名和显示名完全没问题**——198 个计分项全是 `dummy`，名字直接写中文（`金币`/`境界`/`天赋`）。

> **策略**：常驻数值（金币、等级、战力）用 `setdisplay`；动态排版（血条、进度条、菜单）才用 `titleraw`。

---

---

## 75. 镜头与体感

真实地图大量用镜头语言，这四条是最划算的：

### 75.1 `camera` —— FOV 冲击

```mcfunction
execute as @a[tag=…] at @s run camera @s fov_set 52 0.14 out_quad     # 拉到 52°，0.14 秒
execute as @a[tag=…] at @s run camera @s fov_clear 0.50 out_elastic   # 回默认
execute as @a[tag=…] run camera @s fade time 0.1 2 1.5 color 0 0 0    # 黑屏渐变（进/停/出 秒）
```

| 缓动            | 手感              |
| ------------- | --------------- |
| `out_quad`    | 快速起步、缓慢收尾（适合冲击） |
| `out_elastic` | 回弹（适合恢复）        |
| `out_back`    | 过冲再回（适合开镜）      |

### 75.2 `fog` —— 环境氛围

```mcfunction
fog @a[r=24] push "minecraft:fog_the_end" "vladi_fog"
fog @a[r=32] remove "vladi_fog"
```

`push <雾 ID> <自定义名>` / `remove <自定义名>`。必须成对，否则玩家一直灰屏。

### 75.3 `camerashake` —— 打击感

```mcfunction
camerashake add @s 0.5 0.15 positional      # 强度 0.5 / 0.15 秒 / 位置型
camerashake add @s 0.05 0.05 rotational     # 轻抖（连击每刀一次）
camerashake add @a[r=60] 1 0.2              # 爆炸震全场
```

`positional` = 越远越弱（爆炸）；`rotational` = 纯画面转（刀砍）。

### 75.4 `inputpermission` —— 锁操作

```mcfunction
inputpermission set @s movement disabled    # 过场动画锁移动
inputpermission set @s movement enabled
```

### 75.5 `playanimation` —— 播原版动画

```mcfunction
playanimation @s animation.humanoid.riptide riptide_tp 0
playanimation @s animation.trident.wield_first_person_riptide riptide_fp 0
```

`playanimation <目标> <动画名> [下一状态] [混合时间]`。**不用自己做动作**，借原版的最省。

---

---

## 78. 真实地图的六个坏习惯（别学）

| # | 坏习惯                 | 出处         | 后果            | 我们的做法                        |
| - | ------------------- | ---------- | ------------- | ---------------------------- |
| 1 | 单链 135 块硬扛          | 弗拉迪        | 每刻跑满 135 条    | 按功能拆链 + 闸门，空闲 3–4 条          |
| 2 | 229 个循环块只开 10 个     | 指令区 999    | 维护时看不出哪个是活的   | `auto` 状态写进说明文档              |
| 3 | 367 块竖直链            | 指令区 −10000 | 改一个方块要飞 300 格 | 竖直链 ≤ 60 块，超了就拐弯             |
| 4 | 一个 `sound` 表 1145 行 | 指令区 −10000 | 加音效要数格子       | 查表法（第 70 章）压成 1 块            |
| 5 | 用 `§` 颜色码当标签名       | 指令区 999    | 玩家能打出同名字符串冒充  | 标签一律 `a-z0-9_`，且带前缀          |
| 6 | 条件块级联（26 处）         | GKM        | 一条失败后面全跳过     | 每条自带完整条件，`conditional_bit=0` |

**第 4 条值得展开**：`scores={sound=N}` 一条一条列，是"没有查表法"的代价。  
用第 70 章的累加选择器，1145 个音效也只需要 1 个方块（但需要 1145 个文本组件，会超长）。  
**折中**：超过 20 档就分块，每块管 20 档，用 `scores={x=1..20}` / `21..40` 先分桶。

---

# 第十部分 · 附录

## 79. 26 条静默失败清单

这些**都不报错**，只是不生效。是最耗时间的部分。

| #  | 坑                                      | 表现                                           |
| -- | -------------------------------------- | -------------------------------------------- |
| 1  | `facing_direction` 写成 BYTE             | 方块朝下、链全断、按钮吊顶                                |
| 2  | `level.dat` 用 gzip 压缩                  | 导入失败                                         |
| 3  | 单条日志 > 32KB 不拆分片                       | 判损坏，导入失败                                     |
| 4  | 没写 `FinalizedState=2`                  | 区块重新生成，方块全没                                  |
| 5  | 调色板第 0 项不是 air                         | 全图变石头                                        |
| 6  | 子区块单值层只跳 1 字节                          | 后续解析全错位                                      |
| 7  | 方块实体用区块局部坐标                            | 跨区块时挂错位置                                     |
| 8  | 蛇形反向行末块固定朝东                            | 指回前一块，互相触发                                   |
| 9  | `gamerule commandblockoutput` 当"关方块报错" | 聊天栏安静了，方块界面红字照旧                              |
| 10 | `TrackOutput=0` 交付                     | 唯一的内置日志被删，出问题只能靠猜                              |
| 11 | titleraw 的 JSON 里有**真实换行**             | 整条非法，HUD 从不显示                                |
| 12 | 用 `%` 格式化拼 `%%N`                       | 被吃成 `%2`，条件拼接失效                              |
| 13 | `%%N` 当"参数个数"用                         | 只输出第 N 个参数，前缀丢失                              |
| 14 | 以为 `§m`/`§n` 是删除线/下划线                  | 其实是红石色/铜色                                    |
| 15 | 用 `ui.button.click`                    | Bedrock 无声                                   |
| 16 | **闸门写成条件块**                            | 被上一段连坐，整段永久失效                                |
| 17 | 复位命令放段尾                                | 前面一失败就永不归零                                   |
| 18 | 段内第一条放 `damage`                        | 没敌人就失败，后面全跳过                                 |
| 19 | 忘了 `add @a 布尔 0` 兜底                    | `scores={x=0}` 匹配不到未赋值玩家                     |
| 20 | 建档时 `level_old` 没跟 `level` 一起置位        | 新玩家白拿一次 LEVEL UP                             |
| 21 | **结构文件前加 8 字节头**                       | 判损坏 → 导入失败（`.mcstructure` 直接从 `0a 00 00` 开始） |
| 22 | **`*_bit` 写成 INT**                     | 方块状态非法 → 整个结构加载失败                            |
| 23 | 弹丸先给"全体"位移再给"某档"位移                     | 两条都命中，位移叠加变双倍速                               |
| 24 | **连接块没加条件位** | 检测失败也每刻复位一次，白跑一条 `setblock`；空闲开销翻倍 |
| 25 | **业务块加了条件位** | 一条失败后面全被连坐（`damage` 没打中 → 攒能量、连招全跳过） |
| 26 | **连接块朝向写成朝链首** | 链永远接不通，检测满足也不跑 |

---

## 80. 指令确认表（网易服实装状态）

### 62.1 可直接使用

| 指令                                                                  | 关键语法                                                  | 备注               |
| ------------------------------------------------------------------- | ----------------------------------------------------- | ---------------- |
| `scoreboard objectives add`                                         | `<名> <准则> [显示名]`                                      | 准则见 11.1         |
| `scoreboard players set/add/remove/reset`                           | `set <目标> <名> <值>`                                    | 目标可为 `@a` / 虚拟玩家 |
| `scoreboard players operation`                                      | `<目标> <名> <运算符> <来源> <名>`                             | 见第 12 章          |
| `scoreboard players random`                                         | `<目标> <名> <min> <max>`                                | 含两端              |
| `execute as/at/positioned/anchored/if/unless/run`                   | 见 62.2                                                | 可多层嵌套            |
| `damage`                                                            | `damage <目标> <量> [原因] [entity <攻击者>]`                 | **已实装**，走真实血量    |
| `camera`                                                            | `camera <目标> fade time <入> <持> <出> color <r> <g> <b>` | **已实装**，镜头演出     |
| `hud`                                                               | `hud <目标> hide\|reset <元素>`                           | **已实装**，元素见 14 章 |
| `structure`                                                         | `structure save/load <名> <起> <止>`                     | **已实装**          |
| `particle`                                                          | `particle <粒子> <x> <y> <z>`                           | 粒子名见 62.3        |
| `titleraw`                                                          | `titleraw <目标> <title\|subtitle\|actionbar> <JSON>`   |                  |
| `tellraw`                                                           | `tellraw <目标> <JSON>`                                 | 聊天栏，可多行          |
| `title`                                                             | `title <目标> <title\|subtitle\|actionbar> <纯文本>`       | 不支持 JSON         |
| `playsound`                                                         | `playsound <音效> <目标> [x y z] [音量] [音调] [最小音量]`        |                  |
| `stopsound`                                                         | `stopsound <目标> [音效]`                                 |                  |
| `replaceitem entity`                                                | `replaceitem entity <目标> <槽位> <物品> [数量]`              | 槽位见 22 章         |
| `give` / `clear` / `setblock` / `fill` / `clone`                    | 标准语法                                                  |                  |
| `effect`                                                            | `effect <目标> <效果> [秒] [等级] [hideParticles]`           |                  |
| `gamerule`                                                          | `gamerule <规则> <true\|false>`                         |                  |
| `tp` / `setworldspawn` / `time set` / `weather` / `kill` / `summon` | 标准语法                                                  |                  |
| `testfor`                                                           | `testfor <选择器>`                                       | 只做条件，不做事         |

### 62.2 `execute` 子句顺序（写错就整条失效）

```
execute <as 目标> <at 目标> <anchored eyes|feet> <positioned x y z> <if|unless 条件> <run 指令>
```

- `as` 换执行者（改变 `@s`）
- `at` 换执行位置与朝向（改变 `~ ~ ~` 与 `^ ^ ^`）
- `anchored eyes` 以眼睛为原点，`anchored feet` 以脚为原点
- `positioned` 支持绝对 `100 64 100`、相对 `~ ~1 ~`、局部 `^ ^ ^3`
- 条件类型：`if score A B op C D`、`if entity <选择器>`、`if block <x y z> <方块>`、`if blocks ...`
- 条件可叠加，全部满足才 `run`

### 62.3 粒子名（网易可用）

```
minecraft:balloon_gas_particle    刀光主力，白色气流
minecraft:endrod                  细线，弹道
minecraft:critical_hit_emitter
minecraft:enchanting_table_particle
minecraft:basic_flame_particle
minecraft:lava_particle
minecraft:villager_happy
minecraft:heart_particle
minecraft:huge_explosion_emitter
minecraft:sonic_explosion
```

### 62.4 明确不可用

| 项                          | 原因          | 替代                            |
| -------------------------- | ----------- | ----------------------------- |
| `.mcfunction` / `function` | 网易不支持       | 全部写进命令方块链                     |
| `data get/modify`          | 未实装         | 用计分项当变量                       |
| `tag` 大规模使用                | 残留、跨存档污染    | 计分板布尔位 + 每刻 `add @a <位> 0`    |
| `nbt=` 选择器参数               | Bedrock 不支持 | `hasitem` / `scores` / `type` |
| `input` / 按键检测             | 不存在         | 主手物品 / 视角 `rx` / 位置           |

---

## 81. 索引

### 81.1 要做什么 → 看哪章

| 要做的东西                        | 章节            |
| ---------------------------- | ------------- |
| 从零搭一套系统                      | 14 → 15 → 16  |
| 属性 / 升级 / 数值面板               | 16 + 28 + 37  |
| 血条 / 能量条 / 任何条               | 37 + 38 + 18  |
| 菜单 / 商店界面                    | 34 + 35 + 21  |
| 状态标签 / 装备显示                  | 36            |
| 弹窗 / 提示框                     | 40            |
| 近战刀光 / 挥砍特效                  | 47 + 48       |
| 连招 / 技能冷却                    | 48 + 49 + 50  |
| 枪械 / 远程 / 弹道                 | 45 + 50 + 51  |
| 击杀奖励 / 归属                    | 17 + 20 + 52  |
| 死亡 / 复活                      | 24            |
| 界面配色 / 图标                    | 31 + 32 + 33  |
| 按钮音 / 反馈音                    | 53 + 55       |
| 服务器卡顿 / 降算力                  | 8 + 58        |
| 分数 → 坐标 / 方块                 | 26            |
| 存档写不出来 / 导入失败                | 1 → 2 → 3 → 4 |
| 结构文件加载不了                     | 5 + 6         |
| 命令不执行 / 报错                   | 10            |
| HUD 不显示                      | 28 + 42       |
| 存档 / 文件损坏                    | 79            |
| 指令区不跑 / 玩家走开就停               | **74**        |
| 一个数值对应 N 段文本（等级名 / 品阶 / 称号）  | **70**        |
| 用物品区分多种道具                    | **68**        |
| 一次性初始化 / 只跑一次                | **69**        |
| 建造 / 拆解动画、换装、动态地形            | **71**        |
| 踩方块触发 / 方块当开关                | **67**        |
| 常驻数值显示（金币 / 等级 / 战力）         | **73**        |
| 震屏 / 拉 FOV / 雾 / 锁操作 / 播原版动作 | **75**        |
| 全场都能听见的音效                    | **76**        |
| 看真实地图怎么摆 / 怎么断链              | 65 + 66       |

### 81.2 五条统一铁律

1. **能用引擎准则（`health`/`totalKillCount`/`deathCount`）就别自己算**
2. **能用计分板布尔位就别用 tag**
3. **命令按功能拆成独立链**，每条链一个循环闸门，别把不相关的命令堆一起
4. **断链靠朝向**：检测（无条件）→ 连接块（**有条件**，把重置块接回运行方向）→ 重置块（无条件）→ 业务（全部无条件）。断开由外部同类型 `setblock` 打 **连接块** 改朝向完成（第 8 章）
5. **指令区离出生点远就加常加载区块**，否则玩家一走开整片停摆（第 74 章）

### 81.3 三条设计原则

1. **表现层绝不写数据**（第 13 章）
2. **空闲每刻执行条数 = 功能链数**，N 个互斥分支就是 N 条链（第 8 章）
3. **一个 `%%N` 顶一个命令方块**——UI 优先压进一行 JSON（第 29 章）

---

---

## 附：生成器脚本清单

| 脚本                                             | 作用                                                                                                    |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `build_cbworld.py`                             | **底座**：纯命令方块世界（写 LevelDB）+ `binsplit` / `bits2blocks`                                                 |
| `build_katana.py`                              | 拔刀剑生成器（spec 驱动，4 条链）                                                                                  |
| `build_fishrod.py`                             | 鱼竿枪生成器 v1（旧版，3 枪型 / 弹丸实体 / 3 条链）                                                                 |
| `build_tidegun.py`                             | **潮汐鱼竿枪 v3**（`xp_orb` 载体 + 旋转散射 + 三段肢体 + 查表 HUD + 6 条功能链，见第 99 章）                                            |
| `build_refacing_demo.py`                       | **断链演示**（+x 布局，2 条链 / 2 个有条件块；「断开链条」按钮演示改朝向物理断开） |
| `extract_docx.py`                              | **.docx → .txt**（不依赖 python-docx，把 `E:/Pictures` 下的原文转进 `refs/`） |
| `check_props.py`                               | **说明区回读**：箱子里每件物品的名字 / Lore / data / slot，告示牌每一行；`.mcworld` 与 `.mcstructure` 都支持 |
| `lint_commands.py`                             | **指令体检**：`@s` 越界 / JSON 坏 / `%%N` 越界 / 计分项没建档 / 音效不在白名单 / `execute` 缺 `run`                        |
| `build_chain_split_demo.py`                    | **按功能分链演示**（−z 布局，方向约定的标准样例）                                                                          |
| `mcworld_to_structure.py`                      | 世界 → `.mcstructure`                                                                                   |
| `verify_mcworld.py`                            | 回读校验：CRC / 子区块 / 实体坐标 / 链连贯性                                                                          |
| `selfcheck_katana.py` / `selfcheck_fishrod.py` | 交付物自检（16 / 22 项）                                                                                      |
| `build_compat.py`                              | 在真实存档上追加区块（导入失败兜底）                                                                                    |
| `dump_cbworld.py`                              | **拆解别人的世界**：从任意 `.mcworld` 抽出全部命令方块（含 NBT、坐标、朝向、`auto`），支持 `.log` + `.ldb`（Bedrock 的 raw-deflate 压缩块） |

### 标准流程

```bash
# 0. 先体检 spec（30 秒，能拦下 80% 的静默失败）
python scripts/lint_commands.py specs/katana.json

# 1. spec → 世界
python scripts/build_katana.py --spec specs/katana.json \
       --template _template.mcworld --out 世界.mcworld

# 2. 17 项自检
python scripts/selfcheck_katana.py 世界.mcworld

# 3. 世界 → 结构文件
python scripts/mcworld_to_structure.py --input 世界.mcworld --out 指令区.mcstructure

# 4. 结构文件不要加任何头（--header 已废弃，加了必判损坏）
```

### 拆解别人的指令区

```bash
python scripts/dump_cbworld.py 别人的世界.mcworld                 # 摘要：方块数 / 类型 / 朝向 / 条件位 / 链长
python scripts/dump_cbworld.py 别人的世界.mcworld --json w.json   # 结构化（坐标 + 命令 + NBT）
python scripts/dump_cbworld.py 别人的世界.mcworld --raw c.txt     # 纯命令文本，一行一条
```

第 64–78 章的全部数据都是这么来的。学别人的图，先跑这个。

### 游戏内

1. `/give @s structure_block`
2. 放下，模式切 **加载(Load)**
3. 选文件，设偏移，点 **加载**
4. 找到链首方块，按它**正上方**的按钮（初始化）

---

---

# 第十一部分 · 你的 66 份实战原文库

> 这一部分不是总结，是**索引 + 原文**。
> 你要做的任何系统，先在 82 章找到同类，抄骨架，换 ID，再加表现。
> 原文全文在 `refs/`（66 份，约 240 万字，随技能一起分发）。

---
