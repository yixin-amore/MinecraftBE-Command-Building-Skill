# 34 · FMBE 编译器：IR → 校验 → 命令 → BDX

## 链路

```text
FmbeModel / FmbeAnimation
→ FmbeModel.validate()
→ pose / setup / frame commands
→ BDX command blocks
→ bdx_read 回读
```

## 入口

```bash
python3 scripts/fmbe_compile.py model.json \
  --out out/fmbe.bdx \
  --frames-out out/frames.json
```

产物：

- `out/fmbe.bdx`：部件 repeat 块 + 载体 setup 链
- `out/frames.json`：动画关键帧命令
- 终端 JSON：validation / 命令数 / 回读计数

## IR

```python
FmbeModel(
  name="boss",
  blocks=[FmbeBlock(id, name, item, offset, vars)],
  animations=[FmbeAnimation(block_id, duration, keyframes)],
  groups=[FmbeBoneGroup(id, members)],
  export=FmbeExport(prefix, suffix),
  carrier=FmbeCarrier(enabled, entity, display_score),
  origin=(x,y,z),
)
```

`vars` 只接受 13 个 FMBE 变量：

```text
xpos/ypos/zpos
xrot/yrot/zrot
scale
extend_scale
extend_xrot/extend_yrot
xbasepos/ybasepos/zbasepos
```

不接受 `rotatex/rotatey/rotatez`（AIEX-FMBE 这一代没有）。

## 校验

`FmbeModel.validate()` 检查：

- block id 唯一
- 变量名合法、值为有限数
- `scale` / `extend_scale` > 0
- 8 顶点有限（矩阵可算）
- 部件 offset 不重叠（BDX 命令方块不能叠）
- 动画 block 存在
- keyframe tick 在 `0..duration`，不重复、有序
- bone group 成员存在

有 issue 时 `compile_model` 拒绝生成。

## Lowering

- **pose command**：每个部件一条 `playanimation`，13 变量串来自 `FmbeExport.command()`。
- **setup chain**：`summon fox` → `replaceitem` → `scoreboard` → `effect invisibility/resistance`。
- **frame command**：动画 keyframe 合并到 block 基础 vars，生成对应 `playanimation`。
- **BDX**：
  - 每个部件一个 `repeat` 命令方块，位置 = `origin + offset`；
  - setup 链放在 `origin.z - 4`，第一块 impulse，后续 chain；
  - 无命令方块接触/重叠。

## 回读

```bash
python3 scripts/bdx_read.py out/fmbe.bdx --json out/readback.json
```

回读检查：

```text
command_blocks 数 = parts + setup
command 文本 / mode / conditional / needs_redstone / facing
```

## 动画与分组

### 关键帧插值

`FmbeAnimation` 支持（`group_id` 可选，和 `block_id` 二选一）：

```text
block_id 或 group_id    目标
interp = linear | step
step   = 1..N（每 N tick 采样一次）
```

按每个变量独立插值：

```text
keyframe 中出现的变量 → 在相邻关键帧间插值
未出现的变量         → 用 block 的基础 vars
```

示例：

```text
tick 0  yrot=0
tick 10 yrot=90
tick 5  → yrot=45
```

### 时间轴命令链

每个动画编译成一条独立时间轴：

```text
frame tick 0 → impulse 触发块
frame tick n → chain 块，delay = n - 上一帧
同一 tick 多部件 → delay 0，顺序执行
```

命令使用绝对部件位置：

```text
execute positioned <part x y z> run <原始 FMBE 前缀>
```

因此时间轴命令块可以放在模型外，不会把目标带偏。

BDX 中：

```text
timeline 链放在 origin.z - 10 - 2*index
```

第一块是 impulse + Needs Redstone；其余是 chain。

### 分组动画

`FmbeAnimation.group_id` 会展开：

```text
group 自身 members
+ 所有 parent 指向它的子 group（递归）
```

例如 `body` 包含 `base`，`head_group` 的 parent 是 `body`；

动画 `group_id=body` 会同时驱动 `base` + `head`。

`group_switches` 会输出每个分组动画的成员列表，供外部触发/切换选择。

当前是**独立时间轴选择**，不是运行时权重混合。

### FK / BoneGroup

`FmbeBoneGroup` 支持：

```text
parent
offset
rotation（x/y/z 度）
```

`FmbeModel.resolve_offset()` 从叶到根累加：

```text
block offset
→ 子 group 的 rotation / offset
→ 父 group 的 rotation / offset
```

编译、setup、pose、timeline 都使用解析后的绝对位置。

这是**层级偏移/旋转（basic FK）**，不是每帧骨骼旋转动画；

逐帧 group 变换仍需要后续的 `FmbeBoneAnimation`。

## 当前边界

- 时间轴是**单次播放**；`loop=True` 只保留元数据，没有自动循环调度。
- 分组切换是**分数选择 + 独立时间轴**，没有运行时混合/过渡。
- FK 是层级静态偏移/旋转，不是逐帧骨骼动画。
- 载体生命周期只覆盖 spawn/replaceitem/score/隐身/抗性。
