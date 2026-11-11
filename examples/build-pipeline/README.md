# 建筑 → BDX / MCWorld

```bash
python3 ../../scripts/buildgen.py plan.json build.bdx
python3 ../../scripts/mcworldgen.py plan.json build.mcworld
```

- `build.bdx`：完整方块 + 1 个命令方块，任意 BDX 导入器可读。
- `build.mcworld`：打开世界后，behavior pack 的首次 tick function 执行建造。
- 同一个 `plan.json` 驱动两边。

`plan.json` 字段：

| 字段 | 说明 |
|---|---|
| `fills` | `from` / `to` / `block`，可加 `data` 或 `states` |
| `blocks` | 单方块 `pos` / `block` |
| `commands` | 命令方块 `pos` / `type` / `command` |

坐标是绝对世界坐标；MCWorld 模板是平坦世界，y=64 附近可直接用。
