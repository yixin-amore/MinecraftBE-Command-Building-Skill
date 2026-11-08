# 范例：竞技场倒计时（arena-countdown）

**教什么**：`repeat` 秒时钟、计分板状态机、条件门、无条件分支、脉冲标记（`#second`）。

## 行为契约

| 项目 | 内容 |
|---|---|
| 触发 | 开始按钮（Impulse + Needs Redstone） |
| 起始状态 | `#state=0`（idle） |
| 过程 | 每秒一次：显示 3 → 2 → 1 → GO |
| 结束状态 | `#state=2`（running），`#count=0` |
| 重置 | 重置按钮：`#state=0`，清标题 |

## 状态表

| 变量 | 归属 | 含义 | 初值 |
|---|---|---|---|
| `#state` | 全局 | 0=idle 1=counting 2=running | 0 |
| `#count` | 全局 | 剩余秒数 | 0 |
| `#tick` | 全局 | 当前秒内 tick 计数 0..20 | 0 |
| `#second` | 全局 | 本 tick 是否是“整秒” | 0 |

## 三条链

```
clock (repeat, always active, delay 0)
 └─ tick_wrap (chain, conditional)
     └─ pulse (chain, conditional)      ← 只有整秒才走到这里
         └─ show3 / show2 / show1 / go / start_running / count_down (unconditional)
             └─ clear_pulse (unconditional)

start_btn (impulse, needs redstone) → start_count → start_tick → start_title
reset_btn (impulse, needs redstone) → reset_count → reset_tick → reset_title
```

## 关键设计

### 1. 为什么 `tick_wrap` 是 conditional

`clock` 每 tick 给 `#tick` +1；`tick_wrap` 的命令只在 `#tick >= 20` 时成功。
它成功时才把 `#second` 置 1，后面的显示块才有事可做。

### 2. 为什么显示块是 unconditional

如果显示块也设 conditional，`show3` 在 `#count≠3` 时会失败，导致后面的 `show2`、`show1`、`go` 全部跳过。
所以显示块全部 `unconditional`，用 `execute if score #second arena matches 1 ...` 自己判断。
这样每个块只对自己的命令负责，不会被前一个块的失败连锁影响。

### 3. 为什么先显示再减

顺序是 `show3/show2/show1/go` → `count_down`。
如果先减，按下开始后第一眼会看到 2 而不是 3。

### 4. 为什么 `start_tick` 设 19

`start_btn` 按下后，下一次 clock 执行会把 19 加到 20，`tick_wrap` 立刻成立，倒计时不用等满一秒才开始。

### 5. 为什么 `clear_pulse` 必须 unconditional

整秒之外 `pulse` 不会执行，`#second` 可能残留 1；`clear_pulse` 每 tick 都跑，确保归零。

## 搭建步骤

1. 运行初始化（见 `plan.md` 的 Setup）。
2. 放 `clock`：Repeat，Always Active，Delay 0，命令 `scoreboard players add #tick arena 1`。
3. 在它面前放 `tick_wrap`：Chain，Conditional，Always Active，Delay 0。
4. 依次向前放 `pulse`、`show3`、`show2`、`show1`、`go`、`start_running`、`count_down`、`clear_pulse`，全部朝同一方向、紧挨着。
   - `pulse`：Conditional
   - 其余：Unconditional
5. 单独放 `start_btn`：Impulse，Needs Redstone；后面接 `start_count`、`start_tick`、`start_title`（都 Conditional）。
6. 单独放 `reset_btn`：Impulse，Needs Redstone；后面接 `reset_count`、`reset_tick`、`reset_title`（都 Conditional）。
7. 给三个入口各接一个按钮/拉杆。

> 三个链可以放在同一面墙上，但每条链必须各自是直线；不要把一个链的输出接到另一条链的中间。

## 测试

- [ ] 按开始：3、2、1、GO 各停约 1 秒。
- [ ] 连续按两次开始：从 3 重新开始，不跳字。
- [ ] 倒计时中按重置：标题清空，状态回 idle。
- [ ] 两名玩家：都看到相同标题。
- [ ] 倒计时中退出再进：状态不重置；再按开始可以重新开始。

## 变体

- **显示分数而不是固定数字**：把 `show3/show2/show1` 换成一条
  `titleraw @a actionbar {"rawtext":[{"text":"§e"},{"score":{"name":"#count","objective":"arena"}}]}`
  仍然用 `#second` 门控。
- **5 秒倒计时**：`start_count` 设 5，`show` 块改 5..1。
- **结束后自动回 idle**：在 `start_running` 后加一个 `#end_delay` 计时，到点设 `#state=0`。

## 生成构建表

```bash
python3 ../../scripts/chain_lint.py spec.json --format markdown
```

见同目录 `plan.md`（由 linter 生成）。
