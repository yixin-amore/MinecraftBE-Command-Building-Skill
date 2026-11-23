# 39 · FMBE 物理包拆解与兼容性

> 分析对象：`phy_v2.27(1).mcpack`（`物理_v2.26`，作者 BIn_LIn）。
> 本文是独立技术拆解，不包含原包代码；原包不进入本仓库。

## 静态审计

```bash
python3 scripts/mcpack_audit.py phy_v2.27\(1\).mcpack
```

审计输出：

```text
commands       11
playanimation   7
max_line       17,971
issues         tp @s ~~~~~ / line > 10000
```

结果记录在：

```text
examples/fmbe-physics/pack-audit.json
```

## 包结构

```text
manifest.json
pack_icon.png
functions/tick.json
functions/tick.mcfunction
```

类型：行为包 / data module。  
`tick.json` 注册每 tick 执行 `tick` function。

```text
min_engine_version  1.21.60
target              1.21.130（本 skill 目标）
commands            11
playanimation       7
最长单行            17,971 字符
总字符              21,370
```

## 核心结构

```text
fox + tag fmbe
→ 隐身
→ 主手 calcite
→ FMBE 变量/姿态播放
→ 刚体物理表达式在 playanimation 里求值
```

物理变量分两层：

```text
v.*   刚体状态
t.*   玩家拖拽目标
```

刚体状态包括：

```text
px/py/pz          中心位置
vx/vy/vz          线速度
wx/wy/wz          角速度
qw/qx/qy/qz       四元数
a1..a8            8 个角点
I                 近似惯量
gy                地面高度
e / mu            弹性 / 摩擦
dt / g            时间步 / 重力
extend_scale      尺寸
```

## 物理算法

### 1. 8 角点包围盒

用四元数旋转 8 个局部角点，得到世界角点：

```text
corner = center + q · (±hx, ±hy, ±hz)
```

地面碰撞取最低角点，计算穿透并修正：

```text
penetration = ground_y - min(corner.y)
center.y += penetration
```

### 2. 地面冲量

对每个角点计算相对速度，产生 `j1..j8` 冲量：

```text
v + ω × r
```

再把冲量分配到：

```text
vy
wx / wz
```

### 3. 玩家 AABB 碰撞

玩家盒：

```text
pbx1..pbx2
pby1..pby2
pbz1..pbz2
```

和刚体 AABB 做重叠，取最小重叠轴推出：

```text
amp / dir / dirz / ampy
```

### 4. 拖拽

玩家手持木棍：

```text
t.if_pull
t.px/t.py/t.pz
```

目标点在玩家视线前方 3 格；用弹簧增益 `pgain` 和最大速度 `pvmax` 把刚体拉过去。

### 5. 姿态输出

四元数积分后归一化，再转欧拉角：

```text
xrot / yrot / zrot
xpos / ypos / zpos
```

写回 FMBE。

## 逐条命令表

| # | 原文件行 | 命令 | 作用 |
|---:|---:|---|---|
| 1 | 2 | `tag @e[type=fox] add fmbe` | 所有狐狸加 `fmbe` 标签，作为载体 |
| 2 | 4 | `execute as ... tp @s ~~~~~` | 疑似自指/锚定；`~~~~~` 连写需真机确认 |
| 3 | 6 | `effect ... invisibility 1 1 true` | 每 tick 刷新隐身 |
| 4 | 8 | `replaceitem ... calcite` | 主手放 calcite，FMBE 渲染载体 |
| 5 | 10 | `playanimation ... sleeping ...` | 初始化 FMBE 13 变量 + 旋转矩阵 `F.*` |
| 6 | 12 | `playanimation ... creeper.swelling ...` | 设置 `F.s`/swelling scale |
| 7 | 14 | `playanimation ... ender_dragon.neck_head_movement ...` | 用 `F.*` 算头部位置/旋转 |
| 8 | 16 | `playanimation ... warden.move ...` | 用 `F.*` 算身体 X/Z 旋转 |
| 9 | 18 | `playanimation ... attack.rotations ...` | 用 `F.*` 算攻击体 Y 旋转 |
| 10 | 25 | `playanimation @a ... attack.positions ...` | 每玩家写 `t.*`：是否持棍、玩家位置、视线前 3 格目标 |
| 11 | 26 | `playanimation @e[tag=fmbe] ... attack.positions ...` | 刚体物理主表达式，653 个分号语句 |

### 第 5 条：FMBE 矩阵

不是动画，是利用 `playanimation` 表达式写变量：

```text
xpos/ypos/zpos/xrot/yrot/zrot
scale/extend_scale/extend_xrot/extend_yrot
xbasepos/ybasepos/zbasepos
F.r0..r8 / F.e0..e8 / F.p0..p8 / F.s
```

`F.*` 是欧拉角 + 扩展旋转的矩阵/中间量，供第 7–9 条计算头/身体/攻击朝向。

### 第 10 条：玩家目标

```text
if_pull = 主手是否木棍
px/py/pz = 玩家位置
tx/ty/tz = 玩家位置 + 视线方向 × 3
```

物理侧直接读 `t.*`。多人时要注意目标覆盖；所有 fox 共用同一套 `t.*`。

### 第 11 条：653 个语句的分段

| 语句范围 | 内容 |
|---:|---|
| 0–271 | `v.* = v.* ?? 默认值`，初始化刚体/碰撞/输出状态 |
| 272–339 | dt/scale/quaternion/重力/旋转矩阵/扩展轴/8 角点 |
| 340–410 | 地面间隙、8 角点冲量、弹跳、角速度 |
| 411–505 | 水平摩擦、接触面法线、静止/倾倒、角速度衰减 |
| 506–535 | 玩家拖拽：目标点、相对速度、弹簧冲量、松手 |
| 536–554 | 位置积分、穿透修正 |
| 555–592 | 玩家 AABB 重叠、最小轴推出、速度钳制 |
| 593–621 | 角速度/线速度限幅、四元数积分、归一化、输出位置 |
| 622–651 | 四元数转欧拉角、万向锁处理、角度连续化、输出旋转 |

**不是 653 行命令**，是一条 `playanimation` 表达式里的 653 个分号语句。

## 兼容性检查

| 项 | 结论 |
|---|---|
| 1.21.60 → 1.21.130 | 版本下限低于目标，通常可加载；仍需真机 |
| 行为包 / tick.json | 结构正确 |
| `calcite` | 1.21 有效 |
| `playanimation` 变量表达式 | 依赖 FMBE/网易表达式支持 |
| 17,971 字符单行 | **高风险**，需验证函数/命令长度 |
| `tp @s ~~~~~` | **疑似语法问题**，正常应带空格 |
| `@a` 写 `t.*` | 多人时目标可能被覆盖 |
| 所有 fox 共用 `fmbe` | 多物体共用同一个玩家目标 |
| 地面碰撞 | 只有水平地面，不是方块地形 |
| 清理/回收 | 未看到对象销毁逻辑 |

### 重点风险

1. **单行 17,971 字符**  
   如果目标版本或导入器限制函数行长度，会被截断/拒绝。

2. **`tp @s ~~~~~`**  
   这是 `tp @s` 后接五个连写 `~`，没有空格；需要真机确认解析，建议改成 `tp @s ~ ~ ~`。

3. **多人**  
   `playanimation @a ... setVariable` 写 `t.*`；多个玩家时，刚体读取的目标可能不是发起拖拽的玩家。

4. **多物体**  
   所有 fox 都是 `@e[tag=fmbe]`；同一个 `t.*` 目标会作用到全部刚体。

5. **地面/地形**  
   没有方块碰撞检测，只有 `gy` 平面和玩家盒；不能直接做台阶/斜坡/墙。

## 与本 skill 的集成

新增 [fmbe_physics.py](.dsh/skills/mcbe-command-blocks/scripts/fmbe_physics.py)：

```text
RigidBody
PhysicsWorld
8 corners
quaternion orientation
gravity
ground contact
player AABB push-out
spring pull
→ to_fmbe_vars()
```

示例：

[physics_demo.py](.dsh/skills/mcbe-command-blocks/examples/fmbe-physics/physics_demo.py)

```text
80 ticks
y 9.975 → 0.501
80 BDX 命令块
回读 80/80
```

这是**独立实现**，不是原包代码移植。

## 当前差异

| 原包 | 本 skill |
|---|---|
| 全量 8 角点冲量/角速度 | 8 角点 + 近似地面响应 |
| 玩家 AABB | 有 |
| 弹簧拖拽 | 有 |
| 四元数 | 有 |
| 方块地形碰撞 | 无 |
| 多玩家/多物体隔离 | 无 |
| 真机验证 | 无 |

## 建议

- 原包作为**参考实现**保留在仓库外；不要直接复制进公开 skill。
- 需要真机验证：函数行长度、`tp` 语法、网易表达式支持、多人目标。
- 要产品化，先把 `t.*` 改为**按玩家/按物体隔离**，再加方块碰撞。
