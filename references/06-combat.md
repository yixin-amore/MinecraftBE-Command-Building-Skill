# 战斗（44~51 / 84~86 / 102 章）

> 射线与肢体判定、刀光、连招、能量、弹药换弹、鱼竿枪、枪械五条路、伪无子弹、归属与盒子、伪无判定与伪无粒子。
**什么时候读**：做武器/技能/命中判定，或参考已有战斗系统的完整实现。

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**（拆家前是第几章现在还是第几章）；跨文件的章号去主文件的
> 「章号 → 文件 对照表」查。这里的结论可能早于主文件的「⭐ 当前基线」——
> **冲突时以基线为准**。

---

## 44. 输入只有主手

命令方块**读不到按键**。

| 想检测的    | 能做到吗 | 说明                                               |
| ------- | ---- | ------------------------------------------------ |
| 左键 / 右键 | ❌    | 耐久 hack 会随版本失效，`hasitem` 不会                      |
| 主手拿什么   | ✅    | `hasitem={item=X,location=slot.weapon.mainhand}` |
| 视角朝向    | ✅    | `rx` / `ry` / `rxm` / `rym`                      |
| 玩家位置    | ✅    | `x` `y` `z` `r` `dx` `dy` `dz`                   |
| 抬头 / 低头 | ✅    | `rxm=88` / `rxm=-88`                             |
| 潜行 / 跳跃 | ⚠️   | 只能靠 `rm=0.05` 判站立等间接方式                           |

**唯一稳定的输入面**：切物品栏（= 选技能）、抬头低头（= 菜单）、走近（= 自动攻击）。

---

## 45. 射线判定

### 45.1 沿视线推进

```
execute as @a at @s positioned ^ ^ ^1 run ...
execute as @a at @s positioned ^ ^ ^2 run ...
execute as @a at @s positioned ^ ^ ^3 run ...
```

`^ ^ ^N` 是**局部坐标**：`^左 ^上 ^前`，`前` 沿视线方向。

### 45.2 分段命中

```
execute as @a at @s positioned ^^^1 if entity @e[r=0.5,c=1,type=!player] run ...
execute as @a at @s positioned ^^^2 if entity @e[r=0.5,c=1,type=!player] run ...
```

N 递增做射程，每格判一次。

### 45.3 虚拟层（避免误伤地形）

```
positioned ~~-500.5~
```

把判定点挪到 y=-500 的"虚拟位置"，那里什么都没有，**不会误判到真实地形**。  
然后 `at @e[r=0.5,c=1]` 把执行位置切回实体。

### 45.4 敌人黑名单

```
type=!item,type=!player,type=!fishing_hook,type=!xp_orb,type=!boat,type=!arrow
```

❗ 不排除 `item` 的话，地上掉的东西会被当敌人打；  
不排除 `fishing_hook` 的话，鱼竿钩会被打。

### 45.5 用视角锁定

```
execute as @a[rym=..-45] ...    ← 朝北
execute as @a[ry=..45,rym=-45] ...  ← 朝东
```

四个方向用 `ry` / `rym` 的区间切分。

---

## 46. 肢体判定

### 46.0 穷举模板：3 段肢体 × N 格

射线判定没有捷径，就是穷举：**每个距离 × 每个部位**各一条。
100 格 × 3 段 = 300 条，这是"打得到"的代价。

```python
LIMBS = ((1, "-499"), (2, "-499.5"), (3, "-500.5"))   # 头 / 胸 / 腿（相对 y+500 的偏移）
for n in range(1, RANGE + 1):
    for limb, off in LIMBS:
        cmds.append(
            "execute as @e[tag=子弹,scores={射程=%d..,命中格=0}] at @s "
            "positioned ^^^%d positioned ~~%s~ at @e[r=1.2,c=1,身体] "
            "unless score @e[c=1] tg_team = @s tg_team "
            "run scoreboard players set @s 命中格 %d" % (n, n, off, n * 10 + limb))
```

三个要点：

- **编码 `距离*10 + 部位`**：11 = 1 格打中头，1003 = 100 格打中腿。
  一个分数同时记住"哪一格"和"哪个部位"，不用两个变量。
- **`命中格=0` 是"还没打中"的闸门**：一旦命中就不再判后面的格，
  避免 `r=1.2` 的球把相邻两格都算上（一枪扣三次血）。
- **判定只记分，不扣血**：扣血统一走「赋分 → 按分扣血」（18.1），
  所以加枪型 / 改射程都不用动这 300 条。

### 46.0.5 玩家姿态检测（纯命令方块，不用行为包）★

**基岩版没有 `sneaking` 选择器**，但姿态可以靠**碰撞箱高度**读出来：
站立 1.8 格、蹲下 1.5 格、爬行/游泳 0.6 格。
`@s[y=~1.5,dy=1]` 问的是"从脚往上 1.5~2.5 格这个体积里，有没有我的碰撞箱" ——
站立时有，蹲下时没有。**这是唯一可靠的纯命令方块姿态检测法**（U35）。

```text
# 站立
execute as @a at @s if entity @s[y=~1.5,dy=1] run <指令>

# 下蹲（1.0~1.5 之间有碰撞箱，1.5 以上没有）
execute as @a at @s unless entity @s[y=~1.5,dy=1] if entity @s[y=~1,dy=1] run <指令>

# 静止 / 非静止（脚下一格内有没有自己 = 位置没动）
execute as @a at @s anchored feet if entity @s[r=0.01] run <指令>
execute as @a at @s anchored feet unless entity @s[r=0.01] run <指令>

# 游泳 / 爬行 / 滑翔（碰撞箱更矮）
execute as @a at @s unless entity @s[y=~0.7,dy=1] run <指令>
execute as @a at @s unless entity @s[y=~0.7,dy=1] if block ~ ~ ~ water run <指令>
execute as @a at @s unless entity @s[y=~0.7,dy=1] unless block ~ ~ ~ water     unless block ~ ~-0.1 ~ air run <指令>
execute as @a[hasitem=[{item=elytra,location=slot.armor.chest}]] at @s     unless entity @s[y=~0.7,dy=1]     if blocks ~0.295 ~ ~0.295 ~-0.295 ~-0.5 ~-0.295 ~ 319 ~ all run <指令>

# 睡觉 / 死亡 / 存活
execute as @a at @s unless entity @s[y=~0.3,dy=1] run <指令>
execute as @a at @s unless entity @e[type=player,r=0.01] run <指令>
execute as @e[type=player] at @s run <指令>
```

**行走 vs 奔跑**：靠"水平速度"区分。做法是造一个参照点 ——
先 `positioned ~ ~10000 ~` 抬高（避开地形），`facing entity @s feet` 对准脚，
`positioned ^ ^ ^10000` 落回脚上，再 `rotated ~ 0` 把俯仰拉平、`positioned ^ ^ ^-3`
往后水平退 3 格，得到一个"身后 3 格"的点；最后量玩家到这个点的距离。

```text
# 行走
execute as @a at @s if entity @s[y=~1.5,dy=1]     positioned ~ ~10000 ~ facing entity @s feet positioned ^ ^ ^10000     if entity @s[rm=0.01] rotated ~ 0 positioned ^ ^ ^-3     if entity @s[r=2.805,rm=2.775] run <指令>

# 奔跑（同样的参照点，只是距离窗口收窄）
execute as @a at @s if entity @s[y=~1.5,dy=1]     positioned ~ ~10000 ~ facing entity @s feet positioned ^ ^ ^10000     if entity @s[rm=0.01] rotated ~ 0 positioned ^ ^ ^-3     if entity @s[r=2.75,rm=2.71] run <指令>
```

> 数值（2.775 / 2.805 / 2.75 / 2.71）是实测窗口，**不要凭感觉改**。
> 换世界 / 换移动速度后要重新标定。

### 46.1 锚点

```
execute as @a at @s anchored eyes run ...    ← 以眼睛为原点
execute as @a at @s anchored feet run ...    ← 以脚为原点
```

| 部位 | 判定方式                                    |
| -- | --------------------------------------- |
| 头  | `anchored eyes` + `positioned ~ ~ ~`    |
| 胸  | `anchored feet` + `positioned ~ ~1.2 ~` |
| 腿  | `anchored feet` + `positioned ~ ~0.4 ~` |

### 46.2 站立检测

```
execute as @a at @s anchored feet if entity @s[r=0.05] run ...
```

`rm=0.05` 表示"位置几乎没变"，用来判"站着不动"。

### 46.3 已知 bug

❗ `anchored` **每次 `execute` 只生效一次**（MCPE-165051）。  
链式 `anchored eyes positioned ... anchored feet ...` 只有第一个生效。

❗ `anchored` 会**污染相对坐标**（MCPE-162681）。  
`anchored eyes positioned ~ ~ ~` 的 `~` 是以眼睛为基准的，不是脚。

---

## 47. 刀光

### 47.1 思路：摆点，不画线

`positioned ^左^上^前` 在几个固定偏移上各放一个粒子，靠视觉连成弧线。  
**不做逐点射线判定**，只在出手那一帧用 `@e[r=3.5]` 结算一次。

```
execute as @a[scores={slash=1,slash_t=1..}] at @s positioned ^1.2^0.9^3 run particle minecraft:balloon_gas_particle ~~~ 
```

主力粒子：`minecraft:balloon_gas_particle`（白色气流，拖尾感强）。

### 47.2 四形态坐标表（实测值）

坐标格式 `(左, 上, 前)`，空字符串表示 0。

**形态 1 · 横斩（右 → 左，弓形）**

| 左    | 上    | 前 |
| ---- | ---- | - |
| 1.2  | 0.9  | 3 |
| 0.8  | 1.05 | 3 |
| 0.4  | 1.15 | 3 |
| 0    | 1.2  | 3 |
| -0.4 | 1.15 | 3 |
| -0.8 | 1.05 | 3 |
| -1.2 | 0.9  | 3 |

**形态 2 · 上撩（下 → 上）**

| 左    | 上   | 前   |
| ---- | --- | --- |
| 0.9  | 0.2 | 2.5 |
| 0.6  | 0.6 | 2.8 |
| 0.3  | 1.0 | 3   |
| 0    | 1.5 | 3.2 |
| -0.3 | 2.0 | 3   |
| -0.6 | 2.4 | 2.8 |
| -0.9 | 2.8 | 2.5 |

**形态 3 · 下劈（上 → 下）**

| 左    | 上   | 前   |
| ---- | --- | --- |
| 0.9  | 3.0 | 2.5 |
| 0.6  | 2.6 | 2.8 |
| 0.3  | 2.2 | 3   |
| 0    | 1.8 | 3.2 |
| -0.3 | 1.3 | 3   |
| -0.6 | 0.9 | 2.8 |
| -0.9 | 0.5 | 2.5 |

**形态 4 · 回旋（环斩，半径 1.5）**

| 左    | 上   | 前    |
| ---- | --- | ---- |
| 0    | 1.2 | 1.5  |
| 1.1  | 1.2 | 1.1  |
| 1.5  | 1.2 | 0    |
| 1.1  | 1.2 | -1.1 |
| 0    | 1.2 | -1.5 |
| -1.1 | 1.2 | -1.1 |
| -1.5 | 1.2 | 0    |
| -1.1 | 1.2 | 1.1  |

### 47.3 设计规律

- **上撩和下劈是镜像**（`上` 值互换）
- **横斩和回旋是同一族**（水平面），回旋半径固定
- 每个形态 7–8 个点，点间距 0.3–0.4 格，视觉上刚好连成线
- `前` 值在 2.5–3.2 之间，说明刀光在**身前 3 格**处

### 47.4 伤害结算

```
execute as @a[scores={atk_cd=8,combo=1}] at @s run damage @e[r=3.5,type=!item,type=!player] 3 entity_attack entity @s
```

四段伤害 `3 / 3 / 4 / 7`，第四段是收尾重击。

❗ `damage` 必须放在段的**最后**。范围里没敌人就失败，被吃的只有它自己。

---

## 48. 连招状态机

### 48.1 三个分数

```
combo     1..4     当前段数
combo_t   0..12    窗口剩余刻数
atk_cd    0..8     攻击间隔
```

### 48.2 出手判定

```
# 有敌人 + 冷却到 0 → 进入攻击
execute as @a[scores={blade=1,atk_cd=0}] at @s if entity @e[r=3.2,type=!item,type=!player] run scoreboard players set @s atk_cd 8
```

### 48.3 段数推进

```
# 出手那一帧（atk_cd=8）
execute as @a[scores={atk_cd=8}] run scoreboard players operation @s slash = @s combo
execute as @a[scores={atk_cd=8}] run scoreboard players set @s slash_t 4
execute as @a[scores={atk_cd=8}] run scoreboard players add @s combo 1
execute as @a[scores={atk_cd=8,combo=5..}] run scoreboard players set @s combo 1
execute as @a[scores={atk_cd=8}] run scoreboard players set @s combo_t 12
```

### 48.4 窗口过期清零（用乘法，不用条件）

```
scoreboard players operation @a combo_alive = @a combo_t
scoreboard players operation @a combo_alive < one sys     ← min(combo_t, 1) → 0 或 1
scoreboard players operation @a combo *= @a combo_alive
```

窗口过期 `combo_t=0` → `combo_alive=0` → `combo *= 0` → 归零。  
**三条纯算术，零失败风险。**

### 48.5 三个必踩的坑

❗ **`atk_cd` 递减必须在攻击结算之后**。  
放前面的话 `atk_cd=8` 永远匹配不到，攻击不结算。

❗ **连招清零要加 `unless score @s atk_cd matches 8`**。  
否则出手那一帧先清零再加一，永远停在第一段。

❗ **`combo=5..` 要回卷到 1**，且判断放在 `combo += 1` 之后。

---

## 49. 能量与技能

### 49.1 能量

```
energy    0..100    当前能量
energy_t  0..20     条状图格数 = energy / 5
```

```
# 每刀 +8
execute as @a[scores={atk_cd=8}] run scoreboard players add @s energy 8
# 封顶
scoreboard players operation @a energy < hundred sys
# 换算格数
execute as @a run scoreboard players operation @s energy_t = @s energy
execute as @a run scoreboard players operation @s energy_t /= five sys
```

### 49.2 三个技能（实测配置）

| id | 主手物品               | 耗能  | 冷却  | 伤害 | 范围 | 粒子                       | 音效                     |
| -- | ------------------ | --- | --- | -- | -- | ------------------------ | ---------------------- |
| 1  | `blaze_rod` 烈焰棒    | 40  | 40  | 14 | 5  | `huge_explosion_emitter` | `random.explode`       |
| 2  | `feather` 羽毛       | 60  | 60  | 6  | 4  | `endrod`                 | `mob.enderdragon.flap` |
| 3  | `nether_star` 下界之星 | 100 | 100 | 30 | 8  | `sonic_explosion`        | `random.totem`         |

### 49.3 三条件锁（防误触发）

```
execute as @a[hasitem={item=blaze_rod,location=slot.weapon.mainhand},scores={energy=40..,burst_cd=0}] run scoreboard players set @s skill 1
execute as @a[hasitem={item=blaze_rod,location=slot.weapon.mainhand},scores={energy=40..,burst_cd=0}] run scoreboard players set @s burst_cd 40
```

三个条件：**主手物品 + 能量够 + 冷却到 0**。

❗ 冷却 `burst_cd` 在这里同时充当"已触发"的标记——  
设成 40 之后，同刻后续命令的 `burst_cd=0` 就不再成立，天然防重复。

### 49.4 技能释放顺序

```
1. 粒子
2. 音效
3. 扣能量        ← 必须在伤害之前
4. damage        ← 最后
```

❗ **扣能量必须在伤害之前**。`damage` 失败（范围内没敌人）不能白嫖技能。

---

## 50. 弹药与换弹

### 50.1 倒计时

```
ammo      当前弹药
reload    换弹剩余刻数（0 = 不在换弹）
```

```
# 开火
execute as @a[scores={ammo=1..,reload=0}] run scoreboard players remove @s ammo 1
# 打空自动换弹
execute as @a[scores={ammo=0,reload=0}] run scoreboard players set @s reload 40
# 换弹倒计时
scoreboard players remove @a[scores={reload=1..}] reload 1
# 换弹完成
execute as @a[scores={reload=1}] run scoreboard players set @s ammo 30
```

### 50.2 为什么判 `=1` 而不是 `=0`

`reload` 递减到 0 时，`reload=1` 这一帧是**最后一次**。  
判 `=1` 保证"刚归零"的那一帧补弹，判 `=0` 会和"没在换弹"混淆。

### 50.3 换弹进度条

```
reload_t = reload / 2      ← 40 刻 → 20 格
```

然后 20 格条从右往左填充。

---

## 51. 鱼竿枪

> ⚠️ **本章是 v1 版（偏移式）**：`xp_orb` 当"会飞的弹丸"，每刻 `tp` 推进，横向偏移靠
> `^0.03^0^0.9` 每刻累加做散射。**能用，但和原文的真实机制不同。**
> 原文那套（球被 `tp ~~500~` 顶到高空、之后不动、散射靠旋转 yaw/pitch）见**第 99 章**。
> 两套别混用：本章的球会飞，第 99 章的球不飞。

一套完整实现见 `scripts/build_fishrod.py` + `selfcheck_fishrod.py`（20 项自检）。  
下面是从那套实现里提炼的六个要点。

### 51.1 扳机：抛竿，然后立刻收竿

```
# 检测到钩子 = 按下扳机
execute as @a[scores={gun=1,fire_cd=0}] at @s if entity @e[type=fishing_hook,r=6] run scoreboard players set @s firing 1
# 冷却顶到射速
execute as @a[scores={firing=1}] run scoreboard players operation @s fire_cd = @s fire_rate
# 收竿：钩子一没，鱼竿马上能再抛
execute as @a[scores={firing=1}] at @s run kill @e[type=fishing_hook,r=8]
```

`kill` 掉浮漂是**能连发的前提**。不 kill 的话鱼竿处于"已抛出"状态，  
再右键只会收线，打不出第二发。玩家也看不到鱼线和浮漂，视觉上就是纯开枪  
（俗称"伪无鱼竿枪"）。

检测半径 6、收竿半径 8 要略大于钩子生成后的偏移——钩子不是生在玩家原点，  
而是沿视线飞出几格。

### 51.2 弹丸用经验球，不要用钩子本身

钩子有真实物理（重力 + 水流 + 卡方块），当弹丸会飘。**用 `xp_orb`**：  
无重力、可 `tp`、能挂计分板。

```
execute as @a[scores={firing=1}] at @s anchored eyes run summon xp_orb ^ ^ ^1.2
```

### 51.3 朝向继承：两步 tp，顺序不能反

经验球渲染上没朝向，但 `^` 局部坐标**会读它的 Rotation**。所以：

```
# 第一步：挪到玩家位置，同时吃掉玩家的 yRot/pitch
execute as @a[scores={firing=1}] at @s run tp @e[type=xp_orb,r=1.4] ~~~ ~ ~
# 第二步：沿刚灌进去的朝向挪到眼前
execute as @a[scores={firing=1}] at @s anchored eyes run tp @e[type=xp_orb,r=1.4] ^ ^ ^1.2
```

反了就不行：先挪到眼前时子弹朝向还是 0，第二步的 `~~~` 会把朝向覆盖成玩家的，  
但位置已经错了。开火后玩家转头，子弹**不跟随**——这是正确行为。

选择器必须用 `r=1.4` 就近限定，不能写全局 `@e[scores={b_new=1}]`：  
两个玩家同刻开火会互相覆盖对方的子弹参数。

### 51.4 推进与散布：定点偏移累加

```
execute as @e[type=xp_orb,scores={b_life=1..,b_sp=0}] at @s run tp @s ^0^0^0.9
execute as @e[type=xp_orb,scores={b_life=1..,b_sp=1}] at @s run tp @s ^0.03^0^0.9
execute as @e[type=xp_orb,scores={b_life=1..,b_sp=2}] at @s run tp @s ^-0.03^0^0.9
```

横向偏移**每刻累加**，30 刻后自然张成锥形——越远越散。  
比"生成时随机一个角度"真实，而且不需要三角函数。

❗ 一档只能跑一条。若先写"全体 `^^^0.9`"再写"某档 `^0.03^0^0.9`"，  
两档都命中时位移叠加，实际变成 1.8 格/刻。

### 51.5 出弹流水线：扣弹必须排最后

```
召唤 → 打标 → 继承朝向 → 灌参数 → 枪口焰/后坐力/音效 → 扣弹 → 清标记
```

`ammo=1..` 是"能不能出弹"的唯一门槛。扣弹若排在特效之前，  
最后一发的枪口焰和枪声会因为 `ammo` 已变 0 而全部消失。

清标记（`firing=0`）必须最后，否则后面的块看不到标记。

### 51.6 命中：分档伤害 + 先结算后销毁

`/damage` 只吃字面量，不吃计分板。伤害档 `b_dmg=1..4` → 4/8/14/25，一档一条：

```
execute as @e[type=xp_orb,scores={b_life=1..,b_dmg=2}] at @s if entity @e[r=0.9,<敌人过滤>] run damage @e[r=0.9,c=1,<敌人过滤>] 8 entity_attack entity @s
...
execute as @e[type=xp_orb,scores={b_life=1..}] at @s if entity @e[r=0.9,<敌人过滤>] run kill @s
```

**先结算伤害，最后 kill**。反过来会先销毁自己，`entity @s` 失效，伤害打空。

敌人过滤：`type=!player,type=!xp_orb,type=!item,type=!fishing_hook,type=!arrow,type=!boat,type=!armor_stand`

### 51.7 断链：按功能拆成 3 条链

| 链 | 闸门                                              | 管什么                     |
| - | ----------------------------------------------- | ----------------------- |
| A | `if entity @a[hasitem={item=fishing_rod,...}]`  | 兜底 / 枪型 / 配置 / 换弹 / HUD |
| B | 持枪 **且** `if entity @e[type=fishing_hook]`      | 抛竿检测 / 出弹 / 特效 / 音效     |
| C | `if entity @e[type=xp_orb,scores={b_life=1..}]` | 弹道推进 / 命中 / 销毁          |

不持枪、没抛竿、场上没子弹 → 每刻只有 3 条闸门在跑。  
实测 209 块 / 3 条常驻 = 1.4%。

每条链都套 8.0.1 的骨架（检测无条件 → 连接块**有条件** → 重置块 → 业务全部无条件）。

**链的顺序有意义**：A 算出的 `fire_cd` / `gtype` 给 B 用，B 生成的子弹给 C 推进。  
按 z 从小到大排就是执行顺序。

**为什么开火要单独一条链**：抛竿是个瞬时事件，和"持枪"这个持续状态不同频。  
放在同一条链里，要么每刻都白跑一遍开火检测（浪费），  
要么得用条件块把后半个链锁住（一条失败后面全死）。

**HUD 要画两次**：链 A 在扣弹之前画一次（不持枪/不开火时靠它），  
链 B 扣弹之后再画一次覆盖掉——否则弹匣条会比数字慢一帧。

---

---

## 84. 枪械：五条完全不同的路

五份枪械模板的**触发方式完全不同**，这是最关键的区别。抄之前先选路：

| 版本 | 扳机 | 子弹实体 | 射速控制 | 适合 |
|---|---|---|---|---|
| 鱼竿枪 1145 | `fishing_hook` 出现 | **船** `boat` | `连射` 计数递减 | 老图 / 想要船的下落弹道 |
| 枪械 3.0 | `fishing_hook` + `r=2` 内持竿 | 船 / 雪球 | `射击` 归零才可射 | 中型图 |
| 枪械 4.0 | **抬头 `rx=-88`** | 船 | `时刻a` 累计到 100 | 不想让钩子飞出去 |
| 枪械优化版 2.0 | 钩子 + `射速=0` | 船 | `射速` 每刻 `remove N` | 4 种枪 / 全自动 |
| **伪无鱼竿枪** | 钩子出现 → **立刻 `kill`** | `xp_orb`（**不飞，只当载体**） | `间隔` 递减 | **最像真枪，40 种枪 / 免伤 / 归属**（见第 99 章） |

> **伪无鱼竿枪是第五条路，也是最完整的一条**：钩子当扳机立刻杀掉（看不到浮漂），
> `xp_orb` 只承载朝向和散射偏移，弹道靠 `positioned ^^^N` 射线扫描，命中走 `damage 0 override`。
> **别把它和上面四条混着抄**——它的散射是"旋转角度"，不是"位移偏移"。

### 84.1 鱼竿枪 1145：船当子弹（原文）

这是最早也最省实体的做法。**钩子只是扳机，子弹是船。**

```
# 钩子出现 = 有人抛竿 → 给身边持竿的玩家打「开火」
execute as @e[type=fishing_hook] at @s run tag @p[hasitem={item=fishing_rod,location=slot.weapon.mainhand},scores={换弹时间=0,子弹=1..,连射=0,射击间隔=0},r=2,c=1] add 开火

# 连发次数：子弹不够就打完为止
execute as @e[tag=开火,scores={连射=0}] at @s if score @s 子弹 < @s 设置连射 run scoreboard players operation @s 连射 = @s 子弹
execute as @e[tag=开火,scores={连射=0}] at @s if score @s 子弹 >= @s 设置连射 run scoreboard players operation @s 连射 = @s 设置连射
```

把玩家身上的参数**灌进附近的船**，然后船丢到高空当弹丸：

```
execute as @e[scores={连射=1..}] at @s run scoreboard players operation @e[r=2,type=boat] 水平散射 = @s 水平散射
execute as @e[scores={连射=1..}] at @s run scoreboard players operation @e[r=2,type=boat] 伤害 = @s 伤害
execute as @e[scores={连射=1..}] at @s run scoreboard players operation @e[r=2,type=boat] 攻击者 = @s 号码
execute as @e[scores={连射=1..}] at @s run tp @e[r=2,type=boat] ~~1000~
scoreboard players remove @e[scores={连射=1..}] 子弹 1
scoreboard players remove @e[scores={连射=1..}] 连射 1
```

**为什么是船**：船有 `攻击者` 这个概念（被谁推的），能白嫖一个归属字段；
船的碰撞箱大，判定好写；船落到地上不会消失，好清场。
**代价**：船会留在世界里，必须配 `kill @e[type=boat]` 的清场链，否则越打越卡。

**归属用 `号码`**：每个玩家分配一个 `号码` 分数当 uid，子弹身上抄一份 `攻击者`，
命中时比 `攻击者 == 号码` 就知道是谁打的。

### 84.2 枪械 3.0：钩子 + 距离 + 弹夹（原文）

```
# 钩子落地 → 给 r=2 内持竿玩家打「射击」标记（一次抛竿只算一发）
execute @e[type=minecraft:fishing_hook] ~~~ tag @a[scores={弹夹=1..,射击a=0},r=2,hasitem={item=fishing_rod,location=slot.weapon.mainhand}] add 射击
execute @e[type=minecraft:fishing_hook] ~~~ tag @a[scores={弹夹=1..,射击a=0},r=2,hasitem={item=fishing_rod,location=slot.weapon.mainhand}] add 射击a
execute @e[type=minecraft:fishing_hook] ~~~ scoreboard players add @a[scores={弹夹=1..,射击a=0},r=2,hasitem={item=fishing_rod,location=slot.weapon.mainhand}] 射击a 1
```

`射击a` 是**防重入**：钩子存在期间每刻都会命中 `r=2`，靠 `射击a=0` 保证只打一次。
抛竿结束 `射击a` 清零，下一竿才能再打。

**弹夹按枪型分开存**：`弹夹a` / `弹夹b` / `弹夹c` / `弹夹d`，
每把枪一个计分项，`qx种类` 决定看哪一个。

### 84.3 枪械优化版 2.0：射速分数递减（原文）

**这是四份里最干净的射速写法。**

```
# 每刻按枪型扣射速（数字 = 每刻扣多少，越大越快）
scoreboard players remove @a[scores={qx种类=1,射速=1..}] 射速 5
scoreboard players remove @a[scores={qx种类=2,射速=1..}] 射速 10
scoreboard players remove @a[scores={qx种类=3,射速=1..}] 射速 2
scoreboard players remove @a[scores={qx种类=4,射速=1..}] 射速 20

# 射速归零才允许开火
execute @e[type=minecraft:fishing_hook] ~~~ tag @a[scores={弹夹=1..,射速=0},r=2,hasitem={item=fishing_rod,location=slot.weapon.mainhand}] add 射击

# 开火瞬间把射速顶到 100
scoreboard players add @a[scores={弹夹=1..,射速=0},tag=射击,tag=射击a] 射速 100
```

换算：射速顶到 100 后每刻扣 N，`100/N` 刻打一发。

| 枪型 | 每刻扣 | 间隔 | 折合 |
|---|---|---|---|
| 1 | 5 | 20 刻 | 1 秒 1 发 |
| 2 | 10 | 10 刻 | 0.5 秒 1 发 |
| 3 | 2 | 50 刻 | 2.5 秒 1 发 |
| 4 | 20 | 5 刻 | 0.25 秒 1 发 |

**为什么比"冷却倒计时"好**：只有一个数字，不用 `if 冷却==0` 再 `set 冷却 N`，
扣到 0 自动恢复；改枪型只改 `remove` 的 N，不动别处。

**全自动**：`自动=1` 的枪，钩子不在也给标记，靠 `射速=0` 自己续火。

### 84.4 枪械 4.0：抬头触发（原文）

不想让钩子飞出去（很多地图禁了钩子），就用**抬头**当扳机：

```
# 抬头超过 88 度（rx=-88 = 视角朝上）开始累计
execute as @a[hasitem={item=fishing_rod,location=slot.weapon.mainhand},rx=-88] at @s unless entity @s[scores={时刻a=100..,列表=0..}] run scoreboard players add @s 时刻a 1
# 低头立刻清零
scoreboard players reset @a[hasitem={item=fishing_rod,location=slot.weapon.mainhand},rxm=-88,scores={时刻a=0..}] 时刻a
# 累计到 100 = 扣扳机
scoreboard players add @a[hasitem={item=fishing_rod,location=slot.weapon.mainhand},rx=-88,scores={时刻a=100}] 列表 0
scoreboard players reset @a[hasitem={item=fishing_rod,location=slot.weapon.mainhand},rx=-88,scores={时刻a=100}] 时刻a
```

`rx=-88` 是"抬头到 88 度"，`rxm=-88` 是"抬头不超过 88 度"。两个正好互补。
`时刻a` 累计 100 刻 = 5 秒，也就是"举枪 5 秒才能打第一发"——
这个数改成 5 就是"举枪 0.25 秒就能打"，看你要多硬核。

### 84.5 换弹：101 倒计时（三份原文通用）

```
# 开始：设 101（不是 100，因为下面每刻扣 1，到 2 时补弹、到 1 时扣子弹）
scoreboard players set @a[scores={qx种类=1,弹夹a=!12..,换弹=0},hasitem={item=netherite_ingot,quantity=1..,location=slot.weapon.mainhand}] 换弹 101

# 每刻扣 1
scoreboard players remove @a[scores={换弹=1..},hasitem={item=netherite_ingot,quantity=1..,location=slot.weapon.mainhand}] 换弹 1

# 到 2：补满弹夹 + 换弹音效
scoreboard players set @a[scores={换弹=2,qx种类=1},hasitem={item=netherite_ingot,quantity=1..,location=slot.weapon.mainhand}] 弹夹a 12
execute @a[scores={换弹=2},hasitem={item=netherite_ingot,quantity=1..,location=slot.weapon.mainhand}] ~~~ playsound armor.equip_gold @a[r=10] ~ ~ ~

# 到 1：消耗一颗子弹物品
clear @a[scores={换弹=1},hasitem={item=netherite_ingot,quantity=1..,location=slot.weapon.mainhand}] netherite_ingot 0 1

# 到 0：结束
scoreboard players set @a[scores={换弹=1}] 换弹 0
scoreboard players add @a 换弹 0
```

**为什么是 101 而不是 100**：`换弹=2` 和 `换弹=1` 是两个不同的动作（补弹 / 扣物品），
要在同一条倒计时里各占一格。101 刻 ≈ 5 秒，改这个数就是改换弹时间。

**`弹夹a=!12..`**：`!` 是"不匹配"，`!12..` = "不等于 12 及以上" = "没满"。
只在没满时才允许换弹，满了按不出来。

### 84.6 33 种枪声：随机 + 逐值查表（原文）

```
scoreboard players random @e[scores={射击间隔=1..}] 音响 1 33

execute as @e[scores={音效=1..},tag=开火] at @s run playsound crossbow.shoot @a[r=30] ~~~
execute as @e[scores={音效=2},tag=开火] at @s run playsound item.trident.hit @a[r=30] ~~~ 1 1.5
execute as @e[scores={音效=3},tag=开火] at @s run playsound block.stonecutter.use @a[r=30] ~~~ 1 5
...
execute as @e[scores={音效=33},tag=开火] at @s run playsound random.break @a ~~~ 100 1.7
```

**这是"一个分数当枚举"的最朴素实现**：33 个值 → 33 条条件命令。
比 `%%N` 查表法笨，但**能带不同的音高和音量**（`%%N` 只能换文本）。

**`100` 是 minVolume**：`playsound <音效> <目标> <坐标> <音量> <音高> <minVolume>`。
写 100 = 多远都能听见（第 57 章）。

### 84.7 散射：分数当微角度（原文）

```
scoreboard players random @e[hasitem={item=fishing_rod}] 水平散射 -1260 1260
scoreboard players random @e[hasitem={item=fishing_rod}] 垂直散射 -1888 1888

# 抗偏移：枪越好，散得越小
execute as @e[hasitem={item=fishing_rod}] at @s run scoreboard players operation @s 水平散射 /= @s 抗偏移
execute as @e[hasitem={item=fishing_rod}] at @s run scoreboard players operation @s 垂直散射 /= @s 抗偏移

# 每 64 点转 6.4 度，逐段累加
execute as @e[scores={垂直散射=64..},type=boat] at @s run tp @s ~~~~~6.4
execute as @e[scores={垂直散射=64..},type=boat] at @s run scoreboard players remove @s 垂直散射 64
```

**核心思想**：`tp` 的角度只吃小数度，不能直接加 0.01。
所以把角度**放大成整数**（±1260 / ±1888），再以 64 为一档、每档转 6.4 度，
用 `scoreboard remove 64` 循环扣到 0。**这就是"分数当浮点"**（第 26 章二分法的同源思路）。

`抗偏移` 是枪的精度属性：`/= 抗偏移` 让好枪的随机数变小 → 散得小。

### 84.8 弹药溢出回灌（`换弹部分666.txt`）

```
# 打的时候可能一枪扣多发，超过弹夹容量就溢出
execute as @a[scores={枪械编号=1..,zd=1..}] if score @s zd > @s 弹匣容量 run tag @s add 子弹溢出

# 溢出量先存备份
execute as @a[tag=子弹溢出] run scoreboard players operation @s zd备份2 = @s zd
# 弹夹顶到容量
execute as @a[tag=子弹溢出] run scoreboard players operation @s zd = @s 弹匣容量
# 备份减容量 = 真正溢出的量
execute as @a[tag=子弹溢出] run scoreboard players operation @s zd备份2 -= @s 弹匣容量
```

换弹完成后把 `zd备份2` 加回 `zd`，多出来的子弹不会凭空消失。
**霰弹枪 / 连发枪必须做这个**，否则打一枪弹夹变负数。

---

## 85. 伪无子弹：不用实体，逐格算

"伪无"= **不用会飞的子弹实体**，把射程存成分数，一格一格往前测。

> **本章讲"递减式"（射程每刻 -1，子弹自然衰减）；
> 第 99 章讲"截断式"（一次扫完，被墙截断）——原文两套都有，按需选一套，不要混用。**
> `xp_orb` 在两套里都只是**载体**（存朝向和散射），不是子弹本身。

### 85.1 射程备份递减（原文骨架）

```
# 开火时给玩家一个射程
scoreboard players set @s 射程备份 60

# 每刻扣 1，扣到 0 子弹消失
execute as @e[tag=子弹,scores={射程备份=61..}] run scoreboard players set @s 射程备份 60
```

`射程备份` 同时是**剩余射程**和**飞行进度**——`positioned ^^^N` 的 N 就是它。
一个数字干两件事，这是伪无体系最省的地方。

### 85.2 `positioned ^^^N` 逐格摆点（原文）

```
execute as @e[tag=子弹,scores={射程备份=1..}] at @s positioned ^^^1 run particle minecraft:endrod ~~-498.5~
execute as @e[tag=子弹,scores={射程备份=2..}] at @s positioned ^^^2 run particle minecraft:endrod ~~-498.5~
execute as @e[tag=子弹,scores={射程备份=3..}] at @s positioned ^^^3 run particle minecraft:endrod ~~-498.5~
...
execute as @e[tag=子弹,scores={射程备份=60..}] at @s positioned ^^^60 run particle minecraft:endrod ~~-498.5~
```

**60 条命令画一条 60 格的弹道**。每一条都是"如果射程还有这么远，就在第 N 格画个点"。

**代价**：60 格 = 60 个命令方块。这是伪无体系的天花板——
射程想加到 120 就得 120 个方块。所以实际地图射程都在 30–60。

**为什么用 `positioned ^^^N` 而不是每刻 `tp` 一格**：
- `tp` 会改实体位置，实体要一直存在（还是要实体）
- `positioned` 只在计算时偏移，实体可以停在原地不动
- 一次算完 60 格，不依赖 tick 顺序

### 85.3 三段高度判定：头 / 胸 / 腿（原文）

```
execute as @e[tag=子弹,tag=!命中,scores={射程备份=1..}] at @s positioned ^^^1 positioned ~~-500.5~ at @e[r=0.5,c=1,type=!item,type=!fishing_hook,type=!boat,type=!xp_orb,type=!snowball,type=!xp_bottle,type=!fox] unless score @e[c=1] 队伍uid = @s 队伍uid run scoreboard players set @s 判定 1

tag @e[tag=子弹,scores={判定=1}] add 命中

execute as @e[tag=子弹,tag=!命中,scores={射程备份=1..}] at @s positioned ^^^1 positioned ~~-499.5~ at @e[r=0.5,c=1,...] ... run scoreboard players set @s 判定 2

execute as @e[tag=子弹,tag=!命中,scores={射程备份=1..}] at @s positioned ^^^1 positioned ~~-499~ at @e[r=0.5,c=1,...] ... run scoreboard players set @s 判定 3
```

**读法**：三段只差 `~~-500.5~` / `~~-499.5~` / `~~-499~` 这个**垂直基准**，
相对差 0.5 / 1.5 / 2.0 —— 就是腿 / 胸 / 头的高度差。

**`-500` 不是随便选的常量**：球出生后被 `tp ~~500~` 顶到 **y+500**（垂直推高，躲开视野和碰撞），
所有坐标计算都要用 `y-500` 系列减回来。`~~-498.5~` 减 498.5 → 净 +1.5（头顶），
`~~-500.5~` 减 500.5 → 净 -0.5（腿）。**改球的高度就必须同步改这一整组数字。**

**三段合起来才是完整判定**，顺序不能换：先测头（最高），测到就 `add 命中`，
后两段靠 `tag=!命中` 跳过。这样一发子弹只结算一次。

**`type=!...` 那一长串是黑名单**：把物品、鱼竿钩、船、经验球、雪球、喷溅药水、狐狸全排掉，
否则子弹会"命中"自己刚丢出去的粒子载体。

### 85.4 命中结算：`damage 0 override`（原文）

```
execute as @e[tag=子弹,scores={判定=1}] at @s at @e[scores={攻击uid=1..}] if score @e[c=1] 攻击uid = @s uid run scoreboard players operation @e[c=1] headhp -= @s 伤害
...
# 三段都扣完，交给引擎判定死亡
execute as @e[tag=子弹,scores={判定=1..}] at @s at @e[scores={攻击uid=1..}] if score @e[c=1] 攻击uid = @s uid run damage @e[c=1] 0 override
```

**`damage 0 override`** 是整套体系的关键：伤害自己算（`headhp -= 伤害`），
但**死亡必须让引擎判**——否则玩家血扣到 0 还活着。
`damage 0` 打 0 点伤害，只为了让引擎检查一次"该不该死"。

---

## 86. 归属、死亡与盒子

### 86.1 攻击 uid 归属（原文）

```
# 子弹身上记一份「攻击者 uid」
execute as @e[tag=子弹,...] run scoreboard players operation @e[r=0.5,c=1,...] 攻击uid = @s uid

# 命中时比 uid，不是自己人
... unless score @e[c=1] 队伍uid = @s 队伍uid run ...
```

**uid 三件套**：`uid`（我是谁）/ `攻击uid`（谁打我）/ `队伍uid`（我们是不是一伙）。
三个都是计分项，不用 tag —— 因为 tag 没法比大小、没法相减。

### 86.2 三段血 + die 标记（`肢体部分.txt`）

```
tag @e[scores={headhp=..0}] add die
tag @e[scores={chesthp=..0}] add die
testfor @e[tag=die]

# 死亡表现
execute as @a[tag=die] run playsound block.end_portal.spawn @s ~~~ 1 1.25
execute at @a run playsound mob.skeleton.death @p ~~~ 17024 1.25 17024

# 复位（必须放在表现之后）
execute as @e[tag=die] run scoreboard players operation @s headhp = @s headhpmax
execute as @e[tag=die] run scoreboard players operation @s chesthp = @s chesthpmax
```

**顺序铁律**：判定 → 表现 → 复位。复位放前面，玩家永远看不到死亡效果。

### 86.3 死亡检测四行法（`死亡检测.txt`，全文 584 字）

```
tag @e[type=player] remove 活着
tag @a[tag=死亡,tag=!活着] add 活着
tag @a add 死亡
tag @e[type=player] remove 死亡
```

**读法**（每刻跑）：
1. 先假设"没人活着"
2. 上一刻活着、这一刻还在的 → 重新打 `活着`
3. 所有人先打 `死亡`
4. 活着的人去掉 `死亡`

跑完的结果：**`tag=死亡` 且没有 `活着` = 这一秒刚死的人**。
不用血条、不用 `health`、不用 `damage`，纯 tag 差分。**这是全库最省的一条技巧。**

### 86.4 死亡盒子（`死亡盒子系统1.0`）

```
execute as @a[scores={死亡数据=1}] at @s run summon minecraft:chest_minecart ~ ~ ~
execute as @a[scores={死亡数据=1}] at @s run tag @e[type=minecraft:chest_minecart,r=1] add 盒子
execute as @a[scores={死亡数据=1}] at @s run summon hopper_minecart ~ -66 ~
```

箱子矿车装掉落物、漏斗矿车在下面接。用矿车不用箱子方块，因为**矿车能被 `tp` 搬走**，
清场时 `kill @e[type=chest_minecart]` 一条就够。

---

---

## 102. 伪无判定 / 伪无粒子：同一条射线的两种表现

> 出处：`refs/伪无判定.txt`（467 行）、`refs/伪无粒子 - 副本.txt`（134 行）。

**判定和粒子共用同一套 `射程备份` 循环**，只是最后一条命令不同：

```
# 判定：在 N 格处看有没有实心方块 → 截断射程
... positioned ^^^N unless block ^^^ air ... run scoreboard players set @s 射程备份 N

# 粒子：在 N 格处摆一个点 → 画出弹道
... positioned ^^^N run particle minecraft:basic_flame_particle ~~-498.5~
```

所以**粒子和判定天然一致**——不会出现"打中了但没特效"或"有特效但没伤害"。

### 102.1 穿透白名单（原文 40 项，全表）

```
air  scaffolding  ladder  large_fern  yellow_flower  double_plant  red_flower
iron_bars  rail  sapling  torch  redstone_torch  soul_torch  water  lava
tripwire_hook  carpet  lever  spruce_button  wooden_button  stone_button
bamboo_button  crimson_button  dark_oak_button  warped_button  web  trapdoor
wall_banner  unpowered_repeater  unpowered_comparator  redstone_wire
standing_banner  wooden_door  iron_door  spruce_door  dark_oak_door  chain
```

**这是一份"子弹能穿过去"的方块表**。想加"玻璃能打穿"，往表里加 `glass`；
想加"水能挡子弹"，把 `water` 删掉。

### 102.2 每档 N 一行，不许循环

原文 `射程=10` 就有 10 行判定 + 10 行粒子。**Bedrock 没有循环**，
`射程` 加大就要加行——这是这套做法的天花板：**射程 20 就是 40 行**。

优化方向：射程用二分（512/256/…）一次跳到位，只在命中点附近逐格细扫。

---

# 术语表

全文用词固定，避免同义混用：

| 词          | 含义                                                           | 不是什么               |
| ---------- | ------------------------------------------------------------ | ------------------ |
| **链**      | 一串首尾相接的命令方块                                                  | 不是"命令列表"           |
| **链首**     | 链的第一个方块，循环块或脉冲块                                              | 不叫"头块"             |
| **功能链**    | 一条链只干一件事，配一个循环检测块                                             | 不是"一条大链里的几段"       |
| **检测块**    | 链首那个**循环块**，跑 `execute if entity <选择器>`，是链上唯一的无条件块                  | 不叫"闸门"，也不带 `run` |
| **条件位**    | 方块实体的 `conditionalMode`。`1` = 前一块成功才跑；**全链只有连接块用它** | 不叫"条件块开关" |
| **连接块**    | 链的**第 2 格**（检测之后），`conditionalMode=1`，跑 `setblock ~1 ~ ~ chain_command_block["facing_direction"=5]` 把重置块接回运行方向 | 不是"检测块"，也不是重置块 |
| **重置块**    | 链的**第 3 格**（连接之后），`conditionalMode=0`，跑 `setblock ~ ~ ~ chain_command_block["facing_direction"=4]` 把自己摆朝后 | **不许放链尾**（会随业务长度漂移） |
| **常驻链**    | 没有检测、没有连接、没有重置，循环块直接装第一条业务，链自己绕回来（原 `execute if entity @a` 的链） | 不是"没写完的链" |
| **空闲条数**   | 空闲时每刻仍在执行的条数 = **检测块个数**（= 功能链数）                             | 不是"方块总数"           |
| **通道**     | 一个"玩家做了什么"的检测（持某物品 / 看某方向 / 在菜单里）                            | 不是"分支"             |
| **定时器**    | `#tick += 1` + `matches 20..` 这一对                            | 不叫"计数器"（计数器只是它的一半） |
| **静默**     | 只关**聊天栏灰字**；方块控制台照样记（`TrackOutput=1`）                        | 不是"关掉日志"           |
| **断链**     | 让链条在不需要时停止执行                                                 | 不是"删掉命令"           |
| **断链（唯一）** | 检测失败 → 连接块（条件）跳过 → 重置块不被触发 → 业务一条都不跑；断开由外部同类型 `setblock` 把**连接块**改朝向完成 | 不是"所有块都加条件位"（会连坐） |
| **朝向快照**   | 命令方块执行完自己的命令后，沿它**进入执行时**的朝向找下一格；重置块改自己朝向只影响下一刻 | 不是"改完立刻生效" |
| **自动位**    | 方块实体的 `auto`（Byte）。`auto=0` 的循环块不自己跑，等红石                     | 不是"关掉了"            |
| **哨兵**     | 一个藏起来的实体，用它存在与否表示"初始化过了"                                     | 不是"标记方块"           |
| **查表法**    | 累加区间选择器 + `%%(N+1)`，靠失败组件被剔除、索引前移来取值                         | 不是"多写几个 `%%N`"     |
| **方块变量**   | 用某格方块类型当状态，`if block` 读                                      | 不是"存档位"            |
| **常加载区**   | `tickingarea`，让远处的指令区照常执行                                    | 不是"区块加载器"          |
| **锚点**     | 定点盔甲架，配合 `rotated as` + `^` 摆特效点                             | 不是"坐标原点"           |
| **渐进加载**   | `structure load … layer_by_layer/block_by_block <秒>`，拿来做建造动画 | 不是"卡了"             |

**标注约定**：

- ❗ = **会静默失败**的坑（不报错，只是不生效）
- ✅ / ❌ = 正确 / 错误写法对照
- 所有"降 X%""N 条""M 个方块"都是**实测值**，不是估算

---

# 维护约定

1. **单一来源**：本文件是唯一文档，不再有分册、不再有 `references/`
2. **数字必须实测**：生成器打印链数，别估算；报百分比说清分母
3. **新增章节要登记**：更新本文件「目录」+ 第 81 章索引（第十一部分的章节登记在 97 章）
4. **实战手法先验证再写**：第 64–78 章每条都标了出处；新学到的手法先用 `scripts/dump_cbworld.py` 核实，再落笔
5. **踩坑与要求必落账**：用户实测反馈、口头要求、线上报错，**当场**写进「附录 Z」，
   不许只留在对话里。台账按日期追加、永不删除——删掉就等于允许重犯。

---

# 附录 Z · 用户要求与踩坑台账

> 两类东西：**用户明确提过的要求**（必须遵守）、**实测踩过的坑**（必须避开）。
> 按日期追加，永不删除。每次接到用户反馈，**先登记，再改代码 / 改文档**。
