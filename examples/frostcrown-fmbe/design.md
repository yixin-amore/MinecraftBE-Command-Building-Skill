# 设计：霜冠·维丝佩拉 v2（FMBE 真实命中版）

> 网易 1.21.130 · 14 部件 FMBE + 1 个会追人的隐形 cow 载体 + 1 耐久头盔命中检测。
> 448 个命令方块，5 条链：`init_a` / `init_b`（impulse）/ `main`（repeat）/ `pose_idle` / `pose_cast`（repeat，delay 2）。

## 1. 行为契约

| 项 | 内容 |
|---|---|
| 谁触发 | 玩家走进冰窟（体积选择器 `x=504,y=2,z=504,dx=23,dy=6,dz=23`）→ `st 0→1`；复位由红石块 `505 43 506` + `505 43 516` 触发两条 `init` |
| 起始 | `st=0`：14 个 FMBE 部件待机、隐形载体回中心、血条不显示 |
| 中间 | `st=1`：载体追最近 fighter，FMBE 相对跟随；三阶段、两技能、冰甲破盾、真实命中、个人伤害 |
| 结束 | `st=2` 胜利（核心/部件消失、传出、战利品）／`st=3` 团灭（4 秒无 fighter） |
| 失败 | 团灭只播标题；重放红石块复位 |
| 重置 | `init` 清旧部件/核心/冰晶/仆从、重召 FMBE、重设全部分、清触发红石块 |
| 多人 | 全局 Boss；`fighter`/`dmg` 每玩家；任意玩家真实命中都扣全局血 |

## 2. v1 的两个问题与修正

### 2.1 v1：不是 FMBE

v1 是一只 `ravager`；只有粒子/发光，没有模型拼接和动画。v2 改成：

- 14 只 **fox** 部件（主手方块物品模型）；
- 1 只隐形 **cow** 载体（同时是真实受击核心）；
- 两套 `playanimation` 姿态：`idle` 与 `cast`。

### 2.2 v1：扣血是“手持武器靠近”

v1 的判定是：

```mcfunction
execute as @a[tag=fighter,scores={cd=0},hasitem={item=netherite_sword,location=slot.weapon.mainhand}] at @s if entity @e[tag=boss,r=5] ...
```

它只看“剑 + 5 格内 + 冷却”，玩家站着不动也会每 0.4 秒掉血，不是真实打击。v2 改成**护甲碎裂事件**：

```mcfunction
# m05（每 tick）
replaceitem entity @e[tag=boss_core] slot.armor.head 0 keep leather_helmet 1 9999
# m06（conditional，紧跟 m05）
scoreboard players set hit bs 1
```

原理：

1. 核心头盔数据 `9999`，一次受击就碎；
2. `replaceitem ... keep` 在槽位有物品时**不替换**（成功 0）；槽位空了才补（成功 1）；
3. `m06` 是 conditional chain block，只有上一条 `replaceitem` 成功才执行 → `hit=1`；
4. 只有 `hit=1` 才扣血；距离/手持物完全不参与。

真机小链验证（同一 cow、同一头盔）：

```text
BEFORE 0
打一下  → AFTER1 1
再打一下 → AFTER2 2
```

### 2.3 载体：一个会追人的受击核心

FMBE 部件有碰撞箱，会挡住核心。v3 不再放两个固定核心，而是让**载体本身**当核心：

- 隐形 cow `boss_carrier` + `boss_core`；
- 位置 `515.5 4.5 516.3`（模型中心南侧 0.8 格）；
- cow 不渲染护甲，所以 1 耐久皮革头盔不可见；
- 每 tick 面向最近 fighter，距离 >2.5 时沿 `^ ^ ^0.18` 前进；
- 14 个部件以载体为原点相对 `tp`，偏移 = 原绝对坐标 − 载体坐标；
- 出界/待机回中心；y 锁 4.5，避免 `facing` 的 pitch 让载体上下漂。

这样“模型中心”和“真实受击核心”是同一个移动实体，模型追人时核心也追人。

### 2.4 移动 / 转身命令

**根因**：`tp @s ~ ~ ~ facing entity ...` 原地转身在真机上没有刷新 yaw；`tp @s ^ ^ ^0.18` 于是永远沿初始 yaw 往出口跑。

修复：移动命令直接用 `execute ... facing entity ... eyes`，不依赖载体保存的 yaw：

```mcfunction
execute if score st bs matches 1 as @e[tag=boss_carrier] at @s facing entity @a[tag=fighter,c=1] eyes if entity @a[tag=fighter,r=24] unless entity @a[tag=fighter,r=2.5] run tp @s ^ ^ ^0.18
# 部件位置：同一朝向旋转 ^ 偏移
execute as @e[tag=boss_p_head] at @e[tag=boss_carrier] facing entity @a[tag=fighter,c=1] eyes run tp @s ^0 ^2.9 ^-0.8
# 部件 yaw：~0.01 强制刷新
execute as @e[tag=boss_p_head] at @s run tp @s ~ ~ ~0.01 facing entity @a[tag=fighter,c=1] eyes
```

- `execute ... facing entity` 必须带 `eyes`/`feet` 锚点；省略会不生效。
- `^` 偏移随朝向旋转；`tp ... facing ... eyes` 让 item 模型 yaw 一致。
- `~0.01` 是为了避免同点 tp 不刷新 yaw；下一 tick 位置会被重新校正。
- 左右轴客户端确认；镜像就取反 x。

## 3. FMBE 部件## 3. FMBE 部件

| 部件 | 主手物品 | 坐标 | scale / yscale |
|---|---|---|---|
| head | wither_skeleton_skull | 515.5 7.4 515.5 | 0.90 / 1.0 |
| crown | gold_block | 515.5 8.6 515.5 | 0.35 / 0.6 |
| halo | end_rod | 515.5 9.4 515.5 | 0.45 / 0.8 |
| eye_l | sea_lantern | 515.0 7.6 515.1 | 0.15 / 1.0 |
| eye_r | sea_lantern | 516.0 7.6 515.1 | 0.15 / 1.0 |
| torso | blue_ice | 515.5 6.2 515.5 | 1.20 / 1.6 |
| shoulder_l | polished_diorite | 514.1 6.9 515.5 | 0.65 / 0.8 |
| shoulder_r | polished_diorite | 516.9 6.9 515.5 | 0.65 / 0.8 |
| arm_l | packed_ice | 513.3 5.5 515.5 | 0.40 / 2.0 |
| arm_r | packed_ice | 517.7 5.5 515.5 | 0.40 / 2.0 |
| staff | end_rod | 518.8 5.8 515.5 | 0.80 / 1.0 |
| cloak | light_blue_concrete | 515.5 5.8 516.4 | 1.00 / 1.3 |
| wing_l | white_stained_glass | 513.0 6.8 516.0 | 0.70 / 1.2 |
| wing_r | white_stained_glass | 518.0 6.8 516.0 | 0.70 / 1.2 |

- 表内是初始化时的绝对坐标；运行时部件位置 = 载体 `(515.5,4.5,516.3)` + 表内坐标差。
- 每个部件用 **0.4×0.4×0.4 独占体积**打 `boss_part` + `boss_p_<name>`，不靠 `r=0.6`（会重叠）。
- 每个部件 `invisibility/resistance/slowness`；`event ... ageable_grow_up` 保证成年。
- 每 tick 以载体为原点 `tp`，防重力/AI/玩家挤压；载体移动时整组相对跟随。
- 8 条 `playanimation` 链的顺序不能乱，第一条必须是 `controller.animation.fox.move`。

## 4. 动画

`pose_idle` / `pose_cast` 两条 repeat 链，delay 2：

```text
pose=0：14 部件 × 8 条 idle playanimation
pose=1：14 部件 × 8 条 cast playanimation
```

每条命令自己带 `execute if score pose bs matches 0/1`，两条链不会互相覆盖。
`main` 在技能前摇 `ct>=0` 时置 `pose=1`，技能结束 `ct=-1` 时回 0。

- `idle`：双臂垂下、法杖竖直、光环水平、披风微飘。
- `cast`：双臂抬起 105°、法杖前倾、光环倾斜、翅膀展开、头微低。

## 5. 状态表

| 变量 | 载体 | 范围 | 初值 | 说明 |
|---|---|---|---|---|
| `hp` | `bs` | 0..6000 | 6000 | 全局血量 |
| `sh` | `bs` | 0/1 | 0 | 冰甲 |
| `st` | `bs` | 0/1/2/3 | 0 | 待机/战斗/胜利/团灭 |
| `ph` | `bs` | 1..3 | 1 | 阶段 |
| `pa` | `bs` | 1..3 | 1 | 已播报阶段 |
| `t` | `bs` | 0..∞ | 0 | 战斗 tick |
| `bt` | `bs` | 0..19 | 0 | 1 秒节拍 |
| `sc` | `bs` | 0..80 | 60 | 技能冷却 |
| `ct` | `bs` | -1/30..0 | -1 | 前摇 |
| `sk` | `bs` | 1/2 | 1 | 霜环/冰魂 |
| `stg` | `bs` | 0..60 | 0 | 破防窗口 |
| `wn` | `bs` | 0..∞ | 0 | 团灭计时 |
| `hit` | `bs` | 0/1 | 0 | **只由头盔碎裂事件置 1** |
| `pose` | `bs` | 0/1 | 0 | FMBE 姿态 |
| `dmg` | `dmg` | 0..∞ | 0 | 每玩家伤害 |
| `fighter` | tag | — | — | 战斗中玩家 |
| `boss_core` / `boss_carrier` | tag | — | — | 移动载体（受击核心） |
| `boss_part` / `boss_p_<name>` | tag | — | — | FMBE 部件 |

## 6. 链与布局

| 链 | 类型 | 块数 | 坐标 |
|---|---|---:|---|
| `init_a` | impulse + chain | 60 | y=43，`506,43,506` 起蛇形 |
| `init_b` | impulse + chain | 53 | y=43，`506,43,516` 起蛇形 |
| `main` | repeat + chain | 111 | y=42，`506,42,506` 起蛇形 |
| `pose_idle` | repeat + chain | 112 | y=44，`506,44,506` 起 |
| `pose_cast` | repeat + chain | 112 | y=44，`506,44,518` 起 |
| **合计** | | **448** | 包围盒 13×3×21 |

- 5 个链头：`ia01`/`ib01`（Needs Redstone）、`m01`/`pi01`/`pc01`（Always Active）。
- `m06` 是唯一的 conditional 块，紧贴 `m05`；`i` 链拆成 59/53 两段，避免长链吞 tag 命令。
- `init_b` 链尾拔掉 `505 43 506` 和 `505 43 516` 两块触发红石。

## 7. 战斗数值

| 项 | 数值 |
|---|---|
| 总血量 | 6000 |
| 阶段 | 4000 / 2000 |
| 普通命中 | 40 |
| 破防 | 3 秒 ×2 |
| 踩踏 | 8 / 秒，r=4.5 |
| 霜环 | 18 魔法，r=6.5，减速 II |
| 冰魂 | 2 只流浪者，上限 3 |
| 暴雪（P3） | 4 / 秒 |
| 团灭 | 4 秒无 fighter |

## 8. 导入

1. 建筑 `frostcrown-arena.bdx` → StartPos `500 0 500`。
2. 命令 `frostcrown-commands.bdx` → StartPos `506 42 506`；逐块 repair。
3. `ia01`/`ib01` Needs Redstone；`m01/pi01/pc01` Always Active；`m06` conditional 且紧贴 `m05`。
4. 红石块 `505 43 506` + `505 43 516` 触发；走进 `515 2 515` 开战。

## 9. 验证

- `chain_lint.py`：**0 error**，1 warning（`LONG_CHAIN 111`），5 heads，448 blocks。
- `readbdx.py`：448 个命令方块，5 头，坐标/朝向/模式/延迟/条件/命令文本/自定义名全部与 spec 一致。
- 真机命中链：`BEFORE 0 → AFTER1 1 → AFTER2 2`（conditional 块确实读到 replaceitem 成功）。
- 真机导入后：`PARTS 14 / CORES 1 / UNIQUE 14`；进圈 `ST=1 / HP=6000`。
- 方向验证：bot 东侧 `520 2 516` → `EAST_520_516`；bot 北侧 `515 2 510` → `NORTH_516_512`，不再只往出口跑。
- 命中验证：对 `boss_core` 实体攻击一次后 `HP=5960`，`hit` 在事务末尾清 0。
- **模型转身**：位置用 `^` + `facing ... eyes`、yaw 用 `tp ... facing ... eyes`；客户端需确认左右轴和遮挡。
- **待客户端目视验收**：14 部件拼装位置、idle/cast 姿态、移动时的模型朝向、二/三阶段演出（无头 bot 看不到模型）。
