# 24 · FMBE 建模器逆向：方块模型 / 矩阵 / 导出 / 动画

> 来源：`AICB`、`AIEX-FMBE 2.05.1`、`AIEX 2.0.5` 的本地 APK 资源（仅本地研究，不复制代码/不二次分发）。
> 结论：**帮助很大**。它把 FMBE 从“狐狸 + playanimation 黑盒”变成了可计算的方块模型。

## 1. 模型不是“实体部件”，是带 4x4 矩阵的方块

基础几何是 **1×1×1 立方体**，8 个局部顶点：

```text
LBB(-.5,-.5,-.5) RBB(.5,-.5,-.5) LTB(-.5,.5,-.5) RTB(.5,.5,-.5)
LBF(-.5,-.5,.5)  RBF(.5,-.5,.5)  LTF(-.5,.5,.5)  RTF(.5,.5,.5)
```

每个方块有 13 个真实变量：

```text
v.xpos/v.ypos/v.zpos
v.xrot/v.yrot/v.zrot
v.scale
v.extend_scale
v.extend_xrot/v.extend_yrot
v.xbasepos/v.ybasepos/v.zbasepos
```

**不存在** `v.rotatex/rotatey/rotatez`（AIEX-FMBE 这版）。AIEX2 的新版工具另有 `rotatex/y/z`，是另一代口径，不能混。

## 2. 变换顺序（关键）

按应用顺序：

```text
T(base)
→ ScaleY(extend_scale)
→ RotY(-extend_yrot)
→ RotX(-extend_xrot)
→ ScaleZ(extend_scale)
→ RotX(extend_xrot)
→ RotY(extend_yrot)
→ Scale(scale)
→ RotZ(-zrot)
→ RotX(xrot)
→ RotY(-yrot)
→ T(pos)
```

含义：

- `pos` 是最终枢轴/平移，**会移动旋转中心**。
- `basepos` 是局部基准偏移，**不会移动旋转中心**，会先被后续旋转/缩放影响。
- `extend_scale` 同时影响 Y/Z；不是单独拉 Y。
- `extend_xrot` 在 YZ 截面重分配延展；`extend_yrot` 在 XZ 截面重分配。
- XZ 拉伸是绑定的，不能只拉 X 或只拉 Z；复杂形状用多个长方体拼接。

## 3. 8 顶点 / 6 面

```text
back  = LBB,RBB,RTB,LTB
front = LBF,RBF,RTF,LTF
left  = LBB,LBF,LTF,LTB
right = RBB,RBF,RTF,RTB
bottom= LBB,RBB,RBF,LBF
top   = LTB,RTB,RTF,LTF
```

校验时不要只看变量名：用 `matrix4Rows` 和 8 顶点判断是否斜切/拉伸/朝向正确。

## 4. 建模器的 AI 协议

`AIEX-FMBE` 的 phase：

```text
initial: {operations:[...], thought:"..."}
review:  {done:true, reason:"..."} 或继续修正 operations
```

operation：

```json
{"op":"add|update|delete","id":"...","block":{"id":"...","name":"...","command":"...","materialColor":"...","vars":[{"name":"v.xpos","expr":"1"}]}}
```

review 会回传每个方块的 `matrix4Rows` + 8 个世界顶点 + `faceQuads`。这就是我们缺的**几何自检闭环**。

## 5. 导出格式

默认前缀：

```text
execute positioned ~-1.5~~-0.5 run playanimation @e[x=~,z=~,y=~,dx=1,dy=0,dz=0] animation.player.attack.positions _ 0
```

默认后缀：

```text
"{command}" {id}
```

`command` = 该方块所有 `v.*=expr;`，以及绑定到该方块的 `t.*=expr;`。

所以一个方块导出为：

```text
<prefix> "v.xpos=3; v.ypos=1; ...;" <blockName>
```

这是 AIEX-FMBE 的**静态/关键帧导出**；AIEX2 另有 `set_animation_keyframe` / `get_animation_frame` / `create_bone_group` / `compute_fk_chain`，支持时间轴和骨骼链。

## 6. 我们该建的 IR

```text
FmbeBlock(id, name, command, vars, material)
FmbeModel(blocks, globalVars)
FmbeAnimation(blockId, duration, keyframes)
FmbeBoneGroup(id, memberIds)
FmbeExport(prefix, suffix)
```

编译期检查：

- 13 个变量是否在允许集合；拒绝 `rotatex/rotatey/rotatez`（AIEX-FMBE 版）
- 8 顶点是否落在预期 AABB / 关节是否脱节
- `extend_*` 是否真的需要，能否用多个方块替代
- 动画关键帧时间单调、同一时间不重复
- `playanimation` 前缀/后缀、block name
- 导出命令走 CHelper 语法

## 7. 安全提醒

`AIEX-FMBE` 的 web 资源里发现**硬编码的第三方 API Key**（不在此记录明文）。
建议：立即吊销/轮换；不要把 APK/解包资源二次分发；不要在任何示例里保留该 Key。

## 8. 与 NXS 的分工

| | FMBE | NXS |
|---|---|---|
| 本质 | 方块矩阵模型 | execute 坐标架递归 |
| 导出 | `playanimation` 变量串 | 粒子/几何命令 |
| 自检 | 8 顶点/矩阵 | 递归坐标架/射线 |
| 用途 | Boss、武器、展示体 | 法阵、轨道、线框 |

两者可以组合：NXS 画法阵，FMBE 放主体。
