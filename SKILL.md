---
name: mcbe-command-blocks
description: "Minecraft 基岩版（网易 1.21.130）命令 + 建筑双栈。建筑：场地与体量（631/黄金比例）、四层立面、屋顶塔尖、材质板、内饰动线、灯光、奇观、地形；brief→ArchSpec/ArchBuilder→体素→预览→schematic/BDX/mcstructure/fill 批。命令：DSL→spec→cbc、execute/选择器、dummy 计分板状态机、impulse/repeat/chain、条件链、C-tick、BDX、FMBE/MBE、数据化 RPG、菜单/商店/门锁/波次等地图逻辑；UI/音效：24 版式、动效、分层音效与旋律目录。Use for Minecraft building/architecture (cathedral, castle, lobby, interior, terrain, landmark, schematic/BDX/fill) AND Bedrock command blocks/command systems. 静态建筑不要用命令方块逐块搭建；命令栈只做动态机关/交互/演出。Do NOT use for Java Edition datapacks or Java-only syntax."
whenToUse: "当用户要求网易/基岩版/MCBE 指令、命令方块链、计分板逻辑、BDX，或设计/建造/改造 Minecraft 建筑（教堂、城堡、主城、大厅、内饰、地形、地标）、按参考图/结构复刻、导出 schematic/BDX/mcstructure/fill，或设计游戏内 UI/菜单/HUD/音效时。"
---

# MCBE 命令与命令方块链

> **双栈，不是主从**：
> - 命令系统：`DSL → spec → cbc → 结构文件`；只负责动态机关、交互、演出。
> - 静态建筑：`brief → ArchSpec/ArchBuilder → 体素 → 预览 → schematic/BDX/mcstructure/fill`。
>
> **硬规则：静态建筑不要用命令方块逐块搭，也不要用 `setblock`/`fill` 命令链做几何作者层。** 命令方块是动态层；`fill` 只作为体素生成后的投放通道。

## 0.0.0 坐标策略：默认相对（硬规则）

> **所有新生成命令默认使用相对坐标。** 绝对坐标只用于世界锚点、固定结构原点、传送点，并显式标注 `ANCHOR`。

```text
默认：~ ~ ~ / ^ ^ ^ + execute as/at/positioned
例外：ANCHOR: <x y z>
```

写命令前先确定：

1. 执行者是谁：玩家 / 实体 / 命令方块 / execute 源；
2. 需要世界轴 `~` 还是局部朝向 `^`；
3. 选择器是否也用相对坐标；
4. 多命令是否共享同一个 `execute positioned` 源；
5. 绝对坐标是否只是锚点/BDX 放置点。

禁止：

```mcfunction
setblock 100 64 100 minecraft:stone
```

默认：

```mcfunction
execute as @p at @s run setblock ~ ~-1 ~ minecraft:stone
```

完整规则、示例、反例见 `references/38-relative-coordinates.md`。

## 0.0.1 建筑任务入口（与命令系统并列）

先判断任务：

| 任务 | 默认栈 | 产物 |
|---|---|---|
| 静态建筑 / 内饰 / 地形 / 地标 | **ArchSpec / ArchBuilder** | brief + spec + front/top/iso + `.bdx` / `.mcstructure` / `.schematic` + report |
| 大体积投放 | 体素 / BDX / `fill` 批（按使用方导入规范拆分） | fill 清单 + 文件回读点 |
| 可复用模块 | schematic / AuroraBuild | `.schematic` + 放置坐标 |
| 动态机关 / 门 / 演出 / HUD | 命令栈（0.0） | `spec.json` + `cbc.py` + `.mcworld` / BDX |
| 交互建筑的“动”部分 | 建筑栈做体量，命令栈只做触发 | 两者分开交付 |

**禁止**：

- 用 `setblock` / `fill` 命令链手工设计/逐块搭静态建筑（`fill` 仅可用于已生成体素的投放）；
- 用命令方块、FMBE、`playanimation` 当建筑主结构；
- 用 `cbc.py` 排建筑体量。

**建筑 6 问**：场地 / 风格 / 尺度 / 功能 / 主焦点 / 硬约束（版本·性能·高度·投放方式）。

**最小交付**：

```text
brief（场地/体量/焦点/材质）
→ spec（ArchSpec 或 builder 参数）
→ front/top/iso 三视图
→ report（bounds/blocks/issues=0）
→ 文件清单（BDX / mcstructure / schematic / fill 批 + 回读点）
```

如果用户明确要求“用命令方块建静态建筑”，先说明代价（链数、tickingarea、64×64×100、每 tick 预算），再建议建筑栈；只有小体量互动装饰才允许命令方块。

**提示模板**：

```text
用建筑栈做：<类型>，场地 <W×D>，风格 <...>，功能 <...>，
主焦点 <...>，硬约束 <高度/材质/性能/版本>，
输出 brief + spec + front/top/iso + report + 可导入文件清单。
不要用命令方块逐块搭静态体量。
```

## 0.0 语言优先工作流（命令系统默认）

```text
需求
  ↓
corpus_search        找同类实现/命名
  ↓
dsl.py               结构化选择器 / execute 上下文 / 动作
  ↓
spec.json            链、计分项、条件、布局
  ↓
cbc.py               三段式断链 / 条件块 / 宽度 / 链头
  ↓
build_cbworld        .mcworld
  → mcworld_to_structure
  ↓
真机回读             实体 / 计分 / 链 / 位置
```

### 默认命令

```bash
python3 scripts/command_syntax.py execute --version netease-vanilla
python3 scripts/corpus_search.py '拔刀剑' --category weapon --limit 5
python3 scripts/example_dsl.py --dump-spec demo.json
python3 scripts/build_pipeline.py --build-script build_x.py --outdir out --name X
```

### 任务路由

| 任务 | 先查 | 生成 |
|---|---|---|
| 命令格式/参数 | `references/command-syntax.json` | `scripts/command_syntax.py` |
| 武器/拔刀剑/鱼竿枪 | `corpus_search weapon` | `dsl.py` + `build_cbworld.py` |
| 数据化/属性/T显 | `corpus_search data` | `dsl.py` + `cbc.py` |
| 菜单/公告/HUD | `references/30-command-ui-design.md` + `31-command-ui-modern.md` + `32-ui-sound-design.md` | `Tellraw/Title` + 动作栏/副标题 |
| 商店/开箱/经济 | `corpus_search economy` | inventory/scoreboard/structure |
| 音效/打击感/旋律 | `references/32-ui-sound-design.md` §6–§7 | `playsound` + 白名单 + 时间轴 |
| 传送/圆规/二分 | `corpus_search teleport/math` | `positioned/rotated/facing` |
| FMBE/展示体 | `references/24-fmbe-model-ir.md` + `34-fmbe-compiler.md` | `scripts/fmbe_compile.py` |
| NXS/递归几何 | `references/23-nxs.md` + `36-nxs-compiler.md` + `37-nxs-program.md` | `scripts/nxs_compile.py` / `nxs_program.py` |
| BDX/文件 | `references/25-bdx-bridge.md` | `cbjson_to_bdx.py`（文件回读） |
| 建筑类型/风格 | `references/33-architecture-typology.md` + `29-architecture-corpus.md` | `scripts/arch_style.py` |
| 建筑组件 | `references/35-architecture-components.md` | `scripts/arch_compile.py` |
| 山水/园林 | `references/33-architecture-typology.md` §8 | `Site` + `Water/Rock/Plant` 模块 |

### 三层资料

| 层 | 路径 | 用途 |
|---|---|---|
| 语料 | `work/command-corpus/`（2,517 文件 / 1,644 训练记录；可用 `CMD_CORPUS` 指定） | 意图/命名检索；不照抄旧字符串 |
| 语言优先参考 | `references/mct-playbook.md` + `references/mct/` | DSL / cbc / 链布局 / UI / 调试全表 |

### 边界

- FMBE/NXS 目前有 IR/矩阵/参考，**还不是完整编译器**；不要声称已全自动。
- **交付边界**：本 skill 只负责生成 `.bdx` / `.mcstructure` / `.schematic` / fill 清单；导入由使用方负责，导入失败不计入 skill 缺陷。
- BDX 命令方块桥已文件回读 99/99；文件格式、命令文本、条件位、红石位已核对。
- 本 skill 后半的建筑/BDX 章节保留；命令系统优先 0.0。



> **只适用于 Minecraft 基岩版（Bedrock Edition）**。Java 版的 `data`、NBT、`attribute`、`bossbar`、`team`、`item`、`forceload` 等在这里**不存在**。
> 目标版本：**网易我的世界 1.21.130（协议 898）**。命令边界以网易开发者文档 + 游戏内 `/help` 为准；
> 国际版 1.21.x 的部分新命令（`camera`、`inputpermission` 等）网易未验证，默认不要用。

## 0. 开工前先确认

1. **运行环境**：命令方块地图？聊天栏手动执行？还是导入 BDX？
2. **触发方式**：玩家操作、红石信号、还是每 tick 轮询？
3. **玩家规模**：单人、本地联机、还是服务器（决定选择器与状态归属）。
4. **版本**：`/help` 里是否有目标命令；不同版本的方块状态名可能不同。

如果用户给的是 Java 语法，先翻译成基岩版；如果用户明确要 Java 版，说明本技能不适用。

### 0.1 不是背例子：先选计算模型

写命令前先用 3–5 行说清模型，不能直接套模板：

- 这是**状态机**、**数据流/事务**、**队列/调度器**、**树/图**，还是**几何采样**？
- 状态存在哪里：计分板、tag、方块、实体？
- 需要什么数学：整数、取模、钳制、坐标、距离、概率、几何表？
- 复杂度：分支数/实体数/每 tick 命令数/最坏情况？
- 是否用 **N 叉树/执行分叉**（射线、圆、椭圆、体积扫描）？见 `references/nx-tree.md`。

基础模型、内存布局、算法与复杂度见 `references/command-foundations.md`；  
整数/坐标/几何/概率见 `references/command-mathematics.md`。
二分/NX/递归/大数圆规四套坐标运算见 `references/coordinate-arithmetic.md`。

### 0.2 先问用户，再开始设计

设计类请求先做 **3–7 个高杠杆问题**，不要一上来写命令：

1. **期待效果**：玩家第一眼/前 30 秒要看到、听到、感受到什么？（震撼/紧张/爽/神秘/仪式/压迫/治愈）
2. **玩家在做什么**：战斗/解谜/探索/建造/经营/社交？
3. **成功/失败长什么样**：通关瞬间、团灭瞬间各一句话。
4. **约束**：坐标/尺寸/单人多人/版本/性能/现有系统。
5. **输出**：设计/spec/命令/BDX/建筑体块。
6. **差异点**：最不想像什么、参考作品/关键词。

问完先复述“目标 / 期待效果 / 硬约束 / 未知”，再给 **稳健/联动/大胆 3 个方向**，用 6 维评分选一个；红队后再冻结 spec。  
用户说“直接做”时不要追问，但要在开头写清假设。  
完整问题库、期待效果→设计杠杆、联想/SCAMPER/约束/视角/组合法见 `references/intake-and-reasoning.md`。

## 1. 设计流程（按顺序做，不要跳步）

### 1.0 先建模，再写方块

1. 行为契约（1.1）。
2. 选计算模型（状态机/数据流/队列/树/图）。
3. 设计内存布局（分数/tag/数组/队列）。
4. 写数学（范围/取模/钳制/坐标/概率）。
5. 估算复杂度与命令数；超过预算就拆。

模型没定清楚时，先补模型，不要先堆 `execute`。

### 1.1 写清行为契约

用 6 行回答：**谁触发 / 起始状态 / 中间状态 / 结束状态 / 失败时怎样 / 如何重置**。
多人游戏还要写：状态是全局的还是每玩家的？玩家退出、死亡、迟到加入时怎么办？

### 1.2 建状态表

每个变量一行，先定状态再写命令：

| 变量 | 载体 | 归属 | 类型/范围 | 初值 | 谁写 | 谁读 |
|---|---|---|---|---|---|---|
| `fb_state` | 计分板 `arena` | 全局假玩家 | 0=idle 1=count 2=run | 0 | 开始/结束链 | 所有判断 |
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
| Java 方块名 ≠ Bedrock 方块名 | `snow_block` 应为 `snow`；顶层雪是 `snow_layer`，不是 `snow` |
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
# 全局：假玩家，使用 fb_ 前缀（不要用 #，网易会报错）
scoreboard players set fb_state arena 1
scoreboard players add fb_tick arena 1

# 每玩家：@s 或具体玩家名
execute as @a run scoreboard players add @s coins 1
execute as @a[scores={coins=10..}] run ...
```

### 4.2 四种门

```mcfunction
# AND：两个条件都成立
execute if score fb_a obj matches 1 if score fb_b obj matches 1 run say both

# OR：任一成立（先置标记，再判断）
execute if score fb_a obj matches 1 run scoreboard players set fb_flag obj 1
execute if score fb_b obj matches 1 run scoreboard players set fb_flag obj 1
execute if score fb_flag obj matches 1 run say either

# NOT
execute unless entity @e[type=zombie,tag=wave] run say cleared

# 纯条件门（不带 run）：成功则让后面的 conditional chain 继续
execute if score fb_stock shop matches 1..
```

### 4.3 计数器、倒计时、冷却

```mcfunction
# 每秒时钟
scoreboard players add fb_tick arena 1
execute if score fb_tick arena matches 20.. run scoreboard players set fb_tick arena 0

# 倒计时（只在 >0 时减）
execute if score fb_count arena matches 1.. run scoreboard players remove fb_count arena 1

# 冷却（每 tick 减，到 0 停止）
execute if score fb_cd obj matches 1.. run scoreboard players remove fb_cd obj 1

# 取模翻转 0/1
scoreboard players operation fb_state obj %= fb_two obj
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
- 多部件 Boss：初始化链 >70 块要拆段；真实受击别用距离，用 1 耐久护甲 + `replaceitem ... keep` + conditional 块。
- 移动 Boss：让隐形僵尸/怪物用**原版 AI** 追人，不要每 tick `tp` 载体；FMBE 部件以怪物为原点相对 `tp`，载体本身可以当受击核心。
- 拼接优先：多高度部件用世界轴 `~` 跟随；不要直接对多高度部件用 `^` + 单个 facing 目标，pitch 不同会把模型拉散。完整例子见 `examples/frostcrown-fmbe/`。
- `playanimation` 还可写实体 **render controller 变量**（`variable.glow_alpha`、`variable.profession_index` 等），改发光/变体/UV/部件 alpha；必须是对应实体、部分变量只读，详见 `references/render-controller-vars.md`。

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

### 4.7.1 指令计算机：实体像素与栅格

- **显示层**用 item/方块像素；**存储层**仍用计分板/标签，别把 item 当唯一内存。
- `align xyz` + `positioned` 把像素吸附到格点；选择器用 `type=item,tag=px,x/y/z,r`。
- `fill ... air destroy` 会掉落，掉落物可能再次进入 `@e[type=item]` 形成反馈；删除用 `air`/`replace`。
- 时钟用 `fb_tick` + repeat；刷新按规模降级，不要 20 Hz 全量重绘。
- 详见 `references/command-computer.md`。

### 4.7.2 从语料抽框架（19 个社区文件）

- 语料主体是 **N 叉执行树 + 坐标变换 + 实体锚点 + 少量计分板状态**，不是“命令堆”。
- 分层：执行 / 空间 / 数据 / 实体 / UI / 世界 / 性能。
- 典型：binaryTree2D/3D、rotatedCircle（空间）；JSON-Line（UI 编码）；物品数量数据化（查表编码）；鱼竿枪（UID/投射物）；noneEntity（二进制坐标序列）；TNT（structure 回放）。
- 19 文件、3,719 行、2,681 非注释行；`positioned` 1,431、`rotated` 857、`facing` 420。
- 完整分类/统计/反模式见 `references/command-corpus-framework.md`；统计脚本 `scripts/command_corpus.py`。

### 4.7.3 值噪声 / 精度哈希

- 样本“值噪声基本命令”不是普通 Perlin：它用**大坐标浮点精度丢失 + `align` + 四角实体变换**做坐标哈希，再用 `fill` 铺地形。
- 关键：`a/b/c/d` 四角、`point` 落点、`xp_orb` 采样、`fishing_hook` 起点、`nxs` 方向锚点。
- 极端坐标（23388608、1048576、4096 等）是精度工具，不是普通世界坐标；换版本可能变。
- 学习顺序：一个方向 4×4 → 四方向 16×16 → 清理/限高。
- 完整机器（32×32、256 柱子、3 层 fBm、3×3 平滑、随机种子、429 方块）见
  `references/value-noise-terrain-machine.md` 和 `examples/noise-terrain/`；
  它把 7 命令核 / 高斯滤波样本拼成可导入的 BDX，并记录了“秒完成/漏 at @s/计数器未清”等坑。
- 详见 `references/value-noise.md`。

### 4.8 一遍过交付（实测校准）




目标不是“命令写对”，而是“到服务器能跑、能看、不卡”：

- **执行位置**：命令方块远离展示区时，别用 `r/rm` 选实体；用 `x/y/z/dx/dy/dz` 或 `execute positioned`。
- **导入**：BuildTask 之后**逐块 `CommandBlockUpdate` repair**；只摆方块不算导入成功。
- **性能**：FMBE 不要 20 Hz 跑 48 条 Molang；初始化一次 + 1 Hz 刷新 + 每 tick 锚定。
- **实体**：`summon fox` 不要带 name/event 参数；用普通 summon + tag；`hasitem` 查实际 ID（`player_head` 不是 `skull`）。
- **UI**：`title` 纯文本约 512 字节；大面板用 `titleraw`；菜单只发 actionbar，不弹大标题。
- **视觉**：无头 bot 不能看客户端模型；功能可一遍过，视觉需要一张截图校准 `v.ypos/v.zpos/v.xpos`。
- 完整清单和两次交付（雪球菜单 / FMBE 玩家）的坑见 `references/one-pass-delivery.md`。

### 4.9 生成 BDX（命令 + 建筑）

- **BDX** = `BD@` + brotli(`BDX` + `0x00` + `0x00` + command-stream + `ID 88`)；author 保持空；不是 NBT，也不是 zip。
- 命令方块用 `PlaceBlockWithCommandBlockData`（ID 27）；普通方块用 `PlaceBlock` / `PlaceBlockWithBlockStates`。
- `scripts/bdxgen.py`：命令方块，或 `BuildBlock` 普通方块 + 命令方块混排。
- `scripts/buildgen.py`：建筑 plan 的 `fills`/`blocks`/`commands` → 完整 BDX。
- 生成后回读：`mcbeextract` / `BDX.FromFile`，核对方块数、坐标、mode、命令。
- **不生成 MCWorld，不做行为包**；需要世界时由用户用 BDX 导入器导入现有世界。

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
- **构图三把尺**：631（60/30/10 主次）、黄金比例（0.382/0.618 停顿点）、视觉重量（实体/深色/粗线更重；远处小重量有杠杆）。焦点 10% 区域放 50% 细节。
- **立面进深**：至少四层（背墙→凹进→前凸→剪影）；不要一堵白墙贴玻璃。
- **石族/虚空间**：3–5 族石料混色，下重上轻；长翼挖内院/回廊，别做实心盒子。
- 完整方法见 `references/building-corpus-learning.md` 和 `references/building-design.md`；模板 `assets/building-brief.template.md`。

### 4.12.1 建筑编译器

```bash
python3 scripts/arch_pipeline.py --builder examples/arch-chapel/build_chapel.py --outdir examples/arch-chapel/out --start 900,0,900
```

```text
ArchBuilder → arch_compile → .bdx
  → arch_preview（front/top/iso）
  → arch_readback（count/bounds）
  → report.json
```

- `references/28-arch-compiler.md`
- `references/35-architecture-components.md`（8 个组件：幕墙/门楼/主堡/回廊/开间/门廊/飞扶壁/老虎窗）

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
- [ ] 静态建筑没有用 `setblock`/`fill` 命令链做几何作者层；`fill` 只用于投放。
- [ ] 建筑任务已输出 front/top/iso + report，而不是只给命令链。

## 7. 参考文件导航

| 文件 | 什么时候读 |
|---|---|
| `references/command-block-mechanics.md` | 需要精确的方块时序、条件链、成功次数、限制 |
| `references/command-foundations.md` | 命令计算模型、内存、控制流、算法、复杂度、不变量 |
| `references/command-mathematics.md` | 整数/定点、坐标/向量、几何、概率、位集、常见数学坑 |
| `references/nx-tree.md` | N 叉树/NX：执行分叉、射线、圆/椭圆、体积扫描与成本 |
| `references/coordinate-arithmetic.md` | 坐标运算四思想：二分（位移/位置）、NX（分叉/进制）、递归（重入/栈）、大数圆规（圆球近似）+ 计分板全语法 |
| `references/command-computer.md` | 指令计算机：item 像素、栅格吸附、存储/显示分层、反馈风险 |
| `references/command-corpus-framework.md` | 19 个社区指令文件的归类/统计/分层框架/反模式 |
| `references/block-map.md` | Java→Bedrock 方块名映射；雪块 `snow` / 雪层 `snow_layer` |
| `references/value-noise.md` | 值噪声/精度哈希：大坐标精度、align、四角锚点、fill 地形 |
| `references/value-noise-7cmd.md` | 7 命令值噪声核：a/b/c/d/nxs/o、四角插值、落列、缺扫描器 |
| `references/gaussian-filter.md` | 高斯滤波/NX 平滑：t/boat 分叉、二分表面、3×3 权重、计分板侧 box blur、清理风险 |
| `references/value-noise-terrain-machine.md` | 完整值噪声地形机：扫描/噪声/平滑/铺设状态机、局部选择器、溢出、六个失败模式 |
| `references/chain-patterns.md` | 要选型：时钟、门、状态机、队列、波次、冷却 |
| `references/bedrock-command-reference.md` | 查某条命令的基岩版语法和坑 |
| `references/execute-and-selectors.md` | 写 `execute`、选择器、条件表达式 |
| `references/scoreboard-memory.md` | 用 dummy 计分板存状态、做数学、编码 |
| `references/text-ui-and-effects.md` | 标题、actionbar、tellraw、音效、粒子、camerashake、playanimation |
| `references/30-command-ui-design.md` | UI 设计库：24 版式/配色/符号/文案（旧 execute 示例） |
| `references/31-command-ui-modern.md` | 网易 1.21.130 现代 UI 模板/%%2/%%9/HUD 互斥 |
| `references/32-ui-sound-design.md` | UI 通道/标题顺序 + 音效分层/旋律目录/音量预算 |
| `references/33-architecture-typology.md` | 建筑类型卡：日/韩/中/古典/哥特/中世纪/庄园，场地/序列/剖面/结构 |
| `references/34-fmbe-compiler.md` | FMBE IR / 校验 / pose+setup / BDX / 回读 |
| `references/38-relative-coordinates.md` | 默认相对坐标 / `~` vs `^` / 锚点例外 / 选择器相对 |
| `references/35-architecture-components.md` | 8 个建筑组件：幕墙/门楼/主堡/回廊/开间/门廊/飞扶壁/老虎窗 |
| `references/36-nxs-compiler.md` | NxsRaster / Shape / CSG / 自适应点阵 / 预算 / 回读 |
| `references/37-nxs-program.md` | NxsFrame / Program / Spiral / Radial / Path / Orbit / Array |
| `references/command-syntax.json` | 命令合法格式 + 共享 token 词表（纯语法事实） |
| `references/fmbe-mbe.md` | FMBE/MBE 显示实体：前置、8 条链、变量、MBE、SMBE 变体、例子拆解 |
| `references/render-controller-vars.md` | 用 playanimation 改 render controller 变量：实体/变量/只读限制 |
| `references/dataization-rpg.md` | 数据化 RPG：属性分层、伤害事务、T显/血条、等级/经验、装备/怪物、性能与旧语法升级 |
| `references/misc-map-systems.md` | 杂项地图系统：菜单/选人、商店/彩票、开箱、反作弊/领地/卡密门、匹配/密室、拔刀剑、死亡动画 |
| `references/one-pass-delivery.md` | 一遍过交付：执行位置、导入 repair、性能、实体/物品、UI、视觉校准清单 |
| `references/bdx-chain-packaging.md` | BDX 打包：单区块盘旋、初始化/FMBE/主体分离、验收 |
| `references/building-design.md` | 建筑设计：场地/体量/轮廓/材质/立面/屋顶/动线/建造顺序 |
| `references/building-corpus-learning.md` | 建筑/指令语料：索引、归类、风格卡、模仿、建造 |
| `references/gothic-cathedral-case.md` | 案例：300 样本→哥特教堂重做、fill 导入、回读 |
| `references/interior-design.md` | 内饰：动线/焦点/分层/光/材质/教堂模板/检查表 |
| `references/spectacle-design.md` | 亮眼/奇观：剪影/对比/发光/运动/声音/反土味 |
| `references/creative-thinking.md` | 多思考/联动/创造性：6 问、3 方向、联动矩阵、红队、最小闭环 |
| `references/intake-and-reasoning.md` | 提问协议：期待效果/约束/3 方向；联想/SCAMPER/约束/视角/组合 |
| `references/debugging.md` | 链不跑、条件不触发、多人异常、重载失效 |
| `references/bedrock-vs-java.md` | 用户给的是 Java 语法，或需要差异速查 |
| `references/netease-1.21.130.md` | 网易命令边界、`schedule` 结论、未验证命令、旧语法升级 |
| `references/netease-corpus-patterns.md` | 真实网易地图的菜单/状态/结构/表现惯用法 |
| `assets/chain-spec.schema.json` | 写 spec.json 时 |
| `examples/` | 需要完整范例：倒计时、商店、开关灯、噪声地形、FMBE Boss |

## 8. 主要事实来源

- [Command Block — Minecraft Wiki](https://minecraft.wiki/w/Command_Block)（类型、条件、延迟、C-tick、链式触发）
- [Commands/execute — Minecraft Wiki](https://minecraft.wiki/w/Commands/execute)（基岩版 11 个子命令、深度优先 fork）
- [Target selectors — Minecraft Wiki](https://minecraft.wiki/w/Target_selectors)（基岩版参数：`r/rm`、`c`、`family`、`hasitem`、`haspermission`）
- [Commands/scoreboard — Minecraft Wiki](https://minecraft.wiki/w/Commands/scoreboard)（仅 `dummy`、`random`、`test`、`operation`）
- [Minecraft Creator Docs — Commands](https://learn.microsoft.com/en-us/minecraft/creator/commands/)（各命令的基岩版签名）
- [网易开发者官网 — 命令列表及概述](https://dev.mc.163.com/dev/mcmanual/mc-dev/mconline/10-addon教程/第04章：指令系统，你的创作管家/课程04.命令列表及概述.html)（网易 1.21.130 命令边界；明确列出 `schedule`，标注 `fog` 未实装）
