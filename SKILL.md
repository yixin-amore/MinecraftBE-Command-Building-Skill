---
name: mcbe-command-blocks
description: "设计、编写与调试 Minecraft 基岩版（MCBE / Bedrock Edition，网易中国版 1.21.130）命令与命令方块链。覆盖基岩版指令语法、execute 子命令、目标选择器、dummy 计分板状态机、impulse/repeat/chain 命令方块、条件链、tick 延迟、C-tick 红石时序、mcfunction 与 tick.json、数据化 RPG（属性/伤害/T显）、FMBE/MBE 显示实体（playanimation + Molang）、杂项地图系统（菜单/商店/开箱/反作弊/小游戏），以及倒计时、商店、门锁、波次、队列等地图逻辑。Use for Bedrock command blocks, chain design, behavior-pack functions, and Bedrock command syntax. Do NOT use for Java Edition datapacks or Java-only syntax (data/NBT, attribute, bossbar, team, item components)."
whenToUse: "当用户要求网易版/基岩版/MCBE 指令、命令方块、命令方块链、计分板逻辑、行为包函数或地图小游戏机制时。"
---

# MCBE 命令与命令方块链

> **只适用于 Minecraft 基岩版（Bedrock Edition）**。Java 版的 `data`、NBT、`attribute`、`bossbar`、`team`、`item`、`forceload` 等在这里**不存在**。
> 目标版本：**网易我的世界 1.21.130（协议 898）**。命令边界以网易开发者文档 + 游戏内 `/help` 为准；
> 国际版 1.21.x 的部分新命令（`camera`、`inputpermission` 等）网易未验证，默认不要用。

## 0. 开工前先确认

1. **运行环境**：命令方块地图？行为包 + `tick.json`？还是聊天栏手动执行？
2. **触发方式**：玩家操作、红石信号、还是每 tick 轮询？
3. **玩家规模**：单人、本地联机、还是服务器（决定选择器与状态归属）。
4. **版本**：`/help` 里是否有目标命令；不同版本的方块状态名可能不同。

如果用户给的是 Java 语法，先翻译成基岩版；如果用户明确要 Java 版，说明本技能不适用。

## 1. 设计流程（按顺序做，不要跳步）

### 1.1 写清行为契约

用 6 行回答：**谁触发 / 起始状态 / 中间状态 / 结束状态 / 失败时怎样 / 如何重置**。
多人游戏还要写：状态是全局的还是每玩家的？玩家退出、死亡、迟到加入时怎么办？

### 1.2 建状态表

每个变量一行，先定状态再写命令：

| 变量 | 载体 | 归属 | 类型/范围 | 初值 | 谁写 | 谁读 |
|---|---|---|---|---|---|---|
| `#state` | 计分板 `arena` | 全局假玩家 | 0=idle 1=count 2=run | 0 | 开始/结束链 | 所有判断 |
| `@s.coins` | 计分板 `coins` | 每玩家 | int | 0 | 结算链 | 商店 |

**基岩版只有 `dummy` 计分板**，没有自动死亡/击杀/生命值统计。所有状态都要显式读写。

### 1.3 定时间模型

- 需要 **每 tick** 轮询 → `repeat` + `Always Active` + `Delay 0`（20 次/秒）。
- 需要 **每秒** 一次 → `repeat` 计数到 20 再复位，或 `repeat` + `Delay 20`。
- 需要 **红石上升沿** → `impulse` + `Needs Redstone`（按钮/拉杆/压力板）。
- 需要 **延迟 N tick** → `chain` 的 `Delay in Ticks`，或计分板倒计时（更可控、可暂停）。
- 需要 **跨 tick 的长流程** → 状态机 + 每 tick 推进，不要用超长链硬扛。

> 基岩版命令方块只在**偶数 tick（C-tick）**响应红石信号，所以红石时钟最高约 **10 次/秒**；`Always Active` 的 `repeat` 才能到 20 次/秒。

### 1.4 分阶段

一条链只做一件事，按固定顺序排：

```
INPUT → VALIDATE → TRANSITION → OUTPUT → CLEANUP
```

- **INPUT**：读按钮、物品、区域、分数。
- **VALIDATE**：用 `execute if ...` / 纯条件 `execute` 门禁；不通过时，后面的 Conditional 块会跳过（Unconditional 块仍会执行）。
- **TRANSITION**：改状态（计分板/标签/方块）。
- **OUTPUT**：标题、音效、粒子、给予物品、生成实体。
- **CLEANUP**：无条件复位临时标记（放在链尾，且设为 unconditional）。

### 1.5 排布

- 一条主干直线，`chain` 方块**背对**前一个方块（箭头指向下游）。
- 条件块必须紧挨在它的判断对象**正后方**；拐弯/分支后“身后”的方块会变。
- 分支用**并排的多条链**，或同一行里多个 `execute if ... run ...`（彼此不阻塞）。
- 每个方块命名（Hover Note）写成 `阶段.编号.作用`，方便调试。

### 1.6 写命令并自检

- 一条命令一行；命令方块里不用写开头的 `/`（写了也能用）。
- 选择器能窄就窄：`@e[type=zombie,tag=wave,c=1]`，不要裸 `@e`。
- 每个条件都用 `execute if/unless` 表达；纯条件 `execute if ...`（不带 `run`）本身就是合法门。
- 交付前跑一遍 `scripts/chain_lint.py`（见第 5 节）。

### 1.7 写测试计划

至少覆盖：单次触发、连续快速触发、边界值（0/最大值）、多人同时触发、玩家中途加入、区块卸载再加载、重置后再来一轮。

### 1.8 按请求类型调整输出

| 用户请求 | 输出 |
|---|---|
| “这条命令怎么写 / 为什么报错” | 直接给正确命令 + 1–2 个基岩版坑 + 一句验证方法，不要强行输出整套设计 |
| “帮我调试” | 先按 `references/debugging.md` 的三层诊断定位，再给最小修复 |
| “设计一个系统 / 命令方块链” | 走完 1.1–1.7，交付 design + spec + plan + tests |

不确定版本时，先说明假设（如“按 1.21.x”），并给出用 `/help` 验证的方法。

## 2. 不可违反的基岩版事实

| 事实 | 后果 |
|---|---|
| 没有 `data`、`nbt=`、实体/方块 NBT | 不能读写字条、箱子、实体 NBT；用计分板/标签/方块状态代替 |
| `execute` 只有 11 个子命令 | 没有 `store`、`detect`、`runasync`、`if data/items/predicate/biome/dimension/loaded` |
| 计分板只有 `dummy` | 没有 `deathCount`、`health`、`xp` 等自动准则；死亡/击杀要外部事件或自建检测 |
| 没有 `/team`、`/bossbar`、`/attribute`、`/item`、`/forceload` | 用 tag/计分板、titleraw/actionbar、effect、replaceitem、tickingarea 替代 |
| 网易未验证/未实装：`camera`、`inputpermission`、`dialogue`、`loot`、`place`、`recipe`、`scriptevent`、`fog` | 用 `camerashake`、`tp ... facing`、`title`、`structure`、`give` 等替代；详见 `references/netease-1.21.130.md` |
| `schedule` / `function` 在网易官方命令列表内 | 可以调度 Add-on 函数；服务器未启用函数时不要依赖 |
| 方块状态写作 `["state"="value"]` | `[facing=east]` 是 Java 语法，基岩版会解析失败 |
| 文本组件用 `{"rawtext":[{"text":"..."}]}` + `§` 颜色码 | Java 的 `color`、`clickEvent`、`hoverEvent` 不可移植 |
| 红石只在偶数 tick 响应 | 红石时钟最高 10 Hz；`Always Active` 的 repeat 才是 20 Hz |
| 条件链检查的是**身后方块**的成功次数 | 链式条件只反映紧邻前驱；条件失败仍会把触发传给下一个方块 |
| 链式循环每 tick 最多执行一次 | 环状链不会在同一 tick 内无限循环 |
| 命令方块只在加载/常加载区块运行 | 远处机关要用 `tickingarea` |
| 命令文本上限 32,500 字符 | 超长命令要拆成函数或多个方块 |
| 函数单次调用最多 10,000 条命令 | 大循环要分 tick，不能靠函数递归硬跑 |

**网易 1.21.130 特别提醒**：

- `schedule` **有**（网易官方命令列表明确列出），不要删；它调度的是 Add-on 函数。
- 样本里大量导入图仍用旧 `execute @a ~ ~ ~` 语法；新图一律用 `execute as ... at ... run ...`，旧图先手工升级。
- `tickingarea`、`structure`、`testfor`/`testforblocks`、`titleraw`、`camerashake`、`playanimation`、`event`、`damage` 在网易地图中实际使用，属于可用集合。
- 详细边界见 `references/netease-1.21.130.md`。

## 3. 命令方块速查

### 3.1 三种类型

| 类型 | 颜色 | 触发 | 典型用途 |
|---|---|---|---|
| `Impulse` | 橙 | 每次被激活一次 | 按钮、拉杆、一次性事件 |
| `Repeat` | 紫 | 激活期间每 tick（或每 delay tick） | 时钟、轮询、状态机推进 |
| `Chain` | 青 | 被前一个方块触发 | 顺序执行的步骤 |

### 3.2 基岩版五个关键设置

| 设置 | 取值 | 默认 | 说明 |
|---|---|---|---|
| Block Type | Impulse / Chain / Repeat | Impulse | 见上表 |
| Condition | Unconditional / Conditional | Unconditional | Conditional 检查**身后**方块成功次数 > 0 |
| Redstone | Needs Redstone / Always Active | Impulse/Repeat 默认 Needs；Chain 默认 Always | Chain 的 Always Active 只免除红石，仍要前驱触发 |
| Delay in Ticks | 0..N | 0 | Impulse/Repeat 的 0 与 1 等效；Chain 的 0（同 tick）与 1（下一 tick）不同 |
| Execute on First Tick | 开/关 | 开 | 仅 Repeat：激活后是否立刻跑第一次 |

### 3.3 执行时序（背下来）

```
同一 tick：
  repeat 执行 → 触发它面前的 chain → chain 按顺序逐个执行
  条件 chain 检查“身后”方块成功次数；失败则不执行，但仍触发下一个
  每个 chain 每 tick 最多执行一次（环只走一圈）

带 delay：
  chain 在 delay 后继续；不要用“条件失败”来截断整条延迟链，
  条件只决定该方块自己是否执行。需要截断就加一个显式门方块。
```

### 3.4 成功次数不是 0/1

基岩版命令方块的成功次数是**受影响的数量**（玩家数、方块数、命令返回值），不是 Java 的 0/1。
所以 `execute as @a[...] run ...` 后面的 conditional chain 可以当“有没有人”的门；比较器也能读出这个数。

## 4. 状态、门与常用配方

### 4.1 全局状态 vs 每玩家状态

```mcfunction
# 全局：假玩家，名字以 # 开头，不会出现在侧边栏
scoreboard players set #state arena 1
scoreboard players add #tick arena 1

# 每玩家：@s 或具体玩家名
execute as @a run scoreboard players add @s coins 1
execute as @a[scores={coins=10..}] run ...
```

### 4.2 四种门

```mcfunction
# AND：两个条件都成立
execute if score #a obj matches 1 if score #b obj matches 1 run say both

# OR：任一成立（先置标记，再判断）
execute if score #a obj matches 1 run scoreboard players set #flag obj 1
execute if score #b obj matches 1 run scoreboard players set #flag obj 1
execute if score #flag obj matches 1 run say either

# NOT
execute unless entity @e[type=zombie,tag=wave] run say cleared

# 纯条件门（不带 run）：成功则让后面的 conditional chain 继续
execute if score #stock shop matches 1..
```

### 4.3 计数器、倒计时、冷却

```mcfunction
# 每秒时钟
scoreboard players add #tick arena 1
execute if score #tick arena matches 20.. run scoreboard players set #tick arena 0

# 倒计时（只在 >0 时减）
execute if score #count arena matches 1.. run scoreboard players remove #count arena 1

# 冷却（每 tick 减，到 0 停止）
execute if score #cd obj matches 1.. run scoreboard players remove #cd obj 1

# 取模翻转 0/1
scoreboard players operation #state obj %= #two obj
```

### 4.4 分支不要用条件链硬串

错误直觉：`if 不成立 → 后面都不执行`。
实际：条件块失败会**继续触发**下一个块；下一个块若是 unconditional 就会执行。
所以分支写成彼此独立的 `execute if ... run ...`，或用独立链，不要指望“断链”。

### 4.5 FMBE/MBE 显示实体

用狐狸/盔甲架 + 主手/副手物品 + `playanimation` + Molang 伪装方块或模型：

- **FMBE**：狐狸 + 主手物品；1 条初始化 + 7 条变量/姿态 `playanimation`（共 8 条）；一实体一显示。
- **MBE**：盔甲架 + 副手物品；命令更少，但有碰撞箱。
- **SMBE / SMBE-EX / SDME**：社区变体；SDME 在网易当前不可用。
- 前置：成年狐狸、`replaceitem`、`tag`、隐身/抗性/消音、`tickingarea`、`structure save/load`。
- 变量：`v.xpos/ypos/zpos`（1/16 格）、`v.xrot/yrot/zrot`（度）、`v.scale/xzscale/yscale`、`v.xbasepos/...`。
- 每条 `playanimation` 的顺序不能乱；第一条控制器必须是 `controller.animation.fox.move`。
- 显示是客户端视觉，不能当方块检测；一个方块一个实体，先算性能预算。
- 完整前置、8 条命令、变量表、MBE 尺寸/旋转、例子拆解见 `references/fmbe-mbe.md`。

### 4.6 数据化 RPG 属性系统

“数据化”是用 dummy 计分板把生命/攻击/防御/暴击/等级/经验/装备加成变成可计算、可显示的数值：

- 分层：**基础属性 + 装备加成 + Buff = 最终属性**；装备层每 tick 先清零再重建，不要把最终值写回基础值。
- 伤害事务：先给目标 `tag=被攻击`，再算 `攻击 - 防御`，最低 1；暴击/浮动/吸血按固定顺序；结束清 tag，一击只结算一次。
- 生命：clamp 到 `0..最大生命`；死亡先设 0 再 `kill`，经验只给 uid 匹配的击杀者。
- T显：`titleraw actionbar` + score 组件；限频（5~10 Hz）、按需显示（低头/手持面板）；普通 `title` 纯文本约 512 字节会静默失败。
- 隐藏原版 HUD 用 `hud`；网易官方列表未列，先 `/help hud` 验证。
- UID 用 `@r[scores={uid=0}]` 分配；击杀归属不要用玩家名。
- 装备/词条：物品只是外观，数值在计分板；`hasitem` 读槽位，注意胸甲是 `slot.armor.chest`。
- 完整属性层、伤害链、T显/血条、等级/经验、装备/怪物、性能与旧语法升级见 `references/dataization-rpg.md`。

### 4.7 杂项地图系统（菜单/商店/开箱/反作弊/小游戏）

- **菜单/选人**：鸡蛋/雪球/纸做无 UI 按钮，一个整数 objective 存页面，`rxm=88` 低头关闭、`rx=-88` 抬头确认；选人用 `选人` 从 -1 递增 + `tag=选中`。
- **公告栏**：sidebar + 假玩家“行名” + 定期 `remove/add` objective 清旧行；比每 tick `titleraw` 省。
- **商店**：木桶装商品，`clone` + `setblock air destroy` + `tp` item；批量用数字键盘分数；折扣 `价格*折扣/100`。
- **开箱**：进度 + `random` + `clone`/`structure load` + `tp` item + `clear` 钥匙；多人共用输出位会拿错物品。
- **反作弊**：反穿墙用 XP 球探针 + `VL`；防矿透用矿物年龄 + 附近玩家分 + 衰减 + 阈值审核；都只当嫌疑分，不要自动永封。
- **领地/卡密门**：领地是 NPC+基岩+编号+推开，不是真正方块保护；卡密门用 `^^1^` 检查面前铁门 + 蜡烛钥匙。
- **小游戏**：匹配区计数+倒计时；四队按最低人数均衡；密室杀手用角色分数+`@r` 分配；死亡动画用“立即重生 + 自己位置无玩家实体”检测。
- **拔刀剑**：钓鱼钩触发、副手 `data` 武器 ID、盔甲架 `n/旋转` 定方向、粒子+`damage`；`kill` 钩子收尾。
- **触屏坐标**：烟花火箭当屏幕射线，`positioned ^100000^^` + `r` 左右/上下二分，归一化成 0..100 的屏幕比例；分辨率/FOV 变了要重校准。
- 完整套路、代码骨架、文件索引和坑见 `references/misc-map-systems.md`。

### 4.8 一遍过交付（实测校准）

目标不是“命令写对”，而是“到服务器能跑、能看、不卡”：

- **执行位置**：命令方块远离展示区时，别用 `r/rm` 选实体；用 `x/y/z/dx/dy/dz` 或 `execute positioned`。
- **导入**：BuildTask 之后**逐块 `CommandBlockUpdate` repair**；只摆方块不算导入成功。
- **性能**：FMBE 不要 20 Hz 跑 48 条 Molang；初始化一次 + 1 Hz 刷新 + 每 tick 锚定。
- **实体**：`summon fox` 不要带 name/event 参数；用普通 summon + tag；`hasitem` 查实际 ID（`player_head` 不是 `skull`）。
- **UI**：`title` 纯文本约 512 字节；大面板用 `titleraw`；菜单只发 actionbar，不弹大标题。
- **视觉**：无头 bot 不能看客户端模型；功能可一遍过，视觉需要一张截图校准 `v.ypos/v.zpos/v.xpos`。
- 完整清单和两次交付（雪球菜单 / FMBE 玩家）的坑见 `references/one-pass-delivery.md`。

### 4.9 生成 BDX / MCWorld

- **BDX** = `BD@` + brotli(`BDX` + `0x00` + `0x00` + command-stream + `ID 88`)；author 保持空（非空实测被读取器判无效）；不是 NBT，也不是 zip。
- 命令方块用 `PlaceBlockWithCommandBlockData`（ID 27）：block name string ID、facing+conditional、mode、command、delay、flags；坐标用 AddInt32X/Y/Z 相对移动。
- 技能脚本 `scripts/bdxgen.py` 可把 `Block` 列表写成 BDX；普通方块/箱子用完整结构 writer。
- **MCWorld** = zip 根目录 `level.dat` + `levelname.txt` + `db/`；不要手写 LevelDB，用 `world.Open` + `BDX.ToMCWorld`。
- 生成后必须回读：BDX 用 `mcbeextract`/`BDX.FromFile`；MCWorld 用 `world.Open` + `LoadNBT` 检查 `id=CommandBlock`。
- 完整格式、代码、坑和实测见 `references/bdx-mcworld-generation.md`。

### 4.10 BDX 命令链打包：盘旋与初始化分离

**交付纪律**：先冻结 spec，生成完整 BDX，离线回读；服务器只做验收，不边调边交付。

- **单区块盘旋**：命令方块按 16×16 水平格蛇形排布，行尾折返；不同链放不同垂直层，避免互相指向。
- **初始化分离**：
  - 一次性初始化（计分板、tickingarea、生成实体/部件）用 **impulse + chain**；
  - 持续逻辑用 **repeat + chain**；
  - FMBE 的 `playanimation` 属于持续前置，必须放在**独立 repeat 链**，不能塞进普通初始化。
- **触发**：repeat 主链首条在 `(x0,y0,z0)` 放红石块，impulse 头放 `(x1,y0,z0)` 并设 Needs Redstone。
- **FMBE 小坑**：部件 tag 体积要独占（0.4×0.4×0.4），不能重叠；部件 fox 每轮要 `tp` 锚定，防重力/挤压散架。
- **交付包**：BDX + StartPos + 单区块 tickingarea + 依赖建筑说明。
- 完整布局、验证、验收见 `references/bdx-chain-packaging.md`。

### 4.11 多思考、联动、创造性

接到“设计一个系统/地图/菜单”时，先走思考协议，再写命令：

- **先问 6 个问题**：玩家在做什么、看到什么、服务端跑什么、最小闭环、和什么联动、最可能怎么坏。
- **先发散再收敛**：稳健 / 联动 / 大胆 3 个方向，用新鲜感、一致性、可落地、性能、可读性、可测试 6 维选。
- **联动矩阵**：触发→状态→数据→表现→空间→成长→社交→保护；一个系统的输出要成为另一个系统的输入。
- **创造性技巧**：SCAMPER、反转、约束、类比、叙事、奇观、复用已有系统。
- **红队**：多人、性能、逃课、误判、可读性、重置、网易边界。
- **最小闭环优先**：一个触发/状态/反馈/重置跑通，再加第二技能/阶段/地图。
- 先给“目标/3 方向/推荐/联动图/闭环/风险”，确认后再开工；模板见 `assets/design-brief.template.md`。
- 完整方法、评分表、联动样例见 `references/creative-thinking.md`。

### 4.12 建筑/语料学习

用户给大量建筑/指令文件时，先建索引，不要逐文件读：

- **资产分四类**：schematic/schem、BDX、参考图、目录分类。
- **索引**：`scripts/sunrain_index.py` 输出 index.jsonl / stats / catalog / contact sheet；查询用 `scripts/corpus_query.py`。
- **归类三层**：功能（主城/Lobby/空岛/起床/玩法）、风格（中式/日式/中世纪/现代/幻想）、元素（塔/桥/树/内饰/灯光）。
- **风格卡**：尺寸、轮廓、Palette Top、层高、细节密度、动线、可借鉴/不照搬。
- **模仿**：至少改 3 个约束（场地/功能/尺度/母题/材质），保留结构逻辑，不复制坐标。
- **建造顺序**：场地→体块→屋顶→立面→材质→内部→内饰/灯光→环境→截图→导出。
- 完整方法见 `references/building-corpus-learning.md` 和 `references/building-design.md`；模板 `assets/building-brief.template.md`。

### 4.13 内饰设计

室内不是“把家具摆满”，先定功能/动线/焦点/层高：

- **1/3/5 法则**：1 个主焦点、3 个层次（地面/家具/顶部）、每 5~8 格一个变化。
- **先空壳后家具**：先做墙/柱/屋顶/地面，再放座椅/柜台/祭坛；主通道 ≥2 格。
- **光**：暖色吊灯/壁灯 + 冷色彩窗；要有明暗，不要全屋插火把。
- **材质**：地面/墙面/顶部/强调四层；≤5 家族，强调 ≤10%。
- **教堂**：narthex→nave→aisles（侧祭坛/忏悔室）→transept→choir→apse；肋拱+吊灯+彩窗。
- **高级 pass**：切深窗洞、slab 肋拱、rood screen、pulpit、altar rail、mural、censer、地面金带；block states 先实测。
- **检查**：入口识别、主路径不堵、焦点层次、家具尺度、多人碰撞、性能。
- 完整清单、模板、反模式见 `references/interior-design.md`；模板 `assets/interior-brief.template.md`。

### 4.14 亮眼/奇观设计

用户说“不够亮眼”时，不要只加方块：

- 先给 3 个方向（稳健/联动/大胆），选一个**主焦点**。
- 6 个杠杆：剪影、尺度对比、色彩对撞、发光体、运动/声音、叙事焦点。
- 夜景：檐口/扶壁/塔尖 lantern/sea_lantern；内部吊灯/浮空烛/祭坛发光十字；主焦点亮 2~3 档。
- 避免土味：颜色 ≤5 家族；粒子/钟声只放 2~3 个点，节流。
- 工程：fill + 隐藏命令方块；先离线渲染，再服务器回读。
- 详见 `references/spectacle-design.md`；教堂案例见 `references/gothic-cathedral-case.md`。

## 5. 交付物与工具

被要求设计命令方块链时，**不要只丢一堆命令**。交付：

1. `design.md`：行为契约、状态表、时序、ASCII 排布、失败/重置路径。
2. `spec.json`：按 `assets/chain-spec.schema.json` 描述每个方块（类型、条件、红石、延迟、命令、next）。
3. **运行 linter**：

   ```bash
   python3 scripts/chain_lint.py spec.json --format markdown
   ```

   把输出的构建表（方块顺序、设置、坐标、命令）和错误/警告一并交付。
4. 测试清单（单次/连续/边界/多人/重载/重置）。
5. 游戏内搭建步骤：先放哪个、朝哪、每个方块的设置、需要的计分板与 gamerule。

linter 会检查：Java 残留语法、Bedrock 不存在的命令/选择器参数、条件链拓扑、孤立块、环、相邻性、红石频率、延迟语义、`dummy` 计分板误用等。

### 交付模板

```markdown
## 设计：<名字>

### 1. 行为契约
- 触发 / 起始状态 / 结束状态 / 失败行为 / 重置

### 2. 状态表
| 变量 | 载体 | 归属 | 范围 | 初值 | 写入 | 读取 |

### 3. 时序与链图
- 时钟：20 Hz / 10 Hz / 事件驱动
- 链图（repeat → chain → ...）
- 延迟/超时/取消

### 4. 构建表
| # | 方块 | 类型 | 条件 | 红石 | 延迟 | 坐标/朝向 | 命令 |

### 5. 测试
- [ ] 单次 / 连续 / 边界 / 多人 / 重载 / 重置
```

## 6. 回答前自检

- [ ] 每条命令都能在基岩版解析（没有 Java 残留）。
- [ ] 每个链段都有明确的头（`repeat` 或 `impulse`），没有孤立 `chain`。
- [ ] 条件方块紧贴在判断对象的正后方；拐弯处重新确认“身后”。
- [ ] 每个状态变量都有初值、写入点和清理点。
- [ ] 多人：选择器不会把 A 的状态用到 B 身上。
- [ ] 区块加载：远处机关有 `tickingarea`。
- [ ] 时序：红石 10 Hz vs Always Active 20 Hz 说清楚。
- [ ] 存在重置路径，且重置链本身不会被旧状态卡住。
- [ ] 已运行 linter，0 error。

## 7. 参考文件导航

| 文件 | 什么时候读 |
|---|---|
| `references/command-block-mechanics.md` | 需要精确的方块时序、条件链、成功次数、限制 |
| `references/chain-patterns.md` | 要选型：时钟、门、状态机、队列、波次、冷却 |
| `references/bedrock-command-reference.md` | 查某条命令的基岩版语法和坑 |
| `references/execute-and-selectors.md` | 写 `execute`、选择器、条件表达式 |
| `references/scoreboard-memory.md` | 用 dummy 计分板存状态、做数学、编码 |
| `references/text-ui-and-effects.md` | 标题、actionbar、tellraw、音效、粒子、camerashake、playanimation |
| `references/fmbe-mbe.md` | FMBE/MBE 显示实体：前置、8 条链、变量、MBE、SMBE 变体、例子拆解 |
| `references/dataization-rpg.md` | 数据化 RPG：属性分层、伤害事务、T显/血条、等级/经验、装备/怪物、性能与旧语法升级 |
| `references/misc-map-systems.md` | 杂项地图系统：菜单/选人、商店/彩票、开箱、反作弊/领地/卡密门、匹配/密室、拔刀剑、死亡动画 |
| `references/one-pass-delivery.md` | 一遍过交付：执行位置、导入 repair、性能、实体/物品、UI、视觉校准清单 |
| `references/bdx-mcworld-generation.md` | BDX 命令流 / MCWorld zip+LevelDB 的生成、回读与坑 |
| `references/bdx-chain-packaging.md` | BDX 打包：单区块盘旋、初始化/FMBE/主体分离、验收 |
| `references/building-design.md` | 建筑设计：场地/体量/轮廓/材质/立面/屋顶/动线/建造顺序 |
| `references/building-corpus-learning.md` | 建筑/指令语料：索引、归类、风格卡、模仿、建造 |
| `references/gothic-cathedral-case.md` | 案例：300 样本→哥特教堂重做、fill 导入、回读 |
| `references/interior-design.md` | 内饰：动线/焦点/分层/光/材质/教堂模板/检查表 |
| `references/spectacle-design.md` | 亮眼/奇观：剪影/对比/发光/运动/声音/反土味 |
| `references/creative-thinking.md` | 多思考/联动/创造性：6 问、3 方向、联动矩阵、红队、最小闭环 |
| `references/functions-and-packs.md` | 行为包、`.mcfunction`、`tick.json`、manifest、schedule |
| `references/debugging.md` | 链不跑、条件不触发、多人异常、重载失效 |
| `references/bedrock-vs-java.md` | 用户给的是 Java 语法，或需要差异速查 |
| `references/netease-1.21.130.md` | 网易命令边界、`schedule` 结论、未验证命令、旧语法升级 |
| `assets/chain-spec.schema.json` | 写 spec.json 时 |
| `examples/` | 需要完整范例：倒计时、商店、开关灯 |

## 8. 主要事实来源

- [Command Block — Minecraft Wiki](https://minecraft.wiki/w/Command_Block)（类型、条件、延迟、C-tick、链式触发）
- [Commands/execute — Minecraft Wiki](https://minecraft.wiki/w/Commands/execute)（基岩版 11 个子命令、深度优先 fork）
- [Target selectors — Minecraft Wiki](https://minecraft.wiki/w/Target_selectors)（基岩版参数：`r/rm`、`c`、`family`、`hasitem`、`haspermission`）
- [Commands/scoreboard — Minecraft Wiki](https://minecraft.wiki/w/Commands/scoreboard)（仅 `dummy`、`random`、`test`、`operation`）
- [Function (Bedrock Edition) — Minecraft Wiki](https://minecraft.wiki/w/Function_(Bedrock_Edition))（`tick.json`、10,000 条限制）
- [Minecraft Creator Docs — Commands](https://learn.microsoft.com/en-us/minecraft/creator/commands/)（各命令的基岩版签名）
- [网易开发者官网 — 命令列表及概述](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/10-addon教程/第04章：指令系统，你的创作管家/课程04.命令列表及概述.html)（网易 1.21.130 命令边界；明确列出 `schedule`，标注 `fog` 未实装）
