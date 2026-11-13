# 命令方块链模式库（基岩版）

> 记号：`[R]` Repeat，`[I]` Impulse，`[C]` Chain；`(c)` 表示 Conditional，`(u)` 表示 Unconditional。
> 所有命令均为基岩版语法。默认 `Chain` 为 `Always Active`，`Impulse/Repeat` 为 `Needs Redstone`（表中会注明例外）。

## 0. 选型表

| 需求 | 用哪个模式 | 关键设置 |
|---|---|---|
| 每 tick 检查一次 | Tick 时钟 | `[R]` Always Active, Delay 0 |
| 每秒/每 N tick 一次 | 秒时钟 / N 分频 | `[R]` 计数 + 条件复位 |
| 按钮触发一次 | 一次性事件 | `[I]` Needs Redstone |
| 开关灯/开/关两态 | T 翻转 | 状态 + `%= 2` |
| 计分/累计 | 计数器 + 钳制 | `[R]` 或事件触发 + 上限判断 |
| 倒计时/限时 | 倒计时 + 到点触发 | 只在 >0 时减 |
| 技能冷却 | 冷却计数器 | 每 tick 减，到 0 停 |
| A 且 B | AND 门 | 多个 `if` 或条件链 |
| A 或 B | OR 门 | 置标记再判断 |
| 非 A | NOT 门 | `unless` |
| 多分支 | 并行检查/独立链 | 不要靠条件失败断链 |
| 多阶段流程 | 状态机 | `fb_state` + 每 tick/每秒推进 |
| 波次刷怪 | 波次生成器 | 5 秒计时 + `unless entity` |
| 排队/顺序处理 | 固定槽队列 | `fb_q0..fb_qN` + head/tail |
| 每人独立任务 | 每玩家状态 | `execute as @a ...` |
| 商店/提交物品 | 全有或全无 | `hasitem` 门 + `clear` + `give` |
| 进入区域触发 | 邻近触发 | `@a[r=N]` + 冷却 |
| 随机结果 | 随机分支 | `scoreboard players random` |
| 延迟 N tick 再执行 | 延迟链或倒计时 | Chain Delay / 状态机 |

### 0.1 网易 1.21.130 实战补充

- **常加载**：远处机关先 `tickingarea add ~~~ ~100~~100 §k指令区`；没有它，面板/时钟会停。
- **菜单**：`titleraw actionbar` 显示，`scores=` 选页，`rx/rxm` 选“抬头确认/低头取消”。
- **结构复用**：带方块实体的模板用 `structure save/load`；纯方块用 `clone`。
- **旧图**：旧 `execute @a ~ ~ ~` 在 1.21.130 新图不能用；先用 AuroraBuild `command_upgrader` 升级。
- **表现**：用 `camerashake`、`playanimation`、`event`、`damage`；不要用未验证的 `camera`/`inputpermission`/`fog`。
- 详细命令边界见 `netease-1.21.130.md`，真实地图惯用法见 `netease-corpus-patterns.md`。

---

## 1. Tick 时钟

**何时用**：轮询玩家、方块、实体状态；状态机的推进器。

```
[R] clock (Always Active, Delay 0)
 └→ [C] work (u)
```

```mcfunction
# clock
scoreboard players add fb_tick clock 1

# work
execute as @a[tag=ready] at @s run particle flame ~ ~1 ~
```

**坑**：

- 每 tick 都跑，命令要便宜；`fill`/`clone`/全玩家 `particle` 不要放这里。
- 需要 20 Hz 时不能用红石时钟（基岩版红石只有 10 Hz）。

---

## 2. 秒时钟 / N 分频

**何时用**：每秒回血、每秒倒计时、每 5 秒刷怪。

```
[R] clock:  fb_t += 1
 └→ [C] (c) if fb_t >= 20: fb_t = 0      ← 只有复位成功时，后面的条件块才继续
     └→ [C] (c) 每秒任务
```

```mcfunction
# clock
scoreboard players add fb_tick arena 1

# wrap（Conditional）
execute if score fb_tick arena matches 20.. run scoreboard players set fb_tick arena 0

# per_second（Conditional）
execute if score fb_state arena matches 1 run scoreboard players remove fb_count arena 1
```

**要点**：

- `wrap` 是条件块：`fb_t < 20` 时命令失败，后面的**条件块**会跳过；无条件块仍会执行。
- 想要“每秒都执行、但只在状态 1 时生效”，把每秒任务写成 `[C] (u)` + `execute if score fb_state ...`，避免被 `wrap` 的失败连锁影响。
- 5 秒一次：阈值 100；2 秒一次：40。

---

## 3. 一次性事件（按钮/拉杆）

```
[I] on_button (Needs Redstone, Delay 0)
 └→ [C] (c) step_1
     └→ [C] (c) step_2
```

```mcfunction
# on_button
scoreboard players set fb_state arena 1

# step_1
scoreboard players set fb_count arena 3

# step_2
title @a title §6Ready?
```

**坑**：

- `Impulse` 的 Delay 0 也是 1 tick 后执行。
- 按钮会给脉冲，拉杆会给持续信号；拉杆要配 `[I]` 的上升沿检测，或直接用按钮。
- 同一按钮被快速连按时，每次都会触发；需要防抖就加冷却（模式 6）。

---

## 4. T 翻转（开关灯/两态）

```
[I] button: fb_state += 1
 └→ [C] (c) wrap: fb_state %= 2
     └→ [C] (u) if fb_state==1: 开
         └→ [C] (u) if fb_state==0: 关
```

```mcfunction
# button
scoreboard players add fb_state lamp 1

# wrap（Conditional）
scoreboard players operation fb_state lamp %= fb_two lamp

# on（Unconditional）
execute if score fb_state lamp matches 1 run setblock 10 65 10 redstone_block

# off（Unconditional）
execute if score fb_state lamp matches 0 run setblock 10 65 10 air
```

初始化：

```mcfunction
scoreboard objectives add lamp dummy
scoreboard players set fb_two lamp 2
scoreboard players set fb_state lamp 0
```

**坑**：

- `%=` 的除数是 `fb_two`，要确保它被初始化；除数为 0 时基岩版不改变目标值。
- 状态只在 0/1 之间；如果从 2 开始，`2 % 2 = 0`，也能自愈，但最好初始化。
- 两个输出块都设为 **Unconditional**，否则失败的那个会挡住另一个。

---

## 5. 计数器 + 钳制

**何时用**：积分、连杀、收集数量，且不能超过上限。

```
[R] 或 [I]: fb_n += 1
 └→ [C] (u) if fb_n > MAX: fb_n = MAX
```

```mcfunction
# add
scoreboard players add fb_score game 1

# clamp（Unconditional，必须无条件，否则超限后无法回写）
execute if score fb_score game matches 101.. run scoreboard players set fb_score game 100
```

**坑**：

- 钳制块要 `Unconditional`；如果设条件，它只在“上一步成功”时执行，逻辑会变得依赖前驱。
- 要同时处理下限，再加一块 `if fb_n matches ..0 run set 0`。
- 32 位整数上限 2,147,483,647；累计型计数器要定期重置或钳制。

---

## 6. 倒计时 + 到点触发

```
[R] clock: fb_t += 1
 └→ [C] (c) wrap: every 20t, fb_t=0
     └→ [C] (u) if state==1 and fb_count>0: fb_count -= 1
         └→ [C] (u) if fb_count==3: 显示 3
             └→ [C] (u) if fb_count==2: 显示 2
                 └→ [C] (u) if fb_count==1: 显示 1
                     └→ [C] (u) if fb_count==0: GO + state=2
```

```mcfunction
# countdown（Unconditional）
execute if score fb_state arena matches 1 if score fb_count arena matches 1.. run scoreboard players remove fb_count arena 1

# show3（Unconditional）
execute if score fb_state arena matches 1 if score fb_count arena matches 3 run title @a title §e3

# go（Unconditional）
execute if score fb_state arena matches 1 if score fb_count arena matches 0 run title @a title §aGO!

# start（Unconditional）
execute if score fb_state arena matches 1 if score fb_count arena matches 0 run scoreboard players set fb_state arena 2
```

**顺序很重要**：先显示当前值，再减。否则 3 会变成 2 才显示。
**坑**：

- 减到 0 后不要再减；用 `matches 1..` 保护，避免负数。
- 到点触发和状态切换要分开两块，方便测试。
- 需要精确到 tick 的倒计时，直接每 tick 减，不要走秒时钟。

---

## 7. 冷却

```
[R] clock: if fb_cd > 0: fb_cd -= 1
[I] use: if fb_cd == 0: 执行 + fb_cd = N
```

```mcfunction
# clock（Repeat）
execute if score fb_cd item matches 1.. run scoreboard players remove fb_cd item 1

# use（Impulse）
execute if score fb_cd item matches 0 run scoreboard players set fb_cd item 40
 └→ [C] (c) do_thing
```

**坑**：

- 把“检查冷却”和“设置冷却”放在同一条 `execute` 里，成功才继续，避免冷却未到也执行。
- 冷却单位是 tick：40 = 2 秒，20 = 1 秒。
- 多人游戏把 `fb_cd` 换成 `@s` 的分数，不要共用全局冷却（除非是全局技能）。

---

## 8. AND 门

**写法 A（一条命令，推荐）**：

```mcfunction
execute if score fb_a obj matches 1 if score fb_b obj matches 1 run say both
```

**写法 B（条件链）**：

```
[C] (c) if A
 └→ [C] (c) if B
     └→ [C] (c) action
```

**坑**：

- 写法 B 里，第二块检查的是第一块的成功次数；第一块命令失败，第二块就跳过。
- 但第一块失败仍会触发第二块；如果第二块是 Unconditional，它会照跑。所以条件链要全部 `Conditional`。
- 三个以上条件优先写成多个 `if`，可读性更好。

---

## 9. OR 门

```
[C] (u) if A: fb_flag = 1
 └→ [C] (u) if B: fb_flag = 1
     └→ [C] (u) if fb_flag==1: action
         └→ [C] (u) fb_flag = 0
```

```mcfunction
execute if score fb_a obj matches 1 run scoreboard players set fb_flag obj 1
execute if score fb_b obj matches 1 run scoreboard players set fb_flag obj 1
execute if score fb_flag obj matches 1 run say either
scoreboard players set fb_flag obj 0
```

**坑**：

- 三段都设为 Unconditional，否则前一段失败会挡住后一段。
- 用完清零，否则下一轮会误判。
- 需要“哪个条件成立”时，用不同的 flag 或直接分支，不要只用一个 OR 标记。

---

## 10. NOT 门

```mcfunction
execute unless entity @e[type=zombie,tag=wave] run say cleared
execute unless score fb_state obj matches 1 run say not running
```

**坑**：

- `unless` 是“条件不成立时执行”，不是“条件成立时跳过”。
- 空选择器（`@e[...]` 没选中任何实体）在 `if entity` 下是失败，在 `unless entity` 下是成功。
- 不要用 `unless` 去“取消”后面的链；它只影响当前命令。

---

## 11. 多分支

**错误写法**：把分支串成条件链，指望失败后不走后面。

```
[C] (c) if A: ...
 └→ [C] (c) if B: ...   ← 如果 A 失败，B 也会被跳过（因为 B 的条件看 A）
```

**正确写法 A：并行检查（同一行多个 Unconditional）**

```
[C] (u) if A: ...
 └→ [C] (u) if B: ...
     └→ [C] (u) if C: ...
```

**正确写法 B：多条独立链**

```
[I] button ─→ [C] branch_A
           └→ [C] branch_B   ← 物理上从同一个方块分出两条链
```

**坑**：

- 一个方块只能朝向一个方向；物理分支需要两个不同的上游方块，或让每条链各自有入口。
- 并行检查适合“只执行一个分支”的场景；多个条件可能同时成立时，要加优先级或互斥。
- 需要“只走第一个成立的分支”时，用 `fb_done` 标记：每个分支先检查 `fb_done==0`，执行后置 1。

---

## 12. 状态机（多阶段）

```
fb_state: 0=idle 1=countdown 2=running 3=ended
[R] clock
 └→ [C] (c) every second
     └→ [C] (u) if state==1: countdown
         └→ [C] (u) if state==1 and count==0: state=2, 开始
             └→ [C] (u) if state==2: 游戏逻辑
                 └→ [C] (u) if state==2 and 条件: state=3, 结束
                     └→ [C] (u) if state==3: 结算 + 延时重置
```

**要点**：

- 每个阶段只做一件事；状态切换和阶段逻辑分块。
- 每个阶段都要有“进入动作”和“退出动作”。
- 重置不是“把状态改回 0”就完了：还要清 tag、清临时分数、清标题、清实体。
- 结束态建议停留 N tick 再回 idle，避免玩家看到瞬间跳变。

---

## 13. 波次生成器

**何时用**：塔防、生存波次、竞技场。

```
[R] clock: fb_t += 1
 └→ [C] (c) every 100t: fb_t=0
     └→ [C] (u) if state==running and no wave_mob: fb_wave += 1
         └→ [C] (u) if state==running and no wave_mob: 生成 3 只
             └→ [C] (u) if state==running and no wave_mob: 提示
```

```mcfunction
# every_5s（Conditional）
execute if score fb_tick wave matches 100.. run scoreboard players set fb_tick wave 0

# next_wave（Unconditional）
execute if score fb_state wave matches 1 unless entity @e[tag=wave_mob] run scoreboard players add fb_wave wave 1

# spawn（Unconditional）
execute if score fb_state wave matches 1 unless entity @e[tag=wave_mob] run summon zombie wave_mob ~ ~ ~
execute if score fb_state wave matches 1 unless entity @e[tag=wave_mob] run summon zombie wave_mob ~2 ~ ~
execute if score fb_state wave matches 1 unless entity @e[tag=wave_mob] run summon zombie wave_mob ~-2 ~ ~

# tag_them（Unconditional）
tag @e[type=zombie,name=wave_mob] add wave_mob

# announce（Unconditional）
execute if score fb_state wave matches 1 unless entity @e[tag=wave_mob] run title @a actionbar §eWave incoming
```

**坑**：

- 三条 `summon` 都检查“没有 `wave_mob` 标签”，而标签是在三条都生成完之后才统一加的，所以这一轮会生成 3 只；这是故意的。如果你在每条 summon 后立刻打 tag，后两条就会被自己的检查挡住，只生成 1 只。
- `name=` 匹配的是名字，不是 tag；生成后要 `tag ... add`。
- 更稳的写法：用 `fb_spawn_count` 计数器，每 tick 生成一只，生成完复位；这样不会依赖同一 tick 内的顺序。
- 波次开始时先把 `fb_wave += 1`，再生成；如果生成失败（区块未加载），下一轮会重试，不会跳波。

---

## 14. 固定槽队列

基岩版没有数组；用 `fb_q0..fb_qN` 假玩家模拟。

```
fb_head, fb_tail, fb_q0..fb_q3
入队： fb_q[fb_tail] = 值；fb_tail = (fb_tail+1) % 4
出队： 读取 fb_q[fb_head]；fb_head = (fb_head+1) % 4
```

由于不能动态索引，需要用条件分支逐个槽处理：

```mcfunction
# enqueue（假设 fb_tail 已知）
execute if score fb_tail q matches 0 run scoreboard players operation fb_q0 q = fb_value q
execute if score fb_tail q matches 1 run scoreboard players operation fb_q1 q = fb_value q
execute if score fb_tail q matches 2 run scoreboard players operation fb_q2 q = fb_value q
execute if score fb_tail q matches 3 run scoreboard players operation fb_q3 q = fb_value q
scoreboard players add fb_tail q 1
scoreboard players operation fb_tail q %= fb_four q
```

**坑**：

- 队列满/空要有标记，否则会覆盖。
- 每个槽都要初始化；未初始化的分数是“未跟踪”，读取时按 0 处理。
- 槽多时用函数生成重复命令，不要手写 20 遍。

---

## 15. 每玩家独立任务

```mcfunction
# 每人每秒回 1 点（用效果代替生命值写入）
execute as @a[scores={online=1}] run effect @s regeneration 1 0 true

# 每人独立冷却
execute as @a run scoreboard players remove @s cd obj 1
execute as @a[scores={cd=..0}] run scoreboard players set @s cd obj 0
```

**要点**：

- `execute as @a ...` 会为每个玩家 fork 一次；`@s` 指当前玩家。
- 位置相关用 `at @s`；否则命令仍在命令方块位置执行。
- 玩家退出后分数仍在；重新加入要判断“首次加入”并初始化。

---

## 16. 商店 / 提交物品（全有或全无）

```
[I] buy (Needs Redstone)
 └→ [C] (c) 检查库存 > 0（纯条件 execute）
     └→ [C] (c) 扣物品 clear
         └→ [C] (c) give
             └→ [C] (c) 扣库存
                 └→ [C] (u) 清标记
                     └→ [C] (u) 售罄提示
```

```mcfunction
# buy
execute as @a[r=4,hasitem={item=emerald,quantity=1..},c=1] run scoreboard players set @s shop 1

# stock_gate（Conditional，纯条件）
execute if score fb_stock shop matches 1..

# take（Conditional）
execute as @a[r=4,scores={shop=1},c=1] run clear @s emerald 0 1

# give（Conditional）
execute as @a[r=4,scores={shop=1},c=1] run give @s bread 1

# stock（Conditional）
scoreboard players remove fb_stock shop 1

# cleanup（Unconditional）
scoreboard players set @a shop 0

# sold_out（Unconditional）
execute if score fb_stock shop matches 0 run title @a actionbar §cSold out
```

**为什么这样排**：

- 先查库存再扣物品，避免“钱扣了没货”。
- `c=1` 让一次按钮只服务最近的 1 名玩家；否则多人同时买会只扣 1 份库存却发多份货。
- `clear` 成功才继续，避免“没物品也发货”。
- 清理块必须 Unconditional，否则失败路径会留下脏标记。

---

## 17. 邻近触发

```mcfunction
# 每 tick 检查 5 格内没有 tag=in_zone 的玩家
execute as @a[r=5,tag=!in_zone] run title @s actionbar §aEntered
execute as @a[r=5,tag=!in_zone] run tag @s add in_zone

# 离开时清理
execute as @a[rm=6,tag=in_zone] run tag @s remove in_zone
```

**坑**：

- 基岩版用 `r`/`rm`，不是 `distance`。
- `r=5` 是球形距离；要方形区域用 `x/y/z + dx/dy/dz`。
- 高频触发要加冷却或 tag 去重，避免每 tick 刷屏。

---

## 18. 随机结果

```mcfunction
# 给每个玩家一个 1..3 的随机数
execute as @a run scoreboard players random @s rng obj 1 3

# 分支（并行检查，避免互相阻塞）
execute as @a[scores={rng=1}] run give @s bread 1
execute as @a[scores={rng=2}] run give @s apple 1
execute as @a[scores={rng=3}] run give @s carrot 1
```

**坑**：

- `random` 的下限必须小于上限，否则命令失败。
- 这段逻辑要放在**事件触发**的链里；如果放在每 tick 的时钟里，会每 tick 重抽，玩家可能连续中奖。
- 随机数写进分数后要清零或重新随机，避免重复使用旧值。
- 需要“每人只抽一次”时，用 `tag=!drawn` 门。

---

## 19. 延迟 N tick 的两种做法

**做法 A：Chain Delay**

```
[I] start ─→ [C] (Delay 20) 20 tick 后执行 ─→ [C] (Delay 40) 再 40 tick
```

- 优点：简单，少方块。
- 缺点：不能暂停/重置；条件语义在延迟链上不直观；长延迟占方块。

**做法 B：计分板倒计时**

```mcfunction
# start
scoreboard players set fb_delay obj 60

# 每 tick
execute if score fb_delay obj matches 1.. run scoreboard players remove fb_delay obj 1

# 到点
execute if score fb_delay obj matches 0 run say done
```

- 优点：可暂停、可重置、可显示、可多人共享。
- 缺点：需要时钟和状态。

> 需要“取消”时用 B；需要“一次性短延迟”用 A。

---

## 20. 初始化 / 重置链

```
[I] reset (Needs Redstone 或世界启动时由函数调用)
 └→ [C] (c) 清状态
     └→ [C] (c) 清 tag
         └→ [C] (c) 清标题
             └→ [C] (c) 清临时实体
                 └→ [C] (c) 重新给初始物品/位置
```

```mcfunction
scoreboard players set fb_state arena 0
scoreboard players set fb_count arena 0
scoreboard players set fb_tick arena 0
tag @a remove ready
tag @a remove in_zone
title @a clear
kill @e[type=zombie,tag=wave_mob]
```

**坑**：

- 重置链本身不要依赖旧状态；全部用 Unconditional + 直接赋值。
- 重置后要给玩家“可再次开始”的入口（按钮/区域/命令）。
- 世界启动初始化用行为包 `tick.json` 调一次 `init` 函数，或在出生点放一个 `Impulse + Always Active`（注意它可能重复执行）。

---

## 21. 组合建议

- 先画状态表，再选模式；不要先摆方块。
- 一条链 ≤ 15 个方块；超过就拆成“主链 + 子链”，用状态/标签连接。
- 每个模式都留一个“测试入口”（按钮/命令），不要只靠正式流程触发。
- 所有临时标记都在链尾清理；清理块永远 Unconditional。
- 每个 tick 都跑的逻辑，先用 `if` 门挡住昂贵操作。
