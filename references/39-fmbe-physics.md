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
