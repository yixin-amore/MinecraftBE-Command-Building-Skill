# 范例：开关灯（toggle-lamp）

**教什么**：T 翻转、`%=` 取模、并行的 unconditional 分支、方块坐标与朝向。

## 行为契约

| 项目 | 内容 |
|---|---|
| 触发 | 按钮（Impulse + Needs Redstone） |
| 状态 | `#state` 0=关 1=开 |
| 输出 | `10 65 10` 放/移除红石块；`10 66 10` 是红石灯 |
| 结束 | 每次按下在开/关之间切换 |

## 状态表

| 变量 | 归属 | 含义 | 初值 |
|---|---|---|---|
| `#state` | 全局 | 0=off 1=on | 0 |
| `#two` | 全局 | 常量 2 | 2 |

## 链

```
button (impulse) → wrap (chain, conditional) → on (chain, unconditional) → off (chain, unconditional) → click (chain, unconditional)
```

## 坐标与朝向

| 方块 | 坐标 | 朝向 | 设置 |
|---|---|---|---|
| `button` | `10 64 10` | east | Impulse / Unconditional / Needs Redstone / Delay 0 |
| `wrap` | `11 64 10` | east | Chain / Conditional / Always Active / Delay 0 |
| `on` | `12 64 10` | east | Chain / Unconditional / Always Active / Delay 0 |
| `off` | `13 64 10` | east | Chain / Unconditional / Always Active / Delay 0 |
| `click` | `14 64 10` | east | Chain / Unconditional / Always Active / Delay 0 |
| 红石块 | `10 65 10` | — | 由 `on`/`off` 放/移除 |
| 红石灯 | `10 66 10` | — | 被红石块点亮 |

> 所有命令方块朝东（+X），`button` 的按钮贴在它西侧或上方均可；只要红石信号能激活它。

## 关键设计

### 1. 取模翻转

```mcfunction
scoreboard players add #state lamp 1
scoreboard players operation #state lamp %= #two lamp
```

- 0 → 1 → 0 → 1 …
- `%=` 是正余数；`#state` 不会变成 2。
- `#two` 必须初始化；除数为 0 时基岩版不改变目标值（会卡住）。

### 2. 两个输出块都是 unconditional

`on` 的命令在 `#state=0` 时失败（`execute if` 不成立），但它仍然会触发 `off`。
如果 `off` 设成 Conditional，它会检查 `on` 的失败并跳过，灯就关不掉。
所以两个输出块都设 Unconditional，各自用 `execute if` 判断。

### 3. 为什么不直接 `setblock` 到灯的位置

红石灯需要被红石块/充能方块激活。`10 65 10` 的红石块与 `10 66 10` 的灯相邻，灯会亮。
移除红石块后灯灭。这样不用改灯本身。

## 搭建步骤

1. 运行初始化（见 `plan.md`）。
2. 在 `10 64 10` 放 Impulse 命令方块，朝东，Needs Redstone，接按钮。
3. 在 `11..14 64 10` 放 Chain 命令方块，全部朝东。
4. 设置：
   - `11`：Conditional
   - `12`、`13`、`14`：Unconditional
5. 在 `10 65 10` 放一个红石块（初始为开或关都行），在 `10 66 10` 放红石灯。
6. 按按钮测试；如果初始灯状态和 `#state` 不一致，按一次或手动 `setblock` 同步。

## 测试

- [ ] 按一次：红石块出现，灯亮。
- [ ] 再按一次：红石块消失，灯灭。
- [ ] 连按 10 次：状态正确交替，不出现 2 或 -1。
- [ ] 退出重进：`#state` 保留，下一次按仍能切换。
- [ ] 手动把 `10 65 10` 改成空气：下一次按会切到“开”，灯亮（状态以分数为准）。

## 变体

- **三态开关**：`%= 3`，加 `#three`，三个输出块。
- **门**：把 `setblock` 改成 `fill` 门框区域为空气/铁块。
- **每玩家独立开关**：把 `#state` 换成 `@s.state`，用 `execute as @a` 处理。

## 生成构建表

```bash
python3 ../../scripts/chain_lint.py spec.json --format markdown
```

见同目录 `plan.md`。
