# 16 · 七个实战作品的拆解（他人思路 → 可复用套路）

> 样本：`Boss极寒剑尊` / `极冰剑刃` / `冰刺法杖` / `烈焰法杖` / `幽冥残骸` / `Boss史莱姆之王` / `拔刀剑`
> 全部用 `dump_cbworld.py` 逐条回读，共 1643 个命令方块。下面只写**能直接照抄的写法**和**该不该学**。

---

## 零、样本速览

| 作品 | 命令块 | 展示体手法 | 值得抄的点 |
|---|---|---|---|
| Boss极寒剑尊 | 303 | vex + 盔甲架（主手放方块） | 结构文件当 Boss 预制件；`camera rot` 固定机位；`damage` 带伤害源；**0 伤害当受击触发器** |
| 极冰剑刃 | 346 | fox ×6 + 盔甲架 | 9 条前置**全量默认值**写法；`name=` 分身份；10 条 `stopsound`；`uid` 排除自己 |
| 冰刺法杖 | 183 | 盔甲架 + 结构 | **`hasitem` + `data=` 区分同一物品**；`rx/rxm` 视线角触发；hotbar 当技能栏 |
| 烈焰法杖 | 157 | 同上 | 第一人称手部镜头；火龙卷用旋转支架 |
| 幽冥残骸 | 309 | fox ×9 | **血条 `t.healths=q.health`**；`fog` 氛围；`math.random` 做随机外观 |
| Boss史莱姆之王 | 167 | 盔甲架 + slime | **双盔甲架旋转支架**；`unless blocks` 落地检测；分身/分裂 |
| 拔刀剑 | 119 | 盔甲架 + boat | **`rotated as` + `positioned ^^^` 链式推进做弧线** |

---

## 一、命名体系：`summon` 的第 4、5 个参数

他们的展示体不靠计分打标，靠**名字**：

```mcfunction
summon fox ~~~ 0 0 minecraft:ageable_grow_up FM幽冥1
#      ↑实体 ↑坐标 ↑生成事件        ↑名字
```

之后全程用 `@e[name=FM幽冥1]` 精确点名，反选写 `name=!FM幽冥1`。

| | 名字（`name=`） | 计分（`scores={fmbe_gem=N}`） |
|---|---|---|
| 可读性 | 高，回读一眼看出是谁 | 低，得查表 |
| 一条命令控一组 | 要写多个 `name=` | `scores={fmbe_gem=1..}` 一行搞定 |
| 重名风险 | 重名会一起命中 | 不会 |
| 调试 | 可直接 `tp @e[name=xx]` 找 | 要先给分 |

**结论**：**少数主角用名字**（Boss、核心、血条），**成组用计分**。两者可以叠：
`@e[name=FM幽冥地刺,type=fox,scores={计时=85..}]`。

> 注意：`summon` 的生成事件不能省。狐狸写 `minecraft:ageable_grow_up`（成年），
> 省了会生成幼崽，模型尺寸直接差一半。

---

## 二、9 条前置：两套系数（版本差异）

样本里的写法（与主文件十一.1 的差异只在**两个常数**）：

```mcfunction
playanimation @e[tag=wiki:fmbe] animation.player.sleeping none 0 "" controller.animation.fox.move
playanimation @e[tag=wiki:fmbe] animation.creeper.swelling none 0 "v.xbasepos=v.xbasepos??0;v.ybasepos=v.ybasepos??0;v.zbasepos=v.zbasepos??0;v.xpos=v.xpos??0;v.ypos=v.ypos??0;v.zpos=v.zpos??0;v.xrot=v.xrot??0;v.yrot=v.yrot??0;v.zrot=v.zrot??0;v.scale=v.scale??1;v.xzscale=v.xzscale??1;v.yscale=v.yscale??1;v.swelling_scale1=2.1385*math.sqrt(v.xzscale)*math.sqrt(v.scale);v.swelling_scale2=2.1385*math.sqrt(v.yscale)*math.sqrt(v.scale);" wiki:scale
playanimation @e[tag=wiki:fmbe] animation.ender_dragon.neck_head_movement none 0 "v.head_rotation_x=0;v.head_rotation_y=0;v.head_rotation_z=0;v.head_position_x=(v.xbasepos*3741/8000)*math.sqrt(v.xzscale)*math.sqrt(v.scale);v.head_position_y=(10.6925+v.ybasepos*3741/8000)*math.sqrt(v.yscale)*math.sqrt(v.scale);v.head_position_z=(17.108-v.zbasepos*3741/8000)*math.sqrt(v.xzscale)*math.sqrt(v.scale);" wiki:shift_pos
playanimation @e[tag=wiki:fmbe] animation.warden.move none 0 "v.body_x_rot=90+v.xrot;v.body_z_rot=90+v.yrot;" wiki:xrot
playanimation @e[tag=wiki:fmbe] animation.player.attack.rotations none 0 "v.attack_body_rot_y=-v.zrot;" wiki:zrot
playanimation @e[tag=wiki:fmbe] animation.parrot.moving none 0 "v.wing_flap=(16-v.xpos)/0.3;" wiki:xpos
playanimation @e[tag=wiki:fmbe] animation.minecart.move.v1.0 none 0 "v.rail_offset.x=0;v.rail_offset.y=1.6485+v.ypos/16;v.rail_offset.z=0;" wiki:ypos
playanimation @e[tag=wiki:fmbe] animation.parrot.dance none 0 "v.dance.x=-v.zpos;v.dance.y=0;" wiki:zpos
```

**两套系数**（不同版本狐狸模型改过，只能试）：

| 常数 | 旧写法 | 新写法（样本用的） |
|---|---|---|
| 位移系数 | `0.433875` | `3741/8000 = 0.467625` |
| Y 基线 | `10.05185375` | `10.6925` |

判据：**方块摆在 `ybasepos=0` 时是否正好套在狐狸身上**。歪了就是系数不对，换另一套。
两套混用会出现"X 对 Y 偏"的错位，别混。

**9 条里第一条最容易漏**：`animation.player.sleeping` + `controller.animation.fox.move`。
漏了它，后面 8 条全白写——狐狸会自己走、自己转头，方块跟着乱飘。

---

## 三、展示体不止狐狸：盔甲架 + 主手方块

样本里大量用**盔甲架**当展示体：

```mcfunction
summon armor_stand 外壳 ~~~ 0 0 冰块
replaceitem entity @e[tag=外壳] slot.weapon.mainhand 0 slime
playanimation @e[tag=外壳] animation.creeper.swelling none 0 "v.swelling_scale1=5;v.swelling_scale2=5;" 拉长
```

`replaceitem` 塞进主手的**方块**会以小模型渲染，再被 `creeper.swelling` 放大 5~12 倍，
就成了"一个方块"。vex 同理可用（要配 `controller.animation.vex.move` 重置姿态）。

| | 狐狸 | 盔甲架 |
|---|---|---|
| 声音 | 有 10 种狐叫，必须 `stopsound` 压 | **完全无声** |
| 会自己动 | 会（要锁位 + 重置 controller） | 不会，摆哪是哪 |
| 方块尺寸 | 原生 1 格，缩放自然 | 物品模型很小，要放大 5~12 倍 |
| 占生物名额 | 是 | 否（不参与生物 AI） |
| 能否 `playanimation` | 能 | 能（同样的 9 条通道） |

**选择**：要"大方块、要旋转缩放"→ 狐狸；要"安静、要精确摆位、要几十个"→ 盔甲架。

---

## 四、旋转支架：不用 Molang 的公转

史莱姆之王/烈焰法杖的"法阵旋转"是这么做的——**两个隐形盔甲架，一个当转轴，一个当挂点**：

```mcfunction
summon armor_stand 法阵1 ~~20~
summon armor_stand 法阵2 ~~21~
execute as @e[name=法阵1] at @s run tp @s ~~~ ~2.5          # 转轴：每刻自转 2.5°
execute as @e[name=法阵1] at @s run tp @e[name=法阵2] ^^1^10 # 挂载：轴前方 1 格、偏 10 格
execute as @e[name=法阵2] at @s run particle ... ^^1^4.5      # 特效挂在挂点上
```

原理：`tp` 的第二组参数是**旋转**。转轴自己转，挂点用 `^^` 相对它定位 → 挂点绕轴公转。

| | 旋转支架 | `v.yrot` 公转 |
|---|---|---|
| 命令数 | 每个挂点 1 条/刻 | **全部 1 条/刻** |
| 可调性 | 摆在哪里看得见，好调 | 要算角度 |
| 适用 | 少量挂点、要叠加多层嵌套 | 几十个展示体整圈转 |

**别拿它替代 `v.yrot`**：50 个展示体用支架 = 50 条 tp/刻，用 yrot = 1 条。

---

## 五、弧线：`rotated as` + `positioned ^^^` 链式推进

命令里不能写循环，于是他们把循环**展开**：

```mcfunction
execute as @e[tag=刀光] at @s \
  rotated as @e[tag=锚点] positioned ^^^0.5 \
  rotated as @e[tag=锚点] positioned ^^^1 \
  rotated as @e[tag=锚点] positioned ^^^2 \
  rotated as @e[tag=锚点] positioned ^^^4 \
  run particle minecraft:endrod ~~~ ...
```

每一步：`rotated as 锚点`（朝向锚点）→ `positioned ^^^N`（沿视线前进 N 格）。
锚点在动，于是这条"折线"就成了弧。**N 递增（0.5/1/2/4）等于加速**，越走越远。

用途：斩击轨迹、鞭状攻击、绕身螺旋、剑气。

**代价**：一条命令里叠 8~10 个 `rotated as` 就难读难改，且一旦锚点缺失整条失效。
**我们自己的做法更好**：用粒子逐点绘图（`ring_cmds`/`line`），坐标是算出来的，改参数即可。

---

## 六、触发体系（这一节最值钱）

### 6.1 `hasitem` 支持 `data=` —— 一本书一个技能

```mcfunction
give @s enchanted_book 1 104
execute as @a[hasitem={item=enchanted_book,data=104,location=slot.weapon.mainhand}] at @s run ...
```

`data=` 是**附加值（aux）**，和物品类型正交。所以：

| 技能 | 物品 | data |
|---|---|---|
| 冰刺 | enchanted_book | 101 |
| 冰刺·蓄力 | enchanted_book | 102 |
| 冰刺·终结 | enchanted_book | 103 |
| 火球 | enchanted_book | 104 |

> ❗ **这条推翻主文件十一.3 的旧结论**（"`hasitem` 读不到物品名，只能靠类型唯一"）。
> 名字确实读不到，但 **`data=` 能读**，一本附魔书可以当 20 个不同技能用。
> 同法可用于 `nautilus_shell,data=101/102`、`dye,data=8/9/10/12`。

### 6.2 视线俯仰角当触发

```mcfunction
tag @a[rx=-88,rxm=-90,hasitem={item=enchanted_book,data=102}] add 冰刺技能2   # 抬头看天
tag @a[rx=90,rxm=88,hasitem={item=enchanted_book,data=101}] add 冰刺攻击       # 低头看地
```

`rx/rxm` 是俯仰角区间，-90 是正上方，90 是正下方。**抬手看天 = 蓄力，低头 = 释放**，
比按键更符合"施法"的直觉，且不需要任何 UI。

### 6.3 hotbar 当技能栏

```mcfunction
# 塞图标：把槽位换成染料，锁死不被拿走
replaceitem entity @a[...] slot.hotbar 5 dye 1 9 {"minecraft:item_lock":{"mode":"lock_in_slot"},"minecraft:keep_on_death":{}}
# 用掉了（数量变 0）→ 补回成技能书
execute as @a[hasitem={item=dye,data=9,quantity=0}] at @s run replaceitem entity @s[...] slot.hotbar 5 enchanted_book 1 104 {...}
```

`quantity=0` 是"槽位空了"的判定，`quantity=10..` 是"攒够了"。**数量即冷却**。
`item_lock: lock_in_slot` 防玩家把图标拖走，`keep_on_death` 防死亡掉落。

### 6.4 `fishing_hook` 当攻击判定

```mcfunction
execute as @e[type=fishing_hook] at @s if score @p 武器 matches 1..10 run tag @p add 攻击
```

鱼钩飞出去 → 命中即触发。比 `hasitem` 多一层"确实挥出去了"的语义。

### 6.5 `uid` 排除自己

```mcfunction
execute as @e[name=冰刺] at @s at @e[r=1.3,type=!fox] unless score @e[c=1] uid = @s uid run tag @e[c=1] add 受击
```

施法者给每个实体发一个唯一 `uid`，判定时排除"自己人"。

---

## 七、结构文件当预制件

```mcfunction
structure load 冰刺 ~~~                      # 在脚下生成一套冰刺
structure load 恼鬼Boss ~1~1.5~8              # 生成整个 Boss（含实体）
execute as @a[scores={技能=100}] at @s anchored eyes run structure load 冰块2 ^^^   # 视线前方 1 格
```

**先检测空位再放**，防重叠：

```mcfunction
execute if blocks ~~2~ ~~2~ ~-1~-3~ all run structure load 召唤史莱姆王 ~~16~
```

清理：`fill ~~2~ ~~3~ air`，或 `clone` 回原位。

| 路线 | 会真占方块 | 能动画 | 适合 |
|---|---|---|---|
| 结构文件 | **是**（要手动清） | 否（整体不能缩放旋转） | 冰刺、法阵、Boss 预制件、可复用的"模型" |
| 狐狸 FMBE | 否 | 是 | 悬浮方块、剑、旋转结构 |
| 纯粒子 | 否 | 是（但只是一次性） | 法阵线、轨迹、冲击波 |

---

## 八、判定与伤害

```mcfunction
damage @a[r=4] 6 entity_attack entity @s        # 第 4 参数 = 伤害源，击杀归属正确
damage @e[tag=Boss] 0 entity_attack entity @p   # 0 伤害 = "被打了一下"的触发器
```

**0 伤害触发器**很好用：想在某实体"被攻击"时跑一串命令，又不想扣血，
就 `damage ... 0 ... entity @p`，另一边 `execute as @e[tag=受击] ...` 接手。

**落地/命中检测**（体积内全是空气 = 没落地）：

```mcfunction
execute as @e[tag=史莱姆王] at @s unless blocks ~1~-0.3~1 ~-1~-0.3~-1 ~ 300 ~ all run tag @s add 落地
```

`blocks <起点> <终点> <目标方块> [模式]`，`300` 是空气的 runtime id，`all` 表示整块区域都是。
这条比 `if block ~~-1~ air` 稳得多——不会因为站在台阶边缘就误判。

---

## 九、血条：`q.health` 中转

```mcfunction
playanimation @e[name=FM幽冥受击] animation.player.attack.positions move 0 "t.healths=q.health;"
playanimation @e[name=FM幽冥血条] animation.player.attack.positions none 0 "v.xpos=0;v.ypos=90;v.zpos=0;v.scale=1;v.yscale=t.healths/100;v.xzscale=1;" 等效初始
```

`q.health` 是实体当前血量（0~100 时 `t.healths/100` 正好是 0~1）。
`t.` 是**临时变量，同一刻内跨命令可读**，所以第一条写、第二条读。

血条本体就是一根被 `yscale` 压扁的方块（`v.ypos=90` = 抬高 5.6 格）。
**这是"用展示体做 UI"的唯一可靠办法**——`titleraw` 只能出文字，血条必须是几何体。

---

## 十、演出层

| 写法 | 效果 |
|---|---|
| `camera @a[r=60] set minecraft:free ease 5 linear pos ~1~2~5 rot -88 0` | **绝对朝向**机位，适合固定构图 |
| `camera @s set minecraft:free ease 0.2 linear pos ^^5^-3 facing @s` | **相对朝向**，第一人称手部视角 |
| `ease 0.1 linear` | 硬切（换镜头不拖影） |
| `camera @a[r=60] fade` | 黑屏过渡 |
| `camerashake add @a[r=20] 1 0.1 positional` | 落地震屏；`rotational` 是转屏 |
| `/fog @a[r=100] push minecraft:fog_soulsand_valley` | 氛围雾（**记得 `fog pop`**） |

`rot <pitch> <yaw>`：pitch 是俯仰（-90 正上），yaw 是水平。样本用 `rot -88 0` 做"仰拍"。

---

## 十一、音效与清理

**狐叫一共 10 条**，必须每刻压：

```mcfunction
stopsound @a mob.fox.ambient
stopsound @a mob.fox.aggro
stopsound @a mob.fox.bite
stopsound @a mob.fox.death
stopsound @a mob.fox.eat
stopsound @a mob.fox.hurt
stopsound @a mob.fox.screech
stopsound @a mob.fox.sleep
stopsound @a mob.fox.sniff
stopsound @a mob.fox.spit
```

**清理分级**（样本的做法，比一刀 `kill` 干净）：

```mcfunction
execute as @e[name=FM幽冥地刺,scores={计时=85..}] at @s run tp @s ~ ~-10 ~     # 先沉下去
execute as @e[name=FM幽冥地刺,scores={计时=90..}] at @s run tp @s ~ -200 ~     # 再送走
execute as @e[name=FM幽冥地刺,scores={计时=100..}] at @s run kill @s           # 最后删
```

顺手清掉落物：`kill @e[r=200,type=xp_orb]`、`kill @e[name=黏液球,type=item]`。

---

## 十二、四条路线怎么选

| | 狐狸 FMBE | 盔甲架 + 主手方块 | 结构文件 | 纯粒子 |
|---|---|---|---|---|
| 数量上限 | 少（每只 8 条渲染，按组共享） | 多（无声、无 AI） | 不限（是方块） | 不限 |
| 能缩放旋转 | 能，精细 | 能 | 不能 | 不能 |
| 有声音 | 有（10 条要压） | 无 | 无 | 无 |
| 清理 | 摘标记 + tp 虚空 | 直接 `kill` | `fill air` | 自己消失 |
| 适合 | 悬浮剑、旋转方块、主体 | 大量静态/半静态道具 | 预制件、Boss、法阵 | 线框、轨迹、冲击波 |

**混合用法最实际**（样本都在混）：
主体用狐狸 → 配角用盔甲架 → 大件用结构 → 光效用粒子。

---

## 十三、别学的部分

| 反面 | 原因 |
|---|---|
| 一条命令叠 10 个 `rotated as` + `positioned` | 不可读、不可维护，锚点一丢整条失效 |
| 全库 `tag` 混用（样本里 687 处） | 命名混乱、容易互相污染；**我们坚持零 tag + 计分** |
| 用 `@p` 当施法者 | 多人同场会打错人，用 `cam_cast`/`cam_t` |
| 命令方块里写 `/fog`（带前导斜杠） | 部分版本报"未知命令"，去掉斜杠 |
| 用 `kill` 清几百个展示体 | 会卡一帧；先摘标记再 `tp -400` |
| `structure load` 不做空位检测 | 叠在一起会互相顶掉，先 `if blocks ... all` |

---

## 十四、`.bdx` 是什么

样本 `凛冬祈愿2.bdx` 不是 zip，也不是 NBT——头部 `42 44 40`（"BD@"）+ 压缩/加密载荷，
无任何明文可读。它是第三方编辑器的**工程文件**，必须用它自己的导出功能转成 `.mcworld`。

判断依据：样本里的 `.mcworld` 内都有 `detail.json`：

```json
{ "orig_file_path": "指令2(2).bdx", "orig_file_type": "bdx",
  "orig_file_hash": "BCVA...", "convert_dir": "omega_convert\\BCVA..." }
```

**结论**：拿到 `.bdx` 先找它对应的 `.mcworld` 转换产物，别硬解。
