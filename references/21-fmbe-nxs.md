# FMBE / NXS 领域层（我们的补充）

mct 的强项是命令 / 计分板 / 链布局，不是 FMBE 模型，也不是 NXS 接口。
这两层不能靠普通命令 DSL 猜。

## FMBE 应该进入类型系统

```text
FMBEModel
  carrier: zombie / armor_stand ...
  parts: Part(name, item, offset, scale, bind_to=carrier)
  animations: idle / cast
  hit_core: carrier + helmet event
  scheduler: per-tick bind + pose
```

编译器应该校验：

- 14 个部件是否有唯一 name / item / offset
- 每个部件是否都有 bind 命令
- carrier 是否存在，是否只召唤一只
- idle / cast 是否覆盖所有部件
- cleanup 是否会摘 tag / 清实体

这正好对应我们 Frostcrown 的「散架」问题：偏移和绑定是结构，不是字符串。

## NXS

`binaryTree2D.txt` / `binaryTree3D.txt` 就是 NXS 样本（作者 NeilGreentot）。
它不是 FMBE：NXS 是 execute 坐标架/旋转递归画几何；详见 `references/23-nxs.md`。

FMBE 的 13 变量/矩阵/导出细节见 `references/24-fmbe-model-ir.md`；NXS 已泛化为点阵 + CSG 的 `NxsRaster`，细节见 `references/23-nxs.md` §5。

- 锚点实体（`name=tree`）/初始朝向
- 递归角度序列、镜像、跟随目标
- `rotated`/`positioned`/`facing` 的顺序
- 最终 particle 名称
