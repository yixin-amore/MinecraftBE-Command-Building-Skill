# 原文参考与实例（59~60 / 82~83 / 87~97 章）

> 66 份原文索引、两个完整实例（拔刀剑、数据化系统）、建筑打印机、抽奖开箱、商店经济、地皮队伍、数据化 HUD、战斗单位、UI 原文、照抄会坏的地方、搬运六步。
**什么时候读**：要找同类实现抄骨架（**优先读这里**），或核对原文怎么写。

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**（拆家前是第几章现在还是第几章）；跨文件的章号去主文件的
> 「章号 → 文件 对照表」查。这里的结论可能早于主文件的「⭐ 当前基线」——
> **冲突时以基线为准**。

---

## 59. 实例：拔刀剑

### 59.1 规模

| 项    | 值                           |
| ---- | --------------------------- |
| 命令方块 | 210 个（4 条功能链 + 4 面板 + 初始化链） |
| 按钮   | 5 个                         |
| 区块   | 2 个                         |
| 功能链  | 4 条（铁剑 / 烈焰棒 / 羽毛 / 下界之星）   |
| 空闲常驻 | **4 条（1.9%）**               |
| 结构文件 | 124,142 B                   |

### 59.2 四个通道

| 主手   | 闸门                          | 段内命令 | 内容                                |
| ---- | --------------------------- | ---- | --------------------------------- |
| 铁剑   | `hasitem iron_sword`（在循环块里） | 68   | 兜底 + 递减 + 连招 + 出手 + 刀光 + 伤害 + HUD |
| 烈焰棒  | `hasitem blaze_rod`         | 21   | 技能 1                              |
| 羽毛   | `hasitem feather`           | 21   | 技能 2                              |
| 下界之星 | `hasitem nether_star`       | 21   | 技能 3                              |

### 59.3 分数表

```
blade      持刀布尔位
combo      1..4    连招段数
combo_t    0..12   窗口
atk_cd     0..8    攻击间隔
energy     0..100  能量
energy_t   0..20   能量条格数
slash      1..4    刀光形态
slash_t    0..4    刀光存活刻数
burst_cd   0..100  技能冷却
skill      1..3    当前技能
sys                常量与计数器
```

### 59.4 主循环顺序

```
段 A（持剑时，68 条）
  1. 布尔位兜底（blade / 各计数项）
  2. 冷却递减 + clamp（atk_cd / slash_t / burst_cd / combo_t）
  3. 连招窗口（combo *= combo_alive）
  4. 能量封顶 + 换算格数
  5. blade = 1
  6. 出手判定（atk_cd=0 且有敌人 → atk_cd=8）
  7. 段数推进（slash / slash_t / energy / combo / combo_t）
  8. 音效
  9. 刀光粒子（4 形态 × 7~8 点）
 10. 伤害（4 段，放最后）
 11. HUD
段 B/C/D（技能 1/2/3，各 21 条）
```

### 59.5 三个必踩的坑

1. `atk_cd` 递减必须在攻击结算之后
2. 技能扣能量必须放伤害之前
3. 连招清零要加 `unless score @s atk_cd matches 8`

---

## 60. 实例：数据化系统

### 60.1 规模

| 项    | 值              |
| ---- | -------------- |
| 命令方块 | 131 个          |
| 按钮   | 10 个           |
| 功能链  | 2 条（每刻链 / 每秒链） |
| 空闲常驻 | **2 条（1.5%）**  |
| 结构文件 | 84,373 B       |

### 60.2 两条链

| 段 | 闸门                                        | 命令数 | 频率 |
| - | ----------------------------------------- | --- | -- |
| A | `execute if entity @a`                    | 11  | 每刻 |
| B | `execute if score #tick sys matches 20..` | 43  | 每秒 |

段 A 内容：时钟、布尔位兜底、血量同步、受伤差值、受伤窗口递减。  
段 B 内容：`#tick` 归零（段首）、游戏时长、血条动画、经验条、HUD、升级、击杀奖励、建档。

**改造前 55 条全跑，改造后有玩家时每刻 13 条（降 76%），没人时 2 条。**

### 60.3 38 个计分项

```
生命：hp hp_max hp_now hp_t hp_hurta hp_hurt hp_counta
经验：xp xp_max xp_now xp_t
等级：level level_old
属性：attack crit attack_crit
击杀：killtotal killcount award
经济：money playtime
布尔：建档 礼包
系统：sys
```

### 60.4 顺手修掉的 bug

建档时 `level_old` 写成 0、`level` 写成 1，  
下一秒 `unless level = level_old` 成立 → 新玩家白拿一次 LEVEL UP、`xp_max` 多 100。  
**改成两者都置 1。**

---

# 第九部分 · 实战指令区拆解

> **素材**：6 张真实地图的指令区，共 **9127 个命令方块 / 8074 条非空命令**。  
> 全部从 `.mcworld` 的 LevelDB 里直接读出来（`scripts/dump_cbworld.py`），不是看截图猜的。
>
> 这一部分只讲**能复用的手法**，不抄他们的玩法。每条都标了出处，可以回查。

---

---

## 82. 这一部分怎么用（先读这 8 行）

**先纠正一条老规矩。** 以前手册里写「UI 必须照模板，别自创」，那不是禁止创造——
是**那时候能抄的东西太少**。现在这 66 份原文摊开，可抄的骨架从 1 套变成 66 套，
所以规矩改成：

| 旧说法 | 新说法 |
|---|---|
| 禁止自创 UI | **先抄，抄完再改**。抄不到同类才自创，自创要说明为什么抄不到 |
| 只能按手册模板 | **手册模板是地板，不是天花板**。原文里有更好的写法就用原文的 |

**三层用法：**

1. **查 83 章索引表** —— 按「你要做什么」找文件名
2. **翻对应分类章（84–94）** —— 看这份原文的核心机制 + 真实片段
3. **打开 `refs/<文件名>`** —— 抄完整命令，换 ID，搬进 spec

**三条搬运铁律：**

- **只搬机制，不搬 ID** —— 原文的 `zd`/`弹夹a`/`号码` 一律换成你的前缀（`tg_`/`kt_`）
- **只搬结构，不搬坐标** —— 原文的 `~2~~`、`1000 100 1000` 是你的指令区坐标，必须重算
- **只搬能跑通的** —— 原文里 `execute @a ~~~` 这种老语法（1.19.50 之前）要改新写法，
  95 章列了全部照抄会坏的地方

---

## 83. 66 份总索引

> 字数是正文字符数，用来判断"这份是完整系统还是片段"。
> 带 ★ 的是最值得先读的。

### 枪械 / 子弹（8 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| ★ `枪械3.0模板.txt`（两份重复） | 30k | 钩子触发 + 弹夹 + 换弹 101 | 84.3 |
| ★ `枪械优化版2.0.txt` | 37k | 4 种枪 / 射速分数递减 / 全自动 | 84.4 |
| ★ `枪械指令4.0.txt` | 30k | 抬头 `rx=-88` 触发 + 时刻计数 | 84.5 |
| ★ `鱼竿枪1145.txt` | 36k | **船当子弹** + 33 种枪声 + 微角度散射 | 84.2 |
| `鱼竿枪1145 - 副本.txt` | 34k | 同上，早期版 | 84.2 |
| `鱼竿枪1145 - 副本 (2).txt` | 13k | 同上，删减版 | 84.2 |
| `换弹部分666.txt` | 10k | 弹药溢出回灌（`zd > 弹匣容量`） | 84.9 |
| `伪无鱼竿枪.txt` / `- 副本` / `- bf` | 31k / 30k / 15k | 钩子当扳机的完整枪 | 85 |

### 伪无子弹（5 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| ★ `伪无判定.txt` | 91k | 逐格射线 + 三段高度判定 | 85.2 / 85.3 |
| `肢体判定.txt` | 4.2k | 上面那份的干净版（20 行讲完） | 86 |
| `pd1.txt` / `pd2.txt` / `pd3.txt` | 58k ×3 | 判定链的三个分支（同一份复制） | 85.3 |
| `pd3aa.txt` | 57k | 判定链的腿部变体 | 85.3 |
| `伪无粒子.txt` / `- 副本` | 6.6k / 7.8k | 子弹拖尾：`positioned ^^^N` 逐格摆粒子 | 85.1 |

### 建筑打印机（9 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| ★ `jz3 341.txt` | 273k | **打印机驱动**（走格子 + 回卷 + 进度条） | 87 |
| `jz6.txt` | 579k | 最大的一层方块表（红石线 / 中继器） | 87.2 |
| `jz1 120.txt` | 167k | 方块表（磨石 / 铜块） | 87.2 |
| `jz5.txt` | 176k | 方块表（圆石 / 铁块 / 漏斗） | 87.2 |
| `jz2 160.txt` / `jz3.txt` | 75k ×2 | 方块表（安山岩楼梯 / 拉杆） | 87.2 |
| `nx地形.txt` | 4.2k | 极简地形生成（`fill` + 清场） | 87.5 |

### 抽奖 / 开箱（7 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| ★ `开箱.txt` | 12k | 看箱子朝向 + 下方方块定品质 | 88.1 |
| `开箱系统5.0.txt` | 2.2k | `leash_knot` 当展示位 | 88.2 |
| `抽奖机2.0模板.txt` | 5.3k | 运输矿车当奖池 + 金币分档 | 88.2 |
| `抽奖机5.0.txt` | 9.3k | 奖品牌检测 + 物品搬运 | 88.3 |
| `随机开箱2.0.txt` | 3.2k | 进度条 10/20/30 分段 + 铜块触发 | 88.4 |
| `随机开箱子物品模板.txt` | 613 | 奖池物品表 | 88.4 |
| `撬棍开箱功能.txt` / `撬棍功能后续.txt` | 2.4k / 9.7k | `detect` 长按撬棍 + 25 种箱子存档 | 93.3 |

### 商店 / 经济 / 回收（5 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| ★ `免举商店.txt` | 8.4k | 脚下双层方块当商品牌 | 89.1 |
| `金币转账功能模板.txt` | 13k | 转账 6 个中间量 | 89.2 |
| ★ `hsid.txt` | 8k | **物资回收价目表**（70 件，含完整指令） | 89.3 |
| `物资回收.txt` | 1.8k | 金币/经验排行榜 | 89.4 |
| `一键回收功能2.0.txt` | 670 | 区域 tag 批量回收 | 89.4 |

### 地皮 / 队伍 / 装卸 / 回城（7 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| `地皮系统2.0(1).txt` | 4.1k | 假玩家当全局坐标 | 90.1 |
| `efdp.txt` | 3.8k | 地皮保护（区域选择器 `dx/dy/dz`） | 90.1 |
| `组队系统.txt` | 8.5k | `menu` 状态机菜单 | 90.2 |
| `虚拟装卸.txt` | 6.4k | `xp_bottle` 当交互物 | 90.3 |
| `回城.txt` | 1.7k | `%%9` 九段进度 | 90.4 |
| `防秒退狗系统.txt` | 453 | 战场 tag + 秒退判定 | 90.5 |
| `死亡盒子系统1.0(新语法).txt` | 2.5k | 矿车箱子 + 漏斗 | 86.4 |

### 数据化 / HUD（7 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| ★ `数据化指令.txt` | 55k | 数据化全套（234 行） | 91.1 |
| `数据化功能.txt` | 28k | 回血回蓝 / 临时职位属性 | 91.1 |
| `数据化模板.txt` | 13k | 攻防闪血暴 6 项备份 | 91.1 |
| ★ `数据化T显.txt` | 2.7k | 状态栏 + 多段血条（单行 titleraw） | 91.3 |
| `子弹动态t显.txt` | 15k | 鱼竿枪 HUD 全套 | 91.4 |
| `tx.txt` | 9.3k | 食物条用 `ࡅ` 字符 | 91.5 |
| `新建 DOCX 文档 (2).txt` | 11k | 单行 titleraw 超长 HUD | 91.3 |

### 战斗单位（4 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| ★ `精英怪1.0.txt` | 11k | 攻击频率 + 随机 1..5 模式 | 92.1 |
| `副本boss技能制作模板.txt` | 11k | 物品当触发点 + 盔甲架当特效锚 | 92.2 |
| `穷举拔刀剑.txt` | 2.4k | `positioned ^x^y^z` 摆刀光 | 92.3 |
| `肢体部分.txt` | 5.8k | 三段血 + die 标记 + 镜头 | 86.2 |

### 小工具（6 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| `测距仪.txt` | 2.9k | `facing entity ... feet` 量距离 | 93.1 |
| `两点填充.txt` | 3.2k | 蝙蝠选点 + `clone` 填充 | 93.2 |
| `末影箱物品清除功能.txt` | 2.3k | 27 格 `replaceitem ... air` | 93.4 |
| `药品系统.txt` | 795 | 单行 HUD | 93.5 |
| `道具使用系统.txt` | 1.9k | `使用进度 1..100` 长按读条 | 93.5 |
| `死亡检测.txt` | 584 | **四行死亡检测** | 86.3 |

### UI / 物资设计（4 份）

| 文件 | 字 | 是什么 | 看哪章 |
|---|---|---|---|
| ★ `新建 DOCX 文档.txt` | 50k | 菜单 / 信息面板 / 交易市场原文 | 94.1 |
| `物资系统 - 副本.txt` | 7k | 7 品质 × 10 = 70 物资设计稿 | 94.2 |
| `物资系统.txt` | 4.2k | 品质色表 | 94.2 |
| `q.txt` | 13 | 作者 QQ（没用，忽略） | — |

---

---

## 87. 建筑打印机：分数索引 → 方块

**这是全库规模最大的一套（jz 系列合计 140 万字，打印 291776 格）。**
机制其实极简：**一个盔甲架走格子，每一步用分数查表决定放什么方块。**

### 87.1 驱动：走格子 + 回卷（`jz3 341.txt` 原文）

```
execute as @e[name=b] at @s run tp @s ~ ~ ~
titleraw @a actionbar {"rawtext":[{"text":"§g打印进度: "},{"score":{"name":"@e[name=a]","objective":"a"}},{"text":"§g/291776"}]}
scoreboard players add @e[name=a] a 1
scoreboard players add @e[name=b] a 1
scoreboard players add @e[name=b] b 1
execute as @e[name=a] at @s run tp @s ~1 ~ ~
execute if entity @e[name=b,scores={a=98..}] as @e[name=a] at @s run tp @s ~-97 ~ ~1
scoreboard players set @e[name=b,scores={a=98..}] a 1
execute as @e[name=b,scores={b=9119..}] at @s run tp @s ~ ~1 ~
execute as @e[name=b,scores={b=9119..}] at @s run tp @e[name=a] ~1 ~ ~
scoreboard players set @e[name=b,scores={b=9119..}] b 1
```

**两个盔甲架分工：**

| 实体 | 分数 | 作用 |
|---|---|---|
| `a` | `a` = 当前格号 | 走到哪，就在哪放方块 |
| `b` | `a` = 行内第几格（0..97）<br>`b` = 第几行（0..9119） | 只管"该换行了" |

**回卷三行**是精髓：走到第 98 格 → `tp ~-97 ~ ~1`（往回 97 格、往前 1 格）
+ `set a 1` 重置行内计数。**没有 if-else，纯 tp 位移。**

291776 = 98 × 2977，宽 98 是因为**一格链最多 98 个方块**（作者的分层切法）。

### 87.2 分数 → 方块：`!` 负匹配集合（原文）

```
execute as @e[name=a] unless entity @s[scores={a=!420,a=!422..424,a=!427..447,a=!450..452,a=!454,a=!511,...}] at @s run setblock ~ ~ ~ <方块A>
execute as @e[name=a] unless entity @s[scores={a=!510,a=!558,a=!607..608,...}] at @s run setblock ~ ~ ~ <方块B>
```

**这是"查表法"的暴力版**：一条命令负责一种方块，条件是"当前格号**不在**我的列表里"→ 跳过。

`!` 是 Bedrock `scores` 的否定匹配，支持区间 `!422..424`。
一行里堆几十个 `!` 条件，就是一张"哪些格号用这种方块"的集合表。

**为什么用 `unless` 而不是 `if`**：
`if a=420` 只能写一个值；`unless a=!420,!422..424,...` 能一次排除几十个值。
**否定形式才能表达集合。**

**生成方式**：这种表不是手写的。原文是从 `.schematic` 逐格导出，
按方块类型分组、把格号合并成区间，再拼成一行。**要打印建筑就写个导出脚本，别手抄。**

### 87.3 极简地形（`nx地形.txt`，13 条命令）

```
execute if entity @e[type=fishing_hook] run setblock ~~~-1 redstone_block
execute at @e[type=xp_orb] run fill ~ -20 ~ ~~-1~ stone
execute at @e[type=xp_orb] run fill ~ ~ ~ ~~-2~ grass replace air
execute as @e unless entity @s[name=!n,type=!xp_orb,tag=!point,type=!fishing_hook] run kill @s
```

13 条命令造地形：经验球当"笔"，走到哪 `fill` 到哪，鱼竿钩落地放红石块。
**最后一条清场**（`unless` 排除所有该留的实体）是全库通用收尾。

---

## 88. 抽奖与开箱

### 88.1 看箱子朝向 + 下方方块定品质（`开箱.txt`）

```
execute as @a at @s positioned ~ ~1.5 ~ if block ^ ^ ^1.75 beehive positioned ^ ^ ^1.75 if block ~ ~-1 ~ iron_block run scoreboard players set @s 开箱品质 1
execute as @a at @s positioned ~ ~1.5 ~ if block ^ ^ ^1.75 beehive positioned ^ ^ ^1.75 if block ~ ~-1 ~ gold_block run scoreboard players set @s 开箱品质 2
execute as @a at @s positioned ~ ~1.5 ~ if block ^ ^ ^1.75 beehive positioned ^ ^ ^1.75 if block ~ ~-1 ~ diamond_block run scoreboard players set @s 开箱品质 3
execute as @a at @s positioned ~ ~1.5 ~ if block ^ ^ ^1.75 beehive positioned ^ ^ ^1.75 if block ~ ~-1 ~ emerald_block run scoreboard players set @s 开箱品质 4
```

**三层判定叠在一条命令里**：

| 层 | 写法 | 意思 |
|---|---|---|
| 视线 | `positioned ~ ~1.5 ~` + `if block ^ ^ ^1.75 beehive` | 眼前 1.75 格是不是蜂箱（箱子模型） |
| 挪到箱子 | `positioned ^ ^ ^1.75` | 把执行点挪到箱子那一格 |
| 脚下 | `if block ~ ~-1 ~ iron_block` | 箱子下面垫的是什么方块 = 品质 |

**用方块当参数**，不用计分板：改品质只要换垫块，不用改指令。这是第 67 章"方块当变量"的实战版。

### 88.2 运输矿车当奖池（`抽奖机2.0模板.txt`）

```
/scoreboard players set @e[type=chest_minecart] 抽奖 0
execute @e[type=chest_minecart,scores={抽奖=0}] ~~~ scoreboard players set @p[scores={金币=100..},x=●,y=●,z=●,r=2] 抽奖 1
execute @e[type=chest_minecart,scores={抽奖=0}] ~~~ scoreboard players set @p[scores={金币=200..},x=●,y=●,z=●,r=2] 抽奖 2
execute @e[type=chest_minecart,scores={抽奖=0}] ~~~ scoreboard players set @p[scores={金币=300..},x=●,y=●,z=●,r=2] 抽奖 3
```

**奖池 = 矿车里的物品**，抽奖 = 给玩家一个 `抽奖` 分数（1/2/3 档），
后面按分数决定给什么。`●` 是作者留的坐标占位符（**照抄必须换成真实坐标**）。

**`抽奖=0` 是防重入**：矿车还没被抽走，玩家靠近只结算一次。

### 88.3 奖品牌检测（`抽奖机5.0.txt`）

```
execute unless blocks ~14~1~ ~14~1~ ~11~~1 all unless blocks ~14~1~ ~14~1~ ~11~~ all run title @a[x=~15,y=~1,z=~-3,dx=1,dy=1,dz=4] actionbar §b物品检测中§f...
tp @e[type=item,x=~8,y=~,z=~-3,dx=3,dy=3,dz=4] ~10~1.2~-1
kill @e[name="§d一键三连",x=~10,y=~,z=~,dx=3,dy=3,dz=4]
```

`unless blocks A B all` = **两格方块不一样**（A 到 B 之间不全等）。
用来判断"奖品牌有没有被换过"。`blocks` 比 `block` 强在能一次比两端。

### 88.4 进度条开箱（`随机开箱2.0.txt`）

```
execute @a ~ ~ ~ detect ~ ~-0.1 ~ copper_block 0 tag @s add 进度
execute @a[scores={进度=1..}] ~~~ titleraw @s actionbar {"rawtext":[{"translate":"%%7","with":{"rawtext":[
  {"selector":"@s[scores={进度=10..}]"},
  {"selector":"@s[scores={进度=20..}]"},
  {"selector":"@s[scores={进度=30..}]"},...
```

`detect ~ ~-0.1 ~ copper_block 0` = 站在铜块上（`0` 是方块 data）。
`%%7` + 7 个递增选择器 = **7 段进度条**，进度到 10/20/30… 就多亮一段。
这是第 37 章条状图的最小实现，只有 1 条命令。

---

## 89. 商店、经济与回收

### 89.1 免举商店：脚下双层方块（`免举商店.txt`）

```
execute as @a[scores={购买=1..}] at @s if block ~ ~-1 ~ emerald_block run execute as @s at @s if block ~ ~-2 ~ barrel run tag @s add 购买
execute as @a[tag=!购买] at @s run scoreboard players add @s 购买 0
execute as @e[type=egg] at @s run playsound random.orb @p[r=2,c=1,tag=购买,scores={购买=1..}] ~~~ 1 2
```

**双层方块 = 商品 ID**：上面一层是价格档（绿宝石块 / 金块 / 钻石块），
下面一层是商品槽（木桶）。**站上去就选中**，不用菜单、不用抬头。
`egg`（鸡蛋）当"确认"的触发器。

**"免举"的意思**：不用举起物品、不用打开界面，走过去就买。适合大商城。

### 89.2 金币转账（`金币转账功能模板.txt`）

```
/scoreboard objectives add 金币 dummy
/scoreboard objectives add 金币a dummy
/scoreboard objectives add 转账 dummy
/scoreboard objectives add 转账a dummy
... (转账b/c/e/f)
/scoreboard players set 转账 金币 10
```

**6 个中间量**是因为 `operation` 只能两两运算，算一次转账要存好几步中间结果。
**假玩家 `转账` 存全局值**（汇率、手续费），所有玩家共用一份。

### 89.3 物资回收价目表（`hsid.txt`，最值得抄的表结构）

```
execute as @a[hasitem={item=gold_ingot}] at @s if block ~~~ yellow_carpet run scoreboard players add @s 回收 1540
execute as @a[hasitem={item=gold_ingot}] at @s if block ~~~ yellow_carpet run clear @s gold_ingot 0 1
```

| 列 | 例 |
|---|---|
| 中文ID | 贵金属工艺雕像 |
| 游戏内中文名 | 金锭 |
| 英文ID | `gold_ingot` |
| 价格 | 1540 |
| 完整指令 | 上面两行 |

**70 件物资 = 140 条命令**，一条加钱一条清物品。
`if block ~~~ yellow_carpet` = 站在黄地毯上才回收（防止误卖）。

**这张表就是 spec 该长的样子**：`(item, price)` 两列 → 生成器循环出 2N 条命令。
`build_tidegun.py` 的 `GUNS` 表是同一个思路。

### 89.4 一键回收 / 排行榜

```
tag @a[dx=●,dy=●,dz=●] add 回收
execute @a[hasitem={item=●,quantity=1..},tag=回收] ~~~ scoreboard players add @s "积分" ●
execute @a[hasitem={item=●,quantity=1..},tag=回收] ~~~ clear @s [物品ID 特殊值 数量1]

scoreboard objectives add 金币排行榜 dummy §eＣｏｉｎ꧂Ｒａｎｋｉｎｇ
execute as @a run scoreboard players operation @s 金币排行榜 = @s 金币
```

`dx/dy/dz` 是**区域选择器**（从执行点往正方向张开的长方体），比 `r=` 精确。
排行榜 = 每条计分项单独建一个，用 `operation` 每刻同步，`setdisplay list` 显示。
**计分项显示名可以带颜色码和全角字符**，这就是排行榜标题的来源。

---

## 90. 地皮、队伍、装卸、回城

### 90.1 假玩家当全局变量（`地皮系统2.0`）

```
execute @a[tag=创建] ~~~ scoreboard players operation @s 地x = "坐标x" 地x
execute @a[tag=创建] ~~~ scoreboard players add "坐标x" 地x 1
execute @a[tag=创建] ~~~ scoreboard players operation @s 地z = "坐标z" 地z
execute @a[tag=创建,scores={地x=101..}] ~~~ scoreboard players add "坐标z" 地z 1
```

**`"坐标x"` 是假玩家**（引号里不是真玩家名），当全局变量用：
每建一块地皮就 `+1`，新玩家从里面取当前值当地皮编号。
`101..` 是"这一行排满了，换下一行"。

**地皮保护**（`efdp.txt`）用区域选择器：

```
execute as @e[name="地皮保护",type=armor_stand] at @s run scoreboard players operation @a[dx=56,dy=1000,dz=56] 保护b -= @s 保护a
execute as @e[name="地皮保护",type=armor_stand,scores={保护a=1..}] at @s run tp @a[dx=56,dy=1000,dz=56,scores={保护b=!0,地皮x=0,地皮z=0},m=!1] 0 -60 0
```

`dx=56,dy=1000,dz=56` = 56×1000×56 的长方体。**地皮 = 一个盔甲架 + 一个区域选择器**。

### 90.2 `menu` 状态机（`组队系统.txt`）

```
execute as @a[scores={menu=5}] unless score @s 申请倒计时 matches 1.. run tag @s add 组队menu
execute at @a[tag=组队menu] run /playsound random.orb @p ~~~ 1 6
scoreboard players set @a[scores={menu=36..40}] menu 21
execute as @a[scores={menu=21..}] run titleraw @s actionbar {"rawtext":[{"text":"§2◁╢ §f组队系统 §2╟▷ §8Team-up system.
```

**`menu` 一个分数就是整个界面状态**：5 = 组队页，21 = 列表页，36–40 = 滚动区。
`36..40 → 21` 是越界回卷。**这就是第 34 章状态机菜单的真实实现。**

### 90.3 `xp_bottle` 当交互物（`虚拟装卸.txt`）

```
execute as @e[type=xp_bottle] at @s run scoreboard players add @p[r=1.8] 装卸菜单 1
execute as @e[type=xp_bottle] at @s run playsound item.book.page_turn @p[r=1.8]
execute as @a[scores={装卸菜单=2,装卸=0},rx=-88,tag=!装卸] at @s run tag @s add 装卸
```

**喷溅药水瓶当"按钮"**：扔出去 → 附近玩家 `装卸菜单 +1`。
`rx=-88` 要求抬头，`tag=!装卸` 防重复。

**为什么用 xp_bottle**：它落地就碎、不占空间、能被 `kill @e[type=xp_bottle]` 清掉，
而且**扔的动作本身就是输入**（不用命令方块）。

### 90.4 `%%9` 九段进度（`回城.txt`）

```
execute as @a[scores={计算=1..}] run titleraw @s actionbar {"rawtext":[{"translate":"%%9","with":{"rawtext":[
  {"selector":"@s[scores={e=..10}]"},
  {"selector":"@s[scores={计算=..20}]"},
  {"selector":"@s[scores={计算=..30}]"},...
```

**9 个参数、9 段进度**，`%%9` 从后往前剔除失败的组件。
这是第 29 章条件拼接的最完整实例：**一个 `%%9` 顶 9 条命令**。

### 90.5 防秒退（`防秒退狗系统.txt`）

```
/scoreboard objectives add 退 dummy
scoreboard players set @a[tag=战场] 退 1
```

**`tag=战场` 标记"进了战场"**，退出去这个 tag 还在 → `退=1` 就是秒退。
配合死亡检测（86.3）就能做"死了立刻退 = 判定逃跑"。

---

## 91. 数据化与 HUD

### 91.1 备份值体系（`数据化模板.txt`）

```
execute @e ~ ~ ~ scoreboard players operation @s 攻a = @s 攻
execute @e ~ ~ ~ scoreboard players operation @s 防a = @s 防
execute @e ~ ~ ~ scoreboard players operation @s 闪a = @s 闪
execute @e ~ ~ ~ scoreboard players operation @s 暴a = @s 暴
```

**每项属性配一个 `a` 后缀的备份**。用途：
- 基础值 `攻` 不变，临时加成写进 `攻a`
- 战斗结算只用 `攻a`，临时效果到期只要 `攻a = 攻` 一行还原
- **不需要"撤销 buff"逻辑**

**这就是数据化的核心**：`X` 是底子，`Xa` 是当前值。`build_tidegun.py` 的
`tg_temp` / `tg_mag` 是同一个模式。

### 91.2 T 显：手持 + 抬头（`数据化功能.txt`）

```
scoreboard players set @a[hasitem={item=writable_book,location=slot.weapon.mainhand}] T显 1
tag @a[hasitem={item=writable_book,location=slot.weapon.mainhand},rxm=88] add T显
tag @a[hasitem={item=writable_book,location=slot.weapon.mainhand},rx=-88] remove T显
```

**书与笔 = 打开状态栏**：手持书，`T显=1`；抬头到 88 度以内（`rxm=88`）显示，
抬头超过 88 度（`rx=-88`）关掉。

**为什么这么绕**：`actionbar` 是常驻的，没法"按一下显示"。
用 `T显` 分数当开关，HUD 命令全加 `scores={T显=1}` 条件，
就是**可开关的 HUD**。这是第 42 章刷新策略的实战解法。

### 91.3 状态栏 + 多段血条（`数据化T显.txt`，单行 2.7k 字）

```
{"translate":"%%1%%2%%3","with":{"rawtext":[
  {"translate":"%%9","with":{"rawtext":[
    {"selector":"@s[scores={血=0..}]"},
    {"selector":"@s[scores={血=50..}]"},
    {"selector":"@s[scores={血=100..}]"},
    {"selector":"@s[scores={血=150..}]"},
    {"selector":"@s[scores={血=200..}]"},
    {"selector":"@s[scores={血=250..}]"},
    {"selector":"@s[scores={血=300..}]"},
    {"selector":"@s[scores={血=350..}]"},
    {"text":"§r"},
    {"text":"§l§o§c||||||§7||||||||||||||§r"},
    {"text":"§l§o§c|||||§7|||||||||||||||§r"},
    ...
```

**`%%9` 套 `%%1%%2%%3`** = 两层查表：外层选"哪一档血条"，内层拼接。
8 档血量 → 8 个完整血条字符串，一次输出。

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
**`||||` 当格子**：比 `▮` 更细，一格能塞 20 个。这是第 38 章"参数上限"的解法——
**格子数不够就把字符变小**。

### 91.4 鱼竿枪 HUD（`子弹动态t显.txt`）

```
execute as @a[hasitem={item=fishing_rod,location=slot.weapon.mainhand}] run titleraw @s actionbar {"rawtext":[
 {"text":"§p▏§7 * §d鱼 竿 枪 §r 虚拟信息 §r>>> §r ＧＵＮ \n§7---..."},
 {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={换弹=1..}]"},{"text":"---------------------"}]}},
 ...
 {"translate":"%%9","with":{"rawtext":[
   {"selector":"@s[scores={zd百分比=1..10,换弹=0}]"},...
```

**弹匣百分比 → 10 档条**：`zd百分比` 预先算好（`zd*100/最大`），
再 10 个区间查表。**换弹时用 `%%2` 把整条替换成虚线**——同一个 HUD 两套外观。

### 91.5 字符条（`tx.txt`）

```
{"text":"§7ࡅࡅࡅࡅࡅࡅࡅࡅࡅࡅ"}
{"text":"§gࡅ§7ࡅࡅࡅࡅࡅࡅࡅࡅࡅ"}
```

**`ࡅ` 是极窄的竖线字符**，10 个并排只占 3 个汉字宽。
做"细长条"（食物、氧气）用它，`▮` 太胖。

---

## 92. 战斗单位

### 92.1 精英怪：攻击频率 + 随机模式（`精英怪1.0.txt`）

```
execute as @e[type=wither_skeleton,name="重锤战士"] at @s if entity @p[r=13] run scoreboard players add @s "攻击频率" 1
execute as @e[type=wither_skeleton,name="重锤战士",scores={攻击频率=100..}] at @s unless entity @s[scores={攻击模式=1..}] if entity @p[r=13] run scoreboard players random @s 攻击模式 1 5
scoreboard players reset @e[type=wither_skeleton,name="重锤战士",scores={攻击频率=100..}] 攻击频率
scoreboard players add @e[type=wither_skeleton,name="重锤战士",scores={攻击模式=1..}] 攻击时列 1
```

**AI 三段**：
1. 玩家在 13 格内 → `攻击频率 +1`
2. 攒到 100 且没有正在执行的模式 → `random 攻击模式 1 5`（随机选一招）
3. 频率清零，模式执行

**`攻击时列`** 是"这一招的第几帧"，用来做前摇/出招/收招。
**`unless entity @s[scores={攻击模式=1..}]`** 保证一招没打完不会选下一招。

### 92.2 Boss 技能模板（`副本boss技能制作模板.txt`）

```
execute @e[type=item,name="海洋之心",x=●,y=●,z=●,r=3] ~ ~ ~ tag @s add 召唤
tp @e[type=item,name="海洋之心",x=●,y=●,z=●,r=3,tag=召唤] 坐标♥
execute @e[type=item,name="海洋之心",tag=召唤] ~~50~ summon armor_stand 召唤 ~~~
scoreboard players add @e[type=armor_stand,name=召唤] 特效 1
```

**丢物品 = 放技能**：物品扔到指定坐标 → 打 tag → 传走 → 在头顶召唤盔甲架当特效锚点。
**盔甲架 `特效` 计数** 驱动粒子序列，比直接算坐标好调。

### 92.3 穷举拔刀剑（`穷举拔刀剑.txt`）

```
/execute as @a[scores={攻击类型=1,攻击执行=1..,攻击随机=1},hasitem={item=fishing_rod,location=slot.weapon.mainhand}] at @s positioned ^^1.43^3 run particle minecraft:balloon_gas_particle
/execute as @a[...] at @s positioned ^-0.9^0.53^3 run particle minecraft:balloon_gas_particle
/execute as @a[...] at @s positioned ^-0.6^0.83^3 run particle minecraft:balloon_gas_particle
/execute as @a[...] at @s positioned ^-0.3^1.13^3 run particle minecraft:balloon_gas_particle
```

**刀光 = 一条命令一个点**，`positioned ^x^y^z` 摆点，`攻击随机` 选形态。
这就是第 47 章刀光的原始出处，也是 `build_katana.py` 的设计来源。

---

## 93. 小工具

### 93.1 测距仪（`测距仪.txt`）

```
scoreboard players set @r[hasitem={item=compass,location=slot.weapon.mainhand}] d 1
execute at @a[scores={d=1}] run scoreboard players add @a[c=2] d 0
execute at @e[scores={d=1}] facing entity @e[scores={d=0}] feet run summon armor_stand ~~1000~ ~~ name 测量
```

`facing entity ... feet` = **面向某实体的脚**，配合 `summon ... ~~1000~` 拉一条线，
再用 `armor_stand` 的位置算距离。**`c=2`** 是"取两个"（自己和目标）。

### 93.2 两点填充（`两点填充.txt`）

```
execute if entity @a[hasitem={item=bat_spawn_egg,location=slot.weapon.mainhand,slot=0}] run setblock ~-1~~ chain_command_block 4
execute at @e[type=bat,name="选取方块",c=1] run clone ~ ~-1 ~ ~ ~-1 ~ 1000 100 1000 replace force
execute as @e[name="点"] at @s align xyz run tp ~0.5 ~0.5 ~0.5
```

**蝙蝠选点 → `clone` 到缓存区 → 再从缓存区 `clone` 回来**。
`align xyz` 把坐标对齐到方块中心（`~0.5`），否则填充会偏半格。
`replace force` = 覆盖不存在的方块。

### 93.3 撬棍：`detect` 长按（`撬棍开箱功能.txt`）

```
execute @a[hasitem={item=stick,quantity=1..,location=slot.weapon.mainhand},scores={撬棍=0..}] ^ ^1.5 ^1 detect ~ ~ ~ bedrock 0 scoreboard players add @s 撬棍 1
execute @a[hasitem={item=stick,quantity=..0,location=slot.weapon.mainhand},scores={撬棍=1..}]  ~ ~ ~ scoreboard players set @s 撬棍 0
execute @a[hasitem={item=stick,quantity=1..,location=slot.weapon.mainhand},scores={撬棍=1..}] ^ ^1.5 ^1 detect ~ ~ ~ air 0 scoreboard players set @s 撬棍 0
execute @a[hasitem={item=stick,quantity=1..,location=slot.weapon.mainhand},scores={撬棍=100..}] ^ ^1.5 ^1 detect ~ ~ ~ bedrock 0 fill ~~~~~~ air
```

**`detect` 是"看着某方块"**：`^ ^1.5 ^1 detect ~ ~ ~ bedrock 0` = 视线 1 格处是基岩。
- 看着基岩 → `撬棍 +1`（蓄力）
- 松开棍子 → 清零
- 看着空气 → 清零（移开视线就断）
- 攒到 100 → `fill` 破坏

**这是"长按破坏方块"的标准写法**，比 `player_action` 稳。

**25 种箱子存档**（`撬棍功能后续.txt`）：

```
structure save "箱子1" ~ ~1 ~ ~ ~1 ~ false disk true
structure save "箱子2" ~ ~1 ~ ~ ~1 ~ false disk true
...
```

`structure save <名> <起点> <终点> false disk true` —— `false` = 不含实体，
`disk` = 存到磁盘，`true` = 保存后**不删原方块**。

### 93.4 末影箱清除（`末影箱物品清除功能.txt`）

```
execute @a[scores={清箱=0}] ~~~ replaceitem entity @s slot.enderchest 0 air
execute @a[scores={清箱=0}] ~~~ replaceitem entity @s slot.enderchest 1 air
... (0..26)
```

**27 条命令清 27 格**。没有批量写法，`replaceitem` 一次只能一格。
`清箱=0` 是开关：设 1 就跳过整段。

### 93.5 读条（`道具使用系统.txt`）

```
execute as @a[scores={使用进度=1..}] unless entity @s[tag=手持道具] run title @s clear
execute as @a[scores={使用进度=72..}] at @s run title @s clear
execute as @a[scores={使用进度=1..}] unless entity @s[tag=手持道具] run scoreboard players reset @s 使用进度
execute as @a[scores={使用进度=100..}] at @s run scoreboard players set @s 使用进度 0
```

**读条三件套**：进度 +1（别处）→ 中断就 reset → 到 100 结算。
`unless entity @s[tag=手持道具]` = 换手就中断。

---

## 94. UI 原文

### 94.1 菜单 / 信息面板（`新建 DOCX 文档.txt`，50k 字）

```
tellraw @p[tag=使用,scores={菜单=0}] {"rawtext":[{"text":"｜§d〖 §f 信息面板 §lindividual§r§f.  ◆〉"}]}
execute @p[tag=机关] ~ ~ ~ title @s title §g◁§7།§f 交易市场 §7།§g▷
execute @a[scores={uid=0..}] ~ ~ ~ /playsound random.anvil_use @s ~ ~ ~ 10 1.3
```

**这是 UI 排版最好的参考**：`｜`、`〖〗`、`◆〉`、`◁ ། ▷` 这些符号的组合方式，
比手册第 33 章的模板更花，适合做"有品牌感"的界面。
`§l` 只包住一个词（`individual`），前后用 `§r` 复位——**局部加粗**的标准写法。

### 94.2 七品质色表（`物资系统 - 副本.txt`）

| 品质 | 颜色 |
|---|---|
| 损坏 | `§8` |
| 普通 | `§7` |
| 优良 | `§a` |
| 稀有 | `§b` |
| 史诗 | `§5` |
| 珍藏 | `§d` |
| 传说 | `§6` |

**全角数字**：`０１２３４５６７８９` —— 宽度一致，对齐比半角数字好。
价格、伤害、数量用全角，ID 和指令用半角。**这条要记住，是排版的隐规则。**

---

## 95. 原文里照抄会坏的地方

| 原文写法 | 问题 | 改成 |
|---|---|---|
| `execute @a ~~~ scoreboard ...` | 1.19.50 之前的老语法，新版本直接 `Syntax error` | `execute as @a at @s run scoreboard ...` |
| `testfor @e[type=fishing_hook]` | `testfor` 已废弃 | `execute if entity @e[...]` |
| `execute @a[...] ^ ^1.5 ^1 detect ...` | `detect` 被 `if block` 取代 | `execute as @a at @s if block ^ ^1.5 ^1 bedrock run ...` |
| `~~-500.5~` | 只是作者的基准常量，不是"必须 500" | 换 `~~-0.5~` 一样跑，按你的实体高度定 |
| `x=●,y=●,z=●` | `●` 是坐标占位符，**原样粘贴必失败** | 换成真实坐标 |
| `弹夹●` / `qx种类=●` | 同上，`●` 是"填你的数字" | 换成具体值 |
| `@e[type=boat]` 当子弹 | 船会堆在世界里 | 必须配 `kill @e[type=boat]` 清场链 |
| `playsound ... 17024 1.3 17024` | 音量/音高写 17024 = 极大值，能听见但会削波 | 写 `1 1.3 100`（100 是 minVolume 上限） |
| 中文计分项名不加引号 | `scoreboard players add @s 积分 1` 在部分版本解析失败 | `"积分"` 加引号最稳 |
| 一条链 300+ 方块 | 超出单区块加载范围 | 按功能分链 + `tickingarea` |

---

## 96. 从原文搬到 spec 的六步

1. **选型**：在 83 章找到同类，记下文件名
2. **读机制**：只看"触发 / 状态 / 结算 / 表现"四段，别逐行读
3. **抄骨架**：把四段的命令抄进 spec 的 `chains`，一条链一段
4. **换 ID**：`zd`→`tg_ammo`、`弹夹a`→`tg_mag`、`号码`→`uid`
5. **换坐标**：`●`、`~2~~`、`1000 100 1000` 全部重算
6. **补表现**：原文多半没音效/粒子（或只有 1 层），按第 55 章补到 2–4 层

**校验顺序**（缺一不可）：

```
python scripts/lint_commands.py spec.json        # 指令体检（@s 越界 / JSON / 音效 / 计分项）
python scripts/build_tidegun.py --spec spec.json --template _template.mcworld --out 世界.mcworld
python scripts/verify_mcworld.py 世界.mcworld     # 回读校验
python scripts/mcworld_to_structure.py --input 世界.mcworld --out 结构.mcstructure
```

---

## 97. 本部分索引

| 章 | 内容 |
|---|---|
| 82 | 怎么用（抄骨架的三条铁律） |
| 83 | 66 份总索引（按系统分组） |
| 84 | 枪械五条路线 + 换弹 + 33 枪声 + 散射 + 溢出回灌 |
| 85 | 伪无子弹：射程分数 / 逐格摆点 / 三段判定 |
| 86 | uid 归属 / `damage 0 override` / 死亡四行法 / 死亡盒子 |
| 87 | 建筑打印机：走格子 / `!` 负匹配查表 / 回卷 |
| 88 | 开箱品质 / 矿车奖池 / 奖品牌 / 进度条 |
| 89 | 免举商店 / 转账 / 回收价目表 / 排行榜 |
| 90 | 假玩家全局变量 / 地皮保护 / `menu` 状态机 / `xp_bottle` 交互 / 九段进度 |
| 91 | 备份值 / T 显开关 / 多段血条 / 字符条 |
| 92 | 精英怪 AI / Boss 技能 / 穷举刀光 |
| 93 | 测距 / 两点填充 / 撬棍长按 / 清箱 / 读条 |
| 94 | 菜单排版 / 七品质色表 / 全角数字 |
| 95 | 照抄会坏的 10 处 |
| 96 | 搬运六步 + 校验顺序 |
| 98 | 箱子 / 告示牌 / 物品 NBT（说明做进世界） |
| **99** | **伪无鱼竿枪真实原理：钩子=扳机 / `xp_orb`=载体 / 散射=旋转 / 射线命中** ★ |
| **100** | **换弹 `zd`/`zdmax` 双变量模型（单变量必无限装填）** ★ |
| **101** | **组队系统：`队伍uid` + 十进制键盘 + 空 `tp` 刷新** |
| **102** | **伪无判定 / 伪无粒子：同一套射线，穿透白名单 40 项** |

---
