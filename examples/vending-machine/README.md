# 范例：自动售货机（vending-machine）

**教什么**：条件流水线（all-or-nothing）、纯条件门、`hasitem`、`clear`、`c=1`、无条件清理。

## 行为契约

| 项目 | 内容 |
|---|---|
| 触发 | 按钮（Impulse + Needs Redstone） |
| 输入 | 4 格内最近的、至少持有 1 个绿宝石的玩家 |
| 事务 | 库存 > 0 → 扣 1 绿宝石 → 给 1 个面包 → 库存 -1 → 播放音效 |
| 失败 | 任一条件不满足：不扣钱、不发货、清标记 |
| 结束 | 动作栏显示“Sold out”（库存为 0 时） |

## 状态表

| 变量 | 归属 | 含义 | 初值 |
|---|---|---|---|
| `fb_stock` | 全局 | 剩余库存 | 10 |
| `@s.shop` | 每玩家 | 本次购买标记 0/1 | 0 |

## 链

```
buy_btn (impulse)
 └─ stock_gate (conditional)   execute if fb_stock >= 1
     └─ take (conditional)    clear @s emerald 0 1
         └─ give (conditional) give @s bread 1
             └─ stock (conditional) fb_stock -= 1
                 └─ fx (conditional) playsound random.orb @s
                     └─ cleanup (unconditional) @a shop = 0
                         └─ sold_out (unconditional) if fb_stock == 0 → actionbar
```

## 关键设计

### 1. 为什么先查库存再扣钱

顺序是 `stock_gate` → `take`。如果先 `clear` 再查库存，库存不足时玩家的绿宝石已经没了。

### 2. 为什么 `take` / `give` 是 conditional

条件链的含义：当前块只在上一个块成功时才执行。

- `stock_gate` 失败 → `take` 跳过 → 后面的 conditional 全部跳过。
- `take` 失败（玩家没有绿宝石）→ `give` 跳过，不会“没付钱就发货”。
- 库存扣减放在 `give` 之后、音效之前，避免音效失败导致库存不扣。

### 3. 为什么 `cleanup` 是 unconditional

不管事务成功还是失败，都要把 `@s.shop` 清 0，否则下一轮会用到上一轮的标记。
`cleanup` 和 `sold_out` 放在链尾且设为 Unconditional，保证失败路径也会执行。

### 4. 为什么 `c=1`

一次按钮只服务最近的 1 名玩家。否则 3 名玩家同时买，库存只减 1，但发了 3 份货。
如果要支持多人同时购买，需要按人数预扣库存（用计分板逐个 `remove`），复杂度会上升。

### 5. `buy_btn` 失败也没关系

`execute as @a[r=4,hasitem=...]` 如果没选中任何人，命令失败；后面的 conditional 会依次跳过，`cleanup`/`sold_out` 仍然执行。这是预期行为。

## 搭建步骤

1. 运行初始化（见 `plan.md`）。
2. 放 `buy_btn`：Impulse，Needs Redstone，Delay 0，接按钮。
3. 在它面前依次放 `stock_gate`、`take`、`give`、`stock`、`fx`、`cleanup`、`sold_out`，全部 Chain，朝同一方向：
   - `stock_gate`..`fx`：Conditional
   - `cleanup`、`sold_out`：Unconditional
4. 单独放 `restock_btn`：Impulse，Needs Redstone；后面接 `restock_msg`（Conditional）。
5. 在售货机旁放一个按钮/拉杆作为购买入口，另一个作为补货入口。
6. 可选：在机器旁放一个告示牌/悬浮文本写价格。

## 测试

- [ ] 有 1 个绿宝石：扣 1 个，得到 1 个面包，库存 10 → 9。
- [ ] 没有绿宝石：什么都不发生，库存不变。
- [ ] 库存 0：不扣钱、不发货，显示 Sold out。
- [ ] 两名玩家靠近：一次按钮只服务最近的一名。
- [ ] 按下按钮后立刻把绿宝石丢出：`clear` 应失败，面包不应发出。
- [ ] 补货：库存回 10，动作栏提示。

## 变体

- **多种商品**：把 `give @s bread 1` 换成 `give @s <item>`，价格用不同物品/数量；或者用 `fb_price` 分数 + 多个 `clear` 分支。
- **每人限购**：加 `@s.bought` 计数和上限判断。
- **无限库存**：删掉 `stock`/`sold_out`，把 `stock_gate` 改成 `execute if entity @a[...]`。
- **用钻石计价**：把 `emerald` 换成 `diamond`，`clear @s diamond 0 1`。

## 生成构建表

```bash
python3 ../../scripts/chain_lint.py spec.json --format markdown
```

见同目录 `plan.md`。
