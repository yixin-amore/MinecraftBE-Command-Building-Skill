# MinecraftBE Commands & Building — AI Skill

一个面向 AI 的 Minecraft 基岩版（Bedrock Edition）技能包：教模型写**基岩版命令**、设计**命令方块链**，并按工程化流程做**建筑/内饰/奇观**。
目标环境：**网易我的世界 1.21.130（协议 898）**。

> 只针对 Bedrock。Java 版的 `data`、NBT、`execute store`、`team`、`bossbar`、`attribute`、`item`、`forceload` 在这里都不存在。
> 网易 1.21.130 还有自己的边界：`schedule`/`function` 可用；`camera`/`inputpermission`/`dialogue`/`loot`/`place`/`recipe`/`scriptevent`/`fog` 未验证/未实装。

> 交流群：2166056402

## 快速开始

```bash
# 1. 安装到用户级技能目录
git clone https://github.com/yixin-amore/MinecraftBE-Command-Building-Skill.git
mkdir -p ~/.dsh/skills
cp -R MinecraftBE-Command-Building-Skill ~/.dsh/skills/mcbe-command-blocks

# 2. 依赖（只有 BDX 生成需要 brotli）
python3 -m pip install brotli

# 3. 跑一个最小示例
cd ~/.dsh/skills/mcbe-command-blocks
python3 scripts/buildgen.py examples/build-pipeline/plan.json /tmp/demo.bdx
python3 scripts/mcworldgen.py examples/build-pipeline/plan.json /tmp/demo.mcworld
```

- `.bdx`：用 BDX 导入器导入。
- `.mcworld`：直接打开，首次 tick 自动建造。
- 在 DSH 中直接说需求，模型会按 `SKILL.md` 执行。

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
│   ├── bdx-mcworld-generation.md    # BDX 命令流 / MCWorld 生成与回读
│   ├── bdx-chain-packaging.md       # BDX 打包：单区块盘旋/初始化分离/验收
│   ├── building-design.md           # 建筑：场地/体量/轮廓/材质/立面/屋顶/动线
│   ├── building-corpus-learning.md  # 语料索引/归类/风格卡/模仿/建造
│   ├── gothic-cathedral-case.md     # 案例：300 样本→哥特教堂重做
│   ├── interior-design.md           # 内饰：动线/焦点/分层/光/材质/教堂模板
│   ├── spectacle-design.md          # 亮眼/奇观：剪影/对比/发光/运动/声音
│   ├── creative-thinking.md         # 6 问、3 方向、联动矩阵、红队、最小闭环
│   ├── functions-and-packs.md       # mcfunction、tick.json、manifest、schedule
│   ├── debugging.md                 # 症状→原因→修复、探针、二分法
│   ├── bedrock-vs-java.md           # 差异速查 + Java→Bedrock 翻译表
│   ├── netease-1.21.130.md          # 网易命令边界、schedule 结论、未验证命令
│   └── netease-corpus-patterns.md   # 12 个真实网易地图的命令方块语料分析
├── assets/
│   ├── chain-spec.schema.json   # spec.json 的 JSON Schema
│   ├── design-brief.template.md # 设计前思考模板（3 方向/联动图/风险）
│   ├── building-brief.template.md # 建筑简报（参考/体量/材质/动线）
│   ├── interior-brief.template.md # 内饰简报（动线/焦点/分层/光）
│   ├── manifest.template.json   # 行为包 manifest 模板
│   ├── tick.template.json       # tick.json 模板
│   ├── bdx2mcworld.go           # BDX→MCWorld 参考实现
│   └── mcworld-template.mcworld # 干净平坦世界模板
├── scripts/
│   ├── chain_lint.py            # 校验 spec + 生成构建表（无第三方依赖）
│   ├── bdxgen.py                # 完整方块/命令方块 BDX 生成器（brotli）
│   ├── buildgen.py              # 建筑 plan → 完整方块 BDX
│   ├── mcworldgen.py            # 建筑 plan → 可打开即建的 MCWorld
│   ├── sunrain_index.py         # 建筑/BDX/图片语料索引器
│   ├── corpus_query.py          # 索引查询
│   └── schematic_blocks.py      # schematic 材质/方块统计
└── examples/
    ├── arena-countdown/         # 倒计时：秒时钟 + 状态机 + 脉冲标记
    ├── vending-machine/         # 售货机：条件流水线 + 库存 + 清理
    ├── toggle-lamp/             # 开关灯：取模翻转 + 并行分支 + 坐标
    ├── snowball-menu/           # 雪球三级菜单：256 方块、紧凑布局、BDX + UI 预览
    ├── fmbe-player/             # FMBE 1:1 玩家：10 部件、142 方块、预览 + BDX
    ├── bdx-generator/           # BDX/MCWorld 最小生成样例（3 方块）
    └── build-pipeline/          # 建筑 plan → BDX/MCWorld 完整示例
```

## Roadmap

- **建筑设计**：已加入 `building-design.md` + `building-corpus-learning.md` + Sunrain 索引；后续用更多参考细化。
- **项目名称**：`MinecraftBE Commands & Building`；GitHub 仓库 `MinecraftBE-Command-Building-Skill`。

## 1. 安装

### 项目级（只对当前工作区生效）

```bash
git clone https://github.com/yixin-amore/MinecraftBE-Command-Building-Skill.git
mkdir -p <workspace>/.dsh/skills
cp -R MinecraftBE-Command-Building-Skill <workspace>/.dsh/skills/mcbe-command-blocks
```

DSH 启动时会扫描 `<workspace>/.dsh/skills`，目录里必须有 `SKILL.md`。

### 用户级（所有项目生效）

```bash
mkdir -p ~/.dsh/skills
cp -R MinecraftBE-Command-Building-Skill ~/.dsh/skills/mcbe-command-blocks
```

或者软链接，改一处全局生效：

```bash
ln -sfn "$PWD/MinecraftBE-Command-Building-Skill" ~/.dsh/skills/mcbe-command-blocks
```

### 环境要求

| 需求 | 说明 |
|---|---|
| Python 3.10+ | 所有脚本 |
| `brotli` | 仅 `bdxgen.py` / `buildgen.py` |
| BDX 导入器 | 导入 `.bdx` 时需要 |
| Minecraft Bedrock | 打开 `.mcworld` 时需要 |

```bash
python3 -m pip install brotli
```

## 2. 验证安装

```bash
cd ~/.dsh/skills/mcbe-command-blocks
test -f SKILL.md && echo SKILL_OK

python3 scripts/buildgen.py examples/build-pipeline/plan.json /tmp/check.bdx
python3 scripts/mcworldgen.py examples/build-pipeline/plan.json /tmp/check.mcworld
ls -lh /tmp/check.bdx /tmp/check.mcworld
```

预期：

```text
SKILL_OK
{"normal_blocks": 91, "command_blocks": 1, ...}
{"name": "Build Pipeline Demo", ...}
```

## 3. 在 DSH 里使用

直接把需求说清楚，模型会读 `SKILL.md`，先定状态/时序，再写 spec/plan 和文件。

**好需求：**

> “在 `300 64 500` 建一座 20×20 的石屋，导出 BDX 和 MCWorld。”

**需要补参数的需求：**

> “建个好看的主城。”

后者需要先确认坐标、尺寸、风格、功能、性能预算。

常用说法：

- “基岩版怎么让玩家站上金块时触发命令？”
- “设计一个 3 秒倒计时 + 开局的命令方块链，并生成 BDX。”
- “这个链为什么第二个方块不执行？”
- “把这段 Java 命令翻译成基岩版。”
- “按这个 plan 生成 BDX 和 MCWorld。”

## 4. 命令方块：spec → BDX

`spec.json` 描述链；`chain_lint.py` 校验；`bdxgen.py` 生成命令方块 BDX。

```bash
# 校验
python3 scripts/chain_lint.py examples/arena-countdown/spec.json

# 生成构建表
python3 scripts/chain_lint.py examples/arena-countdown/spec.json --write plan.md

# 生成 BDX
python3 scripts/bdxgen.py --spec examples/bdx-generator/demo.json /tmp/demo.bdx
```

最小 spec 片段：

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

## 5. 建筑：plan → BDX / MCWorld

一份 `plan.json` 同时驱动两边：

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
# 完整方块 BDX（普通方块 + 命令方块）
python3 scripts/buildgen.py plan.json out.bdx

# MCWorld：首次 tick 由 behavior pack 建造
python3 scripts/mcworldgen.py plan.json out.mcworld
```

字段：

| 字段 | 说明 |
|---|---|
| `fills` | `from` / `to` / `block`，可加 `data` / `states` |
| `blocks` | 单方块 `pos` / `block` |
| `commands` | 命令方块 `pos` / `type` / `command` |

- `buildgen.py` 展开 fills，写完整 BDX；不依赖 AuroraBuild/Go。
- `mcworldgen.py` 使用仓库内 `assets/mcworld-template.mcworld` + behavior pack，打开世界即建造。
- 大建筑会展开成很多方块；脚本有 2,000,000 块上限，超了拆 plan。

## 6. 导入/打开

### BDX

用任意 BDX 导入器导入 `out.bdx`；导入参数以导入器为准。  
如果是命令方块链，导入后确认：

- 命令方块 mode/chain/facing 正确
- 坐标与世界匹配
- 需要时加 `tickingarea`

### MCWorld

双击 `out.mcworld` 打开即可。首次进入后 behavior pack 的首次 tick 会执行建造。  
如果没建造，先确认世界设置里 **Cheats / Command Blocks** 已开启（模板默认开启）。

## 7. 排错

| 症状 | 处理 |
|---|---|
| `ModuleNotFoundError: brotli` | `python3 -m pip install brotli` |
| DSH 不加载技能 | 确认目录里有 `SKILL.md`，路径是 `.dsh/skills/mcbe-command-blocks/` |
| BDX 无法导入 | 先 `python3 scripts/chain_lint.py` 或检查 BDX 头 `BD@` |
| MCWorld 没建造 | 确认 Cheats/Command Blocks 开启；打开世界后等 1 tick |
| 建筑太大 | 拆 plan；单次 BDX/MCWorld 不要一次塞几百万方块 |
| 命令链不跑 | 检查 head mode、facing、conditional、tickingarea |

## 8. 校验 spec / 生成构建表

```bash
python3 -m pip install brotli   # bdxgen.py 需要
python3 scripts/bdxgen.py --spec examples/bdx-generator/demo.json /tmp/demo.bdx
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
- 旧导入图里的 `execute @a ~ ~ ~` 旧语法，新图不要用；先手工升级。

## License

MIT
