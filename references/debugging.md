# 调试命令方块链（基岩版）

## 1. 先问四个问题

命令方块链不工作时，按顺序排除：

1. **它在跑吗？** 方块被激活/触发了吗？区块在 ticking 吗？
2. **命令解析了吗？** 打开方块看 Previous Output 有没有语法错误。
3. **选择器选中了吗？** 把选择器单独拿出来用 `execute if entity` 测试。
4. **条件成立吗？** 把分数/方块状态打印出来，而不是猜。

不要一开始就改命令；先确定它停在哪一层。

## 2. 三层诊断

```
第 1 层：触发
  ├─ Impulse 有没有红石信号？
  ├─ Repeat 是不是 Always Active / 有没有红石？
  ├─ Chain 的上游有没有执行？
  └─ 区块是不是 ticking？（tickingarea）

第 2 层：解析
  ├─ 打开命令方块看 Previous Output
  ├─ 有没有 “Syntax error” / “Unknown command”？
  └─ 基岩版不支持的 Java 语法？

第 3 层：效果
  ├─ 选择器选中了谁？（execute if entity <selector>）
  ├─ 条件是真还是假？（tellraw 打印分数）
  └─ 命令成功了但没可见效果？（例如 setblock 到已加载区外）
```

## 3. 探针写法

### 打印执行到哪一步

在链的每个阶段插一个“探针块”（调试完删掉）：

```mcfunction
tellraw @a {"rawtext":[{"text":"§e[DBG] stage 1"}]}
```

或只给调试者：

```mcfunction
tellraw @s {"rawtext":[{"text":"§e[DBG] stage 1"}]}
```

### 打印分数

```mcfunction
tellraw @a {"rawtext":[
  {"text":"§e[DBG] state="},
  {"score":{"name":"fb_state","objective":"arena"}},
  {"text":" count="},
  {"score":{"name":"fb_count","objective":"arena"}}
]}
```

或把目标显示到侧边栏：

```mcfunction
scoreboard objectives setdisplay sidebar arena
```

### 测试选择器

单独放一个 Impulse 方块（按钮触发）：

```mcfunction
execute if entity @a[r=5,tag=ready] run say selector_ok
execute unless entity @a[r=5,tag=ready] run say selector_empty
```

### 测试条件

```mcfunction
execute if score fb_state arena matches 1 run say state_is_1
execute unless score fb_state arena matches 1 run say state_is_not_1
```

## 4. 症状 → 原因 → 修复

| 症状 | 常见原因 | 修复 |
|---|---|---|
| 整条链完全不动 | 区块未加载；`commandblocksenabled` 关闭；方块没激活 | 加 `tickingarea`；`gamerule commandblocksenabled true`；检查红石/按钮 |
| 第一个方块跑了，后面不动 | 下一个方块不是 Chain；箭头没朝向它；中间隔了空气 | 换成 Chain，调整朝向，紧贴放置 |
| Chain 不执行但上游成功了 | Chain 是 Needs Redstone 且没供电 | 改 Always Active，或给它红石 |
| Conditional 永远不执行 | 身后不是上游方块（拐弯了）；上游命令失败 | 改成直线；把条件写进 `execute if` |
| 条件失败后后面的块仍执行 | 这是基岩版语义：条件失败仍触发下一个；下一个是 Unconditional | 后面要跳过的块设为 Conditional，或改用 `execute if` |
| 红石时钟比预期慢一半 | 基岩版红石只在偶数 tick 响应（C-tick） | 用 Repeat + Always Active 做 20 Hz；或接受 10 Hz |
| Repeat 每 tick 刷屏 | Always Active + Delay 0 | 加 Delay，或加状态门 |
| 选择器选不中人 | 用了 Java 参数（`distance`/`team`/`limit`/`level`）；`@s` 在命令方块里；分数未跟踪 | 改 `r`/`tag`/`c`/`l`；显式 `execute as @a`；先 `set` 分数 |
| `@e` 选中太多 | 没加 `type`/`family`/`tag`/`c` | 收窄选择器 |
| 分数不变 | 目标名写错；命令失败；`reset` 删了记录 | `/scoreboard objectives list`；看 Previous Output；用 `set 0` 而不是 `reset` |
| 分数变成负数/溢出 | 没做下限/上限；32 位溢出 | 加钳制；用 `matches 1..` 保护减法 |
| `tellraw` 没反应 | 根不是 `rawtext`；JSON 写错；目标不在线 | 改成 `{"rawtext":[...]}`；聊天栏先测；用 `@a` |
| `title` 不显示 | 用 JSON 调了 `title`；`times` 太短 | 用纯文本 `title` 或 `titleraw`；设 `times` |
| 粒子/音效位置不对 | 没有 `at @s`，在命令方块位置播放 | `execute as @a at @s run particle ...` |
| 只有房主有效，别人没效果 | 用了 `@p`/`@s` 但上下文不对；多人状态串了 | 每个玩家显式 `execute as @a`；用 `@s` 的分数 |
| 靠近能用，走远失效 | 区块卸载 | `tickingarea` |
| 重载后失效 | 状态卡住；重置链没跑 | 手动跑 reset；检查初始化链 |
| 新函数 `/function` 找不到 | 新文件需要重启世界（`reload` 只重载已有函数） | 退出重进世界 |
| `fill`/`clone` 失败 | 区域未加载；超出体积；源和目标重叠 | 先加载；拆分；`clone ... force` |
| 命令方块报 “Unknown command” | 用了 Java 命令/语法 | 查 `bedrock-vs-java.md`；用 `/help` 验证 |
| 网易 1.21.130 报 Unknown command | 用了 `camera`/`inputpermission`/`dialogue`/`loot`/`place`/`recipe`/`scriptevent`/`fog`，或旧 `execute` | 查 `netease-1.21.130.md`；换替代方案；旧图先升级 |
| `schedule` 报错但命令存在 | 服务器未启用函数 | 先确认服务器支持并启用函数；否则不要使用 `schedule` |
| 命令没报错但没效果 | `execute if` 条件为假；目标为空 | 用探针打印条件；用 `execute if entity` 测选择器 |

## 5. 二分法

链很长时：

1. 在中间插一个 `say midpoint` 探针。
2. 如果探针不响，问题在前半段；响了，问题在后半段。
3. 重复，直到定位到具体方块。
4. 对可疑方块单独做一个测试按钮，绕过整条链。

## 6. 隔离测试

不要在生产链上直接改。复制一份“测试链”：

- 一个 Impulse 按钮 + 一个 Chain，只放要测的命令。
- 固定坐标/固定玩家，减少变量。
- 用 `say`/`tellraw` 确认命令真的执行。
- 确认后再合并回主链。

## 7. 多人测试清单

- [ ] 两个玩家同时触发，状态不会互相覆盖。
- [ ] 玩家 A 的分数不会被玩家 B 的 `@p` 误用。
- [ ] 玩家退出再进来，状态正确初始化。
- [ ] 旁观者/创造模式玩家不会触发机关（`m=!spectator` 等）。
- [ ] 迟到的玩家看到正确的当前状态（标题/计分板/实体）。
- [ ] 玩家死亡/重生后，tag/分数/物品正确重置。

## 8. 重载/持久化测试

- [ ] 退出世界再进，命令方块链仍在跑。
- [ ] 命令方块链的状态（计分板）保留。
- [ ] 远处机关在无人时仍运行（tickingarea）。
- [ ] `/reload` 后已有函数更新；新函数需要重启。
- [ ] 世界备份后再测试破坏性命令（`fill`/`kill`）。

## 9. 调试完的清理

- 删除所有 `[DBG]` 探针块。
- `gamerule commandblockoutput` 恢复为 `false`（如果之前关了）。
- 恢复 `sendcommandfeedback`。
- 删除测试用的临时实体/计分板目标。
- 把 `tickingarea` 数量控制在 10 个以内。

## 10. 快速检查命令

```mcfunction
# 命令方块是否启用
gamerule commandblocksenabled

# 看命令方块输出
gamerule commandblockoutput true
gamerule sendcommandfeedback true

# 看计分板
scoreboard objectives list
scoreboard players list @s
scoreboard objectives setdisplay sidebar arena

# 看常加载区域
tickingarea list all-dimensions

# 看实体
execute if entity @e[type=zombie,tag=wave]

# 看方块
execute if block ~ ~-1 ~ gold_block
```

## 11. 参考

- [Command Block — Minecraft Wiki](https://minecraft.wiki/w/Command_Block)（触发/条件/延迟）
- [Troubleshooting — Minecraft Wiki](https://minecraft.wiki/w/Tutorial:Command_blocks)（命令方块教程）
- [Function (Bedrock Edition) — Minecraft Wiki](https://minecraft.wiki/w/Function_(Bedrock_Edition))（reload/加载行为）
