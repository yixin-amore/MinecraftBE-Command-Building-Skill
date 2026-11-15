# FMBE：狐狸投影（世界内 3D 表现）

> 本文件是 `mct` skill 的参考资料，主文件是 `../SKILL.md`。
> **章号没变**（拆家前是第几章现在还是第几章）；跨文件的章号去主文件的
> 「章号 → 文件 对照表」查。这里的结论可能早于主文件的「⭐ 当前基线」——
> **冲突时以基线为准**。

> ⚠️ **本文件是外部来源，未在本 skill 的产物里实测过。**
> 来源：B 站 FMBE 系列教程（「纯指令展示方块 · 狐狸投影」）。
> 命令照抄可用，但**系数有版本依赖**，进游戏前先按下面「版本核对」跑一遍。

> **什么时候读我**：要做**世界内的 3D 表现**（悬浮方块、缩放模型、世界内 HUD、
> 商品展示、标记点）时。纯文字 UI 用 `05-ui.md` 的 `titleraw`，那个更便宜。

---

> 🔁 **本文件是"照抄教程"的基础版；本 skill 有实测版，见主文件第十一章。**
> 实测版补了这些（本文件没有）：变量每刻重写、按组共享渲染命令、
> 倾斜轨道（`v.xrot` 当倾角）、`basepos` 固定 + `v.yrot` 公转、
> 虚空清理、粒子绘阵、120 秒演出分工。
>
> ❗ **冲突点**：本文件用 `tag @e[type=fox] add wiki:fmbe` 选目标，
> 与「全库零 tag」（U38/U40）冲突。实测请改成计分打标：
> `scoreboard players set @e[type=fox,r=2,c=1] fmbe_gem 1`，选择器写 `@e[scores={fmbe_gem=1..}]`。


## 一句话原理

**给一只隐身狐狸手里塞个方块，再用 `playanimation` 篡改它的动画变量，
让这个方块可以任意平移 / 旋转 / 缩放。**

狐狸只是「托架」，真正被展示的是它**主手那个方块**。玩家看到的是悬浮的方块，
看不到狐狸（隐身 + 无敌 + 静音）。

**为什么这招成立**：`playanimation` 允许把**任意生物动画的关键帧变量**写进目标实体。
不同动画里恰好有「缩放」「旋转」「位移」这几类变量，把它们当**万能插槽**用，
就能驱动狐狸模型部件的变换。这是基岩版独有的能力，Java 做不到。

---

## 一、准备（一次性）

```mcfunction
# ① 生成狐狸，打标
summon fox ~ ~ ~
tag @e[type=fox] add wiki:fmbe

# ② 隐身 + 无敌（否则会被打死、模型就没了）
effect @e[tag=wiki:fmbe] invisibility 999999 1 true
effect @e[tag=wiki:fmbe] resistance 999999 255 true

# ③ 静音（狐狸叫起来很吵）
stopsound @a mob.fox.spit
stopsound @a mob.fox.sniff
stopsound @a mob.fox.sleep
stopsound @a mob.fox.screech
stopsound @a mob.fox.hurt
stopsound @a mob.fox.eat
stopsound @a mob.fox.death
stopsound @a mob.fox.bite
stopsound @a mob.fox.ambient
stopsound @a mob.fox.aggro

# ④ 手里放要展示的方块（这就是玩家看到的那个）
replaceitem entity @e[tag=wiki:fmbe] slot.weapon.mainhand 0 glass

# ⑤ 每刻同步位置（狐狸会自己走）
execute as @e[tag=wiki:fmbe] at @s run tp @s ~~~
```

> **适配本 skill**：把 `tag=wiki:fmbe` 换成 `scores={tg_fx=1}`（U40 全库零 tag）。
> 生成时用 `scoreboard players set @e[type=fox,r=3,c=1] tg_fx 1` 打标。

---

## 二、前置：定义缩放与基点（3 条，只跑一次）

**新版（26.10.4+，推荐）**：

```mcfunction
playanimation @e[tag=wiki:fmbe] animation.player.sleeping none 0 "" controller.animation.fox.move

playanimation @e[tag=wiki:fmbe] animation.creeper.swelling none 0 "v.xbasepos=v.xbasepos??0;v.ybasepos=v.ybasepos??0;v.zbasepos=v.zbasepos??0;v.xpos=v.xpos??0;v.ypos=v.ypos??0;v.zpos=v.zpos??0;v.xrot=v.xrot??0;v.yrot=v.yrot??0;v.zrot=v.zrot??0;v.scale=v.scale??1;v.xzscale=v.xzscale??1;v.yscale=v.yscale??1;v.swelling_scale1=2.1385*math.sqrt(v.xzscale*v.scale);v.swelling_scale2=2.1385*math.sqrt(v.yscale*v.scale);" wiki.scale

playanimation @e[tag=wiki:fmbe] animation.ender_dragon.neck_head_movement none 0 "v.head_rotation_x=0;v.head_rotation_y=0;v.head_rotation_z=0;v.head_position_x=(v.xbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);v.head_position_y=(10.05185375+v.ybasepos*0.467625)*math.sqrt(v.yscale*v.scale);v.head_position_z=(17.108-v.zbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);" wiki.shift_pos
```

**旧版（-26.0.2）**：`swelling_scale` 用 `sqrt(xzscale)*sqrt(scale)` 分开开方，
位移系数用 `3741/8000`，Y 基数 `10.6925`，标签用 `wiki:scale` / `wiki:shift_pos`。

### 版本核对（必做）

新旧版差异只在**系数**，但错了方块就会偏。核对方法：

1. 生成狐狸，跑一次前置
2. 设 `v.xbasepos=1`，看方块实际偏移是不是 1 格
3. 偏了 → 换另一套系数

| 项目 | 旧版 | 新版（26.10.4+） |
|---|---|---|
| 缩放 | `sqrt(xz)*sqrt(scale)` | `sqrt(xz*scale)` |
| X/Z 位移系数 | `3741/8000` | `0.433875` |
| Y 位移系数 / 基数 | `3741/8000` / `10.6925` | `0.467625` / `10.05185375` |
| 标签 | `wiki:scale` `wiki:shift_pos` | `wiki.scale` `wiki.shift_pos` |

---

## 三、旋转（3 条）

```mcfunction
# X 轴（俯仰）与 Y 轴（偏航）—— 借监守者行走动画
playanimation @e[tag=wiki:fmbe] animation.warden.move none 0 "v.body_x_rot=90+v.xrot;v.body_z_rot=90+v.yrot;" wiki:xrot

# Z 轴（滚转）—— 借玩家攻击旋转动画，取负
playanimation @e[tag=wiki:fmbe] animation.player.attack.rotations none 0 "v.attack_body_rot_y=-v.zrot;" wiki:zrot
```

---

## 四、位移（3 条）

```mcfunction
# X —— 借鹦鹉移动动画的 wing_flap
playanimation @e[tag=wiki:fmbe] animation.parrot.moving none 0 "v.wing_flap=(16-v.xpos)*3.3333333;" wiki:xpos

# Y —— 借矿车移动动画的 rail_offset
playanimation @e[tag=wiki:fmbe] animation.minecart.move.v1.0 none 0 "v.rail_offset.x=0;v.rail_offset.y=1.6485+v.ypos/16;v.rail_offset.z=0;" wiki:ypos

# Z —— 借鹦鹉跳舞动画的 dance
playanimation @e[tag=wiki:fmbe] animation.parrot.dance none 0 "v.dance.x=-v.zpos;v.dance.y=0;" wiki:zpos
```

> 旧版 X 位移是 `(16-v.xpos)/0.3`，与 `*3.3333333` 等价。

---

## 五、变量表（要改哪个数，看这里）

| 变量 | 作用 | 默认 | 备注 |
|---|---|---|---|
| `v.scale` | 整体缩放 | 1 | 等比 |
| `v.xzscale` | 水平缩放 | 1 | 与 `scale` 相乘 |
| `v.yscale` | 垂直缩放 | 1 | 与 `scale` 相乘 |
| `v.xbasepos` `v.ybasepos` `v.zbasepos` | 模型基点偏移（相对出生点） | 0 | 用来把方块挪到指定坐标 |
| `v.xpos` `v.ypos` `v.zpos` | 额外位移 | 0 | 相对基点再挪 |
| `v.xrot` `v.yrot` `v.zrot` | 三轴旋转角 | 0 | 单位是度 |

**`??` 是空值合并**：`v.xpos=v.xpos??0` 意思是「没定义过就取 0」。
前置里那三条就是靠它做初始化的，**不要跳过**，否则后面的写入会拿到 `undefined`。

---

## 六、能用来做什么（本 skill 的应用场景）

| 场景 | 做法 | 代价 |
|---|---|---|
| **世界内悬浮方块**（标记点、路标、商品展示） | 一只狐狸 + 主手方块，`v.ypos` 抬到空中 | 每只 1 实体 + 9 条命令 |
| **世界内血条**（方块阵列当格子） | N 只狐狸排一行，按血量 `v.scale` 缩放到 0 或 1 | N 实体 + N×9 条 |
| **商品展示柜**（商店悬浮商品） | 每格一个狐狸，`v.yrot` 慢慢转 | 同上 |
| **建筑打印机预览** | 用缩放/位移把方块"推"到目标位置，先预览再落 | 同上 |
| **武器特效**（缩放的模型当刀光/弹道） | 狐狸当"贴图"，`v.scale` 从大到小 + `v.xpos` 推进 | 同上 |

**共同的坑**：

1. **每个狐狸都是一个实体**，几十只就会卡。血条别用这个做，用 `titleraw`（05-ui.md）。
2. **狐狸会自己走**，必须每刻 `tp` 回来（或者 `effect slowness 255` 定住）。
3. **`playanimation` 是持续性的**，写一次就一直在跑；改参数要再写一次。
4. **命令很长**（单条 300+ 字符），生成器里要用字符串拼接，别手写。

---

## 七、什么时候不该用

- **纯文字 UI** → 用 `titleraw`（`05-ui.md`），便宜 10 倍
- **只需要"标记一个点"** → 用粒子或发光方块，不用狐狸
- **要精确跟随玩家** → 每刻 `tp` 有延迟，手感会飘
- **服务器实体上限紧张** → 狐狸是实体，会占 mob cap

---

## 八、和其他方案的对比

| 方案 | 能做 3D | 命令成本 | 需要实体 | 版本依赖 |
|---|---|---|---|---|
| `titleraw`（本 skill 主力） | ❌ 只有屏幕文字 | 低 | ❌ | 低 |
| `setdisplay`（原生 HUD） | ❌ 只有分数/标题 | 极低 | ❌ | 低 |
| **FMBE 狐狸投影** | ✅ 任意方块/缩放/旋转 | 中（9 条/只） | ✅ 每只 1 个 | **高（系数有版本差异）** |
| `structure` 静态摆 | ✅ 但不可动 | 低 | ❌ | 低 |

**结论**：FMBE 是「必须做 3D 且必须能动」时的唯一选择，
其他情况一律先用 `titleraw` 或 `structure`。
