# 行为包、mcfunction 与 tick.json（网易 1.21.130）

> 网易 1.21.130 的官方命令列表包含 `/function` 与 `/schedule`，但函数来自 Add-on 行为包；
> 租借服/网络服是否允许行为包与函数要以服务器配置为准。命令方块地图不依赖函数也能运行。

## 1. 什么时候用函数，什么时候用命令方块

| 场景 | 推荐 |
|---|---|
| 玩家按按钮触发的一次性逻辑 | 命令方块（直观、可红石） |
| 需要可视化排布/调试的链 | 命令方块 |
| 每 tick 轮询、大量重复逻辑 | `tick.json` + 函数 |
| 需要版本管理、复用、多人协作 | 函数文件 |
| 需要条件链的“成功/失败”语义 | 命令方块（函数里没有方块条件） |
| 需要精确的方块延迟 | 命令方块 Delay，或函数 + 计分板计时 |
| 复杂数学/循环/批量实体 | 函数（一行行写，易维护） |

函数**不能**配置命令方块；命令方块**可以**调用函数。二者常混合使用。

## 2. 行为包目录结构

```
behavior_packs/
  ArenaPack/
    manifest.json
    functions/
      tick.json
      arena/
        tick.mcfunction
        start.mcfunction
        reset.mcfunction
      shop/
        buy.mcfunction
```

- `functions/` 与 `manifest.json` 同级。
- 子目录就是函数路径的一部分：`functions/arena/start.mcfunction` → `/function arena/start`。
- **没有命名空间前缀**：Bedrock 函数按路径调用，不写 `namespace:`。
- 一个世界可以叠加多个行为包；每个包的 `tick.json` 都会执行（additive）。

## 3. manifest.json

```json
{
  "format_version": 2,
  "header": {
    "name": "Arena Pack",
    "description": "Command-block arena logic",
    "uuid": "00000000-0000-0000-0000-000000000001",
    "version": [1, 0, 0],
    "min_engine_version": [1, 21, 0]
  },
  "modules": [
    {
      "type": "data",
      "uuid": "00000000-0000-0000-0000-000000000002",
      "version": [1, 0, 0]
    }
  ]
}
```

- 两个 UUID 必须不同；用 UUID 生成器生成，不要照抄示例。
- `min_engine_version` 决定命令按哪个版本解析（例如 1.19.70 前后 `fill` 语法不同）。**写你实际测试的版本**。
- 模块类型用 `"data"`。
- 修改 manifest 的 UUID/版本后要重新加载世界。

## 4. tick.json

```json
{
  "values": [
    "arena/tick",
    "shop/tick"
  ]
}
```

- 只接受 `values` 键；值是函数路径，**不带 `.mcfunction`**。
- 按数组顺序每 tick 执行一次（20 次/秒，游戏 tick，不是红石 tick）。
- 多个行为包的 `tick.json` 会叠加执行。
- **tick.json 在世界完全加载前就会开始执行**：函数里要加保护，例如 `execute if entity @a run ...`，不要在加载前做 `fill`/`structure`。
- 每 tick 都跑的函数要便宜：先 `if` 门，再做昂贵操作。

## 5. .mcfunction 规则

```mcfunction
# 注释以 # 开头
scoreboard objectives add arena dummy
scoreboard players set #state arena 0

# 空行可以
execute as @a at @s run particle flame ~ ~1 ~
```

- 一行一条命令，**不写开头的 `/`**。
- `#` 开头是注释；行尾注释不支持（`#` 必须在一行开头）。
- 命令按行顺序执行，同一 tick 内跑完（除非用 `schedule`）。
- 函数里的命令在加载时解析；**任何一行解析失败，整个函数无法加载**。
- 字符串/JSON 里的换行要写成 `\n`，不能真的换行。

## 6. 执行上下文

- `/function` 由谁执行，函数里的命令就继承谁的执行者/位置/维度。
- 命令方块调用函数：命令方块不是实体，`@s` 通常选不中；位置是命令方块位置。
- `tick.json` 调用的函数由服务器执行：位置在世界原点 `0,0,0`（主世界），`@s` 不是玩家。
- 需要玩家上下文时，显式写 `execute as @a at @s ...`。

## 7. 限制

| 项目 | 限制 |
|---|---|
| 单次函数调用命令数 | 10,000（含嵌套调用） |
| 函数文件数量 | 无硬性小上限，但加载/维护成本随数量上升 |
| 每 tick 命令数 | 无硬上限；低端设备上几百条就可能掉帧 |
| 递归 | 会占用 10,000 条预算；不要写无限递归 |
| 命令长度 | 单行仍受命令长度限制；超长 JSON 要拆 |

> 超过 10,000 条不是“报错”，而是**超出部分不执行**；大循环要拆到多个 tick。
> 上限可用 `gamerule functioncommandlimit` 调整（默认 10000），但不要靠它硬跑大循环。

## 8. schedule（基岩版）

```mcfunction
schedule delay add <function> <delayTicks> [append|replace]
schedule delay clear <function>
schedule clear <function>
schedule on_area_loaded add <from x y z> <to x y z> <function>
schedule on_area_loaded add circle <center x y z> <radius> <function>
schedule on_area_loaded add tickingarea <name> <function>
schedule on_area_loaded clear function <function>
schedule on_area_loaded clear tickingarea <name> [function]
```

```mcfunction
# 20 tick 后执行一次
schedule delay add arena/start 20

# 取消
schedule delay clear arena/start

# 区域加载时执行一次
schedule on_area_loaded add 0 0 0 31 0 31 arena/on_load
```

- 基岩版没有 `schedule function <fn> 1t`（Java 写法）。
- 网易 1.21.130 官方命令列表明确列出 `/schedule`（“安排函数在特定的游戏刻后运行”），可以用；但它调度的是 Add-on 函数。
- 延迟单位 tick；`append` 可叠加，`replace` 替换。
- 适合“延迟后执行一次”的函数；循环仍用 `tick.json`。

## 9. 常用骨架

### tick.mcfunction

```mcfunction
# 每 tick：推进 1 秒时钟
scoreboard players add #clock arena 1
execute if score #clock arena matches 20.. run scoreboard players set #clock arena 0
execute if score #clock arena matches 0 run function arena/per_second

# 每 tick：状态机推进（函数内部自己判断状态）
execute if score #state arena matches 1 run function arena/countdown_tick
```

### start.mcfunction

```mcfunction
scoreboard players set #state arena 1
scoreboard players set #count arena 3
scoreboard players set #clock arena 20
title @a title §6Get ready!
```

### reset.mcfunction

```mcfunction
scoreboard players set #state arena 0
scoreboard players set #count arena 0
scoreboard players set #clock arena 0
scoreboard players set @a temp 0
tag @a remove ready
title @a clear
```

## 10. 把命令方块链改写成函数

1. 保持**顺序**：链上的顺序就是函数里的行顺序。
2. 把方块的 `Conditional` 改成显式的 `execute if ...`：
   - 方块条件 = “上一条命令成功”；函数里没有这种隐式状态。
   - 需要“上一条成功才执行”，写成 `execute if score ...` 或先设标记。
3. 把 `Delay` 改成：
   - `schedule delay add`（一次性），或
   - 计分板倒计时（可暂停/重置）。
4. 把 `Chain` 的“触发下一个”改成直接下一行。
5. 把 `Repeat` 改成 `tick.json` 里的函数。
6. 把方块位置相关的命令（`~ ~ ~`）改成显式坐标或 `execute positioned ...`，因为函数执行位置不同。

## 11. 调试

- 先用 `/function <path>` 手动跑一次；报错会显示在聊天栏。
- 函数加载失败通常是某一行语法错；注释掉一半，二分定位。
- `tick.json` 不跑：
  - 文件是否在 `functions/` 下？
  - 路径是否写错（不带 `.mcfunction`）？
  - 行为包是否启用？世界是否重进过？
  - 函数是否被 10,000 条限制截断？
- 改函数后 `/reload`；**新加的函数文件**通常要重启世界。
- 用 `say`/`tellraw` 在关键行打点，确认执行到哪一行。
- 低端设备掉帧：把每 tick 的函数拆成每 2/5/20 tick。

## 12. 参考

- [Introduction to Functions — Microsoft Learn](https://learn.microsoft.com/en-us/minecraft/creator/documents/functionsintroduction)
- [Introduction to tick.json — Microsoft Learn](https://learn.microsoft.com/en-us/minecraft/creator/documents/tickjsonintroduction)
- [Function (Bedrock Edition) — Minecraft Wiki](https://minecraft.wiki/w/Function_(Bedrock_Edition))
- [Commands/schedule — Minecraft Wiki](https://minecraft.wiki/w/Commands/schedule)
