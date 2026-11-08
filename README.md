# MCBE Commands & Command Blocks — AI Skill

一个面向 AI 的 Minecraft 基岩版（Bedrock Edition）技能包：教模型写**基岩版命令**，并按工程化流程**设计命令方块链**。
目标环境：**网易我的世界 1.21.130（协议 898）**。

> 只针对 Bedrock。Java 版的 `data`、NBT、`execute store`、`team`、`bossbar`、`attribute`、`item`、`forceload` 在这里都不存在。
> 网易 1.21.130 还有自己的边界：`schedule`/`function` 可用；`camera`/`inputpermission`/`dialogue`/`loot`/`place`/`recipe`/`scriptevent`/`fog` 未验证/未实装。

## 目录

```
mcbe-command-blocks/
├── SKILL.md                     # 技能入口：设计流程、硬规则、自检、导航
├── references/
│   ├── command-block-mechanics.md   # 方块类型/条件/延迟/C-tick/成功次数/限制
│   ├── chain-patterns.md            # 20 种链模式：时钟、门、状态机、队列、波次…
│   ├── bedrock-command-reference.md # 常用命令的基岩版签名与坑
│   ├── execute-and-selectors.md     # execute 11 子命令 + 选择器参数
│   ├── scoreboard-memory.md         # dummy-only 计分板做内存/数学/状态
│   ├── text-ui-and-effects.md       # tellraw/titleraw/title/音效/粒子/camerashake
│   ├── fmbe-mbe.md                  # FMBE/MBE 显示实体：前置、1+7 条链、变量、例子
│   ├── dataization-rpg.md           # 数据化 RPG：属性/伤害/T显/等级/装备/怪物
│   ├── misc-map-systems.md          # 杂项：菜单/商店/开箱/反作弊/小游戏/拔刀剑
│   ├── one-pass-delivery.md         # 一遍过交付：导入 repair、执行位置、性能、视觉校准
│   ├── functions-and-packs.md       # mcfunction、tick.json、manifest、schedule
│   ├── debugging.md                 # 症状→原因→修复、探针、二分法
│   ├── bedrock-vs-java.md           # 差异速查 + Java→Bedrock 翻译表
│   ├── netease-1.21.130.md          # 网易命令边界、schedule 结论、未验证命令
│   └── netease-corpus-patterns.md   # 12 个真实网易地图的命令方块语料分析
├── assets/
│   ├── chain-spec.schema.json   # spec.json 的 JSON Schema
│   ├── manifest.template.json   # 行为包 manifest 模板
│   └── tick.template.json       # tick.json 模板
├── scripts/
│   └── chain_lint.py            # 校验 spec + 生成构建表（无第三方依赖）
└── examples/
    ├── arena-countdown/         # 倒计时：秒时钟 + 状态机 + 脉冲标记
    ├── vending-machine/         # 售货机：条件流水线 + 库存 + 清理
    ├── toggle-lamp/             # 开关灯：取模翻转 + 并行分支 + 坐标
    ├── snowball-menu/           # 雪球三级菜单：256 方块、紧凑布局、BDX + UI 预览
    └── fmbe-player/             # FMBE 1:1 玩家：6 部件、86 方块、预览 + BDX
```

## 安装

**项目级（当前工作区）**：已经放在

```
<workspace>/.dsh/skills/mcbe-command-blocks/
```

DSH 启动时会扫描 `<project>/.dsh/skills`，技能目录里必须有 `SKILL.md`。

**用户级（所有项目可用）**：

```bash
mkdir -p ~/.dsh/skills
cp -R .dsh/skills/mcbe-command-blocks ~/.dsh/skills/
# 或者用软链接，改一处全局生效：
# ln -s "$PWD/.dsh/skills/mcbe-command-blocks" ~/.dsh/skills/mcbe-command-blocks
```

## 怎么用

直接描述任务，例如：

- “基岩版怎么让玩家站上金块时触发命令？”
- “帮我设计一个 3 秒倒计时 + 开局的命令方块链。”
- “这个命令方块链为什么第二个方块不执行？”
- “把这段 Java 命令翻译成基岩版。”

模型会按 `SKILL.md` 的流程先定状态/时序，再给方块设置与测试清单。

## 校验 spec / 生成构建表

```bash
python3 scripts/chain_lint.py examples/arena-countdown/spec.json
python3 scripts/chain_lint.py examples/arena-countdown/spec.json --format json
python3 scripts/chain_lint.py examples/arena-countdown/spec.json --write plan.md
```

退出码：`0` 无错误；`1` 有错误（或 `--strict` 下有警告）；`2` 文件/参数错误。

它会检查：

- Java 残留命令/选择器参数/方块状态/文本 JSON
- `dummy` 以外的计分板准则、`objectives modify`、`players get`
- 无头链、孤立块、环、多上游、非相邻、朝向错误、条件块身后不对
- 红石 10 Hz、repeat 每 tick 昂贵命令、延迟链条件语义
- 命令长度、`@e` 过宽、`hasitem` 误用 `count=`

## 设计 spec 的最小格式

```json
{
  "name": "my-chain",
  "setup": ["scoreboard objectives add obj dummy"],
  "blocks": [
    {
      "id": "clock",
      "type": "repeat",
      "condition": "unconditional",
      "redstone": "always_active",
      "delay": 0,
      "command": "scoreboard players add #tick obj 1",
      "next": "step"
    },
    {
      "id": "step",
      "type": "chain",
      "condition": "conditional",
      "command": "execute if score #tick obj matches 20.. run scoreboard players set #tick obj 0",
      "next": null
    }
  ],
  "tests": ["..."],
  "notes": ["..."]
}
```

完整字段见 `assets/chain-spec.schema.json`。

## 语料分析（真实网易地图）

本技能用 AuroraBuild 的 `AuroraStructure` 模块解析了用户提供的 12 个 `.bdx` / `.mcworld`：

- 19,501 个命令方块，18,945 条非空命令。
- 命令频率、菜单/常加载/结构/表现模式、旧语法比例见 `references/netease-corpus-patterns.md`。
- 结论：`execute` 是绝对主力；计分板是状态核心；`tickingarea` 是远处机关的命脉；旧 `execute @a ~ ~ ~` 必须升级。

## 主要事实来源

- [Command Block — Minecraft Wiki](https://minecraft.wiki/w/Command_Block)
- [Commands/execute — Minecraft Wiki](https://minecraft.wiki/w/Commands/execute)
- [Target selectors — Minecraft Wiki](https://minecraft.wiki/w/Target_selectors)
- [Scoreboard — Minecraft Wiki](https://minecraft.wiki/w/Scoreboard)
- [Function (Bedrock Edition) — Minecraft Wiki](https://minecraft.wiki/w/Function_(Bedrock_Edition))
- [Minecraft Creator Docs — Commands](https://learn.microsoft.com/en-us/minecraft/creator/commands/)

## 说明

- 技能是**静态知识 + 静态校验**：linter 不能执行 Minecraft，最终以游戏内测试为准。
- 版本以**网易 1.21.130**为基准；`/help` 是版本差异的最终裁判。
- `schedule` **有**（网易官方命令列表明确列出），不要删；它调度 Add-on 函数。
- 旧导入图里的 `execute @a ~ ~ ~` 旧语法，新图不要用；先用 AuroraBuild `command_upgrader` 升级。
