# BDX / MCWorld 生成样例

- `demo.bdx`：3 个命令方块（repeat + 2 chain），由 `scripts/bdxgen.py --spec demo.json demo.bdx` 生成。
- `demo.mcworld`：同一结构转成的可导入世界（flat，命令方块在 `0 64 0`）。
- `demo-extracted.json`：用 BDX 解析器回读的结果，用于验证。
- `demo.json`：方块表（BDX 使用本地坐标；转 MCWorld 时用起始 y=64）。

## 重新生成

```bash
python3 ../../scripts/bdxgen.py --spec demo.json demo.bdx
```

## 转 MCWorld

在参考实现仓库中：

```bash
go run ./cmd/bdx2mcworld demo.bdx demo.mcworld 0 64 0
```

## 验证

- BDX 回读：3 个 command block，`0/1/2 64 0`，mode repeat/chain/chain。
- MCWorld 回读：chunk 存在，NBT 3 条，`id=CommandBlock`，命令与 BDX 一致。
