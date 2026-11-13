# MinecraftBE Commands & Building — AI Skill

一个面向 AI 的 Minecraft 基岩版（Bedrock Edition）技能包：教模型写**基岩版命令**、设计**命令方块链**，并完成**建筑/内饰/奇观**的体素设计与导出。

目标环境：**网易我的世界 1.21.130（协议 898）**。

> 只针对 Bedrock。Java 版的 `data`、NBT、`execute store`、`team`、`bossbar`、`attribute`、`item`、`forceload` 在这里都不存在。
> 网易 1.21.130 的边界：`schedule`/`function` 可用；`camera`/`inputpermission`/`dialogue`/`loot`/`place`/`recipe`/`scriptevent`/`fog` 未验证/未实装。

> 交流群：2166056402

## 范围

- **命令**：命令方块链、计分板状态机、FMBE 显示、菜单、技能、系统逻辑。
- **建筑**：场地、体量、轮廓、材质、立面、屋顶、内饰、灯光。
- **输出**：只生成 **BDX**。不做 MCWorld，不做行为包。

## 先学模型，不是背例子

这个 Skill 不把“例子”当知识本身。每个任务先建立：

1. **计算模型**：状态机 / 数据流事务 / 队列 / 树 / 图 / 几何采样。
2. **内存布局**：计分板、tag、数组、队列、树索引。
3. **数学**：整数、取模、钳制、坐标、距离、概率、几何表。
4. **复杂度**：分支数、实体数、每 tick 命令数、最坏情况。
5. **不变量**：幂等、可重置、有界、可观测。

- [命令计算基础](references/command-foundations.md)
- [命令数学](references/command-mathematics.md)
- [N 叉树 / NX 树](references/nx-tree.md)

## 快速开始

```bash
# 1. 安装到用户级技能目录
git clone https://github.com/yixin-amore/MinecraftBE-Command-Building-Skill.git
mkdir -p ~/.dsh/skills
cp -R MinecraftBE-Command-Building-Skill ~/.dsh/skills/mcbe-command-blocks

# 2. 依赖（BDX 生成需要 brotli）
python3 -m pip install brotli

# 3. 验证
cd ~/.dsh/skills/mcbe-command-blocks
python3 scripts/chain_lint.py examples/arena-countdown/spec.json
python3 scripts/bdxgen.py --spec examples/bdx-generator/demo.json /tmp/demo.bdx
python3 scripts/buildgen.py examples/build-pipeline/plan.json /tmp/build.bdx
```

## 目录

```text
mcbe-command-blocks/
├── SKILL.md
├── references/
│   ├── command-block-mechanics.md
│   ├── command-foundations.md       # 计算模型/内存/控制流/算法/复杂度
│   ├── command-mathematics.md       # 整数/定点/坐标/几何/概率
│   ├── nx-tree.md                   # N 叉树/NX：执行分叉/圆/射线/体积
│   ├── chain-patterns.md
│   ├── bedrock-command-reference.md
│   ├── execute-and-selectors.md
│   ├── scoreboard-memory.md
│   ├── text-ui-and-effects.md
│   ├── fmbe-mbe.md
│   ├── render-controller-vars.md     # playanimation 改 render controller 变量
│   ├── dataization-rpg.md
│   ├── misc-map-systems.md
│   ├── one-pass-delivery.md
│   ├── bdx-chain-packaging.md
│   ├── building-design.md
│   ├── building-corpus-learning.md
│   ├── gothic-cathedral-case.md
│   ├── interior-design.md
│   ├── spectacle-design.md
│   ├── creative-thinking.md
│   ├── debugging.md
│   ├── bedrock-vs-java.md
│   └── netease-1.21.130.md
├── assets/
│   ├── chain-spec.schema.json
│   ├── design-brief.template.md
│   ├── building-brief.template.md
│   └── interior-brief.template.md
├── scripts/
│   ├── chain_lint.py
│   ├── bdxgen.py
│   ├── buildgen.py
│   ├── sunrain_index.py
│   ├── corpus_query.py
│   └── schematic_blocks.py
└── examples/
    ├── arena-countdown/
    ├── vending-machine/
    ├── toggle-lamp/
    ├── snowball-menu/
    ├── fmbe-player/
    ├── bdx-generator/
    └── build-pipeline/
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
| `brotli` | `bdxgen.py` / `buildgen.py` |
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
python3 scripts/buildgen.py examples/build-pipeline/plan.json /tmp/check-build.bdx
ls -lh /tmp/check.bdx /tmp/check-build.bdx
```

## 3. 在 DSH 里使用

直接把需求说清楚，模型会读 `SKILL.md`，先定状态/时序/体量，再写 spec/plan 和 BDX 文件。

**好需求：**

> “设计一个 3 秒倒计时 + 开局传送的命令方块链，并生成 BDX。”

> “在 `300 64 500` 建一座 20×20 的石屋，只导出 BDX。”

> “这个链为什么第二个方块不执行？”

> “把这段 Java 命令翻译成基岩版。”

**需要补参数的需求：**

> “建个好看的主城。”

需要先确认：坐标、尺寸、风格、功能、性能预算。

## 4. 命令方块：spec → BDX

`spec.json` 描述链；`chain_lint.py` 校验；`bdxgen.py` 生成命令方块 BDX。

```bash
python3 scripts/chain_lint.py examples/arena-countdown/spec.json
python3 scripts/chain_lint.py examples/arena-countdown/spec.json --write plan.md
python3 scripts/bdxgen.py --spec examples/bdx-generator/demo.json /tmp/demo.bdx
```

最小 spec：

```json
{
  "name": "my-chain",
  "setup": ["scoreboard objectives add obj dummy"],
  "blocks": [
    {"id": "clock", "type": "repeat", "redstone": "always_active",
     "command": "scoreboard players add fb_tick obj 1", "next": "step"},
    {"id": "step", "type": "chain", "command": "say 20 ticks", "next": null}
  ],
  "tests": ["..."],
  "notes": ["..."]
}
```

完整字段见 `assets/chain-spec.schema.json`。

## 5. 建筑：plan → BDX

一份 `plan.json` 生成完整方块 BDX：

```json
{
  "name": "My Build",
  "fills": [
    {"from": [0, 64, 0], "to": [8, 64, 8], "block": "stone_bricks"}
  ],
  "blocks": [
    {"pos": [4, 65, 4], "block": "sea_lantern"}
  ],
  "commands": [
    {"pos": [0, 65, 0], "type": "chain", "command": "say build ready"}
  ]
}
```

```bash
python3 scripts/buildgen.py plan.json out.bdx
```

| 字段 | 说明 |
|---|---|
| `fills` | `from` / `to` / `block`，可加 `data` / `states` |
| `blocks` | 单方块 `pos` / `block` |
| `commands` | 命令方块 `pos` / `type` / `command` |

- `buildgen.py` 把 plan 展开成普通方块 + 命令方块 BDX。
- `bdxgen.py` 也可直接写 `BuildBlock` / `Block`。
- 大建筑会展开成很多方块；脚本有 2,000,000 块上限，超了拆 plan。

## 6. 导入 BDX

用任意 BDX 导入器导入 `out.bdx`。导入后确认：

- 命令方块 mode / chain / facing 正确
- 坐标与世界匹配
- 需要时加 `tickingarea`
- 建筑方块没有被导入器过滤

## 7. 排错

| 症状 | 处理 |
|---|---|
| `ModuleNotFoundError: brotli` | `python3 -m pip install brotli` |
| DSH 不加载技能 | 确认目录里有 `SKILL.md`，路径是 `.dsh/skills/mcbe-command-blocks/` |
| BDX 无法导入 | 先 `chain_lint.py`；检查 BDX 头 `BD@` |
| 建筑没有出现 | 检查 plan 坐标/`from`/`to`，用 `buildgen.py` 回读统计 |
| 命令链不跑 | 检查 head mode、facing、conditional、tickingarea |
| 多人异常 | 检查每玩家状态/全局假玩家是否混用 |

## 8. 校验 spec / 生成构建表

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
- [Minecraft Creator Docs — Commands](https://learn.microsoft.com/en-us/minecraft/creator/commands/)

## 说明

- 技能是**静态知识 + 静态校验**：linter 不能执行 Minecraft，最终以游戏内测试为准。
- 版本以**网易 1.21.130**为基准；`/help` 是版本差异的最终裁判。
- 旧导入图里的 `execute @a ~ ~ ~` 旧语法，新图不要用；先手工升级。

## License

MIT
