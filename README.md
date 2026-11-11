# MinecraftBE Commands — AI Skill

一个面向 AI 的 Minecraft 基岩版（Bedrock Edition）技能包：教模型写**基岩版命令**、设计**命令方块链**，并生成可直接导入的 **BDX**。

目标环境：**网易我的世界 1.21.130（协议 898）**。

> 只针对 Bedrock。Java 版的 `data`、NBT、`execute store`、`team`、`bossbar`、`attribute`、`item`、`forceload` 在这里都不存在。
> 网易 1.21.130 的边界：`schedule`/`function` 可用；`camera`/`inputpermission`/`dialogue`/`loot`/`place`/`recipe`/`scriptevent`/`fog` 未验证/未实装。

> 交流群：2166056402

## 范围

**只做纯指令：命令、命令方块链、计分板、FMBE 显示、菜单、技能、系统逻辑。**  
**只输出 BDX；不生成 MCWorld，不做建筑生成器。**

## 快速开始

```bash
# 1. 安装到用户级技能目录
git clone https://github.com/yixin-amore/MinecraftBE-Command-Building-Skill.git
mkdir -p ~/.dsh/skills
cp -R MinecraftBE-Command-Building-Skill ~/.dsh/skills/mcbe-command-blocks

# 2. 依赖（只有生成 BDX 需要 brotli）
python3 -m pip install brotli

# 3. 验证
cd ~/.dsh/skills/mcbe-command-blocks
python3 scripts/chain_lint.py examples/arena-countdown/spec.json
python3 scripts/bdxgen.py --spec examples/bdx-generator/demo.json /tmp/demo.bdx
```

## 目录

```text
mcbe-command-blocks/
├── SKILL.md                     # 技能入口：设计流程、硬规则、自检、导航
├── references/
│   ├── command-block-mechanics.md   # 方块类型/条件/延迟/C-tick/成功次数/限制
│   ├── chain-patterns.md            # 20 种链模式：时钟、门、状态机、队列、波次…
│   ├── bedrock-command-reference.md # 常用命令的基岩版签名与坑
│   ├── execute-and-selectors.md     # execute 11 子命令 + 选择器参数
│   ├── scoreboard-memory.md         # dummy-only 计分板做内存/数学/状态
│   ├── text-ui-and-effects.md       # tellraw/titleraw/title/音效/粒子/camerashake
│   ├── fmbe-mbe.md                  # FMBE/MBE 显示实体：1+7 条链、变量、例子
│   ├── dataization-rpg.md           # 数据化 RPG：属性/伤害/T显/等级/装备/怪物
│   ├── misc-map-systems.md          # 杂项：菜单/商店/开箱/反作弊/小游戏
│   ├── one-pass-delivery.md         # 一遍过交付：导入 repair、执行位置、性能
│   ├── bdx-chain-packaging.md       # BDX 打包：单区块盘旋/初始化分离/验收
│   ├── functions-and-packs.md       # mcfunction、tick.json、manifest、schedule
│   ├── debugging.md                 # 症状→原因→修复、探针、二分法
│   ├── bedrock-vs-java.md           # 差异速查 + Java→Bedrock 翻译表
│   └── netease-1.21.130.md          # 网易命令边界、schedule 结论、未验证命令
├── assets/
│   ├── chain-spec.schema.json   # spec.json 的 JSON Schema
│   ├── design-brief.template.md # 设计前思考模板（3 方向/联动图/风险）
│   ├── manifest.template.json   # 行为包 manifest 模板
│   └── tick.template.json       # tick.json 模板
├── scripts/
│   ├── chain_lint.py            # 校验 spec + 生成构建表（无第三方依赖）
│   └── bdxgen.py                # 命令方块 BDX 生成器（brotli）
└── examples/
    ├── arena-countdown/         # 倒计时：秒时钟 + 状态机 + 脉冲标记
    ├── vending-machine/         # 售货机：条件流水线 + 库存 + 清理
    ├── toggle-lamp/             # 开关灯：取模翻转 + 并行分支 + 坐标
    ├── snowball-menu/           # 雪球三级菜单：256 方块、紧凑布局、BDX + UI 预览
    ├── fmbe-player/             # FMBE 1:1 玩家：10 部件、142 方块、预览 + BDX
    └── bdx-generator/           # 命令方块 BDX 最小生成样例
```

## 1. 安装

### 项目级

```bash
git clone https://github.com/yixin-amore/MinecraftBE-Command-Building-Skill.git
mkdir -p <workspace>/.dsh/skills
cp -R MinecraftBE-Command-Building-Skill <workspace>/.dsh/skills/mcbe-command-blocks
```

DSH 启动时会扫描 `<workspace>/.dsh/skills`，目录里必须有 `SKILL.md`。

### 用户级

```bash
mkdir -p ~/.dsh/skills
cp -R MinecraftBE-Command-Building-Skill ~/.dsh/skills/mcbe-command-blocks
```

或软链接：

```bash
ln -sfn "$PWD/MinecraftBE-Command-Building-Skill" ~/.dsh/skills/mcbe-command-blocks
```

### 环境

| 需求 | 说明 |
|---|---|
| Python 3.10+ | 所有脚本 |
| `brotli` | 仅 `bdxgen.py` |
| BDX 导入器 | 导入 `.bdx` 时需要 |

```bash
python3 -m pip install brotli
```

## 2. 验证

```bash
cd ~/.dsh/skills/mcbe-command-blocks
test -f SKILL.md && echo SKILL_OK

python3 scripts/chain_lint.py examples/arena-countdown/spec.json
python3 scripts/bdxgen.py --spec examples/bdx-generator/demo.json /tmp/check.bdx
ls -lh /tmp/check.bdx
```

## 3. 在 DSH 里使用

直接把需求说清楚，模型会读 `SKILL.md`，先定状态/时序，再写 spec/命令和 BDX。

**好需求：**

> “设计一个 3 秒倒计时 + 开局传送的命令方块链，并生成 BDX。”

> “这个链为什么第二个方块不执行？”

> “把这段 Java 命令翻译成基岩版。”

> “做一个雪球三级菜单，输出 BDX。”

**需要补参数的需求：**

> “做个好玩的系统。”

需要先确认：触发、状态、玩家数、UI、性能预算、重置方式。

## 4. spec → BDX

`spec.json` 描述链；`chain_lint.py` 校验；`bdxgen.py` 生成命令方块 BDX。

```bash
# 校验
python3 scripts/chain_lint.py examples/arena-countdown/spec.json

# 生成构建表
python3 scripts/chain_lint.py examples/arena-countdown/spec.json --write plan.md

# 生成 BDX
python3 scripts/bdxgen.py --spec examples/bdx-generator/demo.json /tmp/demo.bdx
```

最小 spec：

```json
{
  "name": "my-chain",
  "setup": ["scoreboard objectives add obj dummy"],
  "blocks": [
    {"id": "clock", "type": "repeat", "redstone": "always_active",
     "command": "scoreboard players add #tick obj 1", "next": "step"},
    {"id": "step", "type": "chain", "command": "say 20 ticks", "next": null}
  ],
  "tests": ["..."],
  "notes": ["..."]
}
```

完整字段见 `assets/chain-spec.schema.json`。

## 5. 导入 BDX

用任意 BDX 导入器导入 `/tmp/demo.bdx`。导入后确认：

- 命令方块 mode / chain / facing 正确
- 坐标与世界匹配
- 需要时加 `tickingarea`
- 分类链有唯一 head，无孤立 chain

## 6. 排错

| 症状 | 处理 |
|---|---|
| `ModuleNotFoundError: brotli` | `python3 -m pip install brotli` |
| DSH 不加载技能 | 确认目录里有 `SKILL.md`，路径是 `.dsh/skills/mcbe-command-blocks/` |
| BDX 无法导入 | 先 `chain_lint.py`；检查 BDX 头 `BD@` |
| 命令链不跑 | 检查 head mode、facing、conditional、tickingarea |
| 多人异常 | 检查每玩家状态/全局假玩家是否混用 |

## 7. 校验 spec / 生成构建表

```bash
python3 scripts/chain_lint.py examples/arena-countdown/spec.json
python3 scripts/chain_lint.py examples/arena-countdown/spec.json --format json
python3 scripts/chain_lint.py examples/arena-countdown/spec.json --write plan.md
```

退出码：`0` 无错误；`1` 有错误（或 `--strict` 下有警告）；`2` 文件/参数错误。

检查内容：

- Java 残留命令/选择器参数/方块状态/文本 JSON
- `dummy` 以外的计分板准则、`objectives modify`、`players get`
- 无头链、孤立块、环、多上游、非相邻、朝向错误、条件块身后不对
- 红石 10 Hz、repeat 每 tick 昂贵命令、延迟链条件语义
- 命令长度、`@e` 过宽、`hasitem` 误用 `count=`

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
- 旧导入图里的 `execute @a ~ ~ ~` 旧语法，新图不要用；先手工升级。

## License

MIT
