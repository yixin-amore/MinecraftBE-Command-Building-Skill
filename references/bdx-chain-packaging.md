# BDX 命令链打包：盘旋布局与初始化分离

## 1. 单区块盘旋

- 一个区块 = 16×16 水平格。
- 一条链按行蛇形：
  - 第 0 行：x=1..15（给红石留 x=0）
  - 第 1 行：x=15..0
  - 第 2 行：x=0..15
  - 行尾向下折；最后一格 `facing=south` 接下一行。
- 不同链放不同垂直层（例如 y0 初始化、y1 持续链、y2 主体），避免链与链相邻误触发。
- 示例：`16×3×9` 的 BDX，354~369 个命令方块，全部在 x64..79 / z0..8。

## 2. 初始化与持续逻辑必须分离

| 链 | 类型 | 放什么 | 不放什么 |
|---|---|---|---|
| 一次性初始化 | impulse + chain | 计分板、tickingarea、生成实体/部件、物品/效果 | 持续 `playanimation` |
| FMBE 前置 | repeat + chain | 8 条 `playanimation`、部件 `tp` 锚定 | 生成实体/初始化 |
| 主体 | repeat + chain | 状态机、技能、UI、重置 | 初始化/FMBE 生成 |

- FMBE 的 `playanimation` 是**持续前置**，独立 repeat 链持续执行。
- 生成生物/部件是**一次性事件**，只放 impulse 链。
- 混链的后果：初始化链过长/断裂导致模型缺件；循环链每 tick 重复 spawn；变量/计分板被重复复位。

## 3. 红石触发

- `(x0,y0,z0)` 放红石块。
- impulse 头放 `(x1,y0,z0)`，`Needs Redstone=true`。
- 主体 repeat 第一条：

```mcfunction
execute if score <init> matches 0 run setblock <x0> <y0> <z0> redstone_block
```

- 初始化链末尾把 `<init>` 设为 1，防止重复触发。

## 4. FMBE 部件

- 一部件一只 fox；主手物品；隐身/抗性/缓慢。
- tag 体积必须独占：`0.4×0.4×0.4`，不要用 `r=0.6` 让头/眼/肩甲重叠。
- 每轮 `tp` 锚定所有部件；`slowness 255` 不阻止重力/挤压，不锚定会散架。
- 位置单位是 **1/16 格**；`v.xpos=1` 是 1/16 格，不是 1 格。
- 8 条 `playanimation` 顺序不能乱；第一条控制器 `controller.animation.fox.move`。
- 只摆坐标不写 `v.xpos/ypos/zpos/xrot/yrot/zrot` 等于散件。

## 5. 交付与验证

- 交付：BDX + StartPos + 单区块 tickingarea + 依赖场景说明。
- 回读：检查 `Width/Height/Length`、block 类型数量、每个 head 的坐标/朝向/命令。
- 一条链只有一个头；无孤立 chain；不同层不互相指向。
- 服务器只做一次导入验收；不边调边交付。

## 6. 验收清单

- [ ] 全部命令方块在一个 16×16 区块内
- [ ] 初始化链是 impulse，不是 repeat
- [ ] FMBE `playanimation` 在独立 repeat 链
- [ ] 生成实体/部件只在 impulse 链
- [ ] 红石块由主体首条命令放置
- [ ] 部件 tag 独占、每轮锚定、姿态/位移完整
- [ ] 交付文件自包含，不依赖手动 spawn
