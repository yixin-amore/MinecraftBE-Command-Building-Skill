# 值噪声地形机：从 7 条核到 32×32 完整机器

> 配套可运行示例：`examples/noise-terrain/`
> 目标环境：网易 1.21.130；10 条链 / 429 命令方块 / 32×32 地形 / 17 档高度。

## 1. 它和「7 命令核」「高斯滤波」的关系

三份样本各解决一段，不要混成一套：

| 样本 | 解决 | 不解决 |
|---|---|---|
| `value-noise.md` | 四角晶格、精度哈希、`fill` 落块 | 完整扫描器、平滑 |
| `value-noise-7cmd.md` | `a/b/c/d + nxs` 的 NX 分叉，一次生成一组采样点 | 外层循环、边界、重置 |
| `gaussian-filter.md` | 邻域加权、二分表面、平滑后重铺 | 高度从哪来、状态机 |
| **本地形机** | 扫描 → 噪声 → 平滑 → 17 档铺设的完整状态机 | 不依赖浮点精度，纯整数 |

关键选择：**不要为了“像样本”而搬 NX 分叉和浮点精度折叠**。

- 256 个柱子实体本身就是 256 路并行，`execute as @e[tag=nt_col]` 一条命令就够；
- 浮点精度折叠换版本可能变，整数哈希 `a*(a+1) % 251` 可复现；
- 真正要学的是“四角晶格 + 双线性 + 实体当坐标 + 邻域平滑”这套骨架。

## 2. 四段式数据流

```text
S10 准备（boot 圈常加载、抽种子）
  → S1 扫描（grid 每 tick 2 根柱子，128 tick）
  → S2..S4 三层值噪声 + 中间高度（3 个 stage）
  → S5..S6 3×3 邻域均值 ×2（2 个 stage）
  → S7 收尾：-偏移、夹 2..18
  → S8 铺设：17 档 × (石头/土/表层/计数)，每 4 tick 一档
  → S99 完成
```

| 状态 | 谁写 | 含义 |
|---|---|---|
| `fb_state` | 各链尾 | 10 准备 / 1 扫描 / 2-7 stage / 8 铺设 / 99 完成 |
| `fb_cur` | 每条链头 | 本 tick 的状态快照，防止同 tick 级联 |
| `fb_cx` `fb_cz` `fb_n` | grid | 列计数 0..8（每 tick 2 根）、行 0..15、计数 0..256 |
| `fb_b` | draw | 当前档位 0..16 |
| `bn2..bn18` | draw | 每档实际铺了多少根柱子（自检） |
| `fb_seed` | boot | 本轮随机种子 0..20000 |

**每个链头先 `fb_cur = fb_state`**：否则同 tick 里前一条链刚推进状态，后面的链会立刻跟着跑，整轮压成 1 tick。

## 3. 计分板侧 3×3 平滑（本项目最有复用价值的一段）

样本用 `t/boat/f` 做 NX 方向树 + 二分表面；本项目高度已经在计分板里，不需要读世界，
所以把“邻域采样”直接放进 `execute`：

```mcfunction
# 中心先入账，cnt=1
execute as @e[tag=nt_col] at @s run scoreboard players operation @s acc = @s hgt
execute as @e[tag=nt_col] at @s run scoreboard players set @s cnt 1

# 8 个邻居：命中才累加，同时数邻居
execute as @e[tag=nt_col] at @s positioned ~-2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players operation @s acc += @e[tag=nt_col,r=0.6,c=1] hgt
execute as @e[tag=nt_col] at @s positioned ~-2 ~ ~-2 if entity @e[tag=nt_col,r=0.6] run scoreboard players add @s cnt 1
# ... 另外 7 个偏移 ...

execute as @e[tag=nt_col] at @s run scoreboard players operation @s acc /= @s cnt
execute as @e[tag=nt_col] at @s run scoreboard players operation @s hgt = @s acc
```

要点：

1. **`as` 后必须 `at @s`**：`positioned ~-2 ~ ~-2` 默认相对命令方块，漏掉 `at @s` 会全采到墙边空气。
2. **边界按实际邻居数 `cnt` 归一化**：角落只有 4 个邻居，固定除以 9 会让边缘整体下沉。
3. **先平滑、后夹断**：中间高度用 `38 + (acc-625)/30`（约 19..57）不夹断；两遍平滑完再 `-28`、夹 `2..18`。先夹再平滑会把山体削成平台。
4. **两遍 3×3 均值 ≈ 高斯**：相邻高差 1.96 → 0.98 格，山体保留；命令数只有 2×22 条。
5. 一条 `execute as` 处理全部 256 根柱子，**不新增实体**；不需要 `t/boat/f` 锚点。

## 4. 扫描器：局部选择器，不要全表扫

v1 每放一根柱子都执行：

```mcfunction
execute as @e[type=armor_stand] unless entity @s[tag=nt_col] unless entity @s[tag=nt_cursor] run tag @s add nt_new
```

256 根柱子时，这是 **每 tick 对全表做两次 `unless entity`**，128 tick 就是几万次检查。
v2 改成游标处的局部选择器：

```mcfunction
execute as @e[tag=nt_cursor] at @s run summon armor_stand ~ ~ ~
execute as @e[tag=nt_cursor] at @s run tag @e[type=armor_stand,r=0.6,tag=!nt_cursor] add nt_col
```

- 新柱子就在游标脚下，`r=0.6` 只命中它；
- 旧柱子至少 2 格远，不会被误标；
- A/B 两根柱子共享一次 `px/pz` 基准计算，grid 从 33 块降到 24 块。

**代价**：依赖“游标处没有别的盔甲架”。生成区先 `kill @e[tag=nt_col]`，并保证没有宠物/展示实体停在游标脚下。

## 5. 数学与溢出

一层值噪声（全部 32 位整数）：

```text
ix = (px + ox) / L          fx = ((px + ox) % L) * (256/L)
iz = (pz + oz) / L          fz = ((pz + oz) % L) * (256/L)
a  = ix*127 + iz*311 + seed + salt
H(a) = a*(a+1) % 251
v  = (H00*fx2*fz2 + H10*fx*fz2 + H01*fx2*fz + H11*fx*fz) / 65536
```

- `fx2 = 256 - fx`，权重和恒为 65536；
- 采样点全在奇数坐标，`fx` 不会正好是 0，避免值噪声在晶格点上退化；
- `a ≤ 7*127 + 7*311 + 521 + 20000 ≈ 2.4e4`，`a*(a+1) ≈ 5.6e8 < 2^31`；
- 平滑和 `≤ 57*9 = 513`，不会溢出；
- 除法是基岩版**朝 0 截断**，哈希输入恒非负，所以 `%` 不需要处理负数。

## 6. 六个必查失败模式

| 现象 | 根因 | 修法 |
|---|---|---|
| 启动 1-2 秒就“完成”，实际没长 | `fb_n/fb_b` 跨轮保留，第一拍就满足完成条件 | boot 清零 `fb_cx/fb_cz/fb_n/fb_b/fb_t/fb_cur`；prep 再兜一次 |
| 地形全平/全 0 | 平滑漏 `at @s`，所有柱子采到墙边空气 | `as ... at @s positioned ...` |
| 第二行整体错位 | 行尾 `tp` 少算/多算 | 第 8 对柱子放完时游标在 `x=29`，换行 `tp ~-28 ~ ~2` |
| 地板没有、柱子掉虚空 | 导入那一 tick 地形区还没加载，`fill/summon` 静默失败 | boot 先 `tickingarea add`，prep 2 tick 后再动土 |
| 命令方块在、命令空 | 服务器丢掉“玩家不在附近”的 `CommandBlockUpdate` | 逐块 `tp → setblock → 数据包`，再补一遍只发数据包的修复遍 |
| repeat 链不走 | 导入器不认 BDX 的“总是开启” | 给每个 repeat 头贴红石块，或换读标志位的导入器 |

## 7. 验证配方

```bash
./run_all.sh
# gen.py → chain_lint.py → sim.py 400 → preview.py → readbdx.py
```

必须同时看三件事：

1. **静态**：`chain_lint.py` 0 error；`readbdx.py` 逐块对 spec（命令文本/坐标/朝向/延迟/红石）。
2. **离线**：`sim.py` 连跑两轮，256 根柱子的 `hgt` 与 `noise.py` 模型逐格相同；第二轮专门抓“秒完成”。
3. **真机**：连续触发两次，读 `fb_seed` / `fb_state` / 高度分布；同一颗种子下游戏内分布应与 `noise.py` 逐档相同。

## 8. 一句话

> **扫描器造 256 个坐标，一条 `execute as` 并行算噪声，`as+at @s+positioned` 做 3×3 平滑，按高度档位 `fill`；状态机分 stage，种子每轮随机，计数器每轮清零。**
