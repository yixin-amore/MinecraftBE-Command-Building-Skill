# 建筑 → BDX

```bash
python3 ../../scripts/buildgen.py plan.json build.bdx
```

- `build.bdx`：普通方块 + 命令方块的完整 BDX。
- 同一个 `plan.json` 也可以拆成命令方块链用 `bdxgen.py` 输出。

## plan 字段

| 字段 | 说明 |
|---|---|
| `fills` | `from` / `to` / `block`，可加 `data` / `states` |
| `blocks` | 单方块 `pos` / `block` |
| `commands` | 命令方块 `pos` / `type` / `command` |

坐标是绝对世界坐标；大建筑请拆 plan，避免超过 2,000,000 方块。
