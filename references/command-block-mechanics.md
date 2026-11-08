# 命令方块机制（基岩版）

> 依据 Minecraft Wiki `Command Block` 与 `Commands/execute` 页面整理，适用于 Bedrock 1.20.70+ / 1.21.x。
> 所有“tick”均指游戏 tick（20 tick = 1 秒）。

## 1. 心智模型

把一条命令方块链想成一台**单指令 CPU**：

```
时钟（repeat / 红石脉冲）
   │  每个 tick 或每次触发推进一步
   ▼
逻辑链（chain）——每个方块执行一条命令，并把“成功/失败”传给下一个条件块
   │
   ▼
输出（setblock / give / title / summon / playsound ...）
```

- **状态**不在方块里，在计分板、tag、方块、实体里。
- **时序**由方块类型 + Delay 决定，不由命令内容决定。
- **条件**只作用于“当前方块”，不会自动截断整条链。

## 2. 三种方块

| 类型 | 颜色 | 何时执行 | 关键点 |
|---|---|---|---|
| Impulse | 橙 | 每次被激活一次 | 按钮/拉杆的“一次性”入口 |
| Repeat | 紫 | 激活期间每 tick（或每 delay tick） | 时钟；`Always Active` 时 20 Hz |
| Chain | 青 | 被它后面的方块触发 | 不自行启动；默认 `Always Active` |

“后面的方块”指**箭头指向它的那个方块**，也就是链的上游。条件模式判断的“身后”则是**箭头反方向**的方块，通常就是上游。

## 3. 基岩版设置项

| 设置 | 取值 | 默认 | 作用 |
|---|---|---|---|
| Block Type | Impulse / Chain / Repeat | Impulse | 见上表 |
| Condition | Unconditional / Conditional | Unconditional | Conditional 要求身后方块成功次数 > 0 |
| Redstone | Needs Redstone / Always Active | Impulse/Repeat：Needs；Chain：Always | Chain 的 Always 只免除红石，仍要上游触发 |
| Execute on First Tick | On / Off | On | 仅 Repeat：激活后是否立刻执行第一次 |
| Delay in Ticks | 0..N | 0 | Impulse/Chain：激活或触发后延迟多久执行；Repeat：两次执行间隔 |
| Hover Note | 字符串 | `!` | 方块名，出现在消息/调试中 |

### Delay 的精确语义

| 类型 | Delay 0 | Delay 1 | Delay N |
|---|---|---|---|
| Impulse | 等同 1 tick | 1 tick 后执行 | N tick 后执行 |
| Repeat | 每 tick | 每 tick（0 与 1 等效） | 每 N tick |
| Chain | **同一 tick** 执行 | 下一 tick 执行 | N tick 后执行 |

> 记忆：**Impulse/Repeat 的 0 和 1 一样；Chain 的 0 和 1 不一样。**

## 4. 激活与触发

### 4.1 红石激活

命令方块可以被以下方式激活：

- 相邻的电源元件（拉杆、按钮、红石块、日光传感器等）
- 相邻的充能方块
- 朝向它的比较器/中继器
- 指向它（或在其上方、无方向）的红石粉

**基岩版只在偶数 tick 响应红石信号**（C-tick / consume tick）。因此：

- 红石时钟最高约 **10 次/秒**。
- 需要 20 Hz 时，用 `Repeat + Always Active + Delay 0`，不要用红石循环。

### 4.2 Always Active

- 设为 `Always Active` 后，方块不再需要红石信号。
- 对 `Impulse`：Always Active 只是免除红石，不会变成循环；但放置/克隆时可能立刻执行一次，入口方块建议保留 Needs Redstone。
- 对 `Repeat`：持续每 tick/每 delay tick 执行。
- 对 `Chain`：默认就是 Always Active；它仍然必须被上游触发，不会自己跑。

### 4.3 链式触发

- 任何**执行过命令**的方块（无论成功失败）都会触发它箭头指向的 `Chain` 方块。
- 被触发的 `Chain`：
  1. 若未激活（Needs Redstone 且没有红石）→ 不执行，但仍把触发传给下一个。
  2. 若已激活：
     - 条件模式且身后方块失败 → 不执行，但**仍触发下一个**。
     - 条件模式且身后成功，或无条件 → 执行命令，并触发下一个。
     - 若本 tick 已经执行过 → 什么都不做（防止环在同一 tick 内无限循环）。

> **最重要的一条**：条件失败不会“断链”。它只是让当前方块不执行，触发继续往下走。
> 因此链尾的清理块要设为 `Unconditional`；分支要用独立的 `execute if ... run ...`，不要靠条件失败来跳过后续块。

## 5. 条件模式到底看谁

`Conditional` 检查的是**箭头反方向的方块**（“身后”），不是“上一个触发它的方块”。

```
直线链（正确）：

  [A 面朝东] → [B 面朝东] → [C 面朝东]
     身后←B     身后←A

  B 的条件只看 A；C 的条件只看 B。
```

```
拐弯（容易错）：

  [A] → [B]
          ↓
         [C]

  C 的身后是 B 上方的空气（不是 B），所以 C 的条件永远不成立。
  拐弯处不要用 Conditional；改用 execute if 写在命令里。
```

因此：

- 条件块要排成直线，且紧贴上游。
- 拐弯、分支、跨高度的位置，用 `execute if ...` 做条件，不用方块条件。
- 需要“整条链都成功才继续”时，让每个条件块都检查**紧邻前驱**，并保持直线。

## 6. 成功次数（Success Count）

- 命令方块执行命令后，会把命令的**成功次数**记在自己身上。
- 基岩版成功次数是整数，可能是受影响数量（玩家数、方块数、返回值），不限于 0/1。
- `Conditional` 方块用“身后方块成功次数 > 0”判断。
- 比较器可以读出成功次数作为红石强度。
- 编辑命令方块并关闭 GUI 会重置成功次数（有改动时）。

设计用法：

```mcfunction
# 后面跟 Conditional chain：只有至少一名玩家在范围内才继续
execute as @a[r=5,tag=ready] run scoreboard players add @s coins 1

# 纯条件门：不改任何东西，只把成功/失败传给下一个 Conditional
execute if score #stock shop matches 1..
```

## 7. 一次触发到底跑几个 tick

### 7.1 无延迟

```
tick T：Repeat 执行 → 触发 Chain A → A 执行 → 触发 B → B 执行 → ...
        整条链在同一 tick 内按顺序跑完。
```

### 7.2 有延迟

```
tick T：   A 执行，随后触发 B；B 设为 Delay 2
tick T+1： B 还在等
tick T+2： B 执行，并触发 C
```

- 延迟链的触发会继续传播；不要假设“条件失败会取消后续延迟”。
- 需要“延迟后只在条件仍成立时执行”，把条件写进 B 的命令：`execute if ... run ...`。
- 需要“延迟后取消”，加一个显式的取消标记 / 门方块，不要依赖条件链。

### 7.3 Repeat 的节拍

```
Always Active, Delay 0, Execute on First Tick On：
  tick 0 执行一次，之后每 tick 一次（20 Hz）

Always Active, Delay 20：
  tick 0 执行一次，之后每 20 tick 一次（1 Hz）

Needs Redstone, Delay 0：
  红石信号只在偶数 tick 被采样 → 最多 10 Hz
```

## 8. 循环

- `Chain` 方块在**同一 tick 内最多执行一次**，所以环形链每 tick 只转一圈。
- 需要“每 tick 多步”时，用 `Repeat` 每 tick 推进一次状态机，而不是在链里写环。
- 需要“固定 N 次”时：
  - N 小：展开成 N 个链方块。
  - N 大：用计分板计数器 + `Repeat`，每 tick 减 1，到 0 停止。
- 需要“同一 tick 内处理一批实体”时，用 `execute as @e[...] run ...` 让命令内部 fork，不要用链环。

## 9. 限制与性能

| 项目 | 限制/建议 |
|---|---|
| 命令文本 | 32,500 字符；实际可读性建议 < 1,000 |
| `maxcommandchainlength` | gamerule 控制单次链执行上限；超长链要拆分 |
| 单 tick 命令数 | 没有硬上限，但每 tick 数百条会掉 TPS；>100 条建议分 tick |
| 函数 | 单次调用最多 10,000 条命令（含嵌套） |
| tickingarea | 最多 10 个；矩形总计 ≤100 区块；圆形半径 ≤4 区块 |
| structure | 单次 ≤ 64×384×64 |
| clone | ≤ 655,360 方块 |
| fill | 大范围会卡；建议 ≤32,768 并分块 |
| 命令方块本身 | 生存不可破坏、活塞推不动；仅创造 OP 可放置/编辑 |

性能原则：

- `Repeat + Always Active` 每 tick 都跑；里面不要放 `fill`/`clone`/`structure`/全玩家 `particle`。
- 先做便宜的 `if` 门，再做昂贵的操作。
- 大范围实体选择用 `type`/`family`/`tag`/`c` 收窄。
- 用 `execute if entity @e[...]` 代替 `testfor @e[...]`（前者可组合，后者是旧命令）。

## 10. 区块加载

- 命令方块只在**已加载且 ticking** 的区块里执行。
- 玩家附近的区块会 ticking；远处机关需要用：

```mcfunction
tickingarea add 0 0 31 31 arena_area
tickingarea add circle 100 64 100 2 arena_circle
tickingarea list
```

- 常加载区域最多 10 个；圆形半径按区块算，最大 4。
- `structure`/`clone` 跨未加载区域会失败；先加载再操作。

## 11. 基岩版独有/易错点

1. **没有 NBT**：不能读写命令方块/箱子/实体的 NBT，也不能用 `summon ... {}`。
2. **不能在命令里配置命令方块**：`setblock` 只能放一个空命令方块；先手动配置一个，再用 `clone` 复制（复制方块实体数据，先在目标版本验证）。
3. **没有 `/data`**：想读状态，只能把状态写进计分板/tag/方块。
4. **没有 `/team`**：用 tag + 计分板模拟队伍。
5. **没有 `/bossbar`**：用 `titleraw actionbar` / 侧边栏模拟。
6. **没有 `/forceload`**：用 `tickingarea`。
7. **`execute` 没有 `store`**：不能把命令返回值写进计分板；用命令自身的副作用 + 成功次数，或先写状态再判断。
8. **`execute` 没有 `detect`**：用 `execute if block`。
9. **红石 10 Hz**：不要用红石钟做 20 Hz 逻辑。
10. **条件链不断链**：见第 4.3 节；这是基岩版地图逻辑最常见的 bug 来源。
11. **`Chain` 默认 Always Active**：很多人以为它需要红石，其实只需要上游触发。
12. **`Delay 0` 的 Chain 是同 tick**：想做“下一 tick 再执行”，必须写 1。

## 12. 一个完整的时序例子

目标：按钮按下后，第 0 tick 记录， 第 2 tick 播放声音，第 5 tick 给物品。

```
[按钮] → [I: scoreboard players set #step obj 1]        (Impulse, Needs Redstone, Delay 0)
        → [C: playsound random.click @a]                  (Chain, Unconditional, Delay 2)
        → [C: give @p bread 1]                            (Chain, Unconditional, Delay 3)
```

实际时间线：

```
tick T     按钮激活，Impulse 在 T+1 执行（Delay 0 = 1 tick）
tick T+1   #step=1，触发下一个 Chain；该 Chain Delay 2
tick T+3   播放声音，触发下一个 Chain；该 Chain Delay 3
tick T+6   给予面包
```

要点：

- Impulse 的 Delay 0 仍然是 1 tick 后执行。
- Chain 的 Delay 是**相对被触发时刻**累加的。
- 需要精确总时长时，用计分板倒计时更直观、可暂停、可重置。

## 13. 参考

- [Command Block — Minecraft Wiki](https://minecraft.wiki/w/Command_Block)
- [Commands/execute — Minecraft Wiki](https://minecraft.wiki/w/Commands/execute)
- [Ticking area — Minecraft Wiki](https://minecraft.wiki/w/Ticking_area)
- [Function (Bedrock Edition) — Minecraft Wiki](https://minecraft.wiki/w/Function_(Bedrock_Edition))
