# 28 · Arch compiler：建筑 → BDX / 预览 / 回读

## 链路

```text
build_*.py (ArchBuilder / ArchSpec)
  → arch_compile.py
  → voxels + .bdx
  → arch_preview.py  (front / top / iso)
  → arch_readback.py (BDX 解码)
  → report.json (count/bounds/issues)
```

## 已实现

```text
scripts/arch_compile.py   ArchBuilder / Palette / BDX
scripts/arch_preview.py   front/top/iso
scripts/arch_readback.py  BDX 普通方块解码
scripts/arch_pipeline.py  一条龙
scripts/arch_spec.py      631/质心/层数/材质比
```

ArchBuilder 当前模块（基础原语 + 组件库见 `35-architecture-components.md`）：

```text
site / walls / floor / crenellate / buttress
lancet_x / lancet_z / rose_z
gable_roof_x / gable_roof_z / spire / pinnacle / tower
```

## 试运行

`examples/arch-chapel/`：60×80×73 哥特小礼拜堂。

```text
voxels        29,807
BDX blocks    29,807
bounds        0,0,0 → 60,73,80
issues        []
```

产物：

- `examples/arch-chapel/out/building.bdx`
- `examples/arch-chapel/out/building-front.png`
- `examples/arch-chapel/out/building-top.png`
- `examples/arch-chapel/out/building-iso.png`
- `examples/arch-chapel/out/report.json`

## 命令

```bash
python3 scripts/arch_pipeline.py \
  --builder examples/arch-chapel/build_chapel.py \
  --outdir examples/arch-chapel/out \
  --start 900,0,900
```
