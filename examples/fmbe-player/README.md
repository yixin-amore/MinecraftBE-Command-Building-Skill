# FMBE 1:1 Player（6 部件）

用 6 只 FMBE 狐狸拼出的 1:1 方块玩家：头 + 身体 + 双臂 + 双腿，整体约 **1.0 格宽 × 2.0 格高**。

![设计预览](player-model-preview.png)

> 预览图是设计示意，不是游戏截图。实际外观以进服为准。

## 服务器部署

- 展示坐标：`70 2 8`
- 底座：`67 1 5` ~ `73 1 11` 的平滑石平台
- 命令方块：`64 210 0` 起，紧凑蛇形，86 个方块；无 tickingarea
- 服务器：28890143

## 六个部件

| 部件 | 实体 tag | 物品 | 缩放 |
|---|---|---|---|
| 头 | `pm_head` | `player_head`（`skull 3`） | 0.5 格 |
| 身体 | `pm_body` | `cyan_concrete` | 0.5 × 0.75 |
| 左臂 | `pm_arm_l` | `light_gray_concrete` | 0.25 × 0.75 |
| 右臂 | `pm_arm_r` | `light_gray_concrete` | 0.25 × 0.75 |
| 左腿 | `pm_leg_l` | `blue_concrete` | 0.25 × 0.75 |
| 右腿 | `pm_leg_r` | `blue_concrete` | 0.25 × 0.75 |

## 初始化 / 重置

```mcfunction
scoreboard players set pm_init pm 0
scoreboard players set pm_render pm 0
kill @e[tag=pm_model]
```

初始化链会清掉展示区狐狸、重新召唤 6 只、给物品/隐身/抗性/缓慢、锚定到 `70 2 8`，然后渲染链跑一遍 FMBE 8 条命令。

- 渲染链：1 Hz 刷新，避免 20 Hz 的 48 条 Molang 命令造成卡顿。
- 锚定链：每 tick `tp @e[tag=pm_model] 70 2 8 0 0`，防止狐狸走散。
- 想改位置：同时改初始化/锚定/`v` 偏移；只改坐标会让部件错位。

## 已知限制

- FMBE 是**客户端视觉**，服务端只能验证狐狸/物品/tag；无头 bot 不能截图。
- 头用 `player_head`，身体/四肢用混凝土；不是皮肤级 1:1，而是 6 个方块部件。
- 如果模型漂浮/下沉，调 `v.ypos`（1/16 格）；如果前后偏移，调 `v.zpos`（当前 -8）。
- 狐狸仍会被玩家推挤，锚定链每 tick 拉回。
