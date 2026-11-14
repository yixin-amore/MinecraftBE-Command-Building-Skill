# 坐标运算四思想：二分 / NX / 递归 / 大数圆规

> 命令方块没有浮点、没有 `sin/cos`、不能给 `tp/fill` 传变量。
> 所谓“坐标运算”，本质是**把整数分数变成字面量坐标**的四套手法。
> 本篇是总纲；执行分叉的细节见 `nx-tree.md`，计分板存储细节见 `scoreboard-memory.md`，
> 整数/定点/几何基础见 `command-mathematics.md`。
>
> 参考来源：逆天神域《如何 2cb 制作沉浸式传送门，1cb 实现多边形填充？——坐标运算教程系列【第一期】》
> （BV1xAM96JEXv，重点是“用 `positioned`+`rotated` 把标量变成方向”）。

---

## 0. 三条公理

| 公理 | 含义 | 后果 |
|---|---|---|
| **A1 位置只能存在实体上** | 计分板只有整数，没有坐标类型 | 要么每 tick 用分数重算实体坐标，要么把实体本身当“位置寄存器” |
| **A2 坐标必须是字面量** | `tp @s ~<分数> ~ ~` 不合法 | 分数→坐标必须靠**离散阶梯**（二分/查表）落成字面量 |
| **A3 方向可以用旋转换** | `rotated as @e` + `^ ^ ^d` 等价于“沿朝向走 d 格” | 不需要 `sin/cos` 就能得到任意方向上的点 |

A2 是所有“坐标运算”的出发点：**你永远在写死数字**，算法只是决定“写哪些数字、按什么顺序写”。

---

## 1. 二分思想

### 1.1 两种用法

| 用法 | 输入 | 输出 | 典型场景 |
|---|---|---|---|
| **位移二分**（贪心拆解） | 一个速度/位移分数 `v` | 若干次 `tp ~2^k` | 弹球、投射物、任意步长移动 |
| **位置二分**（阶梯还原） | 一个绝对位置分数 `p` | 从基准点出发的阶梯 `tp` | 任意点传送、画点、按分数摆实体 |

### 1.2 位移二分：贪心拆 `2^k`

把 `|v|` 拆成 `8+4+2+1` 这类权重，每个权重写一条 `tp`：

```mcfunction
# v = 11 → 走 8 + 2 + 1 个单位（单位 = 1/16 格）
execute as @e[tag=ball] if score @s v matches 8.. at @s run tp @s ~0.5 ~ ~
execute as @e[tag=ball] if score @s v matches 8.. run scoreboard players remove @s v 8
execute as @e[tag=ball] if score @s v matches 4.. at @s run tp @s ~0.25 ~ ~
execute as @e[tag=ball] if score @s v matches 4.. run scoreboard players remove @s v 4
execute as @e[tag=ball] if score @s v matches 2.. at @s run tp @s ~0.125 ~ ~
execute as @e[tag=ball] if score @s v matches 2.. run scoreboard players remove @s v 2
execute as @e[tag=ball] if score @s v matches 1.. at @s run tp @s ~0.0625 ~ ~
execute as @e[tag=ball] if score @s v matches 1.. run scoreboard players remove @s v 1
```

- 4 级覆盖 0..15；8 级覆盖 0..255；成本 `2·ceil(log2(max+1))` 条。
- 比“循环 8 次固定 0.0625”省 4 倍命令，而且**任意步长精确**。
- 负方向：再写一套 `..-8`、`..-4`… 用 `~-0.5`，或者用 1.4 的旋转法共用一套。

### 1.3 位置二分：从基准点还原绝对坐标

先把实体拉到基准点，再用同一套权重把分数**加回去**：

```mcfunction
# 目标 y = 56，基准 -64：by = (56+64)*100 = 12000（单位 0.01 格）
execute as @e[tag=ball] at @s run tp @s 0 -64 0
execute as @e[tag=ball] run scoreboard players operation @s t = @s by
# 每个 rung 的判定门限 = 2^k - 6400（6400 = 基准 -64 的 0.01 格）
execute as @e[tag=ball,scores={t=26368..}] at @s run tp @s ~~327.68~
scoreboard players add @e[tag=ball,scores={t=26368..}] t -32768
execute as @e[tag=ball,scores={t=9984..}] at @s run tp @s ~~163.84~
scoreboard players add @e[tag=ball,scores={t=9984..}] t -16384
# … 一直到 1（门限 = -6399，位移 0.01）
```

**为什么门限要减 6400**：基准是 `-64`，即 `-6400` 个 0.01 格。设剩余量 `t`，
则“位置 + 6400 = 已走的总量”，而“剩余可走 = t + 6400”。
每个 rung 判断 `t + 6400 ≥ 2^k`，等价于 `t ≥ 2^k - 6400`；走完减 `2^k`，不变量保持。
这样 **一个有符号的绝对坐标**（可以低到 -64）就能用纯正向阶梯还原，
不需要为负数再写一套。

> 校验题：`by = 1000`（y=10）。`1000+6400=7400=4096+2048+1024+128+64+32+8`，
> 阶梯依次命中 4096/2048/1024/128/64/32/8 → 总位移 74 格 → `-64+74=10` ✅

### 1.4 符号处理三法

| 方法 | 做法 | 代价 | 适用 |
|---|---|---|---|
| **临时量取反** | `operation @s t = @s p`，再对 `t` 乘 `kneg` | 1 条 | 最常用；**绝不能对 `p` 本身取反** |
| **旋转 180°** | `tp @s ~ ~ ~ ~180 ~` 后用 `^^^` 前向 | 1 条 | 配合 `^^^` 的射线式移动 |
| **双套阶梯** | 正负各写一套 `tp` | ×2 | rung 很少、逻辑要直白 |

**旋转法完整套路（x 轴为例）**：

```mcfunction
execute as @e[tag=ball] at @s run tp @s 0 ~ ~ -90 0        # x 归零，朝向 +x
execute as @e[tag=ball] run scoreboard players operation @s t = @s bx
execute as @e[tag=ball,scores={bx=..-1}] at @s run tp @s ~ ~ ~ ~180 ~   # 转身 → 朝 -x
scoreboard players operation @e[tag=ball,scores={bx=..-1}] t *= kneg k   # 只反临时量
# 之后一律 tp @s ^^^<2^k/100>
```

### 1.5 四个必须记住的坑（都是实测踩出来的）

1. **`*=` 右边不能写字面量**。`scoreboard players operation @s vx *= -1` 会报
   “意外的 -1”；必须先 `scoreboard players set kneg k -1`，再 `*= kneg k`。
2. **选择器只能一组方括号**。`@e[tag=ball][scores={vx=1..}]` 非法，
   必须 `@e[tag=ball,scores={vx=1..}]`。双括号会让整条命令静默报错。
3. **反弹要先除后乘**。系数是负数时，`*= kmul` 会先把分数变成负的，
   紧跟的 `/=` 若带 `scores={vx=1..}` 门限就永远不触发。顺序应为
   `/khor` → `*kmul`（kmul 为负），得到“反向 + 衰减”。
4. **速度要限幅**。一个 tick 位移超过 1 格就会**隧穿** 1 格厚的墙/地板；
   把速度钳到 `±80`（0.8 格/tick）并保证墙体至少 1 格厚即可稳定。

---

## 2. NX 思想（N 叉树 / N 进制）

NX 有两层含义，别混：

| 层 | 含义 | 例子 |
|---|---|---|
| **执行分叉** | 一条命令产生 N 个执行上下文 | `as @e[...]`、`positioned`、`rotated`、`anchored` |
| **N 进制拆位** | 用 base-N 位数代替 2 的幂 | 十进制 `1000/100/10/1`、四进制 `256/64/16/4/1` |

### 2.1 执行分叉 = 树的节点

```text
根（玩家/鱼钩/锚点）
 ├─ positioned ^^^1   → 叶子（近）
 ├─ positioned ^^^2   → 叶子
 ├─ positioned ^^^4   → 叶子
 └─ …… 8/16/32
```

- 一个方块里可以叠很多层 `execute`，所以“2cb 传送门”不是 2 个方块干 2 件事，
  而是 2 个方块里各塞了一棵**分叉树**。
- 成本 = 分支数 × 叶子数 × 20 Hz；分支预算见 `nx-tree.md` §成本。

### 2.2 N 进制拆位：把 16 级二分压成 4 级

二进制要 16 级才能覆盖 0..65535；**十进制只要 4 级**（千/百/十/个）：

```mcfunction
# p = 1234 → 走 1000 + 200 + 30 + 4
execute as @e[tag=t] if score @s p matches 1000.. at @s run tp @s ~10 ~ ~
execute as @e[tag=t] if score @s p matches 1000.. run scoreboard players remove @s p 1000
execute as @e[tag=t] if score @s p matches 100..  at @s run tp @s ~1 ~ ~
execute as @e[tag=t] if score @s p matches 100..  run scoreboard players remove @s p 100
execute as @e[tag=t] if score @s p matches 10..   at @s run tp @s ~0.1 ~ ~
execute as @e[tag=t] if score @s p matches 10..   run scoreboard players remove @s p 10
execute as @e[tag=t] if score @s p matches 1..    at @s run tp @s ~0.01 ~ ~
execute as @e[tag=t] if score @s p matches 1..    run scoreboard players remove @s p 1
```

**取舍**：进制越大，级数越少（命令越少），但每级位移的字面量越大、精度粒度越粗。
一般用 **十进制做位置**（步长 0.01 格，肉眼够细）、**二进制做速度**（步长 0.0625 格，平滑）。

### 2.3 配方：1cb 多边形填充

单个循环方块，每 tick 填**一条水平切片**，切片由“当前行号 → 左右端点”的表决定：

```mcfunction
# 循环方块（Always Active, Delay 0）
# 1) 行号推进
scoreboard players add fb_row arena 1
execute if score fb_row arena matches 12.. run scoreboard players set fb_row arena 0
# 2) 查表拿左右端点（表用 if score 分派，等价于 N 叉树的一层）
execute if score fb_row arena matches 0 run scoreboard players set fb_x1 arena -4
execute if score fb_row arena matches 0 run scoreboard players set fb_x2 arena 4
# … 每行两条
# 3) 用端点画（端点已经被二分/十进制还原成坐标，或直接写死）
fill <x1> <y> <z> <x2> <y> <z> concrete
```

要点：
- **一条命令只能画一条切片**，多边形是靠“多 tick 拼出来”的——所以叫 1cb。
- 端点表就是 N 叉树的“叶子数组”，行号就是遍历顺序。
- 顶点多的多边形：把表换成“顶点表 + 扫描线插值”，插值本身用二分/十进制还原。

### 2.4 配方：2cb 沉浸式传送门

视频里的思路（两个方块）：

```mcfunction
# CB1（循环）：玩家进入门框体积 → 传送到目标点
execute as @a[x=<门框中心>,y=<中心>,z=<中心>,dx=1,dy=2,dz=1] at @s run tp @s <目标坐标>

# CB2（连锁/循环）：用 positioned + rotated 把“门后场景”沿视线补出来
execute as @p positioned <锚点> rotated as @e[tag=nxs] run <fill/clone 局部坐标>
```

- 沉浸感的来源不是“看得更远”，而是**门后有一段被复制的房间/景观**，
  玩家以为看到了远处；`rotated as` 让复制的方向跟玩家朝向一致。
- `tag=nxs` 的实体就是一个“方向锚点”，用 `rotated as @e[tag=nxs]` 借用它的 yaw/pitch。
- 如果当前版本的 `fill` 不吃 `^`，就退回“`positioned` 算出绝对角点 + `fill` 绝对坐标”。

---

## 3. 递归思想

命令方块**没有函数调用**（函数是数据包/行为包，用户常常不允许）。
能用的“递归”只有三种等价形式：

### 3.1 展开（unrolled）

把递归体复制 N 份，用序号区分深度。成本线性，最稳，适合深度 ≤ 8。

```mcfunction
# 深度 3 的展开：每层一个 tag，避免互相干扰
execute as @e[tag=deep0] run tag @s add deep1
execute as @e[tag=deep1] run tag @s add deep2
execute as @e[tag=deep2] run tag @s add deep3
```

### 3.2 重入（self-retrigger）= 尾递归

链尾 `setblock` 一个红石块到链头旁边，下一 tick 链头重新触发：

```mcfunction
# 链尾（循环方块，Always Active）
execute if score fb_done arena matches 0 run setblock <链头旁> redstone_block
```

- 等价于尾递归 → while 循环；每轮 1 tick，**有 1 tick 开销**。
- 必须显式写退出条件，否则永久自激。

### 3.3 栈在计分板里

- 单变量栈：一个分数存深度，`if matches` 分派到“返回地址”块（跳转表）。
- 多值栈：用十进制位拼接（`stack = stack*100 + v`），出栈 `v = stack%100; stack /= 100`。
- 上限：32 位 → 十进制最多 9 层 `*10`，二进制 31 层。

### 3.4 递归的替代：状态机

绝大多数“看起来需要递归”的活，用**状态机 + 队列**更省：
把待处理的坐标/实体塞进 tag 或计分板队列，每 tick 处理一个，天然带节流。
见 `chain-patterns.md` 的状态机与队列模板。

---

## 4. 大数圆规（球面近似）思想（变种 NX）

“大数圆规”= **把半径放大到很大，用整数步进逼近圆弧，再除回来**。
本质是 NX 的一个变种：不是分叉，而是**放大坐标空间换精度**。

### 4.1 圆：整数判定 + 对称

```text
x² + z² ≤ r²        （32 位，r ≤ 215 时安全；再大要先 /10）
```

只算第一象限，再镜像：

```text
(+x,+z) (+x,-z) (-x,+z) (-x,-z)   → 分支数 4N → N
```

用 `fill` 每行画一条弦（半宽 `w = isqrt(r² - dy²)`），一个循环方块一条弦。

### 4.2 球：分层 + 每层半径

```text
for h in -r..r:
    rr = isqrt(r² - h²)      # 该层圆的半径
    fill <圆盘>
```

层数 `2r+1`，每层一个 `fill`（或一个 `fill` 圆盘用 1cb 扫描线）。
`isqrt` 在生成器里算好写成表，运行时不求平方根。

### 4.3 “圆规”式画弧（不需要表的做法）

从圆心出发，用**固定步长 + 方向微调**走 N 步：

```mcfunction
# 每 tick 走一步：positioned 到当前点，rotated 朝向切线，^^^1
execute as @e[tag=pen] at @s rotated as @e[tag=dir] run tp @s ^^^1
execute as @e[tag=pen] at @s run tp @s ~ ~ ~ <旧yaw+步进角>
```

- 步进角必须是 360 的整除数（15°/30°/45°），否则 `tp` 的 yaw 会累加误差。
- 半径越大，同样的整数步进看起来越“圆”；这就是“大数”的含义。
- 需要绝对精度时，用 4.1 的判定式替代。

### 4.4 什么时候用哪个

| 需求 | 方案 | 成本 |
|---|---|---|
| 圆/球**实心填充** | 4.1/4.2 扫描线 + `fill` | 1 条/行 |
| 圆/球**轮廓** | 对称 + 每 15° 一个点 | 24 条/圈 |
| 任意曲线（抛物线/螺旋） | 生成器算表 → 二分还原坐标 | 表长 × 2 |
| 高速运动轨迹 | 4.3 圆规步进 | 1~2 条/tick |

---

## 5. 计分板：全部正确语法（网易 1.21.130）

> 这一节是“抄了就能跑”的版本，坑都标了。存储模型见 `scoreboard-memory.md`。

### 5.1 objectives

```mcfunction
scoreboard objectives add <name> dummy [displayName]
scoreboard objectives remove <name>
scoreboard objectives list
scoreboard objectives setdisplay <list|sidebar|belowname> [objective] [ascending|descending]
```

- 只有 `dummy` 可用；`deathCount`/`health` 等在网易版不可靠。
- `belowname` 无下划线。
- 侧边栏最多 15 行；`#` 开头的假玩家不显示。

### 5.2 players 基础

```mcfunction
scoreboard players set <target> <obj> <int>
scoreboard players add <target> <obj> <int>
scoreboard players remove <target> <obj> <int>
scoreboard players reset <target> [obj]
scoreboard players random <target> <obj> <min> <max>
scoreboard players test <target> <obj> <min> [max]     # 实测可用（返回成功/失败）
```

- `add` 负数 = 减；`remove` 负数 = 加。
- `reset` 是删除记录（不是置 0）。
- `random` 含两端闭区间；目标可以是选择器（`@e[tag=x]`）。
- `get` 在网易 1.21.130 **不可用**；读分数用 `execute if score ...` 或 `tellraw` 的 `score` 组件。

### 5.3 operation（唯一能做“变量运算”的命令）

```mcfunction
scoreboard players operation <target> <obj> <op> <srcTarget> <srcObj>
```

- `op` ∈ `=` `+=` `-=` `*=` `/=` `%=`。
  **`min=` / `max=` 在网易 1.21.130 实测不支持**（格式错误），要钳制就写
  `execute if score @s x < @s y run scoreboard players operation @s x = @s y`。
- **右侧必须是“目标 + objective”，不能是数字**：
  `*= -1` ❌ → 先 `set kneg k -1`，再 `*= kneg k` ✅
- 32 位整数；乘法会溢出；除法是截断除法，除数为 0 时目标不变。
- 负数取模符号随被除数；环形数组要 `((x%n)+n)%n`。

### 5.4 条件写法

```mcfunction
execute if score <t> <obj> matches <区间>
   区间写法：5   |   1..5   |   ..5   |   1..
execute if score <t> <obj> <op> <t2> <obj2>
   op：< 和 <= 实测可用；= 实测不支持（用 matches 判等）
   稳妥写法：a >= b 写成 unless score a < b；a > b 写成 unless score a <= b
execute unless score ...        # 取反
```

- `matches` **只吃区间**，没有比较符；判等用 `matches 5`，判范围用 `matches 1..5`。
- 跨目标比较优先用 `unless` 反向写，避免踩比较符支持的坑。
- 选择器里的分数过滤：`@e[scores={obj=1..5}]`（**只能一组方括号**）。

### 5.5 常用组合模板

```mcfunction
# 钳制
execute if score @s hp matches ..0 run scoreboard players set @s hp 0
execute if score @s hp matches 100.. run scoreboard players set @s hp 100

# 扣费（够才扣）
execute if score fb_cost k <= fb_gold k run scoreboard players operation fb_gold k -= fb_cost k

# 百分比（先乘后除，最后钳制）
scoreboard players operation @s pct = @s cur
scoreboard players operation @s pct *= k100 k
scoreboard players operation @s pct /= kmax k
execute if score @s pct matches 100.. run scoreboard players set @s pct 100

# 初始化（每个玩家一次）
execute as @a unless score @s init matches 1 run scoreboard players set @s init 1
```

### 5.6 错误清单（按出现频率排）

| 症状 | 原因 | 修法 |
|---|---|---|
| “意外的 -1” | `operation *= -1` | 用常量分数 |
| 命令完全没反应 | `@e[tag=x][scores={...}]` 双括号 | 合并成一组 |
| 反弹只减速不反向 | `*=` 系数是正数 | 系数取负，且先除后乘 |
| 归零后又变回原值 | 用了 `reset`（删除）而不是 `set 0` | 分清两者 |
| 分数永远匹配不上 | 分数未初始化（未跟踪） | 显式 `set` 或 `add 0` |
| 溢出成负数 | 32 位乘法 | 先除后乘 / 拆项 |

---

### 5.7 实测记录（网易 1.21.130，2026-11-14）

| 写法 | 结果 |
|---|---|
| `execute if score a syn < b syn` | ✅ 触发 |
| `execute if score a syn <= b syn` | ✅ 触发 |
| `execute if score b syn > a syn` | ✅ 触发 |
| `execute if score a syn >= b syn` | ❌ 指令格式错误 |
| `execute if score a syn = b syn` | ❌ 指令格式错误 |
| `execute as @e[tag=x,scores={t=5..}]` | ✅（单括号） |
| `execute as @e[tag=x][scores={t=5..}]` | ❌ 静默失败（双括号） |
| `scoreboard players test a syn 1 10` | ✅ 无报错 |
| `scoreboard players operation a syn min= b syn` | ❌ 指令格式错误 |
| `scoreboard players operation a syn *= -1` | ❌ “意外的 -1” |
| `scoreboard players random d syn 1 6` | ✅ 无报错 |
| `tag @e[type=armor_stand,r=2] add t`（执行者离目标 13 格） | ❌ 不生效 |
| `tag @e[type=armor_stand,r=1000] add t` | ✅ 生效 |
| `tag @e[type=armor_stand,c=1] add t` | ✅ 生效 |
| `execute positioned <锚点> run tag @e[...r=2]` | ❌ 仍按执行者算距离 |

> 结论 1：**判等/判大用 `matches` 或 `unless` 反向比较**，`min=/max=` 手写。
>
> 结论 2：**`r=` 的距离基准是执行者（玩家/机器人/命令方块），不是 `positioned` 的锚点**。
> 给实体打标签/批量选中时，别用 `r=` 圈定范围——先 `kill` 清场再用
> `tag @e[type=X] add ...`，或用 `c=1` 取最近一个。

## 6. 四思想怎么组合

一个“按分数任意摆点”的最小闭环：

```text
二分（位移/位置）→ 决定坐标字面量
NX（执行分叉）   → 一次摆 N 个点/扫 N 条线
递归（重入）     → 每 tick 推进一行/一帧
大数圆规         → 点集本身是圆/球/螺旋
计分板           → 存位置、速度、行号、栈
```

实践顺序建议：

1. 先用**生成器**把表算好（圆、球、曲线）；
2. 表存成 `if score row matches N` 的稠密分派（NX 的一层）；
3. 每个叶子用**二分阶梯**把表值还原成坐标；
4. 外层用**循环方块 + 重入**每次推进一步；
5. 全部状态塞进 `dummy` 计分板，假玩家用 `fb_` 前缀。

---

## 7. 速查

| 我要… | 用 |
|---|---|
| 按分数移动 | 位移二分（8/4/2/1） |
| 按分数传送到任意点 | 位置二分（基准 + 门限 `2^k - 基准×100`） |
| 负坐标 | 临时量取反（首选）/ 转 180° / 双套阶梯 |
| 沿视线走 | `rotated as` + `^^^d` |
| 一次处理 N 个点 | `execute as` / `positioned` 分叉 |
| 每 tick 推进一步 | 循环方块 + 重入 + 退出条件 |
| 画圆/球 | 扫描线 + `isqrt` 表 + 四象限对称 |
| 读分数 | `execute if score` 或 `tellraw` 组件的 `score` |
