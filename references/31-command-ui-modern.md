# 31 · 命令 UI：网易 1.21.130 现代模板

> 设计规范/版式/配色看 `references/30-command-ui-design.md`。
> 本文件给出新 `execute` 模板、迁移规则和 DSL 写法。

## 1. 坐标式 execute → 新语法

旧版是「选择器 + 坐标 + 子命令」的坐标式 execute；新版拆成 `as / at / run`：

```text
坐标式：execute <selector> <x> <y> <z> <command>
新版：  execute as <selector> at @s run <command>
```

规则：

- `as` 决定选择器/执行者；`at` 决定坐标和朝向。
- 纯 UI（tellraw / titleraw）通常 `as ... at @s run`。
- 需要世界坐标时用 `positioned`，不要把旧坐标塞回 `at`。
- 目标位置/朝向用 `at @s`；世界固定坐标用 `positioned`。

## 2. 动作栏菜单（现代）

```mcfunction
execute as @a[scores={menu=1..6}] at @s run titleraw @s actionbar {"rawtext":[
  {"text":"§p▏§7 * §d我的菜单 §7*§r menu §r>>> information§r\n§7--------------------------------------------------\n\n"},
  {"text":"§7"},
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=1}]"},{"text":"§d"}]}},
  {"text":"# 选项一  "},
  {"text":"§7"},
  {"translate":"%%2","with":{"rawtext":[{"selector":"@s[scores={menu=2}]"},{"text":"§d"}]}},
  {"text":"# 选项二  "},
  {"text":"\n\n§7--------------------------------------------------\n§r"}
]}
```

关闭：

```mcfunction
execute as @a[scores={menu=1..6},rxm=88] at @s run titleraw @s actionbar {"rawtext":[{"text":">>> §7菜单已关闭§f <<<"}]}
```

## 3. 条件染色：`%%2`

顺序必须是：

```text
默认色 → 条件染色块 → 选项文字
```

```json
{"text":"§7"},
{"translate":"%%2","with":{"rawtext":[
  {"selector":"@s[scores={menu=1}]"},
  {"text":"§d"}
]}},
{"text":"# 选项一"}
```

命中：列表 `[selector, text]`，取第 2 个 → 显示 `§d`。  
不命中：selector 被丢弃，列表只剩 `[text]`，第 2 个不存在 → 不显示。

## 4. 八档条：`%%9`

```mcfunction
execute as @a at @s run titleraw @s subtitle {"rawtext":[
  {"translate":"%%9","with":{"rawtext":[
    {"selector":"@s[scores={值=1..10}]"},
    {"selector":"@s[scores={值=1..20}]"},
    {"selector":"@s[scores={值=1..30}]"},
    {"selector":"@s[scores={值=1..40}]"},
    {"selector":"@s[scores={值=1..50}]"},
    {"selector":"@s[scores={值=1..60}]"},
    {"selector":"@s[scores={值=1..70}]"},
    {"selector":"@s[scores={值=1..80}]"},
    {"text":"§c█§8███████§r"},
    {"text":"§c██§8██████§r"},
    {"text":"§6███§8█████§r"},
    {"text":"§6████§8████§r"},
    {"text":"§e█████§8███§r"},
    {"text":"§e██████§8██§r"},
    {"text":"§2███████§8█§r"},
    {"text":"§a████████§r"}
  ]}}
]}
```

规则：

- 8 个累进选择器 + 8 个候选文本
- 译文串数字 = 选择器数 + 1
- 超过 8 档再嵌套；不要漏掉兜底上限

## 5. HUD 与菜单互斥

```mcfunction
# HUD 只在菜单关闭时显示
execute as @a unless score @s menu matches 1.. at @s run titleraw @s actionbar {"rawtext":[...]}
```

动作栏同一时刻只允许一个界面；用**不重叠的计分区间**分配：

```text
menu=1..6       一级菜单
menu=21..35     二级菜单
雪球菜单=1..6
雪球菜单=181..186
```

## 6. DSL 写法

```python
from dsl import As, P, Tellraw, Title

As(P("@a", scores={"menu": "1..6"})).at("@s").run(
    Title("@s", "actionbar", {"rawtext": [
        {"text": "§p▏§7 * §d我的菜单 §7*§r\n"},
    ]})
)

As(P("@a", scores={"金币奖励": "1.."})).at("@s").run(
    Tellraw("@s", {"rawtext": [
        {"text": "§f｜§g〖§e金币 §f> "},
    ]})
)
```

> 复杂 rawtext 仍建议用 Python dict 生成，再交给 `Tellraw/Title` 序列化；不要在 DSL 里拼整段 JSON 字符串。

## 7. 上线前

- [ ] 所有坐标式 execute 已改成 `execute as ... at @s run`
- [ ] `%%2` / `%%9` 在网易 1.21.130 实测
- [ ] 动作栏每 tick 刷新
- [ ] 菜单关闭提示存在
- [ ] HUD 与菜单互斥
- [ ] 奖励分数结算后清零
- [ ] 调试条件 `name=tm` 已删
