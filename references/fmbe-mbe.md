# FMBE / MBE 显示实体（命令方块）

> FMBE / MBE 不是真正的方块，而是**用实体 + 动画 + Molang 伪装出来的显示模型**。
> 服务端看到的是一只狐狸/盔甲架；客户端看到的是方块或物品模型。
> 必读：[FMBE - A New Way to Create Display Entities](https://wiki.bedrock.dev/commands/display-entities.html)、[MBE - Max's Block Entity](https://wiki.bedrock.dev/commands/block-entities.html)。
> 工具/模拟器导航：[FMBE Hub](https://fmbe-hub.ora-san.org/)。

## 1. 先分清几个名字

| 名字 | 载体 | 展示方式 | 备注 |
|---|---|---|---|
| FMBE | 狐狸（fox） | 主手物品模型 | 一套 `playanimation` 链 + Molang；一实体一显示 |
| MBE | 盔甲架 | 副手物品模型 | 命令更少；有盔甲架碰撞箱 |
| SMBE | 盔甲架 | 左手物品 | 奶昔 Smoothie 的 MBE 变体，变量与 FMBE 相同 |
| SMBE-EX | 盔甲架 | 副手物品 | 高级版：内外层旋转、防抖、命令更长、顺序严格 |
| SDME | 双显示 | 两个模型叠加 | 文件标注**网易目前不可用** |

共同点：

- **纯命令 + Molang**，不需要行为包。
- **一个实体只能显示一个模型**；摆 100 个方块就是 100 只实体。
- 实体仍然有 AI/碰撞/声音，必须处理。
- 显示是客户端的；服务端不能把它当方块检测。

## 2. 前置条件（必须）

| 前置 | 说明 |
|---|---|
| `playanimation` | 网易 1.21.130 可用（样本地图 30 次使用） |
| `summon` | 生成狐狸/盔甲架 |
| `replaceitem` | 给主手/副手物品模型 |
| `tag` | 标记显示实体，避免影响野生狐狸 |
| `effect` | 隐身、抗性 |
| `stopsound` | 关掉狐狸叫声 |
| `event` | 让狐狸成年（`minecraft:ageable_grow_up`） |
| `tickingarea` | 远处/无人区显示需要；近处随玩家区块加载 |
| `structure save/load` | 保存带实体的显示装置 |
| 命令方块/函数 | 一条 `playanimation` 链；顺序不能乱 |

### FMBE 最小初始化（聊天栏执行一次）

```mcfunction
summon fox ~~~ ~ ~ minecraft:as_adult "wiki:fmbe"
replaceitem entity @n[name="wiki:fmbe"] slot.weapon.mainhand 0 minecraft:lime_concrete
tag @e[name="wiki:fmbe"] add wiki:fmbe

effect @e[tag=wiki:fmbe] invisibility infinite 255 true
effect @e[tag=wiki:fmbe] resistance infinite 255 true
effect @e[tag=wiki:fmbe] slowness infinite 255 true
event entity @e[tag=wiki:fmbe] minecraft:ageable_grow_up

stopsound @a mob.fox.ambient
stopsound @a mob.fox.bite
stopsound @a mob.fox.death
stopsound @a mob.fox.eat
stopsound @a mob.fox.hurt
stopsound @a mob.fox.screech
stopsound @a mob.fox.sleep
stopsound @a mob.fox.sniff
stopsound @a mob.fox.spit
stopsound @a mob.fox.aggro
```

- `<itemID>` 用方块物品（`lime_concrete`、`oak_planks`）或普通物品（`stick`、`diamond_sword`）。
- `@n` 是最近实体；如果目标版本不支持，用 `@e[name="wiki:fmbe",c=1]` 代替。
- 狐狸会动；用 `tp @e[tag=wiki:fmbe] <锚点>` 或高频 `tp @s ~~~` 固定。
- 狐狸成年用 `minecraft:as_adult` 或 `event ... ageable_grow_up`。

## 2.5 多部件 FMBE：初始化链要分段

一个 14 部件 Boss 不是“召唤 14 只狐狸”这么简单：每个部件要 `summon → tag → 主手物品 → 锚定`，
初始化命令很容易超过 100 块。真机上遇到过：

- 115 块单条 impulse 链，14 只部件都在，但只有 9 个唯一 tag；
- 中间几条 `tag` 被服务器吞掉，`tp`/`replaceitem` 找不到目标，部件留在装配点；
- 拆成 **63 + 53** 两条 impulse 链，各自用红石触发后复查 `PARTS 14 / UNIQUE 14`。

做法：

1. 每个部件一个独占 tag（`boss_p_<name>`）或稳定 name；不要用互相重叠的 `r=0.6` 体积。
2. 初始化链超过 ~70 块就拆段；每段一个 impulse 头，触发红石可以并排。
3. 由最后一段统一清掉所有触发红石，避免重复触发。
4. 初始化后先跑一次计数（`execute as @e[tag=...] run scoreboard add`），再开战。
5. 多部件 FMBE 的碰撞箱会挡住真实受击核心；核心要放在模型前方。移动 Boss 可直接让隐形载体当核心，部件相对跟随。

完整 14 部件、两套姿态、真实命中检测的例子见 `examples/frostcrown-fmbe/`。

## 2.6 移动载体：让整只 FMBE 跟着玩家走

固定锚点的 Boss 不会追人。把“模型中心”做成一个隐形移动载体（cow/僵尸/劫掠兽），
FMBE 部件每 tick 以载体为原点相对 `tp`：

```mcfunction
# 面向最近玩家
execute as @e[tag=carrier] at @s if entity @a[tag=fighter,r=24] run tp @s ~ ~ ~ facing entity @a[tag=fighter,c=1]
# 距离 >2.5 前进 0.18 格/tick；rotated as @s 让 ^ 用载体的朝向
execute if score st bs matches 1 as @e[tag=carrier] at @s rotated as @s if entity @a[tag=fighter,r=24] unless entity @a[tag=fighter,r=2.5] run tp @s ^ ^ ^0.18
# 锁 y、出界回中心
execute if score st bs matches 1 as @e[tag=carrier] at @s run tp @s ~ 4.5 ~
execute if score st bs matches 1 as @e[tag=carrier] at @s unless entity @s[x=506,y=2,z=506,dx=18,dy=8,dz=18] run tp @s 515.5 4.5 516.3
# 部件位置相对载体：^ 随载体 yaw 旋转
# 朝向点 aim 在载体前方 10 格，再用 facing 让部件 yaw 一致
execute as @e[tag=part_head] at @e[tag=carrier] run tp @s ^0 ^2.9 ^-0.8
execute as @e[tag=part_head] at @s run tp @s ~ ~ ~ facing entity @e[tag=aim]
```

- 载体本身当受击核心：戴 1 耐久头盔，`replaceitem ... keep` + conditional 做真实命中；cow 不渲染护甲。
- 部件偏移 = 原绝对坐标 − 载体坐标；用 `^` 让位置随 yaw 旋转，再 `facing aim` 让模型 yaw 一致。只改位置不改 yaw 会“平移不转身”。
- 朝向点 aim 用隐形 armor_stand；记得在二阶段冰晶 tag 里排除它。
- 待机时把载体 `tp` 回中心，避免追到出生点。
- 完整移动版见 `examples/frostcrown-fmbe/`。

## 3. FMBE 的动画链（1 条初始化 + 7 条变量/姿态）

FMBE 的核心是 1 条初始化 + 7 条变量/姿态 `playanimation`（共 8 条），后面的控制器读取前面的变量：

```mcfunction
# 1) 清空/默认值（必须第一个；控制器必须是 controller.animation.fox.move）
playanimation @e[tag=wiki:fmbe] animation.player.sleeping none 0 "" controller.animation.fox.move

# 2) 缩放 + 位置变量默认值
playanimation @e[tag=wiki:fmbe] animation.creeper.swelling none 0 "v.xbasepos=v.xbasepos??0;v.ybasepos=v.ybasepos??0;v.zbasepos=v.zbasepos??0;v.xpos=v.xpos??0;v.ypos=v.ypos??0;v.zpos=v.zpos??0;v.xrot=v.xrot??0;v.yrot=v.yrot??0;v.zrot=v.zrot??0;v.scale=v.scale??1;v.xzscale=v.xzscale??1;v.yscale=v.yscale??1;v.swelling_scale1=2.1385*math.sqrt(v.xzscale*v.scale);v.swelling_scale2=2.1385*math.sqrt(v.yscale*v.scale);" wiki.scale

# 3) 基础位移（1/16 格单位）
playanimation @e[tag=wiki:fmbe] animation.ender_dragon.neck_head_movement none 0 "v.head_rotation_x=0;v.head_rotation_y=0;v.head_rotation_z=0;v.head_position_x=(v.xbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);v.head_position_y=(10.05185375+v.ybasepos*0.467625)*math.sqrt(v.yscale*v.scale);v.head_position_z=(17.108-v.zbasepos*0.433875)*math.sqrt(v.xzscale*v.scale);" wiki.shift_pos

# 4) X/Y 旋转
playanimation @e[tag=wiki:fmbe] animation.warden.move none 0 "v.body_x_rot=90+v.xrot;v.body_z_rot=90+v.yrot;" wiki.xrot

# 5) Z 旋转
playanimation @e[tag=wiki:fmbe] animation.player.attack.rotations none 0 "v.attack_body_rot_y=-v.zrot;" wiki.zrot

# 6) X 位置
playanimation @e[tag=wiki:fmbe] animation.parrot.moving none 0 "v.wing_flap=(16-v.xpos)*3.3333333;" wiki.xpos

# 7) Y/Z 位置
playanimation @e[tag=wiki:fmbe] animation.minecart.move.v1.0 none 0 "v.rail_offset.x=0;v.rail_offset.y=1.6485+v.ypos/16;v.rail_offset.z=0;" wiki.ypos
playanimation @e[tag=wiki:fmbe] animation.parrot.dance none 0 "v.dance.x=-v.zpos;v.dance.y=0;" wiki.zpos
```

- 第一条的控制器必须是 `controller.animation.fox.move`；其余控制器可以命名空间化（`wiki.scale`、`wiki.xrot`…），避免撞车。
- **顺序不能乱**：后面的控制器读取前面写入的 `v.*`。
- 这条链放在 `repeat` 命令方块里持续执行；或在变量变化时重跑。
- 控制变量：

```mcfunction
# 把方块放到狐狸上方 1 格、放大 2 倍、绕 Y 转 45°
playanimation @e[tag=wiki:fmbe] animation.player.attack.positions none 0 "v.xpos=0;v.ypos=16;v.zpos=0;v.xrot=0;v.yrot=45;v.zrot=0;v.scale=2;v.xzscale=1;v.yscale=1;" wiki:set
```

## 4. 变量表

| 变量 | 单位/作用 |
|---|---|
| `v.xpos` `v.ypos` `v.zpos` | 位移，**1/16 格**（16 = 1 格） |
| `v.xrot` `v.yrot` `v.zrot` | 旋转，度；外层欧拉角顺序 **YZX**（普通版） |
| `v.xbasepos` `v.ybasepos` `v.zbasepos` | 基准位移，不改变旋转中心；同样 1/16 格 |
| `v.scale` | 总缩放，默认 1 |
| `v.xzscale` `v.yscale` | XZ/Y 轴缩放 |
| `v.extend_scale` `v.extend_xrot` `v.extend_yrot` | item/高级版的扩展骨骼 |
| `v.F.*` | 矩阵中间量（高级 FMBE） |
| `v.F_*` `v.S_*` `v.T_*` | 多骨骼串联（5骨骼触手） |
| `q.position(0..2)` | 实体在组中的归一化位置（0..1） |
| `q.life_time` | 生命时间（秒） |
| `q.rotation_to_camera(0/1)` | 朝向摄像机的 yaw/pitch |
| `q.is_item_name_any(...)` | 判断手持物品 |
| `q.equipped_item_any_tag(...)` | 按物品 tag 判断 |

> 位置是 1/16 格；`v.ypos=16` 是向上 1 格。旋转是角度制。
> `变量汇总9.26.txt` 里还有大量原版动画变量/骨骼名，可直接查表。

## 5. MBE（盔甲架）最小系统

MBE 用盔甲架的副手物品显示方块，命令比 FMBE 少：

```mcfunction
# 1) 生成盔甲架（名字 Grumm，yaw 81）
summon armor_stand "Grumm" ~~~ ~ ~ 81 0

# 2) 娱乐姿势（让手臂/身体摆成展示姿态）
playanimation @e[name=Grumm] animation.armor_stand.entertain_pose none 0 ""

# 3) 副手放方块物品
replaceitem entity @e[name=Grumm] slot.weapon.offhand 0 minecraft:lime_concrete

# 4) 迷你方块尺寸
playanimation @e[name=Grumm] animation.creeper.swelling none 0 "v.swelling_scale1=2.1385;v.swelling_scale2=2.1385;"

# 5) 完整方块尺寸（与迷你二选一）
# playanimation @e[name=Grumm] animation.creeper.swelling none 0 "v.swelling_scale1=6.4155;v.swelling_scale2=6.4155;"

# 6) 固定 + 隐身
tp @e[name=Grumm] <x> <y> <z> 81 0
effect @e[name=Grumm] invisibility infinite 255 true
```

- 完整方块要按方块类型补位置/旋转；楼梯、台阶、箱子等有单独偏移命令，见 MBE wiki。
- 盔甲架有碰撞箱；玩家可以穿过/挤动，必要时用 `tp` 每 tick 固定。
- 保存/加载：

```mcfunction
structure save wiki:mbe <from> <to> disk
structure load wiki:mbe <to>
```

## 6. SMBE / SMBE-EX / SDME

- **SMBE**：盔甲架左手显示，变量与 FMBE 相同；支持物品/旗帜/工具模式（400+ 物品），但命令链更长，TP 可能抖动。
- **SMBE-EX**：盔甲架副手；新增 `v.ex_xrot` `v.ex_yrot` `v.ex_zrot` 内层旋转；外层 YZX、内层 ZYX；命令顺序严格，标 `*` 的前置命令用于防姿势污染；TP 防抖更好。
- **SDME**：双显示（两个模型叠加）；提供的文件明确标注**网易目前不可用**，不要用于网易 1.21.130。

> 这些是社区系统，版本/平台差异大；用前先看文件头部的版本、平台、前置说明。

## 7. 例子里的应用模式

### 画函数 / 两点连线

```mcfunction
# 用 q.position(0) 把一群狐狸铺在曲线上
playanimation @e[name=curve] animation.player.attack.positions none 0 "v.x=q.position(0)*16;v.y=math.sin(v.x/16*3.14159)*8;v.z=0;v.xrot=0;v.yrot=0;v.zrot=0;"
```

- 两点连线：`v.yscale=长度`、`v.xzscale=0.2`，再用 `v.yrot` 对准方向。
- 画函数：采样 x，算 `f(x)`，用导数/差分算 `v.xrot` 让方块贴合曲线。
- 狐狸数量 = 采样点数量；曲线越长越吃性能。

### 螺旋线 / 平滑追踪

- 螺旋线：盔甲架在中心，`tp @s ^ ^ ^<半径>` + `rotation` 递增；粒子做轨迹。
- 平滑追踪：钓鱼钩/目标实体做锚点，盔甲架带 `uid` 分数配对，每 tick `tp` 到目标附近；用命令链/函数推进。
- 这些例子里的 `camera` 指令在网易 1.21.130 **未验证**；要移植就删掉 camera 部分，用 `tp ... facing` + `title` 代替。

### 任意角度沉浸式传送门

```mcfunction
playanimation @e[type=fox] animation.player.attack.positions none 0 "v.x1=?;v.z1=?;v.x2=?;v.z2=?;v.yaw=q.rotation_to_camera(1);v.fx=q.position(0)-0.5;v.fz=q.position(2)-0.5;v.px=-math.sin(v.yaw);v.pz=math.cos(v.yaw);v.test1=v.pz*(v.x1-v.fx)-v.px*(v.z1-v.fz);v.test2=v.pz*(v.x2-v.fx)-v.px*(v.z2-v.fz);"
```

- 用 `q.rotation_to_camera` 让传送门面向玩家；`test1/test2` 判断玩家在门框哪一侧。
- `?` 处填门框 x/z 坐标；二维双向门可用。

### 爱心 / 椭圆 / 鱼

```mcfunction
playanimation @e[name=a] animation.player.attack.positions none 0 "v.n=4;v.xzscale=0.05;v.r0=v.r0??360*(q.position(0)-0.5)/math.pow(2,v.n);v.r=v.r0;v.a=5;v.b=5;v.xp=v.a*math.cos(v.r);v.yp=v.b*math.sin(v.r);v.zp=0;"
```

- 用 `q.position(0)` 把多只狐狸均匀分布到 0..360°，再用 `cos/sin` 摆成椭圆/爱心/鱼。
- `v.n` 控制分层；`v.r0` 用 `??` 保留首帧值，避免每 tick 重算。

### 5骨骼触手 / 多骨骼

- 用 `v.F_*` `v.S_*` `v.T_*` 把多段骨骼串起来；每段狐狸/盔甲架一个实体。
- 先算父段矩阵，再传给子段；顺序严格。
- 适合触手、尾巴、链条；实体数量随段数线性增长。

## 8. 网易 1.21.130 注意事项

- `playanimation` 可用；`camera` 未验证；`fog` 未实装；`SDME` 不可用。
- FMBE 的 8 条命令 + 变量设置都在命令方块/函数里；注意单条命令 32,500 字符上限。
- 显示实体是**客户端视觉**：不能当方块检测，不能参与碰撞/红石。
- 狐狸有 AI/声音/碰撞；必须隐身、抗性、消音、固定。
- 一个方块一个实体；100 个方块 = 100 只狐狸；先做性能预算。
- 远处显示需要 `tickingarea`；近处随玩家区块加载。
- `structure save/load` 会保存实体；加载后重新打 tag/effect，避免状态丢失。

## 9. 最小检查清单

- [ ] 狐狸成年、隐身、抗性、消音。
- [ ] 主手物品是正确的方块/物品。
- [ ] 8 条 `playanimation` 顺序正确，第一条控制器是 `controller.animation.fox.move`。
- [ ] 变量单位是 1/16 格，旋转是角度。
- [ ] 狐狸被 `tp` 固定在锚点，不会乱跑。
- [ ] 显示实体有 tag，不会误伤野生狐狸。
- [ ] 多部件初始化链 >70 块已拆段；触发后计数确认“部件数 = 唯一 tag 数”。
- [ ] 有真实受击核心；不是用距离/`hasitem` 判定命中。
- [ ] 区块加载/`tickingarea` 已处理。
- [ ] 保存/加载后重新执行初始化。

## 10. 实测校准：多部件模型不要堆在同一点

多部件 FMBE 模型实测：

- **一个部件一只狐狸，狐狸站在部件中心**。不要把 6 只狐狸堆在同一个基点、再用 `v.xpos/ypos/zpos` 拉开；FMBE 物品枢轴/嘴部偏移会把头、身体、手臂的前后关系搞错，出现“头贴在身体前面/上下分离”。
- **坐标取 .5 中心**：`summon fox 70 ...` 实际会吸到 `70.5`，而 `69.625` 这类小数坐标不会；混用会让模型左右不对称。统一用 `70.5 / 70.125 / 70.375 ...` 这种真实中心。
- **tag 用绝对体积选择器**：命令方块在 y=210 时，`r=2` 是相对命令方块，不是模型；用 `x=..,y=..,z=..,dx=..,dy=..,dz=..`。
- **普通版 vs EX 版**：普通版读 `v.xzscale/v.yscale`；EX 版读 `v.extend_scale/v.extend_xrot`。同一命令里两组都写，兼容两种运行时：
  - 身体：`scale=0.5, yscale=1.5` 或 `extend_scale=1.224744871, extend_xrot=90`
  - 四肢：`scale=0.25, yscale=3` 或 `extend_scale=1.732050808, extend_xrot=90`
- **头部/身体接触**：脚底 y=2；腿中心 2.375、身体中心 3.125、头中心 3.75；每段 0.75/0.75/0.5，正好 2.0 格。
- **不要用 `player_head` 当部件**：它的物品枢轴和普通方块不同，实测会头贴到身体前面；用 0.5 格皮肤块 + 头发/眼睛/嘴（v3 共 10 个部件），全部同一类方块。
- **渲染 1 Hz** + **每 tick 分部件锚定**；20 Hz 跑 48 条 Molang 会拖垮服务器。
- AIEX 的结构导出也是“1 命令方块 → 1 狐狸”，狐狸就是站在方块位置；这是比“单基点 + 偏移”更稳的工程方式。

## 11. AIEX 逆向：它为什么准

从 `AIEX-FMBE-v2.05.1-debug.apk.1` 里提取到的关键文件：

- `assets/ai_modeling_system_prompt.txt`：建模 AI 的系统提示词。
- `assets/dist/assets/index.js`：场景、矩阵、导出。
- `AIEX2.0.5` 的 `src/upstream-ex/modules/js/04-import-export/01-var-deps-and-mcstructure-export.js`：**未压缩**的导出实现。

### 10.1 真变量与矩阵

提示词原文要点：

- 基础几何是**中心在原点的 1×1×1 立方体**，8 顶点 `LBB/RBB/LTB/RTB/LBF/RBF/LTF/RTF`；
- 真变量只有：
  `xpos/ypos/zpos`、`xrot/yrot/zrot`、`scale`、
  `extend_scale/extend_xrot/extend_yrot`、`xbasepos/ybasepos/zbasepos`；
- **普通版**才有 `xzscale/yscale`，**EX 版**用 `extend_*`；
- 矩阵组合：
  `T(base) → ScaleY(extend_scale) → RotY(-extend_yrot) → RotX(-extend_xrot) → ScaleZ(extend_scale) → RotX(extend_xrot) → RotY(extend_yrot) → Scale(scale) → RotZ(-zrot) → RotX(xrot) → RotY(-yrot) → T(pos)`；
- AI 必须用 **vertexReport 的 8 顶点 + matrix4Rows** 复核，不能只看变量名。

> 这就是它“准”的根本：不是提示词魔法，而是**每次输出后用矩阵/8 顶点做几何复核**，不满足就继续修。

### 10.2 建模工具

AIEX2 的 EX 模式用 **`add_boxes`** 描述一个柱体：

- `origin`：底面中心；
- `up`：底面指向顶面的单位法线；
- `span`：底面中心到顶面中心的向量，长度=柱长；
- `side`：正方形截面边长。

程序反算成 `scale/extend_scale/extend_xrot/extend_yrot`，并在落盘前用几何回读校验；所以 AI 不需要手算矩阵。

普通版则直接给 `scale + xzscale/yscale`（方块）或 `scale + extend_scale`（EX 方块）。

### 10.3 导出：1 命令方块 → 1 狐狸

AIEX 的 `.mcstructure` 导出：

- 每模型方块 → **1 个命令方块 + 1 只狐狸**；
- 狐狸站在方块位置，命令方块用 `execute positioned ~-1~~ run playanimation @e[x=~,z=~,y=~,r=1] animation.player.attack.positions _ 0 "..."` 选中它；
- 一条命令里写该方块的全部 `v.*`，后缀 `'方块编号：<id>';` 用于重新导入识别；
- 狐狸身上**没有 tag、没有指令**；命令方块只负责“念”变量。

这印证了：**多部件模型必须一只狐狸一个部件、站在各自位置**；把 6 只堆在同一点靠 `v.pos` 拉偏移，枢轴/嘴部偏移一叠加就会头身错位。

### 10.4 对我们的改造

- v2 已改为 **6 只狐狸站在 6 个部件中心**；
- 用绝对体积选择器打 tag，不再用命令方块位置的 `r`；
- 同时写 `xzscale/yscale`（普通版）和 `extend_scale/extend_xrot=90`（EX 版）；
- 头/身体/四肢按 0.5/0.75/0.25 的**真实中心**排列。

> 如果进服看仍有偏差，优先确认是**视角透视**（俯视会把上下层投成左右偏移）还是**部件本身错位**；用平视截图判断，不要用俯视截图校准。

## 12. 来源

- [FMBE - A New Way to Create Display Entities](https://wiki.bedrock.dev/commands/display-entities.html)
- [MBE - Max's Block Entity](https://wiki.bedrock.dev/commands/block-entities.html)
- 用户提供的例子：`FMBE普通版`、`FMBE item`、`fmbe爱心`、`fmbe椭圆`、`fmbe鱼`、`MBE(平替FMBE)`、`SMBE`、`SMBE-EX`、`SDME双显`、`画函数`、`两点连线`、`螺旋线`、`平滑追踪`、`伊蕾娜扫把`、`任意角度沉浸式传送门`、`5骨骼触手`、`变量汇总9.26`
