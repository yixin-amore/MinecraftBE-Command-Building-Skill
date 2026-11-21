# 27 · 建筑 DSL：从 mc-ai-builder 提炼什么

> 参考仓库：`Justcnds/mc-ai-builder`（GPL-3.0）
> 本文只提炼架构与做法，不复制其代码；若要把代码并入本 skill，必须先处理 GPL 兼容性。

## 1. 它做对了什么

它不是“让 AI 直接摆方块”，而是：

```text
自然语言
→ AI 写 JavaScript builder 脚本
→ sandbox 执行
→ voxels
→ 3D 预览 / 导出
```

核心资产：

| 层 | 内容 |
|---|---|
| 语义材质 | `WALL_STONE` / `WALL_DEEP_SLATE` / `ROOF_RED` / `WINDOW` … |
| 风格调色板 | `STYLES`：每类材质 3–6 个候选 + `random/noise/gradient_y/checkerboard` |
| Builder API | `set/fill/walls/line/clear` + `drawRoofBounds/drawPolyRoof/drawSphere/drawCylinder/drawEllipsoid/drawPyramid/drawBezier` |
| 优先级 | `100 openings > 95 frame > 70 window > 60 roof > 50 walls > 20 interior > 0 floor` |
| 风格知识 | `STYLE_KNOWLEDGE`：哥特/日式/中式/中世纪/载具/雕像/自然 |
| 导出 | WorldEdit / Litematica / Axiom / datapack / single command |
| 预览 | three.js 实时体素预览 |

这套东西证明了：**建筑也可以“语言优先”**，而不是让模型逐块写坐标。

## 2. 它缺什么

1. **只有“程序”，没有“构图约束”**
   - 没有 631、黄金比例、视觉重量、焦点预算。
   - AI 可以写出很细的 builder 脚本，但体量关系仍可能是火柴盒。

2. **语义层没有校验**
   - `STYLES` 里有拼写/无效方块（例如错字、旧 ID）。
   - 没有“这条语义材质在当前版本是否存在”的 gate。

3. **没有建筑级 validator**
   - 没有质心、立面层数、开间节奏、轮廓、材质比、方块数预算。
   - 只有执行成功，没有“设计是否成立”。

4. **AI 直接写 JS**
   - 灵活，但不可控；同样的提示可能生成完全不同的结构。
   - 没有 typed module / 可复用构件。

5. **GPL-3.0**
   - 代码不能随手复制进本 skill；只能提炼思想，或做 GPL 兼容处理。

## 3. 我们应该搭的 ArchSpec

```text
ArchSpec（声明式）
  → BuilderOps（语义操作）
  → Resolver（语义类型 + 风格材质 + 确定性纹理）
  → Voxel/BDX
  → Preview + Constraint Report
```

### 3.1 ArchSpec

```python
ArchSpec(
  site=Site(width=180, depth=100),
  masses=[
    Mass("wings", weight=0.60, height=38),
    Mass("center", weight=0.30, height=55),
    Mass("crown", weight=0.10, height=113),
  ],
  golden=[0.382, 0.618, 0.90],
  facade=Facade(bays=8, layers=["back", "recess", "project", "silhouette"]),
  courtyards=[Courtyard(28, 28, cloister=True)],
  palette=Palette(light=0.60, mid=0.30, accent=0.10),
  focal=["dome", "rose", "pinnacle"],
)
```

### 3.2 BuilderOps

不是 `builder.set` 散落，而是**语义操作**：

```text
Wall(axis, from, to, material_role)
Bay(index, width, depth_layers)
Arcade(bays, arch_height)
Roof(kind, pitch, ridge)
Tower(plan, height, spire)
Courtyard(w,d,cloister)
Pinnacle(at, height)
```

### 3.3 Resolver

```text
WALL_STONE + Style("gothic") → stone_bricks / tuff / polished_andesite
ROOF_DARK + Style("gothic") → deepslate_tiles / blackstone
WINDOW + focal=true → blue/purple stained glass + tracery
```

确定性纹理：

```text
gradient_y / noise / checkerboard / stripes
不用 Math.random；坐标哈希，重跑一致
```

### 3.4 校验器

- 631 体量比
- 黄金控制线
- 质心偏离中轴
- 立面层数 ≥ 4
- 10% 焦点区细节密度
- 材质比 60/30/10
- 轮廓 45° 读图
- 方块数 / 区块数

## 4. 和 mct 的关系

| | mct | ArchDSL |
|---|---|---|
| 输入 | 行为/技能需求 | 空间/体量/立面 |
| IR | 命令链 spec | 建筑模块 spec |
| 编译器 | `cbc.py` 链布局 | `arch_compile.py` 体素化 |
| 校验 | 语法/链/条件 | 比例/重心/进深/材质 |
| 输出 | `.mcstructure` | BDX / `.mcstructure` |

两者共享同一个哲学：

```text
自然语言 → 结构化 spec → 编译器 → 产物 → 校验
```

但**不能共用同一个编译器**。
