# 命令方块 BDX 最小样例

- `demo.bdx`：3 个命令方块（repeat + chain + chain），由 `scripts/bdxgen.py --spec demo.json demo.bdx` 生成。
- `demo.json`：命令方块表（BDX 本地坐标）。

## 重新生成

```bash
python3 ../../scripts/bdxgen.py --spec demo.json demo.bdx
```

## 验证

- BDX 回读：3 个 command block，坐标 `0/1/2, 64, 0`，mode repeat/chain/chain。
- 手头没有 BDX 读取器时，至少检查文件头是 `BD@`，且 `demo.bdx` 能被导入器打开。
- 本目录不再包含 MCWorld；技能只输出 BDX。
